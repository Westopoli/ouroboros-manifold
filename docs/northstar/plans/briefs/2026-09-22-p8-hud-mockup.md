# HANDOFF BRIEF — P8 camera, HUD and selection mockup

Self-contained. Handed to an implementor 2026-09-22. Sibling briefs: `2026-09-22-mockup-qa-harness.md` (the harness you use), `2026-09-21-p2-landscape-mockup.md` (the shape to copy).

## Context

The client surfaces that ride rungs P4 to P7 of the prototype ladder and are listed in Round 1 (`docs/legacy/mvp/feature_mvps.md`, E-16 block): S-103 (the tactical camera, fixed top-down interim; R-103-01 to R-103-04), S-105 (selection and control groups; R-105-01 to R-105-06, with Q-105-01 answered: a drag box selects every layer and the layer hotkeys narrow), and prototype `S-P12` (the HUD at its smallest: selection panel, one objective line with progress, layer indicator, mission clock; the lean-HUD reference wait is for S-104 proper). Read `docs/bible/epics/E-16-client-camera-hud-and-world-view.md` lines 28 to 74, and 41 to 59 for the S-104 layout words that S-P12 borrows (objectives top-left, clock top-right, selection bottom-centre, control-group tabs, layer strip on the right edge, nothing else). The README decision (`docs/northstar/README.md:30`): HUD beyond the IGoP reference is TBD design; simple mockups, iterated on feedback.

The 60-second paragraph (E-16, line 22): the HUD shows objectives top-left, clock top-right, portraits bottom-centre, a minimap, control-group tabs, the commander bottom-right, a five-slot layer strip on the right edge; pan, zoom, box-select, bind a control group to 1, press 1 and the group is selected and the tab highlights. Reduce to S-P12's four elements plus the group tabs; leave the minimap, commander and portraits out and list them. Reference: `docs/bible/references/E-16/E-16.png` (IGoP HUD: segmented bars top-left, minimap bottom-left, command card bottom-centre, selected-unit panel bottom-right) with its row in `references/E-16/notes.md`; read it for the "tells the player what is needed and nothing else" aspect, not the layout.

This mockup is the interaction layer alone: a fixed top-down camera over a flat canvas with toy units wandering on two layers, click and box selection across layers, narrowing by layer hotkey, exclusive control groups with recall and double-tap centring, Tab cycling the layer strip's focus, no select-all of any kind, and a lean HUD. Selection logic lives in a headless-testable class.

## Rules for the implementor

- If you are an Opus or Fable chat: plan and review, Sonnet sub-agents build; ask Westley about his Claude usage before a batch of more than two doers. If you are a Sonnet chat: do the work yourself, spawn no sub-agents.
- You are in a git worktree on branch `mockup/hud`. Commit there after each working step with the trailer `Co-Authored-By: Claude <model> <noreply@anthropic.com>`. Do not push; the design chat merges into `main`. Never stage files you did not create or edit for this brief. Never check out another branch.
- Touch only `scenes/mockups/hud/**` and `docs/northstar/research/mockups/hud/**`. Nothing else: not `csrc/`, `simulation/`, `tests/`, `docs/bible/`, other `docs/northstar/`, other `scenes/`, `scenes/mockups/_shared/` (if the harness is broken, stop and report; do not patch it), `project.godot`.
- This is a mockup: placeholder primitives only (boxes, cylinders, prisms, planes, quads, flat colours, `Label3D`, `Control._draw`). No imported models, no textures beyond vertex colour and flat shading. GDScript only. No autoload dependency and no dependency on any other scene: the scene must work if every autoload were removed. You may copy code from the legacy files named under "Godot facts" into your directory and you may reference `theme/fonts/*.ttf` by `res://` path; you may not `preload` or `load` anything outside your directory except `res://scenes/mockups/_shared/qa_driver.gd` and `qa_plants.gd`.
- Renderer parity: your QA renders run under the Compatibility renderer on software GL; Westley views Forward+ on an RTX 3060. Use only what looks the same in both: `StandardMaterial3D` (vertex colour as albedo is fine), `ArrayMesh`/`ImmediateMesh`, `MultiMeshInstance3D`, `Label3D`, one `DirectionalLight3D`, `WorldEnvironment` sky, ambient and depth fog, `CanvasLayer`, `CPUParticles3D`. Do not use SDFGI, VoxelGI, volumetric fog, SSR, SSAO, SSIL, glow, decals, `GPUParticles3D`, or screen-texture shaders.
- No era named in any script identifier or node name (bible rule R-145-01). Where the era shows it is data under `kits/` or `fixtures/`.
- Deterministic: every random draw comes from your own `RandomNumberGenerator` seeded from an integer seed; never the global RNG, never the wall clock. Same seed, same state hash, same pixels.
- **Never set `DISPLAY` yourself and never use `:0` or `:1`.** Every windowed run goes through `scripts/mockup_qa.sh`, which creates a private Xvfb. The GPU belongs to the Agora chain.
- No docstrings or comments except the `# plant: <id>` line above each check in `verify.gd`. Minimal, direct code.
- When something in this brief is under-defined, do not decide: build the simplest thing that shows the question and list it in the finishing report with two or three candidate answers.

