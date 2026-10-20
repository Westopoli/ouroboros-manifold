# spec: docs/northstar/plans/2026-10-19-skill-lab-rev3-plan.md (requirement R8, test T3; defect D3); ledger FINDING-lab-d3; piece LAB-REV3-A
"""LAB-REV3-A, T3 (R8, D3): no copied types. The library keys the Warden aura and the Bastion damage cap on the BUILT-IN type ids
(csrc/unit.c, om_grid_kind and om_resolve_hit_multiplier), so a type the lab copies into a custom id (100 and up) loses both. Fast half:
`fight._register_types` against the real library, no fight. The behaviour half (a Warden mirror and the Bastion cap) is
tests/skilllab/integration/test_rev3_a_types_real.py.

BUILDER CONTRACT (the only behaviour pinned):
  - `fight._register_types(engine, w, setup)` returns, for a unit name whose `Setup.unit_types` entry names itself as its base
    (`{"base": N}` with N == the name) and carries no `scale` and no `set` (exactly what `plays_space._types` writes, plus "reach"),
    the BUILT-IN id `engine.type_id(N)` and its attack range, registers no custom type, and, when the entry has "reach", sets that reach
    on the built-in id (`engine.set_reach(w, builtin_id, up, down)`; om_roster_set_reach works on built-in ids).
  - An entry whose name differs from its base, or with a `scale`/`set`, or with full stats, is a real custom type and keeps the
    custom id from 100 (tests/skilllab/test_reach_binding.py and integration/test_reach_real.py rely on it, unchanged).
  - The reach is per world: a new world's built-in types are back at the library default (0, 0).
  - `plays_space._types` may keep returning the entries it returns; where the copy is removed (there or in `_register_types`) is the
    builder's, the observable is the id `_register_types` gives."""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.skilllab import fight as fight_mod, plays_space  # noqa: E402
from scripts.skilllab.contract import Group, Setup  # noqa: E402
from scripts.skilllab.engine import Engine  # noqa: E402

LAB_TYPES = ("Raider", "Interceptor", "Bombard", "Bastion")      # the four types plays_space._types gives a reach entry


def setup_of(unit_types, *units):
    g = lambda side, unit: Group(side=side, unit=unit, count=1, formation="blob", x=-300.0 if side == 0 else 300.0, y=0.0,
                                 facing_deg=0.0, layer=0, order="attack_move", params={"radius": 20.0})
    return Setup(groups=tuple(g(i % 2, u) for i, u in enumerate(units)), unit_types=unit_types)


@pytest.fixture
def engine():
    return Engine()


@pytest.mark.parametrize("name", LAB_TYPES)
def test_t3_a_lab_type_with_a_reach_is_registered_on_its_builtin_id(engine, name):
    """T3 (D3): `plays_space._types(name)` entries come back as the built-in id, not a copy at 100. Red today: the id is 100."""
    w = engine.new_world(0)
    try:
        types = fight_mod._register_types(engine, w, setup_of(plays_space._types(name), name, "Vanguard"))
    finally:
        engine.free_world(w)
    assert types[name][0] == engine.type_id(name)


@pytest.mark.parametrize("name", LAB_TYPES)
def test_t3_the_reach_is_set_on_the_builtin_id(engine, name):
    """T3 (D3): the bible reach of the type reads back from its built-in id. Red today: the built-in id stays (0, 0)."""
    w = engine.new_world(0)
    try:
        fight_mod._register_types(engine, w, setup_of(plays_space._types(name), name, "Vanguard"))
        got = engine.profile_reach(w, engine.type_id(name))
    finally:
        engine.free_world(w)
    assert got == plays_space._REACH[name]


def test_t3_the_warden_gets_a_builtin_id_too_with_the_reach_it_is_given(engine):
    """T3 (D3): the Warden (aura) is the type the copy hurt first; a reach entry on it keeps id 3. Red today: id 100."""
    w = engine.new_world(0)
    try:
        types = fight_mod._register_types(engine, w, setup_of({"Warden": {"base": "Warden", "reach": (1, 0)}}, "Warden", "Vanguard"))
        got = engine.profile_reach(w, engine.type_id("Warden"))
    finally:
        engine.free_world(w)
    assert (types["Warden"][0], got) == (engine.type_id("Warden"), (1, 0))


def test_t3_no_custom_type_is_registered_for_a_play_with_only_builtin_names(engine):
    """T3 (D3): after registering Raider, Interceptor, Bombard and Bastion no custom id exists. Red today: 100..103 exist
    (om_unit_profile_reach(100) is refused only when the id is unregistered)."""
    w = engine.new_world(0)
    try:
        fight_mod._register_types(engine, w, setup_of(plays_space._types(*LAB_TYPES), *LAB_TYPES))
        with pytest.raises(ValueError):
            engine.profile_reach(w, fight_mod.FIRST_CUSTOM_TYPE_ID)
    finally:
        engine.free_world(w)


def test_t3_the_reach_does_not_leak_into_the_next_world(engine):
    """Isolation (positive control, green on the lab tip): the reach set in one world is gone in the next, so setting it on a
    built-in id cannot be process-global."""
    w = engine.new_world(0)
    try:
        fight_mod._register_types(engine, w, setup_of(plays_space._types("Bombard"), "Bombard", "Vanguard"))
    finally:
        engine.free_world(w)
    w = engine.new_world(0)
    try:
        assert engine.profile_reach(w, engine.type_id("Bombard")) == (0, 0)
    finally:
        engine.free_world(w)


def test_a_genuinely_custom_entry_keeps_its_custom_id(engine):
    """Positive control (green on the lab tip, must stay green): a differently named entry, and a scaled one, are real custom types
    from 100 in order of first use, and a plain built-in name keeps its id."""
    w = engine.new_world(0)
    try:
        types = fight_mod._register_types(engine, w, setup_of(
            {"Tall": {"base": "Vanguard", "scale": {}, "set": {}, "reach": (0, 2)},
             "Far": {"base": "Vanguard", "scale": {"attack_range": 2.0}}}, "Tall", "Far", "Raider"))
    finally:
        engine.free_world(w)
    assert (types["Tall"][0], types["Far"][0], types["Raider"][0]) == (100, 101, engine.type_id("Raider"))
