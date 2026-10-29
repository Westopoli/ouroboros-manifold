# spec: docs/northstar/plans/2026-10-19-harness-enforcement-spec.md "HARNESS-coverage, the weekly coverage number" (rev 4)
"""HARNESS-coverage: status_check.py check `coverage`, scripts/specfactory/coverage_report.py and
scripts/specfactory/coverage_run.sh. Tests first; every test below fails today (the three pieces are absent).

Named drafts (the Architect's, spec): DRAFT-coverage-slack = 0.5 points, DRAFT-coverage-stale-days = 10 days. No
other number is invented here; fixture numbers are arbitrary and say so.

Interfaces fixed here (the spec leaves them open), one line each:
- check function: `check_coverage(baseline_path, runs_dir, today)` in status_check.py, Path, Path, datetime.date;
  returns the module's usual list of (name, ok, detail) with ok True / "warn" / False; name is "coverage".
- DRIFT detail names the key (`zero_a_reachable`, `zero_b_reachable`, `lines_pct_a`, `lines_pct_b`) and carries the
  run value and the baseline value as printed numbers; the OK and WARN detail carries all four run numbers
  (zero counts as ints, lines_pct with one decimal).
- the CLI cannot set `today`, so CLI stale cases use 15 days back (clock-zone safe); the 10 and 11 day edge is
  tested on `check_coverage` with an explicit date.
- the OK "improved" detail contains `coverage improved, run --accept`; the stale detail contains `coverage stale`;
  the no-run WARN text is not asserted.
- coverage_report.py reads `<out_dir>/A` and `<out_dir>/B`, every `*.gcov.json.gz` in each (gcov -f -j output, gcov
  JSON format_version 2: files[].file as a repo-relative path, files[].functions[] name/execution_count,
  files[].lines[] line_number/function_name/count); the files of one directory (release and debug builds) are summed
  per (file, function) and per (file, line); a line is covered when its summed count is above 0; `lines` of a csv row
  is the number of line entries naming the function; weak_stub rows leave the line totals as well as the zero counts;
  lines_pct is round(100 * covered / total, 1); weak_stub is read from the source: the definition in
  `<repo>/<file>` is preceded by `__attribute__((weak))`.
- pytest exit codes reach coverage_report.py as one integer each in `<out_dir>/exit_a` and `<out_dir>/exit_b`
  (the report takes only <out_dir> and <repo>); outputs are `<out_dir>/functions.csv` and `<out_dir>/summary.json`;
  csv booleans are written `True` / `False`.
- coverage_run.sh calls the tools by bare name from PATH (`make`, `pytest`, `gcov`); `--accept <summary>` writes
  `docs/northstar/plans/drift_audits/coverage_baseline.json` under the repo root that holds the script
  (`<root>/scripts/specfactory/coverage_run.sh`), so these tests copy the script into a scratch repo; a missing
  summary exits non-zero and writes nothing; no arguments exit non-zero with a usage line.

Controls: the helper-built summary pairs (drift pair, clean pair) are the positive controls of the detector; both go
through the same CLI, so DRIFT without the check is impossible and OK without the check is impossible too (no
`STATUS coverage` line at all).
"""
import csv
import datetime
import gzip
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent.parent
SC_PATH = REPO / "scripts" / "specfactory" / "status_check.py"
REPORT = REPO / "scripts" / "specfactory" / "coverage_report.py"
RUN_SH = REPO / "scripts" / "specfactory" / "coverage_run.sh"
BASELINE_REL = "docs/northstar/plans/drift_audits/coverage_baseline.json"
RUNS_REL = "docs/northstar/plans/drift_audits/coverage_runs"

COVERAGE_SLACK = 0.5  # DRAFT-coverage-slack
STALE_DAYS = 10  # DRAFT-coverage-stale-days

BASE = dict(zero_a_reachable=43, zero_b_reachable=95, lines_pct_a=88.1, lines_pct_b=74.2)  # arbitrary fixture numbers


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(path.parent))
    try:
        spec.loader.exec_module(mod)
    finally:
        sys.path.remove(str(path.parent))
    return mod


