# Rule pins: docs/stories/H-014.md
"""H-014 (sweep-timer): "The full suite runs on main by itself after three landings, two hours, or nightly at 23:30, and
writes its row; I never ask for a sweep." Spec: docs/northstar/plans/2026-10-29-layered-gate-spec.md section 4,
HARNESS-sweep-timer, amended by section 8 (B2 row format and B3 landing ids; "where this section disagrees with sections
2 to 6, this section wins"). Red on the base because scripts/specfactory/sweep.sh, om-sweep.service and om-sweep.timer
do not exist.

INTERFACES FIXED HERE (the story leaves them open; the builder reads this file)
  sweep.sh locates its repo from its own path: <repo>/scripts/specfactory/sweep.sh, and calls <repo>/scripts/specfactory/
  wt.py and <repo>/scripts/specfactory/merge_gate.sh by that path (the fixture drops stubs of both beside the script).
  `wt.py new sweep-<UTC date-time> --owner sweep-timer --purpose "slow tier" ...` prints a line `WT OK <path> ...`; the
  sweep reads <path> from it. `wt.py done <path> <sha>` is called last.
  `sweep.sh --dry-run` prints exactly one stdout line, `... merge_gate.sh --tier slow <wt> <base sha> <ids>`, <ids> comma
  list (empty allowed); it pushes and records nothing.
  Land ids: from the subjects `Land <id>[,<id>] <sha>` of first-parent merges in <base sha>..origin/main, oldest first
  (section 8 B3 supersedes the paragraph's `attached` rows); a plain records commit or a branch-lineage commit is no landing.
  Row (section 8 B2): `| <UTC %Y-%m-%d %H:%M> | <main sha, 40 hex> | PASS|REJECT | new: <ids|none> | red: <n> | <ids> |`;
  new = the ids of the `GATE <stage> REJECT new failures: [...]` lines; red = the failing ids of every suite in
  <merge_root>/candidate_results/<main sha>.json (suites.<key>.failing_ids), merge_root = dirname of the sweep worktree.
  Commits on main, pushed to origin: the sweeps.md row, and an empty commit `Sweep <YYYY-MM-DD> pass` or
  `Sweep <YYYY-MM-DD> red <n>` (n = the red count of the row). Push under ~/Projects/om-push/records.lock, never gate.lock.
  The gate runs with MERGE_GATE_SUITE_TIMEOUT=2400 MERGE_GATE_PLAYTHROUGH_TIMEOUT=2400 MERGE_GATE_PLAY_TIMEOUT=900 and
  MERGE_GATE_PIECES set (rules.md (b), Gate bullet).

POSITIVE CONTROL (green today): `systemd-analyze verify` of the existing om-nightly-play.timer exits 0. (The control that
pinned status_check.check_sweep was deleted under H-034 Rulings A: H-002 retired it.)
"""
import fcntl
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
SPEC = REPO / "scripts" / "specfactory"
SWEEP = SPEC / "sweep.sh"
UNITS = SPEC / "systemd"
SWEEPS_REL = "docs/northstar/plans/push/sweeps.md"
HEADER = ("# Sweeps\n\n| Date-time UTC | Main sha | Verdict | New | Red | Red ids |\n|---|---|---|---|---|---|\n"
          "| 2026-10-29 21:10 | {base} | BASE | new: none | red: 0 | |\n")
TS = r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}"

STUB_WT = r'''#!/usr/bin/env python3
import os, subprocess, sys
from pathlib import Path
repo = Path(__file__).resolve().parents[2]
root = Path(os.environ["SWEEP_TEST_WT_ROOT"])
with open(root / "wt_calls.log", "a") as f:
    f.write(" ".join(sys.argv[1:]) + "\n")
if sys.argv[1] == "new":
    p = root / sys.argv[2]
    subprocess.run(["git", "-C", str(repo), "worktree", "add", "-q", "--detach", str(p), "origin/main"], check=True)
    print(f"WT OK {p} push/{sys.argv[2]} slots 1/12")
'''
STUB_GATE = r'''#!/bin/bash
# the test sets the verdict: STUB_GATE_LINES (printed), STUB_GATE_FAILING (json list for candidate_results), STUB_GATE_RC
root="$SWEEP_TEST_WT_ROOT"
{ echo "ARGS $*"; env | grep -E '^MERGE_GATE_' | sort; } >> "$root/gate_calls.log"
args=("$@"); wt=""
for ((i=0;i<${#args[@]};i++)); do [[ "${args[i]}" == --tier ]] && wt="${args[i+2]}"; done
sha=$(git -C "$wt" rev-parse HEAD)
# STUB_GATE_NO_RESULT=1: an early reject, which exits before merge_gate_support.py `_store_candidate_result` writes the file
if [[ -z "${STUB_GATE_NO_RESULT:-}" ]]; then
    mkdir -p "$(dirname "$wt")/candidate_results"
    printf '{"main_sha": "%s", "suites": {"regression_csim": {"failing_ids": %s}}}\n' "$sha" "${STUB_GATE_FAILING:-[]}" \
        > "$(dirname "$wt")/candidate_results/$sha.json"
fi
printf '%b' "${STUB_GATE_LINES:-}"
exit "${STUB_GATE_RC:-0}"
'''


