#!/usr/bin/env python3
"""Transcribe an approved voiceover for QA; requires openai-whisper and ffmpeg."""
import argparse
import json
from pathlib import Path
import whisper

def main():
    p = argparse.ArgumentParser()
    p.add_argument("audio", type=Path)
    p.add_argument("--model", default="small")
    p.add_argument("--language", default=None, help="Optional language code; auto-detect if omitted")
    p.add_argument("--output", type=Path, default=Path("transcript.json"))
    args = p.parse_args()
    model = whisper.load_model(args.model)
    result = model.transcribe(str(args.audio), language=args.language, word_timestamps=True)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Transcript written to {args.output}; detected language={result.get('language')}")

if __name__ == "__main__": main()
