# Rule pins: R-087-10, R-087-05, R-084-03, R-098-02, R-190-04
"""E-11 R-087-10 (engine rule fixes 2026-11-08, F7): every range and radius test is spherical, layer height included.

Rule words proved (docs/bible/epics/E-11-units-and-combat.md, as written 2026-11-08):
  R-087-10  "Given any range or radius test between two units (attack range, sensor radius, leash, area radius), When it is evaluated, Then
             the distance is spherical: the horizontal distance and the height difference between the two units' layers (E-17 R-190-04 band
             heights, a unit mid-slope at its slope height) taken together ... The engine measures flat today."
  R-098-02  "Given a blocked cell (R-097-01) or a cover obstacle between them on the layers involved, When it fires, Then the shot is blocked
             exactly as vision is": a line that sight sees along and that crosses no obstacle is not blocked for fire (the I11nl case below).
  E-17 R-190-04  "the five band heights are output, and E-01 R-010-01 reads them to draw a unit at its layer's height."
Spec: docs/northstar/plans/engine-rules-2026-11-08/spec.md "F7". Evidence: docs/reports/2026-11-07-rule-enforcement/appendix-c-invariant-sweep.md I11nl.

Scene S (isolates the metric; the one switch that differs from the shipped configuration is that the units are flyers on an AIR layer, and why):
a canvas 4000 x 4000, era kind 1 (ground), generated terrain whose heights are replaced by `om_terrain_set_heights` with one flat plane at 7000 cm and
one corner cell at 7000 + 5 x 6000 cm (the lab's own trick, scripts/skilllab/arena/hills.py: the highest cell sets the five band floors). Premises dumped
from the built tree (2026-11-11, Round 1 tip 94c2fb5d):
    om_terrain_band_heights  = [70.0, 130.0, 190.0, 250.0, 310.0]   layer L stands at band_heights[L]; layer 1 is 60 wu above layer 0
    OM_TP_RANGE_UP_1 = OM_TP_RANGE_DOWN_1 = OM_TP_AREA_UP_1 = 1.0   (the cross-layer range / area multipliers are 1)
    unit types: SEER / SHOOTER / TARGET / SPLASH are custom types registered here; reach (1 up, 1 down); speed 0 where the test is about range alone,
    so that a unit cannot close the gap and so hide a firing that a spherical rule would not allow.
Why flyers on an air layer: a WALKER standing on a hill (band 2, layer 1) cannot shoot a unit on the flat below it at any range on the built tree
(om_combat_can_shoot is false from 150 wu, see test_R_098_02_i11nl_*). That is the open I11nl case, tested on its own below; over a flat plane
there is no ground cell to confuse it and the metric is what the tests measure.

Detector bounds (not rules; Westley's to change): DRAFT-f7-ticks 60 (long enough for the cohort turn that acquires, plus several shots at interval 0.5 s),
DRAFT-f7-gap 4 wu (the horizontal margins below keep each pair 4 to 9 wu clear of the slant limit, wider than one tick of any push).
"""
import ctypes
import math

import pytest

from conftest import OMFeature
from test_PP_unit_support import attack_move, hp, pos, spawn, step, target

CANVAS = 4000.0
LOW_CM, STEP_CM = 7000, 6000
SEER, SHOOTER, TARGET, SPLASH, PASSIVE = 20, 21, 22, 23, 24
WALKING = 1
TICKS = 60            # DRAFT-f7-ticks
FULL = 1000.0
RANGE = 300.0
LAYER_DZ = 60.0       # band_heights[1] - band_heights[0], asserted from the live world in every scene


def _plane(lib, w, step_cm=STEP_CM):
    """Terrain present, one flat plane; band floors LOW_CM + k * step_cm (read back with om_terrain_band_heights)."""
    assert lib.om_terrain_generate(w, 7, CANVAS, CANVAS) == 0
    n = 40
    cm = [LOW_CM] * (n * n)
    cm[n * n - 1] = LOW_CM + 5 * step_cm
    assert lib.om_terrain_set_heights(w, (ctypes.c_int32 * len(cm))(*cm), n, n) == 1


def _reg(lib, w, tid, hp_, dmg, interval, rng, speed, sensor, aoe=0.0, kind=0):
    assert lib.om_roster_register_custom_unit(w, tid, 0, b"f7_%d" % tid, hp_, dmg, interval, rng, speed, sensor, 1.0, aoe, 0) == 0
    assert lib.om_roster_set_reach(w, tid, 1, 1) == 0
    assert lib.om_roster_set_movement_kind(w, tid, kind) == 0


