---
leaf_id: leaf-10
spec_file: docs/test_specs/cover_asteroid_movement_spec.md
spec_lines: 22-44
test_file: simulation/test_asteroid_movement.py
impl_file: simulation/movement.py
impl_files:
  - simulation/config.py
contract_imports:
  - tactical_map.TacticalMap
  - tactical_map.Asteroid
  - tactical_map.AsteroidField
  - movement.Navmesh
do_not_edit:
  - simulation/damage.py
  - simulation/test_asteroid_ai_los_gate.py
  - simulation/test_asteroid_damage_and_targeting_gate.py
  - simulation/tactical_map.py
  - simulation/fog_of_war.py
  - simulation/gradient_placer.py
  - simulation/snapshot_serializer.py
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
  - docs/test_specs/cover_asteroid_movement_spec.md
  - docs/test_specs/cover_los_rework_spec.md
  - simulation/test_asteroid_umbrella.py
  - simulation/test_cover_umbrella.py
impl_line_budget: 60
test_assertion_budget: 14
wave: 4
---

## Task

Add navmesh asteroid rasterization per spec lines 22-44. Two file edits:

1. `simulation/config.py`: add module-level constant `ASTEROID_MOVEMENT_BLOCK_RADIUS = 8.0` (spec line 24).

2. `simulation/movement.py` `Navmesh.from_tactical_map`: after existing gradient-obstacle pass, append new pass that iterates `tmap.asteroid_field.asteroids` (if `tmap.asteroid_field is not None`), and for each asteroid with `radius_xy >= ASTEROID_MOVEMENT_BLOCK_RADIUS`, mark every navmesh cell whose center lies within `(asteroid.radius_xy + cell_size / 2)` of `(asteroid.x, asteroid.y)` as unwalkable (spec lines 38-42). Conservative rasterization per spec line 42. Iteration order = `asteroid_field.asteroids` index order (spec line 55).

Tests (write RED first):
- Huge asteroid (radius_xy=50, scale_class="huge") at (500,500) → `nm.cell(500.0, 500.0)` returns (r,c) with `nm.is_walkable(r,c) is False`.
- Medium asteroid (radius_xy=10, scale_class="medium") at (500,500) → cell at center unwalkable.
- Small asteroid (radius_xy=5, scale_class="small") at (500,500) → cell at center walkable (below R_BLOCK).
- Tiny asteroid (radius_xy=2, scale_class="tiny") at (500,500) → cell at center walkable.
- `tmap.asteroid_field is None` (legacy maps) → no AttributeError; navmesh builds normally.
- Determinism: build navmesh twice from identical TacticalMap → identical walkable grids.
- Conservative-ring sanity: cell at distance `(R + cell_size/2 + epsilon)` from huge asteroid center stays walkable.

Use minimal `TacticalMap(width=1000, height=1000, gradient_sources=[], spine_nodes=[])` + hand-built `AsteroidField` fixtures. Do NOT import L7 fixture or any sibling test helper.

## Acceptance

Run `cd simulation && python3 -m pytest test_asteroid_movement.py -v`. Confirm RED. Implement in impl_files only. Confirm GREEN. Write final `test_file` + both `impl_files` to `.swarm/pending/leaf-10/` mirroring repo paths (e.g. `simulation/config.py` → `.swarm/pending/leaf-10/simulation/config.py`). Stop.

## Escalation triggers

Stop and report to the parent if:
- A type the test imports is not in contract_imports.
- The impl would need to create a new file.
- The impl would need to edit a file in do_not_edit.
- `Navmesh.from_tactical_map` signature change required to land impl.
- Two sibling assertions seem to require contradictory behavior.
- Impl approaches impl_line_budget with assertions still failing.

## Assumption log

Log inferences (cell-size accessor name on Navmesh, asteroid_field attribute access pattern, cell-center coordinate math, any conservative-ring boundary epsilon) to `.swarm/briefs/wave_2_5R_cover_asteroid/leaf-10.ASSUMPTIONS.md`.
