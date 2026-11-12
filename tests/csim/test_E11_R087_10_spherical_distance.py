# Rule pins: R-087-10, R-087-05, R-005-09, R-084-03, R-098-02, R-190-04
"""E-11 R-087-10 (engine rule fixes 2026-11-08, F7; narrowed 2026-11-11): weapon reach is spherical, layer height included; sight and the leash are horizontal.

DRAFT-slant-ground-only (Round 2, T8, 2026-11-11; a provisional reading pending the owner's ruling, not rule text): the slant is used only when BOTH units are
walking units standing on ground bands (the hill the owner was looking at). When either unit is a flyer, weapon reach is the horizontal distance and the reach
table's range multipliers, as before Round 2. Reason: the air layers' band floors are about 920 wu apart (measured band heights [60.11, 979.86, 1899.61, 2819.36,
3739.11]), so by slant no flying unit could ever reach a unit on another air layer; tests/skilllab/ground/test_slope_top_variants.py::
test_the_flyer_fight_still_ends_by_elimination (units 6 wu apart horizontally on layers 2 and 3, ranges 200 and 300) ran to the 12,000 tick cap instead of ending at tick 3059.
Each test below that depends on the unit kind says so in its docstring. Unit kinds of the tests that existed before T8: the flat-plane scene S (`_world`) registers
FLYERS (om_roster_set_movement_kind 0, the default of `_reg`); `_hill_world`, `_sight_scene` and the leash scenes register WALKERS (kind 1).

Rule words proved (docs/bible/epics/E-11-units-and-combat.md, as ruled 2026-11-11, DEC-slant-is-weapon-reach-2026-11-11):
  R-087-10  "Given a test of whether a weapon reaches (a unit's attack range to its target, an area attack's radius to each unit it would hit), When it is
             evaluated, Then the distance is spherical: the horizontal distance and the height difference between the two units' layers (E-17 R-190-04 band
             heights) taken together (Westley, 2026-11-08: "include layer height, range should be spherical"). Sight is not measured this way: a sensor radius
             stays horizontal, so that high ground sees as far along the ground as low ground and further by its height rules (E-01 R-005-09; Westley on
             H-088: "vantage sees further"), and the leash (R-087-05) stays the horizontal distance the unit itself has walked from its anchor (...)."
  E-01 R-005-09  "Given a ground era, an observer and an enemy within the observer's sensor radius, When the enemy is on a lower layer than the observer,
             Then the enemy is visible (high ground sees down); and When the enemy is on a higher layer, Then it is never visible by passive detection at any
             distance (...)."
  R-087-05  "... if the unit itself pursues farther from the anchor than its own type's sensor radius it drops the target and resumes its attack-move or
             holds (R-096-03). The leash measures the pursuer's own distance from its anchor, never the target's (...)."
  R-098-02  "Given a blocked cell (R-097-01) or a cover obstacle between them on the layers involved, When it fires, Then the shot is blocked
             exactly as vision is": a line that sight sees along and that crosses no obstacle is not blocked for fire (the I11nl case below).
  E-17 R-190-04  "the five band heights are output, and E-01 R-010-01 reads them to draw a unit at its layer's height."
Spec: docs/northstar/plans/engine-rules-2026-11-08/spec.md "F7" (its sensor-radius and leash parts are withdrawn by the ruling above). Evidence:
docs/reports/2026-11-07-rule-enforcement/appendix-c-invariant-sweep.md I11nl.

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

from conftest import OMFeature, OMTacParam
from test_PP_unit_support import attack_move, hp, pos, spawn, step, target

CANVAS = 4000.0
LOW_CM, STEP_CM = 7000, 6000
SEER, SHOOTER, TARGET, SPLASH, PASSIVE, WALKER_T, WALKER_S = 20, 21, 22, 23, 24, 25, 26
WALKING = 1
TICKS = 60            # DRAFT-f7-ticks
FULL = 1000.0
RANGE = 300.0
AREA = 150.0         # the walking splasher's area radius in the area tests
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

def test_R_087_10_attack_range_two_walkers_on_a_hill_outside_range_by_slant_do_not_fire(lib, world_factory):
    """R-087-10 'attack range ... the distance is spherical' (DRAFT-slant-ground-only: both units are walkers on ground bands, the hill case): a walking shooter
    (range 300) on the hill (layer 1, x 950) and a walking target on the flat below (layer 0, x 1247), 297 wu apart on the ground (inside 300 flat) and 303.0 through
    the air (60 wu of layer height): it does not fire in 60 ticks. Neither can walk (speed 0). Premises dumped from the built tree (2026-11-11): layers (1, 0);
    band heights [70.0, 130.0, ...]; both types movement kind 1 (walking); om_unit_can_see(a, b) = 1 (sensor 600). GREEN today and after: the walker pair is the
    case the slant exists for. (Rewritten 2026-11-11, Test-defect: it was a pair of FLYERS on a flat plane, which the provisional rule measures flat.)"""
    w = _hill_world(lib, world_factory)
    a = spawn(lib, w, SHOOTER, 0, 950, 2000, 1)
    b = spawn(lib, w, TARGET, 1, 950 + 297, 2000, 0)
    assert (lib.om_unit_get_layer(w, a), lib.om_unit_get_layer(w, b)) == (1, 0), "premise: layers"
    assert [lib.om_unit_profile_movement_kind(w, SHOOTER), lib.om_unit_profile_movement_kind(w, TARGET)] == [WALKING, WALKING], "premise: both walkers"
    h = _heights(lib, w)
    assert h[:2] == [70.0, 130.0], "band heights %s, the scene assumes 70 and 130" % h
    slant = _slant(297.0, h, 1, 0)
    assert 297.0 <= RANGE < slant, "premise: flat 297 inside %.0f, slant %.1f outside" % (RANGE, slant)
    assert lib.om_unit_can_see(w, a, b), "premise: the shooter sees the target"
    step(lib, w, TICKS)
    assert hp(lib, w, b) == FULL, "a walker fired at a walker %.1f wu away through the air (range %.0f), target hp %.1f" % (slant, RANGE, hp(lib, w, b))


def test_R_087_10_attack_range_control_two_walkers_on_a_hill_inside_range_by_slant_fire(lib, world_factory):
    """R-087-10 control for the walker test above (green today and after; DRAFT-slant-ground-only): the same walking pair 290 wu apart on the ground and 296.2 through the air,
    both inside 300: it fires. Proves the hill scene fires, so the test above is green for the metric and not for a muted pair."""
    w = _hill_world(lib, world_factory)
    a = spawn(lib, w, SHOOTER, 0, 950, 2000, 1)
    b = spawn(lib, w, TARGET, 1, 950 + 290, 2000, 0)
    assert (lib.om_unit_get_layer(w, a), lib.om_unit_get_layer(w, b)) == (1, 0), "premise: layers"
    step(lib, w, TICKS)
    assert hp(lib, w, b) < FULL, "scene broken: no shot landed at 290 wu between walkers on a hill"


def test_R_087_10_attack_range_control_a_unit_inside_range_by_slant_fires(lib, world_factory):
    """R-087-10 control (green today and after; scene S, FLYERS): 290 wu on the ground, 296.2 through the air, both inside 300: the same pair fires. Proves the
    scene fires, so the walker test above is green for the metric and not for a muted shooter."""
    w = _world(lib, world_factory)
    _premise(lib, w, 290.0, RANGE, inside_flat=True, inside_slant=True)
    a = spawn(lib, w, SHOOTER, 0, 1000, 2000, 1)
    b = spawn(lib, w, TARGET, 1, 1290, 2000, 0)
    step(lib, w, TICKS)
    assert hp(lib, w, b) < FULL, "scene broken: no shot landed at 290 wu"


def test_R_087_10_attack_range_control_the_same_layer_is_measured_flat(lib, world_factory):
    """R-087-10 control (green today and after; scene S, FLYERS): two units on the SAME layer have no height difference; 299 wu is inside 300 and fires."""
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


# ------------------------------------------------------------------ DRAFT-slant-ground-only: a flyer is measured flat

AIR_STEP_CM = 92000   # a layer is 920 wu high: the measured air band spacing (band heights [60.11, 979.86, 1899.61, ...]), here [70, 990, 1910, ...]


def _air_world(lib, wf):
    """Scene S with the air layers' spacing: the flat plane of `_plane`, but the corner cell sets a 920 wu band step. Flyers (kind 0) SEER, SHOOTER (range 300, sensor 600),
    TARGET; a walker twin of TARGET (WALKER_T) for the flyer-and-walker pair. All speed 0."""
    w = wf(n_regions=1)
    lib.om_world_set_feature(w, OMFeature.TACTICAL, 1)
    assert lib.om_map_set_canvas(w, CANVAS, CANVAS) == 0
    _plane(lib, w, step_cm=AIR_STEP_CM)
    lib.om_set_era_kind(w, 1)
    _reg(lib, w, SHOOTER, FULL, 10.0, 0.5, RANGE, 0.0, 600.0)
    _reg(lib, w, TARGET, FULL, 1.0, 1.0, 10.0, 0.0, 10.0)
    _reg(lib, w, WALKER_T, FULL, 1.0, 1.0, 10.0, 0.0, 10.0, kind=WALKING)
    _reg(lib, w, WALKER_S, FULL, 10.0, 0.5, RANGE, 0.0, 600.0, kind=WALKING)
    return w


def _air_premise(lib, w, shooter, target, flat, la, lb):
    """Dump and assert the premises of an air scene: band heights, the cross-layer range multipliers, the shooter type's reach, both movement kinds, flat and slant."""
    h = _heights(lib, w)
    assert h[0] == 70.0 and h[1] - h[0] == 920.0, "band heights %s, the scene assumes 70 and 920 apart" % h
    up, down = ctypes.c_uint32(), ctypes.c_uint32()
    assert lib.om_unit_profile_reach(w, SHOOTER if shooter is None else shooter, ctypes.byref(up), ctypes.byref(down)) == 0
    assert (up.value, down.value) == (1, 1), "reach table (up, down) %d, %d: the pair must be allowed one layer apart" % (up.value, down.value)
    mult = [lib.om_tactical_get_param(w, OMTacParam.RANGE_UP_1), lib.om_tactical_get_param(w, OMTacParam.RANGE_DOWN_1)]
    assert mult == [1.0, 1.0], "range multipliers %s: the metric is the type's plain range" % mult
    s = _slant(flat, h, la, lb)
    return s


