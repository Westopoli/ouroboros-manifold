"""Side-by-side parity scenes: the Python reference (simulation/, TacticalEngine) against the C library.

Plan: docs/northstar/plans/2026-10-02-movement-layers-and-search-plan.md, Phase A "Verification" 1;
requirements: docs/northstar/plans/2026-10-02-tactical-port-parity-requirements.md (P1 to P8).
Each scene runs the same units, orders and hand-built map through both engines and compares, per
tick and per unit, position (PARITY_TOLERANCE wu), target (exact) and facing (PARITY_FACING_TOLERANCE
rad), and whether the unit is alive. These tests are the spec for the movement port: they are RED
against today's C, each for the reason in its docstring, and go green when the port reproduces the
Python on that scene. Builders never edit them (CLAUDE.md "Tests are the spec").

The comparator and the fixture are proven by test_parity_harness.py (positive controls).
"""
import math

import pytest

from . import parity_c
from . import parity_python
from .parity_compare import compare
from .parity_scenes import SCENES, SIX
from .parity_tolerance import PARITY_FACING_TOLERANCE, PARITY_TOLERANCE

_PY = {}


def _python_trace(name):
    if name not in _PY:
        _PY[name] = parity_python.run_scene(SCENES[name])
    return _PY[name]


def _assert_parity(name):
    parity_c.build()
    rep = compare(_python_trace(name), parity_c.run_scene(SCENES[name]), PARITY_TOLERANCE, PARITY_FACING_TOLERANCE)
    lines = ["scene %s: C differs from the Python reference" % name,
             "  max position deviation %.4g wu at (tick, uid) %s (tolerance %g)" % (rep.max_pos, rep.max_pos_at, PARITY_TOLERANCE),
             "  max facing deviation %.4g rad at %s (tolerance %g)" % (rep.max_facing, rep.max_facing_at, PARITY_FACING_TOLERANCE),
             "  first position out of tolerance (tick, uid, wu): %s" % (rep.first_pos,),
             "  first target difference (tick, uid, python, c): %s" % (rep.first_target,),
             "  first facing out of tolerance (tick, uid, rad): %s" % (rep.first_facing,),
             "  first alive difference (tick, uid): %s" % (rep.first_alive,)]
    if rep.shape_error:
        lines.append("  SHAPE: " + rep.shape_error)
    if not rep.passes():
        pytest.fail("\n".join(lines), pytrace=False)


# R-097-10 (rewritten 2026-10-23, DEC-Q087-02-2026-10-22, built in engine rules Round 4): an idle unit takes the full displacement from a mover of its
# own side and steps aside; the Python reference lets idle friends block and the mover goes round. The rule says of itself "a deliberate difference from the
# Python reference". The two scenes below have idle friends in the mover's way, so they are NOT compared with the Python (the rest of this file is): each
# asserts what the C engine does now and, as the control that the difference is real, that the Python reference still holds its idle units where they stand.
DELIBERATE_DIFFERENCE = {
    "behind_own_row": ("R-097-10", "DEC-Q087-02-2026-10-22"),
    "three_in_file": ("R-097-10", "DEC-Q087-02-2026-10-22"),
}
ARRIVAL_WU = 22.5                        # R-099-04 arrival: 1.5 collision radii of 15 wu
DRAFT_R097_10_DISPLACED_WU = 5.0         # DRAFT-parity-r097-10-displaced-wu: an idle unit "steps aside" if it ends up farther than this from where it stood
DRAFT_R097_10_STOOD_WU = 0.5             # DRAFT-parity-r097-10-stood-wu: the Python reference's idle unit moves less than this
DRAFT_R097_10_NEAR_GOAL_WU = 45.0        # DRAFT-parity-r097-10-near-goal-wu: three units sharing one goal end within 1.5 collision diameters of it


def _c_trace(name):
    parity_c.build()
    return parity_c.run_scene(SCENES[name])


def _first_within(trace, uid, goal, radius=ARRIVAL_WU):
    return next((t for t, fr in enumerate(trace.frames) if math.hypot(fr[uid][1] - goal[0], fr[uid][2] - goal[1]) <= radius), None)


