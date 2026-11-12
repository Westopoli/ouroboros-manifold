# Rule pins: R-004-06, R-004-08, R-190-04, R-097-01
"""E-01 R-004-06 / R-004-08 (engine rule fixes 2026-11-08, F8): a unit that changes layer on a slope does not jump.

Rule words (docs/bible/epics/E-01-layer-system.md, as written 2026-11-08):
  R-004-06  "Given a unit on a slope that joins layers L and L+1, When it is at any point along the slope's length, Then its transition progress is its
             position along the slope, not a timer: below the midline, units on layer L may attack it and units on layer L+1 may not; at or above the
             midline, units on layer L+1 may attack it and units on layer L may not; the same holds going up or down ..."
  R-004-08  "... while on the slope the unit counts as being on the layer on its side of the midline ... so a unit that turns back before the midline
             has not changed layer and one that crosses the midline and comes back has changed twice."
Neither rule says in words that the position is continuous; the spec (docs/northstar/plans/engine-rules-2026-11-08/spec.md F8) reads them so: the layer may
flip at the midline, twice if the unit comes back, and the unit's position is its own step each tick, never a jump. That reading is the Architect's
(gap reported: a rule line "a layer change moves a unit by its own step and no more" would make it the rule's own words).

The bound: DRAFT-inv-step-slack 1.3 wu above the unit's top step, speed x max(1, OM_TP_SLOPE_DOWN_MULT) / 20 a tick (scripts/skilllab/invariants.py STEP_SLACK;
Westley's to change), read from the live world, never typed in.

Scene (premises dumped from the built tree, Round 1 tip 94c2fb5d, 2026-11-11): canvas 4000, ground era, terrain heights replaced by `om_terrain_set_heights`,
low ground west of x 1100, plateau east of x 1300, a straight ramp between rising 70 to 190 wu (the lab's hills.py ramp: heights LOW_CM 7000 to LOW_CM + 2 x
STEP_CM - 1, band floor at the ramp's middle, so the layer flips at x ~ 1198 and the corner cell sets the 60 wu step). Walkers (movement kind 1), shipped
configuration. Band heights [70, 130, 190, ...]; OM_TP_SLOPE_DOWN_MULT 1.1.
Measured on the built tree:
  a lone walker, any of the six roles, up then down the ramp  excess over its top step 0.00, layer flips once each way: no jump (control below)
  the same walker climbing into 8 friends standing on the ramp's upper part (x 1215 to 1275, layer 1): it flips to layer 1, is pushed back, flips again, over and
      over (the I23 flicker) and moves 10 to 15 wu in one tick (its top step is 2.2 to 8.25) on 27 to 120 ticks of 400 (the I5tL jump); on a flat world the same crowd stops it with no excess.
The F0 checker's `continuity` excuses any unit with a neighbour within 40 wu, so it reports 0 on this scene; these tests do not excuse a push.
"""
import ctypes
import math

import pytest

from conftest import OMFeature
from test_PP_unit_support import BASTION, BOMBARD, INTERCEPTOR, RAIDER, VANGUARD, WARDEN, get_param, pos, spawn, step

CANVAS = 4000.0
LOW_CM, STEP_CM = 7000, 6000
RAMP_FOOT, RAMP_TOP = 1100.0, 1300.0
WALKING = 1
SLACK = 1.3           # DRAFT-inv-step-slack (scripts/skilllab/invariants.py STEP_SLACK)
TICKS = 400
ROLES = [("Raider", RAIDER), ("Interceptor", INTERCEPTOR), ("Vanguard", VANGUARD), ("Warden", WARDEN), ("Bombard", BOMBARD), ("Bastion", BASTION)]


def _world(lib, wf, terrain=True):
    w = wf(n_regions=1)
    lib.om_world_set_feature(w, OMFeature.TACTICAL, 1)
    assert lib.om_map_set_canvas(w, CANVAS, CANVAS) == 0
    if terrain:
        assert lib.om_terrain_generate(w, 7, CANVAS, CANVAS) == 0
        lib.om_set_era_kind(w, 1)
        n = 40
        cm = []
        for _ in range(n):
            for cx in range(n):
                t = min(1.0, max(0.0, ((cx + 0.5) * 100.0 - RAMP_FOOT) / (RAMP_TOP - RAMP_FOOT)))
                cm.append(LOW_CM + int(t * (2 * STEP_CM - 1)))
        cm[n * n - 1] = LOW_CM + 5 * STEP_CM
        assert lib.om_terrain_set_heights(w, (ctypes.c_int32 * len(cm))(*cm), n, n) == 1
    for _, role in ROLES:
        assert lib.om_roster_set_movement_kind(w, role, WALKING) == 0
    return w


def _top_step(lib, w, role):
    down = get_param(lib, w, "OM_TP_SLOPE_DOWN_MULT")
    return lib.om_unit_profile_speed(w, role) * max(1.0, down) / 20.0


