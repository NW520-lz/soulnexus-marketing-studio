"""Bring a finished video's audio to -14 LUFS with a measured two-pass loudnorm; the picture is copied untouched.

Usage: python scripts/loudfix.py daily/<date>/edit/out/master.mp4
Rewrites the file in place (the original is kept next to it as master.pre-loudfix.mp4 only if the pass succeeds).

render.py's single-pass loudnorm lands several dB low on short clips with speech and silence; this pass measures the
rendered file and applies the exact gain, so the -14 LUFS gate in sop.md holds.
"""

import json
import re
import subprocess
import sys
from pathlib import Path

TARGET = "I=-14:TP=-1.5:LRA=11"


def measure(path):
    result = subprocess.run(
        ["ffmpeg", "-hide_banner", "-i", str(path), "-af", f"loudnorm={TARGET}:print_format=json", "-f", "null", "-"],
        capture_output=True, text=True, check=True,
    )
    return json.loads(re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", result.stderr).group(0))


def main():
    video = Path(sys.argv[1]).resolve()
    stats = measure(video)
    apply_filter = (
        f"loudnorm={TARGET}:measured_I={stats['input_i']}:measured_TP={stats['input_tp']}"
        f":measured_LRA={stats['input_lra']}:measured_thresh={stats['input_thresh']}"
        f":offset={stats['target_offset']}:linear=true"
    )
    fixed = video.with_name(video.stem + ".loudfix.mp4")
    subprocess.run(
        ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(video), "-map", "0:v", "-map", "0:a",
         "-c:v", "copy", "-af", f"{apply_filter},aresample=48000", "-c:a", "aac", "-b:a", "192k", str(fixed)],
        check=True,
    )
    backup = video.with_name(video.stem + ".pre-loudfix.mp4")
    video.replace(backup)
    fixed.replace(video)
    print(f"{video}: {float(stats['input_i']):.1f} LUFS -> about -14 (original kept as {backup.name})")


if __name__ == "__main__":
    main()