def test_R_087_10_draft_slant_ground_only_two_flyers_on_adjacent_air_layers_fire_by_horizontal_distance(lib, world_factory):
    """R-087-10 'attack range ... the distance is spherical' read DRAFT-slant-ground-only (a flyer is measured flat): a flying shooter (range 300) on air layer 2 and a
    flying target on air layer 3, 250 wu apart horizontally (inside 300) and about 953 wu through the air (920 wu of layer height): it fires. Premises dumped from the
    built tree (2026-11-11): band heights [70.0, 990.0, 1910.0, ...] (920 apart, as the measured air bands); reach (up 1, down 1) so one layer apart is allowed;
    OM_TP_RANGE_UP_1 = OM_TP_RANGE_DOWN_1 = 1.0; both types movement kind 0 (flying). Red today: the range test is spherical for every unit, the target is 953 wu
    away and nobody fires. The whole-run proof is test_the_flyer_fight_still_ends_by_elimination (tests/skilllab/ground/test_slope_top_variants.py)."""
    w = _air_world(lib, world_factory)
    slant = _air_premise(lib, w, SHOOTER, TARGET, 250.0, 2, 3)
    assert slant > 900.0 > 0 and 250.0 <= RANGE, "premise: flat 250 inside %.0f, slant %.1f far outside" % (RANGE, slant)
    a = spawn(lib, w, SHOOTER, 0, 1000, 2000, 2)
    b = spawn(lib, w, TARGET, 1, 1250, 2000, 3)
    assert (lib.om_unit_get_layer(w, a), lib.om_unit_get_layer(w, b)) == (2, 3), "premise: layers"
    assert [lib.om_unit_profile_movement_kind(w, SHOOTER), lib.om_unit_profile_movement_kind(w, TARGET)] == [0, 0], "premise: both flyers"
    step(lib, w, TICKS)
    assert hp(lib, w, b) < FULL, "two flyers on adjacent air layers, %.0f wu apart horizontally (range %.0f), %.1f through the air: no shot landed in %d ticks" % (250.0, RANGE, slant, TICKS)


