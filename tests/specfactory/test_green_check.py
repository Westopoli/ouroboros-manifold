# spec: docs/legacy/test_specs/drift-gate-and-green-check.md::Acceptance criteria::AC-5
"""Tests for scripts/specfactory/green_check.py.

Builds a throwaway git repo per test with one stub file and a tiny
acceptance test, so this suite never depends on the real ouroboros-manifold
repo's own state or history -- green_check applies to some card's project,
and a synthetic one proves the mechanism without coupling to a real card.
"""
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
GREEN_CHECK = REPO / "scripts" / "specfactory" / "green_check.py"


def _init_project(tmp_path: Path, stub_body: str, include_pytest_test: bool = False) -> Path:
    project = tmp_path / "project"
    project.mkdir()
    (project / "target.py").write_text(stub_body)
    # Sentinel acceptance check: exits non-pytest, non-zero on failure. A
    # green_check implementation that just hardcodes "run pytest on
    # test_target.py" regardless of the card's own acceptance list cannot
    # coincidentally satisfy this when test_target.py does not exist.
    (project / "check_value.py").write_text(
        "import target\n"
        "import sys\n"
        "sys.exit(0 if target.value() == 42 else 1)\n"
    )
    if include_pytest_test:
        (project / "test_target.py").write_text(
            "from target import value\n"
            "def test_value():\n"
            "    assert value() == 42\n"
        )
    subprocess.run(["git", "init", "-q"], cwd=project, check=True)
    subprocess.run(["git", "config", "user.email", "t@example.com"], cwd=project, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=project, check=True)
    subprocess.run(["git", "add", "."], cwd=project, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=project, check=True)
    return project


def _write_card(tmp_path: Path, project: Path) -> Path:
    # Sentinel-shaped acceptance command (not a pytest invocation) -- see
    # _init_project's check_value.py.
    card = tmp_path / "card.md"
    card.write_text(
        "---\n"
        f"project: {project}\n"
        "acceptance:\n"
        f'  - "{sys.executable} check_value.py"\n'
        "snippet_file: target.py\n"
        "---\n"
    )
    return card


def _write_card_pytest(tmp_path: Path, project: Path) -> Path:
    # Pytest-shaped acceptance command, kept alongside the sentinel shape in
    # _write_card so both acceptance-command shapes get coverage.
    card = tmp_path / "card.md"
    card.write_text(
        "---\n"
        f"project: {project}\n"
        "acceptance:\n"
        f'  - "{sys.executable} -m pytest -q test_target.py"\n'
        "snippet_file: target.py\n"
        "---\n"
    )
    return card


def _run(card: Path, reference: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(GREEN_CHECK), str(card), str(reference)],
        capture_output=True, text=True,
    )


def test_green_check_passes_on_a_real_reference(tmp_path):
    project = _init_project(tmp_path, "def value():\n    raise NotImplementedError\n")
    card = _write_card(tmp_path, project)
    reference = tmp_path / "reference.py"
    reference.write_text("def value():\n    return 42\n")
    original = (project / "target.py").read_text()

    proc = _run(card, reference)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert (project / "target.py").read_text() == original, (
        "green_check must apply the reference in a scratch worktree, never "
        "in the caller's own checkout"
    )

    worktrees = subprocess.run(
        ["git", "worktree", "list"], cwd=project, capture_output=True, text=True, check=True,
    )
    worktree_lines = [line for line in worktrees.stdout.splitlines() if line.strip()]
    assert len(worktree_lines) == 1, (
        "green_check must remove its scratch worktree before returning; "
        "git worktree list shows leftovers:\n" + worktrees.stdout
    )


def test_green_check_fails_a_reference_that_does_not_pass(tmp_path):
    project = _init_project(
        tmp_path, "def value():\n    raise NotImplementedError\n", include_pytest_test=True,
    )
    card = _write_card_pytest(tmp_path, project)
    reference = tmp_path / "reference.py"
    reference.write_text("def value():\n    return 0\n")

    proc = _run(card, reference)
    assert proc.returncode == 1, proc.stdout + proc.stderr

    worktrees = subprocess.run(
        ["git", "worktree", "list"], cwd=project, capture_output=True, text=True, check=True,
    )
    worktree_lines = [line for line in worktrees.stdout.splitlines() if line.strip()]
    assert len(worktree_lines) == 1, (
        "green_check must remove its scratch worktree even when the reference "
        "fails acceptance; git worktree list shows leftovers:\n" + worktrees.stdout
    )


