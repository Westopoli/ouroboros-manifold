# spec: docs/northstar/plans/skilllab-harness-spec.md::Acceptance criteria::AC-5; LAB-REV2-L2 (Q-LAB-03: elimination only; the L1/L2 firing seam)
"""fight() on a FakeEngine: spawn order, shifts, unit types, strength and margin, outcomes, firing samples.

Formation placement is stubbed (a fixed, recorded point list) so these tests need neither a compiler nor the
formations leaf; the stub is installed on both `scripts.skilllab.formations.place` and `fight.place`.
"""
import random
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
for _p in (ROOT, Path(__file__).resolve().parent):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import scripts.skilllab.fight as fight_mod  # noqa: E402
import scripts.skilllab.formations as formations_mod  # noqa: E402
from fakes import FakeEngine  # noqa: E402
from scripts.skilllab.contract import SHIFT_MAX, TICKS_PER_SECOND, Group, Setup  # noqa: E402
from scripts.skilllab.fight import fight  # noqa: E402

pytestmark = pytest.mark.usefixtures("seam")   # LAB-REV2-L2: fight() reads the firing counts through the L1/L2 seam (fakes.Seam)


@pytest.fixture(autouse=True)
def place_calls(monkeypatch):
    calls = []

    def stub(kind, n, x, y, facing_deg, params):
        calls.append((kind, n, x, y, facing_deg, params))
        return [(x + 7.0 * i, y) for i in range(n)]

    monkeypatch.setattr(formations_mod, "place", stub)
    monkeypatch.setattr(fight_mod, "place", stub, raising=False)
    return calls


def G(side, unit="Vanguard", count=1, x=None, y=0.0, layer=0, order="attack_move", goal=None):
    x = (-300.0 if side == 0 else 300.0) if x is None else x
    return Group(side=side, unit=unit, count=count, formation="line", x=x, y=y,
                 facing_deg=0.0 if side == 0 else 180.0, layer=layer, order=order, goal=goal,
                 params={"spacing": 30.0})


def S(*groups, unit_types=None, abilities=False, max_ticks=50, sample_every=5, orders_per_unit=False):
    """orders_per_unit=False: these tests read group-level orders (the path kept until E1; per-unit orders are in test_fight_outcomes)."""
    return Setup(groups=tuple(groups), unit_types=unit_types or {}, abilities=abilities,
                 max_ticks=max_ticks, sample_every=sample_every, orders_per_unit=orders_per_unit)


def run(setup, seed=0, swap=False, **fake_kw):
    fake = FakeEngine(**fake_kw)
    return fight(setup, seed, swap, engine=fake), fake


def kill(fake, faction):
    for u in fake.units_of(faction):
        fake.set_hp(u, 0)


def two_vs_four():
    return S(G(0, count=2), G(1, "Warden", count=4), max_ticks=10)


# ---------------------------------------------------------------- AC 5: world, abilities, orders

def test_ac5_one_world_per_call_freed_after_the_last_step():
    """AC-5: one new_world, steps use that world, free_world comes once, after every step."""
    res, fake = run(S(G(0), G(1), max_ticks=6))
    w = fake.world
    names = [c[0] for c in fake.calls]
    assert fake.worlds_made == 1 and fake.worlds_freed == [w]
    assert all(c[1] == w for c in fake.calls_named("step"))
    assert names.index("free_world") > len(names) - 1 - names[::-1].index("step")


@pytest.mark.parametrize("flag,expected", [(False, 1), (True, 0)])
def test_ac5_abilities_flag_controls_disable_abilities_before_any_spawn(flag, expected):
    """AC-5: abilities False calls disable_abilities once, before the first spawn; True never calls it."""
    _, fake = run(S(G(0), G(1), abilities=flag, max_ticks=3))
    names = [c[0] for c in fake.calls]
    assert len(fake.calls_named("disable_abilities")) == expected
    if expected:
        assert names.index("disable_abilities") < names.index("spawn")


