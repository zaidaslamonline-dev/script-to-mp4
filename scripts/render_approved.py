#!/usr/bin/env python3
"""Render one approved Hyperframes video only after every approval gate is true."""
import argparse, json, subprocess, sys
from pathlib import Path

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--campaign", type=Path, required=True)
    p.add_argument("--runs-dir", type=Path, required=True)
    p.add_argument("--output-dir", type=Path, required=True)
    args = p.parse_args()
    campaign = json.loads(args.campaign.read_text(encoding="utf-8"))
    production = campaign.get("production", {})
    if campaign.get("script", {}).get("approved_by_user") is not True or not production.get("voiceover_approved") or not production.get("storyboards_approved") or not production.get("render_approved"):
        sys.exit("BLOCKED: script, voiceover, storyboard, and final render approvals must all be true.")
    variants = campaign.get("variants", [])
    if len(variants) != 1 or variants[0].get("approved") is not True:
        sys.exit("BLOCKED: exactly one script-approved video variant is required.")
    variant = variants[0]
    if variant.get("storyboard_status") != "approved":
        sys.exit("BLOCKED: the single video storyboard must be approved.")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    variant_id = str(variant["variant_id"]).upper()
    variant_runs = args.runs_dir / f"variant-{variant_id}"
    source = variant_runs / "index.html"
    if not source.is_file():
        campaign_root = args.campaign.parent
        storyboard = campaign_root / "storyboards" / f"variant-{variant_id}.json"
        voiceover = campaign_root / "voiceovers" / f"variant-{variant_id}.wav"
        if not storyboard.is_file() or not voiceover.is_file():
            sys.exit("Missing approved storyboard or normalized voiceover.")
        subprocess.run([sys.executable, str(Path(__file__).with_name("build_composition.py")), "--campaign", str(args.campaign.resolve()), "--storyboard", str(storyboard.resolve()), "--voiceover", str(voiceover.resolve()), "--output-dir", str(variant_runs.resolve())], check=True)
        source = variant_runs / "index.html"
    if not source.is_file():
        sys.exit(f"Composition build did not create: {source}")
    out = args.output_dir / f"{campaign['campaign_id']}.mp4"
    subprocess.run(["npx", "--yes", "hyperframes", "render", "--composition", str(source.resolve()), "--output", str(out.resolve()), "--fps", "30", "--quality", "standard"], check=True, cwd=source.parent)
    subprocess.run([sys.executable, str(Path(__file__).with_name("qa_ffprobe.py")), str(out), "--width", "1080", "--height", "1920", "--fps", "30"], check=True)
    print(f"Rendered and structurally validated one video: {out}")

if __name__ == "__main__":
    main()
