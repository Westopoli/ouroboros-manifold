# HANDOFF BRIEF — P5 fog and sensors mockup

Self-contained. Handed to an implementor 2026-09-22. Sibling briefs: `2026-09-22-mockup-qa-harness.md` (the harness you use), `2026-09-21-p2-landscape-mockup.md` (the shape to copy).

## Context

Rung P5 of the prototype ladder (`docs/northstar/PLAN.md:166`): "Fog and sensors: visibility set matches state; unseen units not drawn." Epic E-12, Round 1 stories S-089 (I see what my units see; R-089-01 to R-089-06), S-092 (recon, then fog; R-092-01 to R-092-04), S-093 (fog is for the player, not the engine; R-093-01, R-093-02). S-094 (how fog looks) is Round 3 but its look is what Westley judges here, so its reference rows are your visual target. Read `docs/bible/epics/E-12-fog-and-sensors.md` lines 28 to 42, 69 to 104, and the whole of `docs/bible/references/E-12/notes.md`, then look at `references/E-12/Unexplored.png` and `ExploredButWithoutVision.png`.

The 60-second paragraph: a Vanguard (sensor 700) sees an enemy Raider at 650 wu on the same layer, not at 750; inside an interference zone of intensity 0.5 the Raider is visible at 400 wu and not at 401; an enemy behind a tall obstacle is gone though in range; in the recon phase every obstacle, zone and node is drawn and no enemy; Begin drops fog over the enemy positions; same seed, same visibility sets.

The derived rule in the references (Westley, 2026-09-13) has three fog states for terrain: never seen is pure black; explored without current vision is darkened terrain with enemy buildings still drawn and enemy units not drawn; current vision is full brightness. A fog-memory checkbox turns memory off so everything without current vision is black. Enemy units are never remembered (R-089-04): no ghost markers.

This mockup shows one flat map with obstacles, zones and nodes, a few scripted friendly units with sensor radii, scripted enemy units on loops and two enemy structures, the recon phase and Begin, the three fog states, sensor circles, an interference zone, and the memory toggle. The client never holds a hidden enemy's position (R-089-03): the mockup's toy sim keeps the truth in a separate object and hands the view only the visible set, and a check proves the view has nothing else.

## Rules for the implementor

- If you are an Opus or Fable chat: plan and review, Sonnet sub-agents build; ask Westley about his Claude usage before a batch of more than two doers. If you are a Sonnet chat: do the work yourself, spawn no sub-agents.
- You are in a git worktree on branch `mockup/fog`. Commit there after each working step with the trailer `Co-Authored-By: Claude <model> <noreply@anthropic.com>`. Do not push; the design chat merges into `main`. Never stage files you did not create or edit for this brief. Never check out another branch.
- Touch only `scenes/mockups/fog/**` and `docs/northstar/research/mockups/fog/**`. Nothing else: not `csrc/`, `simulation/`, `tests/`, `docs/bible/`, other `docs/northstar/`, other `scenes/`, `scenes/mockups/_shared/` (if the harness is broken, stop and report; do not patch it), `project.godot`.
- This is a mockup: placeholder primitives only (boxes, cylinders, prisms, planes, quads, flat colours, `Label3D`, `Control._draw`). No imported models, no textures beyond vertex colour and flat shading. GDScript only. No autoload dependency and no dependency on any other scene: the scene must work if every autoload were removed. You may copy code from the legacy files named under "Godot facts" into your directory and you may reference `theme/fonts/*.ttf` by `res://` path; you may not `preload` or `load` anything outside your directory except `res://scenes/mockups/_shared/qa_driver.gd` and `qa_plants.gd`.
- Renderer parity: your QA renders run under the Compatibility renderer on software GL; Westley views Forward+ on an RTX 3060. Use only what looks the same in both: `StandardMaterial3D` (vertex colour as albedo is fine), `ArrayMesh`/`ImmediateMesh`, `MultiMeshInstance3D`, `Label3D`, one `DirectionalLight3D`, `WorldEnvironment` sky, ambient and depth fog, `CanvasLayer`, `CPUParticles3D`. Do not use SDFGI, VoxelGI, volumetric fog, SSR, SSAO, SSIL, glow, decals, `GPUParticles3D`, or screen-texture shaders.
- No era named in any script identifier or node name (bible rule R-145-01). Where the era shows it is data under `kits/` or `fixtures/`.
- Deterministic: every random draw comes from your own `RandomNumberGenerator` seeded from an integer seed; never the global RNG, never the wall clock. Same seed, same state hash, same pixels.
- **Never set `DISPLAY` yourself and never use `:0` or `:1`.** Every windowed run goes through `scripts/mockup_qa.sh`, which creates a private Xvfb. The GPU belongs to the Agora chain.
- No docstrings or comments except the `# plant: <id>` line above each check in `verify.gd`. Minimal, direct code.
- When something in this brief is under-defined, do not decide: build the simplest thing that shows the question and list it in the finishing report with two or three candidate answers.