def test_ac5_orders_follow_group_order_and_go_out_before_the_first_step():
    """AC-5: attack_move to goal or enemy anchor, move to goal, idle gives no order; units are the group's own."""
    a0 = G(0, count=2, order="attack_move", goal=(5.0, 6.0))
    a1 = G(1, count=2, order="move", goal=(7.0, 8.0))
    _, fake = run(S(a0, a1, max_ticks=3))
    u0, u1 = fake.units_of(0), fake.units_of(1)
    am, mv = fake.calls_named("order_attack_move"), fake.calls_named("order_move")
    assert [(sorted(c[2]), c[3], c[4]) for c in am] == [(u0, 5.0, 6.0)]
    assert [(sorted(c[2]), c[3], c[4]) for c in mv] == [(u1, 7.0, 8.0)]
    names = [c[0] for c in fake.calls]
    assert max(names.index("order_attack_move"), names.index("order_move")) < names.index("step")


def test_ac5_attack_move_without_goal_heads_for_the_enemy_anchor_and_idle_orders_nothing():
    """AC-5: goal None attack-moves to the enemy side's anchor; idle groups get no order call."""
    _, fake = run(S(G(0, x=-300.0, y=11.0), G(1, x=250.0, y=-22.0), max_ticks=3))
    got = sorted((sorted(c[2]), c[3], c[4]) for c in fake.calls_named("order_attack_move"))
    assert got == [([1], 250.0, -22.0), ([2], -300.0, 11.0)]
    _, fake = run(S(G(0, order="idle"), G(1, order="idle"), max_ticks=3))
    assert not fake.calls_named("order_attack_move") and not fake.calls_named("order_move")


# ---------------------------------------------------------------- AC 5: unit types

FULL = {"category": 1, "role": "x", "max_hp": 55.0, "base_damage": 3.0, "attack_interval": 10.0,
        "attack_range": 77.0, "speed": 2.0, "sensor_radius": 100.0, "layer_transition_time": 0.0,
        "aoe_radius": 0.0, "ability_id": 0}


def test_ac5_full_stats_entry_is_registered_once_before_spawn_and_used_for_its_units():
    """AC-5 (Readings): a full stats dict is registered verbatim under an id >= 100; its units spawn under it; built-ins use type_id."""
    _, fake = run(S(G(0, "Tank", count=2), G(1, "Warden"), unit_types={"Tank": dict(FULL)}, max_ticks=3))
    regs = fake.calls_named("register_unit_type")
    tid = regs[0][2]
    spawns = fake.spawn_log()
    names = [c[0] for c in fake.calls]
    assert len(regs) == 1 and regs[0][3] == FULL and tid >= 100          # AC-5 Readings: full entries also get ids >= 100
    assert names.index("register_unit_type") < names.index("spawn")
    assert [s[1] for s in spawns] == [tid, tid, fake.type_id("Warden")]


def test_ac5_derived_entry_scales_then_sets_registers_at_100_or_more_once_per_name():
    """AC-5: {base, scale, set} resolves through type_stats of the base, scale before set, id >= 100, one id per name."""
    types = {"LongA": {"base": "Vanguard", "scale": {"attack_range": 2.0, "max_hp": 0.5}, "set": {"attack_range": 7.0}},
             "LongB": {"base": "Warden", "scale": {"attack_range": 1.5}}}
    setup = S(G(0, "LongA", count=2), G(0, "LongA", count=1, x=-200.0), G(0, "LongB"), G(1, "Vanguard"),
              unit_types=types, max_ticks=3)
    _, fake = run(setup)
    regs = {c[3]["attack_range"]: (c[2], c[3]) for c in fake.calls_named("register_unit_type")}
    base_v = FakeEngine().type_stats(None, FakeEngine().type_id("Vanguard"))
    tid_a, st_a = regs[7.0]
    tid_b, st_b = regs[90.0]
    assert len(fake.calls_named("register_unit_type")) == 2 and tid_a >= 100 and tid_b >= 100 and tid_a != tid_b
    assert st_a["max_hp"] == 50.0 and st_a["base_damage"] == base_v["base_damage"]
    assert ("type_stats", fake.world, fake.type_id("Vanguard")) in fake.calls
    assert [s[1] for s in fake.spawn_log()] == [tid_a, tid_a, tid_a, tid_b, fake.type_id("Vanguard")]


