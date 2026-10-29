"""HARNESS-csim-xdist (lane H): the csim and transport stages of the merge gate run under pytest-xdist.

Source: docs/northstar/plans/2026-10-07-visible-game-spec.md, the HARNESS-csim-xdist paragraph (line 442).
Tests-first, written before the builder; every case names the clause it proves. pytest-xdist is NOT installed
in the harness venvs, so nothing here needs it: the conftest hooks are driven with fake config objects, the
`regression` subcommand with a stub python that logs its argv, merge_gate.sh is read as text.

INTERFACES SHARED BY THE BUILDER AND THESE TESTS (verbatim from the paragraph unless marked [test])

1. tests/csim/conftest.py
   * env var OM_CSIM_LIB      path of the release library; OM_CSIM_LIB_DBG path of the debug library.
   * `LIB_PATH` and `DBG_LIB_PATH` read OM_CSIM_LIB / OM_CSIM_LIB_DBG when set, else today's paths
     (<repo>/libouroboros.so, <repo>/libouroboros_dbg.so): a bare `pytest tests/csim`, `-p no:xdist` and
     `-n 0` are unchanged.
   * the import-time build (the module-level `_build_libs()` call, `make -s libouroboros.so libouroboros_dbg.so`)
     is skipped when OM_CSIM_LIB is set.
   * hook `pytest_configure(config)`: the CONTROLLER (no worker_id) when xdist really distributes copies both
     built libraries into the directory $TMPDIR/om_csim_<pid> (<pid> = the main process id) and exports
     OM_CSIM_LIB and OM_CSIM_LIB_DBG pointing at the copies; it calls no second make (the build is the
     import-time one). Hook `pytest_unconfigure(config)` removes that directory.
   * a build failure reaches the workers through the env var OM_CSIM_BUILD_ERROR (the controller exports the
     text of conftest.BUILD_ERROR; a worker's conftest.BUILD_ERROR is that text).
   * Workers inherit the environment, do not run the conftest's make, and load the two exported paths.
2. scripts/specfactory/merge_gate_support.py `regression` gains `--pytest-extra '<args>'`: split with shlex,
   passed as `extra_args` to both suite_regression.run_pytest calls (base and candidate), and appended to
   `suite_key`, so a cached baseline from a different flag set is a miss. run_pytest's argv is
   [python, -m, pytest, -q, -p, no:cacheprovider, *extra_args, *test_args].
3. scripts/specfactory/merge_gate.sh: the csim `regression` call passes `--pytest-extra '-n 5 --dist loadfile'`
   (DRAFT-xdist-workers = 5); the transport call passes `--pytest-extra '-n 2'`; no other regression call does.
4. scripts/specfactory/requirements.txt gains the line `pytest-xdist>=3.6,<4`.

5. Detection (ruled by the Architect, 2026-10-29). Worker = hasattr(config, "workerinput") OR env
   PYTEST_XDIST_WORKER set (either is enough). Controller = no workerinput AND
   config.getoption("numprocesses", 0) truthy AND config.getoption("dist", "no") != "no". Anything else (bare
   pytest, -p no:xdist, -n 0) is neither and runs today's path. The fakes below give a consistent picture on
   all of these. [test] the hook module is loaded by file path, not as a pytest plugin.
6. MERGE_GATE_CSIM_XDIST (ruled 2026-10-29): when set to 0, merge_gate.sh omits the --pytest-extra arguments
   of the csim and transport regression calls, so those stages run the serial command; unset, they carry
   `-n 5 --dist loadfile` and `-n 2`.

UNTESTED (cannot be proved without xdist installed, or are not unit-provable):
   * real distribution: that `-n 5 --dist loadfile` keeps a file's tests on one worker and the csim suite gives
     the same verdict alone and under loadfile (the paragraph's own once-only run of the whole suite both ways).
   * the expected gain (40 min to under 10) and test_PP_move_collision_a5.py / test_PP_portability.py /
     the two E17 S186 files, which the paragraph says stay as they are.

Cases marked CONTROL are green on the built tree and pair with a RED case that proves the new mechanism.
"""
import json
import os
import shlex
import shutil
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
SPECFACTORY = REPO / "scripts" / "specfactory"
SUPPORT = SPECFACTORY / "merge_gate_support.py"
GATE = SPECFACTORY / "merge_gate.sh"
REQUIREMENTS = SPECFACTORY / "requirements.txt"
REAL_CONFTEST = REPO / "tests" / "csim" / "conftest.py"
sys.path.insert(0, str(SPECFACTORY))