## Godot facts (reconnaissance 2026-09-22)

- Binary `~/.local/bin/godot`, `4.6.3.stable.official`. Project root is the repo root. `project.godot` declares Forward+, 1920x1080, fullscreen, stretch `canvas_items`/`expand`, no `[input]` map (use raw keycodes as the landscape mockup does). Nineteen autoloads run on any `--path .` scene launch; one spawns the Python sim and warns about a mac path; harmless. `--script` SceneTree mode loads no autoloads.
- Scene convention: a short `.tscn` (root node with your root script, a `QADriver` child with `res://scenes/mockups/_shared/qa_driver.gd`, and whatever nodes you need) plus scripts. Every mockup scene in this repo is launched by path, never as the main scene. Westley's command is `~/.local/bin/godot --scene scenes/mockups/fog/fog_mockup.tscn` from the repo root; keep that name.
- The harness (read `scenes/mockups/_shared/README.md` first): `scripts/mockup_verify.sh fog [--plant id]` runs your `verify.gd` headless; `scripts/mockup_qa.sh run fog <script.json> <outdir> [--res 1280x720] [--plant id]` runs the scene under Xvfb with `--fixed-fps 30` and replays a JSON action list (`wait_frames`, `move`, `click`, `click_node`, `drag`, `wheel`, `key`, `key_down`, `key_up`, `call`, `seed`, `plant`, `pause`, `screenshot`, `state`, `tree`, `wait_file`); `scripts/mockup_qa.sh diff a.png b.png` prints the fraction of differing pixels; `scripts/mockup_qa.sh scan <outdir>` writes `errors.txt`, `shots.txt`, `marks.txt`. Your scene root must implement the contract: `const PLANTS: Array[String]`, `qa_state() -> Dictionary` (JSON-safe, canonical from data, never from HUD labels; always `seed`, `hash`, `timing_ms`, `regen_count` plus the keys named below), `qa_plant(id) -> bool`, `qa_seed(n)`, and the optional `qa_set(name, value)` and `qa_camera(...)` this brief names. Plants are activated through `preload("res://scenes/mockups/_shared/qa_plants.gd").is_active("<id>")` at a one-line fault site.
- Under Xvfb a 3D scene renders at a few frames per second; keep QA scripts short (a few hundred frames), use 1280x720 by default, and take the 1920x1080 review shots only in the final batch. Window pixels equal screenshot pixels; canvas coordinates are scaled by the stretch (use `click_node` rather than raw pixels for HUD buttons).
- Input gotchas: a full-rect `Control` with the default `mouse_filter = STOP` swallows synthetic mouse events before `_unhandled_input`; put world mouse handling in `_unhandled_input` on a non-Control node and set every full-rect Control to `MOUSE_FILTER_IGNORE` unless it is the designated click surface. Set `focus_mode = FOCUS_NONE` on Buttons and click empty ground before key verbs so a SpinBox does not eat letters.
- Copy the feel of the landscape mockup's HUD and camera code where it fits: `scenes/mockups/landscape/hud.gd` (kit discovery, timing prints, screenshot key), `camera_rig.gd` (pan, edge scroll, wheel zoom, public `pan_to`/`set_height`).
- Colours available to copy: `autoload/theme_constants.gd` (BASE `#0A0D12`, PRIMARY `#e8e6e1`, ERA_ACCENTS), faction colours `#4099FF` and `#FF4738` from `assets/eras/settled_reach/manifest.json`, the hue-from-id function in `autoload/faction_palette.gd:38`. Fonts: `theme/fonts/` (JetBrainsMono, Newsreader).
- Legacy fog is 18 lines (`scripts/tactical/visibility.gd`) and there is no fog shader, mask or ring anywhere; you are building the first one. Sim-side rules to mirror in the toy: `simulation/fog_of_war.py:35-70` (`compute_visibility`, cone factors, vantage), `simulation/config.py:537` (elevation bonus, not needed here), interference from the map's gradient field. Data shape the real client receives: `snapshot_serializer.py:127-130` (`fog_of_war {player_visible_unit_uids, partial_visibility_uids}`).
- Landscape's field-map vocabulary for zones and nodes (`scenes/mockups/landscape/field_map.gd` `grid[]` cells carry `obstacle`, `cover`, `interference`; `nodes[]` carry the nine types); you do not load it, you author a small fixture in the same words.
- Fog render that is Compatibility-safe and cheap under llvmpipe: a 64×64 (or 96×96) cell grid as one `ArrayMesh` quad grid above the ground with per-vertex colour and alpha (black, dim, clear), rebuilt only on cells that changed, or an `ImageTexture` on a single quad updated per tick with `Image.set_pixel`. Either is fine; `Image` is simpler.

