# spec: docs/northstar/plans/2026-10-05-space-lab-stage1-spec.md::orders lane - Step.ping, Step.set_layer, Step.set_emission through the production library
"""The new timeline steps through fight() and the real engine.

A SpyEngine records, after every engine step, what side 0 or 1 can see and where the tracked units are, so each
test reads the effect of a step in the world rather than the call. The recorder runs inside step(), before the
fight's timeline check of that tick, so a step issued at tick T first shows in the record of tick T+1.
Distances come from test_bindings_real.py (ping reach 2000, radius 500, caster on layer 0, target four layers up).
"""
import dataclasses
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.skilllab import engine  # noqa: E402
from scripts.skilllab.contract import Group, Setup, Step  # noqa: E402
from scripts.skilllab.fight import fight  # noqa: E402
from scripts.skilllab.rows import fight_row  # noqa: E402

HIGH = 4                    # four layers above the caster: no passive sight
NEAR = 3
PING_AT = 10                # tick of the ping step; provisional (2026-10-05)
STEP_AT = 5                 # tick of the layer and emission steps; provisional (2026-10-05)
MAX_TICKS = 120             # provisional (2026-10-05)
SETTLE_TICKS = 80           # a Raider takes 20 ticks to change layer; generous margin as in test_bindings_real
EMIT_SEEN_MULT = 2.0        # the csim tests' value
SILENT_RANGE, LOUD_GAP = 600.0, 600.0   # observer sensor 1000: seen at 600 only when emitting (test_bindings_real 7)
IDLE_FAR = 9000.0
DUMMY = {"Dummy": {"base": "Raider", "set": {"base_damage": 0.0}}}   # never fires, so nothing dies and no fight ends early

BASELINE_ROW = {'outcome': 'cap', 'margin': -0.07500000000000007, 'strength_left_0': 0.7799999999999999,
                'strength_left_1': 0.855, 'survivors_0': 3, 'survivors_1': 3, 'heads_0': 3,
                'heads_1': 3, 'ticks': 400, 'first_contact_tick': 65, 'firing_unit_seconds_0': 34.0,
                'firing_unit_seconds_1': 50.75}


class SpyEngine(engine.Engine):
    """Engine that, after each step, records per tick: ids side `watcher` can see, and every spawned unit's layer."""

    def __init__(self, watcher=0):
        super().__init__()
        self.watcher, self.tick = watcher, 0
        self.spawned = []        # (unit id, faction, layer at spawn)
        self.visible = {}        # tick -> set of enemy ids the watcher side can see (sight or ping)
        self.sight = {}          # tick -> set seen by true sight only
        self.layers = {}         # tick -> {unit id: layer}

    def spawn(self, w, type_id, faction, x, y, layer):
        u = super().spawn(w, type_id, faction, x, y, layer)
        self.spawned.append((u, faction, layer))
        return u

    def step(self, w):
        super().step(w)
        self.tick += 1
        foes = [u for u, f, _ in self.spawned if f != self.watcher]
        self.visible[self.tick] = self.visible_enemies(w, self.watcher, foes)
        self.sight[self.tick] = self.seen_by_sight(w, self.watcher, foes)
        self.layers[self.tick] = {u: self.unit_layer(w, u) for u, _, _ in self.spawned}

    def ids_on(self, faction, layer):
        return [u for u, f, la in self.spawned if f == faction and la == layer]

    def first_tick_seen(self, uid):
        return next((t for t in sorted(self.visible) if uid in self.visible[t]), None)


@pytest.fixture(scope="module")
def lib():
    return engine.Engine()


def G(side, unit, x, y, layer, count=1, order="idle"):
    return Group(side=side, unit=unit, count=count, formation="line", x=x, y=y, facing_deg=0.0 if side == 0 else 180.0,
                 layer=layer, order=order, params={"spacing": 30.0})


def run(groups, steps, watcher=0, settings=None, max_ticks=MAX_TICKS):
    spy = SpyEngine(watcher)
    setup = Setup(groups=tuple(groups), unit_types=DUMMY, max_ticks=max_ticks,
                  settings=settings or {}, timeline=tuple(steps))
    return fight(setup, 0, False, engine=spy), spy


def ping_groups():
    """Side 0 Raider caster at the origin, layer 0; side 1 dummies 1600 away on layer 4 and on layer 3."""
    return [G(0, "Raider", 0.0, 0.0, 0), G(1, "Dummy", 1600.0, 0.0, HIGH), G(1, "Dummy", 1500.0, 150.0, NEAR)]


def ping_step(layer):
    return Step.ping(layer, 1500.0, 0.0, casters="all", when=("tick", PING_AT))


# ---- ping ---------------------------------------------------------------------------------------------------

def test_control_without_a_ping_nothing_is_seen():
    _, spy = run(ping_groups(), [])
    assert all(not seen for seen in spy.visible.values())


def test_ping_at_tick_T_reveals_the_unit_in_its_disc_on_that_layer_only():
    result, spy = run(ping_groups(), [ping_step(HIGH)])
    (high,), (near,) = spy.ids_on(1, HIGH), spy.ids_on(1, NEAR)
    assert result.steps_fired == ((0, PING_AT),)
    assert spy.first_tick_seen(high) == PING_AT + 1
    assert all(high not in spy.visible[t] for t in range(1, PING_AT + 1)), "not before the step"
    assert all(near not in seen for seen in spy.visible.values()), "the other layer stays hidden"
    assert all(not s for s in spy.sight.values()), "a ping reveal is not sight"


