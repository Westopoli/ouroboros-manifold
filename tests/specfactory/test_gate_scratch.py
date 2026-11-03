# spec: H-074 gate-scratch-on-disk (docs/stories/H-074.md "Change" parts 1 and 3, "Tests" 1 to 4).
"""H-074: "A gate never fails because a temporary file had nowhere to go."

Story text proved, by part:
  * Change 1: "`merge_gate.sh`, `pre_gate.sh`, `land_push.sh` and `sweep.sh` export `TMPDIR` to
    `<push root>/tmp` (creating it) before any child process starts ... A caller's `TMPDIR` is kept only when it is
    NOT under `/tmp` ... unset, empty, or under `/tmp` it is overridden" (tests 1 to 3 below).
  * Change 1: "`merge_gate.sh` prints the value in force, kept or overridden, once, as its first log line,
    `GATE tmpdir <path>`" (the GATE tmpdir tests).
  * Change 3: "`Disk quota exceeded` or `No space left on device` in a stage log is classified `SCRATCH-FULL`,
    reported as retryable and never as a reject of the story" (test 4).

Hermetic: no real gate, no Godot, no GPU. HOME is a scratch directory, so the push root `$HOME/Projects/om-push` is
scratch (the story lets the builder add OM_PUSH_ROOT or drop it; HOME works under both, so no variable name is pinned).
A stub `git` first on PATH records the TMPDIR each child sees and fails or succeeds as the script under test needs;
stub stages (pre_gate's `PRE_GATE_MERGE_GATE`, a stub pre_gate.sh beside a copy of land_push.sh) record it too.
The script's own `mktemp -t` directory is what the GATE tmpdir line and children are compared with.
"""
import os
import shutil
import stat
import subprocess
import sys
import uuid
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent.parent
SPEC = REPO / "scripts" / "specfactory"
sys.path.insert(0, str(SPEC))
RUN_TIMEOUT_S = 40
REAL_HOME = Path.home()
DISK_ROOT = REAL_HOME / "Projects" / "om-push" / "tmp-gatescratch"  # real disk, never under /tmp

STUB_GIT = """#!/bin/bash
echo "${TMPDIR-<unset>}" >> "$REC"
if [[ -n "${GIT_STUB_OK:-}" ]]; then
    [[ "$*" == *rev-parse* ]] && echo 0123456789012345678901234567890123456789
    exit 0
fi
exit 1
"""
STUB_STAGE = """#!/bin/bash
echo "${TMPDIR-<unset>}" >> "$REC"
exit 0
"""
CALLERS_UNDER_TMP = ["/tmp", "/tmp/claude-1000/x", ""]  # "" is the empty value; /tmp paths need not exist


def _exe(path, body):
    path.write_text(body)
    path.chmod(path.stat().st_mode | stat.S_IXUSR)


@pytest.fixture
def fx(tmp_path):
    """Scratch HOME (push root = HOME/Projects/om-push), a stub bin dir with `git`, a record file, a candidate dir."""
    home = tmp_path / "home"
    home.mkdir()
    (home / ".gitconfig").write_text("")
    bin_ = tmp_path / "bin"
    bin_.mkdir()
    _exe(bin_ / "git", STUB_GIT)
    cand = tmp_path / "wt-cand"
    cand.mkdir()
    DISK_ROOT.mkdir(parents=True, exist_ok=True)
    disk = DISK_ROOT / uuid.uuid4().hex[:12]
    disk.mkdir()
    try:
        yield {"home": home, "bin": bin_, "rec": tmp_path / "rec.txt", "cand": cand, "tmp": tmp_path,
               "disk": disk, "expect": home / "Projects" / "om-push" / "tmp"}
    finally:
        shutil.rmtree(disk, ignore_errors=True)


