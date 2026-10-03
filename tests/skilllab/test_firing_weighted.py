# spec: docs/northstar/plans/skilllab-plan.md::Phase S::item 8 (unit-type-weighted firing count, side sight, reach)
"""count_able_weighted, unit_weight and the Setup.weighted wiring in fight, on fake engines."""
import inspect
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for _p in (ROOT, Path(__file__).resolve().parent):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import pytest  # noqa: E402
import scripts.skilllab.fight as fight_mod  # noqa: E402
import scripts.skilllab.formations as formations_mod  # noqa: E402
from fakes import FakeEngine  # noqa: E402
from fakes_weighted_target import WeightedTargetFakeEngine  # noqa: E402
from scripts.skilllab.contract import TICKS_PER_SECOND, Group, Setup  # noqa: E402
from scripts.skilllab.firing import count_able_weighted, unit_weight  # noqa: E402
from scripts.skilllab.fight import fight  # noqa: E402
from scripts.skilllab.rows import fight_row  # noqa: E402


def world(**kw):
    """Shooter s (side 0) at the origin, enemy e (side 1) 50 away on the same layer; range 100 each."""
    fake = WeightedTargetFakeEngine(**kw)
    w = fake.new_world(0)
    vg = fake.type_id("Vanguard")
    s = fake.spawn(w, vg, 0, 0.0, 0.0, 0)
    e = fake.spawn(w, vg, 1, 50.0, 0.0, 0)
    return fake, w, s, e, {s: 100.0, e: 100.0}, {s: 2.0, e: 3.0}


def able(fake, w, s, e, ranges, weights, **kw):
    return count_able_weighted(fake, w, [s], [e], ranges, weights, **kw)


def test_positive_control_both_sides_able_and_weights_are_the_sums():
    """item 8: with every clause holding, each side reads its unit's weight (a float)."""
    fake, w, s, e, ranges, weights = world()
    out = able(fake, w, s, e, ranges, weights)
    assert out == (2.0, 3.0) and all(isinstance(v, float) for v in out)


def test_weights_sum_over_able_units():
    """item 8: the count is the sum of weights of able units only; a unit out of reach adds nothing."""
    fake, w, s, e, ranges, weights = world()
    vg = fake.type_id("Vanguard")
    s2 = fake.spawn(w, vg, 0, 10.0, 0.0, 0)
    s3 = fake.spawn(w, vg, 0, 900.0, 0.0, 0)
    ranges.update({s2: 100.0, s3: 100.0})
    weights.update({s2: 0.5, s3: 7.0})
    assert count_able_weighted(fake, w, [s, s2, s3], [e], ranges, weights) == (2.5, 3.0)


def test_clause_a_other_layer_fails_with_default_reach_and_holds_with_reach():
    """item 8 (a): reach None means same layer only; a layer-1 enemy removes the shooter; reach (1, 0) restores it."""
    fake, w, s, e, ranges, weights = world()
    fake.units[e]["layer"] = 1
    assert able(fake, w, s, e, ranges, weights) == (0.0, 0.0)
    assert able(fake, w, s, e, ranges, weights, reach={s: (1, 0), e: (0, 0)}) == (2.0, 0.0)


def test_reach_up_down_asymmetry():
    """item 8 (a): a shooter with reach (1, 0) fires one layer up but not one layer down."""
    fake, w, s, e, ranges, weights = world()
    fake.units[s]["layer"] = 1
    fake.units[e]["layer"] = 2
    reach = {s: (1, 0), e: (0, 0)}
    assert able(fake, w, s, e, ranges, weights, reach=reach)[0] == 2.0
    fake.units[e]["layer"] = 0
    assert able(fake, w, s, e, ranges, weights, reach=reach)[0] == 0.0
    assert able(fake, w, s, e, ranges, weights, reach={s: (0, 1), e: (0, 0)})[0] == 2.0
    fake.units[e]["layer"] = 3                 # two up is beyond a reach of one
    assert able(fake, w, s, e, ranges, weights, reach={s: (1, 1), e: (0, 0)})[0] == 0.0


def test_clause_b_range_is_less_or_equal():
    """item 8 (b): at exactly the range the shooter counts; a hair beyond it does not; per-unit ranges."""
    fake, w, s, e, ranges, weights = world()
    ranges[s] = 50.0
    assert able(fake, w, s, e, ranges, weights)[0] == 2.0
    ranges[s] = 49.9999
    assert able(fake, w, s, e, ranges, weights)[0] == 0.0
    assert able(fake, w, s, e, ranges, weights)[1] == 3.0


def test_clause_c_no_engine_target_removes_the_shooter_even_with_an_enemy_in_range_and_visible():
    """item 8b: a unit the engine has given no target (0) counts nothing, however visible the enemy; the other side is unchanged."""
    fake, w, s, e, ranges, weights = world(can_see_fn=lambda f, o, t: True)
    fake.set_target(s, 0)
    assert able(fake, w, s, e, ranges, weights) == (0.0, 3.0)
    fake.set_target(s, e)
    assert able(fake, w, s, e, ranges, weights) == (2.0, 3.0)