## Godot facts (reconnaissance 2026-09-22)

- Binary `~/.local/bin/godot`, `4.6.3.stable.official`. Project root is the repo root. `project.godot` declares Forward+, 1920x1080, fullscreen, stretch `canvas_items`/`expand`, no `[input]` map (use raw keycodes as the landscape mockup does). Nineteen autoloads run on any `--path .` scene launch; one spawns the Python sim and warns about a mac path; harmless. `--script` SceneTree mode loads no autoloads.
- Scene convention: a short `.tscn` (root node with your root script, a `QADriver` child with `res://scenes/mockups/_shared/qa_driver.gd`, and whatever nodes you need) plus scripts. Every mockup scene in this repo is launched by path, never as the main scene. Westley's command is `~/.local/bin/godot --scene scenes/mockups/hud/hud_mockup.tscn` from the repo root; keep that name.
- The harness (read `scenes/mockups/_shared/README.md` first): `scripts/mockup_verify.sh hud [--plant id]` runs your `verify.gd` headless; `scripts/mockup_qa.sh run hud <script.json> <outdir> [--res 1280x720] [--plant id]` runs the scene under Xvfb with `--fixed-fps 30` and replays a JSON action list (`wait_frames`, `move`, `click`, `click_node`, `drag`, `wheel`, `key`, `key_down`, `key_up`, `call`, `seed`, `plant`, `pause`, `screenshot`, `state`, `tree`, `wait_file`); `scripts/mockup_qa.sh diff a.png b.png` prints the fraction of differing pixels; `scripts/mockup_qa.sh scan <outdir>` writes `errors.txt`, `shots.txt`, `marks.txt`. Your scene root must implement the contract: `const PLANTS: Array[String]`, `qa_state() -> Dictionary` (JSON-safe, canonical from data, never from HUD labels; always `seed`, `hash`, `timing_ms`, `regen_count` plus the keys named below), `qa_plant(id) -> bool`, `qa_seed(n)`, and the optional `qa_set(name, value)` and `qa_camera(...)` this brief names. Plants are activated through `preload("res://scenes/mockups/_shared/qa_plants.gd").is_active("<id>")` at a one-line fault site.
- Under Xvfb a 3D scene renders at a few frames per second; keep QA scripts short (a few hundred frames), use 1280x720 by default, and take the 1920x1080 review shots only in the final batch. Window pixels equal screenshot pixels; canvas coordinates are scaled by the stretch (use `click_node` rather than raw pixels for HUD buttons).
- Input gotchas: a full-rect `Control` with the default `mouse_filter = STOP` swallows synthetic mouse events before `_unhandled_input`; put world mouse handling in `_unhandled_input` on a non-Control node and set every full-rect Control to `MOUSE_FILTER_IGNORE` unless it is the designated click surface. Set `focus_mode = FOCUS_NONE` on Buttons and click empty ground before key verbs so a SpinBox does not eat letters.
- Copy the feel of the landscape mockup's HUD and camera code where it fits: `scenes/mockups/landscape/hud.gd` (kit discovery, timing prints, screenshot key), `camera_rig.gd` (pan, edge scroll, wheel zoom, public `pan_to`/`set_height`).
- Colours available to copy: `autoload/theme_constants.gd` (BASE `#0A0D12`, PRIMARY `#e8e6e1`, ERA_ACCENTS), faction colours `#4099FF` and `#FF4738` from `assets/eras/settled_reach/manifest.json`, the hue-from-id function in `autoload/faction_palette.gd:38`. Fonts: `theme/fonts/` (JetBrainsMono, Newsreader).
- Legacy to copy from (never to load): `scenes/tactical/input_router.gd:33-60` (box-select `_draw`: fill `(0.3, 0.8, 1.0, 0.08)`, edge `(0.3, 0.8, 1.0, 0.75)`, width 1.5), `:89-115` (`_handle_digit`, `_finish_selection`), `:119-200` (`_pick_unit_at` with a 30 px radius, `_click_select`, `_box_select` by projected unit positions), `:213-245` (`_bind_group`, `_recall_group`, exclusive membership); note `:201 _select_all_army` exists in the legacy and is forbidden here (R-105-04). `scenes/tactical/hud.gd:385-412` (placement helpers per corner), `:479-560` (`_build_clock`, `_update_clock` from tick at 20 Hz, `_build_selection_panel`), `:675-690` (control-group bar with 10 slots), `:697-770` (layer selector and readout). `scenes/tactical/tactical.gd:185-240` (camera: PAN_SPEED 1500, ZOOM_STEP 300, ZOOM_MIN 150, ZOOM_MAX 12000, edge zone 60 px, wheel zoom). Tests that already encode the selection rules and can be read for cases: `tests/test_input_router_selection.gd`, `tests/test_input_router_control_groups.gd` (read only; do not run or edit).

