# HANDOFF BRIEF — P3 objectives mockup

Self-contained. Handed to an implementor 2026-09-22. Sibling briefs: `2026-09-22-mockup-qa-harness.md` (the harness you use), `2026-09-21-p2-landscape-mockup.md` (the shape to copy).

## Context

Rung P3 of the prototype ladder (`docs/northstar/PLAN.md:164`): "Mission generator places objectives; objectives satisfiable; markers visible and named." Epic E-10, Round 1 stories S-073 (ten archetypes, R-073-01's table), S-075 (one primary objective of five kinds: hold_zone, destroy_targets, escort_to_extraction, survive_duration, eliminate_force; R-075-01 to R-075-07), and the spirit of `S-P01` (the auto-resolved card while the tactical slice is unbuilt). Read `docs/bible/epics/E-10-missions.md` lines 44 to 70 and 86 to 101 first. Round 1 uses one primary objective and no secondaries (`docs/legacy/mvp/feature_mvps.md`, E-10 block).

The E-10 "Obviously working in 60 seconds" text (line 22 of the epic) puts a frontier under telegraphed attack, selects (frontier, defensive_stand), briefs it in three sections, and plays a hold. This mockup shows the tactical half of that: given an archetype, the objective of the right kind is placed at the right kind of place on a generated map, it is visibly marked and named on the ground and in the HUD, its progress is legible, and the placement is satisfiable (reachable, distinct from the player's spawn, within the mission's time). References: `docs/bible/references/E-10/notes.md` says the briefing and debrief screens are missing; there is no marker reference either. Judge against the 60-second paragraph and the reference row 08 in `references/E-17/notes.md` (the map view with objective circles, `E-17-8-wows-map-view.png`).

The map's places come from the landscape generator's node list (nine node types: objective, staging, transit, chokepoint, flank_route, vantage, hazard_anchor, spawn_point, extraction), dumped once to JSON so this mockup shares the landscape's vocabulary without loading its code.

## Rules for the implementor

- If you are an Opus or Fable chat: plan and review, Sonnet sub-agents build; ask Westley about his Claude usage before a batch of more than two doers. If you are a Sonnet chat: do the work yourself, spawn no sub-agents.
- You are in a git worktree on branch `mockup/objectives`. Commit there after each working step with the trailer `Co-Authored-By: Claude <model> <noreply@anthropic.com>`. Do not push; the design chat merges into `main`. Never stage files you did not create or edit for this brief. Never check out another branch.
- Touch only `scenes/mockups/objectives/**` and `docs/northstar/research/mockups/objectives/**`. Nothing else: not `csrc/`, `simulation/`, `tests/`, `docs/bible/`, other `docs/northstar/`, other `scenes/`, `scenes/mockups/_shared/` (if the harness is broken, stop and report; do not patch it), `project.godot`.
- This is a mockup: placeholder primitives only (boxes, cylinders, prisms, planes, quads, flat colours, `Label3D`, `Control._draw`). No imported models, no textures beyond vertex colour and flat shading. GDScript only. No autoload dependency and no dependency on any other scene: the scene must work if every autoload were removed. You may copy code from the legacy files named under "Godot facts" into your directory and you may reference `theme/fonts/*.ttf` by `res://` path; you may not `preload` or `load` anything outside your directory except `res://scenes/mockups/_shared/qa_driver.gd` and `qa_plants.gd`.
- Renderer parity: your QA renders run under the Compatibility renderer on software GL; Westley views Forward+ on an RTX 3060. Use only what looks the same in both: `StandardMaterial3D` (vertex colour as albedo is fine), `ArrayMesh`/`ImmediateMesh`, `MultiMeshInstance3D`, `Label3D`, one `DirectionalLight3D`, `WorldEnvironment` sky, ambient and depth fog, `CanvasLayer`, `CPUParticles3D`. Do not use SDFGI, VoxelGI, volumetric fog, SSR, SSAO, SSIL, glow, decals, `GPUParticles3D`, or screen-texture shaders.
- No era named in any script identifier or node name (bible rule R-145-01). Where the era shows it is data under `kits/` or `fixtures/`.
- Deterministic: every random draw comes from your own `RandomNumberGenerator` seeded from an integer seed; never the global RNG, never the wall clock. Same seed, same state hash, same pixels.
- **Never set `DISPLAY` yourself and never use `:0` or `:1`.** Every windowed run goes through `scripts/mockup_qa.sh`, which creates a private Xvfb. The GPU belongs to the Agora chain.
- No docstrings or comments except the `# plant: <id>` line above each check in `verify.gd`. Minimal, direct code.
- When something in this brief is under-defined, do not decide: build the simplest thing that shows the question and list it in the finishing report with two or three candidate answers.

## Godot facts (reconnaissance 2026-09-22)

- Binary `~/.local/bin/godot`, `4.6.3.stable.official`. Project root is the repo root. `project.godot` declares Forward+, 1920x1080, fullscreen, stretch `canvas_items`/`expand`, no `[input]` map (use raw keycodes as the landscape mockup does). Nineteen autoloads run on any `--path .` scene launch; one spawns the Python sim and warns about a mac path; harmless. `--script` SceneTree mode loads no autoloads.
- Scene convention: a short `.tscn` (root node with your root script, a `QADriver` child with `res://scenes/mockups/_shared/qa_driver.gd`, and whatever nodes you need) plus scripts. Every mockup scene in this repo is launched by path, never as the main scene. Westley's command is `~/.local/bin/godot --scene scenes/mockups/objectives/objectives_mockup.tscn` from the repo root; keep that name.
- The harness (read `scenes/mockups/_shared/README.md` first): `scripts/mockup_verify.sh objectives [--plant id]` runs your `verify.gd` headless; `scripts/mockup_qa.sh run objectives <script.json> <outdir> [--res 1280x720] [--plant id]` runs the scene under Xvfb with `--fixed-fps 30` and replays a JSON action list (`wait_frames`, `move`, `click`, `click_node`, `drag`, `wheel`, `key`, `key_down`, `key_up`, `call`, `seed`, `plant`, `pause`, `screenshot`, `state`, `tree`, `wait_file`); `scripts/mockup_qa.sh diff a.png b.png` prints the fraction of differing pixels; `scripts/mockup_qa.sh scan <outdir>` writes `errors.txt`, `shots.txt`, `marks.txt`. Your scene root must implement the contract: `const PLANTS: Array[String]`, `qa_state() -> Dictionary` (JSON-safe, canonical from data, never from HUD labels; always `seed`, `hash`, `timing_ms`, `regen_count` plus the keys named below), `qa_plant(id) -> bool`, `qa_seed(n)`, and the optional `qa_set(name, value)` and `qa_camera(...)` this brief names. Plants are activated through `preload("res://scenes/mockups/_shared/qa_plants.gd").is_active("<id>")` at a one-line fault site.
- Under Xvfb a 3D scene renders at a few frames per second; keep QA scripts short (a few hundred frames), use 1280x720 by default, and take the 1920x1080 review shots only in the final batch. Window pixels equal screenshot pixels; canvas coordinates are scaled by the stretch (use `click_node` rather than raw pixels for HUD buttons).
- Input gotchas: a full-rect `Control` with the default `mouse_filter = STOP` swallows synthetic mouse events before `_unhandled_input`; put world mouse handling in `_unhandled_input` on a non-Control node and set every full-rect Control to `MOUSE_FILTER_IGNORE` unless it is the designated click surface. Set `focus_mode = FOCUS_NONE` on Buttons and click empty ground before key verbs so a SpinBox does not eat letters.
- Copy the feel of the landscape mockup's HUD and camera code where it fits: `scenes/mockups/landscape/hud.gd` (kit discovery, timing prints, screenshot key), `camera_rig.gd` (pan, edge scroll, wheel zoom, public `pan_to`/`set_height`).
- Colours available to copy: `autoload/theme_constants.gd` (BASE `#0A0D12`, PRIMARY `#e8e6e1`, ERA_ACCENTS), faction colours `#4099FF` and `#FF4738` from `assets/eras/settled_reach/manifest.json`, the hue-from-id function in `autoload/faction_palette.gd:38`. Fonts: `theme/fonts/` (JetBrainsMono, Newsreader).
- Legacy to copy from (never to load): `scenes/tactical/mission_marker.gd` (beam height 800, radius 8, primary colour `(0.3, 0.85, 1.0)`, secondary `(0.4, 0.5, 0.6)`, `Label3D` type label, `_build_zone_ring` at line 72); `scenes/tactical/hud.gd:240-300` (`_rebuild_objectives`, `_update_objectives`, bar 320x6 px, `_OBJ_DESCRIPTIONS` at line 20) and `:627-650` (minimap glyph per kind: square for hold and clear, diamond for eliminate, triangle for escort); the snapshot shape you must emit, `simulation/snapshot_serializer.py:357-380` (`{id, type, progress, status, is_primary, location {x, y}}`), specified at `docs/architecture.md:52-70`.
- Landscape node dump: write `tools/dump_nodes.gd` (`extends SceneTree`, loads `res://scenes/mockups/landscape/field_map.gd`, calls `generate(seed, 24000.0, 60.0)` for seeds 11, 12, 13, writes `fixtures/nodes_seed<N>.json` as `{"canvas": 24000, "seed": N, "nodes": [{"type": "...", "pos": [x, z]}]}`), run it once headless (`godot --headless --path . --script res://scenes/mockups/objectives/tools/dump_nodes.gd`), commit the three JSON files, and never load the landscape script at runtime. If the class cache does not resolve `FieldMap`, run `godot --headless --path . --import` first. The landscape mockup is on `main` and in your worktree; do not modify it.

## What to build

```
scenes/mockups/objectives/
  objectives_mockup.tscn    root Node3D "ObjectivesMockup" with objectives_mockup.gd; children World, CameraRig, HUD, QADriver
  objectives_mockup.gd      the contract; owns load fixture, generate, tick, render
  mission_gen.gd            RefCounted: archetype table, kind selection, placement, satisfiable check, snapshot emit
  places.gd                 RefCounted: loads a nodes fixture, exposes typed lookups and a coarse route grid
  markers.gd                Node3D: beam, name Label3D, zone ring, per-kind glyph mesh
  camera_rig.gd             fixed top-down pan, wheel zoom, edge scroll, canvas-bounded (copy from landscape)
  hud.gd                    CanvasLayer: archetype dropdown, seed spinbox, Regenerate (R), objective line with progress bar, minimap with glyphs, Tick (T) and Play (P)
  fixtures/nodes_seed11.json, nodes_seed12.json, nodes_seed13.json
  tools/dump_nodes.gd
  verify.gd
  qa/smoke.json, qa/checklist.md
```

### 1. `places.gd`

Loads a fixture; `nodes_of(type) -> Array`, `nearest(type, pos)`, `player_spawn()` (the first `spawn_point`), `enemy_spawn()` (the `spawn_point` farthest from the player's), `route_length(a, b)` on a 100 wu grid where cells are open (this mockup has no terrain; the grid is open everywhere except a seeded 5 percent of cells marked blocked around `hazard_anchor` nodes so the route is not always a straight line; A* or BFS, cached per pair). Draw every node as a flat box with a `Label3D` of its type so the map reads as places.

### 2. `mission_gen.gd`

The archetype table from R-073-01 as data (ten rows: name, canvas, primary objective kind; where the row says "or" pick the first for Round 1 and list it). `build(archetype, places, seed) -> Mission`:

- kind from the table; placement by kind: `hold_zone` at the `objective` node (radius 600 wu); `destroy_targets` at a `chokepoint` or `hazard_anchor` (three target boxes within 300 wu, seeded); `escort_to_extraction` from the player spawn to the `extraction` node with a route polyline; `survive_duration` at a `staging` node (required 900 ticks); `eliminate_force` around the enemy spawn (a seeded force of 8 enemy boxes within 500 wu).
- satisfiable: the objective position is inside the canvas, at least 2,000 wu from the player spawn, and `route_length(player_spawn, objective) / 80 wu per s` (Vanguard speed) fits within the archetype's time limit from R-076-01 with base B = 350 ticks × 20 (use the Q-076-01 config band, 250 to 450 ticks, scaled ×20 for this mockup so a route is walkable; list the scaling as under-defined). If not satisfiable, the generator moves to the next candidate node of the same type and reports which it skipped.
- emits the objective in the snapshot shape: `{id, type, progress, status: "active", is_primary: true, location {x, y}}`.
- a toy tick (`tick(mission, state)`) advances progress per R-075-02 to R-075-06 under a scripted situation: for hold, a scripted enemy box enters the zone at tick 200 and leaves at tick 300 so the timer visibly pauses; for destroy, one target box is "destroyed" every 150 ticks; for escort, the escort box walks the route at 60 wu per s; for survive, the timer runs; for eliminate, enemy HP drops on a schedule. Status flips to `complete` at progress 1.0 (R-075-07).

### 3. `markers.gd`, `camera_rig.gd`, `hud.gd`

Marker: a beam (thin tall box, 800 wu, objective colour), the name as `Label3D` (billboard, fixed pixel size so it reads at every zoom), a zone ring (torus or flat ring mesh) for hold, survive, and eliminate radii, per-kind glyph on top (cube, diamond as a rotated cube, cone for escort, sphere for survive, cross of two boxes for eliminate), the escort route as a line of small boxes, target boxes for destroy that turn dark when destroyed. The player's spawn gets a faction-coloured block.

Camera: copy the landscape rig's pan, edge scroll, wheel zoom, and canvas bounds; fixed top-down interim (pitch 90°, R-103-03), heights 800 to 20,000 wu, `qa_camera(height, x, z)`.

HUD: archetype `OptionButton` (ten rows), seed spinbox, Regenerate (R), a single objective line "PRIMARY  Hold the core  ▮▮▮▮▮▯▯▯▯▯ 47%" with a 320x6 bar, a 200x200 minimap with a glyph per kind and the player spawn, Tick (T) advances 50 toy ticks, Play (P) runs to completion at 20 ticks per second, a satisfiable readout (route length, time limit, which nodes were skipped).

### 4. The contract

`PLANTS = ["objective-on-spawn", "marker-unnamed", "progress-static", "kind-mapping-random", "seed-ignored", "route-ignored"]`. `qa_state()`: `seed`, `hash`, `fixture`, `archetype`, `objective` (the snapshot dict), `satisfiable` (bool plus `route_len_wu`, `time_limit_ticks`, `skipped` list), `marker` (`{name, px: [x, y]}` via unproject), `tick`, `timing_ms {gen}`, `regen_count`. `qa_seed(n)`; `qa_set("archetype", name)`, `qa_set("fixture", 12)`; `qa_camera(height, x, z)`; `qa_tick(n)` advances n toy ticks synchronously.

Fault sites: `objective-on-spawn` places every objective at the player spawn; `marker-unnamed` leaves the `Label3D` text empty; `progress-static` makes the toy tick not advance progress; `kind-mapping-random` picks the kind from the seeded RNG instead of the table; `seed-ignored` forces seed 11; `route-ignored` reports route length as straight-line distance and never skips a node.

### 5. Build order (commit after each)

verify.gd red and stubs; node dump tool and fixtures; places and route grid; generator with placement and satisfiable; markers; camera; HUD and toy tick; smoke, checklist, screenshots, README.

## TDD protocol

1. Step 0: write `verify.gd` (`extends SceneTree`; `_init` runs one `_check_<id>()` per row of the check table below, then `quit(0)` or `quit(1)`; prints `FAIL: <id> <msg>` per failure and `VERIFY OK` on success, sharing one `_assert(cond, msg)`). Run `scripts/mockup_verify.sh objectives`: it must print exactly one `FAIL:` line per check and exit 1. Commit as `test(mockup/objectives): red verify.gd`.
2. Step 0 also: the root stub with `PLANTS`, `qa_state`, `qa_plant` (returns true for every listed id even before the feature exists), `qa/smoke.json`, `qa/checklist.md` copied from the template below, the `QADriver` child in the `.tscn`, and `docs/northstar/research/mockups/objectives/README.md` with a one-paragraph "Design as built" placeholder.
3. Each build step: implement, run `mockup_verify.sh`, the named checks flip green, commit. Never edit a threshold; Westley owns them.
4. Every check carries its plant in a `# plant: <id>` line. Once the feature behind a check exists, `scripts/mockup_verify.sh objectives --plant <id>` must print `PLANT <id> LIVE`; if it prints `DEAD`, fix the check or the fault site before committing.
5. Headless checks (verify.gd, dummy renderer, no autoloads): pure data, node-tree shape, API contract, determinism, CPU timing. Instantiate the scene when a check needs the tree: `var root = load("res://scenes/mockups/objectives/objectives_mockup.tscn").instantiate(); get_root().add_child(root); await process_frame`. Never call screenshot verbs headless.
6. Xvfb checks (driver plus shell): pixel diffs, pixel probes at projected positions, screenshot inspection, `fps_ms`. One clean run and one run per plant, in separate out dirs under your scratchpad; never mix the `plant` verb into a clean script.
7. `verify.gd` stays between 100 and 200 lines: at most 12 checks, each at most 15 lines.
8. After the clean and planted Xvfb runs, fill `qa/checklist.md` with the measured numbers, Read every screenshot, answer every visual question with the proving screenshot's name, fix every "no", rerun, and list what you cannot judge under `HELD:`.
9. Copy the review screenshots (1920x1080 batch) into `docs/northstar/research/mockups/objectives/pass1/` and commit them; do not commit any other run output.
10. The report's check table lists, per check: clean result, plant id, planted result.

## Verify checks (`verify.gd`)

| id | check | where | plant |
|---|---|---|---|
| DET-1 | same seed, same archetype, same fixture gives the same `hash` twice | H | `seed-ignored` (seed 12 then equals seed 11 in SEED-2) |
| SEED-2 | seed 11 and seed 12 differ in `hash` for at least 6 of the 10 archetypes (target placement and force layout are seeded) | H | `seed-ignored` |
| KIND-3 | for all ten archetypes the objective kind equals the table's kind | H | `kind-mapping-random` |
| PLACE-4 | hold sits on an `objective` node, escort ends at `extraction`, survive at `staging`, destroy at `chokepoint` or `hazard_anchor`, eliminate within 500 wu of the enemy spawn | H | `objective-on-spawn` |
| SAT-5 | on all three fixtures every archetype is satisfiable, and the objective is at least 2,000 wu from the player spawn | H | `objective-on-spawn` |
| ROUTE-6 | `route_length` around a blocked cell exceeds the straight line; a fixture with the objective walled off reports unsatisfiable and a skip | H | `route-ignored` |
| NAME-7 | after build, marker count equals 1 and its `Label3D.text` is non-empty and equals the objective's display name | H (instantiate) | `marker-unnamed` |
| PROG-8 | `qa_tick(600)` on hold gives progress in (0, 1), monotone non-decreasing, and the enemy-in-zone window pauses it; `qa_tick` to the end flips status to `complete` | H | `progress-static` |
| SHAPE-9 | the emitted objective dict has exactly the snapshot keys `id, type, progress, status, is_primary, location` | H | none |
| JSON-10 | `qa_state()` round-trips through JSON with every key above; `qa_plant("nope")` false, every `PLANTS` id true | H | none |
| TIME-11 | `timing_ms.gen` under 200 ms headless | H | none |

Xvfb oracles: MARKER-X (marker colour present within 6 px of `marker.px` at heights 3,000 and 12,000; under `marker-unnamed` the label region has no text pixels: compare a crop above the marker against the clean run, `diff` ≥ 0.02); PROG-X (`diff hud_p30.png hud_p90.png` ≥ 0.002 over the bar's crop and `objective.progress` 0.3 versus 0.9 in the states; under `progress-static` both 0.0); SEED-X (`diff seed11.png seed12.png` ≥ 0.05 clean, < 0.01 planted); KIND-X (the five kind screenshots pairwise `diff` ≥ 0.01); ERR-0, GPU-0, DET-1 pixel.

## QA script and screenshots

`qa/smoke.json`: `state boot`; `seed 11`; `call qa_camera 3000 12000 12000`; for each of `defensive_stand`, `siege_breaking`, `rear_guard`, `suppression`, `multi_front_defense` (one per kind, in that order): `call qa_set archetype <name>`, `wait_frames 2`, `screenshot kind_<name>`, `state kind_<name>`; then `call qa_set archetype defensive_stand`; `call qa_camera 12000 12000 12000`; `screenshot map_zoom`; `state map_zoom`; `call qa_tick 270`; `screenshot hud_p30`; `state hud_p30`; `call qa_tick 540`; `screenshot hud_p90`; `state hud_p90`; `seed 12`; `screenshot seed12`; `state seed12`; `call qa_set fixture 12`; `state fixture12`; `key R`; `state after_r`. Review batch at 1920x1080: the five kinds at tactical zoom, the map zoom, the HUD at 30 and 90 percent, seeds 11 and 12 (10 shots) into `docs/northstar/research/mockups/objectives/pass1/`.

## Checklist: visual questions

Read each PNG beside `docs/bible/references/E-17/E-17-8-wows-map-view.png` (row 08: objective circles on the map view) and the E-10 60-second paragraph.

| q | question | proves |
|---|---|---|
| Q1 | At tactical zoom, is the objective the first thing your eye lands on, and is its name readable? | P3 acceptance |
| Q2 | Can you tell the five kinds apart from the marker alone, without the HUD line? | S-075 |
| Q3 | At map zoom, do the marker and the zone ring still read; does the escort route read as a route? | P3 acceptance |
| Q4 | Does the HUD line tell you what done looks like in one glance (kind, name, progress)? | R-075-01 |
| Q5 | Does the map read as places (named node boxes) rather than a blank plane with one marker? | E-17 vocabulary |
| Q6 | Any magenta, black, clipped, or overlapping text at 720p? | hygiene |

## What the report must answer

1. Does each kind read at a glance; which glyph or ring did not work?
2. Is the landscape's nine-node vocabulary enough to place every archetype's objective, or did a kind need information the node list does not carry (this bears on E-17's one-generator claim)?
3. How often was a node skipped as unsatisfiable across the three fixtures and ten archetypes, and why?
4. Frame time under llvmpipe at 720p; generation time.
5. Under-defined points with candidates: the time-limit scaling for a walkable mockup, the escort route rule, hold radius, how secondaries would show, the marker's look at the far band.

## Finishing report

Write it as your final message and also as the "Design as built" and "Questions for Westley" sections of `docs/northstar/research/mockups/objectives/README.md` (normal prose; that file is read by Westley), ending with a "Next step" line that says the pass-1 screenshots are in `pass1/` and the mockup awaits his look. The report answers the numbered questions below, includes the check table (check, clean result, plant, planted result), the answers to the visual questions with proving screenshots, the `HELD:` list, timings (`timing_ms`, `fps_ms` under llvmpipe at 720p), the list of commits, and every under-defined point with two or three candidates and no decision.

## Verification (done when all of these hold)

- `scripts/mockup_verify.sh objectives` prints `VERIFY OK`, exit 0; `scripts/mockup_verify.sh objectives --plant <id>` prints `PLANT <id> LIVE` for every id in `PLANTS`.
- `scripts/mockup_qa.sh run objectives scenes/mockups/objectives/qa/smoke.json <scratch>/objectives/clean` gives `exit.txt` 0, `errors.txt` 0, no `UNIFORM` line, `_qa.adapter` containing `llvmpipe`; a second clean run matches the first on every `hash` and every screenshot (`diff` under 0.005).
- One run per plant under `<scratch>/objectives/plant-<id>` and every deterministic oracle in the checklist shows the planted number on the wrong side of its threshold.
- `qa/checklist.md` is filled; every visual question is answered or held; the pass-1 screenshots are committed under `docs/northstar/research/mockups/objectives/pass1/`.
- `git status --short` on your branch shows only `scenes/mockups/objectives/**` and `docs/northstar/research/mockups/objectives/**`; `git diff --stat main -- scenes/tactical scenes/world scenes/main_menu scenes/mockups/landscape scenes/mockups/_shared tests csrc docs/bible docs/northstar/PLAN.md project.godot` is empty.
- The interactive command (`~/.local/bin/godot --scene scenes/mockups/objectives/objectives_mockup.tscn`) is documented in the README with its hotkeys; you cannot run it on Westley's seat, so confirm instead that a wrapper run without `--qa-script` leaves the driver inert (no `_run.json`).