import suite_regression as sr  # noqa: E402

PY = sys.executable
SUITE = "tests/t"
CSIM_EXTRA = "-n 5 --dist loadfile"


def _git(repo, *args):
    return subprocess.run(["git", "-c", "user.email=g@t", "-c", "user.name=g", *args], cwd=repo, check=True,
                          capture_output=True, text=True).stdout.strip()


def _env(extra=None):
    e = {k: v for k, v in os.environ.items()
         if k not in ("MERGE_GATE_BASELINE_CACHE", "MALLOC_PERTURB_", "OM_CSIM_LIB", "OM_CSIM_LIB_DBG",
                      "OM_CSIM_BUILD_ERROR", "PYTEST_XDIST_WORKER")}
    e.update(extra or {})
    return e


# ------------------------------------------------------------------ regression --pytest-extra (mgs + sr)

@pytest.fixture
def stub(tmp_path):
    """A stub `python`: logs argv[1:] as one JSON line per call to STUB_LOG and prints a passing pytest summary."""
    log = tmp_path / "argv.log"
    script = tmp_path / "stubpy"
    script.write_text(f"#!{PY}\nimport json, os, sys\n"
                      "open(os.environ['STUB_LOG'], 'a').write(json.dumps(sys.argv[1:]) + '\\n')\n"
                      "print('1 passed in 0.01s')\n")
    script.chmod(0o755)

    def calls():
        return [json.loads(l) for l in log.read_text().splitlines()] if log.exists() else []
    return {"python": str(script), "log": log, "calls": calls}


@pytest.fixture
def repo(tmp_path):
    """main commit M and a candidate commit on branch feat (repo is checked out at feat)."""
    r = tmp_path / "repo"
    r.mkdir()
    _git(r, "init", "-q", "-b", "main")
    (r / "tests" / "t").mkdir(parents=True)
    (r / "tests" / "t" / "test_a.py").write_text("def test_a():\n    assert True\n")
    _git(r, "add", "-A")
    _git(r, "commit", "-q", "-m", "m")
    m = _git(r, "rev-parse", "HEAD")
    _git(r, "checkout", "-q", "-b", "feat")
    (r / "note.txt").write_text("x\n")
    _git(r, "add", "-A")
    _git(r, "commit", "-q", "-m", "cand")
    return {"dir": r, "base": m, "root": tmp_path / "merge"}


def _regress(repo, stub, tmp_path, *extra_cli):
    return subprocess.run(
        [PY, str(SUPPORT), "regression", str(repo["dir"]), repo["base"], SUITE, "--python", stub["python"],
         "--no-junit", "--merge-root", str(repo["root"]), *extra_cli],
        capture_output=True, text=True, timeout=120,
        env=_env({"STUB_LOG": str(stub["log"]), "TMPDIR": str(tmp_path)}))


def test_C_run_pytest_argv_with_extra_args(stub, tmp_path, monkeypatch):
    """CONTROL for HARNESS-csim-xdist (positive control clause): run_pytest's argv is
    [-m pytest -q -p no:cacheprovider -n 5 --dist loadfile tests/t]."""
    monkeypatch.setenv("STUB_LOG", str(stub["log"]))
    sr.run_pytest(tmp_path, stub["python"], [SUITE], 60, extra_args=CSIM_EXTRA.split())
    assert stub["calls"]() == [["-m", "pytest", "-q", "-p", "no:cacheprovider", "-n", "5", "--dist", "loadfile",
                                SUITE]]


def test_1_pytest_extra_reaches_both_runs_after_cacheprovider(repo, stub, tmp_path):
    """HARNESS-csim-xdist, `regression` gains `--pytest-extra`: `--pytest-extra '-n 5 --dist loadfile'` is split
    and passed to the base run and the candidate run, after `no:cacheprovider`, before the test args."""
    r = _regress(repo, stub, tmp_path, "--pytest-extra", CSIM_EXTRA)
    assert r.returncode == 0, r.stderr[-400:]
    want = ["-m", "pytest", "-q", "-p", "no:cacheprovider", "-n", "5", "--dist", "loadfile", SUITE]
    assert stub["calls"]() == [want, want]