TSC = _load(REPO / "tests" / "specfactory" / "test_status_check.py", "_tsc_for_coverage")


def utc_today():
    return datetime.datetime.now(datetime.timezone.utc).date()


def summary(days_back=0, **over):
    d = dict(BASE, sha="0123456789ab", date=(utc_today() - datetime.timedelta(days=days_back)).isoformat(),
             exit_a=1, exit_b=0)
    d.update(over)
    return d


def put_run(runs, dirname, s):
    p = runs / dirname / "summary.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(s, indent=1) + "\n")


def put_baseline(path, s=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(s or summary(), indent=1) + "\n")


def tree_state(root):
    return {p.relative_to(root).as_posix(): (p.stat().st_mtime_ns, p.read_bytes())
            for p in sorted(root.rglob("*")) if p.is_file()}


def check_cov(tmp_path, base_s, run_s, run_dir="2026-01-01", extra=()):
    """Fixture repo + cov dir; returns (result, STATUS coverage lines, cov dir state before)."""
    TSC.build_fixture(tmp_path)
    cov = tmp_path / "cov"
    put_baseline(cov / "baseline.json", base_s)
    if run_s is not None:
        put_run(cov / "runs", run_dir, run_s)
    else:
        (cov / "runs").mkdir(parents=True, exist_ok=True)
    before = tree_state(cov)
    res = TSC.run_check(tmp_path, "--coverage-baseline", str(cov / "baseline.json"),
                        "--coverage-runs", str(cov / "runs"), *extra)
    lines = [ln for ln in res.stdout.splitlines() if ln.startswith("STATUS coverage ")]
    assert tree_state(cov) == before, "the coverage check must only read"
    return res, lines, cov


# ------------------------------------------------------------------ status_check.py: the check `coverage`

def test_status_check_docstring_says_thirteen_checks_and_lists_coverage():
    """Spec: the "Twelve checks" docstring becomes "Thirteen checks" with a `coverage` entry."""
    doc = SC_PATH.read_text().split('"""')[1]
    assert "Thirteen checks" in doc
    assert "Twelve checks" not in doc
    assert re.search(r"^\s+coverage\s", doc, re.M), "no `coverage` entry in the docstring list"


def test_status_check_has_check_coverage_and_default_constants():
    sc = _load(SC_PATH, "_sc_for_coverage")
    assert callable(getattr(sc, "check_coverage", None))
    assert sc.D_COVERAGE_BASELINE == BASELINE_REL
    assert sc.D_COVERAGE_RUNS == RUNS_REL


def test_cli_help_lists_coverage_arguments():
    r = subprocess.run([sys.executable, str(SC_PATH), "--help"], capture_output=True, text=True, timeout=30)
    assert "--coverage-baseline" in r.stdout and "--coverage-runs" in r.stdout


def test_positive_control_clean_pair_prints_ok_line_last_after_method_pins(tmp_path):
    """Clean pair (run equals baseline): one OK line carrying the four numbers; it is the last STATUS line."""
    res, lines, _ = check_cov(tmp_path, summary(), summary(days_back=1))
    assert len(lines) == 1 and lines[0].startswith("STATUS coverage OK "), res.stdout
    for n in ("43", "95", "88.1", "74.2"):
        assert n in lines[0], lines[0]
    assert "improved" not in lines[0]
    all_status = [ln for ln in res.stdout.splitlines() if ln.startswith("STATUS ")]
    assert all_status[-1] == lines[0], "coverage must be added last in main()'s results block"
    assert any(ln.startswith("STATUS method_pins ") for ln in all_status[:-1])
    assert res.returncode == 0, res.stdout + res.stderr


