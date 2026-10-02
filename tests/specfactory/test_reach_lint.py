# spec: docs/northstar/plans/witty-cuddling-goblet.md::Wave 0 item 3
"""Tests for scripts/specfactory/reach_lint.py.

Builds a throwaway git repo per test with a minimal csrc/ (a header, a
sim.c defining om_world_step, and a pipe/om_pipe.c with a real main()
dispatch loop) and a minimal tests/ tree, so this suite never depends on
the real ouroboros-manifold repo's own reachability picture -- that is
exercised separately (not here) by running the lint against HEAD.
"""
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
REACH_LINT = REPO / "scripts" / "specfactory" / "reach_lint.py"

HEADER = """\
#ifndef FIXTURE_SIM_H
#define FIXTURE_SIM_H
#include <stdint.h>
typedef struct om_world om_world;
uint64_t om_world_step(om_world *w);
void om_wired_helper(om_world *w);
void om_unwired_helper(om_world *w);
#endif
"""

SIM_C = """\
#include "ouroboros_sim.h"
uint64_t om_world_step(om_world *w) {
    om_wired_helper(w);
    return 0;
}
void om_wired_helper(om_world *w) { (void)w; }
void om_unwired_helper(om_world *w) { (void)w; }
"""

PIPE_C = """\
#include "ouroboros_sim.h"
#include <string.h>
static void handle_step(void) { om_world_step((void*)0); }
int main(void) {
    const char *name = "step";
    for (;;) {
        if (!strcmp(name, "step")) {
            handle_step();
        }
        break;
    }
    return 0;
}
"""

TEST_PY = """\
def test_calls_both(lib):
    lib.om_wired_helper(None)
    lib.om_unwired_helper(None)
"""


def _add_decl(header_text: str, decl: str) -> str:
    """header_text with one more `decl` line inserted right before its
    trailing `#endif` -- a plain, unambiguous substring replace (unlike
    str.rstrip, which strips a CHARACTER SET, not a literal suffix, and so
    is the wrong tool here even where it happens to produce the right
    answer by coincidence)."""
    assert header_text.rstrip().endswith("#endif")
    return header_text.rstrip()[: -len("#endif")] + decl + "\n#endif\n"


def _init_project(tmp_path: Path) -> Path:
    project = tmp_path / "project"
    (project / "csrc" / "pipe").mkdir(parents=True)
    (project / "tests" / "csim").mkdir(parents=True)
    (project / "csrc" / "ouroboros_sim.h").write_text(HEADER)
    (project / "csrc" / "sim.c").write_text(SIM_C)
    (project / "csrc" / "pipe" / "om_pipe.c").write_text(PIPE_C)
    (project / "tests" / "csim" / "test_fixture.py").write_text(TEST_PY)
    subprocess.run(["git", "init", "-q"], cwd=project, check=True)
    subprocess.run(["git", "config", "user.email", "t@example.com"], cwd=project, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=project, check=True)
    subprocess.run(["git", "add", "."], cwd=project, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=project, check=True)
    return project


def _run(project: Path, *extra: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(REACH_LINT), "--project", str(project), "--ref", "HEAD", *extra],
        capture_output=True, text=True,
    )


def test_help():
    proc = subprocess.run([sys.executable, str(REACH_LINT), "--help"], capture_output=True, text=True)
    assert proc.returncode == 0
    assert "--ref" in proc.stdout
    assert "--allowlist" in proc.stdout


def test_positive_control_unwired_symbol_fails(tmp_path):
    """om_unwired_helper is declared, defined, and called by a test, but
    nothing in the static call graph from om_world_step or the pipe's
    dispatch loop ever calls it -- the planted violation this lint exists
    to catch."""
    project = _init_project(tmp_path)
    empty_allowlist = tmp_path / "empty_allowlist.toml"
    empty_allowlist.write_text("")
    proc = _run(project, "--allowlist", str(empty_allowlist))
    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert "UNREACHABLE om_unwired_helper" in proc.stdout
    assert "tests/csim/test_fixture.py" in proc.stdout
    assert "REACH LINT FAILED (1 unreachable of 2 tested public symbols)" in proc.stdout
    # om_wired_helper IS reachable (om_world_step -> om_wired_helper) and
    # must never be reported.
    assert "om_wired_helper" not in "".join(
        line for line in proc.stdout.splitlines() if line.startswith("UNREACHABLE")
    )


def test_reachable_symbol_never_flagged(tmp_path):
    project = _init_project(tmp_path)
    empty_allowlist = tmp_path / "empty_allowlist.toml"
    empty_allowlist.write_text("")
    proc = _run(project, "--allowlist", str(empty_allowlist))
    assert "UNREACHABLE om_wired_helper" not in proc.stdout