def test_2_pytest_extra_is_split_with_shlex(repo, stub, tmp_path):
    """HARNESS-csim-xdist, `split with shlex`: a quoted element stays one argv element."""
    r = _regress(repo, stub, tmp_path, "--pytest-extra", "-k 'a or b' -n 2")
    assert r.returncode == 0, r.stderr[-400:]
    for argv in stub["calls"]():
        assert argv[5:9] == ["-k", "a or b", "-n", "2"], argv


def test_C_no_pytest_extra_leaves_argv_unchanged(repo, stub, tmp_path):
    """CONTROL for HARNESS-csim-xdist: without --pytest-extra the argv carries no extra args (bare gate
    unchanged for the other stages)."""
    r = _regress(repo, stub, tmp_path)
    assert r.returncode == 0, r.stderr[-400:]
    plain = ["-m", "pytest", "-q", "-p", "no:cacheprovider", SUITE]
    assert stub["calls"]() == [plain, plain]


def test_3_suite_key_includes_extra_args_so_other_flags_miss(repo, stub, tmp_path):
    """HARNESS-csim-xdist, `appended to suite_key so a cached baseline from a different flag set is a miss`:
    same flags hit; different flags and no flags are misses; the cache holds a key containing the flags."""
    first = _regress(repo, stub, tmp_path, "--pytest-extra", CSIM_EXTRA)
    assert first.returncode == 0, first.stderr[-400:]
    assert f"baseline: computed {repo['base']}" in first.stdout
    again = _regress(repo, stub, tmp_path, "--pytest-extra", CSIM_EXTRA)
    assert f"baseline: cached {repo['base']}" in again.stdout, again.stdout
    other = _regress(repo, stub, tmp_path, "--pytest-extra", "-n 2")
    assert f"baseline: computed {repo['base']}" in other.stdout, other.stdout
    none = _regress(repo, stub, tmp_path)
    assert f"baseline: computed {repo['base']}" in none.stdout, none.stdout
    keys = list(json.loads((repo["root"] / "baseline_cache" / f"{repo['base']}.json").read_text())["suites"])
    assert any(CSIM_EXTRA in k for k in keys), keys
    assert SUITE in keys, keys


def test_C_same_plain_key_hits_without_extra(repo, stub, tmp_path):
    """CONTROL for the suite_key clause: with no --pytest-extra the second run is a cache hit as today."""
    _regress(repo, stub, tmp_path)
    again = _regress(repo, stub, tmp_path)
    assert f"baseline: cached {repo['base']}" in again.stdout, again.stdout


# ------------------------------------------------------------------ merge_gate.sh, requirements.txt

def _regression_calls():
    """Logical lines (backslash continuations joined) of merge_gate.sh that invoke `merge_gate_support.py
    regression`, as shlex token lists keyed by the first tests/ argument."""
    text = GATE.read_text().replace("\\\n", " ")
    calls = {}
    for line in text.splitlines():
        if 'merge_gate_support.py" regression ' in line and "regression-lab" not in line:
            toks = shlex.split(line.split("#")[0])
            tests = next(t for t in toks if t.startswith("tests/"))
            calls[tests] = toks
    return calls


def _extra_of(toks):
    return toks[toks.index("--pytest-extra") + 1] if "--pytest-extra" in toks else None


def test_C_gate_has_csim_transport_and_other_regression_calls():
    """CONTROL for the merge_gate.sh clauses: the reader finds the csim, transport, qa/t1 and specfactory
    regression calls (so the red cases below fail on the flag, not on the parser)."""
    assert {"tests/csim", "tests/transport", "tests/qa/t1", "tests/specfactory"} <= set(_regression_calls())


def test_4_gate_csim_stage_passes_n5_loadfile():
    """HARNESS-csim-xdist, `mg.sh:333 passes --pytest-extra '-n 5 --dist loadfile'` (DRAFT-xdist-workers)."""
    assert _extra_of(_regression_calls()["tests/csim"]) == CSIM_EXTRA


def test_5_gate_transport_stage_passes_n2():
    """HARNESS-csim-xdist, `the transport call --pytest-extra '-n 2'`."""
    assert _extra_of(_regression_calls()["tests/transport"]) == "-n 2"


