# spec: docs/northstar/plans/2026-10-14-skill-lab-rev2-spec.md rulings 1, 2, 5, 6 and "Lab data contract" (LAB-REV2-L2); register Q-LAB-03
"""fight() ends by elimination only, and scores the firing count against the result (spec 2026-10-14).

Ruling 1 (Q-LAB-03): outcome is one of side0, side1, draw (both die on one tick) or cap (a bug detector, never a result);
hold, blind window, draw band, silence, quiet-from-first-damage, stalemate, mop-up and re-issue are retired.
Ruling 5: two predictions per fight (count-only, type-weighted) over the opening window after first contact, compared
with who was left standing. Ruling 6: attack-move is one order per unit (`orders_per_unit`), toward the shared `point`.
The firing counts come through the L1/L2 seam (fakes.Seam), so these tests need no engine and no compiler.

Names the contract leaves open, fixed here (the builder matches them, or the test writer is told):
  - FightResult.winner is the string "side0" / "side1" (the type it already has), None for draw and cap.
  - The opening window is the half-open range [first_contact_tick, first_contact_tick + 40): a sample at the tick
    first_contact_tick + 40 is outside it (DRAFT-opening-window-ticks 40, Westley to confirm).
  - A window's unit-seconds are the sum of the samples inside it times sample_every / 20, as the whole fight's are.
  - OM_TP_FIRING_ARC_DEG is set on the world only when Setup.firing_arc_deg is below 360, so a library without the
    parameter (before LAB-REV2-E0) still runs every default fight.
"""
import dataclasses
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
from fakes_trace import PARAMS, TraceFakeEngine  # noqa: E402
from scripts.skilllab.contract import FightResult, Group, Setup  # noqa: E402
from scripts.skilllab.fight import fight  # noqa: E402

WINDOW = 40            # DRAFT-opening-window-ticks (spec ruling 5)
TICKS_PER_SECOND = 20


@pytest.fixture(autouse=True)
def stub_place(monkeypatch):
    def stub(kind, n, x, y, facing_deg, params):
        return [(x + 7.0 * i, y) for i in range(n)]

    monkeypatch.setattr(formations_mod, "place", stub)
    monkeypatch.setattr(fight_mod, "place", stub, raising=False)


def G(side, count=1, **kw):
    base = dict(side=side, unit="Vanguard", count=count, formation="line", x=-300.0 if side == 0 else 300.0, y=0.0,
                facing_deg=0.0 if side == 0 else 180.0, layer=0, order="attack_move", goal=None, params={"spacing": 30.0})
    base.update(kw)
    return Group(**base)


def S(max_ticks=50, sample_every=5, count=1, **kw):
    return Setup(groups=(G(0, count), G(1, count)), unit_types={}, max_ticks=max_ticks, sample_every=sample_every, **kw)


def run(setup, script=None, engine_cls=FakeEngine):
    fake = engine_cls(script=script)
    return fight(setup, 0, False, engine=fake), fake


def kill(fake, faction):
    for u in fake.units_of(faction):
        fake.set_hp(u, 0)


# ---------------------------------------------------------------- ruling 1: elimination only

def _side0(seam):
    return run(S(), lambda t, f: kill(f, 1) if t == 3 else None)[0]


def _side1(seam):
    return run(S(), lambda t, f: kill(f, 0) if t == 3 else None)[0]


def _draw(seam):
    return run(S(), lambda t, f: (kill(f, 0), kill(f, 1)) if t == 3 else None)[0]


def _cap(seam):
    return run(S(max_ticks=30))[0]


@pytest.mark.parametrize("scenario,outcome,winner", [(_side0, "side0", "side0"), (_side1, "side1", "side1"),
                                                     (_draw, "draw", None), (_cap, "cap", None)])
def test_ruling_1_outcome_is_one_of_four_and_winner_is_the_survivor(seam, scenario, outcome, winner):
    """Q-LAB-03 / ruling 1: elimination gives the survivor as winner; draw (both die on one tick) and cap give None."""
    r = scenario(seam)
    assert (r.outcome, r.winner) == (outcome, winner)


def test_ruling_1_draw_is_both_dead_on_one_tick_with_zero_margin(seam):
    """Ruling 1: a double kill is a draw: no survivors, margin 0.0, one tick after the kill script ran."""
    r = _draw(seam)
    assert (r.outcome, r.survivors, r.strength_left, r.margin, r.ticks) == ("draw", (0, 0), (0.0, 0.0), 0.0, 4)


