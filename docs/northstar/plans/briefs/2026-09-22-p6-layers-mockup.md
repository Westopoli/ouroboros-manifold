# HANDOFF BRIEF — P6 two-layer prototype mockup

Self-contained. Handed to an implementor 2026-09-22. Sibling briefs: `2026-09-22-mockup-qa-harness.md` (the harness you use), `2026-09-21-p2-landscape-mockup.md` (the shape to copy).

## Context

Rung P6 of the prototype ladder (`docs/northstar/PLAN.md:167`): "Two-layer prototype (the layer design phase): layer changes elevation and vision per rule; ring height and dimming; planted wrong-height." This is prototype story `S-P10` from `docs/legacy/mvp/feature_mvps.md` (E-01 block): exactly two layers; a selected unit can be ordered to the other layer and visibly rises or drops over a per-type duration; terrain marks some cells blocked on layer 2; a unit sees the other layer at a shorter range than its own; the HUD shows each unit's layer and which layer the player is focused on. It draws on E-01 stories S-002 (hard transfer, R-002-01, R-002-02, R-002-05), S-004 (transition takes time, R-004-01, R-004-03, R-004-05), S-005 (cross-layer vision, R-005-02, R-005-03 with the adjacent factor 0.50), S-009 (ring per layer, strip focus, R-009-01, R-009-03, R-009-04), S-010 (layers read as height, R-010-01 to R-010-03), at their smallest, without claiming any of them Ready. Read `docs/bible/epics/E-01-layer-system.md` lines 43 to 58, 76 to 106, 147 to 171. The README decision (`docs/northstar/README.md:29`) says the layer system gets a real design phase; this mockup is its first option and testers' reactions feed that phase.

The 60-second paragraph: a Raider and a Bastion on layer 3 next to a tall obstacle are ordered to layer 5; the Raider rises within a second, the Bastion takes several seconds, each unit's ring changes colour when its layer changes; an enemy under the obstacle on layer 1 is unseen; an enemy on layer 4 within half the Raider's sensor range is seen by the Raider and not the Bastion; a transfer through a blocked zone waits until the unit moves clear. Reduce to two layers (1 and 2) with the same beats. References: `docs/bible/references/E-01/notes.md` is a stub (no images). Judge against the paragraph and the height rule R-010-03 (a unit ordered up one layer moves vertically by more than 5 percent of the viewport height at a fixed camera), and hold what you cannot judge.

