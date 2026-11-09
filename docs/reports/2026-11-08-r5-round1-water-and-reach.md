# R5 study, round 1: water across views, reachable ground, bases (2026-11-08)

Westley's round 1 general feedback on the R5 pictures (`docs/northstar/story_reviews/westley/ruled.md`, rows of 2026-11-08) raised four things: water shown in `walk.png` but not in `raw_layout.png`; too little reachable ground and a landscape that is too large-scale; too much text on the pictures; bases always flat. This report holds the two investigations. The text fix and the water fix are built tests-first on the two prototype branches (`wip/r5-obey-shots`, `wip/r5-pass5-shots`); the reach and bases options wait for his pick.

## 1. Water in `walk.png` versus `raw_layout.png`

Cause: the two views use different water definitions. The walk and react views paint every cell whose water value is 0.5 or more (`pass5_ui.gd:469-483`, flag from `pass5_layout.gd:276`). The `visual` view, which the `raw_layout` shot uses (`qa/r5_pass5.json` steps 46-49: `p4_view=visual`, react off, graph on), draws the ground mesh at its real height (`ground.gd:20-60`) with no water test, and water as one plane at y=0 across the canvas (`placer.gd:621-634`, kit `greek.json` `water_is: surface`). The lake fill of the 2026-11-08 water fix (`_flood_lake`, fill level seed elevation + 150 wu) marks cells at positive elevation as water; the plane sits under the ground there, so the lake is blue in walk and plain ground in raw_layout.

His example, L06 seed 11, west of `choke_pass_entrance` (node ratio 0.5, 0.6 on 24,000 wu; cell 120,144): row 144 has water cells at columns 98 to 105 with elevations 413 to 626 wu, all flagged water, none walkable, none a bridge. Map-wide, 4,947 of 15,095 flagged cells (33 percent) lie above 0 and are invisible in the 3D view. The react on/off difference between the two shots moves 92 cells map-wide and none of these. The graph overlay hides nothing.

Fix (tests first, `tests/test_mockup_landscape_water_views.gd`): one function `FieldMap.is_water(i)` is the only water test; every view paints exactly its cells; the visual view draws each lake's surface at its own fill level, so a mountain lake reads as water in 3D. Scratch probe: `scratchpad/probe.gd` of this session.

## 2. Reachable ground, feature scale, bases

(filled when investigation 2 reports)
