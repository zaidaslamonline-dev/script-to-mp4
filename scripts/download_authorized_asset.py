#!/usr/bin/env python3
"""Download a pre-approved asset from the asset manifest using yt-dlp.

This intentionally refuses arbitrary URLs. An asset must be recorded in the
manifest and explicitly marked as downloadable and commercially cleared.
"""
import argparse
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "assets" / "asset-manifest.json"

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--asset-id", required=True)
    parser.add_argument("--rights-confirmed", action="store_true",
                        help="Confirm you own the asset or have permission to download and use it commercially.")
    args = parser.parse_args()
    if not args.rights_confirmed:
        raise SystemExit("Refusing download: pass --rights-confirmed after verifying rights and source terms.")
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    asset = next((a for a in data.get("assets", []) if a.get("asset_id") == args.asset_id), None)
    if not asset:
        raise SystemExit(f"Asset ID not found in {MANIFEST}")
    if not asset.get("download_permitted") or not asset.get("commercial_use_approved"):
        raise SystemExit("Refusing download: manifest must explicitly approve download and commercial use.")
    if not asset.get("source_url") or not asset.get("license_id") or not asset.get("license_url"):
        raise SystemExit("Refusing download: source URL and license metadata are required.")
    output_dir = ROOT / "assets" / "downloads" / args.asset_id
    output_dir.mkdir(parents=True, exist_ok=True)
    command = [
        "yt-dlp", "--no-playlist", "--restrict-filenames",
        "--write-info-json", "--no-overwrites",
        "-o", str(output_dir / "%(id)s.%(ext)s"),
        asset["source_url"],
    ]
    subprocess.run(command, check=True)
    print(f"Downloaded approved asset {args.asset_id} to {output_dir}")

if __name__ == "__main__":
    main()