Layer height on screen is under-defined at landscape scale (the landscape mockup's terraces are hundreds to thousands of wu); use 600 wu between layers as the candidate and list alternatives.

## Rules for the implementor

- If you are an Opus or Fable chat: plan and review, Sonnet sub-agents build; ask Westley about his Claude usage before a batch of more than two doers. If you are a Sonnet chat: do the work yourself, spawn no sub-agents.
- You are in a git worktree on branch `mockup/layers`. Commit there after each working step with the trailer `Co-Authored-By: Claude <model> <noreply@anthropic.com>`. Do not push; the design chat merges into `main`. Never stage files you did not create or edit for this brief. Never check out another branch.
- Touch only `scenes/mockups/layers/**` and `docs/northstar/research/mockups/layers/**`. Nothing else: not `csrc/`, `simulation/`, `tests/`, `docs/bible/`, other `docs/northstar/`, other `scenes/`, `scenes/mockups/_shared/` (if the harness is broken, stop and report; do not patch it), `project.godot`.
- This is a mockup: placeholder primitives only (boxes, cylinders, prisms, planes, quads, flat colours, `Label3D`, `Control._draw`). No imported models, no textures beyond vertex colour and flat shading. GDScript only. No autoload dependency and no dependency on any other scene: the scene must work if every autoload were removed. You may copy code from the legacy files named under "Godot facts" into your directory and you may reference `theme/fonts/*.ttf` by `res://` path; you may not `preload` or `load` anything outside your directory except `res://scenes/mockups/_shared/qa_driver.gd` and `qa_plants.gd`.
- Renderer parity: your QA renders run under the Compatibility renderer on software GL; Westley views Forward+ on an RTX 3060. Use only what looks the same in both: `StandardMaterial3D` (vertex colour as albedo is fine), `ArrayMesh`/`ImmediateMesh`, `MultiMeshInstance3D`, `Label3D`, one `DirectionalLight3D`, `WorldEnvironment` sky, ambient and depth fog, `CanvasLayer`, `CPUParticles3D`. Do not use SDFGI, VoxelGI, volumetric fog, SSR, SSAO, SSIL, glow, decals, `GPUParticles3D`, or screen-texture shaders.
- No era named in any script identifier or node name (bible rule R-145-01). Where the era shows it is data under `kits/` or `fixtures/`.
- Deterministic: every random draw comes from your own `RandomNumberGenerator` seeded from an integer seed; never the global RNG, never the wall clock. Same seed, same state hash, same pixels.
- **Never set `DISPLAY` yourself and never use `:0` or `:1`.** Every windowed run goes through `scripts/mockup_qa.sh`, which creates a private Xvfb. The GPU belongs to the Agora chain.
- No docstrings or comments except the `# plant: <id>` line above each check in `verify.gd`. Minimal, direct code.
- When something in this brief is under-defined, do not decide: build the simplest thing that shows the question and list it in the finishing report with two or three candidate answers.

## Godot facts (reconnaissance 2026-09-22)

- Binary `~/.local/bin/godot`, `4.6.3.stable.official`. Project root is the repo root. `project.godot` declares Forward+, 1920x1080, fullscreen, stretch `canvas_items`/`expand`, no `[input]` map (use raw keycodes as the landscape mockup does). Nineteen autoloads run on any `--path .` scene launch; one spawns the Python sim and warns about a mac path; harmless. `--script` SceneTree mode loads no autoloads.
- Scene convention: a short `.tscn` (root node with your root script, a `QADriver` child with `res://scenes/mockups/_shared/qa_driver.gd`, and whatever nodes you need) plus scripts. Every mockup scene in this repo is launched by path, never as the main scene. Westley's command is `~/.local/bin/godot --scene scenes/mockups/layers/layers_mockup.tscn` from the repo root; keep that name.
- The harness (read `scenes/mockups/_shared/README.md` first): `scripts/mockup_verify.sh layers [--plant id]` runs your `verify.gd` headless; `scripts/mockup_qa.sh run layers <script.json> <outdir> [--res 1280x720] [--plant id]` runs the scene under Xvfb with `--fixed-fps 30` and replays a JSON action list (`wait_frames`, `move`, `click`, `click_node`, `drag`, `wheel`, `key`, `key_down`, `key_up`, `call`, `seed`, `plant`, `pause`, `screenshot`, `state`, `tree`, `wait_file`); `scripts/mockup_qa.sh diff a.png b.png` prints the fraction of differing pixels; `scripts/mockup_qa.sh scan <outdir>` writes `errors.txt`, `shots.txt`, `marks.txt`. Your scene root must implement the contract: `const PLANTS: Array[String]`, `qa_state() -> Dictionary` (JSON-safe, canonical from data, never from HUD labels; always `seed`, `hash`, `timing_ms`, `regen_count` plus the keys named below), `qa_plant(id) -> bool`, `qa_seed(n)`, and the optional `qa_set(name, value)` and `qa_camera(...)` this brief names. Plants are activated through `preload("res://scenes/mockups/_shared/qa_plants.gd").is_active("<id>")` at a one-line fault site.
- Under Xvfb a 3D scene renders at a few frames per second; keep QA scripts short (a few hundred frames), use 1280x720 by default, and take the 1920x1080 review shots only in the final batch. Window pixels equal screenshot pixels; canvas coordinates are scaled by the stretch (use `click_node` rather than raw pixels for HUD buttons).
- Input gotchas: a full-rect `Control` with the default `mouse_filter = STOP` swallows synthetic mouse events before `_unhandled_input`; put world mouse handling in `_unhandled_input` on a non-Control node and set every full-rect Control to `MOUSE_FILTER_IGNORE` unless it is the designated click surface. Set `focus_mode = FOCUS_NONE` on Buttons and click empty ground before key verbs so a SpinBox does not eat letters.
- Copy the feel of the landscape mockup's HUD and camera code where it fits: `scenes/mockups/landscape/hud.gd` (kit discovery, timing prints, screenshot key), `camera_rig.gd` (pan, edge scroll, wheel zoom, public `pan_to`/`set_height`).
- Colours available to copy: `autoload/theme_constants.gd` (BASE `#0A0D12`, PRIMARY `#e8e6e1`, ERA_ACCENTS), faction colours `#4099FF` and `#FF4738` from `assets/eras/settled_reach/manifest.json`, the hue-from-id function in `autoload/faction_palette.gd:38`. Fonts: `theme/fonts/` (JetBrainsMono, Newsreader).
- Legacy to copy from (never to load): `scenes/tactical/unit_renderer.gd:356-420` (`_update_layer_rings`: a `TorusMesh` ring per unit at `layer * LAYER_HEIGHT + 2`, radii 50/44, per-layer `LAYER_COLORS` at line 9) and `:266-267` (non-focused layer dimmed to alpha `INACTIVE_LAYER_ALPHA = 0.4` from `autoload/era_config.gd`); `scenes/tactical/hud.gd:697-770` (layer selector strip and readout, five colour markers); `scenes/tactical/input_router.gd:246-262` (Tab cycles the active layer, hard-transfer and preference commands). The legacy has no transition animation; the toy sim here must add one. Transition durations per type from R-004-01's config: Raider 1.0 s, Bastion 5.0 s (the two types this mockup uses).

## What to build

```
scenes/mockups/layers/
  layers_mockup.tscn        root Node3D "LayersMockup" with layers_mockup.gd; children World, CameraRig, HUD, QADriver
  layers_mockup.gd          the contract; owns map load, tick loop, selection, view sync
  toy_sim.gd                RefCounted: units with layer, pending transfer, transition timer; blocked mask on layer 2; cross-layer vision; step(); hash()
  layer_view.gd             Node3D: two ground planes (layer 1 at y=0, layer 2 at y=LAYER_HEIGHT, the upper one translucent), blocked cells marked on layer 2, units at their layer height with rings, dimming of the non-focused layer, sensor rings (own layer full, other layer half)
  camera_rig.gd             fixed top-down pan, wheel zoom, edge scroll, canvas-bounded (copy from landscape); pitch 60° so height reads
  hud.gd                    CanvasLayer: layer strip (two slots, focused highlighted), per-unit layer list, seed, Reset (R), Step (T), Play (Space), transfer buttons (1, 2)
  fixtures/map_seed11.json  a 4,000 wu canvas, a tall obstacle box, a blocked-on-layer-2 region around it, a vantage marker (unused, listed)
  verify.gd
  qa/smoke.json, qa/checklist.md
```

### 1. `toy_sim.gd`

20 Hz. Units `{uid, type (fast or slow), faction, pos, layer 1 or 2, pending_transfer, transition {from, to, ticks_left}, sensor_wu}`; two friendlies (a fast type with 1.0 s and a slow type with 5.0 s transition, sensor 800 and 300) and three enemies placed per the paragraph (one under the obstacle on layer 1, one on layer 2 within half the fast unit's sensor, one on layer 2 beyond it). A blocked mask on layer 2 (100 wu cells) around the obstacle. `transfer(uid, layer)`: same layer completes immediately (R-002-05); if the unit's cell is open on the target layer the transition starts this tick and completes after the type's duration (R-002-01, R-004-01); if blocked it stays pending and starts on the first tick the unit stands on an open cell (R-002-02); a second transfer replaces a pending one; the unit's `layer` field flips on the completion tick only. `move(uid, x, z)` walks the unit straight at 80 wu/s and keeps a pending transfer (R-002-04). `visible_by(uid)`: same-layer enemies within `sensor`; other-layer enemies within `sensor × 0.5` (R-005-02, R-005-03). `hash()` over positions, layers, transitions.

### 2. `layer_view.gd`

`LAYER_HEIGHT = 600` (candidate). Ground plane per layer; the layer-2 plane is a translucent grid (alpha 0.25) so layer 1 stays visible under it; blocked cells on layer 2 drawn as red-tinted patches on the upper plane; the tall obstacle as a box spanning both layers. Units as blocks at `y = (layer − 1) × LAYER_HEIGHT`, and during a transition at the lerp of the two heights by `ticks_left` (R-010-02). A ring under each unit coloured by layer (two colours), switching on the completion tick (R-009-01). The non-focused layer's units and plane drawn at alpha 0.4 (dimming). Two sensor rings around the selected unit: a full ring on its own layer height and a half-radius ring at the other layer's height. Enemies drawn only when in the union of the friendlies' visible sets (so the unseen layer-1 enemy is absent). Selection ring on the selected unit.

### 3. Camera, HUD, input

Camera copied from the landscape rig with a fixed pitch of 60° (so the vertical offset reads; note that R-103-03's interim is top-down and list the pitch as under-defined), heights 800 to 6,000, `qa_camera(height, x, z)`. HUD: a two-slot layer strip at the right edge (Tab cycles focus, 1 and 2 focus directly), a list of units with their layer colour swatch, transfer buttons "To layer 1" and "To layer 2" acting on the selection (also keys Q and E), Step (T), Play (Space), Reset (R), seed. Left click selects a friendly; right click moves it.

### 4. The contract

`PLANTS = ["instant-transfer", "blocked-ignored", "cross-layer-full-range", "ring-colour-same", "no-dimming", "wrong-height"]`. `qa_state()`: `seed`, `hash`, `tick`, `focus_layer`, `layer_height_wu`, `units` (uid to `{type, layer, pos, transition {to, ticks_left} or null, pending}`), `units_px` (uid to `[x, y]`), `visible_enemy_uids`, `rings` (uid to colour hex), `timing_ms {tick_avg}`, `regen_count`. `qa_seed(n)`; `qa_set("focus_layer", n)`; `qa_camera(height, x, z)`; `qa_tick(n)`; `qa_transfer(uid, layer)`; `qa_move(uid, x, z)`; `qa_select(uid)`.

Fault sites: `instant-transfer` completes any transfer on the issuing tick; `blocked-ignored` starts a transfer on a blocked cell; `cross-layer-full-range` uses the full sensor across layers; `ring-colour-same` gives both layers one ring colour; `no-dimming` draws the non-focused layer at full alpha; `wrong-height` draws every unit at layer 1's height regardless of layer (the ladder's "planted wrong-height").

### 5. Build order (commit after each)

verify.gd red and stubs; toy_sim transfers and blocking; cross-layer vision; view with heights, rings, dimming; camera, HUD, input; smoke, checklist, screenshots, README.

## TDD protocol

1. Step 0: write `verify.gd` (`extends SceneTree`; `_init` runs one `_check_<id>()` per row of the check table below, then `quit(0)` or `quit(1)`; prints `FAIL: <id> <msg>` per failure and `VERIFY OK` on success, sharing one `_assert(cond, msg)`). Run `scripts/mockup_verify.sh layers`: it must print exactly one `FAIL:` line per check and exit 1. Commit as `test(mockup/layers): red verify.gd`.
2. Step 0 also: the root stub with `PLANTS`, `qa_state`, `qa_plant` (returns true for every listed id even before the feature exists), `qa/smoke.json`, `qa/checklist.md` copied from the template below, the `QADriver` child in the `.tscn`, and `docs/northstar/research/mockups/layers/README.md` with a one-paragraph "Design as built" placeholder.
3. Each build step: implement, run `mockup_verify.sh`, the named checks flip green, commit. Never edit a threshold; Westley owns them.
4. Every check carries its plant in a `# plant: <id>` line. Once the feature behind a check exists, `scripts/mockup_verify.sh layers --plant <id>` must print `PLANT <id> LIVE`; if it prints `DEAD`, fix the check or the fault site before committing.
5. Headless checks (verify.gd, dummy renderer, no autoloads): pure data, node-tree shape, API contract, determinism, CPU timing. Instantiate the scene when a check needs the tree: `var root = load("res://scenes/mockups/layers/layers_mockup.tscn").instantiate(); get_root().add_child(root); await process_frame`. Never call screenshot verbs headless.
6. Xvfb checks (driver plus shell): pixel diffs, pixel probes at projected positions, screenshot inspection, `fps_ms`. One clean run and one run per plant, in separate out dirs under your scratchpad; never mix the `plant` verb into a clean script.
7. `verify.gd` stays between 100 and 200 lines: at most 12 checks, each at most 15 lines.
8. After the clean and planted Xvfb runs, fill `qa/checklist.md` with the measured numbers, Read every screenshot, answer every visual question with the proving screenshot's name, fix every "no", rerun, and list what you cannot judge under `HELD:`.
9. Copy the review screenshots (1920x1080 batch) into `docs/northstar/research/mockups/layers/pass1/` and commit them; do not commit any other run output.
10. The report's check table lists, per check: clean result, plant id, planted result.

## Verify checks (`verify.gd`)

| id | check | where | plant |
|---|---|---|---|
| DET-1 | the same command stream over 200 ticks gives equal hashes twice; transition start and end ticks are identical (R-004-05) | H | none; self-test with a global-RNG variant |
| DUR-2 | the fast type completes a transfer in exactly 20 ticks and the slow type in exactly 100; ordered on the same tick, the fast completes first (R-004-03) | H | `instant-transfer` |
| BLOCK-3 | a transfer issued on a blocked cell stays pending with `layer` unchanged; after a move to an open cell it starts on that tick and completes after the duration (R-002-02) | H | `blocked-ignored` |
| SAME-4 | a transfer to the unit's current layer completes immediately with no transition (R-002-05) | H | none |
| VIS-5 | the fast unit sees the layer-2 enemy at 350 wu (sensor 800 × 0.5 = 400) and not at 450; the slow unit (sensor 300) sees neither; the layer-1 enemy under the obstacle is unseen by both | H | `cross-layer-full-range` |
| HEIGHT-6 | after a completed transfer to layer 2 the unit's node `y` equals `layer_height_wu`; mid-transition it is strictly between | H (instantiate) | `wrong-height` |
| RING-7 | ring colours differ between layers and the ring colour flips on the completion tick, not before (R-009-01) | H (instantiate) | `ring-colour-same` |
| DIM-8 | with focus on layer 1, layer-2 units' instance alpha is 0.4; with focus 2, layer-1's is | H (instantiate) | `no-dimming` |
| FOCUS-9 | Tab cycles focus 1 to 2 to 1; the strip's highlighted slot follows (R-009-03) | H (instantiate) | none |
| JSON-10 | `qa_state()` round-trips through JSON with every key; `qa_plant("nope")` false; every `PLANTS` id true | H | none |

Xvfb oracles: HEIGHT-X (`units_px[fast]` before and after a transfer differ vertically by more than 5 percent of the window height, R-010-03; under `wrong-height` they are equal); MID-X (in `transfer_mid.png` the unit's crop differs from both `transfer_before.png` and `transfer_after.png`; under `instant-transfer` mid equals after); DIM-X (`diff focus1.png focus2.png` ≥ 0.05; under `no-dimming` < 0.01); RING-X (the ring colour under the unit in `transfer_after.png` differs from `transfer_before.png`; under `ring-colour-same` equal); BLOCK-X (`blocked_attempt.png` after 30 ticks shows the unit still at layer-1 height and `pending == true`); ERR-0, GPU-0, DET-1 pixel.

## QA script and screenshots

`qa/smoke.json`: `state boot`; `seed 11`; `call qa_camera 2500 2000 2000`; `call qa_select 1`; `screenshot transfer_before`; `state transfer_before`; `call qa_transfer 1 2`; `call qa_tick 10`; `screenshot transfer_mid`; `state transfer_mid`; `call qa_tick 20`; `screenshot transfer_after`; `state transfer_after`; `call qa_transfer 2 2`; `call qa_tick 50`; `screenshot slow_mid`; `state slow_mid`; `call qa_set focus_layer 1`; `screenshot focus1`; `call qa_set focus_layer 2`; `screenshot focus2`; `state focus2`; `call qa_move 1 900 900`; `call qa_tick 60`; `call qa_transfer 1 1`; `call qa_tick 30`; `screenshot blocked_attempt`; `state blocked_attempt`; `call qa_move 1 1600 1600`; `call qa_tick 60`; `screenshot blocked_cleared`; `state blocked_cleared`; `key R`; `state after_r`. Review batch at 1920x1080: before, mid, after, slow mid, focus 1, focus 2, blocked attempt, blocked cleared (8 shots) into `docs/northstar/research/mockups/layers/pass1/`.

## Checklist: visual questions

Judge against the E-01 60-second paragraph and R-010-03 (no reference images exist; say so in the README).

| q | question | proves |
|---|---|---|
| Q1 | Does the unit on layer 2 look higher than the one on layer 1, not merely a different colour? | R-010-01, R-010-03 |
| Q2 | Does the rise read as motion (mid-frame between the two heights), and does the slow type visibly lag the fast one? | R-010-02, R-004-03 |
| Q3 | Can you tell which layer every unit is on from its ring, and which layer is focused from the strip and the dimming? | R-009-01, R-009-03 |
| Q4 | Does the blocked region read as blocked on layer 2 and does the waiting unit read as waiting? | R-002-02 |
| Q5 | Are the two sensor rings legible (full on own layer, half on the other)? | R-005-02 |
| Q6 | Any magenta, black, clipped or overlapping text at 720p? | hygiene |

## What the report must answer

1. Does the two-layer idea read on screen at all, at this camera pitch and height spacing?
2. What breaks if the layer height is 250 wu or 2,000 wu instead of 600 (try both once, screenshot, revert)?
3. Whether dimming or the translucent upper plane hurt reading the lower layer.
4. Frame time under llvmpipe at 720p.
5. Under-defined points with candidates: layer height, camera pitch versus the top-down interim, blocked-cell marking, the strip's look, whether the unit is targetable mid-transition (R-004-02, not modelled), transition durations at large landscape scale.

## Finishing report

Write it as your final message and also as the "Design as built" and "Questions for Westley" sections of `docs/northstar/research/mockups/layers/README.md` (normal prose; that file is read by Westley), ending with a "Next step" line that says the pass-1 screenshots are in `pass1/` and the mockup awaits his look. The report answers the numbered questions below, includes the check table (check, clean result, plant, planted result), the answers to the visual questions with proving screenshots, the `HELD:` list, timings (`timing_ms`, `fps_ms` under llvmpipe at 720p), the list of commits, and every under-defined point with two or three candidates and no decision.

## Verification (done when all of these hold)

- `scripts/mockup_verify.sh layers` prints `VERIFY OK`, exit 0; `scripts/mockup_verify.sh layers --plant <id>` prints `PLANT <id> LIVE` for every id in `PLANTS`.
- `scripts/mockup_qa.sh run layers scenes/mockups/layers/qa/smoke.json <scratch>/layers/clean` gives `exit.txt` 0, `errors.txt` 0, no `UNIFORM` line, `_qa.adapter` containing `llvmpipe`; a second clean run matches the first on every `hash` and every screenshot (`diff` under 0.005).
- One run per plant under `<scratch>/layers/plant-<id>` and every deterministic oracle in the checklist shows the planted number on the wrong side of its threshold.
- `qa/checklist.md` is filled; every visual question is answered or held; the pass-1 screenshots are committed under `docs/northstar/research/mockups/layers/pass1/`.
- `git status --short` on your branch shows only `scenes/mockups/layers/**` and `docs/northstar/research/mockups/layers/**`; `git diff --stat main -- scenes/tactical scenes/world scenes/main_menu scenes/mockups/landscape scenes/mockups/_shared tests csrc docs/bible docs/northstar/PLAN.md project.godot` is empty.
- The interactive command (`~/.local/bin/godot --scene scenes/mockups/layers/layers_mockup.tscn`) is documented in the README with its hotkeys; you cannot run it on Westley's seat, so confirm instead that a wrapper run without `--qa-script` leaves the driver inert (no `_run.json`).
