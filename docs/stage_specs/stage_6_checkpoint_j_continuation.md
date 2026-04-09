# Stage 6 — Checkpoint J Continuation: Soft RPS with Positioning

## Status

Checkpoints A through I: **PASS** (all approved by Westley).
Checkpoint J: **IN PROGRESS** — hard collision + line-of-fire implemented, not yet tested. RPS tuning sweep built but not yet run.

Work paused here to fix bugs earlier in the system. This doc captures everything needed to resume.

---

## What Checkpoint J Requires

**Claim L4:** Strike vs Line on a chokepoint map — Strike uses a flank route and wins >30% of engagements despite the unfavorable RPS matchup. This validates that positioning overcomes the category disadvantage.

The original 6J test (pure Strike-category vs pure Line-category, 10v10) failed because flanking had no mechanical effect — all units fired simultaneously regardless of geometry. The fight was a pure stat check, and Line won 100% because the 2:1 effective damage ratio (1.5x vs 0.75x) is too steep.

---

## What Was Built (Implemented, Untested)

### Hard Collision (`movement.py`)

Post-movement push-apart resolution, SC2 model:
- `_resolve_collisions(store, active, tactical_map, navmesh)` — called at end of `update_movement()` when `HARD_COLLISION_ENABLED=True`
- 3 iterations (`COLLISION_RESOLUTION_ITERATIONS`) over all same-layer unit pairs
- If `dist < 2 * UNIT_COLLISION_RADIUS` (30 wu), push each unit apart by `overlap / 2`
- Cross-faction: friendly AND enemy units collide
- Clamp to map bounds, check navmesh walkability after push
- Deterministic fallback for zero-distance overlap (lower uid pushes left)
- Soft separation weight reduced from 0.8 to 0.5 (hard collision does the real work now)

### Line-of-Fire (`damage.py`)

Friendly unit occlusion check, prevents rear units from firing through friendlies:
- `_friendly_blocks_shot(store, attacker_uid, target_uid, active)` — point-to-line-segment distance check
- For each same-faction, same-layer unit: if its collision circle (radius 15 wu) intersects the attacker-to-target segment (between t=0.05 and t=0.95), shot is blocked
- Obstacle LOS check via `has_combat_los(navmesh, x1, y1, x2, y2)` — Bresenham on navmesh grid
- When blocked: attack timer reset to 0 (prevents damage burst on clearing), `continue` to skip damage

### Blocked Retarget (`damage.py` + `unit.py`)

Prevents units from being permanently stuck behind friendlies:
- `store.blocked_ticks` array (int32) added to `UnitStore`
- In `resolve_damage()`: incremented when shot is blocked, reset to 0 when not blocked
- In `update_targeting()`: if `blocked_ticks[uid] > BLOCKED_RETARGET_TICKS` (40 ticks = 2 sec), force retarget by clearing `auto_engage_target`

### Config additions (`config.py`)

```python
HARD_COLLISION_ENABLED          = True
COLLISION_RESOLUTION_ITERATIONS = 3
LINE_OF_FIRE_ENABLED            = True
BLOCKED_RETARGET_TICKS          = 40    # 2 sec before retargeting around blocker
```

### Combat LOS export (`movement.py`)

```python
def has_combat_los(navmesh, x1, y1, x2, y2):
    if navmesh is None:
        return True
    return _has_los(navmesh, (x1, y1), (x2, y2))
```

Imported by `damage.py` as `from movement import has_combat_los, _ensure_navmesh`.

---

## What Was Built But Not Run

### Diagnostic test (`test_checkpoint_6j.py`)

Modified with verbose output for flank seed 1:
- Per-unit table at first damage and every 200 ticks: uid, type, position, target, LOS-blocked, distance
- Bounding box of each force at first contact
- Arrival spread: tick each Strike unit first enters weapon range, gap between first and last arrival
- Direct approach: summary only (no per-unit output)

### Scenario matrix (`test_6j_matrix.py`)

8 scenarios, 25 seeds each (200 engagements):
1. Open field head-on 10v10
2. Open field flank 10v10 (Strike from the side)
3. Open field surround 10v10 (Strike splits into 2 groups)
4. Chokepoint head-on 10v10
5. Chokepoint flank 10v10
6. Open field head-on 15v10 (Strike numerical advantage)
7. Open field head-on 10v15 (Line numerical advantage)
8. Cover-heavy map, Strike starts in cover, 10v10

Outputs: Strike wins, avg duration, avg survivors per side, avg firing% per side. Firing% = fraction of alive units with a valid non-LOS-blocked target in range, sampled every 50 ticks during combat.

### RPS multiplier tuning sweep (`test_6j_tuning.py`)

Tests 5 multiplier pairs across 3 scenarios (head-on, surround, 15v10), 25 seeds each:
- 1.50 x 0.75 (2.00:1 effective — current)
- 1.40 x 0.80 (1.75:1)
- 1.30 x 0.85 (1.53:1)
- 1.25 x 0.85 (1.47:1)
- 1.20 x 0.90 (1.33:1)

Target criteria: head-on Strike wins <30%, surround wins 30-60%, 15v10 wins >60%.

### Mixed composition tuning (`test_6j_mixed.py`)

