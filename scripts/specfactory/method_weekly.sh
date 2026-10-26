#!/usr/bin/env bash
# Weekly method metrics without a chat (spec method_rev3 Design "Weekly run"; G15 reap with a dry run first).
# See also: systemd/om-method-metrics.timer, method_metrics.py. --dry-run prints "+ <command>" lines and runs nothing.
set -euo pipefail
DRY=0; [ "${1:-}" = "--dry-run" ] && DRY=1
LIVE="${OM_REPO:-$HOME/Projects/ouroboros-manifold}"   # read only for scripts; all work happens in the worktree
SF="$LIVE/scripts/specfactory"
ROOT="$HOME/Projects/om-push"
WEEK=$(date -d "last week" +%G-W%V)
NAME="metrics-$WEEK"
WT="$ROOT/wt/$NAME"
run() { echo "+ $*"; [ "$DRY" = 1 ] || "$@"; }

run python3 "$SF/wt.py" new "$NAME" --owner method_weekly --purpose "weekly method metrics $WEEK"
run git -C "$WT" fetch origin
run git -C "$WT" merge --ff-only origin/main
run python3 "$WT/scripts/specfactory/method_metrics.py" --week "$WEEK" --write
# G15: dry run first, then the real reap (wt.py reap removes only the trees the dry run verdict allows)
run python3 "$SF/wt.py" reap --dry-run
run python3 "$SF/wt.py" reap
run git -C "$WT" add -A
run git -C "$WT" commit -m "METRIC-$WEEK: weekly method metrics"
run flock -w 1800 "$ROOT/records.lock" git -C "$WT" push origin HEAD:main
if [ "$DRY" = 1 ]; then echo "+ python3 $SF/wt.py done $WT <pushed sha>"; exit 0; fi
run python3 "$SF/wt.py" done "$WT" "$(git -C "$WT" rev-parse HEAD)"
