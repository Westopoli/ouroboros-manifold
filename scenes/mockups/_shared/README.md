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

## The two commands

```
scripts/mockup_qa.sh run <mockup> <script.json> <outdir> [--res 1280x720] [--grab engine|external] [--plant id[,id]] [--timeout 600]
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
| `tree` | "name" | visible Controls + all Node3Ds, to `<out>/<name>.json` |
| `wait_file` | "name", max_frames | poll for `<out>/<name>` |

Exit codes: 0 finished, 2 bad args/JSON, 3 harness error (unknown verb/node/method/plant). GDScript runtime errors do not change the exit code — `scan` greps the logs for those.

## Facts this harness proved, not assumed

- **Raw pixel coordinates in `move`/`click`/`drag` ARE window pixels.** Settled by clicking `RegenerateButton` once via `click_node` (which computes its centre through `get_final_transform()`) and once via a raw `click` at the identical numeric coordinate — both incremented `regen_count`. No conversion needed in `_push`.
- `get_viewport().get_visible_rect().size`, called from a bare `Node` (not a `Control`), reports 2.25x the real window size under this project's `canvas_items`/`expand` stretch (2880x1620 at a 1280x720 window). It is internally self-consistent (CameraRig's own edge-scroll check reads the same inflated space), so it never causes a bug, but it is not what "window centre" means to a script author reasoning in real pixels — the driver's initial "kill edge scroll" motion uses `DisplayServer.window_get_size()` instead.
- `xdotool windowactivate --sync` hard-fails under the private Xvfb (no window manager, no `_NET_ACTIVE_WINDOW`) and aborts the rest of the chained xdotool command — `liveness`'s click/key never fired. Use `windowfocus --sync` (`XSetInputFocus`, no WM required).
- ImageMagick 7's `compare -metric AE` prints `"921308 (0.999683)"`, not a bare integer. `diff` greps the leading integer before dividing by total pixels.
- `run` and `liveness` do not launch the scene by path. They boot through `--script res://scenes/mockups/_shared/qa_boot.gd` (a `SceneTree` whose `_initialize` instantiates `--qa-scene` and sets `current_scene`), so no autoload runs: the project's `SimBridge` autoload spawns a Python sim that dies under the wrapper and, after 30 s, `SceneRouter` would route to the error screen and free the mockup mid-script (reproduced twice on the first harness pass). Westley's interactive `--scene` launch still runs the autoloads; a mockup must work either way.
- `scan` ignores Godot's Compatibility-renderer shutdown noise (`... were leaked at exit`, `Pages in use exist at exit`, `... were never freed`, `Buffer ... leaked N bytes`), so `errors.txt` is 0 on a clean run.
- The class_name cache (`.godot/global_script_class_cache.cfg`) is gitignored and cold on a fresh worktree; a fresh checkout needs one `godot --headless --path . --import` before any `run`/`verify` invocation resolves `FieldMap`/`Placer`/etc. `mockup_verify.sh --refresh-cache` does this; `mockup_qa.sh run` does not (call it yourself once per fresh worktree).
- `--quit-after 100000` is a main-loop iteration cap, not a wall-clock timeout; the wrapper's own `timeout --kill-after=10 "$TIMEOUT"` is what actually bounds a run.