def test_ac5_derived_entry_registers_exactly_the_eleven_stat_keys_with_role_base_name_and_ability_id_0():
    """AC-5 (Readings): a derived type is registered with exactly category, role, max_hp, base_damage, attack_interval,
    attack_range, speed, sensor_radius, layer_transition_time, aoe_radius, ability_id; role = base name, ability_id = 0."""
    keys = {"category", "role", "max_hp", "base_damage", "attack_interval", "attack_range", "speed", "sensor_radius",
            "layer_transition_time", "aoe_radius", "ability_id"}
    types = {"LongA": {"base": "Vanguard", "scale": {"attack_range": 2.0}},
             "LongB": {"base": "Warden", "set": {"max_hp": 33.0}}}
    _, fake = run(S(G(0, "LongA"), G(0, "LongB", x=-200.0), G(1), unit_types=types, max_ticks=2))
    regs = [c[3] for c in fake.calls_named("register_unit_type")]
    base_v = FakeEngine().type_stats(None, FakeEngine().type_id("Vanguard"))
    base_w = FakeEngine().type_stats(None, FakeEngine().type_id("Warden"))
    assert len(regs) == 2 and all(set(r) == keys for r in regs)
    assert (regs[0]["role"], regs[0]["ability_id"]) == ("Vanguard", 0)
    assert (regs[1]["role"], regs[1]["ability_id"]) == ("Warden", 0)
    assert regs[0] == dict(base_v, attack_range=base_v["attack_range"] * 2.0, role="Vanguard", ability_id=0)
    assert regs[1] == dict(base_w, max_hp=33.0, role="Warden", ability_id=0)


# ---------------------------------------------------------------- AC 5, 6, 7: spawn order, shifts

def spawn_positions(fake):
    return [(u, f, x, y) for (u, _t, f, x, y, _l) in fake.spawn_log()]


def test_ac7_swap_flips_which_side_spawns_first_keeping_group_order_and_layer():
    """AC-7: swap False spawns all of side 0 first, swap True all of side 1 first; group order kept inside a side."""
    setup = S(G(0, count=2, x=-100.0), G(1, count=2, layer=3), G(0, count=1, x=-50.0), max_ticks=3)
    _, plain = run(setup, swap=False)
    _, swapped = run(setup, swap=True)
    assert [f for _u, f, _x, _y in spawn_positions(plain)] == [0, 0, 0, 1, 1]
    assert [f for _u, f, _x, _y in spawn_positions(swapped)] == [1, 1, 0, 0, 0]
    side0_x = [x for _u, f, x, _y in spawn_positions(swapped) if f == 0]    # groups at -100 (2 units) then -50 (1 unit)
    assert side0_x[0] < -80.0 and side0_x[1] < -80.0 and side0_x[2] > -70.0
    assert {s[5] for s in swapped.spawn_log() if s[2] == 1} == {3}          # the layer reaches the engine


def base_x(side, i):
    return (-300.0 if side == 0 else 300.0) + 7.0 * i      # the stub place: anchor x + 7 per unit, y = 0


@pytest.mark.parametrize("seed", [0, 1, 12345])
@pytest.mark.parametrize("swap", [False, True])
def test_ac6_shift_is_the_next_two_draws_of_random_seed_per_unit_in_spawn_order(seed, swap):
    """AC-6/7: spawn point = formation point + (x, y) uniform in [-SHIFT_MAX, SHIFT_MAX] drawn from Random(seed) in spawn order."""
    _, fake = run(S(G(0, count=3), G(1, count=2), max_ticks=2), seed=seed, swap=swap)
    rng = random.Random(seed)
    index = {0: 0, 1: 0}
    for _u, f, x, y in spawn_positions(fake):
        i, index[f] = index[f], index[f] + 1
        dx, dy = rng.uniform(-SHIFT_MAX, SHIFT_MAX), rng.uniform(-SHIFT_MAX, SHIFT_MAX)
        assert (x - base_x(f, i), y) == pytest.approx((dx, dy), abs=1e-9)


def test_ac6_same_seed_same_shifts_other_seed_other_shifts():
    """AC-6: reproducible by seed; a different seed changes the positions (the shifts are the replicates)."""
    setup = S(G(0, count=4), G(1, count=4), max_ticks=2)
    a = spawn_positions(run(setup, seed=3)[1])
    b = spawn_positions(run(setup, seed=3)[1])
    c = spawn_positions(run(setup, seed=4)[1])
    assert a == b and a != c


