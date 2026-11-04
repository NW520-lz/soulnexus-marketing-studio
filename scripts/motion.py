"""Build the day's HyperFrames packaging project from the brand templates in brand/motion/.

Usage:
  python scripts/motion.py daily/<date> --hook "Your AI actor keeps changing faces?"
      [--cta-title "Make your AI short drama"] [--cta-sub "soulnexus.top"]
      [--hook-style card|typer] [--hook-seconds 2.6] [--cta-seconds 2.5] [--words-per-group 4]

Reads edit/out/base.mp4 (required) and edit/words.json (optional; from transcribe.py --words-json),
writes edit/motion/ with index.html, compositions/captions.html and assets/. Render it with:
  cd daily/<date>/edit/motion && npx --yes hyperframes@0.8.207 render -o ../out/master.mp4
"""

import argparse
import html
import json
import shutil
import subprocess
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parent.parent
TEMPLATES = WORKSPACE / "brand" / "motion"
SENTENCE_END = (".", "?", "!")
PAUSE_SECONDS = 0.15


def video_duration(path):
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
        capture_output=True, text=True, check=True,
    )
    return round(float(result.stdout.strip()), 3)


def caption_groups(words, words_per_group, duration):
    """Group words for on-screen captions: break at a sentence end, a pause, or the word limit."""
    groups, current = [], []
    for index, word in enumerate(words):
        current.append(word)
        next_word = words[index + 1] if index + 1 < len(words) else None
        pause = next_word is not None and next_word["start"] - word["end"] >= PAUSE_SECONDS
        if len(current) == words_per_group or word["text"].endswith(SENTENCE_END) or pause or next_word is None:
            groups.append(current)
            current = []

    timed = []
    for index, group in enumerate(groups):
        # A caption at exactly 0 s looks pre-existing, so the first one opens slightly late.
        start = max(group[0]["start"], 0.15)
        next_start = groups[index + 1][0]["start"] if index + 1 < len(groups) else duration
        end = max(min(group[-1]["end"] + 0.3, next_start - 0.05, duration), group[-1]["end"])
        timed.append({"id": f"g{index}", "start": round(start, 3), "end": round(end, 3), "words": group})
    return timed


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("day_dir")
    parser.add_argument("--hook", required=True)
    parser.add_argument("--cta-title", default="Make your AI short drama")
    parser.add_argument("--cta-sub", default="soulnexus.top")
    parser.add_argument("--hook-style", choices=["card", "typer"], default="card")
    parser.add_argument("--hook-seconds", type=float, default=2.6)
    parser.add_argument("--cta-seconds", type=float, default=2.5)
    parser.add_argument("--words-per-group", type=int, default=4)
    args = parser.parse_args()

    day_dir = Path(args.day_dir).resolve()
    base = day_dir / "edit" / "out" / "base.mp4"
    duration = video_duration(base)
    if duration < args.hook_seconds + args.cta_seconds + 1:
        raise SystemExit(f"base.mp4 is {duration}s, too short for a {args.hook_seconds}s hook and {args.cta_seconds}s CTA")

    motion_dir = day_dir / "edit" / "motion"
    (motion_dir / "assets").mkdir(parents=True, exist_ok=True)
    (motion_dir / "compositions").mkdir(exist_ok=True)
    shutil.copyfile(base, motion_dir / "assets" / "base.mp4")
    shutil.copyfile(TEMPLATES / "logo.png", motion_dir / "assets" / "logo.png")

    # Captions stop where the CTA card covers the frame.
    cta_start = round(duration - args.cta_seconds, 3)
    captions_host = ""
    words_path = day_dir / "edit" / "words.json"
    if words_path.exists():
        raw_words = json.loads(words_path.read_text(encoding="utf-8"))
        # Whisper can invent words over trailing silence; anything starting under the CTA is dropped too.
        words = [
            {"id": f"w{index}", "text": word["text"], "start": word["start"], "end": min(word["end"], cta_start)}
            for index, word in enumerate(raw_words)
            if word["text"] and word["start"] < cta_start - 0.1
        ]
        groups = caption_groups(words, args.words_per_group, cta_start)
        groups_html = "\n".join(
            f'    <div id="{group["id"]}" class="cap-group">'
            + "".join(
                f'<span class="cap-word"><span id="{word["id"]}-bg" class="cap-bg"></span>'
                f'<span id="{word["id"]}-text" class="cap-text">{html.escape(word["text"])}</span></span>'
                for word in group["words"]
            )
            + "</div>"
            for group in groups
        )
        groups_json = json.dumps(
            [{"id": g["id"], "start": g["start"], "end": g["end"],
              "words": [{"id": w["id"], "text": w["text"], "start": w["start"], "end": w["end"]} for w in g["words"]]}
             for g in groups],
            ensure_ascii=False,
        )
        captions = (TEMPLATES / "captions.html").read_text(encoding="utf-8")
        captions = captions.replace("__GROUPS_HTML__", groups_html).replace("__GROUPS_JSON__", groups_json)
        (motion_dir / "compositions" / "captions.html").write_text(captions, encoding="utf-8")
        captions_host = (
            f'<div id="captions" data-composition-id="captions" data-composition-src="compositions/captions.html" '
            f'data-start="0" data-duration="{cta_start}" data-track-index="1" data-track-kind="captions" '
            f'data-width="1080" data-height="1920"></div>'
        )

    hook = (TEMPLATES / f"hook-{args.hook_style}.html").read_text(encoding="utf-8")
    for placeholder, value in {
        "__HOOK_CHARS__": '<span class="cur"></span>'
        + "".join(f'<span class="ch">{html.escape(char)}</span><span class="cur"></span>' for char in args.hook),
        "__HOOK_DURATION__": str(args.hook_seconds),
        "__HOOK__": html.escape(args.hook),
    }.items():
        hook = hook.replace(placeholder, value)
    (motion_dir / "compositions" / "hook.html").write_text(hook, encoding="utf-8")
    hook_host = (
        f'<div id="hook" data-composition-id="hook" data-composition-src="compositions/hook.html" '
        f'data-start="0.15" data-duration="{args.hook_seconds}" data-track-index="2" data-track-kind="graphics" '
        f'data-width="1080" data-height="1920"></div>'
    )

    index = (TEMPLATES / "index.html").read_text(encoding="utf-8")
    for placeholder, value in {
        "__CAPTIONS_HOST__": captions_host,
        "__HOOK_HOST__": hook_host,
        "__DURATION__": str(duration),
        "__CTA_START__": str(cta_start),
        "__CTA_DURATION__": str(args.cta_seconds),
        "__CTA_TITLE__": html.escape(args.cta_title),
        "__CTA_SUB__": html.escape(args.cta_sub),
    }.items():
        index = index.replace(placeholder, value)
    (motion_dir / "index.html").write_text(index, encoding="utf-8")
    print(motion_dir)


if __name__ == "__main__":
    main()
