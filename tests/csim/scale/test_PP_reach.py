# spec: docs/northstar/plans/2026-10-02-movement-layers-and-search-plan.md::Phase A::verification 4 ("reach_lint shows each behaviour reached from om_tactical_step")
# spec: CLAUDE.md::Architecture rules::"Wired, not just tested"
"""Reach checks for the movement, layers and search plan: each new behaviour must be reached from
om_tactical_step (or the tick, the jump, a pipe handler), not only from a test.

HOW reach_lint.py IS INVOKED AND WHAT IT NEEDS
  python3 scripts/specfactory/reach_lint.py --ref <ref> --base-ref <base>      (regression gate)
  python3 scripts/specfactory/reach_lint.py --ref <ref>                        (absolute list)
  * It reads the COMMITTED tree: `git archive <ref> -- csrc tests` into a scratch directory, so
    new code and the tests that call it must be committed first; the working tree is never read.
  * gcc with -fcallgraph-info (any recent gcc) and git; about 2 seconds.
  * It checks PUBLIC symbols only: every `om_*` prototype in csrc/ouroboros_sim.h that some file
    under tests/ calls as `lib.om_x(` and that no static call graph rooted at om_world_step,
    om_tactical_step, om_time_jump_run or an om_pipe.c dispatch handler reaches (and that is not in
    scripts/specfactory/reach_allowlist.toml). Bare, today: 283 of 711 tested symbols are
    unreachable (the absolute run exits 1 for that reason, not for this plan), so the gate used here is
    the regression form: no symbol may be newly unreachable against BASE_REF.
  * A new behaviour that is a `static` helper inside tactical_move.c or unit.c is invisible to it
    (no header symbol). For those, `reached_from_tactical_step` below reads the same call graph
    (reach_lint.build_callgraph, working tree) and asks about named functions. Each wave appends
    the names of its new functions to NEW_BEHAVIOUR; the test then fails while any of them is not
    reachable from om_tactical_step. Static node titles are `csrc/<file>.c:<name>`.

Controls: a function the tick runs must be reported reached; a header function nothing in the tick
calls (om_world_run) must be reported not reached.
"""
import subprocess
import sys
from pathlib import Path

from ._scale_helpers import REPO_ROOT

REPO = Path(REPO_ROOT)
sys.path.insert(0, str(REPO / "scripts" / "specfactory"))
import reach_lint  # noqa: E402

# The commit the plan was written on (rulings-2 Addendum 45). Anything newly unreachable since is the
# plan's doing. Never move it forward to make a failure go away.
BASE_REF = "9e2c27128519c6fe0249032d59dd5155ab218cf1"

# Names of the functions each wave adds (static or public), e.g. "om_move_sweep_clear". Empty until a
# wave adds one; the builder of that wave appends here in the same change.
NEW_BEHAVIOUR = []

_GRAPH = {}


def _graph():
    if "g" not in _GRAPH:
        _GRAPH["g"] = reach_lint.build_callgraph(REPO / "csrc")
    return _GRAPH["g"]


def reached_from_tactical_step(names):
    """{name: True/False}: is a node titled `name` or `csrc/<file>.c:name` reachable from om_tactical_step."""
    graph = _graph()
    seen = reach_lint.reachable_from(graph, {"om_tactical_step"})
    return {n: any(t == n or t.endswith(":" + n) for t in seen) for n in names}


def test_PP_reach_lint_regression_gate_is_clean():
    """Verification 4: reach_lint reports no tested public symbol newly unreachable since BASE_REF.
    Needs the work committed (it reads `git archive HEAD`)."""
    proc = subprocess.run([sys.executable, str(REPO / "scripts" / "specfactory" / "reach_lint.py"),
                           "--ref", "HEAD", "--base-ref", BASE_REF],
                          cwd=REPO, capture_output=True, text=True)
    assert proc.returncode == 0, proc.stdout[-1500:] + proc.stderr[-500:]
    assert "REACH LINT OK" in proc.stdout


def test_PP_reach_new_behaviour_is_reached_from_tactical_step():
    """Every function named in NEW_BEHAVIOUR is reachable from om_tactical_step."""
    missing = [n for n, ok in reached_from_tactical_step(NEW_BEHAVIOUR).items() if not ok]
    assert not missing, f"not reached from om_tactical_step: {missing}"


def test_PP_reach_control_detector_sees_both_answers():
    """Positive control: the detector says yes for a function the tick runs and no for one it never
    calls, so an empty NEW_BEHAVIOUR or a green gate cannot be a detector that always says yes."""
    got = reached_from_tactical_step(["om_move_tick_once", "om_world_run"])
    assert got == {"om_move_tick_once": True, "om_world_run": False}