def test_R_087_10_draft_slant_ground_only_two_flyers_on_adjacent_air_layers_do_not_fire_beyond_the_horizontal_range(lib, world_factory):
    """R-087-10 control for the test above (green today and after; DRAFT-slant-ground-only): the same flyers 350 wu apart horizontally, outside range 300 flat as well as
    by slant: no shot in 60 ticks. Proves the flat measure still bounds fire, so the test above is red for the metric and not for a shooter that fires at any distance."""
    w = _air_world(lib, world_factory)
    _air_premise(lib, w, SHOOTER, TARGET, 350.0, 2, 3)
    a = spawn(lib, w, SHOOTER, 0, 1000, 2000, 2)
    b = spawn(lib, w, TARGET, 1, 1350, 2000, 3)
    step(lib, w, TICKS)
    assert hp(lib, w, b) == FULL, "fired at a flyer 350 wu away horizontally (range %.0f), target hp %.1f" % (RANGE, hp(lib, w, b))


def test_R_087_10_draft_slant_ground_only_control_two_flyers_on_one_air_layer_fire_at_250_wu(lib, world_factory):
    """R-087-10 control for the air tests (green today and after; DRAFT-slant-ground-only): in the same air world (band heights 920 apart) the same flyers 250 wu apart on ONE
    layer (no height difference) fire. Proves the air scene fires, so the cross-layer tests are red for the metric and not for a muted pair."""
    w = _air_world(lib, world_factory)
    _air_premise(lib, w, SHOOTER, TARGET, 250.0, 2, 2)
    a = spawn(lib, w, SHOOTER, 0, 1000, 2000, 2)
    b = spawn(lib, w, TARGET, 1, 1250, 2000, 2)
    step(lib, w, TICKS)
    assert hp(lib, w, b) < FULL, "scene broken: no shot landed at 250 wu on one air layer"