def test_allowlisted_symbol_passes(tmp_path):
    project = _init_project(tmp_path)
    allowlist = tmp_path / "allowlist.toml"
    allowlist.write_text(
        '[[allow]]\n'
        'symbol = "om_unwired_helper"\n'
        'reason = "test fixture: deliberately unwired, exercised only by the lint\'s own suite"\n'
    )
    proc = _run(project, "--allowlist", str(allowlist))
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "REACH LINT OK" in proc.stdout


def test_missing_allowlist_file_means_no_exemptions(tmp_path):
    project = _init_project(tmp_path)
    proc = _run(project, "--allowlist", str(tmp_path / "does_not_exist.toml"))
    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert "UNREACHABLE om_unwired_helper" in proc.stdout


def test_unwired_non_world_int_returning_symbol_is_listed(tmp_path):
    """Positive control, synthetic repo (TD-A94-reach-control). The gap-fix
    plan's Wave 0 item 4 bar was once checked against the live repo's
    om_mission_eval_commander_fate (defined, unit-tested, never called by
    om_mission_end); closing that gap with the real call consumed the control
    (6518a6a5, B7). The same shape lives here: om_eval_fate takes no
    om_world* parameter and returns int32_t, is tested and never called, so
    it must be listed. That also proves the read exemption is name-based, not
    signature-based: the broader signature rule (no om_world* param,
    non-void return) would have exempted exactly this symbol."""
    project = _init_project(tmp_path)
    (project / "csrc" / "ouroboros_sim.h").write_text(
        _add_decl(HEADER, "int32_t om_eval_fate(int32_t verdict);")
    )
    (project / "csrc" / "sim.c").write_text(
        SIM_C + "int32_t om_eval_fate(int32_t verdict) { return verdict; }\n"
    )
    (project / "tests" / "csim" / "test_fixture.py").write_text(
        TEST_PY + "\ndef test_calls_eval_fate(lib):\n    lib.om_eval_fate(0)\n"
    )
    subprocess.run(["git", "add", "."], cwd=project, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "add eval_fate"], cwd=project, check=True)
    empty_allowlist = tmp_path / "empty_allowlist.toml"
    empty_allowlist.write_text("")
    proc = _run(project, "--allowlist", str(empty_allowlist))
    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert "UNREACHABLE om_eval_fate" in proc.stdout, proc.stdout + proc.stderr


# ---------------------------------------------------------------- read exemption --

READ_HEADER = _add_decl(HEADER, "void om_get_widget(om_world *w);")

READ_SIM_C = SIM_C + """
void om_get_widget(om_world *w) { (void)w; }
"""

READ_TEST_PY = TEST_PY + """
def test_calls_get_widget(lib):
    lib.om_get_widget(None)
"""


def _init_project_with_read_accessor(tmp_path: Path) -> Path:
    """Same fixture as _init_project, plus one more unwired symbol whose
    name matches the read-accessor pattern (_get_)."""
    project = tmp_path / "project"
    (project / "csrc" / "pipe").mkdir(parents=True)
    (project / "tests" / "csim").mkdir(parents=True)
    (project / "csrc" / "ouroboros_sim.h").write_text(READ_HEADER)
    (project / "csrc" / "sim.c").write_text(READ_SIM_C)
    (project / "csrc" / "pipe" / "om_pipe.c").write_text(PIPE_C)
    (project / "tests" / "csim" / "test_fixture.py").write_text(READ_TEST_PY)
    subprocess.run(["git", "init", "-q"], cwd=project, check=True)
    subprocess.run(["git", "config", "user.email", "t@example.com"], cwd=project, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=project, check=True)
    subprocess.run(["git", "add", "."], cwd=project, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=project, check=True)
    return project


def test_read_accessor_excluded_by_default(tmp_path):
    project = _init_project_with_read_accessor(tmp_path)
    empty_allowlist = tmp_path / "empty_allowlist.toml"
    empty_allowlist.write_text("")
    proc = _run(project, "--allowlist", str(empty_allowlist))
    assert "UNREACHABLE om_get_widget" not in proc.stdout
    # om_unwired_helper (no get/count/is/has in its name) is still reported.
    assert "UNREACHABLE om_unwired_helper" in proc.stdout


def test_include_reads_shows_read_accessor(tmp_path):
    project = _init_project_with_read_accessor(tmp_path)
    empty_allowlist = tmp_path / "empty_allowlist.toml"
    empty_allowlist.write_text("")
    proc = _run(project, "--allowlist", str(empty_allowlist), "--include-reads")
    assert "UNREACHABLE om_get_widget" in proc.stdout
    assert proc.returncode == 1


# ---------------------------------------------------------------- regression mode --

def _git(project: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=project, check=True, capture_output=True, text=True)


def _rev(project: Path, ref: str = "HEAD") -> str:
    return _git(project, "rev-parse", ref).stdout.strip()