@pytest.mark.parametrize("key,worse", [("zero_a_reachable", 44), ("zero_b_reachable", 96)])
def test_positive_control_zero_count_above_baseline_is_drift_naming_the_number(tmp_path, key, worse):
    res, lines, _ = check_cov(tmp_path, summary(), summary(days_back=1, **{key: worse}))
    drift = [ln for ln in lines if " DRIFT " in ln]
    assert drift, res.stdout
    assert any(key in ln and str(worse) in ln and str(BASE[key]) in ln for ln in drift), drift
    assert res.returncode == 1


@pytest.mark.parametrize("key", ["lines_pct_a", "lines_pct_b"])
def test_lines_drop_of_0_4_points_stays_ok(tmp_path, key):
    assert 0.4 < COVERAGE_SLACK
    res, lines, _ = check_cov(tmp_path, summary(), summary(days_back=1, **{key: round(BASE[key] - 0.4, 1)}))
    assert len(lines) == 1 and lines[0].startswith("STATUS coverage OK "), res.stdout
    assert "improved" not in lines[0]  # a number is worse: plain OK
    assert res.returncode == 0, res.stdout + res.stderr


@pytest.mark.parametrize("key", ["lines_pct_a", "lines_pct_b"])
def test_lines_drop_of_0_6_points_is_drift_naming_the_number(tmp_path, key):
    assert 0.6 > COVERAGE_SLACK
    low = round(BASE[key] - 0.6, 1)
    res, lines, _ = check_cov(tmp_path, summary(), summary(days_back=1, **{key: low}))
    drift = [ln for ln in lines if " DRIFT " in ln]
    assert any(key in ln and str(low) in ln and str(BASE[key]) in ln for ln in drift), res.stdout
    assert res.returncode == 1


def test_better_summary_prints_improved_line_and_leaves_baseline_unchanged(tmp_path):
    better = summary(days_back=1, zero_a_reachable=40, lines_pct_b=75.0)
    res, lines, cov = check_cov(tmp_path, summary(), better)  # check_cov asserts nothing under cov changed
    assert len(lines) == 1 and lines[0].startswith("STATUS coverage OK "), res.stdout
    assert "coverage improved, run --accept" in lines[0]
    for n in ("40", "95", "88.1", "75.0"):
        assert n in lines[0], lines[0]
    assert json.loads((cov / "baseline.json").read_text()) == summary()
    assert res.returncode == 0, res.stdout + res.stderr


def test_a_worse_number_inside_slack_blocks_the_improved_line(tmp_path):
    """Spec: improved needs no number worse; a lower zero count with lines_pct_a down 0.2 is plain OK."""
    mixed = summary(days_back=1, zero_a_reachable=40, lines_pct_a=round(BASE["lines_pct_a"] - 0.2, 1))
    res, lines, _ = check_cov(tmp_path, summary(), mixed)
    assert len(lines) == 1 and lines[0].startswith("STATUS coverage OK "), res.stdout
    assert "improved" not in lines[0]


def test_drift_is_decided_before_improved(tmp_path):
    """A lower zero count does not save a lines drop of 0.6; a lines gain does not save a higher zero count."""
    (tmp_path / "one").mkdir()
    (tmp_path / "two").mkdir()
    r1, l1, _ = check_cov(tmp_path / "one", summary(), summary(days_back=1, zero_a_reachable=40, lines_pct_b=73.6))
    assert any(" DRIFT " in ln and "lines_pct_b" in ln for ln in l1), r1.stdout
    r2, l2, _ = check_cov(tmp_path / "two", summary(), summary(days_back=1, zero_b_reachable=96, lines_pct_a=90.0))
    assert any(" DRIFT " in ln and "zero_b_reachable" in ln for ln in l2), r2.stdout
    assert not any("improved" in ln for ln in l1 + l2)


