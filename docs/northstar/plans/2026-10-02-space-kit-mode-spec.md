# Landscape mockup: space kit mode (spec)

Design-phase mockup, 2026-10-02. Westley: "I like the second kit mode in the landscape mockup suggestion". Built by a Sonnet Doer against this spec; the architect designs and reviews, Westley flies it. Not game code: no C, no tests, no bible rules. Design record: `docs/northstar/research/space_landscape/README.md` (flag Q-166-02).

## 1. What it shows

A space battlefield as five open-or-blocked layers, in Westley's words "like a boolean hyperplane (ice sheet)": open space is crossable, blocked space is filled with asteroids. One block of three-dimensional noise cut into five slices, so asteroids are bodies that span layers and openings line up into shafts. A density slider runs from a light field (mostly open) to a very heavy one (corridors and tunnels). Every open region is reachable; where the noise seals a pocket, a tunnel is cut and shown. Places where a unit could change layer are marked where they are scarce.

## 2. Files

| File | Change |
|---|---|
| `scenes/mockups/landscape/field_map_space.gd` | New. `class_name SpaceFieldMap extends FieldMap`. Overrides `generate`, adds the mask data. All generation is pure: no scene, node or engine-noise calls. |
| `scenes/mockups/landscape/kits/space.json` | New kit, name `space`. Uses only the fixed mesh vocabulary. |
| `scenes/mockups/landscape/placer.gd` | Small additions: a border may carry `layer`, a cell rule may carry `layer_tint`; pieces for a layered map are placed at the layer's height. |
| `scenes/mockups/landscape/hud.gd` | Kit `space` builds a `SpaceFieldMap`; density slider; layer focus keys; labels. |
| `scenes/mockups/landscape/ground.gd` | Builds nothing when the field map is a `SpaceFieldMap` (space has no ground). |
| `scenes/mockups/landscape/landscape_mockup.gd` | `qa_state` gains the space fields; two new plants. |
| `scenes/mockups/landscape/qa/checklist.md` | Rows for the space mode. |

`map_view.gd` and `camera_rig.gd` are reused unchanged if the duck-typed members they read (`nodes`, `borders`, `rivers`, `crossings`, `canvas`, `dim`, `grid`) are present; `rivers` is empty in space.

## 3. The generator, exactly

Constants: `SPACING = 100.0` (inherited), `LAYERS = 5`, `LAYER_HEIGHT_WU = 1000.0` (layer k, 1-based, is drawn at `(k - 1) * 1000`), `CLEAR_RADIUS_WU = 600.0`, `MIN_POCKET_CELLS = 40`, `TUNNEL_HALF_WIDTH_CELLS = 1`, `CROSSING_MARK_MAX_CELLS = 50`.

`generate(p_seed: int, p_canvas: float = 24000.0, p_density: float = 35.0)`; density is the percent of cells to block, clamped to [0, 90].

### 3.1 Noise, written by hand

No `FastNoiseLite`. The point is a generator the C simulation can copy line for line.

- Hash: `hash32(ix, iy, iz, seed) -> int` in [0, 2^32): combine the four ints with multiply-xor-shift steps (for example the pattern `h = ix * 0x8da6b343; h ^= iy * 0xd8163841; h ^= iz * 0xcb1ab31f; h ^= seed; h ^= h >> 13; h *= 0x5bd1e995; h ^= h >> 15`, kept in 32 bits with `& 0xFFFFFFFF` after each multiply). Value at a lattice point is `hash32(...) / 4294967296.0`.
- Value noise in three dimensions: for a sample at `(x, y, z)` in lattice units, take the eight corner values and interpolate with `t * t * (3 - 2 * t)` on each axis.
- Two octaves summed: lattice `(5, 5, 2)` cells across `(canvas, canvas, 5 layers)` with weight 0.65, and lattice `(14, 14, 4)` with weight 0.35. The layer axis samples at `z = (k - 0.5) / 5 * lattice_depth`.
- Plant `space-independent-layers`: use a different seed per layer and the z sample fixed at 0.5, so layers are unrelated. This is the comparison Westley may want to see.

