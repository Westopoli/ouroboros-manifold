# spec: docs/northstar/plans/2026-10-14-skill-lab-rev2-spec.md::Pieces::L1; harness-spec AC-24 (hand-built count)
"""The rev 2 count of LAB-REV2-L1 against the real engine, hand-built geometry, no fight loop.

This file imports neither `fight` nor `plays`: it needs only L1 (firing.py and the engine bindings), so it can be green
before L2 exists. The fight-level cases (the old AC-24 series through fight.fight, the 16 v 16 control read on the
fight's own series, the parity run over fight.fight) live in test_fight_firing_real.py, owned by L2.

Expected numbers come from the geometry and the engine's own tables, never from firing.py. Each case also reads what
the engine DID (hit points after 60 to 100 ticks), so a count that disagrees with the fight is caught here.
"""
import ctypes
import sys
from contextlib import contextmanager
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.skilllab import engine, firing  # noqa: E402

UNIT = "Vanguard"
BASE_X, BASE_Y = 400.0, 400.0   # keeps every point positive


@pytest.fixture(scope="module")
def real_engine():
    return engine.Engine()


@pytest.fixture(scope="module")
def reach(real_engine):
    w = real_engine.new_world(0)
    try:
        stats = real_engine.type_stats(w, real_engine.type_id(UNIT))
    finally:
        real_engine.free_world(w)
    return float(stats["attack_range"])


ARC_OFF = 360.0
CATMULT_NAMES = ["OM_TP_CATMULT_%s_%s" % (a, d) for a in ("LINE", "SIEGE", "STRIKE") for d in ("LINE", "SIEGE", "STRIKE")]
VISION_PARAMS = ("OM_TP_VISION_UP_1", "OM_TP_VISION_DOWN_1")
SPACING = 30.0
FIGHT_TICKS = 60


@contextmanager
def world(lib, catmult=False):
    w = lib.new_world(0)
    lib.disable_abilities(w)
    try:
        if catmult:                      # nine distinct multipliers: a wrong attacker/target pair can never match
            for i, name in enumerate(CATMULT_NAMES):
                lib.set_param(w, lib.param_id(name), 0.5 + 0.1 * i)
        yield w
    finally:
        lib.free_world(w)


def cat_mult(lib, w, attacker_cat, target_cat):
    """The engine's own table, called directly so the oracle does not depend on the wrapper under test."""
    fn = lib._lib.om_tactical_category_multiplier
    fn.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int]
    fn.restype = ctypes.c_double
    return fn(w, attacker_cat, target_cat)


def category(lib, w, name):
    return lib.type_stats(w, lib.type_id(name))["category"]


