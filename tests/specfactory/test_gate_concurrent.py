# spec: docs/northstar/plans/2026-10-07-visible-game-spec.md line 454 (piece HARNESS-gate-concurrent, lane H);
#       design B in docs/northstar/plans/harness/gate-parallel-scout.md
"""HARNESS-gate-concurrent: the merge gate keeps its single lock and runs its regression stages as background jobs.

Built AFTER HARNESS-csim-xdist and HARNESS-gate-reorder on the same branch. Every number and name below is the
piece paragraph's; the paragraph's expected-gain figure (NUMBER-NEEDED) is NOT tested: a timing claim waits for
the measurement report.

INTERFACES SHARED BY THE BUILDER AND THESE TESTS (verbatim from the paragraph; the tests are the contract)

1. "Each `regression` call becomes a background job (`&`) with its own log `$SCRATCH_ROOT/regression_<suite>.log`,
   its own `TMPDIR=$SCRATCH_ROOT/<suite>` and `XDG_DATA_HOME=$SCRATCH_ROOT/<suite>/xdg`; `wait` precedes the first
   `reject`/`ok` line of the block."  <suite> is csim, qa_t1, specfactory, transport, lab (confirmed names); the
   transport log is renamed regression_transport.log. Ruling (Architect, replacing the paragraph body): each job's
   TMPDIR and XDG_DATA_HOME directories are created with `mkdir -p` before the job is backgrounded.
2. Ruled shape (the paragraph's summary sentence): qa_t1 runs FIRST AND ALONE (its WALL_BUDGET 2.0 s detector shares
   CPU badly): it ends before the first of the other jobs starts. Then a FOUR-job concurrent block, csim,
   specfactory, transport, lab, then a single `wait` before the first reject/ok line of the block. "The main and
   candidate pytest passes of each suite run concurrently ... the per-stage [N.Ns] lines are kept." Outputs are
   printed after the wait in a fixed order (the order must not depend on which job finishes first); the verdict set
   is unchanged: a failing job still prints `GATE <stage> REJECT <its own log>`.
3. "Suites that self-build in the candidate (csim, qa/t1) are started after one `make -s libouroboros.so
   libouroboros_dbg.so` in the candidate and their conftests see it up to date (make is then a no-op)."
4. "`_store_cached_baseline` takes `fcntl.flock` on `<main_sha>.json.lock` around read-modify-write; test: two
   threads store two suite keys and both are present."  The lock file sits beside the cache file: the cache path
   with `.lock` appended.
5. "transport's base-pipe worktree (mg.sh:515-526) is built before the block."  The base-pipe worktree is the gate's
   `$SCRATCH_ROOT/mainpipe_base` (OM_MAIN_PIPE).
6. "Tests: a fixture with three stub suites runs them with overlapping timestamps; positive control: today's
   script runs them in series."

Fixture: the stub pattern of test_merge_gate.py (fake repo root whose scripts/specfactory symlinks every real file
except merge_gate_support.py). The stub merge_gate_support.py answers `regression` and `regression-lab` itself
(sleeps, records start/end/TMPDIR/XDG/log path/OM_MAIN_PIPE into $GC_TRACE/<suite>.json, prints a canned line, exits
with the requested rc) and hands every other subcommand to the real file. A `make` shim on PATH logs every make
call (time, cwd, args) to $GC_MAKELOG and execs /usr/bin/make. Runs cost a few seconds each (the stub sleeps).

Red on the base tree: tests 1, 1b, 2, 3 (x5), 3b, 3c, 4[transport], 8, 9, 10, 11 (the gate runs the stages in series,
no per-job TMPDIR/XDG, no lock, base pipe built after csim). Guards that stay green: 4 (four suites), 5, 6, 7 (log
names, [N.Ns] lines, fixed order, verdict set, one candidate make). Controls C1 to C3 are green.
"""
import fcntl
import json
import os
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent.parent
SPEC_DIR = REPO / "scripts" / "specfactory"
sys.path.insert(0, str(SPEC_DIR))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from gate_toy_root import overlay_sweeps, write_story  # noqa: E402
GATE_PATH = "/usr/bin:/bin:/home/westopoli/Projects/agora/.venv/bin"
SUITES = ("csim", "lab", "qa_t1", "specfactory", "transport")
BLOCK = ("csim", "specfactory", "transport", "lab")  # the four concurrent jobs; qa_t1 runs first and alone
CONTROL_SUITES = ("csim", "specfactory", "transport")  # the stubs C2 can drive by plain bash
VERDICT_STAGE = {"csim": "regression_csim", "lab": "regression_lab", "qa_t1": "regression_qa_t1",
                 "specfactory": "specfactory_regression", "transport": "transport"}
