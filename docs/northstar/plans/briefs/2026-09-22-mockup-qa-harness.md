# HANDOFF BRIEF — Mockup self-QA harness, with the landscape mockup as its positive control

Self-contained. Handed to an implementor 2026-09-22. Program context: `2026-09-21-factory-program.md`; plan: `~/.claude/plans/develop-a-plan-to-snuggly-snail.md` (the plan file is not in the repo; everything you need is in this brief).

## Context

Every visual rung of the prototype ladder (`docs/northstar/PLAN.md:155-172`) gets an isolated Godot mockup shaped like `scenes/mockups/landscape/`. Eight more are about to be built in parallel by Sonnet doers. The landscape mockup taught us that a model must look at its own render before Westley does: his review-1 and review-2 complaints (seeds that did not differ, a map overlay drawn in screen space that did not move with the terrain, a slider with no visible effect, a regenerate that froze the game, ring-shaped cities on flat ground, mountains an order of magnitude too small) were all catchable by running the scene, driving it, screenshotting, and checking numbers and pixels.

This brief builds the one shared harness that makes that possible, then retrofits the landscape mockup onto it. The retrofit is the harness's positive control: each of the five complaints above must be caught by a named oracle on a planted build and pass on the clean build. No other mockup starts until this brief's verification passes.

## Rules for the implementor

- If you are an Opus or Fable chat: plan and review, Sonnet sub-agents build; ask Westley about his Claude usage before a batch of more than two doers. If you are a Sonnet chat: do the work yourself, spawn no sub-agents.
- You are in a git worktree on branch `mockup/harness`. Commit there after each working step with the trailer `Co-Authored-By: Claude <model> <noreply@anthropic.com>`. Do not push; the design chat merges into `main`. Never stage files you did not create or edit for this brief. Never check out another branch.
- Touch only: `scenes/mockups/_shared/**`, `scripts/mockup_qa.sh`, `scripts/mockup_verify.sh`, `scenes/mockups/landscape/**`. Nothing under `docs/`, `tests/`, `csrc/`, `simulation/`, other `scenes/`, or `project.godot`.
- GDScript and bash only. No Python beyond `python3 -c` one-liners on the standard library (no numpy; PIL exists but is not to be a dependency of the scripts).
- **Never set `DISPLAY` yourself and never use `:0` or `:1`.** The live seat is XWayland-rootless; synthetic input sent there lands on whatever Westley has focused (this retracted probe D, `docs/northstar/proving_ground/SCORECARD.md:15`). `:1` hangs. Every Godot launch that needs a window goes through `scripts/mockup_qa.sh`, which creates a private Xvfb. The GPU belongs to the Agora chain; the harness uses software GL only.
- Determinism: mockups use their own seeded `RandomNumberGenerator`; the harness runs Godot with `--fixed-fps 30` so `_process(delta)` is constant. No wall clock in behaviour.
- No docstrings or comments unless the logic is non-obvious. Minimal diffs to the landscape mockup: add the contract, the plants' one-line fault sites, and the QADriver child; do not refactor it.
- When something here is under-defined, build the simplest thing that works and list it in the report with two or three candidates. Do not decide design questions.

## Facts (reconnaissance 2026-09-22)

