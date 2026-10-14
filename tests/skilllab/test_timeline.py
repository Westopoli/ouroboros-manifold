# spec: docs/northstar/plans/2026-10-02-movement-layers-and-search-plan.md::Phase S (order timeline: later orders for bait, ambush, fall-back)
"""The order timeline of fight(), on a TimelineFakeEngine (no compiler, no library).

Contract these tests fix (the implementation under scripts/skilllab comes later):
  Step(group, when, order, goal=None)   frozen dataclass in contract.py; group indexes Setup.groups;
      when is ("tick", n) | ("arrive", radius) | ("seen",); order is "attack_move" | "move" | "idle".
  Setup.timeline: tuple = ()            FightResult.steps_fired: tuple = ()   ((step_index, tick), ...) firing order.
  Tick-0 Group.order orders go first, then ("tick", 0) steps in listed order, then the first engine step.
  After each engine.step every unfired Step is checked in listed order; it fires at most once, on the group's
  living units, before the next step. A step whose group has no living units is dropped, never fired.
  Engine gains can_see(w, observer, target) and clear_orders(w, unit_ids) (see tests/skilllab/fakes_timeline.py).
Unit ids: side 0 spawns first, ids from 1 (swap=True spawns side 1 first). Placement is stubbed to a line.
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
from fakes_timeline import TimelineFakeEngine  # noqa: E402
from scripts.skilllab.contract import Group, Setup, Step  # noqa: E402
from scripts.skilllab.fight import fight  # noqa: E402

pytestmark = pytest.mark.usefixtures("seam")   # LAB-REV2-L2: fight() reads the firing counts through the L1/L2 seam (fakes.Seam)

A0, A1 = (-300.0, 0.0), (300.0, 0.0)     # anchors of side 0 and side 1


@pytest.fixture(autouse=True)
def place_stub(monkeypatch):
    def stub(kind, n, x, y, facing_deg, params):
        return [(x + 7.0 * i, y) for i in range(n)]

    monkeypatch.setattr(formations_mod, "place", stub)
    monkeypatch.setattr(fight_mod, "place", stub, raising=False)


def G(side, count=2, order="attack_move", goal=None, anchor=None):
    x, y = anchor or (A0 if side == 0 else A1)
    return Group(side=side, unit="Vanguard", count=count, formation="line", x=x, y=y,
                 facing_deg=0.0 if side == 0 else 180.0, layer=0, order=order, goal=goal, params={})


def S(timeline=(), groups=None, max_ticks=10, **kw):
    return Setup(groups=groups or (G(0), G(1)), unit_types={}, max_ticks=max_ticks,
                 sample_every=5, timeline=tuple(timeline), orders_per_unit=False, **kw)   # group-level order log under test


def run(setup, seed=0, swap=False, **fake_kw):
    fake = TimelineFakeEngine(**fake_kw)
    return fight(setup, seed, swap, engine=fake), fake


def at(schedule):
    """A fake script: schedule {tick_reached: {unit: (x, y)}} applied by the step that reaches that tick."""
    def script(tick, fake):
        for u, (x, y) in schedule.get(tick + 1, {}).items():
            fake.set_pos(u, x, y)
    return script


def idx(fake, name, nth=0):
    return [i for i, c in enumerate(fake.calls) if c[0] == name][nth]


# ---- defaults and tick-0 ordering ---------------------------------------------------------------------------

def test_defaults_are_empty():
    """Setup.timeline defaults to () and FightResult.steps_fired to (); a Step is a frozen dataclass."""
    assert Setup(groups=(G(0), G(1)), unit_types={}).timeline == ()
    result, _ = run(S())
    assert result.steps_fired == ()
    step = Step(group=0, when=("seen",), order="idle")
    assert step.goal is None
    with pytest.raises(dataclasses.FrozenInstanceError):
        step.group = 1


def test_tick_zero_step_fires_after_group_orders_and_before_first_step():
    """("tick", 0) fires right after the tick-0 Group.order orders, before the first engine step, at tick 0."""
    result, fake = run(S([Step(0, ("tick", 0), "move", (5.0, 6.0))]))
    log = fake.order_log
    assert [(t, k) for t, k, _i, _g in log] == [(0, "attack_move"), (0, "attack_move"), (0, "move")]
    assert log[2][3] == (5.0, 6.0) and log[2][2] == [1, 2]
    assert idx(fake, "order_move") < idx(fake, "step")
    assert result.steps_fired == ((0, 0),)


def test_tick_zero_steps_keep_listed_order():
    """Two ("tick", 0) steps issue in listed order, and reversing the list reverses the orders."""
    a, b = Step(1, ("tick", 0), "move", (1.0, 1.0)), Step(0, ("tick", 0), "move", (2.0, 2.0))
    _, fake = run(S([a, b]))
    assert [o[3] for o in fake.orders_of("move")] == [(1.0, 1.0), (2.0, 2.0)]
    result, fake = run(S([b, a]))
    assert [o[3] for o in fake.orders_of("move")] == [(2.0, 2.0), (1.0, 1.0)]
    assert result.steps_fired == ((0, 0), (1, 0))


# ---- ("tick", n) --------------------------------------------------------------------------------------------

def test_tick_step_fires_exactly_at_n_once_and_before_the_next_step():
    """("tick", 3) issues its order after the step that makes tick 3, once, with the group's ids, before step 4."""
    result, fake = run(S([Step(0, ("tick", 3), "move", (9.0, 9.0))], max_ticks=6))
    assert fake.orders_of("move") == [(3, "move", [1, 2], (9.0, 9.0))]
    assert result.steps_fired == ((0, 3),)
    steps = [i for i, c in enumerate(fake.calls) if c[0] == "step"]
    assert steps[2] < idx(fake, "order_move") < steps[3]


