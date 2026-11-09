# Production workflow

1. Select an isolated client brand profile and gather the campaign brief.
2. Curate the script collaboratively in chat; do not generate copy independently or rewrite approved text.
3. Prepare two creative directions with distinct hooks. Variant B may use slight supporting script changes, while preserving approved factual claims and offer.
4. Approve both variant scripts. Save the JSON source and GitHub Issue approval record.
5. Choose the narration path:
   - **Generated:** run the configured TTS engine only after script approval.
   - **Uploaded:** provide an externally generated voiceover (for example, ElevenLabs). Upload one `uploaded-master` file if the configured video output have identical spoken copy, or separate `variant-A` and `variant-B` files if the copy differs. Supported source formats: WAV, MP3, M4A, AAC, FLAC, OGG.
6. Normalize uploaded audio to mono 48 kHz PCM WAV, retain source/provenance hashes, and validate duration. Uploaded audio is never silently replaced by TTS. Listen to it and explicitly approve it; import/generation does not equal approval.
7. Create a visual storyboard contact sheet in the ChatGPT conversation for review. Store the approved scene plan JSON in the campaign folder; use Hyperframes to build the timed composition from that plan and the saved narration.
8. Obtain explicit storyboard approval in chat and record approval separately for both variants.
9. Render each variant as 1080x1920, 30 FPS MP4. Hyperframes owns timeline composition; FFmpeg handles audio post-processing, muxing, encoding, and probes.
10. Run QA; reject invalid renders and preserve failed-run logs. Only bounded safe retries are allowed.
11. Upload final MP4s as GitHub Actions artifacts and provide direct links in chat.
12. Archive approved inputs, model versions, asset provenance, storyboards, voice settings, logs, QA reports, and outputs under immutable run IDs. Revisions create a new run/version; never overwrite prior approved artifacts.

## Approval boundaries
Script approval is not voiceover approval. Voiceover approval is not storyboard approval. Storyboard approval is not render approval. Manual Actions dispatch must validate the same approval fields as chat-driven approval.

## Uploaded voiceover path

Upload source audio into `campaigns/<campaign-id>/voiceovers/`:
- `uploaded-master.wav` (or another supported extension) when both variant scripts are identical.
- Otherwise upload `variant-A.wav` and `variant-B.wav` (or matching supported extensions).

Then comment on [automation issue #1](https://github.com/zaidaslamonline-dev/script-to-mp4/issues/1):
```
/import-voiceover campaign-id
```
The workflow normalizes the audio and commits canonical `variant-A.wav` / `variant-B.wav` plus metadata. It does not approve the audio. Listen and approve before storyboard production.

## Generated voiceover path

After the campaign JSON contains two non-empty approved scripts and `script.approved_by_user=true`, comment on issue #1:
```
/generate-voiceover campaign-id
```
Generation uses the configured TTS engine. Generated audio must also be listened to and explicitly approved.

## Render

Only after script, voiceover, both storyboards, and final render approvals are recorded:
```
/render-approved campaign-id
```
