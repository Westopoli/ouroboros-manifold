# Galaxy bubble field: tests

Written first for `docs/northstar/plans/2026-10-02-galaxy-bubble-field-spec.md` (Step 2).
Frozen from the "galaxy field: failing tests" commit: builders do not edit anything here.
A suspected test defect is reported with evidence, never fixed in place, and no number is widened.

| Run | What | Needs |
|---|---|---|
| `tests/run_fast.sh static` | COST-SHAPE, ONE-DRAW (+ positive controls) | headless |
| `tests/run_fast.sh field` | FIELD-EQ, FIELD-VALUES, FIELD-ORDER, FIELD-CONQUEST, FIELD-MEM | Vulkan device under Xvfb (the card fills the grid) |
| `tests/run_fast.sh verify` | existing `scripts/mockup_verify.sh galaxy` | headless |
| `scripts/galaxy_perf.sh` | DEVICE, SHADER-COMPILES, SHELL-GPU, SHELL-SCALE, REFILL, LOOK-LAYERS, SCREENSHOTS | RTX 3060 under Xvfb |

Files: `field_reference.gd` (exact legacy formulas, quirk included, plus the old order-dependent
rival list), `grid_sampler.gd` (CPU reader of the grid, comparator, small CPU baker for the controls),
`big_galaxy.gd` (400/15 builder), `shader_cost.gd` (static shader analysis), `fixtures/` (the old
shader and old renderer kept as text so the "old system fails" controls survive their deletion),
`results/look/{old,new}/` and the side-by-side sheets.

## Product contract the tests rely on (the spec leaves signatures to the tests)

- `territory_field.gd` (Node): see the header of `test_field.gd`.
- `shaders/shell_field.gdshader`: only `sampler3D` uniforms, constant loop bounds, <= 100 fetches
  per pixel; `uniform int debug_mode`: mode 1 makes every pixel opaque with `ALBEDO.r = layers / 16`
  where layers is the number of faction layers the pixel drew.
- `shell_renderer.gd` on node `ShellRenderer` under `GalaxyView`: `setup / teardown /
  get_faction_shell_count` as before, plus `get_shell_viewport()`, `var res_divisor` (default
  `SHELL_RES_DIVISOR` = 2), `get_territory_field()`, `set_debug_mode(mode)`; exactly one
  `MeshInstance3D` in its subtree (the full-screen draw).
- `GalaxyView.build(galaxy)` and `GalaxyView.set_system_owner(id, faction)` keep working and reach the
  field (an owner change leaves `is_dirty()` true until the next frame's refill).

## Added beyond the spec's tables (flagged for Westley)

`FIELD-VALUES` (cell values within 0.002 x max(1, |value|) of the exact formulas; the spec says
"matches exact formulas to 0.001", half-float rounding is ~0.0005 relative), `FIELD-GRID` (96 cells,
128-unit cube), `FIELD-CONQUEST` sub-checks (clean/dirty/once-per-frame), `ONE-DRAW-factions`,
LOOK-LAYERS also bounds layers by 4 (the ruling's "up to four factions per ray"), SHELL-GPU also
fails a run whose GPU clock was below 1700 MHz. No threshold in the spec's tables was changed.