def test_tick_step_does_not_fire_before_n():
    """Control: the same fight capped at tick 2 never fires the tick-3 step."""
    result, fake = run(S([Step(0, ("tick", 3), "move", (9.0, 9.0))], max_ticks=2))
    assert not fake.orders_of("move") and result.steps_fired == ()


def test_two_steps_on_the_same_tick_fire_in_listed_order():
    """Same tick, listed order: the step listed first is issued and recorded first."""
    a, b = Step(1, ("tick", 2), "move", (1.0, 0.0)), Step(0, ("tick", 2), "attack_move", (2.0, 0.0))
    result, fake = run(S([a, b]))
    assert [o[1] for o in fake.order_log[2:]] == ["move", "attack_move"]
    assert result.steps_fired == ((0, 2), (1, 2))
    result, fake = run(S([b, a]))
    assert [o[1] for o in fake.order_log[2:]] == ["attack_move", "move"]
    assert result.steps_fired == ((0, 2), (1, 2))


def test_steps_fired_lists_in_firing_order_not_listed_order():
    """A step listed first but due later appears later in steps_fired, with its own index."""
    a, b = Step(0, ("tick", 5), "idle"), Step(1, ("tick", 2), "idle")
    result, _ = run(S([a, b]))
    assert result.steps_fired == ((1, 2), (0, 5))


def test_default_goal_is_first_anchor_of_the_other_side():
    """goal None on a move/attack_move step means the other side's first anchor, as for Group.goal."""
    _, fake = run(S([Step(0, ("tick", 1), "move"), Step(1, ("tick", 1), "attack_move")]))
    assert fake.orders_of("move")[0][3] == A1
    assert fake.orders_of("attack_move")[2][3] == A0


# ---- ("arrive", radius) -------------------------------------------------------------------------------------

def arrive_setup(radius=10.0, **kw):
    return S([Step(0, ("arrive", radius), "idle")], groups=(G(0, order="attack_move", goal=(100.0, 0.0)), G(1)),
             **kw)


