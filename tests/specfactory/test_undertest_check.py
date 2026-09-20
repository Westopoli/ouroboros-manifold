# spec: PX-06 prototype experiment (Factory gates the worker cannot move,
# docs/northstar/PLAN.md): shadow-fixture perturbation (a) and diff-scoped
# mutation testing (b).
"""Tests for scripts/specfactory/undertest_check.py.

Uses tiny synthetic git projects (own throwaway git repos under tmp_path),
same style as test_tick_closure.py's synthetic sim.c -- these prove the
mechanism, not the real ouroboros-manifold repo. The real-repo replay of the
204a1/om_step_telegraphs incident (0d65f9e / a493cfd) and the
om_faction_step_budget genuine-candidate check (d641ea2) are run separately,
outside pytest, per the PX-06 brief.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "scripts" / "specfactory"))

import undertest_check  # noqa: E402

_GIT_ENV = {
    **os.environ,
    "GIT_AUTHOR_NAME": "px06", "GIT_AUTHOR_EMAIL": "px06@local",
    "GIT_COMMITTER_NAME": "px06", "GIT_COMMITTER_EMAIL": "px06@local",
}


def _run_git(project: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", "-c", "commit.gpgsign=false", *args], cwd=str(project),
        capture_output=True, text=True, env=_GIT_ENV,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"git {args} failed: {proc.stderr}")
    return proc.stdout.strip()


def _write(project: Path, files: dict[str, str]) -> None:
    for relpath, content in files.items():
        p = project / relpath
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)


def _commit(project: Path, files: dict[str, str], message: str) -> str:
    _write(project, files)
    _run_git(project, "add", "-A")
    _run_git(project, "commit", "-q", "-m", message)
    return _run_git(project, "rev-parse", "HEAD")


def _init_project(tmp_path: Path) -> Path:
    project = tmp_path / "project"
    project.mkdir()
    _run_git(project, "init", "-q")
    return project


CLASSIFY_MAKEFILE = "CC ?= cc\nlibouroboros.so: tiny.c\n\t$(CC) -shared -fPIC -o $@ tiny.c\n"

CLASSIFY_TEST_PY = '''import ctypes
from pathlib import Path

lib = ctypes.CDLL(str(Path(__file__).resolve().parent / "libouroboros.so"))
lib.classify.restype = ctypes.c_int
lib.classify.argtypes = [ctypes.c_int]


def test_classify_true_case():
    assert lib.classify(10) == 1


def test_classify_boundary():
    assert lib.classify(5) == 0
'''


def _classify_c(threshold: int) -> str:
    return (
        "int classify(int x) {\n"
        f"    if (x > {threshold}) {{\n"
        "        return 1;\n"
        "    }\n"
        "    return 0;\n"
        "}\n"
    )


def _classify_project(tmp_path: Path) -> tuple[Path, str, str]:
    """A two-commit synthetic project: a stub `classify` (wrong threshold),
    then a candidate that changes exactly one line (the threshold literal
    and its comparison). Returns (project, base_sha, candidate_sha)."""
    project = _init_project(tmp_path)
    base_sha = _commit(
        project,
        {"Makefile": CLASSIFY_MAKEFILE, "tiny.c": _classify_c(100), "test_tiny.py": CLASSIFY_TEST_PY},
        "stub: classify always false for realistic inputs",
    )
    candidate_sha = _commit(
        project, {"tiny.c": _classify_c(5)}, "candidate: classify(x) = x > 5",
    )
    return project, base_sha, candidate_sha


def test_line_mutants_catalog_on_a_realistic_if_line():
    mutants = dict(undertest_check._line_mutants("    if (x > 5) {\n"))
    assert "    if (x >= 5) {\n" in mutants.values()
    assert "    if (x > 0) {\n" in mutants.values()
    assert "    if (x > 1) {\n" in mutants.values()
    assert "    if (!(x > 5)) {\n" in mutants.values()


def test_line_mutants_flips_arithmetic_and_skips_noop_literals():
    mutants = dict(undertest_check._line_mutants("    d_military = -0.8 * net;\n"))
    assert "    d_military = -0.8 / net;\n" in mutants.values()
    # 0.8 -> 0 and 0.8 -> 1 both present, but no self-mutation for a literal
    # that already equals its own target.
    assert "    d_military = -0 * net;\n" in mutants.values()
    assert "    d_military = -1 * net;\n" in mutants.values()
    zero_to_zero = [v for k, v in undertest_check._line_mutants("x = 0;\n") if "0->0" in k]
    assert zero_to_zero == []


# ---------------------------------------------------------------------------
# RED: written before undertest_check.mutate_diff existed. Captured below via
# a NotImplementedError stand-in and quoted in the PX-06 report; kept here
# unmodified as the acceptance shape.
# ---------------------------------------------------------------------------

def test_mutate_diff_weak_acceptance_leaves_survivors(tmp_path):
    """R1 shape (claim b, positive control): a test that only ever exercises
    the true branch (classify(10) == 1) does not constrain the boundary --
    the comparison flip, both literal-5 mutants, still make classify(10)
    true, so they survive. Only if-negate is caught."""
    project, base_sha, candidate_sha = _classify_project(tmp_path)
    result = undertest_check.mutate_diff(
        base_sha, candidate_sha, "tiny.c", "classify",
        ["test_tiny.py::test_classify_true_case"], project=project,
    )
    assert result["verdict"] == "UNDER_TESTED"
    assert result["total_mutants"] == 4
    assert result["survived"] >= 1
    assert result["killed"] + result["survived"] == result["total_mutants"]
    survivor_mutations = {s["mutation"].split(" @")[0].split(" ")[0] for s in result["survivors"]}
    assert "comparison" in survivor_mutations or "literal" in survivor_mutations


def test_mutate_diff_boundary_test_kills_every_mutant(tmp_path):
    """Negative control: adding the boundary assertion (classify(5) == 0)
    kills every mutant of the changed line -- claim (b)'s OK case."""
    project, base_sha, candidate_sha = _classify_project(tmp_path)
    result = undertest_check.mutate_diff(
        base_sha, candidate_sha, "tiny.c", "classify",
        ["test_tiny.py::test_classify_true_case", "test_tiny.py::test_classify_boundary"],
        project=project,
    )
    assert result["verdict"] == "OK"
    assert result["survived"] == 0
    assert result["killed"] == result["total_mutants"] == 4