def test_6_no_other_gate_regression_call_gets_xdist_flags():
    """HARNESS-csim-xdist: only the csim and transport stages change; qa/t1 and specfactory regression calls
    carry no --pytest-extra. Red until the csim stage carries it (otherwise vacuous)."""
    calls = _regression_calls()
    assert _extra_of(calls["tests/csim"]) is not None, "csim stage has no --pytest-extra yet"
    assert [_extra_of(calls[k]) for k in ("tests/qa/t1", "tests/specfactory")] == [None, None]


def test_7_requirements_gain_pytest_xdist_line():
    """HARNESS-csim-xdist, `scripts/specfactory/requirements.txt (the line pytest-xdist>=3.6,<4)`."""
    assert "pytest-xdist>=3.6,<4" in REQUIREMENTS.read_text().splitlines()


def test_C_requirements_keep_pyyaml_line():
    """CONTROL for the requirements clause: the existing line is still there, one requirement per line."""
    assert "PyYAML>=6.0" in REQUIREMENTS.read_text().splitlines()


# ------------------------------------------------------------------ tests/csim/conftest.py

DRIVER = textwrap.dedent('''
    import importlib.util, json, os, sys, types
    from pathlib import Path
    spec = importlib.util.spec_from_file_location("csim_conftest_under_test", sys.argv[1])
    mod = importlib.util.module_from_spec(spec)
    sys.modules["csim_conftest_under_test"] = mod
    spec.loader.exec_module(mod)

    def fake_config(dist, worker):
        opt = types.SimpleNamespace(numprocesses=5 if dist else 0, dist="loadfile" if dist else "no")
        cfg = types.SimpleNamespace(option=opt,
            getoption=lambda name, default=None: getattr(opt, name.lstrip("-").replace("-", "_"), default),
            pluginmanager=types.SimpleNamespace(hasplugin=lambda n: True, getplugin=lambda n: object()))
        if worker:
            cfg.workerinput = {"workerid": "gw1", "workercount": 5}
        return cfg

    out = {"has_configure": hasattr(mod, "pytest_configure"), "has_unconfigure": hasattr(mod, "pytest_unconfigure"),
           "make_after_import": int(Path(os.environ["STUB_COUNT"]).read_text() or 0) if Path(os.environ["STUB_COUNT"]).exists() else 0,
           "lib_path": str(mod.LIB_PATH), "dbg_path": str(mod.DBG_LIB_PATH), "build_error": mod.BUILD_ERROR}
    mode = sys.argv[2]
    if mode in ("controller", "plain"):
        cfg = fake_config(dist=(mode == "controller"), worker=False)
        if out["has_configure"]:
            mod.pytest_configure(cfg)
        out["env_lib"] = os.environ.get("OM_CSIM_LIB")
        out["env_dbg"] = os.environ.get("OM_CSIM_LIB_DBG")
        out["env_err"] = os.environ.get("OM_CSIM_BUILD_ERROR")
        out["lib_text"] = Path(out["env_lib"]).read_text() if out["env_lib"] and Path(out["env_lib"]).exists() else None
        out["dbg_text"] = Path(out["env_dbg"]).read_text() if out["env_dbg"] and Path(out["env_dbg"]).exists() else None
        out["libdir"] = str(Path(out["env_lib"]).parent) if out["env_lib"] else None
        out["pid"] = os.getpid()
        out["make_after_configure"] = int(Path(os.environ["STUB_COUNT"]).read_text() or 0) if Path(os.environ["STUB_COUNT"]).exists() else 0
        if out["has_unconfigure"]:
            mod.pytest_unconfigure(cfg)
        out["libdir_exists_after_unconfigure"] = bool(out["libdir"]) and Path(out["libdir"]).exists()
    elif mode == "worker":
        cfg = fake_config(dist=True, worker=True)
        before = dict(os.environ)
        if out["has_configure"]:
            mod.pytest_configure(cfg)
        out["env_changed"] = dict(os.environ) != before
        out["make_after_configure"] = int(Path(os.environ["STUB_COUNT"]).read_text() or 0) if Path(os.environ["STUB_COUNT"]).exists() else 0
        out["tmp_dirs"] = sorted(p.name for p in Path(os.environ["TMPDIR"]).glob("om_csim_*"))
    print("RESULT" + json.dumps(out))
''')