def test_arrive_fires_when_centroid_is_within_radius():
    """Both units near the goal: the centroid is 5 wu away (radius 10), so it fires on that tick."""
    result, fake = run(arrive_setup(), script=at({4: {1: (95.0, 0.0), 2: (95.0, 0.0)}}))
    assert result.steps_fired == ((0, 4),)
    assert fake.orders_of("idle") == [(4, "idle", [1, 2], None)]


def test_arrive_does_not_fire_while_centroid_is_far():
    """Control: the centroid stays 80 wu away, so nothing fires."""
    result, fake = run(arrive_setup(), script=at({4: {1: (20.0, 0.0), 2: (20.0, 0.0)}}))
    assert result.steps_fired == () and not fake.orders_of("idle")


def test_arrive_radius_edge():
    """Centroid exactly radius away fires; just over does not."""
    result, _ = run(arrive_setup(), script=at({3: {1: (90.0, 0.0), 2: (90.0, 0.0)}}))
    assert result.steps_fired == ((0, 3),)
    result, _ = run(arrive_setup(), script=at({3: {1: (89.9, 0.0), 2: (89.9, 0.0)}}))
    assert result.steps_fired == ()


def test_arrive_distance_is_euclidean_in_the_plane():
    """A centroid 6 right and 8 up of the goal is exactly 10 away (fires at radius 10, not at 9.9)."""
    sched = {3: {1: (106.0, 8.0), 2: (106.0, 8.0)}}
    result, _ = run(arrive_setup(10.0), script=at(sched))
    assert result.steps_fired == ((0, 3),)
    result, _ = run(arrive_setup(9.9), script=at(sched))
    assert result.steps_fired == ()


def test_arrive_centroid_counts_only_living_units():
    """Unit 2 sits far away and is dead: the centroid is unit 1 alone, on the goal, so it fires."""
    def script(tick, fake):
        if tick == 2:
            fake.set_pos(1, 100.0, 0.0)
            fake.set_pos(2, 500.0, 0.0)
            fake.set_hp(2, 0.0)
    result, _ = run(arrive_setup(), script=script)
    assert result.steps_fired == ((0, 3),)


def test_arrive_centroid_includes_living_stragglers():
    """Control: the same positions with unit 2 alive put the centroid 200 wu out, so nothing fires."""
    def script(tick, fake):
        if tick == 2:
            fake.set_pos(1, 100.0, 0.0)
            fake.set_pos(2, 500.0, 0.0)
    result, _ = run(arrive_setup(), script=script)
    assert result.steps_fired == ()


def test_arrive_with_no_goal_never_fires():
    """An idle group has no goal yet, so it never arrives anywhere, even standing on the other anchor."""
    setup = S([Step(0, ("arrive", 50.0), "move", (1.0, 1.0))], groups=(G(0, order="idle"), G(1)))
    result, fake = run(setup, script=at({2: {1: A1[:2], 2: A1[:2]}}))
    assert result.steps_fired == () and not fake.orders_of("move")


def test_arrive_uses_the_default_goal_of_an_attack_move():
    """An attack_move without a goal heads for the other anchor, and arrive measures against it."""
    setup = S([Step(0, ("arrive", 10.0), "idle")])
    result, _ = run(setup, script=at({3: {1: (295.0, 0.0), 2: (295.0, 0.0)}}))
    assert result.steps_fired == ((0, 3),)
    result, _ = run(setup, script=at({3: {1: (-295.0, 0.0), 2: (-295.0, 0.0)}}))
    assert result.steps_fired == ()


def test_arrive_chain_uses_the_latest_goal():
    """Group moves to A; arrive fires attack_move to B; a later arrive uses B, not A."""
    goal_b = (100.0, 200.0)
    steps = [Step(0, ("arrive", 10.0), "attack_move", goal_b), Step(0, ("arrive", 10.0), "move", (0.0, 0.0))]
    setup = S(steps, groups=(G(0, order="move", goal=(100.0, 0.0)), G(1)), max_ticks=12)
    sched = {3: {1: (100.0, 0.0), 2: (100.0, 0.0)}, 8: {1: goal_b, 2: goal_b}}
    result, fake = run(setup, script=at(sched))
    assert result.steps_fired == ((0, 3), (1, 8))
    assert [(o[0], o[1], o[3]) for o in fake.order_log[2:]] == [(3, "attack_move", goal_b), (8, "move", (0.0, 0.0))]


