# Ground substrate in the C sim, stage 1: the terrain field (spec)

Written 2026-10-05 from the pre-flight scouts G1 (seams) and G2 (generator port). Approvals it rests on: the land mockup pass 6b ("approved for now with those markers", Westley 2026-10-05) and the walkers mockup ("looks great, approved"); "layout before landscape" relaxed for this substrate the same day. Rules: E-17 S-186 to S-190 (R-186-04, R-186-05, R-186-07), E-01 S-200 (R-200-01 to R-200-04), R-001-06; E-13 R-207-05 is stage 2.

## Scope

Stage 1 puts the terrain field into the sim and nothing else: a seeded, deterministic height field at 100 wu cells; per cell its band (layer 1 to 5), whether it is walkable, and the ground flag per layer; the slopes between bands; the ground expressed as blocked bits on the layers below the ground; hashed and saved; a lab loader. Stage 2 (later): walking movement kind, slope routing and the midline rule, ground blocking sight in ground eras, the era-kind switch. Stage 3: pipe frame and client drawing. Missions do not call the generator yet.

What is ported: the mockup's `field_map` noise and normalisation and `pass4_terrain` (landforms, relief, benching, slope analysis, band fit, cliff mask). What is NOT ported in stage 1: the layout shaping of pass 5 and pass 6 (pads, chokes, valleys, routes stamped into the height). Westley's marker is that the layout under the mockup is flawed and is being redesigned; the terrain must obey the new layout later (Q-191-04), so stage 1 ships terrain without a layout. Scale is "later polish" (his words); the relief numbers are carried over as provisional settings.

The ported field will not be bit-identical to the GDScript mockup (different noise and trig). The "look" lane gives Westley a side-by-side to approve or send back.

## Settings (provisional runtime settings; Westley owns the values)

| Setting | Value | Source |
|---|---|---|
| Cell size | 100 wu (fixed) | R-186-05 coarse grid; mockup spacing |
| Bands | 5 | R-200-01 |
| Steep limit | `OM_TP_TERRAIN_STEEP_DEG` = 35 | R-200-03, Q-189-02 (30 to 35); the approved mockups used 35 |
| Canvases | 8,000 / 16,000 / 24,000 in stage 1 (the mapgen blocked-bit grid is fixed at 280 cells a side = 28,000 wu; `om_terrain_generate` rejects a larger canvas with a nonzero code). 32,000 and 64,000 (S-195, S-214) need that grid widened: a later contract piece | archetype sizes |
| Relief | peaks 3,000 to 5,000 wu as the mockup | "scale later polish" |

## Contract piece (lands first, one agent, `push/terrain-base`)

`docs/northstar/spec_factory/signatures.toml` then `sig_table.py --emit`; module `terrain.c` unless noted:

- `int om_terrain_generate(om_world *w, uint64_t seed, double canvas_w, double canvas_h)`: fills the field; 0 on success; clears any old field; sets the mapgen canvas if unset and rejects a canvas that differs from the mapgen canvas (nonzero).
- `int om_terrain_present(const om_world *w)`.
- `double om_terrain_height_at(const om_world *w, double x, double y)` (wu; outside the canvas: 0).
- `int om_terrain_band_at(const om_world *w, double x, double y)` (1 to 5; 0 when absent or outside).
- `int om_terrain_walkable_at(const om_world *w, double x, double y)`.
- `int om_terrain_ground_at(const om_world *w, int layer, double x, double y)` (R-200-02: 1 on the ground's band only; on a slope cell, 1 on both bands it joins).
- `uint32_t om_terrain_band_heights(const om_world *w, double *out, uint32_t cap)` (the five band floors, R-190-04).
- `uint32_t om_terrain_slope_count(const om_world *w)`; `int om_terrain_slope_get(const om_world *w, uint32_t i, OMSlope *out)`; struct `OMSlope { double x0, y0 (bottom edge), x1, y1 (top edge), mx, my (midline), length; int32_t lower_band, upper_band; }` with `source_test = "tests/csim/test_E01_R001_06_slopes.py"`.
- `uint32_t om_terrain_cells(const om_world *w, uint32_t *w_cells, uint32_t *h_cells)`; `int om_terrain_cell_band(const om_world *w, uint32_t cx, uint32_t cy)` (for the look script and the lab: whole-grid reads without a million calls: `uint32_t om_terrain_dump_bands(const om_world *w, uint8_t *out, uint32_t cap)`).
- Tactical parameter `OM_TP_TERRAIN_STEEP_DEG`, appended last in the enum (default 35), `pp_contract.md` row, `conftest.py` member, count tests (the parameter-count tests are updated by the contract agent with a ledger row, as `TD-PING-param-count` was).
- `csrc/om_internal.h`: the terrain state struct (int32 fixed-point height in cm; band, walkable as uint8 arrays; slopes array with a named cap), a `terrain_state` pointer on `om_world` nulled and freed in `csrc/region.c`; prototypes `om_terrain_install_net_hooks`, `om_terrain_apply_ground(w)` (writes the blocked bits).
- `csrc/terrain.c` created with the generated stubs (every function returns 0 / absent).
- Checks as the lockstep base: `make OPT=-O2 WERROR=1`, `sig_table --check`, lints, csim failing ids equal to main's (plus the count tests), transport 277.

## Contract piece 2 (found by the query lane, 2026-10-06): a terrain save slot

The terrain field needs its own save slot: `csrc/tactical_mapgen.c` re-sets the mapgen slot's hooks at lazy allocation and at the end of its own read, so a wrapper on the mapgen slot is overwritten. Add to `csrc/om_internal.h` the three hook pointers `terrain_state_size`, `terrain_state_write`, `terrain_state_read` on `om_world` (nulled in `csrc/region.c` with the other slots, before the install calls) and to `csrc/save.c` a slot `OM_SAVE_SLOT_TERRAIN` = 10, written and parsed exactly as the mapgen slot is (length-prefixed; an empty slot is legal; the read runs on the shadow world first). The save format number stays 6 (no saves of format 6 exist outside today's tests; ledger row `TD-TERRAIN-save-slot`). The query lane then installs its hooks on that slot from `om_terrain_install_net_hooks`: blob = seed u64, cells_w, cells_h, five band floors (i32 cm), heights (i32 cm); walkable, slopes and bands re-derived on load; the read atomic (scratch, caps, install at the end). The two cell-count readings (canvas/100 against canvas/100 + 1) are settled by the field test: n = floor(canvas / 100) cells per side, noise sampled at cell corners.

