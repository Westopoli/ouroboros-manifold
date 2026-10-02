"""A49 (architect rulings 2026-10-01 round 2, Addendum 22): the merge gate's `regression` path
defect. merge_gate_support.regression_check normalises the candidate directory to "<WORKTREE>"
in the candidate side's first-assertion lines with a plain str.replace of str(candidate_dir).
When the caller passes a RELATIVE directory (".", or "repo"), str(candidate_dir) is "." or
"repo", so every dot (or every occurrence of the word) in an assertion line is rewritten:
"assert 1.5 == 2.5" becomes "assert 1<WORKTREE>5 == 2<WORKTREE>5" on the candidate side only,
and any red id whose first line holds a decimal reads as a changed assertion although nothing
about it changed. The baseline side is normalised with its own absolute worktree path and is
never affected.

The contract these tests pin: the same fixture run with an absolute and with a relative
candidate path gives identical output (same `changed_assertions`, empty for identical lines;
same candidate first-assertion text; same ok/detail), and a genuinely changed line is flagged
under both spellings.

Fixture. A throwaway git repo with one always-red test whose first assertion line holds a
decimal (and, for the named-directory spelling, the word "repo"); the candidate commit changes
only a README, so every red id fails exactly as on the base. Red today: the two relative cases.
"""
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts" / "specfactory"))

import merge_gate_support as mgs  # noqa: E402
import suite_regression as sr  # noqa: E402

PYTHON = sr.DEFAULT_PYTHON
DECIMAL_TEST = (
    "def test_decimal():\n"
    "    assert 1.5 == 2.5, 'the repo value 1.5 is not 2.5'\n"
)
CHANGED_TEST = (
    "def test_decimal():\n"
    "    assert 1.5 == 3.5, 'the repo value 1.5 is not 3.5'\n"
)
ID = "test_synth.py::test_decimal"


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True)


def _make_repo(base: Path, candidate_test: str | None = None) -> tuple[Path, str]:
    """Base commit holds DECIMAL_TEST. The candidate commit changes the test to `candidate_test`
    when given, otherwise only a README (an identical red line). Returns (repo, base sha)."""
    base.mkdir(parents=True)
    _git(base, "init", "-q")
    _git(base, "config", "user.email", "gate@test")
    _git(base, "config", "user.name", "gate")
    (base / "test_synth.py").write_text(DECIMAL_TEST)
    _git(base, "add", "test_synth.py")
    _git(base, "commit", "-q", "-m", "base")
    sha = _git(base, "rev-parse", "HEAD").stdout.strip()
    if candidate_test is None:
        (base / "README.md").write_text("docs only\n")
        _git(base, "add", "README.md")
    else:
        (base / "test_synth.py").write_text(candidate_test)
        _git(base, "add", "test_synth.py")
    _git(base, "commit", "-q", "-m", "candidate")
    return base, sha


def _run(candidate_dir: Path, sha: str, worktree_root: Path):
    return mgs.regression_check(candidate_dir, sha, ["test_synth.py"], python_exe=PYTHON,
                                worktree_root=worktree_root)


def test_the_candidate_side_first_line_is_a_decimal_line(tmp_path):
    """Positive control for the fixture: with an absolute path the red id is seen red on both
    sides, its first assertion line is the unmangled decimal line, and nothing is flagged."""
    repo, sha = _make_repo(tmp_path / "repo")
    ok, detail, report = _run(repo, sha, tmp_path)
    assert ok is True, detail
    assert ID in report.before.failing_ids and ID in report.after.failing_ids
    assert "the repo value 1.5 is not 2.5" in report.after.first_assertion[ID]
    assert "the repo value 1.5 is not 2.5" in report.before.first_assertion[ID]
    assert report.changed_assertions == []


def test_a_really_changed_line_is_flagged_under_an_absolute_path(tmp_path):
    """Positive control: a candidate that moves the failing line (2.5 -> 3.5) is a changed
    assertion (a WARN, the gate still accepts)."""
    repo, sha = _make_repo(tmp_path / "repo", CHANGED_TEST)
    ok, detail, report = _run(repo, sha, tmp_path)
    assert ok is True, detail
    assert report.changed_assertions == [ID]


def test_a_really_changed_line_is_flagged_under_a_relative_path(tmp_path, monkeypatch):
    """The same change under a relative spelling is also flagged (green today: the defect only
    adds false positives, it does not hide real changes)."""
    repo, sha = _make_repo(tmp_path / "repo", CHANGED_TEST)
    monkeypatch.chdir(repo)
    ok, detail, report = _run(Path("."), sha, tmp_path)
    assert ok is True, detail
    assert report.changed_assertions == [ID]


def test_dot_candidate_dir_gives_the_same_output_as_the_absolute_path(tmp_path, monkeypatch):
    """A50-style harness fix A49: candidate_dir "." must not turn every dot of an assertion line
    into <WORKTREE>. Same fixture, absolute and relative: identical changed assertions (none),
    identical candidate first-assertion text, identical verdict and detail.
    Red today: the relative run reads 'assert 1<WORKTREE>5 == 2<WORKTREE>5' and flags the id."""
    repo, sha = _make_repo(tmp_path / "repo")
    abs_ok, abs_detail, abs_report = _run(repo, sha, tmp_path)
    monkeypatch.chdir(repo)
    rel_ok, rel_detail, rel_report = _run(Path("."), sha, tmp_path)
    assert abs_report.changed_assertions == []
    assert rel_report.changed_assertions == abs_report.changed_assertions, (
        "relative '.' candidate flagged %r; lines: %r" % (rel_report.changed_assertions,
                                                          rel_report.after.first_assertion))
    assert rel_report.after.first_assertion == abs_report.after.first_assertion
    assert (rel_ok, rel_detail) == (abs_ok, abs_detail)


def test_named_relative_candidate_dir_gives_the_same_output_as_the_absolute_path(tmp_path, monkeypatch):
    """The same for a relative directory name ("repo", run from its parent): the word "repo" in
    an assertion message must survive. Red today: it reads 'the <WORKTREE> value ...'."""
    repo, sha = _make_repo(tmp_path / "repo")
    abs_ok, abs_detail, abs_report = _run(repo, sha, tmp_path)
    monkeypatch.chdir(tmp_path)
    rel_ok, rel_detail, rel_report = _run(Path("repo"), sha, tmp_path)
    assert rel_report.changed_assertions == abs_report.changed_assertions == []
    assert rel_report.after.first_assertion == abs_report.after.first_assertion
    assert (rel_ok, rel_detail) == (abs_ok, abs_detail)


def test_the_absolute_path_is_still_replaced_by_the_placeholder(tmp_path):
    """Positive control (the original F6 behaviour must survive the fix): an assertion line that
    embeds the candidate's absolute directory reads '<WORKTREE>' on the candidate side."""
    repo, sha = _make_repo(tmp_path / "repo")
    probe = ("import pathlib\n"
             "def test_decimal():\n"
             "    raise AttributeError(f'{pathlib.Path(__file__).resolve().parent}/lib.so: undefined symbol')\n")
    (repo / "test_synth.py").write_text(probe)
    _git(repo, "add", "test_synth.py")
    _git(repo, "commit", "-q", "-m", "probe")
    sha2 = _git(repo, "rev-parse", "HEAD~1").stdout.strip()
    ok, detail, report = _run(repo, sha2, tmp_path)
    assert "<WORKTREE>/lib.so" in report.after.first_assertion[ID]
    assert str(repo) not in report.after.first_assertion[ID]
