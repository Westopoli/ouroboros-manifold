---
leaf_id: leaf-09
spec_file: docs/test_specs/cover_asteroid_los_spec.md
spec_lines: 74-76
test_file: tests/test_cover_render.gd
impl_file: scenes/tactical/terrain_renderer.gd
impl_files:
  - autoload/era_theme_resolver.gd
contract_imports:
do_not_edit:
  - simulation/damage.py
  - simulation/test_asteroid_damage_gate.py
  - simulation/tactical_engine.py
  - simulation/test_asteroid_ai_peek.py
  - simulation/asteroid_integration_fixture.py
  - simulation/test_asteroid_integration.py
  - simulation/tactical_map.py
  - simulation/gradient_placer.py
  - simulation/fog_of_war.py
  - simulation/snapshot_serializer.py
  - simulation/config.py
  - docs/bible/bible_world.md
  - docs/bible/bible_combat.md
  - docs/test_specs/cover_asteroid_los_spec.md
  - docs/test_specs/cover_los_rework_spec.md
impl_line_budget: 200
test_assertion_budget: 10
wave: 3
---

## Task

Wire Godot asteroid render per spec_lines 74-76.

`autoload/era_theme_resolver.gd`: add per-era cover asset keys `cover_tiny`, `cover_small`, `cover_medium`, `cover_huge`. Settled Reach era: `cover_tiny` + `cover_small` → existing `asteroid_small.glb`; `cover_medium` → `asteroid_medium.glb`; `cover_huge` → `asteroid_large.glb` (verify GLB paths under `assets/` glob — if absent, escalate). Other eras: keys present but empty string. Add accessor `get_cover_asset(era_id: String, scale_class: String) -> String`.

`scenes/tactical/terrain_renderer.gd`: remove stale comment at line 219. Add `_scatter_cover_asteroids(asteroids: Array, map_seed: int)` called from existing map-load path. Per scale_class, instantiate one `MultiMeshInstance3D` whose source mesh is loaded from `EraThemeResolver.get_cover_asset(current_era_id, class)`. For each asteroid dict (shape from L8: `{id, cluster, x, y, r, h, class}`), append a `Transform3D` with origin `(x, 0, y)` and basis scaled uniformly by `radius_xy / base_glb_radius` (use `radius_xy / 1.0` as placeholder if base_glb_radius unknown — log assumption).

Tests (spec_lines 252-256): `tests/test_cover_render.gd` — instantiate terrain_renderer in isolated scene, feed mock manifest with 4 asteroids (one each scale_class), call `_scatter_cover_asteroids(asteroids, 42)`, assert 4 MultiMeshInstance3D children exist, each with instance_count == 1, each transform origin matches manifest x/y. Headless if practical; otherwise document manual repro steps as comments at top of test. Use `scripts/run_godot_tests.sh` runner if it exists (spec line 252).

## Acceptance

Run `bash scripts/run_godot_tests.sh tests/test_cover_render.gd` if runner exists, else `godot --headless --path . --script res://tests/test_cover_render.gd --quit-after 30`. Confirm RED. Implement in impl_files only. Confirm GREEN. Write final files to `.swarm/pending/leaf-09/` mirroring repo paths. Stop.

## Escalation triggers

Stop and report to the parent if:
- A type the test imports is not in contract_imports.
- The impl would need to create a new file (test_file IS allowed; runner script absent → escalate).
- The impl would need to edit a file in do_not_edit.
- Asteroid GLB paths absent under `assets/` — escalate before guessing.
- Two sibling assertions seem to require contradictory behavior.
- Impl approaches impl_line_budget with assertions still failing.

## Assumption log

Log inferences (GLB asset paths, base_glb_radius value, current_era_id source, map-load hook site, headless feasibility) to `.swarm/briefs/wave_2_5R_cover_asteroid/leaf-09.ASSUMPTIONS.md`.
