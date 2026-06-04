# Stage 0 — Revision: Multi-Faction Simulation

## What This Document Is

This is a **revision spec** for Stage 0. The original Stage 0 spec (Groups A–E) has been implemented. This document describes what needs to change and what needs to be added to upgrade the simulation from a single-antagonist continuous-pressure model to a multi-faction free-for-all galaxy with discrete attacks.

**Read before starting:**
- `game_bible.md` — specifically "Multi-Faction Agent Decision Model," "The Antagonist System" (updated), the revised tick resolution sequence, the revised military drift formula, and "Expansion Packs and Monetization" for the era-agnostic architecture requirement
- `dev_rules.md` — all five development principles
- The original `stage_0_spec.md` — for context on what's already built

**Key design principle for this revision:** The simulation engine must remain **era-agnostic**. No sci-fi-specific concepts in the simulation code. The engine speaks in abstract types: "faction," "region," "military strength," "attack event" — not "fleet," "star system," "invasion." This is Sacred Principle #3 and the foundation of the game's commercial model (skeleton/skin architecture for expansion packs). Every module built or modified in this revision must use abstract vocabulary.

---

## Development Methodology

Same as the original spec: **small, sequential, provable increments.** Each step adds one thing. After each step, run and verify. If output is wrong, fix before moving on. Integration is a separate, deliberate step.

The existing simulation (drift, events, composites, coherence ledger, galaxy generation) is the foundation. We are modifying and extending, not rewriting from scratch. Each change is surgical and verified against the existing system's behavior.

---

## What Already Exists (Do Not Rebuild)

These systems are implemented and working from the original Stage 0:

- **Region model** — 4 granular fields, 2 composite axes, recomputation
- **Galaxy generation** — isolated start template, adjacency graph
- **Passive drift** — all 4 field drift formulas (military, economy, tension, population)
- **Event system** — templates, threshold triggers with noise, chain spawns, collision resolution, mutual exclusion, pending queue
- **Antagonist agent** — single agent with budget, attractiveness scoring, continuous pressure distribution
- **Coherence ledger** — event log, antagonist log, state snapshots
- **Tick loop** — orchestrates the resolution sequence
- **Config** — all tuning values centralized

---

## What Needs to Change

### Summary of Changes

1. **Region model** gains a `faction_id` field
2. **Military drift formula** gains a recruitment term (recovery under good conditions)
3. **Antagonist module** is replaced by a **faction agent module** — multiple independent agents, discrete attacks instead of continuous pressure
4. **Tick loop** gains a border friction step and runs N faction agents instead of one
5. **Event system** gains new event types: Attack, Conquest, Revolt (with faction creation)
6. **Galaxy generation** templates define starting NPC factions
7. **Coherence ledger** gains faction-related entries
8. **Config** gains all new tuning values

---

## Build Steps

### Group I — Faction Foundation (Prove factions exist)

> Prerequisite: Groups A–E complete and working.

**Step I1: Faction registry.**
Create `faction.py`. A Faction has: ID, name, archetype tag (e.g., "conqueror", "player_civilization"), resource budget, budget growth rate, and faction-level modifiers (dict of field → bonus, e.g., {"military": 0.02} for a militaristic faction). The faction registry is a dict of factions keyed by ID. Add a method to compute a faction's total economic output and capacity (sum across owned regions).
- **Prove:** Create 2 factions, print their state. Verify budget starts at configured value, modifiers are accessible.

**Step I2: Region faction ownership.**
Add `faction_id` to the Region model. Update galaxy generation: all player civilization regions get faction_id "player". Add a method to query all regions owned by a given faction. Add a method to query which factions border a given faction (factions that own regions adjacent to regions the queried faction owns).
- **Prove:** Generate a galaxy, print each region with its faction_id. Query regions by faction. Query bordering factions. Verify results match the template topology.

**Step I3: Add a starting NPC faction to the isolated start template.**
Extend the isolated start template: add 1–2 regions owned by a "conqueror" faction on the far edge of the galaxy (beyond the empty regions). These regions start with moderate field values. The conqueror faction starts with a small budget.
- **Prove:** Generate the galaxy, print all regions with faction ownership. Verify the player's civilization and the conqueror each own their expected regions. Verify they don't overlap. Verify there are empty/neutral regions between them.