def test_R_087_10_draft_slant_ground_only_a_flyer_above_a_walker_fires_by_horizontal_distance(lib, world_factory):
    """R-087-10 read DRAFT-slant-ground-only (when either unit is a flyer the reach is measured flat): a flying shooter (range 300) on layer 1 and a walking target on the
    ground (layer 0), 250 wu apart horizontally and about 953 wu through the air (920 wu of layer height): it fires. Premises dumped from the built tree (2026-11-11):
    band heights [70.0, 990.0, ...]; reach (up 1, down 1) so the flyer reaches one layer down; OM_TP_RANGE_UP_1 = OM_TP_RANGE_DOWN_1 = 1.0; shooter movement kind 0
    (flying), target kind 1 (walking); om_unit_can_see(shooter, target) = 1 (sensor 600). Red today: spherical for every unit, the target is 953 wu away."""
    w = _air_world(lib, world_factory)
    slant = _air_premise(lib, w, SHOOTER, WALKER_T, 250.0, 1, 0)
    a = spawn(lib, w, SHOOTER, 0, 1000, 2000, 1)
    b = spawn(lib, w, WALKER_T, 1, 1250, 2000, 0)
    assert (lib.om_unit_get_layer(w, a), lib.om_unit_get_layer(w, b)) == (1, 0), "premise: layers"
    assert [lib.om_unit_profile_movement_kind(w, SHOOTER), lib.om_unit_profile_movement_kind(w, WALKER_T)] == [0, WALKING], "premise: flyer above walker"
    assert lib.om_unit_can_see(w, a, b), "premise: the flyer sees the walker below it"
    step(lib, w, TICKS)
    assert hp(lib, w, b) < FULL, "a flyer 250 wu horizontally from a walker below it (range %.0f, %.1f through the air): no shot landed in %d ticks" % (RANGE, slant, TICKS)


