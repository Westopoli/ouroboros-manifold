"""PX-7: tests for scripts/specfactory/suite_regression.py (the "before" this
probe is willing to trust on the real replay). A synthetic two-test git repo
(never tests/csim, never csrc/) proves whole_suite_regression()'s
before/after diffing and predecessor_only_regression()'s narrower re-run
actually distinguish a merge that introduces a real regression from one that
does not, and that a test already red before a diff is never miscounted as a
"new" failure.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts" / "specfactory"))
import suite_regression as sr  # noqa: E402

PYTHON = "/home/westopoli/Projects/agora/.venv/bin/python"

# The synthetic fixture's libmod.py is a plain .py module, unlike the real
# replay's C .so -- without this, a before/after pair that lands within the
# same mtime tick can reuse a stale __pycache__ .pyc from the "before" run
# and silently hide the change (found empirically while writing this test:
# "return 1" -> "return 2" is the same byte length, so size+mtime alone
# didn't invalidate the cache). Set once for the whole test module.
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"

LIBMOD_BASE = "def value():\n    return 1\n"
TEST_BASE = (
    "import libmod\n\n"
    "def test_always_ok():\n    assert 1 == 1\n\n"
    "def test_depends_on_value():\n    assert libmod.value() == 1\n"
)


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True)


def _init_repo(base_dir: Path, *, test_text: str = TEST_BASE) -> Path:
    repo = base_dir
    repo.mkdir(parents=True, exist_ok=True)
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "px7@test")
    _git(repo, "config", "user.name", "px7")
    (repo / "libmod.py").write_text(LIBMOD_BASE)
    (repo / "test_synth.py").write_text(test_text)
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "base")
    return repo


def _diff_from_edit(repo: Path, new_libmod_text: str) -> str:
    """Writes new_libmod_text, diffs against HEAD, then restores the working
    tree to the base commit's content -- the returned diff is meant to be
    applied by suite_regression.apply_diff, not left lying around."""
    orig = (repo / "libmod.py").read_text()
    (repo / "libmod.py").write_text(new_libmod_text)
    diff = subprocess.run(["git", "diff"], cwd=repo, capture_output=True, text=True).stdout
    (repo / "libmod.py").write_text(orig)
    return diff


def _bad_diff(repo: Path) -> str:
    """Breaks test_depends_on_value: libmod.value() now returns 2."""
    return _diff_from_edit(repo, "def value():\n    return 2\n")


def _good_diff(repo: Path) -> str:
    """Adds an unused function; value() is untouched, nothing should break."""
    return _diff_from_edit(repo, LIBMOD_BASE + "\ndef unused():\n    return 42\n")


# ---------------------------------------------------------------- parse_pytest --

def test_parse_pytest_extracts_failing_ids_in_order():
    stdout = (
        ".FF.                                                     [100%]\n"
        "=================================== FAILURES ===================================\n"
        "=========================== short test summary info ============================\n"
        "FAILED test_synth.py::test_a - assert 1 == 2\n"
        "FAILED test_synth.py::test_b - AssertionError\n"
        "2 failed, 2 passed in 0.02s\n"
    )
    passed, failed, ids = sr.parse_pytest(stdout)
    assert (passed, failed, ids) == (2, 2, ("test_synth.py::test_a", "test_synth.py::test_b"))


def test_parse_pytest_counts_errors_as_failed():
    stdout = "1 passed, 1 error in 0.01s\nERROR test_synth.py::test_c - ImportError\n"
    passed, failed, ids = sr.parse_pytest(stdout)
    assert (passed, failed, ids) == (1, 1, ("test_synth.py::test_c",))


# ---------------------------------------------------------------- whole_suite_regression --

def test_whole_suite_regression_flags_new_failure_positive_control(tmp_path):
    """Positive control: a diff that breaks a previously-green test must be
    named in new_failures and the merge rejected."""
    repo = _init_repo(tmp_path / "repo")
    diff = _bad_diff(repo)
    report = sr.whole_suite_regression(repo, diff, python_exe=PYTHON, test_args=["test_synth.py"])
    assert report.new_failures == ["test_synth.py::test_depends_on_value"]
    assert report.accept is False
    assert report.before.failed == 0
    assert report.after.failed == 1


def test_whole_suite_regression_accepts_clean_diff_negative_control(tmp_path):
    """Negative control: a diff that touches nothing the tests exercise must
    report an empty new-failure set and an accepted merge."""
    repo = _init_repo(tmp_path / "repo")
    diff = _good_diff(repo)
    report = sr.whole_suite_regression(repo, diff, python_exe=PYTHON, test_args=["test_synth.py"])
    assert report.new_failures == []
    assert report.accept is True


def test_pre_existing_failure_is_not_counted_as_new(tmp_path):
    """A test that was already red before the diff must never appear in
    new_failures, even though it's still red after -- proves the tool
    computes red-after-AND-green-before, not just "red after"."""
    test_text = TEST_BASE + "\ndef test_already_red():\n    assert False\n"
    repo = _init_repo(tmp_path / "repo", test_text=test_text)
    diff = _good_diff(repo)
    report = sr.whole_suite_regression(repo, diff, python_exe=PYTHON, test_args=["test_synth.py"])
    assert "test_synth.py::test_already_red" not in report.new_failures
    assert report.accept is True
    assert "test_synth.py::test_already_red" in report.before.failing_ids
    assert "test_synth.py::test_already_red" in report.after.failing_ids


# ---------------------------------------------------------------- predecessor_only_regression --

def test_predecessor_only_can_miss_what_whole_suite_catches(tmp_path):
    """The real finding this probe measures on the actual incident: a
    predecessor-only rule only re-runs the tests it was told to own. When the
    regression lands in a test no predecessor owns, predecessor-only accepts
    while whole-suite correctly rejects the same diff."""
    repo = _init_repo(tmp_path / "repo")
    diff = _bad_diff(repo)

    whole = sr.whole_suite_regression(repo, diff, python_exe=PYTHON, test_args=["test_synth.py"])
    assert whole.new_failures == ["test_synth.py::test_depends_on_value"]
    assert whole.accept is False

    # whole_suite_regression already applied the diff to `repo` above.
    pred = sr.predecessor_only_regression(
        repo, diff, ["test_synth.py::test_always_ok"], python_exe=PYTHON, apply_first=False,
    )
    assert pred.accept is True  # miss: the broken test was never in its list
    assert pred.result.failed == 0


def test_predecessor_only_catches_regression_it_actually_owns(tmp_path):
    """When the predecessor DOES own the broken test, predecessor-only
    rejects too -- proves the miss above is about test ownership, not a
    broken predecessor-only implementation."""
    repo = _init_repo(tmp_path / "repo")
    diff = _bad_diff(repo)

    pred = sr.predecessor_only_regression(
        repo, diff, ["test_synth.py::test_depends_on_value"], python_exe=PYTHON,
    )
    assert pred.accept is False
    assert pred.result.failed == 1
