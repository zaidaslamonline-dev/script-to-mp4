#!/usr/bin/env python3
"""CPU audition for AI4Bharat Indic Parler-TTS; emits one clip per character."""
import json
from pathlib import Path

import numpy as np
import soundfile as sf
import torch
from parler_tts import ParlerTTSForConditionalGeneration
from transformers import AutoTokenizer

MODEL = "ai4bharat/indic-parler-tts"
TEXTS = {
    "sid": "क्या हुआ लाला भाई? फोन तो गरम हो गया, बिज़नेस ठंडा क्यों है? समझ गया! प्रॉब्लम एन्क्वायरीज़ की क्वांटिटी नहीं, क्वालिटी की है।",
    "lala-bhai": "अरे सिड! कोई सिर्फ़ प्राइस पूछता है, कोई सर्विस एरिया के बाहर है, और कोई बोलता है बाद में देखेंगे! अब मैं क्या करूँ?",
}
DESCRIPTIONS = {
    "sid": "A young adult Indian male speaker with a bright, confident, energetic voice, medium pitch, quick conversational delivery, expressive emphasis, natural Hindi pronunciation, close clear studio recording.",
    "lala-bhai": "A middle-aged Indian male speaker with a warm, slightly rough, lively conversational voice, lower medium pitch, expressive comic frustration, natural Hindi pronunciation, close clear studio recording.",
}

def main():
    out = Path("voice-preview")
    out.mkdir(parents=True, exist_ok=True)
    torch.set_num_threads(2)
    device = "cpu"
    model = ParlerTTSForConditionalGeneration.from_pretrained(
        MODEL, torch_dtype=torch.float32, low_cpu_mem_usage=True
    ).to(device)
    tokenizer = AutoTokenizer.from_pretrained(MODEL)
    desc_tokenizer = AutoTokenizer.from_pretrained(model.config.text_encoder._name_or_path)
    results = {}
    for character, text in TEXTS.items():
        prompt = tokenizer(text, return_tensors="pt")
        desc = desc_tokenizer(DESCRIPTIONS[character], return_tensors="pt")
        with torch.inference_mode():
            audio = model.generate(
                input_ids=desc.input_ids,
                attention_mask=desc.attention_mask,
                prompt_input_ids=prompt.input_ids,
                prompt_attention_mask=prompt.attention_mask,
                do_sample=True,
            )
        samples = audio.cpu().numpy().squeeze().astype(np.float32)
        if samples.ndim != 1 or not len(samples):
            raise RuntimeError(f"Unexpected audio shape for {character}: {samples.shape}")
        peak = float(np.max(np.abs(samples)))
        if peak > 0.99:
            samples *= 0.95 / peak
        filename = f"parler-{character}.wav"
        sf.write(out / filename, samples, model.config.sampling_rate, subtype="PCM_16")
        results[character] = {
            "engine": "AI4Bharat Indic Parler-TTS",
            "model": MODEL,
            "description": DESCRIPTIONS[character],
            "sample_rate": int(model.config.sampling_rate),
            "duration_seconds": round(len(samples) / model.config.sampling_rate, 2),
            "file": filename,
        }
        print(f"Generated {filename}")
    (out / "parler-manifest.json").write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")

if __name__ == "__main__":
    main()