def _world(lib, wf, terrain=True):
    w = wf(n_regions=1)
    lib.om_world_set_feature(w, OMFeature.TACTICAL, 1)
    assert lib.om_map_set_canvas(w, CANVAS, CANVAS) == 0
    if terrain:
        _plane(lib, w)
        lib.om_set_era_kind(w, 1)
    _reg(lib, w, SEER, FULL, 1.0, 1.0, 100.0, 0.0, RANGE)
    _reg(lib, w, SHOOTER, FULL, 10.0, 0.5, RANGE, 0.0, 600.0)
    _reg(lib, w, TARGET, FULL, 1.0, 1.0, 10.0, 0.0, 10.0)
    return w


def _heights(lib, w):
    buf = (ctypes.c_double * 8)()
    n = lib.om_terrain_band_heights(w, buf, 8)
    return list(buf)[:n]


def _slant(flat, h, la, lb):
    return math.hypot(flat, h[lb] - h[la])


def _premise(lib, w, flat, limit, inside_flat=True, inside_slant=True):
    """The scene premise, asserted from the live world: the band heights, and which side of `limit` the flat and the slant distance fall."""
    h = _heights(lib, w)
    assert h[:2] == [70.0, 130.0], "band heights %s, the scene assumes 70 and 130" % h
    s = _slant(flat, h, 1, 0)
    assert (flat <= limit) == inside_flat and (s <= limit) == inside_slant, "premise: flat %.1f slant %.1f limit %.1f" % (flat, s, limit)
    return s


# ------------------------------------------------------------------ attack range

def test_R_087_10_attack_range_a_unit_outside_range_by_slant_does_not_fire(lib, world_factory):
    """R-087-10 'attack range ... the distance is spherical': a shooter (range 300) on layer 1 and a target on layer 0, 299 wu apart on the
    ground (inside 300 flat) and 305.0 apart in the air (60 wu of layer height): it does not fire in 60 ticks. The shooter cannot walk (speed 0).
    Red today: the range test is flat, the target loses hit points from the first shot."""
    w = _world(lib, world_factory)
    slant = _premise(lib, w, 299.0, RANGE, inside_flat=True, inside_slant=False)
    a = spawn(lib, w, SHOOTER, 0, 1000, 2000, 1)
    b = spawn(lib, w, TARGET, 1, 1299, 2000, 0)
    assert (lib.om_unit_get_layer(w, a), lib.om_unit_get_layer(w, b)) == (1, 0)
    step(lib, w, TICKS)
    assert hp(lib, w, b) == FULL, "fired at a target %.1f wu away through the air (range %.0f), target hp %.1f" % (slant, RANGE, hp(lib, w, b))


def test_R_087_10_attack_range_control_a_unit_inside_range_by_slant_fires(lib, world_factory):
    """R-087-10 control (green today and after): 290 wu on the ground, 296.2 through the air, both inside 300: the same pair fires. Proves the
    scene fires, so the test above is red for the metric and not for a muted shooter."""
    w = _world(lib, world_factory)
    _premise(lib, w, 290.0, RANGE, inside_flat=True, inside_slant=True)
    a = spawn(lib, w, SHOOTER, 0, 1000, 2000, 1)
    b = spawn(lib, w, TARGET, 1, 1290, 2000, 0)
    step(lib, w, TICKS)
    assert hp(lib, w, b) < FULL, "scene broken: no shot landed at 290 wu"


def test_R_087_10_attack_range_control_the_same_layer_is_measured_flat(lib, world_factory):
    """R-087-10 control (green today and after): two units on the SAME layer have no height difference; 299 wu is inside 300 and fires."""
    w = _world(lib, world_factory)
    a = spawn(lib, w, SHOOTER, 0, 1000, 2000, 1)
    b = spawn(lib, w, TARGET, 1, 1299, 2000, 1)
    step(lib, w, TICKS)
    assert hp(lib, w, b) < FULL, "scene broken: no shot landed at 299 wu on one layer"


def test_R_087_10_attack_range_control_a_world_with_no_terrain_measures_flat(lib, world_factory):
    """Spec F7 'a world with no terrain has no heights and measures flat, as now' (no bible rule words it; the rule text says 'The engine measures
    flat today'): no terrain, layer 1 against layer 0, 299 wu apart: it fires. Green today and after."""
    w = _world(lib, world_factory, terrain=False)
    assert lib.om_terrain_present(w) == 0 and _heights(lib, w) == []
    a = spawn(lib, w, SHOOTER, 0, 1000, 2000, 1)
    b = spawn(lib, w, TARGET, 1, 1299, 2000, 0)
    step(lib, w, TICKS)
    assert hp(lib, w, b) < FULL, "scene broken: no shot landed at 299 wu in a world with no terrain"