- Godot: `~/.local/bin/godot`, `4.6.3.stable.official`, real ELF. Project root is the repo root; `project.godot` says Forward+, viewport 1920x1080, `window/size/mode=3` (fullscreen), stretch `canvas_items`/`expand`, no `[input]` map. Nineteen autoloads run for any `godot --path . <scene>` launch (one spawns the Python sim; harmless, `logs/` is gitignored). `--script` SceneTree mode loads no autoloads.
- Flags confirmed in `godot --help`: `--headless`, `--display-driver x11`, `--rendering-driver opengl3` (implies the Compatibility renderer), `-w`, `--resolution WxH`, `--position X,Y`, `--fixed-fps N`, `--quit-after N` (main-loop iterations, not seconds), `--write-movie`, `--import`. No screenshot flag exists.
- Proven path (probe D `docs/legacy/proving_ground/PD-t2-computer-driving.md`, PX-02 `PX-02-actor-verbs-pause-step.md`): `xvfb-run -a -s "-screen 0 WxHx24"` plus `LIBGL_ALWAYS_SOFTWARE=1 godot --path . --rendering-driver opengl3 <scene>`; xdotool clicks and keys land on the private Xvfb window; in-engine `get_viewport().get_texture().get_image().save_png()` produces real images (the 20 pass-3 landscape shots under `docs/northstar/research/landscape_design/mockup/pass3/` were taken this way; `identify` gives stddev 0.25, not black). Gotcha from PX-02: a full-rect `Control` with the default `mouse_filter = STOP` swallows synthetic mouse events before `_unhandled_input`.
- Installed: `Xvfb`, `xvfb-run`, `xdotool`, ImageMagick 7 (`magick`, `compare`, `identify`, `import`), `ffmpeg`. Machine: 16 cores, 30 GB. Under llvmpipe a 3D scene at 1920x1080 renders at roughly 2 to 6 fps; 1280x720 about twice that.
- Landscape mockup anatomy: root `LandscapeMockup` (Node3D, no script) with children `World`, `CameraRig` (`camera_rig.gd`, public `pan_to`, `set_height`, `get_height`, `get_current_band`, signal `band_changed`), `HUD` (CanvasLayer, `hud.gd`: the orchestrator; `_regenerate()` at line 98 times gen, ground, placer; kits discovered from `kits/*.json`; keys `R`, `Tab`, `F12`; `-- --screenshot-batch` at line 68; `_take_screenshot` at 198), `HUD/MapView` (`map_view.gd`, creates world-space `MapViewGeometry` under `World` at line 32; `_gui_input` at 138 owns clicks in the map band), `HUD/VBoxContainer` (SeedSpinBox, BandLabel, RegenerateButton, KitToggleButton, PieceCountLabel, CanvasLabel, CanvasToggleButton, TimingLabel, StabilityLabel, StabilitySlider). `field_map.gd` (`class_name FieldMap`, `generate(seed, canvas, stability)`, `compute_hash()`, `grid[]` cells with `elevation` in wu, `district`, `nodes[]`), `ground.gd`, `placer.gd`, `verify.gd` (`extends SceneTree`, six checks, `VERIFY OK` / `FAIL: <msg>`, `quit(0/1)`; `_assert` at 168). Existing test runner shape to mirror: `scripts/run_godot_tests.sh:45`.
- Known stale spot: `scenes/mockups/landscape/kits/README.md` documents the palette as `zone_a..zone_c`; the kits and `ground.gd:10` use `zone_a..zone_e`. Fix it in the retrofit.
- The `class_name` cache (`.godot/global_script_class_cache.cfg`, gitignored) may not know a new `class_name` until `godot --headless --path . --import` runs. The harness uses `preload` and never `class_name`, so it is immune; the verify script offers `--refresh-cache`.

## What to build

```
scenes/mockups/_shared/qa_driver.gd     ~170 lines  Node; replays a JSON action script, screenshots, dumps state
scenes/mockups/_shared/qa_plants.gd     ~20 lines   static plant registry; reads env MOCKUP_PLANT
scenes/mockups/_shared/liveness.json    3 lines     the one xdotool scenario
scenes/mockups/_shared/README.md        ~40 lines   the contract, the verb table, the two commands
scripts/mockup_qa.sh                    ~90 lines   run | liveness | diff | scan | selftest
scripts/mockup_verify.sh                ~30 lines   headless verify.gd, with --plant inversion
scenes/mockups/landscape/landscape_mockup.gd   new root script: the contract, delegating to HUD and CameraRig
scenes/mockups/landscape/qa/smoke.json
scenes/mockups/landscape/qa/checklist.md
```

Total harness under 300 lines (`qa_driver.gd` + `qa_plants.gd` + the two scripts). If over, drop the `tree` verb first.

### 1. `qa_driver.gd`

