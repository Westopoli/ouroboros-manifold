# Terrain obeys the layout: mockup pass 1 (spec, 2026-10-15)

**Status: specced by the Architect after the lane P rev 5 audit (8 blocking, all geometric); a Doer builds it on the Mac in the landscape mockup; Westley judges by eye and the measured facts feed the C spec (lane P rev 6). Prototype gate (`agile.md`): no C piece on this until he approves the look and the numbers.**

## Why

Westley, 2026-10-03: "the landscape engine should take the inputs from the layout engine and lean on them ... if the layout engine calls for something like a choke, the landscape engine is required to produce it. Mark that I want to see a prototype of the layout engine, and how the landscape engine reacts to it." Ruled again 2026-10-15 (Q-191-14 (b)), with R-189-07 (at least two walking routes per strategic point, one small-army width, one big-army width, a seeded roll above the minimum). The C draft could not settle on paper how a pad, a wall and a choke survive the band fit, the steep mask and the slope rule; this pass shows it on the approved land mockup (`scenes/mockups/landscape/`, pass 6b approved 2026-10-05/06) and measures it.

## What the pass adds to the mockup

New files only: `scenes/mockups/landscape/obey_layer.gd` (the request builder and the terrain edits) and `obey_overlay.gd` (the drawing and the panel); one new child node in `landscape_mockup.tscn` (the only edit to an existing file, a scene instance line). Nothing under `csrc/`.

1. **Requests from the seed** (no terrain read): two bases on a line through the canvas centre at a seeded angle (the mockup's own RNG, seeded from the scene seed plus 470; angle in [0, 2π) by `u · 2π`, positions by the mockup's existing vector maths, which is free of the C lint), each `DRAFT-base-inset` 2,400 wu in from the canvas edge measured along that line; the objective at the midpoint (every archetype in this pass; the beside-the-defender rule of Q-191-11 is pass 2); two resource sites on the perpendicular through the objective at `DRAFT-resource-clearance` 2,400 wu either side; one choke on the base line at a seeded fraction in [0.35, 0.65], width `w` drawn from [`DRAFT-route-small-width` 180 wu, `DRAFT-route-big-width` 600 wu]; one vantage within `DRAFT-vantage-offset` 1,500 wu of the choke, perpendicular side chosen by the seed; route roll `route_count = 2 + floor(u · 3)`. Canvas sizes: 16,000 (the mockup's default) and 8,000 (the small category), a key toggles. Every number is a named draft in the panel and movable by keys ([ ] on the selected draft).
2. **Terrain obeys**, applied after the mockup's landform stages and before its band fit (the mockup's equivalent of `tg_peak_fit`; the Doer names the function in its report): (a) pads: a plateau of radius `pad_wu` at each base (`DRAFT-base-pad` 1,200), the objective (600) and each site (400) at the median height of the ground within 2·pad, joined to the surrounding ground by a ramp whose slope never exceeds the walking limit (35 degrees, R-189-02), the ramp extending as far as it must; (b) the choke: a corridor of width `w` along the base line at the choke point, kept at the plateau height of the nearer pad, with the ground either side out to `DRAFT-choke-wall` 900 wu raised by `DRAFT-wall-rise` 400 wu (one band step on the default fit) with faces steeper than 35 degrees, so the corridor is the only walkable crossing within the wall span; (c) the vantage: a mound rising `DRAFT-vantage-rise` 300 wu above the local ground with one ramp face. Then the mockup's band fit, steep mask and slope finding run as they do today over the edited field.
3. **The check**, on the finished terrain, with the mockup's real per-band walk masks and slopes (the walk view already has them: the gold ramps and the "layers reachable" count): a route of width `W` between two points exists iff a BFS over walkable cells, restricted to cells whose every neighbour within `ceil(W / 2 / cell) - 1` cells is also walkable on the same band or joined by a slope, connects them; the choke's measured width is the narrowest cross-section of walkable cells along the corridor (in cells and wu). Counts: separate routes between each base and each strategic point (the other base, the objective, both sites) found greedily, each found route plus a one-cell margin removed before the next search, up to `DRAFT-route-max-count` 4; big-width and small-width routes reported separately. The panel prints, per strategic point: routes found at small width, at big width, the choke's measured width, the pad's maximum ring slope, and PASS or FAIL against `route_count`.
4. **The look**: the overlay draws requests (pads as discs, the choke as a bar of width `w`, the wall span, the vantage, the sites), the found routes in two colours (big, small), and the failing clause in red. `V` toggles the overlay; `F1`–`F3` seeds; `C` canvas size; `R` regenerate.

