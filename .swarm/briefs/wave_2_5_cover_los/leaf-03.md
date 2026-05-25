---
leaf_id: leaf-03
spec_file: docs/test_specs/cover_los_rework_spec.md
spec_lines: 135-136
test_file: simulation/test_cover_polygon_placement.py
impl_file: simulation/gradient_placer.py
impl_files:
  - simulation/map_generator.py
contract_imports:
  - CoverPolygon
  - place_cover_polygons
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
  - simulation/fog_of_war.py
  - simulation/damage.py
  - simulation/tactical_engine.py
  - simulation/test_cover_polygon.py
  - simulation/test_cover_visibility.py
  - simulation/test_cover_damage_gate.py
  - simulation/test_cover_ai_peek.py
  - simulation/test_cover_integration.py
impl_line_budget: 150
test_assertion_budget: 15
wave: 2
---

## Task

Convert cover gradient sources into discrete `CoverPolygon` instances per spec lines 47 and 135-136.

Add `place_cover_polygons(inst: InstantiatedLayout) -> list[CoverPolygon]` to `simulation/gradient_placer.py`. For every spine node that today emits a `GradientSource` with `property_type == "cover_density"` (chokepoint, staging, hazard_zone_anchor, objective, flank_route per the existing function body), emit one `CoverPolygon` instead. Vertex generation: circle approximation at the cover-source radius (use the same per-node-type radius constant the existing emission uses — e.g. `config.GRADIENT_CHOKEPOINT_COVER_RADIUS` for chokepoint). Use 12 vertices (full-circle, evenly spaced angles). Assign `polygon_id` as the index in the returned list (0, 1, 2, ...).

Cover `GradientSource` emissions in `place_gradients` are NOT removed in this leaf — they stay until L5 retires `cover_density()` from the damage path. The two functions coexist.

In `simulation/map_generator.py` around line 126-128 where `TacticalMap(...)` is constructed, add one call: `cover_polys = place_cover_polygons(inst)` and pass `cover_polygons=cover_polys` into the `TacticalMap` constructor. Do not modify any other line of `map_generator.py`. Do not touch the `place_gradients` flavoring pipeline.

Write `simulation/test_cover_polygon_placement.py` BEFORE impl (RED first) asserting:
1. Layout containing a single `chokepoint` spine node at position (500, 500) → `place_cover_polygons` returns exactly 1 `CoverPolygon` with `polygon_id == 0` and 12 vertices, all within `±radius` of (500, 500).
2. Layout containing one `chokepoint` + one `objective` at distinct positions → returns 2 polygons with `polygon_id == 0` and `polygon_id == 1`.
3. Layout containing a `vantage` only (no cover emission) → returns empty list.
4. Each vertex of a generated polygon lies within `radius * 1.001` of its source center (rounding tolerance).
5. Polygon vertices are stored as `list[tuple[float, float]]` (not a generator, not a tuple of tuples).

Confirm RED, implement, confirm GREEN.

## Acceptance

Run `cd simulation && python3 -m pytest test_cover_polygon_placement.py -v`. Confirm RED before impl. Implement in `gradient_placer.py` + the single wiring line in `map_generator.py`. Confirm GREEN. Commit the three files. Stop.

## Escalation triggers

Stop and report to the parent if:
- A cover-emitting node type from `place_gradients` is not covered by the new `place_cover_polygons` function (chokepoint, staging, hazard_zone_anchor, objective, flank_route).
- `map_generator.py` requires more than one new import line and one new statement at the `TacticalMap(...)` call site.
- `place_gradients` produces a cover source whose radius constant cannot be reused for polygon generation (i.e., the per-node-type radius isn't exposed).
- L2's `CoverPolygon` class signature differs from what this brief expects.

## Assumption log

If at any point during your run you had to infer something the brief did not specify (vertex order convention CW vs CCW, starting angle, intensity-to-radius mapping for overlapping sources, anything), write it to `.swarm/briefs/wave_2_5_cover_los/leaf-03.ASSUMPTIONS.md` before you commit. Format:

```markdown
## Assumptions made during leaf-03

- **<thing>**: <inferred value> — source: <which spec line / contract symbol / file you looked at, or "no source — pure guess">
```