def test_newest_run_is_picked_by_date_field_not_directory_name(tmp_path):
    """The run directory that sorts last holds the OLDER summary; the newer one is worse -> DRIFT."""
    TSC.build_fixture(tmp_path)
    cov = tmp_path / "cov"
    put_baseline(cov / "baseline.json", summary())
    put_run(cov / "runs", "a-first", summary(days_back=0, zero_a_reachable=50))  # newest by date, worse
    put_run(cov / "runs", "z-last", summary(days_back=5))  # clean but older
    res = TSC.run_check(tmp_path, "--coverage-baseline", str(cov / "baseline.json"),
                        "--coverage-runs", str(cov / "runs"))
    cov_lines = [ln for ln in res.stdout.splitlines() if ln.startswith("STATUS coverage ")]
    assert any(" DRIFT " in ln and "zero_a_reachable" in ln for ln in cov_lines), res.stdout
    # control: swap the dates and the clean run is the newest
    put_run(cov / "runs", "a-first", summary(days_back=5, zero_a_reachable=50))
    put_run(cov / "runs", "z-last", summary(days_back=0))
    res = TSC.run_check(tmp_path, "--coverage-baseline", str(cov / "baseline.json"),
                        "--coverage-runs", str(cov / "runs"))
    cov_lines = [ln for ln in res.stdout.splitlines() if ln.startswith("STATUS coverage ")]
    assert len(cov_lines) == 1 and cov_lines[0].startswith("STATUS coverage OK "), res.stdout


def test_stale_run_warns_coverage_stale_and_exits_0(tmp_path):
    res, lines, _ = check_cov(tmp_path, summary(), summary(days_back=15))
    assert len(lines) == 1 and lines[0].startswith("STATUS coverage WARN "), res.stdout
    assert "coverage stale" in lines[0]
    assert "43" in lines[0] and "74.2" in lines[0]  # the line carries the numbers
    assert res.returncode == 0, res.stdout + res.stderr


def test_no_run_at_all_warns_and_exits_0(tmp_path):
    res, lines, _ = check_cov(tmp_path, summary(), None)
    assert len(lines) == 1 and lines[0].startswith("STATUS coverage WARN "), res.stdout
    assert res.returncode == 0, res.stdout + res.stderr


def test_check_function_stale_edge_is_after_ten_days():
    sc = _load(SC_PATH, "_sc_for_coverage_edge")
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        today = datetime.date(2026, 11, 20)
        put_baseline(d / "b.json", summary())

        def at_age(days):
            runs = d / f"runs{days}"
            put_run(runs, "r", dict(summary(), date=(today - datetime.timedelta(days=days)).isoformat()))
            return sc.check_coverage(d / "b.json", runs, today)

        ten, eleven = at_age(STALE_DAYS), at_age(STALE_DAYS + 1)
        assert [r[0] for r in ten] == ["coverage"] and ten[0][1] is True, ten
        assert eleven[0][0] == "coverage" and eleven[0][1] == "warn" and "coverage stale" in eleven[0][2], eleven
        none = sc.check_coverage(d / "b.json", d / "no-runs-here", today)
        assert none[0][0] == "coverage" and none[0][1] == "warn", none


def test_default_paths_resolve_against_repo(tmp_path):
    """No flags: baseline and runs are read from the default repo-relative paths (through at())."""
    TSC.build_fixture(tmp_path)
    put_baseline(tmp_path / BASELINE_REL, summary())
    put_run(tmp_path / RUNS_REL, "2026-01-01", summary(days_back=1, zero_b_reachable=99))
    res = TSC.run_check(tmp_path)
    lines = [ln for ln in res.stdout.splitlines() if ln.startswith("STATUS coverage ")]
    assert any(" DRIFT " in ln and "zero_b_reachable" in ln for ln in lines), res.stdout


def test_relative_flag_paths_resolve_against_repo_not_cwd(tmp_path):
    TSC.build_fixture(tmp_path)
    put_baseline(tmp_path / "rel" / "b.json", summary())
    put_run(tmp_path / "rel" / "runs", "r", summary(days_back=1, zero_a_reachable=77))
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    cmd = [sys.executable, str(SC_PATH), "--repo", str(tmp_path), "--base", "base",
           "--programme", TSC.PROGRAMME, "--pieces", TSC.PIECES, "--stories", TSC.STORIES,
           "--reviews", TSC.REVIEWS, "--roadmap", TSC.ROADMAP,
           "--coverage-baseline", "rel/b.json", "--coverage-runs", "rel/runs"]
    res = subprocess.run(cmd, capture_output=True, text=True, cwd=elsewhere, timeout=60)
    lines = [ln for ln in res.stdout.splitlines() if ln.startswith("STATUS coverage ")]
    assert any(" DRIFT " in ln and "zero_a_reachable" in ln for ln in lines), res.stdout + res.stderr


