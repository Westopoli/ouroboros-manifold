# spec: docs/northstar/plans/2026-10-14-skill-lab-rev2-spec.md::Contract::The count + Pieces::L1; rulings 5, 8, 10
"""The firing count (scripts/skilllab/firing.py) on a fake engine: no compiler, no library.

Rev 2 (LAB-REV2-L1) replaces harness-spec clause 10. The seam, fixed by the spec's "Lab data contract":

  firing.count_able(engine, w, units0, units1, arc_deg)    -> (int, int)
  firing.count_weighted(engine, w, units0, units1, arc_deg) -> (float, float)
  firing.states(engine, w, units0, units1, arc_deg)         -> [(unit, code), ...]
  firing.parity(engine, w, units0, units1, arc_deg)         -> [unit, ...]   ([] when E0 is absent)

There is no `ranges` argument and no `alive` set any more: a living unit is able when it passes the five gates of
om_combat_can_engage against some living enemy, composed from public queries until E0 lands (spec, "The count"):
reach of the shooter's type at the layer offset, the side's visible set (`visible_enemies`), attack range times the
offset multiplier (OM_TP_RANGE_UP_k / OM_TP_RANGE_DOWN_k through `get_param`), the firing arc (`unit_facing`), and
`can_shoot`. The effective layer is what `unit_layer` returns, with no special case for a unit in transition.

Retired here, with the ruling:
  - test_ac24_different_layers_do_not_count (AC 24 / AC 10 "its own layer only"): retired by R-008-02 and the landed
    cascade (R-164-01 reach table); replaced by the reach tests below, which keep its geometry as the reach (0, 0) case.
  - test_ac10_a_living_unit_missing_from_ranges_raises_keyerror: the `ranges` argument is gone (spec seam).
  - test_firing_alive.py, test_firing_weighted_target.py, test_firing_weighted.py (count_able_weighted, unit_weight, the
    `alive` set, the engine-target-only weighted rule), test_states.py (unit_states strings, order_ends) and their fakes,
    integration/test_weighted_reads_engine_real.py, test_firing_weighted_real.py, test_states_real.py: deleted with the
    L1 seam (ruling 5: the weight is the category multiplier, not damage over interval; the code is a can_engage reason,
    not a string state). Kept: the Engine.profile_reach binding tests (bottom of this file). Their fight-level halves
    (no Setup.weighted, weighted_unit_seconds always populated, Setup.states giving (tick, unit, code)) are re-stated
    for L2 in test_fight_wiring_firing.py and integration/test_fight_firing_real.py.

Engine methods this file fixes for the fake (and so for the builder; the spec's seam names neither):
  unit_type(w, u) -> type id               om_unit_get_unit_type; the count reads the shooter's type, category and range
  category_multiplier(w, a_cat, t_cat)     om_tactical_category_multiplier -> float
  transition_progress(w, u) -> float       om_unit_transition_progress
  can_engage(w, a, b) -> int               om_combat_can_engage; -1 is the "not built" sentinel (E0 stub or no symbol)
plus the Engine methods that already exist: unit_alive, unit_pos, unit_layer, unit_facing, unit_target, type_stats,
profile_reach, visible_enemies(w, side, enemy_ids), param_id, get_param, can_shoot.

Named drafts used here: none of this file's numbers is a threshold; DRAFT-firing-arc-deg 120 appears as the arc width
of the arc tests only because ruling 8 names it.
"""
import ctypes
import inspect
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for _p in (ROOT, Path(__file__).resolve().parent):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import pytest  # noqa: E402
from fakes import FakeEngine, default_stats  # noqa: E402
from scripts.skilllab import engine as engine_mod  # noqa: E402
from scripts.skilllab import firing  # noqa: E402

ARC_OFF = 360.0
ARC_DRAFT = 120.0     # DRAFT-firing-arc-deg (ruling 8)
CAT = {"Raider": 0, "Vanguard": 1, "Bombard": 2}           # the real engine's categories for these three types
DEFAULT_PARAMS = {"OM_TP_TARGET_BY_SIGHT": 1.0, "OM_TP_VISION_UP_1": 0.5, "OM_TP_VISION_DOWN_1": 0.5}


def mult(a_cat, t_cat):
    """Nine distinct category multipliers, so a wrong pair is never equal to the right one."""
    return round(1.0 + 0.25 * a_cat + 0.05 * t_cat, 6)


class CountFake(FakeEngine):
    """FakeEngine plus the queries the rev 2 count composes. Every added method logs like the others."""

    def __init__(self, reach=None, params=None, sees=None, engage_fn=None, categories=True, **kw):
        stats = kw.pop("stats", None) or {}
        merged = {}
        for name, st in default_stats().items():
            merged[name] = dict(st, category=CAT.get(name, 1)) if categories else dict(st)
        for name, st in stats.items():
            merged[name] = dict(merged.get(name, default_stats()[name]), **st)
        super().__init__(stats=merged, **kw)
        self.reach_by_type = dict(reach or {})
        self.params = dict(DEFAULT_PARAMS, **(params or {}))
        self.sees = sees or (lambda side, target: True)
        self.engage_fn = engage_fn
        self.facings = {}
        self.targets = {}

    def unit_type(self, w, u):
        self.calls.append(("unit_type", w, u))
        return self.units[u]["type"]

    def unit_facing(self, w, u):
        self.calls.append(("unit_facing", w, u))
        return self.facings.get(u, 0.0)

    def unit_target(self, w, u):
        self.calls.append(("unit_target", w, u))
        return self.targets.get(u, 0)

    def unit_destination(self, w, u):
        self.calls.append(("unit_destination", w, u))
        return None

    def profile_reach(self, w, type_id):
        self.calls.append(("profile_reach", w, type_id))
        return tuple(self.reach_by_type.get(type_id, (0, 0)))

    def visible_enemies(self, w, side, enemy_ids):
        self.calls.append(("visible_enemies", w, side, list(enemy_ids)))
        return {e for e in enemy_ids if self.sees(side, e)}

    def param_id(self, name):
        self.calls.append(("param_id", name))
        return name

    def get_param(self, w, param):
        self.calls.append(("get_param", w, param))
        return float(self.params.get(param, 1.0))

    def category_multiplier(self, w, attacker_category, target_category):
        self.calls.append(("category_multiplier", w, attacker_category, target_category))
        return mult(attacker_category, target_category)

    def can_engage(self, w, a, b):
        self.calls.append(("can_engage", w, a, b))
        return -1 if self.engage_fn is None else int(self.engage_fn(a, b))


def row_world(enemy_x=140.0, enemy_layer=0, reach=None, **kw):
    """Three side-0 Vanguards in a row at x = 0, 50, 100 and one enemy Vanguard at (enemy_x, 0). Vanguard range 100.
    Default enemy_x = 140: distances 140, 90, 40 -> exactly two of side 0 within reach 100; ids a = 1, 2, 3, e = 4."""
    fake = CountFake(reach=reach, **kw)
    w = fake.new_world(0)
    vg = fake.type_id("Vanguard")
    a = [fake.spawn(w, vg, 0, x, 0.0, 0) for x in (0.0, 50.0, 100.0)]
    e = fake.spawn(w, vg, 1, enemy_x, 0.0, enemy_layer)
    return fake, w, a, e


def vg_reach(up, down):
    return {FakeEngine().type_id("Vanguard"): (up, down)}


# ---------------------------------------------------------------- the seam, exactly (spec "Lab data contract")