def test_arrive_chain_second_step_does_not_fire_at_the_old_goal():
    """Control: the group stays at A after the first arrive; the second (waiting on B) never fires."""
    steps = [Step(0, ("arrive", 10.0), "attack_move", (100.0, 200.0)), Step(0, ("arrive", 10.0), "move", (0.0, 0.0))]
    setup = S(steps, groups=(G(0, order="move", goal=(100.0, 0.0)), G(1)), max_ticks=12)
    result, _ = run(setup, script=at({3: {1: (100.0, 0.0), 2: (100.0, 0.0)}}))
    assert result.steps_fired == ((0, 3),)


# ---- ("seen",) ----------------------------------------------------------------------------------------------

def test_seen_fires_on_the_first_tick_any_member_sees_any_enemy():
    """Unit 2 sees enemy 4 from the third step on; the step fires then, once, with the per-unit call arguments."""
    def sees(fake, observer, target):
        return fake.step_count >= 3 and (observer, target) == (2, 4)
    result, fake = run(S([Step(0, ("seen",), "move", (1.0, 1.0))], max_ticks=6), can_see_fn=sees)
    assert result.steps_fired == ((0, 3),) and len(fake.orders_of("move")) == 1
    calls = fake.calls_named("can_see")
    assert calls and all(c[2] in (1, 2) and c[3] in (3, 4) for c in calls)


def test_seen_does_not_fire_when_nobody_sees():
    """Control: the same fight with sight off never fires."""
    result, fake = run(S([Step(0, ("seen",), "move", (1.0, 1.0))], max_ticks=6))
    assert result.steps_fired == () and not fake.orders_of("move")


def test_seen_ignores_dead_observers():
    """Only unit 1 sees, and it dies at tick 2 before seeing: nothing fires (control below: it lives)."""
    def sees(fake, observer, target):
        return observer == 1 and fake.step_count >= 3

    def kill(tick, fake):
        if tick == 1:
            fake.set_hp(1, 0.0)
    step = [Step(0, ("seen",), "idle")]
    result, _ = run(S(step, max_ticks=6), can_see_fn=sees, script=kill)
    assert result.steps_fired == ()
    result, _ = run(S(step, max_ticks=6), can_see_fn=sees)
    assert result.steps_fired == ((0, 3),)


def test_seen_ignores_dead_targets():
    """Only enemy 3 is visible, and it is dead: nothing fires (control: alive, it fires at tick 1)."""
    def sees(fake, observer, target):
        return target == 3

    def kill(tick, fake):
        if tick == 0:
            fake.set_hp(3, 0.0)
    step = [Step(0, ("seen",), "idle")]
    result, _ = run(S(step, max_ticks=6), can_see_fn=sees, script=kill)
    assert result.steps_fired == ()
    result, _ = run(S(step, max_ticks=6), can_see_fn=sees)
    assert result.steps_fired == ((0, 1),)


def test_seen_for_side_one_group_watches_side_zero():
    """A side-1 group's seen step asks its own units about side-0 units only, and fires once."""
    result, fake = run(S([Step(1, ("seen",), "idle")], max_ticks=4), can_see_fn=lambda f, o, t: True)
    assert result.steps_fired == ((0, 1),)
    assert all(c[2] in (3, 4) and c[3] in (1, 2) for c in fake.calls_named("can_see"))


def test_fired_seen_step_stops_asking():
    """After it fires, the step no longer calls can_see (every can_see call precedes the second engine step)."""
    _, fake = run(S([Step(0, ("seen",), "idle")], max_ticks=5), can_see_fn=lambda f, o, t: True)
    assert fake.calls_named("can_see") and idx(fake, "step", 1) > max(
        i for i, c in enumerate(fake.calls) if c[0] == "can_see")


