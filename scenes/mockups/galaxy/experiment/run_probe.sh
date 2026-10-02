#!/usr/bin/env bash
# Runs the probe on the real GPU without a visible window: Xvfb + Vulkan.
# Usage: run_probe.sh <cfg.json> [dump_dir]
# Every result JSON records the device name Godot reports (meta.device).
set -euo pipefail
cd "$(dirname "$0")/../../../.."
CFG="$(readlink -f "$1")"
DISP=:77
if ! pgrep -af "Xvfb $DISP" >/dev/null; then
  (Xvfb $DISP -screen 0 1920x1080x24 >/dev/null 2>&1 &)
  sleep 2
fi
export DISPLAY=$DISP
ARGS=(--cfg="$CFG")
[ "${2:-}" != "" ] && ARGS+=(--dump="$(readlink -f "$2")")
LOG="${PROBE_LOG:-/tmp/claude-1000/probe.log}"
timeout "${PROBE_TIMEOUT:-900}" godot --path . --rendering-driver vulkan --rendering-method forward_plus \
  --resolution 1920x1080 --disable-vsync \
  res://scenes/mockups/galaxy/experiment/probe.tscn -- "${ARGS[@]}" > "$LOG" 2>&1 || true
grep -E "PROBE|SCRIPT ERROR|SHADER ERROR|Parse Error|Vulkan 1" "$LOG" | head -60
