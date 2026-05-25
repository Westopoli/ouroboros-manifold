---
leaf_id: leaf-02
spec_file: docs/test_specs/cover_asteroid_los_spec.md
spec_lines: 96-150
test_file: simulation/test_asteroid.py
impl_file: simulation/tactical_map.py
contract_imports:
  - tactical_map.Asteroid
  - tactical_map.AsteroidField
  - tactical_map.TacticalMap
  - config.ASTEROID_SPATIAL_HASH_CELL
do_not_edit:
  - docs/bible/bible_world.md
  - docs/bible/bible_combat.md
  - simulation/test_asteroid_bible_lang.py
  - simulation/gradient_placer.py
  - simulation/fog_of_war.py
  - simulation/damage.py
  - simulation/snapshot_serializer.py
  - simulation/config.py
  - simulation/tactical_engine.py
  - simulation/tick.py
  - simulation/drift.py
  - simulation/faction.py
  - simulation/region.py
  - simulation/events.py
  - simulation/event_engine.py
  - simulation/intent_resolver.py
  - simulation/border_friction.py
  - simulation/technology.py
  - simulation/diplomacy.py
  - simulation/world.py
  - simulation/templates.py
  - simulation/theme_scifi.py
  - scenes/**
  - autoload/**
  - docs/bible/**
  - docs/test_specs/cover_asteroid_los_spec.md
  - docs/test_specs/cover_los_rework_spec.md
  - simulation/test_asteroid_umbrella.py
  - simulation/test_cover_umbrella.py
impl_line_budget: 180
test_assertion_budget: 20
---

## Task

Add `Asteroid` class + `AsteroidField` class + `TacticalMap.asteroid_blocks_los(ox, oy, oz, tx, ty, tz) -> bool` to `simulation/tactical_map.py` per spec_lines 96-150. `Asteroid` has slots `(asteroid_id, cluster_id, x, y, radius_xy, height, scale_class)`. `AsteroidField` builds a SpatialHash on construction (cell size = `config.ASTEROID_SPATIAL_HASH_CELL`, value 100.0; if config lacks the constant, hardcode 100.0 and note in assumption log) and exposes `query_cells(bbox)` returning candidate asteroid IDs. `asteroid_blocks_los` runs 2D ray-circle test then z-range check per spec_lines 170-178; returns True iff any asteroid cylinder along ray (within asteroid vertical extent [0, height]) is hit.

`TacticalMap.__init__` initializes `self.asteroid_field = AsteroidField([])` so the attribute exists pre-placement (L3 overwrites). Retire `cover_polygons` / `is_in_cover` / `cover_polygon_containing` (Wave 2.5 polygon work in tree gets removed by this leaf as part of replacement). SpatialHash can be a tiny private class inside tactical_map.py (dict[(int,int)] -> list[int]).

Test cases (spec_lines 217-220): Asteroid construction round-trip; AsteroidField spatial hash insert + query for 100wu bucket; ray-cylinder math axis-aligned hit dead-center; miss by 1wu outside radius; tall asteroid (height 200) blocks ray at z=50; short asteroid (height 20) does NOT block ray at z=65; ray inside cylinder vertical range entirely → blocked.

## Acceptance

Run `cd simulation && python3 -m pytest test_asteroid.py -v`. Confirm RED. Implement in impl_file only. Confirm GREEN. Write final files to `.swarm/pending/leaf-02/` mirroring repo paths. Stop.

## Escalation triggers

Stop and report to the parent if:
- A type the test imports is not in contract_imports.
- The impl would need to create a new file.
- The impl would need to edit a file in do_not_edit.
- Two sibling assertions seem to require contradictory behavior.
- Impl approaches impl_line_budget with assertions still failing.

## Assumption log

If you inferred anything not in the brief (especially: SpatialHash API shape, how `ASTEROID_SPATIAL_HASH_CELL` is obtained pre-L3, edge-case ray when oz==tz or |T-O|==0), log it to `.swarm/briefs/wave_2_5R_cover_asteroid/leaf-02.ASSUMPTIONS.md` before finishing.
