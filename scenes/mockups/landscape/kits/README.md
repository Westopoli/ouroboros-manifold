# Landscape kit schema

A kit JSON reskins the same field-map output for one era. Keys:

- `name` — kit id string.
- `palette` — hex colors for `sky`, `water`, `zone_a`, `zone_b`, `zone_c`, `zone_d`, `zone_e`, `cliff`. Free-standing swatches; individual rules below carry their own `color` too.
- `water_is` — `"surface"` (draw water as a surface, e.g. sea) or `"void"` (draw nothing, placer darkens sky instead).
- `terrain` — ordered list of `{when, piece, density, mesh, size, color}` rules for non-city ground cover (rock, vegetation, field rows, debris, etc). First matching rule per cell wins.
- `city` — same rule shape, keyed by district band (1..4). Applies only where `district >= 1`.
- `borders` — per border kind (`wall`, `coast`, `cliff`, ...) a `{mesh, height, color, crossing}` block; `crossing` maps a crossing kind (`gate`, `bridge`, `pass`, ...) to its own `{mesh, color}`.
- `nodes` — per node type (`objective`, `staging`, `transit`, `chokepoint`, `flank_route`, `vantage`, `hazard_anchor`, `spawn_point`, `extraction`) a `{mesh, color}`.
- `backdrop` — single `{mesh, color, distance}` for the horizon prop.

`when` conditions: a field name (`obstacle`, `cover`, `elevation`, `interference`, `water`, `population`, `wealth`) maps to a `[min, max]` range over the cell's 0..1 value; `zone` matches exactly one of `zone_a`/`zone_b`/`zone_c`; `district` matches exactly one int 0..4. A rule can combine multiple keys (all must match).

`mesh` must be one of the fixed vocabulary below. Any other name makes the placer draw a magenta placeholder box.

Fixed mesh vocabulary: `box`, `box_gable`, `prism`, `cone_on_stick`, `flat_box`, `colonnade`, `wall_segment`, `gate_arch`, `bridge_arches`, `cliff_face`, `stair_ramp`, `acropolis`, `camp_ring`, `mountain_range`, `hab_pod`, `hab_ring`, `spire`, `hull_segment`, `airlock`, `docking_spine`, `ore_chunk`, `derelict`, `ice_shard`, `asteroid_backdrop`, `none`.

Space kit (`space.json`, built on a `SpaceFieldMap`): binary sheets, no ground and no terrain rules. `plate` and `rubble` (`{mesh, size}`, a square tile `[side, thickness]` on `box`) draw every blocked cell; `layers` is five hex colours, layer 1 to 5; `mass` is the hex colour of the one large mass; `tunnel` (`{mesh, size, color}`) outlines a plate dropped for reachability as four thin strips, and its `size` is the unit the strips are scaled from; `shaft` marks scarce layer changes; `small_only` is the hex colour of the small-craft sections' outline and of the cells only small craft can pass; `view_blocked` is the hex colour of blocked cells in the functional views; `palette.water` colours the dark plane under layer 1. `nodes` also takes `spawn_point` there.

Precedence: inside any cell with `district >= 1`, `city` rules win over `terrain` rules.
