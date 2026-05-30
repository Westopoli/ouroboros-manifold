---
leaf_id: leaf-07
spec_file: docs/test_specs/cover_los_rework_spec.md
spec_lines: 154-156
test_file: simulation/test_cover_integration.py
impl_file: simulation/cover_integration_fixture.py
contract_imports:
  - TacticalMap
  - CoverPolygon
  - compute_visibility
  - build_cover_apex_scenario
do_not_edit:
  - docs/bible/game_bible.md
  - docs/bible/bible_simulation.md
  - docs/bible/bible_missions.md
  - docs/bible/bible_chronicle.md
  - docs/bible/bible_antagonist.md
  - docs/bible/bible_monetization.md
  - docs/bible/bible_ai_pipeline.md
  - docs/test_specs/cover_los_rework_spec.md
  - docs/phase1_ship_plan.md
  - docs/priority_queue.md
  - simulation/test_cover_umbrella.py
  - simulation/tactical_map.py
  - simulation/gradient_placer.py
  - simulation/map_generator.py
  - simulation/fog_of_war.py
  - simulation/damage.py
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
  - simulation/test_cover_polygon.py
  - simulation/test_cover_polygon_placement.py
  - simulation/test_cover_visibility.py
  - simulation/test_cover_damage_gate.py
  - simulation/test_cover_ai_peek.py
impl_line_budget: 150
test_assertion_budget: 16
wave: 4
---

## Task

Build the apex integration scenario for cover-LOS rework per spec lines 154-156, and surface a balance-rebaseline list (read-only — do NOT edit balance tests).

Part 1 — fixture (`simulation/cover_integration_fixture.py`). Export a single function `build_cover_apex_scenario() -> tuple[TacticalMap, Store, list[UnitId], list[UnitId]]` (or the smallest equivalent given existing project conventions for unit stores). The fixture builds:
- A `TacticalMap` with width=1000, height=1000, exactly ONE `CoverPolygon` (id=1) centered at (500, 500), 12-vertex circle radius 80.
- Faction A (attackers): 2 units placed at (200, 500) and (800, 500), outside the polygon.
- Faction B (defender): 1 unit placed at (500, 500), inside the polygon.

No additional cover, no obstacles, no fog interference beyond engine defaults.

Part 2 — integration test (`simulation/test_cover_integration.py`). Using the fixture, assert:
1. `tm.is_in_cover(500, 500)` True; `tm.is_in_cover(200, 500)` False; `tm.is_in_cover(800, 500)` False.
2. `compute_visibility` for either attacker → defender NOT in visible set (cover occluder, different polygons / one in none).
3. `compute_visibility` for the defender → attackers MAY be in visible set (defender's polygon vs. attackers' no-polygon means attackers are visible to defender — they are not in cover; spec lines 22-25: "A is not in any cover polygon, OR ...").
4. Apply attack from attacker 1 at defender → damage applied = 0 (L5 visibility gate).
5. Apply attack from defender at attacker 1 → damage applied > 0 IF defender has combat LOS via existing navmesh check (one-sided fire is intentional per spec line 31-32).
6. Move defender to (700, 500) — outside polygon. Re-run `compute_visibility`. Defender now in attackers' visible set. Apply attack from attacker 1 at defender → damage applied > 0.

Part 3 — balance rebaseline list. After the integration test passes, scan `simulation/test_*.py` files for combat outcome assertions that may depend on the now-removed `(1.0 - cover)` multiplier. Generate `.swarm/briefs/wave_2_5_cover_los/leaf-07.REBASELINE_LIST.md` enumerating: file path, test function name, one-line reason it's in scope. Do NOT edit any of the listed test files — list is for Westley's batch sign-off per `feedback_no_test_modification.md`.

Confirm RED on test_cover_integration.py, implement fixture, confirm GREEN.

## Acceptance

Run `cd simulation && python3 -m pytest test_cover_integration.py -v`. Confirm RED before impl. Implement in `cover_integration_fixture.py` only. Confirm GREEN. Then run the full umbrella: `cd simulation && python3 -m pytest test_cover_umbrella.py -v` — every test should be green (no remaining `pytest.skip`). Commit the two files + REBASELINE_LIST.md. Stop.

## Escalation triggers

Stop and report to the parent if:
- The fixture cannot build a 2-attacker / 1-defender scenario using existing public APIs (requires upstream plumbing).
- The defender-fires-at-attacker assertion (test 5) requires modifying the existing `has_combat_los` semantics.
- The umbrella `test_umbrella_f_integration_cover_blocks_fire` is still a `pytest.skip` stub and cannot be made green without parent removing the skip.
- Rebaseline list grows beyond ~20 files — surface for Westley triage before writing the full list.
- Impl approaches `impl_line_budget` with assertions still failing.

## Assumption log

If at any point during your run you had to infer something the brief did not specify (unit type, faction id constants, attack-application call shape, anything), write it to `.swarm/briefs/wave_2_5_cover_los/leaf-07.ASSUMPTIONS.md` before you commit. Format:

```markdown
## Assumptions made during leaf-07

- **<thing>**: <inferred value> — source: <which spec line / contract symbol / file you looked at, or "no source — pure guess">
```
