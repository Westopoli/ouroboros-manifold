# spec: docs/northstar/plans/2026-10-07-visible-game-spec.md, paragraph "HARNESS-flow-spine-teardown" (Architect 2026-10-23); ledger FINDING-flow-spine-tmp-leak; piece HARNESS-flow-spine-teardown (docs/northstar/plans/push/pieces.toml).
"""Proves HARNESS-flow-spine-teardown: a run of tests/qa/desktop/test_flow_spine.py killed
mid-way leaves no /tmp/qa_flow_spine.* dir and no xvfb-run or godot process of its tree.
(The spec paragraph names no S-/R- rule id; none is invented. Rule pins: none.)

Spec text followed: "the fixture registers a finalizer that removes its tempdir and kills its
xvfb-run/godot process tree, and the finalizer runs on abort too (a request.addfinalizer plus a
signal handler for SIGTERM and SIGINT)" and "a run of the flow spine killed mid-way leaves no
/tmp/qa_flow_spine.* dir and no godot or xvfb-run child of it; positive control: the same kill
on main leaves one."

UNSTATED INTERFACE choices (the paragraph gives none; each is mine, a builder satisfies them
without editing this file):
  * "killed mid-way" = the real, unedited tests/qa/desktop/test_flow_spine.py run as
    `python3 -m pytest` is sent SIGTERM (test_..._sigterm) or SIGINT (test_..._sigint) while
    the `game` fixture is in its setup, after the game's tree is up. The run is not allowed
    to reach a test body, so the kill lands where the module-scoped fixture owns the tree.
  * a stub `xvfb-run` and a stub `godot` shadow the real ones on PATH (find_godot() finds
    "godot" first on PATH), so no display or GPU is needed. The stub godot never opens the
    qa port, so the fixture sits in wait_for_port; the stubs write their pids to $STUB_PIDFILE.
  * the run's tempdir root is isolated by TMPDIR=<tmp_path>/tmp (tempfile.mkdtemp honours it),
    so the assertion "no qa_flow_spine.* dir" cannot see another run's dir.
  * "no child left" = every pid in the pidfile (stub xvfb-run, stub godot, its `sleep`) is
    gone or a zombie within SETTLE_S after the pytest process exits.
  * the signal handler must be live by the time GodotGame's scratch dir exists, because the
    test kills as soon as the pidfile has all three pids.
Positive control: the same kill run against a frozen copy of the main-era fixture (generator
with try/finally, no finalizer, no handler) must leave the dir and the tree; it is green on
main and after the build, and shows the detector can see a leak. The control's leftovers
are removed by the test itself.
"""
from __future__ import annotations

import os
import shutil
import signal
import subprocess
import sys
import textwrap
import time
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
FLOW_SPINE = REPO / "tests" / "qa" / "desktop" / "test_flow_spine.py"
DESKTOP = REPO / "tests" / "qa" / "desktop"
UP_TIMEOUT_S = 40.0
SETTLE_S = 10.0

XVFB_STUB = """#!/bin/bash
echo "xvfb $$" >> "$STUB_PIDFILE"
while [ "$1" = "-a" ] || [ "$1" = "-s" ]; do
  if [ "$1" = "-s" ]; then shift; fi
  shift
done
"$@"
"""
GODOT_STUB = """#!/bin/bash
echo "godot $$" >> "$STUB_PIDFILE"
sleep 600 &
echo "sleep $!" >> "$STUB_PIDFILE"
wait
"""

# Frozen main-era fixture (test_flow_spine.py :95-109 before this piece): the positive control.
LEGACY_MODULE = '''
import sys
import pytest
sys.path.insert(0, %(desktop)r)
from daemon_client import GodotGame, pick_free_port

@pytest.fixture(scope="module")
def game():
    g = GodotGame(qa_port=pick_free_port(), seed=1)
    g.start()
    g.wait_for_port(timeout=60.0)
    try:
        yield g
    finally:
        g.stop()

def test_uses_game(game):
    pass
'''


def _alive(pid: int) -> bool:
    try:
        state = Path("/proc/%d/stat" % pid).read_text().rsplit(")", 1)[1].split()[0]
    except (FileNotFoundError, ProcessLookupError):
        return False
    return state != "Z"


def _pids(pidfile: Path) -> dict:
    out = {}
    if pidfile.exists():
        for line in pidfile.read_text().splitlines():
            parts = line.split()
            if len(parts) == 2 and parts[1].isdigit():
                out[parts[0]] = int(parts[1])
    return out