## What to build

```
scenes/mockups/fog/
  fog_mockup.tscn           root Node3D "FogMockup" with fog_mockup.gd; children World, CameraRig, HUD, QADriver
  fog_mockup.gd             the contract; owns fixture load, phase (recon or mission), tick loop, view sync
  truth.gd                  RefCounted: the whole world (friendlies, enemies, structures, terrain, interference); step(); compute_visibility(); hash()
  fog_grid.gd               RefCounted: cell states never_seen, explored, visible; memory flag; update(visible_circles)
  fog_view.gd               Node3D: fog quad, terrain, obstacles, zones, nodes, sensor circles, and ONLY the visible enemies handed to it
  camera_rig.gd             fixed top-down pan, wheel zoom, edge scroll, canvas-bounded (copy from landscape)
  hud.gd                    CanvasLayer: Begin Mission button, phase label, memory checkbox, seed, Reset (R), Step (T), Play (Space), visible-count readout
  fixtures/map_seed11.json  terrain (obstacle boxes, three zones incl. one interference zone at 0.5), nodes, two enemy structures
  scenarios/patrol.json     friendly units with sensor radii and scripted waypoints; enemy units on loops
  verify.gd
  qa/smoke.json, qa/checklist.md
```

### 1. `truth.gd`

Holds everything, ticks at 20 Hz: friendlies `{uid, pos, sensor_wu, layer 0}` following scripted waypoints; enemies `{uid, pos}` on scripted loops; structures `{sid, pos}` static; obstacles as boxes that block line of sight (a segment-box intersection test; "tall" obstacles only); an interference zone as a circle with intensity. `compute_visibility()` per R-089-01, R-089-02, R-089-06: for each friendly, effective radius = sensor × (1 − interference at its position); an enemy is visible if within that radius and no obstacle blocks the segment; the player-visible set is the union; friendlies always visible (R-089-05). Returns `{visible_enemy_uids, visible_structure_sids, circles [{pos, radius_eff}]}`. Recomputed every tick, no memory (R-089-04). `hash()` over positions and the visible set.

### 2. `fog_grid.gd`

Cell grid over the canvas (100 wu cells on a 6,400 wu canvas = 64×64). States: `never_seen`, `explored`, `visible`. `update(circles)`: cells inside any circle become `visible`; cells that were `visible` and now are not become `explored` (if memory on) or `never_seen` (if memory off); nothing ever returns to `never_seen` while memory is on. Recon phase: every cell is `visible` for terrain purposes but the enemy set is empty (R-092-01); Begin sets every cell to `never_seen` except the friendlies' circles (R-092-03), and a check proves terrain stays drawn under `explored`.