# ------------------------------------------------------------------ sensor radius

def test_R_087_10_sensor_radius_a_unit_outside_sensor_radius_by_slant_does_not_see(lib, world_factory):
    """R-087-10 'sensor radius': an observer (sensor 300, range 100) on layer 1 and an enemy on layer 0, 297 wu apart on the ground, 303.0 through the
    air: it does not see it. Red today: om_unit_can_see is true to 300 flat (measured: true at 280 to 299, false at 301)."""
    w = _world(lib, world_factory)
    slant = _premise(lib, w, 297.0, RANGE, inside_flat=True, inside_slant=False)
    a = spawn(lib, w, SEER, 0, 1000, 2000, 1)
    b = spawn(lib, w, TARGET, 1, 1297, 2000, 0)
    assert not lib.om_unit_can_see(w, a, b), "sees an enemy %.1f wu away through the air (sensor radius %.0f)" % (slant, RANGE)


def test_R_087_10_sensor_radius_control_a_unit_inside_sensor_radius_by_slant_sees(lib, world_factory):
    """R-087-10 control (green today and after): 290 wu on the ground, 296.2 through the air, inside 300: it sees the enemy."""
    w = _world(lib, world_factory)
    _premise(lib, w, 290.0, RANGE, inside_flat=True, inside_slant=True)
    a = spawn(lib, w, SEER, 0, 1000, 2000, 1)
    b = spawn(lib, w, TARGET, 1, 1290, 2000, 0)
    assert lib.om_unit_can_see(w, a, b), "scene broken: no sight at 290 wu"


# ------------------------------------------------------------------ area radius

def _splash_scene(lib, wf):
    """A splasher (range 600, area radius 100, speed 0) on layer 0 ordered at B (layer 0); C 90 wu from B on the ground and on layer 1
    (108.2 through the air: outside 100), D 70 wu from B and on layer 1 (92.2: inside). Returns (world, B, C, D) after TICKS ticks."""
    w = _world(lib, wf)
    _reg(lib, w, SPLASH, FULL, 10.0, 0.5, 600.0, 0.0, 600.0, aoe=100.0)
    _reg(lib, w, PASSIVE, FULL, 1.0, 1.0, 10.0, 0.0, 10.0)
    _premise(lib, w, 90.0, 100.0, inside_flat=True, inside_slant=False)
    _premise(lib, w, 70.0, 100.0, inside_flat=True, inside_slant=True)
    x = spawn(lib, w, SPLASH, 0, 500, 2000, 0)
    b = spawn(lib, w, PASSIVE, 1, 900, 2000, 0)
    c = spawn(lib, w, PASSIVE, 1, 900, 2090, 1)
    d = spawn(lib, w, PASSIVE, 1, 900, 1930, 1)
    lib.om_command_attack_target(w, (ctypes.c_uint32 * 1)(x), 1, b)
    step(lib, w, TICKS)
    return w, b, c, d


def test_R_087_10_area_radius_a_unit_outside_the_area_by_slant_is_not_hurt(lib, world_factory):
    """R-087-10 'area radius' (R-084-03): the splash around the target (area radius 100) must not hurt an enemy that is 90 wu from it on the
    ground but on a layer 60 wu higher (108.2 away through the air). Red today: the area query is a flat circle, so it is hurt."""
    w, b, c, d = _splash_scene(lib, world_factory)
    assert hp(lib, w, b) < FULL, "scene broken: the splasher never hit its ordered target"
    assert hp(lib, w, c) == FULL, "hurt by a splash whose centre is 108.2 wu away through the air (area radius 100), hp %.1f" % hp(lib, w, c)


def test_R_087_10_area_radius_control_a_unit_inside_the_area_by_slant_is_hurt(lib, world_factory):
    """R-087-10 control (green today and after): the enemy 70 wu from the target on the ground and 92.2 through the air is inside 100 and is hurt,
    so the splash reaches across layers in this scene and the test above is red for the metric."""
    w, b, c, d = _splash_scene(lib, world_factory)
    assert hp(lib, w, d) < FULL, "scene broken: the splash did not reach a layer-1 enemy 92.2 wu from its centre"


# ------------------------------------------------------------------ leash

LEASH = 310.0
DZ_LEASH = 100.0      # the leash scene's band step: STEP_CM 10000 (a layer is 100 wu high there)


