#!/usr/bin/env bash
set -euo pipefail

# Trigger the media toolchain check without opening the GitHub Actions UI.
# Requires GitHub CLI (gh) authenticated with access to this repository.
REPO="zaidaslamonline-dev/script-to-mp4"
CONTROL_ISSUE=1

if ! command -v gh >/dev/null 2>&1; then
  echo "GitHub CLI (gh) is required. Install it from https://cli.github.com/" >&2
  exit 1
fi

gh auth status >/dev/null
gh issue comment "$CONTROL_ISSUE" --repo "$REPO" --body "/run-media-check"
echo "Triggered Media toolchain check. Follow the run at:"
echo "https://github.com/$REPO/actions/workflows/media-toolchain-check.yml"
