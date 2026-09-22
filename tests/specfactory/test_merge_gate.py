# spec: docs/northstar/plans/briefs/2026-09-22-two-day-push.md, item 1
"""Tests for scripts/specfactory/merge_gate.sh's own orchestration (exit
codes, step lines). The individual mechanisms it calls into --
footprint_check, symbol_ownership_check, regression_check -- have their own
unit tests in test_merge_gate_support.py against synthetic repos; this file
covers what only the shell script itself can be responsible for getting
right: the harness-timeout path (never counted as a regression, distinct
exit code, immediate stop) and that a REJECT-level step still prints its own
line. The full accept/reject path against the real ABI (libm_lint,
suite_regression, acceptance ids, checksum_trace) is exercised for real in
docs/northstar/proving_ground/evidence/push_2026-09-22/gate_replays.md --
those need the genuine csrc/tests/csim tree this repo's own scratch fixture
does not reproduce.
"""
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
GATE = REPO / "scripts" / "specfactory" / "merge_gate.sh"


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True)


def _init_fixture_repo(base_dir: Path, *, makefile: str) -> Path:
    repo = base_dir
    repo.mkdir(parents=True, exist_ok=True)
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "gate@test")
    _git(repo, "config", "user.name", "gate")
    (repo / "csrc").mkdir()
    (repo / "csrc" / "stub.c").write_text("int om_stub(void) { return 0; }\n")
    (repo / "Makefile").write_text(makefile)
    (repo / "tests").mkdir()
    (repo / "tests" / "csim").mkdir()
    (repo / "tests" / "qa").mkdir()
    (repo / "tests" / "qa" / "t1").mkdir()
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "base")
    return repo


def _write_pieces(path: Path, pieces: list[dict]) -> None:
    lines = []
    for p in pieces:
        lines.append("[[piece]]")
        lines.append(f'id = "{p["id"]}"')
        owns = p.get("owns", [])
        lines.append("owns = [" + ", ".join(f'"{o}"' for o in owns) + "]")
        acc = p.get("acceptance", [])
        lines.append("acceptance = [" + ", ".join(f'"{a}"' for a in acc) + "]")
        lines.append(f'depends_on = []')
        lines.append("")
    path.write_text("\n".join(lines))


SLEEPY_MAKEFILE = """\
.PHONY: all
libouroboros.so:
\tsleep 30 && touch $@
libouroboros_dbg.so:
\tsleep 30 && touch $@
"""

FAST_MAKEFILE = """\
libouroboros.so:
\ttouch $@
libouroboros_dbg.so:
\ttouch $@
"""


def test_positive_control_make_timeout_gives_exit_3(tmp_path):
    repo = _init_fixture_repo(tmp_path / "repo", makefile=SLEEPY_MAKEFILE)
    pieces = tmp_path / "pieces.toml"
    _write_pieces(pieces, [{"id": "B1", "owns": ["csrc/stub.c"], "acceptance": []}])

    env = {"MERGE_GATE_PIECES": str(pieces), "MERGE_GATE_MAKE_TIMEOUT": "1", "PATH": "/usr/bin:/bin"}
    proc = subprocess.run(
        ["bash", str(GATE), str(repo), "HEAD", "B1"],
        capture_output=True, text=True, env=env, timeout=30,
    )
    assert proc.returncode == 3, proc.stdout + proc.stderr
    assert "GATE make HARNESS" in proc.stdout


def test_every_step_before_the_first_reject_prints_a_line(tmp_path):
    """Not a reject scenario itself (fixture has no real ABI to check
    acceptance/regression against meaningfully) -- proves the mechanical
    contract: `make` and `libm_lint` and `alg_constants` and `footprint`
    each print their own `GATE <name> ...` line in order."""
    repo = _init_fixture_repo(tmp_path / "repo", makefile=FAST_MAKEFILE)
    pieces = tmp_path / "pieces.toml"
    _write_pieces(pieces, [{"id": "B1", "owns": ["csrc/stub.c"], "acceptance": []}])

    env = {"MERGE_GATE_PIECES": str(pieces), "PATH": "/usr/bin:/bin:/home/westopoli/Projects/agora/.venv/bin"}
    proc = subprocess.run(
        ["bash", str(GATE), str(repo), "HEAD", "B1"],
        capture_output=True, text=True, env=env, timeout=60,
    )
    for step in ("make", "libm_lint", "alg_constants", "footprint", "symbol_ownership"):
        assert f"GATE {step} " in proc.stdout, proc.stdout + proc.stderr


def test_unknown_candidate_dir_is_a_usage_error():
    proc = subprocess.run(
        ["bash", str(GATE), "/nonexistent/path", "HEAD", "B1"],
        capture_output=True, text=True, timeout=10,
    )
    assert proc.returncode == 2
