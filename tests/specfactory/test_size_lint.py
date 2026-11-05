# spec: docs/northstar/plans/witty-cuddling-goblet.md::Wave 0 item 3
"""Tests for scripts/specfactory/size_lint.py (build-unit-size gate)."""
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
SIZE_LINT = REPO / "scripts" / "specfactory" / "size_lint.py"


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True)


def _init_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "csrc").mkdir()
    (repo / "csrc" / "foo.c").write_text("int foo(void) { return 1; }\n")
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "t@example.com")
    _git(repo, "config", "user.name", "t")
    _git(repo, "add", ".")
    _git(repo, "commit", "-q", "-m", "init")
    _git(repo, "branch", "-q", "main")
    return repo


def _write_pieces(tmp_path: Path, body: str) -> Path:
    path = tmp_path / "pieces.toml"
    path.write_text(body)
    return path


def _run(repo: Path, branch: str, base: str, piece_id: str, pieces_path: Path, *extra: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SIZE_LINT), branch, base, "--piece-id", piece_id,
         "--pieces", str(pieces_path), "--project", str(repo), *extra],
        capture_output=True, text=True,
    )


def test_help():
    proc = subprocess.run([sys.executable, str(SIZE_LINT), "--help"], capture_output=True, text=True)
    assert proc.returncode == 0
    assert "--hard-cap-lines" in proc.stdout


def test_small_owned_change_is_ok(tmp_path):
    repo = _init_repo(tmp_path)
    _git(repo, "checkout", "-q", "-b", "feature")
    (repo / "csrc" / "foo.c").write_text("int foo(void) { return 1; }\nint bar(void) { return 2; }\n")
    _git(repo, "commit", "-aqm", "small change")
    pieces = _write_pieces(tmp_path, '[[piece]]\nid = "X"\nowns = ["csrc/foo.c"]\n')

    proc = _run(repo, "feature", "main", "X", pieces)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "SIZE LINT OK" in proc.stdout
    assert "1 changed lines across 1 owned file" in proc.stdout


def test_over_line_threshold_warns_but_does_not_fail(tmp_path):
    repo = _init_repo(tmp_path)
    _git(repo, "checkout", "-q", "-b", "feature")
    big_body = "int foo(void) { return 1; }\n" + "\n".join(f"int f{i}(void) {{ return {i}; }}" for i in range(1600))
    (repo / "csrc" / "foo.c").write_text(big_body + "\n")
    _git(repo, "commit", "-aqm", "big change")
    pieces = _write_pieces(tmp_path, '[[piece]]\nid = "X"\nowns = ["csrc/foo.c"]\n')

    proc = _run(repo, "feature", "main", "X", pieces)
    assert proc.returncode == 0, proc.stdout + proc.stderr  # warn-only, never blocks by default
    assert "SIZE LINT WARN" in proc.stdout


def test_positive_control_hard_cap_fails(tmp_path):
    """Planted violation: the same over-threshold change, but with
    --hard-cap-lines set low enough that it must be caught -- proving this
    lint really can exit nonzero, not just print WARN forever."""
    repo = _init_repo(tmp_path)
    _git(repo, "checkout", "-q", "-b", "feature")
    big_body = "int foo(void) { return 1; }\n" + "\n".join(f"int f{i}(void) {{ return {i}; }}" for i in range(150))
    (repo / "csrc" / "foo.c").write_text(big_body + "\n")
    _git(repo, "commit", "-aqm", "big change")
    pieces = _write_pieces(tmp_path, '[[piece]]\nid = "X"\nowns = ["csrc/foo.c"]\n')

    proc = _run(repo, "feature", "main", "X", pieces, "--hard-cap-lines", "50")
    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert "SIZE LINT FAIL" in proc.stdout
    assert "hard-cap-lines=50" in proc.stdout