**Step I4: Faction-level drift modifiers.**
Modify `apply_drift` to check the owning faction's modifiers and apply them as small bonuses to the relevant drift terms. A militaristic faction's regions get a small military drift bonus. An economically focused faction gets an economy drift bonus. The player's civilization has no special modifiers (neutral).
- **Prove:** Run two identical regions side by side — one owned by a militaristic faction, one by a neutral faction. After 50 ticks of drift only, verify the militaristic faction's region has slightly higher military. The difference should be visible but not dominant.

### Group J — Military Recovery and Border Friction (Prove defense works)

**Step J1: Military recruitment drift term.**
Modify the military strength drift formula to add the recruitment term from the bible:
```
if economy > recruitment_threshold and tension < recruitment_tension_cap:
    recruitment = recruitment_rate * (economy / 100) * (1 - tension / 100)
```
Add `recruitment_threshold`, `recruitment_tension_cap`, and `recruitment_rate` to config.
- **Prove:** Run a region with strong economy and low tension for 50 ticks. Verify military grows slowly (recruitment active). Run a region with weak economy — verify military still decays (recruitment doesn't fire). Run a region with high tension — verify recruitment is suppressed. Run a region with moderate economy — verify recruitment is slower than with strong economy. The recruitment rate should be slow enough that recovery takes many ticks.

**Step J2: Border friction.**
Add border friction to the tick loop (new step 4 in the 7-step sequence). For each region, check if any adjacent regions belong to a hostile faction. If so, apply a small per-tick increase to factional tension and a small per-tick decrease to economic output. Friction amounts are config values. Only applies through border-type edges (or all edges if typed edges aren't implemented yet).
- **Prove:** Run a region with no hostile neighbors for 50 ticks — verify no friction effects. Run the same region with a hostile neighbor — verify tension is slightly higher and economy slightly lower after 50 ticks. The difference should be subtle — border friction is background stress, not active damage.

### Group K — Faction Agent Decisions (Prove factions think)

**Step K1: Budget accumulation.**
Each tick, each faction's budget grows based on the total economic output of its owned regions. Growth formula: `budget += sum(region.economy for region in owned_regions) * budget_growth_rate`. Add `budget_growth_rate` to config (per archetype or global).
- **Prove:** Run 50 ticks with two factions (player + conqueror), no attacks. Print budget growth per tick. Verify the faction with higher total economy accumulates budget faster. Verify budgets grow monotonically.

**Step K2: Attack decision — threshold and target selection.**
Add the attack decision to the faction agent. Each tick, if budget exceeds `attack_threshold` (config value), the agent evaluates potential targets. For the Conqueror archetype, implement the mixed attractiveness scoring: `score = (w_weakness * (100 - target_military) / 100) + (w_value * (target_economy + target_population) / 200)`. The weights are config values. The agent selects the highest-scoring target from adjacent enemy regions.
- **Prove:** Set up a conqueror faction with budget above threshold, adjacent to two player regions — one with low military/high economy, one with high military/low economy. Verify the scoring selects the expected target. Test with equal scores — verify selection still works (break ties by, e.g., lower region ID or random). Test with budget below threshold — verify no attack fires.

**Step K3: Reinforce decision.**
If the agent doesn't attack, it checks for threatened borders — owned regions adjacent to hostile factions where the agent's military is lower than the neighbor's. If found, the agent can spend a portion of budget to boost that region's military directly. Reinforce amount is scaled by budget spent, with a config efficiency rate.
- **Prove:** Set up a faction with a weak border region adjacent to a strong enemy. Verify the agent reinforces that region. Verify the budget decreases by the spent amount. Verify the region's military increases by the expected amount.

**Step K4: Player civilization agent.**
Implement the player's civilization agent using the same framework. Default behavior: never attacks (or attacks only with overwhelming advantage — configurable), always reinforces the weakest border. This is the conservative defensive posture from the bible.
- **Prove:** Run 100 ticks with player civ + conqueror. Verify the player civ accumulates budget and spends it on reinforcements, not attacks. Verify the conqueror accumulates and eventually attacks.

**Step K5: Wire faction agents into the tick loop.**
Replace the old single-antagonist step with a loop over all factions. Each faction's agent runs in the faction agent step (step 3 of the tick sequence). Remove the old antagonist pressure application.
- **Prove:** Run 200 ticks with player civ + conqueror. Print per-tick: faction budgets, decisions (accumulate/attack/reinforce), and targets. Verify the pattern: early ticks are accumulation, then factions start acting. The conqueror should attack player regions. The player civ should reinforce. No crashes, no stale references to the old antagonist system.

### Group L — Attack Resolution (Prove battles happen)

**Step L1: Attack event.**
Create the Attack event type. When a faction agent decides to attack, it spawns an Attack event in the pending queue targeting the enemy region for the current tick (immediate resolution). The event carries: attacker faction ID, attack strength (committed budget portion), and the attacker's archetype tag.
- **Prove:** Trigger an attack manually. Verify the event appears in the pending queue and fires on the expected tick.

**Step L2: Attack resolution with resistance.**
Implement the attack resolution formula from the bible:
```
effective_attack = attack_strength * attack_efficiency
effective_defense = defender_military * resistance_factor
net_force = effective_attack - effective_defense
```
Outcomes: strongly positive net_force → heavy damage to defender (military drops significantly, economy disrupted, tension spikes). Near zero → both sides take moderate damage (attacker loses budget, defender takes some military damage). Strongly negative → attack repelled (attacker loses committed budget, defender takes minor damage). Add a stochastic modifier — roll a multiplier (e.g., 0.7–1.3) on the net_force so evenly matched fights can go either way. All coefficients in config.
- **Prove:** Test three scenarios: overwhelming attack (strength >> defense), evenly matched (strength ≈ defense), and failed attack (strength << defense). Verify each produces the expected outcome pattern. Run the even match 10 times — verify stochastic variation produces different outcomes.

**Step L3: Conquest event.**
After an attack resolves, if the defender's military drops below `conquest_threshold` (config value, near zero), fire a Conquest event: transfer region ownership to the attacking faction. Apply conquest consequences: tension spikes (config amount), population drops slightly, economy disrupted. Log the conquest in the coherence ledger. The Conquest event can spawn follow-up chains (resistance movement, refugee event in adjacent friendly regions).
- **Prove:** Set up a weak defender region (military ~10) and a strong attacker. Run the attack. Verify the region changes faction ownership. Verify tension spiked, economy dropped. Verify the coherence ledger recorded the conquest. Verify follow-up events are queued.

**Step L4: Revolt with faction creation.**
Modify the existing revolt event. When a revolt event fires and succeeds, roll a success rate between ~10–70% (config range). The breakaway faction "steals" that percentage of the region's military and economy. Create a new faction entity in the registry with archetype "breakaway". Transfer region ownership to the new faction. The new faction's starting budget is zero (it just spent everything on the revolt).
- **Prove:** Trigger a revolt in a region with military=60, economy=50. If success rate rolls 40%, verify the original region drops to military=36, economy=30 and the new faction's region has military=24, economy=20. Verify the new faction appears in the registry. Verify the new faction's agent runs on subsequent ticks.

### Group M — Full Multi-Faction Integration Test (Prove the galaxy is a free-for-all)

**Step M1: The 500-tick multi-faction test.**
Run the full simulation (drift with recruitment, events, multi-faction agents with attacks, border friction, conquest, coherence ledger) for 500 ticks on the updated isolated start template (player civ + conqueror). Print a comprehensive summary:
- Per-faction territory count over time (how many regions each faction owns)
- Total attacks launched by each faction, with outcomes (repelled/contested/breakthrough/conquest)
- Conquests — which regions changed hands and when
- Revolts — any breakaway factions formed, their fate
- Per-region field trajectories (start → end, min/max)
- Longest event chain
- Faction budget trajectories

**Prove:** The output tells a story of conflict. The conqueror attacks player regions. The player civ defends. Territory changes hands. Maybe a revolt creates a third faction. The galaxy is contested, not static. Neither side instantly collapses — military recovery and resistance mechanics keep the fight going. The simulation didn't crash, produce NaN, or get stuck in a loop.

**Step M2: Multi-faction stress test.**
Add a second NPC faction (e.g., a "plague" archetype or a second conqueror on the opposite side of the galaxy). Run 500 ticks with 3+ factions.
- **Prove:** Factions fight each other, not just the player. The conqueror might attack the third faction. Two factions might compete for the same neutral region. The galaxy is a genuine free-for-all. Print inter-faction conflict statistics: which factions fought which, total attacks between each pair.

**Step M3: Stochastic consistency test.**
Run the multi-faction simulation 5 times with different seeds. Compare trajectories.
- **Prove:** No two runs are identical. All runs are plausible. The range of outcomes includes: the player dominating, the conqueror dominating, a stalemate, and a breakaway faction emerging as a surprise power. Not all of these need to happen in 5 runs, but the possibility should be visible in the variance.

---

## Input/Output Shapes (New/Modified)

**Faction entity:**
```python
{
    "id": "faction_conqueror",
    "name": "The Conqueror",
    "archetype": "conqueror",
    "budget": 12.5,
    "budget_growth_rate": 0.05,
    "modifiers": {"military": 0.02},
    "diplomatic_stance": {
        "player": "hostile",
        "faction_breakaway_1": "hostile"
    }
}
```

**Region (updated — adds faction_id):**
```python
{
    "id": "region_0",
    "name": "Heartworld",
    "tier": "home",
    "faction_id": "player",
    "fields": {
        "military": 65.0,
        "economy": 70.0,
        "tension": 15.0,
        "population": 50.0
    },
    "composites": {
        "stability": 72.3,
        "capacity": 61.8
    }
}
```

**Attack event:**
```python
{
    "type": "attack",
    "attacker_faction": "faction_conqueror",
    "target_region": "region_1",
    "attack_strength": 8.5,
    "attacker_archetype": "conqueror"
}
```

**Attack resolution result (logged to coherence ledger):**
```python
{
    "type": "attack_result",
    "tick": 142,
    "attacker_faction": "faction_conqueror",
    "defender_faction": "player",
    "target_region": "region_1",
    "attack_strength": 8.5,
    "defender_military_before": 45.0,
    "net_force": 2.3,
    "outcome": "contested",
    "defender_military_after": 38.2,
    "attacker_budget_spent": 8.5,
    "conquest": false
}
```

**Conquest event (logged to coherence ledger):**
```python
{
    "type": "conquest",
    "tick": 187,
    "attacker_faction": "faction_conqueror",
    "defender_faction": "player",
    "region": "region_2",
    "tension_spike": 25,
    "population_loss": 5,
    "economy_disruption": 15,
    "follow_up_events": ["resistance_movement@tick_192"]
}
```

**Revolt result (logged to coherence ledger):**
```python
{
    "type": "revolt",
    "tick": 203,
    "region": "region_1",
    "original_faction": "player",
    "new_faction": "faction_breakaway_1",
    "success_rate": 0.42,
    "military_stolen": 18.9,
    "economy_stolen": 12.6
}
```

---

## Config Additions

All new tuning values added to `config.py`:

```python
# Military recruitment
RECRUITMENT_THRESHOLD = 50        # Economy must be above this for recruitment
RECRUITMENT_TENSION_CAP = 40      # Tension must be below this for recruitment
RECRUITMENT_RATE = 0.03           # Base recruitment rate per tick

# Border friction
BORDER_FRICTION_TENSION = 0.5     # Per-tick tension increase from hostile border
BORDER_FRICTION_ECONOMY = 0.3     # Per-tick economy decrease from hostile border

# Faction agent
ATTACK_THRESHOLD = 10.0           # Minimum budget to consider attacking
BUDGET_GROWTH_RATE = 0.05         # Budget growth per unit of total economy per tick
REINFORCE_EFFICIENCY = 0.5        # Budget-to-military conversion rate for reinforcements

# Attack resolution
ATTACK_EFFICIENCY = 1.0           # Multiplier on committed attack strength
RESISTANCE_FACTOR = 0.8           # How much defender military reduces attack damage
STOCHASTIC_RANGE = [0.7, 1.3]    # Multiplier range for attack resolution randomness
CONQUEST_THRESHOLD = 5.0          # Defender military below this triggers conquest

# Conquest consequences
CONQUEST_TENSION_SPIKE = 25.0     # Tension added to conquered region
CONQUEST_POPULATION_LOSS = 5.0    # Population lost in conquest
CONQUEST_ECONOMY_DISRUPTION = 15.0 # Economy lost in conquest

# Revolt
REVOLT_SUCCESS_RANGE = [0.10, 0.70]  # Min/max success rate for revolt strength theft

# Conqueror attractiveness weights
CONQUEROR_WEAKNESS_WEIGHT = 0.6   # Weight on military weakness in scoring
CONQUEROR_VALUE_WEIGHT = 0.4      # Weight on strategic value in scoring
```

---

## Integration Points

This revision modifies the existing tick loop. The new 7-step tick resolution sequence:

1. Process pending event queue (unchanged)
2. Evaluate fresh event triggers (unchanged)
3. **Run all faction agents** (CHANGED — was single antagonist, now iterates N factions)
4. **Apply border friction** (NEW)
5. Apply passive drift (MODIFIED — military drift now includes recruitment term)
6. Recompute composite axes (unchanged)
7. Log everything (MODIFIED — logs faction agent actions, attack results, conquests)

**Config flags (updated):**
- `config.ENABLE_EVENTS` — unchanged
- `config.ENABLE_FACTIONS` — if False, no faction agents run. Drift and events still work. Replaces the old ENABLE_ANTAGONIST.
- `config.ENABLE_TYPED_EDGES` — unchanged
- `config.ENABLE_NEIGHBOR_DRIFT` — unchanged
- `config.ENABLE_BORDER_FRICTION` — if False, no border friction applied
- `config.ENABLE_RECRUITMENT` — if False, military drift uses decay-only formula (original behavior)

---

## Future Stage Dependencies

Carried forward from the original spec, plus new items:

**Civilization-wide aggregates (needed by Stage 2+).** Sum of region fields across a faction's territory. Now naturally needed for faction budget growth computation — already implemented in this revision.

**Tech level / era tracking (needed by Stage 4+).** Unchanged from original spec. No sci-fi-specific concepts in the simulation.

**Faction diplomacy (needed by Stage 3+).** The faction entity has a `diplomatic_stance` field, but it's not used in Stage 0 beyond "hostile" meaning "will attack." Future stages need: neutral stance (factions ignore each other), alliance (share borders peacefully, trade benefits), and dynamic stance changes (events that shift diplomacy).

**Non-territorial archetypes (needed by Stage 2+).** The Exhaustion, Plague, Phenomenon, and Singularity don't own territory and don't use the standard attack model. Their agent behavior is an open design question. For Stage 0, only territorial archetypes (conqueror, player_civilization, breakaway) are implemented.

**Lineage tracking in the coherence ledger (needed by Stage 3).** Unchanged from original spec.

**Expansion events (needed by Stage 2+).** Unchanged — galaxy model supports runtime region/edge addition.

**Era-agnostic vocabulary (always).** Every module must use abstract types. No sci-fi terms in simulation code. The theme pack layer maps abstractions to era-specific content — that layer doesn't exist yet and doesn't need to, but the simulation must not make it hard to add.

---

## Done Condition

**The simulation passes all three tests in Group M:**

1. **500-tick multi-faction test (M1):** Player civ + conqueror produce a contested galaxy. Attacks happen. Territory changes hands. Revolts may create new factions. Neither side instantly collapses. The story is readable.

2. **Multi-faction stress test (M2):** 3+ factions produce a genuine free-for-all. Factions fight each other, not just the player. Inter-faction conflict statistics show multiple faction pairs in conflict.

3. **Stochastic consistency test (M3):** Five runs with different seeds produce five different plausible stories. The range of outcomes demonstrates genuine strategic uncertainty.

**Westley reads the output and says: "Yes, this galaxy has real conflicts." That is the gate.**

---

## Files Modified / Created

*Filled in after implementation.*

| File | Change Type | Purpose | Status |
|------|-------------|---------|--------|
| `config.py` | Modified | Add all new tuning values | |
| `region.py` | Modified | Add faction_id field | |
| `drift.py` | Modified | Add military recruitment term | |
| `faction.py` | Created | Faction entity, registry, agent decision model | |
| `galaxy.py` | Modified | Templates include NPC factions | |
| `events.py` | Modified | Add Attack, Conquest, Revolt event types | |
| `tick.py` | Modified | 7-step sequence, multi-faction agent loop, border friction | |
| `coherence_ledger.py` | Modified | Faction-related entry types | |
| `antagonist.py` | Deleted | Replaced by faction.py | |
| `test_stage_0_rev.py` | Created | Group M integration tests | |