def grid(lib, w, name, faction, x, y, layer, n=16):
    """n units of one type in a 4-wide grid of 30 wu spacing from (x, y); returns the ids."""
    t = lib.type_id(name)
    return [lib.spawn(w, t, faction, x + SPACING * (i % 4), y + SPACING * (i // 4), layer) for i in range(n)]


def hp_total(lib, w, ids):
    return sum(lib.unit_hp(w, u) for u in ids)


def damage_done(lib, w, ids, ticks=FIGHT_TICKS):
    before = hp_total(lib, w, ids)
    for _ in range(ticks):
        lib.step(w)
    return before - hp_total(lib, w, ids)


# ---------------------------------------------------------------- AC 24 hand-built case, read through count_able
# Side 0: three units in a row A, B, C along +x; side 1: one enemy E behind A on the -x side. Distances from E, as
# fractions of the Vanguard attack range R: A 0.3, B 0.7, C 1.2 (R is read from the engine: no magic position).

def _ac24_units(lib, w, reach):
    t = lib.type_id(UNIT)
    a = [lib.spawn(w, t, 0, BASE_X + f * reach, BASE_Y, 0) for f in (0.0, 0.4, 0.9)]
    e = lib.spawn(w, t, 1, BASE_X - 0.3 * reach, BASE_Y, 0)
    return a, e


def test_ac24_two_of_three_within_reach_reads_2_and_1_through_count_able(real_engine, reach):
    """AC 24 base case (positive control for the two blocker cases below): the hand-built row reads (2, 1)."""
    with world(real_engine) as w:
        a, e = _ac24_units(real_engine, w, reach)
        assert firing.count_able(real_engine, w, a, [e], ARC_OFF) == (2, 1)


def test_ac24_blocker_between_one_pair_removes_one_shooter_from_the_losing_side(real_engine, reach):
    """AC 24 blocker case: a disc between A and B blocks the E-B line only. Side 0 loses B (2 -> 1); side 1 still
    fires through A, so its count is unchanged. The code of B is 5 (line blocked)."""
    with world(real_engine) as w:
        a, e = _ac24_units(real_engine, w, reach)
        assert firing.count_able(real_engine, w, a, [e], ARC_OFF) == (2, 1)           # no-blocker count first
        real_engine.add_blocker(w, BASE_X + 0.2 * reach, BASE_Y, 0.08 * reach)
        assert firing.count_able(real_engine, w, a, [e], ARC_OFF) == (1, 1)
        assert dict(firing.states(real_engine, w, a, [e], ARC_OFF))[a[1]] == 5


def test_ac24_blocker_on_every_line_to_the_enemy_removes_the_enemys_shot_too(real_engine, reach):
    """AC 24 blocker case: a disc between E and A lies on both E-A and E-B. Side 0 drops 2 -> 0 and side 1 drops
    1 -> 0 (it loses its only pair)."""
    with world(real_engine) as w:
        a, e = _ac24_units(real_engine, w, reach)
        assert firing.count_able(real_engine, w, a, [e], ARC_OFF) == (2, 1)           # no-blocker count first
        real_engine.add_blocker(w, BASE_X - 0.15 * reach, BASE_Y, 0.07 * reach)
        assert firing.count_able(real_engine, w, a, [e], ARC_OFF) == (0, 0)


def test_same_layer_16_v_16_reads_16_16_through_the_new_count(real_engine):
    """The control above, through firing.count_able on a hand-placed grid: 16 and 16 (every pair inside range 300 and
    sensor 700)."""
    with world(real_engine) as w:
        s0 = grid(real_engine, w, UNIT, 0, 1000.0, 1000.0, 0)
        s1 = grid(real_engine, w, UNIT, 1, 1150.0, 1000.0, 0)
        assert firing.count_able(real_engine, w, s0, s1, ARC_OFF) == (16, 16)
        assert damage_done(real_engine, w, s0 + s1) > 0


@pytest.mark.parametrize("vision,reach,expected", [
    (0.5, (1, 1), (16, 16)),       # the default one-layer vision factor, reach one each way: both sides see and fire
    (0.0, (1, 1), (0, 0)),         # vision 0 (symmetric, ruling 10): nobody sees across the layer, nobody fires
    (0.5, (0, 0), (0, 0)),         # control: vision is fine, reach 0 is the only cause
])
def test_r005_05_cross_layer_16_v_16_side_0_one_layer_up(real_engine, vision, reach, expected):
    """R-005-05, R-164-01, ruling 10: 16 v 16 Vanguards, side 0 on layer 1 and side 1 on layer 0, 60 to 250 wu
    apart (inside range 300). Vision 0 reads 0 both sides; 0.5 reads positive (all 16: sensor 700 x 0.5 = 350 covers
    the 256 wu corner to corner). The engine agrees: hit points fall only when the count is positive."""
    with world(real_engine) as w:
        real_engine.set_reach(w, real_engine.type_id(UNIT), *reach)
        for name in VISION_PARAMS:
            real_engine.set_param(w, real_engine.param_id(name), vision)
        s0 = grid(real_engine, w, UNIT, 0, 1000.0, 1000.0, 1)
        s1 = grid(real_engine, w, UNIT, 1, 1150.0, 1000.0, 0)
        assert firing.count_able(real_engine, w, s0, s1, ARC_OFF) == expected
        done = damage_done(real_engine, w, s0 + s1)
        assert (done > 0) == (expected != (0, 0)), "the count and the fight disagree: %r, damage %r" % (expected, done)


@pytest.mark.parametrize("spotter,expected,damaged", [(False, (0, 0), False), (True, (1, 0), True)])
def test_s2_screen_bombard_fires_beyond_its_own_sensor_only_with_a_spotter(real_engine, spotter, expected, damaged):
    """Spec L1 Bombard-and-spotter case: a Bombard (sensor 300, range 1200, reach two down) on layer 2 and an enemy
    Vanguard 600 wu away on layer 0. Without a spotter the enemy is outside the side's visible set: able 0. With a
    Raider spotter 350 wu from the Vanguard (sensor 800 sees it; out of both units' ranges, so the spotter itself does
    not fire) the Bombard is able: 1 for side 0, 0 for side 1. The engine agrees (the Vanguard is hit only then)."""
    with world(real_engine) as w:
        real_engine.set_reach(w, real_engine.type_id("Bombard"), 0, 2)
        bombard = real_engine.spawn(w, real_engine.type_id("Bombard"), 0, 1000.0, 1000.0, 2)
        enemy = real_engine.spawn(w, real_engine.type_id(UNIT), 1, 1600.0, 1000.0, 0)
        side0 = [bombard]
        if spotter:
            side0.append(real_engine.spawn(w, real_engine.type_id("Raider"), 0, 1250.0, 1000.0, 0))
        assert firing.count_able(real_engine, w, side0, [enemy], ARC_OFF) == expected
        start = real_engine.unit_hp(w, enemy)
        for _ in range(100):
            real_engine.step(w)
        assert (real_engine.unit_hp(w, enemy) < start) == damaged


def test_s2_screen_the_spotter_changes_only_the_visible_set(real_engine):
    """Control for the case above: range, reach and line are the same with and without the spotter; the visible set
    is the one thing that changes (the enemy enters it)."""
    with world(real_engine) as w:
        bombard = real_engine.spawn(w, real_engine.type_id("Bombard"), 0, 1000.0, 1000.0, 2)
        enemy = real_engine.spawn(w, real_engine.type_id(UNIT), 1, 1600.0, 1000.0, 0)
        assert enemy not in real_engine.visible_enemies(w, 0, [enemy])
        real_engine.spawn(w, real_engine.type_id("Raider"), 0, 1250.0, 1000.0, 0)
        assert enemy in real_engine.visible_enemies(w, 0, [enemy])
        assert real_engine.can_shoot(w, bombard, enemy)


# ---------------------------------------------------------------- the type weight (ruling 5)

def test_ruling5_weight_is_the_engines_category_multiplier_of_the_target_of_record(real_engine):
    """Ruling 5: a Bombard (siege) and a Vanguard (line) 200 wu apart on one layer. Weight 0 is the multiplier of the
    Bombard against the Vanguard's category, weight 1 the Vanguard's against the Bombard's, read with
    om_tactical_category_multiplier, with nine distinct table values so no other pair can match."""
    with world(real_engine, catmult=True) as w:
        bombard = real_engine.spawn(w, real_engine.type_id("Bombard"), 0, 1000.0, 1000.0, 0)
        vanguard = real_engine.spawn(w, real_engine.type_id(UNIT), 1, 1200.0, 1000.0, 0)
        cb, cv = category(real_engine, w, "Bombard"), category(real_engine, w, UNIT)
        assert cb != cv
        expected = (cat_mult(real_engine, w, cb, cv), cat_mult(real_engine, w, cv, cb))
        assert expected[0] != expected[1]
        assert firing.count_able(real_engine, w, [bombard], [vanguard], ARC_OFF) == (1, 1)
        assert firing.count_weighted(real_engine, w, [bombard], [vanguard], ARC_OFF) == pytest.approx(expected)


def test_ruling5_weight_does_not_change_while_hit_points_fall(real_engine):
    """Ruling 5: never health. The pair above fights for 40 ticks (both lose hit points: asserted), stays in range, and
    the weighted count is the same to the last digit."""
    with world(real_engine, catmult=True) as w:
        bombard = real_engine.spawn(w, real_engine.type_id("Bombard"), 0, 1000.0, 1000.0, 0)
        vanguard = real_engine.spawn(w, real_engine.type_id(UNIT), 1, 1200.0, 1000.0, 0)
        before = firing.count_weighted(real_engine, w, [bombard], [vanguard], ARC_OFF)
        hp = (real_engine.unit_hp(w, bombard), real_engine.unit_hp(w, vanguard))
        for _ in range(40):
            real_engine.step(w)
        assert real_engine.unit_hp(w, bombard) < hp[0] and real_engine.unit_hp(w, vanguard) < hp[1]
        assert real_engine.unit_alive(w, bombard) and real_engine.unit_alive(w, vanguard)
        assert firing.count_weighted(real_engine, w, [bombard], [vanguard], ARC_OFF) == before


def test_ruling5_same_category_field_weighs_the_count_times_the_multiplier(real_engine):
    """Ruling 5 / positive control: 16 v 16 Vanguards weigh 16 x m(line, line) per side, and the count stays 16."""
    with world(real_engine, catmult=True) as w:
        s0 = grid(real_engine, w, UNIT, 0, 1000.0, 1000.0, 0)
        s1 = grid(real_engine, w, UNIT, 1, 1150.0, 1000.0, 0)
        c = category(real_engine, w, UNIT)
        m = cat_mult(real_engine, w, c, c)
        assert firing.count_weighted(real_engine, w, s0, s1, ARC_OFF) == pytest.approx((16 * m, 16 * m))


def test_ruling5_target_of_record_skips_a_nearer_enemy_the_shooter_cannot_engage(real_engine):
    """Ruling 5: the nearest ELIGIBLE enemy. A Raider (range 200, reach 0) on layer 0: a Bombard at 80 wu on layer 2 is
    nearer but out of reach; a Vanguard at 180 wu on layer 0 is the target of record. Weight 0 = m(raider, line), not
    m(raider, siege). Side 1: only the Vanguard can fire (reach 0)."""
    with world(real_engine, catmult=True) as w:
        raider = real_engine.spawn(w, real_engine.type_id("Raider"), 0, 1000.0, 1000.0, 0)
        bombard = real_engine.spawn(w, real_engine.type_id("Bombard"), 1, 1080.0, 1000.0, 2)
        vanguard = real_engine.spawn(w, real_engine.type_id(UNIT), 1, 1180.0, 1000.0, 0)
        cr, cb, cv = (category(real_engine, w, n) for n in ("Raider", "Bombard", UNIT))
        assert cat_mult(real_engine, w, cr, cv) != cat_mult(real_engine, w, cr, cb)
        assert firing.count_able(real_engine, w, [raider], [bombard, vanguard], ARC_OFF) == (1, 1)
        got = firing.count_weighted(real_engine, w, [raider], [bombard, vanguard], ARC_OFF)
        assert got == pytest.approx((cat_mult(real_engine, w, cr, cv), cat_mult(real_engine, w, cv, cr)))


def test_ruling5_target_of_record_follows_the_engines_own_target_once_it_has_one(real_engine):
    """Ruling 5: after the engine has chosen (unit_target != 0, here within two ticks), the weight is the multiplier
    against THAT unit's category. The rule's choice between engine target and nearest is pinned on fakes
    (test_firing.py); this case proves the real library's target is the one read."""
    with world(real_engine, catmult=True) as w:
        raider = real_engine.spawn(w, real_engine.type_id("Raider"), 0, 1000.0, 1000.0, 0)
        near = real_engine.spawn(w, real_engine.type_id(UNIT), 1, 1150.0, 1000.0, 0)
        far = real_engine.spawn(w, real_engine.type_id("Bombard"), 1, 1190.0, 1000.0, 0)
        for _ in range(3):
            real_engine.step(w)
        target = real_engine.unit_target(w, raider)
        assert target in (near, far)
        cr = category(real_engine, w, "Raider")
        ct = category(real_engine, w, UNIT if target == near else "Bombard")
        got = firing.count_weighted(real_engine, w, [raider], [near, far], ARC_OFF)
        assert got[0] == pytest.approx(cat_mult(real_engine, w, cr, ct))




# ---------------------------------------------------------------- states (the code is the first failing gate)

def _layered(lib, w, reach, vision):
    """16 v 16 Vanguards, side 0 on layer 1 and side 1 on layer 0, 150 wu apart in x (the cross-layer case above)."""
    lib.set_reach(w, lib.type_id(UNIT), *reach)
    for name in VISION_PARAMS:
        lib.set_param(w, lib.param_id(name), vision)
    return grid(lib, w, UNIT, 0, 1000.0, 1000.0, 1), grid(lib, w, UNIT, 1, 1150.0, 1000.0, 0)


def test_states_cross_layer_control_all_32_units_read_code_zero(real_engine):
    """Positive control for the two rows below: reach (1, 1) and vision 0.5 give code 0 for all 32 units (and the
    count above reads 16 and 16 for the same scene)."""
    with world(real_engine) as w:
        s0, s1 = _layered(real_engine, w, (1, 1), 0.5)
        codes = dict(firing.states(real_engine, w, s0, s1, ARC_OFF))
        assert sorted(codes) == sorted(s0 + s1) and set(codes.values()) == {0}


def test_states_vision_zero_reads_code_2_not_seen_for_all_32_units(real_engine):
    """Spec L1 row: vision 0 (symmetric, ruling 10) with reach one each way passes the reach gate and fails the side's
    visible set: the first failing reason is 2 for every one of the 32 units, on both sides."""
    with world(real_engine) as w:
        s0, s1 = _layered(real_engine, w, (1, 1), 0.0)
        got = firing.states(real_engine, w, s0, s1, ARC_OFF)
        assert len(got) == 32 and {c for _, c in got} == {2}


def test_states_reach_zero_with_vision_half_reads_code_1_out_of_reach_for_all_32_units(real_engine):
    """Spec L1 row: reach (0, 0) with the default vision 0.5 fails the first gate: code 1 for all 32 units, whatever the
    sight and range say (the cross-layer count above reads 0 and 0 for the same scene)."""
    with world(real_engine) as w:
        s0, s1 = _layered(real_engine, w, (0, 0), 0.5)
        got = firing.states(real_engine, w, s0, s1, ARC_OFF)
        assert len(got) == 32 and {c for _, c in got} == {1}


# ---------------------------------------------------------------- parity (goes live when E0 is on main)

SAMPLE_EVERY = 5      # Setup.sample_every: the lab checks parity on every sampled tick
MAX_PARITY_TICKS = 300


def _e0_on_main(lib):
    """E0 adds OM_TP_FIRING_ARC_DEG to the header (parameter enum) and om_combat_can_engage to the library."""
    return "OM_TP_FIRING_ARC_DEG" in engine._load_param_ids() and hasattr(lib._lib, "om_combat_can_engage")


class _ParitySpy(engine.Engine):
    """Real Engine whose step() checks firing.parity on every sampled tick (every SAMPLE_EVERY steps, tick 0 included)
    over the units this wrapper spawned, and keeps every unit the check names. Needs no fight loop: see the scenes."""

    def __init__(self):
        super().__init__()
        self.parity_differences = []
        self.parity_checks = 0
        self._n = 0

    def step(self, w):
        if self._n % SAMPLE_EVERY == 0:
            sides = [[u for u in self._own.get((w.value, f), []) if self.unit_alive(w, u)] for f in (0, 1)]
            if sides[0] and sides[1]:
                self.parity_checks += 1
                self.parity_differences += [(self._n, u) for u in firing.parity(self, w, sides[0], sides[1], ARC_OFF)]
        self._n += 1
        super().step(w)


def _parity_scene(spy, w, scene):
    """The three controls, inline (no plays.py): mirror 16 v 16, numbers 16 v 8, and a cross-layer fog case (side 0 one
    layer up, reach one each way, vision 0.5) so the reach, sight and range gates all run. Every unit attack-moves at the
    enemy's start centroid; OM_TP_TARGET_BY_SIGHT is 1, the only setting tested (overseer default)."""
    spy.disable_abilities(w)
    spy.set_param(w, spy.param_id("OM_TP_TARGET_BY_SIGHT"), 1.0)
    n1 = 8 if scene == "numbers" else 16
    layer0 = 1 if scene == "fog_layers" else 0
    if scene == "fog_layers":
        spy.set_reach(w, spy.type_id(UNIT), 1, 1)
    s0 = grid(spy, w, UNIT, 0, 1000.0, 1000.0, layer0)
    s1 = grid(spy, w, UNIT, 1, 1500.0, 1000.0, 0, n=n1)
    for u in s0:
        spy.order_attack_move(w, [u], 1545.0, 1045.0)
    for u in s1:
        spy.order_attack_move(w, [u], 1045.0, 1045.0)
    return s0, s1


@pytest.mark.parametrize("scene", ["mirror", "numbers", "fog_layers"])
def test_parity_is_empty_on_every_sampled_tick_of_the_controls(scene):
    """Spec L1 row (after E0): the composed set equals the can_engage set on every sampled tick (every 5th) of the
    controls, fog on; a non-empty list is a defect. The third control is the cross-layer fog case, not the planted
    damage scene (that one differs only in a damage multiplier, which no gate reads). Skipped until E0 is on main; with
    the E0 stub (can_engage = -1) it passes trivially and E2 makes it bite."""
    spy = _ParitySpy()
    if not _e0_on_main(spy):
        pytest.skip("E0 not on main")
    w = spy.new_world(0)
    try:
        s0, s1 = _parity_scene(spy, w, scene)
        for _ in range(MAX_PARITY_TICKS):
            if not any(spy.unit_alive(w, u) for u in s0) or not any(spy.unit_alive(w, u) for u in s1):
                break
            spy.step(w)
    finally:
        spy.free_world(w)
    assert spy.parity_checks >= 10
    assert spy.parity_differences == []
