# FixReach Gemini TTS voiceover

This branch generates one continuous multi-character voiceover with a single Gemini TTS API request.

## Stable character voices

Voice IDs are saved in `config/fixreach_voice_profiles.json` and reused across scripts:

- **Sid:** `Puck` — upbeat; assigned to the youthful mentor.
- **Lala Bhai:** `Gacrux` — mature; assigned to the repair-business owner.

Only change these voice IDs as an intentional character-voice decision. Gemini multi-speaker TTS supports two configured speakers per request, matching the current Sid + Lala Bhai format.

## Generate

Every push to `feat/fixreach-edge-tts-voiceover` runs the workflow. It can also be started manually from Actions.

The workflow reads `content/voiceovers/fixreach-better-leads-001.json` and creates:

- `voiceover.wav` — 48 kHz stereo PCM, normalized for post-production
- `voiceover.mp3` — 192 kbps listening copy
- `voiceover_manifest.json` — model, one-request count, speaker-to-voice mapping, delivery cues and duration

Download the `fixreach-gemini-tts-voiceover` artifact from the completed GitHub Actions run.

## Script format

Each turn has a `speaker` and `text`. Speaker names must match the keys in the shared voice profile file. Existing bracketed emotion cues are passed to Gemini as performance tags; `[pause]` and `[slight pause]` are mapped to `[long pause]` and `[short pause]`. The complete speaker-labelled transcript is sent in one request, not one request per line.

Add scripts with the same `segments` structure. Keep the same speaker names and shared profiles to preserve voice identity.

## API and secret

- Model: `gemini-3.1-flash-tts-preview`
- API: Gemini generateContent with multi-speaker voice configuration
- Request count: exactly one TTS API request per workflow execution
- Required GitHub Actions secret: `GEMINI_API_KEY`

The workflow does not print or expose the key. Do not put API keys in script files or commit them to the repository.

## Audio review

The script is Roman Hinglish. Gemini supports Hindi and multi-speaker TTS, but Romanized Hinglish pronunciation and acting quality still need a human listen-through. A technically successful workflow is not the same as creative approval. Listen to the MP3 before using the narration in a final video.
