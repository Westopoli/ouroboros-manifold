# spec: docs/northstar/plans/method_rev3_2026-10-26/spec.md "Design" item 1 (gate rows) and G06 (default 2400, suite-timeout cause)
"""HARNESS-mm-2: merge_gate.sh prints one `GATE row <csv>` line and appends it to the file MERGE_GATE_RUNS_CSV names;
the default SUITE_TIMEOUT is 2400; a timed-out suite signals `suite-timeout <N>s`. Pattern: test_gate_base_stage.py
(a bare origin, a candidate clone, MERGE_GATE_STOP_AFTER=base).

Interfaces fixed here (the spec leaves them open): the row is printed also on a base REJECT and on STOP_AFTER=base
exits (an EXIT trap); `label` is the piece id argument; size columns are `git diff --numstat base..candidate` summed
by path class: product = csrc/ autoload/ scenes/, test = tests/, docs = docs/, lab = scripts/skilllab/; the
suite-timeout signal is tested at suite_regression.py's CLI (the tool the gate's regression stages run through
merge_gate_support.py) and, statically, as the text `suite-timeout` in merge_gate.sh.
"""
import csv
import io
import os
import re
import shutil
import subprocess
import sys
import uuid
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent.parent
SCRIPT = REPO / "scripts" / "specfactory" / "merge_gate.sh"
SREG = REPO / "scripts" / "specfactory" / "suite_regression.py"
FIXTURE_ROOT = Path.home() / "Projects" / "om-push" / "tmp-gaterow"
COLS = ["date", "label", "branch", "base_sha", "candidate_sha", "queue_s", "stage_s", "rc", "reject_stages",
        "reject_causes", "product_lines", "test_lines", "docs_lines", "lab_lines"]


def _git(cwd, *a):
    r = subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", "-c", "commit.gpgsign=false", *a],
                       cwd=cwd, check=True, capture_output=True, text=True)
    return r.stdout.strip()


def _commit(repo, files):
    for rel, n in files.items():
        p = Path(repo) / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("".join(f"l{i}\n" for i in range(n)))
        _git(repo, "add", rel)
    _git(repo, "commit", "-q", "-m", "c")
    return _git(repo, "rev-parse", "HEAD")


@pytest.fixture
def fx():
    root = FIXTURE_ROOT / uuid.uuid4().hex[:12]
    root.mkdir(parents=True)
    try:
        origin, pusher, cand = root / "origin.git", root / "pusher", root / "wt-cand"
        _git(root, "init", "-q", "--bare", "-b", "main", str(origin))
        _git(root, "clone", "-q", str(origin), str(pusher))
        _git(pusher, "checkout", "-q", "-B", "main")
        m1 = _commit(pusher, {"m1.txt": 1})
        _git(pusher, "push", "-q", "origin", "main")
        _git(root, "clone", "-q", str(origin), str(cand))
        _git(cand, "checkout", "-q", "-b", "feat")
        head = _commit(cand, {"csrc/a.c": 3, "tests/t.py": 2, "docs/d.md": 4, "scripts/skilllab/l.py": 5})
        yield {"root": root, "pusher": pusher, "cand": cand, "m1": m1, "head": head}
    finally:
        shutil.rmtree(root)


def _run(fx, csv_path, *, stop_after="base", extra_env=None, label="HARNESS-gate-row-fixture"):
    env = {"PATH": os.environ["PATH"], "HOME": str(Path.home()), "MERGE_GATE_RUNS_CSV": str(csv_path)}
    if stop_after:
        env["MERGE_GATE_STOP_AFTER"] = stop_after
    env.update(extra_env or {})
    r = subprocess.run(["bash", str(SCRIPT), str(fx["cand"]), "origin/main", label],
                       capture_output=True, text=True, env=env, timeout=120)
    rows = [ln for ln in r.stdout.splitlines() if ln.startswith("GATE row ")]
    return r, rows


def _fields(line):
    return next(csv.reader(io.StringIO(line[len("GATE row "):])))


def test_control_fixture_diff_is_countable(fx):
    out = _git(fx["cand"], "diff", "--numstat", f"{fx['m1']}..{fx['head']}")
    assert sorted(ln.split("\t")[0] for ln in out.splitlines()) == ["2", "3", "4", "5"]


