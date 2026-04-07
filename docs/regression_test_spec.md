# Simulation Regression Test Spec — Ouroboros Manifold

> **Purpose:** Machine-checkable thresholds that verify the simulation produces
> the bible's designed experience. Run after any code or config change.
> If any threshold fails, the change broke something — investigate before merging.
>
> **Scenario:** `full_game_50` template, 500 ticks, seed 1, all systems enabled.
> All thresholds derived from the final tuned run (April 6, 2026).
>
> **How to use:** Build a test script that runs the scenario, collects the same
> data as `bible_diagnostic.py` and `region_autopsy.py`, and asserts every
> threshold below. Each threshold has a rationale linking it to a bible requirement.

---

## 1. Starting World Shape

These verify the template hasn't been accidentally modified.

| Check | Threshold | Rationale |
|-------|-----------|-----------|
| Total regions | `== 50` | Template integrity |
| Empty regions at start | `== 42` | Template integrity |
| Inhabited regions at start | `== 8` | 4 factions × 2 regions each |
| Empty fraction | `0.80–0.86` | Bible: expansion space must dominate |
| Starting factions | `== 4` (player, conqueror, fortifier, opportunist) | Template integrity |
| Each faction starts with exactly 2 regions | all 4 factions `region_count == 2` | Template integrity |

**Source:** `bible_diagnostic.py` Section 2.

---

## 2. Expansion Phase (Ticks 0–50)

Bible: "Factions start with few regions and low budgets... factions expand into
empty space rather than fighting each other."

| Check | Threshold | Rationale |
|-------|-----------|-----------|
| Colonizations in ticks 0–50 | `>= 15` | Expansion phase must be active (baseline: 23) |
| Attacks in ticks 0–50 | `<= 5` | No significant combat during expansion (baseline: 0) |
| Conquests in ticks 0–50 | `<= 2` | Territory shouldn't change hands during expansion (baseline: 0) |
| First colonization tick | `<= 15` | Factions colonize early (baseline: tick 9) |
| First attack tick | `>= 40` | Attacks don't start until expansion slows (baseline: tick 52) |
| Col:Atk ratio in ticks 0–50 | `>= 3.0` | Colonization dominates early game (baseline: 23:0 = ∞) |

**Source:** `bible_diagnostic.py` Section 3, window 0–50.

---

## 3. Conflict Phase (Ticks 100–500)

Bible: "Inter-faction attacks begin... the world is always in motion. Territory
changes hands regularly."

| Check | Threshold | Rationale |
|-------|-----------|-----------|
| Total attacks in 500 ticks | `500–2500` | World is active but not degenerate (baseline: 1622) |
| Total conquests in 500 ticks | `200–1000` | Territory changes hands regularly (baseline: 641) |
| Conquests per tick (ticks 100–500) | `>= 0.5` | Bible: "at least one conquest per 20–30 tick window" = ~0.05/tick minimum; actual rate much higher at scale (baseline: ~1.6/tick) |
| Colonizations in ticks 200–500 | `== 0` | All empty regions should be claimed by tick 200 (baseline: 0) |
| Total colonizations | `35–50` | All 42 empties should be colonized eventually (baseline: 42) |

**Source:** `bible_diagnostic.py` Section 3.

---

## 4. Attack Outcome Distribution

Bible: "Damage scales proportionally to how decisive the outcome was."

| Check | Threshold | Rationale |
|-------|-----------|-----------|
| Repelled rate | `15%–40%` | Attacks should fail sometimes but not most of the time (baseline: 20.6%) |
| Contested rate | `40%–75%` | Most attacks produce attrition (baseline: 65.0%) |
| Breakthrough rate | `0.5%–5%` | Decisive victories are rare and meaningful (baseline: 1.4%) |
| Collision rate (collision + collision_loss) | `5%–20%` | Multi-faction pileups happen occasionally (baseline: 13.0%) |
| Mean committed budget | `5–25` | Factions commit meaningful budget per attack (baseline: 11.82) |

**Source:** `bible_diagnostic.py` Section 8.

---

## 5. Faction Survival and Mortality

Bible: "No faction — including the player's — has plot armor or guaranteed survival."
Also: "The player's civilization can collapse."

