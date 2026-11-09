# Triggering repository checks

You do not need to open the GitHub Actions page to start the media toolchain check.

## ChatGPT trigger

The automation control issue is [#1](https://github.com/zaidaslamonline-dev/script-to-mp4/issues/1).
ChatGPT can start a run by posting the exact comment `/run-media-check` there. The workflow accepts this command only from the repository owner account.

## Local command-line trigger

If you want to trigger it from your own machine, install and authenticate the GitHub CLI, then run:

```bash
bash scripts/trigger-media-check.sh
```

The script posts the same command to issue #1. It does not store or ask for a token in the repository.

## Manual backup

The workflow still supports `workflow_dispatch` from the Actions page.

Workflow: [Media toolchain check](../.github/workflows/media-toolchain-check.yml)

## Generate approved voiceovers from chat

After the campaign JSON contains two non-empty approved scripts and `script.approved_by_user=true`, comment on [automation issue #1](https://github.com/zaidaslamonline-dev/script-to-mp4/issues/1):

```
/generate-voiceover campaign-id
```

The workflow uses Kokoro on a CPU runner, generates both WAV files, commits the audio and metadata under `campaigns/<campaign-id>/voiceovers/`, and posts direct file links back to issue #1. The campaign language defaults to `en-us`; set `language` to `hi` for Hindi. A campaign-level `voice_profile.voice_id` can override the default voice. Gujarati remains unsupported by this Kokoro workflow.

Voiceover generation does not approve the audio. Listen to both files and explicitly approve them in the campaign record before storyboard production.

## Render an approved campaign from chat

Comment on [automation issue #1](https://github.com/zaidaslamonline-dev/script-to-mp4/issues/1):

```
/render-approved campaign-id
```

This starts the render workflow only when the repository owner posts the command. The workflow validates the campaign ID, enforces all script/voiceover/storyboard/render approval gates, renders both variants, runs FFprobe checks, and uploads the MP4s as a 14-day artifact. It will fail closed if any approval is missing.

## One local command for both jobs

After installing and authenticating GitHub CLI:

```bash
bash scripts/trigger.sh media-check
bash scripts/trigger.sh generate-voiceover campaign-id
bash scripts/trigger.sh render-approved campaign-id
```

The second command still enforces all approvals in the GitHub workflow; the local script cannot bypass them.
