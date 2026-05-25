---
leaf_id: leaf-07
spec_file: docs/test_specs/cover_asteroid_los_spec.md
spec_lines: 242-244
test_file: simulation/test_asteroid_integration.py
impl_file: simulation/asteroid_integration_fixture.py
contract_imports:
  - tactical_map.TacticalMap
  - tactical_map.Asteroid
  - tactical_map.AsteroidField
  - fog_of_war.compute_visibility
  - gradient_placer.place_asteroid_fields
do_not_edit:
  - simulation/test_asteroid_damage_gate.py
  - simulation/test_asteroid_ai_peek.py
  - scenes/tactical/terrain_renderer.gd
  - autoload/era_theme_resolver.gd
  - tests/test_cover_render.gd
  - simulation/tactical_map.py
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
wave: 3
---

## Task

Build `simulation/asteroid_integration_fixture.py` exporting `build_cover_asteroid_apex_scenario() -> (TacticalMap, store, attackers_list, defenders_list)` per spec_lines 242-244. Scenario: TacticalMap 1000×1000. One asteroid cluster at (500, 500) radius 80 with ~25 asteroids skewed huge (call `gradient_placer.place_asteroid_fields` with a synthetic spine node OR build asteroids by hand so cluster is dense + opaque on line attacker→defender). 2 Raider attackers at (50, 500) and (50, 600); 1 Warden defender at (500, 500) hidden behind the cluster. Return store + uid lists.

Write `test_asteroid_integration.py` with apex assertions (spec_lines 242-244):
- Defender NOT in attacker visibility set (per-asteroid LOS blocked).
- Attacker fires at defender → 0 damage (gate intact under new visibility).
- Defender moves to (900, 500) — clear ground — defender now IN at least one attacker's visibility set; subsequent damage tick reduces defender HP.
- Defender fires from cover at attackers (set defender's auto_engage_target to one attacker) — defender remains hidden from attackers post-fire (no fire-reveal per spec line 49 — defender's own visibility set computed separately and is empty for attackers).

## Acceptance

Run `cd simulation && python3 -m pytest test_asteroid_integration.py -v`. Confirm RED. Implement fixture in impl_file only. Confirm GREEN. Write final files to `.swarm/pending/leaf-07/` mirroring repo paths. Stop.

## Escalation triggers

Stop and report to the parent if:
- A type the test imports is not in contract_imports.
- The impl would need to create a new file (the fixture file IS impl_file; OK to create).
- The impl would need to edit a file in do_not_edit.
- Two sibling assertions seem to require contradictory behavior.
- Impl approaches impl_line_budget with assertions still failing.

## Assumption log

Log inferences (store API for unit creation, Raider/Warden archetype constructors, FIELD_HP / FIELD_X / FIELD_Y constants source, how auto_engage_target is set) to `.swarm/briefs/wave_2_5R_cover_asteroid/leaf-07.ASSUMPTIONS.md`.
