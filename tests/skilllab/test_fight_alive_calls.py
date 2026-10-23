# spec: Architect speed brief, change 1 (fight passes its own living set)
"""A whole fight() makes no unit_alive call, and its result is unchanged."""
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
from scripts.skilllab.contract import Group, Setup  # noqa: E402
from scripts.skilllab.fight import fight  # noqa: E402

pytestmark = pytest.mark.usefixtures("seam")   # LAB-REV2-L2: fight() reads the firing counts through the L1/L2 seam (fakes.Seam)


@pytest.fixture(autouse=True)
def stub_place(monkeypatch):
    def stub(kind, n, x, y, facing_deg, params):
        return [(x + 7.0 * i, y) for i in range(n)]

    monkeypatch.setattr(formations_mod, "place", stub)
    monkeypatch.setattr(fight_mod, "place", stub, raising=False)


def G(side, unit, count):
    return Group(side=side, unit=unit, count=count, formation="line", x=-30.0 if side == 0 else 30.0, y=0.0,
                 facing_deg=0.0 if side == 0 else 180.0, layer=0, order="attack_move", goal=None,
                 params={"spacing": 30.0})


def hurt_and_kill(t, f):
    if t == 1:
        s0, s1 = f.units_of(0), f.units_of(1)
        f.set_hp(s0[0], 50); f.set_hp(s1[0], 20); f.set_hp(s1[2], 10); f.set_hp(s1[1], 0)
    if t == 6:
        f.set_hp(f.units_of(0)[1], 0)


def run():  # script below drives the deaths
    setup = Setup(groups=(G(0, "Vanguard", 2), G(1, "Warden", 4)), unit_types={}, abilities=False,
                  max_ticks=10, sample_every=5)
    fake = FakeEngine(script=hurt_and_kill)
    return fight(setup, 0, False, engine=fake), fake


def test_a_whole_fight_makes_zero_unit_alive_calls():
    _, fake = run()
    assert fake.calls_named("unit_alive") == []


def test_the_result_equals_the_literal_recorded_from_the_pre_change_code():
    # Literals recorded by hand from the pre-change code (unit_alive-based firing), same scripted fight.
    res, _ = run()
    assert res.firing == [(0, 2, 1), (5, 2, 1), (10, 1, 1)]
    assert res.survivors == (1, 3)
    assert res.firing_unit_seconds == (1.25, 0.75)
    assert (res.outcome, res.ticks, res.first_contact_tick) == ("cap", 10, 0)
