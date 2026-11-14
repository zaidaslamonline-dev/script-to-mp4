# FixReach Edge TTS voiceover

This branch adds a dedicated Edge TTS voiceover stage to the existing FixReach production repository.

## Stable character voices

The voice IDs are saved in each script's \`voice_profiles\` object so future scripts reuse the same identities:

- **Sid:** \`hi-IN-AaravNeural\`
- **Lala Bhai:** \`hi-IN-MadhurNeural\`

Change a voice only as an intentional character-voice decision by editing the shared profile file. Do not add per-script overrides unless you deliberately want a one-off alternate voice. Both defaults are Hindi male neural voices. They are starting profiles; listen to the first output and confirm the character fit before locking them as the long-term canon.

## Generate

Every push to \`feat/fixreach-edge-tts-voiceover\` runs the workflow. It can also be started manually from Actions.

The workflow reads:
\`content/voiceovers/fixreach-better-leads-001.json\`

It creates:
- \`voiceover.wav\` — 48 kHz stereo PCM, normalized for post-production
- \`voiceover.mp3\` — 192 kbps listening copy
- \`voiceover_manifest.json\` — speaker-to-voice mapping, delivery cues and duration

Download the \`fixreach-edge-tts-voiceover\` artifact from the completed GitHub Actions run.

## Script format

Each turn has a \`speaker\` and \`text\`. Supported speaker names must exist in \`voice_profiles\`. The opening bracket tag is treated as a delivery cue, not spoken. Inline \`[pause]\` and \`[slight pause]\` markers become silence. Add future characters by adding a profile with a fixed Edge voice ID and using that exact speaker key on their turns.

## Important limitations

- Edge TTS is a network service accessed through the community \`edge-tts\` Python package. No API key is required by this workflow, but Microsoft can change service availability or limits.
- Edge TTS does not expose native acting/emotion controls for these voices. Delivery labels are approximated with subtle speaking-rate and pitch changes; they are not true emotion synthesis.
- The script is written in Roman Hinglish. Hindi neural voices may pronounce Romanized Hindi and English loanwords differently from a native Hinglish speaker. Listen carefully; if pronunciation is off, add a per-turn \`tts_text\` field in Devanagari/phonetic spelling in a future enhancement rather than silently changing the canonical on-screen script.
- A successful workflow means audio files were generated and technically encoded. It does not mean the voice acting has been approved. Listen to the MP3 before marking the voiceover approved or using it in a final video.
- This workflow produces narration only. It does not bypass script, storyboard, or final-render approval gates in the existing video pipeline.