def test_ruling_1_a_quiet_fight_is_not_ended_by_quiet(seam):
    """Q-LAB-03: no stalemate window. 450 ticks without an hp change, then a kill at tick 450: the fight is side0 at 451
    (red on the old code: it ended 'stalemate' after 400 quiet ticks)."""
    r, _ = run(S(max_ticks=1000), lambda t, f: kill(f, 1) if t == 450 else None)
    assert (r.outcome, r.ticks, r.winner) == ("side0", 451, "side0")


def test_ruling_1_a_quiet_fight_to_the_cap_is_a_cap_at_max_ticks(seam):
    """Q-LAB-03: a fight nobody can end runs to max_ticks and is labelled cap, a defect to trace, not a result."""
    r, fake = run(S(max_ticks=100))
    assert (r.outcome, r.ticks, fake.step_count, r.winner) == ("cap", 100, 100, None)


def test_ruling_1_cap_is_never_a_result_so_it_has_no_agreement(seam):
    """Ruling 1 and 5: a capped fight has winner None and agreement 'n/a' even when the counts favour a side."""
    seam.able = lambda t: (3, 0)
    r, _ = run(S(max_ticks=60))
    assert (r.outcome, r.winner, r.agreement) == ("cap", None, "n/a")
    assert r.predicted_count == "side0"      # the prediction is still made and recorded


def test_ruling_1_elimination_on_the_last_step_still_wins_and_one_step_later_is_a_cap(seam):
    """Ruling 1: the cap fires only with both sides alive."""
    setup = S(max_ticks=5)
    on_last, _ = run(setup, lambda t, f: kill(f, 1) if t == 4 else None)
    too_late, fake = run(setup, lambda t, f: kill(f, 1) if t == 5 else None)
    assert (on_last.outcome, on_last.ticks) == ("side0", 5)
    assert (too_late.outcome, too_late.ticks, fake.step_count) == ("cap", 5, 5)


def test_ruling_1_the_retired_outcome_names_are_never_produced(seam):
    """Ruling 1: held, decided and stalemate are not outcomes; over the four scenarios only the four names appear."""
    seen = {s(seam).outcome for s in (_side0, _side1, _draw, _cap)}
    assert seen == {"side0", "side1", "draw", "cap"}


def test_ruling_1_max_ticks_and_sample_every_below_one_raise_and_free_the_world(seam):
    """Ruling 1: max_ticks (the cap) and sample_every below 1 raise ValueError; stalemate_ticks is no longer a field."""
    for kw in ({"max_ticks": 0}, {"max_ticks": -1}, {"sample_every": 0}, {"sample_every": -1}):
        fake = FakeEngine()
        with pytest.raises(ValueError):
            fight(S(**kw), 0, False, engine=fake)
        assert len(fake.worlds_freed) == fake.worlds_made


# ---------------------------------------------------------------- Setup and FightResult fields

RETIRED_SETUP_FIELDS = ("decided_by_survivors", "silence_ticks", "hold_anchor", "hold_ticks", "defender_side", "mopup",
                        "mopup_interval_ticks", "quiet_from_first_damage", "approach", "stalemate_ticks", "objective",
                        "start_distance")


def test_setup_loses_the_retired_fields():
    """Spec 'Lab data contract' / Q-LAB-03: the twelve retired Setup fields are gone."""
    fields = {f.name for f in dataclasses.fields(Setup)}
    assert not fields & set(RETIRED_SETUP_FIELDS), sorted(fields & set(RETIRED_SETUP_FIELDS))


@pytest.mark.parametrize("name", RETIRED_SETUP_FIELDS)
def test_setup_refuses_a_retired_field_as_a_keyword(name):
    """Q-LAB-03: passing a retired field is a TypeError, not a silent no-op (positive control below)."""
    with pytest.raises(TypeError):
        Setup(groups=(), unit_types={}, **{name: 1})


def test_positive_control_setup_still_takes_the_kept_fields():
    s = Setup(groups=(), unit_types={}, max_ticks=7, sample_every=2, trace=True, states=True, abilities=True)
    assert (s.max_ticks, s.sample_every, s.trace, s.states, s.abilities) == (7, 2, True, True, True)