@pytest.mark.parametrize("name", ["count_able", "count_weighted", "states", "parity"])
def test_seam_signature_is_engine_w_units0_units1_arc_deg(name):
    """Spec seam: firing.<name>(engine, w, units0, units1, arc_deg); no ranges, no alive set."""
    fn = getattr(firing, name, None)
    assert fn is not None, "firing.%s is missing" % name
    assert list(inspect.signature(fn).parameters) == ["engine", "w", "units0", "units1", "arc_deg"]


# ---------------------------------------------------------------- same-layer behaviour kept (AC 24 / AC 10)

def test_ac24_three_in_a_row_one_enemy_two_in_reach_reads_2_and_1():
    """AC 24 (positive control, same layer, reach (0, 0)): hand-built case reads able0 = 2, able1 = 1."""
    fake, w, a, e = row_world()
    assert firing.count_able(fake, w, a, [e], ARC_OFF) == (2, 1)


def test_ac24_positive_and_negative_control_on_distance():
    """AC 24 / AC 10: enemy out of every reach reads 0; one unit in reach reads 1; both are real counts."""
    fake, w, a, e = row_world(enemy_x=400.0)
    assert firing.count_able(fake, w, a, [e], ARC_OFF) == (0, 0)
    fake, w, a, e = row_world(enemy_x=170.0)   # distances 170, 120, 70
    assert firing.count_able(fake, w, a, [e], ARC_OFF) == (1, 1)


def test_ac24_blocker_on_one_pair_reads_one_fewer_for_that_side():
    """AC 24: a pair that cannot shoot (can_shoot false) costs the shooter its count; the direction is shooter -> enemy."""
    fake, w, a, e = row_world()
    fake.block(a[1], e, both=True)
    assert firing.count_able(fake, w, a, [e], ARC_OFF) == (1, 1)
    fake, w, a, e = row_world()
    fake.block(e, a[1]); fake.block(e, a[2])   # the enemy cannot shoot either unit in its reach
    assert firing.count_able(fake, w, a, [e], ARC_OFF) == (2, 0)
    fake, w, a, e = row_world()
    fake.block(a[1], e); fake.block(a[2], e)   # side 0 cannot shoot; the enemy still can
    assert firing.count_able(fake, w, a, [e], ARC_OFF) == (0, 1)


def test_ac24_blocked_pair_does_not_hide_a_second_open_target():
    """AC 10: able means SOME living enemy is open; one blocked enemy of two does not remove the unit; a unit counts once."""
    fake, w, a, e1 = row_world()
    e2 = fake.spawn(w, fake.type_id("Vanguard"), 1, 140.0, 10.0, 0)
    fake.block(a[2], e1, both=True)
    assert firing.count_able(fake, w, a, [e1, e2], ARC_OFF) == (2, 2)
    fake.block(a[2], e2, both=True)            # now a3 has no open target
    assert firing.count_able(fake, w, a, [e1, e2], ARC_OFF) == (1, 2)


def test_ac24_dead_units_do_not_count():
    """AC 10: a dead shooter and a dead target both drop out of the count."""
    fake, w, a, e = row_world()
    fake.set_hp(a[2], 0)
    assert firing.count_able(fake, w, a, [e], ARC_OFF) == (1, 1)
    fake.set_hp(a[1], 0)
    assert firing.count_able(fake, w, a, [e], ARC_OFF) == (0, 0)
    fake, w, a, e = row_world()
    fake.set_hp(e, 0)
    assert firing.count_able(fake, w, a, [e], ARC_OFF) == (0, 0)


def test_ac10_each_type_uses_its_own_attack_range():
    """AC 10: reach is per type (read from the engine, not passed in); a long-range type counts where a short one does not."""
    fake = CountFake(stats={"Raider": {"attack_range": 200.0}, "Warden": {"attack_range": 50.0}})
    w = fake.new_world(0)
    rd, wd, vg = (fake.type_id(n) for n in ("Raider", "Warden", "Vanguard"))
    a = [fake.spawn(w, rd, 0, 0.0, 0.0, 0), fake.spawn(w, wd, 0, 50.0, 0.0, 0), fake.spawn(w, vg, 0, 100.0, 0.0, 0)]
    e = fake.spawn(w, vg, 1, 140.0, 0.0, 0)                    # distances 140, 90, 40; ranges 200, 50, 100
    assert firing.count_able(fake, w, a, [e], ARC_OFF) == (2, 1)
    fake.units[a[0]]["type"] = vg                              # the long-range unit becomes a plain Vanguard
    assert firing.count_able(fake, w, a, [e], ARC_OFF) == (1, 1)


def test_ac10_empty_side_reads_zero_and_result_is_an_int_pair():
    """AC 10 (existence): an empty list on either side is zero for both, never an error; ints, not bools or floats."""
    fake, w, a, e = row_world()
    assert firing.count_able(fake, w, [], [e], ARC_OFF) == (0, 0)
    assert firing.count_able(fake, w, a, [], ARC_OFF) == (0, 0)
    out = firing.count_able(fake, w, a, [e], ARC_OFF)
    assert isinstance(out, tuple) and all(type(v) is int for v in out)


def test_ac10_count_asks_the_engine_with_the_world_and_shooter_first():
    """AC 10 interaction (minimum pin, deliberately loose: a builder may order the gates as it likes): whenever
    can_shoot is asked it is can_shoot(w, shooter, enemy) with the world first and the two units on opposite sides,
    and both directions are asked at least once (side 0 at the enemy, the enemy at side 0)."""
    fake, w, a, e = row_world()
    firing.count_able(fake, w, a, [e], ARC_OFF)
    asked = [c[1:] for c in fake.calls_named("can_shoot")]
    assert asked and all(c[0] == w for c in asked)
    assert all((c[1] in a) != (c[2] in a) for c in asked), "a pair must be one unit of each side"
    assert any(c[1] in a and c[2] == e for c in asked) and any(c[1] == e and c[2] in a for c in asked)


@pytest.mark.parametrize("enemy_x,expected", [(100.0, (1, 1)), (100.0001, (0, 0)), (99.9999, (1, 1))])
def test_ac10_range_test_is_distance_less_or_equal_attack_range(enemy_x, expected):
    """AC 10 (Readings): a target at exactly attack_range counts (<=); a hair beyond does not; a hair inside does."""
    fake = CountFake()
    w = fake.new_world(0)
    vg = fake.type_id("Vanguard")
    a = fake.spawn(w, vg, 0, 0.0, 0.0, 0)
    e = fake.spawn(w, vg, 1, enemy_x, 0.0, 0)
    assert firing.count_able(fake, w, [a], [e], ARC_OFF) == expected


# ---------------------------------------------------------------- layer reach (R-008-02, R-164-01, ruling 10)

def test_r008_02_reach_zero_enemy_on_another_layer_reads_zero_both_ways():
    """R-008-02: with reach (0, 0) a unit fires on its own layer only; the retired AC-24 layer case is this one."""
    fake, w, a, e = row_world(enemy_layer=1)
    assert firing.count_able(fake, w, a, [e], ARC_OFF) == (0, 0)


def test_r164_01_reach_one_each_way_lets_both_sides_count_across_one_layer():
    """R-164-01 positive control for the case above: reach (1, 1) on the Vanguard type reads the same geometry as (2, 1)."""
    fake, w, a, e = row_world(enemy_layer=1, reach=vg_reach(1, 1))
    assert firing.count_able(fake, w, a, [e], ARC_OFF) == (2, 1)
    fake, w, a, e = row_world(reach=vg_reach(1, 1))
    for u in a:
        fake.units[u]["layer"] = 1             # side 0 now stands ABOVE the enemy: it fires down, the enemy fires up
    assert firing.count_able(fake, w, a, [e], ARC_OFF) == (2, 1)


