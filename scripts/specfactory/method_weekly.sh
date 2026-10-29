#!/usr/bin/env bash
# Weekly method metrics without a chat (spec method_rev3 Design "Weekly run").
# See also: systemd/om-method-metrics.timer, method_metrics.py. --dry-run prints "+ <command>" lines and runs nothing.
set -euo pipefail
DRY=0; [ "${1:-}" = "--dry-run" ] && DRY=1
LIVE="${OM_REPO:-$HOME/Projects/ouroboros-manifold}"   # read only for scripts; all work happens in the worktree
SF="$LIVE/scripts/specfactory"
ROOT="$HOME/Projects/om-push"
NOW="${OM_NOW:-now}"   # OM_NOW fakes the clock for tests
# A12: the week ending today on a Sunday, else the week that ended last Sunday
if [ "$(date -d "$NOW" +%u)" = 7 ]; then WEEK=$(date -d "$NOW" +%G-W%V); else WEEK=$(date -d "$NOW last sunday" +%G-W%V); fi
NAME="metrics-$WEEK"
WT="$ROOT/wt/$NAME"
run() { echo "+ $*"; [ "$DRY" = 1 ] || "$@"; }

run python3 "$SF/wt.py" new "$NAME" --owner method_weekly --purpose "weekly method metrics $WEEK"
run git -C "$WT" fetch origin
run git -C "$WT" merge --ff-only origin/main
# A12: method_metrics.py exits 1 on any FAIL; set -e must not end the script before the commit records the week
run python3 "$WT/scripts/specfactory/method_metrics.py" --week "$WEEK" --write || true
# A12: the reap stays halted by Westley; only the dry run runs, its output goes into the week's commit
REAP_OUT="$WT/docs/northstar/plans/method_rev3_2026-10-26/metrics/${WEEK}_reap_dryrun.txt"
echo "+ python3 $SF/wt.py reap --dry-run > $REAP_OUT"
if [ "$DRY" != 1 ]; then mkdir -p "$(dirname "$REAP_OUT")"; python3 "$SF/wt.py" reap --dry-run > "$REAP_OUT"; fi
run git -C "$WT" add -A
run git -C "$WT" commit -m "METRIC-$WEEK: weekly method metrics"
run flock -w 1800 "$ROOT/records.lock" git -C "$WT" push origin HEAD:main
if [ "$DRY" = 1 ]; then echo "+ python3 $SF/wt.py done $WT <pushed sha>"; exit 0; fi
run python3 "$SF/wt.py" done "$WT" "$(git -C "$WT" rev-parse HEAD)"
