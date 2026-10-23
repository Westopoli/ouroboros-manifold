# Rule pins: R-096-08@629328
# spec: R-096-08 (the unit holds, fires in range, never walks) - guard order through the production library
"""A guard unit never gets a destination, never walks, and fires once an enemy is in range."""
import dataclasses
import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.skilllab import engine, fight  # noqa: E402
from scripts.skilllab.contract import Group, Setup, Step  # noqa: E402

SETTINGS = {"OM_TP_PURSUE_BY_STEERING": 1}


@pytest.fixture(scope="module")
def lib():
    return engine.Engine()


def _setup(guard_order="guard", steps=(), max_ticks=300):
    guard = Group(side=0, unit="Vanguard", count=1, formation="line", x=400.0, y=400.0, facing_deg=0.0, layer=0,
                  order=guard_order, params={"spacing": 30.0})
    walker = Group(side=1, unit="Vanguard", count=1, formation="line", x=1400.0, y=400.0, facing_deg=180.0, layer=0,
                   order="attack_move", goal=(400.0, 400.0), params={"spacing": 30.0})
    return Setup(groups=(guard, walker), unit_types={}, max_ticks=max_ticks, settings=SETTINGS,
                 timeline=tuple(steps))


def _watch(lib, setup, ticks):
    """Step the fight by hand: [(tick, destination, pos, enemy hp)] for unit 1 (the guard) and unit 2 (the walker)."""
    # fight() does not expose a per-tick hook, so rebuild its world the same way the harness does
    w = lib.new_world(0)
    try:
        lib.disable_abilities(w)
        for n, v in setup.settings.items():
            lib.set_param(w, lib.param_id(n), v)
        tid = lib.type_id("Vanguard")
        a = lib.spawn(w, tid, 0, 400.0, 400.0, 0)
        b = lib.spawn(w, tid, 1, 1400.0, 400.0, 0)
        if setup.groups[0].order == "guard":
            lib.order_guard(w, [a])
        else:
            lib.order_attack_move(w, [a], 1400.0, 400.0)
        lib.order_attack_move(w, [b], 400.0, 400.0)
        out = []
        for tick in range(1, ticks + 1):
            for s in setup.timeline:
                if s.when == ("tick", tick):
                    lib.order_guard(w, [a])
            lib.step(w)
            out.append((tick, lib.unit_destination(w, a), lib.unit_pos(w, a), lib.unit_hp(w, b)))
        return out, a
    finally:
        lib.free_world(w)


def test_guard_unit_has_no_destination_and_stays_put(lib):
    series, _ = _watch(lib, _setup(), 200)
    assert all(dest is None for _, dest, _, _ in series)
    x0, y0 = series[0][2]
    assert all(math.hypot(x - x0, y - y0) <= 1.0 for _, _, (x, y), _ in series)


def test_guard_unit_fires_when_the_enemy_walks_into_range(lib):
    series, _ = _watch(lib, _setup(), 300)
    start_hp = series[0][3]
    assert min(hp for *_, hp in series) < start_hp, "the guard never hurt the walker"
    first_hit = next(t for t, _, _, hp in series if hp < start_hp)
    assert first_hit > 5, "the walker started 1000 wu away; a hit this early means the guard walked"


def test_whole_fight_through_fight_runs_with_guard_defender(lib):
    r = fight.fight(_setup(), 0, False, engine=lib)
    assert r.ticks > 0 and r.heads == (1, 1) and r.first_contact_tick >= 0
    assert r == fight.fight(_setup(), 0, False, engine=lib)


def test_guard_step_at_tick_20_stops_an_attack_move_unit(lib):
    """Through fight(): walking before the step, not moving after it. LAB-REV2-L2: FightResult.states is (tick, unit, code) now,
    never a "walking" string, so the walk and the stop are read from the trace positions alone."""
    s = dataclasses.replace(_setup(guard_order="attack_move", steps=[Step(group=0, when=("tick", 20), order="guard")],
                                   max_ticks=80), trace=True)
    r = fight.fight(s, 0, False, engine=lib)
    assert r.steps_fired == ((0, 20),)
    pos = {t: (x, y) for t, u, x, y, *_ in r.trace if u == 1}
    x0, y0 = pos[21]
    assert all(math.hypot(x - x0, y - y0) <= 1.0 for t, (x, y) in pos.items() if t >= 21)
    assert math.hypot(pos[19][0] - pos[0][0], pos[19][1] - pos[0][1]) > 1.0, "it should have walked before the step"
    assert math.hypot(pos[19][0] - pos[15][0], pos[19][1] - pos[15][1]) > 1.0, "it was still walking just before the step"
