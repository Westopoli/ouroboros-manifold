# Galaxy bubble field and vast-space backdrop: spec and build plan (Architect, 2026-10-02)

## Context

The prototype's bubble shader loops over every system at every step for every faction. Measured on Westley's RTX 3060 (experiment branch `push/galaxy-field-experiment` 7b535246, report `scenes/mockups/galaxy/experiment/REPORT.md`): 36 to 60 ms per frame today, 75 to 138 ms at game size (400 systems, 15 factions). The bubbles are over 99% of the GPU frame; everything else is about 0.4 ms.

The experiment proved the replacement: the field computed once into a 3D grid by the graphics card, then drawn in one pass by stepping through the grid. Measured at game size: **0.5 ms at half resolution, 1.9 ms at full 1080p**, the same at every camera position and for both galaxy sizes. Refilling the grid after a change of owner takes 7 ms (96 grid).

Decisions (Westley, 2026-10-02): bubble budget 2 ms on the RTX 3060 at 400/15, 1080p; same smooth look; tests first with speed enforced; a Sonnet 5.5 builder works from a strong blueprint; vast space gets the dim wash, real-depth star layers and fading edges together. Real-GPU runs work window-free under Xvfb, so no windows open on his desktop.

Work stays in the prototype (`scenes/mockups/galaxy/`, worktree `~/Projects/om-push/wt/galaxy-before-shrink`) on a new branch `push/galaxy-field` cut from `push/mockup-galaxy-scale` 9404a62b. The experiment branch is reference only; nothing is merged from it wholesale. The live galaxy stays held until Westley approves the result.

## Blueprint (what the builder is handed)

Fixed by measurement, not left to the builder:

| Choice | Value | Why (measured) |
|---|---|---|
| Grid | 96 cells a side over a 128-unit cube | first surface within 0.05 units median, 0.2 at the 95th percentile; 64 is twice as bad; 128 costs 16 MB and buys little |
| Grid contents | highest net field among factions, that faction's seam term, that faction's id | matches exact formulas to 0.001 |
| Who fills it | the graphics card: one pass that runs today's field maths once per cell into a slice sheet, read back into a 3D texture | pass 1 to 2 ms, whole refill 7 ms |
| Refill | whole grid on any change of owner, at most once per frame however many systems changed | 7 ms is affordable at conquest rate; a partial refill saves nothing because readback and upload dominate |
| Drawing | one full-screen pass for all factions, 64 steps, half resolution | 0.5 ms; 32 steps shows streaks, 96 misses budget at full resolution |
| Skip map | none | measured slower at 3 of 4 camera positions because systems fill the volume |
| Memory | field as two half-float channels plus a one-byte id texture | 4.2 MB against 6.75 MB as built in the experiment |

Changed from the experiment, by my ruling:

1. **Crossing rule: the first surface of each faction, up to four factions per ray.** The experiment blended every surface crossing of the combined field, which added ridges inside large same-faction blobs that the approved look does not have (visible in `results/look/default_d120.jpg`). A new layer is drawn only when the ray first enters a faction it has not already drawn, whether it got there through open space or straight across a seam. This restores the approved look and is cheaper (crossings were the largest cost after steps).
2. **Significance is normalised the way the old code did it**, quirk included, so the first build is a like-for-like replacement. Tidying the quirk is a separate decision.
3. **The black patch** seen at the top of the 400-system overview is investigated and explained before anything else is tuned.
4. **Close-zoom shading** is checked at the overview opacity (0.5), where creases would show; the experiment only looked at 0.05.

