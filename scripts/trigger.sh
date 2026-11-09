#!/usr/bin/env bash
set -euo pipefail

REPO="zaidaslamonline-dev/script-to-mp4"
CONTROL_ISSUE=1

usage() {
  echo "Usage:"
  echo "  bash scripts/trigger.sh media-check"
  echo "  bash scripts/trigger.sh render-approved <campaign-id>"
}

if ! command -v gh >/dev/null 2>&1; then
  echo "GitHub CLI (gh) is required: https://cli.github.com/" >&2
  exit 1
fi
gh auth status >/dev/null

case "${1:-}" in
  media-check)
    command_text="/run-media-check"
    ;;
  render-approved)
    campaign_id="${2:-}"
    if [[ ! "$campaign_id" =~ ^[a-z0-9][a-z0-9-]*$ ]]; then
      usage >&2
      exit 2
    fi
    command_text="/render-approved $campaign_id"
    ;;
  *)
    usage >&2
    exit 2
    ;;
esac

gh issue comment "$CONTROL_ISSUE" --repo "$REPO" --body "$command_text"
echo "Triggered: $command_text"
echo "Monitor runs: https://github.com/$REPO/actions"
