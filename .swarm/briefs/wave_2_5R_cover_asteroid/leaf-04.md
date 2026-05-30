---
leaf_id: leaf-04
spec_file: docs/test_specs/cover_asteroid_los_spec.md
spec_lines: 152-166
test_file: simulation/test_asteroid_visibility.py
impl_file: simulation/fog_of_war.py
contract_imports:
  - tactical_map.TacticalMap
  - tactical_map.Asteroid
  - tactical_map.AsteroidField
  - config.LAYER_Z_FLOORS
  - config.LAYER_Z_CEILINGS
  - fog_of_war.compute_visibility
do_not_edit:
  - simulation/test_asteroid_placer.py
  - simulation/test_asteroid_manifest.py
  - docs/architecture.md
  - simulation/tactical_map.py
  - simulation/gradient_placer.py
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
impl_line_budget: 140
test_assertion_budget: 20
wave: 2
---

## Task

Replace polygon symmetric-blind pass in `simulation/fog_of_war.py:compute_visibility` with per-asteroid 3D raycast per spec_lines 152-166. For each (observer O, target T) pair that passes existing distance + layer + pulse + sensor cone + same-faction skip checks:
1. `oz = (LAYER_Z_FLOORS[O.layer] + LAYER_Z_CEILINGS[O.layer]) / 2.0`
2. `tz = (LAYER_Z_FLOORS[T.layer] + LAYER_Z_CEILINGS[T.layer]) / 2.0`
3. If `tactical_map.asteroid_blocks_los(O.x, O.y, oz, T.x, T.y, tz)`: skip (T NOT added to O's visible set)
4. Else: add T to O's visible set

Retire any cover_polygon_containing / same-polygon checks from Wave 2.5 (parent will sweep test_cover_* files separately). Keep same-faction short-circuit at original site (do not change pre-Wave-2.5 convention per spec line 273 gotcha 6).

Tests (spec_lines 228-233):
- Observer (500,500,layer 0) + target (50,50,layer 0), no asteroids → target IN visible set.
- Same setup, single huge asteroid (height 200) at midpoint → target NOT in visible set.
- Same, tiny asteroid (height 20) at midpoint, observer + target both layer 1 (z ~65) → target IN visible set (ray over tiny).
- Tall asteroid (height 200) at midpoint, layer 2 observer + target (z ~200) → target NOT in visible set.
- Ray skirting edge (just outside radius_xy) → target IN visible set.

Use minimal store + tactical_map fixtures (build by hand; do NOT pull L7's fixture).

## Acceptance

Run `cd simulation && python3 -m pytest test_asteroid_visibility.py -v`. Confirm RED. Implement in impl_file only. Confirm GREEN. Write final files to `.swarm/pending/leaf-04/` mirroring repo paths. Stop.

## Escalation triggers

Stop and report to the parent if:
- A type the test imports is not in contract_imports.
- The impl would need to create a new file.
- The impl would need to edit a file in do_not_edit.
- Two sibling assertions seem to require contradictory behavior.
- Impl approaches impl_line_budget with assertions still failing.

## Assumption log

Log inferences (existing fog_of_war check ordering, store field names for x/y/layer/uid, how observer iteration occurs) to `.swarm/briefs/wave_2_5R_cover_asteroid/leaf-04.ASSUMPTIONS.md`.
