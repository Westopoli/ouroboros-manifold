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
#
# Stage 0 `base` runs first (also before the --revert exit): the candidate must
# contain the current origin/main, whose sha then replaces <base_ref> for every
# later stage. Env hook (tests only): MERGE_GATE_STOP_AFTER=base exits 0 right
# after the `GATE base OK` line. Other MERGE_GATE_* variables are read where used.
set -uo pipefail

GATE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$GATE_DIR/../.." && pwd)"
PYTHON="${MERGE_GATE_PYTHON:-/home/westopoli/Projects/agora/.venv/bin/python}"
PIECES_TOML="${MERGE_GATE_PIECES:-$REPO_ROOT/docs/northstar/plans/push/pieces.toml}"
SIGNATURES_TOML="${MERGE_GATE_SIGNATURES:-$REPO_ROOT/docs/northstar/spec_factory/signatures.toml}"
PLACEHOLDERS_TXT="${MERGE_GATE_PLACEHOLDERS:-$REPO_ROOT/docs/northstar/spec_factory/placeholder_controls.txt}"
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

# merge_queue.py always checks a candidate out at <merge_root>/wt-<name>, so
# the candidate's own parent dir IS the runs/merge dir the gate never
# otherwise names -- reusable as the baseline-cache location without an
# agora-side change. See merge_gate_support.py's regression_check.
MERGE_ROOT="$(dirname "$CANDIDATE")"

SCRATCH_ROOT="$(mktemp -d -t merge_gate.XXXXXX)"
cleanup() {
    [[ -d "$SCRATCH_ROOT/mainpipe_base" ]] && git -C "$CANDIDATE" worktree remove --force "$SCRATCH_ROOT/mainpipe_base" >/dev/null 2>&1
    rm -rf "$SCRATCH_ROOT"
}
trap cleanup EXIT

# FINDING-ambient-user-dir: no stage reads or writes the machine's ~/.local/share/data.
# project.godot's custom_user_dir_name="data" puts user:// at $XDG_DATA_HOME/data, so every
# stage inherits a scratch XDG_DATA_HOME (dies with SCRATCH_ROOT). Only the export templates
# are linked in (the headless export tests need them); nothing else lives under it.
# See also: scripts/run_godot_tests.sh, tests/qa/desktop/daemon_client.py
export XDG_DATA_HOME="$SCRATCH_ROOT/xdg"
mkdir -p "$SCRATCH_ROOT/xdg/godot"
if [[ -n "${HOME:-}" && -d "$HOME/.local/share/godot/export_templates" ]]; then
    ln -s "$HOME/.local/share/godot/export_templates" "$SCRATCH_ROOT/xdg/godot/export_templates"
fi

REJECTED=0

STAGE_MARK_US="${EPOCHREALTIME/./}"

gate_line() {
    local name="$1" status="$2" detail now_us el
    shift 2
    detail="$*"
    while [[ "$detail" == *$'\n' ]]; do detail="${detail%$'\n'}"; done
    now_us="${EPOCHREALTIME/./}"
    el=$(( (now_us - STAGE_MARK_US + 50000) / 100000 ))
    STAGE_MARK_US="$now_us"
    echo "GATE $name $status $detail [$((el / 10)).$((el % 10))s]"
}

reject() { gate_line "$1" REJECT "${*:2}"; REJECTED=1; }
ok()     { gate_line "$1" OK "${*:2}"; }
warn()   { gate_line "$1" WARN "${*:2}"; }
harness() { gate_line "$1" HARNESS "${*:2}"; }

tail_oneline() { tail -n "${2:-8}" "$1" 2>/dev/null | tr '\n' ' '; }

# -------------------------------------------------------------- 0. base
# The clerk merges origin/main inside gate.lock; a candidate gated against a main that has since
# moved fails tests that compare with main's build. The sha, not the name, is the baseline from here on.
# See also: docs/northstar/plans/workflows_2026-10-07/rules.md section (b) "Gate";
# ledger row FINDING-gate-base-before-lock
if ! git -C "$CANDIDATE" fetch -q origin >"$SCRATCH_ROOT/base_fetch.log" 2>&1; then
    reject base "git fetch origin failed: $(tail_oneline "$SCRATCH_ROOT/base_fetch.log" 3)"
    exit 1
fi
MAIN_SHA="$(git -C "$CANDIDATE" rev-parse --verify -q origin/main)"
if [[ -z "$MAIN_SHA" ]]; then
    reject base "origin/main not found in the candidate"
    exit 1
fi
if ! git -C "$CANDIDATE" merge-base --is-ancestor "$MAIN_SHA" HEAD; then
    reject base "candidate lacks origin/main $MAIN_SHA; merge origin/main inside the lock and rerun"
    exit 1
