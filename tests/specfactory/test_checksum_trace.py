# spec: docs/northstar/plans/briefs/2026-09-22-two-day-push.md, item 3
"""Tests for scripts/specfactory/checksum_trace.py: the pure trace-parsing
and comparison logic always; the real libouroboros.so end to end only when
it (or build/O0, build/O2) is already built (mirrors conftest.py's own
skip-when-unbuilt convention)."""
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "scripts" / "specfactory"))

import checksum_trace as ct  # noqa: E402

PYTHON = "/home/westopoli/Projects/agora/.venv/bin/python"
LIB = REPO / "libouroboros.so"
O0_LIB = REPO / "build" / "O0" / "libouroboros.so"
O2_LIB = REPO / "build" / "O2" / "libouroboros.so"


def test_parse_trace_output_reads_ticks_and_final():
    text = "# header line\ntick 10 111\ntick 20 222\nfinal 222\n"
    rows, final = ct.parse_trace_output(text)
    assert rows == [(10, 111), (20, 222)]
    assert final == 222


def test_parse_trace_output_ignores_unrelated_lines():
    text = "some noise\ntick 10 5\nmore noise\nfinal 5\n"
    rows, final = ct.parse_trace_output(text)
    assert rows == [(10, 5)]
    assert final == 5


def test_compare_traces_identical():
    text = "tick 10 5\nfinal 5\n"
    equal, detail = ct.compare_traces(text, text)
    assert equal is True
    assert "IDENTICAL" in detail


def test_positive_control_compare_traces_diverging_checksum():
    a = "tick 10 5\nfinal 5\n"
    b = "tick 10 6\nfinal 6\n"
    equal, detail = ct.compare_traces(a, b)
    assert equal is False
    assert "tick 10" in detail


def test_positive_control_compare_traces_diverging_final_only():
    a = "tick 10 5\nfinal 5\n"
    b = "tick 10 5\nfinal 9\n"
    equal, detail = ct.compare_traces(a, b)
    assert equal is False
    assert "final" in detail


def test_compare_traces_different_row_counts():
    a = "tick 10 5\nfinal 5\n"
    b = "tick 10 5\ntick 20 5\nfinal 5\n"
    equal, detail = ct.compare_traces(a, b)
    assert equal is False
    assert "different number" in detail


def test_compare_traces_missing_final_line():
    a = "tick 10 5\n"
    b = "tick 10 5\n"
    equal, detail = ct.compare_traces(a, b)
    assert equal is False


def test_parse_features_empty_and_list():
    assert ct.parse_features(None) == []
    assert ct.parse_features("") == []
    assert ct.parse_features("1,2,6") == [1, 2, 6]


def test_cli_compare_exit_codes(tmp_path):
    a = tmp_path / "a.txt"
    b = tmp_path / "b.txt"
    a.write_text("tick 10 5\nfinal 5\n")
    b.write_text("tick 10 6\nfinal 6\n")
    proc = subprocess.run(
        [PYTHON, str(REPO / "scripts" / "specfactory" / "checksum_trace.py"), "--compare", str(a), str(b)],
        capture_output=True, text=True,
    )
    assert proc.returncode == 1
    assert proc.stdout.startswith("DIVERGE")


def test_cli_compare_match_exit_zero(tmp_path):
    a = tmp_path / "a.txt"
    b = tmp_path / "b.txt"
    a.write_text("tick 10 5\nfinal 5\n")
    b.write_text("tick 10 5\nfinal 5\n")
    proc = subprocess.run(
        [PYTHON, str(REPO / "scripts" / "specfactory" / "checksum_trace.py"), "--compare", str(a), str(b)],
        capture_output=True, text=True,
    )
    assert proc.returncode == 0
    assert proc.stdout.startswith("MATCH")


@pytest.mark.skipif(not LIB.exists(), reason="libouroboros.so not built")
def test_real_lib_run_produces_cadence_rows_and_final():
    proc = subprocess.run(
        [PYTHON, str(REPO / "scripts" / "specfactory" / "checksum_trace.py"),
         "--lib", str(LIB), "--seed", "1", "--regions", "10", "--ticks", "30", "--features", "6"],
        capture_output=True, text=True, cwd=str(REPO),
    )
    assert proc.returncode == 0, proc.stderr
    rows, final = ct.parse_trace_output(proc.stdout)
    assert len(rows) >= 1
    assert final is not None


@pytest.mark.skipif(not LIB.exists(), reason="libouroboros.so not built")
def test_real_lib_same_seed_twice_is_identical():
    argv = [PYTHON, str(REPO / "scripts" / "specfactory" / "checksum_trace.py"),
            "--lib", str(LIB), "--seed", "1", "--regions", "10", "--ticks", "30", "--features", "6"]
    out_a = subprocess.run(argv, capture_output=True, text=True, cwd=str(REPO)).stdout
    out_b = subprocess.run(argv, capture_output=True, text=True, cwd=str(REPO)).stdout
    equal, detail = ct.compare_traces(out_a, out_b)
    assert equal is True, detail


@pytest.mark.skipif(not (O0_LIB.exists() and O2_LIB.exists()),
                     reason="build/O0 and build/O2 libs not built (Makefile OPT support)")
def test_o0_vs_o2_determinism_500_ticks():
    def _trace(lib):
        argv = [PYTHON, str(REPO / "scripts" / "specfactory" / "checksum_trace.py"),
                "--lib", str(lib), "--seed", "1", "--regions", "60", "--ticks", "500", "--features", "6"]
        return subprocess.run(argv, capture_output=True, text=True, cwd=str(REPO)).stdout

    out_o0 = _trace(O0_LIB)
    out_o2 = _trace(O2_LIB)
    equal, detail = ct.compare_traces(out_o0, out_o2)
    assert equal is True, detail