def test_ping_on_the_other_layer_reveals_the_other_unit():
    _, spy = run(ping_groups(), [ping_step(NEAR)])
    (high,), (near,) = spy.ids_on(1, HIGH), spy.ids_on(1, NEAR)
    assert spy.first_tick_seen(near) == PING_AT + 1
    assert all(high not in seen for seen in spy.visible.values())


def test_ping_reveal_ends_after_the_reveal_time():
    _, spy = run(ping_groups(), [ping_step(HIGH)], max_ticks=300)
    (high,) = spy.ids_on(1, HIGH)
    seen = [t for t in sorted(spy.visible) if high in spy.visible[t]]
    assert seen and seen[0] == PING_AT + 1 and seen[-1] < 300, "revealed, then hidden again before the end"


# ---- set_layer ----------------------------------------------------------------------------------------------

def test_set_layer_step_moves_its_group_within_the_transition_time_and_leaves_others():
    groups = [G(0, "Raider", 300.0, 400.0, 2, count=2), G(0, "Raider", 1500.0, 1500.0, 2),
              G(1, "Dummy", IDLE_FAR, IDLE_FAR, 2)]
    result, spy = run(groups, [Step.set_layer(0, 3, when=("tick", STEP_AT))])
    moved, control = spy.ids_on(0, 2)[:2], spy.ids_on(0, 2)[2]
    assert result.steps_fired == ((0, STEP_AT),)
    assert all(spy.layers[STEP_AT][u] == 2 for u in moved), "not before the step"
    assert all(spy.layers[STEP_AT + SETTLE_TICKS][u] == 3 for u in moved)
    assert all(layers[control] == 2 for layers in spy.layers.values()), "control: the other group stays"


# ---- set_emission -------------------------------------------------------------------------------------------

def emission_groups():
    """Side 1 Interceptor observer (sensor 1000) at layer 2; side 0 dummy one layer up, 600 away."""
    return [G(0, "Dummy", SILENT_RANGE, 0.0, NEAR), G(1, "Interceptor", 0.0, 0.0, 2)]


def test_emission_step_makes_the_force_visible_from_farther_across_layers():
    settings = {"OM_TP_EMIT_SEEN_MULT": EMIT_SEEN_MULT}
    result, spy = run(emission_groups(), [Step.set_emission(0, True, when=("tick", STEP_AT))], watcher=1,
                      settings=settings)
    (target,) = spy.ids_on(0, NEAR)
    assert result.steps_fired == ((0, STEP_AT),)
    assert all(target not in spy.visible[t] for t in range(1, STEP_AT + 1)), "control: silent, not seen at 600"
    assert spy.first_tick_seen(target) == STEP_AT + 1
    assert all(target in spy.visible[t] for t in range(STEP_AT + 1, MAX_TICKS + 1))


def test_emission_off_step_hides_it_again():
    settings = {"OM_TP_EMIT_SEEN_MULT": EMIT_SEEN_MULT}
    steps = [Step.set_emission(0, True, when=("tick", STEP_AT)), Step.set_emission(0, False, when=("tick", 3 * STEP_AT))]
    result, spy = run(emission_groups(), steps, watcher=1, settings=settings)
    (target,) = spy.ids_on(0, NEAR)
    assert result.steps_fired == ((0, STEP_AT), (1, 3 * STEP_AT))
    assert target in spy.visible[2 * STEP_AT] and target not in spy.visible[3 * STEP_AT + 2]


# ---- order log ----------------------------------------------------------------------------------------------

def test_all_three_new_steps_are_in_the_order_log_with_their_ticks():
    groups = ping_groups() + [G(0, "Raider", 300.0, 400.0, 2)]
    steps = [ping_step(HIGH), Step.set_layer(3, 3, when=("tick", STEP_AT)), Step.set_emission(3, True, when=("tick", 2 * STEP_AT))]
    result, _ = run(groups, steps)
    assert PING_AT == 2 * STEP_AT, "the ping and the emission step share a tick, so listed order decides"
    assert result.steps_fired == ((1, STEP_AT), (0, PING_AT), (2, 2 * STEP_AT))


# ---- no new steps: nothing changes --------------------------------------------------------------------------

def _old_columns(result):
    """LAB-REV2-L2 (Q-LAB-03, spec "CSV columns"): the row gained the window, weighted, prediction and supplied columns; the twelve
    recorded values are compared unchanged (max_ticks 400 is a deliberate cap here, not a defect)."""
    row = fight_row(result, knob="none", knob_value=None, baseline="none", ceiling_hit=0, prefight="ok")
    return {k: row[k] for k in BASELINE_ROW}


def test_a_fight_without_the_new_steps_gives_the_recorded_row(lib):
    def side(s, x, f):
        return Group(side=s, unit="Vanguard", count=3, formation="line", x=x, y=400.0, facing_deg=f, layer=0,
                     order="attack_move", params={"spacing": 30.0})
    setup = Setup(groups=(side(0, 400.0, 0.0), side(1, 1200.0, 180.0)), unit_types={}, max_ticks=400)
    result = fight(setup, 3, False, engine=lib)
    assert _old_columns(result) == BASELINE_ROW
    assert repr(_old_columns(result)) == repr(BASELINE_ROW)
    assert result.steps_fired == ()
    assert _old_columns(fight(dataclasses.replace(setup, timeline=()), 3, False, engine=lib)) == BASELINE_ROW