# ------------------------------------------------------------------ coverage_report.py on a fixture gcov directory

SIM_C = """#include "ouroboros_sim.h"
int om_a_only(void) { return 1; }
int om_b_only(void) { return 2; }
int om_unrun(void) { return 3; }
int om_dead(void) { return 4; }
int om_world_step(void) { return om_a_only() + om_unrun() + om_region_live() + om_region_hook(); }
"""
REGION_C = """#include "ouroboros_sim.h"
__attribute__((weak)) int om_region_hook(void) { return 0; }
int om_region_live(void) { return 5; }
"""
HEADER_H = """int om_a_only(void); int om_b_only(void); int om_unrun(void); int om_dead(void);
int om_world_step(void); int om_region_hook(void); int om_region_live(void);
"""
PIPE_C = """#include "ouroboros_sim.h"
int main(void) { for (;;) { om_b_only(); } }
"""
# (file, function): {run dir: {build: (execution_count, [(line, count), ...])}}; two builds per dir, summed
S, R = "csrc/sim.c", "csrc/region.c"
GCOV = {
    "A": {
        "rel": {(S, "om_world_step"): (2, [(10, 1), (11, 1), (12, 1)]), (S, "om_a_only"): (3, [(20, 3), (21, 3), (22, 0)]),
                (S, "om_b_only"): (0, [(30, 0), (31, 0)]), (S, "om_unrun"): (0, [(40, 0)]),
                (S, "om_dead"): (0, [(50, 0)]), (R, "om_region_hook"): (0, [(5, 0)]),
                (R, "om_region_live"): (1, [(20, 1)])},
        "dbg": {(S, "om_world_step"): (1, [(10, 1), (11, 1), (12, 0)]), (S, "om_a_only"): (1, [(20, 1), (21, 1), (22, 2)]),
                (S, "om_b_only"): (0, [(30, 0), (31, 0)]), (S, "om_unrun"): (0, [(40, 0)]),
                (S, "om_dead"): (0, [(50, 0)]), (R, "om_region_hook"): (0, [(5, 0)]),
                (R, "om_region_live"): (0, [(20, 0)])},
    },
    "B": {
        "rel": {(S, "om_world_step"): (5, [(10, 5), (11, 5), (12, 5)]), (S, "om_a_only"): (0, [(20, 0), (21, 0), (22, 0)]),
                (S, "om_b_only"): (4, [(30, 4), (31, 4)]), (S, "om_unrun"): (0, [(40, 0)]),
                (S, "om_dead"): (0, [(50, 0)]), (R, "om_region_hook"): (0, [(5, 0)]),
                (R, "om_region_live"): (0, [(20, 0)])},
        "dbg": {(S, "om_world_step"): (0, [(10, 0), (11, 0), (12, 0)]), (S, "om_a_only"): (0, [(20, 0), (21, 0), (22, 0)]),
                (S, "om_b_only"): (0, [(30, 0), (31, 0)]), (S, "om_unrun"): (0, [(40, 0)]),
                (S, "om_dead"): (0, [(50, 0)]), (R, "om_region_hook"): (0, [(5, 0)]),
                (R, "om_region_live"): (0, [(20, 0)])},
    },
}
# Expected, worked by hand from the table above.
EXPECT_ROWS = {  # (file, function): (lines, exec_A, exec_B, reachable, weak_stub)
    (S, "om_world_step"): (3, 3, 5, True, False), (S, "om_a_only"): (3, 4, 0, True, False),
    (S, "om_b_only"): (2, 0, 4, True, False), (S, "om_unrun"): (1, 0, 0, True, False),
    (S, "om_dead"): (1, 0, 0, False, False), (R, "om_region_hook"): (1, 0, 0, True, True),
    (R, "om_region_live"): (1, 1, 0, True, False),
}
# zero_a_reachable: om_b_only, om_unrun (hook is weak, dead is unreachable); zero_b_reachable: om_a_only, om_unrun,
# om_region_live. Lines (weak hook excluded): A 7 of 11 = 63.6 (om_a_only line 22 ran in the debug build only);
# B 5 of 11 = 45.5. With the hook counted they would be 58.3 and 41.7.
EXPECT_SUMMARY = dict(zero_a_reachable=2, zero_b_reachable=3, lines_pct_a=63.6, lines_pct_b=45.5, exit_a=1, exit_b=0)
CSV_COLS = ["file", "function", "lines", "exec_A", "exec_B", "reachable", "weak_stub"]