def test_mutate_diff_reports_baseline_skipped_ids(tmp_path):
    """A node id that does not already pass unmutated is excluded from kill
    detection and reported separately -- it cannot prove anything about a
    mutant it already failed before any mutation."""
    project, base_sha, candidate_sha = _classify_project(tmp_path)
    result = undertest_check.mutate_diff(
        base_sha, candidate_sha, "tiny.c", "classify",
        ["test_tiny.py::test_classify_true_case", "test_tiny.py::does_not_exist"],
        project=project,
    )
    assert result["baseline_valid_ids"] == ["test_tiny.py::test_classify_true_case"]
    assert "test_tiny.py::does_not_exist" in result["baseline_skipped_ids"]


HALF_MAKEFILE = "CC ?= cc\nlibouroboros.so: half.c\n\t$(CC) -shared -fPIC -o $@ half.c\n"

HALF_TEST_PY = '''import ctypes
from pathlib import Path

lib = ctypes.CDLL(str(Path(__file__).resolve().parent / "libouroboros.so"))
lib.half.restype = ctypes.c_double
lib.half.argtypes = [ctypes.c_double]


def test_half_of_ten():
    """Given x = 10.0, half(x) = x / 2.0, so half(10.0) is 5.0."""
    assert lib.half(10.0) == 5.0
'''

HALF_GENUINE_C = "double half(double x) {\n    return x / 2.0;\n}\n"
HALF_GUARDED_HARDCODE_C = (
    "double half(double x) {\n"
    "    if (x == 10.0) return 5.0;\n"
    "    return 0.0;\n"
    "}\n"
)
HALF_CONSTANT_HARDCODE_C = "double half(double x) {\n    (void)x;\n    return 5.0;\n}\n"


def _half_project(tmp_path: Path, name: str, half_c: str) -> Path:
    project = tmp_path / name
    project.mkdir()
    _run_git(project, "init", "-q")
    _commit(project, {"Makefile": HALF_MAKEFILE, "half.c": half_c, "test_half.py": HALF_TEST_PY}, "half")
    return project


