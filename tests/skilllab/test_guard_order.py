# Rule pins: R-096-08@629328
# spec: R-096-08 (the unit holds, fires in range, never walks) - guard order in contract, fight, timeline and engine
"""The guard order on fake engines and a stub library: Group.order and Step.order "guard", Engine.order_guard."""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
for _p in (ROOT, Path(__file__).resolve().parent):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import scripts.skilllab.fight as fight_mod  # noqa: E402
import scripts.skilllab.formations as formations_mod  # noqa: E402
from fakes_guard import GuardFakeEngine  # noqa: E402
from scripts.skilllab import timeline  # noqa: E402
from scripts.skilllab.contract import Group, Setup, Step  # noqa: E402
from scripts.skilllab.fight import fight  # noqa: E402
from scripts.skilllab.timeline import validate  # noqa: E402

pytestmark = pytest.mark.usefixtures("seam")   # LAB-REV2-L2: fight() reads the firing counts through the L1/L2 seam (fakes.Seam)

A0, A1 = (-300.0, 0.0), (300.0, 0.0)


@pytest.fixture(autouse=True)
def place_stub(monkeypatch):
    def stub(kind, n, x, y, facing_deg, params):
        return [(x + 7.0 * i, y) for i in range(n)]
    monkeypatch.setattr(formations_mod, "place", stub)
    monkeypatch.setattr(fight_mod, "place", stub, raising=False)


def G(side, count=2, order="attack_move", goal=None, spacing=7.0):
    x, y = A0 if side == 0 else A1
    return Group(side=side, unit="Vanguard", count=count, formation="line", x=x, y=y,
                 facing_deg=0.0 if side == 0 else 180.0, layer=0, order=order, goal=goal, params={"spacing": spacing})


def S(timeline_=(), groups=None, max_ticks=10):
    return Setup(groups=groups or (G(0), G(1)), unit_types={}, max_ticks=max_ticks,
                 sample_every=5, timeline=tuple(timeline_), orders_per_unit=False)   # group-level order log under test


def run(setup, **kw):
    fake = GuardFakeEngine(**kw)
    return fight(setup, 0, False, engine=fake), fake


def test_guard_orders_are_known_to_the_timeline():
    assert "guard" in timeline.ORDERS


def test_guard_group_issues_one_order_guard_with_its_unit_ids():
    _, fake = run(S(groups=(G(0), G(1, order="guard"))))
    assert fake.calls_named("order_guard") == [("order_guard", fake.world, [3, 4])]
    assert [o[2] for o in fake.orders_of("attack_move")] == [[1, 2]]


def test_guard_group_issues_no_move_or_attack_move():
    _, fake = run(S(groups=(G(0, order="guard"), G(1, order="guard"))))
    assert len(fake.calls_named("order_guard")) == 2
    assert not fake.calls_named("order_attack_move") and not fake.calls_named("order_move")


def test_guard_group_ignores_its_goal():
    _, fake = run(S(groups=(G(0, order="guard", goal=(5.0, 5.0)), G(1))))
    assert fake.calls_named("order_guard") == [("order_guard", fake.world, [1, 2])]
    assert not fake.orders_of("move") and len(fake.orders_of("attack_move")) == 1


def test_guard_group_is_not_split_into_slot_chunks():
    """A line wider than the slot radius would be chunked for a move; a guard group is one call."""
    _, fake = run(S(groups=(G(0, count=40, order="guard", spacing=7.0), G(1))))
    wide = [c for c in fake.calls_named("order_guard")]
    assert len(wide) == 1 and wide[0][2] == list(range(1, 41))
    # the other group is far narrower; the control: a wide non-guard group of the same size is chunked
    stretched = Group(side=0, unit="Vanguard", count=40, formation="line", x=-300.0, y=0.0, facing_deg=0.0, layer=0,
                      order="attack_move", params={})
    import scripts.skilllab.formations as f
    fight_mod.place = lambda kind, n, x, y, fd, p: [(x + 40.0 * i, y) for i in range(n)]
    try:
        _, fake2 = run(S(groups=(stretched, G(1))))
    finally:
        fight_mod.place = f.place
    assert len(fake2.orders_of("attack_move")) > 2


def test_guard_group_counts_in_the_headcount():
    result, _ = run(S(groups=(G(0, count=3, order="guard"), G(1, count=2))))
    assert result.heads == (3, 2)


@pytest.mark.parametrize("when,script", [
    (("tick", 3), None),
    (("seen",), "sees"),
])
def test_guard_step_fires_order_guard_once(when, script):
    kw = {"can_see_fn": lambda f, o, t: f.step_count >= 2} if script else {}
    result, fake = run(S([Step(0, when, "guard")], max_ticks=8), **kw)
    assert len(result.steps_fired) == 1
    assert [o for o in fake.order_log if o[1] == "guard"] == [(result.steps_fired[0][1], "guard", [1, 2], None)]
    assert len(fake.calls_named("order_guard")) == 1


def test_guard_step_on_arrive_fires_order_guard_once():
    def script(tick, fake):
        if tick + 1 == 4:
            for u in (1, 2):
                fake.set_pos(u, 95.0, 0.0)
    groups = (G(0, order="attack_move", goal=(100.0, 0.0)), G(1))
    result, fake = run(S([Step(0, ("arrive", 10.0), "guard")], groups=groups), script=script)
    assert result.steps_fired == ((0, 4),)
    assert fake.calls_named("order_guard") == [("order_guard", fake.world, [1, 2])]


def test_guard_step_after_attack_move_replaces_it_and_takes_no_goal():
    result, fake = run(S([Step(0, ("tick", 2), "guard", (1.0, 1.0))]))
    assert [o[1] for o in fake.order_log if o[2] == [1, 2]] == ["attack_move", "guard"]
    assert fake.order_log[-1][3] is None
    assert len(fake.orders_of("attack_move")) == 2 and not fake.orders_of("move")


def test_guard_step_issues_on_living_units_only():
    def kill(tick, fake):
        if tick == 0:
            fake.set_hp(1, 0)
    _, fake = run(S([Step(0, ("tick", 2), "guard")]), script=kill)
    assert fake.calls_named("order_guard") == [("order_guard", fake.world, [2])]


def test_validate_accepts_guard_with_and_without_goal_and_still_rejects_unknown():
    validate(S([Step(0, ("tick", 1), "guard")]))
    validate(S([Step(0, ("tick", 1), "guard", (1.0, 2.0))]))
    validate(S([Step(0, ("tick", 1), "guard", "not a goal")]))        # ignored like idle
    with pytest.raises(ValueError):
        validate(S([Step(0, ("tick", 1), "defend")]))


def test_unknown_group_order_still_raises():
    with pytest.raises(ValueError):
        run(S(groups=(G(0, order="defend"), G(1))))


# ---- Engine.order_guard (stub library) ----

class _Lib:
    def __init__(self, ret=0):
        self.ret, self.seen = ret, None
        self.om_command_guard = self._call

    def _call(self, w, ids, n):
        self.seen = (w, list(ids[:n]), n)
        return self.ret


def _engine(lib):
    from scripts.skilllab.engine import Engine
    e = Engine.__new__(Engine)
    e._lib = lib
    return e


def test_engine_order_guard_passes_ids_and_count():
    lib = _Lib()
    _engine(lib).order_guard("W", [5, 6, 7])
    assert lib.seen == ("W", [5, 6, 7], 3)


def test_engine_order_guard_nonzero_raises_value_error():
    with pytest.raises(ValueError):
        _engine(_Lib(ret=-1)).order_guard("W", [5])
