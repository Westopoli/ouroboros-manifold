# Settlement mockup pass 1 (prototype record, 2026-10-03)

**Approved 2026-10-06.** Westley, verbatim: "Settlements mockup approved". The approval covers the look of pass 1; its five questions and Q-193-01 to Q-193-06 keep their candidates until he answers them.


Spec: `docs/northstar/plans/2026-10-03-settlement-mockup-pass1-spec.md`. Prototype under agile.md, never loaded by the game. Placeholder boxes. Every number below is a CANDIDATE, picked to make the thing visible; none is a rule.

## Run

- Watch it live (needs a display): `godot --path . res://scenes/mockups/settlement/settlement_mockup.tscn`
- Scripted pass, screenshots + state JSON (xvfb, llvmpipe): `scripts/mockup_qa.sh run settlement scenes/mockups/settlement/qa/pass1.json docs/northstar/research/settlement_mockup/pass1 --res 1920x1080 --timeout 400`
- Run once `godot --headless --import --path . --quit` in a fresh worktree.

## What was built (files in `scenes/mockups/settlement/`)

- `settlement_sim.gd`: growth sim on a 121x121 window (100 wu cells) cut from `FieldMap` (seed 11, 24000 wu, read-only; core = `nodes[0]`).
- `settlement_mockup.gd/.tscn`: terrain mesh, MultiMesh boxes, HUD, camera, input, QA contract.
- `qa/pass1.json`: the scripted pass that made the screenshots.

1. Growing density. Potential P starts at 1.0 on the core and spreads one ring per growth tick (3 s sim). Each hop multiplies by a factor: base decay, less for climbing (elevation difference between cells), less for steepness, less far from water, and only 0.85 across water. So it hugs coasts, follows contour lines, no rings. Density D eases toward P x maturity (0.6 rising to 1.0 over 300 s), never falls.
2. Lots and stages. Each lot is jittered up to 0.22 cell and turned by a per-cell hash; where slope is above 0.06 (candidate) it is turned along the contour, with 0.25 rad of jitter, so rows bend with the land. One lot per 100 wu cell; every 4th row and column is a lane, left empty. A lot rises one stage at a time (0.9 s grow animation, 0.4 s in a wave): marked ground, scaffold (orange), built (grey), dense (tall blue-grey).
3. Waves. Three buttons. Shipment: one street (24 cells long, 2 lots deep) goes up in a staggered sweep. Expansion: one street plus a new density seed at its far end. Season: three streets. The differences are my guess, the labels are what to judge.
4. Placement. Click puts a 5x5 cell (500 wu) building. Lots under it are cleared, lots in the 2-cell ring around are reset and refill over about 1 to 8 s, and the building seeds density so the city bends around it.
5. Difficult ground. No lot on water or within 1 cell of water (candidate shore margin); the sea surface is drawn flat at sea level, so the steep seabed no longer reads as ground. Slope above 0.22 gets a cliff dwelling (purple, small, capped at 3 stages), never nothing. Water cells get nothing.
6. Damage. D on the hovered area (13x13 cell yellow marker) drops lots one stage per press down to rubble (dark brown), rebuild starts 10 s later.
7. Paths. Method: one Dijkstra from the core over a cost grid (1 + 6 x slope, +25 per water cell, player buildings impassable), the cheapest route to each of 8 compass sectors on the window edge, thickened by 1 cell each side (300 wu wide, over the 200 wu need). Drawn as one ribbon per route from the core to the window edge, raised to the highest ground in the 3x3 around each point so it sits on the land. Those cells are never built on; a placement re-runs it and lots on the new route are cleared. Routes crossing more than 6 water cells are dropped (so on this map only 5 of 8 sectors get a path; the rest are sea). Toggle P; the HUD prints the route count (5). State reports `path_connected` by a flood fill from the core.
8. Time. 1x, 5x, 20x, Reset (buttons and keys 1/2/3, R).

## Keys

Click place building, D damage under mouse, Z/X/C waves (shipment, expansion, season), 1/2/3 speed, P paths, R reset, WASD or arrows pan, Q/E turn, wheel zoom.

## Candidate numbers

| Name | Value |
|---|---|
| Stage thresholds on density (marked, scaffold, built, dense) | 0.10, 0.22, 0.38, 0.58 |
| Stages | 4 (plus rubble) |
| Growth tick | 3 s sim |
| Spread decay per cell | 0.99 base, climb term elevation difference / 900 wu x 0.5, steepness 0.25 x slope, 0.99 away from water (beyond 3 cells), 0.85 across water |
| Maturity | 0.6 to 1.0 over 300 s |
| Cliff dwelling slope | above 0.22 (slope value; about the steepest 10 percent of land here) |
| Rise animation | 0.9 s, 0.4 s in a wave |
| Wave street | 24 cells (2400 wu) long, 2 lots deep, 0.04 s stagger per lot |
| Player building | 5x5 cells, refill ring 2 cells |
| Damage area | radius 6 cells; rebuild delay 10 s |
| Path width | 3 cells (300 wu); 8 sectors; water crossing cap 6 cells |

## Measured (Godot 4.6.3, xvfb, llvmpipe software GL, 1920x1080; RTX 3060 not used by xvfb, so render cost is unrepresentative)

- Lots standing: 0 at start, 271 at 1 min, 595 at 5 min, 581 after placing and 59 rubble after damage. Instances allocated: 14,641 (idle ones scaled to zero).
- Script cost per frame (sim update, growth, flush, hover pick): 0.1 to 0.5 ms normally, 1.2 ms at 20x. Growth tick 2 to 6 ms. Path recompute about 65 to 70 ms (on placement only). Window frame time under llvmpipe including the screenshot grab: 100 to 1000 ms, dominated by software rendering of the terrain and 14k instances; not a GPU number.
- `qa/pass1.json` runs clean: `errors.txt` count 0.

## Not built / limits

- Lanes are still an axis-aligned grid of empty cells; jitter and contour yaw hide it but streets are not curved.
- Purple dwellings still cluster on dry steep land at the shore; they are on land cells, not sea.
- No real GPU frame time (needs a desktop run).
- Rubble kept the same rise path; no distinct "burnt" look.
- The window is 12100 by 12100 wu around the core, not the whole map; the core is on a coast so about 43 percent of it is sea.
- Paths do not cross sea; sectors with only sea get none.

## Questions for Westley

1. Q-193-01: do shipment / expansion / season feel like different waves, or should one trigger (for example every arrival) be enough? Is a three-street season wave too much?
2. Q-193-02: are 4 stages the right count for the eye (does marked ground add anything, or should it begin at scaffold)? Does 20 s of a street going up read as a spectacle, or too slow or too fast at 1x?
3. Q-193-06: the 300 wu corridors from core to the edge: is one route per compass sector enough way through, or should paths also run between districts? Are dropped sea sectors acceptable?
4. Cliff dwellings: are small purple boxes enough of a signal that the city adapts to steep ground, and should they thin out rather than match the lane grid?
5. Should a placed building also pull density to itself (it does here) or only clear and refill?
