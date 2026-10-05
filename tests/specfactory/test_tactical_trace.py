# spec: docs/northstar/plans/2026-10-05-lockstep-backend-spec.md, "trace" lane row
"""Tests for scripts/specfactory/tactical_trace.py: same build twice gives the
same trace; --compare names the first differing tick and section; a library
without om_world_checksum_full fails clearly."""
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent.parent
SCRIPT = REPO / "scripts" / "specfactory" / "tactical_trace.py"
PYTHON = sys.executable
LIB = REPO / "libouroboros.so"
SHORT = ["--seed", "1", "--ticks", "60"]

needs_lib = pytest.mark.skipif(not LIB.exists(), reason="libouroboros.so not built")


def run(*args):
    return subprocess.run([PYTHON, str(SCRIPT), *args], capture_output=True, text=True, timeout=300)


@needs_lib
def test_trace_identical_across_two_runs():
    a = run("--lib", str(LIB), *SHORT)
    b = run("--lib", str(LIB), *SHORT)
    assert a.returncode == 0, a.stderr
    assert a.stdout == b.stdout
    rows = [ln for ln in a.stdout.splitlines() if ln.startswith("tick ")]
    assert len(rows) == 6
    # "tick T combined s0 ... s8": 3 + 9 fields
    assert len(rows[0].split()) == 12


@needs_lib
def test_positive_control_compare_names_first_differing_tick_and_section(tmp_path):
    a = run("--lib", str(LIB), *SHORT).stdout
    lines = a.splitlines()
    idx = next(i for i, ln in enumerate(lines) if ln.startswith("tick 30 "))
    fields = lines[idx].split()
    fields[3 + 4] = str(int(fields[3 + 4]) ^ 1)  # section s4
    lines[idx] = " ".join(fields)
    fa, fb = tmp_path / "a.txt", tmp_path / "b.txt"
    fa.write_text(a)
    fb.write_text("\n".join(lines) + "\n")
    same = run("--compare", str(fa), str(fa))
    assert same.returncode == 0
    r = run("--compare", str(fa), str(fb))
    assert r.returncode != 0
    assert "tick 30" in r.stdout and "section s4" in r.stdout


def test_missing_symbol_fails_clearly():
    libm = next((p for p in ("/lib/x86_64-linux-gnu/libm.so.6", "/usr/lib/x86_64-linux-gnu/libm.so.6")
                 if Path(p).exists()), None)
    if libm is None:
        pytest.skip("no libm to stand in for a stale library")
    r = run("--lib", libm, *SHORT)
    assert r.returncode != 0
    assert "om_world_checksum_full" in r.stderr
