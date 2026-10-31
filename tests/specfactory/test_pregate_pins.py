# spec: docs/northstar/plans/2026-10-29-layered-gate-spec.md section 9, HARNESS-pregate-pins (story H-017)
"""H-017 pregate-pins: pre_gate.sh runs the pinned csim tests when the diff touches csrc/.

Story H-017: "A change under csrc runs the pinned csim tests before the push, so a moved golden costs a
minute in the pre-gate and never a two-hour gate."

Spec section 9, HARNESS-pregate-pins: "a pre_gate step after the piece's own tests: when `git diff
--name-only <base>..HEAD` contains any path under `csrc/`, build `pipe/ouroboros_pipe` (W7 needs it;
`tests/long/harness.py:18`) and run, with the manifold venv python, the csim files that carry pinned values,
derived at run time by `git grep -l -E 'PINNED_FULL|FLYER_SECTIONS|GOLDEN_|save_sha256' -- tests/csim`
(about 10 files, 87 tests, 39 s on origin/main in the analysis; no typed list anywhere); a non-zero exit
prints `PREGATE pins REJECT <failing ids>` and pre_gate exits non-zero; no csrc change prints `PREGATE pins
skipped: no csrc change`. Tests on a stub repo fixture: a csrc change that moves a pinned value rejects with
the id named; no csrc change prints the skipped line and exits 0; a csrc change with pins unchanged prints
`PREGATE pins OK <n> tests` (positive control); the grep-derived list is non-empty on the real tree (guards
against the pattern rotting). Draft: `DRAFT-pregate-pins-timeout-s` 600."

Fixture: a throwaway git repo (branch "base", HEAD one commit ahead) holding csrc/unit.c, a Makefile whose
`pipe/ouroboros_pipe` target writes the file, tests/csim/test_pinned.py (carries PINNED_FULL; 3 tests, one of
which needs the built pipe) and tests/csim/test_unpinned.py (no pin token; fails if it is ever run, so it
proves the list is the grep-derived one). The merge gate is a stub (PRE_GATE_MERGE_GATE), the venv python is
this interpreter (PRE_GATE_PYTHON).

Not asserted: DRAFT-pregate-pins-timeout-s (600) and the README Numbers row; the spec names no override to
shorten it, so a hung pinned test cannot be tested without waiting ten minutes.

Dumped premises (run on origin/main 2026-10-30): pre_gate.sh prints no "PREGATE pins" line today and exits 0
on every stub case below; the existing step 4 prints "PRE_GATE pins ..." (underscore), a different prefix.
"""
import os
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
SCRIPT = REPO / "scripts" / "specfactory" / "pre_gate.sh"
PIN_PATTERN = "PINNED_FULL|FLYER_SECTIONS|GOLDEN_|save_sha256"

UNIT_C = "#define HP 10\n"
MAKEFILE = (
    "all:\n\t@true\n"
    "pipe/ouroboros_pipe:\n\t@mkdir -p pipe && echo built > pipe/ouroboros_pipe\n"
)
PINNED_TEST = '''from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PINNED_FULL = 10


def test_pin_hp():
    assert f"#define HP {PINNED_FULL}" in (ROOT / "csrc" / "unit.c").read_text()


def test_pipe_is_built():
    assert (ROOT / "pipe" / "ouroboros_pipe").is_file()


def test_pin_constant():
    assert PINNED_FULL == 10
'''
UNPINNED_TEST = "def test_would_fail_if_run():\n    assert False\n"


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=repo, check=True,
                          capture_output=True, text=True).stdout


def _make_repo(tmp_path: Path, head_files: dict) -> Path:
    """Base commit (branch "base") with the csim stub tree, then one HEAD commit writing head_files."""
    repo = tmp_path / "wt"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "t@example.com")
    _git(repo, "config", "user.name", "t")
    _git(repo, "config", "commit.gpgsign", "false")
    base = {"csrc/unit.c": UNIT_C, "Makefile": MAKEFILE, "readme.txt": "base\n",
            "tests/csim/test_pinned.py": PINNED_TEST,
            "tests/csim/test_unpinned.py": UNPINNED_TEST}
    for name, text in base.items():
        (repo / name).parent.mkdir(parents=True, exist_ok=True)
        (repo / name).write_text(text)
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "base")
    _git(repo, "branch", "-q", "base")
    for name, text in head_files.items():
        (repo / name).write_text(text)
        _git(repo, "add", name)
    _git(repo, "commit", "-q", "-m", "head")
    return repo


def _stub_gate(tmp_path: Path) -> Path:
    stub = tmp_path / "stub_gate.sh"
    stub.write_text("#!/usr/bin/env bash\necho 'GATE make OK'\nexit 0\n")
    stub.chmod(0o755)
    return stub


def _run(repo: Path, tmp_path: Path) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    env["PRE_GATE_MERGE_GATE"] = str(_stub_gate(tmp_path))
    env["PRE_GATE_PYTHON"] = sys.executable
    return subprocess.run(["bash", str(SCRIPT), str(repo), "base", "P-1"],
                          cwd=REPO, env=env, capture_output=True, text=True)


