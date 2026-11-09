# Architecture and milestones

## Core media stack
- Hyperframes HTML compositions define timeline clips and declarative timing. Use GSAP for visual motion only; media visibility/playback remains controlled by Hyperframes data attributes.
- FFmpeg/FFprobe handle audio/video transforms, encoding, metadata, and validation.
- Kokoro provides CPU-first local TTS; Whisper verifies generated speech and supplies transcription/timing evidence.
- yt-dlp is an optional reference-footage ingestion adapter and must enforce an operator attestation that the source is owned or licensed for commercial reuse.

## Milestones
1. Repo contracts, client/campaign schemas, and approval validation.
2. Script variants and issue-based approval records.
3. Kokoro/Whisper voice generation, multilingual handling, stable character voice profiles.
4. Hyperframes composition builder and motion/caption primitives.
5. FFmpeg mixdown and yt-dlp authorized-asset ingestion.
6. Render QA, bounded retry, delivery, and immutable archive.
7. Later: Meta Ads performance ingestion (not current scope).

## Cost caveat
No paid API is mandatory in the intended baseline. GitHub Actions quotas, model downloads, CPU-only inference, and artifact retention are hard limits. Start with sequential rendering (one Hyperframes worker) to avoid memory exhaustion on hosted runners.
