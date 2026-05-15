#!/usr/bin/env bash
# git-guard — PreToolUse hook. Blocks dangerous git ops even if upstream allow list slipped.
# Receives PreToolUse JSON on stdin; reads tool_input.command.
# Exit 0 + empty stdout = allow. Print JSON with permissionDecision=deny = block.

set -euo pipefail

INPUT="$(cat)"
CMD="$(printf '%s' "$INPUT" | /usr/bin/python3 -c 'import sys,json; d=json.load(sys.stdin); print(d.get("tool_input",{}).get("command",""))' 2>/dev/null || echo "")"

if [[ -z "$CMD" ]]; then
  exit 0
fi

deny() {
  local reason="$1"
  /usr/bin/python3 -c "import json,sys; print(json.dumps({'hookSpecificOutput':{'hookEventName':'PreToolUse','permissionDecision':'deny','permissionDecisionReason': sys.argv[1]}}))" "$reason"
  exit 0
}

# Hard regex denies — catch destructive patterns even with weird spacing/quoting.
if [[ "$CMD" =~ git[[:space:]]+reset[[:space:]]+--hard ]]; then
  deny "git reset --hard is blocked by git-guard"
fi
if [[ "$CMD" =~ git[[:space:]]+clean[[:space:]]+-[fd] ]]; then
  deny "git clean -f / -d is blocked by git-guard"
fi
if [[ "$CMD" =~ git[[:space:]]+push[[:space:]]+(.*[[:space:]])?(-f|--force) ]]; then
  deny "force push is blocked by git-guard"
fi
if [[ "$CMD" =~ git[[:space:]]+commit[[:space:]]+(.*[[:space:]])?--no-verify ]]; then
  deny "--no-verify is blocked by git-guard (don't bypass hooks)"
fi
if [[ "$CMD" =~ git[[:space:]]+commit[[:space:]]+(.*[[:space:]])?--amend ]]; then
  deny "--amend is blocked by git-guard (create a new commit instead)"
fi
if [[ "$CMD" =~ git[[:space:]]+branch[[:space:]]+(.*[[:space:]])?-D ]]; then
  deny "git branch -D is blocked by git-guard (use -d for safe delete)"
fi
if [[ "$CMD" =~ git[[:space:]]+checkout[[:space:]]+.*--[[:space:]] ]]; then
  deny "git checkout -- <path> can destroy local edits; blocked by git-guard"
fi
if [[ "$CMD" =~ git[[:space:]]+rebase ]]; then
  deny "git rebase is blocked by git-guard (rewriting history needs human review)"
fi

# Branch-guard: block commit/push on protected branches.
if [[ "$CMD" =~ git[[:space:]]+(commit|push) ]]; then
  CURRENT_BRANCH="$(git -C "${CLAUDE_PROJECT_DIR:-.}" symbolic-ref --short HEAD 2>/dev/null || echo "")"
  case "$CURRENT_BRANCH" in
    main|master)
      deny "you are on protected branch '$CURRENT_BRANCH' — create a feature branch via 'git checkout -b wn/<slug>' first"
      ;;
  esac
fi

exit 0
