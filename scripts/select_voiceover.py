#!/usr/bin/env python3
"""Select immutable supplied WAV first; TTS is an explicit fallback only."""
import hashlib, json, os, shutil, subprocess
from pathlib import Path

SOURCE = Path("content/voiceover.wav")
WORK = Path("production/voiceover")
WORK.mkdir(parents=True, exist_ok=True)

def probe(path):
    data = json.loads(subprocess.check_output([
        "ffprobe", "-v", "error", "-select_streams", "a:0",
        "-show_entries", "stream=codec_name,sample_rate,channels",
        "-show_entries", "format=duration,size", "-of", "json", str(path)
    ], text=True))
    streams, fmt = data.get("streams", []), data.get("format", {})
    if not streams or int(fmt.get("size", 0)) <= 44:
        raise SystemExit("Audio is empty, unreadable, or has no audio stream.")
    duration, rate, channels = float(fmt.get("duration", 0)), int(streams[0].get("sample_rate", 0)), int(streams[0].get("channels", 0))
    if duration <= 0 or rate <= 0 or channels <= 0:
        raise SystemExit("FFprobe reported invalid duration/sample rate/channel count.")
    return {"duration_seconds": round(duration, 3), "sample_rate": rate, "channels": channels,
            "codec": streams[0].get("codec_name"), "size_bytes": int(fmt.get("size", 0))}

if SOURCE.is_file():
    selected, origin = SOURCE, "supplied"
    shutil.copy2(SOURCE, WORK / "voiceover-original.wav")
else:
    command = os.environ.get("TTS_FALLBACK_COMMAND", "").strip()
    if not command:
        raise SystemExit("content/voiceover.wav is absent and TTS_FALLBACK_COMMAND is not configured. No speech was generated.")
    selected, origin = WORK / "voiceover-generated.wav", "generated"
    env = os.environ.copy()
    env["VOICEOVER_OUTPUT"] = str(selected.resolve())
    subprocess.run(["bash", "-lc", command], env=env, check=True)
    if not selected.is_file():
        raise SystemExit("TTS fallback command completed without creating VOICEOVER_OUTPUT.")

if selected.suffix.lower() != ".wav":
    raise SystemExit("Selected voiceover must be a WAV file.")
metadata = probe(selected)
metadata.update({"audio_source": origin, "source_path": str(SOURCE if origin == "supplied" else selected),
                 "sha256": hashlib.sha256(selected.read_bytes()).hexdigest()})
normalized = WORK / "voiceover-production.wav"
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(selected), "-map", "0:a:0",
                "-ar", "48000", "-ac", "2", "-c:a", "pcm_s16le", str(normalized)], check=True)
metadata["production_copy"] = str(normalized)
metadata["production_probe"] = probe(normalized)
Path("production/voiceover-report.json").write_text(json.dumps(metadata, indent=2))
print(json.dumps(metadata, indent=2))
