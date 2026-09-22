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
  mockup_qa.sh firstlook <mockup> <outdir> [--res 2560x1440] [--timeout 600]
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
        xvfb-run -a -s "-screen 0 ${res}x24 ${XVFB_EXTRA:--s 0}" bash -c '
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
            --fixed-fps "${QA_FIXED_FPS:-30}" --quit-after 100000 --script res://scenes/mockups/_shared/qa_boot.gd \
            -- --qa-scene "res://$scene" --qa-script "$script_abs" --qa-out "$out_abs" --qa-grab "$grab"
    local exit_code=$?
    set -e
    echo "$exit_code" > "$out_abs/exit.txt"
    cmd_scan "$out_abs"
    return "$exit_code"
}

cmd_firstlook() {
    local mockup="$1" outdir="$2"
    shift 2
    local res="2560x1440" timeout="600"
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --res) res="$2"; shift 2 ;;
            --timeout) timeout="$2"; shift 2 ;;
            *) echo "firstlook: unknown arg $1" >&2; exit 2 ;;
        esac
    done

    local script="scenes/mockups/${mockup}/qa/firstlook.json"
    if [[ ! -f "$script" ]]; then
        echo "firstlook: no script $script" >&2
        exit 2
    fi

    local bad
    bad="$(grep -nE '^[[:space:]]*\[[[:space:]]*"(call|seed|plant|pause)"' "$script" || true)"
    if [[ -n "$bad" ]]; then
        echo "firstlook: $script must drive real-input verbs only (no call/seed/plant/pause):" >&2
        printf '%s\n' "$bad" >&2
        exit 2
    fi

    local scene="scenes/mockups/${mockup}/${mockup}_mockup.tscn"
    if [[ ! -f "$scene" ]]; then
        echo "firstlook: no scene $scene" >&2
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
        LIBGL_ALWAYS_SOFTWARE=1 GALLIUM_DRIVER=llvmpipe LP_NUM_THREADS="$LP_NUM_THREADS" \
        timeout --kill-after=10 "$timeout" \
        xvfb-run -a -s "-screen 0 ${res}x24 ${XVFB_EXTRA:--s 0}" bash -c '
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
            --quit-after 100000 --script res://scenes/mockups/_shared/qa_boot.gd \
            -- --qa-scene "res://$scene" --qa-script "$script_abs" --qa-out "$out_abs" --qa-grab engine --qa-live
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
        err_lines+="$(grep -nE 'SCRIPT ERROR|^ERROR:|^USER ERROR|Node not found' "$log" | grep -vE 'at exit|never freed|leaked [0-9]+ bytes' || true)"$'\n'
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
    local ae_raw ae
    set +e
    ae_raw="$(compare -metric AE -fuzz "${fuzz}%" "$a" "$b" null: 2>&1)"
    set -e
    ae="$(printf '%s' "$ae_raw" | grep -oE '^[0-9]+' || true)"
    if [[ ! "$ae" =~ ^[0-9]+$ ]]; then
        echo "diff: compare did not return a pixel count: $ae_raw" >&2
        exit 2
    fi
    if [[ -n "$heatmap" ]]; then
        magick "$a" "$b" -compose difference -composite -auto-level "$heatmap"
    fi
    awk -v ae="$ae" -v total="$total" 'BEGIN { printf "%.6f\n", ae / total }'
}

