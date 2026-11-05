# Cover-LOS Rework Spec — Wave 2.5 (SUPERSEDED)

**Status:** SUPERSEDED 2026-05-23 by `docs/legacy/test_specs/cover_asteroid_los_spec.md` (Wave 2.5R + 2.6).

Polygon-binary symmetric-blind model documented here was implemented in Wave 2.5 (briefs L1-L7 in `.swarm/briefs/wave_2_5_cover_los/`) but NEVER COMMITTED to main. Working-tree changes from Wave 2.5 will be overlaid by Wave 2.5R per-asteroid raycast impl. This doc retained for history.

---

**Status (historical):** Locked 2026-05-21. Decision-source-of-truth for Wave 2.5 leaf agents.

## Context

Ship-readiness work surfaced spec conflict (`docs/legacy/test_specs/cover_semantics_bible_audit.md`). Bible (`docs/bible_history/bible_2_00_combat.md:421,440,529`, `docs/bible_history/bible_2_00_world.md:144`) defines `cover_density` as continuous-gradient damage-reduction multiplier. Live `simulation/damage.py:132-136,171-175` implements that spec. Westley locked new design 2026-05-21:

**Cover = SC2-style binary LOS-blocker. Polygon model. Symmetric blind. No proximity reveal. No fire-reveal. Non-destructible Phase 1. AI peek = audit + minimal fix.**

This is a bible revision, not a bug fix.

## Design contract (LOCKED)

### Polygon model
- Cover represented as discrete polygons on tactical map. Each polygon = one "rock" / LOS-blocker.
- No gradient. No continuous field. Binary: a point is either inside a cover polygon or not.
- `tactical_map.cover_density()` retired from damage path. Optional: keep gradient API alive for non-cover fields (sensor_interference, elevation, etc.) — but never sampled for cover gameplay.

