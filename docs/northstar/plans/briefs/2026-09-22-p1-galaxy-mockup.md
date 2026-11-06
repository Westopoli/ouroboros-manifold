# HANDOFF BRIEF — P1 galaxy view mockup

Self-contained. Handed to an implementor 2026-09-22. Sibling briefs: `2026-09-22-mockup-qa-harness.md` (the harness you use), `2026-09-21-p2-landscape-mockup.md` (the shape to copy).

## Context

Rung P1 of the prototype ladder (`docs/northstar/PLAN.md:162`): the galaxy view, "points, edges, owner colour, pan, zoom, click to inspect", the world the player sees between missions. Epic E-16, stories S-106 (the galaxy between missions) and S-107 (reading the galaxy), Round 1 minimal per `docs/legacy/mvp/feature_mvps.md` ("regions as points, edges as lines, owner as color, pan, zoom, click to inspect; the existing in-game galaxy animation is the reference"). Rules to read first: `docs/bible/epics/E-16-client-camera-hud-and-world-view.md` lines 75 to 101 (R-106-01 to R-106-05, R-107-01 to R-107-05). Shells (R-106-02's translucent faction shells) and the data panel (R-107-04) are not in this mockup; list them as deferred.

The epic's "Obviously working in 60 seconds" text names the whole client; the galaxy part is: the galaxy fades in, borders visibly morph, a system can be clicked and focused. The look is a design phase, not a reference pull (`docs/bible/references/E-16/notes.md`, "TBD" section): the existing in-game galaxy view "already has good animation" and is the starting point. Two captures exist and are your ground truth: `docs/bible/references/E-16/main_menu.png` (title over a slowly turning particle galaxy with one bright core) and `docs/bible/references/E-09/time_jump_galaxy_and_scroll.png` (territory as translucent coloured shells around system nodes, gold lane lines, a polar grid, a nebula-like star field; the map fills two thirds of the screen). Read both before building.

This mockup is throwaway, isolated, and the first thing Westley will fly for P1. It shows one seeded galaxy: systems as luminous points, filaments between them, owner colour, three zoom bands, pan, zoom, orbit, click to focus, a faction list, and a scripted jump-log replay that flashes and recolours systems.

## Rules for the implementor

- If you are an Opus or Fable chat: plan and review, Sonnet sub-agents build; ask Westley about his Claude usage before a batch of more than two doers. If you are a Sonnet chat: do the work yourself, spawn no sub-agents.
- You are in a git worktree on branch `mockup/galaxy`. Commit there after each working step with the trailer `Co-Authored-By: Claude <model> <noreply@anthropic.com>`. Do not push; the design chat merges into `main`. Never stage files you did not create or edit for this brief. Never check out another branch.
- Touch only `scenes/mockups/galaxy/**` and `docs/northstar/research/mockups/galaxy/**`. Nothing else: not `csrc/`, `simulation/`, `tests/`, `docs/bible/`, other `docs/northstar/`, other `scenes/`, `scenes/mockups/_shared/` (if the harness is broken, stop and report; do not patch it), `project.godot`.
- This is a mockup: placeholder primitives only (boxes, cylinders, prisms, planes, quads, flat colours, `Label3D`, `Control._draw`). No imported models, no textures beyond vertex colour and flat shading. GDScript only. No autoload dependency and no dependency on any other scene: the scene must work if every autoload were removed. You may copy code from the legacy files named under "Godot facts" into your directory and you may reference `theme/fonts/*.ttf` by `res://` path; you may not `preload` or `load` anything outside your directory except `res://scenes/mockups/_shared/qa_driver.gd` and `qa_plants.gd`.
- Renderer parity: your QA renders run under the Compatibility renderer on software GL; Westley views Forward+ on an RTX 3060. Use only what looks the same in both: `StandardMaterial3D` (vertex colour as albedo is fine), `ArrayMesh`/`ImmediateMesh`, `MultiMeshInstance3D`, `Label3D`, one `DirectionalLight3D`, `WorldEnvironment` sky, ambient and depth fog, `CanvasLayer`, `CPUParticles3D`. Do not use SDFGI, VoxelGI, volumetric fog, SSR, SSAO, SSIL, glow, decals, `GPUParticles3D`, or screen-texture shaders.
- No era named in any script identifier or node name (bible rule R-145-01). Where the era shows it is data under `kits/` or `fixtures/`.
- Deterministic: every random draw comes from your own `RandomNumberGenerator` seeded from an integer seed; never the global RNG, never the wall clock. Same seed, same state hash, same pixels.
- **Never set `DISPLAY` yourself and never use `:0` or `:1`.** Every windowed run goes through `scripts/mockup_qa.sh`, which creates a private Xvfb. The GPU belongs to the Agora chain.
- No docstrings or comments except the `# plant: <id>` line above each check in `verify.gd`. Minimal, direct code.
- When something in this brief is under-defined, do not decide: build the simplest thing that shows the question and list it in the finishing report with two or three candidate answers.

## Godot facts (reconnaissance 2026-09-22)

- Binary `~/.local/bin/godot`, `4.6.3.stable.official`. Project root is the repo root. `project.godot` declares Forward+, 1920x1080, fullscreen, stretch `canvas_items`/`expand`, no `[input]` map (use raw keycodes as the landscape mockup does). Nineteen autoloads run on any `--path .` scene launch; one spawns the Python sim and warns about a mac path; harmless. `--script` SceneTree mode loads no autoloads.
- Scene convention: a short `.tscn` (root node with your root script, a `QADriver` child with `res://scenes/mockups/_shared/qa_driver.gd`, and whatever nodes you need) plus scripts. Every mockup scene in this repo is launched by path, never as the main scene. Westley's command is `~/.local/bin/godot --scene scenes/mockups/galaxy/galaxy_mockup.tscn` from the repo root; keep that name.
- The harness (read `scenes/mockups/_shared/README.md` first): `scripts/mockup_verify.sh galaxy [--plant id]` runs your `verify.gd` headless; `scripts/mockup_qa.sh run galaxy <script.json> <outdir> [--res 1280x720] [--plant id]` runs the scene under Xvfb with `--fixed-fps 30` and replays a JSON action list (`wait_frames`, `move`, `click`, `click_node`, `drag`, `wheel`, `key`, `key_down`, `key_up`, `call`, `seed`, `plant`, `pause`, `screenshot`, `state`, `tree`, `wait_file`); `scripts/mockup_qa.sh diff a.png b.png` prints the fraction of differing pixels; `scripts/mockup_qa.sh scan <outdir>` writes `errors.txt`, `shots.txt`, `marks.txt`. Your scene root must implement the contract: `const PLANTS: Array[String]`, `qa_state() -> Dictionary` (JSON-safe, canonical from data, never from HUD labels; always `seed`, `hash`, `timing_ms`, `regen_count` plus the keys named below), `qa_plant(id) -> bool`, `qa_seed(n)`, and the optional `qa_set(name, value)` and `qa_camera(...)` this brief names. Plants are activated through `preload("res://scenes/mockups/_shared/qa_plants.gd").is_active("<id>")` at a one-line fault site.
- Under Xvfb a 3D scene renders at a few frames per second; keep QA scripts short (a few hundred frames), use 1280x720 by default, and take the 1920x1080 review shots only in the final batch. Window pixels equal screenshot pixels; canvas coordinates are scaled by the stretch (use `click_node` rather than raw pixels for HUD buttons).
- Input gotchas: a full-rect `Control` with the default `mouse_filter = STOP` swallows synthetic mouse events before `_unhandled_input`; put world mouse handling in `_unhandled_input` on a non-Control node and set every full-rect Control to `MOUSE_FILTER_IGNORE` unless it is the designated click surface. Set `focus_mode = FOCUS_NONE` on Buttons and click empty ground before key verbs so a SpinBox does not eat letters.
- Copy the feel of the landscape mockup's HUD and camera code where it fits: `scenes/mockups/landscape/hud.gd` (kit discovery, timing prints, screenshot key), `camera_rig.gd` (pan, edge scroll, wheel zoom, public `pan_to`/`set_height`).
- Colours available to copy: `autoload/theme_constants.gd` (BASE `#0A0D12`, PRIMARY `#e8e6e1`, ERA_ACCENTS), faction colours `#4099FF` and `#FF4738` from `assets/eras/settled_reach/manifest.json`, the hue-from-id function in `autoload/faction_palette.gd:38`. Fonts: `theme/fonts/` (JetBrainsMono, Newsreader).
- Legacy galaxy stack to copy from (never to load): `scenes/shared/world_view/renderers/constellation_renderer.gd:127-190` (`_compute_bezier_arc`, `_build_tube_mesh`; tube sides 8, curve segments 16, arc height 0.15 of chord, border width 0.075 versus trade 0.035); `scenes/shared/world_view/cameras/orbital_camera_3d.gd:152-300` (`_input`, `_try_click_focus` raycast pick, `_focus_on_region` 1.5 s tween; PAN 0.5, ORBIT 0.01, ZOOM 5.0, distance 15 to 120); `scenes/shared/world_view/zoom_disclosure_controller.gd` (distance to band blend); `scenes/shared/world_view/main_menu_galaxy.gd:73-102,316-437` (the ambient rig: 12 rings, radial streams, dust, starfield; those use particle shaders, so rebuild the idea with static CPU-built quads); `scenes/debug/test_world_view.gd:6-30` (an 8-region, 3-faction hand fixture shape). Data shape the real client will feed: `simulation/world_view/keyframe_selector.py:151-175` (`regions_snapshot[] {region_id, owner_faction_id, significance, x, y, z, name}`, `connections[] {from_id, to_id, edge_type}`), documented at `docs/architecture.md:72-127`. A 60-region save exists at `saves/autosave/sim.json` (`sim_state.world.regions`, `adjacency`, `edge_types`, `factions`); you may derive a fixture from it once, by a script you keep in `tools/`, but the seeded generator is the primary source.

## What to build

```
scenes/mockups/galaxy/
  galaxy_mockup.tscn        root Node3D "GalaxyMockup" with galaxy_mockup.gd; children World, OrbitCamera, HUD, QADriver
  galaxy_mockup.gd          the contract; owns generate, render, replay
  galaxy_gen.gd             RefCounted seeded generator -> Galaxy (pure data, no nodes)
  galaxy_view.gd            Node3D renderer: points, filaments, ambient field, flashes
  orbit_camera.gd           pan, zoom, orbit, focus, bands
  hud.gd                    CanvasLayer: seed spinbox, Regenerate (R), faction list, tooltip, band label, Play jump log (J)
  fixtures/jump_log_seed11.json
  tools/fixture_from_save.gd   optional, headless, writes fixtures/galaxy_from_save.json
  verify.gd
  qa/smoke.json, qa/focus.json, qa/checklist.md
```

### 1. `galaxy_gen.gd`

`generate(seed: int) -> Galaxy`. Galaxy holds `systems[]` (`{id, pos: Vector3, significance: float, owner: int, name: String}`), `factions[]` (`{id, name, capital, hue}`), `edges[]` (`{a, b, kind}` with kind `border` or `trade`), and `hash() -> int` over all of it. Seeded `RandomNumberGenerator` only.

- Count: 40 to 80 systems (seeded). Positions: a disc of radius 100 units in the XZ plane, Y jitter within ±8, minimum spacing 6 (rejection sample), a denser core. Names: two-syllable seeded strings from a small syllable table (never a real place name).
- Adjacency: each system links to its 3 nearest within 30 units, symmetrised. Every system ends with at least one link (attach isolated ones to their nearest).
- Factions: 6 (seeded 4 to 8). Capitals chosen far apart (farthest-point sampling). Ownership by breadth-first flood from the capitals over adjacency in seeded order, stopping at 85 percent of systems so about 15 percent stay neutral (owner -1). Faction 0 is the player's.
- Edge kind: a link between two same-owner systems is `border`; between different owners (or a neutral) is `trade`. This matches R-106-02's "adjacent same-faction systems joined by faction-coloured filaments" with trade edges thinner and dimmer.
- Significance: capital 1.0, others 0.3 to 0.8 seeded; the player's capital is the single brightest point (R-106-01).
- Hue per faction: the hash-to-hue function copied from `faction_palette.gd:38`; neutral is grey.

### 2. `galaxy_view.gd`

Points: one `MultiMeshInstance3D` of small spheres (or camera-facing quads), instance transform scale = 0.6 + 1.4 × significance, instance colour = faction colour, emission-like brightness by using an unlit `StandardMaterial3D` with vertex colour. Filaments: `ArrayMesh` tubes along bezier arcs lifted 0.15 of the chord out of the plane, border width 0.075 and trade 0.035 (legacy numbers), colour = the owner's colour for border, a dim neutral for trade. Ambient: 400 dust quads and 800 star quads as one MultiMesh each at low alpha, plus a faint polar grid on the plane (lines, no shader), so the space behind the territory is not empty (R-106-05). Faction name `Label3D` floats at each faction's centroid, shown only in the Overview band.

Band properties, interpolated continuously by camera distance (R-106-03; the numbers are the bible's and Westley's): Overview at d ≥ 75 (points shrink to 0.6 scale, filaments at 40 percent alpha, names visible); Regional at 40 ≤ d < 65 (default; points full, filaments dominant, names hidden); Local at d < 25 (focused system 1.5× bright, its filaments 1.5× wide, systems farther than 30 units desaturate to 30 percent). Between bands, lerp.

Flash (R-106-04): `flash(system_id, colour)` scales the point to 3× and back over 0.6 s and draws a ring quad that expands and fades. Recolour: `set_owner(system_id, faction_id)` updates the instance colour and rebuilds the affected filaments.

### 3. `orbit_camera.gd`

Target point on the plane, distance, yaw, pitch (default pitch 55°, yaw 0, distance 50). Left-drag pans the target in the plane; wheel zooms distance by 10 percent per notch, clamped 15 to 120; right-drag orbits yaw and pitch (pitch 20° to 85°); left-click on a system (nearest projected point within 14 px) tweens target to it and distance to 20 over 1.5 s, so the band becomes Local (R-107-01). Public: `get_band()`, `get_distance()`, `qa_camera(distance, target_system_id)` for scripts, `project(system_id) -> Vector2`.

### 4. `hud.gd`

Seed spinbox and Regenerate (R); faction list on the left, always visible: one row per faction with a colour swatch and name; hovering a row brightens that faction's systems and filaments and dims the others to 25 percent; clicking a row pins the dim at 5 percent until the row is clicked again or empty space is clicked (R-107-03). System hover tooltip: name and owner (R-107-05). Band label. Play (J): replays `fixtures/jump_log_seed11.json` at two events per second: `{"kind":"attack","from":id,"to":id}` flashes both, `{"kind":"conquest","from","to"}` flashes both then recolours `to` to `from`'s owner, `{"kind":"revolt","at":id}` flashes `at` in grey. Write 12 events for seed 11 by hand, referencing system ids that exist (verify checks that). Count label: systems, edges by kind.

### 5. The contract

`PLANTS = ["seed-ignored", "owner-colour-flat", "edges-2d-overlay", "pick-radius-zero", "bands-frozen", "conquest-no-recolour"]`. `qa_state()`: `seed`, `hash`, `system_count`, `faction_count`, `edge_counts {border, trade}`, `band`, `distance`, `focused` (system id or -1), `hover_faction`, `pinned_faction`, `systems_px` (id to `[x, y]` for every system via `project`), `owners` (id to owner), `replay {index, done}`, `timing_ms {gen, build}`, `regen_count`. `qa_seed(n)`; `qa_set("hover_faction", id)`, `qa_set("pin_faction", id)`; `qa_camera(distance, target_system_id)`; `qa_replay_step()` advances the jump log one event synchronously.

Fault sites: `seed-ignored` forces seed 11 in `qa_seed`/regenerate; `owner-colour-flat` gives every point one colour; `edges-2d-overlay` draws filaments as 2D lines in a full-rect Control `_draw` instead of tubes in `World`; `pick-radius-zero` sets the click pick radius to 0 px; `bands-frozen` reports and renders Regional at every distance; `conquest-no-recolour` skips `set_owner` on conquest.

### 6. Build order (commit after each)

verify.gd red and stubs; generator with hash; view points and filaments; camera and bands; HUD list, hover, tooltip; replay; smoke and focus scripts, checklist, screenshots, README.

## TDD protocol

1. Step 0: write `verify.gd` (`extends SceneTree`; `_init` runs one `_check_<id>()` per row of the check table below, then `quit(0)` or `quit(1)`; prints `FAIL: <id> <msg>` per failure and `VERIFY OK` on success, sharing one `_assert(cond, msg)`). Run `scripts/mockup_verify.sh galaxy`: it must print exactly one `FAIL:` line per check and exit 1. Commit as `test(mockup/galaxy): red verify.gd`.
2. Step 0 also: the root stub with `PLANTS`, `qa_state`, `qa_plant` (returns true for every listed id even before the feature exists), `qa/smoke.json`, `qa/checklist.md` copied from the template below, the `QADriver` child in the `.tscn`, and `docs/northstar/research/mockups/galaxy/README.md` with a one-paragraph "Design as built" placeholder.
3. Each build step: implement, run `mockup_verify.sh`, the named checks flip green, commit. Never edit a threshold; Westley owns them.
4. Every check carries its plant in a `# plant: <id>` line. Once the feature behind a check exists, `scripts/mockup_verify.sh galaxy --plant <id>` must print `PLANT <id> LIVE`; if it prints `DEAD`, fix the check or the fault site before committing.
5. Headless checks (verify.gd, dummy renderer, no autoloads): pure data, node-tree shape, API contract, determinism, CPU timing. Instantiate the scene when a check needs the tree: `var root = load("res://scenes/mockups/galaxy/galaxy_mockup.tscn").instantiate(); get_root().add_child(root); await process_frame`. Never call screenshot verbs headless.
6. Xvfb checks (driver plus shell): pixel diffs, pixel probes at projected positions, screenshot inspection, `fps_ms`. One clean run and one run per plant, in separate out dirs under your scratchpad; never mix the `plant` verb into a clean script.
7. `verify.gd` stays between 100 and 200 lines: at most 12 checks, each at most 15 lines.
8. After the clean and planted Xvfb runs, fill `qa/checklist.md` with the measured numbers, Read every screenshot, answer every visual question with the proving screenshot's name, fix every "no", rerun, and list what you cannot judge under `HELD:`.
9. Copy the review screenshots (1920x1080 batch) into `docs/northstar/research/mockups/galaxy/pass1/` and commit them; do not commit any other run output.
10. The report's check table lists, per check: clean result, plant id, planted result.

## Verify checks (`verify.gd`)

| id | check | where | plant |
|---|---|---|---|
| DET-1 | `generate(11).hash() == generate(11).hash()`; `qa_seed(11)` twice gives equal `qa_state().hash` | H | `seed-ignored` (makes seed 12 equal seed 11, which the next check catches) |
| SEED-2 | `generate(12).hash() != generate(11).hash()` and at least 30 percent of systems by index differ in position by more than 5 units (or the counts differ) | H | `seed-ignored` |
| CONN-3 | for every faction, its systems form one connected component over `border` edges | H | `owner-colour-flat` does not affect this; plant is a generator fault `flood-skips` that is not in PLANTS, so instead assert with a hand-built two-component fixture that the check function itself returns false (self-test of the check) |
| KIND-4 | no `border` edge joins two systems with different owners; no `trade` edge joins two with the same owner | H | none needed (data invariant); include a self-test as in CONN-3 |
| COLOUR-5 | after render, every point instance colour equals the palette of its owner; neutral is grey | H (instantiate the scene) | `owner-colour-flat` |
| BAND-6 | `get_band()` at distances 80, 50, 20 is Overview, Regional, Local | H | `bands-frozen` |
| PICK-7 | `project(id)` then pick at that pixel returns `id`; pick 40 px away returns -1 | H | `pick-radius-zero` |
| EDGES-8 | the filament mesh parent is a `Node3D` under `World`; no full-rect `Control` other than the tooltip layer draws in `_draw` | H | `edges-2d-overlay` |
| REPLAY-9 | every event in the fixture names existing ids; after stepping a conquest, `owners[to] == owners_before[from]` | H | `conquest-no-recolour` |
| JSON-10 | `qa_state()` round-trips through `JSON.stringify` and has every key listed above; `qa_plant("nope")` is false and every `PLANTS` id is true | H | none |
| TIME-11 | `timing_ms.gen + timing_ms.build` under 500 ms headless | H | none |

Xvfb oracles in the checklist: SEED-X (`diff seed11_regional.png seed12_regional.png` ≥ 0.15 clean, < 0.02 under `seed-ignored`); FOCUS-X (after `qa/focus.json` clicks the pixel of system 5 taken from `systems_px` in the boot state, `focused == 5` and `band == "Local"`; under `pick-radius-zero` `focused == -1`); HOVER-X (`diff regional.png hover_f1.png` ≥ 0.03; under `owner-colour-flat` the faction rows are one colour); BAND-X (`diff overview.png local.png` ≥ 0.30); FLASH-X (`diff before_replay.png mid_replay.png` ≥ 0.01 in the flashed systems' neighbourhood, and `owners` changed after the conquest event; under `conquest-no-recolour` unchanged); ERR-0, GPU-0, DET-1 pixel.

## QA script and screenshots

`qa/smoke.json`: `state boot`; `seed 11`; `call qa_camera 90 -1`; `screenshot overview`; `call qa_camera 50 -1`; `screenshot regional`; `state regional`; `call qa_camera 20 0`; `screenshot local`; `state local`; `call qa_camera 50 -1`; `seed 12`; `screenshot seed12_regional`; `state seed12`; `seed 11`; `call qa_set hover_faction 1`; `screenshot hover_f1`; `call qa_set hover_faction -1`; `screenshot before_replay`; `state before_replay`; `call qa_replay_step` × 3; `screenshot mid_replay`; `state mid_replay`; `key R`; `state after_r`. Then write `qa/focus.json` by hand from `boot.json`'s `systems_px[5]`: `seed 11`; `call qa_camera 50 -1`; `click <x> <y>`; `wait_frames 60`; `state focused`; `screenshot focused`. Final review batch at 1920x1080: overview, regional, local, hover, mid-replay at seeds 11 and 12 (10 shots) into `docs/northstar/research/mockups/galaxy/pass1/`.

## Checklist: visual questions

Read each PNG beside `docs/bible/references/E-16/main_menu.png` and `docs/bible/references/E-09/time_jump_galaxy_and_scroll.png`.

| q | question | proves |
|---|---|---|
| Q1 | At Regional, can you tell which systems belong together without reading any label? | R-106-01, R-106-02 |
| Q2 | Are border filaments visibly thicker and brighter than trade filaments? | R-106-02 |
| Q3 | Does Local brighten the focused system and desaturate distant ones; does Overview read as a whole map with names? | R-106-03 |
| Q4 | Is the ambient field present and behind the territory, not competing with it? | R-106-05 |
| Q5 | Does the replay frame show a flash that reads as an event at a system? | R-106-04 |
| Q6 | Any magenta, black, or clipped HUD text at 720p? | hygiene |
| Q7 | Does the whole thing read as a cousin of the reference captures (luminous points, lanes, dark nebula space) rather than a graph diagram? | design phase |

## What the report must answer

1. Does the galaxy read as territory at a glance, and at which band best?
2. Does border versus trade read; does the Local band feel like focusing?
3. Frame time per band under llvmpipe at 720p and the count of systems and edges; expected RTX figure is Westley's to measure.
4. What the seeded generator cannot do that the real snapshot will need (for example, the save fixture's edge kinds versus the generated ones).
5. Under-defined points with candidates: band distances, shell treatment, significance formula, whether right-drag orbit should exist in Round 1, flash duration, replay pace.

## Finishing report

Write it as your final message and also as the "Design as built" and "Questions for Westley" sections of `docs/northstar/research/mockups/galaxy/README.md` (normal prose; that file is read by Westley), ending with a "Next step" line that says the pass-1 screenshots are in `pass1/` and the mockup awaits his look. The report answers the numbered questions below, includes the check table (check, clean result, plant, planted result), the answers to the visual questions with proving screenshots, the `HELD:` list, timings (`timing_ms`, `fps_ms` under llvmpipe at 720p), the list of commits, and every under-defined point with two or three candidates and no decision.

## Verification (done when all of these hold)

- `scripts/mockup_verify.sh galaxy` prints `VERIFY OK`, exit 0; `scripts/mockup_verify.sh galaxy --plant <id>` prints `PLANT <id> LIVE` for every id in `PLANTS`.
- `scripts/mockup_qa.sh run galaxy scenes/mockups/galaxy/qa/smoke.json <scratch>/galaxy/clean` gives `exit.txt` 0, `errors.txt` 0, no `UNIFORM` line, `_qa.adapter` containing `llvmpipe`; a second clean run matches the first on every `hash` and every screenshot (`diff` under 0.005).
- One run per plant under `<scratch>/galaxy/plant-<id>` and every deterministic oracle in the checklist shows the planted number on the wrong side of its threshold.
- `qa/checklist.md` is filled; every visual question is answered or held; the pass-1 screenshots are committed under `docs/northstar/research/mockups/galaxy/pass1/`.
- `git status --short` on your branch shows only `scenes/mockups/galaxy/**` and `docs/northstar/research/mockups/galaxy/**`; `git diff --stat main -- scenes/tactical scenes/world scenes/main_menu scenes/mockups/landscape scenes/mockups/_shared tests csrc docs/bible docs/northstar/PLAN.md project.godot` is empty.
- The interactive command (`~/.local/bin/godot --scene scenes/mockups/galaxy/galaxy_mockup.tscn`) is documented in the README with its hotkeys; you cannot run it on Westley's seat, so confirm instead that a wrapper run without `--qa-script` leaves the driver inert (no `_run.json`).