EQUAL_SLEEPS = {s: 2.0 for s in SUITES}
SKEWED_SLEEPS = {"csim": 0.5, "lab": 3.0, "qa_t1": 2.5, "specfactory": 1.5, "transport": 1.0}
GATE_TIMEOUT_S = 240
# Test-defect TD-HARNESS-gate-concurrent-1 (ruler Architect 2026-10-29): HARNESS-gate-reorder stops the gate before
# the regression block when any earlier stage REJECTs, and on this toy repo six stages reject for reasons that have
# nothing to do with concurrency (decisive line: `GATE early_exit REJECT allowlist_strict;sig_blocked;sig_check;
# reach_lint;status;placeholder_controls`). Same mechanism as test_gate_reorder.py's NOISY_TOOLS: stub those tools in
# the fake root. status_check.py joins them here because the fake root's docs/ is the real tree, whose lane table
# disagrees with the toy repo.
NOISY_TOOLS = ("alg_constants.py", "reach_lint.py", "sig_table.py", "status_check.py")
OK_STUB = "import sys\nsys.exit(0)\n"
REAL_SUPPORT_COPY = "merge_gate_support_real.py"

STUB_SUPPORT = '''\
import json, os, sys, time
from pathlib import Path
REAL = {real!r}
argv = sys.argv[1:]
if not argv or argv[0] not in ("regression", "regression-lab"):
    os.execv(sys.executable, [sys.executable, REAL, *argv])
names = {{"tests/csim": "csim", "tests/qa/t1": "qa_t1", "tests/specfactory": "specfactory", "tests/transport": "transport"}}
suite = "lab" if argv[0] == "regression-lab" else names[argv[3]]
start = time.time()
tmpdir, xdg = os.environ.get("TMPDIR", ""), os.environ.get("XDG_DATA_HOME", "")
rec = {{"suite": suite, "start": start, "tmpdir": tmpdir, "xdg": xdg,
        "tmpdir_exists": os.path.isdir(tmpdir), "xdg_exists": os.path.isdir(xdg),
        "log": os.readlink("/proc/self/fd/1"), "om_main_pipe": os.environ.get("OM_MAIN_PIPE", "")}}
rec["om_main_pipe_exec"] = bool(rec["om_main_pipe"]) and os.access(rec["om_main_pipe"], os.X_OK)
time.sleep(json.loads(os.environ["GC_SLEEPS"])[suite])
rec["end"] = time.time()
trace = Path(os.environ["GC_TRACE"]); trace.mkdir(exist_ok=True)
(trace / (suite + ".json")).write_text(json.dumps(rec))
rc = json.loads(os.environ["GC_RCS"]).get(suite, 0)
print(("REJECT " if rc else "") + "stub " + suite)
sys.exit(rc)
'''

MAKE_SHIM = '#!/bin/sh\nprintf \'%s|%s|%s\\n\' "$(date +%s.%N)" "$PWD" "$*" >> "$GC_MAKELOG"\nexec /usr/bin/make "$@"\n'

