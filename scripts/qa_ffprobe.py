#!/usr/bin/env python3
"""Basic MP4 structural QA using the ffprobe executable."""
import argparse, json, subprocess, sys
from fractions import Fraction
from pathlib import Path

def main():
    p = argparse.ArgumentParser()
    p.add_argument("video", type=Path)
    p.add_argument("--width", type=int, default=1080)
    p.add_argument("--height", type=int, default=1920)
    p.add_argument("--fps", type=int, default=30)
    args = p.parse_args()
    if not args.video.is_file():
        sys.exit(f"Missing video: {args.video}")
    raw = subprocess.check_output([
        "ffprobe", "-v", "error", "-show_streams", "-show_format",
        "-of", "json", str(args.video)
    ], text=True)
    info = json.loads(raw)
    streams = info.get("streams", [])
    video = next((s for s in streams if s.get("codec_type") == "video"), None)
    audio = next((s for s in streams if s.get("codec_type") == "audio"), None)
    errors = []
    if not video: errors.append("No video stream")
    else:
        if video.get("width") != args.width or video.get("height") != args.height:
            errors.append(f"Wrong dimensions: {video.get('width')}x{video.get('height')}")
        rate = Fraction(video.get("avg_frame_rate", "0/1"))
        if rate != args.fps: errors.append(f"Wrong FPS: {rate}")
    if not audio: errors.append("No audio stream")
    duration = float(info.get("format", {}).get("duration", 0))
    if duration <= 0: errors.append("Invalid duration")
    if errors:
        print("\n".join("FAIL: " + e for e in errors))
        sys.exit(1)
    print(json.dumps({"status":"passed","file":str(args.video),"duration_seconds":duration,
                      "width":video["width"],"height":video["height"],"fps":args.fps,
                      "audio_codec":audio.get("codec_name")}, indent=2))

if __name__ == "__main__": main()