@pytest.mark.parametrize("reach,expected", [((1, 0), (2, 0)), ((0, 1), (0, 1)), ((0, 0), (0, 0))])
def test_r164_01_up_and_down_reach_are_separate(reach, expected):
    """R-164-01: side 0 stands one layer BELOW the enemy. Up reach 1 lets side 0 fire up; down reach 1 lets the enemy
    fire down. (1, 0): side 0 only; (0, 1): the enemy only; (0, 0): neither."""
    fake, w, a, e = row_world(enemy_layer=1, reach=vg_reach(*reach))
    assert firing.count_able(fake, w, a, [e], ARC_OFF) == expected


def test_r164_01_two_layers_apart_needs_reach_two():
    """R-164-01: reach (1, 1) does not span two layers; (2, 2) does."""
    fake, w, a, e = row_world(enemy_layer=2, reach=vg_reach(1, 1))
    assert firing.count_able(fake, w, a, [e], ARC_OFF) == (0, 0)
    fake, w, a, e = row_world(enemy_layer=2, reach=vg_reach(2, 2))
    assert firing.count_able(fake, w, a, [e], ARC_OFF) == (2, 1)


def test_r164_01_reach_is_the_shooters_type_not_the_targets():
    """R-164-01: only the enemy's type (Raider) can fire down one layer; side 0's Vanguards cannot fire up.
    The Raider's range is 80: only the unit 40 away is in it."""
    fake = CountFake(reach={FakeEngine().type_id("Raider"): (1, 1)})
    w = fake.new_world(0)
    vg, rd = fake.type_id("Vanguard"), fake.type_id("Raider")
    a = [fake.spawn(w, vg, 0, x, 0.0, 0) for x in (0.0, 50.0, 100.0)]
    e = fake.spawn(w, rd, 1, 140.0, 0.0, 1)
    assert firing.count_able(fake, w, a, [e], ARC_OFF) == (0, 1)


def test_unit_in_transition_is_on_the_layer_unit_layer_returns():
    """Spec "The count": the effective layer of a unit in transition is what unit_layer returns; no special case."""
    fake, w, a, e = row_world(reach=vg_reach(0, 0))
    fake.units[e]["layer"] = 1                 # the engine has already switched it
    assert firing.count_able(fake, w, a, [e], ARC_OFF) == (0, 0)
    fake.units[e]["layer"] = 0                 # and back: only unit_layer decides
    assert firing.count_able(fake, w, a, [e], ARC_OFF) == (2, 1)


# ---------------------------------------------------------------- offset multipliers (ruling 10; spec gate 3)

def test_r005_range_up_multiplier_shrinks_the_range_of_a_unit_firing_up():
    """Ruling 10 / gate 3: a shooter's range at a layer offset is attack_range x OM_TP_RANGE_UP_1 when firing up one
    layer. Side 0 (below) fires up at the enemy: distances 140, 90, 40 against range 100 x m."""
    for m, expected_able0 in ((1.0, 2), (0.95, 2), (0.8, 1), (0.5, 1), (0.3, 0)):
        fake, w, a, e = row_world(enemy_layer=1, reach=vg_reach(1, 1), params={"OM_TP_RANGE_UP_1": m})
        got = firing.count_able(fake, w, a, [e], ARC_OFF)
        assert got[0] == expected_able0, "RANGE_UP_1 = %s" % m
        assert got[1] == 1, "the enemy fires DOWN; RANGE_UP_1 must not touch it"


def test_r005_range_down_multiplier_shrinks_the_range_of_a_unit_firing_down():
    """Ruling 10: the enemy (above) fires down: OM_TP_RANGE_DOWN_1 scales its range (100 x 0.3 = 30 reaches nobody
    at 40 wu or more), while side 0 firing up keeps its full range."""
    fake, w, a, e = row_world(enemy_layer=1, reach=vg_reach(1, 1), params={"OM_TP_RANGE_DOWN_1": 0.3})
    assert firing.count_able(fake, w, a, [e], ARC_OFF) == (2, 0)


def test_r005_offset_two_reads_the_two_layer_multiplier_not_the_one_layer_one():
    """Ruling 10: a two-layer offset reads OM_TP_RANGE_UP_2. UP_1 = 0.1 must not apply; UP_2 = 0.5 does (range 50)."""
    fake, w, a, e = row_world(enemy_layer=2, reach=vg_reach(2, 2),
                              params={"OM_TP_RANGE_UP_1": 0.1, "OM_TP_RANGE_UP_2": 0.5})
    assert firing.count_able(fake, w, a, [e], ARC_OFF)[0] == 1


def test_r005_same_layer_ignores_every_offset_multiplier():
    """Ruling 10 control: at offset 0 no multiplier applies, whatever the engine holds."""
    params = {"OM_TP_RANGE_UP_1": 0.1, "OM_TP_RANGE_DOWN_1": 0.1, "OM_TP_RANGE_UP_2": 0.1}
    fake, w, a, e = row_world(params=params)
    assert firing.count_able(fake, w, a, [e], ARC_OFF) == (2, 1)


# ---------------------------------------------------------------- the side's visible set (spec gate 2; ruling 10)

def test_r005_05_target_must_be_in_the_shooters_sides_visible_set():
    """Gate 2: a unit counts only against enemies in its side's visible set. Hidden from side 0 -> side 0 reads 0."""
    fake, w, a, e = row_world()
    fake.sees = lambda side, target: not (side == 0 and target == e)
    assert firing.count_able(fake, w, a, [e], ARC_OFF) == (0, 1)


def test_r005_05_visibility_is_per_target_and_per_side():
    """Gate 2: side 1 sees only a[0] (out of its range) -> side 1 reads 0; side 0 is unaffected. Seeing a[1] restores 1."""
    fake, w, a, e = row_world()
    fake.sees = lambda side, target: side == 0 or target == a[0]
    assert firing.count_able(fake, w, a, [e], ARC_OFF) == (2, 0)
    fake.sees = lambda side, target: side == 0 or target == a[1]
    assert firing.count_able(fake, w, a, [e], ARC_OFF) == (2, 1)


def test_r005_05_the_visible_set_is_asked_for_the_side_and_the_enemy_ids():
    """Gate 2 interaction (minimum pin, deliberately loose): visible_enemies(w, side, enemy_ids) is asked with the
    world first, the shooter's own side number, and ids that are only the OTHER side's units; both sides are asked."""
    fake, w, a, e = row_world()
    firing.count_able(fake, w, a, [e], ARC_OFF)
    asked = fake.calls_named("visible_enemies")
    assert {c[2] for c in asked} == {0, 1} and all(c[1] == w for c in asked)
    assert all(set(c[3]) <= {e} for c in asked if c[2] == 0)
    assert all(set(c[3]) <= set(a) for c in asked if c[2] == 1)


# ---------------------------------------------------------------- the firing arc (ruling 8; spec gate 4)

def arc_world(bearing_deg, shooter_facing=0.0, enemy_facing=None, arc_dist=90.0):
    """Shooter a at the origin facing `shooter_facing` (radians); enemy e at `arc_dist` along `bearing_deg`.
    The enemy faces the shooter unless told otherwise, so only the shooter's arc is under test. 90 wu < range 100,
    so float error in the trigonometry never touches the range edge."""
    fake = CountFake()
    w = fake.new_world(0)
    vg = fake.type_id("Vanguard")
    b = math.radians(bearing_deg)
    a = fake.spawn(w, vg, 0, 0.0, 0.0, 0)
    e = fake.spawn(w, vg, 1, arc_dist * math.cos(b), arc_dist * math.sin(b), 0)
    fake.facings[a] = shooter_facing
    fake.facings[e] = b + math.pi if enemy_facing is None else enemy_facing
    return fake, w, a, e


