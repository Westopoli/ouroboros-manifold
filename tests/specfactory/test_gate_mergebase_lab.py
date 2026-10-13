# spec: merge gate harness fixes 2026-10-06 (footprint diffs the merge base; regression_lab stage).
"""Fix 1: changed_files / footprint diff against the merge base, so a file pushed to main after
the candidate branched is not an "unmapped file". Fix 2: the regression_lab stage runs
tests/skilllab/integration and /ground when csrc/ or scripts/skilllab/ changes, skipped otherwise."""
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts" / "specfactory"))

import merge_gate_support as mgs  # noqa: E402


def _git(repo, *args):
    return subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True).stdout.strip()


def _commit(repo, name, text="x\n", msg=None):
    p = repo / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text)
    _git(repo, "add", name)
    _git(repo, "commit", "-q", "-m", msg or name)


def _fixture(tmp_path, cand_file):
    """main = base; candidate branches, adds cand_file; main then gains docs/late.md."""
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "config", "user.email", "g@t")
    _git(repo, "config", "user.name", "g")
    _commit(repo, "base.txt")
    _git(repo, "checkout", "-q", "-b", "cand")
    _commit(repo, cand_file)
    _git(repo, "checkout", "-q", "main")
    _commit(repo, "docs/late.md")
    _git(repo, "checkout", "-q", "cand")
    return repo


def test_changed_files_ignores_files_main_gained_after_branching(tmp_path):
    repo = _fixture(tmp_path, "docs/mine.md")
    assert mgs.changed_files(repo, "main") == ["docs/mine.md"]


def test_changed_files_still_lists_a_genuine_candidate_file(tmp_path):
    """Positive control: the candidate's own file is listed, so the fixture can show a diff at all."""
    repo = _fixture(tmp_path, "csrc/x.c")
    assert "csrc/x.c" in mgs.changed_files(repo, "main")


def test_lab_stage_runs_when_csrc_changes(tmp_path, monkeypatch):
    repo = _fixture(tmp_path, "csrc/x.c")
    seen = []
    monkeypatch.setattr(mgs, "regression_check",
                        lambda cand, base, args, **kw: (seen.append(list(args)) or (True, "stub", None)))
    ok, detail = mgs.regression_lab_check(repo, "main")
    assert ok and seen == [["tests/skilllab/integration", "tests/skilllab/ground"]]


def test_lab_stage_runs_when_scripts_skilllab_changes(tmp_path, monkeypatch):
    repo = _fixture(tmp_path, "scripts/skilllab/a.py")
    seen = []
    monkeypatch.setattr(mgs, "regression_check",
                        lambda cand, base, args, **kw: (seen.append(args) or (True, "stub", None)))
    mgs.regression_lab_check(repo, "main")
    assert seen


def test_lab_stage_skipped_on_docs_only_diff(tmp_path, monkeypatch):
    repo = _fixture(tmp_path, "docs/mine.md")
    monkeypatch.setattr(mgs, "regression_check", lambda *a, **k: (_ for _ in ()).throw(AssertionError("ran")))
    ok, detail = mgs.regression_lab_check(repo, "main")
    assert ok and detail.startswith("skipped")


def test_gate_script_wires_regression_lab_and_merge_base():
    sh = (REPO / "scripts/specfactory/merge_gate.sh").read_text()
    assert "regression-lab" in sh and "reject regression_lab" in sh and "merge-base" in sh
