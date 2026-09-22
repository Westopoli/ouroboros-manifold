# HANDOFF BRIEF — P2 landscape mockup in Godot

Self-contained. Handed to an implementor chat 2026-09-21. Program context: `2026-09-21-factory-program.md`.

## Context

Rung P2 of the prototype ladder (landscape and biome generation) opens with a design phase Westley joins and a Godot mockup he approves before any test is authored. The design conversation is done; its record is `docs/northstar/research/landscape_design/README.md` in the ouroboros repo (read it first: Westley's verbatim answers, the design as it stands, the four reference images under `docs/bible/references/E-17/E-17-5..8*.png` with rows in `references/E-17/notes.md`). This brief turns that design into one throwaway Godot scene Westley can fly around, so he can say "yes, that's it" or send it back. Nothing in it is product code; nothing in it becomes a card. After approval the epics (E-17, E-16, E-19) are rewritten by the design lane and Stage 5 tests are authored; the mockup then stays in the repo as visual ground truth.

The design in one paragraph. One generator produces a **field map**: a canvas, a spine of typed nodes, zones with borders between them, and continuous gradients (obstacle, cover, elevation, interference, water, population, wealth). It never names a rock or a house. One **placer** reads the field map plus a **kit** (an era's mapping from field values and border kinds to placeholder pieces) and instantiates pieces. Two kits ship in the mockup: **Greek** (the classical walled city of the reference images) and **Settled Reach** (an asteroid station cluster: walls are hull sections, water is vacuum, bridges are docking spines). Same seed, same field map, toggle the kit, only the rendering changes (this is bible rule R-147-03). The city *is* the battlefield: the objective is the city core, staging is the farmland outside the walls, chokepoints are gates and bridges, vantages are the acropolis hill. Scale: 20 to 30 tactical screens, with three zoom bands (micro, tactical, map view).

## Rules for the implementor

- If you are an Opus or Fable chat: plan and review, Sonnet sub-agents build; ask Westley about his Claude usage before a batch of more than two doers. If you are a Sonnet chat: do the work yourself, spawn no sub-agents.
- This is a mockup: placeholder primitives only (boxes, cylinders, prisms, planes, flat colours). No asset pipeline, no imported models, no textures beyond vertex colour and flat shading. "Playful, bright, Age of Empires Online" is a palette and a silhouette register, not an art task.
- All new files under `scenes/mockups/landscape/` in `~/Projects/ouroboros-manifold`, plus screenshots under `docs/northstar/research/landscape_design/mockup/`. Touch nothing else: not `csrc/`, `simulation/`, `tests/`, `docs/bible/`, `docs/northstar/` (except the screenshot folder and one status line in `landscape_design/README.md` under "Next step"), not the existing `scenes/` files, not `project.godot` unless the Godot facts section below says the version line must change (ask Westley first if so).
- Godot only, GDScript only, no C, no Python. No Ollama calls (the GPU belongs to the Agora chain); the mockup itself may use the GPU when Westley runs it.
- Commit on `main` and push after each working step (scene skeleton; generator; placer with Greek kit; Settled Reach kit; camera bands; map view; screenshots). Trailer `Co-Authored-By: Claude <model> <noreply@anthropic.com>`. Never stage files you did not create.
- The mockup must not name an era in any script identifier: kits are data (`kits/greek.json`, `kits/settled_reach.json`); the placer reads kit names from a list. This is bible rule R-145-01 and it is the point of the two-kit demonstration.
- Deterministic: the generator takes an integer seed and uses its own `RandomNumberGenerator` instance seeded from it, never the global RNG or wall clock. Same seed, same piece list (checked in verification).
- When something in the design is under-defined, do not decide: build the simplest thing that shows the question and list it in the finishing report as a question with two or three candidate answers.

## Godot facts (reconnaissance 2026-09-21)

- Binary: `~/.local/bin/godot`, `4.6.3.stable.official`. `project.godot` declares `config/features=PackedStringArray("4.7", "Forward Plus")`. `godot --headless --path . --quit` opens the project with exit 0 and no version warning, so leave `project.godot` alone; if the editor refuses the mockup scene on the feature tag, stop and ask Westley.
- Opening the project spawns the old Python sim through `autoload/tactical_bridge.gd` and warns about a hard-coded mac path in `scenes/tactical/perf_logger.gd:23`. Harmless for the mockup. Run the mockup scene directly (`godot --path . scenes/mockups/landscape/landscape_mockup.tscn`) and do not depend on any autoload; the scene must work if every autoload were removed.
- Existing tactical camera to copy the feel from, not to reuse: `scenes/tactical/tactical.gd` (`PAN_SPEED=1500`, `ZOOM_MIN=150`, `ZOOM_MAX=12000`, fixed 65° pitch from `_update_camera`, edge scroll zone 60 px, wheel zoom in `_input`). Copy the pan and edge-scroll logic into `camera_rig.gd`; change the pitch to about 50° for the tactical band and ease it to 90° in the map band; raise the ceiling to 40,000.
- Existing renderer for reference only: `scenes/tactical/terrain_renderer.gd` (`MultiMeshInstance3D` scatter in `_scatter_environment` at line 226 and `_scatter_cover_asteroids` at 296; canvas is world-space XZ with Y up, default `[8000, 8000]`). Same axis convention in the mockup: X and Z on the ground, Y up, one wu = one Godot unit.
- Placeholder conventions already in the repo: `BoxMesh`, `CylinderMesh`, `TorusMesh`, `SphereMesh`; an unresolved asset falls back to a `SphereMesh` (line 354). The mockup's magenta box for an unknown kit mesh follows the same idea.
- Colours already in the repo: `autoload/theme_constants.gd` `ERA_ACCENTS` (`settled_reach=#4a9eb8`, `roman=#c9a84c`); `assets/eras/settled_reach/manifest.json` `era_accent_color` and `faction_colors` (`0=#4099FF`, `1=#FF4738`). Use the two faction colours for the placeholder unit blocks and the two accents as each kit's HUD accent. The Greek kit's world palette is new; take it from the reference images (terracotta roofs, pale stone, cypress green, wheat, turquoise water).
- The Python layout library (`simulation/layout_library/layout_01_fortress_ridge.json`: `zones[].position_ratio`, `node_type`, `edges[]`) is the shape to echo in the mockup's one hand-authored skeleton: store it as `skeleton.json` with `position_ratio` per node so the report can say what a growing library would look like. Do not import or call the Python generator.
- No headless test runner exists in the main tree; `verify.gd` (below) is run with `godot --headless --path . --script scenes/mockups/landscape/verify.gd` and must `quit()` with an exit code. Headless exit prints RID and ObjectDB leak warnings from the dummy renderer; those are noise, not failures.

## What to build

Directory `scenes/mockups/landscape/`:

```
landscape_mockup.tscn        root scene: world, camera, HUD
field_map.gd                 seeded generator -> FieldMap (pure data, no nodes)
placer.gd                    FieldMap + kit -> piece instances (MultiMesh per piece type)
ground.gd                    heightfield mesh from elevation, vertex-coloured by biome blend
camera_rig.gd                RTS camera with three zoom bands
map_view.gd                  overlay for the map-view band (grid, icons, order arrows)
hud.gd                       seed box, regenerate, kit toggle, band label, stability slider
kits/greek.json
kits/settled_reach.json
kits/README.md               the kit schema in ten lines
```

### 1. `field_map.gd`: the generator

Input: `seed: int`, `canvas: float` (default 16,000 wu, medium canvas per E-17 R-116-01), `stability: float` in [0, 100] (default 60; feeds R-115-01's idea that a war-torn region is rougher). Output: a `FieldMap` object with:

- `canvas`: side length in wu.
- `nodes`: array of `{type, pos}` with type in the nine E-17 R-113-01 types (`objective, staging, transit, chokepoint, flank_route, vantage, hazard_anchor, spawn_point, extraction`). Use **one hand-authored skeleton** (positions as fractions of canvas, jittered up to 3 percent per node, per R-112-03) shaped like the reference images: objective (city core) on a rise inside a river bend near the coast; two staging nodes on the farmland side; two chokepoints where the wall meets the two land approaches and one at the river bridge; a flank route around the hill; one vantage on the hill; one hazard anchor in the marsh; spawn points on the far side; extraction on the coast. Q-119-02 (layout method) is open: one skeleton is all the mockup needs and the report says so.
- `grid`: a sample grid at 100 wu spacing (161 × 161 for 16,000 wu; E-17's scale requirement names 100 wu) holding per cell: `obstacle, cover, elevation, interference, water, population, wealth` in [0, 1], and `zone` (int) and `district` (int).
- Gradients are built the way E-17 R-114-02/03 say: sources with position, radius, intensity, falloff, summed and clamped. Use the R-114-03 anchor values (obstacle 0.85 r600 at chokepoints, elevation 0.90 r700 at vantage, interference 0.75 r500 at hazard anchors, cover 0.55 r550 at chokepoints, and so on) plus low-frequency value noise (Godot `FastNoiseLite`, seeded) at small amplitude so fields read as terrain, not discs. Water: a coast along one edge and a river from the hills to the coast that passes the objective; represent as a signed distance so the coastline and river banks are smooth. Population: peaks at the objective, falls off with distance and with elevation, zero over water; wealth: a second peak offset toward the coast (harbor), scaled by `stability`. Stability lowers interference and raises cover when high; the slider in the HUD should visibly change the map.
- Elevation is **terraced**: after summing, quantize to five levels (E-01 says always five layers) with a smoothed step so terraces read as cliffs at the steps and slopes elsewhere. The hill under the vantage must reach level 4 or 5; the coast is level 0.
- `zone` per cell: the biome patch, argmax over three seeded noise fields (in Greek terms: forest, farmland, rock; in Settled Reach terms: dust, ore field, ice; the generator calls them `zone_a/b/c`). Never named in the generator.
- `district` per cell: 0 = wild, 1..4 = population bands (thresholds 0.2, 0.4, 0.6, 0.8), so the city has a dense core ringed by looser districts, and the core sits inside the wall.
- `borders`: polylines traced with marching squares over the grid for three kinds: `coast` (water 0.5 isoline), `cliff` (terrace level change), `wall` (district ≥ 2 boundary against district ≤ 1; the outer wall). Each polyline carries its kind. `crossings`: where a border polyline passes within 300 wu of a chokepoint node, mark a crossing on that border of kind `gate` (wall) or `bridge` (coast/river) or `pass` (cliff); the placer draws the border with a gap and a crossing piece there.
- A `hash()` method: a stable integer over the piece-relevant data (nodes, borders, a sampled subset of the grid), used by the verification script.

Budget: generation under 500 ms on Westley's machine in the editor (the E-17 target of 50 ms is for the C generator; the mockup only has to be fast enough to regenerate on a key press).

### 2. Kits and the placer

A kit is JSON, schema (put it in `kits/README.md`):

```json
{
  "name": "greek",
  "palette": {"sky": "#8fd3ff", "water": "#2aa7d6", "zone_a": "#4f9a3c", "zone_b": "#c9c04a", "zone_c": "#9c8f7a", "cliff": "#7d6d5a"},
  "water_is": "surface",            // "surface" draws a plane at level 0; "void" draws nothing and darkens the sky
  "terrain": [
    {"when": {"obstacle": [0.6, 1.0]}, "piece": "rock",  "density": 0.8, "mesh": "prism", "size": [120, 200], "color": "#8a7f70"},
    {"when": {"cover": [0.4, 1.0], "zone": "zone_a"}, "piece": "tree", "density": 1.0, "mesh": "cone_on_stick", "size": [60, 110], "color": "#2f7a2f"},
    {"when": {"zone": "zone_b", "district": 0}, "piece": "field_row", "density": 0.3, "mesh": "flat_box", "size": [200, 60], "color": "#e0c84a"}
  ],
  "city": [
    {"when": {"district": 1}, "piece": "hut",    "density": 0.25, "mesh": "box",      "size": [60, 40],  "color": "#c86a3c"},
    {"when": {"district": 2}, "piece": "house",  "density": 0.5,  "mesh": "box_gable","size": [80, 60],  "color": "#d9773f"},
    {"when": {"district": 3}, "piece": "villa",  "density": 0.6,  "mesh": "box_gable","size": [120, 80], "color": "#e28a4a"},
    {"when": {"district": 4}, "piece": "temple", "density": 0.3,  "mesh": "colonnade","size": [240, 140],"color": "#f2e9d0"}
  ],
  "borders": {
    "wall":  {"mesh": "wall_segment", "height": 90,  "color": "#bfb39a", "crossing": {"gate":   {"mesh": "gate_arch",  "color": "#a89a7a"}}},
    "coast": {"mesh": "none",        "crossing": {"bridge": {"mesh": "bridge_arches", "color": "#bfb39a"}}},
    "cliff": {"mesh": "cliff_face",  "height": 0,   "color": "#7d6d5a", "crossing": {"pass":   {"mesh": "stair_ramp", "color": "#9c8f7a"}}}
  },
  "nodes": {"objective": {"mesh": "acropolis", "color": "#f2e9d0"}, "staging": {"mesh": "camp_ring", "color": "#8a4a3c"}},
  "backdrop": {"mesh": "mountain_range", "color": "#e8eef5", "distance": 30000}
}
```

`mesh` names are a fixed vocabulary the placer implements once with primitives (box, box_gable, prism, cone_on_stick, flat_box, colonnade, wall_segment, gate_arch, bridge_arches, cliff_face, stair_ramp, acropolis, camp_ring, mountain_range, and for the second kit: hab_pod, hab_ring, spire, hull_segment, airlock, docking_spine, ore_chunk, derelict, ice_shard, asteroid_backdrop). A kit may reference only names from that vocabulary; an unknown name draws a magenta box (the bible's placeholder rule, R-146-03).

The placer, for every grid cell, evaluates the `terrain` rules and then the `city` rules (city rules win inside district ≥ 1), draws a seeded Bernoulli at `density` scaled by the cell's fields, and jitters the piece inside the cell; pieces stand on the terraced ground height. Borders become chains of `mesh` segments along the polyline, with the gap and crossing piece at each crossing. Nodes get their marker piece. Everything is `MultiMeshInstance3D`, one per (piece, kit), so 20 to 30 screens of pieces render at 60 fps on an RTX 3060 at the tactical band; if not, cull by distance (the far band draws nothing but ground and borders anyway).

Settled Reach kit: `water_is: "void"`, ground is drawn only where elevation ≥ level 1 (terraces become asteroid bodies floating over void), zone colours are dust/ore/ice greys and blues, city pieces are hab pods and rings and a spire for the core, the wall is hull segments with airlocks, the river/coast crossing is a docking spine, the backdrop is an asteroid field and a nebula-coloured sky. The mockup must make the same wall, gate, bridge and hill obviously the same *place* in both kits.

### 3. Ground

`ground.gd` builds one `ArrayMesh` (or a few chunks) from the elevation grid: vertex height = terrace level × 250 wu with the smoothed step; vertex colour = blend of the zone palette weighted by the three zone noise fields (this is the "no visible tile seams" claim, R-119-01, so blending is per vertex, not per tile); a darker band on steep faces (cliffs). Water is a flat plane at level 0 when the kit says `surface`. Under the Settled Reach kit, cells with water > 0.5 or level 0 are dropped from the mesh.

### 4. Camera and the three bands

`camera_rig.gd`: classic RTS camera (pitch about 50°, yaw fixed, WASD and edge pan, wheel zoom, canvas-bounded per E-16 R-103-02). Three bands by camera height:

| Band | Height (wu) | What changes |
|---|---|---|
| micro | 300 to 1,200 | pieces at full detail; a few placeholder unit blocks (two colours, ten each) walk a fixed loop near a gate so scale reads |
| tactical | 1,200 to 6,000 | the default; whole districts and the wall in view; this is the Age of Empires Online view and the screenshot Westley judges first |
| map | 6,000 to 40,000 | pitch eases to 90° top-down, pieces fade out, `map_view.gd` overlay appears: 10 × 10 grid with letters and numbers, borders as clean lines, water as flat colour, unit groups as chevron icons, objective circles at objective nodes; click a group then click a point draws a curved order arrow (no movement; the arrow is the mockup) |

Band label in the HUD. Zoom is continuous; the band is a state the HUD shows and the renderer uses for LOD.

### 5. HUD

Seed spinbox and Regenerate (R key); kit toggle (Tab) cycling the kits list; stability slider (0 to 100); band label; a piece count. Nothing else.

### 6. Screenshots for Westley

After each kit and band works, save PNGs to `docs/northstar/research/landscape_design/mockup/`: `<kit>_<band>_seed<N>.png` for both kits and all three bands at seed 11 and seed 12 (12 images), plus `greek_tactical_seed11_stability20.png` and `_stability90.png`. Godot: `get_viewport().get_texture().get_image().save_png(...)` from a debug key (F12) in the HUD script. These are the review artefacts; commit them.

## What the report must answer

For Westley, in plain language with the screenshots:

1. Does the same seed under both kits read as the same place? (Point at the wall, gate, bridge, hill in both.)
2. Does the tactical band read as Age of Empires Online in register: bright, blocky, instantly readable place types?
3. Does elevation read? Do the terraces feel like height at micro and tactical bands?
4. Does the map band work as a command surface: are groups and borders legible at 20 to 30 screens?
5. Does the city read as the battlefield: core, districts, wall, gates, fields, staging outside?
6. Frame rate at each band on Westley's RTX 3060; piece counts; generation time.
7. Every place the design was under-defined and what you did (candidates, no decisions): expected at least the layout skeleton (Q-119-02), the terrace height (250 wu is a guess), the district thresholds, what a `pass` looks like, and how the map-band arrow should behave.
8. Anything that argues the one-generator-two-mappers idea does not hold (for example, if city placement needed information the field map does not carry).

Do not recommend design changes; report evidence and questions. The design lane and Westley decide.

## Verification

- `godot --headless --path . --script scenes/mockups/landscape/verify.gd` (write it, `extends SceneTree`, `_init` runs the checks and calls `quit(code)`): generates seed 11 twice, asserts equal `hash()`; generates seed 12, asserts different; loads both kits and asserts every `mesh` name is in the placer's vocabulary; prints piece counts per kit. Exit code 0.
- Both kits at all three bands render without errors in the editor output; the 14 screenshots exist and are committed.
- `git status --short` shows only `scenes/mockups/landscape/**` and `docs/northstar/research/landscape_design/mockup/**` before each commit; `git log` on `main` has the step commits; the existing `scenes/` and `tests/` are untouched (`git diff --stat main~N -- scenes/tactical tests` empty).
- The design lane's E-02 baseline is unaffected because nothing under `csrc/` or `tests/` changed.

---
