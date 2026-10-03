# spec: docs/northstar/plans/2026-10-02-movement-layers-and-search-plan.md::Phase S::first bullet (per-fight settings in Setup)
# spec: docs/northstar/plans/2026-10-02-movement-layers-and-search-plan.md::Appendix::PP-contract (om_tactical_set_param)
"""Setup.settings bound to the production library through om_tactical_get_param / om_tactical_set_param.

These tests need the C calls of piece PP-contract (not yet in the library): they stay red, for that reason,
until it lands. Parameters are referenced by NAME; the harness's `Engine.param_id(name)` supplies the value
the library exports (parsed from the header's `om_tac_param` enum, the contract document's source of truth),
so nothing here writes an enum number. Defaults are the plan's: OM_TP_PURSUE_BY_STEERING,
OM_TP_ROUTE_AROUND_TERRAIN, OM_TP_TARGET_BY_SIGHT, OM_TP_ROUTE_ACROSS_LAYERS 1; OM_TP_LEASH_BEFORE_DAMAGE 0;
OM_TP_TARGET_POLICY 0 (nearest). Ranges: the plan says out of range is refused and changes nothing; the
contract document gives the numbers, so the out-of-range probes use values no range could contain for a
switch or a two-way policy (-1, 2, NaN).
"""
import dataclasses
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.skilllab import engine, fight, plays, rows  # noqa: E402

DEFAULTS = {"OM_TP_PURSUE_BY_STEERING": 1.0, "OM_TP_ROUTE_AROUND_TERRAIN": 1.0, "OM_TP_TARGET_BY_SIGHT": 1.0,
            "OM_TP_ROUTE_ACROSS_LAYERS": 1.0, "OM_TP_LEASH_BEFORE_DAMAGE": 0.0, "OM_TP_TARGET_POLICY": 0.0}


@pytest.fixture(scope="module")
def library():
    return engine.Engine()


@pytest.fixture
def world(library):
    w = library.new_world(0)
    yield w
    library.free_world(w)


class FirstTickSpy(engine.Engine):
    """Records every setting as get_param sees it at the moment of the first step."""

    def __init__(self, names):
        super().__init__()
        self.names, self.seen = list(names), None

    def step(self, w):
        if self.seen is None:
            self.seen = {n: self.get_param(w, self.param_id(n)) for n in self.names}
        super().step(w)


def setup_with(settings=None, trace=True, size=8, enemies=8, swap=False, max_ticks=600):
    kw = {} if settings is None else {"settings": settings}
    base = plays.blob_play(size)(enemies, swap)
    return dataclasses.replace(base, trace=trace, max_ticks=max_ticks, **kw)


def observe(settings=None, seed=0, swap=False, eng=None):
    r = fight.fight(setup_with(settings, swap=swap), seed, swap, engine=eng)
    return rows.fight_row(r), repr(r.trace)


# ---- the lookup and the calls ------------------------------------------------------------------------------

def test_param_id_returns_the_library_enum_value_per_name(library):
    ids = {n: library.param_id(n) for n in DEFAULTS}
    assert all(isinstance(i, int) and i >= 0 for i in ids.values())
    assert len(set(ids.values())) == len(ids)


def test_param_id_refuses_an_unknown_name(library):
    with pytest.raises(ValueError, match="OM_TP_NO_SUCH_THING"):
        library.param_id("OM_TP_NO_SUCH_THING")


@pytest.mark.parametrize("name,default", sorted(DEFAULTS.items()))
def test_fresh_world_reads_the_plan_default(library, world, name, default):
    assert library.get_param(world, library.param_id(name)) == default


def test_set_then_get_round_trips_and_is_per_world(library, world):
    pid = library.param_id("OM_TP_TARGET_POLICY")
    library.set_param(world, pid, 1.0)
    assert library.get_param(world, pid) == 1.0
    other = library.new_world(0)
    try:
        assert library.get_param(other, pid) == 0.0       # a second world is untouched: no process-wide state
    finally:
        library.free_world(other)


@pytest.mark.parametrize("name,value", [("OM_TP_TARGET_POLICY", 2.0), ("OM_TP_TARGET_POLICY", -1.0),
                                        ("OM_TP_PURSUE_BY_STEERING", 2.0), ("OM_TP_TARGET_POLICY", float("nan"))])
def test_out_of_range_is_refused_loudly_and_changes_nothing(library, world, name, value):
    pid = library.param_id(name)
    before = library.get_param(world, pid)
    with pytest.raises(ValueError):
        library.set_param(world, pid, value)
    assert library.get_param(world, pid) == before


def test_unknown_param_id_is_refused(library, world):
    with pytest.raises(ValueError):
        library.set_param(world, 10 ** 6, 1.0)


# ---- inside a fight ----------------------------------------------------------------------------------------

def test_settings_are_in_place_before_the_first_tick():
    spy = FirstTickSpy(DEFAULTS)
    fight.fight(setup_with({"OM_TP_TARGET_POLICY": 1.0, "OM_TP_LEASH_BEFORE_DAMAGE": 1.0}), 0, False, engine=spy)
    assert spy.seen == dict(DEFAULTS, OM_TP_TARGET_POLICY=1.0, OM_TP_LEASH_BEFORE_DAMAGE=1.0)


def test_unset_fight_sees_every_default_at_the_first_tick():
    spy = FirstTickSpy(DEFAULTS)
    fight.fight(setup_with(), 0, False, engine=spy)
    assert spy.seen == DEFAULTS


def test_unknown_and_out_of_range_settings_refuse_the_fight(library):
    with pytest.raises(ValueError):
        fight.fight(setup_with({"OM_TP_NO_SUCH_THING": 1.0}), 0, False, engine=library)
    with pytest.raises(ValueError):
        fight.fight(setup_with({"OM_TP_TARGET_POLICY": 5.0}), 0, False, engine=library)


def test_a_fight_with_settings_leaves_nothing_behind_for_the_next(library):
    """The library keeps no setting across worlds: a fight after a changed-setting fight equals a fresh one."""
    fresh = observe(seed=3)
    observe({"OM_TP_TARGET_POLICY": 1.0, "OM_TP_LEASH_BEFORE_DAMAGE": 1.0}, seed=3)
    assert observe(seed=3) == fresh


@pytest.mark.parametrize("seed,swap", [(0, False), (1, True), (2, False)])
def test_null_control_every_setting_at_its_default_changes_nothing(library, seed, swap):
    """Defaults are read from the library, not typed in: the explicit set equals the unset fight, row and trace."""
    w = library.new_world(0)
    try:
        defaults = {n: library.get_param(w, library.param_id(n)) for n in DEFAULTS}
    finally:
        library.free_world(w)
    assert observe(defaults, seed, swap) == observe(None, seed, swap)
