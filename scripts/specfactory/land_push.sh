#!/usr/bin/env bash
# H-059: land_push.sh <worktree> <id>. Under push.lock: fetch, merge origin/main, the pre_gate re-check, `git push HEAD:main`.
# Prints `PUSHED <sha>` (exit 0) or `PUSH REJECT <why>` (exit 1); fails closed when push.lock is not won in time.
# pre_gate.sh is found beside this script; the lock is $HOME/Projects/om-push/push.lock.
# See also: docs/method/clerk.md step 7, scripts/specfactory/pre_gate.sh
set -uo pipefail
[[ $# -eq 2 ]] || { echo "usage: land_push.sh <worktree> <id>" >&2; exit 64; }
WT="$1"; ID="$2"
# H-074: gate scratch lives on the real disk, not the quota-limited /tmp tmpdisk. A caller TMPDIR is kept only when it is not
# /tmp or under /tmp. See also: docs/stories/H-074.md, tests/specfactory/test_gate_scratch.py (inlined in four scripts: land_push.sh is copied alone in tests)
case "${TMPDIR:-}" in ""|/tmp|/tmp/*) TMPDIR="$HOME/Projects/om-push/tmp" ;; esac
mkdir -p "$TMPDIR" && export TMPDIR
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# LAND_PUSH_LOCK_TIMEOUT_S is a test seam: tests shorten the 600 s default to prove the fail-closed path.
TIMEOUT_S="${LAND_PUSH_LOCK_TIMEOUT_S:-600}"
LOCK="$HOME/Projects/om-push/push.lock"
reject() { echo "PUSH REJECT $*"; exit 1; }

mkdir -p "$(dirname "$LOCK")" && exec 9>>"$LOCK" || reject "cannot open $LOCK"
flock -w "$TIMEOUT_S" 9 || reject "push.lock not won in ${TIMEOUT_S}s"

cd "$WT" || reject "no worktree $WT"
git fetch -q origin || reject "git fetch origin failed"
git merge -q --no-edit origin/main >/dev/null 2>&1 || reject "merge of origin/main conflicts"
"$HERE/pre_gate.sh" "$WT" origin/main "$ID" >/dev/null 2>&1 || reject "pre_gate re-check failed for $ID"
git push -q origin HEAD:main 2>/dev/null || reject "git push HEAD:main refused (main moved?)"
echo "PUSHED $(git rev-parse HEAD)"
