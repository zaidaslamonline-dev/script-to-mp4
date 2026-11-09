#!/usr/bin/env python3
"""Import one user-supplied narration file; never invoke TTS."""
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
    raw = subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(path)], text=True).strip()
    duration = float(raw)
    if duration <= 0:
        raise SystemExit(f"Invalid or empty audio: {path}")
    return duration

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--campaign", type=Path, required=True)
    p.add_argument("--voiceover-dir", type=Path, required=True)
    args = p.parse_args()
    campaign = json.loads(args.campaign.read_text(encoding="utf-8"))
    if campaign.get("script", {}).get("approved_by_user") is not True:
        raise SystemExit("BLOCKED: script approval is required.")
    variants = campaign.get("variants", [])
    if len(variants) != 1 or variants[0].get("approved") is not True or not str(variants[0].get("script_text", "")).strip():
        raise SystemExit("BLOCKED: this single-video import requires exactly one non-empty script-approved variant.")
    folder = args.voiceover_dir
    folder.mkdir(parents=True, exist_ok=True)
    names = ["uploaded-master" + ext for ext in EXTS] + ["variant-A" + ext for ext in EXTS]
    found = [folder / name for name in names if (folder / name).is_file()]
    if len(found) != 1:
        raise SystemExit("Provide exactly one audio file named uploaded-master.<ext> or variant-A.<ext>.")
    source = found[0]
    target = folder / "variant-A.wav"
    subprocess.run(["ffmpeg", "-y", "-i", str(source), "-vn", "-ac", "1", "-ar", "48000", "-c:a", "pcm_s16le", str(target)], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    duration = probe(target)
    text = str(variants[0]["script_text"]).strip()
    metadata = {
        "source": "user_uploaded_external_voiceover", "engine": "external", "provider": "user_supplied",
        "voice_profile": "single_voice_all_characters", "variant_id": "A",
        "script_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "script_match_status": "requires_user_listen_and_approval", "source_file": source.name,
        "source_sha256": sha256(source), "normalized_sha256": sha256(target),
        "duration_seconds": round(duration, 3), "sample_rate": 48000, "channels": 1, "format": "wav_pcm_s16le"
    }
    target.with_suffix(".json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    print(json.dumps(metadata, indent=2))
    print("Imported one complete narration. Voiceover approval is still required.")

if __name__ == "__main__":
    main()