def test_more_than_one_owned_file_warns(tmp_path):
    repo = _init_repo(tmp_path)
    (repo / "csrc" / "bar.c").write_text("int bar(void) { return 1; }\n")
    _git(repo, "add", ".")
    _git(repo, "commit", "-qm", "add bar")
    _git(repo, "checkout", "-q", "-b", "feature")
    (repo / "csrc" / "foo.c").write_text("int foo(void) { return 2; }\n")
    (repo / "csrc" / "bar.c").write_text("int bar(void) { return 2; }\n")
    _git(repo, "commit", "-aqm", "touch both")
    pieces = _write_pieces(tmp_path, '[[piece]]\nid = "X"\nowns = ["csrc/foo.c", "csrc/bar.c"]\n')

    proc = _run(repo, "feature", "main", "X", pieces)
    assert "SIZE LINT WARN" in proc.stdout
    assert "2 owned file(s)" in proc.stdout


def test_non_owned_files_are_not_counted(tmp_path):
    """A piece's branch also touching a new test file (a real shape: W-1f's
    branch changed csrc/enemy_macro.c plus two test files, but B13 owns only
    the .c file) must not inflate this piece's own size against files a
    separate docs-profile tests landing owns."""
    repo = _init_repo(tmp_path)
    (repo / "tests").mkdir()
    (repo / "tests" / "test_foo.py").write_text("def test_a(): pass\n")
    _git(repo, "add", ".")
    _git(repo, "commit", "-qm", "add test dir")
    _git(repo, "checkout", "-q", "-b", "feature")
    (repo / "csrc" / "foo.c").write_text("int foo(void) { return 2; }\n")
    (repo / "tests" / "test_foo.py").write_text("def test_a(): pass\ndef test_b(): pass\ndef test_c(): pass\n")
    _git(repo, "commit", "-aqm", "code plus tests")
    pieces = _write_pieces(tmp_path, '[[piece]]\nid = "X"\nowns = ["csrc/foo.c"]\n')

    proc = _run(repo, "feature", "main", "X", pieces)
    assert "2 changed lines across 1 owned file" in proc.stdout
    assert "test_foo.py" not in proc.stdout


def test_piece_not_in_pieces_toml_is_skipped_as_docs_profile(tmp_path):
    """CONST-1's real shape: 11 files, 526 changed lines, no pieces.toml
    entry at all -- a docs-profile landing this lint must not try to size."""
    repo = _init_repo(tmp_path)
    _git(repo, "checkout", "-q", "-b", "feature")
    (repo / "csrc" / "foo.c").write_text("int foo(void) { return 2; }\n" * 50)
    _git(repo, "commit", "-aqm", "const rewrite")
    pieces = _write_pieces(tmp_path, "")

    proc = _run(repo, "feature", "main", "CONST-1", pieces)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "SIZE LINT SKIP" in proc.stdout
    assert "docs-profile" in proc.stdout


def test_explicit_docs_profile_flag_skips_even_with_owns(tmp_path):
    repo = _init_repo(tmp_path)
    _git(repo, "checkout", "-q", "-b", "feature")
    (repo / "csrc" / "foo.c").write_text("int foo(void) { return 2; }\n")
    _git(repo, "commit", "-aqm", "change")
    pieces = _write_pieces(tmp_path, '[[piece]]\nid = "X"\nowns = ["csrc/foo.c"]\n')

    proc = _run(repo, "feature", "main", "X", pieces, "--profile", "docs")
    assert proc.returncode == 0
    assert "SIZE LINT SKIP" in proc.stdout


def test_real_examples_from_the_repo():
    """The brief's own two worked examples, run against the real repo."""
    proc_w1f = subprocess.run(
        [sys.executable, str(SIZE_LINT), "c46afcdf", "origin/main", "--piece-id", "B13"],
        cwd=REPO, capture_output=True, text=True,
    )
    assert proc_w1f.returncode == 0, proc_w1f.stdout + proc_w1f.stderr
    assert "SIZE LINT OK" in proc_w1f.stdout
    assert "csrc/enemy_macro.c" in proc_w1f.stdout

    proc_const1 = subprocess.run(
        [sys.executable, str(SIZE_LINT), "8baad88c", "origin/main", "--piece-id", "CONST-1"],
        cwd=REPO, capture_output=True, text=True,
    )
    assert proc_const1.returncode == 0, proc_const1.stdout + proc_const1.stderr
    assert "SIZE LINT SKIP" in proc_const1.stdout