### 3.2 Threshold

Collect every sample into one array, sort a copy, take the value at index `floor(density / 100 * n)`; cells at or below it are blocked. Result: `masks[k]` as a `PackedByteArray` of `dim * dim` entries, 1 open, 0 blocked, for k in 0..4.

### 3.3 Layout places, kept

The layout library stays (Westley, 2026-10-02), so the mockup keeps a minimal spine and clears space for it: objective at the canvas centre; two spawn points at 15 percent and 85 percent of the canvas on the diagonal; two staging nodes 1,500 wu from each spawn toward the centre; one vantage at the centre of the quarter farthest from both spawns. Each is a node in `nodes` with the existing type names. Within `CLEAR_RADIUS_WU` of each node every layer is set open.

### 3.4 Reachability and tunnels

- Flood fill over open cells with six neighbours: the four in-plane neighbours on the same layer, and the cell directly above and below where both are open.
- The main region is the one containing the objective's cell on layer 1 (index 0).
- Every other region with fewer than `MIN_POCKET_CELLS` cells is filled solid (set blocked).
- Every other region of that size or larger gets a tunnel: from the region's cell nearest the objective (in plane distance), walk a straight line on that region's layer toward the objective's cell (Bresenham), opening each cell and its in-plane neighbours within `TUNNEL_HALF_WIDTH_CELLS`, until a cell of the main region is opened or reached. Record each tunnel as a polyline of world points with its layer in `tunnels`.
- Repeat the flood fill once after carving; any region still cut off is reported in `qa_state` and left as it is.
- Plant `space-no-carve`: skip the filling and carving, so pockets stay. Positive control for the check.

### 3.5 Crossings

A crossing cell is one open on layer k and k + 1. Group crossing cells per layer pair into in-plane connected clusters. A cluster is marked (drawn) only if it has at most `CROSSING_MARK_MAX_CELLS` cells; big open areas are obviously crossable and are not cluttered with marks. `crossings` holds one entry per marked cluster: `{point, kind = "shaft", layer_from, layer_to}`. `crossing_pct` per layer pair is recorded for `qa_state`.

### 3.6 What the inherited members hold

- `grid`: every cell as in `FieldMap` with `elevation = 0.0`, `water = 0.0`, `zone = 0`, `district = 0`, `population = 0.0`, `wealth = 0.0`, `slope = 0.0`, `interference = 0.0`, `cover = 0.0`, and `obstacle` equal to the share of layers blocked at that cell (0.0 to 1.0), so the map view and anything reading `obstacle` still gets a meaningful value.
- `borders`: for each layer k, the marching-squares outline of `masks[k]` at threshold 0.5, each border `{kind = "asteroid", layer = k + 1, points}`. Reuse `_march_squares` and `_stitch_segments`.
- `nodes`, `crossings` as above; `rivers = []`.
- New: `masks`, `tunnels`, `density`, `layer_stats` (per layer: blocked share, open share), `pockets_filled`, `tunnels_cut`, `regions_unreachable_after`.
- `compute_hash()` is overridden to hash the masks, the nodes and the tunnels, so a seed and a density give one hash.

## 4. Drawing

- **Blocked cells.** For each layer, each blocked cell: a piece from the kit's `terrain` rule `{"when": {"blocked": true}}` placed at the layer's height plus `_ground_offset`. To keep instance counts sane: an edge cell (any in-plane neighbour open, or the layer above or below open there) always gets a piece; an interior cell gets one with density 0.25. Jitter as today.
- **Layer tint.** Each layer's pieces are tinted: the rule's colour mixed toward white by `0.12 * (k - 1)`, so higher layers read lighter, like ice toward the surface.
- **Borders.** The asteroid outline per layer, drawn with the kit's `borders.asteroid` mesh (`ice_shard`, height 300) at the layer's height, along the polyline as today's border placement does, no crossing gaps.
- **Tunnels.** Each tunnel polyline drawn with the kit's `tunnel` mesh (`flat_box`, colour `#3fd0ff`) laid along the path at the layer's height, so a cut tunnel reads as a lit corridor.
- **Crossing marks.** One `hab_ring` (colour `#ffd23f`) at each marked cluster's point, at the lower layer's height plus 500, so it sits between the two layers.
- **Nodes.** As today, at layer 1's height.
- **Backdrop.** The kit's `asteroid_backdrop` as today. Sky from the palette; no ground mesh; no water.
- **Layer focus.** Keys 1 to 5 focus a layer; 0 shows all equally. Pieces on unfocused layers are drawn with their colour darkened by 55 percent. Implemented by rebuilding the per-layer MultiMesh colours, not by regenerating. The HUD shows "Focus: layer k" or "Focus: all".