def _git(cwd, *a):
    return subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", "-c", "commit.gpgsign=false", *a],
                          cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()


def make_source_repo(root):
    for rel, text in (("csrc/ouroboros_sim.h", HEADER_H), ("csrc/sim.c", SIM_C), ("csrc/region.c", REGION_C),
                      ("csrc/pipe/om_pipe.c", PIPE_C)):
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)
    _git(root, "init", "-q", "-b", "main")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "fixture")
    return root


def write_gcov_dir(out):
    for phase, builds in GCOV.items():
        for build, table in builds.items():
            files = {}
            for (f, fn), (ex, lines) in table.items():
                ent = files.setdefault(f, {"file": f, "functions": [], "lines": []})
                ent["functions"].append({"name": fn, "demangled_name": fn, "start_line": lines[0][0],
                                         "execution_count": ex})
                ent["lines"] += [{"line_number": n, "function_name": fn, "count": c, "unexecuted_block": c == 0}
                                 for n, c in lines]
            d = out / phase
            d.mkdir(parents=True, exist_ok=True)
            with gzip.open(d / f"{build}.gcov.json.gz", "wt") as fh:
                json.dump({"format_version": "2", "gcc_version": "15.2.0", "files": list(files.values())}, fh)
    (out / "exit_a").write_text("1\n")
    (out / "exit_b").write_text("0\n")


@pytest.fixture
def report(tmp_path):
    repo = make_source_repo(tmp_path / "repo")
    out = tmp_path / "out"
    write_gcov_dir(out)
    r = subprocess.run([sys.executable, str(REPORT), str(out), str(repo)], capture_output=True, text=True, timeout=120)
    return r, out, repo


def read_csv(out):
    with open(out / "functions.csv", newline="") as fh:
        rd = csv.DictReader(fh)
        return rd.fieldnames, list(rd)


def test_report_writes_functions_csv_with_the_spec_columns(report):
    r, out, _ = report
    assert r.returncode == 0, r.stdout + r.stderr
    cols, rows = read_csv(out)
    assert cols == CSV_COLS
    assert len(rows) == len(EXPECT_ROWS)


def test_report_csv_rows_sum_builds_and_flag_reachable_and_weak_stub(report):
    r, out, _ = report
    assert r.returncode == 0, r.stdout + r.stderr
    _, rows = read_csv(out)
    got = {(x["file"], x["function"]): (int(x["lines"]), int(x["exec_A"]), int(x["exec_B"]),
                                        x["reachable"] == "True", x["weak_stub"] == "True") for x in rows}
    assert got == EXPECT_ROWS


