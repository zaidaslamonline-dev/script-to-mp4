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
