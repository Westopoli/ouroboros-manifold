# Mockup self-QA harness

## The scene-root contract

Every mockup's root node script implements:

```gdscript
const PLANTS: Array[String] = [...]        # every plant id this mockup implements
func qa_state() -> Dictionary              # required; JSON-safe values only (no Vector*); canonical from data, never from HUD labels
func qa_plant(id: String) -> bool          # required; unknown id returns false; known id activates it, re-applies (regenerates), returns true
func qa_seed(n: int) -> void               # expected on any seeded mockup; synchronous regenerate
func qa_set(name: String, value) -> void   # optional; set a slider or toggle by name
func qa_camera(height: float, x: float, z: float) -> void   # optional; deterministic camera jump
```

All synchronous: side effects complete on return; the driver adds frames. Add `scenes/mockups/_shared/qa_driver.gd` as a child named `QADriver` of the scene root; it is inert unless `--qa-script` is present in the launch's user args.

A mockup's fault site is one line: `var s := 11 if QaPlants.is_active("seed-ignored") else p_seed`, with `const QaPlants := preload("res://scenes/mockups/_shared/qa_plants.gd")` at the top of the file. Three entry points, one registry: the `MOCKUP_PLANT` env var (headless verify and `run --plant`), the driver's `plant` verb, and the root's own `qa_plant`.

## The commands

```
scripts/mockup_qa.sh run <mockup> <script.json> <outdir> [--res 1280x720] [--grab engine|external] [--plant id[,id]] [--timeout 600]
scripts/mockup_qa.sh firstlook <mockup> <outdir> [--res 2560x1440] [--timeout 600]
scripts/mockup_qa.sh liveness <mockup> <outdir>
scripts/mockup_qa.sh diff <a.png> <b.png> [fuzz%=5] [heatmap.png]
scripts/mockup_qa.sh scan <outdir>
scripts/mockup_qa.sh selftest
scripts/mockup_verify.sh <mockup> [--plant id[,id]] [--timeout 120] [--refresh-cache]
```

`run` never touches the live seat: `env -u DISPLAY -u WAYLAND_DISPLAY -u XAUTHORITY` plus `--display-driver x11` inside a private `xvfb-run` session. Never set `DISPLAY` yourself, never use `:0`/`:1`.

## Verb table (qa_driver.gd)

| verb | args | behaviour |
|---|---|---|
| `wait_frames` | n | n awaited `process_frame` |
| `move` | x, y | mouse motion, window pixels |
| `click` | x, y [, button=1] | move, press, release |
| `click_node` | "Path/To/Control" | click at the control's screen-space centre |
| `drag` | x0, y0, x1, y1 [, steps=8] | move, press, lerped moves, release |
| `wheel` | n | abs(n) wheel events, up if n>0 |
| `key` | "R" | press + release |
| `key_down`, `key_up` | "W" | hold across frames |
| `call` | "method", args... | `root.callv(method, args)` |
| `seed` | n | sugar for `call qa_seed n` |
| `plant` | "id" | `root.qa_plant(id)`; false exits 3 |
| `pause` | true/false | `get_tree().paused` |
| `screenshot` | "name" | engine or external grab, see below |
| `state` | "name" | `root.qa_state()` + `_qa` info, to `<out>/<name>.json` |
| `expect` | "state.key.path", "changed"\|"increased"\|"equals" [, value] | reads `root.qa_state()` live, compares the value at `path` (dot-separated, numeric segments index into arrays) against the last `state` verb's dump (`changed`/`increased`) or the literal `value` (`equals`); prints `QA_EXPECT ok|FAIL <path>` |
| `tree` | "name" | visible Controls + all Node3Ds, to `<out>/<name>.json` |
| `wait_file` | "name", max_frames | poll for `<out>/<name>` |

Exit codes: 0 finished, 2 bad args/JSON, 3 harness error (unknown verb/node/method/plant). GDScript runtime errors do not change the exit code — `scan` greps the logs for those.

## First look

Why: the builders' and screenshot reviewers' QA drove every mockup only through `call qa_*` verbs at 1280x720 with the sim stepped by `qa_tick` — never through the real buttons, keys and edges at Westley's resolution with the clock running. Three mockups shipped past that QA broken: nothing moved (the sims start paused), buttons did nothing (they act on a selection a click never made), seed/reset did nothing, and edge scroll only worked toward the top-left (mouse compared in canvas space against window pixels, which only diverge on a screen bigger than 1920x1080). `firstlook` drives real input only, at his resolution, with the sim running.

```
scripts/mockup_qa.sh firstlook <mockup> <outdir> [--res 2560x1440] [--timeout 600]
```

