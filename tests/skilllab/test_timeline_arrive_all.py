# spec: Architect ruling A198 (both sides switch to attack_move together) - ("arrive_all", radius) in scripts/skilllab/timeline.py
"""("arrive_all", r) is due when every mover group with living units has its centroid within r of ITS original goal.
Mover groups are those with a recorded goal at timeline start; the start goals are kept when earlier steps fire."""
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
from scripts.skilllab import timeline  # noqa: E402
from scripts.skilllab.contract import Group, Setup, Step  # noqa: E402
from scripts.skilllab.fight import fight  # noqa: E402

pytestmark = pytest.mark.usefixtures("seam")   # LAB-REV2-L2: fight() reads the firing counts through the L1/L2 seam (fakes.Seam)

GOAL0, GOAL1 = (100.0, 0.0), (-100.0, 0.0)
R = 10.0


@pytest.fixture(autouse=True)
def place_stub(monkeypatch):
    def stub(kind, n, x, y, facing_deg, params):
        return [(x + 7.0 * i, y) for i in range(n)]

    monkeypatch.setattr(formations_mod, "place", stub)
    monkeypatch.setattr(fight_mod, "place", stub, raising=False)


def G(side, goal, order="attack_move"):
    return Group(side=side, unit="Vanguard", count=2, formation="line", x=-300.0 if side == 0 else 300.0, y=0.0,
                 facing_deg=0.0 if side == 0 else 180.0, layer=0, order=order, goal=goal, params={})


def S(steps, groups=None, max_ticks=10):
    return Setup(groups=groups or (G(0, GOAL0), G(1, GOAL1)), unit_types={}, max_ticks=max_ticks, sample_every=5, timeline=tuple(steps))


def both(radius=R):
    return [Step(0, ("arrive_all", radius), "idle"), Step(1, ("arrive_all", radius), "idle")]


def at(schedule):
    """schedule {tick_reached: {unit: (x, y)}} applied by the step that reaches that tick."""
    def script(tick, fake):
        for u, (x, y) in schedule.get(tick + 1, {}).items():
            fake.set_pos(u, x, y)
    return script


def run(setup, **kw):
    fake = TimelineFakeEngine(**kw)
    return fight(setup, 0, False, engine=fake), fake


def on(units, point):
    return {u: point for u in units}


def test_not_due_while_one_group_is_outside_the_radius():
    sched = {3: {**on((1, 2), GOAL0), **on((3, 4), (-20.0, 0.0))}}
    result, fake = run(S(both()), script=at(sched))
    assert result.steps_fired == () and fake.orders_of("idle") == []


def test_due_when_every_group_is_inside_and_both_steps_fire_on_that_tick():
    sched = {3: on((1, 2), GOAL0), 5: on((3, 4), GOAL1)}
    result, fake = run(S(both()), script=at(sched))
    assert result.steps_fired == ((0, 5), (1, 5))
    assert [o[0] for o in fake.orders_of("idle")] == [5, 5]


def test_second_step_is_not_blocked_by_the_first_having_reset_goals():
    """Step 0 is an attack_move (which resets goals[0] as it fires); step 1 must still see group 0's start goal."""
    steps = [Step(0, ("arrive_all", R), "attack_move", (0.0, 0.0)), Step(1, ("arrive_all", R), "attack_move", (0.0, 0.0))]
    sched = {2: {**on((1, 2), GOAL0), **on((3, 4), GOAL1)}}
    result, _ = run(S(steps), script=at(sched))
    assert result.steps_fired == ((0, 2), (1, 2))


def test_a_dead_group_does_not_block():
    def script(tick, fake):
        if tick == 2:
            for u in (3, 4):
                fake.set_pos(u, 900.0, 900.0)
                fake.set_hp(u, 0.0)
            for u in (1, 2):
                fake.set_pos(u, *GOAL0)
    result, _ = run(S([Step(0, ("arrive_all", R), "idle")]), script=script)
    assert result.steps_fired == ((0, 3),)


def test_a_living_group_far_from_its_goal_blocks_even_if_it_stands_on_the_other_goal():
    sched = {3: {**on((1, 2), GOAL0), **on((3, 4), GOAL0)}}
    result, _ = run(S(both()), script=at(sched))
    assert result.steps_fired == ()


def test_a_group_with_no_goal_is_not_a_mover():
    groups = (G(0, GOAL0), G(1, None, order="idle"))
    result, _ = run(S([Step(0, ("arrive_all", R), "idle")], groups=groups), script=at({3: on((1, 2), GOAL0)}))
    assert result.steps_fired == ((0, 3),)


def test_radius_edge():
    result, _ = run(S(both()), script=at({3: {**on((1, 2), (90.0, 0.0)), **on((3, 4), (-90.0, 0.0))}}))
    assert result.steps_fired == ((0, 3), (1, 3))
    result, _ = run(S(both()), script=at({3: {**on((1, 2), (89.9, 0.0)), **on((3, 4), (-90.0, 0.0))}}))
    assert result.steps_fired == ()


def test_validate_accepts_a_positive_radius():
    timeline.validate(S([Step(0, ("arrive_all", 60.0), "attack_move")]))


@pytest.mark.parametrize("when", [("arrive_all",), ("arrive_all", 0), ("arrive_all", -5.0)])
def test_validate_rejects_a_missing_or_nonpositive_radius(when):
    with pytest.raises(ValueError):
        timeline.validate(S([Step(0, when, "attack_move")]))