Tests whether force-level (not unit-level) RPS category assignment produces better balance:
- Strike force: 3 Vanguard + 5 Raider + 2 Interceptor (all tagged category=Strike)
- Line force: 5 Vanguard + 3 Warden + 2 Raider (all tagged category=Line)
- Overrides `store.category[uid]` at spawn to force the composition's category tag

Tests 3 multiplier pairs (2.00:1, 1.53:1, 1.33:1) across the same 3 scenarios.

---

## Open Questions (Need Data First)

### Per-unit vs per-force RPS

Currently the RPS multiplier is per-unit-type category (`damage.py:36-37`). A Vanguard on the Strike force still has category=Line. `test_6j_mixed.py` overrides this to test force-level assignment. **Neither approach has been run yet** — the data will reveal which feels right.

### RPS multiplier sweet spot

The 2:1 effective ratio (1.5x / 0.75x) may be too steep for positioning to matter. The tuning sweep tests down to 1.33:1. If none of the tested pairs hit the target criteria, the ratio may need to go even lower, or the problem is in unit stats (HP gap between Strike and Line is 3.2x for Raider vs Vanguard).

### Strike vs Siege inversion (deferred)

Bastion at 2100 HP is effectively unkillable by Strike (Raider effective DPS with 1.5x mult = 33.75, time to kill = 62 sec). Bombard AoE shreds low-HP Strike units. This is a known issue but deferred — it needs a stat baseline conversation. Not blocking 6J.

---

## Current Unit Stats (Live in config.py)

These diverge from the spec's Tier 2 baseline — HP was bumped 1.5x during Checkpoint D tuning to hit the engagement duration targets (L5/L6/L7).

| | Raider | Interceptor | Vanguard | Warden | Bombard | Bastion |
|---|---|---|---|---|---|---|
| HP | 375 | 525 | 1200 | 900 | 1050 | 2100 |
| Base dmg | 18 | 12 | 15 | 8 | 35 | 14 |
| Atk interval | 0.8s | 1.0s | 1.2s | 1.5s | 3.0s | 1.8s |
| DPS | 22.5 | 12.0 | 12.5 | 5.3 | 11.7 | 7.8 |
| Atk range | 200 | 250 | 300 | 350 | 600 | 400 |
| Speed | 150 | 130 | 80 | 70 | 50 | 40 |

Other config changes from spec baseline:
- `RALLY_HEAL_AMOUNT`: 150 -> 225 (proportional to 1.5x HP bump)
- `WARDEN_AURA_REPAIR_RATE`: 0.5 -> 0.75 (same reason)
- Warden speed: 90 -> 70 (changed during tuning)

---

## Files Modified During 6J Work

- `simulation/config.py` — 4 new constants (collision/LOS flags)
- `simulation/unit.py` — `blocked_ticks` array added to UnitStore.__init__
- `simulation/movement.py` — `_resolve_collisions()`, `has_combat_los()`, separation weight 0.8->0.5
- `simulation/damage.py` — `_friendly_blocks_shot()`, obstacle LOS check, blocked-tick tracking/retarget, import of `has_combat_los`/`_ensure_navmesh` from movement
- `simulation/test_checkpoint_6j.py` — diagnostic output for flank seed 1
- `simulation/test_6j_matrix.py` — NEW, 8-scenario matrix test
- `simulation/test_6j_tuning.py` — NEW, RPS multiplier sweep
- `simulation/test_6j_mixed.py` — NEW, mixed comp with force-level category

---

## Resume Sequence

1. **Run `test_checkpoint_6j.py`** — verify collision + LOS code doesn't crash. Read the flank seed 1 diagnostics. Does the geometry look different from direct approach? Are units being LOS-blocked? Is the arrival spread tight or strung out?

2. **Run `test_6j_matrix.py`** — get the full 8-scenario picture. Key columns: Strike wins and firing% asymmetry. If firing% is identical between sides in all scenarios, the LOS system isn't creating the intended geometry advantage.

3. **Run `test_6j_tuning.py`** — find the multiplier sweet spot. If no pair hits the target criteria (head-on <30%, surround 30-60%, 15v10 >60%), the issue is deeper than the multiplier.

4. **Run `test_6j_mixed.py`** — compare per-force vs per-unit-type category. If the mixed comp test produces better balance curves, discuss with Westley whether to change the RPS system to force-level.

5. **Based on data, decide:**
   - If a multiplier pair works: update `config.py`, re-run the canonical `test_checkpoint_6j.py` to confirm L4 passes.
   - If the problem is unit stats (HP gap too large): propose stat changes to Westley.
   - If the problem is collision/LOS not creating enough asymmetry: tune `UNIT_COLLISION_RADIUS`, `COLLISION_RESOLUTION_ITERATIONS`, or the `_friendly_blocks_shot` t-range (currently 0.05-0.95).

6. **Regression check** after any config changes: run `test_checkpoint_6d.py` (engagement durations) and spot-check `test_checkpoint_6e.py` (abilities).

7. **After 6J passes:** proceed to Checkpoint K (performance stress test) and Checkpoint L (final invariants + Tactical Review Reports).

---

## Approved Plan Reference

The full implementation plan is at `~/.claude/plans/vectorized-rolling-corbato.md`. It covers the collision + LOS design rationale, why flanking should work after these changes, and regression risk assessment. All code described in the plan has been implemented.