def test_setup_gains_point_orders_per_unit_firing_arc_cone_and_max_ticks_default():
    """Spec: point, orders_per_unit=True, firing_arc_deg=360.0, cone={} and max_ticks=12000 (the cap, bug detector only)."""
    names = {f.name for f in dataclasses.fields(Setup)}
    assert {"point", "orders_per_unit", "firing_arc_deg", "cone", "max_ticks"} <= names
    s = Setup(groups=(), unit_types={})
    assert (s.orders_per_unit, s.firing_arc_deg, s.cone, s.max_ticks) == (True, 360.0, {}, 12000)
    assert s.cone is not Setup(groups=(), unit_types={}).cone      # a fresh dict per Setup


def test_setup_takes_the_new_fields_as_keywords():
    s = Setup(groups=(), unit_types={}, point=(10.0, -4.0), orders_per_unit=False, firing_arc_deg=120.0,
              cone={"Bombard": (300.0, 45.0, 1.0)})
    assert (s.point, s.orders_per_unit, s.firing_arc_deg, s.cone) == ((10.0, -4.0), False, 120.0, {"Bombard": (300.0, 45.0, 1.0)})


def test_fight_result_has_the_contract_fields():
    names = {f.name for f in dataclasses.fields(FightResult)}
    need = {"outcome", "winner", "margin", "strength_left", "survivors", "heads", "ticks", "first_contact_tick", "firing",
            "firing_unit_seconds", "firing_window", "weighted_unit_seconds", "weighted_window", "predicted_count",
            "predicted_type", "agreement", "states"}
    assert need <= names, sorted(need - names)


# ---------------------------------------------------------------- ruling 5: window, predictions, agreement

def _scripted(win0, win1, later0=0, later1=0, w_win=None, w_later=None, kill_side=1, kill_tick=100, sample_every=5, count=1):
    """A fight whose first contact is tick 10. Inside the window [10, 50) the able counts are (win0, win1); from tick 50 on
    (later0, later1). The tick-50 sample is outside the window on purpose. kill_side dies at kill_tick (None: nobody)."""
    def able(t):
        if t < 10:
            return 0, 0
        return (win0, win1) if t < 10 + WINDOW else (later0, later1)

    def weighted(t):
        if t < 10:
            return 0.0, 0.0
        w_in = w_win if w_win is not None else (win0, win1)
        w_out = w_later if w_later is not None else (later0, later1)
        return w_in if t < 10 + WINDOW else w_out

    def script(t, f):
        if kill_side is not None and t == kill_tick - 1:
            kill(f, kill_side)
    return able, weighted, script


def _fight(seam, **kw):
    able, weighted, script = _scripted(**{k: v for k, v in kw.items() if k not in ("max_ticks",)})
    seam.able, seam.weighted = able, weighted
    r, _ = run(S(max_ticks=kw.get("max_ticks", 200)), script)
    return r


def test_ruling_5_first_contact_is_the_first_sample_where_someone_is_able(seam):
    r = _fight(seam, win0=3, win1=1)
    assert r.first_contact_tick == 10
    assert r.firing[0] == (0, 0, 0) and (10, 3, 1) in r.firing


def test_ruling_5_first_contact_is_minus_one_when_nobody_is_ever_able(seam):
    r, _ = run(S(max_ticks=20))
    assert r.first_contact_tick == -1


def test_ruling_5_window_covers_forty_ticks_from_first_contact_and_excludes_the_tick_after(seam):
    """Eight samples (10, 15, ..., 45) at 3 and 1 able; the sample at tick 50 (9, 9) is outside the window, so (6.0, 2.0)."""
    r = _fight(seam, win0=3, win1=1, later0=9, later1=9)
    assert r.firing_window == pytest.approx((3 * 8 * 5 / TICKS_PER_SECOND, 1 * 8 * 5 / TICKS_PER_SECOND))
    assert r.firing_window == pytest.approx((6.0, 2.0))


def test_ruling_5_whole_fight_unit_seconds_still_cover_every_sample(seam):
    """The whole-fight total (a chart) is kept beside the window; the later 9s count there."""
    r = _fight(seam, win0=3, win1=1, later0=9, later1=9)
    expected = tuple(sum(row[1 + s] for row in r.firing) * 5 / TICKS_PER_SECOND for s in (0, 1))
    assert r.firing_unit_seconds == pytest.approx(expected)
    assert r.firing_unit_seconds[0] > r.firing_window[0] and r.firing_unit_seconds[1] > r.firing_window[1]


