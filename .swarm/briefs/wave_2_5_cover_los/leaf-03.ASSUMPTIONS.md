## Assumptions made during leaf-03

- **Vertex order CCW**: angle increases `0 -> 2pi`, standard math convention — source: no source — pure guess (brief said "circle approximation 12 vertices evenly spaced", didn't specify winding).
- **Starting angle 0 rad (east, +x axis)**: first vertex at `(cx + r, cy)` — source: no source — pure guess (brief unspecified).
- **`hazard_zone_anchor` radius constant = `GRADIENT_HAZARD_COVER_RADIUS`**: hazard nodes emit TWO gradient sources (sensor_interference at `GRADIENT_HAZARD_RADIUS`, cover at `GRADIENT_HAZARD_COVER_RADIUS`). Used the cover one for polygon — source: `place_gradients` body lines 71-86 in `gradient_placer.py`.
- **`flank_route` radius = `GRADIENT_FLANK_COVER_RADIUS`** (cover, not obstacle): same dual-emission pattern; cover one chosen — source: `place_gradients` body lines 99-113.
- **Configurable verts via `COVER_POLYGON_VERTS`** (defaults to 12 via `getattr`): spec line 51 mentioned `COVER_POLYGON_VERTS = 12` as "possible new config". Used `getattr` so test passes today (constant not yet added) and a future config write picks it up — source: spec line 51.
- **Cover `GradientSource` emissions in `place_gradients` kept intact**: brief paragraph 2 explicit "the two functions coexist" — source: brief line 57.
