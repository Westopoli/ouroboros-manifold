# HANDOFF BRIEF — P4 units, movement and combat mockup

Self-contained. Handed to an implementor 2026-09-22. Sibling briefs: `2026-09-22-mockup-qa-harness.md` (the harness you use), `2026-09-21-p2-landscape-mockup.md` (the shape to copy).

## Context

Rung P4 of the prototype ladder (`docs/northstar/PLAN.md:165`): "Six units, movement and combat on one layer; units move where sent, face travel, die visibly." Epics and Round 1 stories: E-11 S-082 (the six, R-082-01's table), S-084 (flat damage), S-085 (fights last long enough to read; R-085-01: a 10v10 mirror lasts at least 45 s), S-087 (flinch, obey, shoot the nearest); E-13 S-096 (four commands; R-096-01 to R-096-04), S-097 (around, not through; R-097-03, R-097-05, R-097-08), S-100 (facing, R-100-01, R-100-02); E-18 S-132 (silhouette is the information, R-132-01), S-136 (death is unmistakable, R-136-01), S-138 (the look, R-138-01). Read `docs/bible/epics/E-11-units-and-combat.md` lines 41 to 65, 78 to 107 and 126 to 142; `E-13-movement-and-command.md` lines 42 to 76 and 99 to 110; `E-18-visual-style-and-combat-visuals.md` lines 28 to 40, 82 to 93 and 108 to 119. Abilities are off in Round 1.

The 60-second paragraphs you are visualising: E-11 (10 Vanguards versus 10 Raiders at 250 wu, Vanguards win with 5 or more survivors and the fight lasts at least 45 s; 10 Bombards at 1,000 wu kill the Vanguards before they close; 4 Raiders around the flank kill 4 Bombards), E-13 (4 Raiders and 4 Bastions 300 wu apart move 3,000 wu and arrive together; split, the Raiders arrive in 20 s; an attack-move into an enemy line stops the first units and flows the rest around into a concave front; a plain move through fire does not stop or shoot), E-18 (six silhouettes distinguishable at tactical zoom, Strike smallest and Siege largest, Bastion wider than long, Bombard longest; a hit blooms warm for a third of a second, no shake; a death flares, drifts along its last heading, darkens over 3 to 5 s). References: `docs/bible/references/E-11/notes.md` and `E-18/notes.md` say the silhouette and combat references are missing; `E-18/E-18-1.png` and `E-18-2.png` exist (read their rows in `E-18/notes.md` if any; otherwise treat them as the look register); `E-13/E-13.png` exists with `E-13/notes.md`. Judge against those and the 60-second paragraphs; hold what you cannot judge.

This mockup is a toy tactical sim in GDScript at a fixed 20 Hz tick, seeded and replayable from a command list, one flat layer, primitive silhouettes from a kit, with hit flash and death visuals. It exists so Westley can see six shapes, a fight, a flank, and a death and say whether they read.

## Rules for the implementor

- If you are an Opus or Fable chat: plan and review, Sonnet sub-agents build; ask Westley about his Claude usage before a batch of more than two doers. If you are a Sonnet chat: do the work yourself, spawn no sub-agents.
- You are in a git worktree on branch `mockup/units`. Commit there after each working step with the trailer `Co-Authored-By: Claude <model> <noreply@anthropic.com>`. Do not push; the design chat merges into `main`. Never stage files you did not create or edit for this brief. Never check out another branch.
- Touch only `scenes/mockups/units/**` and `docs/northstar/research/mockups/units/**`. Nothing else: not `csrc/`, `simulation/`, `tests/`, `docs/bible/`, other `docs/northstar/`, other `scenes/`, `scenes/mockups/_shared/` (if the harness is broken, stop and report; do not patch it), `project.godot`.
- This is a mockup: placeholder primitives only (boxes, cylinders, prisms, planes, quads, flat colours, `Label3D`, `Control._draw`). No imported models, no textures beyond vertex colour and flat shading. GDScript only. No autoload dependency and no dependency on any other scene: the scene must work if every autoload were removed. You may copy code from the legacy files named under "Godot facts" into your directory and you may reference `theme/fonts/*.ttf` by `res://` path; you may not `preload` or `load` anything outside your directory except `res://scenes/mockups/_shared/qa_driver.gd` and `qa_plants.gd`.
- Renderer parity: your QA renders run under the Compatibility renderer on software GL; Westley views Forward+ on an RTX 3060. Use only what looks the same in both: `StandardMaterial3D` (vertex colour as albedo is fine), `ArrayMesh`/`ImmediateMesh`, `MultiMeshInstance3D`, `Label3D`, one `DirectionalLight3D`, `WorldEnvironment` sky, ambient and depth fog, `CanvasLayer`, `CPUParticles3D`. Do not use SDFGI, VoxelGI, volumetric fog, SSR, SSAO, SSIL, glow, decals, `GPUParticles3D`, or screen-texture shaders.
- No era named in any script identifier or node name (bible rule R-145-01). Where the era shows it is data under `kits/` or `fixtures/`.
- Deterministic: every random draw comes from your own `RandomNumberGenerator` seeded from an integer seed; never the global RNG, never the wall clock. Same seed, same state hash, same pixels.
- **Never set `DISPLAY` yourself and never use `:0` or `:1`.** Every windowed run goes through `scripts/mockup_qa.sh`, which creates a private Xvfb. The GPU belongs to the Agora chain.
- No docstrings or comments except the `# plant: <id>` line above each check in `verify.gd`. Minimal, direct code.
- When something in this brief is under-defined, do not decide: build the simplest thing that shows the question and list it in the finishing report with two or three candidate answers.

## Godot facts (reconnaissance 2026-09-22)

- Binary `~/.local/bin/godot`, `4.6.3.stable.official`. Project root is the repo root. `project.godot` declares Forward+, 1920x1080, fullscreen, stretch `canvas_items`/`expand`, no `[input]` map (use raw keycodes as the landscape mockup does). Nineteen autoloads run on any `--path .` scene launch; one spawns the Python sim and warns about a mac path; harmless. `--script` SceneTree mode loads no autoloads.
- Scene convention: a short `.tscn` (root node with your root script, a `QADriver` child with `res://scenes/mockups/_shared/qa_driver.gd`, and whatever nodes you need) plus scripts. Every mockup scene in this repo is launched by path, never as the main scene. Westley's command is `~/.local/bin/godot --scene scenes/mockups/units/units_mockup.tscn` from the repo root; keep that name.
- The harness (read `scenes/mockups/_shared/README.md` first): `scripts/mockup_verify.sh units [--plant id]` runs your `verify.gd` headless; `scripts/mockup_qa.sh run units <script.json> <outdir> [--res 1280x720] [--plant id]` runs the scene under Xvfb with `--fixed-fps 30` and replays a JSON action list (`wait_frames`, `move`, `click`, `click_node`, `drag`, `wheel`, `key`, `key_down`, `key_up`, `call`, `seed`, `plant`, `pause`, `screenshot`, `state`, `tree`, `wait_file`); `scripts/mockup_qa.sh diff a.png b.png` prints the fraction of differing pixels; `scripts/mockup_qa.sh scan <outdir>` writes `errors.txt`, `shots.txt`, `marks.txt`. Your scene root must implement the contract: `const PLANTS: Array[String]`, `qa_state() -> Dictionary` (JSON-safe, canonical from data, never from HUD labels; always `seed`, `hash`, `timing_ms`, `regen_count` plus the keys named below), `qa_plant(id) -> bool`, `qa_seed(n)`, and the optional `qa_set(name, value)` and `qa_camera(...)` this brief names. Plants are activated through `preload("res://scenes/mockups/_shared/qa_plants.gd").is_active("<id>")` at a one-line fault site.
- Under Xvfb a 3D scene renders at a few frames per second; keep QA scripts short (a few hundred frames), use 1280x720 by default, and take the 1920x1080 review shots only in the final batch. Window pixels equal screenshot pixels; canvas coordinates are scaled by the stretch (use `click_node` rather than raw pixels for HUD buttons).
- Input gotchas: a full-rect `Control` with the default `mouse_filter = STOP` swallows synthetic mouse events before `_unhandled_input`; put world mouse handling in `_unhandled_input` on a non-Control node and set every full-rect Control to `MOUSE_FILTER_IGNORE` unless it is the designated click surface. Set `focus_mode = FOCUS_NONE` on Buttons and click empty ground before key verbs so a SpinBox does not eat letters.
- Copy the feel of the landscape mockup's HUD and camera code where it fits: `scenes/mockups/landscape/hud.gd` (kit discovery, timing prints, screenshot key), `camera_rig.gd` (pan, edge scroll, wheel zoom, public `pan_to`/`set_height`).
- Colours available to copy: `autoload/theme_constants.gd` (BASE `#0A0D12`, PRIMARY `#e8e6e1`, ERA_ACCENTS), faction colours `#4099FF` and `#FF4738` from `assets/eras/settled_reach/manifest.json`, the hue-from-id function in `autoload/faction_palette.gd:38`. Fonts: `theme/fonts/` (JetBrainsMono, Newsreader).
- Legacy to copy from (never to load): `autoload/tactical_bridge.gd:67-125` (render interpolation between ticks: a 3-tick delay ring buffer, `lerp_angle` on facing); `scenes/tactical/unit_renderer.gd:172-300` (MultiMesh batching per type and faction, V-formation offsets at line 24); `scenes/tactical/visuals/destruction_manager.gd:1-6` (the death sequence timings: bloom 0.5 s, drift, darken, lifecycle 0 to 5 s fresh, 5 to 15 s cooling) and `impact_feedback_manager.gd:1-4` (hit detected by HP drop, burst scaled by damage, colour from attacker faction); `scenes/tactical/command_indicator.gd` (move versus attack-move click ping, lifetime 1.5 s); `scenes/debug/test_squad_impact_origins.gd` (a sim-less harness that seeds units directly). The roster table is R-082-01 in the epic; copy the numbers into `kits/*.json` as data per unit role, never into identifiers.
- Faction colours `#4099FF` and `#FF4738` from `assets/eras/settled_reach/manifest.json`; per-role silhouettes are primitives you build from `BoxMesh`, `PrismMesh`, `CylinderMesh`, `SphereMesh` per R-132-01's shape words.

## What to build

```
scenes/mockups/units/
  units_mockup.tscn         root Node3D "UnitsMockup" with units_mockup.gd; children World, CameraRig, HUD, QADriver
  units_mockup.gd           the contract; owns kit load, scenario load, tick loop, render sync
  toy_sim.gd                RefCounted: units, commands, steering, collision, targeting, damage, deaths; step() per tick; hash()
  roster.gd                 RefCounted: the six roles with stats from the kit (data), category order checks
  unit_view.gd              Node3D: one MultiMesh per (role, faction); facing, interpolation, hit flash, death sequence
  camera_rig.gd             fixed top-down pan, wheel zoom, edge scroll, canvas-bounded (copy from landscape)
  hud.gd                    CanvasLayer: scenario dropdown, kit toggle (Tab), seed, Reset (R), Play/Pause (Space), Step (T), tick and survivors readout
  kits/greek.json, kits/settled_reach.json
  scenarios/lineup.json, mirror_10v10.json, bombards_1000.json, flank_4v4.json, formation_move.json, plain_move_under_fire.json
  verify.gd
  qa/smoke.json, qa/checklist.md
```

### 1. `roster.gd` and kits

A kit is JSON: `name`, `palette` (ground, faction_0, faction_1, flash, wreck), and `roles`: six entries keyed by role (`flanker, screen, frontliner, support, artillery, anchor`) each with `stats` (hp, damage, interval_s, range_wu, speed_wu_s, sensor_wu, category) copied from R-082-01, `silhouette` (a mesh recipe from a fixed vocabulary: `swept_dart, flat_wing, wedge_slab, spire_radial, long_barrel, wide_block`, plus `size [length, width, height]` in wu and a `squad` count of 1 or 3 to 5 for Strike per R-132-03), and a display name (the era's word for it: the Greek kit may say "peltast", the Settled Reach kit "raider"; names are data). `roster.gd` loads a kit and exposes the six by role; the category orderings of R-082-02 to R-082-04 are checks, not code paths.

### 2. `toy_sim.gd`

Fixed tick 1/20 s. Units: `{uid, role, faction, pos: Vector2, facing, hp, order {kind, point, target}, target, attack_timer, anchor, alive, death_tick}`. Obstacles: a few axis-aligned boxes with a 100 wu route grid (cells inside a box blocked). Commands per R-096: `move`, `attack_move`, `attack_target`, `stop` (accepted here only as "clear order", and reported as rejected with a reason if the brief's reader wants R-096-06 literal; list it). All commands for a tick apply before state advances (R-096-07) and are recorded with the tick.

Per tick, in this order: apply commands; targeting (R-087-03, R-087-04, R-087-05, R-087-06, re-acquire every 4th tick); movement (route on the grid by BFS from the unit's cell to the point's cell, straightened by line of sight; probe 40 wu ahead, sweep alternate angles on an ally block, keep a deflected heading 60 wu, R-097-03, R-097-04); collision pass (pairs within 30 wu pushed apart along their line, up to 3 iterations, stationary unit takes 0, R-097-05 to R-097-08); attacks (timer per interval × 20 ticks, flat damage with no falloff, backswing pause 0.5 s, R-084-01, R-084-02, R-084-04); facing (target if attacking, heading if moving, else keep; turn rate capped 6.0, 4.0, 2.5 rad/s by category, R-100-01, R-100-02); deaths (hp ≤ 0 marks `alive = false`, `death_tick`; wrecks have no collision, R-136-02). Plain move never acquires or returns fire (R-096-01); attack-move halts and fires in range, drops a target that moves 200 wu from the anchor (R-096-02, R-096-03). `hash()` over positions, facings, hp, alive. A `run(scenario, ticks) -> hash` for verify. Flinch (R-087-01) may be skipped; list it.

Scenarios are JSON: `units[] {role, faction, pos}`, `obstacles[]`, `commands[] {tick, kind, uids, point or target}`. Author the six named above at the E-11 and E-13 60-second numbers (positions in wu, 250 wu and 1,000 wu separations, 3,000 wu move).

### 3. `unit_view.gd`

One `MultiMeshInstance3D` per (role, faction) with the kit's silhouette mesh; Strike roles draw their squad as 3 to 5 small copies in a V. Transforms from the sim with a 3-tick render delay and lerp (`lerp_angle` on facing). Hit flash: on an HP drop, the instance colour blooms toward the kit's flash colour for 0.33 s, no camera shake. Death: bloom 0.5 s brighter than a hit, then the wreck drifts along its last heading decelerating, darkens toward a desaturated faction colour over 3 to 5 s, and is removed at 15 s. Selection ring (flat ring mesh) under selected units; a move or attack-move click ping on the ground for 1.5 s (green for move, orange for attack-move).

### 4. Camera, HUD, input

Camera: copy the landscape rig; fixed top-down (pitch 90°), heights 500 to 12,000 wu, canvas 8,000 × 8,000 wu, `qa_camera(height, x, z)`. Input: left click selects a friendly unit, drag box selects, right click issues move, Shift right click attack-move, right click on an enemy attack-target; keys Space play/pause, T step one tick, R reset scenario, Tab kit toggle, F12 screenshot. HUD: scenario `OptionButton`, kit name, tick counter, survivors per faction, the selected units' roles and HP, the command log's last three lines.

### 5. The contract

`PLANTS = ["pass-through", "facing-fixed", "instant-fight", "silhouettes-same", "seed-ignored", "no-death-visual"]`. `qa_state()`: `seed`, `hash`, `kit`, `scenario`, `tick`, `alive {0: n, 1: n}`, `units` (uid to `{role, faction, pos, facing, hp, alive}`), `units_px` (uid to `[x, y]`), `bboxes` (role to `[length, width, height]`), `flashes_active`, `wrecks_active`, `timing_ms {tick_avg}`, `regen_count`. `qa_seed(n)`; `qa_set("scenario", name)`, `qa_set("kit", name)`; `qa_camera(height, x, z)`; `qa_tick(n)` runs n ticks synchronously; `qa_command(kind, uids, x, z)` queues a command.

Fault sites: `pass-through` skips the collision pass and the obstacle block; `facing-fixed` never updates facing; `instant-fight` multiplies damage by 50; `silhouettes-same` uses one box for every role; `seed-ignored` forces seed 11 (the seed drives target re-acquisition tie breaks and the sweep order); `no-death-visual` removes a dead unit's instance on the death tick with no sequence.

### 6. Build order (commit after each)

verify.gd red and stubs; roster and kits; toy_sim with move and collision; targeting and damage; facing and deaths; unit_view with flash and death; camera, HUD, input; scenarios; smoke, checklist, screenshots, README.

## TDD protocol

1. Step 0: write `verify.gd` (`extends SceneTree`; `_init` runs one `_check_<id>()` per row of the check table below, then `quit(0)` or `quit(1)`; prints `FAIL: <id> <msg>` per failure and `VERIFY OK` on success, sharing one `_assert(cond, msg)`). Run `scripts/mockup_verify.sh units`: it must print exactly one `FAIL:` line per check and exit 1. Commit as `test(mockup/units): red verify.gd`.
2. Step 0 also: the root stub with `PLANTS`, `qa_state`, `qa_plant` (returns true for every listed id even before the feature exists), `qa/smoke.json`, `qa/checklist.md` copied from the template below, the `QADriver` child in the `.tscn`, and `docs/northstar/research/mockups/units/README.md` with a one-paragraph "Design as built" placeholder.
3. Each build step: implement, run `mockup_verify.sh`, the named checks flip green, commit. Never edit a threshold; Westley owns them.
4. Every check carries its plant in a `# plant: <id>` line. Once the feature behind a check exists, `scripts/mockup_verify.sh units --plant <id>` must print `PLANT <id> LIVE`; if it prints `DEAD`, fix the check or the fault site before committing.
5. Headless checks (verify.gd, dummy renderer, no autoloads): pure data, node-tree shape, API contract, determinism, CPU timing. Instantiate the scene when a check needs the tree: `var root = load("res://scenes/mockups/units/units_mockup.tscn").instantiate(); get_root().add_child(root); await process_frame`. Never call screenshot verbs headless.
6. Xvfb checks (driver plus shell): pixel diffs, pixel probes at projected positions, screenshot inspection, `fps_ms`. One clean run and one run per plant, in separate out dirs under your scratchpad; never mix the `plant` verb into a clean script.
7. `verify.gd` stays between 100 and 200 lines: at most 12 checks, each at most 15 lines.
8. After the clean and planted Xvfb runs, fill `qa/checklist.md` with the measured numbers, Read every screenshot, answer every visual question with the proving screenshot's name, fix every "no", rerun, and list what you cannot judge under `HELD:`.
9. Copy the review screenshots (1920x1080 batch) into `docs/northstar/research/mockups/units/pass1/` and commit them; do not commit any other run output.
10. The report's check table lists, per check: clean result, plant id, planted result.

## Verify checks (`verify.gd`)

| id | check | where | plant |
|---|---|---|---|
| DET-1 | `run(mirror_10v10, 600)` twice gives the same hash; seed 12 differs from seed 11 on the flank scenario | H | `seed-ignored` |
| ROSTER-2 | six roles loaded from each kit with R-082-02 to R-082-04 orderings (Strike faster than Line faster than Siege; anchor has ≥ 2× the next HP; flanker least; both Strike sensors exceed both Siege) | H | none (data); self-test with a broken kit dict |
| SIL-3 | the six silhouette bounding boxes are pairwise distinct (no two within 10 percent on all three axes); Strike smallest volume, Siege largest; anchor width > length; artillery the longest | H | `silhouettes-same` |
| MIRROR-4 | `mirror_10v10` (frontliner mirror at 250 wu, attack-move both) lasts ≥ 900 ticks before one side is dead; the E-11 line-versus-Strike variant ends with ≥ 5 frontliners alive | H | `instant-fight` |
| SOLID-5 | over `formation_move` and `flank_4v4`, no unit centre is inside an obstacle box and no two live units are closer than 28 wu at the end of any tick | H | `pass-through` |
| FACE-6 | for every moving unit with speed > 1 wu/s, facing is within 0.18 rad of its velocity heading after the turn-rate cap has had 20 ticks; an attacking unit faces its target | H | `facing-fixed` |
| PLAIN-7 | in `plain_move_under_fire` the moving units never acquire a target and never stop before the point (R-096-01) | H | none; self-test by issuing attack-move instead |
| DEATH-8 | a killed unit leaves `alive`, keeps a wreck entry for 60 to 100 ticks of visual, then is removed; wrecks never collide | H (instantiate for the view) | `no-death-visual` |
| FORM-9 | `formation_move`: 4 flankers and 4 anchors ordered together arrive within 40 ticks of each other; split, the flankers arrive in about 400 ticks | H | none |
| JSON-10 | `qa_state()` round-trips through JSON with every key; `qa_plant("nope")` false; every `PLANTS` id true | H | none |
| TIME-11 | `timing_ms.tick_avg` under 2 ms for 20 units headless | H | none |

Xvfb oracles: SIL-X (the lineup screenshot has six distinct coloured blobs: crop each unit's `units_px` neighbourhood and check pairwise `diff` ≥ 0.05; under `silhouettes-same` < 0.02); FIGHT-X (`diff fight_t0.png fight_t300.png` ≥ 0.03 and `flashes_active > 0` in the mid-fight state; under `instant-fight` the fight is over by tick 60, `alive` one side 0); DEATH-X (crop around a dying unit: `diff death_t0.png death_t20.png` ≥ 0.05 and `wrecks_active ≥ 1`; under `no-death-visual` the crop is background and `wrecks_active == 0`); FACE-X (a unit ordered east then north shows a different silhouette orientation: crop `diff` ≥ 0.05; under `facing-fixed` < 0.01); KIT-X (`diff lineup_greek.png lineup_settled_reach.png` ≥ 0.10); SEED-X on the flank scenario; ERR-0, GPU-0, DET-1 pixel.

## QA script and screenshots

`qa/smoke.json`: `state boot`; `seed 11`; `call qa_set scenario lineup`; `call qa_camera 1500 4000 4000`; `screenshot lineup_greek`; `state lineup`; `call qa_set kit settled_reach`; `screenshot lineup_settled_reach`; `call qa_set kit greek`; `call qa_set scenario mirror_10v10`; `call qa_camera 2500 4000 4000`; `screenshot fight_t0`; `call qa_tick 300`; `screenshot fight_t300`; `state fight_t300`; `call qa_tick 900`; `screenshot fight_end`; `state fight_end`; `call qa_set scenario flank_4v4`; `call qa_tick 200`; `screenshot flank_t200`; `state flank_t200`; `call qa_set scenario lineup`; `call qa_command move [1] 6000 4000`; `call qa_tick 30`; `screenshot face_east`; `call qa_command move [1] 6000 1000`; `call qa_tick 30`; `screenshot face_north`; `state face_north`; `call qa_set scenario bombards_1000`; `call qa_tick 140`; `screenshot death_t0`; `state death_t0`; `call qa_tick 20`; `screenshot death_t20`; `state death_t20`; `seed 12`; `call qa_set scenario flank_4v4`; `call qa_tick 200`; `state seed12_flank`; `key R`; `state after_r`. Review batch at 1920x1080: both lineups, fight mid and end, flank result, the death pair, map zoom of the fight (8 shots) into `docs/northstar/research/mockups/units/pass1/`.

## Checklist: visual questions

Read each PNG beside `docs/bible/references/E-18/E-18-1.png`, `E-18-2.png`, `E-13/E-13.png` and the three 60-second paragraphs.

| q | question | proves |
|---|---|---|
| Q1 | In the lineup, can you name all six roles from shape alone (smallest dart, flat wing, wedge, spire, long barrel, wide block)? | R-132-01, R-132-02 |
| Q2 | Are the same six roles obviously the same roles in both kits? | R-145-01, S-138 |
| Q3 | Mid-fight, can you tell who is winning and where the front is; are hits visible without shake? | S-085, S-134 (minimal) |
| Q4 | Is the death unmistakable: flare, drift, darkening? | R-136-01 |
| Q5 | Does the flank result read as Raiders behind Bombards, not a blob? | E-11 60-second text |
| Q6 | Do units face their travel and their targets; does a turn look like a turn? | R-100-01 |
| Q7 | Any magenta, black, clipped or overlapping HUD text at 720p? | hygiene |

## What the report must answer

1. Which silhouettes read and which did not, in each kit.
2. Fight pace: ticks to first death and to the end in each scenario; does 45 s feel readable?
3. Whether the toy steering produced a concave front on the attack-move scenario, or what it did instead.
4. Frame time under llvmpipe at 720p with 20 units; tick time.
5. Under-defined points with candidates: unit sizes in wu at this camera height, squad rendering for Strike, projectile look, flinch, the stop command, damage scale for the toy.

## Finishing report

Write it as your final message and also as the "Design as built" and "Questions for Westley" sections of `docs/northstar/research/mockups/units/README.md` (normal prose; that file is read by Westley), ending with a "Next step" line that says the pass-1 screenshots are in `pass1/` and the mockup awaits his look. The report answers the numbered questions below, includes the check table (check, clean result, plant, planted result), the answers to the visual questions with proving screenshots, the `HELD:` list, timings (`timing_ms`, `fps_ms` under llvmpipe at 720p), the list of commits, and every under-defined point with two or three candidates and no decision.

## Verification (done when all of these hold)

- `scripts/mockup_verify.sh units` prints `VERIFY OK`, exit 0; `scripts/mockup_verify.sh units --plant <id>` prints `PLANT <id> LIVE` for every id in `PLANTS`.
- `scripts/mockup_qa.sh run units scenes/mockups/units/qa/smoke.json <scratch>/units/clean` gives `exit.txt` 0, `errors.txt` 0, no `UNIFORM` line, `_qa.adapter` containing `llvmpipe`; a second clean run matches the first on every `hash` and every screenshot (`diff` under 0.005).
- One run per plant under `<scratch>/units/plant-<id>` and every deterministic oracle in the checklist shows the planted number on the wrong side of its threshold.
- `qa/checklist.md` is filled; every visual question is answered or held; the pass-1 screenshots are committed under `docs/northstar/research/mockups/units/pass1/`.
- `git status --short` on your branch shows only `scenes/mockups/units/**` and `docs/northstar/research/mockups/units/**`; `git diff --stat main -- scenes/tactical scenes/world scenes/main_menu scenes/mockups/landscape scenes/mockups/_shared tests csrc docs/bible docs/northstar/PLAN.md project.godot` is empty.
- The interactive command (`~/.local/bin/godot --scene scenes/mockups/units/units_mockup.tscn`) is documented in the README with its hotkeys; you cannot run it on Westley's seat, so confirm instead that a wrapper run without `--qa-script` leaves the driver inert (no `_run.json`).
