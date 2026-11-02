# Editor debug log, 2026-11-02

Branch `push/editor-debug`, worktree `om-push/wt/ed-run`, Godot 4.6.3 (Westley's editor and `godot.real` are the same version; the brief's mention of 4.7.2 was wrong). Hand-over for the Architect.

## Outcome

Westley ran the chain from his own checkout (`~/Projects/ouroboros-manifold`, main at `761c36cd`) after rebuilding its pipe binary: privacy, menu, galaxy, a mission, Deploy, a 2D match, end of mission all worked. No project source file changed. Every real problem found was environment state, not code. The `'done'` error is no longer seen, but its cause is inferred, not proven (row 1).

## Method

`chainrun.py` (this folder) walks the chain through the QA daemon (`tests/qa/desktop/daemon_client.py`) without the galaxy `step 10` shortcut the tests use, captures the console, and prints only distinct `ERROR` signatures. Run it as `python3 chainrun.py <worktree> <run-name> [--soak S] [--step10]`. Runs: r001 (98 signatures, all from row 2), r002 (0 signatures, walk reaches tactical, screenshot checked), r005 (stale pipe forced through `OM_PIPE`, row 1 evidence). `--real` (real window and GPU) did not work from the agent shell: Vulkan device init fails there with `ERR_CANT_CREATE`, a sandbox limit.

## Rows

| # | Console line | Where | Cause | Fix | Why no test caught it | What would pin it |
|---|---|---|---|---|---|---|
| 1 | `Invalid access to property or key 'done' on a base object of type 'Dictionary'.` (Westley, at Deploy, 2k+ copies; the `at:` line was not captured) | candidate only: `scenes/tactical_c/objective_markers.gd:43` reads `o["done"]` | Inferred: Westley's `pipe/ouroboros_pipe` was 123 KB from 2026-10-09; the current build is 1.69 MB and `OM_ABI_VERSION` became 9 on 2026-10-29. Not proven: forcing that stale binary in the worktree gave row 1b, not `'done'`. | Rebuilt: `scripts/build_pipe_linux.sh`, then atomic `cp` + `mv` into `pipe/` (the old binary was busy). After that the chain worked. | The tests build their own fresh pipe. `pipe/` is untracked, so nothing compares it to `csrc/`. | A client startup check that the pipe's ABI version equals the expected one, with a plain message in the ErrorPanel. Not checked whether one exists today. |
| 1b | `ERROR: galaxy_view: live snapshot failed: timed out waiting for the first snapshot` and `ERROR: mission_briefing: live mission frame failed: timed out waiting for the first snapshot` | `scenes/galaxy/galaxy_view.gd`, `scenes/mission_briefing/` (push_error) | Same stale pipe: no first snapshot arrives. The walk then sits on the ErrorPanel with no Deploy. | Same as row 1. | Same. | Same. |
| 2 | 98 distinct lines, e.g. `Cannot open file 'res://.godot/imported/vanguard_t1.glb-....scn'` | `assets/eras/settled_reach/units/*.glb` | The fresh worktree had never been imported. | `godot.real --headless --import --path .` (prints 0 errors after). | Gate trees are imported before play; the editor imports on open. | Not a bug for Westley's flow. A cold-clone note in the build notes would do. |
| 3 | `ERROR: GDExtension dynamic library not found: 'res://addons/godotsteam/godotsteam.gdextension'.` plus `Error loading extension` and two `os_unix.cpp:1061 ... ERR_FILE_NOT_FOUND` | `addons/godotsteam/` | Westley's checkout holds only the `.gdextension` file, not the Steam libraries (the worktree has them copied in). | Not fixed, benign. The beta chain never uses Steam (guarded by `Engine.has_singleton("Steam")`). | Gate trees copy the libraries. | A beta-channel story that copies or stubs the libraries, or makes the extension optional. |

## Still red (seen in Westley's final run, not fixed)

- `WARNING: SceneRouter: queued 'main_menu' replaced by 'main_menu'`, repeated at least four times. Backtrace: `autoload/scene_router.gd:43` `go_to`, called from `scenes/loading_screen/loading_screen.gd:47` `_process`. Loading screen asks for the same scene every frame. Related to the privacy-flag race documented in `tests/qa/desktop/daemon_client.py` (`GodotGame.start`), where the harness deletes the flag before each launch to dodge it.
- Exit-time renderer leaks: `ERROR: Pages in use exist at exit in PagedAllocator ...`, `ERROR: 1 shaders of type SceneForwardClusteredShaderRD were never freed`, `ERROR: 1 RID allocations of type ... Mesh/Material/Shader/Instance were leaked at exit`, `ERROR: 2 resources still in use at exit`, `WARNING: ObjectDB instances leaked at exit`. One 3D mesh instance is alive at quit. Not found which scene owns it; `--verbose` was not run.
- Not run: Westley's console from Deploy to the end of the mission was not pasted as a full log, only the lines above; `godot.real --headless --import --path .` was clean in the worktree only.
- Not tested: the real-GPU Vulkan path from the agent shell (sandbox), and a Continue from an existing save.

## Why the tests missed this class

The QA harness runs under Xvfb with software GL, builds a fresh pipe, deletes the privacy flag, and steps the galaxy 10 ticks before the mission. A real checkout has a long-lived untracked `pipe/`, real GPU rendering, existing saves and flags, and no shortcut. The failure Westley named at the start of the beta staircase, "passes tests, but doesn't actually run", sits in that gap.
