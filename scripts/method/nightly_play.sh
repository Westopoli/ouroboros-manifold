#!/bin/bash
# H-004: nightly play of main. Plays `play.sh --check`, keeps the game open for the nightly minutes,
# turns PLAY REJECT and Godot ERROR lines of .play.log into FINDING lines.
# See also: scripts/method/file_findings.py (reads the log), docs/stories/H-004.md; the 30B driver is H-007.
set -u
MAIN="${OM_MAIN:-$HOME/Projects/om-push/main}"
MINUTES="${DRAFT_NIGHTLY_PLAY_MINUTES:-20}"   # DRAFT-nightly-play-minutes
LOG="$HOME/Projects/om-push/nightly/$(date +%F).log"
PLAY="$MAIN/scripts/play.sh --check"
if [ "${1:-}" = "--dry-run" ]; then
  echo "cd $MAIN && $PLAY; keep open ${MINUTES} min; log $LOG"
  exit 0
fi
mkdir -p "$(dirname "$LOG")"
cd "$MAIN" || exit 1
git fetch -q origin && git merge -q --ff-only origin/main
: > "$MAIN/.play.log"
{ echo "nightly play $(date -Is) $(git rev-parse --short HEAD)"; } > "$LOG"
bash "$MAIN/scripts/play.sh" --check >> "$LOG" 2>&1
timeout "${MINUTES}m" bash "$MAIN/scripts/play.sh" >> "$LOG" 2>&1
grep -E 'PLAY REJECT|SCRIPT ERROR|ERROR' "$MAIN/.play.log" 2>/dev/null | sed -E 's/^/FINDING /' >> "$LOG"
exit 0
