# spec: docs/northstar/plans/2026-10-29-layered-gate-spec.md section 9 "HARNESS-rulepins-split" (story H-018)
# Rule pins: R-990-01@?, R-999-05@?
"""Tests for story H-018 (rulepins-split): scripts/specfactory/rule_pins_tests.py.

Story H-018 quote: "The pins warning tells stale pins from tests that were never pinned, instead of one number
nobody reads."
Spec (docs/northstar/plans/2026-10-29-layered-gate-spec.md section 9, HARNESS-rulepins-split), word for word:
  "Fix: the line becomes `PINS WARN <n> stale, <m> missing outside the diff`, same prefix (merge_gate.sh:332 and
  pre_gate.sh grep `PINS WARN`), no threshold, no new reject. Tests: a fixture with one stale and two missing pins
  prints `1 stale, 2 missing`; zero of both prints `PINS OK` as today (positive control); the prefix is unchanged."

Fixture (all under <root>/tests/, rule R-990-01 from the test_spec_provenance fixture tree, run with
`check <root> --only tests/test_clean.py` so the other two files are outside the diff):
  test_clean.py  correct own pin                                -> in the diff, no finding
  test_stale.py  own pin R-990-01@000000 (wrong)                -> 1 stale
  test_miss.py   no own line, not in the sidecar, cites R-990-01 and R-999-05 -> 2 missing
The tool's existing meaning of the words (rule_pins_tests.py:63-66): "stale" is an id that has a pin that is wrong,
"missing" is an id with no pin at all.

Unstated by the spec (not tested): the text when only one of the two counts is zero.
Red reason on the built tree: the tool prints `PINS WARN 3 stale outside the diff` (rule_pins_tests.py:82).
"""
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from test_rule_pins_tests import PIN, SCRIPT, STALE, _put, _root  # noqa: E402

CLEAN = f"# Rule pins: R-990-01@{PIN}\ndef test_x():\n    \"\"\"R-990-01\"\"\"\n"
STALE_FILE = f"# Rule pins: R-990-01@{STALE}\ndef test_x():\n    \"\"\"R-990-01\"\"\"\n"
MISS_FILE = "def test_x():\n    \"\"\"R-990-01 R-999-05\"\"\"\n"


def _run(root: Path, *only: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SCRIPT), "check", str(root), "--only", *only],
                          cwd=root, capture_output=True, text=True)


def _fixture(tmp_path: Path, stale: int, missing_files: int) -> Path:
    root = _root(tmp_path)
    _put(root, "tests/test_clean.py", CLEAN)
    if stale:
        _put(root, "tests/test_stale.py", STALE_FILE)
    if missing_files:
        _put(root, "tests/test_miss.py", MISS_FILE)
    return root


def _warn(res) -> list:
    return [l for l in res.stdout.splitlines() if l.startswith("PINS WARN")]


# ---- positive controls: green today -----------------------------------------------------------------------

def test_control_zero_stale_zero_missing_prints_pins_ok_as_today(tmp_path):
    """Spec: "zero of both prints `PINS OK` as today (positive control)"."""
    root = _fixture(tmp_path, stale=0, missing_files=0)
    res = _run(root, "tests/test_clean.py")
    assert res.returncode == 0, res.stdout + res.stderr
    assert res.stdout.splitlines() == ["PINS OK 1 files 1 ids"], res.stdout


def test_control_outside_findings_still_warn_with_the_prefix_and_exit_0(tmp_path):
    """Spec: "same prefix ..., no threshold, no new reject" and "the prefix is unchanged"."""
    root = _fixture(tmp_path, stale=1, missing_files=1)
    res = _run(root, "tests/test_clean.py")
    warn = _warn(res)
    assert res.returncode == 0, res.stdout + res.stderr
    assert len(warn) == 1 and warn[0].startswith("PINS WARN ") and warn[0].endswith(" outside the diff"), res.stdout
    assert not [l for l in res.stdout.splitlines() if l.startswith("PINS REJECT")], res.stdout


def test_control_a_named_stale_file_still_rejects_with_the_old_line(tmp_path):
    """Spec: "no new reject" - the reject lines are unchanged."""
    root = _fixture(tmp_path, stale=1, missing_files=0)
    res = _run(root, "tests/test_stale.py")
    rej = [l for l in res.stdout.splitlines() if l.startswith("PINS REJECT")]
    assert res.returncode == 1, res.stdout + res.stderr
    assert rej == [f"PINS REJECT tests/test_stale.py R-990-01 stale {STALE} {PIN}"], res.stdout


# ---- red until the line is split ---------------------------------------------------------------------------

def test_one_stale_and_two_missing_print_the_split_line(tmp_path):
    """Spec: "a fixture with one stale and two missing pins prints `1 stale, 2 missing`"; the line is
    `PINS WARN <n> stale, <m> missing outside the diff`."""
    root = _fixture(tmp_path, stale=1, missing_files=1)
    res = _run(root, "tests/test_clean.py")
    assert res.returncode == 0, res.stdout + res.stderr
    assert _warn(res) == ["PINS WARN 1 stale, 2 missing outside the diff"], res.stdout