@pytest.mark.parametrize("bearing,arc,inside", [
    (0.0, ARC_DRAFT, True), (59.0, ARC_DRAFT, True), (61.0, ARC_DRAFT, False),
    (-59.0, ARC_DRAFT, True), (-61.0, ARC_DRAFT, False), (180.0, ARC_DRAFT, False),
    (89.0, 180.0, True), (91.0, 180.0, False), (179.0, 360.0, True), (180.0, 360.0, True),
])
def test_r100_04_a_unit_counts_only_with_the_target_inside_the_arc_about_its_facing(bearing, arc, inside):
    """Ruling 8 / gate 4: able requires the target inside the arc (half-width = arc_deg / 2 either side of the facing).
    The enemy faces the shooter, so only side 0's arc decides; at 360 the arc is off (today's behaviour, the control)."""
    fake, w, a, e = arc_world(bearing)
    assert firing.count_able(fake, w, [a], [e], arc) == (1 if inside else 0, 1)


def test_r100_04_the_arc_turns_with_the_facing_and_wraps_at_pi():
    """Ruling 8: the angle is the shortest arc between facing and bearing. Facing 3.1 rad and a target at -3.1 rad are
    0.08 rad apart, not 6.2 apart: inside any arc; a facing turned away by 90 degrees is outside a 120 degree arc."""
    fake, w, a, e = arc_world(math.degrees(-3.1), shooter_facing=3.1)
    assert firing.count_able(fake, w, [a], [e], ARC_DRAFT)[0] == 1
    fake, w, a, e = arc_world(0.0, shooter_facing=math.pi / 2)
    assert firing.count_able(fake, w, [a], [e], ARC_DRAFT)[0] == 0
    fake, w, a, e = arc_world(0.0, shooter_facing=math.pi / 2 - 0.3)    # 72.8 degrees off: still outside half-width 60
    assert firing.count_able(fake, w, [a], [e], ARC_DRAFT)[0] == 0
    fake, w, a, e = arc_world(0.0, shooter_facing=0.5)                   # 28.6 degrees off: inside
    assert firing.count_able(fake, w, [a], [e], ARC_DRAFT)[0] == 1


def test_r100_04_a_flanked_unit_with_its_back_to_the_enemy_is_not_able_until_it_turns():
    """Ruling 8: the arc gates the SHOT: facing away reads 0, and the same unit reads 1 once the engine's face pass has
    turned it (facing is read live from unit_facing each call)."""
    fake, w, a, e = arc_world(0.0, shooter_facing=math.pi)
    assert firing.count_able(fake, w, [a], [e], ARC_DRAFT) == (0, 1)
    fake.facings[a] = 0.0
    assert firing.count_able(fake, w, [a], [e], ARC_DRAFT) == (1, 1)


def test_r100_04_the_arc_is_per_shooter_each_side_uses_its_own_facing():
    """Ruling 8: the enemy facing away from side 0 cannot fire at it; side 0 facing the enemy can: (1, 0). Swapped: (0, 1)."""
    fake, w, a, e = arc_world(0.0, shooter_facing=0.0, enemy_facing=0.0)
    assert firing.count_able(fake, w, [a], [e], ARC_DRAFT) == (1, 0)
    fake, w, a, e = arc_world(0.0, shooter_facing=math.pi, enemy_facing=math.pi)
    assert firing.count_able(fake, w, [a], [e], ARC_DRAFT) == (0, 1)


def test_r100_04_the_arc_gate_composes_with_the_other_gates():
    """Gate 4 with gate 5: inside the arc but can_shoot false still reads 0; arc fails and can_shoot true reads 0 too."""
    fake, w, a, e = arc_world(0.0)
    fake.block(a, e)
    assert firing.count_able(fake, w, [a], [e], ARC_DRAFT) == (0, 1)
    fake, w, a, e = arc_world(90.0)
    assert firing.count_able(fake, w, [a], [e], ARC_DRAFT) == (0, 1)


def test_r100_04_boundary_is_inclusive_and_arc_360_or_more_is_off():
    """Overseer defaults (Architect to confirm): the arc boundary is inclusive, so a target exactly half the arc off the
    facing (90 degrees of a 180 arc, built at exact coordinates (0, 90)) counts; arc_deg >= 360 means the arc is off,
    even with the target straight behind."""
    fake = CountFake()
    w = fake.new_world(0)
    vg = fake.type_id("Vanguard")
    a = fake.spawn(w, vg, 0, 0.0, 0.0, 0)
    e = fake.spawn(w, vg, 1, 0.0, 90.0, 0)
    assert firing.count_able(fake, w, [a], [e], 180.0)[0] == 1
    fake, w, a, e = arc_world(180.0)
    for arc in (360.0, 400.0, 720.0):
        assert firing.count_able(fake, w, [a], [e], arc)[0] == 1, arc
    assert firing.count_able(fake, w, [a], [e], 359.0)[0] == 0     # control: 359 is not off (half-width 179.5 < 180)


# ---------------------------------------------------------------- the type weight (ruling 5)

def weight_world(near_cat="Vanguard", far_cat="Bombard", shooter="Raider", **kw):
    """A shooter at the origin; a near enemy at 30 wu and a far enemy at 60 wu, all range 100 or more, same layer.
    ids: shooter 1, near 2, far 3."""
    fake = CountFake(stats={"Bombard": {"attack_range": 150.0}}, **kw)
    w = fake.new_world(0)
    s = fake.spawn(w, fake.type_id(shooter), 0, 0.0, 0.0, 0)
    near = fake.spawn(w, fake.type_id(near_cat), 1, 30.0, 0.0, 0)
    far = fake.spawn(w, fake.type_id(far_cat), 1, 60.0, 0.0, 0)
    return fake, w, s, near, far


def test_ruling5_weight_is_the_category_multiplier_of_attacker_against_target():
    """Ruling 5: one Raider (category 0) against one Vanguard (category 1), both able: (m(0, 1), m(1, 0))."""
    fake = CountFake()
    w = fake.new_world(0)
    r = fake.spawn(w, fake.type_id("Raider"), 0, 0.0, 0.0, 0)
    v = fake.spawn(w, fake.type_id("Vanguard"), 1, 50.0, 0.0, 0)
    got = firing.count_weighted(fake, w, [r], [v], ARC_OFF)
    assert got == (mult(0, 1), mult(1, 0))
    assert all(type(x) is float for x in got)
    assert ("category_multiplier", w, 0, 1) in fake.calls and ("category_multiplier", w, 1, 0) in fake.calls


def test_ruling5_weights_sum_over_the_able_units_and_an_unable_unit_adds_nothing():
    """Ruling 5: three Raiders able against one Vanguard add three multipliers; one out of range adds none."""
    fake = CountFake()
    w = fake.new_world(0)
    rd, vg = fake.type_id("Raider"), fake.type_id("Vanguard")
    a = [fake.spawn(w, rd, 0, x, 0.0, 0) for x in (0.0, 10.0, 20.0)]
    e = fake.spawn(w, vg, 1, 70.0, 0.0, 0)                    # Raider range 80: all three reach; the Vanguard (100) too
    assert firing.count_weighted(fake, w, a, [e], ARC_OFF) == pytest.approx((3 * mult(0, 1), mult(1, 0)))
    fake.units[a[0]]["x"] = 500.0                              # out of range of everything
    assert firing.count_weighted(fake, w, a, [e], ARC_OFF)[0] == pytest.approx(2 * mult(0, 1))
    assert firing.count_weighted(fake, w, [], [e], ARC_OFF) == (0.0, 0.0)


