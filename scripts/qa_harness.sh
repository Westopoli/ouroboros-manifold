#!/usr/bin/env bash
# scripts/qa_harness.sh -- F6 seam (two-day push, item 5). Drives the real
# game (not a mockup) through the QADaemon autoload and scenes/harness/**,
# both piece C7's (docs/northstar/plans/briefs/2026-09-22-two-day-push.md).
# Neither exists yet, so every subcommand is a skeleton: it names its target,
# checks for it, and prints a usage line instead of launching Godot at all
# when the target is missing. Once C7 lands, cmd_run/cmd_liveness/cmd_scan
# are ready to drive scenes/harness/harness.tscn using the same Xvfb pattern
# scripts/mockup_qa.sh already proved (docs/northstar/plans/briefs/
# 2026-09-22-mockup-qa-harness.md): a private Xvfb, software GL, never the
# live seat's DISPLAY (:0 or :1).
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
HARNESS_SCENE="scenes/harness/harness.tscn"

if command -v godot >/dev/null 2>&1; then
    GODOT="godot"
elif [[ -x "$HOME/.local/bin/godot" ]]; then
    GODOT="$HOME/.local/bin/godot"
elif [[ -x "/Applications/Godot.app/Contents/MacOS/Godot" ]]; then
    GODOT="/Applications/Godot.app/Contents/MacOS/Godot"
else
    echo "ERROR: godot binary not found. Install Godot 4.x or add to PATH." >&2
    exit 2
fi

usage() {
    cat >&2 <<EOF
usage:
  qa_harness.sh run [--res WxH] [--timeout N]
  qa_harness.sh liveness [--timeout N]
  qa_harness.sh scan <outdir>

run/liveness need ${HARNESS_SCENE} (piece C7); it is not built yet.
EOF
    exit 2
}

require_harness() {
    if [[ ! -f "$REPO_ROOT/$HARNESS_SCENE" ]]; then
        echo "qa_harness.sh: ${HARNESS_SCENE} not built yet (piece C7); nothing to run" >&2
        usage
    fi
}

# A fresh directory outside the checkout: Godot writes crash/perf logs and
# other cwd-relative files (autoload/sim_bridge.gd's logs/, perf_logger.gd)
# even with --path pinning the project root elsewhere, and this is real
# game state, not a disposable mockup -- cmd_run/cmd_liveness never launch
# from inside $REPO_ROOT.
scratch_dir() {
    mktemp -d -t qa_harness.XXXXXX
}

cmd_run() {
    require_harness
    local res="1280x720" timeout="120"
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --res) res="$2"; shift 2 ;;
            --timeout) timeout="$2"; shift 2 ;;
            *) echo "run: unknown arg $1" >&2; exit 2 ;;
        esac
    done

    local scratch out_abs
    scratch="$(scratch_dir)"
    out_abs="$scratch/out"
    mkdir -p "$out_abs"

    set +e
    ( cd "$scratch" && env -u DISPLAY -u WAYLAND_DISPLAY -u XAUTHORITY \
        LIBGL_ALWAYS_SOFTWARE=1 GALLIUM_DRIVER=llvmpipe \
        timeout --kill-after=10 "$timeout" \
        xvfb-run -a -s "-screen 0 ${res}x24" \
        "$GODOT" --path "$REPO_ROOT" --display-driver x11 --rendering-driver opengl3 \
            -w --position 0,0 --resolution "$res" --fixed-fps 30 --quit-after 100000 \
            "res://${HARNESS_SCENE}" >"$out_abs/stdout.log" 2>"$out_abs/stderr.log" )
    local exit_code=$?
    set -e
    echo "$exit_code" > "$out_abs/exit.txt"
    echo "$out_abs"
    return "$exit_code"
}

cmd_liveness() {
    require_harness
    local timeout="60"
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --timeout) timeout="$2"; shift 2 ;;
            *) echo "liveness: unknown arg $1" >&2; exit 2 ;;
        esac
    done

    local scratch out_abs
    scratch="$(scratch_dir)"
    out_abs="$scratch/out"
    mkdir -p "$out_abs"

    set +e
    ( cd "$scratch" && env -u DISPLAY -u WAYLAND_DISPLAY -u XAUTHORITY \
        LIBGL_ALWAYS_SOFTWARE=1 GALLIUM_DRIVER=llvmpipe \
        timeout --kill-after=10 "$timeout" \
        xvfb-run -a -s "-screen 0 1280x720x24" bash -c '
            OUT="$1"; shift
            (
                xdotool search --sync --name "^QA:" windowactivate --sync mousemove 640 360 click 1
                touch "$OUT/xdotool.done"
            ) &
            "$@" >"$OUT/stdout.log" 2>"$OUT/stderr.log"
        ' _ "$out_abs" \
        "$GODOT" --path "$REPO_ROOT" --display-driver x11 --rendering-driver opengl3 \
            -w --position 0,0 --resolution 1280x720 --fixed-fps 30 --quit-after 100000 \
            "res://${HARNESS_SCENE}" )
    local exit_code=$?
    set -e
    echo "$exit_code" > "$out_abs/exit.txt"
    echo "$out_abs"
    return "$exit_code"
}

cmd_scan() {
    local outdir="${1:-}"
    if [[ -z "$outdir" || ! -d "$outdir" ]]; then
        echo "scan: usage: qa_harness.sh scan <outdir>" >&2
        exit 2
    fi
    local errors_file="$outdir/errors.txt"
    local marks_file="$outdir/marks.txt"
    : > "$errors_file"
    : > "$marks_file"
    for log in "$outdir/stdout.log" "$outdir/stderr.log"; do
        [[ -f "$log" ]] || continue
        grep -nE 'SCRIPT ERROR|^ERROR:|^USER ERROR|Node not found' "$log" >> "$errors_file" || true
        grep -nE 'QA_WARN|QA_CALL' "$log" >> "$marks_file" || true
    done
    echo "errors: $(wc -l < "$errors_file")"
}

[[ $# -ge 1 ]] || usage
sub="$1"
shift
case "$sub" in
    run) cmd_run "$@" ;;
    liveness) cmd_liveness "$@" ;;
    scan) cmd_scan "$@" ;;
    *) usage ;;
esac