MAKEFILE = """\
libouroboros.so:
\ttouch $@
libouroboros_dbg.so:
\ttouch $@
pipe/ouroboros_pipe:
\tmkdir -p pipe && printf '#!/bin/sh\\n' > $@ && chmod +x $@
"""


def _git(repo, *args):
    return subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", "-c", "commit.gpgsign=false", *args],
                          cwd=repo, check=True, capture_output=True, text=True).stdout.strip()


def _fake_root(tmp_path):
    root = tmp_path / "fakeroot"
    (root / "scripts" / "specfactory").mkdir(parents=True)
    (root / "docs").symlink_to(REPO / "docs")
    overlay_sweeps(root)  # H-020: never the live sweeps.md
    for f in SPEC_DIR.iterdir():
        if f.name not in ("merge_gate_support.py", *NOISY_TOOLS):
            (root / "scripts" / "specfactory" / f.name).symlink_to(f)
    for name in NOISY_TOOLS:
        (root / "scripts" / "specfactory" / name).write_text(OK_STUB)
    # A real copy, not a symlink: the support file runs sig_table.py by its resolved path, so only a copy that
    # sits in the fake root calls the stub next to it. The stub support hands every other subcommand to the copy.
    real = root / "scripts" / "specfactory" / REAL_SUPPORT_COPY
    shutil.copy(SPEC_DIR / "merge_gate_support.py", real)
    stub = root / "scripts" / "specfactory" / "merge_gate_support.py"
    stub.write_text(STUB_SUPPORT.format(real=str(real)))
    return root, stub


def _fixture_repo(path):
    path.mkdir(parents=True)
    _git(path, "init", "-q")
    (path / "csrc").mkdir()
    (path / "csrc" / "stub.c").write_text("int om_stub(void) { return 0; }\n")
    (path / "Makefile").write_text(MAKEFILE)
    for d in ("tests/csim", "tests/qa/t1", "tests/transport"):
        (path / d).mkdir(parents=True)
    (path / "tests" / "transport" / "keep.txt").write_text("x\n")
    write_story(path, "B1")  # H-020
    _git(path, "add", "-A")
    _git(path, "commit", "-q", "-m", "base")
    _git(path, "remote", "add", "origin", str(path))
    _git(path, "update-ref", "refs/remotes/origin/main", "HEAD")
    return path


def _env(tmp_path, sleeps, rcs):
    shim = tmp_path / "shim"
    shim.mkdir(exist_ok=True)
    (shim / "make").write_text(MAKE_SHIM)
    (shim / "make").chmod(0o755)
    pieces = tmp_path / "pieces.toml"
    placeholders = tmp_path / "placeholders.txt"
    placeholders.write_text("")
    pieces.write_text('[[piece]]\nid = "B1"\nowns = ["csrc/stub.c"]\nacceptance = []\ndepends_on = []\n')
    return {"MERGE_GATE_PIECES": str(pieces), "PATH": f"{shim}:{GATE_PATH}", "GC_SLEEPS": json.dumps(sleeps),
            "GC_RCS": json.dumps(rcs), "GC_TRACE": str(tmp_path / "trace"), "GC_MAKELOG": str(tmp_path / "make.log"),
            "MERGE_GATE_PLACEHOLDERS": str(placeholders)}


def run_gate(tmp_path, sleeps, rcs=None):
    """Run the fake root's merge_gate.sh on the fixture repo, stamping each stdout line on arrival."""
    root, _ = _fake_root(tmp_path)
    repo = _fixture_repo(tmp_path / "repo")
    env = _env(tmp_path, sleeps, rcs or {})
    gate = root / "scripts" / "specfactory" / "merge_gate.sh"
    p = subprocess.Popen(["bash", str(gate), "--tier", "full", str(repo), "HEAD", "B1"], stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, env=env)
    timer = threading.Timer(GATE_TIMEOUT_S, p.kill)
    timer.start()
    lines = [(time.time(), ln.rstrip("\n")) for ln in p.stdout]
    p.wait()
    timer.cancel()
    trace = tmp_path / "trace"
    recs = {s: json.loads((trace / f"{s}.json").read_text()) for s in SUITES if (trace / f"{s}.json").exists()}
    makes = []
    if (tmp_path / "make.log").exists():
        for ln in (tmp_path / "make.log").read_text().splitlines():
            t, cwd, args = ln.split("|", 2)
            makes.append((float(t), cwd, args))
    return {"rc": p.returncode, "lines": lines, "recs": recs, "makes": makes,
            "out": "\n".join(t for _, t in lines)}


