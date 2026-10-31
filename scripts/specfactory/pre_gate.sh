#!/usr/bin/env bash
# scripts/specfactory/pre_gate.sh <candidate_worktree> <base_ref> <piece_ids> [<test path> ...]
#
# Method rev 2, the two-tier gate: the cheap pre-gate a builder runs before the
# push and a landing clerk runs before taking gate.lock, so a full gate is never
# spent on noise or lint rejects. Prints one line per step,
# `PRE_GATE <step> OK|REJECT|WARN <detail>`, and ends `PRE_GATE verdict OK`
# (exit 0) or `PRE_GATE verdict REJECT` (exit 1). Exit 2: usage.
# Steps: (1) noise (.uid / .import files in status or deleted .import in the
# diff), (2) gate (merge_gate.sh --revert, output passed through verbatim),
# (3) tests (each given .py / pytest id or .gd file), (4) pins (rule pins of the
# diff's tests); H-017 adds `PREGATE pins skipped|OK|REJECT` after the tests step. H-006: no owner-row or provenance step; `PREGATE story OK <n> paths` names the story's Tests paths,
# which run as the piece's tests when none are given.
# Never takes ~/Projects/om-push/gate.lock, never pushes, never writes in <wt> (but the csrc pins step builds pipe/ouroboros_pipe there).
#
# See also: merge_gate.sh --revert
set -uo pipefail

if [[ $# -lt 3 ]]; then
    echo "usage: pre_gate.sh <candidate_worktree> <base_ref> <piece_ids> [<test path> ...]" >&2
    exit 2
fi
if [[ ! -d "$1" ]]; then
    echo "pre_gate.sh: candidate worktree not found: $1" >&2
    exit 2
fi

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WT="$(cd "$1" && pwd)"
BASE="$2"
PIECES="$3"
shift 3
VENV_PYTHON="${PRE_GATE_PYTHON:-$HOME/Projects/ouroboros-manifold/.venv/bin/python}"
MERGE_GATE="${PRE_GATE_MERGE_GATE:-$HERE/merge_gate.sh}"

# A pre-gate dry run must write no gate row (HARNESS-mm-7, method rev 3 A6).
export MERGE_GATE_RUNS_CSV=/dev/null
REJECTED=0
OUT="$(mktemp -d -t pre_gate.XXXXXX)"
trap 'rm -rf "$OUT"' EXIT

# ---- (1) noise ---------------------------------------------------------------
# NOTE-uid-files: an untracked or added <name>.gd.uid is fine when <name>.gd is
# added (A) in the diff. -uall so a .uid inside an untracked directory shows.
diff_status="$(git -C "$WT" diff --name-status "$BASE"...HEAD 2>/dev/null)"
added_gd="$(printf '%s\n' "$diff_status" | awk -F'\t' '$1 == "A" {print $2}')"
offenders=()

while IFS= read -r line; do
    [[ -z "$line" ]] && continue
    xy="${line:0:2}"
    rest="${line:3}"
    paths=()
    if [[ "$rest" == *" -> "* ]]; then
        paths+=("${rest%% -> *}" "${rest##* -> }")
    else
        paths+=("$rest")
    fi
    for p in "${paths[@]}"; do
        p="${p#\"}"; p="${p%\"}"
        case "$p" in
            *.uid)
                ok=0
                if [[ "$p" == *.gd.uid && ( "$xy" == "??" || "${xy:0:1}" == "A" ) ]]; then
                    if printf '%s\n' "$added_gd" | grep -Fxq -- "${p%.uid}"; then ok=1; fi
                fi
                [[ $ok -eq 0 ]] && offenders+=("$p")
                ;;
            *.import) offenders+=("$p") ;;
        esac
    done
done < <(git -C "$WT" status --porcelain -uall 2>/dev/null)

while IFS=$'\t' read -r st path _; do
    [[ "$st" == D* && "$path" == *.import ]] && offenders+=("$path (deleted in diff)")
done <<< "$diff_status"