`extends Node`. A mockup adds it as a child named `QADriver` of the scene root. Inert unless `--qa-script` is present in `OS.get_cmdline_user_args()`, so Westley's interactive runs are unaffected.

`_ready()`: `process_mode = PROCESS_MODE_ALWAYS`; parse user args `--qa-script <path>`, `--qa-out <dir>` (default `user://qa`), `--qa-grab engine|external` (default engine); read the script file (`FileAccess.get_file_as_string`), `JSON.parse_string`, must be an Array else exit 2; `_root = get_tree().current_scene`; if the root lacks `qa_state` or `qa_plant`, exit 3; `DisplayServer.window_set_title("QA:" + _root.name)`; start `_run()`.

`_run()`: await two `process_frame` (root `_ready` done and one draw); inject one mouse motion to the viewport centre (defines the mouse position and kills edge scroll); for each action `await _do(action)`; write `<out>/_run.json` with `_qa_info()`; `get_tree().quit(0)`.

Actions are arrays, first element the verb:

| verb | args | behaviour |
|---|---|---|
| `wait_frames` | n | n awaited `process_frame` |
| `move` | x, y | `InputEventMouseMotion` (position, global_position, relative) through `_push` |
| `click` | x, y [, button=1] | move, then `InputEventMouseButton` pressed, one frame, released, one frame |
| `click_node` | "HUD/VBoxContainer/RegenerateButton" | find the `Control` under the root, centre = `ctrl.get_viewport().get_final_transform() * ctrl.get_global_rect().get_center()` (canvas to window px), then `click` |
| `drag` | x0, y0, x1, y1 [, steps=8] | move, press, `steps` lerped motions one frame apart, release |
| `wheel` | n | abs(n) wheel-up (n > 0) or wheel-down events, pressed and released, one frame apart, at the current mouse position |
| `key` | "R" | `OS.find_keycode_from_string`; `InputEventKey` pressed (keycode, physical_keycode, unicode), one frame, released, one frame |
| `key_down`, `key_up` | "W" | hold across frames; `Input.is_key_pressed` must reflect it |
| `call` | "method", args... | `_root.callv(method, args)`; print `QA_CALL <method> -> <result>`; missing method exits 3 |
| `seed` | n | `call qa_seed n` |
| `plant` | "id" | `_root.qa_plant(id)`; false exits 3 |
| `pause` | true/false | `get_tree().paused` |
| `screenshot` | "name" | see below |
| `state` | "name" | `_root.qa_state()` merged with `{"_qa": _qa_info()}`, `JSON.stringify(d, "  ")` to `<out>/<name>.json` |
| `tree` | "name" | every visible `Control`: `{path, class, text, rect_px}` in window px; every `Node3D`: `{path, class, parent}`; to `<out>/<name>.json` |
| `wait_file` | "name", max_frames | poll `FileAccess.file_exists(<out>/<name>)` once per frame |

`_push(e)`: `_synth_pending += 1; Input.parse_input_event(e); Input.flush_buffered_events()`; the caller awaits one frame. `_input(e)`: if `_synth_pending > 0` decrement, else `_os_inputs += 1`; remember a one-line summary as `_last_input`. This is how liveness tells real OS input from synthesised input.