def test_ruling_5_weighted_window_and_whole_are_always_populated_from_the_weighted_count(seam):
    r = _fight(seam, win0=3, win1=1, later0=9, later1=9, w_win=(2.5, 4.0), w_later=(7.0, 7.0))
    assert r.weighted_window == pytest.approx((2.5 * 8 * 5 / 20, 4.0 * 8 * 5 / 20))
    assert r.weighted_unit_seconds[0] == pytest.approx((2.5 * 8 + 7.0 * len([x for x in r.firing if x[0] >= 50])) * 5 / 20)
    assert isinstance(r.weighted_unit_seconds, tuple) and isinstance(r.weighted_window, tuple)


def test_ruling_5_window_scales_with_sample_every(seam):
    """With sample_every 2 the window holds 20 samples; unit-seconds are the same (3 able for 2 s = 6.0)."""
    able, weighted, script = _scripted(win0=3, win1=1)
    seam.able, seam.weighted = able, weighted
    r, _ = run(S(max_ticks=200, sample_every=2), script)
    # first contact at tick 10 (a multiple of 2); samples 10, 12, ..., 48 are in the window
    assert r.first_contact_tick == 10
    assert r.firing_window == pytest.approx((3 * 20 * 2 / 20, 1 * 20 * 2 / 20))


def test_ruling_5_window_is_zero_when_there_was_no_contact(seam):
    r, _ = run(S(max_ticks=20))
    assert r.firing_window == (0.0, 0.0) and r.weighted_window == (0.0, 0.0)


def test_ruling_5_predictions_name_the_larger_window_total_and_ignore_the_later_fight(seam):
    """Count: side0 (3 v 1 in the window) although side1 leads after tick 50; type-weighted: side1 (4.0 v 2.5)."""
    r = _fight(seam, win0=3, win1=1, later0=0, later1=9, w_win=(2.5, 4.0), w_later=(0.0, 9.0))
    assert (r.predicted_count, r.predicted_type) == ("side0", "side1")
    assert r.firing_unit_seconds[1] > r.firing_unit_seconds[0]       # control: the whole-fight totals would say side1


def test_ruling_5_equal_window_totals_are_a_tie(seam):
    r = _fight(seam, win0=2, win1=2, w_win=(1.5, 1.5))
    assert (r.predicted_count, r.predicted_type) == ("tie", "tie")


@pytest.mark.parametrize("win,w_win,kill_side,expected,agreement", [
    # side 0 wins (side 1 dies)
    ((3, 1), (3.0, 1.0), 1, ("side0", "side0"), "both_right"),
    ((3, 1), (1.0, 3.0), 1, ("side0", "side1"), "count_right_type_wrong"),
    ((1, 3), (3.0, 1.0), 1, ("side1", "side0"), "count_wrong_type_right"),
    ((1, 3), (1.0, 3.0), 1, ("side1", "side1"), "both_wrong"),
    # side 1 wins (side 0 dies): the same table from the other side
    ((1, 3), (1.0, 3.0), 0, ("side1", "side1"), "both_right"),
    ((1, 3), (3.0, 1.0), 0, ("side1", "side0"), "count_right_type_wrong"),
    ((3, 1), (1.0, 3.0), 0, ("side0", "side1"), "count_wrong_type_right"),
    ((3, 1), (3.0, 1.0), 0, ("side0", "side0"), "both_wrong"),
])
def test_ruling_5_agreement_table(seam, win, w_win, kill_side, expected, agreement):
    """Ruling 5: the agreement label names which of the two predictions matched who was left standing."""
    r = _fight(seam, win0=win[0], win1=win[1], w_win=w_win, kill_side=kill_side)
    assert (r.predicted_count, r.predicted_type) == expected
    assert r.agreement == agreement


@pytest.mark.parametrize("win,w_win", [((2, 2), (3.0, 1.0)), ((3, 1), (2.0, 2.0)), ((2, 2), (2.0, 2.0))])
def test_ruling_5_a_tie_in_either_prediction_makes_agreement_na(seam, win, w_win):
    """Spec: 'n/a' when either prediction is a tie (positive control for the table above: the same fight with no tie is scored)."""
    r = _fight(seam, win0=win[0], win1=win[1], w_win=w_win)
    assert r.agreement == "n/a"
    control = _fight(seam, win0=3, win1=1, w_win=(3.0, 1.0))
    assert control.agreement == "both_right"


def test_ruling_5_a_draw_has_agreement_na_but_keeps_its_predictions(seam):
    able, weighted, _ = _scripted(win0=3, win1=1)
    seam.able, seam.weighted = able, weighted
    r, _ = run(S(max_ticks=200), lambda t, f: (kill(f, 0), kill(f, 1)) if t == 99 else None)
    assert (r.outcome, r.agreement) == ("draw", "n/a")
    assert (r.predicted_count, r.predicted_type) == ("side0", "side0")


