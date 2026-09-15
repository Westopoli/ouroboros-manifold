#!/usr/bin/env bash
# Calls Antigravity CLI (agy) as a headless text worker for one transcription-class
# task. Same contract Claude uses day-side and Agora's `spec` tool uses at night.
#
# Usage: scripts/agy_task.sh <prompt-file> <schema-file> [extra agy args...]
#
# Prints agy's JSON result on stdout. Non-zero exit if agy itself errors; the
# caller still has to check the JSON's "status" field for tool-level failures
# (denied_actions, empty response) since agy exits 0 on those.
set -euo pipefail

if [[ $# -lt 2 ]]; then
  echo "usage: $0 <prompt-file> <schema-file> [extra agy args...]" >&2
  exit 2
fi

PROMPT_FILE="$1"
SCHEMA_FILE="$2"
shift 2

# agy picks file-based token storage over the keyring whenever SSH_CONNECTION
# (or SSH_CLIENT/SSH_TTY) is set, which the calling shell may inherit even when
# the actual login used the keyring. Unset them so agy finds the real sign-in.
# See docs/northstar/research/gemini_compute.md for the isolation that found this.
unset SSH_CONNECTION SSH_CLIENT SSH_TTY

export PATH="$HOME/.local/bin:$PATH"

exec agy \
  --prompt "$(cat "$PROMPT_FILE")" \
  --output-format json \
  --json-schema "$SCHEMA_FILE" \
  --effort high \
  --dangerously-skip-permissions \
  --sandbox \
  "$@"
