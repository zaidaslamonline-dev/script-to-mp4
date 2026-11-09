#!/usr/bin/env python3
"""Generate 16 Kokoro Hindi voice auditions: 8 options for Sid and 8 for Lala Bhai."""
import argparse
import json
from pathlib import Path

import numpy as np
import soundfile as sf
from kokoro import KPipeline

TEXT = {
    "sid": "क्या हुआ लाला भाई? फोन तो गरम हो गया, बिज़नेस ठंडा क्यों है? समझ गया! प्रॉब्लम एन्क्वायरीज़ की क्वांटिटी नहीं, क्वालिटी की है।",
    "lala-bhai": "अरे सिड! कोई सिर्फ़ प्राइस पूछता है, कोई सर्विस एरिया के बाहर है, और कोई बोलता है बाद में देखेंगे! अब मैं क्या करूँ?",
}

# Kokoro's Hindi voice set. Each voice is auditioned with two distinct pacing choices.
VOICE_IDS = ["hf_alpha", "hf_beta", "hm_omega", "hm_psi"]
SPEEDS = [0.92, 1.06]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=Path("voice-preview"))
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    pipeline = KPipeline(lang_code="h", device="cpu")
    results = {}
    for character, text in TEXT.items():
        for voice_index, voice in enumerate(VOICE_IDS, start=1):
            for pace_index, speed in enumerate(SPEEDS, start=1):
                chunks = []
                for _graphemes, _phonemes, audio in pipeline(text, voice=voice, speed=speed):
                    if audio is not None:
                        chunks.append(audio.detach().cpu().numpy())
                if not chunks:
                    raise RuntimeError(f"Kokoro returned no audio: {character}, {voice}")
                audio = np.concatenate(chunks).astype(np.float32)
                peak = float(np.max(np.abs(audio)))
                if peak > 0.99:
                    audio *= 0.95 / peak
                option = (voice_index - 1) * 2 + pace_index
                filename = f"{character}-option-{option:02d}.wav"
                path = args.output_dir / filename
                sf.write(path, audio, 24000, subtype="PCM_16")
                results[f"{character}-option-{option:02d}"] = {
                    "character": character,
                    "option": option,
                    "engine": "Kokoro",
                    "voice_id": voice,
                    "language": "Hindi",
                    "speed": speed,
                    "sample_rate": 24000,
                    "duration_seconds": round(len(audio) / 24000, 2),
                    "file": filename,
                }
                print(f"Generated {filename} ({voice}, speed={speed})")

    (args.output_dir / "voice-options.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"Generated {len(results)} audition clips.")

if __name__ == "__main__":
    main()
