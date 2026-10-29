# spec: docs/northstar/plans/2026-10-29-layered-gate-spec.md section 9 (HARNESS-pregate-pins)
# Rule pins: none (harness piece, layered-gate spec section 9)
"""Tests for the pre_gate.sh `pins` step of HARNESS-pregate-pins (written before the step exists).

Spec text in force (section 9 paragraph, word for word):

**HARNESS-pregate-pins** (analysis issue 1; owns `scripts/specfactory/pre_gate.sh` and `tests/specfactory/test_pregate_pins.py`; depends on nothing queued, disjoint from the stack; builds in the next free slot). Tool: Workflow. E0's first gate ran 7056.9 s to reject on three flyer-blob trace pins and a W7 changed assertion that a hand-written golden list had missed (TD-LAB-E0-goldens-2); the hashes moved through `csrc/tactical_move.c` and `csrc/unit.c`, not through the three pin files the Architect named, so the trigger is any `csrc/` change. Fix: a pre_gate step after the piece's own tests: when `git diff --name-only <base>..HEAD` contains any path under `csrc/`, build `pipe/ouroboros_pipe` (W7 needs it; `tests/long/harness.py:18`) and run, with the manifold venv python, the csim files that carry pinned values, derived at run time by `git grep -l -E 'PINNED_FULL|FLYER_SECTIONS|GOLDEN_|save_sha256' -- tests/csim` (about 10 files, 87 tests, 39 s on origin/main in the analysis; no typed list anywhere); a non-zero exit prints `PREGATE pins REJECT <failing ids>` and pre_gate exits non-zero; no csrc change prints `PREGATE pins skipped: no csrc change`. Tests on a stub repo fixture: a csrc change that moves a pinned value rejects with the id named; no csrc change prints the skipped line and exits 0; a csrc change with pins unchanged prints `PREGATE pins OK <n> tests` (positive control); the grep-derived list is non-empty on the real tree (guards against the pattern rotting). Draft: `DRAFT-pregate-pins-timeout-s` 600.

Picked details (Architect, interface of this piece):
  D1  The step runs after step (3) tests and before step (4) rule pins of pre_gate.sh.
      Trigger: `git -C "$WT" diff --name-only "$BASE"...HEAD` holds a path beginning csrc/.
  D2  Trigger: (a) `make -s -j8 pipe/ouroboros_pipe` in the worktree; (b) the file list is
      derived at run time by the spec's grep, never typed; (c) the files run as
      `MALLOC_PERTURB_=255 PYTHONDONTWRITEBYTECODE=1 timeout 600 "$VENV_PYTHON" -m pytest <files> -q -p no:cacheprovider`;
      (d) exit 0 prints `PREGATE pins OK <n> tests` (n = pytest passed count); non-zero prints
      `PREGATE pins REJECT <failing ids>` (FAILED or ERROR node ids, space separated) and
      sets REJECTED=1.
  D3  The three line formats are the spec's: prefix PREGATE, one space, the word pins.
  D4  Failure modes the spec does not give: `PREGATE pins REJECT timeout 600s`,
      `PREGATE pins REJECT build pipe/ouroboros_pipe failed`,
      `PREGATE pins REJECT no pinned test files found`, `PREGATE pins REJECT pytest exit <rc>`.
  D5  The pytest runs under MALLOC_PERTURB_=255 (test_pins_run_under_malloc_perturb).

Stub repo: a tmp_path git repo with csrc/value.h, csrc/other.c, a Makefile whose
pipe/ouroboros_pipe recipe is `mkdir -p pipe && touch pipe/ouroboros_pipe`, a pinned csim test
(PINNED_FULL, reads csrc/value.h) and an unpinned csim test that always fails (it must never run).
pre_gate.sh is the real one, run against the stub with the PRE_GATE_PYTHON, PRE_GATE_MERGE_GATE
and MERGE_GATE_PIECES seams so steps (1), (2), (4) and (5) are inert.

Red/green on the base tree (no pins step yet): the four pre_gate tests are red for a missing
PREGATE line; the pattern half of the real-tree test is red; C1 to C3 are green.
"""
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent.parent
PRE_GATE = REPO / "scripts" / "specfactory" / "pre_gate.sh"
SPEC_DOC = REPO / "docs" / "northstar" / "plans" / "2026-10-29-layered-gate-spec.md"
PATTERN = "PINNED_FULL|FLYER_SECTIONS|GOLDEN_|save_sha256"
GREP = ["git", "grep", "-l", "-E", PATTERN, "--", "tests/csim"]
PIN_ID = "tests/csim/test_pin.py::test_pinned_value"