def test_2_prints_one_gate_row_with_the_columns(fx, tmp_path):
    r, rows = _run(fx, tmp_path / "g.csv")
    assert len(rows) == 1, f"GATE row lines: {rows!r}\n{r.stdout}{r.stderr}"
    f = _fields(rows[0])
    assert len(f) == len(COLS), f"{len(f)} fields: {f}"
    d = dict(zip(COLS, f))
    assert re.fullmatch(r"\d{4}-\d\d-\d\d", d["date"]), d["date"]
    assert d["label"] == "HARNESS-gate-row-fixture" and d["branch"] == "feat"
    assert d["base_sha"] == fx["m1"] and d["candidate_sha"] == fx["head"]
    assert d["rc"] == "0" and d["queue_s"].isdigit()
    assert float(d["stage_s"]) >= 0
    assert [d[k] for k in ("product_lines", "test_lines", "docs_lines", "lab_lines")] == ["3", "2", "4", "5"]


def test_2_appends_the_same_row_to_the_runs_csv(fx, tmp_path):
    p = tmp_path / "g.csv"
    r, rows = _run(fx, p)
    assert rows and p.is_file(), f"{p} not written\n{r.stdout}{r.stderr}"
    assert p.read_text().splitlines()[-1] == rows[0][len("GATE row "):]
    _run(fx, p)
    assert len(p.read_text().splitlines()) >= 2, "second run must append, not overwrite"


def test_2_base_reject_still_writes_a_row_with_rc_1_and_the_stage(fx, tmp_path):
    _commit(fx["pusher"], {"m2.txt": 1})
    _git(fx["pusher"], "push", "-q", "origin", "main")
    r, rows = _run(fx, tmp_path / "g.csv", stop_after=None)
    assert r.returncode == 1 and len(rows) == 1, f"{rows!r}\n{r.stdout}{r.stderr}"
    d = dict(zip(COLS, _fields(rows[0])))
    assert d["rc"] == "1" and "base" in d["reject_stages"]


# audit finding 2 (HARNESS-mm-9): a multi-piece landing label is a comma list; unquoted it shifts every later column
# (every multi-piece landing so far is unreadable). The label field is csv-quoted: "A,B,C".
def test_2_multi_piece_label_is_csv_quoted_and_parses_to_14_fields(fx, tmp_path):
    p = tmp_path / "g.csv"
    r, rows = _run(fx, p, label="A,B,C")
    assert len(rows) == 1, f"GATE row lines: {rows!r}\n{r.stdout}{r.stderr}"
    f = _fields(rows[0])
    assert len(f) == 14, f"{len(f)} fields: {f}"
    d = dict(zip(COLS, f))
    assert d["label"] == "A,B,C" and d["branch"] == "feat" and d["rc"] == "0", d
    assert d["candidate_sha"] == fx["head"] and [d[k] for k in ("product_lines", "test_lines", "docs_lines", "lab_lines")] == ["3", "2", "4", "5"], d


def test_2_multi_piece_label_row_in_the_runs_csv_parses_the_same(fx, tmp_path):
    p = tmp_path / "g.csv"
    _run(fx, p, label="A,B,C")
    with open(p, newline="") as f:
        data = list(csv.reader(f))
    assert len(data) == 1 and len(data[0]) == 14 and data[0][1] == "A,B,C", data


def test_2_control_single_piece_label_is_written_unquoted(fx, tmp_path):
    p = tmp_path / "g.csv"
    r, rows = _run(fx, p, label="HARNESS-one")
    assert rows[0].startswith("GATE row ") and f",HARNESS-one,feat," in rows[0] and '"' not in rows[0], rows[0]


def test_2_default_suite_timeout_is_2400():
    text = SCRIPT.read_text()
    m = re.search(r'^SUITE_TIMEOUT="\$\{MERGE_GATE_SUITE_TIMEOUT:-(\d+)\}"', text, re.M)
    assert m, "SUITE_TIMEOUT default line not found"
    assert m.group(1) == "2400", f"default is {m.group(1)}"


def test_2_script_names_suite_timeout_in_a_reject_detail():
    assert "suite-timeout" in SCRIPT.read_text()


def test_2_timed_out_suite_regression_says_suite_timeout_not_a_traceback(tmp_path):
    repo = tmp_path / "r"
    (repo / "tests").mkdir(parents=True)
    (repo / "tests" / "test_slow.py").write_text("import time\n\ndef test_slow():\n    time.sleep(8)\n")
    (repo / "f.txt").write_text("a\n")
    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "base")
    (repo / "f.txt").write_text("b\n")
    diff = tmp_path / "d.diff"
    diff.write_text(_git(repo, "diff") + "\n")
    _git(repo, "checkout", "-q", "--", "f.txt")
    r = subprocess.run([sys.executable, str(SREG), str(repo), str(diff), "--python", sys.executable,
                        "--test-args", "tests", "--timeout", "1"], capture_output=True, text=True, timeout=120)
    out = r.stdout + r.stderr
    assert "suite-timeout 1s" in out, out[-600:]
    assert "Traceback" not in out and r.returncode != 0, out[-600:]