def _pins_lines(res: subprocess.CompletedProcess):
    return [l for l in res.stdout.splitlines() if l.startswith("PREGATE pins")]


# ---- positive controls: green today, prove the fixture and the pattern work -------------------

def test_control_grep_derived_list_is_non_empty_on_the_real_tree():
    """H-017 / spec section 9: "the grep-derived list is non-empty on the real tree (guards against the
    pattern rotting)"."""
    out = subprocess.run(["git", "-C", str(REPO), "grep", "-l", "-E", PIN_PATTERN, "--", "tests/csim"],
                         capture_output=True, text=True)
    files = [l for l in out.stdout.splitlines() if l.strip()]
    assert out.returncode == 0 and files, out.stdout + out.stderr


def test_control_stub_pins_green_at_base_red_when_moved(tmp_path):
    """H-017 control: the stub's pinned test passes at the base value and fails once csrc/unit.c moves, so a
    red pre_gate below means the step is missing, not that the fixture is broken."""
    repo = _make_repo(tmp_path, {"csrc/unit.c": "#define HP 11\n"})
    (repo / "pipe").mkdir()
    (repo / "pipe" / "ouroboros_pipe").write_text("x\n")
    base_tree = tmp_path / "base_tree"
    _git(repo, "worktree", "add", "-q", str(base_tree), "base")
    (base_tree / "pipe").mkdir()
    (base_tree / "pipe" / "ouroboros_pipe").write_text("x\n")
    cmd = [sys.executable, "-m", "pytest", "tests/csim/test_pinned.py", "-q", "-p", "no:cacheprovider"]
    ok = subprocess.run(cmd, cwd=base_tree, capture_output=True, text=True)
    bad = subprocess.run(cmd, cwd=repo, capture_output=True, text=True)
    assert ok.returncode == 0, ok.stdout + ok.stderr
    assert bad.returncode != 0 and "test_pin_hp" in bad.stdout, bad.stdout + bad.stderr


def test_control_no_csrc_change_pre_gate_exits_zero(tmp_path):
    """H-017 control: with no csrc change the stub repo passes the whole pre-gate today and after."""
    repo = _make_repo(tmp_path, {"readme.txt": "head\n"})
    res = _run(repo, tmp_path)
    assert res.stdout.splitlines()[-1] == "PRE_GATE verdict OK", res.stdout + res.stderr
    assert res.returncode == 0


# ---- the step ---------------------------------------------------------------------------------

def test_no_csrc_change_prints_skipped_line_and_exits_zero(tmp_path):
    """H-017 / spec section 9: "no csrc change prints `PREGATE pins skipped: no csrc change`" and exits 0."""
    repo = _make_repo(tmp_path, {"readme.txt": "head\n"})
    res = _run(repo, tmp_path)
    assert _pins_lines(res) == ["PREGATE pins skipped: no csrc change"], res.stdout + res.stderr
    assert res.returncode == 0


def test_csrc_change_that_moves_a_pin_rejects_naming_the_id(tmp_path):
    """H-017 / spec section 9: "a csrc change that moves a pinned value rejects with the id named" - "a
    non-zero exit prints `PREGATE pins REJECT <failing ids>` and pre_gate exits non-zero"."""
    repo = _make_repo(tmp_path, {"csrc/unit.c": "#define HP 11\n"})
    res = _run(repo, tmp_path)
    lines = _pins_lines(res)
    assert len(lines) == 1 and lines[0].startswith("PREGATE pins REJECT "), res.stdout + res.stderr
    assert "test_pin_hp" in lines[0]
    assert "test_would_fail_if_run" not in res.stdout, "an unpinned csim file was run"
    assert res.stdout.splitlines()[-1] == "PRE_GATE verdict REJECT"
    assert res.returncode != 0


def test_csrc_change_with_pins_unchanged_prints_ok_n_tests(tmp_path):
    """H-017 / spec section 9 (positive control): "a csrc change with pins unchanged prints `PREGATE pins OK
    <n> tests`"; the stub's 3 tests include one that needs the built pipe/ouroboros_pipe ("build
    `pipe/ouroboros_pipe`") and exclude the unpinned file ("the csim files that carry pinned values")."""
    repo = _make_repo(tmp_path, {"csrc/unit.c": UNIT_C + "/* comment only */\n"})
    res = _run(repo, tmp_path)
    assert _pins_lines(res) == ["PREGATE pins OK 3 tests"], res.stdout + res.stderr
    assert res.stdout.splitlines()[-1] == "PRE_GATE verdict OK"
    assert res.returncode == 0


def test_pins_step_runs_after_the_pieces_own_tests(tmp_path):
    """H-017 / spec section 9: "a pre_gate step after the piece's own tests"."""
    repo = _make_repo(tmp_path, {"csrc/unit.c": UNIT_C + "/* comment only */\n"})
    out = _run(repo, tmp_path).stdout.splitlines()
    tests_i = next(i for i, l in enumerate(out) if re.match(r"^PRE_GATE tests ", l))
    pins_is = [i for i, l in enumerate(out) if l.startswith("PREGATE pins")]
    assert pins_is, out
    assert tests_i < pins_is[0] < len(out) - 1, out