def have_common_instant(intervals):
    """True when every (start, end) interval is running at one shared instant."""
    return max(s for s, _ in intervals) < min(e for _, e in intervals)


def verdicts(run):
    """[(arrival time, stage, status, line)] of the gate's five regression-block verdict lines, in print order."""
    out = []
    for t, ln in run["lines"]:
        parts = ln.split(" ", 3)
        if len(parts) >= 3 and parts[0] == "GATE" and parts[1] in VERDICT_STAGE.values() and parts[2] in ("OK", "REJECT", "WARN"):
            out.append((t, parts[1], parts[2], ln))
    return out


@pytest.fixture(scope="module")
def equal_run(tmp_path_factory):
    run = run_gate(tmp_path_factory.mktemp("equal"), EQUAL_SLEEPS)
    assert set(run["recs"]) == set(SUITES), run["out"]  # the harness itself works: every stub ran
    return run


@pytest.fixture(scope="module")
def skewed_run(tmp_path_factory):
    run = run_gate(tmp_path_factory.mktemp("skewed"), SKEWED_SLEEPS)
    assert set(run["recs"]) == set(SUITES), run["out"]
    return run


@pytest.fixture(scope="module")
def reject_run(tmp_path_factory):
    run = run_gate(tmp_path_factory.mktemp("reject"), EQUAL_SLEEPS, {"csim": 1, "specfactory": 1})
    assert set(run["recs"]) == set(SUITES), run["out"]
    return run


# ------------------------------------------------------------------ positive controls (green on the base tree)

def test_c1_overlap_detector_reads_serial_as_serial_and_overlap_as_overlap():
    """Control for tests 1, 1b and 2 (paragraph clause "positive control: today's script runs them in series")."""
    assert have_common_instant([(0.0, 2.0), (0.1, 2.1), (0.2, 2.2)])
    assert not have_common_instant([(0.0, 2.0), (2.0, 4.0), (4.0, 6.0)])


def test_c2_stub_suites_measure_series_and_overlap_correctly(tmp_path):
    """Control for tests 1 and 2: the same stub script, run by plain bash in series and then as background jobs,
    yields disjoint and then overlapping timestamps; so a red test 1 means the gate runs them in series."""
    root, stub = _fake_root(tmp_path)
    env = {**_env(tmp_path, {s: 1.0 for s in SUITES}, {}), "TMPDIR": str(tmp_path)}
    cmds = [f'"{sys.executable}" "{stub}" regression c b tests/{p}' for p in CONTROL_SUITES]
    for mode, sep, tail in (("series", ";", ""), ("background", " &", "wait")):
        for f in (tmp_path / "trace").glob("*.json"):
            f.unlink()
        script = (sep + " ").join(cmds) + (" & wait" if mode == "background" else "")
        subprocess.run(["bash", "-c", script], env=env, check=True, capture_output=True)
        recs = [json.loads((tmp_path / "trace" / f"{s}.json").read_text()) for s in CONTROL_SUITES]
        assert have_common_instant([(r["start"], r["end"]) for r in recs]) == (mode == "background"), (mode, recs)


def test_c3_fixture_gate_runs_all_five_stubs_to_a_verdict(equal_run):
    """Control: the stub harness reaches the regression block and every stub answered its verdict line."""
    assert [v[1] for v in verdicts(equal_run)] and {v[1] for v in verdicts(equal_run)} == set(VERDICT_STAGE.values()), \
        equal_run["out"]