@pytest.fixture
def cx(tmp_path):
    """A fixture tree holding a copy of the real tests/csim/conftest.py, a csrc/x.c, and a stub `make` on PATH
    that counts its calls and writes RELEASE / DEBUG into libouroboros.so / libouroboros_dbg.so in its cwd
    (or, with STUB_MAKE_FAIL set, prints `compile boom` on stderr and exits 1)."""
    tree = tmp_path / "tree"
    (tree / "tests" / "csim").mkdir(parents=True)
    (tree / "csrc").mkdir()
    (tree / "csrc" / "x.c").write_text("int x;\n")
    shutil.copy(REAL_CONFTEST, tree / "tests" / "csim" / "conftest.py")
    bindir = tmp_path / "bin"
    bindir.mkdir()
    make = bindir / "make"
    make.write_text("#!/bin/sh\n"
                    'n=$(cat "$STUB_COUNT" 2>/dev/null || echo 0); echo $((n+1)) > "$STUB_COUNT"\n'
                    '[ -n "$STUB_MAKE_FAIL" ] && { echo "compile boom" >&2; exit 1; }\n'
                    "printf RELEASE > libouroboros.so; printf DEBUG > libouroboros_dbg.so\n")
    make.chmod(0o755)
    tmpdir = tmp_path / "tmpdir"
    tmpdir.mkdir()
    driver = tmp_path / "driver.py"
    driver.write_text(DRIVER)

    def run(mode, env_extra=None):
        (tmp_path / "make_count").unlink(missing_ok=True)  # one counter per driver process
        env = _env({"PATH": f"{bindir}:{os.environ['PATH']}", "STUB_COUNT": str(tmp_path / "make_count"),
                    "TMPDIR": str(tmpdir), **(env_extra or {})})
        r = subprocess.run([PY, str(driver), str(tree / "tests" / "csim" / "conftest.py"), mode],
                           capture_output=True, text=True, env=env, timeout=120, cwd=str(tmp_path))
        lines = [l for l in r.stdout.splitlines() if l.startswith("RESULT")]
        assert lines, f"driver failed: {r.stderr[-800:]}"
        return json.loads(lines[-1][len("RESULT"):]), tree, tmpdir
    return run


def test_C_bare_import_runs_make_and_uses_repo_paths(cx):
    """CONTROL for HARNESS-csim-xdist (`positive control: today's conftest calls make in every process`):
    with no OM_CSIM_LIB the import-time build runs make once and LIB_PATH / DBG_LIB_PATH are the repo-root
    paths, so a bare `pytest tests/csim`, `-p no:xdist` and `-n 0` are unchanged."""
    out, tree, _ = cx("plain")
    assert out["make_after_import"] == 1
    assert out["lib_path"] == str(tree / "libouroboros.so")
    assert out["dbg_path"] == str(tree / "libouroboros_dbg.so")


def test_8_worker_import_skips_make_and_loads_exported_paths(cx, tmp_path):
    """HARNESS-csim-xdist, `import-time build is guarded and skipped when OM_CSIM_LIB is set` and `LIB_PATH and
    DBG_LIB_PATH read their variable when set`: a worker (env carries OM_CSIM_LIB / OM_CSIM_LIB_DBG) calls make
    zero times and loads those two paths."""
    env = {"OM_CSIM_LIB": str(tmp_path / "l" / "a.so"), "OM_CSIM_LIB_DBG": str(tmp_path / "l" / "b.so"),
           "PYTEST_XDIST_WORKER": "gw1"}
    out, _, _ = cx("worker", env)
    assert out["make_after_import"] == 0, "make ran in a process that has OM_CSIM_LIB set"
    assert out["lib_path"] == env["OM_CSIM_LIB"]
    assert out["dbg_path"] == env["OM_CSIM_LIB_DBG"]


def test_9_worker_configure_hook_builds_and_exports_nothing(cx, tmp_path):
    """HARNESS-csim-xdist, `a pytest_configure hook that runs when worker_id is absent`: with a worker config
    the hook exists, makes no copy directory, changes no env var and calls no make."""
    env = {"OM_CSIM_LIB": str(tmp_path / "l" / "a.so"), "OM_CSIM_LIB_DBG": str(tmp_path / "l" / "b.so"),
           "PYTEST_XDIST_WORKER": "gw1"}
    out, _, _ = cx("worker", env)
    assert out["has_configure"], "tests/csim/conftest.py has no pytest_configure hook"
    assert out["make_after_configure"] == 0 and out["tmp_dirs"] == [] and out["env_changed"] is False