def test_R_087_10_draft_slant_ground_only_a_walker_under_a_flyer_fires_by_horizontal_distance(lib, world_factory):
    """R-087-10 read DRAFT-slant-ground-only, the other direction (the rule says 'either unit'): a walking shooter (range 300) on the ground (layer 0) and a flying target
    on layer 1 above it, 250 wu apart horizontally and 953 through the air: it fires. Premises as the test above with the kinds swapped (shooter walking, target flying;
    reach (1, 1) of the walking type). Red today for the same reason. (Not in the brief's list: added because the provisional rule is worded 'either unit'.)"""
    w = _air_world(lib, world_factory)
    slant = _air_premise(lib, w, WALKER_S, TARGET, 250.0, 0, 1)
    a = spawn(lib, w, WALKER_S, 0, 1000, 2000, 0)
    b = spawn(lib, w, TARGET, 1, 1250, 2000, 1)
    assert (lib.om_unit_get_layer(w, a), lib.om_unit_get_layer(w, b)) == (0, 1), "premise: layers"
    assert [lib.om_unit_profile_movement_kind(w, WALKER_S), lib.om_unit_profile_movement_kind(w, TARGET)] == [WALKING, 0], "premise: walker under flyer"
    assert lib.om_unit_can_see(w, a, b), "premise: the walker sees the flyer above it"
    step(lib, w, TICKS)
    assert hp(lib, w, b) < FULL, "a walker 250 wu horizontally from a flyer above it (range %.0f, %.1f through the air): no shot landed in %d ticks" % (RANGE, slant, TICKS)


# ------------------------------------------------------------------ sensor radius: horizontal (R-005-09)

def _sight_scene(lib, wf, dx):
    """The shipped configuration (walkers, a hill, ground era, sight on, as `_hill_world` builds it): an observer (SEER, sensor 300, speed 0) on the hill
    (layer 1, x 950) and an enemy (TARGET) on the flat below (layer 0) `dx` wu east on the same row. Layer 1 stands 60 wu above layer 0 here, so a
    shot at 297 wu on the ground is 303.0 through the air: outside 300 by slant, inside by the ground."""
    w = _hill_world(lib, wf)
    _reg(lib, w, SEER, FULL, 1.0, 1.0, 100.0, 0.0, RANGE, kind=WALKING)
    a = spawn(lib, w, SEER, 0, 950, 2000, 1)
    b = spawn(lib, w, TARGET, 1, 950 + dx, 2000, 0)
    assert (lib.om_unit_get_layer(w, a), lib.om_unit_get_layer(w, b)) == (1, 0), "premise: layers"
    h = _heights(lib, w)
    assert h[:2] == [70.0, 130.0], "band heights %s, the scene assumes 70 and 130" % h
    return w, a, b


def test_R_087_10_sensor_radius_a_unit_on_a_hill_sees_an_enemy_below_at_its_full_horizontal_sensor_radius(lib, world_factory):
    """R-087-10 'a sensor radius stays horizontal' with E-01 R-005-09 'high ground sees down': an observer (sensor radius 300) on the hill (layer 1) and an
    enemy on the flat below (layer 0), 297 wu apart on the ground (303.0 through the air, 60 wu of layer height): it sees the enemy. Premises dumped
    from the built tree (2026-11-11): layers (1, 0); band heights [70.0, 130.0, ...]; om_unit_can_see is true at 250, 280 and 297 wu on the ground by the
    horizontal rule (measured on the Round 1 tip: true to 299, false at 301). Red when the sensor radius is measured through the air (the Architect's
    2026-11-08 extension, withdrawn 2026-11-11), which cuts the sight of a unit on a hill to 294.0 wu on the ground."""
    w, a, b = _sight_scene(lib, world_factory, 297.0)
    slant = _slant(297.0, _heights(lib, w), 1, 0)
    assert slant > RANGE > 297.0, "premise: slant %.1f must be over the sensor radius %.0f and the ground distance under it" % (slant, RANGE)
    assert lib.om_unit_can_see(w, a, b), "does not see an enemy %.1f wu away on the ground below it (sensor radius %.0f; %.1f through the air)" % (297.0, RANGE, slant)