fi
ok base "$MAIN_SHA"
BASE_REF="$MAIN_SHA"
[[ "${MERGE_GATE_STOP_AFTER:-}" == "base" ]] && exit 0

# -------------------------------------------------------------- 1. make
if grep -q '\$(OPT)' "$CANDIDATE/Makefile" 2>/dev/null; then
    MAKE_ARGS=(OPT=-O2 WERROR=1)
else
    MAKE_OPT_WARN="Makefile does not reference \$(OPT) yet (F2 not landed); falling back to plain make"
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
[[ -n "${MAKE_OPT_WARN:-}" ]] && warn make "$MAKE_OPT_WARN"
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

ALGS_LOG="$SCRATCH_ROOT/allowlist_strict.log"
"$PYTHON" "$GATE_DIR/alg_constants.py" --lint "$CANDIDATE/csrc" --strict >"$ALGS_LOG" 2>&1
if [[ $? -ne 0 ]]; then
    reject allowlist_strict "$(grep '^STALE\|^FAIL' "$ALGS_LOG" | tr '\n' ';' | head -c 600)"
else
    ok allowlist_strict ""
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

# -------------------------------------------------------------- 4b. gd class_name uniqueness
GDCLS_LOG="$SCRATCH_ROOT/gd_class_names.log"
"$PYTHON" "$GATE_DIR/merge_gate_support.py" gd-class-names "$CANDIDATE" >"$GDCLS_LOG" 2>&1
if [[ $? -ne 0 ]]; then
    reject gd_class_names "$(head -n1 "$GDCLS_LOG")"
else
    ok gd_class_names "$(cat "$GDCLS_LOG")"
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

# -------------------------------------------------------------- 5a. signature table BLOCKED items
SIGB_LOG="$SCRATCH_ROOT/sig_blocked.log"
"$PYTHON" "$GATE_DIR/merge_gate_support.py" sig-blocked --project "$REPO_ROOT" \
    --table "$SIGNATURES_TOML" >"$SIGB_LOG" 2>&1
if [[ $? -ne 0 ]]; then
    reject sig_blocked "$(tr '\n' ' ' <"$SIGB_LOG")"
else
    ok sig_blocked "$(cat "$SIGB_LOG")"
fi

# -------------------------------------------------------------- 5a2. signature artifacts emit-clean (candidate's own table)
SIGC_LOG="$SCRATCH_ROOT/sig_check.log"
"$PYTHON" "$GATE_DIR/merge_gate_support.py" sig-check --project "$CANDIDATE" \
    --table "$CANDIDATE/docs/northstar/spec_factory/signatures.toml" >"$SIGC_LOG" 2>&1
if [[ $? -ne 0 ]]; then
    reject sig_check "$(tr '\n' ' ' <"$SIGC_LOG")"
else
    ok sig_check "$(cat "$SIGC_LOG")"
fi

# -------------------------------------------------------------- 5b. reachability lint
# Gap-fix plan (witty-cuddling-goblet.md, Wave 0 item 3): every tested public
# csrc/ouroboros_sim.h symbol must be reachable from a real tick/jump/pipe
# root, or allowlisted. Runs here, ahead of the REVERT_MODE early return
# below, so it is part of both this script's profiles: the full merge run,
# and the lighter revert/docs-shaped run that stops right after this block.
#
# --base-ref: regression mode, not absolute -- origin/main carries ~337
# pre-existing tested-but-unreachable symbols today (most of E-06..E-17 is
# real, tested, and simply not wired into a live path yet), and gating on
# the absolute count would reject every candidate against that baseline
# forever. Only a symbol newly unreachable in this candidate versus the
# rebased base (regressed, or new-and-unreachable) rejects, mirroring how
# regression_csim/regression_qa_t1 above compare failing-id sets rather than
# absolute pass/fail counts.
REACH_LOG="$SCRATCH_ROOT/reach_lint.log"
"$PYTHON" "$GATE_DIR/reach_lint.py" --ref "HEAD" --base-ref "$(git -C "$CANDIDATE" merge-base "$BASE_REF" HEAD 2>/dev/null || echo "$BASE_REF")" --project "$CANDIDATE" >"$REACH_LOG" 2>&1
if [[ $? -ne 0 ]]; then
    reject reach_lint "$(tail_oneline "$REACH_LOG" 10)"
else
    ok reach_lint "$(tail_oneline "$REACH_LOG" 1)"
fi