def test_10_controller_copies_libs_to_tmpdir_pid_dir_and_exports(cx):
    """HARNESS-csim-xdist, controller hook: with xdist distributing, both built libraries are copied to
    $TMPDIR/om_csim_<pid> and OM_CSIM_LIB / OM_CSIM_LIB_DBG point at the copies; the hook calls no second make."""
    out, tree, tmpdir = cx("controller")
    assert out["has_configure"], "tests/csim/conftest.py has no pytest_configure hook"
    assert out["libdir"] == str(tmpdir / f"om_csim_{out['pid']}")
    assert (out["lib_text"], out["dbg_text"]) == ("RELEASE", "DEBUG")
    assert out["env_lib"] != str(tree / "libouroboros.so") and out["env_dbg"] != str(tree / "libouroboros_dbg.so")
    assert out["make_after_import"] == 1 and out["make_after_configure"] == 1


def test_11_unconfigure_removes_the_copy_directory(cx):
    """HARNESS-csim-xdist, `removed in pytest_unconfigure`: after the controller's pytest_unconfigure the
    $TMPDIR/om_csim_<pid> directory is gone (and it existed before)."""
    out, _, tmpdir = cx("controller")
    assert out["has_unconfigure"], "tests/csim/conftest.py has no pytest_unconfigure hook"
    assert out["libdir"] and out["lib_text"] == "RELEASE", "controller made no copy directory to remove"
    assert out["libdir_exists_after_unconfigure"] is False and not list(tmpdir.glob("om_csim_*"))


def test_12_non_distributing_controller_exports_nothing(cx):
    """HARNESS-csim-xdist, `xdist really distributes`: with -n 0 / dist no the hook exists, copies nothing and
    exports nothing (negative control of test 10), and LIB_PATH stays the repo path."""
    out, tree, tmpdir = cx("plain")
    assert out["has_configure"], "tests/csim/conftest.py has no pytest_configure hook"
    assert out["env_lib"] is None and out["env_dbg"] is None and not list(tmpdir.glob("om_csim_*"))
    assert out["lib_path"] == str(tree / "libouroboros.so")


def test_13_build_failure_reaches_workers_via_om_csim_build_error(cx, tmp_path):
    """HARNESS-csim-xdist, `a build failure reaches the workers through OM_CSIM_BUILD_ERROR`: the controller
    whose make failed exports OM_CSIM_BUILD_ERROR containing the compiler text; a worker given that variable
    reports it as conftest.BUILD_ERROR without running make."""
    out, _, _ = cx("controller", {"STUB_MAKE_FAIL": "1"})
    assert out["has_configure"], "tests/csim/conftest.py has no pytest_configure hook"
    assert "compile boom" in (out["build_error"] or ""), "controller BUILD_ERROR lost the compiler text"
    assert "compile boom" in (out["env_err"] or ""), "controller did not export OM_CSIM_BUILD_ERROR"
    env = {"OM_CSIM_LIB": str(tmp_path / "l" / "a.so"), "OM_CSIM_LIB_DBG": str(tmp_path / "l" / "b.so"),
           "OM_CSIM_BUILD_ERROR": "compile boom", "PYTEST_XDIST_WORKER": "gw1"}
    w, _, _ = cx("worker", env)
    assert w["make_after_import"] == 0 and "compile boom" in (w["build_error"] or "")


# ------------------------------------------------------------------ MERGE_GATE_CSIM_XDIST (stub run of merge_gate.sh)