def test_ruling5_weight_never_changes_with_hit_points():
    """Ruling 5: weight is the multiplier and nothing else; wounded units (hp 1) weigh what healthy ones did."""
    fake = CountFake()
    w = fake.new_world(0)
    r = fake.spawn(w, fake.type_id("Raider"), 0, 0.0, 0.0, 0)
    v = fake.spawn(w, fake.type_id("Vanguard"), 1, 50.0, 0.0, 0)
    healthy = firing.count_weighted(fake, w, [r], [v], ARC_OFF)
    fake.set_hp(r, 1.0); fake.set_hp(v, 1.0)
    assert firing.count_weighted(fake, w, [r], [v], ARC_OFF) == healthy


def test_ruling5_weight_ignores_damage_interval_and_health_of_the_type():
    """Ruling 5: never damage, interval or health. A same-category type with 100x damage, a tenth of the interval and a
    twentieth of the health weighs exactly what the plain one does."""
    base = CountFake()
    w = base.new_world(0)
    r = base.spawn(w, base.type_id("Raider"), 0, 0.0, 0.0, 0)
    v = base.spawn(w, base.type_id("Vanguard"), 1, 50.0, 0.0, 0)
    plain = firing.count_weighted(base, w, [r], [v], ARC_OFF)
    odd = CountFake(stats={"Raider": {"base_damage": 1000.0, "attack_interval": 2.0, "max_hp": 3.5}})
    w2 = odd.new_world(0)
    r2 = odd.spawn(w2, odd.type_id("Raider"), 0, 0.0, 0.0, 0)
    v2 = odd.spawn(w2, odd.type_id("Vanguard"), 1, 50.0, 0.0, 0)
    assert firing.count_weighted(odd, w2, [r2], [v2], ARC_OFF) == plain


def test_ruling5_weight_ignores_the_cross_layer_damage_multiplier():
    """Ruling 5 / 10: a cross-layer damage multiplier (OM_TP_DAMAGE_UP_1 = 0.25) is not in the weight; the count's
    gates are untouched by it too."""
    fake, w, a, e = row_world(enemy_layer=1, reach=vg_reach(1, 1), params={"OM_TP_DAMAGE_UP_1": 0.25,
                                                                           "OM_TP_DAMAGE_DOWN_1": 0.25})
    got = firing.count_weighted(fake, w, a, [e], ARC_OFF)
    assert got == pytest.approx((2 * mult(1, 1), mult(1, 1)))


def test_ruling5_target_of_record_is_the_nearest_eligible_enemy_when_the_engine_has_no_target():
    """Ruling 5: unit_target 0 -> the nearest eligible enemy (the Vanguard at 30, category 1), not the Bombard at 60."""
    fake, w, s, near, far = weight_world()
    assert firing.count_weighted(fake, w, [s], [near, far], ARC_OFF)[0] == mult(0, 1)


def test_ruling5_target_of_record_is_the_engine_target_when_it_is_eligible():
    """Ruling 5: the engine's target (the Bombard at 60, category 2) wins over the nearer eligible Vanguard."""
    fake, w, s, near, far = weight_world()
    fake.targets[s] = far
    assert firing.count_weighted(fake, w, [s], [near, far], ARC_OFF)[0] == mult(0, 2)
    assert ("unit_target", w, s) in fake.calls


@pytest.mark.parametrize("why", ["blocked", "dead", "out of reach", "not seen", "out of range"])
def test_ruling5_an_ineligible_engine_target_is_replaced_by_the_nearest_eligible_enemy(why):
    """Ruling 5: the engine target counts only when eligible; blocked, dead, off-layer beyond reach, unseen or out of
    range, the nearest eligible enemy (the Vanguard at 30) is the target of record instead."""
    fake, w, s, near, far = weight_world()
    fake.targets[s] = far
    if why == "blocked":
        fake.block(s, far)
    elif why == "dead":
        fake.set_hp(far, 0)
    elif why == "out of reach":
        fake.units[far]["layer"] = 1
    elif why == "not seen":
        fake.sees = lambda side, target: target != far
    elif why == "out of range":
        fake.units[far]["x"] = 400.0
    assert firing.count_weighted(fake, w, [s], [near, far], ARC_OFF)[0] == mult(0, 1)


def test_ruling5_nearest_eligible_skips_a_nearer_enemy_that_is_ineligible():
    """Ruling 5: 'nearest eligible', not 'nearest': the Vanguard at 30 is blocked, so the Bombard at 60 is the target."""
    fake, w, s, near, far = weight_world()
    fake.block(s, near)
    assert firing.count_weighted(fake, w, [s], [near, far], ARC_OFF)[0] == mult(0, 2)


def test_ruling5_a_unit_with_no_eligible_enemy_weighs_nothing():
    """Ruling 5: every enemy blocked -> the shooter is not able and contributes 0.0, whatever the engine targets."""
    fake, w, s, near, far = weight_world()
    fake.targets[s] = far
    fake.block(s, near); fake.block(s, far)
    assert firing.count_weighted(fake, w, [s], [near, far], ARC_OFF)[0] == 0.0


def test_ruling5_weight_and_count_agree_on_who_is_able():
    """Ruling 5: the weighted prediction is the count with weights: the units contributing to count_weighted are
    exactly the units count_able counts (here a mixed field with a blocker, an off-layer and a dead enemy)."""
    fake, w, a, e = row_world(reach=vg_reach(0, 0))
    fake.block(a[1], e)
    able = firing.count_able(fake, w, a, [e], ARC_OFF)
    weights = firing.count_weighted(fake, w, a, [e], ARC_OFF)
    assert able == (1, 1)
    assert weights == pytest.approx((able[0] * mult(1, 1), able[1] * mult(1, 1)))


# ---------------------------------------------------------------- states
# Architect ruling on the target of record (LAB-REV2-L1): per unit per sample the target of record is the engine's
# target if can_engage against it is 0; else the nearest living enemy of a hostile faction with can_engage 0; else the
# nearest living hostile enemy (so the code is the first failing reason 1..5 against it); -1 only when no living
# hostile exists. Overseer defaults, pending the Architect's confirmation: nearest = planar x, y distance, tie to the
# lowest unit id; the list is ordered by unit id with dead units omitted. Codes: 1 out of reach, 2 not seen by the side,
# 3 out of range at this offset, 4 outside the arc, 5 line blocked. Diagnostic order is that order: the lowest failing
# gate is the one reported.

def test_states_gives_code_zero_to_a_unit_that_can_engage_and_minus_one_when_no_enemy_lives():
    """Spec seam: states -> [(unit, code)] with code the can_engage result against the target of record, -1 when none.
    Row world: a[1], a[2] and the enemy can engage (0); a[0] is 140 wu from the enemy, out of range 100 (code 3);
    lone side: -1."""
    fake, w, a, e = row_world()
    got = firing.states(fake, w, a, [e], ARC_OFF)
    assert isinstance(got, list) and all(isinstance(t, tuple) and len(t) == 2 for t in got)
    assert all(type(u) is int and type(c) is int for u, c in got)
    codes = dict(got)
    assert codes[a[0]] == 3
    assert codes[a[1]] == 0 and codes[a[2]] == 0 and codes[e] == 0
    fake, w, a, e = row_world()
    codes = dict(firing.states(fake, w, a, [], ARC_OFF))
    assert all(codes[u] == -1 for u in a)