def _init_regression_project(tmp_path: Path) -> tuple[Path, str, str]:
    """(project, base_sha, candidate_sha). Base: om_wired_helper is called
    from om_world_step (reachable); om_preexisting_unwired is declared,
    defined, tested, and never called (a pre-existing finding at the base
    already). Candidate, on top of base: the call to om_wired_helper is
    REMOVED from om_world_step (a regression -- it goes from reachable to
    unreachable), and a brand new tested-but-uncalled symbol
    om_new_unwired is added. om_preexisting_unwired is untouched."""
    project = _init_project(tmp_path)
    header = _add_decl(HEADER, "void om_preexisting_unwired(om_world *w);")
    sim_c = SIM_C + """
void om_preexisting_unwired(om_world *w) { (void)w; }
"""
    test_py = TEST_PY + """
def test_calls_preexisting(lib):
    lib.om_preexisting_unwired(None)
"""
    (project / "csrc" / "ouroboros_sim.h").write_text(header)
    (project / "csrc" / "sim.c").write_text(sim_c)
    (project / "tests" / "csim" / "test_fixture.py").write_text(test_py)
    _git(project, "add", ".")
    _git(project, "commit", "-qm", "base: add pre-existing unwired symbol")
    base_sha = _rev(project)

    header2 = _add_decl(header, "void om_new_unwired(om_world *w);")
    sim_c2 = """\
#include "ouroboros_sim.h"
uint64_t om_world_step(om_world *w) {
    return 0;
}
void om_wired_helper(om_world *w) { (void)w; }
void om_unwired_helper(om_world *w) { (void)w; }
void om_preexisting_unwired(om_world *w) { (void)w; }
void om_new_unwired(om_world *w) { (void)w; }
"""
    test_py2 = test_py + """
def test_calls_new(lib):
    lib.om_new_unwired(None)
"""
    (project / "csrc" / "ouroboros_sim.h").write_text(header2)
    (project / "csrc" / "sim.c").write_text(sim_c2)
    (project / "tests" / "csim" / "test_fixture.py").write_text(test_py2)
    _git(project, "add", ".")
    _git(project, "commit", "-qm", "candidate: drop wired_helper call, add new_unwired")
    candidate_sha = _rev(project)

    return project, base_sha, candidate_sha


def _run_regression(project: Path, base_sha: str, candidate_sha: str, *extra: str) -> subprocess.CompletedProcess:
    empty_allowlist = project.parent / "empty_allowlist.toml"
    if not empty_allowlist.exists():
        empty_allowlist.write_text("")
    return subprocess.run(
        [sys.executable, str(REACH_LINT), "--project", str(project),
         "--ref", candidate_sha, "--base-ref", base_sha,
         "--allowlist", str(empty_allowlist), *extra],
        capture_output=True, text=True,
    )


def test_regression_ignores_preexisting_unreachable_symbol(tmp_path):
    project, base_sha, candidate_sha = _init_regression_project(tmp_path)
    proc = _run_regression(project, base_sha, candidate_sha)
    assert "om_preexisting_unwired" not in proc.stdout


def test_regression_catches_new_unwired_symbol(tmp_path):
    project, base_sha, candidate_sha = _init_regression_project(tmp_path)
    proc = _run_regression(project, base_sha, candidate_sha)
    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert "NEW UNREACHABLE om_new_unwired" in proc.stdout


def test_positive_control_regression_catches_regressed_symbol(tmp_path):
    """Planted violation for the regression mode specifically: a symbol
    reachable at the base (om_wired_helper, called from om_world_step)
    loses that call in the candidate -- goes from reachable to unreachable
    -- and must be reported even though it existed (reachable) before."""
    project, base_sha, candidate_sha = _init_regression_project(tmp_path)
    proc = _run_regression(project, base_sha, candidate_sha)
    assert "NEW UNREACHABLE om_wired_helper" in proc.stdout


def test_regression_clean_when_ref_equals_base(tmp_path):
    project, base_sha, candidate_sha = _init_regression_project(tmp_path)
    proc = _run_regression(project, candidate_sha, candidate_sha)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "REACH LINT OK" in proc.stdout


def test_bare_mode_still_prints_full_list_unaffected_by_base_ref_flag(tmp_path):
    """The standalone CLI's absolute mode (no --base-ref) is unchanged --
    it still reports every tested-but-unreachable symbol at --ref alone,
    pre-existing findings included."""
    project, base_sha, candidate_sha = _init_regression_project(tmp_path)
    empty_allowlist = tmp_path / "empty_allowlist.toml"
    empty_allowlist.write_text("")
    proc = subprocess.run(
        [sys.executable, str(REACH_LINT), "--project", str(project), "--ref", candidate_sha,
         "--allowlist", str(empty_allowlist)],
        capture_output=True, text=True,
    )
    assert "UNREACHABLE om_preexisting_unwired" in proc.stdout
    assert "UNREACHABLE om_new_unwired" in proc.stdout
    assert "UNREACHABLE om_wired_helper" in proc.stdout
