---
leaf_id: leaf-08
spec_file: docs/test_specs/cover_asteroid_los_spec.md
spec_lines: 205-213
test_file: simulation/test_asteroid_manifest.py
impl_file: simulation/snapshot_serializer.py
impl_files:
  - docs/architecture.md
contract_imports:
  - tactical_map.TacticalMap
  - tactical_map.Asteroid
  - tactical_map.AsteroidField
  - snapshot_serializer.serialize_cover_asteroids
do_not_edit:
  - simulation/test_asteroid_placer.py
  - simulation/test_asteroid_visibility.py
  - simulation/tactical_map.py
  - simulation/gradient_placer.py
  - simulation/fog_of_war.py
  - simulation/damage.py
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
impl_line_budget: 80
test_assertion_budget: 12
wave: 2
---

## Task

Add `serialize_cover_asteroids(tactical_map) -> list[dict]` to `simulation/snapshot_serializer.py` per spec_lines 205-213. Return list of `{"id": a.asteroid_id, "cluster": a.cluster_id, "x": a.x, "y": a.y, "r": a.radius_xy, "h": a.height, "class": a.scale_class}` for each asteroid in `tactical_map.asteroid_field.asteroids`. Static at map load — DO NOT add to per-tick delta. If `snapshot_serializer` has a `build_map_manifest` (or similar) function, add `"cover_asteroids": serialize_cover_asteroids(tm)` to its returned dict at the same site. If unsure where manifest is built, escalate.

Update `docs/architecture.md` per CLAUDE.md tick-delta-shape rule (spec line 270 gotcha 3): add note describing `cover_asteroids` field, shape, and "static at map load — not in tick delta" semantics. Do this BEFORE impl per CLAUDE.md rule.

Tests (spec_lines 246-250):
- TacticalMap with one cluster (use L3's `place_asteroid_fields` after L3 lands, or hand-build AsteroidField with 3 asteroids) → `serialize_cover_asteroids(tm)` returns 3-item list.
- Each entry has keys `{id, cluster, x, y, r, h, class}`.
- Round-trip JSON dump+load → counts + first-entry fields preserved.

## Acceptance

Run `cd simulation && python3 -m pytest test_asteroid_manifest.py -v`. Confirm RED. Update docs/architecture.md first, then implement serializer in impl_file. Confirm GREEN. Write final files to `.swarm/pending/leaf-08/` mirroring repo paths. Stop.

## Escalation triggers

Stop and report to the parent if:
- A type the test imports is not in contract_imports.
- The impl would need to create a new file.
- The impl would need to edit a file in do_not_edit.
- Manifest builder site unclear — escalate before editing.
- Two sibling assertions seem to require contradictory behavior.
- Impl approaches impl_line_budget with assertions still failing.

## Assumption log

Log inferences (manifest builder function name + site, whether AsteroidField is hand-built vs L3-derived in test, JSON encoder used) to `.swarm/briefs/wave_2_5R_cover_asteroid/leaf-08.ASSUMPTIONS.md`.