def test_ac6_shift_range_is_plus_minus_shift_max_on_each_axis():
    """AC-6: over many units the shifts fill [-10, +10] per axis, never beyond (positive control: the bounds are reached)."""
    n = 300
    _, fake = run(S(G(0, count=n), G(1, count=n), max_ticks=1), seed=7)
    sx, sy, index = [], [], {0: 0, 1: 0}
    for _u, f, x, y in spawn_positions(fake):
        i, index[f] = index[f], index[f] + 1
        sx.append(x - base_x(f, i))
        sy.append(y)
    assert max(map(abs, sx + sy)) <= SHIFT_MAX
    assert min(sx) < -0.9 * SHIFT_MAX and max(sx) > 0.9 * SHIFT_MAX
    assert min(sy) < -0.9 * SHIFT_MAX and max(sy) > 0.9 * SHIFT_MAX


def test_ac5_fight_places_each_group_through_formations_place(place_calls):
    """AC-5/AC-4 interaction: fight asks formations.place for every group with that group's own arguments."""
    g0, g1 = G(0, count=3), G(1, count=2)
    run(S(g0, g1, max_ticks=2))
    assert ("line", 3, -300.0, 0.0, 0.0, {"spacing": 30.0}) in place_calls
    assert ("line", 2, 300.0, 0.0, 180.0, {"spacing": 30.0}) in place_calls


# ---------------------------------------------------------------- AC 8: strength and margin

def test_ac8_strength_margin_survivors_heads_with_scripted_hp():
    """AC-8: strength = sum(hp / starting hp over the living) / starting headcount; margin = side 0 minus side 1."""
    def hurt(t, f):
        if t == 1:
            s0, s1 = f.units_of(0), f.units_of(1)
            f.set_hp(s0[0], 50); f.set_hp(s1[0], 20); f.set_hp(s1[2], 10)

    res, _ = run(two_vs_four(), script=hurt)
    assert (res.outcome, res.ticks, res.heads, res.survivors) == ("cap", 10, (2, 4), (2, 4))
    assert res.strength_left == pytest.approx((0.75, 0.6875)) and res.margin == pytest.approx(0.0625)

    def hurt_and_kill(t, f):
        hurt(t, f)
        if t == 1:
            f.set_hp(f.units_of(1)[1], 0)

    res, _ = run(two_vs_four(), script=hurt_and_kill)
    assert res.survivors == (2, 3) and res.heads == (2, 4)
    assert res.strength_left == pytest.approx((0.75, 0.4375)) and res.margin == pytest.approx(0.3125)


def test_ac8_starting_hp_is_what_unit_hp_read_after_spawn_not_the_type_max():
    """AC-8: a unit that spawned at 80% of its type's max hp and then loses nothing has strength 1.0."""
    res, _ = run(two_vs_four(), spawn_hp_scale=0.8)
    assert res.strength_left == pytest.approx((1.0, 1.0)) and res.margin == pytest.approx(0.0)


def test_ac7_results_are_from_side_0_point_of_view_whichever_side_spawned_first():
    """AC-7/8: the same scripted fight reports the same side-0 numbers for swap False and True."""
    def script(t, f):
        if t == 2:
            kill(f, 1)
            f.set_hp(f.units_of(0)[1], 50)

    a, _ = run(two_vs_four(), script=script, swap=False)
    b, _ = run(two_vs_four(), script=script, swap=True)
    keys = lambda r: (r.outcome, r.margin, r.strength_left, r.survivors, r.heads, r.ticks)  # noqa: E731
    assert keys(a) == keys(b) and a.heads == (2, 4)
    assert a.outcome == "side0" and a.margin == pytest.approx(0.75)


# ---------------------------------------------------------------- AC 9: outcomes

