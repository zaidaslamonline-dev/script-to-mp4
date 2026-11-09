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
