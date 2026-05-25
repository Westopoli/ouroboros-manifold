# Cover-Asteroid Movement Spec — Wave 2.6M

**Status:** Locked 2026-05-23. Decision-source-of-truth for Wave 2.6M leaf agents. Sibling spec to `cover_asteroid_los_spec.md` (Wave 2.5R+2.6). LOS spec is fire/vision gate; this spec is movement gate + AI targeting LOS gate.

## Context

Wave 2.5R+2.6 landed per-asteroid LOS (vision/fire blocked by asteroid cylinders). Sub-agent audit (L6, 2026-05-23) surfaced two follow-up gaps:

1. **Asteroids are visibility-only.** Units physically walk through asteroid clusters — ships pass through matter. Bible terrain commitments (combat:196 — "go over, go around, exploit blocked layers"; missions:74,137 — "chokepoints between approach vectors", "flanking route through difficult terrain") presume path planner respects terrain.
2. **AI targeting bypasses LOS.** `update_targeting` (damage.py:248-271) spatial-hash query filters by distance + layer + faction only — no visibility gate. AI engages unseen targets if close enough; attack timer burns on phantoms; chronicle text degrades.

Both gaps undermine bible heuristics already locked:
- **Principle 4 (Positional Thinking Over Command Shortcuts):** terrain shape must be readable from player commands.
- **Litmus #1 (Commander or god):** unit babysitting unit-rock collision = god-mode micromanagement.
- **Pacing heuristic:** stuck units = static = broken.
- **Chronicle material:** "ship hit rock" ≠ narrative; "AI engages phantom behind cluster" ≠ narrative.

Wave 2.6M closes both. Sibling-scope, parallel-safe with each other.

## Design contract (LOCKED 2026-05-23)

### A. Movement-block threshold

Asteroid blocks unit movement iff `asteroid.radius_xy >= ASTEROID_MOVEMENT_BLOCK_RADIUS`. Default `R_BLOCK = 8.0` — medium-floor (medium scale_class spans 8-20wu; huge spans 20-80wu). Numerical, not class-based, so future scale-range tuning doesn't silently shift block behavior.

- `tiny` (1-3wu radius) → pass-through (debris).
- `small` (3-8wu radius) → pass-through (small rocks).
- `medium` (8-20wu radius) → block (chunk).
- `huge` (20-80wu radius) → block (landmark).

### B. Navmesh rasterization (NOT slide collision)

Pathfinder must know about blockers up-front so:
- Player path preview during pause shows real path geometry.
- AI plans routes around clusters, not through them.
- Chokepoint map character (gaps between asteroids) functions as designed.

Rasterization at navmesh build time (`Navmesh.from_tactical_map`):
1. Existing gradient-obstacle pass runs first (`obstacle_density >= threshold` → unwalkable).
2. New asteroid pass: for each asteroid in `tactical_map.asteroid_field.asteroids` with `radius_xy >= R_BLOCK`, mark every navmesh cell whose center lies within `(radius_xy + cell_size/2)` of `(asteroid.x, asteroid.y)` as unwalkable.
3. Conservative rasterization: cell unwalkable if cell-center within (radius + half-cell). Trades a small false-block ring (~half a cell) for guarantee that no walkable cell intersects asteroid interior.

NO runtime slide collision in `_resolve_collisions`. NO navmesh edits at tick time. Asteroids are static at map load (per LOS spec), navmesh is static after build.

### C. AI targeting LOS gate

`update_targeting` in `damage.py:248-271` (attack-move pursuit) queries `tmap.spatial_hash.query(...)` for candidate targets within sensor radius. Filter must add visibility check: candidate `other` is admissible iff `other in visibility_map.get(uid, set())`. Visibility map already computed by `compute_visibility(store, tactical_map)` upstream; pass it through `update_targeting`'s call site or recompute at function entry.

- Gate applies to AI sensor-pursuit only (auto_engage_target acquisition).
- Player-issued attack commands NOT gated at command time — unit walks to LOS, fires when target enters visibility set. (Standard SC2/RTS pattern; player intent respected, execution gated by physics.)
- Mid-engagement target loss already handled by `damage.py` visibility gate (Wave 2.5R): zero damage when target hidden, regardless of `auto_engage_target` state. No change to mid-engagement behavior.

### D. Determinism + perf

