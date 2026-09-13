# Stage 4 Addendum — Collision Resolver and Admin Revolt Ownership Guard

> **Context:** Two E2 failures surfaced during Stage 4 validation. Root cause analysis
> found two missing mechanics that the bible specifies but were never assigned to a stage spec.
> This addendum adds them to Stage 4 scope.

---

## Bug 1: Admin Revolt Breakaway Overwrites Conquest

**Symptom:** E2 critical failure. A conquest transfers region ownership to faction A
on the same tick that an admin revolt chain's terminal ADMIN_BREAKAWAY event fires on
that region, creating faction B. Faction B overwrites A's conquest.

**Root cause:** The ADMIN_BREAKAWAY terminal event does not check whether the region
still belongs to the faction the chain was spawned against.

**Fix — ownership guard on admin revolt terminal event.**

In the ADMIN_BREAKAWAY event resolution (the terminal event of the admin revolt chain),
before creating the breakaway faction, check:

```
if region.faction_id != chain.parent_faction_id:
    # The region changed hands since the revolt started.
    # The separatist movement's political context no longer exists.
    # Prune the terminal event. Log as a pruned chain.
    return
```

This is consistent with the bible's pending queue design: "The world moved on and the
crisis resolved itself before it could escalate." The admin revolt chain is
non-interruptible in terms of *condition checks on intermediate events*, but the terminal
event creating a faction in a region that no longer belongs to the parent faction is a
logical impossibility, not a suppressed chain.

**Files to modify:** `admin_revolt.py` (or wherever ADMIN_BREAKAWAY resolution lives).

**Test:** Set up a region owned by faction A with an admin revolt chain 2 ticks from
completing. On the tick before completion, have faction B conquer the region. On the
completion tick, confirm the breakaway does NOT fire. Confirm the event log records a
pruned entry with reason "region ownership changed." Confirm faction A's territory count
decreased by 1 (from the conquest, not the revolt). Confirm no new breakaway faction
was created.

**🛑 CHECKPOINT — Run scenarios 07_full_game_50 and 09_lifecycle_4faction seed 1. Confirm E2 passes.**

---

## Bug 2: Two Attacks on Same Region Same Tick Resolve Sequentially

**Symptom:** E2 critical failure in scenario 10_time_jump. Region should belong to
fortifier after conquest but belongs to conqueror. Two factions attacked the same region
on the same tick. The second attack overwrote the first conquest.

**Root cause:** The bible specifies a probabilistic collision resolver for same-tick
same-target attacks (`docs/bible_history/bible_2_00_simulation.md` → "Contested regions — collision resolution").
This was never implemented. Stage 3 spec only implemented colonization collisions
(checkpoint E2: coin-flip winner, loser refunded). Attack collisions were missed.

**Bible spec (verbatim from `docs/bible_history/bible_2_00_simulation.md`):**

> "When two or more factions target the same region on the same tick (whether through
> attacks, colonization, or a mix), the intent resolver runs a collision resolution.
> Each participant's effective strength is computed from their committed budget, weighted
> by an economy factor (factions with stronger economies fight more effectively in
> collisions) and tech multipliers. The winner is chosen probabilistically — higher
> effective strength means higher probability of winning, but upsets are possible. The
> victory margin determines consequences: a dominant victory leaves the winner with
> retained budget and a strong garrison, while a narrow victory produces a weakened
> claim with reduced military. Losers spend their committed budget and take a tension
> hit to their home regions."

### What to Build

**`collision.py`** — Collision resolver module. Contains one entry point called by
tick step 3 when 2+ actions target the same region on the same tick.

**Detection (in `tick.py` step 3):** After all faction agents have chosen their actions
for this tick but before resolving any of them, scan for collisions: group all attack
and colonization actions by target region. Any target region with 2+ actions routes
to the collision resolver instead of sequential resolution.

Non-colliding actions resolve normally through the existing path.

**Resolution algorithm:**

```
For each collision group (2+ actions on the same target region):

1. Compute effective strength per participant:
   effective_strength = committed_budget * economy_factor * tech_attack_mult

   economy_factor = avg_faction_economy / 100
   tech_attack_mult = faction's tech attack multiplier (from archetype tech mapping)

   For colonization actions, committed_budget = COLONIZE_COST.

2. Compute win probability per participant:
   win_probability_i = effective_strength_i / sum(all effective_strengths)

3. Roll weighted random to select winner.

4. Compute victory margin:
   margin = winner_effective_strength / sum(loser_effective_strengths)

5. Apply consequences:

   Winner:
   - If target was uninhabited: colonize with margin-adjusted starter values.
     Strong margin (>2.0): full colony starter values.
     Narrow margin (<1.0): colony starter values * COLLISION_NARROW_PENALTY (e.g. 0.7).
   - If target was owned by another faction: run normal attack resolution
     (breakthrough/contested/repelled) of winner vs defender, but with
     winner's committed_budget reduced by (1 - margin_retention_fraction).
     A dominant win retains most budget for the attack. A narrow win
     means the collision consumed most of the winner's strength before
     they even engaged the defender.
   - Garrison placement uses the margin-adjusted committed budget.

   Losers (all non-winners):
   - committed_budget fully spent (budget -= committed_budget)
   - Home region tension += COLLISION_LOSS_TENSION (config value)
   - If the loser was attacking (not colonizing), their attack does NOT
     resolve against the target — they lost the collision and withdrew.

6. Log the collision event:
   - event_type: "COLLISION"
   - participants: list of {faction_id, committed_budget, effective_strength}
   - winner: faction_id
   - margin: float
   - target_region: region_id
   - collision_flag: True  (for chronicle significance scoring)
```

