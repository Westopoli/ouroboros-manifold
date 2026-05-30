---
leaf_id: leaf-02
spec_file: docs/test_specs/cover_los_rework_spec.md
spec_lines: 67-87
test_file: simulation/test_cover_polygon.py
impl_file: simulation/tactical_map.py
contract_imports:
  - CoverPolygon
  - TacticalMap
  - is_in_cover
  - cover_polygon_containing
do_not_edit:
  - docs/bible/bible_world.md
  - docs/bible/bible_combat.md
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
  - simulation/gradient_placer.py
  - simulation/map_generator.py
  - simulation/fog_of_war.py
  - simulation/damage.py
  - simulation/tactical_engine.py
impl_line_budget: 150
test_assertion_budget: 18
wave: 1
---

## Task

Add the `CoverPolygon` class and polygon-containment API to `simulation/tactical_map.py` per spec lines 67-87 and 107-113.

Add a `CoverPolygon` class with `__slots__ = ("polygon_id", "vertices")`. Constructor signature: `__init__(self, polygon_id: int, vertices: list[tuple[float, float]])`. Vertices represent a closed polygon stored open (last vertex != first vertex). No vertex normalization, no validation beyond Python type hints.

Add to `TacticalMap.__init__` a new keyword parameter `cover_polygons: list[CoverPolygon] | None = None`. Default to an empty list when `None`. Store on `self.cover_polygons`. Do not break any existing call site — every other constructor parameter is unchanged and the new parameter has a default. The 30+ existing `TacticalMap(...)` callers must remain functional with no changes.

Add `TacticalMap.is_in_cover(self, x: float, y: float) -> bool`: returns True iff any polygon in `self.cover_polygons` contains the point. Use ray-casting (count edge crossings from (x, y) to (+∞, y); odd crossings = inside). Edge convention: a point exactly on an edge counts as INSIDE (spec line 133, gotcha 3).

Add `TacticalMap.cover_polygon_containing(self, x: float, y: float) -> int | None`: iterate `self.cover_polygons` in list order; return the `polygon_id` of the first polygon containing the point per the same ray-casting algorithm; return None if no polygon contains the point.

Do not retire `cover_density()` in this leaf — that retirement is L5's job. Do not edit any caller of `TacticalMap`.

Write `simulation/test_cover_polygon.py` with the following assertions BEFORE writing impl (RED first):
1. `CoverPolygon(7, [(0,0),(10,0),(10,10),(0,10)])` constructs; `.polygon_id == 7`; `.vertices` length 4.
2. Empty TacticalMap (no `cover_polygons` kwarg) → `cover_polygons == []`, `is_in_cover(5,5) is False`, `cover_polygon_containing(5,5) is None`.
3. TacticalMap with one square polygon id=1 at (0,0)-(100,100). `is_in_cover(50, 50)` True. `cover_polygon_containing(50, 50)` == 1.
4. Same map. Point at (200, 200) → `is_in_cover` False, `cover_polygon_containing` None.
5. TacticalMap with two non-overlapping squares (id=1 at (0..100), id=2 at (200..300)). Point (50,50) → id 1. Point (250, 250) → id 2. Point (150, 150) → None.
6. Edge convention: point exactly on a polygon edge (e.g., (0, 50) on the left edge of the id=1 square) → `is_in_cover` True, `cover_polygon_containing` returns 1.
7. Non-convex polygon (an L-shape with 6 vertices). Point in the inner corner of the L is inside; point in the L's "missing" rectangle is outside.

Confirm the test fails RED first, then implement the class + methods, then confirm GREEN.

## Acceptance

Run `cd simulation && python3 -m pytest test_cover_polygon.py -v`. Confirm RED before impl. Implement in `tactical_map.py` only. Confirm GREEN. Then run `cd simulation && python3 -m pytest test_cover_umbrella.py::test_umbrella_a_cover_polygon_class_exists test_cover_umbrella.py::test_umbrella_a_tactical_map_exposes_cover_polygons test_cover_umbrella.py::test_umbrella_a_is_in_cover_api test_cover_umbrella.py::test_umbrella_a_cover_polygon_containing_api -v` and confirm all four umbrella-A tests pass. Commit the two files. Stop.

## Escalation triggers

Stop and report to the parent if:
- Adding `cover_polygons` to `TacticalMap.__init__` breaks any existing caller.
- Ray-casting on the L-shape assertion (test 7) requires a special-case branch outside the canonical algorithm.
- The class needs additional methods beyond `is_in_cover` and `cover_polygon_containing` to satisfy the tests.
- Impl approaches `impl_line_budget` with tests still failing.

## Assumption log

If at any point during your run you had to infer something the brief did not specify (default polygon-id type, ray-casting tie-breaking on horizontal edges, anything), write it to `.swarm/briefs/wave_2_5_cover_los/leaf-02.ASSUMPTIONS.md` before you commit. Format:

```markdown
## Assumptions made during leaf-02

- **<thing>**: <inferred value> — source: <which spec line / contract symbol / file you looked at, or "no source — pure guess">
```
