# Script to MP4

Private, approval-gated production pipeline for two distinct vertical Meta Ads variants per approved campaign.

## Stack
- **Hyperframes + HTML/CSS/GSAP**: declarative timeline and motion-graphics composition.
- **FFmpeg / FFprobe**: media processing, audio mixing, encoding, and output inspection.
- **Kokoro TTS**: local CPU-first voice generation.
- **OpenAI Whisper**: multilingual speech-to-text verification and caption alignment (not TTS).
- **yt-dlp**: optional ingestion of reference footage only when the operator has the rights and the source terms permit downloading/reuse.
- **GitHub Actions on ubuntu-latest**: orchestration and rendering.

## Output contract
- 1080x1920 (9:16), 30 FPS, MP4/H.264
- Runtime derived from approved narration/scene timing
- Two genuinely distinct hooks and creative directions per approved script
- Hybrid captions and adaptive hyper-edited pacing
- Client-specific branding, reusable mascot/voice identities
- Automated QA and immutable run archives

## Safety and approvals
No production render may run unless the script, both variant scripts, voiceover, both storyboards, and render request are explicitly approved. Manual workflow dispatch is not an approval bypass. Never rewrite approved copy silently.

## Getting started
See [docs/WORKFLOW.md](docs/WORKFLOW.md), [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md), and [docs/LICENSING.md](docs/LICENSING.md).

The initial commit is a scaffold. Rendering and media adapters are being built in stages; a green manifest validation is not proof that an MP4 render is production-ready.

## Cost
No mandatory paid API is intended. GitHub Actions quotas, CPU-only model speed, model download time, and artifact retention limits still apply.


## FixReach single-video render

The dedicated workflow is `.github/workflows/fixreach-render.yml`. It renders one 1080x1920, 30 FPS MP4 from the existing Viraj voiceover, timed Whisper captions, and the supplied transparent Sid/Lala Bhai poses. The deterministic renderer is `scripts/render_fixreach.py`.

To enable the render, place the supplied archive at `content/fixreach-transparent-characters.zip` (or extract its PNGs into `assets/characters/`). The workflow validates the required named poses, normalizes the narration, generates captions, renders the six scenes, and runs FFprobe plus a full FFmpeg decode check. A push of the archive or character files starts the render workflow automatically; it can also be run manually from Actions.

The current storyboard timings are a production draft. The final campaign approval flags remain unchanged; this workflow produces a review candidate and does not silently mark voiceover, storyboard, or final render approvals as granted.