## 5. HUD

- Kit toggle gains `space`. When the kit is `space`, `_regenerate` builds a `SpaceFieldMap` with the density; otherwise unchanged.
- Density slider 0 to 90, label "Density: N% blocked", debounced on drag end exactly like stability (stability is hidden when the kit is space; density is hidden otherwise).
- Labels: per-layer blocked percent, pockets filled, tunnels cut, regions still unreachable (should be 0), marked crossings.
- Existing seed, regenerate, canvas toggle and band controls unchanged.

## 6. QA

- `PLANTS` gains `space-no-carve` and `space-independent-layers`.
- `qa_state` gains, when the kit is space: `density`, `layer_blocked_pct` (array of 5), `pockets_filled`, `tunnels_cut`, `regions_unreachable_after`, `crossing_pct` (array of 4), `crossing_marks`, `focus_layer`, and `hash` already covers the masks.
- `qa_set` gains `density` and `focus`.
- The checklist gets rows: same seed and density give the same hash on two runs; `space-no-carve` raises `regions_unreachable_after` above 0 at density 70 on at least one of seeds 11 to 16; with carving it is 0 for every seed 11 to 16 at densities 15, 35, 55, 70; `space-independent-layers` lowers the mean `crossing_pct` at density 70 compared with the default; the kit switch between `greek`, `settled_reach` and `space` works in any order without error.

## 7. Acceptance for Westley's flight

Screenshots, seeds 11 and 12, densities 15, 35, 55 and 70, at the micro, tactical and map bands, plus one at tactical with layer 3 focused, saved under `docs/northstar/research/space_landscape/mockup/` (not committed: generated files stay out of git; the architect copies a selection into the repo for the review). What he is asked to judge: does a light field read as open space with a few obstacles; does a heavy field read as corridors and tunnels; do shafts between layers read as the places that matter; does the layer focus make one layer readable; is anything annoying.

## 8. Rules for the Doer

- Build exactly this. Where the spec is silent, choose the smallest thing and say so in the report; do not add features.
- No engine noise or random calls in `field_map_space.gd` except the hash above; the placer may keep using its seeded `RandomNumberGenerator` as today.
- Keep each file's style. Comments only where a choice is not obvious.
- Run `scripts/mockup_verify.sh landscape` if Godot is on this machine (`/Applications/Godot.app/Contents/MacOS/Godot`); if the script cannot find it, say so rather than editing the script.
- No git commands; no commit. Do not touch tests, `csrc/`, the bible or the register. Report once at the end, caveman-terse, ten lines at most: files changed with line counts, what the verify said, timings for one regenerate at canvas 24,000 and density 55, anything chosen where the spec was silent, anything not done.

---

# Pass 2 (2026-10-02, after Westley's first flight)

His review is verbatim in `docs/northstar/research/space_landscape/README.md`. Pass 1 stays as the base; this section changes the generator's shape, the drawing, and the clearing. Everything in sections 2 to 8 not contradicted here still holds.

## P2.1 The picture to match

Fractured sea ice seen from above: large plates with straight, broken edges; narrow dark channels between plates; fields of small fragments; open water; now and then one large irregular mass. Five such sheets, each from its own seed, stacked, make a tight, thick field over the whole map. Blocked space is a plate, open space is water. Nothing else is drawn.

## P2.2 Generator: plates, not blobs