# ------------------------------------------------------------------ the mechanism (red on the base tree)

def test_1_the_four_block_jobs_run_side_by_side(equal_run):
    """HARNESS-gate-concurrent: csim, specfactory, transport and lab run side by side (stub suites with overlapping
    timestamps; ruled four-job block). Red today: the gate runs the stages one after the other."""
    iv = {s: (equal_run["recs"][s]["start"], equal_run["recs"][s]["end"]) for s in BLOCK}
    assert have_common_instant(list(iv.values())), f"stub intervals {iv}: the four suites never run at the same instant"


def test_1b_qa_t1_runs_first_and_alone(equal_run):
    """HARNESS-gate-concurrent (ruled): qa_t1 "runs FIRST AND ALONE": it ends before the first of the four block
    jobs starts. Red today: the gate runs csim and lab before it and specfactory after it."""
    q = equal_run["recs"]["qa_t1"]
    first = min(equal_run["recs"][s]["start"] for s in BLOCK)
    assert q["end"] <= first, f"qa_t1 ran {q['start']:.2f}..{q['end']:.2f}, first block job started {first:.2f}"


def test_2_wait_precedes_the_first_verdict_line_of_the_block(equal_run):
    """HARNESS-gate-concurrent: "`wait` precedes the first `reject`/`ok` line of the block" (the four-job block;
    qa_t1's own line is not part of it). Red today: the first block verdict line prints when csim ends, while the
    other jobs have not started."""
    first = min(v[0] for v in verdicts(equal_run) if v[1] != VERDICT_STAGE["qa_t1"])
    last_end = max(equal_run["recs"][s]["end"] for s in BLOCK)
    assert first >= last_end - 0.05, f"first verdict line at {first:.2f}, last job ended {last_end:.2f}"


@pytest.mark.parametrize("suite", SUITES)
def test_3_each_job_has_its_own_tmpdir_and_xdg(equal_run, suite):
    """HARNESS-gate-concurrent: each job runs with "its own `TMPDIR=$SCRATCH_ROOT/<suite>` and
    `XDG_DATA_HOME=$SCRATCH_ROOT/<suite>/xdg`" (the scratch root is the directory of the job's own log)."""
    r = equal_run["recs"][suite]
    scratch = os.path.dirname(r["log"])
    assert r["tmpdir"] == f"{scratch}/{suite}", f"TMPDIR={r['tmpdir']!r}"
    assert r["xdg"] == f"{scratch}/{suite}/xdg", f"XDG_DATA_HOME={r['xdg']!r}"


def test_3b_the_job_directories_exist_when_the_job_starts(equal_run):
    """HARNESS-gate-concurrent: the same clause; a job's TMPDIR and XDG_DATA_HOME must be usable at start."""
    bad = {s: (r["tmpdir_exists"], r["xdg_exists"]) for s, r in equal_run["recs"].items()
           if not (r["tmpdir_exists"] and r["xdg_exists"])}
    assert not bad, f"missing directories at job start (tmpdir, xdg): {bad}"


def test_3c_no_two_jobs_share_a_tmpdir_or_xdg(equal_run):
    """HARNESS-gate-concurrent: the same clause, "each in its own scratch and XDG"."""
    tmp = [r["tmpdir"] for r in equal_run["recs"].values()]
    xdg = [r["xdg"] for r in equal_run["recs"].values()]
    assert len(set(tmp)) == len(SUITES) and len(set(xdg)) == len(SUITES), f"TMPDIR {tmp} XDG {xdg}"
    assert "" not in tmp and "" not in xdg


# ------------------------------------------------------------------ guards (green on the base tree, stay green)

