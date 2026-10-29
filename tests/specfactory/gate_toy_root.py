"""Shared fixture helper (not a test module) for tests that run merge_gate.sh on a toy repo and must get past the
early block into the regression block and later stages.

Test-defect TD-HARNESS-gate-reorder-2 to -7 (ruler Architect 2026-10-29): HARNESS-gate-reorder ends the run at the
first REJECT of the early block (`GATE early_exit REJECT ...`), and a toy repo trips status (the real lane table
disagrees with the toy base), footprint and placeholder_controls, plus alg_constants/sig_table/reach_lint when the
toy repo has no signature table. The fix is the one test_gate_concurrent.py uses (commit 38715223): a fake gate
root whose copy of those tools exits 0, an empty placeholder list, and a HOME for the gate's `$HOME` read.
See also: tests/specfactory/test_gate_concurrent.py _fake_root, test_gate_reorder.py NOISY_TOOLS
"""
import shutil
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
SPEC_DIR = REPO / "scripts" / "specfactory"
OK_STUB = "import sys\nsys.exit(0)\n"
ALL_NOISY_TOOLS = ("alg_constants.py", "reach_lint.py", "sig_table.py", "status_check.py")


def fake_gate_root(tmp_path, noisy=ALL_NOISY_TOOLS):
    """Returns the path of merge_gate.sh inside a fake root under tmp_path. Every scripts/specfactory file is a
    symlink to this tree except the `noisy` tools (stubs that exit 0) and merge_gate_support.py (a real copy:
    it runs sig_table.py by its resolved path, so only a copy in the fake root calls the stub beside it)."""
    root = tmp_path / "gateroot"
    spec = root / "scripts" / "specfactory"
    spec.mkdir(parents=True)
    (root / "docs").symlink_to(REPO / "docs")
    for f in SPEC_DIR.iterdir():
        if f.name not in ("merge_gate_support.py", *noisy):
            (spec / f.name).symlink_to(f)
    for name in noisy:
        (spec / name).write_text(OK_STUB)
    shutil.copy(SPEC_DIR / "merge_gate_support.py", spec / "merge_gate_support.py")
    return spec / "merge_gate.sh"


def gate_env(tmp_path, pieces, **extra):
    """The env a toy-repo gate run needs: HOME (merge_gate.sh reads $HOME under set -u), an empty placeholder list,
    and a runs csv under tmp_path so the run never appends to the real ~/Projects/om-push/gate_runs.csv."""
    placeholders = tmp_path / "placeholders.txt"
    placeholders.write_text("")
    return {"HOME": str(tmp_path / "home"), "MERGE_GATE_PIECES": str(pieces),
            "MERGE_GATE_PLACEHOLDERS": str(placeholders), "MERGE_GATE_RUNS_CSV": str(tmp_path / "runs.csv"),
            "PATH": "/usr/bin:/bin:/home/westopoli/Projects/agora/.venv/bin", **extra}