| Check | Threshold | Rationale |
|-------|-----------|-----------|
| All 4 original factions alive at tick 100 | `>= 3 of 4` | Factions shouldn't die in the expansion phase (baseline: 4/4) |
| Player faction alive at tick 100 | `true` | Player should survive early game (baseline: alive at 500) |
| Factions alive at tick 500 | `10–40` | Rich political landscape from breakaways (baseline: 24) |
| At least 1 original faction peak territory >= 10 | `true` | Factions should build real empires (baseline: conqueror peaked at 13, opportunist at 15) |

**Cross-seed check (run seeds 1–5):**

| Check | Threshold | Rationale |
|-------|-----------|-----------|
| Player faction dies in at least 1 of 5 seeds | `true` | Bible: player has no plot armor (J13) |
| At least 2 original factions survive all 500 ticks in each seed | `true` | World shouldn't collapse to single faction |

**Source:** `bible_diagnostic.py` Sections 4, 12.

---

## 6. Tension Equilibrium

Bible: "Proportional tension decay prevents permanent runaway spirals."
Home regions should be stable; contested frontiers should be elevated but not
permanently maxed.

| Check | Threshold | Rationale |
|-------|-----------|-----------|
| Regions with mean tension > 90 (last 200 ticks) | `<= 15 of 50` (30%) | Most regions should not be permanent wastelands (baseline: 14/50) |
| Home regions mean tension | all `< 50` | Home regions are stable (baseline: 0.9–33.9) |
| At least 10 regions with mean tension 35–65 | `true` | Healthy contested-but-stable zone exists (baseline: ~15 regions) |
| No region flatlined (range < 5 over last 200 ticks AND mean > 95) | `<= 5` | A few permanent hotspots are OK, many are not (baseline: ~3–4) |

**Source:** `bible_diagnostic.py` Section 6. Compute from region tension stats
over the last 200 ticks.

---

## 7. Admin Revolts

Bible: "Once an admin revolt fires, it always completes and produces a new
independent faction."

| Check | Threshold | Rationale |
|-------|-----------|-----------|
| Admin revolt chains started | `>= 50` | System is active at 50-region scale (baseline: 118) |
| Admin revolt completion rate | `>= 70%` | Most chains should complete (baseline: 131/118 > 100%) |
| Admin revolts produce breakaway factions | completion count `> 0` | Terminal event creates factions (baseline: 131) |

**Source:** `bible_diagnostic.py` Section 3 (A-Revolts column) and Section 12.

---

## 8. Breakaway Behavior

Bible: Breakaways "operate as independent agents — they can be attacked, they
can attack."

| Check | Threshold | Rationale |
|-------|-----------|-----------|
| Total breakaway factions spawned | `50–200` | Fragmentation produces new factions (baseline: ~120) |
| Breakaways with attack rate > 5% (of those surviving 50+ ticks) | `>= 20%` | Some breakaways become active participants (baseline: ~30%) |
| Zombie breakaways (100+ ticks, 100% accumulate) | `<= 5` | Ghost factions are cleaned up (baseline: 0) |

**Source:** `bible_diagnostic.py` Section 11, `region_autopsy.py` Section E.

---

## 9. Conquest Churn (Ping-Pong)

Not a bible target per se, but excessive churn on specific regions indicates
broken agent behavior or degenerate attractiveness scoring.

| Check | Threshold | Rationale |
|-------|-----------|-----------|
| Worst region ownership changes in 500 ticks | `<= 120` | Some hotspots are OK, extreme churn is not (baseline: 97) |
| Regions with > 50 ownership changes | `<= 5 of 50` | Most regions should be reasonably stable (baseline: ~3–4) |
| Mean ownership changes across all regions | `5–25` | World is dynamic but not chaotic (baseline: ~15) |

**Source:** `region_autopsy.py` Section A.

---

## 10. Colony Viability

Colonies must survive long enough to develop, not immediately death-spiral.

| Check | Threshold | Rationale |
|-------|-----------|-----------|
| `COLONY_START_POPULATION` | `>= 25` | Below this, overcapacity decay kills the colony (see ECO_POP_RATIO math) |
| `COLONY_START_ECONOMY` | `>= 20` | Must exceed POPULATION_SUBSISTENCE (15) for pop growth |
| Breakaway spawn average economy | `>= 15` | Breakaways spawn above subsistence (baseline: 23.0) |
| At least 20 former-empty regions with mean tension < 80 | `true` | Most colonies should eventually stabilize (baseline: ~25–30) |

