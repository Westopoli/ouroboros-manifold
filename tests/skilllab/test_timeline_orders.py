# spec: docs/northstar/plans/2026-10-05-space-lab-stage1-spec.md::orders lane (Step.ping, Step.set_layer, Step.set_emission)
"""The three new timeline Step kinds on a fake engine (no compiler, no library).

Contract these tests fix (names from the brief; everything else is read off behaviour):
  Step.ping(layer, x, y, casters="all", when=...)   issues engine.ping(w, caster, layer, x, y) once per caster
  Step.set_layer(group, layer, when=...)            issues engine.set_layer(w, ids, layer) on the group's living ids
  Step.set_emission(group, on, when=...)            issues engine.set_emission(w, ids, on) on the group's living ids
  `when` is any of the existing kinds ("tick", n) | ("arrive", r) | ("arrive_all", r) | ("seen",).
  Each fired step appears in FightResult.steps_fired as (step_index, tick), the fight's order log.
  A setup with none of these steps gives the same row as before the change (BASELINE_ROW, recorded on
  push/lab-run-5 before these tests were written).
Reading flagged for the architect: the spec's "casters = group name" has no group names in Group, so only
casters="all" is tested here, and only through effects that hold whichever side "all" covers.
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
from scripts.skilllab.rows import fight_row  # noqa: E402

pytestmark = pytest.mark.usefixtures("seam")   # LAB-REV2-L2: fight() reads the firing counts through the L1/L2 seam (fakes.Seam)

A0, A1 = (-300.0, 0.0), (300.0, 0.0)
PING_LAYER, PING_X, PING_Y = 4, 1500.0, 0.0     # provisional (2026-10-05)
TARGET_LAYER = 3                                  # provisional (2026-10-05)

BASELINE_ROW = {'outcome': 'cap', 'margin': 0.0, 'strength_left_0': 1.0, 'strength_left_1': 1.0, 'survivors_0': 2,
                'survivors_1': 2, 'heads_0': 2, 'heads_1': 2, 'ticks': 10, 'first_contact_tick': -1,
                'firing_unit_seconds_0': 0.0, 'firing_unit_seconds_1': 0.0}


class OrdersFakeEngine(TimelineFakeEngine):
    """Adds the three bindings the new steps call; each logs (tick, kind, args)."""

    def __init__(self, **kw):
        super().__init__(**kw)
        self.new_log = []

    def ping(self, w, caster, layer, x, y):
        self.new_log.append((self.step_count, "ping", caster, layer, x, y))
        return 0

    def set_layer(self, w, ids, layer):
        self.new_log.append((self.step_count, "set_layer", list(ids), layer))

    def set_emission(self, w, ids, on):
        self.new_log.append((self.step_count, "set_emission", list(ids), bool(on)))

    def of(self, kind):
        return [e for e in self.new_log if e[1] == kind]


@pytest.fixture(autouse=True)
def place_stub(monkeypatch):
    def stub(kind, n, x, y, facing_deg, params):
        return [(x + 7.0 * i, y) for i in range(n)]

    monkeypatch.setattr(formations_mod, "place", stub)
    monkeypatch.setattr(fight_mod, "place", stub, raising=False)


def G(side, count=2):
    x, y = A0 if side == 0 else A1
    return Group(side=side, unit="Vanguard", count=count, formation="line", x=x, y=y,
                 facing_deg=0.0 if side == 0 else 180.0, layer=0, order="attack_move", params={})


def S(timeline=(), max_ticks=10):
    return Setup(groups=(G(0), G(1)), unit_types={}, max_ticks=max_ticks,
                 sample_every=5, timeline=tuple(timeline), orders_per_unit=False)   # group-level order log under test


def run(setup, seed=0, **fake_kw):
    fake = OrdersFakeEngine(**fake_kw)
    return fight(setup, seed, False, engine=fake), fake


def ping(tick=3, **kw):
    return Step.ping(PING_LAYER, PING_X, PING_Y, when=("tick", tick), **kw)


# ---- construction ------------------------------------------------------------------------------------------

def test_constructors_keep_their_arguments_and_are_frozen():
    p = Step.ping(PING_LAYER, PING_X, PING_Y, casters="all", when=("tick", 3))
    assert isinstance(p, Step) and p.when == ("tick", 3)
    assert Step.ping(PING_LAYER, PING_X, PING_Y, when=("tick", 3)) == p, "casters defaults to 'all'"
    sl = Step.set_layer(1, 3, when=("tick", 4))
    assert isinstance(sl, Step) and sl.group == 1 and sl.when == ("tick", 4)
    se = Step.set_emission(0, True, when=("seen",))
    assert isinstance(se, Step) and se.group == 0 and se.when == ("seen",)
    assert Step.set_emission(0, False, when=("seen",)) != se, "on is part of the step"
    assert Step.set_layer(1, 2, when=("tick", 4)) != sl, "layer is part of the step"
    with pytest.raises(dataclasses.FrozenInstanceError):
        sl.group = 0


# ---- validation (existing rules apply to the new kinds) -----------------------------------------------------

@pytest.mark.parametrize("when", [("tick", -1), ("arrive", 0), ("arrive_all", 0), ("later", 3), ()])
def test_bad_when_is_rejected_for_every_new_kind(when):
    makers = (lambda: Step.ping(PING_LAYER, PING_X, PING_Y, when=when), lambda: Step.set_layer(0, 3, when=when),
              lambda: Step.set_emission(0, True, when=when))
    for make in makers:
        with pytest.raises(ValueError):   # rejected at construction or by fight(), either way before any step
            run(S([make()]))


@pytest.mark.parametrize("make", [lambda g: Step.set_layer(g, 3, when=("tick", 1)),
                                  lambda g: Step.set_emission(g, True, when=("tick", 1))])
def test_group_index_out_of_range_is_rejected(make):
    for bad in (2, -1):
        with pytest.raises(ValueError):
            run(S([make(bad)]))


# ---- issuing through the bindings ---------------------------------------------------------------------------

def test_ping_step_calls_the_binding_at_its_tick_with_layer_and_point():
    result, fake = run(S([ping(3)]))
    calls = fake.of("ping")
    assert calls, "no ping reached the engine"
    assert all(c[0] == 3 and c[3:] == (PING_LAYER, PING_X, PING_Y) for c in calls)
    assert len({c[2] for c in calls}) == len(calls), "one ping per caster"
    assert set(c[2] for c in calls) <= set(fake.units)
    assert result.steps_fired == ((0, 3),)


def test_ping_step_is_issued_once_not_every_tick():
    _, fake = run(S([ping(3)], max_ticks=12))
    assert {c[0] for c in fake.of("ping")} == {3}


def test_set_layer_step_issues_the_groups_ids_and_layer_at_its_tick():
    result, fake = run(S([Step.set_layer(1, 3, when=("tick", 4))]))
    assert fake.of("set_layer") == [(4, "set_layer", [3, 4], 3)]
    assert result.steps_fired == ((0, 4),)


def test_set_emission_step_issues_the_groups_ids_and_flag_at_its_tick():
    steps = [Step.set_emission(0, True, when=("tick", 2)), Step.set_emission(0, False, when=("tick", 6))]
    result, fake = run(S(steps))
    assert fake.of("set_emission") == [(2, "set_emission", [1, 2], True), (6, "set_emission", [1, 2], False)]
    assert result.steps_fired == ((0, 2), (1, 6))


def test_new_steps_do_not_issue_movement_orders():
    _, base = run(S())
    _, fake = run(S([ping(3), Step.set_layer(0, 3, when=("tick", 3)), Step.set_emission(1, True, when=("tick", 3))]))
    assert fake.order_log == base.order_log


# ---- when kinds ---------------------------------------------------------------------------------------------

def test_seen_when_fires_for_a_new_step_once_the_group_sees_an_enemy():
    step = Step.set_emission(0, True, when=("seen",))
    result, fake = run(S([step]), can_see_fn=lambda f, a, t: f.step_count >= 4)
    assert fake.of("set_emission") == [(4, "set_emission", [1, 2], True)]
    assert result.steps_fired == ((0, 4),)
    result, fake = run(S([step]))
    assert fake.of("set_emission") == [] and result.steps_fired == ()


def test_arrive_when_fires_a_new_step_when_the_group_reaches_its_goal():
    def script(tick, fake):
        if tick + 1 == 5:
            for u in fake.units_of(0):
                fake.set_pos(u, A1[0], A1[1])
    step = Step.set_layer(0, 2, when=("arrive", 50.0))
    result, fake = run(S([step]), script=script)
    assert result.steps_fired == ((0, 5),)
    assert fake.of("set_layer") == [(5, "set_layer", [1, 2], 2)]


def test_arrive_all_when_is_accepted_and_fires_for_a_new_step():
    def script(tick, fake):
        if tick + 1 == 5:
            for u in fake.units_of(0):
                fake.set_pos(u, A1[0], A1[1])
            for u in fake.units_of(1):
                fake.set_pos(u, A0[0], A0[1])
    result, _ = run(S([Step.set_emission(1, True, when=("arrive_all", 50.0))]), script=script)
    assert result.steps_fired == ((0, 5),)


# ---- order log ----------------------------------------------------------------------------------------------

def test_every_new_step_appears_in_the_order_log_in_listed_order_among_the_old_kinds():
    steps = [Step.set_emission(1, True, when=("tick", 2)), ping(2), Step(0, ("tick", 5), "move", (1.0, 1.0)),
             Step.set_layer(0, 3, when=("tick", 7))]
    result, _ = run(S(steps))
    assert result.steps_fired == ((0, 2), (1, 2), (2, 5), (3, 7))


def test_a_step_on_a_dead_group_is_dropped_like_the_old_kinds():
    def script(tick, fake):
        for u in fake.units_of(0):
            fake.set_hp(u, 0.0)
    result, fake = run(S([Step.set_layer(0, 3, when=("tick", 5))]), script=script)
    assert result.steps_fired == () and fake.of("set_layer") == []


# ---- no new steps: nothing changes --------------------------------------------------------------------------

ROW5 = dict(knob="none", knob_value=None, baseline="none", ceiling_hit=0, prefight="ok")   # LAB-REV2-L2: the five supplied columns


def _old_columns(row):
    """The twelve columns of BASELINE_ROW (recorded before the rev 2 columns existed), in the row's order."""
    return {k: row[k] for k in BASELINE_ROW}


def test_a_fight_without_the_new_steps_gives_the_recorded_row_and_no_new_calls():
    """LAB-REV2-L2: the rev 2 columns come after the twelve recorded ones, which are unchanged."""
    result, fake = run(S())
    row = fight_row(result, **ROW5)
    assert _old_columns(row) == BASELINE_ROW
    assert repr(_old_columns(row)) == repr(BASELINE_ROW)
    assert list(row)[:len(BASELINE_ROW)] == list(BASELINE_ROW)
    assert result.steps_fired == () and fake.new_log == []


def test_old_steps_alone_leave_the_row_unchanged_by_the_new_code():
    old = [Step(0, ("tick", 3), "move", (5.0, 6.0))]
    r1, _ = run(S(old))
    r2, _ = run(S(old))
    assert fight_row(r1, **ROW5) == fight_row(r2, **ROW5) and r1.steps_fired == ((0, 3),)