def test_tick_and_arrive_steps_never_ask_for_sight():
    """Only ("seen",) steps call can_see; with no seen step the library is never asked."""
    _, fake = run(S([Step(0, ("tick", 2), "idle"), Step(1, ("arrive", 5.0), "idle")]))
    assert not fake.calls_named("can_see")


# ---- idle, dropped steps ------------------------------------------------------------------------------------

def test_idle_clears_orders_of_the_groups_units_and_issues_nothing_else():
    """idle makes one clear_orders call listing the group's ids, and no move or attack order at that moment."""
    result, fake = run(S([Step(0, ("tick", 2), "idle", (1.0, 2.0, 3.0))]))
    assert fake.calls_named("clear_orders")[0][2] == [1, 2] and len(fake.calls_named("clear_orders")) == 1
    assert [o for o in fake.order_log if o[0] == 2] == [(2, "idle", [1, 2], None)]
    assert result.steps_fired == ((0, 2),)


def test_idle_clears_only_living_units():
    """A unit dead by the firing tick is not cleared."""
    def kill(tick, fake):
        if tick == 0:
            fake.set_hp(2, 0.0)
    _, fake = run(S([Step(0, ("tick", 2), "idle")]), script=kill)
    assert fake.calls_named("clear_orders")[0][2] == [1]


def test_step_on_an_annihilated_group_is_dropped():
    """Group 0 (units 1, 2) dies at tick 1 while group 2 of the same side lives: its tick-3 step is dropped."""
    groups = (G(0, 2), G(1, 2), G(0, 1, anchor=(-250.0, 40.0)))

    def kill(tick, fake):
        if tick == 0:
            fake.set_hp(1, 0.0)
            fake.set_hp(2, 0.0)
    result, fake = run(S([Step(0, ("tick", 3), "idle"), Step(2, ("tick", 3), "idle")], groups=groups, max_ticks=6),
                       script=kill)
    assert result.steps_fired == ((1, 3),)
    assert [c[2] for c in fake.calls_named("clear_orders")] == [[3]]


def test_a_dropped_step_does_not_block_later_steps():
    """Control for the drop: with group 0 alive both steps fire in order."""
    groups = (G(0, 2), G(1, 2), G(0, 1, anchor=(-250.0, 40.0)))
    result, _ = run(S([Step(0, ("tick", 3), "idle"), Step(2, ("tick", 3), "idle")], groups=groups, max_ticks=6))
    assert result.steps_fired == ((0, 3), (1, 3))


# ---- validation ---------------------------------------------------------------------------------------------

BAD = [
    Step(2, ("tick", 1), "idle"),
    Step(-1, ("tick", 1), "idle"),
    Step(0, ("tick", 1), "charge"),
    Step(0, ("later", 1), "idle"),
    Step(0, ("tick", -1), "idle"),
    Step(0, ("arrive", 0), "idle"),
    Step(0, ("arrive", -5.0), "idle"),
    Step(0, (), "idle"),
    Step(0, ("tick",), "idle"),
    Step(0, ("tick", 1, 2), "idle"),
    Step(0, ("seen", 5), "idle"),
    Step(0, ("arrive",), "idle"),
    Step(0, ("tick", 1), "move", (1.0,)),
    Step(0, ("tick", 1), "attack_move", (1.0, 2.0, 3.0)),
    Step(0, ("tick", 1), "move", 5),
]


@pytest.mark.parametrize("step", BAD, ids=[repr(s.when) + s.order + repr(s.group) + repr(s.goal) for s in BAD])
def test_invalid_step_is_rejected_before_any_world_is_made(step):
    """Each malformed step raises ValueError and the engine has not been touched."""
    fake = TimelineFakeEngine()
    with pytest.raises(ValueError):
        fight(S([step]), 0, False, engine=fake)
    assert fake.calls == []


