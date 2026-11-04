"""Local studio page for the daily marketing flow: the user handles files and approvals here, Claude runs the stages.

  python scripts/studio.py serve                     # http://127.0.0.1:5280 (localhost only)
  python scripts/studio.py status daily/<day> --stage editing --busy --message "Cutting the base edit"
  python scripts/studio.py status daily/<day> --handled          # mark every signal so far as handled
  python scripts/studio.py wait daily/<day>          # block until the user sends a new signal, print it, exit

Per day directory:
  status.json    written by Claude: {"stage", "busy", "message", "handled_signals"}
  signals.jsonl  written by the page: one {"time", "action", "note"} per button press
  checklist.json written by Claude in stage A: [{"file", "what", "kind", "orientation", "seconds", "required"}]

Stages: research, recording, editing, review_edit, writing_posts, review_posts, uploading, review_publish, done.
"""

import argparse
import json
import mimetypes
import re
import shutil
import sys
import time
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

WORKSPACE = Path(__file__).resolve().parent.parent
DAILY = WORKSPACE / "daily"
PAGE = WORKSPACE / "studio" / "index.html"
PORT = 5280
DAY_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}(-\d+)?$")
SAFE_NAME = re.compile(r"[^A-Za-z0-9._-]+")
ACTIONS = {"footage_ready", "edit_approved", "edit_changes", "posts_approved", "posts_changes", "published"}
TEXT_FILES = ("research.md", "plan.md", "posts.md", "log.md")


