# Land mockup pass 5: the layout leads, the terrain obeys (prototype spec, 2026-10-03)

Prototype under `agile.md`, Prototype gate. One Doer. It may skip determinism, budgets and tests; it is never loaded by the game. Land kits only; do not touch `field_map_space.gd`.

**What Westley must be able to judge.** His words, register Q-191-04 (amended 2026-10-03): "the landscape engine should take the inputs from the layout engine and lean on them. For example, if the layout engine calls for something like a choke, the landscape engine is required to produce it. Mark that I want to see a prototype of the layout engine, and how the landscape engine reacts to it." Also Q-191-01 (a scoring per kind of place, "I want to see it in action"), Q-191-03 (both sides the same distance from the objective and from each significant resource; "I don't care what the shape is, I only care about those numbers"), Q-192-02 (the layout decides choke width). Read those rows, Q-191-05 and Q-192-04 in `ambiguity_register.md`, and `docs/northstar/research/landscape_design/options_2026-10-03_walkable_land.md`.

**Inputs that exist.** Eight layouts as node graphs in `simulation/layout_library/layout_0N_*.json`: zones with `position_ratio`, `node_type` (staging, objective, chokepoint, vantage, flank_route, transit, hazard anchor, spawn, extraction), properties, and edges. The pass 4 terrain, its blocked-ground mask, ramps, relief and canvas controls in `scenes/mockups/landscape/`.

**Build:**

1. **Layout picker.** Load the eight layouts; a selector chooses one (or from the seed). Draw its nodes and edges over the map, typed by colour and labelled, with a toggle.
2. **Terrain obeys.** After the terrain is generated, for the chosen layout:
   - each node's ground is made standable (a levelled pad sized to its kind);
   - each edge becomes a walking route: where the blocked-ground mask or water breaks it, cut a pass, lay a ramp between bands, or bridge the water, so a walker can follow every edge;
   - each chokepoint is made a real choke: the walkable way through is narrowed to the layout's width and its sides are blocked ground or water. The layouts say only "narrow" and "moderate"; use 300 wu and 600 wu as candidates, printed, each on a slider;
   - each vantage is put on high ground (the highest ground near its position, or raised), reachable by a route;
   - a flank route is a second walking route that bypasses its choke.
   Draw every piece of ground the terrain changed for the layout in its own colour with a toggle, so "how the landscape reacts" can be seen, and a toggle that turns the reaction off so before and after can be compared.
3. **Places per kind.** Find, by a separate scoring for each kind, on the obeying terrain: a base for each side (at or near the staging nodes), economic locations, two significant resources, expansion sites, neutral settlements. Counts scale with canvas (candidates, printed). Show each kind's score as a heat view on a key, and the winners as markers.
4. **Equal distance.** Place the significant resources and check the objective so each side's walking distance to the objective, and to each significant resource, is equal within a tolerance (candidate 10 percent, printed). The HUD prints both sides' walking distances and straight-line distances to each, and the difference. When a seed cannot meet it, say so in the HUD; do not hide it.
5. **Checks in the HUD.** Every layout edge walkable (yes or count broken); every choke's measured width; every vantage reachable; walking route between the two bases exists and its length.

**Not in this pass:** landforms batch 2, settlements, the archetype's landform bias, anything in the space kit.

**Deliver.** Screenshots at 1920x1080 in `docs/northstar/research/landscape_design/mockup/pass5/` through `scripts/mockup_qa.sh` and a new `qa/pass5.json`: for layouts 01, 03 and 06 on seed 11 and layout 01 on seeds 12 and 13: the layout overlay on the raw terrain (reaction off), the same with the reaction on and the changed ground coloured, the walk view, and one close-up of a choke. One heat view per place kind on layout 01 seed 11. A table for all eight layouts on seeds 11 to 13: edges walkable over edges, choke widths, vantages reachable, base-to-base walking distance, each side's distance to the objective and to each resource, generate time.

**Record.** Add a "Pass 5" section to `docs/northstar/research/landscape_design/README.md`: what was built, the candidate numbers, the keys, the table, and questions for Westley (choke widths, the distance measure and tolerance, the counts, whether the cut routes read as natural). Edit no other doc.

**Hand back.** Own worktree from origin/main, branch `push/proto-land-p5`, push and stop. Look at every screenshot yourself. Report under 30 lines: commit, files, the table, anything not built and why. Kill only pids you started.