def _leash_world(lib, wf):
    """A west plateau (layer 1, 170 wu) that falls over x 950 to 1150 to a low plane (layer 0, 70 wu); the corner cell sets a 100 wu band step.
    P, a walker (speed 100, range 100, sensor 310, so the leash is 310), idles on the plateau at x 870; T, a walker enemy, stands 120 wu ahead at x 990 (same
    layer). Once P holds T, T is ordered east at P's pace; P chases down the ramp and the leash (R-087-05) drops the target. Both readings of 'height'
    agree where the leash breaks: P is on the low plane (x >= 1150) and the anchor is on the plateau (x <= 950)."""
    w = wf(n_regions=1)
    lib.om_world_set_feature(w, OMFeature.TACTICAL, 1)
    assert lib.om_map_set_canvas(w, CANVAS, CANVAS) == 0
    assert lib.om_terrain_generate(w, 7, CANVAS, CANVAS) == 0
    lib.om_set_era_kind(w, 1)
    n, step_cm = 40, 10000
    cm = []
    for _ in range(n):
        for cx in range(n):
            t = min(1.0, max(0.0, (1150.0 - (cx + 0.5) * 100.0) / 200.0))
            cm.append(LOW_CM + int(t * step_cm))
    cm[n * n - 1] = LOW_CM + 5 * step_cm
    assert lib.om_terrain_set_heights(w, (ctypes.c_int32 * len(cm))(*cm), n, n) == 1
    _reg(lib, w, SEER, FULL, 1.0, 1.0, 100.0, 100.0, LEASH, kind=WALKING)
    _reg(lib, w, TARGET, FULL, 0.0, 1.0, 10.0, 100.0, 10.0, kind=WALKING)
    return w


def test_R_087_10_leash_a_pursuer_drops_its_target_at_the_spherical_distance_from_its_anchor(lib, world_factory):
    """R-087-10 'leash' (R-087-05 'the leash measures the pursuer's own distance from its anchor'): P anchors on the plateau (layer 1, 170 wu) and chases
    a fleeing enemy down onto the low plane (layer 0, 70 wu): 100 wu lower. With a leash of 310 the target must be dropped once sqrt(h^2 + 100^2) > 310,
    h = 293.4 wu of ground distance, so P's ground distance from the anchor on the tick before the drop is at most 293.4 + one step (5.5) = 299. Red today:
    the leash is flat, P chases to 310 + (measured on the built tree: drops at 310 to 315)."""
    w = _leash_world(lib, world_factory)
    h = _heights(lib, w)
    assert h[:2] == [70.0, 170.0], "band heights %s, the scene assumes 70 and 170" % h
    p = spawn(lib, w, SEER, 0, 870, 2050, 1)
    t = spawn(lib, w, TARGET, 1, 990, 2050, 1)
    anchor = None
    held, ordered, drop_h = False, False, None
    for k in range(400):
        before = pos(lib, w, p)
        step(lib, w)
        if not held and target(lib, w, p) == t:
            held, anchor = True, before
        if held and not ordered:
            lib.om_command_move(w, [t], 1, 3500.0, 2050.0)
            ordered = True
        if held and drop_h is None and target(lib, w, p) != t:
            drop_h = math.hypot(before[0] - anchor[0], before[1] - anchor[1])
            break
    assert held, "scene broken: the pursuer never took the target"
    assert drop_h is not None, "never dropped the target in 400 ticks (leash %.0f)" % LEASH
    bound = math.sqrt(LEASH ** 2 - DZ_LEASH ** 2) + 6.0
    assert drop_h <= bound, "dropped at %.1f wu of ground distance from its anchor; the spherical leash breaks at %.1f (flat: %.0f)" % (drop_h, bound - 6.0, LEASH)


def test_R_087_10_leash_control_the_target_is_held_to_the_flat_limit_on_one_layer(lib, world_factory):
    """R-087-05 control (green today and after): on one layer (a flat plane, no height difference) the same chase is dropped at 310 flat, within
    one step of it; the chase is real and the leash is the thing that ends it."""
    w = _world(lib, world_factory)
    _reg(lib, w, SEER, FULL, 1.0, 1.0, 100.0, 100.0, LEASH, kind=WALKING)
    _reg(lib, w, TARGET, FULL, 0.0, 1.0, 10.0, 100.0, 10.0, kind=WALKING)
    p = spawn(lib, w, SEER, 0, 870, 2050, 1)
    t = spawn(lib, w, TARGET, 1, 990, 2050, 1)
    anchor, held, ordered, drop_h = None, False, False, None
    for k in range(400):
        before = pos(lib, w, p)
        step(lib, w)
        if not held and target(lib, w, p) == t:
            held, anchor = True, before
        if held and not ordered:
            lib.om_command_move(w, [t], 1, 3500.0, 2050.0)
            ordered = True
        if held and drop_h is None and target(lib, w, p) != t:
            drop_h = math.hypot(before[0] - anchor[0], before[1] - anchor[1])
            break
    assert held and drop_h is not None, "scene broken: held %s, dropped at %s" % (held, drop_h)
    assert LEASH - 6.0 <= drop_h <= LEASH + 6.0, "dropped at %.1f, the flat leash is %.0f" % (drop_h, LEASH)


