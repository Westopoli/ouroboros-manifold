# spec: docs/northstar/plans/2026-10-01-architect-rulings-2.md, Addendum 41 (A114), gate half;
# docs/northstar/plans/briefs/2026-09-22-two-day-push.md decision 7
"""The merge gate runs control_liveness.py over the ATTACHING piece's own controls and rejects a dead one.

Contract these tests pin (the implementation does not exist yet, so the fake-repo tests are red):

  Step name and line: `GATE control_liveness OK|REJECT <detail>`, printed by merge_gate.sh in the
  merge profile only (never under --revert, like the other acceptance-shaped steps).

  Piece -> controls map (pieces.toml has no controls field): the epics named by the piece's
  `acceptance` paths (`.../test_E<NN>_...`) select `tests/csim/controls/test_control_e<NN>_*.py` in the
  CANDIDATE. A piece with no E<NN> acceptance path (every HARNESS piece) has no controls and passes.
  Only the piece ids passed to merge_gate.sh (comma-separated allowed) are checked; already-attached
  pieces that were not passed keep their status and are never re-checked.

  Placeholders: a control listed in placeholder_controls.txt (repo-relative paths, one per line;
  env override MERGE_GATE_PLACEHOLDERS, default docs/northstar/spec_factory/placeholder_controls.txt)
  is removed from the set BEFORE control_liveness.py runs, so a listed placeholder is never run, never
  judged and never rejects here. The detail reports them as `placeholders_skipped=N`. A111's separate
  gate owns "a placeholder not listed / a listed one starting to pass" under its own step name; this
  step only ever sees controls that are not listed. An unlisted dead control rejects here.

  Harness API (merge_gate_support.py):
    piece_controls(piece_ids, pieces_path, project) -> list[Path]   all epic controls, placeholders included
    control_liveness_check(project, piece_ids, pieces_path, placeholders_path, scratch_root=None,
                           python_exe=None) -> (ok, detail)
  CLI: `merge_gate_support.py control-liveness <project> <piece_ids> --pieces P --placeholders P
        --scratch-root DIR [--python PY]`, exit 1 on any DEAD, detail on stdout.
  control_liveness.py gains `--project DIR` (default: this repo) naming the tree whose conftest.py,
  libouroboros*.so and spec_factory tables the scratch tree mirrors; the gate passes the CANDIDATE.

Fake repos carry a stub conftest whose `dbg` fixture records whether om_debug_inject ran, so a live
control (asserts the injection took effect) differs between the as-written and neutralised runs, and a
dead one (asserts something independent of the injection) does not. DEAD needs a C change nowhere.
ERROR handling (a control that cannot run at all) is deliberately not pinned: see the A114 report.
"""
import re
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent.parent
GATE = REPO / "scripts" / "specfactory" / "merge_gate.sh"
LIVENESS = REPO / "scripts" / "specfactory" / "control_liveness.py"
SUPPORT = REPO / "scripts" / "specfactory" / "merge_gate_support.py"
PYTHON = "/home/westopoli/Projects/agora/.venv/bin/python"
sys.path.insert(0, str(REPO / "scripts" / "specfactory"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from gate_toy_root import write_story  # noqa: E402

import merge_gate_support as mgs  # noqa: E402

STUB_CONFTEST = '''import pytest


class OMBugE99:
    PROBE = 9901


class _Handle:
    def __init__(self):
        self.injected = False

    def om_debug_inject(self, w, bug):
        self.injected = True


def _configure_debug(h):
    pass


@pytest.fixture
def dbg():
    h = _Handle()
    _configure_debug(h)
    return h
'''

LIVE_CONTROL = '''from conftest import OMBugE99


def test_control_live(dbg):
    dbg.om_debug_inject(None, OMBugE99.PROBE)
    assert dbg.injected, "injection did not take effect"
'''

# Same shape, but the assertion does not depend on the injection: both runs agree.
DEAD_CONTROL = '''from conftest import OMBugE99


def test_control_dead(dbg):
    dbg.om_debug_inject(None, OMBugE99.PROBE)
    assert 1 + 1 == 2
'''


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True)


def _piece(pid: str, epic: str | None) -> str:
    acc = f'["tests/csim/test_{epic}_S001_probe.py"]' if epic else "[]"
    return f'[[piece]]\nid = "{pid}"\nowns = ["csrc/{pid}.c"]\nacceptance = {acc}\ndepends_on = []\n'


def _fake_project(root: Path, controls: dict[str, str]) -> Path:
    """A candidate-shaped repo: stub conftest plus the named control files."""
    (root / "tests" / "csim" / "controls").mkdir(parents=True)
    (root / "csrc").mkdir()
    (root / "csrc" / "stub.c").write_text("int om_stub(void) { return 0; }\n")
    (root / "Makefile").write_text("libouroboros.so:\n\ttouch $@\nlibouroboros_dbg.so:\n\ttouch $@\n")
    (root / "tests" / "csim" / "conftest.py").write_text(STUB_CONFTEST)
    for name, body in controls.items():
        (root / "tests" / "csim" / "controls" / name).write_text(body)
    return root


def _pieces(tmp_path: Path, *rows: str) -> Path:
    p = tmp_path / "pieces.toml"
    p.write_text("\n".join(rows))
    return p


def _placeholders(tmp_path: Path, *rels: str) -> Path:
    p = tmp_path / "placeholder_controls.txt"
    p.write_text("".join(r + "\n" for r in rels))
    return p


def _check(project, ids, pieces, placeholders, tmp_path):
    return mgs.control_liveness_check(project, ids, pieces, placeholders,
                                      scratch_root=tmp_path / "scratch", python_exe=PYTHON)


# --------------------------------------------------------------- piece -> controls map

def test_piece_controls_maps_acceptance_epics_to_control_files(tmp_path):
    proj = _fake_project(tmp_path / "p", {
        "test_control_e99_live.py": LIVE_CONTROL,
        "test_control_e98_other_epic.py": LIVE_CONTROL,
    })
    pieces = _pieces(tmp_path, _piece("B1", "E99"), _piece("H1", None))
    got = [p.name for p in mgs.piece_controls(["B1"], pieces, proj)]
    assert got == ["test_control_e99_live.py"]
    assert mgs.piece_controls(["H1"], pieces, proj) == []


def test_piece_controls_keeps_placeholders_in_the_map(tmp_path):
    """Placeholder removal is the check's job, not the map's: the map is the piece's whole epic."""
    proj = _fake_project(tmp_path / "p", {"test_control_e99_ph.py": DEAD_CONTROL})
    pieces = _pieces(tmp_path, _piece("B1", "E99"))
    assert [p.name for p in mgs.piece_controls(["B1"], pieces, proj)] == ["test_control_e99_ph.py"]


# --------------------------------------------------------------- liveness check (unit, fake repo)

def test_control_planted_dead_control_really_is_dead(tmp_path):
    """The fixture itself: control_liveness.py --project says LIVE for the live stub, DEAD for the planted one."""
    proj = _fake_project(tmp_path / "p", {"test_control_e99_live.py": LIVE_CONTROL,
                                          "test_control_e99_dead.py": DEAD_CONTROL})
    out = subprocess.run([PYTHON, str(LIVENESS), "--project", str(proj), "--scratch-root",
                          str(tmp_path / "scr"), "--python", PYTHON,
                          str(proj / "tests/csim/controls/test_control_e99_live.py"),
                          str(proj / "tests/csim/controls/test_control_e99_dead.py")],
                         capture_output=True, text=True).stdout
    assert "LIVE  test_control_e99_live.py" in out, out
    assert "DEAD  test_control_e99_dead.py" in out, out


def test_check_rejects_a_dead_control(tmp_path):
    proj = _fake_project(tmp_path / "p", {"test_control_e99_dead.py": DEAD_CONTROL})
    ok, detail = _check(proj, ["B1"], _pieces(tmp_path, _piece("B1", "E99")), _placeholders(tmp_path), tmp_path)
    assert ok is False
    assert "test_control_e99_dead.py" in detail and "DEAD" in detail


def test_check_passes_a_live_control(tmp_path):
    proj = _fake_project(tmp_path / "p", {"test_control_e99_live.py": LIVE_CONTROL})
    ok, detail = _check(proj, ["B1"], _pieces(tmp_path, _piece("B1", "E99")), _placeholders(tmp_path), tmp_path)
    assert ok is True, detail
    assert "LIVE=1" in detail and "DEAD=0" in detail


def test_check_passes_a_piece_with_no_controls(tmp_path):
    proj = _fake_project(tmp_path / "p", {"test_control_e98_unrelated_dead.py": DEAD_CONTROL})
    pieces = _pieces(tmp_path, _piece("B1", "E99"), _piece("H1", None))
    for pid in ("B1", "H1"):  # an epic with no control files, and a piece with no epic at all
        ok, detail = _check(proj, [pid], pieces, _placeholders(tmp_path), tmp_path)
        assert ok is True, detail


def test_check_never_runs_or_rejects_a_listed_placeholder(tmp_path):
    rel = "tests/csim/controls/test_control_e99_placeholder.py"
    proj = _fake_project(tmp_path / "p", {"test_control_e99_placeholder.py": DEAD_CONTROL})
    pieces = _pieces(tmp_path, _piece("B1", "E99"))
    ok, detail = _check(proj, ["B1"], pieces, _placeholders(tmp_path, rel), tmp_path)
    assert ok is True, detail
    assert "placeholders_skipped=1" in detail
    # Positive control for the separation: the same file, unlisted, is a dead control and rejects.
    ok, detail = _check(proj, ["B1"], pieces, _placeholders(tmp_path), tmp_path)
    assert ok is False and "test_control_e99_placeholder.py" in detail


def test_check_only_checks_the_piece_ids_passed(tmp_path):
    proj = _fake_project(tmp_path / "p", {"test_control_e99_live.py": LIVE_CONTROL,
                                          "test_control_e98_dead.py": DEAD_CONTROL})
    pieces = _pieces(tmp_path, _piece("B1", "E99"), _piece("B2", "E98"))
    ok, detail = _check(proj, ["B1"], pieces, _placeholders(tmp_path), tmp_path)
    assert ok is True, detail  # B2's dead control is not B1's business
    ok, detail = _check(proj, ["B1", "B2"], pieces, _placeholders(tmp_path), tmp_path)
    assert ok is False and "test_control_e98_dead.py" in detail


def test_cli_exit_codes(tmp_path):
    proj = _fake_project(tmp_path / "p", {"test_control_e99_dead.py": DEAD_CONTROL})
    pieces = _pieces(tmp_path, _piece("B1", "E99"), _piece("H1", None))
    ph = _placeholders(tmp_path)

    def run(ids: str):
        return subprocess.run([PYTHON, str(SUPPORT), "control-liveness", str(proj), ids,
                               "--pieces", str(pieces), "--placeholders", str(ph),
                               "--scratch-root", str(tmp_path / "scr"), "--python", PYTHON],
                              capture_output=True, text=True)
    bad = run("B1")
    assert bad.returncode == 1 and "test_control_e99_dead.py" in bad.stdout + bad.stderr
    good = run("H1")
    assert good.returncode == 0, good.stdout + good.stderr


# --------------------------------------------------------------- the gate script (fake candidate)

def _gate(tmp_path: Path, controls: dict[str, str], ids: str, *rows: str, placeholders=(), revert=False):
    repo = _fake_project(tmp_path / "cand", controls)
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "gate@test")
    _git(repo, "config", "user.name", "gate")
    for one in ids.split(","):  # H-020: one story file per id the gate run names
        write_story(repo, one)
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "base")
    _git(repo, "remote", "add", "origin", str(repo))
    _git(repo, "update-ref", "refs/remotes/origin/main", "HEAD")
    pieces = _pieces(tmp_path, *rows)
    env = {"MERGE_GATE_PIECES": str(pieces),
           "MERGE_GATE_PLACEHOLDERS": str(_placeholders(tmp_path, *placeholders)),
           "PATH": "/usr/bin:/bin:/home/westopoli/Projects/agora/.venv/bin"}
    cmd = ["bash", str(GATE)] + (["--revert"] if revert else []) + [str(repo), "HEAD", ids]
    return subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=300)


