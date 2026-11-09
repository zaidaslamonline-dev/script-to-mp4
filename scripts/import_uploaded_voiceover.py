#!/usr/bin/env python3
"""Import user-supplied narration audio; never invoke TTS in this path."""
import argparse, hashlib, json, subprocess, sys
from pathlib import Path

EXTS = (".wav", ".mp3", ".m4a", ".aac", ".flac", ".ogg")

def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def probe(path):
    raw = subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", str(path)
    ], text=True).strip()
    duration = float(raw)
    if duration <= 0:
        raise SystemExit(f"Invalid or empty audio: {path}")
    return duration

def normalize(source, target):
    subprocess.run([
        "ffmpeg", "-y", "-i", str(source), "-vn", "-ac", "1",
        "-ar", "48000", "-c:a", "pcm_s16le", str(target)
    ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    return probe(target)

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--campaign", type=Path, required=True)
    p.add_argument("--voiceover-dir", type=Path, required=True)
    args = p.parse_args()
    campaign = json.loads(args.campaign.read_text(encoding="utf-8"))
    if campaign.get("script", {}).get("approved_by_user") is not True:
        raise SystemExit("BLOCKED: script approval is required before importing voiceover.")
    variants = campaign.get("variants", [])
    if len(variants) != 2 or any(v.get("approved") is not True or not str(v.get("script_text", "")).strip() for v in variants):
        raise SystemExit("BLOCKED: exactly two non-empty, script-approved variants are required.")
    folder = args.voiceover_dir
    folder.mkdir(parents=True, exist_ok=True)
    master = [folder / ("uploaded-master" + ext) for ext in EXTS]
    master = [x for x in master if x.is_file()]
    if len(master) > 1:
        raise SystemExit("Ambiguous upload: keep exactly one uploaded-master audio file.")
    sources = {}
    if master:
        texts = {str(v["script_text"]).strip() for v in variants}
        if len(texts) != 1:
            raise SystemExit("A shared uploaded-master is allowed only when Variant A and B have identical spoken scripts. Upload variant-A and variant-B files instead.")
        sources = {"A": master[0], "B": master[0]}
    else:
        for key in ("A", "B"):
            found = [folder / f"variant-{key}{ext}" for ext in EXTS]
            found = [x for x in found if x.is_file()]
            if len(found) != 1:
                raise SystemExit(f"Provide exactly one variant-{key} audio file ({', '.join(EXTS)}), or one uploaded-master file.")
            sources[key] = found[0]
    for item in variants:
        key = str(item["variant_id"]).upper()
        source = sources[key]
        target = folder / f"variant-{key}.wav"
        duration = normalize(source, target)
        text = str(item["script_text"]).strip()
        metadata = {
            "source": "user_uploaded_external_voiceover",
            "engine": "external",
            "provider": "user_supplied",
            "voice_profile": "single_voice_all_characters",
            "variant_id": key,
            "script_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
            "script_match_status": "requires_user_listen_and_approval",
            "source_file": source.name,
            "source_sha256": sha256(source),
            "normalized_sha256": sha256(target),
            "duration_seconds": round(duration, 3),
            "sample_rate": 48000,
            "channels": 1,
            "format": "wav_pcm_s16le",
        }
        target.with_suffix(".json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
        print(json.dumps(metadata))
    print("Imported and normalized uploaded voiceover(s). Voiceover approval is still required.")

if __name__ == "__main__":
    main()