def test_shadow_fixture_genuine_candidate_passes_with_recomputed_expected(tmp_path):
    """Claim (a), genuine side: the docstring states the formula, so the
    perturbed literal's expected value is recomputed (10 -> 12, 5.0 -> 6.0)
    and a real formula keeps passing."""
    project = _half_project(tmp_path, "genuine", HALF_GENUINE_C)
    result = undertest_check.shadow_fixture(
        "test_half.py", "test_half.py::test_half_of_ten",
        {"find": "lib.half(10.0)", "replace": "lib.half(12.0)", "recompute": [("== 5.0", "== 6.0")]},
        project=project,
    )
    assert result["baseline_pass"] is True
    assert result["perturbed_pass"] is True
    assert result["verdict"] == "OK"


def test_shadow_fixture_guarded_hardcode_fails_when_perturbed(tmp_path):
    """Claim (a), hard-coded side: `if (x == 10.0) return 5.0;` passes the
    unperturbed fixture but fails once the literal moves and the expected
    value is recomputed -- exactly the R7g incident's shape in miniature."""
    project = _half_project(tmp_path, "guarded_hardcode", HALF_GUARDED_HARDCODE_C)
    result = undertest_check.shadow_fixture(
        "test_half.py", "test_half.py::test_half_of_ten",
        {"find": "lib.half(10.0)", "replace": "lib.half(12.0)", "recompute": [("== 5.0", "== 6.0")]},
        project=project,
    )
    assert result["baseline_pass"] is True
    assert result["perturbed_pass"] is False
    assert result["verdict"] == "FAIL"


def test_shadow_fixture_genuine_outcome_changes_without_recompute(tmp_path):
    """No stated formula supplied by the caller: the check falls back to
    requiring the PASS/FAIL outcome to change. A genuine implementation's
    answer does change (5.0 -> 6.0, but the expected literal is untouched),
    so it goes from passing to failing -- that flip is what distinguishes
    'computes' from 'hard-codes'."""
    project = _half_project(tmp_path, "genuine_no_recompute", HALF_GENUINE_C)
    result = undertest_check.shadow_fixture(
        "test_half.py", "test_half.py::test_half_of_ten",
        {"find": "lib.half(10.0)", "replace": "lib.half(12.0)"},
        project=project,
    )
    assert result["baseline_pass"] is True
    assert result["perturbed_pass"] is False
    assert result["verdict"] == "OK"


def test_shadow_fixture_constant_hardcode_is_flagged_without_recompute(tmp_path):
    """A candidate that ignores its input entirely keeps returning the same
    constant no matter the perturbation -- outcome does not change, which
    this check reports as HARDCODE_SUSPECTED rather than silently OK."""
    project = _half_project(tmp_path, "constant_hardcode", HALF_CONSTANT_HARDCODE_C)
    result = undertest_check.shadow_fixture(
        "test_half.py", "test_half.py::test_half_of_ten",
        {"find": "lib.half(10.0)", "replace": "lib.half(12.0)"},
        project=project,
    )
    assert result["baseline_pass"] is True
    assert result["perturbed_pass"] is True
    assert result["verdict"] == "HARDCODE_SUSPECTED"


HALF_TEST_PY_ALREADY_WRONG = HALF_TEST_PY.replace("== 5.0", "== 999.0")


def test_shadow_fixture_is_inconclusive_when_baseline_already_fails(tmp_path):
    project = tmp_path / "already_broken"
    project.mkdir()
    _run_git(project, "init", "-q")
    _commit(
        project,
        {"Makefile": HALF_MAKEFILE, "half.c": HALF_GENUINE_C, "test_half.py": HALF_TEST_PY_ALREADY_WRONG},
        "half but the test was always wrong",
    )
    result = undertest_check.shadow_fixture(
        "test_half.py", "test_half.py::test_half_of_ten",
        {"find": "lib.half(10.0)", "replace": "lib.half(11.0)"},
        project=project,
    )
    assert result["baseline_pass"] is False
    assert result["verdict"] == "INCONCLUSIVE"


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q"]))