## What to build

```
scenes/mockups/hud/
  hud_mockup.tscn           root Node3D "HudMockup" with hud_mockup.gd; children World, CameraRig, Input (Node), HUD (CanvasLayer), QADriver
  hud_mockup.gd             the contract; owns the toy units, tick, selection state, camera, HUD sync
  selection.gd              RefCounted: selection set, groups, narrow, add/remove, box; pure functions over unit records; no nodes
  toy_units.gd              RefCounted: 24 units on two layers wandering deterministically (seeded waypoints), two factions, HP; step()
  camera_rig.gd             fixed top-down (pitch 90°), WASD and edge pan, wheel zoom, canvas-bounded, never layer-bound; centre_on(pos)
  input_router.gd           Node: _unhandled_input for click, shift-click, drag box, digits, Ctrl+digit, double-tap digit, layer hotkeys, Tab
  hud.gd                    CanvasLayer: objective line top-left, clock top-right, selection panel bottom-centre, group tabs, layer strip right edge, box-select overlay
  fixtures/mission_seed11.json   one objective (name, kind, scripted progress curve), canvas 6,000 × 6,000 wu
  verify.gd
  qa/smoke.json, qa/box.json, qa/checklist.md
```

### 1. `selection.gd`

Records `{uid, faction, layer, pos, hp}`. `click(uid)` sets the selection to that unit if friendly (R-105-01); `shift_click(uid)` toggles membership (R-105-05); `box(rect_px, project)` selects every friendly whose projected position is inside, on every layer (R-105-01, Q-105-01 b); `narrow(layer)` keeps only that layer's units and does not touch strip focus (R-105-06); `bind(digit)` moves the selected units into group `digit`, removing them from any other group (exclusive membership, R-105-02); `recall(digit)` sets the selection to the group; `recall` twice within 0.4 s reports `centre_requested` with the group's centroid (R-105-02); `commands()` returns the list of command names the class supports and it must not contain any select-all, select-all-army, or select-all-of-type (R-105-04). Dead units drop out of selections and groups.

### 2. `toy_units.gd`

Twenty-four units: 16 friendly and 8 enemy, spread over two layers (layer 1 at y = 0, layer 2 at y = 400 wu with a dimmed translucent plane, as the layers mockup does), each with a seeded waypoint loop at 40 wu/s, HP that decays slowly on a few units so the panel changes. `step()` at 20 Hz. `hash()`.

### 3. `camera_rig.gd` and `input_router.gd`