def _gate_regression_argvs(tmp_path, xdist_env):
    """Run the real merge_gate.sh against a tiny candidate clone (a Makefile with empty targets, tests/csim and
    tests/transport directories) with MERGE_GATE_PYTHON = a stub that logs its argv and exits 0, and return the
    logged argv lists of the `merge_gate_support.py regression` calls keyed by their tests/ argument."""
    root = tmp_path / "gate"
    root.mkdir()
    origin, pusher, cand = root / "origin.git", root / "pusher", root / "wt-cand"
    _git(root, "init", "-q", "--bare", "-b", "main", str(origin))
    _git(root, "clone", "-q", str(origin), str(pusher))
    _git(pusher, "checkout", "-q", "-B", "main")
    (pusher / "Makefile").write_text("libouroboros.so libouroboros_dbg.so pipe/ouroboros_pipe pipe/ouroboros_pipe_dbg:\n"
                                     "\t@true\n")
    for d in ("tests/csim", "tests/transport"):
        (pusher / d).mkdir(parents=True)
        (pusher / d / ".keep").write_text("\n")
    _git(pusher, "add", "-A")
    _git(pusher, "commit", "-q", "-m", "m1")
    _git(pusher, "push", "-q", "origin", "main")
    _git(root, "clone", "-q", str(origin), str(cand))
    _git(cand, "checkout", "-q", "-b", "feat")
    (cand / "feat.txt").write_text("f\n")
    _git(cand, "add", "-A")
    _git(cand, "commit", "-q", "-m", "feat")
    log = tmp_path / "gate_argv.log"
    stubpy = tmp_path / "gatestub"
    stubpy.write_text(f"#!{PY}\nimport json, os, sys\n"
                      "open(os.environ['STUB_LOG'], 'a').write(json.dumps(sys.argv[1:]) + '\\n')\n")
    stubpy.chmod(0o755)
    env = _env({"MERGE_GATE_PYTHON": str(stubpy), "STUB_LOG": str(log), "MERGE_GATE_MAKE_TIMEOUT": "60"})
    if xdist_env is not None:
        env["MERGE_GATE_CSIM_XDIST"] = xdist_env
    subprocess.run(["bash", str(GATE), str(cand), "origin/main", "HARNESS-csim-xdist"], capture_output=True,
                   text=True, env=env, timeout=300, cwd=str(tmp_path))
    argvs = [json.loads(l) for l in log.read_text().splitlines()] if log.exists() else []
    out = {}
    for a in argvs:
        if "regression" in a[:2] or (len(a) > 1 and a[1] == "regression"):
            out[next(t for t in a if t.startswith("tests/"))] = a
    return out


def test_15_gate_stub_run_unset_passes_n5_and_n2(tmp_path):
    """HARNESS-csim-xdist, MERGE_GATE_CSIM_XDIST unset (ruled 2026-10-29), the stub-run reader is sound (the stages are reached); with the variable unset the
    stub-run gate's csim regression call carries `--pytest-extra '-n 5 --dist loadfile'` and the transport call
    `--pytest-extra '-n 2'`. Red on the base until the stage flags exist (the stub run itself works today)."""
    calls = _gate_regression_argvs(tmp_path, None)
    assert {"tests/csim", "tests/transport"} <= set(calls), f"stub run did not reach the stages: {sorted(calls)}"
    got = {k: (a[a.index("--pytest-extra") + 1] if "--pytest-extra" in a else None) for k, a in calls.items()}
    assert (got["tests/csim"], got["tests/transport"]) == (CSIM_EXTRA, "-n 2")


def test_14_gate_csim_xdist_zero_omits_pytest_extra(tmp_path):
    """HARNESS-csim-xdist, MERGE_GATE_CSIM_XDIST=0 (Architect ruling 2026-10-29): merge_gate.sh omits the
    --pytest-extra arguments of the csim and transport regression calls, so those stages run the serial command
    (no `-n`). Positive control inside the test: the unset run has the flags, so the omission is the variable's
    doing, and the stage is still invoked."""
    (tmp_path / "u").mkdir()
    (tmp_path / "z").mkdir()
    unset = _gate_regression_argvs(tmp_path / "u", None)
    zero = _gate_regression_argvs(tmp_path / "z", "0")
    assert {"tests/csim", "tests/transport"} <= set(zero), f"stub run did not reach the stages: {sorted(zero)}"
    assert "--pytest-extra" in unset["tests/csim"] and "--pytest-extra" in unset["tests/transport"], \
        "unset run carries no --pytest-extra (the xdist flags are not in the gate yet)"
    assert "--pytest-extra" not in zero["tests/csim"] and "--pytest-extra" not in zero["tests/transport"]
    assert not any("-n" in t.split() for t in zero["tests/csim"] + zero["tests/transport"])