def test_green_check_exits_3_on_a_missing_card(tmp_path):
    reference = tmp_path / "reference.py"
    reference.write_text("def value():\n    return 42\n")

    proc = _run(tmp_path / "no_such_card.md", reference)
    assert proc.returncode == 3, proc.stdout + proc.stderr


def test_green_check_exits_3_on_a_missing_reference(tmp_path):
    project = _init_project(tmp_path, "def value():\n    raise NotImplementedError\n")
    card = _write_card(tmp_path, project)

    proc = _run(card, tmp_path / "no_such_reference.py")
    assert proc.returncode == 3, proc.stdout + proc.stderr


def test_green_check_refuses_a_reference_that_also_passes_on_the_stub(tmp_path):
    # Stub already returns 42 -- a "reference" here proves nothing.
    project = _init_project(tmp_path, "def value():\n    return 42\n")
    card = _write_card(tmp_path, project)
    reference = tmp_path / "reference.py"
    reference.write_text("def value():\n    return 42\n")

    proc = _run(card, reference)
    assert proc.returncode == 2, proc.stdout + proc.stderr
    assert "already passes" in (proc.stdout + proc.stderr).lower()

    worktrees = subprocess.run(
        ["git", "worktree", "list"], cwd=project, capture_output=True, text=True, check=True,
    )
    worktree_lines = [line for line in worktrees.stdout.splitlines() if line.strip()]
    assert len(worktree_lines) == 1, (
        "green_check must remove its scratch worktree even on the "
        "already-passes refusal path; git worktree list shows leftovers:\n"
        + worktrees.stdout
    )


def test_green_check_worktree_uses_committed_head_not_working_tree_state(tmp_path):
    # Committed stub still raises; an uncommitted edit makes it look already
    # solved. A real `git worktree add` checks out committed HEAD and
    # ignores the dirty working tree, so acceptance still fails before the
    # reference is applied and the run ends 0 once it is. A naive copy of
    # the working directory would pick up the dirty "return 42" instead,
    # trip the already-passes refusal, and exit 2.
    project = _init_project(tmp_path, "def value():\n    raise NotImplementedError\n")
    card = _write_card(tmp_path, project)
    reference = tmp_path / "reference.py"
    reference.write_text("def value():\n    return 42\n")
    (project / "target.py").write_text("def value():\n    return 42\n")

    proc = _run(card, reference)
    assert proc.returncode == 0, proc.stdout + proc.stderr


def test_green_check_exits_3_on_empty_acceptance_list(tmp_path):
    project = _init_project(tmp_path, "def value():\n    raise NotImplementedError\n")
    card = tmp_path / "card.md"
    card.write_text(
        "---\n"
        f"project: {project}\n"
        "acceptance:\n"
        "snippet_file: target.py\n"
        "---\n"
    )
    reference = tmp_path / "reference.py"
    reference.write_text("def value():\n    return 42\n")

    proc = _run(card, reference)
    assert proc.returncode == 3, proc.stdout + proc.stderr


def test_green_check_exits_3_when_project_is_not_a_directory(tmp_path):
    bogus_project = tmp_path / "does_not_exist"
    card = tmp_path / "card.md"
    card.write_text(
        "---\n"
        f"project: {bogus_project}\n"
        "acceptance:\n"
        f'  - "{sys.executable} check_value.py"\n'
        "snippet_file: target.py\n"
        "---\n"
    )
    reference = tmp_path / "reference.py"
    reference.write_text("def value():\n    return 42\n")

    proc = _run(card, reference)
    assert proc.returncode == 3, proc.stdout + proc.stderr


def test_spec_factory_doc_documents_green_check():
    doc = (REPO / "docs" / "northstar" / "spec_factory.md").read_text()
    assert "green_check.py" in doc, (
        "docs/northstar/spec_factory.md's pipeline table must gain a "
        "green_check.py row per AC6"
    )
    assert "tests/csim/references" in doc, (
        "docs/northstar/spec_factory.md must say where green_check's "
        "reference bodies live"
    )