**Config values to add:**

```python
# ── Collision resolution (Stage 4 addendum) ────────────────────────
COLLISION_NARROW_PENALTY      = 0.7   # colony starter value multiplier for narrow collision wins
COLLISION_LOSS_TENSION        = 3.0   # tension added to each loser's home region
COLLISION_MARGIN_RETAIN_HIGH  = 0.85  # budget retention for dominant wins (margin > 2.0)
COLLISION_MARGIN_RETAIN_LOW   = 0.40  # budget retention for narrow wins (margin < 1.0)
# Linear interpolation between LOW and HIGH for margins between 1.0 and 2.0
```

### Also fix: Colonization collisions

The existing colonization collision (Stage 3 checkpoint E2) uses a coin flip with
budget refund. Upgrade it to use the same collision resolver. Colonization actions
enter the collision with `committed_budget = COLONIZE_COST`. Economy factor and tech
multipliers apply the same way. Losers spend their colonization cost (no refund —
bible says losers spend their committed budget). This replaces the existing coin-flip
logic in the colonization path.

### Files to modify

- **`collision.py`** (new) — collision resolution logic
- **`tick.py`** — step 3: collect all actions, detect same-target groups, route
  collisions to `collision.py`, resolve non-collisions normally
- **`config.py`** — add collision config values
- **`invariants.py`** — add K1 invariant (see below)

### Behavioral Claims

**Claim K1: Collision resolver fires on same-tick same-target attacks.** When 2+
factions target the same region on the same tick, the collision resolver must fire
instead of sequential resolution. Only one faction should end up with the region.

- When: 2+ attack/colonize actions target the same region on the same tick
- Then: exactly 1 winner via probabilistic selection, all losers spend budget,
  region ownership is unambiguous after resolution
- Over: every collision in the run
- Pattern: threshold bound
- Governing configs: (code bug if violated — always escalate)
- Severity: critical

**Claim K2: Collision winner correlates with strength.** Over 100+ collisions across
multiple seeds, the faction with higher effective strength should win >55% of the time.
Upsets are possible but the stronger faction wins more often than not.

- When: collision resolves
- Then: across all collisions, higher-strength participant wins >55%
- Over: aggregate across full run
- Pattern: statistical bound
- Governing configs: (design issue if violated — check economy_factor and tech scaling)
- Severity: warning

**Claim K3: Collision losers pay full cost.** Every collision loser must have their
committed budget spent and their home region tension increased.

- When: collision resolves
- Then: for each loser, budget decreased by committed amount, home tension increased
- Over: every collision
- Pattern: threshold bound
- Governing configs: `COLLISION_LOSS_TENSION`
- Severity: critical

### Test

**Unit test:** Set up 3 factions adjacent to the same region (owned by a 4th faction
or uninhabited). Give faction A committed_budget=40, faction B committed_budget=25,
faction C committed_budget=15. Set economies: A=60, B=40, C=80.

Effective strengths: A=40×0.6=24, B=25×0.4=10, C=15×0.8=12.
Win probabilities: A=52%, B=22%, C=26%.

Run 100 times. Confirm A wins ~50%, C wins ~25%, B wins ~22%. Confirm every run
produces exactly 1 owner. Confirm losers always spend budget and take tension hit.
Print the distribution.

**🛑 CHECKPOINT — Run all 4 scenarios (07, 08, 09, 10). Confirm E2 passes in all. Confirm K1–K3 pass.**

---

## Invariant Threshold Adjustments

While validating Stage 4, three existing invariant thresholds produced recurring
warnings that are not simulation bugs but overly strict thresholds. Adjust:

**B3 (tension-economy):** Currently flags when economy < midpoint for 30 ticks AND
tension trending down. The bible's proportional tension decay is *designed* to produce
strong decay at high tension even under economic pressure. Refine the check: only flag
if tension is below `TENSION_ECONOMY_MIDPOINT` AND economy is below midpoint AND
tension is trending down. When tension is already high, downward trend is the
proportional decay working correctly.

**J8 (conflict after expansion):** Lower threshold from 1.5× to 1.3×. The 50-region
map produces attacks during expansion via border friction (bible-correct behavior),
which elevates the pre-expansion baseline and compresses the ratio. 1.3× still detects
that conflict accelerates after expansion without demanding a clean phase boundary the
map geometry can't produce.

**A1 (field flatline) — population field only:** Widen the flatline range threshold
for population from 3.0 to 5.0. The bible says population is "the slowest-moving field"
— a population at equilibrium with range 2.8 over 60 ticks is stable, not flatlined.
Other fields keep the existing threshold.

---

## Updated Done Condition

All original Stage 4 validation criteria, plus:

- E2 passes across all scenarios and seeds (no conquest ownership mismatches)
- K1–K3 pass (collision resolver works correctly)
- Collision events appear in the event log with `collision_flag: True`
- No regressions in A–J invariants from the collision resolver changes