## Shots and the report

`--shot <dir>`: for seeds 1 to 3 on both canvases, the walk view with the overlay, named `obey_<canvas>_<seed>.png`, plus `obey_panel_<canvas>_<seed>.txt` with the panel's numbers; the Doer attaches all twelve and a table of the measured facts: for each seed and canvas, the choke width asked and measured, routes found per strategic point at both widths, the maximum pad ring slope, PASS/FAIL, and the wall time of the check. One line per spec point it could not meet.

## Tests

`tests/test_mockup_obey.gd` (test writer first): the scene loads without the pipe; `--shot` leaves the twelve files; on seed 1 at 16,000 the panel reports PASS; the choke's measured width is within one cell of the asked width; no pad ring slope exceeds 35 degrees; the check runs under `DRAFT-obey-budget` 250 ms per seed on this Mac (printed, asserted at 4x). Positive controls: a hand-built field with the corridor walled on both sides reports FAIL on routes; a pad with a 60-degree ring reports FAIL on slope.

## What Westley judges

Whether a choke the layout asked for reads as a real choke of that width on the land; whether pads look like places rather than stamps; whether two routes of the two widths exist and read as such; the small canvas. His verdict and the measured table become lane P rev 6: the C pieces (P0, T-OBEY, P3) are written from the mockup's procedure, with the cell arithmetic, the band-fit ordering and the snap rule taken from what worked.

## Pass 1 result (2026-10-16, Doer report; branch `push/proto-terrain-obeys` 804f666b)

Measured on the mockup's real per-band data (routes small/big per point, roll in brackets):

| canvas | seed | choke asked / measured | base_b | objective | site_0 | site_1 | ring max | result | check ms |
|---|---|---|---|---|---|---|---|---|---|
| 16000 | 1 | 467 / 410 | 2/0 (4) | 2/0 | 2/0 | 2/0 | 33.6 | FAIL routes | 111 |
| 16000 | 2 | 502 / 510 | 2/0 (2) | 4/1 | 4/1 | 4/1 | 31.2 | FAIL routes (base_b big 0) | 133 |
| 16000 | 3 | 264 / 190 | 4/1 (2) | 4/1 | 4/1 | 4/1 | 31.9 | PASS | 124 |
| 8000 | 1 | 467 / 420 | 4/1 (4) | 4/3 | 4/2 | 4/1 | 56.6 | FAIL ring (objective) | 47 |
| 8000 | 2 | 502 / 510 | 4/1 (2) | 4/3 | 4/3 | 4/2 | 61.8 | FAIL ring | 52 |
| 8000 | 3 | 264 / 290 | 4/2 (2) | 4/0 | 4/1 | 4/3 | 58.9 | FAIL ring, routes | 41 |

Facts for lane P rev 6: (1) pads, the choke and the vantage are produced and measured within one cell, with pad rings under 35 degrees on the 16,000 canvas; (2) they do not make routes: only about 59 percent of cells walk at 35 degrees, base exits are 1 to 2 cells wide, and a big-width route (5 cells) past a 466 wu choke needs a bypass beyond the 900 wu wall that terraced ground never has; raising the ramp reach to 8,000 wu changed nothing; so **the engine must carve routes** (a corridor of width W along a found path, widened and graded) as a fourth edit, and the check is then a proof, not a hope; (3) the choke on the base line crosses the objective pad for most rolls, so the request geometry needs the objective off the line or the choke range narrowed (the pass slid the choke inside [0.35, 0.65] to clear pads; on 8,000 no clear spot exists); (4) on the 8,000 canvas the pads overlap the walls and the ring slopes reach 57 to 62 degrees: insets and pads must scale with the canvas; (5) the drafts the C spec lacked: choke-length 600, wall-gap 125, wall-face 100, ramp-grade 28, ramp-reach 2,400, vantage-radius 250; (6) the mockup had no hook between the landform stages and the band fit, so the edits run after generate and re-run the band fit and ramps; the C hook sits after the landforms and before `_build_slope`, which matches the draft's insertion point. Without the edits every case fails everything (the positive control).

## Out of scope

Space maps (Q-191-10 (a), deferred to lane D), the beside-the-defender objective, neutral towns and lots (P1 as specced), the C sim, saves.

## Run

```
GODOT=/Applications/Godot.app/Contents/MacOS/Godot
git fetch origin && git checkout push/proto-terrain-obeys
$GODOT --path . res://scenes/mockups/landscape/landscape_mockup.tscn
```
