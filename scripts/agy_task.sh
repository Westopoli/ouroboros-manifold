#!/usr/bin/env bash
# Calls Antigravity CLI (agy) as a headless text worker for one transcription-class
# task. Same contract Claude uses day-side and Agora's `spec` tool uses at night.
#
# Usage: scripts/agy_task.sh <prompt-file> <schema-file> [extra agy args...]
#
# Model and effort are overridable by env, both defaulting to the original
# behavior (agy's own default model = Gemini Flash; effort high):
#   AGY_MODEL   agy model id (e.g. claude-sonnet-4-6) — draws on that model's
#               quota group. Unset = agy default. `agy models` lists ids.
#   AGY_EFFORT  low|medium|high (default high).
# The Claude group (claude-sonnet-4-6, claude-opus-4-6-thinking) has a separate
# quota from Gemini; route transcription work there when Gemini's is drained.
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

# Default to Claude Sonnet through agy's Claude/GPT quota group (see `agy models`):
# the Gemini five-hour window drains fast under parallel fills (2026-09-14).
AGY_MODEL="${AGY_MODEL:-claude-sonnet-4-6}"

exec agy \
  --prompt "$(cat "$PROMPT_FILE")" \
  --output-format json \
  --json-schema "$SCHEMA_FILE" \
  --effort "${AGY_EFFORT:-high}" \
  ${AGY_MODEL:+--model "$AGY_MODEL"} \
  --dangerously-skip-permissions \
  --sandbox \
  "$@"
