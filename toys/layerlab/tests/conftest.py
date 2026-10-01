"""Pytest session setup for the layer lab: put toys/layerlab on sys.path and build the library once.

Run from toys/layerlab/ (SPEC.md section 10). A failed make aborts the whole session loudly.
"""
import subprocess
import sys
from pathlib import Path

import pytest

LAB = Path(__file__).resolve().parent.parent

if str(LAB) not in sys.path:
    sys.path.insert(0, str(LAB))


def pytest_sessionstart(session):
    proc = subprocess.run(["make"], cwd=LAB, capture_output=True, text=True)
    if proc.returncode != 0:
        raise pytest.UsageError(
            "make failed in %s (rc=%d)\n--- stdout ---\n%s\n--- stderr ---\n%s"
            % (LAB, proc.returncode, proc.stdout, proc.stderr)
        )


@pytest.fixture(scope="session")
def lab_dir():
    return LAB


@pytest.fixture(scope="session")
def scenarios_dir():
    return LAB / "scenarios"
