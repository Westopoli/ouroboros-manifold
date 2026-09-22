#!/usr/bin/env bash
# scripts/specfactory/merge_gate.sh <candidate_worktree> <base_ref> <piece_id>
#
# F6 item 1 (two-day push, decision 8 "whole_suite"). Every step prints one
# line `GATE <step> OK|REJECT|WARN|HARNESS <detail>`. Exit codes: 0 every
# step OK/WARN, 1 at least one REJECT, 3 a harness error (make timeout or
# a real compile failure -- never counted as a regression, and the run stops
# immediately since nothing downstream is meaningful without a build).
#
# The tools this calls (libm_lint.py, alg_constants.py, merge_gate_support.py,
# checksum_trace.py, undertest_check.py, pieces.toml, signatures.toml,
# symbol_modules.toml) always come from THIS repo (scripts/specfactory's own
# location) -- never from the candidate worktree, which cannot edit any of
# them. Only `make`, `pytest` and `git diff` run against the candidate.
set -uo pipefail

GATE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$GATE_DIR/../.." && pwd)"
PYTHON="${MERGE_GATE_PYTHON:-/home/westopoli/Projects/agora/.venv/bin/python}"
PIECES_TOML="${MERGE_GATE_PIECES:-$REPO_ROOT/docs/northstar/plans/push/pieces.toml}"
SIGNATURES_TOML="$REPO_ROOT/docs/northstar/spec_factory/signatures.toml"
SYMBOL_MODULES_TOML="$REPO_ROOT/docs/northstar/spec_factory/symbol_modules.toml"
MAKE_TIMEOUT="${MERGE_GATE_MAKE_TIMEOUT:-300}"
SUITE_TIMEOUT="${MERGE_GATE_SUITE_TIMEOUT:-600}"

REVERT_MODE=0
if [[ "${1:-}" == "--revert" ]]; then
    REVERT_MODE=1
    shift
fi