### Symmetric blind
- Unit A is "in cover" iff `is_in_cover(A.x, A.y)` returns true (point-in-any-cover-polygon).
- Unit A is **visible** to observer B iff:
  - B is in A's faction (always visible to self-side), OR
  - A is not in any cover polygon, OR
  - A and B are in the **same** cover polygon (cover doesn't block sight between two units sharing the same polygon).
- Combat fire = no damage if attacker cannot see target (target not in attacker's `visible` set).

### No proximity reveal
- Close-range observer does NOT pierce cover. Cover blocks regardless of observer distance.

### No fire-reveal
- Defender in cover firing OUT at attacker who can't see them stays hidden. One-sided fire is intentional tactical asymmetry. Defender can shoot at any unit defender's faction has visibility on (via own sensor cone or allied sensor cones). Attacker outside cover sees no muzzle flash, no reveal.

### Non-destructible (Phase 1)
- Cover polygons are static. No HP. Cannot be destroyed.
- `docs/bible_history/bible_2_00_missions.md:263` line on "destroying cover positions" deferred to post-launch DLC consideration.

### AI peek behavior — audit + minimal fix
- L6 sub-agent audits current AI targeting in `simulation/tactical_engine.py` + behavior scripts.
- If audit finds AI clumps in cover and never engages (because nothing visible to fire at), add minimal "advance to cover edge to fire" nudge.
- Full behavior-tree rewrite OUT OF SCOPE.

## Files in scope

### Simulation
- `simulation/tactical_map.py` — add `cover_polygons: List[CoverPolygon]` data structure, `is_in_cover(x, y) -> bool`, `cover_polygon_containing(x, y) -> Optional[int]` (returns polygon id for "same-polygon" symmetric-blind check).
- `simulation/gradient_placer.py` — cover-source emission converts to polygon (circle approximation 8–12 vertices at radius). Non-cover gradient placement untouched.
- `simulation/fog_of_war.py:46-103` — `compute_visibility()` adds cover-occluder pass per the symmetric-blind algorithm.
- `simulation/damage.py:132-136, 171-175` — rip `(1.0 - cover)` mult. Add visibility-gate: attack only deals damage if `target in attacker_visible_set`.
- `simulation/tactical_engine.py` (AI targeting paths) — audit; minimal cover-peek fix if AI clumps.
- `simulation/config.py` — no `COVER_VISION_THRESHOLD` needed (polygon = binary). Possible new config: `COVER_POLYGON_VERTS = 12` (circle approximation resolution).

### Tests
- New: `simulation/test_cover_polygon.py` — `is_in_cover` point-in-poly correctness, `cover_polygon_containing` polygon-id mapping.
- New: `simulation/test_cover_visibility.py` — symmetric-blind algorithm: A in cover hidden from B outside; A in cover visible to B in same poly; A in cover invisible to B in different poly; A outside cover always visible.
- New: `simulation/test_cover_damage_gate.py` — attack at hidden target → 0 damage; attack at visible target in cover → full damage (no mult reduction).
- Updated: any existing test asserting cover-as-damage-mult outcomes. Re-baseline expected. **Tests in scope require explicit Westley sign-off per `feedback_no_test_modification.md` — L7 brief enumerates affected files.**
- New: `simulation/test_cover_integration.py` — apex addendum: 2 attackers + 1 defender in cover, attackers can't see defender, no damage; defender moves out, attackers see + damage resumes.

### Bible
- `docs/bible_history/bible_2_00_world.md:142-150` — rewrite `cover_density` definition. New language: polygon LOS-blocker; hides units inside from outside observers; does NOT reduce damage; does NOT block movement.
- `docs/bible_history/bible_2_00_combat.md:419-425` — strip `(1.0 - cover_density)` from damage formula. Damage = `base × category_multiplier`.
- `docs/bible_history/bible_2_00_combat.md:439-441` — replace "Cover" paragraph with new "Cover & Vision" section: symmetric blind, no proximity reveal, no fire-reveal.
- `docs/bible_history/bible_2_00_combat.md:529` — extend obstacle LOS line to mention cover polygons as additional LOS-blockers (still cover-distinct-from-obstacles per `docs/bible_history/bible_2_00_world.md:142`).
- `docs/bible_history/bible_2_00_missions.md` — spot-check; existing language is behavioral, likely no edits.

## Type contract

### Locked symbols (audit registry — top-level declarations for the /swarm-review symbol scanner)

```python
class CoverPolygon: ...
class TacticalMap: ...

COVER_POLYGON_VERTS = 12

def is_in_cover(x, y): ...
def cover_polygon_containing(x, y): ...
def place_cover_polygons(inst): ...
def compute_visibility(store, tactical_map): ...
def build_cover_apex_scenario(): ...
```

### Canonical shapes (human reference)

```python
# simulation/tactical_map.py (additions)

class CoverPolygon:
    __slots__ = ("polygon_id", "vertices")

    def __init__(self, polygon_id: int, vertices: list[tuple[float, float]]):
        self.polygon_id = polygon_id
        self.vertices = vertices  # closed polygon, last != first

class TacticalMap:
    cover_polygons: list[CoverPolygon]

    def is_in_cover(self, x: float, y: float) -> bool:
        ...

    def cover_polygon_containing(self, x: float, y: float) -> int | None:
        ...
```

```python
# simulation/fog_of_war.py (compute_visibility additions)

# After existing distance + layer + pulse checks:
#   - if target NOT in cover → visible (existing logic stands)
#   - if target IN cover → visible iff observer IN SAME cover polygon
def _cover_visibility_passes(target_x, target_y, observer_x, observer_y, tactical_map) -> bool:
    ...
```

```python
# simulation/damage.py (attack target gate)

# Replace `(1.0 - cover)` multiplier with visibility gate:
#   if target not in attacker_visible_set: return 0 (skip attack)
#   else: dmg = base_dmg * mult  (no cover multiplier)
```

## Algorithms

### Point-in-polygon
Ray-casting: count edge crossings from (x, y) to (+∞, y). Odd = inside, even = outside.

### Cover polygon containing
Iterate `cover_polygons`, return first `polygon_id` where point-in-polygon true, else `None`.

### Symmetric-blind visibility
For observer O looking at target T:
1. Existing distance + layer + pulse + sensor checks pass → continue.
2. Sample `target_polygon = tactical_map.cover_polygon_containing(T.x, T.y)`.
3. If `target_polygon is None` → visible (target not in cover).
4. Else sample `observer_polygon = tactical_map.cover_polygon_containing(O.x, O.y)`.
5. If `target_polygon == observer_polygon` → visible (same polygon).
6. Else → not visible (target hidden behind their cover).

### Damage visibility gate
For each attack tick where attacker A targets unit T:
1. If `T not in compute_visibility()[A.uid]` → skip attack (no damage applied).
2. Else apply existing `has_combat_los` (navmesh obstacle check).
3. If both pass → `dmg = base_dmg * category_multiplier` (no cover term).

## Test expectations

### L2 isolated (tactical_map polygon API)
- 3 polygons placed at known positions. Point inside poly 1 → `is_in_cover` true, `cover_polygon_containing` returns 1's id. Point inside poly 2 → returns 2's id. Point outside all → `is_in_cover` false, `cover_polygon_containing` returns None. Point on edge → deterministic (declare convention: edge = inside).

### L3 (gradient_placer → polygon conversion)
- Pre-Wave 2.5: cover gradient sources at chokepoint + objective. Post: each source produces 1 polygon (8–12 vertex circle approximation at source radius). `tactical_map.cover_polygons` populated. `tactical_map.cover_density()` either returns 0.0 OR retired entirely (decision in L3 brief).

### L4 (fog_of_war cover-occluder)
- A in cover poly 1, B outside → A not in B's visible set.
- A in cover poly 1, B in cover poly 1 → A in B's visible set.
- A in cover poly 1, B in cover poly 2 → A not in B's visible set.
- A outside cover, B outside cover → existing logic applies (visible if in sensor cone).
- Same-faction units always rendered to player (own-faction render layer, unchanged). NOT tracked in `compute_visibility()` set — same-faction pair short-circuits at `fog_of_war.py:73` per pre-Wave-2.5 convention. Downstream consumers (`damage.py`, AI targeting) only query enemy-faction membership, so empty same-faction set is intentional.

### L5 (damage gate)
- Attacker outside, target in cover → no damage applied (target invisible).
- Attacker in same cover as target → full damage (visible, no mult).
- Attacker outside, target outside → full damage (visible, no mult).
- Confirm no `(1.0 - cover_density)` term remains in damage formula.

### L6 (AI peek)
- Audit: dispatch sim scenario with cover polygons + AI faction defender. Assert AI does NOT clump indefinitely without firing. If clumping detected, minimal "move-to-edge-when-visible-target-exists-outside-own-poly" behavior added.

### L7 (apex integration + balance re-baseline)
- Apex E2E test addendum: scenario walk verifies 2-attacker / 1-defender cover scene plays out as designed.
- Balance re-baseline: identify all `simulation/test_*.py` files asserting combat outcomes that depend on cover. Surface list to Westley for sign-off before edits.

## Open questions resolved (no more forks)

- ✅ Cover impl: polygon
- ✅ Symmetric blind: yes (both directions)
- ✅ Proximity reveal: no
- ✅ Fire-reveal: no (defender stays hidden)
- ✅ Destructible: no (Phase 1)
- ✅ AI peek: audit + minimal fix only
- ✅ Threshold: N/A (polygon binary)
- ✅ Same-polygon visibility: yes (both units in same poly see each other)

## Estimate

- Wave 2.5 realistic: 4–5 days.
- Parallel to Wave 3 (B6 pause menu, B3 tutorial wiring, B4 PAN_SPEED). Zero file overlap.
- Combined critical-path within Phase 1's 2–4 week budget.

## Gotchas

1. **Combat balance reshuffle.** All A2–J archetype tests tuned with cover damage-mult. Re-baseline expected. Per CLAUDE.md invariant rules: scope narrowing OK without approval; widening / threshold loosening requires Westley OK.
2. **AI cover clumping.** Real risk. L6 must surface diagnostic before deciding extent of fix.
3. **Polygon edge convention.** Point on polygon edge = inside (declare in L2 brief). Avoid ambiguity in fixture tests.
4. **Tests requiring permission.** Per `feedback_no_test_modification.md`, no test edit without explicit Westley OK. L7 brief lists files up-front for batch sign-off.

## Verification

- L1–L7 all green per their internal assertions.
- Apex E2E test green end-to-end on fresh checkout.
- Bible reads coherent: cover = LOS-block, no damage-mult contradictions across spokes.
- Westley plays one mission and confirms cover feels SC2-equivalent (LOS-block, symmetric blind, no fire-reveal).
