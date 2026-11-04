"""Render a vertical social video from an edit plan with ffmpeg.

Usage: python scripts/render.py daily/<date>/edit/edit.json

edit.json (paths are relative to the day directory, i.e. the parent of edit/):
{
  "output": "edit/out/master.mp4",
  "width": 1080, "height": 1920, "fps": 30,
  "clips": [
    {"file": "footage/01-hook.mp4", "start": 0.0, "end": 3.2},
    {"file": "footage/02-canvas.mp4", "start": 5.0, "end": 12.0, "crop": "0.3,0.5,1.5"}
  ],
  "voiceover": {"file": "footage/vo.m4a", "clip_volume": 0.2},
  "music": {"file": "footage/bgm.mp3", "volume": 0.12},
  "subtitles": "edit/subs.srt",
  "subtitle_font": "Microsoft YaHei"
}

"crop" is an optional "center_x,center_y,zoom" for screen recordings: the centre is a fraction of
the source frame, zoom 1 is the largest region with the output aspect ratio that fits the source.
"voiceover", "music" and "subtitles" are optional. Audio is normalised to -14 LUFS.
"""

import json
import subprocess
import sys
from pathlib import Path


def has_audio(path):
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries", "stream=index", "-of", "csv=p=0", str(path)],
        capture_output=True, text=True, check=True,
    )
    return bool(result.stdout.strip())


def main():
    plan_path = Path(sys.argv[1]).resolve()
    day_dir = plan_path.parent.parent
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    width, height, fps = plan.get("width", 1080), plan.get("height", 1920), plan.get("fps", 30)

    inputs, filters, concat_labels = [], [], []
    input_count = 0
    for index, clip in enumerate(plan["clips"]):
        source = day_dir / clip["file"]
        duration = clip["end"] - clip["start"]
        inputs += ["-ss", str(clip["start"]), "-t", str(duration), "-i", str(source)]
        clip_input = input_count
        input_count += 1

        video_chain = f"[{clip_input}:v]"
        if clip.get("crop"):
            center_x, center_y, zoom = (float(value) for value in clip["crop"].split(","))
            # Zoom 1 is the largest region with the output aspect ratio that fits the source;
            # the region is centred on (center_x, center_y) and clamped inside the frame.
            video_chain += (
                f"crop=w=min(iw\\,ih*{width}/{height})/{zoom}:h=ow*{height}/{width}"
                f":x=max(0\\,min(iw-ow\\,iw*{center_x}-ow/2)):y=max(0\\,min(ih-oh\\,ih*{center_y}-oh/2)),"
            )
        video_chain += (
            f"scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height},"
            f"fps={fps},setsar=1,format=yuv420p[v{index}]"
        )
        filters.append(video_chain)

        if has_audio(source):
            audio_label = f"{clip_input}:a"
        else:
            inputs += ["-f", "lavfi", "-t", str(duration), "-i", "anullsrc=r=48000:cl=stereo"]
            audio_label = f"{input_count}:a"
            input_count += 1
        filters.append(f"[{audio_label}]aresample=48000,aformat=channel_layouts=stereo[a{index}]")
        concat_labels.append(f"[v{index}][a{index}]")

    filters.append(f"{''.join(concat_labels)}concat=n={len(plan['clips'])}:v=1:a=1[vcat][acat]")
    video_out, audio_out = "[vcat]", "[acat]"

    subtitles = plan.get("subtitles")
    if subtitles:
        font = plan.get("subtitle_font", "Microsoft YaHei")
        style = f"FontName={font},FontSize=13,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BorderStyle=1,Outline=2,Shadow=0,Alignment=2,MarginV=70"
        # ffmpeg runs with cwd=day_dir so the subtitle path needs no drive-letter escaping.
        subtitle_path = Path(subtitles).as_posix()
        filters.append(f"{video_out}subtitles='{subtitle_path}':force_style='{style}'[vsub]")
        video_out = "[vsub]"

    mix_labels = [audio_out]
    voiceover = plan.get("voiceover")
    if voiceover:
        inputs += ["-i", str(day_dir / voiceover["file"])]
        vo_input = input_count
        input_count += 1
        filters.append(f"{audio_out}volume={voiceover.get('clip_volume', 0.2)}[aclip]")
        filters.append(f"[{vo_input}:a]aresample=48000,aformat=channel_layouts=stereo[avo]")
        mix_labels = ["[aclip]", "[avo]"]
    music = plan.get("music")
    if music:
        inputs += ["-stream_loop", "-1", "-i", str(day_dir / music["file"])]
        music_input = input_count
        input_count += 1
        filters.append(f"[{music_input}:a]aresample=48000,aformat=channel_layouts=stereo,volume={music.get('volume', 0.12)}[amus]")
        mix_labels.append("[amus]")
    if len(mix_labels) > 1:
        filters.append(f"{''.join(mix_labels)}amix=inputs={len(mix_labels)}:duration=first:normalize=0[amix]")
        audio_out = "[amix]"
    else:
        audio_out = mix_labels[0]
    filters.append(f"{audio_out}loudnorm=I=-14:TP=-1.5:LRA=11[aout]")

    output = day_dir / plan["output"]
    output.parent.mkdir(parents=True, exist_ok=True)
    command = [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error", *inputs,
        "-filter_complex", ";".join(filters),
        "-map", video_out, "-map", "[aout]",
        "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
        "-movflags", "+faststart", str(output),
    ]
    subprocess.run(command, cwd=day_dir, check=True)
    print(output)


if __name__ == "__main__":
    main()
