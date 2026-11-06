# Cover-Asteroid LOS Spec — Wave 2.5R + 2.6

**Status:** Locked 2026-05-23. Decision-source-of-truth for Wave 2.5R+2.6 leaf agents. Supersedes `docs/legacy/test_specs/cover_los_rework_spec.md` (polygon-binary symmetric-blind model — never committed to main).

## Context

Wave 2.5 polygon-binary symmetric-blind model implemented + tested green in working tree but never merged. Visual review (2026-05-22) surfaced design fork: Westley specified per-asteroid realistic LOS (each asteroid is a real geometric LOS-blocker; observer sees target iff no asteroid between them), not polygon abstraction. Polygon model is "wrong-feeling at edges" (target 1m inside polygon edge, observer 1m outside → polygon says hidden, real geometry says visible).

Westley locked new design 2026-05-23. Wave 2.5 polygon impl scrapped. Wave 2.5R + 2.6 = single ship block (per-asteroid sim + Godot visual render). HOLD on Wave 2.5 commit batch.

## Design contract (LOCKED 2026-05-23)

### Per-asteroid LOS model
- Cover = a cluster of discrete asteroids (rocks). Each asteroid has position, radius_xy (footprint), height (vertical extent), scale_class (asset key).
- Visibility = real 3D ray-cylinder geometry. Ray from observer center to target center. If any asteroid cylinder intersects ray AND ray passes through asteroid's vertical extent → blocked. Else visible.
- No polygon "membership" rules. No symmetric-blind abstraction. Pure geometry.

### Continuous size → layer block
- Asteroid blocks LOS at layer i iff `asteroid.height ≥ LAYER_Z_FLOORS[i]`.
- Tiny asteroid (height < 30) blocks layer 0 only.
- Tall asteroid (height ≥ 100) blocks layers 0+1+2.
- Continuous: no enum size→layer map; the height value alone drives layer block.

### Asteroid placement
- Each cover-emitting spine node (chokepoint, staging, objective, hazard_zone_anchor, flank_route) emits ONE `AsteroidField` (cluster).
- Cluster center = spine node position. Cluster radius = pre-existing config radius per node type (`GRADIENT_CHOKEPOINT_COVER_RADIUS`, etc.).
- Asteroid count ~6× pre-existing `BASE_DENSITY := 0.00015` (player needs dense cover signal).
- Distribution: uniform within cluster bounds (rejection sampling within radius).
- Scale class distribution per cluster:
  - 60% tiny (1-3wu radius)
  - 25% small (3-8wu)
  - 10% medium (8-20wu)
  - 5% huge (20-80wu — landmark-scale, possibly bigger than half cluster radius)
- Height formula (Phase 1, D2=A): `height = radius_xy * uniform(0.5, 2.0)` — Pixar-bbox feel without AABB pipeline work. Post-launch refinement (D2=C): bake script reads GLB AABBs into JSON; sim reads JSON at startup.

### Era asset bundle wiring
- `EraThemeResolver` extended with per-era cover asset keys: `cover_tiny`, `cover_small`, `cover_medium`, `cover_huge`.
- Settled Reach era: all 4 keys point to existing asteroid GLBs (`asteroid_small.glb` for tiny+small, `asteroid_medium.glb` for medium, `asteroid_large.glb` for huge — scale-variance via per-instance Transform3D).
- Other eras: keys left empty (TODO post-launch).

### Static at map load
- Asteroids non-destructible Phase 1. Belong in map manifest, sent ONCE at mission load via `snapshot_serializer.py`. NOT in tick delta.
- `docs/architecture.md` updated noting cover_asteroids field added to manifest shape.

### Spatial hash for raycast perf
- Cell size 100wu (D4). Asteroids inserted at construction. Visibility raycast queries cells along ray bounding box.

### Combat fire = visibility gate (unchanged from Wave 2.5)
- No damage if target not in attacker's `compute_visibility()` set. Visibility set computed via per-asteroid raycast. Defender in cover firing OUT at unseen attacker stays hidden (defender visibility computed separately).

### AI peek (carry over from Wave 2.5)
- Audit AI targeting in `simulation/tactical_engine.py` + behavior scripts.
- If AI clumps in cover (never engages because nothing visible), add minimal "advance to fire" nudge.
- Full behavior-tree rewrite OUT OF SCOPE.

