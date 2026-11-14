#!/usr/bin/env python3
"""Generate a multi-character FixReach voiceover with Edge TTS.

Input text remains the canonical script. Optional [delivery] and [pause] cues
are removed from speech and translated into safe prosody/pause controls.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import re
import shutil
import subprocess
import wave
from pathlib import Path

import edge_tts

PAUSE_MS = {"pause": 650, "slight pause": 320}
DELIVERY = {
    "frustrated": ("+3%", "+1Hz"),
    "disappointed": ("-4%", "-2Hz"),
    "playful": ("+7%", "+2Hz"),
    "teasing": ("+5%", "+1Hz"),
    "annoyed": ("-2%", "-1Hz"),
    "confident": ("+1%", "+0Hz"),
    "emphasis": ("-2%", "+1Hz"),
    "confused": ("+3%", "+2Hz"),
    "explaining": ("-3%", "+0Hz"),
    "upbeat": ("+6%", "+1Hz"),
    "clear": ("-5%", "+0Hz"),
    "deliberate": ("-7%", "-1Hz"),
    "reassuring": ("-4%", "-1Hz"),
    "realization": ("+5%", "+2Hz"),
    "excited": ("+8%", "+2Hz"),
    "affirming": ("+1%", "+0Hz"),
    "energetic": ("+8%", "+1Hz"),
    "direct": ("-1%", "+0Hz"),
    "enthusiastic": ("+7%", "+1Hz"),
    "cheerful": ("+5%", "+1Hz"),
    "slight pause": ("+0%", "+0Hz"),
}

def run(command: list[str]) -> None:
    subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def make_silence(path: Path, milliseconds: int) -> None:
    frames = int(48000 * milliseconds / 1000)
    with wave.open(str(path), "wb") as out:
        out.setnchannels(2)
        out.setsampwidth(2)
        out.setframerate(48000)
        out.writeframes(b"\x00\x00\x00\x00" * frames)

def parse_segment(segment: dict, profile: dict) -> list[tuple[str, str, str]]:
    """Return ordered ('text'|'pause', value, rate/pitch payload) items.

    All bracketed stage directions are consumed, including mid-sentence changes.
    """
    raw = segment.get("tts_text", segment["text"]).strip()
    current_rate = profile.get("rate", "+0%")
    current_pitch = profile.get("pitch", "+0Hz")
    items: list[tuple[str, str, str]] = []

    for part in re.split(r"(\[[^\]]+\])", raw):
        if not part or not part.strip():
            continue
        if part.startswith("[") and part.endswith("]"):
            cue = part[1:-1].strip().lower()
            if cue in PAUSE_MS:
                items.append(("pause", str(PAUSE_MS[cue]), ""))
                continue
            for label in (piece.strip() for piece in cue.split(",")):
                if label in DELIVERY:
                    current_rate, current_pitch = DELIVERY[label]
            # Delivery tags are instructions, never spoken words.
            continue
        items.append(("text", part.strip(), f"{current_rate}|{current_pitch}"))

    return items

async def synthesize(text: str, voice: str, rate: str, pitch: str, target: Path) -> None:
    communicate = edge_tts.Communicate(
        text=text,
        voice=voice,
        rate=rate,
        pitch=pitch,
        volume="+0%",
    )
    await communicate.save(str(target))

async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--script", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--voice-profiles", type=Path, default=Path("config/fixreach_voice_profiles.json"))
    args = parser.parse_args()

    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        raise SystemExit("ffmpeg and ffprobe are required.")
    data = json.loads(args.script.read_text(encoding="utf-8"))
    if args.voice_profiles.is_file():
        profiles = json.loads(args.voice_profiles.read_text(encoding="utf-8"))
    else:
        profiles = data.get("voice_profiles", {})
    segments = data["segments"]
    if not segments:
        raise SystemExit("The script contains no dialogue segments.")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    work = args.output_dir / "_work"
    work.mkdir(exist_ok=True)
    ordered_wavs: list[Path] = []
    manifest_segments = []
    chunk_number = 0

    for turn_number, segment in enumerate(segments, start=1):
        speaker = segment["speaker"]
        if speaker not in profiles:
            raise SystemExit(f"No stable voice profile configured for speaker: {speaker}")
        profile = profiles[speaker]
        voice = profile["voice"]
        items = parse_segment(segment, profile)
        spoken_parts = 0
        for kind, value, prosody in items:
            if kind == "pause":
                silence = work / f"chunk_{chunk_number:04d}.wav"
                make_silence(silence, int(value))
                ordered_wavs.append(silence)
                chunk_number += 1
                continue

            rate, pitch = prosody.split("|", 1)
            spoken = value
            mp3_path = work / f"turn_{turn_number:03d}_part_{spoken_parts:02d}.mp3"
            wav_path = work / f"chunk_{chunk_number:04d}.wav"
            await synthesize(spoken, voice, rate, pitch, mp3_path)
            run([
                "ffmpeg", "-y", "-v", "error", "-i", str(mp3_path),
                "-ar", "48000", "-ac", "2", "-c:a", "pcm_s16le", str(wav_path)
            ])
            ordered_wavs.append(wav_path)
            chunk_number += 1
            spoken_parts += 1

        manifest_segments.append({
            "turn": turn_number,
            "speaker": speaker,
            "voice": voice,
            "delivery_cues": re.findall(r"\[([^\]]+)\]", segment["text"]),
            "text": segment["text"],
        })

        # Natural turn-taking pause, except after the final turn.
        if turn_number < len(segments):
            silence = work / f"chunk_{chunk_number:04d}.wav"
            make_silence(silence, int(data.get("turn_pause_ms", 180)))
            ordered_wavs.append(silence)
            chunk_number += 1

    concat_file = work / "concat.txt"
    concat_file.write_text(
        "".join(f"file '{p.resolve().as_posix()}'\n" for p in ordered_wavs),
        encoding="utf-8",
    )
    raw_wav = work / "voiceover_raw.wav"
    run([
        "ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0",
        "-i", str(concat_file), "-c:a", "pcm_s16le", "-ar", "48000",
        "-ac", "2", str(raw_wav),
    ])

    wav_out = args.output_dir / "voiceover.wav"
    mp3_out = args.output_dir / "voiceover.mp3"
    run([
        "ffmpeg", "-y", "-v", "error", "-i", str(raw_wav),
        "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",
        "-ar", "48000", "-ac", "2", "-c:a", "pcm_s16le", str(wav_out),
    ])
    run([
        "ffmpeg", "-y", "-v", "error", "-i", str(wav_out),
        "-codec:a", "libmp3lame", "-b:a", "192k", str(mp3_out),
    ])
    duration = float(subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", str(wav_out)
    ], text=True).strip())

    manifest = {
        "campaign_id": data["campaign_id"],
        "title": data["title"],
        "engine": "Microsoft Edge TTS via edge-tts",
        "language": data.get("language", "hi-IN"),
        "voice_profiles": profiles,
        "duration_seconds": round(duration, 3),
        "sample_rate_hz": 48000,
        "channels": 2,
        "segments": manifest_segments,
        "notes": [
            "Speaker voice IDs are stored in the script for consistent reuse.",
            "Delivery tags are approximated with rate and pitch; Edge TTS does not provide native emotion acting for these voices.",
            "Listen to the generated audio before approving it for video production."
        ],
    }
    (args.output_dir / "voiceover_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "campaign_id": data["campaign_id"],
        "duration_seconds": round(duration, 3),
        "wav": str(wav_out),
        "mp3": str(mp3_out),
    }, ensure_ascii=False))

if __name__ == "__main__":
    asyncio.run(main())