if [[ $# -ne 3 ]]; then
    echo "usage: merge_gate.sh [--revert] <candidate_worktree> <base_ref> <piece_id>[,<piece_id>...]" >&2
    exit 2
fi
if [[ ! -d "$1" ]]; then
    echo "merge_gate.sh: candidate worktree not found: $1" >&2
    exit 2
fi

CANDIDATE="$(cd "$1" && pwd)"
BASE_REF="$2"
PIECE_ID="$3"

SCRATCH_ROOT="$(mktemp -d -t merge_gate.XXXXXX)"
cleanup() { rm -rf "$SCRATCH_ROOT"; }
trap cleanup EXIT

REJECTED=0

gate_line() {
    local name="$1" status="$2"
    shift 2
    echo "GATE $name $status $*"
}

reject() { gate_line "$1" REJECT "${*:2}"; REJECTED=1; }
ok()     { gate_line "$1" OK "${*:2}"; }
warn()   { gate_line "$1" WARN "${*:2}"; }
harness() { gate_line "$1" HARNESS "${*:2}"; }

tail_oneline() { tail -n "${2:-8}" "$1" 2>/dev/null | tr '\n' ' '; }

# -------------------------------------------------------------- 1. make
if grep -q '\$(OPT)' "$CANDIDATE/Makefile" 2>/dev/null; then
    MAKE_ARGS=(OPT=-O2 WERROR=1)
else
    warn make "Makefile does not reference \$(OPT) yet (F2 not landed); falling back to plain make"
    MAKE_ARGS=()
fi

MAKE_LOG="$SCRATCH_ROOT/make.log"
timeout "$MAKE_TIMEOUT" make -s -C "$CANDIDATE" "${MAKE_ARGS[@]}" libouroboros.so libouroboros_dbg.so \
    >"$MAKE_LOG" 2>&1
MAKE_RC=$?
if [[ $MAKE_RC -eq 124 ]]; then
    harness make "make timed out after ${MAKE_TIMEOUT}s"
    exit 3
elif [[ $MAKE_RC -ne 0 ]]; then
    harness make "COMPILE ERROR (rc=$MAKE_RC): $(tail_oneline "$MAKE_LOG")"
    exit 3
fi
ok make ""

# -------------------------------------------------------------- 2. libm_lint
LIBM_LOG="$SCRATCH_ROOT/libm_lint.log"
"$PYTHON" "$GATE_DIR/libm_lint.py" "$CANDIDATE/csrc" >"$LIBM_LOG" 2>&1
if [[ $? -ne 0 ]]; then
    reject libm_lint "$(tail_oneline "$LIBM_LOG" 20)"
else
    ok libm_lint ""
fi

# -------------------------------------------------------------- 3. alg_constants --lint
ALG_LOG="$SCRATCH_ROOT/alg_constants.log"
"$PYTHON" "$GATE_DIR/alg_constants.py" --lint "$CANDIDATE/csrc" >"$ALG_LOG" 2>&1
if [[ $? -ne 0 ]]; then
    reject alg_constants "$(tail_oneline "$ALG_LOG" 20)"
else
    ok alg_constants ""
fi

# -------------------------------------------------------------- 4. footprint fence
FP_LOG="$SCRATCH_ROOT/footprint.log"
"$PYTHON" "$GATE_DIR/merge_gate_support.py" footprint "$CANDIDATE" "$BASE_REF" "$PIECE_ID" \
    --pieces "$PIECES_TOML" >"$FP_LOG" 2>&1
if [[ $? -ne 0 ]]; then
    reject footprint "$(cat "$FP_LOG")"
else
    ok footprint "$(cat "$FP_LOG")"
fi

# -------------------------------------------------------------- 5. symbol-ownership lint
SYM_LOG="$SCRATCH_ROOT/symbols.log"
"$PYTHON" "$GATE_DIR/merge_gate_support.py" symbols "$CANDIDATE" "$BASE_REF" \
    --signatures "$SIGNATURES_TOML" --symbol-modules "$SYMBOL_MODULES_TOML" >"$SYM_LOG" 2>&1
if [[ $? -ne 0 ]]; then
    reject symbol_ownership "$(cat "$SYM_LOG")"
else
    ok symbol_ownership "$(cat "$SYM_LOG")"
fi

# `merge_cli.py revert`: only make, lints and footprint (decision 8: "no
# acceptance, no regression" -- a revert's job is to get main back to a
# known-good state fast, not to re-prove the piece it's undoing).
if [[ "$REVERT_MODE" -eq 1 ]]; then
    if [[ "$REJECTED" -eq 1 ]]; then
        exit 1
    fi
    exit 0
fi

# -------------------------------------------------------------- 6. suite_regression, tests/csim and tests/qa/t1 separately
REG_CSIM_LOG="$SCRATCH_ROOT/regression_csim.log"
"$PYTHON" "$GATE_DIR/merge_gate_support.py" regression "$CANDIDATE" "$BASE_REF" tests/csim \
    --python "$PYTHON" --timeout "$SUITE_TIMEOUT" >"$REG_CSIM_LOG" 2>&1
if [[ $? -ne 0 ]]; then
    reject regression_csim "$(cat "$REG_CSIM_LOG")"
else
    ok regression_csim "$(cat "$REG_CSIM_LOG")"
fi

REG_QA_LOG="$SCRATCH_ROOT/regression_qa_t1.log"
"$PYTHON" "$GATE_DIR/merge_gate_support.py" regression "$CANDIDATE" "$BASE_REF" tests/qa/t1 \
    --python "$PYTHON" --timeout "$SUITE_TIMEOUT" >"$REG_QA_LOG" 2>&1
if [[ $? -ne 0 ]]; then
    reject regression_qa_t1 "$(cat "$REG_QA_LOG")"
else
    ok regression_qa_t1 "$(cat "$REG_QA_LOG")"
fi

# -------------------------------------------------------------- 7. piece acceptance ids green
ACCEPT_IDS="$("$PYTHON" -c "
import tomllib
d = tomllib.loads(open('$PIECES_TOML', 'rb').read().decode())
for p in d.get('piece', []):
    if p.get('id') == '$PIECE_ID':
        for a in p.get('acceptance') or []:
            if a.endswith('.py') or '::' in a or a in ('tests/transport', 'tests/qa/t1', 'tests/csim'):
                print(a)
" 2>/dev/null)"

if [[ -n "$ACCEPT_IDS" ]]; then
    ACCEPT_LOG="$SCRATCH_ROOT/acceptance.log"
    ( cd "$CANDIDATE" && "$PYTHON" -m pytest -q -p no:cacheprovider $ACCEPT_IDS ) >"$ACCEPT_LOG" 2>&1
    if [[ $? -ne 0 ]]; then
        reject acceptance "$(tail_oneline "$ACCEPT_LOG" 15)"
    else
        ok acceptance ""
    fi
else
    warn acceptance "no pytest-collectible acceptance ids for piece $PIECE_ID"
fi

# -------------------------------------------------------------- 8. pytest tests/qa/t1
QA_LOG="$SCRATCH_ROOT/qa_t1.log"
( cd "$CANDIDATE" && "$PYTHON" -m pytest tests/qa/t1 -q -p no:cacheprovider ) >"$QA_LOG" 2>&1
if [[ $? -ne 0 ]]; then
    reject qa_t1 "$(tail_oneline "$QA_LOG" 15)"
else
    ok qa_t1 ""
fi

# -------------------------------------------------------------- 9. tests/transport, if present and the pipe builds
if [[ -d "$CANDIDATE/tests/transport" ]]; then
    PIPE_LOG="$SCRATCH_ROOT/pipe_build.log"
    ( cd "$CANDIDATE" && timeout "$MAKE_TIMEOUT" make -s pipe/ouroboros_pipe ) >"$PIPE_LOG" 2>&1
    if [[ $? -eq 0 ]]; then
        TRANSPORT_LOG="$SCRATCH_ROOT/transport.log"
        ( cd "$CANDIDATE" && "$PYTHON" -m pytest tests/transport -q -p no:cacheprovider ) >"$TRANSPORT_LOG" 2>&1
        if [[ $? -ne 0 ]]; then
            reject transport "$(tail_oneline "$TRANSPORT_LOG" 15)"
        else
            ok transport ""
        fi
    else
        warn transport "pipe/ouroboros_pipe did not build: $(tail_oneline "$PIPE_LOG")"
    fi
else
    warn transport "no tests/transport directory in this candidate"
fi

# -------------------------------------------------------------- 10. checksum_trace O0 vs O2
if grep -q '\$(OPT)' "$CANDIDATE/Makefile" 2>/dev/null; then
    O0O2_LOG="$SCRATCH_ROOT/o0o2_build.log"
    ( cd "$CANDIDATE" && timeout "$MAKE_TIMEOUT" make -s build/O0/libouroboros.so build/O2/libouroboros.so ) \
        >"$O0O2_LOG" 2>&1
    if [[ $? -eq 0 ]]; then
        TRACE_O0="$SCRATCH_ROOT/trace_o0.txt"
        TRACE_O2="$SCRATCH_ROOT/trace_o2.txt"
        ( cd "$CANDIDATE" && "$PYTHON" "$GATE_DIR/checksum_trace.py" \
            --lib build/O0/libouroboros.so --seed 1 --regions 60 --ticks 500 --features 6 ) \
            >"$TRACE_O0" 2>&1
        ( cd "$CANDIDATE" && "$PYTHON" "$GATE_DIR/checksum_trace.py" \
            --lib build/O2/libouroboros.so --seed 1 --regions 60 --ticks 500 --features 6 ) \
            >"$TRACE_O2" 2>&1
        CMP_LOG="$SCRATCH_ROOT/compare.log"
        "$PYTHON" "$GATE_DIR/checksum_trace.py" --compare "$TRACE_O0" "$TRACE_O2" >"$CMP_LOG" 2>&1
        if [[ $? -ne 0 ]]; then
            reject checksum_trace "$(cat "$CMP_LOG")"
        else
            ok checksum_trace "$(cat "$CMP_LOG")"
        fi
    else
        warn checksum_trace "build/O0 or build/O2 did not build: $(tail_oneline "$O0O2_LOG")"
    fi
else
    warn checksum_trace "Makefile does not support OPT yet; O0 vs O2 comparison skipped"
fi

# -------------------------------------------------------------- 11. undertest_check (WARN only, never blocks)
UT_OUT="$("$PYTHON" -c "
import sys
sys.path.insert(0, '$GATE_DIR')
import merge_gate_support as m
for line in m.undertest_warn('$CANDIDATE', '$BASE_REF', '$PIECE_ID', pieces_path='$PIECES_TOML'):
    print(line)
" 2>&1)"
warn undertest_check "$(echo "$UT_OUT" | tr '\n' '; ')"

# --------------------------------------------------------------
if [[ "$REJECTED" -eq 1 ]]; then
    exit 1
fi
exit 0