MAKEFILE = "pipe/ouroboros_pipe:\n\tmkdir -p pipe && touch pipe/ouroboros_pipe\n"
PIN_TEST = (
    'from pathlib import Path\n\n'
    'PINNED_FULL = "1"\n\n\n'
    'def test_pinned_value():\n'
    '    root = Path(__file__).resolve().parent.parent.parent\n'
    '    assert (root / "csrc" / "value.h").read_text().strip() == PINNED_FULL\n'
)
UNPINNED_FAIL = "def test_always_fails():\n    assert False, 'must never run: no pin token in this file'\n"
ENV_TEST = (
    'import os\n\n'
    'GOLDEN_ENV = "255"\n\n\n'
    'def test_malloc_perturb_is_set():\n'
    '    assert os.environ["MALLOC_PERTURB_"] == GOLDEN_ENV\n'
)


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True).stdout


def _write(repo: Path, rel: str, text: str) -> None:
    p = repo / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text)


def _commit(repo: Path, msg: str) -> None:
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", msg)


def _base_repo(tmp_path: Path, extra: dict | None = None) -> Path:
    repo = tmp_path / "cand"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "pins@test")
    _git(repo, "config", "user.name", "pins")
    _write(repo, "csrc/value.h", "1\n")
    _write(repo, "csrc/other.c", "int other(void) { return 0; }\n")
    _write(repo, "Makefile", MAKEFILE)
    _write(repo, "tests/csim/test_pin.py", PIN_TEST)
    _write(repo, "tests/csim/test_unpinned.py", UNPINNED_FAIL)
    _write(repo, "docs/note.md", "note\n")
    for rel, text in (extra or {}).items():
        _write(repo, rel, text)
    _commit(repo, "base")
    _git(repo, "remote", "add", "origin", str(repo))
    _git(repo, "update-ref", "refs/remotes/origin/main", "HEAD")
    return repo


def _pre_gate(tmp_path: Path, repo: Path) -> subprocess.CompletedProcess:
    stub_gate = tmp_path / "stub_merge_gate.sh"
    stub_gate.write_text("#!/usr/bin/env bash\nexit 0\n")
    stub_gate.chmod(0o755)
    env = {k: v for k, v in os.environ.items() if k != "MALLOC_PERTURB_"}
    env.update({"PRE_GATE_PYTHON": sys.executable,
                "PRE_GATE_MERGE_GATE": str(stub_gate),
                "MERGE_GATE_PIECES": str(tmp_path / "no_such_pieces.toml")})
    return subprocess.run(["bash", str(PRE_GATE), str(repo), "origin/main", "STUB"],
                          capture_output=True, text=True, env=env, timeout=300)


def _out(proc: subprocess.CompletedProcess) -> str:
    return proc.stdout + proc.stderr


def _last_line(proc: subprocess.CompletedProcess) -> str:
    return [ln for ln in proc.stdout.splitlines() if ln.strip()][-1]


def test_csrc_change_that_moves_a_pin_rejects(tmp_path):
    repo = _base_repo(tmp_path)
    _write(repo, "csrc/value.h", "2\n")
    _commit(repo, "move the pinned value")
    proc = _pre_gate(tmp_path, repo)
    out = _out(proc)
    reject = [ln for ln in out.splitlines() if ln.startswith("PREGATE pins REJECT")]
    assert reject, "no PREGATE pins REJECT line in the pre_gate output:\n" + out
    assert PIN_ID in reject[0], reject[0]
    assert "test_always_fails" not in out
    assert proc.returncode != 0, out
    assert _last_line(proc) == "PRE_GATE verdict REJECT", out


