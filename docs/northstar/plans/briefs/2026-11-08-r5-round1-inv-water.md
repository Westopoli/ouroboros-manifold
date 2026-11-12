# R5 round 1, investigation 1: water in `walk.png` versus `raw_layout.png` (pass 5)

Role: Engineer (Sonnet 5.5), read-only investigation. Spawn nothing. Think tersely. Report once, at the end, under 40 lines, as the text of one report section (normal prose, for a human reader). Do not open any PNG as an image; read code and data.

## Westley's words (2026-11-08)

"One inconsistency across all the screenshots was that in the walk.pngs sometimes what shows as water or 'impassable' just looks like flat ground on the raw_layout.png. For example, to the left of choke_pass_entrance on walk.png there's a blue dot indicating water, yet on the raw_layout it just looks like flat ground, no water. I want you to investigate if this is an issue with water appearing at different levels on the walk.png than on the raw_layout.png (if there is consistency between png types of the same screenshot)."

## Where

Worktree `~/Projects/om-wt/r5-pass5` (branch `wip/r5-pass5-shots`, pass 5 of the landscape mockup plus the 2026-11-08 water fix in `scenes/mockups/landscape/field_map.gd`). Pictures on main: `~/Projects/ouroboros-manifold/docs/northstar/story_reviews/westley/layout_engine/r5-recovery/pass5/L0N_s11_{raw_layout,react,walk}.png`. The QA script that made them: `scenes/mockups/landscape/qa/r5_pass5.json` (each `screenshot` step is preceded by `qa_set` calls that choose the view). `choke_pass_entrance` is a node of layout 06 (`simulation/layout_library/layout_06_flanking_pass.json`), so his example is `L06_s11_*`.

## Questions, in order

1. Which view does each of the three shots use (`p4_view`, `p5` flags, graph on or off)? Quote the QA steps.
2. How does each view colour water? Read `Pass4Terrain.cell_colors` (`pass4_terrain.gd`, the walk view) and whatever draws the ground under `raw_layout` (the band/height view, or the plain terrain mesh: find it). Is water a different threshold, a different source (`grid[i].water` versus `p4.layer == 0` versus the mesh's sea level), or drawn at a different height in the two views? Is the lake fill of the water fix (`_flood_lake`, breadth-first, `LAKE_FILL_HEIGHT`) visible in both views or only in the walk mask?
3. For `L06_s11`, find the cell(s) just west of `choke_pass_entrance` (node position ratio from the layout JSON, canvas from the QA script, `FieldMap.SPACING`) and read, from the same generated field (run the generator headlessly with seed 11 if you can: `godot.real --headless --path ~/Projects/om-wt/r5-pass5 -s <scratch script>` is allowed; write scratch scripts only under `/tmp/claude-1000/-home-westopoli-Projects-ouroboros-manifold/db98320a-0522-401b-91ae-f1f3583f73a5/scratchpad/`), the water value, the height, the band and the walk-mask value there. Say which view would paint it water and which would not, and why.
4. Is the inconsistency one of these: (a) the two views use different water definitions; (b) the raw_layout shot is taken before the pass 5 reaction (pads, corridors) or before the water fix runs, and the walk shot after; (c) the graph overlay in raw_layout hides small water cells; (d) something else. Give the one answer the evidence supports, with file:line.
5. Propose the smallest fix that makes every view paint the same cells as water (one definition, one function), as a sentence; do not implement it.

Report format: the five answers numbered, each with file:line evidence, and a final line "Cause: ..." in one sentence.
