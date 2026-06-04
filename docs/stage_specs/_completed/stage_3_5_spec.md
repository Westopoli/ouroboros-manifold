# Stage 3.5 — Diplomacy and Technology

## Goal
Prove that factions form cooperative relationships through sustained non-aggression, benefit from cooperation (adjacency sharing, border friction removal, tech convergence), betray each other through probability-based betrayal rolls, and advance technologically at rates determined by their economic and population base — producing emergent diplomatic landscapes and technology progression with genuine stochastic divergence across seeds.

## Context
**Read in game_bible.md (v1.17):** "The Simulation Backbone" section, specifically:
- Diplomatic Stance (hostile/neutral/cooperative, peace formation, betrayal mechanic)
- Technology System (tech_level, archetype-interpreted multipliers, growth formula, convergence, breakaway inheritance, technology loss, tech tiers)
- Multi-Faction Agent Decision Model (faction entity model — now includes tech_level)
- Attack event resolution (tech multipliers feed into attack_efficiency and resistance_factor)
- Border friction (gated by hostile stance — cooperative and neutral borders produce no friction)
- Tick Resolution Sequence (Stage 3.5 adds tech growth and diplomacy checks to the existing loop)

**Era-agnostic naming:** Per Sacred Design Principle #3, the engine uses abstract mechanical vocabulary only. "tech_level" not "science level," "cooperative" not "allied" or "trading partners," "convergence_rate" not "knowledge_transfer_rate."

**Builds on:** Stage 3 (faction agents, attack resolution, conquest, reinforce, border friction, budget accumulation) and the intent-resolution loop (snapshot-decide-resolve). Stage 3.5 adds diplomacy mechanics and technology as a faction attribute. It modifies the existing attack resolution formula to incorporate tech multipliers and modifies border friction to gate on diplomatic stance.

**What Stage 3.5 does NOT include:** Tech tiers affecting unit generation (tactical layer dependency — later stage), technology loss event templates (event library content — can be authored separately), sci-fi era tier creative content, coherence ledger integration (Stage 4), chronicle generation. Stage 3.5 tests with 3+ factions to exercise diplomacy dynamics.

## What to Build

### Files to create:

**`diplomacy.py`** — Diplomatic stance management and peace/betrayal mechanics. Contains:
- Per-faction-pair stance tracking (hostile/neutral/cooperative)
- Non-aggression timer tracking per neutral border pair
- Peace formation check (timer threshold + stability check → Diplomatic Overture event)
- Betrayal probability computation per cooperative pair per tick
- Betrayal resolution (surprise attack + stance flip to hostile)
- Stance query helpers (is_hostile, is_cooperative, etc. — used by border friction, adjacency bonus, agent decisions)

**`technology.py`** — Technology system. Contains:
- Per-tick tech_level growth computation (economy-driven with population floor)
- Tech convergence computation for cooperative pairs (best-partner-only)
- Archetype multiplier lookup (tech_level × archetype → attack_efficiency_modifier, defense_efficiency_modifier, economy_growth_modifier)
- Breakaway tech inheritance (copy parent tech_level on faction creation)

### Files to modify:

**`faction.py` (or `faction_agent.py`)** — Extend faction entity:
- Add `tech_level` field to faction data structure (float, 0–100, starting value per archetype config)
- Add starting `tech_level` ranges per archetype to config

**`attack_resolver.py`** — Integrate tech multipliers:
- `effective_attack = attack_strength * attack_efficiency * attacker_tech_attack_modifier`
- `effective_defense = defender_military * resistance_factor * defender_tech_defense_modifier`
- Tech modifiers are looked up from the archetype multiplier table via `technology.py`

**`border_friction.py`** — Gate on diplomatic stance:
- Only apply friction to regions bordering **hostile** factions (current behavior)
- Skip friction for neutral and cooperative borders (new — reads stance from `diplomacy.py`)

**`tick.py`** (or equivalent tick loop) — Add new steps:
- After faction agent resolution (step 3): run betrayal checks on cooperative pairs
- After border friction (step 4): apply tech growth per faction, apply tech convergence for cooperative pairs
- Diplomacy checks (peace formation) can run alongside or after drift (step 5)