def test_ac9_side0_side1_and_ticks_count_the_steps_taken():
    """AC-9/8: side 1 wiped out -> "side0", side 0 wiped out -> "side1"; ticks equals the steps taken."""
    def side0_wins(t, f):
        if t == 2:
            kill(f, 1)
            f.set_hp(f.units_of(0)[1], 50)

    def side1_wins(t, f):
        if t == 2:
            kill(f, 0)
            for u, hp in zip(f.units_of(1), (40, 20, 0, 0)):
                f.set_hp(u, hp)

    r0, f0 = run(two_vs_four(), script=side0_wins)
    r1, f1 = run(two_vs_four(), script=side1_wins)
    assert (r0.outcome, r0.ticks, f0.step_count, r0.survivors) == ("side0", 3, 3, (2, 0))
    assert r0.margin == pytest.approx(0.75)
    assert (r1.outcome, r1.ticks, f1.step_count, r1.survivors) == ("side1", 3, 3, (0, 2))
    assert r1.margin == pytest.approx(-0.375)


def test_ac9_both_sides_losing_their_last_unit_on_the_same_tick_is_a_draw():
    """AC-9 (A201): mutual wipe-out is "draw" with margin 0; positive control: only side 1 dying is "side0"."""
    both, fake = run(two_vs_four(), script=lambda t, f: (kill(f, 0), kill(f, 1)) if t == 3 else None)
    only1, _ = run(two_vs_four(), script=lambda t, f: kill(f, 1) if t == 3 else None)
    assert (both.outcome, both.ticks, both.survivors, both.strength_left, both.margin) == ("draw", 4, (0, 0), (0.0, 0.0), 0.0)
    assert only1.outcome == "side0"


def test_ac9_cap_when_max_ticks_is_reached_with_both_alive_and_elimination_on_the_last_step_still_wins():
    """AC-9: the cap fires only with both sides alive; a wipe-out on step max_ticks is a win, one step later is a cap."""
    setup = S(G(0), G(1), max_ticks=5)
    last_step, _ = run(setup, script=lambda t, f: kill(f, 1) if t == 4 else None)
    too_late, fake = run(setup, script=lambda t, f: kill(f, 1) if t == 5 else None)
    assert (last_step.outcome, last_step.ticks) == ("side0", 5)
    assert (too_late.outcome, too_late.ticks, fake.step_count) == ("cap", 5, 5)


def test_ac9_quiet_ticks_never_end_a_fight(seam):
    """Q-LAB-03 (stalemate retired): a long quiet stretch ends nothing; the fight runs to the cap, and a change does not matter."""
    def poke(t, f):
        if t % 10 == 9:
            u = f.units_of(1)[0]
            f.set_hp(u, f.units[u]["hp"] - 1)

    quiet, _ = run(S(G(0), G(1), max_ticks=100))
    poked, _ = run(S(G(0), G(1), max_ticks=100), script=poke)
    assert (quiet.outcome, quiet.ticks) == ("cap", 100)
    assert (poked.outcome, poked.ticks) == ("cap", 100)


# ---------------------------------------------------------------- AC 11: every field populated

def _scenario_side0():
    return run(two_vs_four(), script=lambda t, f: kill(f, 1) if t == 2 else None)[0]


def _scenario_cap():
    return run(two_vs_four())[0]


def _scenario_mutual():
    return run(two_vs_four(), script=lambda t, f: (kill(f, 0), kill(f, 1)) if t == 1 else None)[0]


@pytest.mark.parametrize("scenario,outcome", [(_scenario_side0, "side0"), (_scenario_cap, "cap"), (_scenario_mutual, "draw")])
def test_ac11_every_result_field_is_populated_with_its_type(scenario, outcome):
    """AC-11: outcome, ticks, margin, strength_left, survivors, heads, first_contact_tick, firing, seconds on every outcome."""
    r = scenario()
    assert r.outcome == outcome
    assert type(r.ticks) is int and r.ticks > 0 and isinstance(r.margin, float)
    assert all(isinstance(v, tuple) and len(v) == 2 for v in (r.strength_left, r.survivors, r.heads, r.firing_unit_seconds))
    assert type(r.first_contact_tick) is int and isinstance(r.firing, list) and len(r.firing) >= 1
    assert all(len(row) == 3 for row in r.firing) and r.heads[0] > 0 and r.heads[1] > 0


# ---------------------------------------------------------------- AC 10: firing samples (fight <-> firing)

def _table(seam, table):
    """The able counts by tick: table.get(tick, (0, 0)). Returns the seam, whose .calls_named('count_able') lists the calls."""
    seam.able = lambda tick: table.get(tick, (0, 0))
    return seam


