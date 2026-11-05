# A3 Option B — Implementation Verification

Date: 2026-05-20
Agent: H (Sonnet implementer)
Spec: BLOCKER A3 Option B per `docs/legacy/test_specs/a3_bible_audit_per_archetype_map.md` + `docs/legacy/test_specs/a3_map_cover_audit.md`.

## Run protocol

Script: `simulation/verify_a3_coverage.py`. Boots each of the 10 canonical archetypes through `map_generator.generate_map` with a neutral RegionState (all fields 50, stability 0.5) at seed 42, canvas_size="medium". Reports compatible layouts, chosen layout, full gradient-source counts, and cover-density emission origins.

## Summary

| archetype | map generates? | cover emissions | bbox span (px) | compatible layouts |
|---|---|---|---|---|
| defensive_stand | Y | 7 | 8580 × 11194 | 5 |
| siege_breaking | Y | 5 | 8734 × 6117 | 6 |
| reconquest | Y | 8 | 11367 × 12675 | 7 |
| assault | Y | 7 | 8580 × 11194 | 5 |
| suppression | Y | 8 | 11367 × 12675 | 2 |
| multi_front_defense | Y | 5 | 8734 × 6117 | 3 |
| interception | Y | 7 | 11976 × 12818 | 8 |
| evacuation | Y | 8 | 11367 × 12675 | 7 |
| containment | Y | 5 | 8734 × 6117 | 3 |
| counterinsurgency | Y | 8 | 11367 × 12675 | 2 |

All 10 archetypes now generate non-empty maps. No `EMPTY_FIELD_FALLBACK`. Cover emissions span beyond just the player staging area in every archetype.

## Per-archetype detail (seed 42, medium canvas)

### defensive_stand
- chosen: layout_01_fortress_ridge
- canvas: 16000 × 16000
- cover origins: staging, hazard_zone_anchor, chokepoint × 2, flank_route × 2, objective
- bbox: (2805, 3070) → (11385, 14264)
- defender's prepared line (chokepoints + objective) now has cover, not just staging.

### siege_breaking
- chosen: layout_08_elevated_strongpoint
- canvas: 16000 × 16000
- cover origins: staging, objective, chokepoint × 3
- bbox: (3708, 4564) → (12442, 10681)
- 3 ringed chokepoints (enemy forward positions) emit cover — matches bible "enemy positions ring the perimeter — fortified forward bases."

### reconquest
- chosen: layout_06_flanking_pass
- canvas: 16000 × 16000
- cover origins: staging, hazard_zone_anchor × 2, chokepoint × 2, flank_route × 2, objective
- bbox: (2129, 1589) → (13496, 14264)
- Partial fortification readable in cover at chokepoints + objective per bible.

### assault
- chosen: layout_01_fortress_ridge
- canvas: 16000 × 16000
- cover origins: staging, hazard_zone_anchor, chokepoint × 2, flank_route × 2, objective
- bbox: (2805, 3070) → (11385, 14264)
- Defender's chokepoints + objective now emit cover — matches bible "prepared positions, fortified chokepoints."

### suppression
- chosen: layout_06_flanking_pass (seed 42 picked the dual-tagged option; layout_07_scattered_outposts is also compatible)
- canvas: 16000 × 16000
- cover origins: staging, hazard_zone_anchor × 2, chokepoint × 2, flank_route × 2, objective
- bbox: (2129, 1589) → (13496, 14264)
- Note: layout_07 (true scattered outposts) is available; seed 42 happened to pick layout_06. Across seeds both will be drawn.

### multi_front_defense
- chosen: layout_08_elevated_strongpoint
- canvas: 16000 × 16000
- cover origins: staging, objective, chokepoint × 3
- bbox: (3708, 4564) → (12442, 10681)
- Cover at each of the 3 chokepoints (one per front) — fixes the "worst cover coverage of all defended archetypes" finding in the audit.

### interception
- chosen: layout_02_open_plains_assault
- canvas: 16000 × 16000
- cover origins: staging, chokepoint × 1, flank_route × 4, objective
- bbox: (1649, 1446) → (13625, 14264)
- Bible "open terrain, no prepared positions" — layout_02 has only 1 chokepoint (vs 3 for chokepoint-heavy layouts). Cover is sparse + flank-driven, matching "terrain features provide tactical options."

### evacuation
- chosen: layout_06_flanking_pass
- canvas: 16000 × 16000
- cover origins: staging, hazard_zone_anchor × 2, chokepoint × 2, flank_route × 2, objective
- bbox: (2129, 1589) → (13496, 14264)
- Defensive holding position (chokepoint) + objective (extraction point) both have cover.

### containment
- chosen: layout_08_elevated_strongpoint
- canvas: 16000 × 16000
- cover origins: staging, objective, chokepoint × 3
- bbox: (3708, 4564) → (12442, 10681)
- Wide front, 3 chokepoints (boundary positions), cover at each — matches bible "garrison multiple chokepoints simultaneously."

### counterinsurgency
- chosen: layout_06_flanking_pass (seed 42; layout_07_scattered_outposts also compatible)
- canvas: 16000 × 16000
- cover origins: staging, hazard_zone_anchor × 2, chokepoint × 2, flank_route × 2, objective
- bbox: (2129, 1589) → (13496, 14264)
- hazard_zone_anchor zones now emit cover_density in addition to sensor_interference — insurgents "hide behind cover in defensible pockets" per bible.

## Sources changed

- `simulation/archetype_filters.py` — added `interception`, `containment` to FAIRNESS_PROFILES; rewrote ARCHETYPE_FILTERS entries for siege_breaking, reconquest, suppression, evacuation; added new entries for interception, containment; kept raid + rear_guard (test-protected).
- `simulation/gradient_placer.py` — added cover_density emission at chokepoint, objective, hazard_zone_anchor zones.
- `simulation/config.py` — added GRADIENT_CHOKEPOINT_COVER_*, GRADIENT_OBJECTIVE_COVER_*, GRADIENT_HAZARD_COVER_* constants.
- `simulation/layout_library/layout_02_open_plains_assault.json` — tag `interception` added.
- `simulation/layout_library/layout_03_three_front_valley.json` — tags `siege_breaking`, `containment` added.
- `simulation/layout_library/layout_04_dense_urban_grid.json` — tag `reconquest` added.
- `simulation/layout_library/layout_05_coastal_wedge.json` — tag `evacuation` added.
- `simulation/layout_library/layout_07_scattered_outposts.json` — tag `suppression` added.
- `simulation/layout_library/layout_08_elevated_strongpoint.json` — tag `containment` added.
- `simulation/pipe_transport.py:397` — EMPTY_FIELD_FALLBACK marker added to existing error log.

## Calibration source (cover radius/intensity)

Per `docs/bible_history/bible_2_00_world.md:188` ("cover density gradients are placed in defensible positions and approach corridors"). Anchored to existing staging/flank cover constants:

| zone type | radius | intensity | rationale |
|---|---|---|---|
| staging (existing) | 800 | 0.60 | broad rear-area safe zone |
| chokepoint (NEW) | 550 | 0.55 | tighter than staging, denser than flank — prepared defensive ground |
| objective (NEW) | 400 | 0.50 | single focal point with prepared positions |
| hazard_zone_anchor (NEW) | 400 | 0.35 | mild — rebels/units hide *within* interference, cover overlay mild |
| flank_route (existing) | 450 | 0.40 | mild concealment along flank |

Single set of constants per zone type — per-archetype tuning is a post-launch concern.