def test_states_code_zero_exactly_where_count_able_counts():
    """Spec seam: the zero-code units of states are the units count_able counts (same composition, one source)."""
    fake, w, a, e = row_world(enemy_layer=1, reach=vg_reach(1, 0))   # side 0 fires up: two of three; the enemy cannot
    codes = dict(firing.states(fake, w, a, [e], ARC_OFF))
    zeros0 = sum(1 for u in a if codes[u] == 0)
    zeros1 = 1 if codes[e] == 0 else 0
    assert (zeros0, zeros1) == firing.count_able(fake, w, a, [e], ARC_OFF) == (2, 0)


def fail_world(code):
    """One shooter a (side 0) at the origin, one enemy e (side 1) 60 wu away on the same layer; exactly the gate named by
    `code` fails for a (0: none). Returns (fake, w, a, e, arc_deg). Range 100, reach (0, 0), full sight, facing 0."""
    fake = CountFake()
    w = fake.new_world(0)
    vg = fake.type_id("Vanguard")
    a = fake.spawn(w, vg, 0, 0.0, 0.0, 0)
    e = fake.spawn(w, vg, 1, 60.0, 0.0, 0)
    arc = ARC_OFF
    if code == 1:
        fake.units[e]["layer"] = 1                                     # reach (0, 0): out of reach
    elif code == 2:
        fake.sees = lambda side, target: not (side == 0 and target == e)
    elif code == 3:
        fake.units[e]["x"] = 400.0
    elif code == 4:
        arc, fake.facings[a] = ARC_DRAFT, math.pi                      # the enemy is straight behind a
    elif code == 5:
        fake.block(a, e)
    return fake, w, a, e, arc


@pytest.mark.parametrize("code", [0, 1, 2, 3, 4, 5])
def test_states_code_is_the_one_failing_gate_exact_ints(code):
    """Each of the five reasons alone, on its own geometry, reads its exact int: 1 out of reach, 2 not seen, 3 out of
    range, 4 outside the arc, 5 blocked; 0 when nothing fails (the positive control of the five)."""
    fake, w, a, e, arc = fail_world(code)
    got = dict(firing.states(fake, w, [a], [e], arc))[a]
    assert got == code and type(got) is int


@pytest.mark.parametrize("code", [0, 1, 2, 3, 4, 5])
def test_count_able_counts_exactly_the_code_zero_units_across_the_five_failure_geometries(code):
    """Spec: a unit counts when its code is 0. For side 0 the count is 1 for the control (0) and 0 for each failure
    geometry 1..5; for every geometry the counted units are exactly the zero-code units of states, both sides."""
    fake, w, a, e, arc = fail_world(code)
    states = dict(firing.states(fake, w, [a], [e], arc))
    zeros = (1 if states[a] == 0 else 0, 1 if states[e] == 0 else 0)
    got = firing.count_able(fake, w, [a], [e], arc)
    assert got == zeros and got[0] == (1 if code == 0 else 0)


@pytest.mark.parametrize("code", [1, 2, 3, 4, 5])
def test_weight_is_zero_for_every_unable_code(code):
    """Ruling 5: the type weight sums over code-0 units only; codes 1..5 contribute 0.0 to side 0."""
    fake, w, a, e, arc = fail_world(code)
    assert dict(firing.states(fake, w, [a], [e], arc))[a] == code
    assert firing.count_weighted(fake, w, [a], [e], arc)[0] == 0.0


def test_weight_is_zero_for_code_minus_one_and_the_control_weighs_the_multiplier():
    """Ruling 5: -1 (no living hostile) contributes 0.0 as well; the code-0 control weighs mult(1, 1), so the zeros
    above are not a function that always returns 0."""
    fake, w, a, e, arc = fail_world(0)
    assert firing.count_weighted(fake, w, [a], [e], arc)[0] == mult(1, 1)
    fake.set_hp(e, 0)
    assert dict(firing.states(fake, w, [a], [e], arc))[a] == -1
    assert firing.count_weighted(fake, w, [a], [e], arc) == (0.0, 0.0)


@pytest.mark.parametrize("fails,code", [
    ("reach+range", 1), ("unseen+range", 2), ("range+arc", 3), ("arc+blocked", 4),
    ("unseen+arc+blocked", 2), ("all", 1),
])
def test_states_code_is_the_lowest_failing_gate_when_several_fail(fails, code):
    """Diagnostic order 1 reach, 2 seen, 3 range, 4 arc, 5 line: with several gates failing at once the lowest number
    is reported."""
    fake, w, a, e, arc = fail_world(0)
    parts = fails.split("+") if fails != "all" else ["reach", "unseen", "range", "arc", "blocked"]
    if "reach" in parts:
        fake.units[e]["layer"] = 1
    if "unseen" in parts:
        fake.sees = lambda side, target: not (side == 0 and target == e)
    if "range" in parts:
        fake.units[e]["x"] = 400.0
    if "arc" in parts:
        arc, fake.facings[a] = ARC_DRAFT, math.pi
    if "blocked" in parts:
        fake.block(a, e)
    assert dict(firing.states(fake, w, [a], [e], arc))[a] == code


def test_states_range_failure_at_a_layer_offset_is_code_3_not_1():
    """Gate 3 is 'out of range at this offset': reach (1, 1) passes gate 1, and RANGE_UP_1 = 0.3 shrinks 100 to 30, so
    the enemy 60 wu away on the next layer up is code 3."""
    fake, w, a, e, arc = fail_world(0)
    fake.units[e]["layer"] = 1
    fake.reach_by_type = vg_reach(1, 1)
    assert dict(firing.states(fake, w, [a], [e], arc))[a] == 0
    fake.params["OM_TP_RANGE_UP_1"] = 0.3
    assert dict(firing.states(fake, w, [a], [e], arc))[a] == 3


def two_enemy_world(near_x, far_x):
    """Shooter s (side 0) at the origin, two enemies on the +x axis: near at near_x, far at far_x. ids: s 1, near 2, far 3."""
    fake = CountFake()
    w = fake.new_world(0)
    vg = fake.type_id("Vanguard")
    s = fake.spawn(w, vg, 0, 0.0, 0.0, 0)
    near = fake.spawn(w, vg, 1, near_x, 0.0, 0)
    far = fake.spawn(w, vg, 1, far_x, 0.0, 0)
    return fake, w, s, near, far


def test_states_code_is_against_the_nearest_hostile_when_none_is_able():
    """Ruling: nobody able -> the code is the first failing reason against the NEAREST living hostile. Near (30) is
    blocked (5), far (400) is out of range (3): the code is 5, not 3."""
    fake, w, s, near, far = two_enemy_world(30.0, 400.0)
    fake.block(s, near)
    assert dict(firing.states(fake, w, [s], [near, far], ARC_OFF))[s] == 5


def test_states_code_follows_the_nearest_when_the_reasons_are_swapped():
    """The swapped case: near (120) is out of range (3), far (140) is not seen by the side (2): the code is 3."""
    fake, w, s, near, far = two_enemy_world(120.0, 140.0)
    fake.sees = lambda side, target: target != far
    assert dict(firing.states(fake, w, [s], [near, far], ARC_OFF))[s] == 3