Replace section 3.1 to 3.2 for the default mode. Keep the hand-written hash and value noise (the noise now modulates, it no longer thresholds).

1. **Per layer, its own seed:** `layer_seed = p_seed + k * LAYER_SEED_STEP`. Layers are independent by default. Keep the plant `space-independent-layers` as a no-op alias and add plant `space-coherent-layers` that uses one seed with the z-offset of pass 1 for comparison.
2. **Plates by jittered lattice (Worley).** Lay a lattice of plate centres over the canvas with cell size `PLATE_CELL_WU` (default 1,600 wu); jitter each centre within its cell by the hash. For each map cell find the nearest and second-nearest centres (search the 3 by 3 neighbouring lattice cells) with plain Euclidean distance, giving `d1`, `d2` and the nearest centre's id. A map cell belongs to plate `id`.
3. **Channels.** A map cell is open water where `d2 - d1 < CHANNEL_WU` (default 160 wu, so channels are one to two cells wide). This gives straight broken edges between plates.
4. **Open water pools.** Each plate is kept or dropped by its own hash against the density: a plate is dropped (all its cells open) when `hash01(plate) > density / 100`. Dropped plates adjacent to each other merge into pools.
5. **Rubble.** Inside dropped plates, a second lattice with cell size `RUBBLE_CELL_WU` (default 400 wu) makes small fragments: a rubble plate is kept when `hash01(rubble) < RUBBLE_SHARE` (default 0.35), with its own channel width `RUBBLE_CHANNEL_WU` (default 100). Rubble is also blocked space.
6. **Stochastic variation across the map.** Sample the pass 1 two-octave noise per layer (lattice 5 by 5 and 14 by 14, weights 0.65 and 0.35, in two dimensions) as `v` in [0, 1] and use it to vary the field: plate cell size scales by `0.6 + 0.8 * v` (small plates where v is low, large where high), and the drop test uses `density / 100 + (v - 0.5) * 0.3`, so some areas are packed and some are open. This is the existing engine's stochasticity put to use.
7. **The odd large mass.** With probability 0.5 per layer by hash, one plate chosen by hash is grown: every plate whose centre lies within 2,200 wu of it is merged into it and the channels between them are closed.
8. **Edges.** Erode each kept plate's outline by removing a boundary cell where `hash01(cell) < 0.15`, so edges are broken rather than exact.
9. Density, as before, is the slider's percent blocked, but it is now the share of plates kept, not a quantile of noise. Record the actual blocked share per layer as before.

## P2.3 Clearing for layout places

No discs. For each node, drop the plate containing its cell and every plate whose centre lies within `CLEAR_RADIUS_WU` of the node, so the clearing is a pool of plate shapes. Rubble is not generated inside these pools.

## P2.4 Reachability

As section 3.4, with one change: a cut-off region is joined to the main region by dropping plates, not by a straight tunnel. From the region's nearest cell, walk the plate adjacency graph (plates sharing a channel) toward the objective's plate by breadth-first search and drop every plate on the path; a dropped plate is recorded in `tunnels` as its outline so the HUD can still count and show cuts. Small pockets are still filled solid.

## P2.5 Drawing: binary sheets

Replace section 4.