def read_json(path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def read_signals(day_dir):
    path = day_dir / "signals.jsonl"
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_status(day_dir, status):
    (day_dir / "status.json").write_text(json.dumps(status, ensure_ascii=False, indent=1), encoding="utf-8")


def day_state(day_dir):
    status = read_json(day_dir / "status.json", {"stage": "research", "busy": False, "message": "", "handled_signals": 0})
    signals = read_signals(day_dir)
    footage_dir = day_dir / "footage"
    footage = sorted(p.name for p in footage_dir.iterdir() if p.is_file()) if footage_dir.exists() else []
    review_dir = day_dir / "edit" / "review"
    master = day_dir / "edit" / "out" / "master.mp4"
    publish_dir = day_dir / "publish"
    return {
        "day": day_dir.name,
        "status": status,
        "pending_signals": signals[status.get("handled_signals", 0):],
        "checklist": read_json(day_dir / "checklist.json", []),
        "footage": footage,
        "texts": {name: (day_dir / name).read_text(encoding="utf-8") for name in TEXT_FILES if (day_dir / name).exists()},
        "master": f"edit/out/master.mp4?v={int(master.stat().st_mtime)}" if master.exists() else None,
        "review": sorted(f"edit/review/{p.name}" for p in review_dir.glob("*.png")) if review_dir.exists() else [],
        "publish_shots": sorted(f"publish/{p.name}" for p in publish_dir.glob("*.png")) if publish_dir.exists() else [],
    }


def resolve_day(name):
    if not DAY_PATTERN.match(name):
        return None
    day_dir = DAILY / name
    return day_dir if day_dir.is_dir() else None


class StudioHandler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def send_json(self, payload, code=200):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        url = urlparse(self.path)
        parts = [unquote(p) for p in url.path.split("/") if p]
        if not parts:
            body = PAGE.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if parts == ["api", "days"]:
            days = sorted((p.name for p in DAILY.iterdir() if p.is_dir() and DAY_PATTERN.match(p.name)), reverse=True)
            self.send_json({"days": days, "today": datetime.now().strftime("%Y-%m-%d")})
            return
        if len(parts) == 3 and parts[:2] == ["api", "day"]:
            day_dir = resolve_day(parts[2])
            if day_dir is None:
                self.send_json({"error": "no such day"}, 404)
                return
            self.send_json(day_state(day_dir))
            return
        if len(parts) >= 3 and parts[0] == "files":
            day_dir = resolve_day(parts[1])
            target = (day_dir / Path(*parts[2:])).resolve() if day_dir else None
            if target is None or not target.is_file() or day_dir.resolve() not in target.parents:
                self.send_error(404)
                return
            self.send_file(target)
            return
        self.send_error(404)

    def send_file(self, path):
        size = path.stat().st_size
        content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        start, end = 0, size - 1
        # Browsers need byte ranges to seek inside a video.
        match = re.match(r"bytes=(\d*)-(\d*)", self.headers.get("Range", ""))
        if match and (match.group(1) or match.group(2)):
            if match.group(1):
                start = int(match.group(1))
                end = int(match.group(2)) if match.group(2) else size - 1
            else:
                start = max(size - int(match.group(2)), 0)
            end = min(end, size - 1)
            self.send_response(206)
            self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
        else:
            self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Content-Length", str(end - start + 1))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        with path.open("rb") as source:
            source.seek(start)
            remaining = end - start + 1
            while remaining > 0:
                chunk = source.read(min(1024 * 1024, remaining))
                if not chunk:
                    break
                try:
                    self.wfile.write(chunk)
                except ConnectionError:
                    return
                remaining -= len(chunk)

    def do_PUT(self):
        # PUT /api/day/<day>/footage?name=<file name>, body is the raw file.
        url = urlparse(self.path)
        parts = [unquote(p) for p in url.path.split("/") if p]
        day_dir = resolve_day(parts[2]) if len(parts) == 4 and parts[:2] == ["api", "day"] and parts[3] == "footage" else None
        name = SAFE_NAME.sub("-", parse_qs(url.query).get("name", [""])[0]).strip(".-")
        if day_dir is None or not name:
            self.send_json({"error": "bad upload"}, 400)
            return
        footage_dir = day_dir / "footage"
        footage_dir.mkdir(exist_ok=True)
        partial = footage_dir / f".{name}.part"
        remaining = int(self.headers.get("Content-Length", "0"))
        with partial.open("wb") as out:
            while remaining > 0:
                chunk = self.rfile.read(min(1024 * 1024, remaining))
                if not chunk:
                    break
                out.write(chunk)
                remaining -= len(chunk)
        if remaining:
            partial.unlink()
            self.send_json({"error": "upload interrupted"}, 400)
            return
        # The same slot may be re-uploaded with another extension; keep only the newest file.
        stem = Path(name).stem
        for old in footage_dir.glob(f"{stem}.*"):
            if old.name != name:
                old.unlink()
        shutil.move(partial, footage_dir / name)
        self.send_json({"saved": name})

    def do_POST(self):
        # POST /api/day/<day>/signal  {"action": ..., "note": ...}
        parts = [unquote(p) for p in urlparse(self.path).path.split("/") if p]
        day_dir = resolve_day(parts[2]) if len(parts) == 4 and parts[:2] == ["api", "day"] and parts[3] == "signal" else None
        length = int(self.headers.get("Content-Length", "0"))
        try:
            payload = json.loads(self.rfile.read(length).decode("utf-8") or "{}") if length < 65536 else {}
        except (UnicodeDecodeError, ValueError):
            payload = {}
        if day_dir is None or not isinstance(payload, dict) or payload.get("action") not in ACTIONS:
            self.send_json({"error": "bad signal"}, 400)
            return
        signal = {"time": datetime.now().isoformat(timespec="seconds"), "action": payload["action"], "note": str(payload.get("note", ""))[:4000]}
        with (day_dir / "signals.jsonl").open("a", encoding="utf-8") as out:
            out.write(json.dumps(signal, ensure_ascii=False) + "\n")
        self.send_json({"ok": True})


def serve():
    DAILY.mkdir(exist_ok=True)
    server = ThreadingHTTPServer(("127.0.0.1", PORT), StudioHandler)
    print(f"studio on http://127.0.0.1:{PORT}", flush=True)
    server.serve_forever()


def set_status(day_dir, args):
    status = read_json(day_dir / "status.json", {"stage": "research", "busy": False, "message": "", "handled_signals": 0})
    if args.stage:
        status["stage"] = args.stage
    status["busy"] = args.busy
    if args.message is not None:
        status["message"] = args.message
    if args.handled:
        status["handled_signals"] = len(read_signals(day_dir))
    write_status(day_dir, status)
    print(json.dumps(status, ensure_ascii=False))


def wait(day_dir):
    while True:
        handled = read_json(day_dir / "status.json", {}).get("handled_signals", 0)
        pending = read_signals(day_dir)[handled:]
        if pending:
            print(json.dumps(pending, ensure_ascii=False), flush=True)
            return
        time.sleep(1)


def main():
    # Windows consoles default to GBK; Claude reads this output as UTF-8.
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("serve")
    status_parser = commands.add_parser("status")
    status_parser.add_argument("day_dir")
    status_parser.add_argument("--stage", choices=["research", "recording", "editing", "review_edit", "writing_posts", "review_posts", "uploading", "review_publish", "done"])
    status_parser.add_argument("--busy", action="store_true")
    status_parser.add_argument("--message")
    status_parser.add_argument("--handled", action="store_true")
    wait_parser = commands.add_parser("wait")
    wait_parser.add_argument("day_dir")
    args = parser.parse_args()

    if args.command == "serve":
        serve()
        return
    day_dir = Path(args.day_dir).resolve()
    if not day_dir.is_dir():
        sys.exit(f"{day_dir} does not exist")
    if args.command == "status":
        set_status(day_dir, args)
    else:
        wait(day_dir)


if __name__ == "__main__":
    main()
