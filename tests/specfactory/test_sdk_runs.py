# spec: docs/northstar/plans/method_rev3_2026-10-26/spec.md "Design" item 2 (run rows), HARNESS-mm-3
"""sdk_engineer.py --dry-run appends one run row to the file SDK_RUNS_CSV names.

Interfaces fixed here (the spec leaves them open): columns date,label,piece,role,model,turns,cost,outcome (header
written when the file is new); new optional flags `--piece`, `--role`, `--label` fill the row (label defaults to
`<piece> <role>`); a dry run records turns 0, cost 0 and an outcome that is non-empty (success, stop:<reason> or
error); the status_check cases for this piece (findings, metrics, method_pins, story/contract keys) are in
test_status_check.py.
"""
import csv
import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
SCRIPT = REPO / "scripts" / "specfactory" / "sdk_engineer.py"
COLS = ["date", "label", "piece", "role", "model", "turns", "cost", "outcome"]


def _fixture(tmp_path):
    wt = tmp_path / "wt"
    wt.mkdir(exist_ok=True)
    (wt / ".git").write_text("gitdir: /nonexistent\n")  # a linked worktree has a .git file
    brief = tmp_path / "brief.md"
    brief.write_text("RESULT first line\n")
    return wt, brief


def _run(tmp_path, csv_path, *extra):
    wt, brief = _fixture(tmp_path)
    env = {k: v for k, v in os.environ.items() if k != "ANTHROPIC_AUTH_TOKEN"}
    env["SDK_RUNS_CSV"] = str(csv_path)
    return subprocess.run([sys.executable, str(SCRIPT), "--worktree", str(wt), "--brief", str(brief), "--dry-run",
                           "--piece", "HARNESS-x", "--role", "build", *extra], capture_output=True, text=True,
                          env=env, timeout=60)


def test_control_dry_run_without_the_new_flags_still_works(tmp_path):
    wt, brief = _fixture(tmp_path)
    r = subprocess.run([sys.executable, str(SCRIPT), "--worktree", str(wt), "--brief", str(brief), "--dry-run"],
                       capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, r.stdout + r.stderr


def test_3_dry_run_appends_one_row_with_the_columns(tmp_path):
    p = tmp_path / "runs" / "sdk_runs.csv"
    r = _run(tmp_path, p)
    assert r.returncode == 0, r.stdout + r.stderr
    assert p.is_file(), f"{p} not written\n{r.stdout}{r.stderr}"
    rows = list(csv.reader(p.read_text().splitlines()))
    data = [x for x in rows if x != COLS]
    assert len(data) == 1 and len(data[0]) == len(COLS), rows
    d = dict(zip(COLS, data[0]))
    assert d["piece"] == "HARNESS-x" and d["role"] == "build" and d["label"] == "HARNESS-x build", d
    assert d["model"] == "claude-sonnet-5-5" and d["turns"] == "0" and d["outcome"], d
    assert len(d["date"]) == 10 and float(d["cost"]) == 0.0


def test_3_a_second_run_appends_and_keeps_one_header(tmp_path):
    p = tmp_path / "sdk_runs.csv"
    _run(tmp_path, p)
    (tmp_path / "wt2").mkdir()
    _run(tmp_path, p, "--model", "claude-fable-5-1")
    rows = p.read_text().splitlines()
    assert sum(1 for x in rows if x.startswith("date,")) == 1 and len(rows) == 3, rows
    assert "claude-fable-5-1" in rows[-1]