Camera: copy the legacy constants (pan 1500 wu/s, wheel zoom 300 per notch, height 150 to 12,000 wu clamped to the canvas so the view never leaves the map, R-103-02), pitch fixed at 90° (R-103-03), edge scroll zone 60 px, `centre_on(pos)`; no auto-anchoring, no follow, no modes (R-103-01); the focused layer never moves the camera (R-103-04). Input, in `_unhandled_input` on a non-Control node: left click picks the nearest projected friendly within 30 px; Shift+click toggles; left drag draws the box and on release selects across layers; digits 1 to 9 recall, Ctrl+digit binds, a second press of the same digit within 0.4 s centres the camera; keys Q and E (layer hotkeys 1 and 2) narrow the selection; Tab cycles the strip focus; no other selection hotkeys exist. Right click issues a toy move (straight line) so the selection can be seen to obey.

### 4. `hud.gd`

Top-left: one objective line "HOLD  The Core  ▮▮▮▮▯▯▯▯▯▯  38%" with a 320x6 bar driven by the fixture's progress curve over the tick. Top-right: the mission clock derived from the tick (`tick / 20` seconds as `mm:ss`), never from the wall clock. Bottom-centre: the selection panel with a count, a row per unit type present (type name, count, summed HP) and each unit's layer colour dot. Bottom-centre below it: control-group tabs 1 to 9 (bound ones show the count; the recalled one highlights). Right edge: a two-slot layer strip with the focused slot highlighted; a narrow hint under it. The box-select overlay drawn in a full-rect Control with `mouse_filter = IGNORE` (it draws; it does not eat input). Every Control has `focus_mode = NONE`. Fonts from `theme/fonts/`.

### 5. The contract

