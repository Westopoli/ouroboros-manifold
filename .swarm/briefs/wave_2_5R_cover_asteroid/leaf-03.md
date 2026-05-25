---
leaf_id: leaf-03
spec_file: docs/test_specs/cover_asteroid_los_spec.md
spec_lines: 191-203
test_file: simulation/test_asteroid_placer.py
impl_file: simulation/gradient_placer.py
impl_files:
  - simulation/config.py
contract_imports:
  - tactical_map.Asteroid
  - tactical_map.AsteroidField
  - config.ASTEROID_SPATIAL_HASH_CELL
  - config.LAYER_Z_FLOORS
  - config.LAYER_Z_CEILINGS
  - config.ASTEROID_BASE_DENSITY
  - config.ASTEROID_SCALE_DISTRIBUTION
  - config.ASTEROID_SCALE_RANGES
  - config.ASTEROID_HEIGHT_RATIO_RANGE
  - gradient_placer.place_asteroid_fields
do_not_edit:
  - simulation/test_asteroid_visibility.py
  - simulation/test_asteroid_manifest.py
  - docs/architecture.md
  - simulation/tactical_map.py
  - simulation/fog_of_war.py
  - simulation/damage.py
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
  - docs/test_specs/cover_los_rework_spec.md
  - simulation/test_asteroid_umbrella.py
  - simulation/test_cover_umbrella.py
impl_line_budget: 180
test_assertion_budget: 20
wave: 2
---

## Task

Add asteroid-related constants to `simulation/config.py` (additive only — do not edit pre-existing constants) per spec_lines 64-71:
- `ASTEROID_SPATIAL_HASH_CELL = 100.0`
- `LAYER_Z_FLOORS = [0.0, 30.0, 100.0]`
- `LAYER_Z_CEILINGS = [30.0, 100.0, 300.0]`
- `ASTEROID_BASE_DENSITY = 0.00090`
- `ASTEROID_SCALE_DISTRIBUTION = {"tiny": 0.60, "small": 0.25, "medium": 0.10, "huge": 0.05}`
- `ASTEROID_SCALE_RANGES = {"tiny": (1.0, 3.0), "small": (3.0, 8.0), "medium": (8.0, 20.0), "huge": (20.0, 80.0)}`
- `ASTEROID_HEIGHT_RATIO_RANGE = (0.5, 2.0)`

Add `place_asteroid_fields(inst) -> AsteroidField` to `simulation/gradient_placer.py` per spec_lines 191-203. For each spine_node of type in {chokepoint, staging, objective, hazard_zone_anchor, flank_route} (use pre-existing cover-emitting node-type list — reuse same set the polygon work used; if ambiguous, hardcode this set and log assumption). Per node: compute cluster radius from pre-existing `GRADIENT_<NODE>_COVER_RADIUS` constants (chokepoint → `GRADIENT_CHOKEPOINT_COVER_RADIUS`, etc.; if any constant absent, use 50.0 and log). Count = `pi * radius**2 * ASTEROID_BASE_DENSITY`. Sample asteroids per spec: scale_class weighted by `ASTEROID_SCALE_DISTRIBUTION`; `radius_xy = uniform(*ASTEROID_SCALE_RANGES[class])`; `height = radius_xy * uniform(*ASTEROID_HEIGHT_RATIO_RANGE)`; position = rejection sample uniform in disk of cluster radius around node position. Deterministic seed `random.Random(cluster_id * 1009 + getattr(inst, "map_seed", 0))`. Return `AsteroidField(all_asteroids)`.

Tests (spec_lines 222-226): single-chokepoint produces N asteroids within ±10% of density formula; scale-class proportions within ±10% (loose for stochasticity); all positions within radius; 5-node-type test → 5 clusters with own counts; vantage-only spine → empty field; deterministic same-seed re-run identical.

## Acceptance

Run `cd simulation && python3 -m pytest test_asteroid_placer.py -v`. Confirm RED. Implement in impl_files only. Confirm GREEN. Write final files to `.swarm/pending/leaf-03/` mirroring repo paths. Stop.

## Escalation triggers

Stop and report to the parent if:
- A type the test imports is not in contract_imports.
- The impl would need to create a new file.
- The impl would need to edit a file in do_not_edit.
- Two sibling assertions seem to require contradictory behavior.
- Impl approaches impl_line_budget with assertions still failing.

## Assumption log

Log inferences (cover-emitting node-type set, GRADIENT_*_COVER_RADIUS lookups, seed source if `inst.map_seed` absent) to `.swarm/briefs/wave_2_5R_cover_asteroid/leaf-03.ASSUMPTIONS.md`.