def test_ac10_fight_calls_count_able_each_sample_with_the_right_units_world_and_arc(seam):
    """AC-10 interaction (rev 2 seam): one firing.count_able(engine, w, units0, units1, arc_deg) per sample, tick 0 first,
    with each side's unit ids, the world and Setup.firing_arc_deg (no ranges: the count reads the engine)."""
    types = {"Tank": dict(FULL), "Long": {"base": "Vanguard", "scale": {"attack_range": 2.0}}}
    setup = S(G(0, "Tank", count=2), G(0, "Long", x=-200.0), G(1, "Vanguard", count=2),
              unit_types=types, max_ticks=12, sample_every=3)
    res, fake = run(setup)
    calls = seam.calls_named("count_able")
    first = calls[0]
    assert [c[6] for c in calls] == [t for t, _a, _b in res.firing]
    assert first[6] == 0 and first[1] is fake and first[2] == fake.world and first[5] == 360.0
    assert (sorted(first[3]), sorted(first[4])) == ([1, 2, 3], [4, 5])


def test_ac10_firing_series_contact_tick_and_unit_seconds_come_from_the_counts(seam):
    """AC-10: firing = (tick, able0, able1) at 0 and every sample_every ticks; seconds = sum(able) * sample_every / 20."""
    _table(seam, {6: (4, 0), 9: (2, 1)})
    res, _ = run(S(G(0, count=2), G(1), max_ticks=12, sample_every=3))
    ticks = [t for t, _a, _b in res.firing]
    by_tick = {t: (a, b) for t, a, b in res.firing}
    assert ticks == [0, 3, 6, 9, 12]       # AC-10 Readings: the final tick (12, a multiple of 3) is sampled too
    assert by_tick[6] == (4, 0) and by_tick[9] == (2, 1) and by_tick[3] == (0, 0)
    assert res.first_contact_tick == 6
    assert res.firing_unit_seconds == pytest.approx((6 * 3 / TICKS_PER_SECOND, 1 * 3 / TICKS_PER_SECOND))


@pytest.mark.parametrize("table,expected", [({}, -1), ({0: (0, 1)}, 0), ({10: (0, 2)}, 10)])
def test_ac10_first_contact_tick_is_first_sample_with_anyone_able_or_minus_one(seam, table, expected):
    """AC-10: -1 when never; the first sampled tick where able0 + able1 > 0 otherwise (sample_every 5)."""
    _table(seam, table)
    res, _ = run(S(G(0), G(1), max_ticks=20, sample_every=5))
    assert res.first_contact_tick == expected
    assert (res.firing_unit_seconds == (0.0, 0.0)) == (expected == -1)


# The two end-to-end tests that read the real count through a FakeEngine (near / far / blocked / other layer; a derived
# longer reach) belong to the count itself: LAB-REV2-L1 tests/skilllab/test_firing.py and integration/test_firing_real.py.
# fight() only forwards the seam (above); retired here by the L1/L2 seam of the 2026-10-14 contract.


# ================================================================ Readings added after the spec ruling

def test_ac5_new_world_is_called_before_any_other_engine_call_that_needs_a_world():
    """AC-5/AC-3 (Readings): new_world(seed) comes before disable_abilities, register_unit_type, type_stats and every spawn."""
    types = {"Long": {"base": "Vanguard", "scale": {"attack_range": 2.0}}}
    _, fake = run(S(G(0, "Long"), G(1), unit_types=types, max_ticks=2))
    names = [c[0] for c in fake.calls]
    for later in ("disable_abilities", "register_unit_type", "type_stats", "spawn"):
        assert names.index("new_world") < names.index(later)


def test_ac5_ids_of_registered_types_go_in_order_of_first_use():
    """AC-5 (Readings): ids >= 100 follow the order the types are first used by a group, not the unit_types order."""
    types = {"A": dict(FULL), "B": {"base": "Vanguard", "scale": {"attack_range": 2.0}}}
    _, fake = run(S(G(0, "B"), G(0, "A", x=-200.0), G(1), unit_types=types, max_ticks=2))
    tid_b, tid_a = fake.spawn_log()[0][1], fake.spawn_log()[1][1]
    _, fake = run(S(G(0, "A"), G(0, "B", x=-200.0), G(1), unit_types=types, max_ticks=2))
    tid_a2, tid_b2 = fake.spawn_log()[0][1], fake.spawn_log()[1][1]
    assert 100 <= tid_b < tid_a and 100 <= tid_a2 < tid_b2


