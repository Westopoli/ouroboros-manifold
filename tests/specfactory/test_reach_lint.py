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


def test_real_repo_head_lists_om_mission_eval_commander_fate():
    """The gap-fix plan's own acceptance bar for this lint (Wave 0 item 4):
    run against origin/main (HEAD here), it must list
    om_mission_eval_commander_fate -- defined, unit-tested, never called by
    om_mission_end. If it does not show up, the lint itself is wrong."""
    proc = _run(REPO)
    assert "UNREACHABLE om_mission_eval_commander_fate" in proc.stdout, proc.stdout + proc.stderr