cmd_liveness() {
    local mockup="$1" outdir="$2"
    local scene="scenes/mockups/${mockup}/${mockup}_mockup.tscn"
    if [[ ! -f "$scene" ]]; then
        echo "liveness: no scene $scene" >&2
        exit 2
    fi
    mkdir -p "$outdir"
    local out_abs script_abs
    out_abs="$(realpath "$outdir")"
    script_abs="$(realpath "scenes/mockups/_shared/liveness.json")"

    LP_NUM_THREADS="${LP_NUM_THREADS:-2}"
    set +e
    env -u DISPLAY -u WAYLAND_DISPLAY -u XAUTHORITY \
        LIBGL_ALWAYS_SOFTWARE=1 GALLIUM_DRIVER=llvmpipe LP_NUM_THREADS="$LP_NUM_THREADS" \
        timeout --kill-after=10 120 \
        xvfb-run -a -s "-screen 0 1280x720x24 ${XVFB_EXTRA:--s 0}" bash -c '
            OUT="$1"; shift
            (
                xdotool search --sync --name "^QA:" windowfocus --sync mousemove 640 360 click 1 key r
                touch "$OUT/xdotool.done"
            ) &
            "$@" >"$OUT/stdout.log" 2>"$OUT/stderr.log"
        ' _ "$out_abs" \
        "$GODOT" --path . --display-driver x11 --rendering-driver opengl3 -w --position 0,0 --resolution 1280x720 \
            --fixed-fps "${QA_FIXED_FPS:-30}" --quit-after 100000 --script res://scenes/mockups/_shared/qa_boot.gd \
            -- --qa-scene "res://$scene" --qa-script "$script_abs" --qa-out "$out_abs" --qa-grab engine
    local exit_code=$?
    set -e
    echo "$exit_code" > "$out_abs/exit.txt"
    cmd_scan "$out_abs"

    local os_inputs
    os_inputs="$(python3 -c "
import json
d = json.load(open('$out_abs/liveness.json'))
print(d['_qa']['os_inputs'])
" 2>/dev/null || echo -1)"
    if [[ "$os_inputs" -ge 2 ]] 2>/dev/null; then
        echo "LIVENESS OK os_inputs=$os_inputs"
        return 0
    fi
    echo "LIVENESS FAIL os_inputs=$os_inputs" >&2
    return 1
}

cmd_selftest() {
    local tmp
    tmp="$(mktemp -d)"
    local failures=0

    echo '[["nope", 1]]' > "$tmp/unknown_verb.json"
    mkdir -p "$tmp/out1"
    local exit1=0
    cmd_run landscape "$tmp/unknown_verb.json" "$tmp/out1" --timeout 120 >/dev/null 2>&1 || exit1=$?
    if [[ "$exit1" != "3" ]]; then
        echo "selftest: unknown-verb script expected exit 3, got $exit1" >&2
        failures=$((failures + 1))
    fi

    printf 'not { json' > "$tmp/not_json.json"
    mkdir -p "$tmp/out2"
    local exit2=0
    cmd_run landscape "$tmp/not_json.json" "$tmp/out2" --timeout 120 >/dev/null 2>&1 || exit2=$?
    if [[ "$exit2" != "2" ]]; then
        echo "selftest: not-json script expected exit 2, got $exit2" >&2
        failures=$((failures + 1))
    fi

    echo '[["state","ok"]]' > "$tmp/ok.json"
    mkdir -p "$tmp/out3"
    local exit3=0
    cmd_run landscape "$tmp/ok.json" "$tmp/out3" --timeout 180 >/dev/null 2>&1 || exit3=$?
    if [[ "$exit3" != "0" || ! -f "$tmp/out3/ok.json" ]]; then
        echo "selftest: ok script expected exit 0 and ok.json, got exit $exit3" >&2
        failures=$((failures + 1))
    fi

    rm -rf "$tmp"
    if [[ "$failures" -gt 0 ]]; then
        echo "SELFTEST FAILED ($failures)" >&2
        exit 1
    fi
    echo "SELFTEST OK"
}

[[ $# -ge 1 ]] || usage
sub="$1"
shift
case "$sub" in
    run) cmd_run "$@" ;;
    firstlook) cmd_firstlook "$@" ;;
    scan) cmd_scan "$@" ;;
    diff) cmd_diff "$@" ;;
    liveness) cmd_liveness "$@" ;;
    selftest) cmd_selftest "$@" ;;
    *) usage ;;
esac
