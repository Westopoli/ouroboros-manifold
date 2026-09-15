#!/usr/bin/env bash
# Calls Antigravity CLI (agy) as a headless text worker for one transcription-class
# task. Same contract Claude uses day-side and Agora's `spec` tool uses at night.
#
# Usage: scripts/agy_task.sh <prompt-file> <schema-file> [extra agy args...]
#
# Model is selectable so the factory can move between the two quota groups agy
# exposes (`agy models`): the Gemini group and the Claude/GPT group, which have
# separate limits. Default is Claude Sonnet — the Gemini five-hour window drains
# fast under parallel fills (2026-09-14).
#   AGY_MODEL   agy model id (default claude-sonnet-4-6). `agy models` lists ids.
#   AGY_EFFORT  low|medium|high (default high). GEMINI ONLY: the Claude/GPT models
#               are fixed "thinking" tiers and reject --effort, so it is passed
#               only when the model is a Gemini one.
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

AGY_MODEL="${AGY_MODEL:-claude-sonnet-4-6}"

args=(--model "$AGY_MODEL"
      --prompt "$(cat "$PROMPT_FILE")"
      --output-format json
      --json-schema "$SCHEMA_FILE"
      --dangerously-skip-permissions
      --sandbox)

# --effort is a Gemini-only flag; the Claude/GPT models reject it.
case "$AGY_MODEL" in
  claude-*|gpt-*) : ;;
  *) args+=(--effort "${AGY_EFFORT:-high}") ;;
esac

exec agy "${args[@]}" "$@"
