#!/usr/bin/env python3
"""Render both approved Hyperframes variants only after every approval gate is true."""
import argparse
import json
import subprocess
import sys
from pathlib import Path

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--campaign", type=Path, required=True)
    p.add_argument("--runs-dir", type=Path, required=True)
    p.add_argument("--output-dir", type=Path, required=True)
    args = p.parse_args()
    campaign = json.loads(args.campaign.read_text(encoding="utf-8"))
    script_ok = campaign.get("script", {}).get("approved_by_user") is True
    production = campaign.get("production", {})
    if not script_ok or not production.get("voiceover_approved") or not production.get("storyboards_approved") or not production.get("render_approved"):
        sys.exit("BLOCKED: script, voiceover, storyboard, and final render approvals must all be true.")

    variants = campaign.get("variants", [])
    if len(variants) != 2 or any(v.get("approved") is not True for v in variants):
        sys.exit("BLOCKED: exactly two script-approved variants are required.")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for variant in variants:
        variant_id = str(variant["variant_id"]).upper()
        source = args.runs_dir / f"variant-{variant_id}" / "index.html"
        if not source.is_file():
            sys.exit(f"Missing approved composition: {source}")
        out = args.output_dir / f"{campaign['campaign_id']}-variant-{variant_id}.mp4"
        subprocess.run(
            ["npx", "--yes", "hyperframes", "render", "--composition", str(source.resolve()),
             "--output", str(out.resolve()), "--fps", "30", "--quality", "standard"],
            check=True,
        )
        subprocess.run(
            [sys.executable, "scripts/qa_ffprobe.py", str(out), "--width", "1080", "--height", "1920", "--fps", "30"],
            check=True,
        )
    print(f"Rendered and structurally validated {len(variants)} variants in {args.output_dir}")

if __name__ == "__main__":
    main()