`PLANTS = ["box-one-layer", "group-shared", "select-all-exists", "camera-unbounded", "clock-wallclock", "narrow-moves-focus"]`. `qa_state()`: `seed`, `hash`, `tick`, `clock_s`, `selected` (uids), `groups` (digit to uids), `focus_layer`, `camera {height, x, z}`, `bounds {min_x, max_x, min_z, max_z}`, `units` (uid to `{faction, layer, pos, hp}`), `units_px` (uid to `[x, y]`), `commands` (the selection class's command list), `objective {name, progress}`, `timing_ms {tick_avg}`, `regen_count`. `qa_seed(n)`; `qa_set("focus_layer", n)`; `qa_camera(height, x, z)`; `qa_tick(n)`; `qa_select(uids)`; `qa_bind(digit)`; `qa_recall(digit)`; `qa_narrow(layer)`.

Fault sites: `box-one-layer` makes the box select only the focused layer; `group-shared` skips removal from other groups on bind; `select-all-exists` adds a `select_all` command and binds it to a key; `camera-unbounded` removes the canvas clamp; `clock-wallclock` derives the clock from `Time.get_ticks_msec()`; `narrow-moves-focus` sets strip focus when narrowing.

### 6. Build order (commit after each)

verify.gd red and stubs; selection.gd; toy units; camera; input router; HUD; smoke and box scripts, checklist, screenshots, README.

## TDD protocol

1. Step 0: write `verify.gd` (`extends SceneTree`; `_init` runs one `_check_<id>()` per row of the check table below, then `quit(0)` or `quit(1)`; prints `FAIL: <id> <msg>` per failure and `VERIFY OK` on success, sharing one `_assert(cond, msg)`). Run `scripts/mockup_verify.sh hud`: it must print exactly one `FAIL:` line per check and exit 1. Commit as `test(mockup/hud): red verify.gd`.
2. Step 0 also: the root stub with `PLANTS`, `qa_state`, `qa_plant` (returns true for every listed id even before the feature exists), `qa/smoke.json`, `qa/checklist.md` copied from the template below, the `QADriver` child in the `.tscn`, and `docs/northstar/research/mockups/hud/README.md` with a one-paragraph "Design as built" placeholder.
3. Each build step: implement, run `mockup_verify.sh`, the named checks flip green, commit. Never edit a threshold; Westley owns them.
4. Every check carries its plant in a `# plant: <id>` line. Once the feature behind a check exists, `scripts/mockup_verify.sh hud --plant <id>` must print `PLANT <id> LIVE`; if it prints `DEAD`, fix the check or the fault site before committing.
5. Headless checks (verify.gd, dummy renderer, no autoloads): pure data, node-tree shape, API contract, determinism, CPU timing. Instantiate the scene when a check needs the tree: `var root = load("res://scenes/mockups/hud/hud_mockup.tscn").instantiate(); get_root().add_child(root); await process_frame`. Never call screenshot verbs headless.
6. Xvfb checks (driver plus shell): pixel diffs, pixel probes at projected positions, screenshot inspection, `fps_ms`. One clean run and one run per plant, in separate out dirs under your scratchpad; never mix the `plant` verb into a clean script.
7. `verify.gd` stays between 100 and 200 lines: at most 12 checks, each at most 15 lines.
8. After the clean and planted Xvfb runs, fill `qa/checklist.md` with the measured numbers, Read every screenshot, answer every visual question with the proving screenshot's name, fix every "no", rerun, and list what you cannot judge under `HELD:`.
9. Copy the review screenshots (1920x1080 batch) into `docs/northstar/research/mockups/hud/pass1/` and commit them; do not commit any other run output.
10. The report's check table lists, per check: clean result, plant id, planted result.

## Verify checks (`verify.gd`)

| id | check | where | plant |
|---|---|---|---|
| DET-1 | 300 ticks twice give equal hashes; seed 12 differs | H | none; self-test |
| BOX-2 | a box over units on both layers selects all of them (R-105-01, Q-105-01) | H | `box-one-layer` |
| NARROW-3 | `narrow(2)` keeps only layer-2 units and leaves `focus_layer` unchanged (R-105-06) | H | `narrow-moves-focus` |
| GROUP-4 | binding a unit to 2 after it was in 1 removes it from 1; recall(2) selects exactly group 2 (R-105-02) | H | `group-shared` |
| CENTRE-5 | recall(2) twice within 0.4 s reports `centre_requested` at the group centroid; once does not | H | none |
| NOALL-6 | `commands()` contains no name matching `select_all`, `select_all_army`, `select_all_of_type`, and no key in the input router maps to one (R-105-04) | H | `select-all-exists` |
| SHIFT-7 | shift-click adds an unselected unit and removes a selected one (R-105-05) | H | none |
| BOUND-8 | `qa_camera` to a point outside the canvas clamps `camera.x/z` inside `bounds` at every height (R-103-02); pitch is 90° (R-103-03); changing `focus_layer` leaves the camera unchanged (R-103-04) | H (instantiate) | `camera-unbounded` |
| CLOCK-9 | after `qa_tick(1200)`, `clock_s == 60` regardless of wall time (two runs 0.5 s apart agree) | H | `clock-wallclock` |
| PANEL-10 | after `qa_select` of three units of two types, the panel shows two rows with the right counts and summed HP; `focus_mode == NONE` on every Control; the overlay Control's `mouse_filter == IGNORE` | H (instantiate) | none |
| JSON-11 | `qa_state()` round-trips through JSON with every key; `qa_plant("nope")` false; every `PLANTS` id true | H | none |

Xvfb oracles: BOX-X (`qa/box.json` drags a real box, written from `units_px` in the boot state, around units known to sit on both layers; `selected` equals the expected uids; under `box-one-layer` it contains only one layer's); TAB-X (`diff recall_none.png recall_2.png` ≥ 0.001 over the tabs' crop; under `group-shared` the counts differ from clean); EDGE-X (two screenshots after `key_down D` for 60 frames at the east bound are identical, `diff` < 0.001 excluding the clock crop; under `camera-unbounded` they differ); DRAG-X (`box_mid.png` shows the box overlay: the overlay crop differs from `boot.png`); ERR-0, GPU-0, DET-1 pixel.

## QA script and screenshots

`qa/smoke.json`: `state boot`; `seed 11`; `call qa_camera 3000 3000 3000`; `screenshot boot`; `call qa_select [1,2,3]`; `screenshot selected_mixed`; `state selected_mixed`; `call qa_narrow 2`; `screenshot narrowed`; `state narrowed`; `call qa_select [1,2,3]`; `call qa_bind 2`; `call qa_select []`; `screenshot recall_none`; `call qa_recall 2`; `screenshot recall_2`; `state recall_2`; `call qa_recall 2`; `state centred`; `key Tab`; `state after_tab`; `call qa_camera 3000 5900 3000`; `key_down D`; `wait_frames 60`; `screenshot east_a`; `wait_frames 60`; `screenshot east_b`; `key_up D`; `state at_bound`; `call qa_tick 1200`; `state clock`; `screenshot clock`; `key R`; `state after_r`. Then `qa/box.json` by hand from `boot.json`: `seed 11`; `call qa_camera 3000 3000 3000`; `drag x0 y0 x1 y1 12`; `state boxed`; `screenshot boxed`; plus a `box_mid.png` taken by a `drag` with a `screenshot` between (split the drag into `move`, `click`-press semantics if the driver's `drag` cannot pause mid-way; if it cannot, list it). Review batch at 1920x1080: boot, selected mixed, narrowed, recall, box mid, boxed, at bound, clock (8 shots) into `docs/northstar/research/mockups/hud/pass1/`.

## Checklist: visual questions

Read each PNG beside `docs/bible/references/E-16/E-16.png` and the E-16 60-second paragraph.

| q | question | proves |
|---|---|---|
| Q1 | Is the HUD lean: only the objective line, clock, selection panel, group tabs and layer strip, and nothing that competes with the world? | S-P12, R-104-09 |
| Q2 | Is the selection state obvious at a glance (rings on units, panel, tab highlight)? | S-105 |
| Q3 | Does the layer strip read as focus, and does narrowing read as a change of selection and not of focus? | R-105-06, R-009-03 |
| Q4 | Is the box overlay visible while dragging and gone after? | R-105-01 |
| Q5 | Does the camera stop cleanly at the bound without a jolt? | R-103-02 |
| Q6 | Is all text legible at 720p; any clipped or overlapping element? | hygiene |

## What the report must answer

1. Is the interim top-down camera enough to play with, and what did edge scroll feel like at the bound?
2. HUD density: what could go, what is missing before a tester could play?
3. Double-tap timing and the narrow hint: did they read?
4. Frame time under llvmpipe at 720p with 24 units.
5. Under-defined points with candidates: strip look, minimap in Round 1 or not, double-tap window, selection ring look, whether narrowing should be a toggle.

## Finishing report

Write it as your final message and also as the "Design as built" and "Questions for Westley" sections of `docs/northstar/research/mockups/hud/README.md` (normal prose; that file is read by Westley), ending with a "Next step" line that says the pass-1 screenshots are in `pass1/` and the mockup awaits his look. The report answers the numbered questions below, includes the check table (check, clean result, plant, planted result), the answers to the visual questions with proving screenshots, the `HELD:` list, timings (`timing_ms`, `fps_ms` under llvmpipe at 720p), the list of commits, and every under-defined point with two or three candidates and no decision.

## Verification (done when all of these hold)

- `scripts/mockup_verify.sh hud` prints `VERIFY OK`, exit 0; `scripts/mockup_verify.sh hud --plant <id>` prints `PLANT <id> LIVE` for every id in `PLANTS`.
- `scripts/mockup_qa.sh run hud scenes/mockups/hud/qa/smoke.json <scratch>/hud/clean` gives `exit.txt` 0, `errors.txt` 0, no `UNIFORM` line, `_qa.adapter` containing `llvmpipe`; a second clean run matches the first on every `hash` and every screenshot (`diff` under 0.005).
- One run per plant under `<scratch>/hud/plant-<id>` and every deterministic oracle in the checklist shows the planted number on the wrong side of its threshold.
- `qa/checklist.md` is filled; every visual question is answered or held; the pass-1 screenshots are committed under `docs/northstar/research/mockups/hud/pass1/`.
- `git status --short` on your branch shows only `scenes/mockups/hud/**` and `docs/northstar/research/mockups/hud/**`; `git diff --stat main -- scenes/tactical scenes/world scenes/main_menu scenes/mockups/landscape scenes/mockups/_shared tests csrc docs/bible docs/northstar/PLAN.md project.godot` is empty.
- The interactive command (`~/.local/bin/godot --scene scenes/mockups/hud/hud_mockup.tscn`) is documented in the README with its hotkeys; you cannot run it on Westley's seat, so confirm instead that a wrapper run without `--qa-script` leaves the driver inert (no `_run.json`).
