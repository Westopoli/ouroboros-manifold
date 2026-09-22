# spec: docs/northstar/plans/push/specs/C7.md::Acceptance::AC-1
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_qa_daemon_gd_suite_passes():
    result = subprocess.run(
        ["scripts/run_godot_tests.sh", "tests/test_qa_daemon.gd"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, (
        f"tests/test_qa_daemon.gd failed (exit {result.returncode})\n"
        f"--- stdout ---\n{result.stdout[-2000:]}\n"
        f"--- stderr ---\n{result.stderr[-2000:]}"
    )
