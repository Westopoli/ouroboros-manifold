# spec: LAB-REV2-L6 (docs/northstar/plans/2026-10-14-skill-lab-rev2-spec.md, the L6 row: fight.py)
"""fight.py registers a custom unit type's movement kind, and refuses a spawn the engine answers with unit id 0.

Contract these tests fix for scripts/skilllab/fight.py (through the production library, no fakes):
  unit_types[name]["movement"] == "walking" (a base form or a full-stats form) -> om_roster_set_movement_kind(type, 1);
  no "movement" key -> the engine default (flying, 0); the key never reaches om_roster_register_custom_unit's stats.
  engine.spawn returning 0 (a walker placed on ground it cannot walk) -> an error whose message says "lab defect", because
  a unit with id 0 is silently counted dead (measured 2026-10-14).
Seed 11 on a 12000 canvas: (2000, 2000) and (2100, 2000) are walkable ground on band 1; (3500, 4000) is not, nor is anything
within the replicate jitter (contract.SHIFT_MAX) of it."""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.skilllab import engine, fight  # noqa: E402
from scripts.skilllab.contract import Group, Setup, Terrain  # noqa: E402

FLYING, WALKING = 0, 1
WALKABLE, UNWALKABLE = (2000.0, 2000.0), (3500.0, 4000.0)
FOE = (2100.0, 2000.0)


class Spy(engine.Engine):
    """Reads each spawned type's movement kind just before the world is freed."""

    def __init__(self):
        super().__init__()
        self.types, self.kinds = set(), {}

    def spawn(self, w, type_id, side, x, y, layer):
        self.types.add(type_id)
        return super().spawn(w, type_id, side, x, y, layer)

    def free_world(self, w):
        for tid in self.types:
            self.kinds[tid] = self.movement_kind(w, tid)
        super().free_world(w)


def _full_stats():
    lib = engine.Engine()
    w = lib.new_world(0)
    try:
        tid = lib.type_id("Vanguard")
        return {**lib.type_stats(w, tid), "role": "Vanguard", "ability_id": 0}
    finally:
        lib.free_world(w)


def _setup(unit_types, at=WALKABLE, unit="Walker", foe="Vanguard"):
    groups = (Group(side=0, unit=unit, count=1, formation="points", x=at[0], y=at[1], facing_deg=0.0, layer=0, order="idle",
                    params={"points": [at]}),
              Group(side=1, unit=foe, count=1, formation="points", x=FOE[0], y=FOE[1], facing_deg=180.0, layer=0, order="idle",
                    params={"points": [FOE]}))
    return Setup(groups=groups, unit_types=unit_types, max_ticks=1, terrain=Terrain(canvas=(12000.0, 12000.0), field_seed=11))


def _kind_of_walker(unit_types):
    spy = Spy()
    fight.fight(_setup(unit_types), 1, False, engine=spy)
    return spy.kinds[fight.FIRST_CUSTOM_TYPE_ID]


def test_a_custom_type_in_base_form_with_movement_walking_reads_kind_1():
    assert _kind_of_walker({"Walker": {"base": "Vanguard", "scale": {}, "set": {}, "movement": "walking"}}) == WALKING


def test_a_custom_type_in_full_stats_form_with_movement_walking_reads_kind_1():
    assert _kind_of_walker({"Walker": {**_full_stats(), "movement": "walking"}}) == WALKING


def test_a_custom_type_without_movement_stays_flying():
    """Positive control for the two tests above: the same types without the key read 0."""
    assert _kind_of_walker({"Walker": {"base": "Vanguard", "scale": {}, "set": {}}}) == FLYING
    assert _kind_of_walker({"Walker": _full_stats()}) == FLYING


def test_a_built_in_type_stays_flying():
    spy = Spy()
    fight.fight(_setup({}, unit="Vanguard"), 1, False, engine=spy)
    assert set(spy.kinds.values()) == {FLYING}


def test_a_walker_placed_on_unwalkable_seed_11_ground_raises_the_lab_defect_error():
    types = {"Walker": {"base": "Vanguard", "scale": {}, "set": {}, "movement": "walking"}}
    with pytest.raises(Exception, match="lab defect") as err:
        fight.fight(_setup(types, at=UNWALKABLE), 1, False, engine=engine.Engine())
    assert "id 0" in str(err.value)


def test_positive_control_the_same_walker_on_walkable_ground_does_not_raise():
    types = {"Walker": {"base": "Vanguard", "scale": {}, "set": {}, "movement": "walking"}}
    r = fight.fight(_setup(types, at=WALKABLE), 1, False, engine=engine.Engine())
    assert r.heads == (1, 1)