def test_ac5_unknown_unit_name_raises_valueerror_from_type_id_unwrapped_and_the_world_is_freed():
    """AC-5 (Readings): a name that is neither in unit_types nor built-in raises ValueError (the engine's own), and the world is freed."""
    fake = FakeEngine()
    with pytest.raises(ValueError) as exc:
        fight(S(G(0, "Zebra"), G(1), max_ticks=3), 0, False, engine=fake)
    assert "Zebra" in str(exc.value) and type(exc.value) is ValueError
    assert len(fake.worlds_freed) == fake.worlds_made


@pytest.mark.parametrize("entry", [
    {"base": "Vanguard", "scale": {"no_such_stat": 2.0}},
    {"base": "Vanguard", "set": {"no_such_stat": 2.0}},
])
def test_ac5_derived_entry_touching_a_stat_its_base_lacks_raises_valueerror(entry):
    """AC-5 (Readings): scale or set naming a stat the base type lacks raises ValueError."""
    fake = FakeEngine()
    with pytest.raises(ValueError):
        fight(S(G(0, "Odd"), G(1), unit_types={"Odd": entry}, max_ticks=3), 0, False, engine=fake)
    assert len(fake.worlds_freed) == fake.worlds_made


@pytest.mark.parametrize("groups", [
    (G(0, count=0), G(1)),
    (G(0), G(1, count=0)),
    (G(0),),
    (G(1),),
])
def test_ac5_a_side_with_no_units_raises_valueerror(groups):
    """AC-5 (Readings): count 0 on a side, or no group for a side, raises ValueError."""
    fake = FakeEngine()
    with pytest.raises(ValueError):
        fight(S(*groups, max_ticks=3), 0, False, engine=fake)
    assert len(fake.worlds_freed) == fake.worlds_made


@pytest.mark.parametrize("field", ["max_ticks", "sample_every"])
@pytest.mark.parametrize("value", [0, -1])
def test_ac5_max_ticks_sample_every_below_one_raise_valueerror(field, value):
    """AC-5 (Readings): max_ticks or sample_every below 1 raises ValueError (stalemate_ticks is no longer a field, Q-LAB-03)."""
    kw = {"max_ticks": 5, "sample_every": 5}
    kw[field] = value
    fake = FakeEngine()
    with pytest.raises(ValueError):
        fight(S(G(0), G(1), **kw), 0, False, engine=fake)
    assert len(fake.worlds_freed) == fake.worlds_made


def test_ac5_sample_every_one_is_valid_and_samples_every_tick():
    """AC-5/10 (Readings): sample_every = 1 is the lowest valid value (not rejected); every tick 0..max_ticks is sampled."""
    res, _ = run(S(G(0), G(1), max_ticks=4, sample_every=1))
    assert res.outcome == "cap" and [t for t, _a, _b in res.firing] == [0, 1, 2, 3, 4]


def test_ac5_max_ticks_one_is_valid_and_caps_after_one_step():
    """AC-5/9 (Readings): max_ticks = 1 is accepted; both alive after one step is a cap at tick 1."""
    res, fake = run(S(G(0), G(1), max_ticks=1, sample_every=5))
    assert (res.outcome, res.ticks, fake.step_count) == ("cap", 1, 1)


@pytest.mark.parametrize("order,call", [("attack_move", "order_attack_move"), ("move", "order_move")])
def test_ac5_order_with_no_goal_goes_to_the_anchor_of_the_first_group_of_the_other_side(order, call):
    """AC-5 (Readings): goal None (attack_move or move) targets the first group's anchor of the other side."""
    setup = S(G(0, x=-300.0, y=11.0, order=order), G(1, x=250.0, y=-22.0, order=order),
              G(1, x=400.0, y=99.0, order=order), max_ticks=3)
    _, fake = run(setup)
    first_side0 = [c for c in fake.calls_named(call) if c[2] == [1]]
    side1_first = [c for c in fake.calls_named(call) if c[2] == [2]]
    assert [(c[3], c[4]) for c in first_side0] == [(250.0, -22.0)]
    assert [(c[3], c[4]) for c in side1_first] == [(-300.0, 11.0)]


