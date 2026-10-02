#!/usr/bin/env bash
# Fast checks, every iteration, no window on the desktop:
#   1. static + draw-count checks (headless, dummy renderer): COST-SHAPE, ONE-DRAW
#   2. field checks on a real Vulkan device under Xvfb: FIELD-EQ, FIELD-VALUES,
#      FIELD-ORDER, FIELD-CONQUEST, FIELD-MEM (the grid is filled by the card)
#   3. the existing mockup verify (scripts/mockup_verify.sh galaxy)
# Usage: scenes/mockups/galaxy/tests/run_fast.sh [static|field|verify]...  (default: all)
# Exit 0 only when every selected stage passes. Never kills processes.
set -uo pipefail
cd "$(dirname "$0")/../../../.."
OUT="${TMPDIR:-/tmp}/galaxy_fast"
mkdir -p "$OUT"
STAGES=("$@")
[ ${#STAGES[@]} -eq 0 ] && STAGES=(static field verify)
rc=0

run_static() {
  timeout "${FAST_TIMEOUT:-300}" godot --headless --path . --script res://scenes/mockups/galaxy/tests/test_static.gd 2>&1 | tee "$OUT/static.log" | grep -E "^CHECK |^STATIC TESTS|SCRIPT ERROR|Parse Error"
  grep -q "^STATIC TESTS OK" "$OUT/static.log"
}

run_field() {
  local disp="${GALAXY_PERF_DISPLAY:-:77}"
  if ! pgrep -af "Xvfb $disp" >/dev/null; then
    (Xvfb "$disp" -screen 0 1920x1080x24 >/dev/null 2>&1 &)
    sleep 2
  fi
  DISPLAY="$disp" timeout "${FAST_TIMEOUT:-900}" godot --path . --rendering-driver vulkan --rendering-method forward_plus \
    --resolution 1920x1080 --script res://scenes/mockups/galaxy/tests/test_field.gd 2>&1 | tee "$OUT/field.log" | grep -E "^DEVICE |^CHECK |^FIELD TESTS|SCRIPT ERROR|SHADER ERROR|Parse Error"
  grep -q "^FIELD TESTS OK" "$OUT/field.log"
}

run_verify() {
  scripts/mockup_verify.sh galaxy 2>&1 | grep -E "^FAIL|^VERIFY"
  [ "${PIPESTATUS[0]}" -eq 0 ]
}

for s in "${STAGES[@]}"; do
  echo "== $s =="
  case "$s" in
    static) run_static || rc=1 ;;
    field)  run_field  || rc=1 ;;
    verify) run_verify || rc=1 ;;
    *) echo "unknown stage $s" >&2; rc=2 ;;
  esac
done
[ $rc -eq 0 ] && echo "ALL FAST CHECKS OK" || echo "FAST CHECKS FAILED"
exit $rc