def test_gate_step_rejects_a_dead_control_of_the_attaching_piece(tmp_path):
    proc = _gate(tmp_path, {"test_control_e99_dead.py": DEAD_CONTROL}, "B1", _piece("B1", "E99"))
    assert "GATE control_liveness REJECT" in proc.stdout, proc.stdout + proc.stderr
    assert "test_control_e99_dead.py" in proc.stdout
    assert proc.returncode == 1


def test_gate_step_passes_a_live_control(tmp_path):
    proc = _gate(tmp_path, {"test_control_e99_live.py": LIVE_CONTROL}, "B1", _piece("B1", "E99"))
    assert "GATE control_liveness OK" in proc.stdout, proc.stdout + proc.stderr


def test_gate_step_passes_a_piece_with_no_controls(tmp_path):
    proc = _gate(tmp_path, {"test_control_e98_dead.py": DEAD_CONTROL}, "B1", _piece("B1", "E99"))
    assert "GATE control_liveness OK" in proc.stdout, proc.stdout + proc.stderr


def test_gate_step_does_not_fail_a_listed_placeholder(tmp_path):
    rel = "tests/csim/controls/test_control_e99_placeholder.py"
    proc = _gate(tmp_path, {"test_control_e99_placeholder.py": DEAD_CONTROL}, "B1", _piece("B1", "E99"),
                 placeholders=(rel,))
    assert "GATE control_liveness OK" in proc.stdout, proc.stdout + proc.stderr
    assert "placeholders_skipped=1" in proc.stdout


