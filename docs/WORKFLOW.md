# Production workflow

1. Select an isolated client brand profile and gather the campaign brief.
2. Curate the script collaboratively in chat; do not generate copy independently or rewrite approved text.
3. Prepare two creative directions with distinct hooks. Variant B may use slight supporting script changes, while preserving approved factual claims and offer.
4. Approve both variant scripts. Save the JSON source and GitHub Issue approval record.
5. Generate both Kokoro voiceovers on Ubuntu only after script approval; commit WAV files and metadata into the campaign's GitHub folder.
6. Listen to both voiceovers in chat and record explicit voiceover approval. Generation does not equal approval.
7. Create a visual storyboard contact sheet in the ChatGPT conversation for review. Store the approved scene plan JSON in the campaign folder; use Hyperframes to build the timed composition from that plan and the saved narration.
8. Obtain explicit storyboard approval in chat and record approval separately for both variants.
9. Render each variant as 1080x1920, 30 FPS MP4. Hyperframes owns timeline composition; FFmpeg handles audio post-processing, muxing, encoding, and probes.
10. Run QA; reject invalid renders and preserve failed-run logs. Only bounded safe retries are allowed.
11. Upload final MP4s as GitHub Actions artifacts and provide direct links in chat.
12. Archive approved inputs, model versions, asset provenance, storyboards, voice settings, logs, QA reports, and outputs under immutable run IDs. Revisions create a new run/version; never overwrite prior approved artifacts.

## Approval boundaries
Script approval is not storyboard approval. Storyboard approval is not render approval. Manual Actions dispatch must validate the same approval fields as chat-driven approval.

## Chat-controlled stages

- Script approval is recorded in `campaign.json` only after explicit user approval in chat.
- `/generate-voiceover <campaign-id>` creates and commits the two approved voiceovers. The assistant then presents them for listening and approval.
- The assistant creates a campaign-specific storyboard preview in chat using image generation. After approval, it saves the scene plan JSON and marks the storyboard approvals in `campaign.json`.
- `/render-approved <campaign-id>` is used only after final render approval. The render workflow can rebuild compositions from committed storyboard JSON and voiceover WAVs, so temporary run folders do not need to be committed.

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

The optional BGM input is rejected unless its asset ID resolves to a manifest record with verified commercial rights and a matching SHA-256 file hash. Omit BGM if no cleared track is available.\n\nThe Kokoro adapter currently supports English and Hindi. Gujarati is explicitly blocked because Kokoro does not provide a Gujarati voice pack; use a separately approved recording or evaluated Gujarati TTS engine rather than substituting another language.