# -------------------------------------------------------------- 5b-gd. Godot reach lint (HARNESS-gdreach)
# Same regression mode as reach_lint: only a .gd newly unreachable from the main scene/autoloads rejects.
GDREACH_LOG="$SCRATCH_ROOT/gd_reach_lint.log"
"$PYTHON" "$GATE_DIR/gd_reach_lint.py" --ref "HEAD" --base-ref "$(git -C "$CANDIDATE" merge-base "$BASE_REF" HEAD 2>/dev/null || echo "$BASE_REF")" --project "$CANDIDATE" >"$GDREACH_LOG" 2>&1
if [[ $? -ne 0 ]]; then
    reject gd_reach "$(grep '^NEW UNREACHABLE' "$GDREACH_LOG" | tr '\n' ' ')"
else
    warn gd_reach "$(tail_oneline "$GDREACH_LOG" 1)"
fi

# -------------------------------------------------------------- 5c. single-owner lint
# Same gap-fix plan item: no file owned by two in-flight pieces. Reads
# THIS repo's own pieces.toml ($PIECES_TOML), never the candidate's copy
# (same rule this whole script follows for every other spec-factory tool).
OWNER_LOG="$SCRATCH_ROOT/owner_lint.log"
"$PYTHON" "$GATE_DIR/owner_lint.py" --pieces "$PIECES_TOML" >"$OWNER_LOG" 2>&1
if [[ $? -ne 0 ]]; then
    reject owner_lint "$(cat "$OWNER_LOG")"
else
    ok owner_lint "$(tail_oneline "$OWNER_LOG" 1)"
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

# -------------------------------------------------------------- 5c-pins. rule pins (HARNESS-C1b; full gate only)
# Single-owner pattern: tests changed by the diff and the specs of this piece. The pre-gate runs its own step, so a
# revert never reaches here. See also: pre_gate.sh step pins, rule_pins_tests.py, rule_pins.py
RP_LOG="$SCRATCH_ROOT/rule_pins.log"
mapfile -t RP_DIFF < <(git -C "$CANDIDATE" diff --name-only "$BASE_REF"...HEAD 2>/dev/null)
RP_RC=0
"$PYTHON" "$GATE_DIR/rule_pins_tests.py" check "$CANDIDATE" --only ${RP_DIFF[@]+"${RP_DIFF[@]}"} >"$RP_LOG" 2>&1 || RP_RC=1
RP_SPECS=()
while IFS= read -r sp_path; do
    [[ -f "$CANDIDATE/$sp_path" ]] && RP_SPECS+=("$sp_path")