def _farthest_after(trace, uid, tick):
    """Farthest the unit is, on any later tick, from where it stood at `tick`."""
    x0, y0 = trace.frames[tick][uid][1:3]
    return max(math.hypot(fr[uid][1] - x0, fr[uid][2] - y0) for fr in trace.frames[tick:])


def test_S097_R097_03_behind_own_row():
    """S-097, R-097-03 and R-097-04 (P8): a Raider ordered to move past three idle friends abreast.
    Test-defect (engine rules Round 4, R-097-10, DELIBERATE_DIFFERENCE): the Python takes the first clear of its sweep angles, friends blocking, and walks round
    the row while the three stand; the C now walks through and the idle friend in its way steps aside (it did not before: the mover took the whole push and
    waited). Measured: both Raiders arrive within the arrival radius of (1400, 2000) at tick 79 (Python) and 77 (C); the Python friends do not move at all, the
    C friend at y 2035 ends 15.9 wu from its post. Asserted: the C Raider arrives, a C friend is displaced by more than DRAFT_R097_10_DISPLACED_WU, and no
    Python friend moves more than DRAFT_R097_10_STOOD_WU."""
    assert "behind_own_row" in DELIBERATE_DIFFERENCE
    goal, c, py = (1400.0, 2000.0), _c_trace("behind_own_row"), _python_trace("behind_own_row")
    assert _first_within(c, 3, goal) is not None, "the C Raider never came within %g wu of its point" % ARRIVAL_WU
    assert _first_within(py, 3, goal) is not None, "control: the Python Raider never arrived, so the scene is not the one the C is held to"
    moved = {u: _farthest_after(c, u, 0) for u in (0, 1, 2)}
    assert max(moved.values()) > DRAFT_R097_10_DISPLACED_WU, "no idle friend stepped aside for the C Raider: farthest from post %r" % moved
    stood = {u: _farthest_after(py, u, 0) for u in (0, 1, 2)}
    assert max(stood.values()) < DRAFT_R097_10_STOOD_WU, "control: a Python friend moved (farthest from post %r), the Python no longer blocks with idle friends" % stood


def test_S097_R097_03_R099_04_three_in_file():
    """S-097 R-097-03 (P8), S-099 R-099-04 (collision): three single-unit move orders to one point, two fast units behind a slow one in file.
    Test-defect (engine rules Round 4, R-097-10, DELIBERATE_DIFFERENCE): the Python followers sweep round the leader and the two that arrive first stay where
    they stopped; the C now lets the slow Vanguard walk through the Raiders that have arrived and each of them steps aside. Measured: the Python Raider 1 stands
    still after arriving at tick 116, the C Raider 1 is moved 7.4 wu by the Vanguard afterwards; the three C units end 19.3, 25.2 and 27.7 wu from (1600, 2000).
    Asserted: every C unit ends within DRAFT_R097_10_NEAR_GOAL_WU of the point; a C unit that had arrived is later displaced by more than
    DRAFT_R097_10_DISPLACED_WU; no Python unit that had arrived moves more than DRAFT_R097_10_STOOD_WU afterwards."""
    assert "three_in_file" in DELIBERATE_DIFFERENCE
    goal, c, py = (1600.0, 2000.0), _c_trace("three_in_file"), _python_trace("three_in_file")
    ends = {u: math.hypot(c.frames[-1][u][1] - goal[0], c.frames[-1][u][2] - goal[1]) for u in (0, 1, 2)}
    assert max(ends.values()) < DRAFT_R097_10_NEAR_GOAL_WU, "a C unit ends far from the point (wu from it): %r" % ends

    def after_arrival(trace):
        out = {}
        for u in (0, 1, 2):
            t = _first_within(trace, u, goal)
            if t is not None:
                out[u] = _farthest_after(trace, u, t)
        return out
    cm, pm = after_arrival(c), after_arrival(py)
    assert cm, "no C unit came within %g wu of the point" % ARRIVAL_WU
    assert max(cm.values()) > DRAFT_R097_10_DISPLACED_WU, "no C unit that had arrived stepped aside afterwards (farthest from its stop %r)" % cm
    assert pm and max(pm.values()) < DRAFT_R097_10_STOOD_WU, "control: a Python unit that had arrived moved afterwards (%r), or none arrived" % pm
