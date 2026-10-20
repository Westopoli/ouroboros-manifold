# spec: docs/northstar/plans/2026-10-02-movement-layers-and-search-plan.md::Phase S::first bullet (per-fight settings in Setup)
# spec: docs/northstar/plans/2026-10-02-movement-layers-and-search-plan.md::Appendix::PP-contract (om_tactical_set_param)
"""Setup.settings, on a FakeEngine (no compiler, no library).

Contract these tests fix (the implementation under scripts/skilllab comes later):
  Setup.settings: mapping of an `OM_TP_*` parameter NAME to a number, default empty.
  fight() resolves each name with engine.param_id(name) (the library's own enum value, never a number the
  harness made up), then engine.set_param(w, id, float(value)), after new_world and before the first step.
  Engine.set_param raises ValueError when the library refuses (unknown id, out of range); fight() lets it
  propagate: no step is taken, the world is still freed, nothing is caught and nothing is skipped.
  An unknown name raises ValueError from param_id the same way.
  Settings belong to the world, so they never carry from one fight to the next.
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
from fakes_trace import PARAMS, TraceFakeEngine  # noqa: E402
from scripts.skilllab.contract import Group, Setup  # noqa: E402
from scripts.skilllab.fight import fight  # noqa: E402

pytestmark = pytest.mark.usefixtures("seam")   # LAB-REV2-L2: fight() reads the firing counts through the L1/L2 seam (fakes.Seam)


@pytest.fixture(autouse=True)
def place_stub(monkeypatch):
    def stub(kind, n, x, y, facing_deg, params):
        return [(x + 7.0 * i, y) for i in range(n)]

    monkeypatch.setattr(formations_mod, "place", stub)
    monkeypatch.setattr(fight_mod, "place", stub, raising=False)


def G(side, count=2):
    return Group(side=side, unit="Vanguard", count=count, formation="line", x=-300.0 if side == 0 else 300.0,
                 y=0.0, facing_deg=0.0 if side == 0 else 180.0, layer=0, order="attack_move", goal=None,
                 params={"spacing": 30.0})


def S(settings=None, max_ticks=10):
    kw = {} if settings is None else {"settings": settings}
    return Setup(groups=(G(0), G(1)), unit_types={}, max_ticks=max_ticks, **kw)


def run(setup, **fake_kw):
    fake = TraceFakeEngine(**fake_kw)
    return fight(setup, 0, False, engine=fake), fake


def first_index(calls, name):
    return next(i for i, c in enumerate(calls) if c[0] == name)


# ---- shape -------------------------------------------------------------------------------------------------

def test_settings_default_is_empty_and_makes_no_call():
    assert len(Setup(groups=(G(0), G(1)), unit_types={}).settings) == 0
    _result, fake = run(S())
    assert not fake.calls_named("set_param") and not fake.calls_named("param_id")


def test_each_setting_is_set_through_the_library_s_own_id():
    settings = {"OM_TP_TARGET_POLICY": 1, "OM_TP_LEASH_BEFORE_DAMAGE": 1.0}
    _result, fake = run(S(settings))
    sets = fake.calls_named("set_param")
    assert sorted((c[2], c[3]) for c in sets) == sorted(
        (PARAMS[n][0], float(v)) for n, v in settings.items())
    assert all(isinstance(c[3], float) for c in sets)
    assert sorted(c[1] for c in fake.calls_named("param_id")) == sorted(settings)   # the ids came from a lookup


def test_settings_are_applied_before_the_first_tick():
    """Before the first step, and visible through get_param on the world at tick 0 (the fake records the table
    at the first step)."""
    seen = {}

    def script(k, fake):
        if k == 0:
            seen.update(fake.params)

    settings = {"OM_TP_TARGET_POLICY": 1.0, "OM_TP_PURSUE_BY_STEERING": 0.0}
    _result, fake = run(S(settings), script=script)
    last_set = max(i for i, c in enumerate(fake.calls) if c[0] == "set_param")
    assert last_set < first_index(fake.calls, "step")
    assert seen[PARAMS["OM_TP_TARGET_POLICY"][0]] == 1.0
    assert seen[PARAMS["OM_TP_PURSUE_BY_STEERING"][0]] == 0.0
    assert seen[PARAMS["OM_TP_ROUTE_AROUND_TERRAIN"][0]] == PARAMS["OM_TP_ROUTE_AROUND_TERRAIN"][1]  # untouched


def test_settings_do_not_carry_to_the_next_fight():
    fake = TraceFakeEngine()
    fight(S({"OM_TP_TARGET_POLICY": 1.0}), 0, False, engine=fake)
    n = len(fake.calls)
    seen = {}
    fake.script = lambda k, f: None if seen else seen.update(f.params)    # step_count runs on across fights
    fight(S(), 0, False, engine=fake)
    assert not [c for c in fake.calls[n:] if c[0] == "set_param"]
    assert seen[PARAMS["OM_TP_TARGET_POLICY"][0]] == PARAMS["OM_TP_TARGET_POLICY"][1]


# ---- refusal, loudly ---------------------------------------------------------------------------------------

def test_unknown_setting_name_is_refused_before_any_step():
    fake = TraceFakeEngine()
    with pytest.raises(ValueError, match="OM_TP_NO_SUCH_THING"):
        fight(S({"OM_TP_NO_SUCH_THING": 1.0}), 0, False, engine=fake)
    assert not fake.calls_named("step")
    assert fake.worlds_freed == [fake.world]


def test_one_bad_name_among_good_ones_still_refuses_the_whole_fight():
    fake = TraceFakeEngine()
    with pytest.raises(ValueError):
        fight(S({"OM_TP_TARGET_POLICY": 1.0, "OM_TP_NO_SUCH_THING": 1.0}), 0, False, engine=fake)
    assert not fake.calls_named("step")


@pytest.mark.parametrize("name,value", [("OM_TP_TARGET_POLICY", 2.0), ("OM_TP_TARGET_POLICY", -1.0),
                                        ("OM_TP_PURSUE_BY_STEERING", 7.0), ("OM_TP_TARGET_POLICY", float("nan"))])
def test_out_of_range_setting_is_refused_before_any_step(name, value):
    """The library refuses (the fake mirrors om_tactical_set_param returning -1); the harness neither catches
    nor retries it, and the fight is never played with a half-applied set."""
    fake = TraceFakeEngine()
    with pytest.raises(ValueError):
        fight(S({name: value}), 0, False, engine=fake)
    assert not fake.calls_named("step")
    assert fake.worlds_freed == [fake.world]


def test_a_refusal_is_not_swallowed_into_a_default_run():
    """Positive control for the refusal detector: the same Setup with a valid value runs to the end."""
    result, fake = run(S({"OM_TP_TARGET_POLICY": 1.0}))
    assert result.ticks == 10 and fake.calls_named("step")


ARC = "OM_TP_FIRING_ARC_DEG"


def test_the_fake_mirrors_the_arc_range_lo_5_default_360_hi_360():
    """Decision 48: the arc's lower bound is 5 (it was 10), so the grid's smallest point 7.5 is inside the range."""
    assert PARAMS[ARC][1:] == (360.0, 5.0, 360.0)


@pytest.mark.parametrize("value", [4.9, 0.0, -1.0])
def test_an_arc_below_5_is_a_settings_error_through_settings_and_through_the_setup_field(value):
    """The engine refuses below lo (no clamp); the lab passes the value as given and lets the refusal stand, before any step."""
    for setup in (S({ARC: value}), Setup(groups=(G(0), G(1)), unit_types={}, max_ticks=10, firing_arc_deg=value)):
        fake = TraceFakeEngine()
        with pytest.raises(ValueError):
            fight(setup, 0, False, engine=fake)
        assert not fake.calls_named("step") and fake.params[PARAMS[ARC][0]] == 360.0     # refused, not clamped to 5


@pytest.mark.parametrize("value", [5.0, 7.5, 15.0, 360.0])
def test_control_an_arc_of_5_7_5_15_and_360_is_accepted_and_reaches_the_world_unchanged(value):
    """Positive control for the refusal above: the same two routes with a valid value run to the end; 7.5 is the grid's smallest point."""
    result, fake = run(S({ARC: value}))
    assert result.ticks == 10 and fake.params[PARAMS[ARC][0]] == value
    fake2 = TraceFakeEngine()
    fight(Setup(groups=(G(0), G(1)), unit_types={}, max_ticks=10, firing_arc_deg=value), 0, False, engine=fake2)
    assert fake2.params[PARAMS[ARC][0]] == value


# ---- the settings reach the result ------------------------------------------------------------------------

def test_a_setting_changed_from_default_changes_what_the_fight_returns():
    """Binding positive control on the fake: a script that reads the table the way a rule would."""
    def script(k, fake):
        if k == 2 and fake.params[PARAMS["OM_TP_TARGET_POLICY"][0]] == 1.0:
            for u in fake.units_of(1):
                fake.set_hp(u, 0)

    base, _ = run(S(), script=script)
    changed, _ = run(S({"OM_TP_TARGET_POLICY": 1.0}), script=script)
    assert (base.outcome, base.ticks) != (changed.outcome, changed.ticks)


def test_a_setting_at_its_default_changes_nothing():
    """Null control on the fake: every parameter set to the fake's own default gives the unset result."""
    def script(k, fake):
        if k == 2 and fake.params[PARAMS["OM_TP_TARGET_POLICY"][0]] == 1.0:
            for u in fake.units_of(1):
                fake.set_hp(u, 0)

    explicit = {n: d for n, (_i, d, _lo, _hi) in PARAMS.items()}
    base, _ = run(S(), script=script)
    same, _ = run(S(explicit), script=script)
    assert dataclasses.asdict(base) == dataclasses.asdict(same)