## Lanes (from `push/terrain-base`; files disjoint; tests first by a different agent)

| Lane | Files | What |
|---|---|---|
| noise | `csrc/terrain_noise.c`, `tests/csim/test_E17_S186_noise_deterministic.py` | Integer-hash value noise (lattice, fixed-point interpolation), 1-D and 2-D, octaves; a table sine and cosine (named size); `isqrt` or IEEE `sqrt` only; no libm beyond `sqrt`; no world rng consumed (the field comes from the seed alone, R-186-04). Internal prototypes in `om_internal.h` belong to the contract piece: the contract agent declares `om_tn_value2(seed, x, y)`, `om_tn_sin/cos(angle_units)`, `om_tn_fbm2(...)` with fixed-point signatures the noise lane implements. Tests: same inputs same outputs across two processes; values bounded; octave weights sum; the sine table hits 0, 1, 0, -1 at the quarter points |
| gen | `csrc/terrain.c` (generation half, above a marker), `tests/csim/test_E17_S186_terrain_field.py` | Port of `field_map` noise, normalisation and edge bias, and `pass4_terrain` landforms (mesa, canyon, islands), relief enforcement, benching, cliff mask, band fit `clamp(floor((h - lo) / step), 0, 4)` over the five bands; fixed-point throughout; every mockup constant carried over as a named provisional define. Tests: byte-identical field for a seed in two processes; different seeds differ; every band has ground (R-200-01); heights inside the relief range; generation under 2 s at 24,000 (R-186-07 allows 5 s; measured) and under 1 s at 16,000; a 32,000 canvas is refused |
| query | `csrc/terrain.c` (query half, below the marker) | `band_at`, `walkable_at` (slope from the 4-direction footprint as the mockup, against `OM_TP_TERRAIN_STEEP_DEG`), `ground_at`, band heights, dumps, slopes (a slope = a run of walkable cells crossing a band boundary: bottom edge, top edge, midline, length; R-001-06), `om_terrain_apply_ground` (R-200-02: blocked bits set on layers 1..k-1 at every cell; cleared on regenerate), section-8 hash and save hooks below the net-hooks marker (format stays 6: no version-6 saves exist beyond today's tests; ledger row). Tests: `tests/csim/test_E01_S200_ground_is_the_layers.py` (R-200-01, -02; blocked bits agree with bands; `om_mapgen_cell_blocked` reads them), `test_E17_S189_steep_ground.py` (walkable iff slope at or below the parameter; raising the parameter never removes walkable cells), `test_E01_R001_06_slopes.py` (every slope joins adjacent bands, has positive length, midline between the edges; seeds 11 to 13 have slopes), save round trip and section hash equal after load |
| look | `scripts/terrain_look.py`, `docs/northstar/research/landscape_design/sim_port/` | Python over ctypes: for seeds 11, 12, 13 at 16,000 write a PPM/PNG of bands (the mockup's band colours), steep cells shaded, slopes marked; beside each, the mockup's screenshot of the same seed (`scenes/mockups/walkers/qa/` or a new shot from the walkers mockup); a page `README.md` with the pairs and the numbers (walkable share, largest connected region, band shares) for both. This is what Westley looks at |
| lab | `scripts/skilllab/engine.py` (bindings only), `tests/skilllab/integration/test_terrain_bindings_real.py` | `terrain_generate`, `terrain_band_at`, `terrain_walkable_at`, `terrain_dump_bands`; a fight on a generated field runs and its movement respects the blocked bits (a unit on layer 1 cannot enter a band-3 cell) |

Order: contract, gate; noise then gen then query (each tests first); look and lab after query; clerk merges to `push/terrain-land`, runs the gate, does not push to main.

## Limits, stop and kill rules

As the lockstep run: Sonnet, one step, own worktree `~/Projects/om-push/wt/terrain-<lane>`, at most 40 tool calls, build first, never `make clean`, stage by name, memory scope for anything long, kill only own pids, report once. Stop on: a recorded hash that moves (the field consumes no world rng, so none should), a symbol the spec does not list, a test that looks wrong, a file outside the lane, a number nobody gave. The run stops if the contract fails its gate or two lanes are dropped.
