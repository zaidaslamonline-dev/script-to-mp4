#!/usr/bin/env python3
"""Generate clean, separate Kokoro Hindi voice audition clips (never eSpeak fallback)."""
import argparse
import json
from pathlib import Path
import numpy as np
import soundfile as sf
from kokoro import KPipeline

SAMPLES = {
    "sid": {
        "voice": "hm_psi",
        "text": "क्या हुआ लाला भाई? फोन तो गरम हो गया, बिज़नेस ठंडा क्यों है? समझ गया! प्रॉब्लम एन्क्वायरीज़ की क्वांटिटी नहीं, क्वालिटी की है।",
        "speed": 1.04,
    },
    "lala-bhai": {
        "voice": "hm_omega",
        "text": "अरे सिड! कोई सिर्फ़ प्राइस पूछता है, कोई सर्विस एरिया के बाहर है, और कोई बोलता है बाद में देखेंगे! अब मैं क्या करूँ?",
        "speed": 0.94,
    },
}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=Path("voice-preview"))
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    pipeline = KPipeline(lang_code="h", device="cpu")
    results = {}
    for character, cfg in SAMPLES.items():
        chunks = []
        for _graphemes, _phonemes, audio in pipeline(cfg["text"], voice=cfg["voice"], speed=cfg["speed"]):
            if audio is not None:
                chunks.append(audio.detach().cpu().numpy())
        if not chunks:
            raise RuntimeError(f"Kokoro returned no audio for {character}")
        audio = np.concatenate(chunks).astype(np.float32)
        peak = float(np.max(np.abs(audio)))
        if peak > 0.99:
            audio *= 0.95 / peak
        path = args.output_dir / f"{character}.wav"
        sf.write(path, audio, 24000, subtype="PCM_16")
        results[character] = {
            "engine": "Kokoro", "voice": cfg["voice"], "language": "Hindi",
            "speed": cfg["speed"], "sample_rate": 24000,
            "duration_seconds": round(len(audio) / 24000, 2), "peak": round(float(np.max(np.abs(audio))), 4),
            "file": str(path),
        }
    (args.output_dir / "voice-preview.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    main()