def git(cwd, *a, check=True, env=None):
    r = subprocess.run(["git", "-C", str(cwd), *a], capture_output=True, text=True,
                       env={**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
                            "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t", **(env or {})})
    assert not check or r.returncode == 0, f"git {a}: {r.stderr}"
    return r.stdout.strip()


def build(tmp: Path, lands=("id1", "id2"), row_extra=""):
    """A fixture repo with origin: base commit A (the last PASS/BASE anchor of sweeps.md), a plain records commit, then one
    `Land <id> <sha>` --no-ff merge per id, then a plain records commit after the last landing. Returns the namespace."""
    origin = tmp / "origin.git"
    repo = tmp / "repo"
    subprocess.run(["git", "init", "-q", "--bare", "-b", "main", str(origin)], check=True)
    subprocess.run(["git", "clone", "-q", str(origin), str(repo)], check=True, capture_output=True)
    git(repo, "switch", "-q", "-c", "main")
    sdir = repo / "scripts" / "specfactory"
    sdir.mkdir(parents=True)
    (sdir / "wt.py").write_text(STUB_WT)
    (sdir / "merge_gate.sh").write_text(STUB_GATE)
    for f in ("wt.py", "merge_gate.sh"):
        (sdir / f).chmod(0o755)
    if SWEEP.exists():
        shutil.copy(SWEEP, sdir / "sweep.sh")
        (sdir / "sweep.sh").chmod(0o755)
    (repo / "docs/northstar/plans/push").mkdir(parents=True)
    (repo / "docs/northstar/plans/push/pieces.toml").write_text("")
    (repo / "README").write_text("base\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "base")
    a = git(repo, "rev-parse", "HEAD")
    (repo / SWEEPS_REL).write_text(HEADER.format(base=a) + row_extra)
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "Records: BASE row")
    for i in lands:
        git(repo, "switch", "-q", "-c", f"s/{i}")
        (repo / f"{i}.txt").write_text(i)
        git(repo, "add", "-A")
        git(repo, "commit", "-q", "-m", f"builder commit for {i}")
        c = git(repo, "rev-parse", "--short", "HEAD")
        git(repo, "switch", "-q", "main")
        git(repo, "merge", "-q", "--no-ff", "-m", f"Land {i} {c}", f"s/{i}")
    (repo / "notes.txt").write_text("records\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "Records: after the last landing")
    git(repo, "push", "-q", "origin", "main")
    git(repo, "fetch", "-q", "origin")
    wtroot = tmp / "wts"
    wtroot.mkdir()
    home = tmp / "home"
    (home / "Projects" / "om-push").mkdir(parents=True)
    return type("Fx", (), {"origin": origin, "repo": repo, "a": a, "wtroot": wtroot, "home": home,
                           "sweep": sdir / "sweep.sh"})


def run_sweep(fx, *args, lines="", failing="[]", rc=0, timeout=120, result=True):
    env = {**os.environ, "HOME": str(fx.home), "SWEEP_TEST_WT_ROOT": str(fx.wtroot), "STUB_GATE_LINES": lines,
           "STUB_GATE_FAILING": failing, "STUB_GATE_RC": str(rc), "STUB_GATE_NO_RESULT": "" if result else "1",
           "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}
    assert fx.sweep.exists(), f"missing {SWEEP.relative_to(REPO)}"
    return subprocess.run(["bash", str(fx.sweep), *args], cwd=fx.repo, env=env, capture_output=True, text=True,
                          timeout=timeout)


def origin_main(fx, rel=SWEEPS_REL):
    return git(fx.origin, "show", f"main:{rel}", check=False)


# --- (1), (2): the dry run -------------------------------------------------------------------------------------------

def test_1_dry_run_prints_the_slow_gate_line_with_the_landed_ids(tmp_path):
    """(1) "on a fixture repo with a `sweeps.md` whose last PASS is sha A and two attached rows after A, `sweep.sh
    --dry-run` prints the `merge_gate.sh --tier slow <wt> A <id1,id2>` line it would run and nothing else" (two `Land`
    merges after A stand for the two rows: section 8 B3)."""
    fx = build(tmp_path)
    r = run_sweep(fx, "--dry-run")
    assert r.returncode == 0, r.stderr
    out = r.stdout.strip().splitlines()
    assert len(out) == 1, f"expected one line, got {out!r}"
    assert re.search(rf"merge_gate\.sh --tier slow \S+ {fx.a} id1,id2$", out[0]), out[0]
    assert origin_main(fx) == HEADER.format(base=fx.a).rstrip("\n"), "a dry run must not touch sweeps.md"
    assert git(fx.origin, "log", "--format=%s", "-1") == "Records: after the last landing", "a dry run must not push"


def test_2_dry_run_with_no_landing_after_A_prints_an_empty_id_list(tmp_path):
    """(2) "with no attached row after A it prints the line with an empty id list"."""
    fx = build(tmp_path, lands=())
    r = run_sweep(fx, "--dry-run")
    assert r.returncode == 0, r.stderr
    out = r.stdout.strip().splitlines()
    assert len(out) == 1, out
    assert re.search(rf"merge_gate\.sh --tier slow \S+ {fx.a} ?$", out[0]), out[0]


def test_2b_the_anchor_is_the_last_pass_or_base_row_not_a_reject_row(tmp_path):
    """Rule pin, status_check.py `sweep` (spec section 8 F10): "treats the last PASS or BASE row as the anchor"; a REJECT
    row never moves the anchor, so ids landed before it are still listed."""
    fx = build(tmp_path)
    rej = f"| 2026-10-30 08:00 | {git(fx.repo, 'rev-parse', 'HEAD')} | REJECT | new: t::y | red: 1 | t::y |\n"
    (fx.repo / SWEEPS_REL).write_text((fx.repo / SWEEPS_REL).read_text() + rej)
    git(fx.repo, "add", "-A")
    git(fx.repo, "commit", "-q", "-m", "Records: REJECT row")
    git(fx.repo, "push", "-q", "origin", "main")
    git(fx.repo, "fetch", "-q", "origin")
    out = run_sweep(fx, "--dry-run").stdout.strip()
    assert re.search(rf"--tier slow \S+ {fx.a} id1,id2$", out), out


# --- (3), group 6: the row ---------------------------------------------------------------------------------------------

def test_3_rejecting_gate_log_gives_a_REJECT_row_naming_the_id(tmp_path):
    """(3) "a fixture gate log with one `GATE regression_csim REJECT new failures: ['t::x']` line yields a `sweeps.md`
    row ending `REJECT t::x`" (row form of section 8 B2: `| REJECT | new: t::x | red: 1 | t::x |`)."""
    fx = build(tmp_path)
    main_sha = git(fx.origin, "rev-parse", "main")
    r = run_sweep(fx, lines="GATE regression_csim REJECT new failures: ['t::x']\\n", failing="[\"t::x\"]", rc=1)
    assert r.returncode == 0, r.stderr
    last = origin_main(fx).rstrip("\n").splitlines()[-1]
    assert re.fullmatch(rf"\| {TS} \| {main_sha} \| REJECT \| new: t::x \| red: 1 \| t::x \|", last), last


def test_3b_clean_gate_log_gives_a_PASS_row_and_a_pass_commit(tmp_path):
    """(3) "a clean log yields `PASS`"; H-014: the sweep writes "an empty commit `Sweep <date> pass`"."""
    fx = build(tmp_path)
    main_sha = git(fx.origin, "rev-parse", "main")
    r = run_sweep(fx, lines="GATE tier slow OK\\n")
    assert r.returncode == 0, r.stderr
    last = origin_main(fx).rstrip("\n").splitlines()[-1]
    assert re.fullmatch(rf"\| {TS} \| {main_sha} \| PASS \| new: none \| red: 0 \| ? ?\|", last), last
    subjects = git(fx.origin, "log", "--format=%s", f"{main_sha}..main").splitlines()
    assert any(re.fullmatch(r"Sweep \d{4}-\d{2}-\d{2} pass", s) for s in subjects), subjects


def test_3c_reject_writes_the_red_n_commit(tmp_path):
    """H-014: the sweep writes "an empty commit whose subject is `Sweep <date> pass` or `Sweep <date> red <n>`"; the
    empty commit changes no file."""
    fx = build(tmp_path)
    main_sha = git(fx.origin, "rev-parse", "main")
    run_sweep(fx, lines="GATE regression_csim REJECT new failures: ['t::x']\\n", failing="[\"t::x\"]", rc=1)
    subjects = git(fx.origin, "log", "--format=%H %s", f"{main_sha}..main").splitlines()
    red = [s for s in subjects if re.fullmatch(r"[0-9a-f]{40} Sweep \d{4}-\d{2}-\d{2} red 1", s)]
    assert len(red) == 1, subjects
    assert git(fx.origin, "show", "--format=", "--stat", red[0].split()[0]) == "", "the Sweep commit must be empty"


def test_6_absolute_red_list_comes_from_the_stored_result(tmp_path):
    """Group 6 (section 8 B2): "a fixture result json with 3 failing ids and no new ones yields `PASS | new: none | red:
    3`"."""
    fx = build(tmp_path)
    r = run_sweep(fx, lines="GATE tier slow OK\\n", failing='["t::a", "t::b", "t::c"]')
    assert r.returncode == 0, r.stderr
    last = origin_main(fx).rstrip("\n").splitlines()[-1]
    assert re.search(r"\| PASS \| new: none \| red: 3 \| t::a, ?t::b, ?t::c \|$", last), last
    subjects = git(fx.origin, "log", "--format=%s", "-3").splitlines()
    assert any(re.fullmatch(r"Sweep \d{4}-\d{2}-\d{2} (pass|red 3)", s) for s in subjects), subjects


# --- H-034 (sweep-row-on-early-reject): an early reject still writes its row ---------------------------------------------
# Story: "A sweep that cannot finish still writes its row, so a red or broken sweep shows in the status and never passes as
# silence." DEC-sweep-row-on-early-reject-2026-10-31. An early reject (merge_gate.sh early_exit, rc 1) leaves no
# candidate_results/<sha>.json; only a log with no `GATE ` line (or rc > 1) is a harness error with no row.
H034_ID_A = "tests/qa/test_a.py::test_one"
H034_ID_B = "tests/qa/test_b.py::test_two"
H034_EARLY = (f"GATE acceptance REJECT   scene returns ... FAILED {H034_ID_A} FAILED {H034_ID_B} ===\\n"
              "GATE early_exit REJECT acceptance [0.0s]\\n")


def _h034_cols(row):
    """The row split as merge_gate.sh does (awk -F'|'): [0] date, [1] sha, [2] verdict, [3] new, [4] red, [-1] last column."""
    return [c.strip() for c in row.split("|")[1:-1]]


def _h034_red_sidecars(fx):
    return sorted(fx.wtroot.glob("sweep-*.gate.log.red"))


def test_h034_early_reject_without_result_file_writes_a_REJECT_early_row(tmp_path):
    """H-034 Tests: "a planted gate log holding `GATE acceptance REJECT ... FAILED a::b FAILED c::d` and `GATE early_exit
    REJECT acceptance` with no result file yields exit 0, a sweeps.md row with verdict `REJECT`, red 2 and `early
    acceptance` in the last column, and a `.red` sidecar naming the two ids." Red today: sweep.sh exits 1 with `no row
    written`. Columns as merge_gate.sh 5c-status reads them (awk -F'|': $4 verdict, $6 red, $7 last)."""
    fx = build(tmp_path)
    main_sha = git(fx.origin, "rev-parse", "main")
    r = run_sweep(fx, lines=H034_EARLY, rc=1, result=False)
    assert r.returncode == 0, r.stderr
    last = origin_main(fx).rstrip("\n").splitlines()[-1]
    assert re.fullmatch(rf"\| {TS} \| {main_sha} \| REJECT \| new: [^|]*\| red: 2 \| [^|]*\|", last), last
    assert _h034_cols(last)[2] == "REJECT" and "early acceptance" in _h034_cols(last)[-1], last
    side = _h034_red_sidecars(fx)
    assert len(side) == 1, side
    assert side[0].read_text().split() == sorted([H034_ID_A, H034_ID_B]), side[0].read_text()


def test_h034_early_reject_still_writes_the_red_n_sweep_commit(tmp_path):
    """H-034 Files: "The `Sweep` commit and the sweeps.md row are written as today (H-014, H-021)": an empty commit
    `Sweep <date> red 2` follows the row. Red today for the same reason as the row test."""
    fx = build(tmp_path)
    main_sha = git(fx.origin, "rev-parse", "main")
    run_sweep(fx, lines=H034_EARLY, rc=1, result=False)
    subjects = git(fx.origin, "log", "--format=%H %s", f"{main_sha}..main").splitlines()
    red = [s for s in subjects if re.fullmatch(r"[0-9a-f]{40} Sweep \d{4}-\d{2}-\d{2} red 2", s)]
    assert len(red) == 1, subjects
    assert git(fx.origin, "show", "--format=", "--stat", red[0].split()[0]) == "", "the Sweep commit must be empty"


def test_h034_early_reject_row_names_the_first_rejecting_stage(tmp_path):
    """H-034 Files: `early <stage>` in the last column "naming the first rejecting stage when no result file exists" (the
    verdict stays exactly `REJECT`, Rulings D): two REJECT stages in log order (story, then acceptance) name `story`."""
    fx = build(tmp_path)
    lines = (f"GATE story REJECT no Machine lines in docs/stories/X.md\\n"
             f"GATE acceptance REJECT ... FAILED {H034_ID_A} ===\\n"
             "GATE early_exit REJECT story acceptance [0.0s]\\n")
    r = run_sweep(fx, lines=lines, rc=1, result=False)
    assert r.returncode == 0, r.stderr
    last = origin_main(fx).rstrip("\n").splitlines()[-1]
    cols = _h034_cols(last)
    assert cols[2] == "REJECT" and "early story" in cols[-1] and "acceptance" not in cols[-1], last


def test_h034_bare_early_reject_counts_one_red_per_bare_stage(tmp_path):
    """H-034 Files: red count = "the number of distinct ids quoted in `GATE <stage> REJECT` lines ... plus one per bare
    REJECT stage"; the `early_exit` line is the summary of the stage line and counts for nothing. One bare story REJECT:
    verdict `REJECT`, `early story` in the last column, red 1, an empty `.red` sidecar."""
    fx = build(tmp_path)
    lines = "GATE story REJECT no Machine lines in docs/stories/X.md\\nGATE early_exit REJECT story [0.0s]\\n"
    r = run_sweep(fx, lines=lines, rc=1, result=False)
    assert r.returncode == 0, r.stderr
    last = origin_main(fx).rstrip("\n").splitlines()[-1]
    cols = _h034_cols(last)
    assert cols[2] == "REJECT" and cols[4] == "red: 1" and "early story" in cols[-1], last
    side = _h034_red_sidecars(fx)
    assert len(side) == 1 and side[0].read_text().strip() == "", side


def test_h034_red_counts_quoted_ids_and_FAILED_tokens_distinct_and_not_the_early_exit_line(tmp_path):
    """H-034 Rulings B: "`FAILED <id>` tokens count, quoted ids count, `early_exit` counts for nothing": a story REJECT
    quoting two ids and an acceptance REJECT with two FAILED tokens, one repeating a quoted id, give red 3 (distinct) and a
    sidecar of exactly those three ids. Red today: exit 1, no row."""
    fx = build(tmp_path)
    lines = ("GATE story REJECT new failures: ['t::q', 't::r']\\n"
             "GATE acceptance REJECT ... FAILED t::r FAILED t::s ===\\n"
             "GATE early_exit REJECT story acceptance [0.0s]\\n")
    r = run_sweep(fx, lines=lines, rc=1, result=False)
    assert r.returncode == 0, r.stderr
    last = origin_main(fx).rstrip("\n").splitlines()[-1]
    assert _h034_cols(last)[4] == "red: 3", last
    side = _h034_red_sidecars(fx)
    assert len(side) == 1 and side[0].read_text().split() == ["t::q", "t::r", "t::s"], side


def test_h034_control_log_with_no_GATE_line_is_still_a_harness_error(tmp_path):
    """H-034 negative control, green today: "a log with no `GATE ` line still exits 1 with the harness-error message", no
    row, nothing pushed."""
    fx = build(tmp_path)
    before_sweeps, before_main = origin_main(fx), git(fx.origin, "rev-parse", "main")
    r = run_sweep(fx, lines="make: *** [all] Error 2\\n", rc=1, result=False)
    assert r.returncode == 1, (r.returncode, r.stdout, r.stderr)
    assert "no row written" in r.stderr, r.stderr
    assert origin_main(fx) == before_sweeps and git(fx.origin, "rev-parse", "main") == before_main, "a harness error pushed"


def test_h034_log_with_no_GATE_line_is_a_harness_error_even_with_a_result_file(tmp_path):
    """H-034 Rulings C: "no `GATE ` line but a result file present" is a harness error too: exit 1 with the harness-error
    message, no row, nothing pushed. Red today: with the result file planted sweep.sh writes a REJECT row for rc 1."""
    fx = build(tmp_path)
    before_sweeps, before_main = origin_main(fx), git(fx.origin, "rev-parse", "main")
    r = run_sweep(fx, lines="make: *** [all] Error 2\\n", rc=1, result=True)
    assert r.returncode == 1, (r.returncode, r.stdout, r.stderr)
    assert "no row written" in r.stderr, r.stderr
    assert origin_main(fx) == before_sweeps and git(fx.origin, "rev-parse", "main") == before_main, "a harness error pushed"


def test_h034_control_rc_above_one_is_still_a_harness_error_even_with_REJECT_lines(tmp_path):
    """H-034 Files: "rc greater than 1 ... is a harness error (message as today, exit 1)", green today: the early-reject
    log with rc 2 and no result file writes no row."""
    fx = build(tmp_path)
    before_sweeps, before_main = origin_main(fx), git(fx.origin, "rev-parse", "main")
    r = run_sweep(fx, lines=H034_EARLY, rc=2, result=False)
    assert r.returncode == 1 and "no row written" in r.stderr, (r.returncode, r.stderr)
    assert origin_main(fx) == before_sweeps and git(fx.origin, "rev-parse", "main") == before_main, "a harness error pushed"


def test_h034_control_rejecting_gate_with_a_result_file_keeps_the_plain_REJECT_verdict(tmp_path):
    """H-034 Files: "`REJECT` as today otherwise", green today and after: the same REJECT lines with rc 1 and a result file
    give verdict `REJECT` and no `early` in the last column."""
    fx = build(tmp_path)
    r = run_sweep(fx, lines="GATE regression_csim REJECT new failures: ['t::x']\\n", failing="[\"t::x\"]", rc=1)
    assert r.returncode == 0, r.stderr
    last = origin_main(fx).rstrip("\n").splitlines()[-1]
    assert re.search(r"\| REJECT \| new: t::x \|", last) and "early" not in _h034_cols(last)[-1], last


# --- (5): the append ---------------------------------------------------------------------------------------------------

def test_5_appended_row_is_last_and_earlier_rows_are_byte_identical(tmp_path):
    """(5) "positive control: the row appended to a fixture `sweeps.md` is the last line and the earlier rows are
    byte-identical"."""
    fx = build(tmp_path)
    before = origin_main(fx)
    run_sweep(fx, lines="GATE tier slow OK\\n")
    after = origin_main(fx)
    assert after.startswith(before.rstrip("\n") + "\n"), "earlier rows changed"
    assert len(after.rstrip("\n").splitlines()) == len(before.rstrip("\n").splitlines()) + 1


# --- the run itself: arguments, environment, locks, worktree ------------------------------------------------------------

def test_7_gate_runs_slow_tier_with_the_rules_environment_and_the_worktree_is_finished(tmp_path):
    """Spec: "runs `merge_gate.sh --tier slow <wt> <base sha> <ids>` in the foreground with the environment of rules.md
    (b)'s Gate bullet ... `wt.py done`": `wt.py new sweep-<UTC date-time> --owner sweep-timer --purpose "slow tier"` from
    origin/main, then `wt.py done <path> <pushed sha>`."""
    fx = build(tmp_path)
    run_sweep(fx, lines="GATE tier slow OK\\n")
    gate = (fx.wtroot / "gate_calls.log").read_text()
    assert re.search(rf"ARGS --tier slow \S+ {fx.a} id1,id2\n", gate), gate
    for kv in ("MERGE_GATE_SUITE_TIMEOUT=2400", "MERGE_GATE_PLAYTHROUGH_TIMEOUT=2400", "MERGE_GATE_PLAY_TIMEOUT=900"):
        assert kv in gate, gate
    assert re.search(r"MERGE_GATE_PIECES=\S*pieces\.toml", gate), gate
    calls = (fx.wtroot / "wt_calls.log").read_text().splitlines()
    new = [c for c in calls if c.startswith("new ")]
    assert len(new) == 1 and re.match(r"new sweep-\d{4}-?\d{2}-?\d{2}\S* ", new[0]), calls
    assert "--owner sweep-timer" in new[0] and "slow tier" in new[0], new[0]
    done = [c for c in calls if c.startswith("done ")]
    assert len(done) == 1 and done[0].split()[-1] == git(fx.origin, "rev-parse", "main"), (done, calls)


def test_8_sweep_runs_while_gate_lock_is_held(tmp_path):
    """Spec: "It takes no lock on `gate.lock`: a sweep and a landing gate run at once by design"."""
    fx = build(tmp_path)
    lock = fx.home / "Projects" / "om-push" / "gate.lock"
    with open(lock, "w") as fh:
        fcntl.flock(fh, fcntl.LOCK_EX)
        r = run_sweep(fx, lines="GATE tier slow OK\\n", timeout=60)
    assert r.returncode == 0, r.stderr
    assert origin_main(fx).rstrip("\n").splitlines()[-1].split("|")[3].strip() == "PASS"


def test_9_push_waits_on_records_lock(tmp_path):
    """Spec: "commits it and pushes under `records.lock` (the records push line of rules.md)": with the lock held the push
    does not land; once released it does."""
    import time
    fx = build(tmp_path)
    lock = fx.home / "Projects" / "om-push" / "records.lock"
    before = git(fx.origin, "rev-parse", "main")
    with open(lock, "w") as fh:
        fcntl.flock(fh, fcntl.LOCK_EX)
        env = {**os.environ, "HOME": str(fx.home), "SWEEP_TEST_WT_ROOT": str(fx.wtroot), "STUB_GATE_LINES": "GATE tier slow OK\\n",
               "STUB_GATE_FAILING": "[]", "STUB_GATE_RC": "0",
               "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}
        assert fx.sweep.exists(), "missing scripts/specfactory/sweep.sh"
        p = subprocess.Popen(["bash", str(fx.sweep)], cwd=fx.repo, env=env, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE, text=True)
        time.sleep(8)
        held = git(fx.origin, "rev-parse", "main")
    out, err = p.communicate(timeout=90)
    assert held == before, "the sweep pushed while records.lock was held"
    assert git(fx.origin, "rev-parse", "main") != before, f"the sweep never pushed after the lock was released: {out!r} {err!r}"


# --- (4): the unit files -----------------------------------------------------------------------------------------------

def test_4_unit_files_exist_with_the_nightly_schedule_and_the_origin_main_exec():
    """(4) "the unit files parse (`systemd-analyze verify` when present, else a text check of `OnCalendar` and
    `ExecStart`)"; "`OnCalendar=*-*-* 23:30:00` local (DRAFT-sweep-nightly), `Persistent=true`, the service runs `sweep.sh`
    from `origin/main` the way `om-token-report.service` runs its script"."""
    timer, service = UNITS / "om-sweep.timer", UNITS / "om-sweep.service"
    assert timer.is_file() and service.is_file(), f"missing {timer.relative_to(REPO)} / {service.relative_to(REPO)}"
    t, s = timer.read_text(), service.read_text()
    assert re.search(r"^OnCalendar=\*-\*-\* 23:30:00$", t, re.M), t
    assert re.search(r"^Persistent=true$", t, re.M), t
    assert re.search(r"^ExecStart=.*origin/main:scripts/specfactory/sweep\.sh", s, re.M), s
    assert re.search(r"^Type=oneshot$", s, re.M), s


def test_4b_systemd_analyze_verifies_the_new_timer():
    """(4) `systemd-analyze verify` exits 0 on the new timer (and so on its service)."""
    if not shutil.which("systemd-analyze"):
        pytest.skip("systemd-analyze not present; test_4 is the text check")
    timer = UNITS / "om-sweep.timer"
    assert timer.is_file(), f"missing {timer.relative_to(REPO)}"
    r = subprocess.run(["systemd-analyze", "verify", str(timer)], capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr


# --- positive controls (green today) -----------------------------------------------------------------------------------

def test_control_systemd_analyze_verify_passes_on_the_existing_timer():
    """Control for (4): the verify call is sound; the same call on om-nightly-play.timer exits 0 today."""
    if not shutil.which("systemd-analyze"):
        pytest.skip("systemd-analyze not present")
    r = subprocess.run(["systemd-analyze", "verify", str(UNITS / "om-nightly-play.timer")], capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr


# --- DEC-sweep-drift-warn-2026-10-30: the gate's status stage and the sweep rows -----------------------------------------
# Fixture: the tests/specfactory/test_gate_reorder.py one (a candidate repo plus a gate repo holding the real merge_gate.sh).
# Ruling (docs/stories/H-014.md "Deadlock ruling"): "the gate's status stage treats `STATUS sweep DRIFT` as a WARN under
# every tier and rejects on every other DRIFT as before; what blocks a landing after a bad sweep is the last `sweeps.md`
# row being REJECT, which the status stage checks as `GATE status REJECT sweep red <n> at <sha>`".
sys.path.insert(0, str(Path(__file__).resolve().parent))
import test_gate_reorder as gr  # noqa: E402

SWEEP_DRIFT_STUB = "print('STATUS sweep DRIFT 9 landings and 40.0 h since the BASE row at 93c0583d')\n"
OTHER_DRIFT_STUB = "print('STATUS lane_table DRIFT lane X cites a sha the base lacks')\n"


def _gate_run(tmp_path, *, stubs=None, sweeps_text=None):
    story = "## Machine lines\n\nFlag: harness\nTests: none\n"  # the H-006 story stage rejects a candidate without one
    gate, cand = gr._build(tmp_path, drift=False, gate_script=gr.SPEC_DIR / "merge_gate.sh",
                           pieces=gr.OWNS_CLEAN,
                           # the toy repo has no real sim library: a copy of gate_flag.py beside a stub trace tool, so the flag stage cannot end the run
                           stubs={"checksum_trace.py": gr.OK_STUB, "tactical_trace.py": gr.OK_STUB, "gate_flag.py": (SPEC / "gate_flag.py").read_text(), **(stubs or {})},
                           candidate_files={"feat.txt": "feat\n", "docs/stories/B1.md": story})
    if sweeps_text is not None:
        gr._overlay(gate.parents[2], SWEEPS_REL, sweeps_text)
    env = {"PATH": gr.GATE_PATH, "HOME": str(Path.home()), "MERGE_GATE_RUNS_CSV": str(tmp_path / "runs.csv"),
           "MERGE_GATE_PIECES": str(tmp_path / "pieces.toml"),
           "MERGE_GATE_PLACEHOLDERS": str(tmp_path / "placeholders.txt")}
    r = subprocess.run(["bash", str(gate), str(cand), "origin/main", "B1"], capture_output=True, text=True, env=env,
                       timeout=gr.RUN_TIMEOUT_S)
    return r.returncode, r.stdout.splitlines(), r.stdout + r.stderr


def test_control_other_status_drift_still_rejects(tmp_path):
    """Control for the two tests below (green today and after): a status_check stub printing a non-sweep DRIFT gates to
    `GATE status REJECT`, so the stub mechanism drives the stage and "every other DRIFT" still rejects."""
    rc, lines, out = _gate_run(tmp_path, stubs={"status_check.py": OTHER_DRIFT_STUB})
    assert any(ln.startswith("GATE status REJECT") and "lane_table" in ln for ln in lines), out


def test_10_sweep_drift_is_a_warn_and_the_run_goes_on_past_status(tmp_path):
    """H-014 deadlock ruling: "the gate's status stage treats `STATUS sweep DRIFT` as a WARN under every tier": a
    status_check stub printing `STATUS sweep DRIFT ...` gates to `GATE status WARN`, with no status REJECT and no
    early_exit, and the stages after status still run."""
    rc, lines, out = _gate_run(tmp_path, stubs={"status_check.py": SWEEP_DRIFT_STUB})
    st = [ln for ln in lines if ln.startswith("GATE status ")]
    assert len(st) == 1 and st[0].startswith("GATE status WARN"), f"status lines {st!r}\n{out}"
    assert "STATUS sweep DRIFT" in st[0], st[0]
    assert gr._idx(lines, "early_exit") is None, out
    assert gr._idx(lines, "rule_pins") is not None and gr._idx(lines, "rule_pins") > gr._idx(lines, "status"), out


def test_11_a_reject_row_last_in_sweeps_blocks_the_landing(tmp_path):
    """H-014 deadlock ruling: "what blocks a landing after a bad sweep is the last `sweeps.md` row being REJECT ...
    `GATE status REJECT sweep red <n> at <sha>`" (gate.md: "a landing after a red sweep waits for the bisect")."""
    sha = "a" * 40
    text = HEADER.format(base=sha) + f"| 2026-10-30 08:00 | {sha} | REJECT | new: t::y | red: 1 | t::y |\n"
    rc, lines, out = _gate_run(tmp_path, sweeps_text=text)
    assert any(re.match(r"GATE status REJECT .*sweep red 1 at " + sha[:8], ln) for ln in lines), out
    assert rc == 1, out
