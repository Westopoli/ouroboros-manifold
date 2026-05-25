---
leaf_id: leaf-01
spec_file: docs/test_specs/cover_asteroid_los_spec.md
spec_lines: 79-81
test_file: simulation/test_asteroid_bible_lang.py
impl_file: docs/bible/bible_world.md
impl_files:
  - docs/bible/bible_combat.md
contract_imports:
do_not_edit:
  - simulation/tactical_map.py
  - simulation/test_asteroid.py
  - simulation/fog_of_war.py
  - simulation/damage.py
  - simulation/gradient_placer.py
  - simulation/snapshot_serializer.py
  - simulation/config.py
  - simulation/tactical_engine.py
  - simulation/asteroid_integration_fixture.py
  - scenes/tactical/terrain_renderer.gd
  - autoload/era_theme_resolver.gd
  - tests/test_cover_render.gd
  - docs/bible/game_bible.md
  - docs/bible/bible_simulation.md
  - docs/bible/bible_missions.md
  - docs/bible/bible_chronicle.md
  - docs/bible/bible_antagonist.md
  - docs/bible/bible_monetization.md
  - docs/bible/bible_ai_pipeline.md
  - docs/architecture.md
  - docs/test_specs/cover_asteroid_los_spec.md
  - docs/test_specs/cover_los_rework_spec.md
  - simulation/test_asteroid_umbrella.py
  - simulation/test_cover_umbrella.py
impl_line_budget: 80
test_assertion_budget: 12
---

## Task

Rewrite cover language in `docs/bible/bible_world.md` line 144 area and `docs/bible/bible_combat.md` lines 419-441 + 529 per spec_lines 79-81. New language: cover = cluster of asteroid LOS-blockers; per-asteroid 3D LOS; continuous size → layer block (height ≥ LAYER_Z_FLOORS[i] blocks layer i); non-destructible Phase 1. Remove polygon model phrasing (Wave 2.5 superseded). Remove cover_density damage-multiplier phrasing. Keep bible authoritative tone.

Test file is a guard: greps both bible files for required tokens (asteroid, LOS / line of sight) and forbidden tokens (cover_density damage formula, "polygon LOS-blocker" Wave-2.5 language).

## Acceptance

Run `cd simulation && python3 -m pytest test_asteroid_bible_lang.py -v`. Confirm RED. Edit both bible files only. Confirm GREEN. Write final test_file and impl_files to `.swarm/pending/leaf-01/` mirroring repo paths. Stop.

## Escalation triggers

Stop and report to the parent if:
- A type the test imports is not in contract_imports.
- The impl would need to create a new file.
- The impl would need to edit a file in do_not_edit.
- Two sibling assertions seem to require contradictory behavior.
- Impl approaches impl_line_budget with assertions still failing.

## Assumption log

If you inferred anything not in the brief, log it to `.swarm/briefs/wave_2_5R_cover_asteroid/leaf-01.ASSUMPTIONS.md` before finishing.
