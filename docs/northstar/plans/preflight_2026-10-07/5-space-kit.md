# Pre-flight scout 5-space-kit (2026-10-07, Sonnet, read-only)

Scout 5, lane D (space landscape). Read-only; the worktree at `~/Projects/om-push/wt/pf-vg5` is removed. The worktree was on origin/main `a612d1c8`.

**1. The space kit generator and how it draws**
- **Location:** `scenes/mockups/landscape/field_map_space.gd`, 1520 lines, `class SpaceFieldMap extends FieldMap`. It is already on origin/main, byte-identical to the copies on `push/proto-land-iter` and `mac/prototypes`. The drawing is in `placer.gd:238-336` (`_place_sheets`, `place_view`). The kit file is `kits/space.json`.
- **Inputs:** `generate(seed, canvas = 24000, density = 35)` at `field_map_space.gd:149`. Tunables are plain members at `:105-125`: `plate_cell_wu` 1600, `layer_gap_wu` 1000, `size_spread`, `density_swing`, `shared_density`, `join_mode` (widen or drop), `small_share` 7.5, `sections_near_layout`. The layout nodes come from `_build_nodes` (`:327`), a fixed set on the canvas diagonal: objective, 2 spawns, 2 staging, 1 vantage.
- **Output per layer (5 layers):**
  - `masks[k]`: 100 wu cells, open or blocked.
  - `kinds[k]`: plate, mass or rubble.
  - `plate_polys[k]`: straight-edged polygons with a kind, 190 to 530 per layer at pass 3.
  - `fill_cells`, `walls[k]`, `tunnels`, `crossing_pct`, `section_frames`.
  - `masks_ordinary` (300 wu passage) and `small_masks` (100 wu, a placeholder until Q-166-05).
  - It does not produce lanes or cover discs. A guaranteed route to the objective comes from a carve step: widen a channel or drop plates.
- **Drawing:** 3D, Godot `MeshInstance3D`. Each layer is up to 4 opaque flat-colour sheets (plates and rubble, mass, and two wall meshes, `CULL_DISABLED`), at y = (k-1) × 1000 wu. A plate is a fan from its centroid with a 60 wu skirt. Layer focus, a solo top-down view and the functional views run by recolouring and hiding meshes, with no regeneration. The live view `scenes/tactical_c/tactical_view.gd` is a 672-line `Node2D`, so a 3D sheet view does not exist in-game yet.

**2. Sim side today**
- `om_map_generate`, `_gradients`, `_spine` are STUBs (`csrc/tactical_mapgen.c:495-508`). `om_map_add_layer_restriction_zone` is a STUB (`:352`).
- A live mission lays out a fixed map in `om_mission_instantiate_map` (`csrc/mission.c:2388-2418`): canvas, objective node, one cover disc, two spawn points and structure slots. There are no layer masks and no era branch.
- **Frame `map`** (`docs/architecture.md:260`): `canvas`, `nodes[]`, `cover[{x,y,r,h}]`, `obstacles[{x,y,r}]`. It has no masks or polygons.
- **Reusable sim primitive:** `blocked_bits` in `tactical_mapgen.c:184`, one bit per 100 wu cell per layer. It is written by `om_map_block_rect` (`:832`) and `om_mapgen_cell_set_density` (`:282`), the call `csrc/terrain.c:1051` uses. It is read by routing, `fog.c:332-385` (sight, lower layer of the pair) and `om_map_sample_layer_accessibility`. It is saved and net-hashed (`:1019`), and `om_map_clear` wipes it per mission. A space generator therefore needs no new blocking contract, only a writer.
- **`scripts/skilllab/maps.py` (216 lines) is not the same vocabulary.** It makes axis-aligned rectangles with a layer range (kinds block, wall, lane) and cover discs, on a 4000 wu canvas with Python `random`. The kit's polygons reduce to the same sim primitive (blocked cells per layer), but the lab does not use them.
- **Ground precedent** (terrain stage 3 spec): `terrain_dump` frame at `csrc/pipe/om_pipe.c:2324`, with `c_bridge.gd` and `terrain_layer.gd` consumers. Stage 3a edits the same `mission.c` function, so lane D must serialise after it.

**3. What a C port needs**
- **Randomness:** none from the engine. Only the hand-written `hash32` (`:259`) plus value noise. The file header says "the C simulation can copy this file line for line".
- **Float use:** only + − × /, `sqrt` (via `normalized`, `distance_to`), floor, ceil, round, lerp. `libm_lint` allows `sqrt`, `floor`, `ceil`, `round` and `fabs`. `Makefile:28` builds with `-ffp-contract=off -fno-fast-math`, so double C is deterministic across platforms. `terrain_noise.c` (Q16 table sin) is the integer precedent, but this generator does not need it.
- **Bit-exact with the mockup: no, not guaranteed.**
  - GDScript `Vector2` is float32 in standard Godot builds, while the noise arrays are float64. Polygon clipping happens in float32, and the cell masks are rasterised from those polygons.
  - Matching it exactly would mean emulating float32 and Godot's compiler FMA behaviour.
  - The mockup's grid also has 241 points per side (`dim = canvas/100 + 1`), against the sim's 240 cells.
  - `compute_hash` uses Godot `hash()`, which is not portable.
  - Treat the C port as the authority. The mockup becomes a statistical reference: blocked share per density, 0 unreachable regions, hash stable per seed.