def test_report_summary_has_the_spec_keys_and_types(report):
    r, out, repo = report
    assert r.returncode == 0, r.stdout + r.stderr
    s = json.loads((out / "summary.json").read_text())
    assert set(s) == {"sha", "date", "zero_a_reachable", "zero_b_reachable", "lines_pct_a", "lines_pct_b",
                      "exit_a", "exit_b"}
    assert re.fullmatch(r"[0-9a-f]{12}", s["sha"])
    assert s["sha"] == _git(repo, "rev-parse", "--short=12", "HEAD")
    assert re.fullmatch(r"\d{4}-\d\d-\d\d", s["date"])
    assert datetime.date.fromisoformat(s["date"]) in {utc_today() + datetime.timedelta(days=k) for k in (-1, 0, 1)}
    for k in ("zero_a_reachable", "zero_b_reachable", "exit_a", "exit_b"):
        assert type(s[k]) is int, (k, s[k])
    for k in ("lines_pct_a", "lines_pct_b"):
        assert type(s[k]) is float, (k, s[k])
        assert s[k] == round(s[k], 1)


def test_report_summary_numbers_exclude_weak_stub_rows(report):
    r, out, _ = report
    assert r.returncode == 0, r.stdout + r.stderr
    s = json.loads((out / "summary.json").read_text())
    assert {k: s[k] for k in EXPECT_SUMMARY} == EXPECT_SUMMARY


# ------------------------------------------------------------------ coverage_run.sh

STUB_BIN = {
    "make": '#!/bin/bash\necho "make|$PWD|$*" >> "$STUB_LOG"\ntouch libouroboros.so libouroboros_dbg.so\n',
    "pytest": ('#!/bin/bash\nn=$(grep -c "^pytest|" "$STUB_LOG")\necho "pytest|$PWD|$*" >> "$STUB_LOG"\n'
               'if [ "$n" = 0 ]; then touch "$PWD/a.gcda"; exit 1; fi\ntouch "$PWD/b.gcda"; exit 0\n'),
    "gcov": ('#!/bin/bash\nif find "$STUB_OUT/tree" -name a.gcda | grep -q .; then ph=phaseA; else ph=phaseB; fi\n'
             'echo "gcov|$PWD|$*|$ph|gcda=$(find "$STUB_OUT/tree" -name \'*.gcda\' -printf \'%f \')" >> "$STUB_LOG"\n'
             'printf \'{"format_version":"2","files":[]}\' | gzip > "$PWD/$ph-$RANDOM.gcov.json.gz"\n'),
}


@pytest.fixture(scope="module")
def stub_run(tmp_path_factory):
    root = tmp_path_factory.mktemp("covrun")
    repo = make_source_repo(root / "repo")
    for rel in ("tests/csim/test_x.py", "tests/transport/test_y.py", "Makefile"):
        (repo / rel).parent.mkdir(parents=True, exist_ok=True)
        (repo / rel).write_text("# stub\n")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "tests")
    bindir = root / "bin"
    bindir.mkdir()
    for name, body in STUB_BIN.items():
        (bindir / name).write_text(body)
        (bindir / name).chmod(0o755)
    out = root / "out"
    log = root / "stub.log"
    log.write_text("")
    env = dict(os.environ, PATH=f"{bindir}:{os.environ['PATH']}", STUB_LOG=str(log), STUB_OUT=str(out))
    r = subprocess.run(["bash", str(RUN_SH), str(repo), str(out)], capture_output=True, text=True, env=env,
                       cwd=root, timeout=300)
    calls = [ln.split("|") for ln in log.read_text().splitlines()]
    return r, repo, out, calls


def test_run_without_arguments_fails_with_usage():
    assert RUN_SH.is_file(), "scripts/specfactory/coverage_run.sh is absent"
    r = subprocess.run(["bash", str(RUN_SH)], capture_output=True, text=True, timeout=30)
    assert r.returncode != 0
    assert "usage" in (r.stdout + r.stderr).lower()


