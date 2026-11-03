#!/usr/bin/env bash
# kill-guard — PreToolUse hook (Bash). Denies kill, pkill, killall and fuser -k at the start of a command segment;
# processes are killed through scripts/method/proc.py reap (H-081). Words inside quotes are not segment starts.
# See also: .claude/hooks/git-guard.sh (same JSON in, same deny out)
set -euo pipefail
INPUT="$(cat)"
printf '%s' "$INPUT" | /usr/bin/python3 -c '
import json, re, shlex, sys
try:
    cmd = json.load(sys.stdin).get("tool_input", {}).get("command", "")
except Exception:
    sys.exit(0)
lex = shlex.shlex(cmd, posix=True, punctuation_chars=";&|()\n")
lex.whitespace_split = True
lex.commenters = ""
try:
    toks = list(lex)
except ValueError:
    toks = cmd.split()
seg = []
segs = []
for t in toks:
    if t and all(c in ";&|()\n" for c in t):
        segs.append(seg); seg = []
    else:
        seg.append(t)
segs.append(seg)
for s in segs:
    while s and (re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*=.*", s[0]) or s[0] in ("sudo", "exec", "command", "nohup", "time")):
        s = s[1:]
    if not s:
        continue
    head = s[0].rsplit("/", 1)[-1]
    bad = head in ("kill", "pkill", "killall") or (head == "fuser" and any(re.fullmatch(r"-[A-Za-z]*k[A-Za-z]*", x) for x in s[1:]))
    if bad:
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
              "permissionDecisionReason": "denied: processes are killed through scripts/method/proc.py reap (docs/stories/H-081.md)"}}))
        break
'
exit 0