@pytest.mark.parametrize("suite", SUITES)
def test_4_each_job_logs_to_regression_suite_log(equal_run, suite):
    """HARNESS-gate-concurrent: "its own log `$SCRATCH_ROOT/regression_<suite>.log`". Guard for csim, lab, qa_t1,
    specfactory; red-then-green for transport (today its log is transport.log)."""
    assert os.path.basename(equal_run["recs"][suite]["log"]) == f"regression_{suite}.log"


def test_5_stage_lines_keep_their_timing_and_print_order_does_not_follow_finish_order(equal_run, skewed_run):
    """HARNESS-gate-concurrent: "the per-stage [N.Ns] lines are kept" and outputs print "in fixed order". Guard:
    every verdict line ends in [N.Ns]; the sequence of the five lines is the same when the jobs finish in a
    different order (SKEWED_SLEEPS finishes csim first and lab last)."""
    for v in verdicts(equal_run) + verdicts(skewed_run):
        assert v[3].rstrip().endswith("s]") and "[" in v[3], v[3]
    assert [v[1] for v in verdicts(equal_run)] == [v[1] for v in verdicts(skewed_run)]


def test_6_verdict_set_is_unchanged_and_each_line_carries_its_own_log(reject_run):
    """HARNESS-gate-concurrent: "the verdict set unchanged". Guard: csim and specfactory stubs fail; exactly their
    lines are REJECT, each with its own log text, and the other three stay OK."""
    by_stage = {v[1]: v for v in verdicts(reject_run)}
    for suite in SUITES:
        v = by_stage[VERDICT_STAGE[suite]]
        failing = suite in ("csim", "specfactory")
        assert v[2] == ("REJECT" if failing else "OK"), v[3]
        assert f"stub {suite}" in v[3] and sum(f"stub {s}" in v[3] for s in SUITES) == 1, v[3]
    # the gate's exit code is not asserted: the fixture repo trips other stages (allowlist_strict, sig_table, ...)


def test_7_one_candidate_make_of_the_libs_precedes_every_job(equal_run):
    """HARNESS-gate-concurrent: "started after one `make -s libouroboros.so libouroboros_dbg.so` in the
    candidate". Guard (today's stage 1 make already satisfies it): exactly one make call names both libs, and it
    finishes logging before the earliest job starts."""
    libs = [m for m in equal_run["makes"] if {"libouroboros.so", "libouroboros_dbg.so"} <= set(m[2].split())]
    assert len(libs) == 1, equal_run["makes"]
    assert libs[0][0] < min(r["start"] for r in equal_run["recs"].values())


# ------------------------------------------------------------------ the rest of the mechanism (red on the base tree)

def test_8_transport_base_pipe_worktree_is_built_before_the_block(equal_run):
    """HARNESS-gate-concurrent: "transport's base-pipe worktree is built before the block". Red today: the
    mainpipe_base make runs in the transport stage, after csim, lab, qa_t1 and specfactory have run."""
    base = [m for m in equal_run["makes"] if m[1].endswith("/mainpipe_base") and "pipe/ouroboros_pipe" in m[2]]
    assert base, equal_run["makes"]
    first_job = min(equal_run["recs"][s]["start"] for s in BLOCK)
    assert base[0][0] < first_job, f"base-pipe make at {base[0][0]:.2f}, first block job started {first_job:.2f}"
    assert equal_run["recs"]["transport"]["om_main_pipe_exec"]


