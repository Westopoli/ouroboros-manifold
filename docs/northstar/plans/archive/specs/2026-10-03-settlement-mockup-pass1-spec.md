# Settlement mockup pass 1: a base that builds itself (prototype spec, 2026-10-03)

Prototype under `agile.md`, Prototype gate. One Doer. It may skip determinism, budgets and tests; it is never loaded by the game. Placeholder boxes only.

**What Westley must be able to judge.** Whether a base rising by itself reads as a spectacle, and by eye: which events should start a wave of building (Q-193-01), how many stages a lot goes through (Q-193-02), and whether armies always have a way through (Q-193-06). The rules are E-17 S-193 (R-193-01 to R-193-09); his direction is E-17 R-166-01. Read both first, and `docs/northstar/research/economy_design/settlement_generation_options.md`.

**Build, as a new scene in `scenes/mockups/settlement/`.** Use the landscape mockup's field map (`scenes/mockups/landscape/field_map.gd`) read-only for terrain, water, slope and the city core. Do not edit any file under `scenes/mockups/landscape/`; another prototype is changing them now. If you need something it does not expose, copy it into your own file.

1. **Growing density.** A density field that starts at the core and spreads a little each step, shaped by water, slope and distance from the core, so districts run along rivers, coasts and contour lines and never form rings.
2. **Lots and stages.** A lot rises a stage each time the density at its cell passes a threshold: marked ground, scaffold, built, dense. Four stages and their thresholds are your candidates; print them. A short rise animation between stages.
3. **Waves.** Three buttons named for candidate events (shipment arrives, expansion founded, season turns). Each triggers a wave in which a whole street goes up at once. The same wave for all three is fine; the labels are what he judges.
4. **Player placement.** A click places one large building. The self-built pieces under it are cleared and the pieces around it refill over the next seconds.
5. **Difficult ground.** On ground too steep for a normal lot, a different placeholder is built (a cliff dwelling, in its own colour), never nothing.
6. **Damage.** A key on the hovered area runs lots backward toward rubble; they rebuild afterwards.
7. **Paths.** Natural paths through the settlement stay clear, at least one formation wide (200 wu). Pick a simple method, say which, and draw the paths with a toggle.
8. **Time.** Speed 1x, 5x, 20x, and reset.

**Deliver.** Screenshots at 1920x1080 in `docs/legacy/research/settlement_mockup/pass1/`: start, after one minute and five minutes of growth, just after a wave, after placing a building, after damage, and the paths overlay. Piece counts and frame time. The command to run it.

**Record.** `docs/legacy/research/settlement_mockup/README.md`: what was built, the candidate numbers you picked, the keys, and the questions for Westley. Edit no other doc.

**Hand back.** Own worktree from origin/main, branch `push/proto-settlement-p1`, push and stop. Report under 30 lines: commit, files, numbers, anything not built and why.