# ---------------------------------------------------------------- states

def test_states_are_tick_unit_code_triples_from_the_seam_when_requested(seam):
    """Spec: states is [(tick, unit, code)], code the can_engage result against the target of record (-1 when none);
    Setup.states stays the switch. Units are listed in id order, every living unit, every tick."""
    seam.codes = lambda t, u: {1: 0, 2: 3}[u] if t >= 2 else -1
    r, _ = run(S(max_ticks=4, states=True))
    assert all(isinstance(x, tuple) and len(x) == 3 and all(type(v) is int for v in x) for x in r.states)
    by_tick = {}
    for t, u, c in r.states:
        by_tick.setdefault(t, []).append((u, c))
    assert sorted(by_tick) == [0, 1, 2, 3, 4]
    assert by_tick[1] == [(1, -1), (2, -1)] and by_tick[3] == [(1, 0), (2, 3)]


def test_states_are_none_when_not_requested_and_the_seam_is_not_asked(seam):
    r, _ = run(S(max_ticks=4))
    assert r.states is None
    assert seam.calls_named("states") == []


def test_states_list_only_living_units(seam):
    """Spec: states cover the living units; a unit whose hp reads 0 has no entry from the tick it dies (unit 3 dies in step 3)."""
    r, _ = run(S(count=2, max_ticks=8, states=True), lambda t, f: f.set_hp(f.units_of(1)[0], 0) if t == 2 else None)
    assert {u for t, u, c in r.states if t == 0} == {1, 2, 3, 4}
    assert {u for t, u, c in r.states if t >= 3} == {1, 2, 4}


# ---------------------------------------------------------------- the seam call shape

def test_seam_count_able_and_weighted_get_engine_world_every_spawned_id_and_the_arc(seam):
    """Spec seam: firing.count_able(engine, w, units0, units1, arc_deg); fight hands every spawned id (dead ones too)
    and Setup.firing_arc_deg, once per sample tick, tick 0 first."""
    r, fake = run(S(count=2, max_ticks=10, sample_every=5, firing_arc_deg=360.0),
                  lambda t, f: f.set_hp(f.units_of(1)[0], 0) if t == 2 else None)
    for name in ("count_able", "count_weighted"):
        calls = seam.calls_named(name)
        assert [c[6] for c in calls] == [t for t, _a, _b in r.firing]
        assert all(c[1] is fake and c[2] == fake.world for c in calls)
        assert all(sorted(c[3]) == [1, 2] and sorted(c[4]) == [3, 4] for c in calls)
        assert all(c[5] == 360.0 for c in calls)


def test_seam_receives_the_setup_arc(seam):
    run(S(max_ticks=5, firing_arc_deg=120.0), engine_cls=TraceFakeEngine)
    assert {c[5] for c in seam.calls} == {120.0}


def test_fight_does_not_call_the_firing_module_beyond_the_four_seam_functions(seam, monkeypatch):
    """Spec seam: 'fight.py calls these and nothing else from firing.py'. Any other public firing name is poisoned."""
    import scripts.skilllab.firing as firing_mod
    allowed = {"count_able", "count_weighted", "states", "parity"}
    for name in [n for n in dir(firing_mod) if callable(getattr(firing_mod, n)) and not n.startswith("_") and n not in allowed]:
        monkeypatch.setattr(firing_mod, name, lambda *a, _n=name, **k: pytest.fail("fight called firing.%s" % _n))
        monkeypatch.setattr(fight_mod, name, lambda *a, _n=name, **k: pytest.fail("fight called firing.%s" % _n), raising=False)
    r, _ = run(S(max_ticks=10))
    assert r.outcome == "cap"


# ---------------------------------------------------------------- the arc parameter

def test_firing_arc_below_360_is_set_on_the_world(seam):
    """Spec: Setup.firing_arc_deg is set through OM_TP_FIRING_ARC_DEG."""
    r, fake = run(S(max_ticks=3, firing_arc_deg=120.0), engine_cls=TraceFakeEngine)
    pid = PARAMS["OM_TP_FIRING_ARC_DEG"][0]
    assert fake.params[pid] == 120.0
    assert ("set_param", fake.world, pid, 120.0) in fake.calls