done < <("$PYTHON" "$GATE_DIR/rule_pins.py" spec-of "$PIECES_TOML" "$PIECE_ID" 2>/dev/null)
if (( ${#RP_SPECS[@]} )); then
    (cd "$CANDIDATE" && "$PYTHON" "$GATE_DIR/rule_pins.py" check "${RP_SPECS[@]}" --only ${RP_DIFF[@]+"${RP_DIFF[@]}"}) >>"$RP_LOG" 2>&1 || RP_RC=1
fi
if grep -q '^PINS REJECT' "$RP_LOG" || (( RP_RC != 0 )); then
    reject rule_pins "$(grep '^PINS REJECT' "$RP_LOG" | tr '\n' ' ')$(grep -q '^PINS REJECT' "$RP_LOG" || tail_oneline "$RP_LOG" 3)"
elif grep -q '^PINS WARN' "$RP_LOG"; then
    warn rule_pins "$(grep '^PINS WARN' "$RP_LOG" | tr '\n' ' ')"
else
    ok rule_pins "$(tail_oneline "$RP_LOG" 1)"
fi

# -------------------------------------------------------------- 5c. control liveness (A114): the attaching piece's own controls
CL_LOG="$SCRATCH_ROOT/control_liveness.log"
"$PYTHON" "$GATE_DIR/merge_gate_support.py" control-liveness "$CANDIDATE" "$PIECE_ID" \
    --pieces "$PIECES_TOML" --placeholders "$PLACEHOLDERS_TXT" --scratch-root "$SCRATCH_ROOT/liveness" \
    --python "$PYTHON" >"$CL_LOG" 2>&1
if [[ $? -ne 0 ]]; then
    reject control_liveness "$(sed 's/^REJECT //' "$CL_LOG" | tr '\n' ' ')"
else
    ok control_liveness "$(sed 's/^OK //' "$CL_LOG" | tr '\n' ' ')"
fi

PC_LOG="$SCRATCH_ROOT/placeholder_controls.log"
"$PYTHON" "$GATE_DIR/merge_gate_support.py" placeholder-controls "$CANDIDATE" \
    --placeholders "$PLACEHOLDERS_TXT" >"$PC_LOG" 2>&1
if [[ $? -ne 0 ]]; then
    reject placeholder_controls "$(sed 's/^REJECT //' "$PC_LOG" | tr '\n' ' ')"
else
    ok placeholder_controls "$(sed 's/^OK //' "$PC_LOG" | tr '\n' ' ')"
fi

# -------------------------------------------------------------- 5d. pipe binary before the first regression stage
# See also: FINDING-ambient-user-dir; specfactory_regression boots Godot (test_gate_userdir test_6/6b) and needs pipe/ouroboros_pipe before it runs
# The transport stage (section 9) builds it again later; that make is then a no-op. A build
# failure is not rejected here: the transport stage reports it as it always did.
PRE_PIPE_LOG="$SCRATCH_ROOT/pipe_build_pre_regression.log"
( cd "$CANDIDATE" && timeout "$MAKE_TIMEOUT" make -s pipe/ouroboros_pipe ) >"$PRE_PIPE_LOG" 2>&1

# -------------------------------------------------------------- 6. suite_regression, tests/csim and tests/qa/t1 separately
REG_CSIM_LOG="$SCRATCH_ROOT/regression_csim.log"
"$PYTHON" "$GATE_DIR/merge_gate_support.py" regression "$CANDIDATE" "$BASE_REF" tests/csim \
    --python "$PYTHON" --timeout "$SUITE_TIMEOUT" --merge-root "$MERGE_ROOT" >"$REG_CSIM_LOG" 2>&1
if [[ $? -ne 0 ]]; then
    reject regression_csim "$(cat "$REG_CSIM_LOG")"
else
    ok regression_csim "$(cat "$REG_CSIM_LOG")"
fi

REG_LAB_LOG="$SCRATCH_ROOT/regression_lab.log"
"$PYTHON" "$GATE_DIR/merge_gate_support.py" regression-lab "$CANDIDATE" "$BASE_REF" \
    --python "$PYTHON" --timeout "$SUITE_TIMEOUT" --merge-root "$MERGE_ROOT" >"$REG_LAB_LOG" 2>&1
if [[ $? -ne 0 ]]; then
    reject regression_lab "$(cat "$REG_LAB_LOG")"
else
    ok regression_lab "$(cat "$REG_LAB_LOG")"
fi

REG_QA_LOG="$SCRATCH_ROOT/regression_qa_t1.log"
"$PYTHON" "$GATE_DIR/merge_gate_support.py" regression "$CANDIDATE" "$BASE_REF" tests/qa/t1 \
    --python "$PYTHON" --timeout "$SUITE_TIMEOUT" --merge-root "$MERGE_ROOT" >"$REG_QA_LOG" 2>&1
if [[ $? -ne 0 ]]; then
    reject regression_qa_t1 "$(cat "$REG_QA_LOG")"
else
    ok regression_qa_t1 "$(cat "$REG_QA_LOG")"
fi

REG_SF_LOG="$SCRATCH_ROOT/regression_specfactory.log"
"$PYTHON" "$GATE_DIR/merge_gate_support.py" regression "$CANDIDATE" "$BASE_REF" tests/specfactory \
    --python "$PYTHON" --timeout "$SUITE_TIMEOUT" --merge-root "$MERGE_ROOT" >"$REG_SF_LOG" 2>&1
if [[ $? -ne 0 ]]; then
    reject specfactory_regression "$(tr '\n' ' ' <"$REG_SF_LOG")"
else
    ok specfactory_regression "$(cat "$REG_SF_LOG")"
fi

# -------------------------------------------------------------- 7. piece acceptance ids green
ACCEPT_SPLIT="$("$PYTHON" "$GATE_DIR/merge_gate_support.py" acceptance-ids "$PIECE_ID" \
    --pieces "$PIECES_TOML" 2>/dev/null)"
ACCEPT_IDS="$(echo "$ACCEPT_SPLIT" | sed -n 's/^PY //p')"
GODOT_IDS="$(echo "$ACCEPT_SPLIT" | sed -n 's/^GD //p')"
GODOT_COUNT="$(echo "$GODOT_IDS" | grep -c . || true)"

# -------------------------------------------------------------- 6c. godot import (desktop/scene acceptance only)
# A fresh candidate worktree has no .godot/imported cache; a desktop QA test
# (tests/qa/desktop/*) or a .gd acceptance id launches the real project and
# fails on missing imports before it ever reaches its own assertions
# (2026-09-22, C8's test_flow_spine.py failed in the gate while green in an
# imported checkout). Importing once here, before either acceptance step
# runs, fixes that; a csim-only piece has neither id shape and pays nothing.
NEED_GODOT_IMPORT=0
if [[ -n "$GODOT_IDS" ]]; then
    NEED_GODOT_IMPORT=1
fi
while IFS= read -r ACCEPT_ID_LINE; do
    [[ -z "$ACCEPT_ID_LINE" ]] && continue
    if [[ "$ACCEPT_ID_LINE" == tests/qa/desktop/* ]]; then
        NEED_GODOT_IMPORT=1
    fi
done <<< "$ACCEPT_IDS"

if [[ "$NEED_GODOT_IMPORT" -eq 1 ]]; then
    GODOT_BIN=""
    if command -v godot >/dev/null 2>&1; then
        GODOT_BIN="godot"
    elif [[ -x "/Applications/Godot.app/Contents/MacOS/Godot" ]]; then
        GODOT_BIN="/Applications/Godot.app/Contents/MacOS/Godot"
    elif [[ -x "/Applications/Godot_mono.app/Contents/MacOS/Godot" ]]; then
        GODOT_BIN="/Applications/Godot_mono.app/Contents/MacOS/Godot"
    fi
    if [[ -z "$GODOT_BIN" ]]; then
        reject godot_import "godot binary not found (see scripts/run_godot_tests.sh lookup)"
    else
        # A fresh candidate worktree has no .venv; autoload/sim_bridge.gd
        # falls back to system python3, which has no numpy, so the sim dies
        # at import and every scene routes to error_screen (gate gap,
        # 2026-09-22). Link the harness venv in before importing; the
        # candidate worktree is discarded after the gate, so no cleanup.
        VENV_TARGET="${MERGE_GATE_VENV:-$HOME/Projects/agora/.venv}"
        if [[ ! -e "$CANDIDATE/.venv" ]]; then
            ln -s "$VENV_TARGET" "$CANDIDATE/.venv"
            echo "ok venv_link \"$VENV_TARGET\""
        fi
        run_godot_import() {
            timeout 300 env -u DISPLAY -u WAYLAND_DISPLAY -u XAUTHORITY \
                "$GODOT_BIN" --headless --path "$CANDIDATE" --import >"$1" 2>&1
        }
        # rc 124 (timeout) or rc >= 128 (killed by signal, e.g. 139 = SIGSEGV)
        # is Godot dying mid-reimport, not the candidate's code
        # (push_C7-2-20260924-092100.log line 23, "Segmentation fault (core
        # dumped)" rejected a candidate that had nothing wrong with it). A
        # plain nonzero exit (bad scene, real import error) is still the
        # candidate's fault and stays REJECT.
        is_signal_or_timeout() { [[ "$1" -eq 124 || "$1" -ge 128 ]]; }

        IMPORT_LOG="$SCRATCH_ROOT/godot_import.log"
        IMPORT_START=$(date +%s)
        run_godot_import "$IMPORT_LOG"
        IMPORT_RC=$?
        IMPORT_SECS=$(( $(date +%s) - IMPORT_START ))
        if [[ $IMPORT_RC -eq 0 ]]; then
            ok godot_import "${IMPORT_SECS}s"
        elif is_signal_or_timeout "$IMPORT_RC"; then
            # One retry after wiping the partial cache the crash/timeout left
            # behind, before deciding this is a harness fault.
            rm -rf "$CANDIDATE/.godot/imported"
            IMPORT_LOG2="$SCRATCH_ROOT/godot_import_retry.log"
            IMPORT_START=$(date +%s)
            run_godot_import "$IMPORT_LOG2"
            IMPORT_RC2=$?
            IMPORT_SECS=$(( $(date +%s) - IMPORT_START ))
            if [[ $IMPORT_RC2 -eq 0 ]]; then
                ok godot_import "${IMPORT_SECS}s (retry after rc=$IMPORT_RC, cache cleared)"
            elif is_signal_or_timeout "$IMPORT_RC2"; then
                harness godot_import "rc=$IMPORT_RC2 after retry (first rc=$IMPORT_RC): $(tail_oneline "$IMPORT_LOG2" 3)"
                exit 3
            else
                reject godot_import "retry rc=$IMPORT_RC2: $(tail_oneline "$IMPORT_LOG2" 15)"
            fi
        else
            reject godot_import "$(tail_oneline "$IMPORT_LOG" 15)"
        fi
    fi
fi

if [[ -n "$ACCEPT_IDS" ]]; then
    ACCEPT_LOG="$SCRATCH_ROOT/acceptance.log"
    ( cd "$CANDIDATE" && "$PYTHON" -m pytest -q -p no:cacheprovider $ACCEPT_IDS ) >"$ACCEPT_LOG" 2>&1
    if [[ $? -ne 0 ]]; then
        # A straggler increment (push/<piece>-<n>) submits before the rest of
        # its piece's acceptance is green; merge_gate_support.py resolves the
        # id and reports WARN with the green/red split instead of REJECT. A
        # full piece id (acceptance-verdict prints bare REJECT) keeps reject.
        IDS_FILE="$SCRATCH_ROOT/acceptance_ids.txt"
        printf '%s\n' $ACCEPT_IDS > "$IDS_FILE"
        VERDICT="$("$PYTHON" "$GATE_DIR/merge_gate_support.py" acceptance-verdict "$PIECE_ID" \
            --pieces "$PIECES_TOML" --ids-file "$IDS_FILE" --pytest-log "$ACCEPT_LOG")"
        if [[ "$VERDICT" == WARN* ]]; then
            warn acceptance "${VERDICT#WARN }"
        else
            reject acceptance "$(tail_oneline "$ACCEPT_LOG" 15)"
        fi
    else
        ok acceptance ""
    fi
elif [[ -n "$GODOT_IDS" ]]; then
    warn acceptance "no pytest acceptance ids; $GODOT_COUNT godot ids"
else
    warn acceptance "no pytest-collectible acceptance ids for piece $PIECE_ID"
fi

# -------------------------------------------------------------- 7b. piece acceptance ids, godot side
if [[ -n "$GODOT_IDS" ]]; then
    GODOT_LOG="$SCRATCH_ROOT/acceptance_godot.log"
    ( timeout "$SUITE_TIMEOUT" "$CANDIDATE/scripts/run_godot_tests.sh" $GODOT_IDS ) >"$GODOT_LOG" 2>&1
    if [[ $? -eq 0 ]]; then
        ok acceptance_godot "$(grep -c '^PASS: res://' "$GODOT_LOG") files PASS"
    else
        GD_IDS_FILE="$SCRATCH_ROOT/godot_ids.txt"
        printf '%s\n' $GODOT_IDS > "$GD_IDS_FILE"
        VERDICT="$("$PYTHON" "$GATE_DIR/merge_gate_support.py" acceptance-verdict "$PIECE_ID" \
            --pieces "$PIECES_TOML" --ids-file "$GD_IDS_FILE" --godot-log "$GODOT_LOG")"
        if [[ "$VERDICT" == WARN* ]]; then
            warn acceptance_godot "${VERDICT#WARN }"
        else
            FIRST_FAIL="$(grep -m1 '^FAIL: res://' "$GODOT_LOG")"
            reject acceptance_godot "${FIRST_FAIL:-$(tail_oneline "$GODOT_LOG" 10)}"
        fi
    fi
fi

# -------------------------------------------------------------- 8. tests/qa/t1 absolute run retired
# regression_qa_t1 (step 6) already compares the failing-id sets on base and
# candidate; an absolute run would reject every candidate while a fenced test
# for an unattached piece (Q2's detectors) is red on main by design.
ok qa_t1 "covered by regression_qa_t1"

# -------------------------------------------------------------- 9. tests/transport, if present and the pipe builds
if [[ -d "$CANDIDATE/tests/transport" ]]; then
    PIPE_LOG="$SCRATCH_ROOT/pipe_build.log"
    # See also: tests/transport/test_pipe_vg_identity.py skips without OM_MAIN_PIPE
    # Build base-ref's pipe once and export it so the candidate and base runs see the same env;
    # a separate baseline cache keeps skip counts cached without it from leaking in.
    if [[ -z "${OM_MAIN_PIPE:-}" ]]; then
        MAINPIPE_DIR="$SCRATCH_ROOT/mainpipe_base"
        if git -C "$CANDIDATE" worktree add --detach "$MAINPIPE_DIR" "$BASE_REF" >"$SCRATCH_ROOT/mainpipe.log" 2>&1 \
            && ( cd "$MAINPIPE_DIR" && timeout "$MAKE_TIMEOUT" make -s pipe/ouroboros_pipe ) >>"$SCRATCH_ROOT/mainpipe.log" 2>&1 \
            && [[ -x "$MAINPIPE_DIR/pipe/ouroboros_pipe" ]]; then
            export OM_MAIN_PIPE="$MAINPIPE_DIR/pipe/ouroboros_pipe"
            export MERGE_GATE_BASELINE_CACHE="${MERGE_GATE_BASELINE_CACHE:-$MERGE_ROOT/baseline_cache_mainpipe}"
            mkdir -p "$MERGE_GATE_BASELINE_CACHE"
        else
            warn transport "OM_MAIN_PIPE not set, base pipe did not build: $(tail_oneline "$SCRATCH_ROOT/mainpipe.log")"
        fi
    fi
    ( cd "$CANDIDATE" && timeout "$MAKE_TIMEOUT" make -s pipe/ouroboros_pipe ) >"$PIPE_LOG" 2>&1
    if [[ $? -eq 0 ]]; then
        PIPE_DBG_LOG="$SCRATCH_ROOT/pipe_dbg_build.log"
        ( cd "$CANDIDATE" && timeout "$MAKE_TIMEOUT" make -s pipe/ouroboros_pipe_dbg ) >"$PIPE_DBG_LOG" 2>&1
        if [[ $? -ne 0 ]]; then
            warn transport "pipe/ouroboros_pipe_dbg did not build: $(tail_oneline "$PIPE_DBG_LOG")"
        fi
        TRANSPORT_LOG="$SCRATCH_ROOT/transport.log"
        "$PYTHON" "$GATE_DIR/merge_gate_support.py" regression "$CANDIDATE" "$BASE_REF" tests/transport \
            --python "$PYTHON" --timeout "$SUITE_TIMEOUT" --merge-root "$MERGE_ROOT" \
            --before-build "make -s pipe/ouroboros_pipe" >"$TRANSPORT_LOG" 2>&1
        if [[ $? -ne 0 ]]; then
            # --before-build (merge_gate_support.py's regression_check) now
            # builds pipe/ouroboros_pipe on the base-ref side too, same as this
            # step already does for $CANDIDATE, so a REJECT here means an id
            # newly fails against a REAL main build, not the old skip(before)
            # -> fail(after) false positive from an unbuilt baseline
            # (2026-09-24: B5-3, B9-1-2 rejected on ids that pass clean against
            # a freshly built main). Before piece T1 attaches, main has no
            # om_pipe.c at all -- the before_build there just fails and the
            # base-ref worktree falls back to skipping, same as always; WARN
            # until attach/T1 for that one case.
            if git -C "$CANDIDATE" tag -l 'attach/T1' | grep -q .; then
                reject transport "$(cat "$TRANSPORT_LOG")"
            else
                warn transport "before attach/T1: $(cat "$TRANSPORT_LOG")"
            fi
        else
            ok transport "$(cat "$TRANSPORT_LOG")"
        fi
    else
        warn transport "pipe/ouroboros_pipe did not build: $(tail_oneline "$PIPE_LOG")"
    fi
else
    warn transport "no tests/transport directory in this candidate"
fi

# -------------------------------------------------------------- 9b. playthrough (desktop flow suite, real client under xvfb)
# Runs on the merged tree only when the diff touches game code; red outside
# playthrough_known_red.txt rejects. See merge_gate_support.py playthrough_check.
PT_LOG="$SCRATCH_ROOT/playthrough.log"
"$PYTHON" "$GATE_DIR/merge_gate_support.py" playthrough "$CANDIDATE" "$BASE_REF" \
    --python "$PYTHON" --timeout "${MERGE_GATE_PLAYTHROUGH_TIMEOUT:-900}" >"$PT_LOG" 2>&1
if [[ $? -ne 0 ]]; then
    reject playthrough "$(sed 's/^REJECT //' "$PT_LOG" | tr '\n' ' ')"
else
    ok playthrough "$(sed 's/^OK //' "$PT_LOG" | tr '\n' ' ')"
fi

# -------------------------------------------------------------- 9b. lane_plays (per-lane desktop plays, real client under xvfb)
# Runs the plays of each lane whose globs (lane_plays.toml) the diff touches; red outside
# lane_plays_known_red.txt rejects. See merge_gate_support.py lane_plays_check.
LP_LOG="$SCRATCH_ROOT/lane_plays.log"
"$PYTHON" "$GATE_DIR/merge_gate_support.py" lane_plays "$CANDIDATE" "$BASE_REF" \
    --python "$PYTHON" --timeout "${MERGE_GATE_PLAY_TIMEOUT:-900}" >"$LP_LOG" 2>&1
if [[ $? -ne 0 ]]; then
    reject lane_plays "$(sed 's/^REJECT //' "$LP_LOG" | tr '\n' ' ')"
elif grep -q '^OK skipped' "$LP_LOG"; then
    warn lane_plays "$(sed 's/^OK //' "$LP_LOG" | tr '\n' ' ')"
else
    ok lane_plays "$(sed 's/^OK //' "$LP_LOG" | tr '\n' ' ')"
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

# -------------------------------------------------------------- 10b. tactical_trace O0 vs O2
# Scripted mission plus scripted command stream, full checksums every tenth tick.
# See also: stage 10 above (strategic checksum_trace), scripts/specfactory/tactical_trace.py.
if grep -q '\$(OPT)' "$CANDIDATE/Makefile" 2>/dev/null; then
    if [[ -f "$CANDIDATE/build/O0/libouroboros.so" && -f "$CANDIDATE/build/O2/libouroboros.so" ]]; then
        TT_O0="$SCRATCH_ROOT/tactical_o0.txt"
        TT_O2="$SCRATCH_ROOT/tactical_o2.txt"
        ( cd "$CANDIDATE" && "$PYTHON" "$GATE_DIR/tactical_trace.py" \
            --lib build/O0/libouroboros.so --seed 1 --ticks 1500 ) >"$TT_O0" 2>&1
        TT_RC0=$?
        ( cd "$CANDIDATE" && "$PYTHON" "$GATE_DIR/tactical_trace.py" \
            --lib build/O2/libouroboros.so --seed 1 --ticks 1500 ) >"$TT_O2" 2>&1
        TT_RC2=$?
        if grep -q 'lacks om_world_checksum_full' "$TT_O0" "$TT_O2"; then
            warn tactical_trace "library lacks om_world_checksum_full; tactical O0 vs O2 comparison skipped"
        elif [[ $TT_RC0 -ne 0 || $TT_RC2 -ne 0 ]]; then
            reject tactical_trace "trace run failed: $(tail_oneline "$TT_O0") / $(tail_oneline "$TT_O2")"
        else
            TT_CMP="$SCRATCH_ROOT/tactical_compare.log"
            "$PYTHON" "$GATE_DIR/tactical_trace.py" --compare "$TT_O0" "$TT_O2" >"$TT_CMP" 2>&1
            if [[ $? -ne 0 ]]; then
                reject tactical_trace "$(cat "$TT_CMP")"
            else
                ok tactical_trace "$(cat "$TT_CMP")"
            fi
        fi
    else
        warn tactical_trace "build/O0 or build/O2 missing; tactical comparison skipped"
    fi
else
    warn tactical_trace "Makefile does not support OPT yet; tactical O0 vs O2 comparison skipped"
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

# -------------------------------------------------------------- 12. size_lint (WARN only, merge profile only)
# Gap-fix plan Wave 0 item 3: this step only runs past the REVERT_MODE
# early return above, so it is merge-profile-only by construction (a revert
# or a docs-profile run never reaches here). Always warn, never reject,
# regardless of size_lint.py's own exit code: --hard-cap-lines is off by
# default (Westley sets it later), and even once it is set, promoting a
# size finding from warn to reject in the live gate is his call to make
# separately, not something this wiring change decides on his behalf.
SIZE_LOG="$SCRATCH_ROOT/size_lint.log"
"$PYTHON" "$GATE_DIR/size_lint.py" HEAD "$BASE_REF" --piece-id "$PIECE_ID" \
    --pieces "$PIECES_TOML" --project "$CANDIDATE" >"$SIZE_LOG" 2>&1
warn size_lint "$(tail_oneline "$SIZE_LOG" 3)"

# -------------------------------------------------------------- 13. look (WARN only until Westley's threshold lands)
# Frames of the candidate vs main's at the same play moment, dirs from env;
# merge_gate_support.py look never rejects. See also: spec G1.
if [[ -d "${MERGE_GATE_LOOK_CANDIDATE:-}" && -d "${MERGE_GATE_LOOK_BASE:-}" ]]; then
    LOOK_LOG="$SCRATCH_ROOT/look.log"
    "$PYTHON" "$GATE_DIR/merge_gate_support.py" look "$MERGE_GATE_LOOK_CANDIDATE" "$MERGE_GATE_LOOK_BASE" >"$LOOK_LOG" 2>&1
    if [[ "$(head -c4 "$LOOK_LOG")" == "WARN" ]]; then
        warn look "$(sed 's/^WARN //' "$LOOK_LOG" | tr '\n' ' ')"
    else
        ok look "$(sed 's/^OK //' "$LOOK_LOG" | tr '\n' ' ')"
    fi
else
    warn look "no frame dirs (MERGE_GATE_LOOK_CANDIDATE / MERGE_GATE_LOOK_BASE unset); skipped"
fi

# -------------------------------------------------------------- 14. status (HARNESS-C1b)
# The status copies must agree (guard 7): any `STATUS <check> DRIFT` line rejects, a WARN warns. Reads THIS repo.
# See also: status_check.py, pre_gate.sh
STATUS_LOG="$SCRATCH_ROOT/status.log"
"$PYTHON" "$GATE_DIR/status_check.py" --repo "$REPO_ROOT" --base "$BASE_REF" >"$STATUS_LOG" 2>&1
if grep -q '^STATUS [a-z_]* DRIFT' "$STATUS_LOG"; then
    reject status "$(grep '^STATUS [a-z_]* DRIFT' "$STATUS_LOG" | tr '\n' ' ')"
elif grep -q '^STATUS [a-z_]* WARN' "$STATUS_LOG"; then
    warn status "$(grep '^STATUS [a-z_]* WARN' "$STATUS_LOG" | tr '\n' ' ')"
else
    ok status "$(tail_oneline "$STATUS_LOG" 1)"
fi

# --------------------------------------------------------------
if [[ "$REJECTED" -eq 1 ]]; then
    exit 1
fi
exit 0