- Rasterization deterministic (asteroid set fixed at map load; iteration order = `asteroid_field.asteroids` index order).
- One-time cost in `from_tactical_map`; per-tick cost zero.
- For large maps (24000²), navmesh build already ~5s per movement.py:237 comment. Asteroid pass adds bounded extra work (~O(num_blocking_asteroids × cells_per_asteroid)). Settled-Reach map sizes (1000-2000wu, ~25-50 huge asteroids per cluster, ~5-10 clusters) = trivial. Document if extrapolation to large maps becomes hot.

## Files in scope

### L10 — movement-block (navmesh rasterization)
- `simulation/movement.py` — `Navmesh.from_tactical_map`: add post-gradient pass for asteroid rasterization. Owned by L10.
- `simulation/config.py` — add `ASTEROID_MOVEMENT_BLOCK_RADIUS = 8.0`. Owned by L10.

### L11 — targeting LOS gate
- `simulation/damage.py` — `update_targeting`: filter sensor-pursuit candidates by `visibility_map`. Owned by L11.

### Tests
- `simulation/test_asteroid_movement.py` (L10) — navmesh blocks huge/medium asteroid cells; tiny/small asteroid cells walkable; pathfinder routes around huge cluster; deterministic across rebuilds.
- `simulation/test_asteroid_ai_los_gate.py` (L11) — AI does NOT acquire hidden target via sensor-pursuit; AI DOES acquire visible target normally; mid-engagement target stepping into cover triggers re-acquisition (auto_engage_target cleared next tick).

### Umbrella
- `simulation/test_asteroid_umbrella.py` (parent-owned) — append:
  - `test_umbrella_h_movement_block_huge` — huge asteroid → cell unwalkable.
  - `test_umbrella_h_movement_passthrough_tiny` — tiny asteroid → cell walkable.
  - `test_umbrella_i_ai_targeting_los_gate` — AI sensor-pursuit honors visibility.

## Type contract

### Locked symbols (audit registry)

```python
ASTEROID_MOVEMENT_BLOCK_RADIUS = 8.0

class Navmesh: ...
def from_tactical_map(cls, tmap): ...

def update_targeting(store, tmap, dt): ...
def compute_visibility(store, tactical_map): ...
```

### Canonical shapes (human reference)

No new types. `Navmesh.grid[r][c]` boolean unchanged. `update_targeting` signature unchanged (visibility recomputed at entry OR passed in — sub-agent picks; both acceptable).

## Out of scope

- Slide/tangent runtime collision — rejected per Wave 2.6M design audit.
- Re-rasterization during tick — asteroids static.
- Asteroid destruction — non-destructible Phase 1 per LOS spec.
- Per-unit-size collision tuning (capital ship vs strike craft vs sensor drone differing block thresholds) — Phase 1 single global `R_BLOCK`.
- Full BT rewrite for AI cover behavior — out per LOS spec line 54.
- Player-command-time LOS gate ("can't issue attack on hidden target") — rejected; player intent respected.

## Leaf decomposition

| Leaf | Wave | Scope | Parallel? |
|---|---|---|---|
| L10 | 2.6M | navmesh asteroid rasterization (movement.py + config.py) + tests | parallel w/ L11 |
| L11 | 2.6M | update_targeting visibility filter (damage.py) + tests | parallel w/ L10 |

L10 + L11 own disjoint files. Run in parallel after this spec lands + /swarm-review passes.

After L10+L11 merge: re-dispatch L7 apex integration (defender-behind-cluster scenario now valid — attackers route around, AI doesn't engage hidden).

## Acceptance

All seven umbrella tests cited above + per-leaf brief acceptance tests GREEN. Full umbrella (now 17 tests post-augmentation) GREEN. Apex integration (L7) GREEN.

## Gotchas

1. **Combat balance reshuffle (carry over from LOS spec).** A2-J archetype tests may shift further as units route around asteroids (longer travel times). Re-baseline per CLAUDE.md invariant rules; no widening.
2. **Pathfinder cache invalidation.** `PathCache` keys on (start_cell, goal_cell). Navmesh asteroid-block changes the path between same cells, but cache built post-rasterization — first-tick paths reflect blocks. No invalidation needed since asteroids are static.
3. **AI sensor-pursuit visibility-map recompute cost.** `compute_visibility` is already called by `damage.py:resolve_damage`. L11 must reuse that result (pass through) OR document the per-tick cost of duplicate compute. Preferred: pass-through.
4. **`update_targeting` signature change risk.** If L11 adds `visibility_map` parameter, every call site must update. Audit call sites first; if multiple, escalate before changing signature — fallback = recompute inside function.
