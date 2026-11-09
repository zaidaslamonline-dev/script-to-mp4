#!/usr/bin/env python3
"""Build a Hyperframes HTML storyboard from approved campaign data and a reviewed scene plan."""
import argparse
import html
import json
import shutil
import sys
from pathlib import Path

def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--campaign", type=Path, required=True)
    p.add_argument("--storyboard", type=Path, required=True)
    p.add_argument("--voiceover", type=Path, required=True)
    p.add_argument("--output-dir", type=Path, required=True)
    args = p.parse_args()

    campaign = load_json(args.campaign)
    board = load_json(args.storyboard)
    if not campaign.get("script", {}).get("approved_by_user"):
        sys.exit("BLOCKED: script approval is required before storyboard composition.")
    if not campaign.get("production", {}).get("voiceover_approved"):
        sys.exit("BLOCKED: voiceover approval is required before storyboard composition.")
    if not args.voiceover.is_file():
        sys.exit(f"Missing voiceover: {args.voiceover}")

    variant_id = str(board.get("variant_id", "")).upper()
    approved_variants = {str(v.get("variant_id", "")).upper(): v for v in campaign.get("variants", [])}
    if variant_id not in approved_variants or not approved_variants[variant_id].get("approved"):
        sys.exit(f"BLOCKED: variant {variant_id or '(missing)'} is not script-approved.")
    scenes = board.get("scenes")
    duration = float(board.get("duration_seconds", 0))
    if not isinstance(scenes, list) or not scenes or duration <= 0:
        p.error("Storyboard needs duration_seconds > 0 and a non-empty scenes array.")

    normalized = []
    for index, scene in enumerate(scenes):
        text = str(scene.get("text", "")).strip()
        start = float(scene.get("start", -1))
        end = float(scene.get("end", -1))
        if not text or start < 0 or end <= start or end > duration + 0.05:
            p.error(f"Invalid scene at index {index}: require text and 0 <= start < end <= duration.")
        normalized.append((index, start, end - start, text))

    args.output_dir.mkdir(parents=True, exist_ok=True)
    assets = args.output_dir / "assets"
    assets.mkdir(exist_ok=True)
    shutil.copy2(args.voiceover, assets / "voiceover.wav")

    brand_path = Path("clients") / campaign["client_id"] / "brand.json"
    brand = load_json(brand_path) if brand_path.is_file() else {}
    colors = brand.get("brand", {}).get("colors", {})
    primary = colors.get("primary", "#080808")
    accent = colors.get("accent", "#39FF14")
    safe_primary = primary if isinstance(primary, str) and primary.startswith("#") else "#080808"
    safe_accent = accent if isinstance(accent, str) and accent.startswith("#") else "#39FF14"

    clips = []
    for index, start, length, text in normalized:
        clips.append(
            f'<div id="scene-{index+1}" class="clip scene" data-start="{start:.3f}" '
            f'data-duration="{length:.3f}" data-track-index="{index+1}">'
            f'<span>{html.escape(text)}</span></div>'
        )
    markup = "\n".join(clips)
    document = f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(campaign.get("campaign_id", "campaign"))} — Variant {html.escape(variant_id)}</title>
<style>
*{{box-sizing:border-box}}html,body{{margin:0;width:100%;height:100%;background:{safe_primary};color:#fff;font-family:Arial,sans-serif}}
#root{{position:relative;width:1080px;height:1920px;overflow:hidden;background:{safe_primary}}}
.scene{{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;padding:100px;text-align:center}}
.scene span{{font-size:96px;line-height:1.02;font-weight:900;letter-spacing:-3px;text-transform:uppercase;text-wrap:balance;text-shadow:0 8px 35px #000}}
.scene:nth-of-type(2n) span{{color:{safe_accent}}}
</style></head><body>
<div id="root" data-composition-id="root" data-width="1080" data-height="1920" data-duration="{duration:.3f}">
<audio id="voiceover" data-start="0" data-duration="{duration:.3f}" data-track-index="0" src="./assets/voiceover.wav"></audio>
{markup}
</div></body></html>'''
    (args.output_dir / "index.html").write_text(document, encoding="utf-8")
    manifest = {
        "campaign_id": campaign.get("campaign_id"), "variant_id": variant_id,
        "duration_seconds": duration, "voiceover": "assets/voiceover.wav",
        "scene_count": len(normalized), "status": "storyboard_draft",
        "note": "HTML preview only; rendering remains blocked until storyboard and render approvals are recorded."
    }
    (args.output_dir / "composition-manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))

if __name__ == "__main__":
    main()