**Source:** `bible_diagnostic.py` Sections 6, 10. Config values.

---

## 11. Entrenchment

Bible: "Established territory structurally harder to take than newly claimed territory."

| Check | Threshold | Rationale |
|-------|-----------|-----------|
| `ENTRENCHMENT_RAMP_TICKS` | `>= 75` | Below this, entrenchment maxes too fast for ping-pong prevention |
| Regions held 100+ ticks reach entrenchment > 1.9 | `true` | Long-held territory gets full defense bonus |
| Agent expected_net accounts for entrenchment | `true` (code check) | Agents shouldn't ignore defense multiplier when choosing targets |

**Source:** `pingpong_diagnostic.py` Test 3. Config values.

---

## 12. Border Friction

Bible: "Background stress of contested borders, not active military engagement."

| Check | Threshold | Rationale |
|-------|-----------|-----------|
| `BORDER_FRICTION_TENSION` | `<= 0.20` | Higher values cause tension spiral via economy feedback loop |
| `BORDER_FRICTION_ECONOMY` | `<= 0.10` | Higher values push economy to floor, triggering subsistence crisis cascade |
| Default diplomatic stance for unknown faction pairs | `"neutral"` (code check) | Bible: neutral means no friction |
| Active friction code path is flat (not military-scaled) | `true` (code check) | Verify `tick.py` `_apply_border_friction` is called, not `border_friction.py` |

**Source:** Config values. `region_autopsy.py` Section F.

---

## 13. Scoring and Agent Decisions

Bible: "The colonize and attack decisions share a single candidate pool."

| Check | Threshold | Rationale |
|-------|-----------|-----------|
| Colonization candidates visible in early ticks (Section 9 `#Col > 0`) | ticks 1–10 all factions see `#Col >= 1` | Colonization scoring is active |
| `ColScore` is numeric (not None) when `#Col > 0` | `true` | Scoring function produces values |
| `ATTRACT_VALUE_MULTIPLIER` | `>= 1.5` | Below this, weakness dominates and wastelands are over-targeted |
| Original factions attack rate at tick 500 | conqueror `>= 30%`, fortifier `>= 20%` | Factions are aggressive, not permanently accumulating |

**Source:** `bible_diagnostic.py` Sections 9, 11. Config values.

---

## Config Snapshot (Tuned Values)

These are the config values that produce the above behavior. If any change,
re-run the full regression suite.

```
BUDGET_GROWTH_RATE          = 0.025
REGION_MAINTENANCE_COST     = 8.0
ATTACK_COMMIT_FRACTION      = 0.7
ATTACK_EFFICIENCY           = 1.0
RESISTANCE_FACTOR           = 0.55
BREAKTHROUGH_THRESHOLD      = 15.0
CONQUEST_THRESHOLD          = 5.0
COLONIZE_COST               = 20.0
COLONY_START_MILITARY       = 10.0
COLONY_START_ECONOMY        = 20.0
COLONY_START_TENSION        = 20.0
COLONY_START_POPULATION     = 25.0
MILITARY_DECAY_RATE         = 0.006
RECRUITMENT_BASELINE        = 0.1
RECRUITMENT_THRESHOLD       = 20.0
RECRUITMENT_CEILING         = 90.0
ECONOMY_BASE_GROWTH         = 2.0
TENSION_ECONOMY_RATE        = 0.5
TENSION_NATURAL_DECAY_RATE  = 0.2
TENSION_ECONOMY_MIDPOINT    = 50.0
ECONOMY_FLOOR               = 8.0
BORDER_FRICTION_TENSION     = 0.15
BORDER_FRICTION_ECONOMY     = 0.05
ECON_OSCILLATION_AMPLITUDE  = 6.0
ECON_OSCILLATION_PERIOD     = 15
ADMIN_REVOLT_BASE_RATE      = 0.001
ADMIN_REVOLT_SCALING_RATE   = 0.0005
ADMIN_REVOLT_INFLECTION_POINT = 4
REVOLT_BASE_PROBABILITY     = 0.007
REVOLT_TENSION_EXPONENT     = 0.8
ENTRENCHMENT_BASE           = 1.0
ENTRENCHMENT_MAX            = 2.0
ENTRENCHMENT_RAMP_TICKS     = 100
REVOLT_BREAKAWAY_POP_FLOOR  = 25.0
ATTRACT_VALUE_MULTIPLIER    = 2.0
```
