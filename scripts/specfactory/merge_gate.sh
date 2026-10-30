#!/usr/bin/env bash
# scripts/specfactory/merge_gate.sh [--revert] [--tier fast|slow|full] <candidate_worktree> <base_ref> <piece_id>[,...]
#
# F6 item 1 (two-day push, decision 8 "whole_suite"). Every step prints one
# line `GATE <step> OK|REJECT|WARN|HARNESS <detail>`. Exit codes: 0 every
# step OK/WARN, 1 at least one REJECT, 3 a harness error (make timeout or
# a real compile failure -- never counted as a regression, and the run stops
# immediately since nothing downstream is meaningful without a build).
#
# The tools this calls (libm_lint.py, alg_constants.py, merge_gate_support.py,
# checksum_trace.py, undertest_check.py, signatures.toml,
# symbol_modules.toml) always come from THIS repo (scripts/specfactory's own
# location) -- never from the candidate worktree, which cannot edit any of
# them. Only `make`, `pytest` and `git diff` run against the candidate.
#
# Stage 0 `base` runs first (also before the --revert exit): the candidate must
# contain the current origin/main, whose sha then replaces <base_ref> for every
# later stage. Env hook (tests only): MERGE_GATE_STOP_AFTER=base exits 0 right
# after the `GATE base OK` line. Other MERGE_GATE_* variables are read where used.
#
# Tiers (HARNESS-gate-tiers; the flags in either order before the three positionals; default full):
#   full  every stage, as before.
#   fast  the landing tier: the lints, acceptance (the piece's ids plus the test files the diff touches), transport and
#         the csim files `merge_gate_support.py select-csim` picks; skips regression_lab, regression_qa_t1,
#         the specfactory suite, playthrough, lane_plays, checksum_trace, tactical_trace, undertest_check, size_lint
#         and look. No stage is reordered.
#   slow  the sweep: every stage, with <base_ref> (the last green sweep's main sha) kept as the regression base and
#         the diff stages run over the union diff base...HEAD; the piece id is a comma list. A regression reject names
#         the first-parent landings since <base_ref>.
# `GATE tier <name>` is the first GATE line. See also: tests/specfactory/test_gate_tiers.py,
# Flag (HARNESS-gate-flag): the story's `Flag:` line (docs/stories/<id>.md on the candidate, `gate_flag.py story-impact`; H-006) adds the stage `flag` right after
#   make (`GATE flag SKIP revert mode` under --revert; a story file missing `Flag:` or `Tests:` is `GATE story REJECT missing <key>`). Without --tier an
#   explicit key picks the tier: sim and contract run `fast`; harness runs fast plus the specfactory suite and no csim or
#   transport; client runs fast plus playthrough, lane plays and qa/t1, transport only when the diff touches autoload/ or
#   tests/transport/, and no csim, lab or specfactory suite. --tier given wins. See also: tests/specfactory/test_gate_flag.py
# docs/northstar/plans/2026-10-29-layered-gate-spec.md section 8 B1
set -uo pipefail

GATE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$GATE_DIR/../.." && pwd)"
PYTHON="${MERGE_GATE_PYTHON:-/home/westopoli/Projects/agora/.venv/bin/python}"
SIGNATURES_TOML="${MERGE_GATE_SIGNATURES:-$REPO_ROOT/docs/northstar/spec_factory/signatures.toml}"
PLACEHOLDERS_TXT="${MERGE_GATE_PLACEHOLDERS:-$REPO_ROOT/docs/northstar/spec_factory/placeholder_controls.txt}"
SYMBOL_MODULES_TOML="$REPO_ROOT/docs/northstar/spec_factory/symbol_modules.toml"
MAKE_TIMEOUT="${MERGE_GATE_MAKE_TIMEOUT:-300}"
SUITE_TIMEOUT="${MERGE_GATE_SUITE_TIMEOUT:-2400}"

