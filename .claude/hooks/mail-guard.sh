#!/usr/bin/env bash
# mail-guard — PreToolUse hook on SendMessage (H-077). Chats talk through scripts/method/mail.py send, never SendMessage;
# only `main` and a sub-agent id (a hex id starting with "a") are allowed. Same deny form as git-guard.sh.
# See also: docs/method/communication.md, scripts/specfactory/method_check.py (comm_send).
set -euo pipefail

INPUT="$(cat)"
TO="$(printf '%s' "$INPUT" | /usr/bin/python3 -c 'import sys,json; d=json.load(sys.stdin); print(d.get("tool_input",{}).get("to",""))' 2>/dev/null || echo "")"

if [[ "$TO" == "main" || "$TO" =~ ^a[0-9a-f]{8,} ]]; then
  exit 0
fi
/usr/bin/python3 -c "import json,sys; print(json.dumps({'hookSpecificOutput':{'hookEventName':'PreToolUse','permissionDecision':'deny','permissionDecisionReason': sys.argv[1]}}))" "denied: cross-chat messages go through scripts/method/mail.py send (docs/method/communication.md)"
exit 0