def test_clause_d_can_shoot_false_removes_the_shooter():
    """item 8 (d): a blocked pair removes that shooter; the reverse direction still counts."""
    fake, w, s, e, ranges, weights = world()
    fake.block(s, e)
    assert able(fake, w, s, e, ranges, weights) == (0.0, 3.0)


def test_long_range_unit_counts_as_soon_as_the_engine_gave_it_a_target_without_a_spotter():
    """item 8b: the engine decides who has a target; a long-range unit with its target counts, a friend's sight is not read."""
    fake = WeightedTargetFakeEngine(can_see_fn=lambda f, o, t: False)       # nobody sees anybody by the lab's old rule
    w = fake.new_world(0)
    vg = fake.type_id("Vanguard")
    bomb = fake.spawn(w, vg, 0, 0.0, 0.0, 0)
    e = fake.spawn(w, vg, 1, 200.0, 0.0, 0)
    ranges, weights = {bomb: 250.0, e: 5.0}, {bomb: 4.0, e: 1.0}
    fake.set_target(bomb, 0)
    assert count_able_weighted(fake, w, [bomb], [e], ranges, weights)[0] == 0.0       # not yet acquired
    fake.set_target(bomb, e)
    assert count_able_weighted(fake, w, [bomb], [e], ranges, weights)[0] == 4.0       # acquired, no spotter
    assert not fake.calls_named("can_see")


def test_dead_units_contribute_nothing_and_the_engine_is_never_asked_about_a_dead_shooter():
    """item 8b: a dead shooter and a dead target drop out; unit_target is never asked of a unit not in the living set."""
    fake, w, s, e, ranges, weights = world()
    fake.set_hp(e, 0)
    assert able(fake, w, s, e, ranges, weights) == (0.0, 0.0)
    fake, w, s, e, ranges, weights = world()
    fake.set_hp(s, 0)
    assert able(fake, w, s, e, ranges, weights) == (0.0, 0.0)
    fake, w, s, e, ranges, weights = world()
    vg = fake.type_id("Vanguard")
    dead = fake.spawn(w, vg, 0, 5.0, 0.0, 0)
    ranges[dead], weights[dead] = 100.0, 1.0
    fake.set_hp(dead, 0)
    count_able_weighted(fake, w, [s, dead], [e], ranges, weights)
    assert all(c[2] != dead for c in fake.calls_named("unit_target"))


def test_the_count_never_asks_about_sight():
    """item 8b: no can_see calls, however many units are on the field."""
    fake = WeightedTargetFakeEngine()
    w = fake.new_world(0)
    vg = fake.type_id("Vanguard")
    a = [fake.spawn(w, vg, 0, float(i), 0.0, 0) for i in range(4)]
    b = [fake.spawn(w, vg, 1, 30.0 + i, 0.0, 0) for i in range(3)]
    ranges = {u: 100.0 for u in a + b}
    weights = {u: 1.0 for u in a + b}
    assert count_able_weighted(fake, w, a, b, ranges, weights) == (4.0, 3.0)
    assert not fake.calls_named("can_see")


def test_swapping_sides_swaps_the_tuple():
    """item 8: symmetry; the same world with the lists swapped reads the tuple reversed."""
    fake, w, s, e, ranges, weights = world()
    fake.block(s, e)
    assert count_able_weighted(fake, w, [s], [e], ranges, weights) == (0.0, 3.0)
    assert count_able_weighted(fake, w, [e], [s], ranges, weights) == (3.0, 0.0)


def test_deterministic():
    """item 8: two calls on the same world return the same tuple."""
    fake, w, s, e, ranges, weights = world()
    assert able(fake, w, s, e, ranges, weights) == able(fake, w, s, e, ranges, weights)


def test_weights_argument_is_required():
    """item 8: weights has no default (omitting it is a TypeError); reach defaults to None."""
    sig = inspect.signature(count_able_weighted)
    assert sig.parameters["weights"].default is inspect.Parameter.empty
    assert sig.parameters["reach"].default is None
    fake, w, s, e, ranges, _ = world()
    with pytest.raises(TypeError):
        count_able_weighted(fake, w, [s], [e], ranges)


def test_unit_weight_is_damage_over_interval_exactly():
    """item 8: unit_weight = base_damage / attack_interval from the type stats dict."""
    assert unit_weight({"base_damage": 10.0, "attack_interval": 20.0}) == 0.5
    assert unit_weight({"base_damage": 3.0, "attack_interval": 4.0, "max_hp": 9.0}) == 0.75
    assert unit_weight({"base_damage": 0.0, "attack_interval": 1.0}) == 0.0