- Runs `scenes/mockups/<mockup>/qa/firstlook.json` at 2560x1440 by default (his desktop is 4480x1440; 2560x1440 keeps the same 1440 height and exceeds the 1920x1080 base canvas on both axes — the exact condition his bug reports needed).
- Boots with `--qa-live` (sets the `QA_LIVE` env var; a mockup's "paused under QA" rule must key off its absence, not just "`--qa-script` is present" — see Rules below).
- No `--fixed-fps`: the sim's own clock runs at real wall speed, so `wait_frames` is real time here, not simulated ticks.
- Refuses to run (exit 2, printing the offending line) a script containing `call`, `seed`, `plant`, or `pause` — only real-input verbs are allowed: `move`, `click`, `click_node`, `drag`, `wheel`, `key`, `key_down`, `key_up`, `wait_frames`, `screenshot`, `state`, `expect`.

### The convention

Every mockup's `qa/firstlook.json` follows the same shape; adapt the exact state keys and controls to what that mockup's `qa_state()` and its own controls doc actually expose — not every mockup has a `tick`, a `selected`, or all four bindings:

1. Launch, wait 5 s of real time, `expect tick increased` — the sim runs by itself. A mockup with no autonomous clock (a static generator like `landscape`) instead asserts nothing changes without input (`regen_count`/`seed`/`kit`/etc. all `equals` their launch defaults): the point is "the mockup does what it claims at rest," not "every mockup ticks."
2. `move` to each of the four screen edges for 2 s (real-time budget — a slow llvmpipe frame already moves the camera a long way, so a handful of `wait_frames` covers it), `expect` the field that shows camera motion (`camera.x`/`camera.z` if `qa_state()` exposes them, or a fixed world point's projected pixel otherwise) `changed` in the direction that edge should pan. Prefer `changed` over a directional `increased` for anything measured across more than one edge test chained on the same running camera: `firstlook` scripts have no reset verb (`call`/`seed`/`pause` are banned), so edge N's test always starts from wherever edge N-1 left the camera, and a field that projects both world axes onto one screen axis (a 3D camera's projected point) can read a *different but still genuine* sign for the same edge depending on that leftover position — `changed` (any non-zero move, either direction) catches a dead edge exactly as strictly as `increased` once the noise floor below is zero, without being fooled by a context-dependent sign flip on a working one. If the motion field is also driven by something that settles asymptotically every time the camera stops moving (a ground-follow height lerp, an easing pan), `move` back to a neutral point and `wait_frames` long enough for that settle to fully finish (35 real frames was enough to reach bit-exact convergence under this harness's llvmpipe timing on `landscape`, confirmed by two `state` dumps 15 frames apart matching to the last printed digit) *before* the `state` an edge's `expect` will be measured against — an unsettled baseline leaves a residual few-pixel drift each frame that registers as `changed` on its own, with no edge scroll at all, and undermines a positive control's planted-fault case (the "no motion happened" reading needs to be exact, not "close to").
3. `move` onto a HUD control for 2 s; `expect` no side effect from hovering alone (camera unchanged, or, where the mockup exposes no camera field and the hover point isn't near a screen edge anyway, an integer like `regen_count` that only a real click moves, held `equals` its pre-hover value).
4. `click_node` every button the mockup's controls list, each followed by `expect` of the state key that button owns (regenerate changes `hash` or bumps `regen_count`, reset returns `tick` to 0, play toggles `playing`, kit toggle changes `kit`).
5. `key` every hotkey the mockup binds, with the same expectations as the button it duplicates.
6. A real `click` on a unit's projected pixel taken from a previous `state`'s `units_px` (or equivalent — the literal pixel the script author read from a prior run), `expect selected changed`; a `drag` box, `expect selected changed` — only for mockups with a selection system.
7. A `screenshot` after each group.

The mockup's own controls list (its README section or `qa/checklist.md`) is the contract `firstlook` tests: every documented button and hotkey gets an entry, or the doc is wrong.

### Rules

- A mockup's sim runs on an interactive launch, and pauses only under `--qa-script` **without** `--qa-live` — check for `QA_LIVE` being unset, not just "`--qa-script` is present."
- Every mouse comparison happens in one coordinate space. Two correct patterns: canvas everywhere (`get_viewport().get_mouse_position()` against `get_viewport().get_visible_rect().size`), or window pixels everywhere (`get_final_transform()`). Mixing them (one side canvas, one side `DisplayServer.window_get_size()`) is exactly the "edge scroll only works top-left" bug: it dead-zones the far threshold on a window bigger than the 1920x1080 base canvas, while the near threshold (compared against a small constant near zero) reads the same in either space and keeps working.
- No edge scroll while `gui_get_hovered_control()` is non-null.
- A button that acts on a selection acts on all friendlies when nothing is selected, and says so (label or tooltip) — never a silent no-op.
- **`get_viewport().get_mouse_position()` — and anything a mockup polls from it every frame — does not update from the driver's synthetic `move`/`click`/`drag` verbs.** It reflects the real OS/`DisplayServer` cursor, which `Input.parse_input_event()` alone never moves; the `InputEventMouseMotion` delivered to `_input()` on that same call always carries the correct, already-canvas-transformed position. A mockup that needs "where is the mouse" for anything `firstlook` must prove (edge scroll, hover checks) should track its own `_mouse_pos` from `_input()` instead of polling — correct in real play too, since Godot always delivers `_input` mouse events pre-transformed into viewport-local units. `qa_driver.gd`'s synthetic moves now also warp the real cursor (see Facts below), so a mockup that still polls is provable by `firstlook`, but tracking from `_input()` remains the pattern to write into a new camera rig — it doesn't depend on `warp_mouse` behaving identically on every platform and display driver, and a mockup that polls has no fallback if it ever doesn't.

### Reviewer

A fresh-eyes reviewer runs `firstlook` itself and reads its `QA_EXPECT` lines and screenshots before reading the builder's checklist. A checklist claim ("edge scroll works", "regenerate changes the map") that `firstlook` didn't independently exercise is not yet reviewed.

## Facts this harness proved, not assumed

- **Raw pixel coordinates in `move`/`click`/`drag` ARE window pixels.** Settled by clicking `RegenerateButton` once via `click_node` (which computes its centre through `get_final_transform()`) and once via a raw `click` at the identical numeric coordinate — both incremented `regen_count`. No conversion needed in `_push`.
- `get_viewport().get_visible_rect().size`, called from a bare `Node` (not a `Control`), reports 2.25x the real window size under this project's `canvas_items`/`expand` stretch (2880x1620 at a 1280x720 window). It is internally self-consistent (CameraRig's own edge-scroll check reads the same inflated space), so it never causes a bug, but it is not what "window centre" means to a script author reasoning in real pixels — the driver's initial "kill edge scroll" motion uses `DisplayServer.window_get_size()` instead.
- `xdotool windowactivate --sync` hard-fails under the private Xvfb (no window manager, no `_NET_ACTIVE_WINDOW`) and aborts the rest of the chained xdotool command — `liveness`'s click/key never fired. Use `windowfocus --sync` (`XSetInputFocus`, no WM required).
- ImageMagick 7's `compare -metric AE` prints `"921308 (0.999683)"`, not a bare integer. `diff` greps the leading integer before dividing by total pixels.
- `run` and `liveness` boot through `--script res://scenes/mockups/_shared/qa_boot.gd`, a `SceneTree` whose `_initialize` first frees every autoload node under the root (Godot instantiates the project's 19 autoloads even in `--script` mode) and then instantiates `--qa-scene` as `current_scene`. Why: the `SimBridge` autoload spawns the Python sim; in a worktree that sim dies at once (no built `libouroboros.so`, no `logs/`), `SimBridge._process` sees the dead pid and asks `SceneRouter` to route to the error screen, whose 0.3 s fade to black is the progressive dimming builders saw across three or four screenshots, and whose `_swap_scene` then frees the mockup, which is the stall at the next `screenshot` verb. `QA_KEEP_AUTOLOADS=1` keeps them for experiments. Westley's interactive `--scene` launch still runs the autoloads; a mockup must work either way. Consequence: no `ScanlineOverlay` in QA renders (a 3 percent scanline darkening), so QA pixels differ very slightly from his seat.
- Xvfb starts with `-s 0` (X screensaver off; it was a suspect for the stall and is harmless to disable). `XVFB_EXTRA` overrides that server argument and `QA_FIXED_FPS` the fixed frame rate, for experiments.
- `scan` ignores Godot's Compatibility-renderer shutdown noise (`... were leaked at exit`, `Pages in use exist at exit`, `... were never freed`, `Buffer ... leaked N bytes`), so `errors.txt` is 0 on a clean run.
- The class_name cache (`.godot/global_script_class_cache.cfg`) is gitignored and cold on a fresh worktree; a fresh checkout needs one `godot --headless --path . --import` before any `run`/`verify` invocation resolves `FieldMap`/`Placer`/etc. `mockup_verify.sh --refresh-cache` does this; `mockup_qa.sh run` does not (call it yourself once per fresh worktree).
- `--quit-after 100000` is a main-loop iteration cap, not a wall-clock timeout; the wrapper's own `timeout --kill-after=10 "$TIMEOUT"` is what actually bounds a run.
- `qa_driver.gd`'s `_make_motion` (used by `move`/`click`/`drag`) also calls `DisplayServer.warp_mouse()` (skipped under `--headless`, where it errors with no display). Proven on `landscape` at 2560x1440, camera parked over a fixed world point: without the warp, repeated `move` calls into the right edge zone left `objective_px` drifting <2px per frame (the residual ground-follow lerp settling, not a pan — `camera_rig.gd`'s edge-scroll polls `get_viewport().get_mouse_position()`, unmoved by the synthetic events); with the warp, the identical script panned the camera cleanly on all four edges (`objective_px` moving 60-230px per frame while parked at an edge). This is what makes `landscape/qa/firstlook.json` (`scenes/mockups/landscape/camera_rig.gd` is unmodified, still polling) a real positive control instead of one that can never move regardless of whether the coordinate-space bug is present.
- `scan`'s `errors.txt` also counts `QA_EXPECT FAIL` lines (the same grep as the other error classes, so the same "at exit/never freed/leaked bytes" exclusions apply); `marks.txt` lists every `QA_EXPECT ok`/`FAIL` line alongside `QA_WARN`/`QA_CALL`/timing.