def test_gate_step_ignores_other_attached_pieces(tmp_path):
    proc = _gate(tmp_path, {"test_control_e99_live.py": LIVE_CONTROL, "test_control_e98_dead.py": DEAD_CONTROL},
                 "B1", _piece("B1", "E99"), _piece("B2", "E98"))
    assert "GATE control_liveness OK" in proc.stdout, proc.stdout + proc.stderr


def test_gate_step_takes_comma_separated_piece_ids(tmp_path):
    proc = _gate(tmp_path, {"test_control_e99_live.py": LIVE_CONTROL, "test_control_e98_dead.py": DEAD_CONTROL},
                 "B1,B2", _piece("B1", "E99"), _piece("B2", "E98"))
    assert "GATE control_liveness REJECT" in proc.stdout, proc.stdout + proc.stderr


def test_gate_step_is_skipped_in_revert_mode(tmp_path):
    proc = _gate(tmp_path, {"test_control_e99_dead.py": DEAD_CONTROL}, "B1", _piece("B1", "E99"), revert=True)
    assert "GATE control_liveness" not in proc.stdout, proc.stdout + proc.stderr


# --------------------------------------------------------------- the real repo
# Needs libouroboros_dbg.so (conftest builds it). Real controls, real conftest, no fakes.

REAL_PIECES = REPO / "docs" / "northstar" / "plans" / "push" / "pieces.toml"
REAL_PLACEHOLDERS = REPO / "docs" / "northstar" / "spec_factory" / "placeholder_controls.txt"
DEAD_E04 = "test_control_e04_chain_counter_unsaved.py"


