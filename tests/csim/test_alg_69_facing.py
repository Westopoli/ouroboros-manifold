"""ALG-69 Facing (docs/bible/algorithms.md; S-088): "Target if attacking, heading if moving, else hold; turn rate
capped at FACING_ROTATION_SPEED_STRIKE = 6.0, LINE = 4.0, SIEGE = 2.5 rad/s."

The tactical tick is 20 per second (ALG-60 timing note), so the cap is rate / 20 radians per tick: Strike 0.3, Line 0.2,
Siege 0.125. Types: Raider = Strike, Vanguard = Line, Bombard = Siege (roster, S-082). Positive control: the three
categories turn at three different rates, so a wrong table would fail the per-type comparison.
"""
import math

import pytest

from conftest import OMFeature

RAIDER, VANGUARD, BOMBARD, SUPPLY = 0, 2, 4, 6
PLAYER, ENEMY = 0, 1
RATE = {RAIDER: 6.0, VANGUARD: 4.0, BOMBARD: 2.5}  # rad/s, typed from ALG-69
TICK_RATE = 20


def _world(lib):
    w = lib.om_world_new(1, 1)
    assert w
    lib.om_world_set_feature(w, OMFeature.TACTICAL, 1)
    return w


def _facing_trace(lib, w, u, steps):
    out = []
    for _ in range(steps):
        lib.om_world_step(w)
        out.append(lib.om_unit_get_facing(w, u))
    return out


def _turn_per_tick(trace):
    """The largest single-tick change in facing along the trace (the cap shows once the unit is turning)."""
    return max(abs(b - a) for a, b in zip(trace, trace[1:]))


@pytest.mark.parametrize("utype", [RAIDER, VANGUARD, BOMBARD])
def test_ALG_69_attacking_unit_turns_toward_its_target_at_the_category_rate_cap(lib, utype):
    w = _world(lib)
    u = lib.om_unit_spawn(w, utype, PLAYER, 0.0, 0.0, 0)
    lib.om_unit_spawn(w, SUPPLY, ENEMY, -100.0, 0.0, 0)  # directly behind: the largest turn, pi
    trace = _facing_trace(lib, w, u, 60)
    cap = RATE[utype] / TICK_RATE
    assert _turn_per_tick(trace) == pytest.approx(cap)  # capped, never faster
    assert abs(trace[-1]) == pytest.approx(math.pi, abs=1e-4)  # and it ends facing the target (behind it)


def test_control_ALG_69_the_three_categories_turn_at_three_different_rates(lib):
    caps = []
    for utype in (RAIDER, VANGUARD, BOMBARD):
        w = _world(lib)
        u = lib.om_unit_spawn(w, utype, PLAYER, 0.0, 0.0, 0)
        lib.om_unit_spawn(w, SUPPLY, ENEMY, -100.0, 0.0, 0)
        caps.append(_turn_per_tick(_facing_trace(lib, w, u, 60)))
    assert len({round(c, 6) for c in caps}) == 3
    assert caps[0] != pytest.approx(RATE[VANGUARD] / TICK_RATE)


def test_ALG_69_a_moving_unit_faces_its_heading(lib):
    w = _world(lib)
    u = lib.om_unit_spawn(w, RAIDER, PLAYER, 0.0, 0.0, 0)
    lib.om_command_move(w, [u], 1, 0.0, 5000.0)  # due +y: heading pi/2
    trace = _facing_trace(lib, w, u, 14)
    assert trace[0] == pytest.approx(RATE[RAIDER] / TICK_RATE)  # turning at the cap from facing 0
    assert trace[-1] == pytest.approx(math.pi / 2, abs=1e-4)


def test_ALG_69_a_unit_that_neither_attacks_nor_moves_holds_its_facing(lib):
    w = _world(lib)
    u = lib.om_unit_spawn(w, RAIDER, PLAYER, 0.0, 0.0, 0)
    lib.om_unit_set_facing(w, u, 1.0)
    trace = _facing_trace(lib, w, u, 10)
    assert all(f == pytest.approx(1.0) for f in trace)


def test_control_ALG_69_a_moving_unit_does_not_hold(lib):
    w = _world(lib)
    u = lib.om_unit_spawn(w, RAIDER, PLAYER, 0.0, 0.0, 0)
    lib.om_unit_set_facing(w, u, 1.0)
    lib.om_command_move(w, [u], 1, 0.0, -5000.0)
    trace = _facing_trace(lib, w, u, 10)
    assert trace[-1] != pytest.approx(1.0)