## Files in scope

### Simulation
- `simulation/tactical_map.py` — replace `CoverPolygon` class with `Asteroid` + `AsteroidField` classes. Add `tactical_map.asteroid_field` (single field aggregating all asteroids across clusters). Add `asteroid_blocks_los(ox, oy, oz, tx, ty, tz) -> bool` method using spatial-hash query + 3D ray-cylinder intersect. Retire `is_in_cover` + `cover_polygon_containing` polygon APIs.
- `simulation/gradient_placer.py` — replace `place_cover_polygons` with `place_asteroid_fields(inst) -> AsteroidField`. Cluster generation per node type per F3/D5/D6.
- `simulation/fog_of_war.py` — replace polygon symmetric-blind pass with per-asteroid raycast. Calls `tactical_map.asteroid_blocks_los(...)`. Uses observer/target z derived from layer (layer i → z = midpoint of `[LAYER_Z_FLOORS[i], LAYER_Z_CEILINGS[i]]`).
- `simulation/damage.py` — visibility-gate already in place from Wave 2.5 work; no change expected. Regression test verifies still correct under new visibility model.
- `simulation/tactical_engine.py` — AI audit (read-only) + minimal cover-peek fix if needed.
- `simulation/config.py` — new constants:
  - `ASTEROID_SPATIAL_HASH_CELL = 100.0`
  - `LAYER_Z_FLOORS = [0.0, 30.0, 100.0]`
  - `LAYER_Z_CEILINGS = [30.0, 100.0, 300.0]`
  - `ASTEROID_BASE_DENSITY = 0.00090`  # ~6× existing
  - `ASTEROID_SCALE_DISTRIBUTION = {"tiny": 0.60, "small": 0.25, "medium": 0.10, "huge": 0.05}`
  - `ASTEROID_SCALE_RANGES = {"tiny": (1.0, 3.0), "small": (3.0, 8.0), "medium": (8.0, 20.0), "huge": (20.0, 80.0)}`
  - `ASTEROID_HEIGHT_RATIO_RANGE = (0.5, 2.0)`
- `simulation/snapshot_serializer.py` (or map manifest writer) — emit `cover_asteroids` field at map load. Shape: `list[{asteroid_id, cluster_id, x, y, radius_xy, height, scale_class}]`.

### Godot
- `scenes/tactical/terrain_renderer.gd` — new `_scatter_cover_asteroids(asteroids: Array, map_seed: int)`. One MultiMeshInstance3D per scale_class. Transform3D per asteroid (position + uniform scale based on radius_xy). Drop stale comment at line 219.
- `autoload/era_theme_resolver.gd` (or equivalent) — add `cover_tiny/small/medium/huge` asset keys per era. Settled Reach populated; other eras TODO.

### Bible
- `docs/bible_history/bible_2_00_world.md:144` — rewrite `cover_density` definition AGAIN: cover = cluster of asteroid LOS-blockers; per-asteroid 3D LOS; continuous size → layer block; non-destructible Phase 1.
- `docs/bible_history/bible_2_00_combat.md:439-441` — replace "Cover & Vision" section with per-asteroid LOS language; remove "symmetric blind" / "same polygon visible" phrasing.
- `docs/bible_history/bible_2_00_combat.md:529` — keep cover-as-LOS-blocker mention; phrase as "asteroid cluster" rather than "polygon."

### Tests
- New: `simulation/test_asteroid.py` — `Asteroid` + `AsteroidField` construction, spatial hash insert/query, 3D ray-cylinder intersect math (axis-aligned + diagonal rays, height in/out of range).
- New: `simulation/test_asteroid_placer.py` — `place_asteroid_fields` distribution per node type, scale class proportions, density math.
- New: `simulation/test_asteroid_visibility.py` — fog_of_war per-asteroid LOS: tiny asteroid blocks layer 0 only; tall asteroid blocks all layers; ray "over" short asteroid (different layers) visible; ray "around" asteroid visible.
- New: `simulation/test_asteroid_damage_gate.py` — damage gates correctly under per-asteroid visibility.
- New: `simulation/test_asteroid_ai_peek.py` — AI audit assertion: no clumping.
- New: `simulation/test_asteroid_integration.py` — apex scenario: 2 attackers + defender behind asteroid cluster; defender hidden; defender moves out → damage resumes.
- New: `simulation/test_asteroid_manifest.py` — snapshot_serializer emits `cover_asteroids` field, correct shape.
- New: `tests/test_cover_render.gd` (Godot) — terrain_renderer scatters asteroids on test map manifest. Headless if possible.
- Updated: `simulation/test_cover_umbrella.py` — parent-owned. Adjust assertions: rename tests, swap polygon API checks for asteroid API checks, retain D2 (no `(1.0 - cover)` regex) + E (bible language) tests.

