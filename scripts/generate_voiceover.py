#!/usr/bin/env python3
"""Generate a WAV voiceover with Kokoro on CPU from approved script text."""
import argparse
import json
import sys
import hashlib
from pathlib import Path

LANGUAGES = {
    "en": "a", "en-us": "a", "en-gb": "b",
    "hi": "h",
}
# Kokoro currently has no Gujarati voice/G2P pipeline. Never silently substitute.
SUPPORTED_VOICES = {"a", "b", "h"}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--text-file", type=Path, required=True)
    parser.add_argument("--campaign", type=Path, required=True, help="Campaign JSON containing approvals and approved variant copy")
    parser.add_argument("--variant", required=True, choices=["A", "B"])
    parser.add_argument("--language", required=True, help="en, en-us, en-gb, or hi")
    parser.add_argument("--voice", required=True, help="Kokoro voice ID, e.g. af_heart or hf_alpha")
    parser.add_argument("--speed", type=float, default=1.0)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--metadata", type=Path)
    args = parser.parse_args()

    language = args.language.lower()
    lang_code = LANGUAGES.get(language)
    if not lang_code:
        parser.error(
            f"Unsupported Kokoro language '{args.language}'. Supported here: English and Hindi. "
            "Gujarati requires a separately approved voice provider or recorded narration; no silent fallback is allowed."
        )
    if args.voice[:1].lower() != lang_code:
        parser.error(f"Voice '{args.voice}' does not match language '{args.language}' (expected prefix '{lang_code}').")
    if not 0.7 <= args.speed <= 1.3:
        parser.error("--speed must be between 0.7 and 1.3.")
    campaign = json.loads(args.campaign.read_text(encoding="utf-8"))
    if campaign.get("script", {}).get("approved_by_user") is not True:
        parser.error("Script approval is required before TTS generation.")
    variant = next((v for v in campaign.get("variants", []) if str(v.get("variant_id", "")).upper() == args.variant), None)
    if not variant or variant.get("approved") is not True:
        parser.error(f"Variant {args.variant} is not script-approved.")
    text = args.text_file.read_text(encoding="utf-8").strip()
    approved_text = str(variant.get("script_text", "")).strip()
    if not approved_text or text != approved_text:
        parser.error("TTS input must exactly match the approved variant script_text in the campaign JSON.")
    if not text:
        parser.error("Approved script text is empty.")

    try:
        import numpy as np
        import soundfile as sf
        from kokoro import KPipeline
        from importlib.metadata import version as package_version
    except ImportError as exc:
        sys.exit(f"Missing TTS dependency: {exc}. Install requirements-audio.txt")

    # Explicit CPU selection keeps GitHub-hosted runners predictable.
    pipeline = KPipeline(lang_code=lang_code, device="cpu")
    chunks = []
    for _graphemes, _phonemes, audio in pipeline(text, voice=args.voice, speed=args.speed):
        if audio is not None:
            chunks.append(audio.detach().cpu().numpy())
    if not chunks:
        sys.exit("Kokoro returned no audio.")
    waveform = np.concatenate(chunks).astype(np.float32)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(args.output), waveform, 24000, subtype="PCM_16")
    duration = len(waveform) / 24000
    metadata = {
        "engine": "kokoro", "engine_version": package_version("kokoro"), "variant_id": args.variant,
        "script_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "language": language, "voice_id": args.voice,
        "speed": args.speed, "device": "cpu", "sample_rate": 24000,
        "duration_seconds": round(duration, 3), "output": str(args.output),
    }
    metadata_path = args.metadata or args.output.with_suffix(".json")
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    print(json.dumps(metadata, indent=2))

if __name__ == "__main__":
    main()