def test_the_default_arc_makes_no_param_call_so_a_library_without_the_parameter_still_runs(seam):
    """Control and the reason for the rule above: at 360 the parameter is untouched (E0 may not be on main)."""
    r, fake = run(S(max_ticks=3), engine_cls=TraceFakeEngine)
    assert not fake.calls_named("set_param") and not fake.calls_named("param_id")
    assert r.outcome == "cap"


# ---------------------------------------------------------------- the cone (needs LAB-REV2-E2)

def _has_set_cone():
    try:
        from scripts.skilllab.engine import Engine
    except Exception:
        return False
    return hasattr(Engine, "set_cone")


@pytest.mark.skipif(not _has_set_cone(), reason="needs LAB-REV2-E2 (om_roster_set_cone) and an Engine.set_cone binding; "
                                               "the spec names no lab-side binding, so none exists yet")
def test_cone_entries_are_applied_through_set_cone_once_per_type(seam):
    class ConeFake(FakeEngine):
        def set_cone(self, w, type_id, rng, half_angle, share):
            self.calls.append(("set_cone", w, type_id, rng, half_angle, share))
            return 0

    setup = S(max_ticks=3, cone={"Vanguard": (300.0, 45.0, 1.0)})
    _, fake = run(setup, engine_cls=ConeFake)
    assert [c[2:] for c in fake.calls_named("set_cone")] == [(2, 300.0, 45.0, 1.0)]


# ---------------------------------------------------------------- ruling 6: one order per unit, toward the shared point

def _orders(fake):
    return [(c[2], c[3], c[4]) for c in fake.calls_named("order_attack_move")]


def test_ruling_6_default_issues_one_attack_move_per_unit_to_the_shared_point(seam):
    """Spec: orders_per_unit=True means one order_attack_move call per unit; `point` is the shared attack-move point."""
    setup = S(count=3, max_ticks=2, point=(25.0, -40.0))
    _, fake = run(setup)
    got = _orders(fake)
    assert sorted(ids for ids, _x, _y in got) == [[1], [2], [3], [4], [5], [6]]
    assert all((x, y) == (25.0, -40.0) for _ids, x, y in got)


def test_ruling_6_orders_per_unit_false_is_one_order_for_the_group_at_the_point(seam):
    """Control: the group order (still available until E1 is on main and L4 flips the default) is one call per group."""
    setup = S(count=3, max_ticks=2, point=(25.0, -40.0), orders_per_unit=False)
    _, fake = run(setup)
    got = _orders(fake)
    assert sorted(ids for ids, _x, _y in got) == [[1, 2, 3], [4, 5, 6]]
    assert all((x, y) == (25.0, -40.0) for _ids, x, y in got)


def test_ruling_6_a_group_goal_overrides_the_point_for_that_group(seam):
    setup = Setup(groups=(G(0, 2, goal=(5.0, 6.0)), G(1, 2)), unit_types={}, max_ticks=2, point=(25.0, -40.0))
    _, fake = run(setup)
    goals = {ids[0]: (x, y) for ids, x, y in _orders(fake)}
    assert goals[1] == goals[2] == (5.0, 6.0)
    assert goals[3] == goals[4] == (25.0, -40.0)


def test_ruling_6_per_unit_orders_go_out_before_the_first_step(seam):
    _, fake = run(S(count=2, max_ticks=3, point=(0.0, 0.0)))
    names = [c[0] for c in fake.calls]
    assert max(i for i, n in enumerate(names) if n == "order_attack_move") < names.index("step")


def test_ruling_6_a_guard_group_gets_a_guard_order_not_an_attack_move(seam):
    from fakes_guard import GuardFakeEngine
    setup = Setup(groups=(G(0, 2), G(1, 2, order="guard")), unit_types={}, max_ticks=2, point=(25.0, -40.0))
    _, fake = run(setup, engine_cls=GuardFakeEngine)
    assert [c[2] for c in fake.calls_named("order_guard")] == [[3, 4]]
    assert sorted(ids for ids, _x, _y in _orders(fake)) == [[1], [2]]


# ---------------------------------------------------------------- nothing of the retired rules is left in the loop

def test_no_mop_up_or_reissue_orders_after_the_opening_orders(seam):
    """Q-LAB-03: orders are issued once at tick 0 and never again by the fight loop (a side that stops stays stopped)."""
    r, fake = run(S(count=2, max_ticks=450, point=(0.0, 0.0)))
    assert len(fake.calls_named("order_attack_move")) == 4
    first_step = [c[0] for c in fake.calls].index("step")
    assert all(i < first_step for i, c in enumerate(fake.calls) if c[0] == "order_attack_move")