def _run(fx, argv, caller, extra_env=None, cwd=None):
    env = {"PATH": f"{fx['bin']}:{os.environ['PATH']}", "HOME": str(fx["home"]), "REC": str(fx["rec"])}
    if caller is not None:
        env["TMPDIR"] = caller
    env.update(extra_env or {})
    r = subprocess.run(argv, capture_output=True, text=True, env=env, timeout=RUN_TIMEOUT_S, cwd=cwd or str(fx["tmp"]))
    recs = fx["rec"].read_text().splitlines() if fx["rec"].exists() else []
    return r, recs


def _merge_gate(fx, caller):
    return _run(fx, ["bash", str(SPEC / "merge_gate.sh"), str(fx["cand"]), "origin/main", "H-074"], caller)


def _pre_gate(fx, caller):
    stage = fx["tmp"] / "stage_gate.sh"
    _exe(stage, STUB_STAGE)
    return _run(fx, ["bash", str(SPEC / "pre_gate.sh"), str(fx["cand"]), "origin/main", "H-074"], caller,
                {"PRE_GATE_MERGE_GATE": str(stage), "PRE_GATE_PYTHON": sys.executable})


def _land_push(fx, caller):
    scripts = fx["tmp"] / "scripts"
    scripts.mkdir()
    shutil.copy(SPEC / "land_push.sh", scripts / "land_push.sh")
    _exe(scripts / "pre_gate.sh", STUB_STAGE)  # found beside land_push.sh
    return _run(fx, ["bash", str(scripts / "land_push.sh"), str(fx["cand"]), "H-074"], caller, {"GIT_STUB_OK": "1"})


def _sweep(fx, caller):
    # stub git exits 1 at sweep's first `git fetch`, so nothing real runs; the first child still shows its TMPDIR
    return _run(fx, ["bash", str(SPEC / "sweep.sh"), "--dry-run"], caller)


SCRIPTS = {"merge_gate": _merge_gate, "pre_gate": _pre_gate, "land_push": _land_push, "sweep": _sweep}


def _gate_tmpdir_lines(r):
    return [ln for ln in r.stdout.splitlines() if ln.startswith("GATE tmpdir ")]


# ---- test 1: TMPDIR unset -> under the push root, directory created, children see it ---------------------------------
@pytest.mark.parametrize("name", list(SCRIPTS))
def test_t1_unset_tmpdir_becomes_push_root_tmp(fx, name):
    """H-074 Change 1: "export `TMPDIR` to `<push root>/tmp` (creating it) before any child process starts"."""
    r, recs = SCRIPTS[name](fx, None)
    assert recs, f"{name}: no child ran; harness broken\n{r.stdout}\n{r.stderr}"
    assert set(recs) == {str(fx["expect"])}, f"{name}: children saw TMPDIR {sorted(set(recs))}, wanted {fx['expect']}"
    assert fx["expect"].is_dir(), f"{name}: {fx['expect']} not created"


def test_t1_merge_gate_prints_gate_tmpdir_line_with_push_root(fx):
    """H-074 Change 1: "`merge_gate.sh` prints the value in force ... as its first log line, `GATE tmpdir <path>`"."""
    r, _ = _merge_gate(fx, None)
    assert _gate_tmpdir_lines(r) == [f"GATE tmpdir {fx['expect']}"], f"stdout:\n{r.stdout}"
    gate = [ln for ln in r.stdout.splitlines() if ln.startswith("GATE ")]
    assert gate[0].startswith("GATE tmpdir "), f"GATE tmpdir not the first GATE line: {gate[:2]}"  # see Q-1 in report


# ---- test 2: caller TMPDIR on real disk is kept -----------------------------------------------------------------------
@pytest.mark.parametrize("name", list(SCRIPTS))
def test_t2_control_children_see_a_disk_caller_tmpdir(fx, name):
    """H-074 Change 1 / Tests 3 positive control: "A caller's `TMPDIR` is kept only when it is NOT under `/tmp`";
    this control is green today and proves the stub harness reports a TMPDIR faithfully."""
    caller = fx["disk"] / "mine"
    caller.mkdir()
    r, recs = SCRIPTS[name](fx, str(caller))
    assert recs, f"{name}: no child ran; harness broken\n{r.stdout}\n{r.stderr}"
    assert set(recs) == {str(caller)}, f"{name}: children saw {sorted(set(recs))}, wanted caller's {caller}"
    assert not str(caller).startswith("/tmp"), "control premise: disk dir must not be under /tmp"