def _run_killed(tmp_path: Path, target: Path, sig: int):
    """Run pytest on target with the stubs, kill it with sig once the tree is up.
    Returns (leftover scratch dirs, live pids of the tree, pytest returncode)."""
    bindir = tmp_path / "bin"
    tmpdir = tmp_path / "tmp"
    bindir.mkdir()
    tmpdir.mkdir()
    for name, body in (("xvfb-run", XVFB_STUB), ("godot", GODOT_STUB)):
        (bindir / name).write_text(body)
        (bindir / name).chmod(0o755)
    pidfile = tmp_path / "pids.txt"
    env = dict(os.environ)
    env.update(PATH="%s:%s" % (bindir, env["PATH"]), TMPDIR=str(tmpdir), STUB_PIDFILE=str(pidfile))
    proc = subprocess.Popen(
        [sys.executable, "-m", "pytest", "-x", "-q", "-p", "no:cacheprovider", str(target)],
        cwd=str(REPO), env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        start_new_session=True,
    )
    tree = {}
    try:
        deadline = time.monotonic() + UP_TIMEOUT_S
        while time.monotonic() < deadline and not {"xvfb", "godot", "sleep"} <= set(tree):
            if proc.poll() is not None:
                break
            time.sleep(0.2)
            tree = _pids(pidfile)
        assert {"xvfb", "godot", "sleep"} <= set(tree), "the stub game tree never came up (pytest rc=%s)\n%s" % (
            proc.poll(), (proc.communicate(timeout=5)[0] or b"").decode(errors="replace")[-1500:])
        assert list(tmpdir.glob("qa_flow_spine.*")), "control: no scratch dir while the tree is up"
        proc.send_signal(sig)
        try:
            proc.wait(timeout=SETTLE_S)
        except subprocess.TimeoutExpired:
            pass
        end = time.monotonic() + SETTLE_S
        while time.monotonic() < end and any(_alive(p) for p in tree.values()):
            time.sleep(0.2)
        left_dirs = sorted(p.name for p in tmpdir.glob("qa_flow_spine.*"))
        left_pids = {k: p for k, p in tree.items() if _alive(p)}
        return left_dirs, left_pids, proc.returncode
    finally:
        for p in list(tree.values()):  # clean up whatever the run under test left
            try:
                os.kill(p, signal.SIGKILL)
            except ProcessLookupError:
                pass
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        proc.wait(timeout=10)
        shutil.rmtree(tmpdir, ignore_errors=True)


@pytest.mark.parametrize("sig,name", [(signal.SIGTERM, "sigterm"), (signal.SIGINT, "sigint")])
def test_killed_flow_spine_leaves_no_tempdir_and_no_tree(tmp_path, sig, name):
    # Proves HARNESS-flow-spine-teardown: a flow spine killed mid-way leaves no
    # /tmp/qa_flow_spine.* dir and no xvfb-run/godot child of it (red on main: (a) behaviour,
    # the fixture's finally never runs on SIGTERM and the tree has no finalizer).
    left_dirs, left_pids, rc = _run_killed(tmp_path, FLOW_SPINE, sig)
    assert not left_dirs, "%s left scratch dirs: %s (pytest rc=%s)" % (name, left_dirs, rc)
    assert not left_pids, "%s left live processes of the game tree: %s (pytest rc=%s)" % (name, left_pids, rc)


@pytest.mark.parametrize("sig,name", [(signal.SIGTERM, "sigterm"), (signal.SIGINT, "sigint")])
def test_positive_control_main_era_fixture_leaks_on_kill(tmp_path, sig, name):
    # Positive control for HARNESS-flow-spine-teardown: the same kill against the main-era
    # fixture must leave the scratch dir and the stub tree; shows the detector above can see a
    # leak. The kill can land in wait_for_port, before the old try/finally is entered, so the
    # old fixture leaks on SIGINT too.
    mod = tmp_path / "legacy" / "test_legacy_flow_spine.py"
    mod.parent.mkdir()
    mod.write_text(textwrap.dedent(LEGACY_MODULE) % {"desktop": str(DESKTOP)})
    left_dirs, left_pids, rc = _run_killed(tmp_path, mod, sig)
    assert left_dirs, "control: the main-era fixture left no scratch dir on %s; the detector is blind" % name
    assert left_pids, "control: the main-era fixture left no process on %s; the detector is blind" % name
