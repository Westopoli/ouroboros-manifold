"""Group speed cap is the slowest member's BASE speed, whatever any member is doing at order time.

Proves E-13 R-095-01 (S-095): "every unit's speed is capped at the slowest member's base speed, fixed at order
time". Bug: om_command_group_move (csrc/tactical_move.c) takes the minimum of om_unit_effective_speed, which is 0
for a unit in backswing (just fired), so the cap becomes 0 and the whole group never moves. Any move or
attack-move order given during a fight can do it. Q-095-01 (a unit that activates a movement ability leaves the
group) is not touched: no ability is used here, and the cap is read before any ability could matter.

The Python reference (simulation/movement.py apply_group_move) has no speed cap at all, so there is no Python test.

A unit is put in backswing with om_unit_deal_damage (the helper test_E11_S084_flat_damage.py uses for R-084-04);
the enemy stands far off, outside every range and path. Expected distances come from speed and tick length:
speed / 20 wu per tick (OM_TACTICAL_TICK_RATE = 20) times 40 ticks, less a 10 percent margin for turning.
Tests 1 to 3 are red today (cap 0); the control is green.
"""
import ctypes
import math

import pytest

from test_PP_unit_support import attack_move, pos, spawn, step

RAIDER, VANGUARD, BASTION = 0, 2, 5
FRIEND, ENEMY = 0, 1
TICKS = 40
BACKSWING_TICKS = 11      # the pause set by om_unit_deal_damage (0.5 s, 10 ticks) is still on for 11 steps in this scene (measured)
DIST = 600.0
MARGIN = 0.90
ENEMY_AT = (-6000.0, 3000.0)


def _setup(lib, w, types, swinging):
    """Units of `types` stacked 100 wu apart in y; those at indices in `swinging` are in backswing."""
    ids = [spawn(lib, w, t, FRIEND, 0.0, 100.0 * i) for i, t in enumerate(types)]
    foe = spawn(lib, w, BASTION, ENEMY, *ENEMY_AT)
    for i in swinging:
        lib.om_unit_deal_damage(w, ids[i], foe, 1.0)
        assert lib.om_unit_in_backswing(w, ids[i]) == 1, "scene error: not in backswing"
    return ids


def _group_move(lib, w, ids):
    arr = (ctypes.c_uint32 * len(ids))(*ids)
    assert lib.om_command_group_move(w, arr, len(ids), DIST, 100.0) != 0


def _check(lib, w, ids, types, cap_type):
    base = lib.om_unit_profile_speed(w, cap_type)
    # Test-defect (F2 engine rule fixes, 2026-11-08): a member in backswing at order time now waits out the 0.5 s pause (R-084-04, ALG-60; group
    # members used to ignore it), so the 40 ticks are measured after the pause, which is what this test is about (the cap is the base speed, not 0).
    step(lib, w, BACKSWING_TICKS)
    for u in ids:
        assert lib.om_unit_get_current_speed(w, u) == pytest.approx(base, abs=1e-9), \
            f"unit {u}: group cap is {lib.om_unit_get_current_speed(w, u)}, base speed of the slowest member is {base}"
    start = {u: pos(lib, w, u) for u in ids}
    step(lib, w, TICKS)
    want = base / 20.0 * TICKS
    for u in ids:
        x0, y0 = start[u]
        x1, y1 = pos(lib, w, u)
        gx, gy = DIST + 0.0, 100.0 + (y0 - 100.0)   # slot: click point plus the unit's offset from the centroid
        d0 = math.hypot(gx - x0, gy - y0)
        gained = d0 - math.hypot(gx - x1, gy - y1)
        assert want * MARGIN <= gained <= want + 0.5, \
            f"unit {u} closed {gained:.2f} wu on its slot in {TICKS} ticks; the cap gives {want:.2f}"


@pytest.mark.parametrize("swinging", [[0], [1], [0, 1, 2]])
def test_R_095_01_group_move_cap_is_base_speed_when_a_member_is_in_backswing(lib, world_factory, swinging):
    w = world_factory(n_regions=1)
    types = [VANGUARD] * 3
    ids = _setup(lib, w, types, swinging)
    _group_move(lib, w, ids)
    _check(lib, w, ids, types, VANGUARD)


@pytest.mark.parametrize("swinging", [[0], [1], [0, 1, 2]])
def test_R_095_01_attack_move_cap_is_base_speed_when_a_member_is_in_backswing(lib, world_factory, swinging):
    w = world_factory(n_regions=1)
    types = [VANGUARD] * 3
    ids = _setup(lib, w, types, swinging)
    assert attack_move(lib, w, ids, DIST, 100.0) is not None
    _check(lib, w, ids, types, VANGUARD)


@pytest.mark.parametrize("swinging", [[0], [1]])
def test_R_095_01_mixed_group_cap_is_the_slow_types_base_speed_when_one_is_in_backswing(lib, world_factory, swinging):
    """Raider (150 wu/s) and Bastion (40 wu/s): the cap is the Bastion's 40, not 0, whichever one is mid-swing."""
    w = world_factory(n_regions=1)
    types = [RAIDER, BASTION]
    ids = _setup(lib, w, types, swinging)
    _group_move(lib, w, ids)
    _check(lib, w, ids, types, BASTION)


def test_control_R_095_01_group_move_with_nobody_in_backswing_moves_at_base_speed(lib, world_factory):
    """Positive control (green today): the same orders with nobody in backswing give the base speed cap."""
    w = world_factory(n_regions=1)
    types = [VANGUARD] * 3
    ids = _setup(lib, w, types, [])
    _group_move(lib, w, ids)
    _check(lib, w, ids, types, VANGUARD)


def test_control_R_095_01_attack_move_with_nobody_in_backswing_moves_at_base_speed(lib, world_factory):
    w = world_factory(n_regions=1)
    types = [VANGUARD] * 3
    ids = _setup(lib, w, types, [])
    attack_move(lib, w, ids, DIST, 100.0)
    _check(lib, w, ids, types, VANGUARD)