def test_ac5_world_is_freed_even_when_the_engine_raises_mid_fight():
    """AC-5 (Readings): freed in a finally, so a step that raises still frees the world once."""
    def boom(t, f):
        if t == 2:
            raise RuntimeError("engine fell over")

    fake = FakeEngine(script=boom)
    with pytest.raises(RuntimeError, match="fell over"):
        fight(S(G(0), G(1), max_ticks=10), 0, False, engine=fake)
    assert fake.worlds_freed == [fake.world]


def test_ac8_strength_is_not_clamped_above_one():
    """AC-8 (Readings): a unit above its starting hp counts above 1 (hp 150 of 100 -> 1.5)."""
    res, _ = run(two_vs_four(), script=lambda t, f: f.set_hp(f.units_of(0)[0], 150) if t == 1 else None)
    assert res.strength_left == pytest.approx(((1.5 + 1.0) / 2, 1.0)) and res.margin == pytest.approx(0.25)


def test_ac9_elimination_wins_over_cap_on_the_same_tick():
    """AC-9 (Readings): a wipe-out on the very tick the cap lands is still "side0"."""
    def kill_last(t, f):
        if t == 9:
            kill(f, 1)

    res, _ = run(S(G(0), G(1), max_ticks=10), script=kill_last)
    assert (res.outcome, res.ticks) == ("side0", 10)


@pytest.mark.parametrize("max_ticks,sample_every,expected", [(12, 3, [0, 3, 6, 9, 12]), (11, 3, [0, 3, 6, 9]),
                                                             (5, 5, [0, 5]), (4, 5, [0])])
def test_ac10_a_sample_is_also_taken_on_the_final_tick_when_it_is_a_multiple_of_sample_every(max_ticks, sample_every, expected):
    """AC-10 (Readings): final tick sampled iff it is a multiple of sample_every (never a sample off the grid)."""
    res, _ = run(S(G(0), G(1), max_ticks=max_ticks, sample_every=sample_every))
    assert [t for t, _a, _b in res.firing] == expected


@pytest.mark.parametrize("script,outcome,ticks,expected", [
    (None, "cap", 12, [0, 5, 10]),                                                       # cap on a non-multiple: no sample off the grid
    (lambda t, f: kill(f, 1) if t == 9 else None, "side0", 10, [0, 5, 10]),               # elimination on a multiple
    (lambda t, f: kill(f, 0) if t == 4 else None, "side1", 5, [0, 5]),                    # elimination on a multiple
    (lambda t, f: (kill(f, 0), kill(f, 1)) if t == 9 else None, "draw", 10, [0, 5, 10]),  # mutual wipe-out on a multiple
    (lambda t, f: kill(f, 1) if t == 6 else None, "side0", 7, [0, 5]),                    # control: elimination off the grid
])
def test_ac10_final_tick_sample_also_holds_when_the_fight_ends_by_elimination(script, outcome, ticks, expected):
    """AC-10 (Readings): the final tick is sampled when it is a multiple of sample_every whatever ended the fight
    (elimination exactly on a multiple, mutual wipe-out); an elimination off the grid adds no sample."""
    setup = S(G(0), G(1), max_ticks=12, sample_every=5)
    res, _ = run(setup, script=script)
    assert (res.outcome, res.ticks) == (outcome, ticks)
    assert [t for t, _a, _b in res.firing] == expected


def test_ac10_fight_hands_count_able_every_spawned_id_even_after_units_die(seam):
    """AC-10 (Readings): units0/units1 hold every spawned id on every call; count_able, not fight, skips the dead."""
    run(S(G(0, count=2), G(1, count=3), max_ticks=10, sample_every=5),
        script=lambda t, f: f.set_hp(f.units_of(1)[0], 0) if t == 2 else None)
    seen = seam.calls_named("count_able")
    assert len(seen) >= 2
    assert all(sorted(c[3]) == [1, 2] and sorted(c[4]) == [3, 4, 5] for c in seen)