if (( ${#offenders[@]} )); then
    echo "PRE_GATE noise REJECT ${offenders[*]}"
    REJECTED=1
else
    echo "PRE_GATE noise OK no .uid or .import noise"
fi

# ---- (2) gate ----------------------------------------------------------------
"$MERGE_GATE" --revert "$WT" "$BASE" "$PIECES"
grc=$?
if (( grc != 0 )); then
    echo "PRE_GATE gate REJECT merge_gate.sh --revert exit $grc"
    REJECTED=1
else
    echo "PRE_GATE gate OK merge_gate.sh --revert exit 0"
fi

# ---- (3) tests ---------------------------------------------------------------
# H-006: the story file's `Tests:` paths run as the piece's own tests when none are given. The story id is the first id.
# See also: merge_gate_support.py story_tests, docs/stories/H-006.md
STORY_FILE="$WT/docs/stories/${PIECES%%,*}.md"
if [[ -f "$STORY_FILE" ]]; then
    mapfile -t story_tests < <("$VENV_PYTHON" -c 'import sys; sys.path.insert(0, sys.argv[1]); import merge_gate_support as m; print(*m.story_tests(sys.argv[2]), sep="\n")' "$HERE" "$STORY_FILE")
    [[ "${story_tests[0]:-}" == "" ]] && story_tests=()
    echo "PREGATE story OK ${#story_tests[@]} paths"
    (( $# == 0 )) && set -- ${story_tests[@]+"${story_tests[@]}"}
fi
if (( $# == 0 )); then
    echo "PRE_GATE tests WARN no tests given"
else
    for t in "$@"; do
        log="$OUT/test.log"
        if [[ "$t" == *.gd ]]; then
            (cd "$WT" && timeout 1800 scripts/run_godot_tests.sh "$t") >"$log" 2>&1
        elif [[ "$t" == tests/qa/desktop* ]]; then
            (cd "$WT" && PYTHONDONTWRITEBYTECODE=1 xvfb-run -a "$VENV_PYTHON" -m pytest "$t" -q -x -p no:cacheprovider) >"$log" 2>&1
        else
            (cd "$WT" && PYTHONDONTWRITEBYTECODE=1 "$VENV_PYTHON" -m pytest "$t" -q -x -p no:cacheprovider) >"$log" 2>&1
        fi
        trc=$?
        last="$(grep -v '^[[:space:]]*$' "$log" | tail -n 1)"
        if (( trc != 0 )); then
            echo "PRE_GATE tests REJECT $t exit $trc: $last"
            REJECTED=1
        else
            echo "PRE_GATE tests OK $t: $last"
        fi
    done
fi

# ---- (3b) csrc pins ----------------------------------------------------------
# HARNESS-pregate-pins (H-017): a csrc/ change in the diff builds pipe/ouroboros_pipe and runs the csim files
# that carry pinned values, so a moved golden rejects here and not in a full gate. The list is grep-derived.
# Writes pipe/ouroboros_pipe in <wt> (the build output). DRAFT-pregate-pins-timeout-s 600 bounds build and run.
# See also: docs/northstar/plans/2026-10-29-layered-gate-spec.md section 9, docs/stories/H-017.md
if ! git -C "$WT" diff --name-only "$BASE"...HEAD 2>/dev/null | grep -q '^csrc/'; then
    echo "PREGATE pins skipped: no csrc change"
else
    mapfile -t pin_files < <(git -C "$WT" grep -l -E 'PINNED_FULL|FLYER_SECTIONS|GOLDEN_|save_sha256' -- tests/csim)
    plog="$OUT/pregate_pins.log"
    if (( ${#pin_files[@]} == 0 )); then
        echo "PREGATE pins REJECT no pinned csim files found"
        REJECTED=1
    elif ! (cd "$WT" && timeout 600 make pipe/ouroboros_pipe) >"$plog" 2>&1; then
        echo "PREGATE pins REJECT pipe/ouroboros_pipe build failed: $(tail -n 1 "$plog")"
        REJECTED=1
    else
        (cd "$WT" && PYTHONDONTWRITEBYTECODE=1 timeout 600 "$VENV_PYTHON" -m pytest "${pin_files[@]}" -q --tb=no -rfE -p no:cacheprovider) >"$plog" 2>&1
        prc=$?
        if (( prc == 124 )); then
            echo "PREGATE pins REJECT timeout 600 s"
            REJECTED=1
        elif (( prc != 0 )); then
            echo "PREGATE pins REJECT $(awk '/^(FAILED|ERROR) /{print $2}' "$plog" | paste -sd' ')"
            REJECTED=1
        else
            echo "PREGATE pins OK $(grep -Eo '[0-9]+ passed' "$plog" | tail -n 1 | cut -d' ' -f1) tests"
        fi
    fi
fi

# ---- (4) pins ----------------------------------------------------------------
# One PRE_GATE pins line per tool line; a failing tool is a reject.
# See also: rule_pins.py, rule_pins_tests.py, enforcement spec section 1 HARNESS-C1b
mapfile -t diff_files < <(git -C "$WT" diff --name-only "$BASE"...HEAD 2>/dev/null)

pins_step() {
    local rc
    "$@" >"$OUT/pins.log" 2>&1
    rc=$?
    while IFS= read -r l; do
        [[ "$l" == PINS\ * ]] && echo "PRE_GATE pins ${l#PINS }"
    done <"$OUT/pins.log"
    if (( rc != 0 )) && ! grep -q '^PINS REJECT' "$OUT/pins.log"; then
        echo "PRE_GATE pins REJECT $2 exit $rc: $(tail -n 1 "$OUT/pins.log")"
    fi
    return "$rc"
}
pins_step "$VENV_PYTHON" "$HERE/rule_pins_tests.py" check "$WT" --only ${diff_files[@]+"${diff_files[@]}"} || REJECTED=1
if (( REJECTED )); then
    echo "PRE_GATE verdict REJECT"
    exit 1
fi
echo "PRE_GATE verdict OK"
exit 0