def test_9_main_and_candidate_passes_of_a_suite_run_concurrently(tmp_path):
    """HARNESS-gate-concurrent: "The main and candidate pytest passes of each suite run concurrently". The
    stub suite's one test sleeps 2 s and records its file path; `merge_gate_support.py regression` runs it
    on the base-ref worktree and on the candidate. Red today: the two passes run one after the other."""
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q")
    (repo / "tests" / "stub").mkdir(parents=True)
    (repo / "tests" / "stub" / "test_t.py").write_text(
        "import os, time, pathlib\n"
        "def test_t():\n"
        "    t0 = time.time(); time.sleep(2)\n"
        "    d = pathlib.Path(os.environ['GC_TRACE']); d.mkdir(exist_ok=True)\n"
        "    (d / (str(abs(hash(__file__))) + '.json')).write_text(repr((t0, time.time(), __file__)))\n")
    write_story(repo, "B1")  # H-020 (this test runs no gate; named by the story)
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "base")
    (repo / "note.txt").write_text("x\n")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "candidate")
    trace = tmp_path / "trace"
    r = subprocess.run([sys.executable, str(SPEC_DIR / "merge_gate_support.py"), "regression", str(repo), "HEAD~1",
                        "tests/stub", "--python", sys.executable, "--timeout", "120"],
                       cwd=str(repo), capture_output=True, text=True, timeout=120,
                       env={**os.environ, "GC_TRACE": str(trace)})
    spans = [eval(f.read_text()) for f in trace.glob("*.json")]
    assert len(spans) == 2, (r.stdout, r.stderr, spans)
    assert have_common_instant([(a, b) for a, b, _ in spans]), f"base and candidate passes ran in series: {spans}"


# ------------------------------------------------------------------ _store_cached_baseline lock

def _result():
    import suite_regression as sr
    return sr.RunResult(passed=1, failed=0, failing_ids=(), wall_s=0.0, returncode=0)


def test_10_store_cached_baseline_blocks_while_the_lock_file_is_held(tmp_path):
    """HARNESS-gate-concurrent: "`_store_cached_baseline` takes `fcntl.flock` on `<main_sha>.json.lock` around
    read-modify-write". Deterministic form: hold LOCK_EX on `<cache>.lock`; a store must not complete until it is
    released. Red today: the store ignores the lock and finishes at once."""
    import merge_gate_support as mgs
    cache = tmp_path / "baseline_cache" / "abc123.json"
    cache.parent.mkdir()
    lock_path = Path(str(cache) + ".lock")
    with open(lock_path, "w") as lk:
        fcntl.flock(lk, fcntl.LOCK_EX)
        t = threading.Thread(target=mgs._store_cached_baseline, args=(cache, "h", "abc123", "tests/csim", _result()))
        t.start()
        time.sleep(0.6)
        blocked = t.is_alive() and not cache.exists()
        fcntl.flock(lk, fcntl.LOCK_UN)
    t.join(10)
    assert blocked, "the store finished while another holder had the .lock file locked"
    assert not t.is_alive() and json.loads(cache.read_text())["suites"].keys() == {"tests/csim"}


def test_11_two_threads_storing_two_suite_keys_leave_both_present(tmp_path):
    """HARNESS-gate-concurrent: the paragraph's named test, "two threads store two suite keys and both are
    present", repeated over fresh caches with a barrier so the two read-modify-writes collide. Race-dependent
    on today's code (a lost entry or a clash on the shared .json.tmp name); the lock makes it hold every round."""
    import merge_gate_support as mgs
    bad = []
    for i in range(60):
        cache = tmp_path / f"c{i}" / f"sha{i}.json"
        cache.parent.mkdir()
        barrier = threading.Barrier(2)
        errors = []

        def store(key):
            try:
                barrier.wait()
                mgs._store_cached_baseline(cache, "h", f"sha{i}", key, _result())
            except Exception as e:  # a clash on the temp file surfaces here
                errors.append(repr(e))
        ts = [threading.Thread(target=store, args=(k,)) for k in ("tests/csim", "tests/specfactory")]
        [t.start() for t in ts]
        [t.join() for t in ts]
        try:
            have = set(json.loads(cache.read_text())["suites"])
        except (OSError, ValueError):  # a missing or torn cache file is a lost entry
            have = set()
        if errors or have != {"tests/csim", "tests/specfactory"}:
            bad.append((i, sorted(have), errors))
    assert not bad, f"{len(bad)} of 60 rounds lost a suite key or raised: {bad[:3]}"
