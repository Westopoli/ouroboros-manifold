# Checkpoint D — Per-(Layout, Archetype) Fairness Audit

Post-C pass rates: 0/63 pairs (0%). Three systemic root causes persist after the zero-count fix (D1) and profile authoring (D2).

## Systemic Diagnosis

### Root Cause 1: Vantage nodes positioned on enemy side

All vantage nodes across layouts 01, 02, 03, 05, 06 sit at y=0.30–0.38. Since staging is at y=0.72–0.92 and spawn_point at y=0.04–0.08, every vantage node is closer (Euclidean) to spawn than to staging. Result: `_proximity_balance` returns 0.00 for every layout that has vantage.

Exception: layout_08 has staging at center (0.5, 0.5), so its vantage nodes at y=0.36 are closer to staging. Ratio = 2.00 (opposite problem — all player-side).

Layouts 04, 07 have zero vantage → skipped (correct post-D1).

**Fix class: A (rebalance positions).** Move vantage nodes toward y≈0.52–0.58 so they're roughly equidistant from both sides.

### Root Cause 2: Travel time (BFS hops) structurally asymmetric

The `_travel_time_balance` metric counts BFS hops to the nearest chokepoint (or objective if no chokepoints). Staging typically connects through transit/approach nodes to chokepoints (2–4 hops), while spawn_point connects through the objective area (1–2 hops). This produces inherent asymmetry.

Current travel ratios (constant across all archetypes for a given layout):
| Layout | Travel Ratio | Player Hops | Enemy Hops | Front Type |
|--------|-------------|-------------|------------|------------|
| 01_fortress_ridge | 1.00 | 2 | 2 | chokepoint |
| 02_open_plains | 0.50 | 2 | 4 | chokepoint |
| 03_three_front | 0.50 | 1 | 2 | chokepoint |
| 04_dense_urban | 0.25 | 1 | 4 | chokepoint |
| 05_coastal_wedge | 1.00 | 2 | 2 | chokepoint |
| 06_flanking_pass | 0.67 | 2 | 3 | chokepoint |
| 07_scattered | 4.00 | 4 | 1 | objective |
| 08_elevated | 0.50 | 1 | 2 | chokepoint |

