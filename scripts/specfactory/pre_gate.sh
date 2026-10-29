#!/usr/bin/env bash
# scripts/specfactory/pre_gate.sh <candidate_worktree> <base_ref> <piece_ids> [<test path> ...]
#
# Method rev 2, the two-tier gate: the cheap pre-gate a builder runs before the
# push and a landing clerk runs before taking gate.lock, so a full gate is never
# spent on noise, lint, footprint or owner-row rejects. Prints one line per step,
# `PRE_GATE <step> OK|REJECT|WARN <detail>`, and ends `PRE_GATE verdict OK`
# (exit 0) or `PRE_GATE verdict REJECT` (exit 1). Exit 2: usage.
# Steps: (1) noise (.uid / .import files in status or deleted .import in the
# diff), (2) gate (merge_gate.sh --revert, output passed through verbatim),
# (3) tests (each given .py / pytest id or .gd file), (4) pins (rule pins of the
# diff's tests and of the specs of the landing), (5) provenance (spec_provenance.py
# on the spec of every piece row; HARNESS-C1b, enforcement spec sections 1 and 2).
# Never takes ~/Projects/om-push/gate.lock, never pushes, never writes in <wt>.
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

# ---- (4) pins ----------------------------------------------------------------
# One PRE_GATE pins line per tool line; a failing tool is a reject. The specs come from `rule_pins.py spec-of`.
# See also: rule_pins.py, rule_pins_tests.py, enforcement spec section 1 HARNESS-C1b
PIECES_TOML="${MERGE_GATE_PIECES:-$WT/docs/northstar/plans/push/pieces.toml}"
IFS=, read -r -a piece_ids <<< "$PIECES"
spec_paths=()
if [[ -f "$PIECES_TOML" ]]; then
    mapfile -t spec_lines < <("$VENV_PYTHON" "$HERE/rule_pins.py" spec-of "$PIECES_TOML" "$PIECES")
    for i in "${!piece_ids[@]}"; do
        [[ "${spec_lines[$i]:--}" != "-" ]] && spec_paths+=("${spec_lines[$i]}")
    done
fi
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
if (( ${#spec_paths[@]} )); then
    (cd "$WT" && pins_step "$VENV_PYTHON" "$HERE/rule_pins.py" check "${spec_paths[@]}" --only ${diff_files[@]+"${diff_files[@]}"}) || REJECTED=1
fi

# ---- (5) provenance ----------------------------------------------------------
# A row without a spec key is a WARN; REJECT once FU-HARNESS-findings is attached (the C1b switch, as owner_lint reads it: bare string or inline table; See also: owner_lint.py:37-44).
# See also: spec_provenance.py (method rev 3). DRAFT-pregate-spec-env keeps PRE_GATE_SPEC as an extra path.
no_spec="WARN"
if [[ -f "$PIECES_TOML" ]] && "$VENV_PYTHON" -c 'import sys, tomllib; rows = tomllib.load(open(sys.argv[1], "rb")).get("piece", []); st = lambda r: (r.get("status") or {}).get("state") if isinstance(r.get("status"), dict) else r.get("status"); sys.exit(0 if any(r.get("id") == "FU-HARNESS-findings" and st(r) == "attached" for r in rows) else 1)' "$PIECES_TOML"; then
    no_spec="REJECT"
fi
if [[ ! -f "$PIECES_TOML" ]]; then
    echo "PRE_GATE provenance WARN no pieces file $PIECES_TOML"
else
    for i in "${!piece_ids[@]}"; do
        if [[ "${spec_lines[$i]:--}" == "-" ]]; then
            echo "PRE_GATE provenance $no_spec no spec key for ${piece_ids[$i]}"
            [[ "$no_spec" == REJECT ]] && REJECTED=1
        fi
    done
fi
all_specs=("${spec_paths[@]}")
[[ -n "${PRE_GATE_SPEC:-}" ]] && all_specs+=("$PRE_GATE_SPEC")
for spec in "${all_specs[@]}"; do
    if "$VENV_PYTHON" "$HERE/spec_provenance.py" "$WT/$spec" --pieces "$PIECES"; then
        echo "PRE_GATE provenance OK $spec"
    else
        echo "PRE_GATE provenance REJECT $spec"
        REJECTED=1
    fi
done

if (( REJECTED )); then
    echo "PRE_GATE verdict REJECT"
    exit 1
fi
echo "PRE_GATE verdict OK"
exit 0