def test_idle_step_ignores_its_goal_and_a_valid_step_is_accepted():
    """Control: a goal of any shape on an idle step is ignored, and a well-formed timeline runs."""
    result, _ = run(S([Step(0, ("tick", 1), "idle", (1.0, 2.0, 3.0)), Step(1, ("arrive", 0.5), "move", (3.0, 4.0)),
                       Step(0, ("seen",), "attack_move")]))
    assert result.steps_fired == ((0, 1),)


# ---- unaffectedness, determinism, swap ----------------------------------------------------------------------

def recorded_setup():
    return Setup(groups=(G(0, 2), G(1, 3)), unit_types={}, max_ticks=50, sample_every=2,
                 trace=True, timeline=(), orders_per_unit=False)


def recorded_script(tick, fake):
    if tick == 2:
        fake.set_hp(3, 40.0)
    if tick == 4:
        fake.set_hp(4, 0.0)
        fake.set_hp(5, 0.0)


def test_empty_timeline_matches_the_recorded_pre_timeline_run():
    """A result recorded from fight() before the timeline existed (seed 7, scripted damage) is reproduced
    exactly, the orders are the two tick-0 attack_moves only, and the trace is 5 units x 51 ticks."""
    result, fake = run(recorded_setup(), seed=7, script=recorded_script)
    assert (result.outcome, result.margin, result.strength_left) == ("cap", 0.8666666666666667,
                                                                       (1.0, 0.13333333333333333))
    assert (result.survivors, result.heads, result.ticks, result.first_contact_tick) == ((2, 1), (2, 3), 50, -1)
    assert result.firing == [(t, 0, 0) for t in range(0, 51, 2)]
    assert result.firing_unit_seconds == (0.0, 0.0) and result.steps_fired == ()
    assert len(result.trace) == 5 * 51
    assert [(o[0], o[1], o[2]) for o in fake.order_log] == [(0, "attack_move", [1, 2]), (0, "attack_move", [3, 4, 5])]
    assert not fake.calls_named("can_see") and not fake.calls_named("clear_orders")


def test_timeline_does_not_change_trace_length():
    """Steps that fire add orders but do not add or drop trace rows against the same scripted fight."""
    plain, _ = run(recorded_setup(), seed=7, script=recorded_script)
    steps = (Step(0, ("tick", 5), "move", (0.0, 0.0)), Step(1, ("tick", 9), "idle"))
    with_steps, _ = run(dataclasses.replace(recorded_setup(), timeline=steps), seed=7, script=recorded_script)
    assert with_steps.steps_fired == ((0, 5), (1, 9))
    assert len(with_steps.trace) == len(plain.trace) == 5 * 51
    assert with_steps.ticks == plain.ticks


def test_timeline_runs_are_deterministic():
    """Same setup, seed and scripted fake give equal results and equal order logs."""
    setup = dataclasses.replace(recorded_setup(), timeline=(Step(0, ("arrive", 20.0), "idle"),
                                                            Step(1, ("tick", 4), "move")))
    (r1, f1), (r2, f2) = (run(setup, seed=3, script=recorded_script) for _ in range(2))
    assert r1 == r2 and f1.order_log == f2.order_log


def test_swap_fires_the_same_steps():
    """swap=True spawns side 1 first (different unit ids) but the same group steps fire at the same ticks."""
    def script(tick, fake):
        if tick == 3:
            for u in fake.units_of(0):
                fake.set_pos(u, 295.0, 0.0)
    setup = S([Step(1, ("tick", 2), "idle"), Step(0, ("arrive", 10.0), "idle")], max_ticks=8)
    plain, f0 = run(setup, script=script)
    swapped, f1 = run(setup, swap=True, script=script)
    assert plain.steps_fired == swapped.steps_fired == ((0, 2), (1, 4))
    assert [c[2] for c in f0.calls_named("clear_orders")] == [[3, 4], [1, 2]]
    assert [c[2] for c in f1.calls_named("clear_orders")] == [[1, 2], [3, 4]]