## Type contract

### Locked symbols (audit registry — top-level declarations for the /swarm-review symbol scanner)

```python
class Asteroid: ...
class AsteroidField: ...
class TacticalMap: ...

ASTEROID_SPATIAL_HASH_CELL = 100.0
LAYER_Z_FLOORS = [0.0, 30.0, 100.0]
LAYER_Z_CEILINGS = [30.0, 100.0, 300.0]
ASTEROID_BASE_DENSITY = 0.00090
ASTEROID_SCALE_DISTRIBUTION = {}
ASTEROID_SCALE_RANGES = {}
ASTEROID_HEIGHT_RATIO_RANGE = (0.5, 2.0)

def asteroid_blocks_los(ox, oy, oz, tx, ty, tz): ...
def place_asteroid_fields(inst): ...
def compute_visibility(store, tactical_map): ...
def serialize_cover_asteroids(tactical_map): ...
def build_cover_asteroid_apex_scenario(): ...

# Wave 2.6M extensions (movement-block + AI targeting LOS gate)
ASTEROID_MOVEMENT_BLOCK_RADIUS = 8.0

class Navmesh: ...

def update_targeting(store, tmap, dt): ...
```

### Canonical shapes (human reference)

```python
# simulation/tactical_map.py

class Asteroid:
    __slots__ = ("asteroid_id", "cluster_id", "x", "y", "radius_xy", "height", "scale_class")

    def __init__(self, asteroid_id, cluster_id, x, y, radius_xy, height, scale_class):
        self.asteroid_id = asteroid_id
        self.cluster_id = cluster_id
        self.x = x
        self.y = y
        self.radius_xy = radius_xy
        self.height = height
        self.scale_class = scale_class  # "tiny" | "small" | "medium" | "huge"

class AsteroidField:
    __slots__ = ("asteroids", "spatial_hash")

    def __init__(self, asteroids: list[Asteroid]):
        self.asteroids = asteroids
        self.spatial_hash = SpatialHash(ASTEROID_SPATIAL_HASH_CELL)
        for ast in asteroids:
            self.spatial_hash.insert(ast.asteroid_id, ast.x, ast.y)

class TacticalMap:
    asteroid_field: AsteroidField

    def asteroid_blocks_los(self, ox, oy, oz, tx, ty, tz) -> bool:
        """True if any asteroid cylinder intersects ray (observer → target) within asteroid's vertical extent."""
        ...
```

```python
# simulation/fog_of_war.py (compute_visibility revision)

# For each (observer O, target T) pair passing distance + layer + pulse checks:
#   - oz = layer_z_midpoint(O.layer)
#   - tz = layer_z_midpoint(T.layer)
#   - if tactical_map.asteroid_blocks_los(O.x, O.y, oz, T.x, T.y, tz): skip (blocked)
#   - else: add T to visible set
```

```python
# simulation/damage.py (visibility gate, carried over from Wave 2.5)

# if target not in compute_visibility()[attacker_uid]: skip (no damage)
```

## Algorithms

### 3D ray-cylinder intersection
For ray from `(ox, oy, oz)` to `(tx, ty, tz)` vs cylinder at `(ax, ay)` with radius `r` and vertical extent `[0, h]`:

1. **2D projection check:** Does the 2D ray (ox,oy)→(tx,ty) pass within distance `r` of point (ax, ay)?
   - Parametric line: `P(s) = O + s*(T-O)`, s ∈ [0,1].
   - Closest point to (ax, ay): `s_close = clamp(dot((A-O), (T-O)) / |T-O|², 0, 1)`.
   - If `|P(s_close) - A| > r` → 2D miss → return False (not blocked).