**`world.py` / world template** — Extend for 3+ factions:
- Starting template places 3–4 factions (minimum needed to exercise diplomacy: two factions that can form peace, one that stays hostile)
- Starting diplomatic stances per archetype pair (Conqueror starts hostile to all, Fortifier starts neutral to non-Conqueror factions, etc.)

**Config additions to `config.py`** — All new config values for Stage 3.5. Feature flags: `ENABLE_DIPLOMACY = True`, `ENABLE_TECHNOLOGY = True`.

## Input/Output Shapes

### Diplomatic Stance Registry (data structure in diplomacy.py):
```python
{
    # Keyed by sorted faction pair tuple for consistency
    ("conqueror_01", "player_civ"): {
        "stance": "hostile",
        "non_aggression_ticks": 0,       # only tracked for neutral pairs
    },
    ("fortifier_01", "player_civ"): {
        "stance": "neutral",
        "non_aggression_ticks": 47,      # counting up toward peace threshold
    },
    ("fortifier_01", "conqueror_01"): {
        "stance": "cooperative",
        "non_aggression_ticks": 0,       # not tracked for cooperative pairs
        "cooperative_since_tick": 312,   # for logging/chronicle
    }
}
```

### Tech State (fields on faction entity):
```python
{
    "faction_id": "fortifier_01",
    "tech_level": 34.7,
    "tech_tier": 2,                      # derived: 0–33 = tier 1, 34–66 = tier 2, 67–100 = tier 3
    "tech_growth_this_tick": 0.043,      # for logging
    "tech_convergence_this_tick": 0.012, # for logging (0 if no cooperative partner)
    "tech_multipliers": {                # looked up from archetype table
        "attack_efficiency": 1.06,
        "defense_efficiency": 1.08,
        "economy_growth": 1.05
    }
}
```

### Peace Formation Event Log Entry:
```python
{
    "event_type": "diplomatic_overture",
    "tick": 358,
    "factions": ["fortifier_01", "player_civ"],
    "result": "success",                 # or "failed"
    "non_aggression_duration": 80,       # ticks of sustained non-aggression
    "avg_border_stability": 62.3,        # stability of border regions at time of check
    "compatibility_score": 0.74          # economic compatibility factor
}
```

### Betrayal Event Log Entry:
```python
{
    "event_type": "betrayal",
    "tick": 512,
    "betrayer": "conqueror_01",
    "victim": "fortifier_01",
    "betrayal_probability": 0.023,       # the rolled probability this tick
    "opportunity_modifier": 1.8,         # military advantage factor
    "pressure_modifier": 1.3,            # internal tension factor
    "archetype_weight": 2.5,             # conqueror betrayal weight
    "attack_target_region": "region_fort_frontier_1",
    "cooperative_duration_ticks": 200    # how long they were cooperative before betrayal
}
```

### Per-Tick Tech Growth Log Entry:
```python
{
    "tick": 400,
    "faction_id": "fortifier_01",
    "tech_level_before": 34.65,
    "tech_level_after": 34.71,
    "base_growth": 0.043,               # from economy/population formula
    "convergence_bonus": 0.012,          # from best cooperative partner
    "best_partner": "player_civ",        # null if no cooperative partner
    "best_partner_tech": 41.2,
    "avg_economy": 48.3,
    "avg_population": 62.1,
    "pop_floor_applied": false,          # true if population factor was clamped to floor
    "tier_before": 2,
    "tier_after": 2,                     # changes on tier transition
    "tier_transition": false
}
```

## Integration Points

**Reads from Stage 3:**
- Faction entity (ID, archetype, owned_regions, budget, diplomatic_stances)
- Region state (all four granular fields, composite axes, faction_id)
- World graph (adjacency)
- Attack resolver (to fire betrayal attacks)
- Intent resolver (betrayal attacks enter the intent system)

**Writes to Stage 3 factions:**
- tech_level updates per tick
- diplomatic_stance changes (neutral→cooperative on peace formation, cooperative→hostile on betrayal)
- Tech multiplier modifiers applied to attack_efficiency and resistance_factor

**Writes to Stage 3 regions (indirect):**
- Border friction gating (cooperative/neutral borders skip friction — modifies existing behavior)
- Adjacency bonus gating (cooperative borders contribute adjacency bonus — extends existing behavior)
- Betrayal attack damage (through existing attack resolution pipeline)