def test_R_087_10_sensor_radius_control_a_unit_on_a_hill_sees_an_enemy_below_well_inside_the_radius(lib, world_factory):
    """R-087-10 control (green today and after): the same pair 250 wu apart on the ground (257.0 through the air, inside 300 either way): it sees the
    enemy. Proves the scene sees at all, so the test above is red for the metric and not for a blind observer."""
    w, a, b = _sight_scene(lib, world_factory, 250.0)
    assert lib.om_unit_can_see(w, a, b), "scene broken: no sight at 250 wu"


def test_R_087_10_sensor_radius_control_a_unit_on_a_hill_does_not_see_an_enemy_below_beyond_the_horizontal_radius(lib, world_factory):
    """R-087-10 / R-005-09 control (green today and after): the same pair 303 wu apart on the ground, beyond the sensor radius 300 whatever the layers:
    it does not see the enemy ('an enemy within the observer's sensor radius'). Proves the radius still bounds sight, so the test above is not red
    for a metric that sees to any distance."""
    w, a, b = _sight_scene(lib, world_factory, 303.0)
    assert not lib.om_unit_can_see(w, a, b), "sees an enemy 303 wu away on the ground, beyond its sensor radius %.0f" % RANGE


# ------------------------------------------------------------------ area radius

def _cliff_world(lib, wf):
    """A walker world for the area radius (DRAFT-slant-ground-only: walkers on ground bands): a hill (layer 1) west of x 1200 that falls in one cell to a flat plane (layer 0),
    60 wu lower (the 60 wu band step of `_plane`, corner cell as `_hill_world`). Walker types SPLASH (range 600, area radius 150, speed 0), PASSIVE (speed 0). The cell beside the cliff is too steep to stand on (om_unit_spawn returns 0 at x 1170 to 1210, measured 2026-11-11), so the pairs below keep 50 wu clear of x 1200 on both sides."""
    w = wf(n_regions=1)
    lib.om_world_set_feature(w, OMFeature.TACTICAL, 1)
    assert lib.om_map_set_canvas(w, CANVAS, CANVAS) == 0
    assert lib.om_terrain_generate(w, 7, CANVAS, CANVAS) == 0
    lib.om_set_era_kind(w, 1)
    n = 40
    cm = [LOW_CM + (2 * STEP_CM - 1 if cx < 12 else 0) for _ in range(n) for cx in range(n)]
    cm[n * n - 1] = LOW_CM + 5 * STEP_CM
    assert lib.om_terrain_set_heights(w, (ctypes.c_int32 * len(cm))(*cm), n, n) == 1
    _reg(lib, w, SPLASH, FULL, 10.0, 0.5, 600.0, 0.0, 600.0, aoe=AREA, kind=WALKING)
    _reg(lib, w, PASSIVE, FULL, 1.0, 1.0, 10.0, 0.0, 10.0, kind=WALKING)
    return w