def test_states_nearest_is_found_wherever_it_is_listed():
    """The nearest enemy listed LAST (and a list in descending distance) still decides the code."""
    fake, w, s, near, far = two_enemy_world(30.0, 400.0)
    fake.block(s, near)
    assert dict(firing.states(fake, w, [s], [far, near], ARC_OFF))[s] == 5
    fake, w, s, near, far = two_enemy_world(120.0, 140.0)
    fake.sees = lambda side, target: target != far
    assert dict(firing.states(fake, w, [s], [far, near], ARC_OFF))[s] == 3


def test_states_nearest_is_planar_distance_whatever_the_layer():
    """Overseer default: nearest by planar x, y distance. The enemy at 50 wu on layer 1 (out of reach, code 1) is nearer
    than the enemy at 60 wu on layer 0 (blocked, code 5), though they are on different layers: the code is 1."""
    fake = CountFake()
    w = fake.new_world(0)
    vg = fake.type_id("Vanguard")
    s = fake.spawn(w, vg, 0, 0.0, 0.0, 0)
    up = fake.spawn(w, vg, 1, 50.0, 0.0, 1)
    level = fake.spawn(w, vg, 1, 0.0, 60.0, 0)
    fake.block(s, level)
    assert dict(firing.states(fake, w, [s], [level, up], ARC_OFF))[s] == 1


def test_states_equal_distance_goes_to_the_lowest_unit_id():
    """Overseer default: a tie in distance goes to the lowest unit id, wherever it is listed. Both enemies 40 wu away
    (one each side of the shooter); the lower id is blocked (5), the higher is not seen (2): the code is 5."""
    fake = CountFake()
    w = fake.new_world(0)
    vg = fake.type_id("Vanguard")
    s = fake.spawn(w, vg, 0, 0.0, 0.0, 0)
    low = fake.spawn(w, vg, 1, 40.0, 0.0, 0)
    high = fake.spawn(w, vg, 1, -40.0, 0.0, 0)
    assert low < high
    fake.block(s, low)
    fake.sees = lambda side, target: target != high
    assert dict(firing.states(fake, w, [s], [high, low], ARC_OFF))[s] == 5


def test_states_a_dead_nearest_enemy_is_skipped():
    """Only LIVING hostiles can be the target of record: the nearer enemy is dead, the far one (blocked) decides: 5, not -1."""
    fake, w, s, near, far = two_enemy_world(30.0, 60.0)
    fake.set_hp(near, 0)
    fake.block(s, far)
    assert dict(firing.states(fake, w, [s], [near, far], ARC_OFF))[s] == 5


def test_states_unable_engine_target_does_not_pick_the_code_when_nobody_is_able():
    """The engine's target drives the code only through can_engage 0. Here it targets the far enemy (out of range, 3),
    nobody is able, and the code is the first failing reason against the NEAREST living hostile (blocked, 5)."""
    fake, w, s, near, far = two_enemy_world(30.0, 400.0)
    fake.targets[s] = far
    fake.block(s, near)
    assert dict(firing.states(fake, w, [s], [near, far], ARC_OFF))[s] == 5


def test_states_is_code_zero_when_the_engine_target_is_unable_but_another_enemy_is_able():
    """The engine's target (far, blocked) is not able; the nearest able enemy makes it code 0, and the unit is counted."""
    fake, w, s, near, far = two_enemy_world(30.0, 60.0)
    fake.targets[s] = far
    fake.block(s, far)
    assert dict(firing.states(fake, w, [s], [near, far], ARC_OFF))[s] == 0
    assert firing.count_able(fake, w, [s], [near, far], ARC_OFF)[0] == 1


def test_states_minus_one_only_when_no_living_hostile_exists():
    """-1 means no living hostile: all enemies dead, or none listed. One living enemy that cannot be engaged is never -1:
    it reads its reason 1..5 (here out of range, 3)."""
    fake, w, s, near, far = two_enemy_world(30.0, 60.0)
    fake.set_hp(near, 0); fake.set_hp(far, 0)
    assert dict(firing.states(fake, w, [s], [near, far], ARC_OFF))[s] == -1
    fake, w, s, near, far = two_enemy_world(30.0, 400.0)
    fake.set_hp(near, 0)
    got = dict(firing.states(fake, w, [s], [near, far], ARC_OFF))[s]
    assert got == 3 and got != -1


def test_states_an_engine_target_outside_the_enemy_list_is_ignored():
    """A target the engine names that is not in units1 (here a third side-1 unit, closer and able, not passed in) is not
    an enemy of this call: the code is read against the listed enemy only (blocked, 5), the count is 0."""
    fake, w, s, near, far = two_enemy_world(30.0, 60.0)
    fake.targets[s] = near
    fake.block(s, far)
    assert dict(firing.states(fake, w, [s], [far], ARC_OFF))[s] == 5
    assert firing.count_able(fake, w, [s], [far], ARC_OFF)[0] == 0
    assert firing.count_weighted(fake, w, [s], [far], ARC_OFF)[0] == 0.0


def test_states_are_ordered_by_unit_id_and_omit_the_dead():
    """The list is ordered by unit id across both sides whatever order the lists come in; dead units are omitted."""
    fake, w, a, e = row_world()
    ids = firing.states(fake, w, [a[2], a[0], a[1]], [e], ARC_OFF)
    assert [u for u, _ in ids] == sorted(a + [e])
    fake.set_hp(a[1], 0)
    fake.set_hp(e, 0)
    assert [u for u, _ in firing.states(fake, w, a, [e], ARC_OFF)] == [a[0], a[2]]


def test_states_use_can_engage_for_the_code_when_the_engine_has_it():
    """After E0 the code is the engine's own can_engage answer against the target of record: every pair says 4, so the
    states read 4 (the composed gates would say 0 or 3 here). A value from the engine is passed through unchanged."""
    fake, w, a, e = row_world(engage_fn=lambda x, y: 4)
    codes = dict(firing.states(fake, w, a, [e], ARC_OFF))
    assert codes[a[1]] == 4 and codes[e] == 4
    assert ("can_engage", w, a[1], e) in fake.calls


# ---------------------------------------------------------------- parity (spec: "after E0 ... a difference is a defect")

def test_parity_is_empty_when_e0_is_absent_whatever_the_composed_count_says():
    """Spec: parity returns [] when E0 is absent. can_engage is the not-built sentinel -1 for every pair."""
    fake, w, a, e = row_world()
    assert fake.can_engage(w, a[0], e) == -1                  # the fake models the stub / missing symbol
    assert firing.parity(fake, w, a, [e], ARC_OFF) == []


def test_parity_is_empty_when_the_engine_and_the_composition_agree():
    """Spec: the composed set equals the can_engage set -> []. Composed able here: a[1], a[2], e."""
    able = set()
    fake, w, a, e = row_world(engage_fn=lambda x, y: 0 if x in able else 1)
    able.update({a[1], a[2], e})
    assert firing.parity(fake, w, a, [e], ARC_OFF) == []


def test_parity_lists_every_unit_where_the_two_answers_differ():
    """Positive control of the detector: a planted disagreement is named. The engine says a[0] can engage (composed:
    out of range) and a[2] cannot (composed: able)."""
    able = {1, 2, 4}                                           # a[0] = 1, a[1] = 2, e = 4 engage; a[2] = 3 does not
    fake, w, a, e = row_world(engage_fn=lambda x, y: 0 if x in able else 1)
    assert sorted(firing.parity(fake, w, a, [e], ARC_OFF)) == [a[0], a[2]]


