# spec: docs/northstar/plans/skilllab-harness-spec.md::Acceptance criteria::AC-24; 2026-10-14-skill-lab-rev2-spec.md::L1
"""AC 24 firing count against the real engine, hand-built geometry; rev 2 count of LAB-REV2-L1 (below the AC-24 cases).

Side 0: three units in a row, A, B, C along +x. Side 1: one enemy E behind A on the -x side.
Distances from E, as fractions of the Vanguard attack range R: A 0.3, B 0.7, C 1.2.
Replicate shifts are at most 10 world units per axis, far inside every margin (R is read from
the engine, so no position is a magic number).
"""
import ctypes
import sys
from contextlib import contextmanager
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.skilllab import engine, fight, firing  # noqa: E402
from scripts.skilllab.contract import Group, Setup  # noqa: E402

UNIT = "Vanguard"
BASE_X, BASE_Y = 400.0, 400.0   # keeps every point positive


class _BlockerEngine:
    """Real Engine plus blockers added to each new world; every other call passes through."""

    def __init__(self, real, blockers):
        self._real = real
        self._blockers = blockers

    def __getattr__(self, name):
        return getattr(self._real, name)

    def new_world(self, *args, **kwargs):
        w = self._real.new_world(*args, **kwargs)
        for x, y, r in self._blockers:
            self._real.add_blocker(w, x, y, r)
        return w


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


def _points(reach):
    a = (BASE_X, BASE_Y)
    b = (BASE_X + 0.4 * reach, BASE_Y)
    c = (BASE_X + 0.9 * reach, BASE_Y)
    e = (BASE_X - 0.3 * reach, BASE_Y)
    return a, b, c, e


def _setup(reach):
    a, b, c, e = _points(reach)
    side0 = Group(side=0, unit=UNIT, count=3, formation="points", x=BASE_X, y=BASE_Y,
                  facing_deg=0.0, layer=0, order="idle", params={"points": [a, b, c]})
    side1 = Group(side=1, unit=UNIT, count=1, formation="points", x=e[0], y=e[1],
                  facing_deg=180.0, layer=0, order="idle", params={"points": [e]})
    return Setup(groups=(side0, side1), unit_types={}, abilities=False, max_ticks=10, sample_every=5)


def _tick0(result):
    tick, able0, able1 = result.firing[0]
    assert tick == 0
    return able0, able1


def test_two_of_three_within_reach_reads_2_and_1(real_engine, reach):
    """AC 24 base case, also the no-blocker count the blocker cases compare against."""
    result = fight.fight(_setup(reach), 0, False, engine=real_engine)
    assert _tick0(result) == (2, 1)
    assert result.first_contact_tick == 0


@pytest.mark.parametrize("seed", [1, 2, 3])
def test_count_holds_across_replicate_shifts(real_engine, reach, seed):
    """AC 24 / AC 6: the replicate shift (<= 10 wu per axis) does not change the hand-built count."""
    assert _tick0(fight.fight(_setup(reach), seed, True, engine=real_engine)) == (2, 1)


def test_blocker_between_one_pair_removes_one_shooter_from_the_losing_side(real_engine, reach):
    """AC 24 blocker case: disc between A and B blocks the E-B line only. Side 0 loses B (2 -> 1);
    side 1 still fires through A, so its count is unchanged."""
    a, b, c, e = _points(reach)
    assert _tick0(fight.fight(_setup(reach), 0, False, engine=real_engine)) == (2, 1)   # no-blocker count first
    blocker = ((a[0] + b[0]) / 2.0, BASE_Y, 0.08 * reach)
    blocked = _BlockerEngine(real_engine, [blocker])
    assert _tick0(fight.fight(_setup(reach), 0, False, engine=blocked)) == (1, 1)


def test_blocker_on_every_line_to_the_enemy_removes_the_enemys_shot_too(real_engine, reach):
    """AC 24 blocker case: disc between E and A lies on both E-A and E-B. Side 0 drops 2 -> 0,
    side 1 drops 1 -> 0 (it loses its only pair)."""
    a, b, c, e = _points(reach)
    assert _tick0(fight.fight(_setup(reach), 0, False, engine=real_engine)) == (2, 1)   # no-blocker count first
    blocker = ((a[0] + e[0]) / 2.0, BASE_Y, 0.07 * reach)
    blocked = _BlockerEngine(real_engine, [blocker])
    assert _tick0(fight.fight(_setup(reach), 0, False, engine=blocked)) == (0, 0)


