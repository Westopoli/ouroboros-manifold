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


def test_S097_R097_03_behind_own_row():
    """S-097, R-097-03 and R-097-04 (P8): a Raider ordered to move past three idle friends abreast must
    sweep +30, -30, +60, -60, +90, -90 degrees and take the first clear one, friends blocking.
    RED today: the C sweeps 13 angles at 15 degrees, snaps facing to the deflection, and waits when
    none is clear; first behavioural divergence at tick 8 (the first blocked probe, 1.96 wu and
    0.27 rad apart), the C Raider ends stalled at (974.6, 2019.1) while the Python walks round the
    row and arrives. (A position flag at tick 3 below 1e-5 wu is the C's trig error, not the gap.)"""
    _assert_parity("behind_own_row")


def test_S097_R097_03_R099_04_three_in_file():
    """S-097 R-097-03 (P8), S-099 R-099-04 (collision): three single-unit move orders to one point,
    two fast units behind a slow one in file; the followers must sweep round the leader.
    RED today: first divergence at tick 1: the Python takes +60 degrees (its +30 and -30 probes are
    still blocked by the unit ahead), the C takes +45 (its 15-degree sweep), and the C facing snaps
    to the deflection where the Python turns toward its move target."""
    _assert_parity("three_in_file")
