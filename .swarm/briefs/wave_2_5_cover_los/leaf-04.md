---
leaf_id: leaf-04
spec_file: docs/test_specs/cover_los_rework_spec.md
spec_lines: 89-97
test_file: simulation/test_cover_visibility.py
impl_file: simulation/fog_of_war.py
contract_imports:
  - TacticalMap
  - is_in_cover
  - cover_polygon_containing
  - compute_visibility
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
  - simulation/test_cover_damage_gate.py
  - simulation/test_cover_ai_peek.py
  - simulation/test_cover_integration.py
impl_line_budget: 120
test_assertion_budget: 16
wave: 2
---

## Task

Add a cover-occluder pass to `simulation/fog_of_war.py` `compute_visibility(store, tactical_map)` (currently at lines 46-103) per spec lines 89-97 and 115-122.

After the existing distance + layer + pulse + sensor checks succeed (i.e., the observer would otherwise see the target), add the symmetric-blind check from spec lines 115-122:

1. `target_polygon = tactical_map.cover_polygon_containing(target.x, target.y)`
2. If `target_polygon is None` → keep the existing visibility result (target not in cover, no occlusion).
3. Else `observer_polygon = tactical_map.cover_polygon_containing(observer.x, observer.y)`.
4. If `target_polygon == observer_polygon` → keep visibility (same-polygon mutual sight).
5. Else exclude the target from the observer's visible set (cover occludes).

Same-faction visibility (existing logic, preserved): units always see their own faction regardless of cover. Do NOT apply the cover-occluder pass to same-faction pairs — they remain mutually visible per the spec ("B is in A's faction (always visible to self-side)") at spec line 23. Read same-faction status using the faction attribute already accessed by the existing same-faction branch inside `compute_visibility` at lines 46-103; do not introduce a new faction lookup mechanism.

No new external imports. Do not touch the sensor cone, pulse, layer, or distance code paths. Only the post-pass cover occluder is added.

Write `simulation/test_cover_visibility.py` BEFORE impl (RED first). Build minimal `TacticalMap` fixtures using two non-overlapping cover polygons (id 1 at (0..100)x(0..100), id 2 at (200..300)x(200..300)) and a small store of units. Assertions:

1. Attacker faction A at (500, 500) outside cover. Target faction B at (50, 50) inside polygon 1. Different factions → attacker's `visible` set does NOT contain target.
2. Attacker A at (10, 10) inside polygon 1. Target B at (50, 50) inside polygon 1. Different factions, same polygon → visible.
3. Attacker A at (10, 10) inside polygon 1. Target B at (250, 250) inside polygon 2. Different factions, different polygons → NOT visible.
4. Attacker A at (500, 500) outside cover. Target B at (510, 510) outside cover. Different factions, both outside → existing logic (visible if within sensor range; build fixture so it IS visible).
5. Same faction, both outside cover → visible (regression guard for existing behavior).
6. Same faction, one inside polygon 1 and one outside cover → visible (cover does NOT occlude same-faction).
7. Same faction, in different polygons → visible (cover does NOT occlude same-faction).

Confirm RED, implement, confirm GREEN.

## Acceptance

Run `cd simulation && python3 -m pytest test_cover_visibility.py -v`. Confirm RED before impl. Implement in `fog_of_war.py` only. Confirm GREEN. Then run `cd simulation && python3 -m pytest test_cover_umbrella.py::test_umbrella_c_symmetric_blind_target_in_cover_observer_outside test_cover_umbrella.py::test_umbrella_c_same_polygon_units_see_each_other test_cover_umbrella.py::test_umbrella_c_different_polygons_blind -v` and confirm all three umbrella-C tests pass (note: the spec doc indicates these umbrella tests are currently `pytest.skip` stubs — surface to parent if they remain skipped after a faithful impl). Commit the two files. Stop.

## Escalation triggers

Stop and report to the parent if:
- `fog_of_war.compute_visibility` cannot accept a `tactical_map` argument (signature changes upstream).
- Same-faction lookup is not available in the existing fog_of_war data structures.
- The cover occluder breaks any existing fog_of_war test not in this brief's scope.
- The umbrella-C tests are gated by `pytest.skip` and cannot be turned green without parent approval to remove the skip.
- Impl approaches `impl_line_budget` with assertions still failing.

## Assumption log

If at any point during your run you had to infer something the brief did not specify (whether to use a helper function, how to access the unit's faction from the store, anything), write it to `.swarm/briefs/wave_2_5_cover_los/leaf-04.ASSUMPTIONS.md` before you commit. Format:

```markdown
## Assumptions made during leaf-04

- **<thing>**: <inferred value> — source: <which spec line / contract symbol / file you looked at, or "no source — pure guess">
```
