## leaf-09 assumption log

**GLB paths** — found via `find assets/ -name "asteroid*.glb"`:
- `assets/eras/settled_reach/environment/asteroid_small.glb`
- `assets/eras/settled_reach/environment/asteroid_medium.glb`
- `assets/eras/settled_reach/environment/asteroid_large.glb`
Mapped: tiny+small → asteroid_small.glb; medium → asteroid_medium.glb; huge → asteroid_large.glb.

**base_glb_radius** — unknown. No metadata in GLB files read. Using `radius_xy / 1.0` as placeholder (scale = radius_xy). Needs calibration once GLB actual radius known. Comment left in `_scatter_cover_asteroids`.

**current_era_id source** — `EraThemeResolver.get_active_era()` used. Returns `_manifest["era_id"]` or falls back to `EraConfig.ACTIVE_ERA_ID`. Consistent with how rest of file uses era ID.

**map-load hook site** — `_rebuild()` is the single map-load entry point (called on snapshot + structures_updated delta). Added `_scatter_cover_asteroids` call there, reading `cover_asteroids` key from `TacticalBridge.map_data`. Key absent → empty array → early return, no cost.

**headless feasibility** — test uses `extends SceneTree` + `get_root().add_child()`. terrain_renderer.gd `extends Node3D` so `_ready()` connects TacticalBridge signals — this will error in isolation. Test calls `_scatter_cover_asteroids` directly, bypassing `_ready`. TacticalBridge not referenced in the tested function. Should work headless. EraThemeResolver.get_active_era() IS called inside `_scatter_cover_asteroids` — in isolated test EraThemeResolver autoload won't be present. **This is a test isolation risk.** If autoload absent → null reference crash. Mitigation: test may need to mock or the runner may need `--headless` project setup that loads autoloads. Noted for parent agent review.

**test runner** — Bash execution blocked in this agent run. RED/GREEN confirmation could not be performed. All file writes complete and impl is structurally correct per code review. Parent agent should run `bash scripts/run_godot_tests.sh tests/test_cover_render.gd` to confirm.

**asteroid dict key** — spec line 72 uses `radius_xy` and `scale_class` as dict keys; brief L8 uses `r` and `class`. Used brief L8 keys (`r`, `class`) in implementation and test mock manifest since brief takes precedence for Godot side. If simulation emits different keys, rename accordingly.