**Does NOT touch:**
- Drift formulas (Stage 1 — unchanged, though economy_growth_modifier from tech could optionally scale drift; deferred)
- Event engine internals (Stage 2 — peace formation events use the public queue insertion interface)
- Coherence ledger (Stage 4)
- Unit generation or tactical layer (later stages)

**Config flags:** `ENABLE_DIPLOMACY`. When False, all stances remain at their starting values, no peace forms, no betrayal rolls. `ENABLE_TECHNOLOGY`. When False, tech_level stays at starting value, no growth, no multipliers applied. Default: both True.

## Build Order and Checkpoints

Each numbered step is a mandatory checkpoint. After completing each step, run the specified test, show the output to Westley, and **STOP. Do not continue to the next step until Westley approves.**

> **REMINDER — THIS IS NON-NEGOTIABLE.** Do not evaluate output yourself and decide to proceed. Do not batch multiple steps. Do not "fix" something and continue without showing the fix. Each checkpoint requires Westley's explicit approval before the next step begins. See dev_rules.md "Mandatory Checkpoints — STOP AND WAIT" for the full policy.

---

### A — Technology: Faction Entity Extension and Per-Tick Growth

**A1. Add tech_level to the faction entity and implement per-tick growth.**
Extend the faction data structure with `tech_level` (float, starting value from archetype config range). Create `technology.py` with the growth function:

```
tech_growth = base_tech_rate * (avg_faction_economy / 100) * max(population_floor, avg_faction_population / 100)
```

Where `avg_faction_economy` and `avg_faction_population` are the mean values across all owned regions.