# ======================================================================= rev 2 (LAB-REV2-L1)
# The new seam: firing.count_able / count_weighted / states / parity (engine, w, units0, units1, arc_deg).
# Cases are built by hand on the real library; the expected numbers come from the geometry and the engine's own
# tables, never from firing.py. Each case also reads what the engine DID (hit points after 60 to 100 ticks), so a count
# that disagrees with the fight is caught here and not only by the lab's own parity check.

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


def test_control_same_layer_16_v_16_blob_reads_16_16_on_the_lab_series(real_engine):
    """Positive control (green before and after L1): two Vanguard blobs of 16 on one layer, inside every range and
    sensor, read 16 and 16 on the fight's own firing series at tick 0, as they do today."""
    blob = lambda side, x, f: Group(side=side, unit=UNIT, count=16, formation="blob", x=x, y=1000.0, facing_deg=f,
                                    layer=0, order="idle", params={"radius": 60.0})
    setup = Setup(groups=(blob(0, 1000.0, 0.0), blob(1, 1150.0, 180.0)), unit_types={}, max_ticks=10, sample_every=5)
    assert fight.fight(setup, 0, False, engine=real_engine).firing[0] == (0, 16, 16)


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


def test_r164_01_vision_zero_and_half_differ_only_in_vision(real_engine):
    """Control for the case above: with reach (1, 1) and vision 0.5 the count is positive for BOTH sides, so the 0 in
    the vision-0 row is the vision gate and nothing else."""
    with world(real_engine) as w:
        real_engine.set_reach(w, real_engine.type_id(UNIT), 1, 1)
        s0 = grid(real_engine, w, UNIT, 0, 1000.0, 1000.0, 1)
        s1 = grid(real_engine, w, UNIT, 1, 1150.0, 1000.0, 0)
        able0, able1 = firing.count_able(real_engine, w, s0, s1, ARC_OFF)
        assert able0 > 0 and able1 > 0


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


# ---------------------------------------------------------------- parity (goes live when E0 is on main)

def _e0_on_main(lib):
    """E0 adds OM_TP_FIRING_ARC_DEG to the header (parameter enum) and om_combat_can_engage to the library."""
    return "OM_TP_FIRING_ARC_DEG" in engine._load_param_ids() and hasattr(lib._lib, "om_combat_can_engage")


class _ParitySpy(engine.Engine):
    """Real Engine whose step() checks firing.parity every 20 ticks (every sampled tick of the lab) over the units this
    wrapper spawned, and keeps every unit the check names."""

    def __init__(self):
        super().__init__()
        self.parity_differences = []
        self.parity_checks = 0
        self._n = 0

    def step(self, w):
        if self._n % 20 == 0:
            sides = [[u for u in self._own.get((w.value, f), []) if self.unit_alive(w, u)] for f in (0, 1)]
            if sides[0] and sides[1]:
                self.parity_checks += 1
                self.parity_differences += [(self._n, u) for u in firing.parity(self, w, sides[0], sides[1], ARC_OFF)]
        self._n += 1
        super().step(w)


@pytest.mark.parametrize("control", ["mirror", "numbers", "planted"])
def test_parity_is_empty_on_every_sampled_tick_of_the_three_controls(control):
    """Spec L1 row (after E0): the composed set equals the can_engage set on every sampled tick of the controls
    (mirror 16 v 16, numbers 16 v 8, planted 20 percent damage), fog on. The test is skipped until E0 is on main;
    with the E0 stub (can_engage = -1) it passes trivially, and E2 makes it bite. A non-empty list is a defect."""
    from scripts.skilllab import plays
    spy = _ParitySpy()
    if not _e0_on_main(spy):
        pytest.skip("E0 not on main")
    play = plays.damage_play(16) if control == "planted" else plays.blob_play(16)
    setup = play(8 if control == "numbers" else 16, False)
    fight.fight(setup, 0, False, engine=spy)
    assert spy.parity_checks > 0
    assert spy.parity_differences == []
