# spec: ruling A201 (the stall detector mislabels): draw, cap and quiet stalemate are three outcomes
"""fight() outcome labels on a FakeEngine: "draw" (both last units die on one tick), "cap" (still active at
max_ticks), "stalemate" (stalemate_ticks ticks with no hp change). Placement is stubbed like test_fight.py."""
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


@pytest.fixture(autouse=True)
def stub_place(monkeypatch):
    def stub(kind, n, x, y, facing_deg, params):
        return [(x + 7.0 * i, y) for i in range(n)]

    monkeypatch.setattr(formations_mod, "place", stub)
    monkeypatch.setattr(fight_mod, "place", stub, raising=False)


def G(side, count=1):
    return Group(side=side, unit="Vanguard", count=count, formation="line", x=-300.0 if side == 0 else 300.0, y=0.0,
                 facing_deg=0.0 if side == 0 else 180.0, layer=0, order="attack_move", goal=None,
                 params={"spacing": 30.0})


def S(max_ticks=50, stalemate_ticks=1000):
    return Setup(groups=(G(0), G(1)), unit_types={}, max_ticks=max_ticks, stalemate_ticks=stalemate_ticks,
                 sample_every=5)


def run(setup, script=None):
    return fight(setup, 0, False, engine=FakeEngine(script=script))


def kill(fake, faction):
    for u in fake.units_of(faction):
        fake.set_hp(u, 0)


def _double_kill():
    return run(S(), lambda t, f: (kill(f, 0), kill(f, 1)) if t == 3 else None)


def _quiet():
    return run(S(max_ticks=100, stalemate_ticks=10))


def _capped():
    def poke(t, f):                      # a hp change every 4 ticks keeps the fight loud until the cap
        if t % 4 == 3:
            u = f.units_of(1)[0]
            f.set_hp(u, f.units[u]["hp"] - 1)
    return run(S(max_ticks=30, stalemate_ticks=10), poke)


def _side0():
    return run(S(), lambda t, f: kill(f, 1) if t == 3 else None)


def _side1():
    return run(S(), lambda t, f: kill(f, 0) if t == 3 else None)


@pytest.mark.parametrize("scenario,outcome", [(_double_kill, "draw"), (_quiet, "stalemate"), (_capped, "cap"),
                                              (_side0, "side0"), (_side1, "side1")])
def test_each_ending_has_its_own_label(scenario, outcome):
    assert scenario().outcome == outcome


def test_double_kill_is_a_draw_with_zero_margin_and_no_survivors():
    r = _double_kill()
    assert (r.outcome, r.margin, r.survivors, r.strength_left, r.ticks) == ("draw", 0.0, (0, 0), (0.0, 0.0), 4)


def test_positive_control_old_labelling_called_the_draw_a_stalemate():
    """The old code labelled the double kill "stalemate"; it must not any more, and a real quiet one still is."""
    assert _double_kill().outcome != "stalemate"
    assert _quiet().outcome == "stalemate"


def test_quiet_stalemate_ends_after_stalemate_ticks():
    r = _quiet()
    assert (r.outcome, r.ticks) == ("stalemate", 10)


def test_default_stalemate_window_is_400_quiet_ticks():
    r = run(S(max_ticks=6000, stalemate_ticks=Setup(groups=(), unit_types={}).stalemate_ticks))
    assert (r.outcome, r.ticks) == ("stalemate", 400)


def test_cap_when_hp_still_changes_at_max_ticks():
    r = _capped()
    assert (r.outcome, r.ticks) == ("cap", 30)


@pytest.mark.parametrize("scenario,outcome", [(_double_kill, "draw"), (_quiet, "stalemate"), (_capped, "cap")])
def test_the_three_non_win_labels_never_mix(scenario, outcome):
    """Each scenario gets exactly its own label and none of the other two."""
    got = scenario().outcome
    assert got == outcome
    assert {got} & ({"draw", "stalemate", "cap"} - {outcome}) == set()