def test_run_copies_the_tree_without_git_and_builds_only_there(stub_run):
    r, repo, out, calls = stub_run
    assert r.returncode == 0, r.stdout + r.stderr
    assert (out / "tree" / "csrc" / "sim.c").is_file() and (out / "tree" / "tests" / "csim").is_dir()
    assert not (out / "tree" / ".git").exists()
    makes = [c for c in calls if c[0] == "make"]
    assert makes, "make was never run"
    assert all(c[1] == str(out / "tree") for c in calls if c[0] in ("make", "pytest")), calls
    assert not list(repo.rglob("*.gcda")) and not (repo / "libouroboros.so").exists()
    args = " ".join(c[2] for c in makes)
    for t in ("all", "pipe/ouroboros_pipe", "pipe/ouroboros_pipe_dbg", "OPT=-O0 --coverage"):
        assert t in args, (t, args)


def test_run_pytest_steps_csim_then_transport_with_spec_flags_and_no_abort(stub_run):
    r, _, out, calls = stub_run
    assert r.returncode == 0, "a failing csim pytest run (exit 1) must not abort the run: " + r.stdout + r.stderr
    py = [c for c in calls if c[0] == "pytest"]
    assert len(py) == 2, py
    a, b = py[0][2], py[1][2]
    for t in ("tests/csim", "--ignore=tests/csim/scale", "--ignore=tests/csim/controls", "-q", "no:cacheprovider"):
        assert t in a, (t, a)
    assert "-x" not in a.split()
    assert "tests/transport" in b and "-q" in b.split() and "no:cacheprovider" in b
    assert (out / "exit_a").read_text().strip() == "1" and (out / "exit_b").read_text().strip() == "0"


def test_run_gcov_into_A_then_gcda_deleted_then_gcov_into_B(stub_run):
    r, _, out, calls = stub_run
    assert r.returncode == 0, r.stdout + r.stderr
    a_files = sorted(p.name for p in (out / "A").glob("*.gcov.json.gz"))
    b_files = sorted(p.name for p in (out / "B").glob("*.gcov.json.gz"))
    assert a_files and all(n.startswith("phaseA-") for n in a_files), a_files
    assert b_files and all(n.startswith("phaseB-") for n in b_files), b_files
    gcovs = [c for c in calls if c[0] == "gcov"]
    assert all("-f" in c[2].split() and "-j" in c[2].split() for c in gcovs), gcovs
    b_calls = [c for c in gcovs if c[3] == "phaseB"]
    assert b_calls and all("a.gcda" not in c[4] for c in b_calls), "the .gcda files of run A were not deleted"


@pytest.fixture
def scratch_root(tmp_path):
    (tmp_path / "scripts" / "specfactory").mkdir(parents=True)
    for p in (RUN_SH, REPORT):
        if p.exists():
            shutil.copy(p, tmp_path / "scripts" / "specfactory" / p.name)
    _git(tmp_path, "init", "-q", "-b", "main")
    return tmp_path


def run_accept(root, *args):
    return subprocess.run(["bash", str(root / "scripts" / "specfactory" / "coverage_run.sh"), "--accept", *args],
                          capture_output=True, text=True, cwd=root, timeout=30)


def test_accept_byte_copies_the_summary_to_the_baseline(scratch_root, tmp_path_factory):
    raw = b'{"sha":"0123456789ab","date":"2026-10-29",  "zero_a_reachable": 2,\n"lines_pct_a": 63.0}\r\n\xc3\xa9 no trailing newline'
    src = tmp_path_factory.mktemp("sum") / "summary.json"
    src.write_bytes(raw)
    dest = scratch_root / BASELINE_REL
    dest.parent.mkdir(parents=True)
    dest.write_bytes(b"old baseline\n")
    r = run_accept(scratch_root, str(src))
    assert r.returncode == 0, r.stdout + r.stderr
    assert dest.read_bytes() == raw
    assert src.read_bytes() == raw


def test_accept_of_a_missing_summary_fails_and_writes_no_baseline(scratch_root, tmp_path_factory):
    assert RUN_SH.is_file(), "scripts/specfactory/coverage_run.sh is absent"
    r = run_accept(scratch_root, str(tmp_path_factory.mktemp("none") / "summary.json"))
    assert r.returncode != 0
    assert not (scratch_root / BASELINE_REL).exists()