- **Plates.** Every blocked cell of layer k is one flat square tile, `flat_box` sized `[100, PLATE_THICKNESS_WU]` (thickness 60), at height `(k - 1) * LAYER_GAP_WU`, no jitter, so plates read as continuous sheets with straight edges. Tile colour per layer from the kit's `layers` array (five colours, pale blue-white for layer 1 grading to brighter white-blue for layer 5; the kit gives the five hex values). No shards, no asteroid pieces, no borders drawn.
- **Layer gap.** `LAYER_GAP_WU` default 1,000 (Q-246-01 (a), DRAFT-space-layer-gap), so from the tactical camera the sheets separate. The HUD gets a gap slider (400 to 3,000) so Westley can find the spacing that reads.
- **Water.** Under each layer, nothing. Under layer 1 only, a single dark plane the size of the canvas at height -40, colour from the kit's `palette.water`, so open space reads as water in the photo's way. Fog or sky unchanged.
- **The large mass** is drawn with the same tiles, in the kit's `mass` colour (dark grey-brown).
- **Rubble** uses the plate tiles at half thickness.
- **Crossings.** Keep the marks, but make them a flat `hab_ring` 240 wu across in the kit's `shaft` colour, at the lower layer's height plus half the gap, visible at the map band.
- **Cut plates** are outlined with the `tunnel` colour as a thin flat frame (four thin `flat_box` strips around the dropped plate's bounding box), not a corridor.
- **Layer focus** as before: keys 1 to 5 darken the other layers by 55 percent; 0 shows all.
- **Top-down button.** The HUD gets a "Top-down" toggle that sets the camera pitch to straight down at the current height, so the stacked sheets can be compared with the photo; the existing bands and the height floor are unaffected when it is off.

## P2.6 HUD and QA additions

- Sliders: density (as before), layer gap, plate size (`PLATE_CELL_WU` 800 to 3,200). Labels: per-layer blocked percent, plates per layer, plates dropped for clearing, plates dropped for reachability, rubble share.
- `qa_state` adds `plate_cell_wu`, `layer_gap_wu`, `plates_per_layer` (array), `plates_cut`, `top_down`.
- `qa_set` adds `plate_cell`, `layer_gap`, `top_down`.
- Checklist: the pass 1 rows hold; add: no cleared area is a disc (at density 70, seed 11, the cells open within 600 wu of the objective are not all open: at least one blocked cell inside the radius); top-down screenshots at densities 15, 35, 55, 70 for seeds 11 and 12, plus tactical and map, plus one tactical with layer 3 focused.

## P2.7 Rules for the Doer

As section 8. Keep the pass 1 generator reachable through the plant `space-noise-blobs` for comparison, so the two can be flown side by side. Report once, ten lines at most.

---

# Pass 3 (2026-10-02, after the architect's read of pass 2)

Pass 2 screenshots: `docs/northstar/research/space_landscape/mockup/pass2/`. What they show against the photo: plates have ragged, stair-stepped outlines, not straight broken edges, because the plate lattice was warped per row and column and because every plate is drawn as 100 wu tiles; rubble covers 47 percent of the map at 15 percent density, so a light field reads as static, not as a few floes on open water; crossing marks number in the hundreds and clutter every view; and the top-down view shows the union of all five layers, so it reads as one dense sheet whatever the density. Pass 3 fixes these four things and changes nothing else.

## P3.1 True plates with straight edges

- Plate centres: a square lattice of cell size `PLATE_CELL_WU` with each centre jittered by up to 45 percent of the cell size in x and y by hash. No row or column warping. The noise `v` scales only the jitter and the drop test, not the lattice.
- Plate membership by nearest centre (Euclidean, 3 by 3 neighbourhood), as pass 2 intended. Channels by `d2 - d1 < CHANNEL_WU`.
- **Draw each plate as one polygon, not as tiles.** For each kept plate build its cell polygon: start from the lattice cell's square expanded by one cell size, clip it by the perpendicular bisector half-plane against each of the eight neighbouring centres, then inset every edge by `CHANNEL_WU / 2`. Erode by moving each vertex toward the centroid by a hashed amount up to 12 percent of its distance, so edges stay straight and corners vary. Triangulate as a fan from the centroid and emit it into one `ArrayMesh` per layer (top face plus a 60 wu skirt, flat shaded), coloured by the layer. Rubble plates the same way on their finer lattice. The cell grid (`masks`) is still filled from the plate polygons by point-in-polygon on each cell centre, so play data and picture agree.
- The large mass: union of the merged plates' polygons is not needed; draw the merged plates as plates in the `mass` colour with their shared channels closed (skip the inset on edges shared inside the mass).

## P3.2 Rubble where it belongs

- Rubble is generated only in dropped plates that lie next to a kept plate (share a channel with one), and its keep share is `RUBBLE_SHARE * v` where `v` is the noise at the rubble plate's centre, so rubble gathers at the edges of packed areas and open water stays open. Pools of dropped plates farther from any kept plate get no rubble.
- At density 15 the blocked share per layer, rubble included, must land between 10 and 25 percent; at 70 between 60 and 80. Report the measured values.

## P3.3 Crossing marks

- Marks off by default. Key `C` toggles them. The HUD still counts crossings.
- When on, one mark per cluster at most, and only clusters of 8 to 50 cells (bigger ones are obvious, smaller ones are noise).

## P3.4 Reading the layers

- In top-down with a layer focused (keys 1 to 5), the other layers are hidden, not darkened. With focus 0 in top-down, layers are drawn with the lower layers lighter and the upper layers more saturated, and each higher layer is offset 60 wu in x and y so stacked edges show as a stepped outline rather than a union.
- Outside top-down, focus darkens as before.
- A "Solo" label on the HUD shows when only one layer is visible.

## P3.5 QA

- `qa_state` adds `plate_polygon_count` per layer and `crossing_marks_shown`.
- Checklist adds the blocked-share bands of P3.2 as measured rows, and the determinism and carving rows from pass 2 hold.
- The QA script takes top-down shots at density 15, 35, 55 and 70 for seeds 11 and 12 with focus 0, and at density 55 with focus 3, plus tactical at density 55.

## P3.6 Rules for the Doer

As section 8 and P2.7. Pass 1 and pass 2 generators may be removed; only the plate generator of this pass needs to stay (drop the `space-noise-blobs` plant). Report once, ten lines at most, with the measured blocked shares.

---

# Pass 4 (2026-10-03, after Westley's review of pass 3)

His review is verbatim in `docs/northstar/research/space_landscape/README.md`. Pass 3 is the base. Six changes, nothing else.

## P4.1 Size variety

- Plate size varies across the map. The lattice stays regular (so membership search stays 3 by 3), but each lattice centre is kept or merged by a size field: sample the two-octave noise `u` at the lattice cell's middle; where `u` is below `0.5 - SPREAD / 2` the centre is removed, and the cells that would have belonged to it go to the nearest surviving centre, which makes a large floe; where `u` is above `0.5 + SPREAD / 2` the cell is split into four centres (jittered sub-lattice at half size), which makes small floes. `SPREAD` is a HUD slider "Size spread" from 0 (even, as pass 3) to 1, default 0.6. Membership is computed against the surviving centre set with a 5 by 5 neighbourhood so removed centres do not leave holes.
- Rubble as pass 3.

## P4.2 Density variety

- The drop test's swing by the noise rises from `(v - 0.5) * 0.3` to `(v - 0.5) * DENSITY_SWING`, with `DENSITY_SWING` a HUD slider "Density swing" from 0 to 1.2, default 0.8, so some areas are packed and some are nearly open water at the same slider density. The measured blocked share per layer must still average within 10 points of the slider over seeds 11 to 16 at densities 15, 35, 55 and 70; if the swing pushes the average off, rescale the keep share so it lands, and report the before and after.

## P4.3 Shared density across layers

- Toggle "Shared density" (HUD button and `qa_set("shared_density", bool)`), default on. On: every layer samples the same density noise `v` (seeded from `p_seed` alone), while plate centres, jitter, size field and erosion still use the layer's own seed, so packed regions stack over packed regions and each layer keeps its own plate pattern. Off: as pass 3, independent.
- Report mean `crossing_pct` at density 70 with the toggle on and off, seeds 11 to 16.

## P4.4 Fill the gap

- For every cell blocked on layer k and also blocked on layer k + 1, the layer k geometry at that cell is extruded from layer k's height up to layer k + 1's height, so the two read as one solid body. Implement by building, per layer, a second mesh: for each plate, the set of its cells that are blocked above forms one or more regions; emit each region as a flat-shaded extruded polygon (trace the region's outline on the cell grid with the existing marching squares, extrude the outline as a wall from layer k's top to layer k + 1's bottom, colour it the layer's colour darkened 20 percent). Cells blocked only on their own layer keep the thin plate. Rubble included.
- Top-down with all layers shown still steps the layers by 60 wu; with a layer focused, solo, the extrusion of the focused layer is shown too.

## P4.5 Gap

- The layer gap slider stays, range widened to 200 to 3,000, default 1,000.

## P4.6 Defect

- Crossing marks must not be drawn when the HUD says they are off, in any view. Add `qa_set("marks", bool)` and `qa_state.crossing_marks_shown` must agree with what is drawn.

## P4.7 QA

- `qa_state` adds `size_spread`, `density_swing`, `shared_density`, `filled_cells_per_pair` (array of 4: cells blocked on both layers of each pair).
- `qa_set` adds `size_spread`, `density_swing`, `shared_density`, `marks`.
- Checklist adds: the blocked-share averages of P4.2; `shared_density` on raises mean `filled_cells_per_pair` over seeds 11 to 16 at density 55 compared with off; marks off draws no marks (screenshot pixel check is not required; the state field suffices).
- The QA script takes, for seeds 11 and 12 at densities 15, 35, 55 and 70: top-down with all layers; top-down with layer 3 focused; and one angled shot from above the stack (camera height 9,000, pitch as the tactical band gives) so the filled bodies can be seen from the side; plus density 55 with shared density off for comparison.

## P4.8 Rules for the Doer

As section 8, P2.7 and P3.6. Report once, ten lines at most, with the measured averages and the shared-on and shared-off comparison.

---

# Pass 5 (2026-10-03, after Westley's passage-width decisions)

Decisions, verbatim, in `docs/northstar/research/space_landscape/README.md` ("Decisions (2026-10-03): passage widths"). Pass 4 is the base. The mockup now shows two maps on top of the pretty one: what ordinary units can pass and what small craft can pass.

## P5.1 Two functional masks

- `MIN_PASSAGE_WU = 300.0` (ordinary units; Westley's number). `SMALL_PASSAGE_WU = 100.0` (placeholder until Q-166-05).
- After the pass 4 generation produces the fine mask per layer (`masks[k]`, 1 open), derive two more per layer:
  - `small_masks[k]`: the fine mask closed at the small passage: a cell is open only if an open disc of diameter `SMALL_PASSAGE_WU` fits over it (morphological opening of the open set with a disc of radius 50 wu, on the 100 wu grid that is a 1-cell radius: keep an open cell only if all four in-plane neighbours are open; use the structuring element the grid gives, say so).
  - `masks_ordinary[k]`: the fine mask opened with a disc of radius `MIN_PASSAGE_WU / 2` (150 wu, radius 1.5 cells: the 3 by 3 block), **except inside small-craft sections**, where cells keep the `small_masks` value. A cell is open for ordinary units only if a 3 by 3 block of open cells covers it.
- The clearing around layout nodes and the reachability check and plate dropping run on `masks_ordinary`; a map must be connected for ordinary units. Report `regions_unreachable_after` for ordinary units, and separately the share of small-craft-open cells that ordinary units cannot reach (`small_only_pct` per layer).

## P5.2 Small-craft sections

- `SMALL_SHARE` slider "Small-craft share" from 0 to 20 percent, default 7.5. Sections are chosen per layer as contiguous batches of plates: pick seed plates by hash where the pass 4 noise `v` is in its top quartile (packed areas, where fine gaps exist), grow each by adding adjacent plates (sharing a channel) until the batch reaches `BATCH_PLATES` (default 6) plates, and stop adding batches when the sections' cells reach `SMALL_SHARE` of the layer's cells. Record `small_section_pct` per layer.
- Toggle "Sections near layout" (default off): when on, seed plates are instead the plates nearest the objective, staging and vantage nodes, so the sections sit where the layout matters. Both are kept so Westley can compare.
- Inside a section the fine fracture of pass 4 is the functional map for small craft (P5.1). Outside, fine detail is visual only.

## P5.3 Views

- Key `V` cycles the view: `visual` (pass 4 drawing), `ordinary` (draws `masks_ordinary`: blocked cells as flat tiles in a muted grey, open as nothing; the pretty mesh hidden), `small` (draws `small_masks` the same way, with small-craft-only cells, open for small craft and blocked for ordinary units, in the kit's `small_only` colour, an orange). HUD shows the view name. `qa_set("view", name)`.
- Section outlines: in every view, each small-craft section is outlined with a thin flat frame in the `small_only` colour at its layer's height, so Westley sees where the batches are.
- Layer focus, top-down and solo work in every view.

## P5.4 Triangle fix

- Gap fill: instead of one closed slab per filled cell, group the filled cells per layer into in-plane connected regions, trace each region's outline with the existing marching squares, and emit only the outline wall from the layer's top to the layer above's bottom (the wall pass already does this; the per-cell slabs are removed). Where the region's top would show (it never does, the plate above covers it), emit nothing.
- Target: at seed 11, canvas 24,000, density 70, under 500,000 triangles in the visual view. Report triangles at densities 15, 55 and 70 in the visual view, measured the way `qa/_tri_count` did (sum of surface triangles over the generated children), and put a `triangles` field in `qa_state`.

## P5.5 QA

- `qa_state` adds `view`, `small_share`, `small_section_pct` (array of 5), `small_only_pct` (array of 5), `regions_unreachable_after` now for ordinary units, `triangles`, `sections_near_layout`.
- `qa_set` adds `view`, `small_share`, `sections_near_layout`.
- Checklist adds: ordinary-unit reachability 0 on seeds 11 to 16 at densities 15, 35, 55, 70; `small_section_pct` within 2 points of the slider on average; triangles under 500,000 at density 70; `small_only_pct` above 0 at density 55 on every seed.
- The QA script takes, for seeds 11 and 12 at densities 35 and 55: top-down with layer 3 focused in each of the three views; angled all-layers in the visual view; plus density 55 with "Sections near layout" on, top-down, layer 3, small view.

## P5.6 Rules for the Doer

As section 8 and the pass rules before. Do not delete the pass 4 fracture code; it is what runs inside the sections. Report once, ten lines at most, with the measured reachability, section shares, small-only shares and triangle counts.

---

# Pass 6 (2026-10-03)

Two changes, nothing else. Westley saw the teal frames and asked what they were; the answer led to both.

## P6.1 Debug frames off by default

- The frames around plates dropped for reachability (teal, kit `tunnel` colour) and the clearing frames, if any, are hidden by default. Key `F` toggles them; `qa_set("frames", bool)`; `qa_state.frames_shown`. The small-craft section outline (orange) stays visible in every view, since it is landscape, not debug.

## P6.2 Join by widening a channel, not by dropping plates

- When a region is cut off from the main region on the ordinary-unit map, join it by **widening one channel**: find the pair of cells (one in the region, one in the main region) with the shortest in-plane distance across blocked cells on that layer, trace the straight line between them, and open every cell within `MIN_PASSAGE_WU / 2` (150 wu, the 3 by 3 block) of the line. The fine mask and the plate polygons are updated to match: cells opened this way are cut out of the plates they belonged to (clip the polygon by the widened channel's rectangle, or re-derive the polygon's cells from the mask; say which). Repeat until no region of `MIN_POCKET_CELLS` or more remains cut off, with the same cap on iterations as today. Small pockets are still filled solid.
- Plate dropping stays available behind a HUD toggle "Join: widen | drop" (default widen) and `qa_set("join", "widen"|"drop")`, so the two can be compared on the same seed.
- Report, seeds 11 to 16, densities 35, 55 and 70, both modes: blocked share per layer, plates dropped, channels widened, cells opened by joining, `regions_unreachable_after` (must be 0 in both).

## P6.3 Side-by-side

- The QA script takes, for seed 11 at densities 35 and 55 and seed 12 at density 55, the top-down layer 3 visual view with join = drop and join = widen, same camera, frames off, so the architect can lay them side by side. Name them `<seed>_d<density>_drop.png` and `<seed>_d<density>_widen.png`.

## P6.4 Rules

As before. Report once, eight lines at most, with the table from P6.2.
