"""Python reference, wave A5 (Addendum 57, A156): every unit starts collision pair checks, up to 10 passes.

E-13 R-097-10 (the collision rule, renumbered from the second R-097-06 by A158) and ALG-68. The old rule here
was "only a moving unit starts a pair check, and only against higher ids" with COLLISION_RESOLUTION_ITERATIONS = 3
passes. The new rule: every unit, moving or stopped, starts checks; the push pass repeats up to 10 times a tick
(`COLLISION_PASSES` in the C) and stops early when no pair is closer than 30 wu; the stationary-pair split and
the push-out stay. The C sim carries the same change (tests/csim/test_PP_move_collision_a5.py), so parity holds.
This file is tooling-side; the Python is not part of the game loop.

Run from this directory: `python -m pytest -q test_collision_all_start_checks.py`.
Early stop: the Python exposes no pass counter, so it is tested by outcome only (an un-overlapped world is
left exactly as it was).
"""
import math

from tactical_engine import TacticalEngine
from command import Command
from test_maps import open_field
from unit import FIELD_X, FIELD_Y

DIAMETER = 30.0  # 2 x UNIT_COLLISION_RADIUS 15
TOL = 0.05       # numeric slack, not a rule threshold


def _engine():
    return TacticalEngine(open_field(), seed=1)


def _pos(engine, uid):
    return (float(engine.store.data[uid, FIELD_X]), float(engine.store.data[uid, FIELD_Y]))


def _min_pair(engine, uids):
    ps = [_pos(engine, u) for u in uids]
    return min(math.hypot(ps[i][0] - ps[j][0], ps[i][1] - ps[j][1])
               for i in range(len(ps)) for j in range(i + 1, len(ps)))


def _move(engine, uids, x, y):
    engine.command_queue.add(Command(tick=0, type="move", unit_ids=list(uids),
                                     params={"target_x": x, "target_y": y}))


def test_R_097_10_a_unit_walking_into_a_stopped_one_is_pushed_out():
    """R-097-10: stopped S (id 0) at (1000,1000); M (id 1, the higher id) walks toward it from (1020,1000).
    After the tick the pair is >= 30 wu apart and S has not moved. The old rule checks the pair only when its
    lower-id unit (S) moved, so M ends inside S."""
    e = _engine()
    s = e.store.spawn("Raider", 0, 1000.0, 1000.0)
    m = e.store.spawn("Raider", 0, 1020.0, 1000.0)
    assert s < m
    _move(e, [m], 900.0, 1000.0)
    e.step()
    assert _pos(e, s) == (1000.0, 1000.0), "the stopped unit was pushed"
    assert _min_pair(e, [s, m]) >= DIAMETER - TOL


def test_R_097_10_positive_control_lower_id_mover_is_pushed():
    """Positive control (green on the old rule too): the mirror scene with the mover at the LOWER id is pushed
    out by the old rule as well. M (id 0) at (1020,1000) walks toward stopped S (id 1) at (1000,1000)."""
    e = _engine()
    m = e.store.spawn("Raider", 0, 1020.0, 1000.0)
    s = e.store.spawn("Raider", 0, 1000.0, 1000.0)
    _move(e, [m], 900.0, 1000.0)
    e.step()
    assert _pos(e, s) == (1000.0, 1000.0)
    assert _min_pair(e, [m, s]) >= DIAMETER - TOL


def test_R_097_10_stopped_overlapping_units_are_checked_and_split():
    """R-097-10 (stopped units are checked; the split rule stays): three stopped units at x 1000, 1015, 1040 on
    one row. Nobody moves, yet every unit starts checks: after one tick no pair is closer than 30 wu, and the
    equal splits keep the sum of the x positions (3055) and y at 1000. Old rule: nobody moved, nothing checked."""
    e = _engine()
    ids = [e.store.spawn("Raider", 0, x, 1000.0) for x in (1000.0, 1015.0, 1040.0)]
    assert _min_pair(e, ids) < DIAMETER
    e.step()
    assert _min_pair(e, ids) >= DIAMETER - TOL
    ps = [_pos(e, u) for u in ids]
    assert abs(sum(p[0] for p in ps) - 3055.0) < TOL
    assert all(abs(p[1] - 1000.0) < TOL for p in ps)


def test_R_097_10_a_row_needing_more_than_three_passes_converges_in_the_cap():
    """R-097-10 (up to 10 passes a tick): three stopped units 12 wu apart. On a scratch build of the new rule
    3 passes leave the closest pair near 29.2 wu and 10 reach 30.0; after one tick every pair is >= 30 (TOL).
    Old rule: nobody moved, nothing checked, the row stays at 12 wu."""
    e = _engine()
    ids = [e.store.spawn("Raider", 0, 1000.0 + 12.0 * i, 1000.0) for i in range(3)]
    e.step()
    assert _min_pair(e, ids) >= DIAMETER - TOL


def test_R_097_10_a_world_with_no_overlap_is_left_alone():
    """R-097-10 (stop early when no pair is closer than 30 wu): stopped units 31 wu apart do not move in any
    tick. Outcome only (no pass counter)."""
    e = _engine()
    ids = [e.store.spawn("Raider", 0, 1000.0 + 31.0 * i, 1000.0) for i in range(4)]
    for _ in range(3):
        e.step()
    for i, u in enumerate(ids):
        assert _pos(e, u) == (1000.0 + 31.0 * i, 1000.0)


def test_R_097_10_positive_control_overlap_is_pushed():
    """Positive control for the test above: stopped units 29 wu apart do move (every unit starts checks)."""
    e = _engine()
    ids = [e.store.spawn("Raider", 0, 1000.0 + 29.0 * i, 1000.0) for i in range(2)]
    e.step()
    assert _min_pair(e, ids) >= DIAMETER - TOL
    assert _pos(e, ids[0]) != (1000.0, 1000.0)


def test_R_101_01_twenty_unit_scene_keeps_every_pair_at_29_over_200_ticks():
    """R-101-01 at A157's tolerance (30.0 - 1.0): the 20-unit scene of
    tests/csim/test_E13_S101_movement_that_reads.py (4 x 5 block 35 wu apart, one group move to (1000,70), the
    4000 x 4000 open field). Worst pair on the old rule: 4.98 wu (A154); with the fix 29.11."""
    e = _engine()
    ids = [e.store.spawn("Raider", 0, r * 35.0, c * 35.0) for r in range(4) for c in range(5)]
    _move(e, ids, 1000.0, 70.0)
    for tick in range(200):
        e.step()
        worst = _min_pair(e, ids)
        assert worst >= 29.0, f"tick {tick}: worst pair {worst:.2f} wu"