Screenshot: if `DisplayServer.get_name() == "headless"` print `QA_WARN headless no screenshot <name>` and return; await two `process_frame`, then `await RenderingServer.frame_post_draw`; engine grab = `get_viewport().get_texture().get_image()`, sample a 16x9 grid of pixels and print `QA_WARN uniform <name>` if they are all one colour, `save_png(<out>/<name>.png)`; external grab = pause the tree, write `<out>/<name>.grab`, `wait_file <name>.done` (cap 3000 frames), unpause (the shell wrapper's poll loop does the `import -window root` grab and renames `.grab` to `.done`).

`_qa_info()`: `{frame, os_inputs, last_input, shots, plants: QaPlants.active(), adapter: RenderingServer.get_video_adapter_name(), method: RenderingServer.get_current_rendering_method(), display: DisplayServer.get_name(), window_px: [w, h], fps_ms: Performance.get_monitor(Performance.TIME_PROCESS) * 1000}`.

Exit codes: 0 script finished; 2 arguments or JSON unreadable; 3 harness error (unknown verb, missing method or node, unknown plant). The driver never asserts on game state; every oracle lives in the shell or in the agent's reading of the outputs. GDScript runtime errors do not change the exit code, which is why `scan` greps the logs.

### 2. `qa_plants.gd`

```gdscript
static var _active: Dictionary = {}
static var _env_loaded := false
static func activate(id: String) -> void: _active[id] = true
static func is_active(id: String) -> bool:
	if not _env_loaded:
		_env_loaded = true
		for p in OS.get_environment("MOCKUP_PLANT").split(",", false): _active[p] = true
	return _active.has(id)
static func active() -> Array: return _active.keys()
```

A mockup's fault site is one line, for example `var s := 11 if QaPlants.is_active("seed-ignored") else p_seed`, with `const QaPlants := preload("res://scenes/mockups/_shared/qa_plants.gd")` at the top of the file. Three entry points, one registry: the env var (headless verify and the `run --plant` flag), the driver's `plant` verb, and the root's `qa_plant`.

### 3. The scene-root contract (document it in `_shared/README.md`)

```gdscript
const PLANTS: Array[String] = [...]        # every plant id this mockup implements
func qa_state() -> Dictionary              # required; JSON-safe values only (no Vector*); canonical from data, never from HUD labels;
                                           # always includes seed, hash, timing_ms, regen_count, plus the keys the mockup's brief names
func qa_plant(id: String) -> bool          # required; unknown id returns false; known id activates it, re-applies (regenerates), returns true
func qa_seed(n: int) -> void               # expected on any seeded mockup; synchronous regenerate
func qa_set(name: String, value) -> void   # optional; set a slider or toggle by name
func qa_camera(height: float, x: float, z: float) -> void   # optional; deterministic camera jump
```

All synchronous: side effects complete on return; the driver adds frames.

### 4. `scripts/mockup_qa.sh`

```
scripts/mockup_qa.sh run <mockup> <script.json> <outdir> [--res 1280x720] [--grab engine|external] [--plant id[,id]] [--timeout 600]
scripts/mockup_qa.sh liveness <mockup> <outdir>
scripts/mockup_qa.sh diff <a.png> <b.png> [fuzz%=5] [heatmap.png]
scripts/mockup_qa.sh scan <outdir>
scripts/mockup_qa.sh selftest
```

`run` launches `scenes/mockups/<mockup>/<mockup>_mockup.tscn`:

```bash
export LIBGL_ALWAYS_SOFTWARE=1 GALLIUM_DRIVER=llvmpipe LP_NUM_THREADS="${LP_NUM_THREADS:-2}" MOCKUP_PLANT="${PLANT:-}"
env -u DISPLAY -u WAYLAND_DISPLAY -u XAUTHORITY \
  timeout --kill-after=10 "$TIMEOUT" \
  xvfb-run -a -s "-screen 0 ${RES}x24" bash -c '<poll loop for *.grab in the background>; "$@" >"$OUT/stdout.log" 2>"$OUT/stderr.log"' _ "$OUT" \
  "$GODOT" --path . --display-driver x11 --rendering-driver opengl3 -w --position 0,0 --resolution "$RES" \
    --fixed-fps 30 --quit-after 100000 "$SCENE" -- --qa-script "$(realpath "$SCRIPT")" --qa-out "$(realpath "$OUT")" --qa-grab "$GRAB"
```

Then writes `exit.txt` and runs `scan`. `env -u` plus `--display-driver x11` makes it impossible to touch the live seat. `-w --position 0,0 --resolution` makes window px equal screen px equal screenshot px. `--fixed-fps 30` keeps `_process` delta constant so two runs of the same script produce the same pixels. `--quit-after` is a frame cap; `timeout` is the wall cap. `LP_NUM_THREADS=2` lets nine runs share sixteen cores.

`scan` writes `errors.txt` (count and lines matching `SCRIPT ERROR|^ERROR:|^USER ERROR|Node not found` in both logs), `shots.txt` (`identify -format '%f %wx%h sd=%[fx:standard_deviation]\n'` per PNG, with a `UNIFORM <file>` line for any stddev under 0.002), `marks.txt` (lines with `QA_WARN`, `QA_CALL`, `timing`).

`diff` prints the fraction of differing pixels: `compare -metric AE -fuzz "$FUZZ%" a b null:` (exit 1 means "different", not an error) divided by `identify -format '%[fx:w*h]'`; with a fourth argument also writes a difference heatmap via `magick a b -compose difference -composite -auto-level`.

`liveness` runs the same wrapper with `scenes/mockups/_shared/liveness.json` (`[["wait_file","xdotool.done",3000],["wait_frames",2],["state","liveness"]]`) and, inside the Xvfb session, `xdotool search --sync --name '^QA:'`, `windowactivate --sync`, `mousemove 640 360 click 1`, `key r`, then `touch <out>/xdotool.done`. Pass: `liveness.json` has `_qa.os_inputs >= 2`.

`selftest` runs three canned scripts against the landscape mockup and checks exit codes: a script with an unknown verb (expect 3), a file that is not JSON (expect 2), `[["state","ok"]]` (expect 0 and `ok.json` present).

### 5. `scripts/mockup_verify.sh`

```
scripts/mockup_verify.sh <mockup> [--plant id[,id]] [--timeout 120] [--refresh-cache]
```

Mirrors `scripts/run_godot_tests.sh:45`: `MOCKUP_PLANT="$PLANT" timeout "$TIMEOUT" godot --headless --path . --script "res://scenes/mockups/<mockup>/verify.gd" --quit-after 100000`, tee to `<scratch>/verify-<mockup>.log`. With no plant: pass iff exit 0 and a `VERIFY OK` line. With a plant: pass iff exit non-zero and at least one `FAIL:` line, printing `PLANT <id> LIVE (<n> FAIL)`; otherwise print `PLANT <id> DEAD` and exit 1. `--refresh-cache` (or any `.gd` newer than `.godot/global_script_class_cache.cfg`) first runs `godot --headless --path . --import` quietly.

### 6. Landscape retrofit

- New `landscape_mockup.gd` on the root node: `PLANTS = ["seed-ignored", "overlay-screen-space", "stability-noop", "flat-terrain", "city-disc", "regen-stall"]`; `qa_state()` returns `seed`, `hash` (`FieldMap.compute_hash()`), `canvas_wu`, `stability`, `kit`, `band`, `camera_height`, `elevation_max_wu` (max cell elevation), `overlay` (`{parent_class, parent_path, visible}` of the map-view geometry node), `city` (`{footprint_aspect, fraction_within_r_of_core}` over district >= 1 cells, r = 2000 wu), `timing_ms` (`{gen, ground, placer, total}` from `_regenerate`), `regen_count`, `piece_total`, `objective_px` (the objective node's `unproject_position` through the camera, as `[x, y]`). `qa_plant`, `qa_seed`, `qa_set("stability", v)`, `qa_set("kit", name)`, `qa_camera(height, x, z)` delegate to `HUD` and `CameraRig`. Add a `QADriver` child (Node, `_shared/qa_driver.gd`) to `landscape_mockup.tscn`.
- Fault sites, one line each: `seed-ignored` in `hud.gd:_regenerate` (seed forced to 11); `overlay-screen-space` in `map_view.gd` (draw the grid in `_draw()` screen space and skip creating `MapViewGeometry`); `stability-noop` in `field_map.gd:generate` (stability forced to 60); `flat-terrain` in `field_map.gd` (elevation scaled by 0.05); `city-disc` in `field_map.gd` (population = radial falloff from the core, ignoring slope and water); `regen-stall` in `hud.gd:_regenerate` (`OS.delay_msec(3000)`).
- `verify.gd` gains contract checks, each with its plant named in a preceding line `# plant: <id>` (the one place a comment is allowed): every `PLANTS` id returns true from `qa_plant` and `qa_plant("nope")` is false; `qa_state()` survives `JSON.stringify` and has every key above; `qa_seed(11)` twice gives equal state hashes; with `flat-terrain` active `elevation_max_wu` drops below 1000 (threshold: clean must be >= 3000); with `city-disc` active `fraction_within_r_of_core` rises above 0.9 (clean must be < 0.7); with `stability-noop` active the hash at stability 20 equals the hash at 90 (clean must differ); the map-view geometry parent is a `Node3D` under `World` (clean) and is not under `overlay-screen-space`. Run red before implementing the contract; commit the red state first.
- `qa/smoke.json`, in order: `state boot`; `seed 11`; `call qa_camera 3000 12000 12000`; `screenshot seed11_tactical`; `state seed11`; `seed 12`; `screenshot seed12_tactical`; `state seed12`; `seed 11`; `call qa_set stability 20`; `screenshot stab20`; `state stab20`; `call qa_set stability 90`; `screenshot stab90`; `state stab90`; `call qa_camera 1500 12000 12000`; `screenshot overlay_low`; `state overlay_low`; `call qa_camera 9000 12000 12000`; `screenshot overlay_high`; `state overlay_high`; `key R`; `state after_key_r`; `click_node HUD/VBoxContainer/RegenerateButton`; `state after_click_regen`; `click_node HUD/VBoxContainer/KitToggleButton`; `screenshot kit2_tactical`; `state kit2`. Default resolution 1280x720.
- `qa/checklist.md`, filled with measured numbers:

| id | oracle | threshold (candidate; Westley owns) | plant |
|---|---|---|---|
| ERR-0 | `errors.txt` count 0, `exit.txt` 0, no `UNIFORM` | exact | none |
| GPU-0 | `_qa.adapter` contains `llvmpipe`, `_qa.method == "gl_compatibility"` | exact | none |
| DET-1 | two clean runs: `seed11.json.hash` equal, `diff run1/seed11_tactical.png run2/seed11_tactical.png` | < 0.005 | none |
| SEED-2 | `hash` differs 11 vs 12 and `diff seed11_tactical.png seed12_tactical.png` | >= 0.20 clean; < 0.02 under `seed-ignored` | `seed-ignored` |
| CTRL-3 | `stab20.json.stability != stab90.json.stability`, `diff stab20.png stab90.png` | >= 0.05 clean; < 0.01 under `stability-noop` | `stability-noop` |
| OVERLAY-4 | `overlay.parent_class == "Node3D"` under `World`; `objective_px` at the two heights differ by >= 30 px and the marker colour is present at both positions in the matching PNGs | exact | `overlay-screen-space` |
| TIME-5 | `timing_ms.total` and `regen_count` increments after `key R` and after `click_node` | total <= 2000 ms; `regen_count` +1 each | `regen-stall` |
| SCALE-6 | `elevation_max_wu` and `canvas_wu` | >= 3000 and >= 24000 | `flat-terrain` |
| SHAPE-7 | `city.fraction_within_r_of_core` | < 0.7 | `city-disc` |

Visual questions (answered by Reading the PNGs beside `docs/bible/references/E-17/E-17-9..13*.png`, rows 09 to 13 in `references/E-17/notes.md`): Q1 does the tactical shot read as terrain with distinct biome bands; Q2 without the label, can you name what changed between `stab20.png` and `stab90.png`; Q3 do the overlay lines sit on the terrain at both heights; Q4 is elevation legible (cliffs shaded, valley versus peak); Q5 does the city read as districts along the river or coast and not a disc; Q6 any magenta or black pixels; Q7 any clipped HUD text at 720p. Each answer names the screenshot that proves it; anything you cannot judge goes in a `HELD:` list.

The mapping the harness must demonstrate: complaint "seeds don't differ / regenerate freezes" is caught by SEED-2 and TIME-5; "map lines don't move with the map" by OVERLAY-4 and Q3; "can't tell what the slider does" by CTRL-3 and Q2; "elevation weak, maps small" by SCALE-6 and Q4; "cities are circles" by SHAPE-7 and Q5.

### 7. Build order (commit after each)

1. `qa_plants.gd`, `qa_driver.gd` with only `state`, `wait_frames`, `screenshot`, `call`; `mockup_qa.sh run` and `scan`; run against the landscape mockup with a root stub that returns a minimal `qa_state` (this is the first end-to-end proof: a PNG that is not uniform and a JSON with `llvmpipe` in it).
2. `verify.gd` contract checks (red), `mockup_verify.sh` with the plant inversion.
3. `landscape_mockup.gd` full contract; checks go green.
4. Plants and their fault sites; every `--plant` prints `LIVE`.
5. Remaining driver verbs (`move`, `click`, `click_node`, `drag`, `wheel`, `key`, `key_down`/`key_up`, `plant`, `pause`, `tree`, `wait_file`); settle the open question below; `selftest`.
6. `liveness`, external grab path, `diff`.
7. `smoke.json`, two clean runs and one run per plant, `checklist.md` filled with the numbers, `_shared/README.md`, `kits/README.md` fix.

### Open question to settle on the first run (report the answer)

Whether `Input.parse_input_event` mouse positions are window pixels under the project's `canvas_items`/`expand` stretch at 1280x720. Settle it by clicking `RegenerateButton` once through `click_node` and once through raw `click` at the same computed pixel and comparing `regen_count`. If raw pixels are canvas units instead, convert in `_push` and say so in `_shared/README.md`.

## What the report must answer

1. The checklist table with clean and planted numbers for every oracle, and the answers to Q1 to Q7 with the proving screenshot, plus the `HELD:` list.
2. Wall time and frame time of one smoke run at 1280x720 and at 1920x1080; the `_qa.adapter` string.
3. The answer to the open question above, and any other harness fact a mockup brief should state (for example whether `key R` needs a prior click on empty ground to take focus from the SpinBox).
4. Anything in the driver design that did not work as written and what you did instead.
5. Under-defined points and candidates (never decisions): the default fuzz for `diff`, whether `tree` should include invisible Controls, the uniform-screenshot threshold.

## Verification

- `scripts/mockup_verify.sh landscape` prints `VERIFY OK`, exit 0. `scripts/mockup_verify.sh landscape --plant <id>` prints `PLANT <id> LIVE` for each of the six plants.
- `scripts/mockup_qa.sh selftest` passes (exit codes 3, 2, 0).
- `scripts/mockup_qa.sh run landscape scenes/mockups/landscape/qa/smoke.json <scratch>/landscape/clean` gives `exit.txt` 0, `errors.txt` 0, no `UNIFORM`, `_qa.adapter` containing `llvmpipe`; run twice, DET-1 holds.
- `scripts/mockup_qa.sh run landscape ... --plant seed-ignored <scratch>/landscape/plant-seed-ignored` then `scripts/mockup_qa.sh diff` on `seed11_tactical.png` versus `seed12_tactical.png` is below 0.02, while the clean pair is at or above 0.20. Same pattern for `stability-noop` (CTRL-3), `overlay-screen-space` (OVERLAY-4), `flat-terrain` (SCALE-6), `city-disc` (SHAPE-7), `regen-stall` (TIME-5).
- `scripts/mockup_qa.sh liveness landscape <scratch>/landscape/liveness` reports `os_inputs >= 2`.
- `grep -n ':0\b' scripts/mockup_qa.sh` and `grep -n 'DISPLAY=' scripts/mockup_qa.sh scenes/mockups/_shared/*.gd` are empty.
- Westley's interactive command still works unchanged: `~/.local/bin/godot --scene scenes/mockups/landscape/landscape_mockup.tscn` (you cannot run this on his seat; confirm instead that a `run` without `--qa-script` in the user args leaves the driver inert, by launching the scene under the wrapper with an empty `--` and checking no `_run.json` appears).
- `git status --short` on your branch shows only the paths this brief allows; `git diff --stat main -- docs tests csrc simulation project.godot` is empty.
