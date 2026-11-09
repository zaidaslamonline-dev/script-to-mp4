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
    if any(v.get("storyboard_status") != "approved" for v in variants):
        sys.exit("BLOCKED: each variant storyboard must be individually approved.")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for variant in variants:
        variant_id = str(variant["variant_id"]).upper()
        variant_runs = args.runs_dir / f"variant-{variant_id}"
        source = variant_runs / "index.html"
        if not source.is_file():
            # Rebuild from committed campaign inputs on the runner. This keeps
            # generated run directories out of Git while making render reproducible.
            campaign_root = args.campaign.parent
            storyboard = campaign_root / "storyboards" / f"variant-{variant_id}.json"
            voiceover = campaign_root / "voiceovers" / f"variant-{variant_id}.wav"
            if not storyboard.is_file():
                sys.exit(f"Missing approved storyboard source: {storyboard}")
            if not voiceover.is_file():
                sys.exit(f"Missing approved voiceover file: {voiceover}")
            subprocess.run(
                [sys.executable, str(Path(__file__).with_name("build_composition.py")),
                 "--campaign", str(args.campaign.resolve()),
                 "--storyboard", str(storyboard.resolve()),
                 "--voiceover", str(voiceover.resolve()),
                 "--output-dir", str(variant_runs.resolve())],
                check=True,
            )
            source = variant_runs / "index.html"
        if not source.is_file():
            sys.exit(f"Composition build did not create: {source}")
        out = args.output_dir / f"{campaign['campaign_id']}-variant-{variant_id}.mp4"
        subprocess.run(
            ["npx", "--yes", "hyperframes", "render", "--composition", str(source.resolve()),
             "--output", str(out.resolve()), "--fps", "30", "--quality", "standard"],
            check=True, cwd=source.parent,
        )
        subprocess.run(
            [sys.executable, str(Path(__file__).with_name("qa_ffprobe.py")), str(out), "--width", "1080", "--height", "1920", "--fps", "30"],
            check=True,
        )
    print(f"Rendered and structurally validated {len(variants)} variants in {args.output_dir}")

if __name__ == "__main__":
    main()