@pytest.mark.parametrize("interval", [0.0, -1.0])
def test_unit_weight_nonpositive_interval_raises(interval):
    """item 8: attack_interval <= 0 is a ValueError."""
    with pytest.raises(ValueError):
        unit_weight({"base_damage": 10.0, "attack_interval": interval})


# ---- fight wiring ----

@pytest.fixture(autouse=True)
def place_stub(monkeypatch):
    def stub(kind, n, x, y, facing_deg, params):
        return [(x + 7.0 * i, y) for i in range(n)]
    monkeypatch.setattr(formations_mod, "place", stub)
    monkeypatch.setattr(fight_mod, "place", stub, raising=False)


def G(side, count, x):
    return Group(side=side, unit="Vanguard", count=count, formation="line", x=x, y=0.0,
                 facing_deg=0.0, layer=0, order="attack_move", params={"spacing": 7.0})


def S(**kw):
    return Setup(groups=(G(0, 2, -30.0), G(1, 1, 30.0)), unit_types={}, max_ticks=10, stalemate_ticks=1000,
                 sample_every=5, **kw)


def test_setup_weighted_defaults_false_and_result_weighted_is_none():
    """item 8: the field is off by default and a default fight neither records weighted nor touches can_see / profile_reach."""
    assert Setup(groups=(), unit_types={}).weighted is False
    fake = FakeEngine()
    r = fight(S(), 0, False, engine=fake)
    assert r.weighted is None
    assert not fake.calls_named("profile_reach") and not fake.calls_named("can_see")


def test_default_result_is_unchanged_by_the_new_field():
    """item 8: weighted=False gives the same result as before: equal across runs, firing series untouched."""
    a, b = fight(S(), 0, False, engine=FakeEngine()), fight(S(weighted=False), 0, False, engine=FakeEngine())
    assert a == b and a.firing[0] == (0, 2, 1)


def test_weighted_series_is_sampled_at_the_firing_ticks():
    """item 8: weighted is [(tick, w0, w1)] at the same ticks as firing; 2 units of 0.5 against 1 of 0.5."""
    fake = WeightedTargetFakeEngine()
    r = fight(S(weighted=True), 0, False, engine=fake)
    assert [t for t, _, _ in r.weighted] == [t for t, _, _ in r.firing] == [0, 5, 10]
    assert r.weighted == [(0, 1.0, 0.5), (5, 1.0, 0.5), (10, 1.0, 0.5)]
    assert fake.calls_named("profile_reach")


def test_weighted_series_is_deterministic():
    """item 8: same setup and seed give the same weighted series."""
    run = lambda: fight(S(weighted=True), 3, False, engine=WeightedTargetFakeEngine()).weighted
    assert run() == run()


def test_fight_row_weighted_columns_only_when_recorded():
    """item 8: weighted_unit_seconds_0/_1 = sum(w * sample_every / 20); absent, not blank, when not weighted."""
    on = fight_row(fight(S(weighted=True), 0, False, engine=WeightedTargetFakeEngine()), tag="x")
    assert on["weighted_unit_seconds_0"] == pytest.approx(3 * 1.0 * 5 / TICKS_PER_SECOND)
    assert on["weighted_unit_seconds_1"] == pytest.approx(3 * 0.5 * 5 / TICKS_PER_SECOND)
    off = fight_row(fight(S(), 0, False, engine=FakeEngine()), tag="x")
    assert "weighted_unit_seconds_0" not in off and "weighted_unit_seconds_1" not in off


# ---- Engine.profile_reach binding (stubbed library) ----

class _Lib:
    def __init__(self, ret=0, write=None):
        self.ret, self.write, self.seen = ret, write, None
        self.om_unit_profile_reach = self._call

    def _call(self, w, t, up, down):
        self.seen = (t, up, down)
        ref = lambda p: p._obj if hasattr(p, "_obj") else p.contents
        if self.write:
            ref(up).value, ref(down).value = self.write
        return self.ret


def _engine(lib):
    from scripts.skilllab.engine import Engine
    e = Engine.__new__(Engine)
    e._lib = lib
    return e


def test_profile_reach_returns_the_pair_the_library_wrote():
    """item 8: profile_reach returns (up, down) as ints."""
    lib = _Lib(write=(2, 1))
    out = _engine(lib).profile_reach(None, 4)
    assert out == (2, 1) and all(type(v) is int for v in out) and lib.seen[0] == 4


def test_profile_reach_initialises_up_and_down_to_zero_for_the_inert_stub():
    """item 8: the library's stub writes nothing; the binding must still read (0, 0), not garbage."""
    assert _engine(_Lib()).profile_reach(None, 0) == (0, 0)


def test_profile_reach_nonzero_return_raises_value_error():
    """item 8: a nonzero return (unknown type) is a ValueError."""
    with pytest.raises(ValueError):
        _engine(_Lib(ret=-1)).profile_reach(None, 999)
