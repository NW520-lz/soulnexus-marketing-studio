"""Turn spoken lines into one voice-over track with ElevenLabs text-to-speech.

Usage: python scripts/tts.py daily/<date>/edit/vo.json [--voice <voice_id>] [--model eleven_multilingual_v2]

vo.json (paths are relative to the day directory, i.e. the parent of edit/):
{
  "output": "edit/src/vo.m4a",
  "lines": [
    {"start": 0.4, "text": "A kitten knight is given a dragon's egg."},
    {"start": 3.2, "text": "One line in, a script out."}
  ]
}

"start" is when the line begins in the rough cut (seconds). Each line is synthesised once and cached in
edit/vo/ by text + voice + model, so reruns and re-edits cost no extra characters. A line that runs into the
next one is reported; shorten its text rather than speeding it up.

The API key comes from ELEVENLABS_API_KEY (environment or the .env file in the workspace root), the voice
from --voice or ELEVENLABS_VOICE_ID. No vo.json means no voice-over: the edit stays caption-only.
"""

import argparse
import hashlib
import json
import os
import subprocess
import urllib.error
import urllib.request
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parent.parent
API = "https://api.elevenlabs.io/v1/text-to-speech"
OUTPUT_FORMAT = "mp3_44100_128"


def read_setting(name):
    if os.environ.get(name):
        return os.environ[name]
    env_file = WORKSPACE / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            key, _, value = line.partition("=")
            if key.strip() == name and value.strip():
                return value.strip().strip('"')
    return None


def synthesize(text, previous_text, next_text, voice_id, model_id, api_key):
    body = {"text": text, "model_id": model_id}
    if previous_text:
        body["previous_text"] = previous_text
    if next_text:
        body["next_text"] = next_text
    request = urllib.request.Request(
        f"{API}/{voice_id}?output_format={OUTPUT_FORMAT}",
        data=json.dumps(body).encode("utf-8"),
        headers={"xi-api-key": api_key, "Content-Type": "application/json", "Accept": "audio/mpeg"},
    )
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            return response.read()
    except urllib.error.HTTPError as error:
        raise SystemExit(f"ElevenLabs returned {error.code}: {error.read().decode('utf-8', 'replace')[:300]}")


def audio_duration(path):
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
        capture_output=True, text=True, check=True,
    )
    return float(result.stdout.strip())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("vo_json")
    parser.add_argument("--voice", default=read_setting("ELEVENLABS_VOICE_ID"))
    parser.add_argument("--model", default="eleven_multilingual_v2")
    args = parser.parse_args()

    api_key = read_setting("ELEVENLABS_API_KEY")
    if not api_key:
        raise SystemExit("ELEVENLABS_API_KEY is not set (environment or .env in the workspace root)")
    if not args.voice:
        raise SystemExit("No voice: pass --voice or set ELEVENLABS_VOICE_ID")

    plan_path = Path(args.vo_json).resolve()
    day_dir = plan_path.parent.parent
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    lines = sorted(plan["lines"], key=lambda line: line["start"])

    cache_dir = day_dir / "edit" / "vo"
    cache_dir.mkdir(parents=True, exist_ok=True)

    clips = []
    for index, line in enumerate(lines):
        key = hashlib.sha1(f"{args.voice}|{args.model}|{line['text']}".encode("utf-8")).hexdigest()[:16]
        clip = cache_dir / f"{key}.mp3"
        if clip.exists():
            print(f"cached   {line['start']:6.2f}s  {line['text']}")
        else:
            previous_text = lines[index - 1]["text"] if index > 0 else None
            next_text = lines[index + 1]["text"] if index + 1 < len(lines) else None
            clip.write_bytes(synthesize(line["text"], previous_text, next_text, args.voice, args.model, api_key))
            print(f"spoken   {line['start']:6.2f}s  {line['text']}  ({len(line['text'])} chars)")
        clips.append((clip, line["start"], audio_duration(clip)))

    for (clip, start, length), following in zip(clips, clips[1:] + [None]):
        if following and start + length > following[1]:
            print(f"WARNING  line at {start:.2f}s ends at {start + length:.2f}s, after the next line starts at {following[1]:.2f}s")

    inputs, filters = [], []
    for index, (clip, start, _) in enumerate(clips):
        inputs += ["-i", str(clip)]
        delay_ms = int(round(start * 1000))
        filters.append(f"[{index}:a]aresample=48000,aformat=channel_layouts=stereo,adelay={delay_ms}:all=1[a{index}]")
    filters.append(f"{''.join(f'[a{i}]' for i in range(len(clips)))}amix=inputs={len(clips)}:normalize=0:dropout_transition=0[aout]")

    output = day_dir / plan["output"]
    output.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", *inputs, "-filter_complex", ";".join(filters),
         "-map", "[aout]", "-c:a", "aac", "-b:a", "192k", str(output)],
        check=True,
    )
    print(f"{output}  ({audio_duration(output):.2f}s)")


if __name__ == "__main__":
    main()
