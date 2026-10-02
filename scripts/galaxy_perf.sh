#!/usr/bin/env bash
# Real-GPU checks for the galaxy shell, window-free (Xvfb + Vulkan).
#
#   scripts/galaxy_perf.sh [--tag new|old] [--only SHELL-GPU,REFILL,...]
#
# Checks (scenes/mockups/galaxy/tests/gpu_checks.gd): DEVICE, SHELL-GPU
# (<= 2.0 ms full 1080p, <= 0.7 ms half resolution, 400 systems / 15 factions,
# four camera positions), SHELL-SCALE (400/15 within 15% of 219/4), REFILL
# (<= 12 ms), LOOK-LAYERS, SCREENSHOTS; plus SHADER-COMPILES here (no shader or
# script error in the Godot log). Exit 0 only if every check passes. --tag old
# captures pictures of the current renderer into results/look/old for the
# side-by-side sheets; the default tag new refuses to save legacy pictures.
#
# MEASUREMENT METHOD (kept here because it is easy to get wrong):
#  - Never time presented frames: under Xvfb each present costs 60-130 ms, the
#    GPU idles ~90% of the time and drops to 200-900 MHz, and light workloads
#    read up to ~15x too slow (a 0.4 ms scene read 7 ms).
#  - GPU time is the shell SubViewport's RenderingServer measured render time
#    (GPU timestamps), taken over 120 back-to-back RenderingServer.force_draw(false)
#    calls (no present) after 60 warm-up draws; median and p95 reported, the
#    budget is judged on the median.
#  - A burner viewport keeps the card saturated so the clocks stay up; the SM
#    clock is read with nvidia-smi after each measurement and a run below
#    1700 MHz fails.
#  - Valid only on the RTX 3060 (DEVICE check). An Xvfb display is started if
#    missing and never killed; Godot is never signalled.
set -uo pipefail
cd "$(dirname "$0")/.."
TAG="new"
ONLY=""
while [ $# -gt 0 ]; do
  case "$1" in
    --tag) TAG="$2"; shift 2 ;;
    --only) ONLY="$2"; shift 2 ;;
    *) echo "usage: $0 [--tag new|old] [--only ID,ID]" >&2; exit 2 ;;
  esac
done
DISP="${GALAXY_PERF_DISPLAY:-:77}"
if ! pgrep -af "Xvfb $DISP" >/dev/null; then
  (Xvfb "$DISP" -screen 0 1920x1080x24 >/dev/null 2>&1 &)
  sleep 2
fi
OUT="${TMPDIR:-/tmp}/galaxy_perf"
mkdir -p "$OUT"
LOG="$OUT/gpu_$TAG.log"
ARGS=(--tag="$TAG")
[ -n "$ONLY" ] && ARGS+=(--only="$ONLY")
DISPLAY="$DISP" timeout "${GALAXY_PERF_TIMEOUT:-1200}" godot --path . --rendering-driver vulkan --rendering-method forward_plus \
  --resolution 1920x1080 --disable-vsync \
  res://scenes/mockups/galaxy/tests/gpu_checks.tscn -- "${ARGS[@]}" > "$LOG" 2>&1
GODOT_RC=$?
grep -E "^CHECK |^GPU CHECKS|^GPU run invalid|^LOOK-LAYERS calibration|Vulkan 1\.|Using Device" "$LOG"
rc=0
if grep -Eq "SHADER ERROR|SCRIPT ERROR|Parse Error|Compile Error" "$LOG"; then
  echo "CHECK SHADER-COMPILES FAIL $(grep -E 'SHADER ERROR|SCRIPT ERROR|Parse Error|Compile Error' "$LOG" | head -3 | tr '\n' ' ')"
  rc=1
else
  echo "CHECK SHADER-COMPILES PASS no shader or script error in the Godot log ($LOG)"
fi
[ "$GODOT_RC" -ne 0 ] && rc=1
[ $rc -eq 0 ] && echo "GALAXY PERF OK" || echo "GALAXY PERF FAILED"
exit $rc
