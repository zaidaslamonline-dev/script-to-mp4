# Production workflow

1. Select an isolated client brand profile and gather the campaign brief.
2. Curate the script collaboratively in chat; do not generate copy independently or rewrite approved text.
3. Prepare two creative directions with distinct hooks. Variant B may use slight supporting script changes, while preserving approved factual claims and offer.
4. Approve both variant scripts. Save the JSON source and GitHub Issue approval record.
5. Generate Kokoro voiceover on Ubuntu. Use Whisper for multilingual transcript verification/caption alignment, not for TTS.
6. Store versioned voice profiles and per-character voice assignments.
7. Build both Hyperframes storyboards using narration-derived timing. Obtain explicit storyboard approval.
8. Render each variant as 1080x1920, 30 FPS MP4. Hyperframes owns timeline composition and animation; FFmpeg handles audio post-processing, muxing, encoding, and probes.
9. Run QA; reject invalid renders and preserve failed-run logs. Only bounded safe retries are allowed.
10. Attach both MP4s to the GitHub Issue and provide direct chat download links.
11. Archive approved inputs, model versions, asset provenance, storyboards, voice settings, logs, QA reports, and outputs under immutable run IDs.
12. Revisions create a new run/version; never overwrite prior approved artifacts.

## Approval boundaries
Script approval is not storyboard approval. Storyboard approval is not render approval. Manual Actions dispatch must validate the same approval fields as chat-driven approval.

## Current command-line entry points

These commands are deliberately separate so each approval gate remains visible:

```bash
# 1. Generate TTS only after setting script.approved_by_user=true,
#    variant.approved=true, and exact variant.script_text in campaign JSON.
python scripts/generate_voiceover.py \
  --campaign campaigns/example-campaign/campaign.json \
  --variant A --text-file runs/approved-script-A.txt \
  --language en --voice af_heart --output runs/variant-A/voiceover.wav

# 2. Verify the generated voiceover and create timed caption data.
python scripts/verify_whisper.py runs/variant-A/voiceover.wav \
  --language en --output runs/variant-A/transcript.json
python scripts/captions_from_whisper.py runs/variant-A/transcript.json \
  --output runs/variant-A/captions.json

# 3. Build a reviewable HTML storyboard draft (does not render an MP4).
python scripts/build_composition.py \
  --campaign campaigns/example-campaign/campaign.json \
  --storyboard campaigns/example-campaign/storyboards/variant-A.json \
  --voiceover runs/variant-A/voiceover.wav \
  --captions runs/variant-A/captions.json \
  --output-dir runs/variant-A

# 4. Render both variants only after every approval gate is recorded.
python scripts/render_approved.py \
  --campaign campaigns/example-campaign/campaign.json \
  --runs-dir runs --output-dir renders
```

The Kokoro adapter currently supports English and Hindi. Gujarati is explicitly blocked because Kokoro does not provide a Gujarati voice pack; use a separately approved recording or evaluated Gujarati TTS engine rather than substituting another language.
