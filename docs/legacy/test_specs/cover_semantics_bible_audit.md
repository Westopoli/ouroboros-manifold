# Cover Semantics — Bible Audit

Date: 2026-05-18

## Headline finding

The Bible explicitly specifies that `cover_density` is a **damage-reduction mechanic** that "reduces incoming damage as a percentage" (docs/bible_history/bible_2_00_combat.md:440). Cover is semantically distinct from obstacles: obstacles block movement and line of sight, while cover provides protection without blocking paths. The Bible contains no language stating that cover blocks line-of-sight; rather, it emphasizes cover as a continuous gradient field that makes positions "defensible" and "fortified" by reducing damage. Terrain obstacles (mapped to `obstacle_density`, not `cover_density`) are the exclusive LOS-blocking mechanism.

## Quotes (chronological in their files)

### docs/bible_history/bible_2_00_world.md (Terrain Model)

- `docs/bible_history/bible_2_00_world.md:142-144` — "`obstacle_density` — blocks unit movement. High density creates walls, barriers, and terrain that must be navigated around. **Distinct from cover** — obstacles impede movement, cover provides protection without necessarily blocking paths. ... `cover_density` — reduces incoming damage for units in that area. **Distinct from obstacles** — cover protects without necessarily blocking movement. Enables terrain like trenches, low walls, and debris fields that are easy to traverse but provide protection." — semantic: **damage-reduction only; explicitly NOT LOS-blocking**

### docs/bible_history/bible_2_00_combat.md (Damage & Targeting)

- `docs/bible_history/bible_2_00_combat.md:421` — "`damage_per_attack = base_damage × category_multiplier × (1.0 - cover_density_at_position)`" — semantic: **damage-reduction multiplier**

- `docs/bible_history/bible_2_00_combat.md:440` — "`cover_density` gradient at target unit's position reduces incoming damage as a percentage. Cover_density 0.4 → unit takes 60% damage. Era-agnostic." — semantic: **damage-reduction only**

- `docs/bible_history/bible_2_00_combat.md:269` — "Environmental features drift through the combat zone — terrain that provided cover shifts, opening or closing sightlines" — semantic: **behavioral (dynamic cover changes battlefield visibility)**

- `docs/bible_history/bible_2_00_combat.md:529` — "Terrain obstacles still block line of sight — units cannot fire through navmesh obstacles." — semantic: **LOS-blocking is tied to obstacles, NOT cover**

- `docs/bible_history/bible_2_00_combat.md:578` — "ambush — hold at a hidden position (ideally in a sensor interference zone or behind cover)" — semantic: **behavioral (cover creates defensible positions for tactical hiding)**

### docs/bible_history/bible_2_00_missions.md (Mission Design Directives)

- `docs/bible_history/bible_2_00_missions.md:74` (defensive_stand) — "Defensible terrain. Chokepoints between enemy approach vectors and the objective. Prepared positions with cover." — semantic: **behavioral (cover signifies defensible/prepared terrain, not explicit LOS or damage mechanic)**

- `docs/bible_history/bible_2_00_missions.md:137` (assault) — "Enemy territory. The defender has prepared positions, fortified chokepoints, established infrastructure." — semantic: **behavioral (infrastructure/fortifications imply cover)**

- `docs/bible_history/bible_2_00_missions.md:200` (interception) — "Open terrain. No prepared positions for either side… Terrain features provide tactical options (cover, elevation, sensor interference) but neither side has fortifications." — semantic: **behavioral (cover listed alongside tactical options, not as mechanical LOS blocker)**

- `docs/bible_history/bible_2_00_missions.md:263` (counterinsurgency) — "Insurgent forces are initially hidden — scattered across the map in sensor interference zones, **behind cover**, in defensible pockets… Destroying infrastructure (objectives, cover positions) is mechanically possible but counterproductive." — semantic: **behavioral + damage (cover makes forces harder to root out; destroying cover positions is a mechanical choice)**

## Cross-cutting interpretation

The Bible corpus treats cover as a **purely damage-reduction gradient field**. Cover and obstacles are explicitly separated by function: obstacles block movement and line of sight; cover reduces damage without blocking movement. There is no Bible language anywhere stating or implying that cover blocks line-of-sight. The only LOS-blocking mechanism named in the Bible is `obstacle_density` (mapped to navmesh obstacles, which already implement LOS-blocking in the engine via `has_combat_los` checks in damage.py:36-38). Cover's role is to make defensive positions feel "fortified" and "prepared" by reducing incoming damage, creating a mechanical incentive for positioning and a tactical reason to defend specific map zones. Behaviorally, cover enables ambush (players hide to avoid detection — handled by sensor/fog, not cover) and makes fortified positions defensible (handled by damage multiplier).

## Conflict with live code?

**Current implementation (simulation/damage.py:131-137, 170-177):**
```python
cover = 0.0
if tactical_map is not None:
    cover = tactical_map.cover_density(store.data[target, FIELD_X], store.data[target, FIELD_Y])
dmg = base_dmg * mult * (1.0 - cover)
```

**Bible says:** Cover is damage-reduction only. Damage formula `(1.0 - cover_density)` is explicitly specified in docs/bible_history/bible_2_00_combat.md:421 and reinforced in docs/bible_history/bible_2_00_combat.md:440.

**Conflict:** **NO** — live code is in perfect alignment with Bible spec. The damage multiplier `(1.0 - cover)` is the Bible's canonical damage formula. No deviation, no gap.

## Recommendation for H4 decision

The live code is Bible-aligned and requires no rework. Cover is working as specified: a damage-reduction gradient field, not an LOS blocker. The existing implementation via `tactical_map.cover_density(x, y)` sampled at target position, multiplied into the damage formula, is correct.

**However,** a separate issue exists on the tactical map side: map generation today places cover gradients only at `staging` zones and `flank_route` zones (per a3_map_cover_audit.md:19-22), while the Bible directs cover placement at `chokepoint` and `objective` zones in defensive archetypes (docs/bible_history/bible_2_00_missions.md:74, 137, 242, 263). This is a **map-generation gap**, not a damage-code gap. The `place_gradients` function in simulation/gradient_placer.py needs to emit `cover_density` sources at additional zone types to align with Bible's tactical intent. The damage mechanics themselves are correct and require zero changes.

**Westley's stated design intent** ("cover stops line-of-sight, gives tactical depth via information; NOT a damage-reduction mechanic") is **contradicted by the current Bible spec**. The current published Bible explicitly makes cover a damage-reduction mechanic (docs/bible_history/bible_2_00_combat.md:421, 440) with no LOS-blocking language. This is not a code conflict; it is a **spec conflict that must be resolved by Westley**:
- Option 1: Update the Bible to remove damage-reduction language and reframe cover as LOS-only + information-tactical depth. Then rebuild the damage formula to use LOS checks instead of cover multipliers.
- Option 2: Accept the current Bible spec (damage-reduction cover) and update the cover-LOS design intent to match.
- Option 3: Implement both (cover reduces damage AND blocks LOS via navmesh integration), aligning spec and code.

The flag for H4 is the spec gap, not the code correctness.
