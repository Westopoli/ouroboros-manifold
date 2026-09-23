# leaf-01 assumptions

C5 spec (docs/northstar/plans/push/specs/C5.md) and the fenced test
(tests/test_tactical_view.gd) leave a few concrete choices open. Logged
per the brief's "log every inference" instruction.

- **Screen-direction convention (spec lines 84-86, note's Q- candidate
  "(a) assert only one dominant screen axis")**: picked world +x -> screen
  +x, world +y -> screen +y (no axis flip), scale 0.25, camera centered
  in screen space. Test only asserts dominant-axis-changed
  (`_check_moved_unit_and_facing_R100_01`, lines 203-208 of the test), so
  any sign/scale choice holding that invariant satisfies it; this is the
  simplest one.
- **Projection/scale constants**: `WORLD_SCALE = 0.25`, screen space fixed
  at 1920x1080 (`SCREEN_W`/`SCREEN_H` constants), independent of the
  actual runtime viewport. Chosen because the test's own viewport check
  (test lines 148-162) falls back to 1920x1080 under `--headless` (the
  note's "Reference-stub proof" point 3: `get_root().size` reads 100x100
  headless regardless of `project.godot`'s configured 1920x1080), so
  computing screen position against the project's configured resolution
  rather than querying `get_viewport()` at runtime is what actually keeps
  `units_px` inside the asserted bounds.
- **Camera default**: camera initializes to `(canvas/2, canvas/2)` on the
  first `load_frame` call, then never auto-recenters on later
  `load_frame` calls (only `qa_pan` changes it after that). Spec doesn't
  state an initial camera value; centering on the map matches
  `_check_units_count_and_px_in_viewport` (test lines 142-162), which
  needs the tick0 fixture's units (world x 800-3400, y 800-3200 inside a
  4000 canvas) to already be on-screen before any `qa_pan` call.
- **`selected`'s internal shape**: plain `Array` of `int` unit ids
  (matches `qa_box_select`'s return type and what
  `_check_box_select_then_move_R105_01`, test lines 250-270, immediately
  feeds into `issue_command`'s `unit_ids`). Pruned on `load_frame` to drop
  ids no longer present in the new frame's `units` array (not asserted by
  the test either way; kept for consistency since a scene reload
  shouldn't leave stale ghost selection ids around).
- **`facing-fixed` freeze semantics**: "freeze at whatever it had"
  (spec line 62-63) implemented as: on activation, snapshot the
  currently-loaded frame's per-unit facing into `_frozen_facing`; any
  unit not yet in that map (not present in the frame at activation time)
  gets frozen at the facing value from the first `load_frame` call it
  appears in after activation. The test
  (`_check_plant_facing_fixed_R100_01`, test lines 305-316) only checks
  that two post-activation reads of unit 4's facing are equal to each
  other, not any specific value, so this satisfies it under any
  activation-time frame.
- **Rendering primitive**: `Polygon2D` per unit (small square,
  `UNIT_SIZE = 24.0`), not `ColorRect`/`MeshInstance3D` — spec line 83
  names `Polygon2D` as one of the allowed options and it's a `Node2D`
  subtype, so it shares the manually-computed screen-space coordinate
  system with the root `Node2D` without mixing in `Control`'s separate
  layout/anchor system. No fenced check inspects the scene tree's visual
  nodes (only `qa_state()`/`qa_box_select()`'s returned data), so this is
  decorative/for-real-use only, not load-bearing for the test.
- **No additional helper script**: everything fit in one file,
  `scenes/tactical_c/tactical_view.gd` (212 lines), under the 500-line
  `impl_line_budget`. No second script was needed.