def _walk(lib, w, unit, ticks, bound):
    """Per tick: (tick, displacement, layer before, layer after) for every tick the unit moved more than `bound`; plus the layer sequence."""
    bad, layers = [], [lib.om_unit_get_layer(w, unit)]
    for t in range(1, ticks + 1):
        p0, l0 = pos(lib, w, unit), lib.om_unit_get_layer(w, unit)
        step(lib, w)
        p1, l1 = pos(lib, w, unit), lib.om_unit_get_layer(w, unit)
        d = math.hypot(p1[0] - p0[0], p1[1] - p0[1])
        if d > bound:
            bad.append((t, round(d, 2), l0, l1))
        if l1 != layers[-1]:
            layers.append(l1)
    return bad, layers


@pytest.mark.parametrize("name,role", ROLES, ids=[r[0] for r in ROLES])
def test_R_004_06_control_a_lone_walker_up_and_down_a_ramp_moves_at_its_own_pace(lib, world_factory, name, role):
    """R-004-06 / R-004-08 control (green today and after): one walker of the role crosses the ramp up (to x 1400) and back down (to x 900); on every tick,
    the layer-change ticks included, it moves at most its top step + 1.3 wu; it was on layer 1 at the top and is on layer 0 again at the foot. The layer may
    flip any number of times; the position never jumps. Green today: no jump without a crowd."""
    w = _world(lib, world_factory)
    a = spawn(lib, w, role, 0, 900, 2050, 0)
    bound = _top_step(lib, w, role) + SLACK
    lib.om_command_move(w, [a], 1, 1400.0, 2050.0)
    bad_up, layers_up = _walk(lib, w, a, TICKS, bound)
    assert layers_up[-1] == 1, "premise: %s never reached layer 1 (layers %s, at %s)" % (name, layers_up, pos(lib, w, a))
    lib.om_command_move(w, [a], 1, 900.0, 2050.0)
    bad_dn, layers_dn = _walk(lib, w, a, TICKS, bound)
    assert layers_dn[-1] == 0, "premise: %s never came back to layer 0 (layers %s, at %s)" % (name, layers_dn, pos(lib, w, a))
    assert not (bad_up or bad_dn), "%s moved more than %.2f wu in a tick: up %s, down %s" % (name, bound, bad_up[:3], bad_dn[:3])


@pytest.mark.parametrize("name,role", ROLES, ids=[r[0] for r in ROLES])
def test_R_004_08_a_walker_changing_layer_among_friends_never_jumps(lib, world_factory, name, role):
    """R-004-06 / R-004-08 (the spec's reading: the layer flips, the position does not jump): one walker of the role climbs the ramp toward x 1400 where 8
    friendly Vanguards stand idle on the ramp's upper part (x 1215 to 1275, layer 1, 30 wu apart, the packing the lab's march makes). On every one of 400
    ticks it moves at most its top step + 1.3 wu. Red today: it flips to layer 1, moves 10 to 15 wu in that tick, is pushed back, flips again, 27 to 120
    ticks over the bound per role (Raider 120, Bastion 27), the I5tL jump and the I23 flicker."""
    w = _world(lib, world_factory)
    for i in range(8):
        spawn(lib, w, VANGUARD, 0, 1215 + 30 * (i % 3), 2020 + 30 * (i // 3), 1)
    a = spawn(lib, w, role, 0, 900, 2050, 0)
    bound = _top_step(lib, w, role) + SLACK
    lib.om_command_move(w, [a], 1, 1400.0, 2050.0)
    bad, layers = _walk(lib, w, a, TICKS, bound)
    assert len(layers) > 1, "premise: %s never changed layer (%s) at %s" % (name, layers, pos(lib, w, a))
    assert not bad, "%s moved more than %.2f wu in a tick on %d of %d ticks, first %s (layer flips %d)" % (name, bound, len(bad), TICKS, bad[:3], len(layers) - 1)


@pytest.mark.parametrize("name,role", ROLES, ids=[r[0] for r in ROLES])
def test_R_004_08_control_the_same_crowd_on_flat_ground_stops_a_walker_without_a_jump(lib, world_factory, name, role):
    """R-004-08 control (green today and after): the same 8 friends, the same walker, the same order on a world with no terrain (nothing to change layer
    on): the walker is held up by the crowd and never moves more than its top step + 1.3 wu in a tick. So the excess above is the layer change's doing."""
    w = _world(lib, world_factory, terrain=False)
    for i in range(8):
        spawn(lib, w, VANGUARD, 0, 1215 + 30 * (i % 3), 2020 + 30 * (i // 3), 0)
    a = spawn(lib, w, role, 0, 900, 2050, 0)
    bound = _top_step(lib, w, role) + SLACK
    lib.om_command_move(w, [a], 1, 1400.0, 2050.0)
    bad, layers = _walk(lib, w, a, TICKS, bound)
    assert layers == [0]
    assert not bad, "%s moved more than %.2f wu in a tick on flat ground: %s" % (name, bound, bad[:3])
