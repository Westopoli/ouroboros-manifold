#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

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
    cat >&2 <<'EOF'
usage:
  mockup_qa.sh run <mockup> <script.json> <outdir> [--res 1280x720] [--grab engine|external] [--plant id[,id]] [--timeout 600]
  mockup_qa.sh liveness <mockup> <outdir>
  mockup_qa.sh diff <a.png> <b.png> [fuzz%=5] [heatmap.png]
  mockup_qa.sh scan <outdir>
  mockup_qa.sh selftest
EOF
    exit 2
}

cmd_run() {
    local mockup="$1" script="$2" outdir="$3"
    shift 3
    local res="1280x720" grab="engine" plant="" timeout="600"
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --res) res="$2"; shift 2 ;;
            --grab) grab="$2"; shift 2 ;;
            --plant) plant="$2"; shift 2 ;;
            --timeout) timeout="$2"; shift 2 ;;
            *) echo "run: unknown arg $1" >&2; exit 2 ;;
        esac
    done

    local scene="scenes/mockups/${mockup}/${mockup}_mockup.tscn"
    if [[ ! -f "$scene" ]]; then
        echo "run: no scene $scene" >&2
        exit 2
    fi
    mkdir -p "$outdir"
    local out_abs
    out_abs="$(realpath "$outdir")"
    local script_abs
    script_abs="$(realpath "$script")"

    LP_NUM_THREADS="${LP_NUM_THREADS:-2}"
    set +e
    env -u DISPLAY -u WAYLAND_DISPLAY -u XAUTHORITY \
        LIBGL_ALWAYS_SOFTWARE=1 GALLIUM_DRIVER=llvmpipe LP_NUM_THREADS="$LP_NUM_THREADS" MOCKUP_PLANT="$plant" \
        timeout --kill-after=10 "$timeout" \
        xvfb-run -a -s "-screen 0 ${res}x24" bash -c '
            OUT="$1"; shift
            (
                while true; do
                    for grab_file in "$OUT"/*.grab; do
                        [[ -e "$grab_file" ]] || continue
                        base="${grab_file%.grab}"
                        import -window root -display "$DISPLAY" "${base}.png" 2>/dev/null
                        mv "$grab_file" "${base}.done"
                    done
                    sleep 0.1
                done
            ) &
            poll_pid=$!
            "$@" >"$OUT/stdout.log" 2>"$OUT/stderr.log"
            code=$?
            kill "$poll_pid" 2>/dev/null
            exit "$code"
        ' _ "$out_abs" \
        "$GODOT" --path . --display-driver x11 --rendering-driver opengl3 -w --position 0,0 --resolution "$res" \
            --fixed-fps 30 --quit-after 100000 "$scene" -- --qa-script "$script_abs" --qa-out "$out_abs" --qa-grab "$grab"
    local exit_code=$?
    set -e
    echo "$exit_code" > "$out_abs/exit.txt"
    cmd_scan "$out_abs"
    return "$exit_code"
}

cmd_scan() {
    local outdir="$1"
    local errors_file="$outdir/errors.txt"
    local shots_file="$outdir/shots.txt"
    local marks_file="$outdir/marks.txt"

    local err_lines=""
    for log in "$outdir/stdout.log" "$outdir/stderr.log"; do
        [[ -f "$log" ]] || continue
        err_lines+="$(grep -nE 'SCRIPT ERROR|^ERROR:|^USER ERROR|Node not found' "$log" || true)"$'\n'
    done
    err_lines="$(printf '%s' "$err_lines" | sed '/^$/d')"
    local err_count=0
    if [[ -n "$err_lines" ]]; then
        err_count="$(printf '%s\n' "$err_lines" | wc -l)"
    fi
    {
        echo "count: ${err_count}"
        [[ -n "$err_lines" ]] && printf '%s\n' "$err_lines"
    } > "$errors_file"

    : > "$shots_file"
    shopt -s nullglob
    for png in "$outdir"/*.png; do
        local line
        line="$(identify -format '%f %wx%h sd=%[fx:standard_deviation]\n' "$png" 2>/dev/null || echo "$png UNREADABLE")"
        echo "$line" >> "$shots_file"
        local sd
        sd="$(echo "$line" | grep -oE 'sd=[0-9.]+' | cut -d= -f2 || echo "1")"
        if [[ -n "$sd" ]] && awk "BEGIN{exit !($sd < 0.002)}"; then
            echo "UNIFORM $(basename "$png")" >> "$shots_file"
        fi
    done
    shopt -u nullglob

    : > "$marks_file"
    for log in "$outdir/stdout.log" "$outdir/stderr.log"; do
        [[ -f "$log" ]] || continue
        grep -nE 'QA_WARN|QA_CALL|timing' "$log" >> "$marks_file" || true
    done
}

cmd_diff() {
    local a="$1" b="$2" fuzz="${3:-5}" heatmap="${4:-}"
    local total
    total="$(identify -format '%[fx:w*h]' "$a" 2>/dev/null)"
    local ae
    set +e
    ae="$(compare -metric AE -fuzz "${fuzz}%" "$a" "$b" null: 2>&1)"
    set -e
    if [[ ! "$ae" =~ ^[0-9]+$ ]]; then
        echo "diff: compare did not return a pixel count: $ae" >&2
        exit 2
    fi
    if [[ -n "$heatmap" ]]; then
        magick "$a" "$b" -compose difference -composite -auto-level "$heatmap"
    fi
    awk -v ae="$ae" -v total="$total" 'BEGIN { printf "%.6f\n", ae / total }'
}

cmd_liveness() {
    echo "liveness: not implemented yet" >&2
    exit 2
}

cmd_selftest() {
    echo "selftest: not implemented yet" >&2
    exit 2
}

[[ $# -ge 1 ]] || usage
sub="$1"
shift
case "$sub" in
    run) cmd_run "$@" ;;
    scan) cmd_scan "$@" ;;
    diff) cmd_diff "$@" ;;
    liveness) cmd_liveness "$@" ;;
    selftest) cmd_selftest "$@" ;;
    *) usage ;;
esac
