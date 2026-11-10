#!/usr/bin/env python3
"""Convert Whisper word timestamps into short, readable caption cards."""
import argparse
import json
from pathlib import Path\nfrom romanize_captions import romanizer

def main():
    p = argparse.ArgumentParser()
    p.add_argument("transcript", type=Path)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--max-words", type=int, default=5)
    p.add_argument("--max-chars", type=int, default=30)
    args = p.parse_args()
    if args.max_words < 1 or args.max_chars < 8:
        p.error("--max-words must be positive and --max-chars at least 8")
    data = json.loads(args.transcript.read_text(encoding="utf-8"))
    ur = romanizer()\n    words = []
    for segment in data.get("segments", []):
        for word in segment.get("words", []):
            token = str(word.get("word", "")).strip()
            if token and word.get("start") is not None and word.get("end") is not None:
                start, end = float(word["start"]), float(word["end"])
                if start >= 0 and end > start:
                    words.append({"text": token, "start": start, "end": end})
    if not words:
        raise SystemExit("No word-level timestamps found. Re-run Whisper with word_timestamps enabled.")
    captions, group = [], []
    def flush():
        if group:
            captions.append({
                "text": ur.romanize_string(" ".join(w["text"] for w in group).strip()),
                "start": round(group[0]["start"], 3),
                "end": round(group[-1]["end"], 3),
            })
            group.clear()
    for word in words:
        candidate = " ".join([w["text"] for w in group] + [word["text"]])
        terminal = word["text"].endswith((".", "!", "?", ";", ":"))
        if group and (len(group) >= args.max_words or len(candidate) > args.max_chars):
            flush()
        group.append(word)
        if terminal:
            flush()
    flush()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps({"captions": captions}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {len(captions)} timed captions to {args.output}")

if __name__ == "__main__":
    main()
