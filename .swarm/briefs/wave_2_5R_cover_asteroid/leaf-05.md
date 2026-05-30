---
leaf_id: leaf-05
spec_file: docs/test_specs/cover_asteroid_los_spec.md
spec_lines: 162-166
test_file: simulation/test_asteroid_damage_gate.py
impl_file: simulation/damage.py
contract_imports:
  - tactical_map.TacticalMap
  - tactical_map.Asteroid
  - tactical_map.AsteroidField
  - fog_of_war.compute_visibility
do_not_edit:
  - simulation/test_asteroid_ai_peek.py
  - simulation/asteroid_integration_fixture.py
  - simulation/test_asteroid_integration.py
  - scenes/tactical/terrain_renderer.gd
  - autoload/era_theme_resolver.gd
  - tests/test_cover_render.gd
  - simulation/tactical_map.py
  - simulation/gradient_placer.py
  - simulation/fog_of_war.py
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
impl_line_budget: 60
test_assertion_budget: 12
wave: 3
---

## Task

Regression-only leaf. Damage visibility gate carried over from Wave 2.5 (`damage.py` already calls `compute_visibility()` and zero-damages if target not in attacker's visible set per spec line 49 + 162-166). Confirm: (a) no `(1.0 - cover)` term remains anywhere in `simulation/damage.py`; (b) under new per-asteroid visibility from L4, gate still produces 0 damage when target hidden and full damage when visible.

If a regex sweep finds `(1.0 - cover` still present, REMOVE that term (single-line edit allowed). If gate logic missing, add minimal check: at start of per-attacker target loop, if target not in `visibility_map.get(attacker_uid, set())`, skip damage application.

Tests (spec_lines 235-237):
- Tall asteroid blocks LOS → attacker fires at target → 0 damage applied (HP unchanged).
- No asteroid → attacker fires at target → damage applied (HP reduced).
- Regex assert: `re.search(r"\(1\.0?\s*[-−]\s*cover", open(damage.__file__).read())` returns None.
- Confirm `damage.resolve_damage` still callable with `(store, tactical_map, dt)` signature (don't change signature).

Use minimal store + tactical_map fixtures (build by hand; do NOT pull L7's fixture).

## Acceptance

Run `cd simulation && python3 -m pytest test_asteroid_damage_gate.py -v`. Confirm RED (or already GREEN if Wave 2.5 left gate intact — that's fine; just confirm regex sweep + L4 compatibility test pass). Implement in impl_file only if needed. Write final files to `.swarm/pending/leaf-05/` mirroring repo paths. Stop.

## Escalation triggers

Stop and report to the parent if:
- A type the test imports is not in contract_imports.
- The impl would need to create a new file.
- The impl would need to edit a file in do_not_edit.
- Two sibling assertions seem to require contradictory behavior.
- Impl approaches impl_line_budget with assertions still failing.

## Assumption log

Log inferences (current Wave 2.5 gate location in damage.py, `resolve_damage` signature, how visibility_map is supplied) to `.swarm/briefs/wave_2_5R_cover_asteroid/leaf-05.ASSUMPTIONS.md`.