def test_t2_merge_gate_gate_tmpdir_prints_the_callers_value(fx):
    """H-074 Change 1: "`GATE tmpdir` prints the value in force, kept or overridden" (kept case)."""
    caller = fx["disk"] / "mine"
    caller.mkdir()
    r, _ = _merge_gate(fx, str(caller))
    assert _gate_tmpdir_lines(r) == [f"GATE tmpdir {caller}"], f"stdout:\n{r.stdout}"


# ---- test 3: caller TMPDIR empty or under /tmp is overridden ------------------------------------------------------------
@pytest.mark.parametrize("caller", CALLERS_UNDER_TMP)
@pytest.mark.parametrize("name", list(SCRIPTS))
def test_t3_tmp_caller_tmpdir_is_overridden(fx, name, caller):
    """H-074 Change 1 ruling 2026-11-02: "unset, empty, or under `/tmp` it is overridden" with the push root's `tmp`."""
    r, recs = SCRIPTS[name](fx, caller)
    assert recs, f"{name}: no child ran; harness broken\n{r.stdout}\n{r.stderr}"
    assert set(recs) == {str(fx["expect"])}, f"{name} caller {caller!r}: children saw {sorted(set(recs))}, wanted {fx['expect']}"
    assert fx["expect"].is_dir()


@pytest.mark.parametrize("caller", CALLERS_UNDER_TMP)
def test_t3_merge_gate_gate_tmpdir_prints_the_override(fx, caller):
    """H-074 Change 1: "`GATE tmpdir` prints the value in force, kept or overridden" (overridden case)."""
    r, _ = _merge_gate(fx, caller)
    assert _gate_tmpdir_lines(r) == [f"GATE tmpdir {fx['expect']}"], f"caller {caller!r}; stdout:\n{r.stdout}"


# ---- test 4: SCRATCH-FULL classification (merge_gate_support.lane_plays_check, the stage the story names) ---------------
PLAYS = "tests/qa/desktop/plays"


def _lane_check(tmp_path, play_body):
    import merge_gate_support as mgs
    (tmp_path / PLAYS / "C").mkdir(parents=True)
    (tmp_path / PLAYS / "C" / "play_x.py").write_text(play_body)
    (tmp_path / "lanes.toml").write_text('[lanes]\nC = ["scenes/ground3d/**"]\n')
    (tmp_path / "known.txt").write_text("")
    return mgs.lane_plays_check(tmp_path, "HEAD", python_exe=sys.executable, timeout=120,
                                known_red_path=tmp_path / "known.txt", lane_map_path=tmp_path / "lanes.toml",
                                plays_dir=PLAYS, changed=["scenes/ground3d/a.gd"], setup=False)


def test_t4_control_ordinary_assertion_failure_still_rejects(tmp_path):
    """H-074 Tests 4 positive control: "an ordinary assertion failure in the same stubbed log still rejects"."""
    ok, detail = _lane_check(tmp_path, "def test_play_x():\n    assert 1 == 2, 'plain failure'\n")
    assert not ok and "red outside known-red list" in detail and "SCRATCH-FULL" not in detail, detail


@pytest.mark.parametrize("text", ["Disk quota exceeded", "No space left on device"])
def test_t4_scratch_full_is_classified_not_rejected(tmp_path, text):
    """H-074 Change 3: "`Disk quota exceeded` ... or `No space left on device` in a stage log is classified
    `SCRATCH-FULL`, reported as retryable and never as a reject of the story"."""
    ok, detail = _lane_check(tmp_path, f"def test_play_x():\n    assert 1 == 2, 'fatal error: error writing to /tmp/cc1.s: {text}'\n")
    assert "SCRATCH-FULL" in detail, detail
    assert "red outside known-red list" not in detail, detail