2. **Z-range check at intersection segment:** Compute `s_enter, s_exit` — parametric range where 2D ray is within `r` of (ax, ay). (Solve quadratic for ray-circle intersection.)
3. **Vertical:** Compute `z_enter = oz + s_enter*(tz-oz)`, `z_exit = oz + s_exit*(tz-oz)`. If `min(z_enter, z_exit) > h` → ray passes over top of cylinder → return False. Else → blocked → return True.

### Spatial hash query for raycast
- Compute 2D bounding box of ray `[(ox,oy), (tx,ty)]` expanded by max possible asteroid radius (80wu per D6).
- Query spatial hash cells overlapping bbox → candidate asteroid IDs.
- Run ray-cylinder intersect on each candidate. First True → blocked, short-circuit return.

### Layer Z midpoint
```python
def layer_z_midpoint(layer: int) -> float:
    return (LAYER_Z_FLOORS[layer] + LAYER_Z_CEILINGS[layer]) / 2.0
```

### Place asteroid fields (gradient_placer)
For each cover-emitting spine node:
1. Compute cluster center = node position; radius = config radius constant for node type.
2. Compute target asteroid count = `π * radius² * ASTEROID_BASE_DENSITY * intensity`.
3. For each asteroid:
   - Sample scale_class per `ASTEROID_SCALE_DISTRIBUTION`.
   - Sample `radius_xy ~ uniform(*ASTEROID_SCALE_RANGES[scale_class])`.
   - Sample `height = radius_xy * uniform(*ASTEROID_HEIGHT_RATIO_RANGE)`.
   - Sample position: rejection-sample uniform in disk of cluster radius around center.
   - Assign incrementing `asteroid_id`, cluster's `cluster_id`.
4. Return `AsteroidField([all_asteroids])`.

Deterministic seed: `cluster_id * 1009 + map_seed`.

### Snapshot serialization
Emit at map manifest write (NOT per-tick):
```python
"cover_asteroids": [
    {"id": a.asteroid_id, "cluster": a.cluster_id, "x": a.x, "y": a.y,
     "r": a.radius_xy, "h": a.height, "class": a.scale_class}
    for a in tactical_map.asteroid_field.asteroids
]
```

## Test expectations

### L2 (Asteroid + AsteroidField data structure + raycast math)
- `Asteroid` construction with all 7 fields; round-trip.
- `AsteroidField` spatial hash populated on construction; query returns asteroids in 100wu bucket.
- 3D ray-cylinder math: axis-aligned ray hits cylinder dead-center; misses by 1wu outside radius; ray passes over tall enough → blocked; ray passes over too-short asteroid (height 20, ray z always > 50) → NOT blocked; ray entirely within cylinder vertical range → blocked.

### L3 (gradient_placer asteroid clusters)
- Single chokepoint node → cluster generated; asteroid count matches density formula within ±10%; scale_class distribution within ±5% of `ASTEROID_SCALE_DISTRIBUTION`; all positions within cluster radius.
- Five-node-type test: chokepoint, staging, objective, hazard_zone_anchor, flank_route each produce one cluster with own count/radius.
- Vantage-only layout → empty AsteroidField.
- Deterministic: same seed → same asteroid list.

### L4 (fog_of_war per-asteroid LOS)
- Observer (500,500, layer 0), target (50,50, layer 0), no asteroids → visible.
- Same setup, single huge asteroid (height 200) between → blocked.
- Same, tiny asteroid (height 20) between, observer + target both at layer 1 (z ~65) → NOT blocked (ray passes over tiny).
- Tall asteroid (height 200) at midpoint, observer + target at layer 2 (z ~200) → ray clips top — verify behavior per height >= LAYER_Z_FLOORS rule (height 200 ≥ floor[2]=100 → blocks layer 2 → blocked).
- Ray skirting asteroid edge (just outside radius_xy) → visible.

### L5 (damage gate regression)
- Same scenarios as L4 but checking damage applied: blocked → 0 damage, visible → full damage. Confirms gate intact under new visibility computation.
- Confirm no `(1.0 - cover)` term remains in `damage.py`.

### L6 (AI peek audit)
- Dispatch scenario: defender Warden hidden behind tall asteroid cluster; attacker Raider outside. AI must NOT clump indefinitely; defender's allies (or defender itself if move-to-fire fix added) must engage within N ticks.

