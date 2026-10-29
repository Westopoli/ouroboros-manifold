# spec: ruling A196 (per-side target policy): Setup.target_policy pair, OM_TP_TARGET_POLICY_FACTION_1
"""Setup.target_policy on a FakeEngine.

Contract: None sets nothing; otherwise a pair (p0, p1), each None (leave unset), 0 or 1. fight() validates it
beside the other checks (ValueError before new_world), then after the Setup.settings loop sets
OM_TP_TARGET_POLICY to p0 (when not None) and OM_TP_TARGET_POLICY_FACTION_1 to p1 (when not None), so the pair
wins over a plain settings entry of the same id.
"""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
for _p in (ROOT, Path(__file__).resolve().parent):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import fakes_trace  # noqa: E402
import scripts.skilllab.fight as fight_mod  # noqa: E402
import scripts.skilllab.formations as formations_mod  # noqa: E402
from fakes_trace import PARAMS, TraceFakeEngine  # noqa: E402
from scripts.skilllab.contract import Group, Setup  # noqa: E402
from scripts.skilllab.fight import fight  # noqa: E402

pytestmark = pytest.mark.usefixtures("seam")   # LAB-REV2-L2: fight() reads the firing counts through the L1/L2 seam (fakes.Seam)

F1 = "OM_TP_TARGET_POLICY_FACTION_1"
P0 = "OM_TP_TARGET_POLICY"


@pytest.fixture(autouse=True)
def stubs(monkeypatch):
    def stub(kind, n, x, y, facing_deg, params):
        return [(x + 7.0 * i, y) for i in range(n)]

    monkeypatch.setattr(formations_mod, "place", stub)
    monkeypatch.setattr(fight_mod, "place", stub, raising=False)
    entry = (47, -1.0, -1.0, 1.0)          # the engine's new id: default -1 (unset, follows faction 0)
    monkeypatch.setitem(PARAMS, F1, entry)
    monkeypatch.setitem(fakes_trace._BY_ID, 47, (F1,) + entry[1:])


def G(side):
    return Group(side=side, unit="Vanguard", count=2, formation="line", x=-300.0 if side == 0 else 300.0,
                 y=0.0, facing_deg=0.0 if side == 0 else 180.0, layer=0, order="attack_move", goal=None,
                 params={"spacing": 30.0})


def S(pair="absent", settings=None):
    kw = {} if pair == "absent" else {"target_policy": pair}
    if settings is not None:
        kw["settings"] = settings
    return Setup(groups=(G(0), G(1)), unit_types={}, max_ticks=10, **kw)


def run(setup):
    fake = TraceFakeEngine()
    fight(setup, 0, False, engine=fake)
    return fake


def sets(fake):
    return [(c[2], c[3]) for c in fake.calls_named("set_param")]


def test_default_is_none():
    assert S().target_policy is None


def test_none_pair_sets_nothing_extra():
    assert sets(run(S(None))) == [] and sets(run(S())) == []


def test_only_faction_0():
    assert sets(run(S((1, None)))) == [(PARAMS[P0][0], 1.0)]


def test_only_faction_1():
    assert sets(run(S((None, 1)))) == [(PARAMS[F1][0], 1.0)]


def test_both_with_values():
    got = sets(run(S((0, 1))))
    assert sorted(got) == sorted([(PARAMS[P0][0], 0.0), (PARAMS[F1][0], 1.0)])
    assert all(isinstance(v, float) for _i, v in got)


def test_pair_is_set_after_the_settings_loop():
    fake = run(S((1, 1), settings={"OM_TP_LEASH_BEFORE_DAMAGE": 1.0, "OM_TP_PURSUE_BY_STEERING": 0.0}))
    ids = [i for i, _v in sets(fake)]
    assert ids[:2] == [PARAMS["OM_TP_LEASH_BEFORE_DAMAGE"][0], PARAMS["OM_TP_PURSUE_BY_STEERING"][0]] or \
        set(ids[:2]) == {PARAMS["OM_TP_LEASH_BEFORE_DAMAGE"][0], PARAMS["OM_TP_PURSUE_BY_STEERING"][0]}
    assert set(ids[2:]) == {PARAMS[P0][0], PARAMS[F1][0]} and len(ids) == 4
    assert max(i for i, c in enumerate(fake.calls) if c[0] == "set_param") < \
        next(i for i, c in enumerate(fake.calls) if c[0] == "step")


def test_pair_wins_over_settings_entry():
    seen = {}
    fake = TraceFakeEngine(script=lambda k, f: None if seen else seen.update(f.params))
    fight(S((0, None), settings={P0: 1.0}), 0, False, engine=fake)
    assert seen[PARAMS[P0][0]] == 0.0
    assert seen[PARAMS[F1][0]] == -1.0     # still unset


def test_settings_entry_stays_valid_when_pair_is_none():
    seen = {}
    fake = TraceFakeEngine(script=lambda k, f: None if seen else seen.update(f.params))
    fight(S(None, settings={P0: 1.0}), 0, False, engine=fake)
    assert seen[PARAMS[P0][0]] == 1.0


@pytest.mark.parametrize("pair", [(2, None), (None, 2), (-1, None), (None, -1), ("x", None), (None, "x"),
                                  (0, 1, 0), (0,), (), 1])
def test_bad_pair_raises_before_new_world(pair):
    fake = TraceFakeEngine()
    with pytest.raises(ValueError):
        fight(S(pair), 0, False, engine=fake)
    assert not fake.calls_named("new_world") and not fake.calls_named("step")
