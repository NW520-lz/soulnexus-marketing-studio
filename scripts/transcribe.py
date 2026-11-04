"""Transcribe a voiceover into short SRT captions (a few words per line, as short-form video expects).

Usage: python scripts/transcribe.py <audio-or-video> <output.srt> [--words-json words.json] [--words 5] [--model small] [--language en]

--words-json also writes every word with its start/end seconds, for animated captions.

Requires faster-whisper (`python -m pip install faster-whisper`); the model downloads on first use.
"""

import argparse
import json

from faster_whisper import WhisperModel

# Spellings whisper should prefer for the product and model names we say on camera.
PRODUCT_VOCABULARY = "SoulNexus, soulnexus.top, Seedance, MiniMax, Nano Banana, GPT Image, AI short drama."


def timestamp(seconds):
    millis = int(round(seconds * 1000))
    hours, millis = divmod(millis, 3_600_000)
    minutes, millis = divmod(millis, 60_000)
    secs, millis = divmod(millis, 1000)
    return f"{hours:02}:{minutes:02}:{secs:02},{millis:03}"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("source")
    parser.add_argument("output")
    parser.add_argument("--words", type=int, default=5)
    parser.add_argument("--model", default="small")
    parser.add_argument("--language", default="en")
    parser.add_argument("--words-json")
    args = parser.parse_args()

    model = WhisperModel(args.model, device="cpu", compute_type="int8")
    segments, _ = model.transcribe(
        args.source, language=args.language, word_timestamps=True, vad_filter=True,
        initial_prompt=PRODUCT_VOCABULARY,
    )

    words = [word for segment in segments for word in segment.words]
    # A caption ends after `--words` words or at the end of a sentence, whichever comes first.
    captions, current = [], []
    for word in words:
        current.append(word)
        if len(current) == args.words or word.word.strip().endswith((".", "?", "!")):
            captions.append(current)
            current = []
    if current:
        captions.append(current)
    with open(args.output, "w", encoding="utf-8") as srt:
        for number, caption in enumerate(captions, start=1):
            text = "".join(word.word for word in caption).strip()
            srt.write(f"{number}\n{timestamp(caption[0].start)} --> {timestamp(caption[-1].end)}\n{text}\n\n")
    if args.words_json:
        timed_words = [{"text": word.word.strip(), "start": round(word.start, 3), "end": round(word.end, 3)} for word in words]
        with open(args.words_json, "w", encoding="utf-8") as out:
            json.dump(timed_words, out, ensure_ascii=False, indent=1)
    print(f"{len(captions)} captions -> {args.output}")


if __name__ == "__main__":
    main()