### L7 (apex integration)
- 2 attackers + 1 defender behind asteroid cluster (cluster center at (500,500), radius 80, ~25 asteroids).
- Verify: defender not in attacker visibility set; attacker fires at defender → 0 damage; defender moves to (900,500) clear ground → attackers see + damage applies; defender fires from cover at attackers (one-sided fire) → asymmetry preserved.

### L8 (snapshot manifest)
- Mission load → manifest contains `cover_asteroids` array with per-asteroid fields.
- Shape stable: `id, cluster, x, y, r, h, class`.
- Round-trip: sim writes → JSON load → field counts match.
- `docs/architecture.md` updated noting field added.

### L9 (Godot render)
- Test scene loads map with one known cluster → MultiMeshInstance3D for each scale_class populated with correct instance count.
- Per-asteroid Transform3D position matches manifest x/y; uniform scale derived from radius_xy.
- EraThemeResolver returns correct GLB scene per scale_class for "settled_reach" era.
- Stale comment at terrain_renderer.gd:219 removed.

## Verification

- L1–L9 all green per their internal assertions.
- Umbrella test (parent-owned) flips A/B/C/D/F skips to per-asteroid assertions; 13/13 green.
- `simulation/test_cover_*.py` Wave-2.5 polygon files DELETED in cleanup phase (parent-owned).
- Bible reads coherent: cover = asteroid LOS-blocker; no polygon language; no damage-mult language.
- Westley plays one mission and confirms asteroid cover feels right (visual density, LOS feel, layered blocking).

## Gotchas

1. **Wave 2.5 polygon code overlay.** Working tree has Wave 2.5 polygon impl. Wave 2.5R replaces same files. Parent must cleanly stage Wave 2.5R changes (Wave 2.5 working-tree edits get OVERWRITTEN, not committed).
2. **Test deletion.** Wave 2.5 test files (`test_cover_polygon.py`, `test_cover_visibility.py`, `test_cover_damage_gate.py`, `test_cover_ai_peek.py`, `test_cover_integration.py`, `cover_integration_fixture.py`, `test_cover_polygon_placement.py`) get deleted in parent cleanup. Wave 2.5R tests have new names (`test_asteroid_*.py`). Umbrella adjusted in parent task.
3. **Manifest shape stability.** `docs/architecture.md` shape rule per CLAUDE.md — update doc BEFORE L8 impl.
4. **Raycast perf at scale.** ~50-150 asteroids per cluster × ~5 clusters = 250-750 asteroids per map. With 100wu spatial hash + ~30 units querying ~5 enemies each per tick = manageable. Profile if tick time degrades; cell size + max-radius bbox knobs available.
5. **Test thresholds re per-asteroid stochasticity.** Cluster asteroid counts use random sampling; assert within ±10-15% tolerance, not exact.
6. **Same-faction visibility convention (L4 → carry over from Wave 2.5):** same-faction units NOT tracked in `compute_visibility()` set per `fog_of_war.py:73` pre-existing skip. Asteroid LOS does not change this — same-faction continues to short-circuit before raycast. Player still sees own units via separate render layer.

## Open questions (none — all forks resolved)

- ✅ Visibility algorithm: 3D ray-cylinder per-asteroid (F1=B / D1=A)
- ✅ Size → layer: continuous, height vs LAYER_Z_FLOORS (F2)
- ✅ Density + variance: 6× current; 60/25/10/5 tiny/small/medium/huge (F3)
- ✅ Plumbing: map manifest static at load (F4=A / Q4=A)
- ✅ Era assets: bundle path via EraThemeResolver; Settled Reach asteroids only (F5 / Q1=B)
- ✅ Height formula: `radius_xy * uniform(0.5, 2.0)` Phase 1; GLB AABB bake post-launch (D2=A → C)
- ✅ Layer Z floors: [0, 30, 100] + ceilings [30, 100, 300]; Godot tune later (D3)
- ✅ Spatial hash cell: 100wu (D4)
- ✅ Cluster distribution: uniform (D5)
- ✅ Scale ranges: tiny 1-3 / small 3-8 / medium 8-20 / huge 20-80 (D6)
