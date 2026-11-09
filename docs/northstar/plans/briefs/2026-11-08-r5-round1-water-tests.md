# R5 round 1, fix 2: one water definition for every view. Tests (red) first.

Role: Engineer (Sonnet 5.5), test writer. Tests only; a different engineer builds. Spawn nothing. Think tersely. Report once, under 25 lines: files, test names, run command, the red output's decisive line.

## Finding (investigation 1, 2026-11-08)

The walk and react views paint every cell with `grid[i].water >= 0.5` as water (`pass5_ui.gd:469-483`, `pass5_layout.gd:276`). The `visual` view (used for `raw_layout`) draws the ground mesh at real height (`ground.gd:20-60`) and water as one plane at y=0 (`placer.gd:621-634`, kit `water_is: surface`). Lake cells filled by `_flood_lake` (`field_map.gd`, `DRAFT_LAKE_FILL_HEIGHT` 150) sit 400 to 630 wu above 0 on L06 seed 11 (row gy 144, gx 98 to 105, 24,000 wu canvas, `SPACING` 100), so they are blue in walk and plain ground in raw_layout. Map-wide, 4,947 of 15,095 flagged cells are above 0. Westley: "investigate if this is an issue with water appearing at different levels on the walk.png than on the raw_layout.png".

## The rule the tests pin

One function `FieldMap.is_water(i: int) -> bool` (`water >= 0.5`) is the only water test in the landscape mockup; every view (visual ground mesh, react, walk, heat) paints exactly the set of cells it returns true for; the visual view draws a lake's surface at that lake's fill level (the `_flood_lake` level, stored per cell as `grid[i].water_level` or a parallel `PackedFloat32Array`), not at y=0, so a mountain lake is seen as water in 3D.

## Where

Both worktrees carry the same landscape files; write the same test file in each: `~/Projects/om-wt/r5-pass5` (branch `wip/r5-pass5-shots`) and `~/Projects/om-wt/r5-obey` (branch `wip/r5-obey-shots`). Files: `scenes/mockups/landscape/field_map.gd`, `ground.gd`, `placer.gd`, `pass4_ui.gd`, `pass5_ui.gd`, `pass5_layout.gd`, kits `kits/greek.json`. Harness: `tests/test_mockup_landscape_waterline.gd` (`extends SceneTree`, run by `scripts/run_godot_tests.sh`); copy its generation setup. Scratch only in `/tmp/claude-1000/-home-westopoli-Projects-ouroboros-manifold/db98320a-0522-401b-91ae-f1f3583f73a5/scratchpad/`.

## Tests: `tests/test_mockup_landscape_water_views.gd`

1. `FieldMap.is_water` exists and equals `water >= 0.5` for every cell (seed 11, 24,000; seed 1, 16,000).
2. Every lake cell has a `water_level` at or above its elevation and equal across the connected lake (one waterline per basin; reuse the waterline test's basin walk), and sea cells have level 0.
3. The visual ground mesh marks water where `is_water` is true and nowhere else: expose from `GroundBuilder` (or the node that owns the mesh) a method `water_cells_drawn() -> PackedByteArray` the test compares cell for cell with `is_water`; the builder implements it alongside the drawing change. Count equality and per-cell equality.
4. The visual water surface height at cell i equals `water_level[i]` for a sample of 50 lake cells above 0 (expose `water_surface_height(i)` the same way), and is 0 for sea cells.
5. Regression: L06 seed 11 (layout 6, HUD defaults, react off), cells gx 98 to 105 at gy 144 are `is_water` and are drawn as water in the visual view.
6. Mask views unchanged: the walk and react masks paint exactly `is_water` cells (compare against the existing colour routine's water set).
7. Positive control: with the current code, assertion 3's probe does not exist and the y=0 plane would miss the 4,947 above-zero cells; assert on the current code that at least 30 percent of `is_water` cells have elevation above 0 (so the plane cannot show them), proving the test's target is real.

Each assertion names this brief and the Westley sentence. No implementation. Both files red for the expected reasons. Commit per worktree with subject `R5 round 1: red tests for one water definition across views` and trailer `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`; add only your test files and their `.uid`, never `-A`.
