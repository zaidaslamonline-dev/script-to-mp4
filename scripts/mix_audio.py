#!/usr/bin/env python3
"""Mix approved narration with a commercially cleared music bed using voice-triggered ducking."""
import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--voiceover", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--bgm", type=Path)
    p.add_argument("--asset-id")
    p.add_argument("--manifest", type=Path, default=Path("assets/asset-manifest.json"))
    p.add_argument("--duck-db", type=float, default=-18.0)
    args = p.parse_args()
    if not args.voiceover.is_file():
        p.error(f"Voiceover not found: {args.voiceover}")
    args.output.parent.mkdir(parents=True, exist_ok=True)

    if args.bgm:
        if not args.asset_id:
            p.error("--asset-id is required when using background music.")
        if not args.bgm.is_file() or not args.manifest.is_file():
            p.error("BGM file and asset manifest must both exist.")
        manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
        asset = next((a for a in manifest.get("assets", []) if a.get("asset_id") == args.asset_id), None)
        if not asset:
            p.error(f"Asset {args.asset_id} is not registered in the asset manifest.")
        required = ("rights_verified", "commercial_use_allowed", "license", "source_url", "sha256")
        if not all(asset.get(k) for k in required) or asset.get("rights_verified") is not True or asset.get("commercial_use_allowed") is not True:
            p.error("BGM asset lacks verified commercial-use rights and provenance.")
        digest = hashlib.sha256(args.bgm.read_bytes()).hexdigest()
        if digest.lower() != str(asset["sha256"]).lower():
            p.error("BGM file hash does not match the approved asset manifest entry.")
        gain = 10 ** (args.duck_db / 20)
        filters = (
            f"[1:a]volume={gain:.6f}[music];"
            "[music][0:a]sidechaincompress=threshold=0.03:ratio=8:attack=20:release=450[ducked];"
            "[0:a][ducked]amix=inputs=2:duration=first:dropout_transition=2,"
            "alimiter=limit=0.95[out]"
        )
        command = [
            "ffmpeg", "-y", "-i", str(args.voiceover), "-stream_loop", "-1", "-i", str(args.bgm),
            "-filter_complex", filters, "-map", "[out]", "-ar", "48000", "-ac", "2",
            "-c:a", "pcm_s16le", str(args.output),
        ]
    else:
        command = ["ffmpeg", "-y", "-i", str(args.voiceover), "-map", "0:a:0",
                   "-ar", "48000", "-ac", "2", "-c:a", "pcm_s16le", str(args.output)]
    subprocess.run(command, check=True)
    print(json.dumps({"output": str(args.output), "bgm_used": bool(args.bgm),
                      "ducking_db": args.duck_db if args.bgm else None}, indent=2))

if __name__ == "__main__":
    main()
