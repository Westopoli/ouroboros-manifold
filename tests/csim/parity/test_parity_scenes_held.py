"""HELD (kept only on push/pp-a23): the parity scenes still red after the A2+A3 integration. Moved verbatim from test_parity_scenes.py; move back when their code lands."""
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


def test_S087_R087_04_R100_01_target_walks_out_of_range():
    """S-087 R-087-04 (P1), S-100 R-100-01 (P7): an attack-moving Raider with an enemy 150 wu away
    keeps marching until its own cohort turn gives it a target, then holds while the target is
    within range and walks after it when it leaves. (P2, R-084-01, the first shot, is not visible in
    position, target or facing; it needs an hp channel and its own tolerance, not built here.)
    RED today: first divergence at tick 1. The C holds the instant any hostile is in range, with no
    target at all (om_tac_hold(w, u, 0), unit.c); the Python marches until its cohort turn at tick 4.
    The C's pursuit is a straight-line position write, and its targeting cohort is id % 4 on
    1-based ids where the Python's is uid % 4 (measure.py --diagnose shifts the ids to remove that
    one offset and the scene still diverges at tick 1 on the hold)."""
    _assert_parity("target_walks_out_of_range")


def test_S096_R096_02_attack_move_group_of_8():
    """S-096 R-096-02 (P5), S-087 R-087-04 (P1), S-100 R-100-01 (P7): eight Raiders attack-moved
    together take formation slots and meet three idle Vanguards.
    RED today: the C sends every unit to the one shared point (no slots: om_command_attack_move is a
    loop of om_command_move), sweeps at 15 degrees, and its stationary firing units never turn; first
    divergence at tick 1, first target difference at tick 75."""
    _assert_parity("attack_move_group_of_8")


def test_S097_R097_01_wall_with_a_gap():
    """S-097 R-097-01 and R-097-02 (P3): a Vanguard ordered across the Python's test wall (rows 4 and
    5, cols 3 to 18 of a 100 wu grid) must route round it through the open corner.
    RED today: the C steers straight at the goal (its route cache is a stub; the BFS length is never
    followed): first divergence at tick 1, and the C Vanguard ends stalled against the wall at
    (1000.1, 403.0) while the Python arrives at (975.7, 915.2) by tick 479."""
    _assert_parity("wall_with_a_gap")


def test_S087_R087_06_return_fire_on_the_march():
    """S-087 R-087-06 (P6), S-100 R-100-01 (P7): an attack-moving Picket (range 100, sensor 150) with
    no target is hit by an idle Sniper (range 250) 200 wu off its line; it must turn on the attacker
    and attack-move to it, dropping its old destination, and the Sniper must turn to fire.
    RED today: the C answers return fire for idle units only, so the marching Picket ignores the
    hit and walks on past along y = 2000 (first target and facing difference at tick 165, position
    by 3.7 wu at tick 166, 471 wu apart by tick 300), and the stationary Sniper never turns. The
    first position flag, tick 5 at 1.1e-6 wu, is not the port gap: it is the C's om_cos/om_atan2
    trig error on the straight march (see parity_tolerance.py)."""
    _assert_parity("return_fire_on_the_march")