**Test:** Generate a world with 2 factions. Run 200 ticks with ONLY tech growth enabled (no diplomacy, no agents making attacks — just budget accumulation, drift, and tech growth). Print per-faction tech_level at every 25 ticks. Confirm:
- Tech_level grows each tick proportional to average economy
- The faction with higher average economy grows tech faster
- A faction with low population (manually set one faction's regions to population 15) still grows tech but slower — and confirm the population floor clamps (print whether floor was applied each tick)
- Tech_level stays within 0–100 bounds
- Print the per-tick growth breakdown for both factions at tick 50 (avg_economy, avg_population, pop_floor_applied, base_growth)

Run 3 seeds and confirm tech trajectories vary due to drift affecting economy/population differently.

**🛑 CHECKPOINT A1 — STOP and show output to Westley.**

---

### B — Technology: Archetype Multipliers

**B1. Implement per-archetype tech multiplier lookup.**
Create the archetype multiplier table in config. Each archetype has a distribution of the ~20% total budget across three axes: attack_efficiency, defense_efficiency, economy_growth. The multiplier at any tech_level is:

```
modifier = 1.0 + (tech_level / 100) * archetype_axis_weight
```

Where `archetype_axis_weight` is the fraction of the ~20% budget allocated to that axis. Example: Conqueror allocates 0.16 to attack, 0.02 to defense, 0.02 to economy. At tech_level 50: attack_modifier = 1.08, defense_modifier = 1.01, economy_modifier = 1.01.

**Starting archetype multiplier distributions (total ~0.20 per archetype):**
- **Conqueror:** attack 0.16, defense 0.02, economy 0.02
- **Fortifier:** attack 0.03, defense 0.09, economy 0.08
- **Warlord:** attack 0.14, defense 0.04, economy 0.02
- **Opportunist:** attack 0.10, defense 0.05, economy 0.05
- **Schism:** attack 0.12, defense 0.04, economy 0.04
- **player_civilization:** attack 0.06, defense 0.07, economy 0.07
- **breakaway:** attack 0.06, defense 0.08, economy 0.06

**Test:** For each archetype, print the three multipliers at tech_level 0, 25, 50, 75, and 100. Confirm:
- At tech_level 0, all multipliers are 1.0
- At tech_level 100, the total bonus across all three axes sums to ~0.20 per archetype
- The Conqueror's attack multiplier at tech 100 (~1.16) is much higher than their defense (~1.02)
- The Fortifier's defense and economy multipliers are roughly equal and both higher than attack
- The player_civilization has a balanced distribution

**🛑 CHECKPOINT B1 — STOP and show output to Westley.**

**B2. Integrate tech multipliers into attack resolution.**
Modify `attack_resolver.py` so that:
- `effective_attack = attack_strength * ATTACK_EFFICIENCY * attacker_tech_attack_modifier`
- `effective_defense = defender_military * RESISTANCE_FACTOR * defender_tech_defense_modifier`

**Test:** Set up two factions with identical military and budget. Run 100 attack simulations with:
1. Both at tech_level 0 (baseline) — confirm ~50/50 outcome split
2. Attacker at tech_level 100, defender at tech_level 0 — confirm attacker wins more often (~60/40 neighborhood)
3. Both at tech_level 100 but attacker is Conqueror (high attack multiplier), defender is Fortifier (high defense multiplier) — confirm the Conqueror's attack bonus and the Fortifier's defense bonus partially offset
4. Attacker at tech_level 50, defender at tech_level 50, same archetype — confirm ~50/50 (equal tech cancels out)

Print outcome distributions and average net_force for each scenario.

**🛑 CHECKPOINT B2 — STOP and show output to Westley.**

---

### C — Diplomacy: Stance Registry and Border Friction Gating

**C1. Implement the diplomatic stance registry.**
Create `diplomacy.py` with the stance registry: a dict keyed by sorted faction pair tuples, storing stance and non_aggression_ticks. Initialize from a starting stance matrix per archetype pair (config data). Provide query helpers: `is_hostile(a, b)`, `is_cooperative(a, b)`, `is_neutral(a, b)`, `get_stance(a, b)`.

**Starting stance matrix:**
- Conqueror → all others: hostile
- Fortifier → Conqueror: hostile; all others: neutral
- Opportunist → Conqueror: hostile; all others: neutral
- Player_civilization → mirrors what others set toward it
- Breakaway → parent faction: hostile; all others: neutral
- Schism → parent faction: hostile; all others: hostile

**Test:** Generate a world with 4 factions (player_civ, conqueror, fortifier, opportunist). Print the full stance matrix. Confirm:
- Conqueror is hostile to everyone
- Fortifier is neutral toward player_civ and opportunist, hostile toward conqueror
- Player_civ mirrors: hostile to conqueror, neutral to fortifier and opportunist
- All stance queries return correct values

**🛑 CHECKPOINT C1 — STOP and show output to Westley.**

**C2. Gate border friction on hostile stance.**
Modify `border_friction.py` to check diplomatic stance before applying friction. Only hostile borders produce friction. Neutral and cooperative borders produce zero friction.

**Test:** Set up a world where:
- Player_civ borders conqueror (hostile) and fortifier (neutral)
- Run 50 ticks with border friction enabled
- Print per-tick friction on the player's border regions
- Confirm: the region bordering the conqueror receives friction, the region bordering the fortifier receives zero friction
- Flip the fortifier stance to hostile manually, re-run — confirm friction now applies to both borders

**🛑 CHECKPOINT C2 — STOP and show output to Westley.**

**C3. Gate adjacency bonus on cooperative stance.**
Modify the adjacency bonus computation (in drift or wherever it lives) so that:
- Regions bordering **same-faction** regions: adjacency bonus applies (existing behavior)
- Regions bordering **cooperative** faction regions: adjacency bonus applies (new)
- Regions bordering **neutral or hostile** faction regions: no adjacency bonus (existing behavior for hostile, new explicit check for neutral)

**Test:** Set up a player_civ region bordering a fortifier region (neutral stance). Print economy drift with and without adjacency bonus. Confirm no bonus while neutral. Manually flip stance to cooperative. Re-run — confirm adjacency bonus now includes the fortifier's neighboring region. Print the bonus amount and confirm it matches the fortifier region's economy scaled by the existing adjacency formula.

**🛑 CHECKPOINT C3 — STOP and show output to Westley.**

---

### D — Diplomacy: Peace Formation

**D1. Implement the non-aggression timer and Diplomatic Overture event.**
For each neutral border pair, increment `non_aggression_ticks` each tick. Reset to 0 if either faction attacks the other (check intent log or attack log) or if either faction's border region stability drops below a config threshold. When `non_aggression_ticks` reaches the peace formation threshold (config value), fire a Diplomatic Overture check:

```
success_probability = base_peace_probability * economic_compatibility * stability_factor * archetype_disposition
```

- `economic_compatibility` = 1.0 - abs(avg_economy_A - avg_economy_B) / 100 (similar economies cooperate more easily)
- `stability_factor` = min(border_stability_A, border_stability_B) / 100 (both sides must be stable)
- `archetype_disposition` = per-archetype config weight (Fortifier high, Conqueror low)

If the roll succeeds: both factions transition neutral → cooperative. Log the event. If it fails: reset the non_aggression timer and start counting again.

**Test:** Set up player_civ and fortifier as neutral, sharing a border, with stable regions (stability 60+). Run ticks until the non_aggression timer reaches the peace threshold. Print:
- The timer incrementing each tick
- The Diplomatic Overture check when threshold is reached (all probability components, final probability, roll result)
- If successful: confirm stance changed to cooperative, timer reset, event logged
- If failed: confirm timer reset, stance unchanged

Run 50 trials of the Diplomatic Overture roll (at a fixed world state) and print success rate. Confirm it's in a reasonable range (not 0%, not 100%).

Then test the timer reset: set up the same pair but have the conqueror attack the fortifier's border region mid-timer. Confirm the non_aggression_ticks resets to 0 on the tick the attack occurs.

**🛑 CHECKPOINT D1 — STOP and show output to Westley.**

**D2. Verify peace formation doesn't happen between hostile pairs.**
Set up conqueror (hostile to all) adjacent to fortifier. Run 200 ticks. Confirm:
- No non_aggression timer is tracked for the hostile pair (they attack each other, so the timer would reset constantly anyway)
- No Diplomatic Overture fires between hostile factions
- The conqueror remains hostile to everyone throughout

**🛑 CHECKPOINT D2 — STOP and show output to Westley.**

---

### E — Diplomacy: Betrayal

**E1. Implement the per-tick betrayal probability roll.**
Each tick, for every cooperative pair, compute each faction's independent betrayal probability:

```
betrayal_chance = base_betrayal_rate * archetype_betrayal_weight * opportunity_modifier * pressure_modifier
```

- `base_betrayal_rate` — small per-tick config value (starting point: 0.002, meaning ~0.2% base chance per tick)
- `archetype_betrayal_weight` — per-archetype config (Conqueror: 2.5, Fortifier: 0.3, Opportunist: 2.0, Schism: 1.5, player_civ: 0.5, breakaway: 1.0)
- `opportunity_modifier` — `max(1.0, own_border_military / partner_border_military)` — only increases when you're stronger. Capped at a config max (e.g., 3.0).
- `pressure_modifier` — `max(1.0, own_avg_tension / 50)` — only increases when tension is above baseline. Higher tension = more likely to betray.

If the roll succeeds: the betraying faction launches a surprise attack on the partner's weakest border region. Stance flips to hostile. The attack enters the intent system as a normal attack intent (uses existing attack resolution). Log the betrayal event.

**Test:** Set up conqueror and fortifier as cooperative. Set conqueror's border military to 50, fortifier's border military to 20 (opportunity modifier ~2.5). Set conqueror's average tension to 40.

Compute and print the betrayal probability breakdown: base_rate, archetype_weight, opportunity_modifier, pressure_modifier, final_probability.

Then run 10,000 independent betrayal rolls at this probability and print the success rate. Confirm it's in the expected range (e.g., if final probability is 0.01, expect ~100 successes in 10,000 trials, or 1%).

**🛑 CHECKPOINT E1 — STOP and show output to Westley.**

**E2. Verify betrayal consequences.**
Trigger a betrayal (either by seeding a high probability or forcing the roll). Confirm:
- The stance flips from cooperative to hostile immediately
- A surprise attack is launched against the victim's weakest border region
- The attack resolves through the normal attack resolution pipeline
- Border friction activates on the next tick (was zero when cooperative, now applies)
- Adjacency bonus from the former partner stops on the next tick
- Tech convergence from the former partner stops on the next tick
- The betrayal event is logged with all probability components

Print the full state transition: stance before/after, border friction before/after, adjacency bonus before/after, tech convergence before/after.

**🛑 CHECKPOINT E2 — STOP and show output to Westley.**

---

### F — Technology: Convergence in Cooperative Peace

**F1. Implement best-partner-only tech convergence.**
Each tick, for each faction with at least one cooperative partner, find the partner with the highest tech_level. Compute:

```
tech_sharing_bonus = convergence_rate * max(0, best_partner_tech - own_tech) / 100
```

Add the bonus to the faction's tech growth for this tick. If no cooperative partner, bonus is 0. If own tech is higher than all partners, bonus is 0. The `convergence_rate` is a config value.

**Test:** Set up three factions: player_civ (tech 20), fortifier (tech 50), opportunist (tech 40). Player_civ is cooperative with both fortifier and opportunist.

Run 100 ticks with tech growth and convergence enabled. Print per-tick:
- Player_civ's tech_level, base growth, convergence bonus, best partner (should be fortifier at tech 50)
- Confirm convergence bonus is based on fortifier's tech (the higher partner), not opportunist's
- Confirm the bonus shrinks as player_civ's tech approaches fortifier's tech
- Confirm fortifier gets zero convergence bonus from player_civ (fortifier is the higher-tech partner)
- Print tech trajectories for all three factions at ticks 0, 25, 50, 75, 100

**🛑 CHECKPOINT F1 — STOP and show output to Westley.**

**F2. Verify convergence stops on betrayal.**
From the state at the end of F1, trigger a betrayal (fortifier betrays player_civ). Run 20 more ticks. Confirm:
- Player_civ's convergence bonus drops to whatever opportunist provides (lower partner tech, so smaller bonus)
- If player_civ has no remaining cooperative partners after the betrayal, convergence bonus is 0
- Print the transition: convergence bonus on the tick before betrayal vs. the tick after

**🛑 CHECKPOINT F2 — STOP and show output to Westley.**

---

### G — Breakaway Tech Inheritance

**G1. Verify breakaway factions inherit parent tech_level.**
Trigger a revolt that creates a breakaway faction (this may require manually firing a revolt event or using existing Stage 2 revolt templates). Confirm:
- The breakaway faction's tech_level equals the parent faction's tech_level at the tick of creation
- The breakaway then grows (or stagnates) tech independently based on its own economy/population
- Print parent tech at revolt tick, breakaway tech at revolt tick, both tech levels 50 ticks later

If revolts are not yet implemented in the event system, mock this by manually creating a breakaway faction mid-simulation and setting its tech_level to the parent's current value. Confirm the growth diverges afterward.

**🛑 CHECKPOINT G1 — STOP and show output to Westley.**

---

### H — Agent Decision Integration

**H1. Verify agent decisions respect diplomatic stance.**
With 3+ factions and mixed stances (some hostile, some neutral, some cooperative), run the agent decision loop. Confirm:
- Factions do NOT include cooperative or neutral neighbors' regions in their attack candidate pool
- Factions DO include hostile neighbors' regions in their attack candidate pool
- A faction with only cooperative/neutral neighbors has no attack candidates (accumulates or reinforces only)
- Print the candidate pool for each faction's decision on a representative tick, showing which regions were included/excluded and why

**🛑 CHECKPOINT H1 — STOP and show output to Westley.**

**H2. Verify betrayal creates new attack opportunities.**
After a betrayal flips a cooperative pair to hostile, confirm:
- The betrayed faction's regions now appear in the betrayer's attack candidate pool on the next tick
- Border friction begins applying
- The betrayed faction's agent may shift toward reinforcing the newly hostile border
- Print decision logs for both factions on the tick before and after the betrayal

**🛑 CHECKPOINT H2 — STOP and show output to Westley.**

---

### I — Full Integration Test

**I1. Run a full simulation with 4 factions over 500 ticks.**
Generate a world with 4 factions (player_civ, conqueror, fortifier, opportunist) from an extended starting template. Run 500 ticks with everything enabled: drift, oscillation, Stage 2 events, faction agents, border friction, diplomacy, technology. Print a comprehensive summary:

- **Diplomatic timeline:** stance changes over time (when did peace form? when did betrayal happen?)
- **Tech timeline:** per-faction tech_level at ticks 0, 100, 200, 300, 400, 500
- **Tech tier transitions:** any faction that crossed a tier boundary, which tick, which tier
- **Territory timeline:** region ownership at ticks 0, 100, 200, 300, 400, 500
- **Budget timeline:** per-faction budget at every 100 ticks
- **Action summary:** per-faction counts of each action type
- **Attack log:** every attack with tick, attacker, defender, outcome, was it a betrayal attack
- **Conquest log:** every conquest with tick, region, previous owner, new owner
- **Peace formation log:** every Diplomatic Overture (success and failure)
- **Betrayal log:** every betrayal with all probability components
- **Convergence summary:** which factions benefited from tech convergence and for how long

Confirm:
- At least one peace forms during 500 ticks (if not, base_peace_probability or non_aggression_threshold needs tuning)
- At least one betrayal occurs during 500 ticks (if not, base_betrayal_rate needs tuning)
- Tech_level increases for factions with healthy economies
- Factions in cooperative relationships show higher tech growth than isolated factions (convergence visible)
- The conqueror's tech attack multiplier produces visibly better attack outcomes at higher tech
- Border friction correctly applies only on hostile borders
- Adjacency bonus correctly applies on cooperative borders
- No degenerate states: no faction's tech at 100 within 200 ticks (growth is too fast), no faction permanently stuck at 0 (growth is too slow)
- The simulation tells a recognizable story: factions expand, some form peace, cooperation produces tech and economic benefits, betrayal disrupts the peace, the world keeps moving

**🛑 CHECKPOINT I1 — STOP and show output to Westley.**

**I2. Run 5 seeds and confirm stochastic divergence.**
Run the same 500-tick simulation with 5 different random seeds. Print per-seed summary: final diplomatic state between all pairs, final tech_levels, total peace formations, total betrayals, total conquests, which faction controls the most territory. Confirm genuine divergence — different seeds produce different diplomatic histories.

**🛑 CHECKPOINT I2 — STOP and show output to Westley.**

**I3. Run a 1000-tick long-run test.**
Extend to 1000 ticks. Confirm:
- Tech_level progression is gradual (no faction hits 100 before tick 500 unless tuning says otherwise)
- Peace/betrayal cycles occur (cooperative relationships form, some break, some persist)
- Tech convergence produces visible narrowing of tech gaps between cooperative factions
- Tier transitions occur for at least one faction (tech crosses 33 or 67 boundary)
- No degenerate states at this timescale
- Print summary at ticks 0, 250, 500, 750, 1000

**🛑 CHECKPOINT I3 — STOP and show output to Westley.**

---

## Config Values — Starting Points

```python
# ── Technology (Stage 3.5 A) ──────────────────────────────────────────────────

ENABLE_TECHNOLOGY = True

# Per-tick base growth rate. This is the primary tuning knob for tech speed.
# At base_tech_rate 0.05, a faction with avg economy 50 and avg population 60
# grows at 0.05 * 0.5 * 0.6 = 0.015 per tick, reaching tech 15 at tick 1000.
# Adjust upward if tech progression feels too slow.
BASE_TECH_RATE = 0.05

# Population floor for tech growth formula.
# Prevents double-penalty death trap for post-conquest factions.
TECH_POPULATION_FLOOR = 0.3

# Tech convergence rate for cooperative partners.
# At 0.03 with a tech gap of 30, bonus = 0.03 * 30/100 = 0.009/tick.
TECH_CONVERGENCE_RATE = 0.03

# Starting tech_level ranges per archetype (rolled at creation).
ARCHETYPE_STARTING_TECH = {
    "conqueror": (5, 15),
    "fortifier": (10, 20),
    "warlord": (5, 10),
    "opportunist": (8, 15),
    "schism": (0, 0),       # inherits parent tech, but if spawned fresh: 0
    "player_civilization": (10, 20),
    "breakaway": (0, 0),    # always inherits parent tech
}

# Per-archetype multiplier distributions (total ~0.20 per archetype).
# Format: {archetype: {"attack": weight, "defense": weight, "economy": weight}}
ARCHETYPE_TECH_MULTIPLIERS = {
    "conqueror":            {"attack": 0.16, "defense": 0.02, "economy": 0.02},
    "fortifier":            {"attack": 0.03, "defense": 0.09, "economy": 0.08},
    "warlord":              {"attack": 0.14, "defense": 0.04, "economy": 0.02},
    "opportunist":          {"attack": 0.10, "defense": 0.05, "economy": 0.05},
    "schism":               {"attack": 0.12, "defense": 0.04, "economy": 0.04},
    "player_civilization":  {"attack": 0.06, "defense": 0.07, "economy": 0.07},
    "breakaway":            {"attack": 0.06, "defense": 0.08, "economy": 0.06},
}

# Tech tier boundaries (uniform, 3 tiers).
TECH_TIER_BOUNDARIES = [0, 34, 67]  # tier 1: 0–33, tier 2: 34–66, tier 3: 67–100

# ── Diplomacy (Stage 3.5 C–E) ────────────────────────────────────────────────

ENABLE_DIPLOMACY = True

# Non-aggression timer threshold (ticks of sustained peace before overture).
PEACE_FORMATION_THRESHOLD = 80

# Stability threshold — both factions' border regions must be above this.
PEACE_STABILITY_THRESHOLD = 35.0

# Base probability that a Diplomatic Overture succeeds.
PEACE_BASE_PROBABILITY = 0.5

# Per-archetype disposition toward forming peace (multiplier on peace probability).
ARCHETYPE_PEACE_DISPOSITION = {
    "conqueror": 0.1,        # almost never seeks peace
    "fortifier": 2.0,        # actively seeks peace
    "warlord": 0.2,          # rarely seeks peace
    "opportunist": 1.0,      # neutral
    "schism": 0.3,           # ideologically opposed to cooperation
    "player_civilization": 1.5,  # somewhat inclined toward peace
    "breakaway": 0.8,        # slightly cautious
}

# Base betrayal rate per tick per cooperative pair.
BASE_BETRAYAL_RATE = 0.002

# Per-archetype betrayal weight (multiplier on betrayal probability).
ARCHETYPE_BETRAYAL_WEIGHT = {
    "conqueror": 2.5,
    "fortifier": 0.3,
    "warlord": 2.0,
    "opportunist": 2.0,
    "schism": 1.5,
    "player_civilization": 0.5,
    "breakaway": 1.0,
}

# Cap on opportunity modifier (prevents extreme probabilities).
BETRAYAL_OPPORTUNITY_CAP = 3.0

# Starting diplomatic stance matrix.
# Format: {(archetype_a, archetype_b): stance}
# Pairs not listed default to "neutral".
STARTING_STANCE_OVERRIDES = {
    ("conqueror", "player_civilization"): "hostile",
    ("conqueror", "fortifier"): "hostile",
    ("conqueror", "opportunist"): "hostile",
    ("conqueror", "warlord"): "hostile",
    ("conqueror", "schism"): "hostile",
    ("conqueror", "breakaway"): "hostile",
    ("schism", "player_civilization"): "hostile",
    ("schism", "fortifier"): "hostile",
    ("schism", "opportunist"): "hostile",
    ("schism", "warlord"): "hostile",
    # All other pairs default to neutral
}
```

---

## Done Condition

Run the Stage 3.5 simulation (500+ ticks, 5 seeds, 4 factions) and confirm:
1. Tech_level grows per tick based on economy with population floor — declining factions stagnate, thriving factions advance
2. Archetype tech multipliers produce ~20% max advantage asymmetrically distributed per archetype identity
3. Tech multipliers visibly affect attack outcomes (~60/40 neighborhood at maximum tech gap)
4. Diplomatic stances correctly gate border friction (hostile only), adjacency bonus (same-faction and cooperative only), and attack candidate pools (hostile only)
5. Peace forms through sustained non-aggression + stability + Diplomatic Overture probability roll
6. Betrayal fires per-tick with probability scaled by archetype, opportunity, and internal pressure
7. Betrayal produces a surprise attack + stance flip to hostile + immediate loss of cooperative benefits
8. Tech convergence accelerates the lower-tech partner in cooperative relationships (best-partner-only)
9. Breakaway factions inherit parent tech_level at creation
10. Agent decisions respect diplomatic stance (no attacking cooperative/neutral neighbors)
11. Different seeds produce different diplomatic and technological histories
12. Long-run behavior (1000 ticks) is coherent — tech progression is gradual, peace/betrayal cycles emerge, no degenerate states

Westley signs off on the full integration test output before Stage 4 begins.

## Files Created
*(Filled in after implementation)*
