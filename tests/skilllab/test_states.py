# spec: docs/northstar/plans/2026-10-02-movement-layers-and-search-plan.md::Phase S (trace states, order ends)
"""Setup.states: per-unit state rows and order_ends, on a scripted StatesFakeEngine (no compiler, no library).

Contract these tests fix:
  Setup.states: bool = False        opt-in. FightResult.states / .order_ends (after weighted_unit_seconds) are None
                                    when False; every other field is unchanged.
  FightResult.states                [(tick, unit, state)] for each living unit at tick 0 and after every step,
                                    ordered by tick then unit id; dead units omitted. state, first match wins:
                                    "can fire"  a living same-layer enemy within range and can_shoot true;
                                    "blocked"   not that, but a living same-layer enemy within range (all unshootable);
                                    "walking"   not those, and engine.unit_destination(w, u) is a tuple;
                                    "no target" otherwise.
  FightResult.order_ends            ((unit, tick), ...) by unit id: the first tick after the unit had a destination
                                    at which it has none. Never-had or never-ended units are absent.
Vanguard range in the fake is 100. Units: side 0 gets ids 1.., then side 1 (swap False).
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
from fakes_states import StatesFakeEngine  # noqa: E402
from scripts.skilllab.contract import FightResult, Group, Setup  # noqa: E402
from scripts.skilllab.fight import fight  # noqa: E402
from scripts.skilllab.rows import fight_row  # noqa: E402

NEAR, FAR = 50.0, 500.0      # distance between a pair; range is 100
STATES = {"can fire", "blocked", "walking", "no target"}


@pytest.fixture(autouse=True)
def place_stub(monkeypatch):
    def stub(kind, n, x, y, facing_deg, params):
        return [(x + 7.0 * i, y) for i in range(n)]

    monkeypatch.setattr(formations_mod, "place", stub)
    monkeypatch.setattr(fight_mod, "place", stub, raising=False)


def G(side, count=1, layer=0):
    return Group(side=side, unit="Vanguard", count=count, formation="line", x=-300.0 if side == 0 else 300.0,
                 y=0.0, facing_deg=0.0 if side == 0 else 180.0, layer=layer, order="attack_move", goal=None,
                 params={"spacing": 30.0})


def S(counts=(1, 1), states=True, trace=False, max_ticks=6, layers=(0, 0), **kw):
    return Setup(groups=(G(0, counts[0], layers[0]), G(1, counts[1], layers[1])), unit_types={},
                 max_ticks=max_ticks, stalemate_ticks=1000, sample_every=1, states=states, trace=trace, **kw)


def pair_at(dist, ids=((1,), (2,))):
    """pos_fn putting every listed unit of side 0 at x=0 and side 1 at x=dist (rows 100 apart in y)."""
    pos = {}
    for row, (a, b) in enumerate(zip(*ids)):
        pos[a] = lambda t, row=row: (0.0, 100.0 * row)
        pos[b] = lambda t, row=row: (dist, 100.0 * row)
    return pos


def run(setup, swap=False, **fake_kw):
    fake = StatesFakeEngine(**fake_kw)
    return fight(setup, 0, swap, engine=fake), fake


def at(result, tick):
    return {u: s for t, u, s in result.states if t == tick}


# ---- the four states and their priority --------------------------------------------------------------------

def test_can_fire_when_an_enemy_is_in_range_and_shootable():
    r, _ = run(S(), pos_fn=pair_at(NEAR))
    assert all(at(r, t) == {1: "can fire", 2: "can fire"} for t in range(r.ticks + 1))


def test_blocked_when_in_range_but_unshootable():
    r, _ = run(S(), pos_fn=pair_at(NEAR), shoot_fn=lambda t, a, b: False)
    assert all(at(r, t) == {1: "blocked", 2: "blocked"} for t in range(r.ticks + 1))


def test_walking_when_out_of_range_with_a_destination():
    r, _ = run(S(), pos_fn=pair_at(FAR), dest_fn={1: lambda t: (9.0, 9.0), 2: lambda t: (9.0, 9.0)})
    assert all(at(r, t) == {1: "walking", 2: "walking"} for t in range(r.ticks + 1))


def test_no_target_when_out_of_range_and_no_destination():
    r, _ = run(S(), pos_fn=pair_at(FAR))
    assert all(at(r, t) == {1: "no target", 2: "no target"} for t in range(r.ticks + 1))


def test_can_fire_beats_walking():
    r, _ = run(S(), pos_fn=pair_at(NEAR), dest_fn={1: lambda t: (9.0, 9.0)})
    assert at(r, 0)[1] == "can fire"


def test_blocked_beats_walking():
    r, _ = run(S(), pos_fn=pair_at(NEAR), shoot_fn=lambda t, a, b: False, dest_fn={1: lambda t: (9.0, 9.0)})
    assert at(r, 0)[1] == "blocked"


def test_one_shootable_enemy_among_unshootable_ones_gives_can_fire():
    """Two enemies in range, only one shootable: can fire, not blocked."""
    pos = {1: lambda t: (0.0, 0.0), 2: lambda t: (NEAR, 0.0), 3: lambda t: (0.0, NEAR)}
    r, _ = run(S(counts=(1, 2)), pos_fn=pos, shoot_fn=lambda t, a, b: not (a == 1 and b == 2))
    assert at(r, 0)[1] == "can fire"


def test_an_enemy_on_another_layer_is_not_a_target():
    r, _ = run(S(layers=(0, 1)), pos_fn=pair_at(NEAR))
    assert at(r, 0) == {1: "no target", 2: "no target"}


def test_state_changes_follow_the_tick():
    """Out of range until tick 3, then in range; blocked from tick 5; a destination until tick 2."""
    pos = {1: lambda t: (0.0, 0.0), 2: lambda t: (FAR if t < 3 else NEAR, 0.0)}
    r, _ = run(S(), pos_fn=pos, shoot_fn=lambda t, a, b: t < 5, dest_fn={1: lambda t: (9.0, 9.0) if t < 3 else None})
    assert [at(r, t)[1] for t in range(7)] == ["walking"] * 3 + ["can fire"] * 2 + ["blocked"] * 2
    assert [at(r, t)[2] for t in range(7)] == ["no target"] * 3 + ["can fire"] * 2 + ["blocked"] * 2


# ---- shape, order, dead units --------------------------------------------------------------------------------

@pytest.mark.parametrize("swap", [False, True])
def test_rows_are_triples_ordered_by_tick_then_unit_id(swap):
    r, fake = run(S(counts=(3, 2)), swap=swap, pos_fn=pair_at(NEAR, ((1, 2), (4, 5))))
    assert all(len(row) == 3 and row[2] in STATES for row in r.states)
    keys = [(t, u) for t, u, _ in r.states]
    assert keys == sorted(keys) and keys[0][0] == 0 and keys[-1][0] == r.ticks
    assert len(r.states) == (r.ticks + 1) * 5
    assert sorted({u for _, u, _ in r.states}) == sorted(fake.spawn_order)


def test_dead_units_are_omitted_from_the_tick_they_die():
    """Unit 3 (side 1) reads hp 0 from tick 3: present for ticks 0-2, absent after; the survivors keep rows."""
    pos = {1: lambda t: (0.0, 0.0), 3: lambda t: (NEAR, 0.0), 2: lambda t: (FAR * 2, 0.0)}
    r, _ = run(S(counts=(1, 2)), pos_fn=pos, hp_at={3: 3})
    assert [3 in at(r, t) for t in range(7)] == [True] * 3 + [False] * 4
    assert all(1 in at(r, t) and 2 in at(r, t) for t in range(7))


def test_a_dead_enemy_is_not_a_target():
    pos = {1: lambda t: (0.0, 0.0), 3: lambda t: (NEAR, 0.0), 4: lambda t: (FAR * 2, 0.0)}
    r, _ = run(S(counts=(1, 2)), pos_fn=pos, hp_at={3: 3})
    assert at(r, 2)[1] == "can fire" and at(r, 3)[1] == "no target"


# ---- order_ends ----------------------------------------------------------------------------------------------

def test_order_ends_first_end_only_sorted_by_unit():
    dest = {
        1: lambda t: (1.0, 1.0) if t < 3 else None,                      # ends at 3
        2: lambda t: (1.0, 1.0) if t in (1, 2, 5) else None,             # starts at 1, ends at 3, returns, ends at 6
        4: lambda t: (1.0, 1.0),                                         # never ends
    }                                                                    # unit 3 never has one
    r, _ = run(S(counts=(2, 2)), pos_fn=pair_at(FAR, ((1, 2), (3, 4))), dest_fn=dest)
    assert r.order_ends == ((1, 3), (2, 3))


def test_a_unit_that_never_had_a_destination_or_never_ended_is_absent():
    r, _ = run(S(), pos_fn=pair_at(FAR), dest_fn={2: lambda t: (1.0, 1.0)})
    assert r.order_ends == ()


def test_order_end_at_tick_zero_cannot_happen_and_a_late_start_counts():
    r, _ = run(S(), pos_fn=pair_at(FAR), dest_fn={1: lambda t: (1.0, 1.0) if 2 <= t < 4 else None})
    assert r.order_ends == ((1, 4),)


# ---- opt-in ----------------------------------------------------------------------------------------------------

def test_states_default_is_off_and_both_fields_are_none():
    assert Setup(groups=(G(0), G(1)), unit_types={}).states is False
    r, fake = run(S(states=False), pos_fn=pair_at(NEAR))
    assert r.states is None and r.order_ends is None
    assert not fake.calls_named("unit_destination")


def test_new_fields_follow_weighted_unit_seconds_and_default_to_none():
    names = [f.name for f in dataclasses.fields(FightResult)]
    assert names[-3:] == ["states", "order_ends", "mopup_orders"]   # TD-SL-mopup-field-order: mopup_orders appended last
    assert names.index("states") == names.index("weighted_unit_seconds") + 1
    old = FightResult(outcome="cap", margin=0.0, strength_left=(1.0, 1.0), survivors=(1, 1), heads=(1, 1), ticks=1,
                      first_contact_tick=-1, firing=[], firing_unit_seconds=(0.0, 0.0))
    assert old.states is None and old.order_ends is None


def test_states_work_with_trace_off_and_on():
    off, _ = run(S(states=True, trace=False), pos_fn=pair_at(NEAR))
    on, _ = run(S(states=True, trace=True), pos_fn=pair_at(NEAR))
    assert off.trace is None and off.states is not None
    assert on.trace is not None and on.states == off.states


def test_states_do_not_change_any_other_field_or_row():
    plain, _ = run(S(states=False), pos_fn=pair_at(NEAR))
    omitted, _ = run(dataclasses.replace(S(), states=False), pos_fn=pair_at(NEAR))
    with_states, _ = run(S(states=True), pos_fn=pair_at(NEAR))
    assert fight_row(plain, play="p") == fight_row(omitted, play="p") == fight_row(with_states, play="p")
    for f in dataclasses.fields(FightResult):
        if f.name not in ("states", "order_ends"):
            assert getattr(plain, f.name) == getattr(with_states, f.name), f.name


# ---- agreement with the firing series -------------------------------------------------------------------------

def test_can_fire_count_equals_the_firing_series_at_every_sample():
    """Positions close and open and the shooter set changes by tick: states must agree with count_able."""
    pos = {1: lambda t: (0.0, 0.0), 2: lambda t: (0.0, 60.0), 3: lambda t: (NEAR if t % 2 == 0 else FAR, 0.0),
           4: lambda t: (FAR if t < 4 else NEAR, 60.0)}
    r, _ = run(S(counts=(2, 2), max_ticks=8), pos_fn=pos, shoot_fn=lambda t, a, b: (a + b + t) % 3 != 0)
    assert len(r.firing) == 9
    for t, a0, a1 in r.firing:
        row = at(r, t)
        assert sum(1 for u, s in row.items() if u in (1, 2) and s == "can fire") == a0
        assert sum(1 for u, s in row.items() if u in (3, 4) and s == "can fire") == a1
    assert any(a0 + a1 > 0 for _, a0, a1 in r.firing) and any(a0 + a1 == 0 for _, a0, a1 in r.firing)