def _splash_scene(lib, wf):
    """A walking splasher (range 600, area radius 150, speed 0) on the flat (layer 0, x 1700) ordered at B (layer 0, x 1250); C 140 wu from B on the ground and on the hill (layer 1;
    152.3 through the air: outside 150), D 110 wu from B and on the hill (125.3: inside). Premises dumped from the built tree (2026-11-11): band heights [70.0, 130.0, ...]; all four
    units movement kind 1 (walking); layers as listed. Returns (world, B, C, D) after TICKS ticks."""
    w = _cliff_world(lib, wf)
    h = _heights(lib, w)
    assert h[:2] == [70.0, 130.0], "band heights %s, the scene assumes 70 and 130" % h
    x = spawn(lib, w, SPLASH, 0, 1700, 2000, 0)
    b = spawn(lib, w, PASSIVE, 1, 1250, 2000, 0)
    c = spawn(lib, w, PASSIVE, 1, 1120, 2000 + math.sqrt(140.0 ** 2 - 130.0 ** 2), 1)
    d = spawn(lib, w, PASSIVE, 1, 1140, 2000, 1)
    assert [lib.om_unit_get_layer(w, u) for u in (x, b, c, d)] == [0, 0, 1, 1], "premise: layers"
    assert {lib.om_unit_profile_movement_kind(w, t) for t in (SPLASH, PASSIVE)} == {WALKING}, "premise: walkers"
    flat_c, flat_d = math.hypot(1250 - 1120, 2000 + math.sqrt(140.0 ** 2 - 130.0 ** 2) - 2000), 1250 - 1140
    assert abs(flat_c - 140.0) < 1e-9 and flat_d == 110.0, "premise: C %.1f and D %.1f wu from B on the ground" % (flat_c, flat_d)
    assert flat_c < AREA < _slant(flat_c, h, 0, 1) and _slant(flat_d, h, 0, 1) < AREA, "premise: C inside the area flat and outside by slant, D inside by both"
    lib.om_command_attack_target(w, (ctypes.c_uint32 * 1)(x), 1, b)
    step(lib, w, TICKS)
    return w, b, c, d


def test_R_087_10_area_radius_a_walker_outside_the_area_by_slant_is_not_hurt(lib, world_factory):
    """R-087-10 'area radius' (R-084-03), DRAFT-slant-ground-only (splasher and victims are walkers on ground bands): the splash around the target (area radius 150) must not
    hurt a walking enemy that is 140 wu from it on the ground but on a layer 60 wu higher (152.3 away through the air). GREEN today and after. (Rewritten 2026-11-11, Test-defect:
    the units were flyers on a flat plane; the provisional rule measures a flyer flat, so the same geometry for flyers is a different question, see the gap in the report.)"""
    w, b, c, d = _splash_scene(lib, world_factory)
    assert hp(lib, w, b) < FULL, "scene broken: the splasher never hit its ordered target"
    assert hp(lib, w, c) == FULL, "hurt by a splash whose centre is 152.3 wu away through the air (area radius 150), hp %.1f" % hp(lib, w, c)


def test_R_087_10_area_radius_control_a_walker_inside_the_area_by_slant_is_hurt(lib, world_factory):
    """R-087-10 control (green today and after; DRAFT-slant-ground-only): the walking enemy 110 wu from the target on the ground and 125.3 through the air is inside 150 and is hurt,
    so the splash reaches across layers in this scene and the test above is green for the metric."""
    w, b, c, d = _splash_scene(lib, world_factory)
    assert hp(lib, w, d) < FULL, "scene broken: the splash did not reach a layer-1 enemy 125.3 wu from its centre"


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


def test_R_087_10_leash_a_pursuer_drops_its_target_at_the_horizontal_distance_from_its_anchor_whatever_the_layers(lib, world_factory):
    """R-087-10 'the leash (R-087-05) stays the horizontal distance the unit itself has walked from its anchor' and R-087-05 'the leash measures the pursuer's
    own distance from its anchor': P anchors on the plateau (layer 1, 170 wu) and chases a fleeing enemy down onto the low plane (layer 0, 70 wu): 100 wu
    lower. With a leash of 310 (its sensor radius) the target is dropped once the ground distance from the anchor passes 310, within one step (5.5 wu)
    of it: not at the 293.4 wu that a leash through the air would give. Premises dumped from the built tree (2026-11-11): band heights [70.0, 170.0, ...];
    on a flat plane (the control below) the same chase drops at 310 to 315. Red when the leash is measured through the air."""
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
    sph = math.sqrt(LEASH ** 2 - DZ_LEASH ** 2)
    assert LEASH - 6.0 <= drop_h <= LEASH + 6.0, "dropped at %.1f wu of ground distance from its anchor; the horizontal leash breaks at %.0f (through the air it would break at %.1f)" % (drop_h, LEASH, sph)


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