if [[ "${1:-}" == "--prune-evidence" && $# -eq 1 ]]; then
    exec "$PYTHON" "$GATE_DIR/merge_gate_support.py" prune-evidence
fi

REVERT_MODE=0
TIER=""
usage() {
    echo "usage: merge_gate.sh [--revert] [--tier fast|slow|full] <candidate_worktree> <base_ref> <piece_id>[,<piece_id>...]" >&2
    exit 2
}
while [[ $# -gt 0 ]]; do
    case "$1" in
        --revert) REVERT_MODE=1; shift ;;
        --tier) [[ $# -ge 2 ]] || usage; TIER="$2"; shift 2 ;;
        *) break ;;
    esac
done
case "${TIER:-full}" in fast|slow|full) ;; *) usage ;; esac
if [[ "$REVERT_MODE" -eq 1 && "${TIER:-full}" != full ]]; then
    usage
fi
TIER_GIVEN="$TIER"
TIER="${TIER:-full}"

if [[ $# -ne 3 ]]; then
    usage
fi
if [[ ! -d "$1" ]]; then
    echo "merge_gate.sh: candidate worktree not found: $1" >&2
    exit 2
fi

CANDIDATE="$(cd "$1" && pwd)"
BASE_REF="$2"
PIECE_ID="$3"
# Run directory name of the kept playthrough / lane_plays evidence (merge_gate_support.py _evidence_run_dir).
MERGE_GATE_START_UTC="$(date -u +%Y%m%d-%H%M)"
export MERGE_GATE_START_UTC
export MERGE_GATE_PIECE_ID="$PIECE_ID"

# merge_queue.py always checks a candidate out at <merge_root>/wt-<name>, so
# the candidate's own parent dir IS the runs/merge dir the gate never
# otherwise names -- reusable as the baseline-cache location without an
# agora-side change. See merge_gate_support.py's regression_check.
MERGE_ROOT="$(dirname "$CANDIDATE")"

SCRATCH_ROOT="$(mktemp -d -t merge_gate.XXXXXX)"
# GATE row (HARNESS-mm-2): one csv line per run on every exit, also appended to MERGE_GATE_RUNS_CSV.
# See also: docs/northstar/plans/method_rev3_2026-10-26/spec.md "Design" item 1, docs/northstar/plans/push/gate_runs.csv
ROW_STAGES=""
ROW_CAUSES=""
STAGE_SUM_DS=0
gate_row() {
    local rc="$1" cand base sums p t d l a n path
    cand="$(git -C "$CANDIDATE" rev-parse HEAD 2>/dev/null)"
    base="${MAIN_SHA:-}"
    p=0; t=0; d=0; l=0
    if [[ -n "$base" ]]; then
        while IFS=$'\t' read -r a n path; do
            [[ "$a" =~ ^[0-9]+$ ]] || continue
            case "$path" in
                csrc/*|autoload/*|scenes/*) p=$((p + a)) ;;
                scripts/skilllab/*) l=$((l + a)) ;;
                tests/*) t=$((t + a)) ;;
                docs/*) d=$((d + a)) ;;
            esac
        done < <(git -C "$CANDIDATE" diff --numstat "$base..$cand" 2>/dev/null)
    fi
    local row label="$PIECE_ID"
    if [[ "$label" == *[,\"]* ]]; then label="\"${label//\"/\"\"}\""; fi
    row="$(date +%F),$label,$(git -C "$CANDIDATE" rev-parse --abbrev-ref HEAD 2>/dev/null),$base,$cand,${MERGE_GATE_QUEUE_S:-0},$((STAGE_SUM_DS / 10)).$((STAGE_SUM_DS % 10)),$rc,$ROW_STAGES,$ROW_CAUSES,$p,$t,$d,$l"
    echo "GATE row $row"
    local csv="${MERGE_GATE_RUNS_CSV:-${HOME:-$SCRATCH_ROOT}/Projects/om-push/gate_runs.csv}"
    mkdir -p "$(dirname "$csv")"
    echo "$row" >>"$csv"
}
cleanup() {
    gate_row "$GATE_RC"
    [[ -d "$SCRATCH_ROOT/mainpipe_base" ]] && git -C "$CANDIDATE" worktree remove --force "$SCRATCH_ROOT/mainpipe_base" >/dev/null 2>&1
    rm -rf "$SCRATCH_ROOT"
}
trap 'GATE_RC=$?; cleanup' EXIT

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
    STAGE_SUM_DS=$((STAGE_SUM_DS + el))
    echo "GATE $name $status $detail [$((el / 10)).$((el % 10))s]"
}

reject() {
    local c="${*:2}"
    gate_line "$1" REJECT "$c"; REJECTED=1
    ROW_STAGES="${ROW_STAGES:+$ROW_STAGES;}$1"
    c="$(printf '%s' "$c" | tr ',"\n' '   ' | cut -c1-120)"
    ROW_CAUSES="${ROW_CAUSES:+$ROW_CAUSES;}$c"
}
# HARNESS-gate-reorder: the cheap, decisive stages run first; the first REJECT among them (or before them) ends the run
# here, before the regression block. Checks the global REJECTED flag; ROW_STAGES names every REJECTed stage so far.
# See also: tests/specfactory/test_gate_reorder.py
early_exit_if_rejected() {
    if [[ "$REJECTED" -eq 1 ]]; then
        gate_line early_exit REJECT "$ROW_STAGES"
        exit 1
    fi
}
# A suite_regression timeout surfaces as a TimeoutExpired traceback in the stage log; name it.
# See also: suite_regression.py main (suite-timeout <N>s), spec G06
reg_detail() { if grep -q TimeoutExpired "$1"; then echo "suite-timeout ${SUITE_TIMEOUT}s"; else cat "$1"; fi; }
ok()     { gate_line "$1" OK "${*:2}"; }
warn()   { gate_line "$1" WARN "${*:2}"; }
harness() { gate_line "$1" HARNESS "${*:2}"; }

tail_oneline() { tail -n "${2:-8}" "$1" 2>/dev/null | tr '\n' ' '; }

# HARNESS-gate-flag: the piece's `impact` key. rc 0 key valid, 2 value outside the four (the flag stage rejects), 3 no key.
# Without --tier, a valid key picks the tier; no key keeps today's default, full.
# H-006: the key is the `Flag:` line of docs/stories/<id>.md on the candidate (the story id is the piece id); no pieces.toml.
# See also: docs/stories/H-006.md, merge_gate_support.py story_flag
IMPACT=""
IMPACT_RC=3
STORY_BAD=""
if [[ "$REVERT_MODE" -eq 0 && -n "$PIECE_ID" ]]; then
    STORY_BAD="$("$PYTHON" "$GATE_DIR/merge_gate_support.py" story-check "$CANDIDATE" "$PIECE_ID" 2>&1 | tr '\n' ' ')"
    if [[ -z "$STORY_BAD" ]]; then
        IMPACT="$("$PYTHON" "$GATE_DIR/gate_flag.py" story-impact "$CANDIDATE/docs/stories/${PIECE_ID%%,*}.md" 2>"$SCRATCH_ROOT/impact.err")"
        IMPACT_RC=$?
        case "$IMPACT" in harness|client|sim|contract) ;; *) [[ "$IMPACT_RC" -eq 2 ]] || IMPACT_RC=3 ;; esac
    fi
fi
FLAG_PICKS=""
if [[ -z "$TIER_GIVEN" && "$IMPACT_RC" -eq 0 ]]; then
    TIER=fast
    case "$IMPACT" in harness|client) FLAG_PICKS="$IMPACT" ;; esac
fi
# Which suites run: the tier's, narrowed or widened by the flag when it picked the tier (diff = the client transport trigger).
RUN_PT=1; RUN_QA_T1=1; RUN_CSIM=1; RUN_LAB=1; RUN_SF=1; RUN_TRANSPORT=1
if [[ "$TIER" == fast ]]; then RUN_PT=0; RUN_QA_T1=0; RUN_LAB=0; RUN_SF=0; fi
case "$FLAG_PICKS" in
    harness) RUN_CSIM=0; RUN_SF=1; RUN_TRANSPORT=0 ;;
    client) RUN_PT=1; RUN_QA_T1=1; RUN_CSIM=0; RUN_TRANSPORT=diff ;;
esac

echo "GATE tier $TIER"

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
if [[ "$TIER" == slow ]]; then
    # B1: the slow tier's regression base is the positional <base_ref>, the last green sweep's main sha; the ancestry
    # rule above is unchanged. See also: tests/specfactory/test_gate_tiers.py group 8
    BASE_REF="$(git -C "$CANDIDATE" rev-parse --verify -q "$BASE_REF^{commit}")"
    if [[ -z "$BASE_REF" ]]; then
        reject base "slow tier base_ref not found in the candidate"
        exit 1
    fi
else
    BASE_REF="$MAIN_SHA"
fi
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

# -------------------------------------------------------------- 1a. story (H-006)
# A story file without `Flag:` or `Tests:` (or no file) rejects here and ends the run before the flag stage.
if [[ -n "$STORY_BAD" ]]; then
    reject story "$STORY_BAD"
    early_exit_if_rejected
fi

# -------------------------------------------------------------- 1b. flag (HARNESS-gate-flag)
# Layer 1 of the layered gate: the two determinism traces against the base and the diff footprint, judged by the piece's
# impact flag. See also: gate_flag.py verdict, tests/specfactory/test_gate_flag.py
if [[ "$REVERT_MODE" -eq 1 ]]; then
    gate_line flag SKIP "revert mode"
elif [[ -z "$PIECE_ID" ]]; then
    gate_line flag SKIP "no ids"
elif [[ -n "$TIER_GIVEN" ]]; then
    # DEC-gate-tier-given-skips-flag-2026-10-30: a given --tier means the caller chose the suites; no traces, no footprint.
    gate_line flag SKIP "tier given"
elif [[ "$IMPACT_RC" -eq 2 ]]; then
    reject flag "$(tail_oneline "$SCRATCH_ROOT/impact.err" 3)"
elif [[ "$IMPACT_RC" -ne 0 ]]; then
    gate_line flag SKIP "no flag (treated as sim); traces not checked"
else
    FLAG_LOG="$SCRATCH_ROOT/flag.log"
    "$PYTHON" "$GATE_DIR/gate_flag.py" verdict "$CANDIDATE" "$BASE_REF" "$IMPACT" \
        --merge-root "$MERGE_ROOT" --lib "$CANDIDATE/libouroboros.so" >"$FLAG_LOG" 2>"$SCRATCH_ROOT/flag.err"
    FLAG_RC=$?
    FLAG_LINE="$(grep -m1 '^flag ' "$FLAG_LOG")"
    [[ -n "$FLAG_LINE" ]] || FLAG_LINE="gate_flag.py failed: $(tail_oneline "$SCRATCH_ROOT/flag.err" 3)"
    if [[ "$FLAG_RC" -ne 0 ]]; then
        reject flag "$FLAG_LINE"
    else
        ok flag "$FLAG_LINE"
    fi
fi

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
if [[ -z "$PIECE_ID" ]]; then
    ok footprint "skipped: no ids"
else
    # H-006: a WARN for diff files outside the story's Files section, never a reject (DEC-ownership-by-conflict-2026-10-30).
    "$PYTHON" "$GATE_DIR/merge_gate_support.py" story-footprint "$CANDIDATE" "$BASE_REF" \
        "$CANDIDATE/docs/stories/${PIECE_ID%%,*}.md" >"$FP_LOG" 2>&1
    if [[ "$(head -c4 "$FP_LOG")" == "WARN" ]]; then
        warn footprint "$(sed 's/^WARN //' "$FP_LOG")"
    else
        ok footprint "$(cat "$FP_LOG")"
    fi
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

# `merge_cli.py revert`: only make, lints and footprint (decision 8: "no
# acceptance, no regression" -- a revert's job is to get main back to a
# known-good state fast, not to re-prove the piece it's undoing).
if [[ "$REVERT_MODE" -eq 1 ]]; then
    if [[ "$REJECTED" -eq 1 ]]; then
        exit 1
    fi
    exit 0
fi

# -------------------------------------------------------------- 5c-status. status (HARNESS-C1b; early block, HARNESS-gate-reorder)
# The status copies must agree (guard 7): any `STATUS <check> DRIFT` line rejects, a WARN warns. Reads THIS repo.
# --base is origin/main's sha in every tier: the slow tier's <base_ref> is the regression base only, and the sweep check
# reads its own anchor from sweeps.md. See also: status_check.py, pre_gate.sh
STATUS_LOG="$SCRATCH_ROOT/status.log"
"$PYTHON" "$GATE_DIR/status_check.py" --repo "$REPO_ROOT" --base "$MAIN_SHA" >"$STATUS_LOG" 2>&1
# H-014 (DEC-sweep-drift-warn-2026-10-30): `STATUS sweep DRIFT` (a sweep is due) is a WARN, since the sweep itself runs through
# this gate; a landing after a bad sweep is blocked by the last sweeps.md row being REJECT. See also: sweep.sh
SWEEP_ROW=$(grep '^|' "$REPO_ROOT/docs/northstar/plans/push/sweeps.md" 2>/dev/null | tail -1)
SWEEP_VERDICT=$(awk -F'|' '{v=$4; gsub(/ /,"",v); print v}' <<<"$SWEEP_ROW")
SWEEP_SHA=$(awk -F'|' '{s=$3; gsub(/ /,"",s); print s}' <<<"$SWEEP_ROW")
# DEC-sweep-fix-exemption-2026-10-30: the story whose `Fixes-sweep:` is the red row's swept sha may land on that red row.
STORY_FIXES=$(sed -n 's/^Fixes-sweep:[ \t]*//p' "$CANDIDATE/docs/stories/${PIECE_ID%%,*}.md" 2>/dev/null | tail -1)
if [[ "$SWEEP_VERDICT" == REJECT && -n "$STORY_FIXES" && "$STORY_FIXES" == "$SWEEP_SHA" ]]; then
    warn status "sweep red $(awk -F'|' '{r=$6; gsub(/[^0-9]/,"",r); print r}' <<<"$SWEEP_ROW") at $SWEEP_SHA fixed by ${PIECE_ID%%,*}"
elif [[ "$SWEEP_VERDICT" == REJECT ]]; then
    reject status "sweep red $(awk -F'|' '{r=$6; gsub(/[^0-9]/,"",r); print r}' <<<"$SWEEP_ROW") at $(awk -F'|' '{s=$3; gsub(/ /,"",s); print s}' <<<"$SWEEP_ROW")"
elif grep -q '^STATUS [a-z_]* DRIFT' "$STATUS_LOG" && grep '^STATUS [a-z_]* DRIFT' "$STATUS_LOG" | grep -qv '^STATUS sweep DRIFT'; then
    reject status "$(grep '^STATUS [a-z_]* DRIFT' "$STATUS_LOG" | grep -v '^STATUS sweep DRIFT' | tr '\n' ' ')"
elif grep -q '^STATUS [a-z_]* \(WARN\|DRIFT\)' "$STATUS_LOG"; then
    warn status "$(grep '^STATUS [a-z_]* \(WARN\|DRIFT\)' "$STATUS_LOG" | tr '\n' ' ')"
else
    ok status "$(tail_oneline "$STATUS_LOG" 1)"
fi

# -------------------------------------------------------------- 5c-pins. rule pins (HARNESS-C1b; full gate only)
# Single-owner pattern: tests changed by the diff and the specs of this piece. The pre-gate runs its own step, so a
# revert never reaches here. See also: pre_gate.sh step pins, rule_pins_tests.py, rule_pins.py
RP_LOG="$SCRATCH_ROOT/rule_pins.log"
mapfile -t RP_DIFF < <(git -C "$CANDIDATE" diff --name-only "$BASE_REF"...HEAD 2>/dev/null)
RP_RC=0
"$PYTHON" "$GATE_DIR/rule_pins_tests.py" check "$CANDIDATE" --only ${RP_DIFF[@]+"${RP_DIFF[@]}"} >"$RP_LOG" 2>&1 || RP_RC=1
# H-006: no spec-of read (it needed pieces.toml); the story file carries no spec pins.
RP_NOTE=""
RP_NOTE=" (spec pins skipped: no pieces table)"
if grep -q '^PINS REJECT' "$RP_LOG" || (( RP_RC != 0 )); then
    reject rule_pins "$(grep '^PINS REJECT' "$RP_LOG" | tr '\n' ' ')$(grep -q '^PINS REJECT' "$RP_LOG" || tail_oneline "$RP_LOG" 3)"
elif grep -q '^PINS WARN' "$RP_LOG"; then
    warn rule_pins "$(grep '^PINS WARN' "$RP_LOG" | tr '\n' ' ')$RP_NOTE"
else
    ok rule_pins "$(tail_oneline "$RP_LOG" 1)$RP_NOTE"
fi

# -------------------------------------------------------------- 5c. control liveness (A114): the attaching piece's own controls
CL_LOG="$SCRATCH_ROOT/control_liveness.log"
if [[ -z "$PIECE_ID" ]]; then
    ok control_liveness "skipped: no ids"
else
    "$PYTHON" "$GATE_DIR/merge_gate_support.py" control-liveness "$CANDIDATE" "$PIECE_ID" \
        --placeholders "$PLACEHOLDERS_TXT" --scratch-root "$SCRATCH_ROOT/liveness" \
        --python "$PYTHON" >"$CL_LOG" 2>&1
    if [[ $? -ne 0 ]]; then
        reject control_liveness "$(sed 's/^REJECT //' "$CL_LOG" | tr '\n' ' ')"
    else
        ok control_liveness "$(sed 's/^OK //' "$CL_LOG" | tr '\n' ' ')"
    fi
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

# -------------------------------------------------------------- 7. piece acceptance ids green
ACCEPT_SPLIT="$("$PYTHON" "$GATE_DIR/merge_gate_support.py" story-acceptance "$CANDIDATE" "$PIECE_ID" 2>/dev/null)"
ACCEPT_IDS="$(echo "$ACCEPT_SPLIT" | sed -n 's/^PY //p')"
GODOT_IDS="$(echo "$ACCEPT_SPLIT" | sed -n 's/^GD //p')"
if [[ "$TIER" == fast ]]; then
    # The fast tier's acceptance is the row's ids plus every test file under tests/ the diff touches (not the desktop
    # plays: no frame in this tier). See also: the HARNESS-gate-tiers paragraph of 2026-10-07-visible-game-spec.md
    while IFS= read -r CHANGED_TEST; do
        [[ -n "$CHANGED_TEST" && -f "$CANDIDATE/$CHANGED_TEST" && "$CHANGED_TEST" != tests/qa/desktop/* ]] || continue
        grep -qxF "$CHANGED_TEST" <<<"$ACCEPT_IDS" || ACCEPT_IDS="${ACCEPT_IDS:+$ACCEPT_IDS$'\n'}$CHANGED_TEST"
    done < <(git -C "$CANDIDATE" diff --name-only "$BASE_REF"...HEAD -- 'tests/*test_*.py')
fi
GODOT_COUNT="$(echo "$GODOT_IDS" | grep -c . || true)"

# -------------------------------------------------------------- 6c. godot import (desktop/scene acceptance only)
# A fresh candidate worktree has no .godot/imported cache; a desktop QA test
# (tests/qa/desktop/*) or a .gd acceptance id launches the real project and
# fails on missing imports before it ever reaches its own assertions
# (2026-09-22, C8's test_flow_spine.py failed in the gate while green in an
# imported checkout). Importing once here, before either acceptance step
# runs, fixes that; a csim-only piece has neither id shape and pays nothing.
NEED_GODOT_IMPORT=0
VENV_LINK_MADE=0
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
        # 2026-09-22). Link the harness venv in before importing. The link
        # stays through the acceptance and transport stages and the gate
        # removes it before the playthrough stage (ledger
        # FINDING-gate-venv-link-vs-fresh-checkout: the playthrough's
        # test_fresh_checkout_boots_to_main_menu_without_numpy_or_logs
        # asserts the checkout has no .venv).
        # See also: "venv_unlink" block above "9b. playthrough" below;
        # tests/qa/desktop/test_fresh_checkout_boot.py.
        VENV_TARGET="${MERGE_GATE_VENV:-$HOME/Projects/agora/.venv}"
        if [[ ! -e "$CANDIDATE/.venv" ]]; then
            ln -s "$VENV_TARGET" "$CANDIDATE/.venv" && VENV_LINK_MADE=1
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
        # H-006: no pieces table, so no straggler-increment WARN: a red acceptance id rejects.
        reject acceptance "$(tail_oneline "$ACCEPT_LOG" 15)"
    else
        ok acceptance ""
    fi
elif [[ -n "$GODOT_IDS" ]]; then
    warn acceptance "no pytest acceptance ids; $GODOT_COUNT godot ids"
elif [[ -z "$PIECE_ID" ]]; then
    ok acceptance "skipped: no ids"
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
        FIRST_FAIL="$(grep -m1 '^FAIL: res://' "$GODOT_LOG")"
        reject acceptance_godot "${FIRST_FAIL:-$(tail_oneline "$GODOT_LOG" 10)}"
    fi
fi

# -------------------------------------------------------------- 8. tests/qa/t1 absolute run retired
# regression_qa_t1 (step 6) already compares the failing-id sets on base and
# candidate; an absolute run would reject every candidate while a fenced test
# for an unattached piece (Q2's detectors) is red on main by design.
ok qa_t1 "covered by regression_qa_t1"

# -------------------------------------------------------------- 9. tests/transport, if present and the pipe builds
# HARNESS-gate-concurrent: this early section only builds (the base-ref pipe worktree and the candidate pipes) and
# collects the warnings; the transport run and every `GATE transport` line belong to the concurrent block in section 6.
# See also: TRANSPORT_RUN and TRANSPORT_WARNS in section 6, tests/specfactory/test_gate_concurrent.py test_2, test_8
TRANSPORT_RUN=0
TRANSPORT_WARNS=()
if [[ "$RUN_TRANSPORT" == diff ]]; then
    RUN_TRANSPORT=0
    git -C "$CANDIDATE" diff --name-only "$BASE_REF"...HEAD | grep -qE '^(autoload/|tests/transport/)' && RUN_TRANSPORT=1
fi
if [[ "$RUN_TRANSPORT" -eq 0 ]]; then
    :  # the flag left transport out
elif [[ -d "$CANDIDATE/tests/transport" ]]; then
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
            TRANSPORT_WARNS+=("OM_MAIN_PIPE not set, base pipe did not build: $(tail_oneline "$SCRATCH_ROOT/mainpipe.log")")
        fi
    fi
    ( cd "$CANDIDATE" && timeout "$MAKE_TIMEOUT" make -s pipe/ouroboros_pipe ) >"$PIPE_LOG" 2>&1
    if [[ $? -eq 0 ]]; then
        PIPE_DBG_LOG="$SCRATCH_ROOT/pipe_dbg_build.log"
        ( cd "$CANDIDATE" && timeout "$MAKE_TIMEOUT" make -s pipe/ouroboros_pipe_dbg ) >"$PIPE_DBG_LOG" 2>&1
        if [[ $? -ne 0 ]]; then
            TRANSPORT_WARNS+=("pipe/ouroboros_pipe_dbg did not build: $(tail_oneline "$PIPE_DBG_LOG")")
        fi
        TRANSPORT_RUN=1
    else
        TRANSPORT_WARNS+=("pipe/ouroboros_pipe did not build: $(tail_oneline "$PIPE_LOG")")
    fi
else
    TRANSPORT_WARNS+=("no tests/transport directory in this candidate")
fi

# venv_unlink: remove the .venv link godot_import made (only the link; the
# target is untouched, a pre-existing .venv is never removed).
# See also: the venv_link comment in "6c. godot import" above; ledger
# FINDING-gate-venv-link-vs-fresh-checkout; tests/qa/desktop/test_fresh_checkout_boot.py.
if [[ "$VENV_LINK_MADE" -eq 1 && -L "$CANDIDATE/.venv" ]]; then
    rm -f "$CANDIDATE/.venv"
    echo "ok venv_unlink \"$VENV_TARGET\""
fi

# The fast tier skips playthrough and lane_plays (no frame in that tier) unless the client flag picked it; `fi` follows lane_plays.
if [[ "$RUN_PT" -eq 1 ]]; then
# -------------------------------------------------------------- 9b. playthrough (desktop flow suite, real client under xvfb)
# Runs on the merged tree only when the diff touches game code; red outside
# playthrough_known_red.txt rejects. See merge_gate_support.py playthrough_check.
PT_LOG="$SCRATCH_ROOT/playthrough.log"
"$PYTHON" "$GATE_DIR/merge_gate_support.py" playthrough "$CANDIDATE" "$BASE_REF" \
    --python "$PYTHON" --timeout "${MERGE_GATE_PLAYTHROUGH_TIMEOUT:-900}" >"$PT_LOG" 2>&1
if [[ $? -ne 0 ]]; then
    reject playthrough "$(sed -e '/^EVIDENCE /d' -e 's/^REJECT //' "$PT_LOG" | tr '\n' ' ')"
    sed -n 's/^EVIDENCE /GATE evidence kept: /p' "$PT_LOG"
else
    ok playthrough "$(sed 's/^OK //' "$PT_LOG" | tr '\n' ' ')"
fi

# -------------------------------------------------------------- 9b. lane_plays (per-lane desktop plays, real client under xvfb)
# Runs the plays of each lane whose globs (lane_plays.toml) the diff touches; red outside
# lane_plays_known_red.txt rejects. Shared paths (lane_plays.toml [shared]) run the lanes listed there. See merge_gate_support.py lane_plays_check.
LP_LOG="$SCRATCH_ROOT/lane_plays.log"
"$PYTHON" "$GATE_DIR/merge_gate_support.py" lane_plays "$CANDIDATE" "$BASE_REF" \
    --python "$PYTHON" --timeout "${MERGE_GATE_PLAY_TIMEOUT:-900}" >"$LP_LOG" 2>&1
if [[ $? -ne 0 ]]; then
    reject lane_plays "$(sed -e '/^EVIDENCE /d' -e 's/^REJECT //' "$LP_LOG" | tr '\n' ' ')"
    sed -n 's/^EVIDENCE /GATE evidence kept: /p' "$LP_LOG"
elif grep -q '^OK skipped' "$LP_LOG"; then
    warn lane_plays "$(sed 's/^OK //' "$LP_LOG" | tr '\n' ' ')"
else
    ok lane_plays "$(sed 's/^OK //' "$LP_LOG" | tr '\n' ' ')"
fi
fi

early_exit_if_rejected

# -------------------------------------------------------------- 6. suite_regression: qa/t1 alone, then csim, transport, lab and specfactory side by side
# HARNESS-gate-concurrent. qa/t1 runs first and alone (its WALL_BUDGET detector shares CPU badly); then the four other
# suites run as background jobs, each with its own log $SCRATCH_ROOT/regression_<suite>.log, TMPDIR $SCRATCH_ROOT/<suite>
# and XDG_DATA_HOME $SCRATCH_ROOT/<suite>/xdg. `wait` precedes the first reject/ok line of the block; the verdict lines
# print after it in a fixed order (transport, csim, lab, specfactory), each with its own log. Each suite's base and
# candidate passes run side by side inside merge_gate_support.py regression_check; the libs were built once in
# section 1, so the self-building conftests of csim and qa/t1 find them up to date.
# See also: tests/specfactory/test_gate_concurrent.py, docs/northstar/plans/harness/gate-parallel-scout.md design B
job_dirs() {
    mkdir -p "$SCRATCH_ROOT/$1/xdg/godot"
    if [[ -n "${HOME:-}" && -d "$HOME/.local/share/godot/export_templates" ]]; then
        ln -sfn "$HOME/.local/share/godot/export_templates" "$SCRATCH_ROOT/$1/xdg/godot/export_templates"
    fi
}

# The fast tier runs neither qa/t1, lab nor specfactory, and csim only on the selected files (`select-csim`).
# A slow-tier reject names the first-parent landings since <base_ref>. See also: tests/specfactory/test_gate_tiers.py
slow_landings() {
    [[ "$TIER" == slow ]] || return 0
    printf '; landings since %s: %s' "${BASE_REF:0:12}" \
        "$(git -C "$CANDIDATE" log --first-parent --format=%h "$BASE_REF..$MAIN_SHA" 2>/dev/null | tr '\n' ' ')"
}

if [[ "$RUN_QA_T1" -eq 1 ]]; then
    job_dirs qa_t1
    REG_QA_LOG="$SCRATCH_ROOT/regression_qa_t1.log"
    TMPDIR="$SCRATCH_ROOT/qa_t1" XDG_DATA_HOME="$SCRATCH_ROOT/qa_t1/xdg" \
    "$PYTHON" "$GATE_DIR/merge_gate_support.py" regression "$CANDIDATE" "$BASE_REF" tests/qa/t1 \
        --python "$PYTHON" --timeout "$SUITE_TIMEOUT" --merge-root "$MERGE_ROOT" >"$REG_QA_LOG" 2>&1
    if [[ $? -ne 0 ]]; then
        reject regression_qa_t1 "$(reg_detail "$REG_QA_LOG")$(slow_landings)"
    else
        ok regression_qa_t1 "$(cat "$REG_QA_LOG")"
    fi
fi

# MALLOC_PERTURB_=255 fills freed and fresh heap so a read of uninitialised memory fails the same way on every run;
# the baseline run and the branch run both inherit it.
# MALLOC_PERTURB_ is also in the baseline cache key. See also: MALLOC_PERTURB_ in merge_gate_support.py regression_check
# The csim stage runs under pytest-xdist (DRAFT-xdist-workers = 5); MERGE_GATE_CSIM_XDIST=0 runs the serial command
# (the first gate after HARNESS-csim-xdist lands seeds its serial baseline that way). Same switch on the transport stage.
# See also: tests/csim/conftest.py pytest_configure, the xdist branch is the last one so the call reader finds it
job_dirs csim
job_dirs lab
job_dirs specfactory
CSIM_ARGS=(tests/csim)
CSIM_SKIPPED=""
if [[ "$TIER" == fast && "$RUN_CSIM" -eq 1 ]]; then
    CSIM_SELECTION="$("$PYTHON" "$GATE_DIR/merge_gate_support.py" select-csim "$CANDIDATE" "$BASE_REF" \
        --signatures "$SIGNATURES_TOML" --symbol-modules "$SYMBOL_MODULES_TOML")" \
        || { harness regression_csim "select-csim failed"; exit 3; }
    if [[ -n "$CSIM_SELECTION" ]]; then
        mapfile -t CSIM_ARGS <<<"$CSIM_SELECTION"
    else
        CSIM_SKIPPED="skipped: no csrc change"
    fi
fi
REG_CSIM_LOG="$SCRATCH_ROOT/regression_csim.log"
REG_CSIM_PID=""
if [[ "$RUN_CSIM" -eq 0 || -n "$CSIM_SKIPPED" ]]; then
    :
elif [[ "$TIER" == fast ]]; then
    # The selected files run under the same xdist switch as the full suite.
    CSIM_XDIST=(--pytest-extra '-n 5 --dist loadfile')
    [[ "${MERGE_GATE_CSIM_XDIST:-}" == 0 ]] && CSIM_XDIST=()
    # The support path sits in a variable so the call readers of test_csim_xdist.py and test_gate_cache_seed.py, which
    # key the full-suite calls by their literal `tests/<dir>` argument, do not take this selected-files call for one.
    SUPPORT_PY="$GATE_DIR/merge_gate_support.py"
    TMPDIR="$SCRATCH_ROOT/csim" XDG_DATA_HOME="$SCRATCH_ROOT/csim/xdg" \
    MALLOC_PERTURB_=255 "$PYTHON" "$SUPPORT_PY" regression "$CANDIDATE" "$BASE_REF" "${CSIM_ARGS[@]}" \
        --python "$PYTHON" --timeout "$SUITE_TIMEOUT" --merge-root "$MERGE_ROOT" "${CSIM_XDIST[@]}" >"$REG_CSIM_LOG" 2>&1 &
    REG_CSIM_PID=$!
elif [[ "${MERGE_GATE_CSIM_XDIST:-}" == 0 ]]; then
    TMPDIR="$SCRATCH_ROOT/csim" XDG_DATA_HOME="$SCRATCH_ROOT/csim/xdg" \
    MALLOC_PERTURB_=255 "$PYTHON" "$GATE_DIR/merge_gate_support.py" regression "$CANDIDATE" "$BASE_REF" tests/csim \
        --python "$PYTHON" --timeout "$SUITE_TIMEOUT" --merge-root "$MERGE_ROOT" >"$REG_CSIM_LOG" 2>&1 &
    REG_CSIM_PID=$!
else
    TMPDIR="$SCRATCH_ROOT/csim" XDG_DATA_HOME="$SCRATCH_ROOT/csim/xdg" \
    MALLOC_PERTURB_=255 "$PYTHON" "$GATE_DIR/merge_gate_support.py" regression "$CANDIDATE" "$BASE_REF" tests/csim \
        --python "$PYTHON" --timeout "$SUITE_TIMEOUT" --merge-root "$MERGE_ROOT" \
        --pytest-extra '-n 5 --dist loadfile' >"$REG_CSIM_LOG" 2>&1 &
    REG_CSIM_PID=$!
fi

REG_LAB_LOG="$SCRATCH_ROOT/regression_lab.log"
REG_LAB_PID=""
REG_SF_LOG="$SCRATCH_ROOT/regression_specfactory.log"
REG_SF_PID=""
if [[ "$RUN_LAB" -eq 1 ]]; then
    TMPDIR="$SCRATCH_ROOT/lab" XDG_DATA_HOME="$SCRATCH_ROOT/lab/xdg" \
    "$PYTHON" "$GATE_DIR/merge_gate_support.py" regression-lab "$CANDIDATE" "$BASE_REF" \
        --python "$PYTHON" --timeout "$SUITE_TIMEOUT" --merge-root "$MERGE_ROOT" >"$REG_LAB_LOG" 2>&1 &
    REG_LAB_PID=$!
fi
if [[ "$RUN_SF" -eq 1 ]]; then
    TMPDIR="$SCRATCH_ROOT/specfactory" XDG_DATA_HOME="$SCRATCH_ROOT/specfactory/xdg" \
    "$PYTHON" "$GATE_DIR/merge_gate_support.py" regression "$CANDIDATE" "$BASE_REF" tests/specfactory \
        --python "$PYTHON" --timeout "$SUITE_TIMEOUT" --merge-root "$MERGE_ROOT" >"$REG_SF_LOG" 2>&1 &
    REG_SF_PID=$!
fi

REG_TRANSPORT_LOG="$SCRATCH_ROOT/regression_transport.log"
REG_TRANSPORT_PID=""
if [[ "$TRANSPORT_RUN" -eq 1 ]]; then
    job_dirs transport
    if [[ "${MERGE_GATE_CSIM_XDIST:-}" == 0 ]]; then
        TMPDIR="$SCRATCH_ROOT/transport" XDG_DATA_HOME="$SCRATCH_ROOT/transport/xdg" \
        MALLOC_PERTURB_=255 "$PYTHON" "$GATE_DIR/merge_gate_support.py" regression "$CANDIDATE" "$BASE_REF" tests/transport \
            --python "$PYTHON" --timeout "$SUITE_TIMEOUT" --merge-root "$MERGE_ROOT" \
            --before-build "make -s pipe/ouroboros_pipe" >"$REG_TRANSPORT_LOG" 2>&1 &
    else
        TMPDIR="$SCRATCH_ROOT/transport" XDG_DATA_HOME="$SCRATCH_ROOT/transport/xdg" \
        MALLOC_PERTURB_=255 "$PYTHON" "$GATE_DIR/merge_gate_support.py" regression "$CANDIDATE" "$BASE_REF" tests/transport \
            --python "$PYTHON" --timeout "$SUITE_TIMEOUT" --merge-root "$MERGE_ROOT" \
            --before-build "make -s pipe/ouroboros_pipe" --pytest-extra '-n 2' >"$REG_TRANSPORT_LOG" 2>&1 &
    fi
    REG_TRANSPORT_PID=$!
fi

REG_CSIM_RC=0; REG_LAB_RC=0; REG_SF_RC=0; REG_TRANSPORT_RC=0
[[ -n "$REG_CSIM_PID" ]] && { wait "$REG_CSIM_PID"; REG_CSIM_RC=$?; }
[[ -n "$REG_LAB_PID" ]] && { wait "$REG_LAB_PID"; REG_LAB_RC=$?; }
[[ -n "$REG_SF_PID" ]] && { wait "$REG_SF_PID"; REG_SF_RC=$?; }
[[ -n "$REG_TRANSPORT_PID" ]] && { wait "$REG_TRANSPORT_PID"; REG_TRANSPORT_RC=$?; }

for ((i = 0; i < ${#TRANSPORT_WARNS[@]}; i++)); do
    warn transport "${TRANSPORT_WARNS[$i]}"
done
if [[ -n "$REG_TRANSPORT_PID" ]]; then
    if [[ "$REG_TRANSPORT_RC" -ne 0 ]]; then
        # --before-build (merge_gate_support.py's regression_check) builds pipe/ouroboros_pipe on the base-ref side
        # too, so a REJECT here means an id newly fails against a REAL main build, not the old skip(before) ->
        # fail(after) false positive from an unbuilt baseline (2026-09-24: B5-3, B9-1-2). Before piece T1 attaches,
        # main has no om_pipe.c at all and the before_build just fails; WARN until attach/T1 for that one case.
        if git -C "$CANDIDATE" tag -l 'attach/T1' | grep -q .; then
            reject transport "$(cat "$REG_TRANSPORT_LOG")$(slow_landings)"
        else
            warn transport "before attach/T1: $(cat "$REG_TRANSPORT_LOG")"
        fi
    else
        ok transport "$(cat "$REG_TRANSPORT_LOG")"
    fi
fi

if [[ "$RUN_CSIM" -eq 0 ]]; then
    :
elif [[ -n "$CSIM_SKIPPED" ]]; then
    ok regression_csim "$CSIM_SKIPPED"
elif [[ "$REG_CSIM_RC" -ne 0 ]]; then
    reject regression_csim "$(reg_detail "$REG_CSIM_LOG")$(slow_landings)"
else
    ok regression_csim "$(cat "$REG_CSIM_LOG")"
fi

if [[ "$RUN_LAB" -eq 1 ]]; then
    if [[ "$REG_LAB_RC" -ne 0 ]]; then
        reject regression_lab "$(reg_detail "$REG_LAB_LOG")$(slow_landings)"
    else
        ok regression_lab "$(cat "$REG_LAB_LOG")"
    fi
fi
if [[ "$RUN_SF" -eq 1 ]]; then
    if [[ "$REG_SF_RC" -ne 0 ]]; then
        reject specfactory_regression "$(reg_detail "$REG_SF_LOG" | tr '\n' ' ')$(slow_landings)"
    else
        ok specfactory_regression "$(cat "$REG_SF_LOG")"
    fi
fi

# The fast tier skips stages 10 to 13 (checksum_trace, tactical_trace, undertest_check, size_lint, look); `fi` before the exit.
if [[ "$TIER" != fast ]]; then
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
UT_OUT="undertest_check skipped: no ownership table (H-006)"
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
    --project "$CANDIDATE" >"$SIZE_LOG" 2>&1
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
fi

# --------------------------------------------------------------
if [[ "$REJECTED" -eq 1 ]]; then
    exit 1
fi
exit 0
