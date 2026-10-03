# Land mockup pass 4: where walkers can go (prototype spec, 2026-10-03)

Prototype under `agile.md`, Prototype gate. One Doer. It may skip determinism, budgets and tests; it is never loaded by the game. Land kits only; do not touch `field_map_space.gd`.

**What Westley must be able to judge.** Where units can and cannot walk, whether every map has real height on all five layers, and whether the landforms give the variety he has in mind. His words are in `ambiguity_register.md` under Q-188-01, Q-189-02, Q-189-03, Q-189-04, Q-187-01, Q-187-02, Q-192-03; read those rows first.

**Build, in `scenes/mockups/landscape/`:**

1. **Too-steep view.** A key cycles: off, steeper than 30 degrees, steeper than 35. Ground over the limit is drawn in a clear flat red, the 30 to 35 band in orange. The HUD prints the share of land too steep at 30, 32.5 and 35.
2. **(X) cursor.** With a "unit selected" toggle on, hovering too-steep ground shows an X at the cursor.
3. **Band view.** A key colours the ground by layer 1 to 5. Bands are fitted per map between its lowest and highest ground. The HUD prints the five band heights, the height of each step in wu, and the share of land on each layer.
4. **Minimum relief.** The generator guarantees a minimum difference between lowest and highest ground, set by a slider in wu. Pick a starting value, say why, and mark it as a candidate; the number is Westley's.
5. **Benched against natural.** The share of benched ground is drawn per map from the seed and printed. A slider overrides it so both extremes can be seen.
6. **Landforms, batch 1.** Mesa, canyon and island chain blended into the noise as large shaped features. A selector: from the seed, or forced. Caldera, fjord and terraced massif are batch 2, not this pass.
7. **Walk view.** Flood from the city core over ground that is not water and not too steep at the current limit. Land a walker cannot reach is tinted. The HUD prints the share of land reachable, how many of the five layers are reachable, and the share of peaks (local high points on layers 4 and 5) reachable. About 70 percent of peaks reachable is the expectation (Q-192-03); report what the maps give, do not tune to it.
8. **Variety measure.** Choose one measure of landscape variety, print it per map, and say in the record which one and why (Q-187-02 asks you to choose and then ask him).

**Not in this pass:** the layout engine and places (pass 5), settlement growth, anything in the space kit.

**Deliver.** Screenshots at 1920x1080 in `docs/northstar/research/landscape_design/mockup/pass4/`, through `scripts/mockup_qa.sh` and a new `qa/pass4.json`: seeds 11, 12 and 13 in the visual, band, steep-30, steep-35 and walk views from the map height; one tactical close-up of a too-steep edge with the X cursor; seed 11 with each landform forced. A numbers table for seeds 11 to 16 (relief, step heights, share per layer, share too steep at each limit, reachable shares, generate time).

**Record.** Add a "Pass 4" section to `docs/northstar/research/landscape_design/README.md`: what was built, the numbers, the keys to fly it, and a short list of questions for Westley (the steepness figure, the minimum relief, what "unreasonably hard to reach" should measure, whether the variety is what he meant). Edit no other doc.

**Hand back.** Own worktree from origin/main, branch `push/proto-land-p4`, push and stop. Report under 30 lines: commit, files, the numbers table, anything not built and why.