def test_parity_is_evaluated_live_on_every_call_so_a_difference_that_appears_later_is_caught():
    """The lab calls parity on every sampled tick (Setup.sample_every, 5 by default), so the result must follow the
    world, not a cache: the engine and the composition agree at tick 0; at tick 5 a[2] steps out of range (composed:
    unable) while the engine still says it can engage, and a[2] is named; at tick 10 it steps back and parity is empty.
    Fake-engine twin of the real-engine parity test in integration/test_firing_real.py."""
    fake, w, a, e = row_world(engage_fn=lambda x, y: 0 if x in (a_ids[1], a_ids[2], e_id) else 1)
    a_ids, e_id = a, e
    assert firing.parity(fake, w, a, [e], ARC_OFF) == []
    fake.set_pos(a[2], 400.0, 0.0)
    assert firing.parity(fake, w, a, [e], ARC_OFF) == [a[2]]
    fake.set_pos(a[2], 100.0, 0.0)
    assert firing.parity(fake, w, a, [e], ARC_OFF) == []


def test_parity_is_a_list_of_ints_and_asks_the_engine_with_the_world_first():
    """Spec seam: parity -> list[int]; can_engage is asked as can_engage(w, shooter, enemy)."""
    able = {2, 3}
    fake, w, a, e = row_world(engage_fn=lambda x, y: 0 if x in able else 1)
    out = firing.parity(fake, w, a, [e], ARC_OFF)
    assert isinstance(out, list) and all(type(u) is int for u in out)
    asked = fake.calls_named("can_engage")
    assert asked and all(c[1] == w for c in asked)
    assert any(c[2] in a and c[3] == e for c in asked) and any(c[2] == e and c[3] in a for c in asked)


# ---------------------------------------------------------------- engine bindings (fake library, no compiler)

class _Fn:
    """One C function of a fake library: records argtypes and restype like a ctypes function pointer, returns `ret`."""

    def __init__(self, ret):
        self.argtypes = None
        self.restype = None
        self.ret = ret
        self.calls = []

    def __call__(self, *args):
        self.calls.append(args)
        return self.ret


class _FakeLib:
    """Stands in for ctypes.CDLL: any symbol exists unless listed in `missing` (then AttributeError, like a real one)."""

    def __init__(self, missing=(), returns=None):
        self._missing = set(missing)
        self._returns = dict(returns or {})

    def __getattr__(self, name):
        if name.startswith("__") or name in self._missing:
            raise AttributeError(name)
        fn = _Fn(self._returns.get(name, 0))
        object.__setattr__(self, name, fn)
        return fn


def make_engine(**kw):
    """An Engine whose library is the fake: Engine.__new__ skips the CDLL load, _bind runs for real.

    FRAGILE BY DESIGN, read before changing engine.py: only _bind runs, so Engine.can_engage must tolerate a missing
    om_combat_can_engage using ONLY state that _bind set (or getattr(self._lib, ..., None) at call time). Anything set in
    __init__ (caches, flags such as a `_has_can_engage` computed there) does not exist on this object and raises
    AttributeError; do not move such state to __init__ without moving this helper with it."""
    eng = engine_mod.Engine.__new__(engine_mod.Engine)
    eng._lib = _FakeLib(**kw)
    eng._bind()
    return eng


W = ctypes.c_void_p(1)


def test_binding_transition_progress_is_a_double_taking_world_and_unit():
    """Spec L1 row: engine.transition_progress(w, u) wraps om_unit_transition_progress(const om_world*, uint32_t) ->
    double, returned as a float."""
    eng = make_engine(returns={"om_unit_transition_progress": 0.25})
    fn = eng._lib.om_unit_transition_progress
    assert fn.restype is ctypes.c_double and fn.argtypes == [ctypes.c_void_p, ctypes.c_uint32]
    got = eng.transition_progress(W, 7)
    assert got == 0.25 and type(got) is float
    assert fn.calls == [(W, 7)]


def test_binding_can_engage_returns_the_library_answer_when_the_symbol_exists():
    """Spec contract: om_combat_can_engage(const om_world*, uint32_t, uint32_t) -> int, passed through unchanged."""
    eng = make_engine(returns={"om_combat_can_engage": 3})
    fn = eng._lib.om_combat_can_engage
    assert fn.restype is ctypes.c_int and fn.argtypes == [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_uint32]
    got = eng.can_engage(W, 4, 9)
    assert got == 3 and type(got) is int and fn.calls == [(W, 4, 9)]


def test_binding_can_engage_is_the_not_built_sentinel_minus_one_when_the_symbol_is_missing():
    """Before E0 the library has no om_combat_can_engage: binding must not fail, and can_engage reads -1 (the same value
    the E0 stub returns). Positive control: a library that has the symbol does not read -1 for an answer of 0."""
    eng = make_engine(missing={"om_combat_can_engage"})
    assert eng.can_engage(W, 4, 9) == -1
    assert make_engine(returns={"om_combat_can_engage": 0}).can_engage(W, 4, 9) == 0


def test_binding_can_engage_passes_the_stub_value_minus_one_through():
    """E0 stub: the symbol exists and returns -1; the binding returns -1."""
    assert make_engine(returns={"om_combat_can_engage": -1}).can_engage(W, 4, 9) == -1


def test_binding_unit_type_and_category_multiplier_wrap_their_library_functions():
    """The two reads the count needs (names fixed by this file): unit_type -> om_unit_get_unit_type (int), and
    category_multiplier -> om_tactical_category_multiplier(om_world*, int, int) -> double (float)."""
    eng = make_engine(returns={"om_unit_get_unit_type": 5, "om_tactical_category_multiplier": 1.5})
    t, m = eng._lib.om_unit_get_unit_type, eng._lib.om_tactical_category_multiplier
    assert t.restype is ctypes.c_int32 and t.argtypes == [ctypes.c_void_p, ctypes.c_uint32]
    assert m.restype is ctypes.c_double and m.argtypes == [ctypes.c_void_p, ctypes.c_int, ctypes.c_int]
    got = eng.unit_type(W, 3)
    assert got == 5 and type(got) is int and t.calls == [(W, 3)]
    got = eng.category_multiplier(W, 2, 1)
    assert got == 1.5 and type(got) is float and m.calls == [(W, 2, 1)]


# ---------------------------------------------------------------- Engine.profile_reach binding (moved from the retired
# test_firing_weighted.py: the binding is unchanged, only its caller changed; the count composes reach from it)

class _ReachLib:
    def __init__(self, ret=0, write=None):
        self.ret, self.write, self.seen = ret, write, None
        self.om_unit_profile_reach = self._call

    def _call(self, w, t, up, down):
        self.seen = (t, up, down)
        ref = lambda p: p._obj if hasattr(p, "_obj") else p.contents
        if self.write:
            ref(up).value, ref(down).value = self.write
        return self.ret


def _reach_engine(lib):
    e = engine_mod.Engine.__new__(engine_mod.Engine)
    e._lib = lib
    return e


def test_profile_reach_returns_the_pair_the_library_wrote():
    """profile_reach returns (up, down) as ints."""
    lib = _ReachLib(write=(2, 1))
    out = _reach_engine(lib).profile_reach(None, 4)
    assert out == (2, 1) and all(type(v) is int for v in out) and lib.seen[0] == 4


def test_profile_reach_initialises_up_and_down_to_zero_for_the_inert_stub():
    """A library that writes nothing reads (0, 0), not garbage."""
    assert _reach_engine(_ReachLib()).profile_reach(None, 0) == (0, 0)


def test_profile_reach_nonzero_return_raises_value_error():
    """A nonzero return (unknown type) is a ValueError."""
    with pytest.raises(ValueError):
        _reach_engine(_ReachLib(ret=-1)).profile_reach(None, 999)
