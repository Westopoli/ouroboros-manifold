# Rule pins: R-095-02@47ddf5
# spec: Architect ruling A198 (R-095-02, the group_move order kind) - scripts/skilllab/{fight,timeline}.py; LAB-REV2-L2: the approach opening A198 first served is retired (Q-LAB-03), the order kind stays for timeline steps
"""Group.order and Step.order accept "group_move": one Engine.order_group_move per group. Fake engine; no library."""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
for _p in (ROOT, Path(__file__).resolve().parent):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import scripts.skilllab.fight as fight_mod  # noqa: E402
import scripts.skilllab.formations as formations_mod  # noqa: E402
from fakes_group_move import GroupMoveFakeEngine  # noqa: E402
from scripts.skilllab import timeline  # noqa: E402
from scripts.skilllab.contract import Group, Setup, Step  # noqa: E402
from scripts.skilllab.fight import fight  # noqa: E402

pytestmark = pytest.mark.usefixtures("seam")   # LAB-REV2-L2: fight() reads the firing counts through the L1/L2 seam (fakes.Seam)

A0, A1 = (-300.0, 0.0), (300.0, 0.0)


@pytest.fixture(autouse=True)
def place_stub(monkeypatch):
    def stub(kind, n, x, y, facing_deg, params):
        return [(x + 7.0 * i, y) for i in range(n)]

    monkeypatch.setattr(formations_mod, "place", stub)
    monkeypatch.setattr(fight_mod, "place", stub, raising=False)


def G(side, count=2, order="group_move", goal=None):
    x, y = A0 if side == 0 else A1
    return Group(side=side, unit="Vanguard", count=count, formation="line", x=x, y=y,
                 facing_deg=0.0 if side == 0 else 180.0, layer=0, order=order, goal=goal, params={})


def S(timeline=(), groups=None, max_ticks=10):
    return Setup(groups=groups or (G(0), G(1)), unit_types={}, max_ticks=max_ticks,
                 sample_every=5, timeline=tuple(timeline))


def run(setup, **kw):
    fake = GroupMoveFakeEngine(**kw)
    return fight(setup, 0, False, engine=fake), fake


def test_orders_contains_group_move():
    assert "group_move" in timeline.ORDERS


def test_group_order_issues_one_group_move_per_group_and_nothing_else():
    _, fake = run(S())
    assert [c[0] for c in fake.calls if c[0].startswith("order_")] == ["order_group_move", "order_group_move"]
    assert fake.orders_of("move") == [] and fake.orders_of("attack_move") == []
    assert [o[:3] for o in fake.orders_of("group_move")] == [(0, "group_move", [1, 2]), (0, "group_move", [3, 4])]


def test_goal_none_is_the_first_anchor_of_the_other_side_and_explicit_goal_is_kept():
    _, fake = run(S(groups=(G(0), G(1, goal=(5.0, 6.0)))))
    assert [o[3] for o in fake.orders_of("group_move")] == [A1, (5.0, 6.0)]


def test_group_order_is_validated_not_rejected():
    run(S())
    with pytest.raises(ValueError):
        run(S(groups=(G(0, order="group_hop"), G(1))))


def test_idle_group_stays_idle_next_to_a_group_move():
    _, fake = run(S(groups=(G(0), G(1, order="idle"))))
    assert len(fake.orders_of("group_move")) == 1


# ---- steps --------------------------------------------------------------------------------------------------

def test_tick_step_fires_a_group_move_once_with_the_group_ids():
    result, fake = run(S([Step(0, ("tick", 3), "group_move", (9.0, 9.0))], groups=(G(0, order="idle"), G(1, order="idle")),
                         max_ticks=6))
    assert fake.orders_of("group_move") == [(3, "group_move", [1, 2], (9.0, 9.0))]
    assert result.steps_fired == ((0, 3),)
    steps = [i for i, c in enumerate(fake.calls) if c[0] == "step"]
    first = [i for i, c in enumerate(fake.calls) if c[0] == "order_group_move"][0]
    assert steps[2] < first < steps[3]
    assert fake.orders_of("move") == []


def test_tick_step_does_not_fire_early():
    result, fake = run(S([Step(0, ("tick", 3), "group_move", (9.0, 9.0))], groups=(G(0, order="idle"), G(1, order="idle")),
                         max_ticks=2))
    assert fake.orders_of("group_move") == [] and result.steps_fired == ()


def test_step_goal_none_is_the_first_anchor_of_the_other_side():
    _, fake = run(S([Step(0, ("tick", 1), "group_move"), Step(1, ("tick", 1), "group_move")],
                    groups=(G(0, order="idle"), G(1, order="idle"))))
    assert [o[3] for o in fake.orders_of("group_move")] == [A1, A0]


def test_arrive_step_fires_a_group_move_once():
    s = S([Step(0, ("arrive", 10.0), "group_move", (7.0, 7.0))],
          groups=(G(0, order="attack_move", goal=(100.0, 0.0)), G(1, order="idle")))

    def script(tick, fake):
        if tick == 3:
            fake.set_pos(1, 100.0, 0.0)
            fake.set_pos(2, 100.0, 0.0)
    result, fake = run(s, script=script)
    assert result.steps_fired == ((0, 4),)
    assert fake.orders_of("group_move") == [(4, "group_move", [1, 2], (7.0, 7.0))]


def test_seen_step_fires_a_group_move_once():
    s = S([Step(0, ("seen",), "group_move", (7.0, 7.0))], groups=(G(0, order="idle"), G(1, order="idle")))
    result, fake = run(s, can_see_fn=lambda f, a, t: f.step_count >= 2)
    assert len(fake.orders_of("group_move")) == 1
    assert [i for i, _ in result.steps_fired] == [0]


def test_validate_accepts_group_move_and_rejects_unknown_names():
    timeline.validate(S([Step(0, ("tick", 1), "group_move", (1.0, 2.0))]))
    with pytest.raises(ValueError):
        timeline.validate(S([Step(0, ("tick", 1), "group_hop", (1.0, 2.0))]))
    with pytest.raises(ValueError):
        timeline.validate(S([Step(0, ("tick", 1), "group_move", (1.0,))]))