def test_no_csrc_change_skips(tmp_path):
    repo = _base_repo(tmp_path)
    _write(repo, "docs/note.md", "changed\n")
    _commit(repo, "docs only")
    proc = _pre_gate(tmp_path, repo)
    out = _out(proc)
    assert "PREGATE pins skipped: no csrc change" in out.splitlines(), out
    assert "PREGATE pins OK" not in out and "PREGATE pins REJECT" not in out, out
    assert "test_always_fails" not in out
    assert proc.returncode == 0, out
    assert _last_line(proc) == "PRE_GATE verdict OK", out


def test_csrc_change_with_pins_unchanged_is_ok(tmp_path):
    """Positive control: a csrc change the pin does not see passes the step."""
    repo = _base_repo(tmp_path)
    with open(repo / "csrc" / "other.c", "a") as f:
        f.write("/* a comment the pin does not see */\n")
    _commit(repo, "comment in csrc")
    proc = _pre_gate(tmp_path, repo)
    out = _out(proc)
    assert "PREGATE pins OK 1 tests" in out.splitlines(), out
    assert "test_always_fails" not in out
    assert proc.returncode == 0, out
    assert _last_line(proc) == "PRE_GATE verdict OK", out


def test_grep_derived_list_is_non_empty_on_the_real_tree():
    found = subprocess.run(GREP, cwd=REPO, capture_output=True, text=True)
    assert found.returncode == 0 and found.stdout.split(), "the pin grep finds no csim file on the real tree"
    assert PATTERN in PRE_GATE.read_text(), "the pin grep pattern is not in scripts/specfactory/pre_gate.sh"


def test_pins_run_under_malloc_perturb(tmp_path):
    repo = _base_repo(tmp_path, {"tests/csim/test_env.py": ENV_TEST})
    with open(repo / "csrc" / "other.c", "a") as f:
        f.write("/* a comment the pin does not see */\n")
    _commit(repo, "comment in csrc")
    proc = _pre_gate(tmp_path, repo)
    out = _out(proc)
    assert "PREGATE pins OK 2 tests" in out.splitlines(), out
    assert proc.returncode == 0, out


# ---- controls (green on the base tree) ---------------------------------------

def test_control_c1_stub_pin_really_moves(tmp_path):
    repo = _base_repo(tmp_path)
    cmd = [sys.executable, "-m", "pytest", "tests/csim/test_pin.py", "-q", "-p", "no:cacheprovider"]
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
    before = subprocess.run(cmd, cwd=repo, capture_output=True, text=True, env=env)
    assert before.returncode == 0, before.stdout
    _write(repo, "csrc/value.h", "2\n")
    after = subprocess.run(cmd, cwd=repo, capture_output=True, text=True, env=env)
    assert after.returncode != 0, after.stdout
    assert "test_pinned_value" in after.stdout


def test_control_c2_stub_grep_lists_only_the_pinned_file(tmp_path):
    repo = _base_repo(tmp_path)
    found = subprocess.run(GREP, cwd=repo, capture_output=True, text=True).stdout.split()
    assert found == ["tests/csim/test_pin.py"], found


def test_control_c3_pattern_equals_the_spec_pattern():
    quoted = "git grep -l -E '" + PATTERN + "' -- tests/csim"
    assert quoted in (__doc__ or ""), "the file header does not quote the spec grep"
    spec_text = SPEC_DOC.read_text()
    paragraph = [p for p in spec_text.split("\n") if p.startswith("**HARNESS-pregate-pins**")]
    assert len(paragraph) == 1, "spec paragraph HARNESS-pregate-pins not found"
    assert quoted in paragraph[0], "the test pattern differs from the spec pattern"