Structure (one owner per file, each about one unit of work):
- `territory_field.gd`: owns the grid. Input: the full list of systems (position, significance, owner). Output: the field texture, the id texture, the palette. Knows nothing about cameras or drawing. Marks itself dirty on any owner change and refills once on the next frame.
- `shaders/field_bake.gdshader`: the per-cell field maths (lifted from `shell_metaball.gdshader`'s three field functions, evaluated for all factions in one loop over systems).
- `shaders/shell_field.gdshader`: the drawing pass.
- `shell_renderer.gd`: the half-resolution SubViewport and overlay (kept from `legacy_shell_renderer.gd`), zoom-band opacity, faction labels, the same `setup / teardown / get_faction_shell_count` surface so `galaxy_view.gd` changes by a few lines. `SHELL_RES_DIVISOR` stays as the hook for the manual quality setting.
- `legacy_shell_renderer.gd` and `shell_metaball.gdshader` are deleted in the same change. The Compatibility-renderer stand-in (flat billboards for the software QA render) is kept inside the new renderer.
- A reference implementation of the exact formulas in GDScript lives with the tests, not in the product.

## Steps

**Step 1: spec doc (me).** The blueprint above as `docs/northstar/plans/2026-10-02-galaxy-bubble-field-spec.md` on main, with the measured tables and the experiment files named as reference reading.

**Step 2: failing tests first (Engineer, `model: sonnet`), under `scenes/mockups/galaxy/tests/`, builder may not edit.** The experiment's `probe.gd` harness (back-to-back forced draws, device-name check, Xvfb launcher) is promoted into a kept tool `scripts/galaxy_perf.sh`; its measurement method is documented in the script because ordinary frame timing under Xvfb reads about 15 times too slow.

Headless checks (every iteration):
| Check | Requirement | Positive control |
|---|---|---|
| FIELD-EQ | grid versus exact formulas on 2,000 random rays: first surface within 0.1 units median and 0.4 at the 95th percentile; at most 2% of rays find a different first surface; no isolated bubble missed; seeds 11, 12, 13 and 400/15 | a grid filled with the wrong radius fails |
| FIELD-ORDER | grid identical whatever order systems were added (the old incomplete-rival bug) | old per-faction rival list fails |
| FIELD-CONQUEST | after an owner change the grid equals a fresh fill | skipping the refill fails |
| COST-SHAPE | drawing shader has no loop bounded by system or faction count and no per-system texture; at most 100 fetches per pixel worst case | old shader fails |
| ONE-DRAW | one shell draw at 4, 8 and 15 factions | old renderer fails |
| FIELD-MEM | field textures at most 5 MB | — |
| existing verify checks | still pass; a check that assumes one box per faction is changed only through a test-defect row | existing plants |

Real-GPU checks (window-free, each round after headless is green):
| Check | Requirement |
|---|---|
| DEVICE | log names the RTX 3060; llvmpipe or dummy renderer invalidates the run |
| SHADER-COMPILES | no shader error |
| SHELL-GPU | shell at most **2.0 ms at full 1080p** and at most **0.7 ms at half resolution** (the shipped default), at all four camera positions (120, 25, 7.5, inside a bubble), 400/15 |
| SHELL-SCALE | 400/15 within 15% of 219/4 |
| REFILL | grid refill after an owner change at most 12 ms |
| LOOK-LAYERS | on seed 11 at distance 120, no surface is drawn inside a faction's own blob: per-pixel layer count never exceeds the number of distinct factions along that ray (counted on the CPU from the grid) |
| SCREENSHOTS | saved beside the old shader's at the same four positions |

Thresholds other than the 2.0 ms are my proposals from the measured numbers plus headroom; Westley owns them.

**Step 3: build (Doer, `model: sonnet`).** Briefed with the spec, the experiment files as worked reference, the test commands, the file list and the order: `territory_field.gd` + bake shader until the headless field checks pass; then drawing shader + renderer until the GPU checks pass; then deletion of the legacy pair. Never edits tests; a suspected test defect comes back to me. Commits to `push/galaxy-field`, reports once with the final numbers. If a budget is missed it reports the best number and the limit; nothing is loosened.

**Step 4: look review.** I compare old and new screenshots at the four positions; then Westley views it with the usual command pointed at the new branch. His eye is the acceptance.

**Step 5: vast space (same pattern, after Step 4 so GPU timings are not disturbed).** Replaces the starfield and dust in `legacy_ambient_rig.gd`; rings, streams and core unchanged.
- Wash: a very dim, low-contrast, direction-only background, computed once, no animation.
- Depth layers: four static star layers, one draw each, at about 100, 250, 800 and 2,500 units; star size grows with depth so stars stay 1 to 3 pixels; camera far plane raised to cover them.
- Fading edges: density and brightness fall off smoothly in every layer; nothing stops at a radius.
- Dust that follows the camera: one wrapping volume of motes centred on the camera, fading near its faces; replaces the radius-60 dust.
- Not in this pass: distant galaxy impostors, soft zoom limit.
- Tests first: layer count and depth ratios (each at least 2.5 times the previous); star count per radial shell falls monotonically over each layer's outer half; outermost layer at least 5 times beyond the camera's reach; far plane covers it; wrap rule keeps every mote within half a box of the camera for 1,000 random camera positions; old starfield and dust emitters gone; at most 6 added draws. Real GPU: backdrop adds at most 0.5 ms at all four positions; shaders compile; screenshots while orbiting at 120 and 25.
- Acceptance: Westley's eye, plus my check for a visible radius, layers moving in lock-step, and shimmering sub-pixel stars.

**Step 6: close out.** Rulings addendum recording these decisions and the measured numbers; perf audit doc gets a "Measured on RTX 3060" section; after Westley approves the look, one message to the coordinator with the files and constants the live galaxy takes, new `pieces.toml` rows, and the galaxy speed budget written into E-13 in the same commit; memory file updated.

## Verification

1. New tests fail against the old system (positive controls live) before any build.
2. `scripts/mockup_verify.sh galaxy` prints `VERIFY OK`; `scripts/galaxy_perf.sh` names the RTX 3060 and reports the shell within budget at all four positions for 400/15.
3. Old/new screenshots side by side; Westley views with `OM_GODOT_GUI=1 godot --path ~/Projects/om-push/wt/galaxy-before-shrink res://scenes/mockups/galaxy/galaxy_mockup.tscn` on the new branch.
4. Same sequence for the backdrop with its 0.5 ms budget.

## Not covered, known

- Only the RTX 3060 is measured. Entry cards are estimated at about 2.2 times slower (about 1.1 ms at half resolution).
- A real windowed run (frame pacing, compositor) is not measured by the harness; Westley's own viewing is the check.
- The faceted mesh mode for weak hardware is a later piece off the same grid.
- Connecting-line batching and per-frame script cost (about 1.2 ms) are separate later pieces.
