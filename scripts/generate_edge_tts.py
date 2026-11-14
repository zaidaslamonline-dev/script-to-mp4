#!/usr/bin/env python3
"""Generate one continuous, two-character FixReach voiceover in one Gemini TTS request."""
from __future__ import annotations
import argparse, base64, json, os, re, shutil, subprocess, urllib.error, urllib.request
from pathlib import Path

MODEL = "gemini-3.1-flash-tts-preview"
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent"

def run(command):
    subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--script", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--voice-profiles", type=Path, default=Path("config/fixreach_voice_profiles.json"))
    args = parser.parse_args()
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        raise SystemExit("ffmpeg and ffprobe are required.")
    data = json.loads(args.script.read_text(encoding="utf-8"))
    profiles = json.loads(args.voice_profiles.read_text(encoding="utf-8")) if args.voice_profiles.is_file() else data.get("voice_profiles", {})
    segments = data.get("segments", [])
    if not segments:
        raise SystemExit("The script contains no dialogue segments.")
    if len(profiles) != 2:
        raise SystemExit(f"Gemini multi-speaker TTS requires exactly 2 configured speakers; found {len(profiles)}.")

    lines, manifest_segments = [], []
    for index, segment in enumerate(segments, start=1):
        speaker = segment["speaker"]
        if speaker not in profiles:
            raise SystemExit(f"No stable Gemini voice profile configured for speaker: {speaker}")
        spoken = segment.get("tts_text", segment["text"]).strip()
        spoken = spoken.replace("[slight pause]", "[short pause]").replace("[pause]", "[long pause]")
        lines.append(f"{speaker}: {spoken}")
        manifest_segments.append({
            "turn": index, "speaker": speaker, "voice": profiles[speaker]["voice"],
            "delivery_cues": re.findall(r"\[([^\]]+)\]", segment["text"]),
            "text": segment["text"],
        })

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise SystemExit("GEMINI_API_KEY is missing. Add it under GitHub Actions repository secrets.")
    speaker_configs = [{
        "speaker": name,
        "voiceConfig": {"prebuiltVoiceConfig": {"voiceName": profile["voice"]}}
    } for name, profile in profiles.items()]

    prompt = (
        "Perform the following verbatim conversation in natural Indian Hindi/Hinglish. "
        "The dialogue is written in Roman Hinglish: preserve the exact words and do not translate, "
        "summarize, add, or omit dialogue. Speaker labels identify who speaks and must not be read aloud. "
        "Square-bracketed audio directions are performance cues, not spoken words. "
        "Make the exchange sound like two real people talking naturally, with clear turn-taking. "
        "Sid is a youthful, confident, quick-witted male mentor with an upbeat, friendly delivery. "
        "Lala Bhai is a mature, warm, grounded male repair-business owner; expressive, slightly "
        "exasperated at first, then increasingly relieved and enthusiastic. Keep both voices distinct.\n\n"
        + "\n".join(lines)
    )
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "responseModalities": ["AUDIO"],
            "speechConfig": {"multiSpeakerVoiceConfig": {"speakerVoiceConfigs": speaker_configs}}
        }
    }
    req = urllib.request.Request(
        API_URL, data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json", "x-goog-api-key": api_key}, method="POST"
    )
    # Exactly one Gemini API request for the entire script; no per-line synthesis or retries.
    try:
        with urllib.request.urlopen(req, timeout=240) as response:
            result = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Gemini TTS API returned HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Could not reach Gemini TTS API: {exc.reason}") from exc

    parts = result.get("candidates", [{}])[0].get("content", {}).get("parts", [])
    audio_parts = [p["inlineData"] for p in parts if p.get("inlineData", {}).get("data")]
    if not audio_parts:
        raise RuntimeError("Gemini returned no audio data: " + json.dumps(result.get("promptFeedback", {})))
    audio = b"".join(base64.b64decode(p["data"]) for p in audio_parts)
    mime = audio_parts[0].get("mimeType", "audio/pcm;rate=24000").lower()
    if not mime.startswith("audio/pcm"):
        raise RuntimeError(f"Unexpected Gemini audio MIME type: {mime}")
    rate = 24000
    if "rate=" in mime:
        try: rate = int(mime.split("rate=", 1)[1].split(";", 1)[0])
        except ValueError: pass

    args.output_dir.mkdir(parents=True, exist_ok=True)
    work = args.output_dir / "_work"
    work.mkdir(exist_ok=True)
    raw = work / "gemini_output.pcm"
    raw.write_bytes(audio)
    raw_wav = work / "voiceover_raw.wav"
    run(["ffmpeg", "-y", "-v", "error", "-f", "s16le", "-ar", str(rate), "-ac", "1", "-i", str(raw), "-c:a", "pcm_s16le", str(raw_wav)])
    wav_out, mp3_out = args.output_dir / "voiceover.wav", args.output_dir / "voiceover.mp3"
    run(["ffmpeg", "-y", "-v", "error", "-i", str(raw_wav), "-af", "loudnorm=I=-16:TP=-1.5:LRA=11", "-ar", "48000", "-ac", "2", "-c:a", "pcm_s16le", str(wav_out)])
    run(["ffmpeg", "-y", "-v", "error", "-i", str(wav_out), "-codec:a", "libmp3lame", "-b:a", "192k", str(mp3_out)])
    duration = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(wav_out)], text=True).strip())
    manifest = {
        "campaign_id": data["campaign_id"], "title": data["title"],
        "engine": "Google Gemini 3.1 Flash TTS", "model": MODEL, "api_requests": 1,
        "language": data.get("language", "hi-IN"), "voice_profiles": profiles,
        "duration_seconds": round(duration, 3), "sample_rate_hz": 48000, "channels": 2,
        "segments": manifest_segments,
        "notes": [
            "The complete dialogue was synthesized in one Gemini multi-speaker API request.",
            "Speaker voice IDs are stored in the shared profile file and reused for future scripts.",
            "Square-bracketed delivery and pause cues are passed as acting instructions, not dialogue.",
            "Listen to the generated audio before approving it for video production."
        ]
    }
    (args.output_dir / "voiceover_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"campaign_id": data["campaign_id"], "model": MODEL, "api_requests": 1, "duration_seconds": round(duration, 3), "wav": str(wav_out), "mp3": str(mp3_out)}))

if __name__ == "__main__":
    main()