def test_real_repo_piece_with_only_live_controls_passes(tmp_path):
    """B9 (E-10): its 9 other E-10 controls are listed placeholders, its one real control is live."""
    ok, detail = mgs.control_liveness_check(REPO, ["B9"], REAL_PIECES, REAL_PLACEHOLDERS,
                                            scratch_root=tmp_path / "scr", python_exe=PYTHON)
    assert ok is True, detail
    assert "LIVE=1" in detail and "placeholders_skipped=" in detail


def test_real_repo_gate_step_runs_on_b1_and_names_its_control(tmp_path):
    """B1 (E-04) carries test_control_e04_chain_counter_unsaved.py. The step must run on it and report a
    well-formed detail line naming the control; the verdict (OK or REJECT) is NOT asserted, so fixing the
    control never breaks this test. The 'gate rejects a dead control' positive control is the planted
    fixture tests above (test_check_rejects_a_dead_control, test_gate_step_rejects_a_dead_control_of_the_
    attaching_piece), which depend on no real control. Ledger row TD-A128-liveness-real-repo (replaces the
    real-repo B1 reject test, which broke whenever e04 got its hook)."""
    assert DEAD_E04 in [p.name for p in mgs.piece_controls(["B1"], REAL_PIECES, REPO)]
    ok, detail = mgs.control_liveness_check(REPO, ["B1"], REAL_PIECES, REAL_PLACEHOLDERS,
                                            scratch_root=tmp_path / "scr", python_exe=PYTHON)
    assert isinstance(ok, bool)
    assert re.match(r"LIVE=\d+ DEAD=\d+ ERROR=\d+ placeholders_skipped=\d+", detail), detail
    live, dead, err = (int(x) for x in re.findall(r"(?:LIVE|DEAD|ERROR)=(\d+)", detail)[:3])
    assert ok == (dead + err == 0), detail
    assert live + dead + err >= 1
    if not ok:  # a rejection must name the control it rejects
        assert DEAD_E04 in detail or "test_control_e04_" in detail or "test_control_" in detail, detail


@pytest.mark.parametrize("piece", ["B7", "B8"])
def test_real_repo_b7_and_b8_pass_with_live_hooks(tmp_path, piece):
    """B7 (E-08, OM_BUG_TIME_JUMP_CLAMP_SKIPPED) and B8 (E-09) have their hooks planted: the step reports
    OK with LIVE counts (their other controls are listed placeholders)."""
    ok, detail = mgs.control_liveness_check(REPO, [piece], REAL_PIECES, REAL_PLACEHOLDERS,
                                            scratch_root=tmp_path / "scr", python_exe=PYTHON)
    assert ok is True, detail
    assert "DEAD=0" in detail and "LIVE=1" in detail