- **Size:** full file about 20 units of ~100 lines. Sim-minimum (masks plus carve, skipping sections, crossings and walls) is about 1000 lines, so about 10 to 12 units. Rough function sizes: `_build_plate_layer` 245, `_widen_channel` 70, `_build_sections` 66, `_main_nearest` 58, `_label_regions` 54.
- **Client agreement:** if the client regenerated the look from the seed, it would diverge from the sim at boundary cells. Two safe routes:
  - **Dump masks and kinds** (like `terrain_dump`), about 36 KB packed. The client draws from them, and they also survive a save and load, since the bits are saved and polygons are not. The risk is stair-stepped edges, which Westley rejected in pass 2.
  - **Also export polygons.** Estimated at about 60k numbers, roughly 400 KB of JSON, once per mission.

**4. Stories and flags**
- **No space-landscape story exists.** S-166 is land, and E-17 line 24 says "no story here covers it". The only space-era statements are R-188-05, R-114-04, R-190-05 and S-196 (R-196-01 to -05).
- **S-001** (R-001-04): the binary mask per layer. The player sees blocked layers and detours.
- **S-007:** cover height blocks sight by layer. The kit's plates do not carry a height. Sight is blocked by the fog.c cell check (R-098-02) instead.
- **Q-STAGE3-03** is open, yet the programme says "→ yes".
- **Q-S3-01** (vision tube) is open, and its options page T3 is not built.
- **Q-166-02** is open ("design continues"), and so are Q-166-05 (small craft size) and Q-150-02.
- **Stale doc:** R-188-05 says all five layers are open at every position on a space map. That contradicts the approved kit and needs rewriting.

**5. Owner rows and collisions**
- `csrc/tactical_mapgen.c`: PP-mapgen (pending). B15m is attached.
- `csrc/mission.c`: B9 (pending), plus stage 3a's edit to the same function.
- `csrc/terrain.c` and `terrain_noise.c`: TERRAIN-1 (pending).
- `csrc/ouroboros_sim.h`, `signatures.toml`, `docs/architecture.md`: PP-contract (pending), A94, SPEEDCAP and others.
- `csrc/pipe/om_pipe.c`: T1 (attached).
- `autoload/c_bridge.gd` and `scenes/tactical_c/**`: C5, C8 and others (attached), and lane A shares the view.
- `scenes/mockups/landscape/*.gd`: no owner except `qa/**` (MK-harness).

**Lane D piece list (proposed, in order)**
1. **Contract:** a space-field dump verb and frame, either a new verb or `terrain_dump` extended, plus `om_space_field_*` signatures. Frame size added to the budget probe. Owners are PP-contract, `docs/architecture.md` and `om_internal.h`.
2. **Sim, 3 to 4 pieces in a new file** (`csrc/space_field.c`, new owner row): hash and noise, plate lattice and polygons, rasterise and carve, masks written to `blocked_bits`. Optional: sections and small masks, if the small craft is in scope.
3. **Mission wiring** in `mission.c`: generate in a space era after `om_map_set_canvas`, with nodes, spawns and structure slots cleared. Queue after stage 3a.
4. **Pipe:** the dump handler in `om_pipe.c`.
5. **Client:** `c_bridge` decode, then a `space_layer` drawing in `tactical_c`, 2D or 3D per the flag below. Queue after lane A's view structure.
6. **Tests:** a positive control (carve off gives unreachable regions, as the `space-no-carve` plant does), isolation, integration, a wiring check from `mission_start` to the frame, and a C-versus-mockup statistics comparison.

**Open flags to rule before launch**
1. Answer Q-STAGE3-03 (yes or no) and give Q-166-02 closing status.
2. Authority and drawing method: masks only (stair-step risk), or masks plus polygons in the dump, or the client regenerating the look (not recommended).
3. Is lane D's client 2D (like stage 3d's `ImageTexture` per layer, top-down with a focus layer) or 3D sheets? The 3D view is lane C's and not yet built. The camera and vision tube (Q-S3-01) block any 3D reading of five opaque sheets.
4. Layout nodes: the mockup's diagonal nodes against the mission's edge-midpoint spawns and structure slots, and the 600 wu clear radius. Does it clear discs around structure slots too?
5. Unit spawn layer, and whether a unit may sit in a blocked cell.
6. What S-007 means for plates (a height in layers, or a per-layer mask only).
7. Rewrite R-188-05 and E-17 line 24, and the `cover_asteroids` section of `architecture.md` (dead legacy).
8. The 240 against 241 grid decision, small-craft scope (Q-166-05), and whether the `blocked_bits` save format needs a version bump (it already stores bits).
9. Does the lab (`maps.py`) get the kit as a map family? Out of scope unless Westley says so.
