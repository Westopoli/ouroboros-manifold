# Landscape kit schema

A kit JSON reskins the same field-map output for one era. Keys:

- `name` — kit id string.
- `palette` — hex colors for `sky`, `water`, `zone_a`, `zone_b`, `zone_c`, `cliff`. Free-standing swatches; individual rules below carry their own `color` too.
- `water_is` — `"surface"` (draw water as a surface, e.g. sea) or `"void"` (draw nothing, placer darkens sky instead).
- `terrain` — ordered list of `{when, piece, density, mesh, size, color}` rules for non-city ground cover (rock, vegetation, field rows, debris, etc). First matching rule per cell wins.
- `city` — same rule shape, keyed by district band (1..4). Applies only where `district >= 1`.
- `borders` — per border kind (`wall`, `coast`, `cliff`, ...) a `{mesh, height, color, crossing}` block; `crossing` maps a crossing kind (`gate`, `bridge`, `pass`, ...) to its own `{mesh, color}`.
- `nodes` — per node type (`objective`, `staging`, `transit`, `chokepoint`, `flank_route`, `vantage`, `hazard_anchor`, `spawn_point`, `extraction`) a `{mesh, color}`.
- `backdrop` — single `{mesh, color, distance}` for the horizon prop.

`when` conditions: a field name (`obstacle`, `cover`, `elevation`, `interference`, `water`, `population`, `wealth`) maps to a `[min, max]` range over the cell's 0..1 value; `zone` matches exactly one of `zone_a`/`zone_b`/`zone_c`; `district` matches exactly one int 0..4. A rule can combine multiple keys (all must match).

`mesh` must be one of the fixed vocabulary below. Any other name makes the placer draw a magenta placeholder box.

Fixed mesh vocabulary: `box`, `box_gable`, `prism`, `cone_on_stick`, `flat_box`, `colonnade`, `wall_segment`, `gate_arch`, `bridge_arches`, `cliff_face`, `stair_ramp`, `acropolis`, `camp_ring`, `mountain_range`, `hab_pod`, `hab_ring`, `spire`, `hull_segment`, `airlock`, `docking_spine`, `ore_chunk`, `derelict`, `ice_shard`, `asteroid_backdrop`, `none`.

Precedence: inside any cell with `district >= 1`, `city` rules win over `terrain` rules.