# ------------------------------------------------------------------ I11nl: sight and fire agree

def _hill_world(lib, wf):
    """The shipped configuration: a hill (layer 1 west of x 1000, falling to layer 0 by x 1200), walkers, sight on, ground era, as the lab's `vantage`
    builds it (heights 70 to 190 wu over the ramp, the corner cell sets the 60 wu step; scripts/skilllab/arena/hills.py LOW_CM 7000, STEP_CM 6000)."""
    w = wf(n_regions=1)
    lib.om_world_set_feature(w, OMFeature.TACTICAL, 1)
    assert lib.om_map_set_canvas(w, CANVAS, CANVAS) == 0
    assert lib.om_terrain_generate(w, 7, CANVAS, CANVAS) == 0
    lib.om_set_era_kind(w, 1)
    n = 40
    cm = []
    for _ in range(n):
        for cx in range(n):
            t = min(1.0, max(0.0, (1200.0 - (cx + 0.5) * 100.0) / 200.0))
            cm.append(LOW_CM + int(t * (2 * STEP_CM - 1)))
    cm[n * n - 1] = LOW_CM + 5 * STEP_CM
    assert lib.om_terrain_set_heights(w, (ctypes.c_int32 * len(cm))(*cm), n, n) == 1
    _reg(lib, w, SHOOTER, FULL, 10.0, 0.5, RANGE, 0.0, 600.0, kind=WALKING)
    _reg(lib, w, TARGET, FULL, 1.0, 1.0, 10.0, 0.0, 10.0, kind=WALKING)
    return w


def test_R_098_02_i11nl_a_unit_that_sees_an_enemy_below_it_inside_range_can_shoot_it(lib, world_factory):
    """R-098-02 'the shot is blocked exactly as vision is' with R-087-10: no obstacle stands on the line (the scene has none), the shooter (range 300)
    on the hill (layer 1, x 1000) sees the enemy on the flat below (layer 0, x 1200, 200 wu away, 208.8 through the air), so it can shoot it and does.
    Premises dumped from the built tree: layers (1, 0); om_unit_can_see(a, b) = 1; om_combat_can_shoot(a, b) = 0 and (b, a) = 0 at 150 wu and every
    distance up to 340 wu tried (it is true at 100 wu, where the target stands on the ramp's layer 1). This is the sweep's I11nl case (L-0061 ticks 59 to
    61, Wardens 2 and 26, 338 to 348 wu) reproduced in four lines: not a range effect, since can_shoot has no range test. Red today."""
    w = _hill_world(lib, world_factory)
    a = spawn(lib, w, SHOOTER, 0, 1000, 2000, 1)
    b = spawn(lib, w, TARGET, 1, 1200, 2000, 0)
    assert (lib.om_unit_get_layer(w, a), lib.om_unit_get_layer(w, b)) == (1, 0), "premise: layers"
    assert lib.om_unit_can_see(w, a, b), "premise: the shooter sees the enemy below it"
    assert lib.om_combat_can_shoot(w, a, b), "sees the enemy (%d) but om_combat_can_shoot is false; sight says clear, fire says blocked" % lib.om_unit_can_see(w, a, b)
    step(lib, w, TICKS)
    assert hp(lib, w, b) < FULL, "no shot landed at 208.8 wu in %d ticks" % TICKS


def test_R_098_02_i11nl_control_a_unit_on_the_same_layer_as_the_enemy_shoots_it(lib, world_factory):
    """R-098-02 control (green today and after): the same hill, the enemy on the hill beside the shooter (same layer, 200 wu): it shoots."""
    w = _hill_world(lib, world_factory)
    a = spawn(lib, w, SHOOTER, 0, 600, 2000, 1)
    b = spawn(lib, w, TARGET, 1, 800, 2000, 1)
    assert lib.om_combat_can_shoot(w, a, b), "scene broken: no shot on one layer"
    step(lib, w, TICKS)
    assert hp(lib, w, b) < FULL