Only layouts 01 and 05 have travel ≈ 1.0. Travel = 0.50 fails every profile (even raid's 1.00±0.30 only accepts 0.70–1.30). Travel = 4.00 (layout_07) and 0.25 (layout_04) are extreme outliers.

**Fix class: B (add/remove edges).** Specific edge changes per layout to equalize hop counts. See per-layout sections below.

### Root Cause 3: Path balance (max-flow) asymmetric on some layouts

Most layouts have path_balance = 1.00 (symmetric edge-disjoint paths). Two outliers:
- layout_01: ratio 3.00 (player has 3 paths to objective, enemy has 1)
- layout_05: ratio 2.00 (player has 2 paths, enemy has 1)

Path = 1.00 passes 7/10 archetypes but fails assault (needs 1.50–1.90), defensive_stand (needs 0.45–0.75), and evacuation (needs 1.05–1.55).

**Fix class: B (add edges) for outliers; C (filter exclusion) for archetype-specific path mismatches** that are inherent to the layout's design intent.

### Root Cause 4: Hazard positions asymmetric

- Layouts 01, 05, 06: hazards at y=0.62–0.78 (player side). Ratio = 2.00.
- Layout 04: hazard at y=0.38 (enemy side). Ratio = 0.00.
- Layout 07: 5 hazards distributed. Ratio = 0.67.
- Layouts 02, 03, 08: no hazards → skipped.

**Fix class: A (rebalance positions).**

---

## Per-Layout Proposed Fixes

### Layout 01: Fortress Ridge

**Current ratios:** path=3.00, travel=1.00, vantage=0.00, hazard=2.00
**Archetype pools:** assault, defensive_stand, evacuation, raid, rear_guard, reconquest, siege_breaking, suppression (8 archetypes)

**Proposed fixes:**
1. **Class A — vantage:** Move `vantage_left` (0.22, 0.32) → (0.22, 0.55) and `vantage_right` (0.78, 0.32) → (0.78, 0.55). Shifts vantage from enemy-side to roughly equidistant. Expected ratio: ~1.0.
2. **Class A — hazard:** Move `ravine_hazard` (0.5, 0.62) → (0.5, 0.48). Shifts from player-side to center. Expected ratio: ~1.0.
3. **Class B — path balance:** Add edge `spawn_enemy → reinforcement_left` (or `reinforcement_right`). Gives enemy a second edge-disjoint path to objective (spawn→reinforcement→objective). Expected: enemy paths 1→2, ratio 3/2 = 1.50. Alternatively, add both reinforcement edges: enemy gets 3 paths, ratio = 3/3 = 1.00.

**Post-fix estimated ratios:** path≈1.0–1.5, travel=1.0, vantage≈1.0, hazard≈1.0.

**With path≈1.0:** passes multi_front, counterinsurgency, siege, reconquest, suppression, raid, rear_guard. Fails assault (needs 1.50+), defensive_stand (needs ≤0.75), evacuation (needs 1.05+).
**With path≈1.5:** passes assault, siege, evacuation, reconquest, suppression, raid, rear_guard. Fails defensive_stand (needs ≤0.75), multi_front (needs 0.85–1.15).

**Recommendation:** Add one enemy reinforcement edge for path≈1.5. Use Class C to exclude defensive_stand (a 3-path player layout doesn't match "constrained defensive ingress"). 5/8 archetypes pass; defensive_stand excluded from this layout.

### Layout 02: Open Plains Assault

**Current ratios:** path=1.00, travel=0.50, vantage=0.00, hazard=skipped
**Archetype pools:** assault, defensive_stand, evacuation, raid, rear_guard, reconquest, siege_breaking, suppression

**Proposed fixes:**
1. **Class A — vantage:** Move `vantage_ridge` (0.5, 0.35) → (0.5, 0.55). Expected ratio: ~1.0 (equidistant from both sides).
2. **Class B — travel:** Add edge `objective_command → ford_chokepoint`. Enemy path: spawn→objective→ford = 2 hops. Player: staging→advance→ford = 2 hops. Expected ratio: 2/2 = 1.00.

**Post-fix estimated ratios:** path=1.0, travel≈1.0, vantage≈1.0, hazard=skipped.

**Passes:** multi_front (not in pool), counterinsurgency (not in pool), siege, reconquest, suppression, raid, rear_guard = 5 non-prototype + the pool archetypes it's in.
**Fails:** assault (path needs 1.50+), defensive_stand (path needs ≤0.75), evacuation (path needs 1.05+).

**Recommendation:** Class C — exclude assault and defensive_stand from this layout (path=1.0 can't satisfy their directional path requirements without fundamentally changing the layout). Evacuation borderline — path=1.0 is 0.05 below the 1.05 lower bound; could pass with jitter variance.

### Layout 03: Three-Front Valley

**Current ratios:** path=1.00, travel=0.50, vantage=0.00, hazard=skipped
**Archetype pools:** multi_front_defense, evacuation, raid, rear_guard, reconquest, siege_breaking, suppression

**Proposed fixes:**
1. **Class A — vantage:** Move `vantage_west_ridge` (0.12, 0.38) → (0.12, 0.52) and `vantage_east_ridge` (0.88, 0.38) → (0.88, 0.52). Expected ratio: ~1.0.
2. **Class B — travel:** Player has direct edge `staging_center → chokepoint_north` (1 hop). Enemy is spawn→transit→chokepoint (2 hops). Two options:
   - *Option A:* Add intermediate transit between staging and chokepoints. E.g., add `transit_center_south` at (0.5, 0.55) with edges staging→transit_center_south→chokepoint_north. Remove direct staging→chokepoint edges. Player = 2 hops, enemy = 2 hops. Ratio = 1.0. **Recommended.** Preserves multi-front topology while equalizing approach time.
   - *Option B:* Add direct spawn→chokepoint edges. Enemy = 1 hop. Ratio = 1/1 = 1.0. But this makes enemy appear directly at chokepoints, undermining the "approach from multiple directions" character.

**Post-fix estimated ratios:** path=1.0, travel≈1.0, vantage≈1.0, hazard=skipped.

**Passes:** multi_front_defense (path=1.0 in 0.85–1.15 ✓), siege, reconquest, suppression, raid, rear_guard.
**Fails:** evacuation (path needs 1.05+).

**Recommendation:** Option A for travel fix. Class C to tighten evacuation filter if path remains at 1.0.

### Layout 04: Dense Urban Grid

**Current ratios:** path=1.00, travel=0.25, vantage=skipped, hazard=0.00
**Archetype pools:** assault, defensive_stand, multi_front_defense, evacuation, raid, rear_guard, reconquest, siege_breaking, suppression

**Proposed fixes:**
1. **Class A — hazard:** Move `hazard_rubble` (0.5, 0.38) → (0.5, 0.55). Shifts from enemy-side to center. Expected ratio: ~1.0.
2. **Class B — travel:** Two changes needed:
   - Remove direct edge `staging_south → choke_central_square`. Player now routes staging→block_sw→choke_west (2 hops) or staging→block_se→choke_east (2 hops).
   - Add edge `objective_citadel → hazard_rubble` (or `reinforcement_north → choke_central_square`). Enemy: spawn→objective→reinforcement→choke_central = 3 hops. Still asymmetric. Better: add `objective_citadel → choke_central_square` directly. Enemy: spawn→objective→choke = 2 hops. Ratio = 2/2 = 1.0.

**Post-fix estimated ratios:** path=1.0, travel≈1.0, vantage=skipped, hazard≈1.0.

**Passes:** multi_front (path 0.85–1.15 ✓), siege, reconquest, suppression, raid, rear_guard.
**Fails:** assault (path needs 1.50+), defensive_stand (path needs ≤0.75), evacuation (path needs 1.05+).

**Recommendation:** Class B travel fix as described. Class C to exclude assault and defensive_stand (same rationale as layout 02). Evacuation borderline.

### Layout 05: Coastal Wedge

**Current ratios:** path=2.00, travel=1.00, vantage=0.00, hazard=2.00
**Archetype pools:** assault, defensive_stand, evacuation, raid, rear_guard, reconquest, siege_breaking, suppression

**Proposed fixes:**
1. **Class A — vantage:** Move `cliff_vantage` (0.28, 0.52) → (0.55, 0.65). Currently closer to spawn (0.14, 0.08) than staging (0.82, 0.88). Moving to (0.55, 0.65) makes it roughly equidistant. Expected ratio: ~1.0.
2. **Class A — hazard:** Move `hazard_surf_zone` (0.42, 0.78) → (0.42, 0.55). Shifts from player-side to center. Expected ratio: ~1.0.
3. **Class B — path balance:** Add edge `spawn_enemy → reinforcement_harbor`. Enemy gains second path: spawn→reinforcement→objective (in addition to spawn→objective). Expected: enemy paths 1→2, ratio 2/2 = 1.0.

**Post-fix estimated ratios:** path≈1.0, travel=1.0, vantage≈1.0, hazard≈1.0.

**Passes:** siege, reconquest, suppression, raid, rear_guard, multi_front (not in pool), counterinsurgency (not in pool).
**Fails:** assault (path needs 1.50+), defensive_stand (path needs ≤0.75), evacuation (path needs 1.05+).

**Recommendation:** Class B path fix. Class C to exclude assault and defensive_stand. Evacuation borderline.

### Layout 06: Flanking Pass

**Current ratios:** path=1.00, travel=0.67, vantage=0.00, hazard=2.00
**Archetype pools:** assault, defensive_stand, counterinsurgency, evacuation, raid, rear_guard, reconquest, siege_breaking, suppression

**Proposed fixes:**
1. **Class A — vantage:** Move `vantage_summit_west` (0.25, 0.30) → (0.25, 0.52) and `vantage_summit_east` (0.75, 0.30) → (0.75, 0.52). Expected ratio: ~1.0.
2. **Class A — hazard:** Move `hazard_cliff_west` (0.18, 0.65) → (0.18, 0.48) and `hazard_cliff_east` (0.82, 0.65) → (0.82, 0.48). Shifts from player-side to center. Expected ratio: ~1.0.
3. **Class B — travel:** Add edge `objective_stronghold → choke_pass_exit`. Enemy: spawn→objective→choke_exit = 2 hops. Player: staging→approach→choke_entrance = 2 hops. Ratio ≈ 1.0. (Note: player path goes to choke_entrance, enemy to choke_exit — both are chokepoints, so BFS picks the closer one for each side.)

**Post-fix estimated ratios:** path=1.0, travel≈1.0, vantage≈1.0, hazard≈1.0.

**Passes:** counterinsurgency (path 0.75–1.25 ✓), siege, reconquest, suppression, raid, rear_guard.
**Fails:** assault (path 1.50+), defensive_stand (path ≤0.75), evacuation (path 1.05+).

**Recommendation:** All three fixes. Class C to exclude assault, defensive_stand. Evacuation borderline.

### Layout 07: Scattered Outposts

**Current ratios:** path=1.00, travel=4.00, vantage=skipped, hazard=0.67
**Archetype pools:** counterinsurgency, evacuation, raid, rear_guard, reconquest, siege_breaking, suppression

**Proposed fixes:**
1. **Class B — travel:** This layout has no chokepoints, so front_ids = objective. Enemy has direct edge spawn→objective (1 hop). Player must traverse 4 zones (staging→patrol→hazard→hazard_nw→objective = 4 hops min). Options:
   - *Option A:* Add direct edge `staging_base → objective_cache`. Player = 1 hop. Ratio = 1/1 = 1.0. But this bypasses the entire patrol/hazard traversal that defines the layout's gameplay.
   - *Option B:* Remove direct `spawn_insurgents → objective_cache` edge. Add intermediate zone (e.g., `insurgent_camp` at (0.5, 0.13)) with edges spawn→camp→objective. Enemy = 2 hops. Player still 4. Ratio = 4/2 = 2.0. Still bad.
   - *Option C:* Add a shortcut edge `patrol_south → objective_cache` (skip the hazard traversal). Player = 2 hops. Enemy = 1. Ratio = 2/1 = 2.0. Combine with removing spawn→objective direct edge + adding intermediate: player = 2, enemy = 2. Ratio = 1.0.
   - **Recommended: Option C variant** — add `patrol_south → objective_cache` edge AND add intermediate zone between spawn and objective. This preserves hazard traversal as alternative routes while giving a direct patrol→objective path.
2. **Hazard ratio 0.67:** 5 hazard nodes, ratio reflects distribution. After position adjustments (move some hazards toward player side), ratio could approach 1.0. Class A.

**Post-fix estimated ratios:** path=1.0, travel≈1.0 (with both edge changes), vantage=skipped, hazard≈1.0.

**Passes:** counterinsurgency (all metrics in range), suppression, raid, rear_guard, reconquest, siege.
**Fails with travel still >1.3:** If travel fix is partial, many archetypes fail.

**Recommendation:** This layout is purpose-built for counterinsurgency (scattered interference zones, no chokepoints). Its topology is a poor fit for archetypes that assume conventional front-line combat. **Class C recommended:** tighten non-prototype archetype filters to require chokepoints for siege_breaking, require multiple paths for evacuation, etc. — which would naturally exclude this layout. Keep in counterinsurgency and suppression pools. Attempt Class B travel fix for those two archetypes only.

### Layout 08: Elevated Strongpoint

**Current ratios:** path=1.00, travel=0.50, vantage=2.00, hazard=skipped
**Archetype pools:** multi_front_defense, evacuation, raid, rear_guard, reconquest, siege_breaking, suppression

**Proposed fixes:**
1. **Class A — vantage:** Move `vantage_north_crest` (0.35, 0.36) → (0.35, 0.22) and `vantage_south_crest` (0.65, 0.36) → (0.65, 0.22). Staging is at (0.5, 0.5), spawn at (0.5, 0.05). Moving vantage toward y≈0.22 makes them roughly equidistant: staging distance = sqrt(0.15^2 + 0.28^2) ≈ 0.32, spawn distance = sqrt(0.15^2 + 0.17^2) ≈ 0.23. Still slightly enemy-favored. Alternative: (0.35, 0.28) gives staging dist ≈ 0.26, spawn dist ≈ 0.27 — roughly equal. **Use (0.35, 0.28) and (0.65, 0.28).** Expected ratio: ~1.0.
2. **Class B — travel:** Player has direct edge staging→choke_north (1 hop). Enemy: spawn→transit_north→choke_north (2 hops). Options:
   - Remove direct staging→choke_north edge and route through reinforcement_north_bunker. Player: staging→reinforcement→choke = 2 hops. Enemy stays at 2. Ratio = 1.0.
   - Edge `reinforcement_north_bunker → choke_north_approach` already exists. So staging→reinforcement→choke_north = 2 hops. Just remove the direct staging→choke_north edge.

**Post-fix estimated ratios:** path=1.0, travel≈1.0, vantage≈1.0, hazard=skipped.

**Passes:** multi_front (path 0.85–1.15 ✓), siege, reconquest, suppression, raid, rear_guard.
**Fails:** evacuation (path needs 1.05+).

**Recommendation:** Both fixes. Class C to exclude evacuation if path stays at 1.0.

---

## Per-(Layout, Archetype) Classification Table

Legend: **A** = Class A position fix, **B** = Class B edge/node change, **C** = Class C filter exclusion.
"Pass after A+B" = expected to pass after proposed Class A and B fixes land.

### Prototype archetypes

| Layout | Archetype | Failing Metrics | Fix Class | Pass after A+B? |
|--------|-----------|----------------|-----------|-----------------|
| 01 | assault | path, vantage, hazard | A+B | path≈1.5 → yes (1.50–1.90) |
| 01 | defensive_stand | path, vantage, hazard | C | no — path≥1.0 can't reach ≤0.75 |
| 02 | assault | path, travel, vantage | B+C | no — path=1.0, needs 1.50+ |
| 02 | defensive_stand | path, travel, vantage | B+C | no — path=1.0, needs ≤0.75 |
| 04 | assault | path, travel, hazard | B+C | no — path=1.0, needs 1.50+ |
| 04 | defensive_stand | path, travel, hazard | B+C | no — path=1.0, needs ≤0.75 |
| 05 | assault | path, vantage, hazard | A+B | path≈1.0 → no (needs 1.50+). C. |
| 05 | defensive_stand | path, vantage, hazard | A+B+C | path≈1.0 → no (needs ≤0.75). C. |
| 06 | assault | path, travel, vantage, hazard | A+B+C | path=1.0 → no. C. |
| 06 | defensive_stand | path, travel, vantage, hazard | A+B+C | path=1.0 → no. C. |
| 03 | multi_front_defense | travel, vantage | A+B | yes (path=1.0, travel≈1.0, vantage≈1.0) |
| 04 | multi_front_defense | travel, hazard | A+B | yes (path=1.0, travel≈1.0, hazard≈1.0) |
| 08 | multi_front_defense | travel, vantage | A+B | yes (path=1.0, travel≈1.0, vantage≈1.0) |
| 06 | counterinsurgency | travel, vantage, hazard | A+B | yes (path=1.0, travel≈1.0) |
| 07 | counterinsurgency | travel, hazard | A+B | yes if travel fix lands |

### Non-prototype archetypes — siege_breaking (pool: 8)

| Layout | Failing Metrics | Fix Class | Pass after A+B? |
|--------|----------------|-----------|-----------------|
| 01 | path, vantage, hazard | A+B | path≈1.5 → yes (0.95–1.45) |
| 02 | travel, vantage | A+B | yes (path=1.0, travel≈1.0) |
| 03 | travel, vantage | A+B | yes |
| 04 | travel, hazard | A+B | yes |
| 05 | path, vantage, hazard | A+B | path≈1.0 → yes (0.95–1.45) |
| 06 | vantage, hazard | A | yes (travel=0.67 in 0.65–1.05 ✓) |
| 07 | travel, hazard | B | partial — depends on travel fix |
| 08 | travel, vantage | A+B | yes |

### Non-prototype archetypes — reconquest (pool: 8)

| Layout | Failing Metrics | Fix Class | Pass after A+B? |
|--------|----------------|-----------|-----------------|
| 01 | path, vantage, hazard | A+B | path≈1.0 → yes (0.90–1.30) |
| 02 | travel, vantage | A+B | yes |
| 03 | travel, vantage | A+B | yes |
| 04 | travel, hazard | A+B | yes |
| 05 | path, vantage, hazard | A+B | yes |
| 06 | travel, vantage, hazard | A+B | yes |
| 07 | travel, hazard | B | depends on travel fix |
| 08 | travel, vantage | A+B | yes |

### Non-prototype archetypes — suppression (pool: 8)

| Layout | Failing Metrics | Fix Class | Pass after A+B? |
|--------|----------------|-----------|-----------------|
| 01 | path, vantage, hazard | A+B | path≈1.0 → yes (0.75–1.25) |
| 02 | travel, vantage | A+B | yes |
| 03 | travel, vantage | A+B | yes |
| 04 | travel, hazard | A+B | yes |
| 05 | path, vantage, hazard | A+B | yes |
| 06 | travel, vantage, hazard | A+B | yes |
| 07 | travel, hazard | B | depends on travel fix |
| 08 | travel, vantage | A+B | yes |

### Non-prototype archetypes — evacuation (pool: 8)

| Layout | Failing Metrics | Fix Class | Pass after A+B? |
|--------|----------------|-----------|-----------------|
| 01 | path, travel, vantage, hazard | A+B | path≈1.5 → yes (1.05–1.55) |
| 02 | path, travel, vantage | A+B | path=1.0 → no (needs 1.05+). C borderline. |
| 03 | path, travel, vantage | A+B | path=1.0 → no. C. |
| 04 | path, travel, hazard | A+B | path=1.0 → no. C. |
| 05 | path, travel, vantage, hazard | A+B | path≈1.0 → no. C. |
| 06 | path, vantage, hazard | A+B | path=1.0 → no. C. |
| 07 | path, travel, hazard | B | path=1.0 → no. C. |
| 08 | path, travel, vantage | A+B | path=1.0 → no. C. |

**Note:** Evacuation's path target (1.30, 0.25) requires multiple extraction routes (ratio 1.05–1.55). Only layout_01 (with path≈1.5 after fix) satisfies this. Consider either: (a) widening the path tolerance, (b) adding a second player path to one or two layouts, or (c) accepting a 1-layout pool for evacuation. **Escalation candidate.**

### Non-prototype archetypes — raid (pool: 8)

| Layout | Failing Metrics | Fix Class | Pass after A+B? |
|--------|----------------|-----------|-----------------|
| 01 | path, vantage, hazard | A+B | path≈1.0 → yes (0.70–1.30) |
| 02 | travel, vantage | A+B | yes |
| 03 | travel, vantage | A+B | yes |
| 04 | travel, hazard | A+B | yes |
| 05 | path, vantage, hazard | A+B | yes |
| 06 | travel, vantage, hazard | A+B | yes |
| 07 | travel, hazard | B | depends on travel fix |
| 08 | travel, vantage | A+B | yes |

### Non-prototype archetypes — rear_guard (pool: 8)

| Layout | Failing Metrics | Fix Class | Pass after A+B? |
|--------|----------------|-----------|-----------------|
| 01 | path, vantage, hazard | A+B | path≈1.0 → yes (0.55–1.05) |
| 02 | travel, vantage | A+B | yes |
| 03 | travel, vantage | A+B | yes |
| 04 | travel, hazard | A+B | yes |
| 05 | path, vantage, hazard | A+B | yes |
| 06 | travel, vantage, hazard | A+B | yes |
| 07 | travel, hazard | B | depends on travel fix |
| 08 | travel, vantage | A+B | yes |

---

## Summary of Proposed Class C Filter Changes

Non-prototype archetypes currently use stub filters (staging + spawn + objective only). Tightening these filters both excludes genuinely incompatible pairs and gives each archetype a more meaningful layout pool.

### Recommended filter tightenings:

1. **siege_breaking:** Add `_zone_gte("chokepoint", 1)`. Siege-breaking implies fortified positions to break through. Excludes layout_07 (no chokepoints). Pool: 8 → 7.

2. **evacuation:** Add `_edge_gte("path", 3)` and/or `_zone_gte("flank_route", 1)`. Evacuation needs multiple extraction routes. Even with this, path_balance ratio is the binding constraint — most layouts have path=1.0 which is below evacuation's target. **Escalation needed:** evacuation may have a 1–2 layout pool after fixes, which is viable but low-diversity.

3. **reconquest, suppression, raid, rear_guard:** Keep broad filters (staging + spawn + objective). These archetypes have wide tolerances and symmetric-ish targets. After Class A+B fixes, most layouts will pass. Layout_07 may need Class C exclusion from all except counterinsurgency and suppression.

### Recommended layout exclusions for specific pairs:

| Archetype | Exclude Layout | Reason |
|-----------|---------------|--------|
| defensive_stand | layout_01 | path=3.0 → can't reach ≤0.75 even with fixes |
| assault | layout_02, 04, 05, 06 | path=1.0 → can't reach 1.50+ |
| defensive_stand | layout_02, 04, 05, 06 | path=1.0 → can't reach ≤0.75 |
| evacuation | layout_02, 03, 04, 05, 06, 07, 08 | path=1.0 → can't reach 1.05+ |

**Note on assault and defensive_stand:** These archetypes have directional path requirements that only some topologies can satisfy. After excluding incompatible layouts:
- **assault** pool: layout_01 (path≈1.5 after fix). Pool = 1. **Escalation candidate** — very low diversity.
- **defensive_stand** pool: none of the current layouts produce path < 0.75 after fixes. **Escalation candidate** — either the profile target needs review or a layout must be authored with asymmetric enemy-favored paths.

---

## Escalation Items

Three items require Westley's input before Checkpoint E:

### E1: Defensive Stand path target may be unattainable

The defensive_stand profile targets path_balance (0.60, 0.15), meaning player has 0.45–0.75× the enemy's edge-disjoint paths to objectives. None of the 8 layouts produce this ratio — all have path ≥ 1.0. This is a structural design tension: the layouts were authored with player approaching from staging toward objectives (the layout puts the player's start on one end and the objective on the other), which inherently gives the player more or equal path options compared to the enemy who spawns near/at the objective.

Options: (a) Author a new layout where enemy has more paths to objective than player. (b) Widen defensive_stand's path tolerance. (c) Accept defensive_stand uses best-of-N retry behavior (current behavior). Per CLAUDE.md, widening a prototype tolerance requires approval.

### E2: Assault pool may shrink to 1

After fixes, only layout_01 (with path≈1.5) satisfies assault's path_balance (1.70, 0.20). Layout_01's fixed path ratio of 1.5 is at the edge of the 1.50–1.90 tolerance band. A 1-layout pool for assault means zero layout diversity for that archetype.

Options: (a) Accept 1-layout pool. (b) Add enemy edges to a second layout to create path asymmetry. (c) Widen assault path tolerance slightly.

### E3: Evacuation pool may shrink to 1

Similar to E2: evacuation needs path > 1.05. Only layout_01 achieves this after fixes. Options are the same.

---

## Change Census

| Class | Count | Description |
|-------|-------|-------------|
| A (position) | 14 zone moves | Vantage and hazard repositioning across 6 layouts |
| B (edge/node) | ~10 edge changes | Travel time equalization (7 layouts) + path balance (2 layouts) |
| B (node add) | 1–2 zones | Layout_03 intermediate transit; layout_07 intermediate spawn zone |
| C (filter) | ~8 pair exclusions | Assault, defensive_stand, evacuation filter tightening |

**Estimated post-fix pass rate:** ~45–50 of 63 pairs (71–79%), up from 0/63. The remaining ~13–18 failures are archetype-specific path_balance mismatches requiring either new layouts (out of scope) or profile review (escalation items above).
