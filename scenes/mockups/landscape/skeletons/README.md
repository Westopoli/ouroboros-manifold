One skeleton is a hand-authored node layout (Q-119-02: layout method still open — this is "skeletons now, count growing", not a decision). `field_map.gd` picks one deterministically from `seed % skeleton_count`, then jitters positions up to 8% (`JITTER_MAX`).

Schema:

```json
{
  "id": "hillside_river",
  "name": "Hillside River",
  "nodes": [{"type": "objective", "position_ratio": [0.50, 0.62]}, ...],
  "river_ratio": [[0.58, 0.10], [0.62, 0.25], ...],
  "coast_y_ratio": 0.90
}
```

- `nodes`: exactly one each of `objective`, `flank_route`, `vantage`, `hazard_anchor`, `extraction`; exactly two `staging` and two `spawn_point`; exactly three `chokepoint`, always ordered `[first land approach, second land approach, river bridge]` — `field_map.gd` reads index 2 as the bridge for its elevation/interference sources, so every skeleton file must keep that order.
- `river_ratio`: control points for the river polyline, from the highlands down to the coast, passing near the objective (the river bend the city sits in).
- `coast_y_ratio`: the coastline's fixed y-ratio (all four skeletons keep the coast on the south edge in this pass — varying which edge is water is future work, not built).

All ratios are fractions of the canvas in [0,1]; `field_map.gd` converts to world units and jitters.
