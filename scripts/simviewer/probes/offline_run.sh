#!/bin/bash
# Two hours of unattended sweeps (sim lane 2026-10-12, "Method notes"). Usage: offline_run.sh OUTDIR
# Every step logs "name wall=Ns exit=N" to OUTDIR/run.log; step output goes to OUTDIR/<step>.log.
# A failing step never stops the next one. PROBE_SMOKE=1 runs every step at one-seed sizes.
# Nothing is printed to the terminal; run.log is the record.
set -u
set -m
OUT="${1:?usage: offline_run.sh OUTDIR}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
mkdir -p "$OUT" || exit 2
OUT="$(cd "$OUT" && pwd)"
LOG="$OUT/run.log"
cd "$ROOT" || exit 2
SMOKE="${PROBE_SMOKE:-0}"
exec 2>/dev/null   # job-control notices from the kill watchers must not reach the terminal

say() { echo "$(date '+%Y-%m-%d %H:%M:%S') $*" >> "$LOG"; }

# step NAME CAP_SECONDS CMD...   stdout+stderr to OUT/NAME.log; killed (whole group) after CAP_SECONDS.
step() {
  local name="$1" cap="$2"; shift 2
  local t0=$SECONDS rc
  say "START $name"
  "$@" > "$OUT/$name.log" 2>&1 &
  local pid=$!
  ( sleep "$cap"; kill -TERM -- "-$pid" 2>/dev/null; sleep 5; kill -KILL -- "-$pid" 2>/dev/null ) > /dev/null 2>&1 &
  local watcher=$!
  wait "$pid"; rc=$?
  kill "$watcher" 2>/dev/null; pkill -P "$watcher" 2>/dev/null
  wait "$watcher" 2>/dev/null
  if [ "$rc" -ge 128 ]; then say "$name killed or crashed (signal $((rc-128)); cap ${cap}s)"; fi
  say "$name wall=$((SECONDS-t0))s exit=$rc"
}

PY=python3
[ -x "$ROOT/.venv/bin/python" ] && PY="$ROOT/.venv/bin/python"

if [ "$SMOKE" = 1 ]; then
  MC_ARGS="--seeds 1 --missions 1"; CT_ARGS="--seeds 1 --chapters 1"; LAB_ARGS="--workers 2 --layouts 1"
  PYTEST_EXTRA="--collect-only -q"; TOP_SEL="-k test_core_world_new"
else
  MC_ARGS="--seeds 1-50 --missions 10"; CT_ARGS="--seeds 1-20 --chapters 5"; LAB_ARGS="--workers 8"
  PYTEST_EXTRA=""; TOP_SEL=""
fi
SKIP="tests/csim/test_VG_E_e1q_lots.py::test_lot_stage_equals_the_threshold_count"

say "offline run begins (smoke=$SMOKE) out=$OUT"
step make 900 make -j8 all pipe/ouroboros_pipe_dbg
step mission_choice 3600 "$PY" scripts/simviewer/probes/mission_choice.py $MC_ARGS --out "$OUT/mission_choice"
step chronicle_twin 3600 python3 scripts/simviewer/probes/chronicle_twin.py $CT_ARGS --out "$OUT/chronicle_twin"

for d in controls parity scale; do
  step "csim_$d" 1200 python3 -m pytest "tests/csim/$d" -q -p no:cacheprovider --no-header -rf --deselect "$SKIP" $PYTEST_EXTRA
done
# top-level files only: --ignore the three folders (pytest collects test_*.py there, not the helper scripts)
step csim_top 1200 python3 -m pytest tests/csim -q -p no:cacheprovider --no-header -rf --deselect "$SKIP" \
  --ignore=tests/csim/controls --ignore=tests/csim/parity --ignore=tests/csim/scale $TOP_SEL $PYTEST_EXTRA

mkdir -p "$OUT/lab"
if python3 -m scripts.skilllab --help > "$OUT/lab_help.log" 2>&1; then
  step lab 3600 python3 -m scripts.skilllab --out "$OUT/lab" $LAB_ARGS batch layout_search
else
  say "lab skipped: python3 -m scripts.skilllab --help failed on this Mac (see lab_help.log)"
fi

date '+%Y-%m-%d %H:%M:%S' > "$OUT/DONE"
say "DONE"
exit 0