### 3. `fog_view.gd`

Draws terrain (ground plane, obstacle boxes, zone patches, node markers with `Label3D` type text) always; the fog quad over it with per-cell colour: `never_seen` opaque black, `explored` 60 percent black, `visible` clear; enemy structures drawn when their cell is `explored` or `visible` (darkened when explored); enemy units drawn only when in the visible set handed in by the root, and the view never receives the others (the root passes a filtered list; a check inspects the view's data). Sensor circles as flat ring meshes at each friendly's effective radius (visibly smaller inside interference, R-094-02); the interference zone drawn as a hatched or tinted patch so revealed, fogged and interference read as three treatments (R-094-01). Friendlies as faction-coloured blocks with a heading.

### 4. Camera, HUD, input

Camera copied from the landscape rig, fixed top-down, heights 500 to 8,000 wu, canvas-bounded, `qa_camera(height, x, z)`. HUD: phase label ("RECON" or "MISSION t=..."), Begin Mission (B), memory checkbox (M) default on, seed spinbox, Reset (R), Step (T) 20 ticks, Play (Space), readout "visible enemies n of N, cells seen p percent". Left click selects a friendly to show its circle bold; right click issues a move to it (straight line, no steering needed).

### 5. The contract

`PLANTS = ["fog-leak", "no-memory", "recon-shows-enemy", "radius-ignored", "los-ignored", "seed-ignored"]`. `qa_state()`: `seed`, `hash`, `phase`, `tick`, `memory`, `visible_enemy_uids`, `view_enemy_uids` (what the view actually holds), `enemy_count_total`, `cells {never_seen, explored, visible}`, `circles` (uid to effective radius), `enemies_px` (uid to `[x, y]` for every enemy, from truth, for oracles only), `timing_ms {tick_avg}`, `regen_count`. `qa_seed(n)`; `qa_set("memory", bool)`, `qa_set("phase", "mission")` (same as Begin); `qa_camera(height, x, z)`; `qa_tick(n)`; `qa_move(uid, x, z)`.

Fault sites: `fog-leak` hands the view every enemy; `no-memory` sends unseen cells back to `never_seen` even with memory on; `recon-shows-enemy` draws enemies in recon; `radius-ignored` uses the raw sensor radius inside interference; `los-ignored` skips the obstacle segment test; `seed-ignored` forces seed 11 (the seed jitters enemy loop phases).

### 6. Build order (commit after each)

verify.gd red and stubs; truth with visibility; fog grid; view with three states and enemy filter; circles and interference; recon and Begin; camera, HUD, input; smoke, checklist, screenshots, README.

## TDD protocol

1. Step 0: write `verify.gd` (`extends SceneTree`; `_init` runs one `_check_<id>()` per row of the check table below, then `quit(0)` or `quit(1)`; prints `FAIL: <id> <msg>` per failure and `VERIFY OK` on success, sharing one `_assert(cond, msg)`). Run `scripts/mockup_verify.sh fog`: it must print exactly one `FAIL:` line per check and exit 1. Commit as `test(mockup/fog): red verify.gd`.
2. Step 0 also: the root stub with `PLANTS`, `qa_state`, `qa_plant` (returns true for every listed id even before the feature exists), `qa/smoke.json`, `qa/checklist.md` copied from the template below, the `QADriver` child in the `.tscn`, and `docs/northstar/research/mockups/fog/README.md` with a one-paragraph "Design as built" placeholder.
3. Each build step: implement, run `mockup_verify.sh`, the named checks flip green, commit. Never edit a threshold; Westley owns them.
4. Every check carries its plant in a `# plant: <id>` line. Once the feature behind a check exists, `scripts/mockup_verify.sh fog --plant <id>` must print `PLANT <id> LIVE`; if it prints `DEAD`, fix the check or the fault site before committing.
5. Headless checks (verify.gd, dummy renderer, no autoloads): pure data, node-tree shape, API contract, determinism, CPU timing. Instantiate the scene when a check needs the tree: `var root = load("res://scenes/mockups/fog/fog_mockup.tscn").instantiate(); get_root().add_child(root); await process_frame`. Never call screenshot verbs headless.
6. Xvfb checks (driver plus shell): pixel diffs, pixel probes at projected positions, screenshot inspection, `fps_ms`. One clean run and one run per plant, in separate out dirs under your scratchpad; never mix the `plant` verb into a clean script.
7. `verify.gd` stays between 100 and 200 lines: at most 12 checks, each at most 15 lines.
8. After the clean and planted Xvfb runs, fill `qa/checklist.md` with the measured numbers, Read every screenshot, answer every visual question with the proving screenshot's name, fix every "no", rerun, and list what you cannot judge under `HELD:`.
9. Copy the review screenshots (1920x1080 batch) into `docs/northstar/research/mockups/fog/pass1/` and commit them; do not commit any other run output.
10. The report's check table lists, per check: clean result, plant id, planted result.

## Verify checks (`verify.gd`)

| id | check | where | plant |
|---|---|---|---|
| DET-1 | `step` 300 ticks twice from seed 11 gives equal hashes; seed 12 differs | H | `seed-ignored` |
| VIS-2 | the 60-second numbers: sensor 700 sees at 650 not 750; at interference 0.5 sees at 350 not 351 (radius 700 × 0.5); union over two friendlies equals the set-union of their sets | H | `radius-ignored` |
| LOS-3 | an enemy in range behind a tall obstacle is not visible; the same enemy with the obstacle removed is | H | `los-ignored` |
| VIEW-4 | after a tick with 3 of 8 enemies visible, `view_enemy_uids` has exactly those 3 and the view's node count for enemies is 3 | H (instantiate) | `fog-leak` |
| RECON-5 | in recon every cell is `visible` for terrain, `view_enemy_uids` is empty, and no unit moves over 20 ticks; after Begin, cells outside the friendlies' circles are `never_seen` and terrain nodes are still drawn | H | `recon-shows-enemy` |
| MEM-6 | a cell that was `visible` becomes `explored` when the circle leaves it and never `never_seen` again while memory is on; with memory off it becomes `never_seen` | H | `no-memory` |
| STRUCT-7 | an enemy structure in an `explored` cell is drawn (darkened) and one in `never_seen` is not; enemy units in `explored` cells are not drawn | H (instantiate) | `fog-leak` |
| SYM-8 | A sees B does not imply B sees A when B's sensor is smaller (R-089-06) | H | none; self-test |
| JSON-9 | `qa_state()` round-trips through JSON with every key; `qa_plant("nope")` false; every `PLANTS` id true | H | none |
| TIME-10 | `timing_ms.tick_avg` under 3 ms for 8 friendlies, 12 enemies, a 64×64 grid | H | none |

Xvfb oracles: HIDDEN-X (for every enemy uid not in `visible_enemy_uids`, the pixel at `enemies_px[uid]` in `mission_t100.png` is fog-black or dim terrain, never the enemy colour; for every visible one it is the enemy colour; under `fog-leak` a hidden position shows the enemy colour); RECON-X (`recon.png` has no enemy-colour pixels at any `enemies_px`; under `recon-shows-enemy` it does); TRAIL-X (`diff mission_t100.png mission_t300.png` ≥ 0.02 and `cells.explored` grew); MEM-X (`diff memory_on.png memory_off.png` ≥ 0.05 and `cells.explored == 0` when memory off); RING-X (the selected friendly's ring radius in pixels inside interference is smaller than outside: compare the two `circles` values and confirm by cropping); ERR-0, GPU-0, DET-1 pixel.

## QA script and screenshots

`qa/smoke.json`: `state boot`; `seed 11`; `call qa_camera 4000 3200 3200`; `screenshot recon`; `state recon`; `call qa_set phase mission`; `screenshot begin`; `state begin`; `call qa_tick 100`; `screenshot mission_t100`; `state mission_t100`; `call qa_tick 200`; `screenshot mission_t300`; `state mission_t300`; `screenshot memory_on`; `call qa_set memory false`; `wait_frames 2`; `screenshot memory_off`; `state memory_off`; `call qa_set memory true`; `call qa_move 1 1500 1500`; `call qa_tick 200`; `screenshot in_interference`; `state in_interference`; `call qa_camera 1200 1500 1500`; `screenshot close_ring`; `seed 12`; `call qa_set phase mission`; `call qa_tick 100`; `state seed12`; `key R`; `state after_r`. Review batch at 1920x1080: recon, begin, t100, t300, memory off, in interference, close ring, map zoom (8 shots) into `docs/northstar/research/mockups/fog/pass1/`.

## Checklist: visual questions

Read each PNG beside `docs/bible/references/E-12/Unexplored.png` and `ExploredButWithoutVision.png` and the derived rule in `references/E-12/notes.md`.

| q | question | proves |
|---|---|---|
| Q1 | Are the three states tellable apart at a glance: black, dimmed-with-terrain, clear? | derived rule, R-094-01 |
| Q2 | In `mission_t300.png`, can you see where the units have been (the explored trail) and that no enemy unit is drawn there? | S-089, memory rule |
| Q3 | Is the enemy structure visible but darkened in explored space? | derived rule |
| Q4 | In `recon.png`, is every obstacle, zone and node readable and is there no enemy anywhere? | R-092-01 |
| Q5 | Does the ring inside the interference zone read as smaller, and does the zone read as a third treatment? | R-094-02 |
| Q6 | With memory off, is everything without current vision black? | fog-memory decision |
| Q7 | Any magenta, black-where-it-should-not-be, clipped or overlapping text at 720p? | hygiene |

## What the report must answer

1. Do the three states read; what dim level did you use and does it need to change?
2. Does the recon-then-fog moment read as a mode change?
3. Whether the view ever held a hidden enemy (VIEW-4's evidence) and how the filter is structured so the real client can copy it.
4. Frame time under llvmpipe at 720p with the fog quad updating every tick.
5. Under-defined points with candidates: fog cell size, dim level, edge softness, whether sensor circles show for unselected units (Q-094-01), ghost markers (Q-089-01), how interference should look.

## Finishing report

Write it as your final message and also as the "Design as built" and "Questions for Westley" sections of `docs/northstar/research/mockups/fog/README.md` (normal prose; that file is read by Westley), ending with a "Next step" line that says the pass-1 screenshots are in `pass1/` and the mockup awaits his look. The report answers the numbered questions below, includes the check table (check, clean result, plant, planted result), the answers to the visual questions with proving screenshots, the `HELD:` list, timings (`timing_ms`, `fps_ms` under llvmpipe at 720p), the list of commits, and every under-defined point with two or three candidates and no decision.

## Verification (done when all of these hold)

- `scripts/mockup_verify.sh fog` prints `VERIFY OK`, exit 0; `scripts/mockup_verify.sh fog --plant <id>` prints `PLANT <id> LIVE` for every id in `PLANTS`.
- `scripts/mockup_qa.sh run fog scenes/mockups/fog/qa/smoke.json <scratch>/fog/clean` gives `exit.txt` 0, `errors.txt` 0, no `UNIFORM` line, `_qa.adapter` containing `llvmpipe`; a second clean run matches the first on every `hash` and every screenshot (`diff` under 0.005).
- One run per plant under `<scratch>/fog/plant-<id>` and every deterministic oracle in the checklist shows the planted number on the wrong side of its threshold.
- `qa/checklist.md` is filled; every visual question is answered or held; the pass-1 screenshots are committed under `docs/northstar/research/mockups/fog/pass1/`.
- `git status --short` on your branch shows only `scenes/mockups/fog/**` and `docs/northstar/research/mockups/fog/**`; `git diff --stat main -- scenes/tactical scenes/world scenes/main_menu scenes/mockups/landscape scenes/mockups/_shared tests csrc docs/bible docs/northstar/PLAN.md project.godot` is empty.
- The interactive command (`~/.local/bin/godot --scene scenes/mockups/fog/fog_mockup.tscn`) is documented in the README with its hotkeys; you cannot run it on Westley's seat, so confirm instead that a wrapper run without `--qa-script` leaves the driver inert (no `_run.json`).
