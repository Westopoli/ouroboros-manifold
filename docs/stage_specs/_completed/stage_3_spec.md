# Stage 3 — Faction Agents and Territorial Conflict

## Goal
Prove that faction agents accumulate budget, evaluate targets, launch attacks, colonize uninhabited regions, and reinforce threatened borders — producing territorial conflict with conquest, overextension dynamics, and genuine stochastic divergence across seeds. Two factions (the Conqueror archetype and the player's civilization) compete in a world where the Stage 2 event chain system runs underneath, creating emergent interactions between civilizational crises and military action.

## Context
**Read in game_bible.md (v1.11):** "The Simulation Backbone" section, specifically:
- Multi-Faction Agent Decision Model (faction entity, budget accumulation with maintenance cost, four-decision agent, scored selection with archetype weights, reinforce mechanics, expected outcome evaluation, attractiveness scoring)
- Tick Resolution Sequence (all 7 steps are now relevant — Stage 3 adds steps 3 and 4)
- Attack event resolution (resistance mechanic, three outcome bands with scaled damage, stochastic modifier, breakthrough/contested/repelled)
- Conquest events (ownership transfer, economy floor bypass, consequences enter event queue)
- Uninhabited Region Mechanics (colonization as agent decision, cost, starter field values, contested resolution)
- Diplomatic Stance (hostile/neutral/allied, mechanical effects — Stage 3 uses hostile only)
- Border friction (scales with hostile neighbor military strength)
- Agent information model (perfect neighbor visibility for simulation agents)

**Era-agnostic naming:** Per Sacred Design Principle #3, the engine uses abstract mechanical vocabulary only. All code, config, and log output must use abstract terms. "faction" not "empire," "region" not "star system," "force" not "fleet," "unit" not "ship." The bible uses themed names for readability in prose — the spec's names are authoritative for implementation.

**Builds on:** Stage 1 (world graph, multi-region drift, oscillation, adjacency bonus) and Stage 2 (event chain architecture, threshold triggers, pending queue, collision resolution, economy floor). Stage 3 adds faction agents (tick step 3) and border friction (tick step 4) to the existing tick loop.

**What Stage 3 does NOT include:** Coherence ledger (Stage 4), chronicle generation (Stage 5+), mission system (later stages), non-Conqueror archetypes (later stages), diplomatic stance changes (event library concern), breakaway factions from revolts (event library concern). Stage 3 tests with exactly two factions: one Conqueror, one player civilization. Both start hostile and remain hostile throughout.

## What to Build

### Files to create:

**`faction_agent.py`** — The faction entity model and agent decision system. Contains:
- Faction data structure (ID, archetype, owned_regions, budget, attack_confidence, diplomatic_stances, archetype config)
- Budget accumulation (economy minus maintenance, scaled by archetype growth rate)
- Reinforce evaluator (threat score, threat ratio, spending curve, overreaction variance with tension modifier, target selection with probabilistic rotation)
- Attack/colonize evaluator (shared candidate pool, attractiveness scoring, expected outcome check)
- Scored decision selector (normalize raw scores, apply archetype weights, pick winner)
- Per-tick decision log (all four raw scores, weighted scores, winning action, budget before/after)

**`attack_resolver.py`** — Attack event resolution, separate from the agent decision logic. Contains:
- Attack resolution formula (effective_attack, effective_defense, net_force with stochastic modifier)
- Outcome band classification (breakthrough, contested, repelled)
- Scaled damage computation per outcome band
- Conquest trigger check (defender military below conquest threshold)
- Conquest event creation (inserted into Stage 2 pending event queue for next-tick processing)
- Attack event logging (attacker, defender, committed budget, net_force, outcome band, damage applied)

**`border_friction.py`** — Border friction system. Contains:
- Per-region friction calculation (iterate hostile border edges, scale by hostile neighbor military)
- Friction application (tension increase, economy drag per hostile edge)

**`conquest_templates.py`** — Hand-authored conquest consequence event templates for the Stage 2 event queue. Contains:
- Conquest consequence template (tension spike, population drop, economy disruption — with economy floor bypass flag)
- 1–2 conquest follow-up chain templates (post-conquest instability, representing resistance/unrest in conquered territory)

**`test_stage3.py`** — Test harness for Stage 3. Generates a world with two factions from the isolated start template (player civilization on one side, Conqueror on the other, separated by uninhabited buffer). Runs 500+ ticks. Prints faction summaries, territory changes, budget history, attack logs, and per-tick decision logs.

**Config additions to `config.py`** — All new config values for Stage 3. Feature flag: `ENABLE_FACTION_AGENTS = True`, `ENABLE_BORDER_FRICTION = True`.

## Input/Output Shapes

### Faction Entity (data structure in faction_agent.py):
```python
{
    "faction_id": "conqueror_01",
    "archetype": "conqueror",
    "owned_regions": ["region_conq_home", "region_conq_frontier"],
    "budget": 45.0,
    "attack_confidence": 14.5,       # rolled at creation from archetype range
    "diplomatic_stances": {
        "player_civ": "hostile"
    },
    "config": {
        "archetype_growth_rate": 0.03,
        "attack_weight": 0.8,
        "expand_weight": 0.7,
        "defend_weight": 0.2,
        "commit_fraction": 0.70,
        "confidence_range": (12, 18),
        "reinforce_threat_threshold": 1.8,   # high — rarely reinforces
        # ... other archetype-specific config
    }
}
```

### Per-Tick Decision Log Entry (output of faction_agent.py):
```python
{
    "tick": 203,
    "faction_id": "conqueror_01",
    "budget_before": 45.0,
    "budget_after": 13.5,
    "budget_growth_this_tick": 1.8,
    "maintenance_total": 16.0,        # region_maintenance_cost * num_regions
    "gross_economy": 52.0,            # sum of all owned region economy
    "net_economy": 36.0,              # gross - maintenance
    "scores": {
        "attack": {
            "raw": 18.3,              # best expected_net_force
            "normalized": 0.72,
            "weighted": 0.576,        # normalized * attack_weight
            "target": "region_player_frontier_1",
            "commit_amount": 31.5
        },
        "colonize": {
            "raw": 0.45,             # best attractiveness score
            "normalized": 0.45,
            "weighted": 0.315,
            "target": "region_empty_3"
        },
        "reinforce": {
            "raw": 1.2,             # highest threat ratio
            "normalized": 0.60,
            "weighted": 0.12,
            "target": "region_conq_frontier"
        }
    },
    "action": "attack",
    "action_detail": {
        "target": "region_player_frontier_1",
        "committed_budget": 31.5,
        "expected_net": 18.3
    }
}
```

### Attack Event Log Entry (output of attack_resolver.py):
```python
{
    "event_id": "attack_evt_0012",
    "tick": 203,
    "attacker_faction": "conqueror_01",
    "defender_faction": "player_civ",
    "target_region": "region_player_frontier_1",
    "attack_strength": 31.5,
    "effective_attack": 22.05,        # attack_strength * attack_efficiency
    "defender_military": 28.0,
    "effective_defense": 19.6,        # defender_military * resistance_factor
    "raw_net_force": 2.45,
    "stochastic_modifier": 1.12,
    "modified_net_force": 2.74,
    "outcome": "contested",
    "damage_applied": {
        "defender": {"military": -2.2, "economy": -1.4, "tension": +1.6},
        "attacker_home_tension": +1.5
    },
    "conquest_triggered": false,
    "field_state_before": {"military": 28.0, "economy": 34.0, "tension": 42.0, "population": 48.0},
    "field_state_after": {"military": 25.8, "economy": 32.6, "tension": 43.6, "population": 48.0}
}
```

### Border Friction Log Entry (per region per tick):
```python
{
    "region_id": "region_player_frontier_1",
    "tick": 203,
    "hostile_edges": [
        {"neighbor": "region_conq_frontier", "neighbor_military": 45.0,
         "tension_friction": 0.045, "economy_friction": 0.023}
    ],
    "total_tension_friction": 0.045,
    "total_economy_friction": 0.023
}
```

## Integration Points

**Reads from Stage 1:**
- Region state (all four granular fields, composite axes)
- World graph (adjacency, region ownership, region tier)
- Oscillation state (agents read real oscillated values)

**Reads from Stage 2:**
- Event log (for context, not for agent decisions)
- Pending event queue (to insert conquest consequences)

**Writes to Stage 1 regions:**
- Attack damage deltas (applied directly in step 3)
- Reinforce military boosts (applied directly in step 3)
- Colonization initialization (new region field values)
- Border friction deltas (applied in step 4)
- Region faction_id changes (conquest transfers ownership)

**Writes to Stage 2:**
- Conquest consequence events inserted into pending event queue (processed on next tick)

**Does NOT touch:**
- Drift formulas (Stage 1 — unchanged)
- Event engine internals (Stage 2 — unchanged, only uses its public queue insertion interface)
- Coherence ledger (Stage 4)

**Config flags:** `ENABLE_FACTION_AGENTS`. When False, the tick loop skips step 3 entirely. `ENABLE_BORDER_FRICTION`. When False, the tick loop skips step 4 entirely. Default: both True.

**Tick loop integration:** Stage 3 adds steps 3 and 4 to the existing tick loop. The full Stage 3 tick loop is:
1. Process pending event queue (Stage 2)
2. Evaluate fresh threshold triggers (Stage 2)
3. Run all faction agents (new — Stage 3)
4. Apply border friction (new — Stage 3)
5. Apply passive drift (Stage 1)
6. Recompute composite axes (Stage 1)
7. Log everything (expanded — Stage 3 adds faction action logs, attack logs, friction logs)

**Critical sequencing note:** Step 3 (faction agents) runs AFTER steps 1–2 (events). This is intentional — agents see the post-event state of regions and can exploit emerging crises. Attack damage from step 3 is applied immediately to region state, so step 4 (border friction) and step 5 (drift) see the post-attack state. Conquest events from step 3 are queued for step 1 of the NEXT tick.

## Build Order and Checkpoints

Each numbered step is a mandatory checkpoint. After completing each step, run the specified test, show the output to Westley, and **STOP. Do not continue to the next step until Westley approves.**

> **REMINDER — THIS IS NON-NEGOTIABLE.** Do not evaluate output yourself and decide to proceed. Do not batch multiple steps. Do not "fix" something and continue without showing the fix. Each checkpoint requires Westley's explicit approval before the next step begins. See dev_rules.md "Mandatory Checkpoints — STOP AND WAIT" for the full policy.

---

### A — Faction Entity Model and World Template Extension

**A1. Define the faction data structure and extend the world template.**
Create `faction_agent.py` with the faction entity data structure. Extend the isolated start template to place a Conqueror faction: 1–2 regions on the far side of the empty space, separated from the player's frontier by at least one uninhabited buffer region. The Conqueror's starting regions use their own field value ranges (config values per archetype). Initialize diplomatic stances (all hostile for Stage 3). Roll attack_confidence for each faction from their archetype range.

**Test:** Generate a world. Print the world graph showing all regions with their faction ownership and field values. Print both faction entities with their IDs, archetypes, owned regions, starting budget (0), attack_confidence rolls, and diplomatic stances. Confirm the Conqueror's regions are separated from the player's regions by at least one uninhabited region. Run 3 seeds and confirm attack_confidence varies between seeds.

**🛑 CHECKPOINT A1 — STOP and show output to Westley.**

---

### B — Budget Accumulation

**B1. Implement budget accumulation with maintenance cost.**
Each tick, for each faction, compute budget growth: `sum(region.economy - region_maintenance_cost for region in owned_regions) * archetype_growth_rate`. Budget cannot go below 0 (clamp). Add budget_growth to the faction's budget.

**Test:** Generate a world. Run 50 ticks with ONLY budget accumulation enabled (no agent decisions, no friction, no events). Print per-tick budget for both factions. Confirm:
- Budget grows each tick proportional to net economy (gross economy minus maintenance)
- Player civilization (3 regions: 1 home ~65 econ, 2 frontiers ~30 econ) grows faster than Conqueror (1–2 regions with archetype-specific econ ranges)
- If region_maintenance_cost is set to 8, a frontier at economy 30 contributes (30-8) * growth_rate per tick
- Print the per-region contribution breakdown (economy, maintenance, net) for each faction each tick

**🛑 CHECKPOINT B1 — STOP and show output to Westley.**

**B2. Verify overextension dynamics with maintenance cost.**
Manually give one faction 5 regions: 1 home (economy 65), 2 frontiers (economy 30), 2 conquered husks (economy 3). Print per-tick budget growth. Confirm the husks are net drains. Confirm total budget growth is lower than a faction with just 3 healthy regions. Try maintenance_cost values of 6, 8, and 10 and print the budget growth at each — this informs the tuning starting point.

**🛑 CHECKPOINT B2 — STOP and show output to Westley.**

---

### C — Border Friction

**C1. Implement border friction scaling with hostile neighbor military.**
Create `border_friction.py`. For each region with a hostile neighbor, apply per-tick friction: `tension_friction = base_tension_friction * (hostile_neighbor_military / 100)` and `economy_friction = base_economy_friction * (hostile_neighbor_military / 100)`. Sum friction from all hostile edges per region. Apply after faction agents (step 4 in tick loop).

**Test:** Generate a world. Set the Conqueror's border region to military 60. Run 50 ticks with ONLY border friction enabled (no agents, no events, drift ON). Print per-tick tension and economy for the player's frontier region adjacent to the Conqueror. Confirm:
- Tension increases slightly each tick from friction
- Economy decreases slightly each tick from friction
- The friction magnitudes are proportional to the Conqueror's military (set to 60, then 30, then 90 — print the per-tick friction at each to confirm scaling)
- Drift still dominates the field trajectories — friction is a secondary pressure, not the primary driver
- Print the border friction log entries showing the per-edge breakdown

**🛑 CHECKPOINT C1 — STOP and show output to Westley.**

---

### D — Attack Evaluation and Resolution (No Agent Decision System Yet)

This section implements the attack pipeline in isolation. The agent decision system (which decides WHEN to attack) comes in section F. Here we build and prove the attack mechanics themselves.

**D1. Implement the expected outcome evaluation.**
Given an attacker faction (with budget and attack_confidence) and a target region, compute the expected outcome: `potential_commit = budget * commit_fraction`, `expected_attack = potential_commit * attack_efficiency`, `expected_defense = target_military * resistance_factor`, `expected_net = expected_attack - expected_defense`. Return whether the attack passes the confidence threshold.

**Test:** Set up a Conqueror with budget 50, attack_confidence 15. Test against targets at military 10, 25, 40, 60, 80. Print the full evaluation for each: potential_commit, expected_attack, expected_defense, expected_net, passes_threshold (yes/no). Confirm the agent would attack military 10 and 25 but not 60 or 80. Confirm the boundary case — find the military value where the decision flips.

**🛑 CHECKPOINT D1 — STOP and show output to Westley.**

**D2. Implement the attack resolver with scaled damage.**
Create `attack_resolver.py`. Given attack_strength, defender_military, and config values, compute: effective_attack, effective_defense, raw net_force, stochastic modifier (rolled from configured range), modified net_force, outcome band, and scaled damage for each field per outcome band.

**Test:** Run the resolver against three scenarios designed to produce one of each outcome:
- Breakthrough: attack_strength 80 vs defender_military 20 (strong positive net_force)
- Contested: attack_strength 40 vs defender_military 35 (small positive net_force)
- Repelled: attack_strength 20 vs defender_military 50 (negative net_force)

For each scenario, print: all intermediate values (effective_attack, effective_defense, raw net_force, modifier, modified net_force), the outcome band, and the damage applied to each field. Run the contested scenario 20 times with different seeds — confirm the stochastic modifier sometimes flips it to breakthrough or repelled. Print the outcome distribution.

**🛑 CHECKPOINT D2 — STOP and show output to Westley.**

**D3. Implement conquest trigger and conquest event queue insertion.**
When a breakthrough drives defender military below the conquest threshold, create a Conquest consequence event and insert it into the Stage 2 pending event queue for next-tick processing. The conquest event: transfers region ownership to the attacking faction, applies immediate field damage (tension spike, population drop, economy disruption — with economy floor bypass flag), and spawns 1–2 follow-up chain events through the existing chain spawn mechanism.

Create `conquest_templates.py` with the conquest consequence template(s). These are hand-authored like the Stage 2 test templates.

**Test:** Set up a region at military 5, economy 15. Launch an overwhelming attack (attack_strength 100). Confirm:
- The attack produces a breakthrough
- Defender military drops below conquest threshold
- Conquest event is created and inserted into the pending event queue
- The conquest event's effects include economy floor bypass flag
- Print the conquest event entry in the pending queue (scheduled_tick, effects, chain spawns)

Then run 5 more ticks to let the conquest event process through the Stage 2 event engine. Confirm:
- Region ownership transferred to the attacker
- Conquest consequence deltas applied (tension spike, economy disruption, population drop)
- Economy dropped below the normal floor (8.0) due to bypass flag
- Any chain spawns from the conquest template are in the pending queue
- Print the full event log showing the conquest event and its chain

**🛑 CHECKPOINT D3 — STOP and show output to Westley.**

---

### E — Colonization

**E1. Implement colonization as an agent action.**
When the agent selects an uninhabited region from the candidate pool, spend colonization_cost from budget and initialize the region with starter field values (colony_start_military, colony_start_economy, colony_start_tension, colony_start_population). Set the region's faction_id to the colonizing faction. Add the region to the faction's owned_regions list.

**Test:** Set up a Conqueror adjacent to an uninhabited region. Manually trigger a colonization action. Confirm:
- Budget decreased by colonization_cost
- Region initialized with correct starter field values
- Region ownership set to Conqueror
- Print the region state before and after colonization
- Run 20 ticks of drift on the new colony — confirm it develops through normal drift mechanics (economy grows slowly via adjacency bonus and base growth, military stabilizes via baseline recruitment)

**🛑 CHECKPOINT E1 — STOP and show output to Westley.**

**E2. Verify contested colonization.**
Set up two factions adjacent to the same uninhabited region. Trigger both to colonize on the same tick. Confirm the first faction (randomized order) claims the region, the second faction's budget is refunded. Run 20 times and confirm the winner is roughly 50/50.

**🛑 CHECKPOINT E2 — STOP and show output to Westley.**

---

### F — Reinforce Mechanics

**F1. Implement the reinforce threat evaluation and spending curve.**
For each owned border region adjacent to hostile territory, compute threat ratio: `adjacent_hostile_military / own_region_military`. Apply the spending curve (low/moderate/high threat tiers). Apply the overreaction variance roll (random multiplier, range modified by factional tension). Apply diminishing returns formula for the actual military boost.

**Test:** Set up a player civilization region at military 25, adjacent to a Conqueror region at military 45. Trigger a reinforce action with budget 30. Print: threat ratio (1.8), spending curve tier (high), base spend amount, variance roll, final spend amount, diminishing returns calculation, actual military boost. Run 20 times with different seeds — confirm the variance roll produces visible variation in the final boost. Print the distribution.

Then test with the same military values but region factional tension at 10 vs 60. Confirm tension=60 produces wider variance in the boost amounts.

**🛑 CHECKPOINT F1 — STOP and show output to Westley.**

**F2. Verify probabilistic target rotation for multi-border reinforcement.**
Set up a faction with three border regions at threat ratios 1.8, 1.2, and 0.9. Run the target selection 100 times. Confirm:
- The region at ratio 1.8 is selected most often (~50–60%)
- The region at ratio 1.2 is selected sometimes (~25–35%)
- The region at ratio 0.9 is selected rarely (~10–20%)
- Print the distribution

Then set one region to threat ratio 2.5 (above critical threshold). Run 100 times. Confirm it is selected every time (critical override).

**🛑 CHECKPOINT F2 — STOP and show output to Westley.**

---

### G — Attractiveness Scoring

**G1. Implement the Conqueror's attractiveness scoring function.**
Implement the three-factor scoring: weakness, current_value, strategic_position with the bible's config weights (w1=0.40, w2=0.25, w3=0.35). The candidate pool includes both enemy-owned regions and uninhabited regions adjacent to the Conqueror's territory.

**Test:** Set up a world with:
- Player frontier at military 20, economy 35, population 45 (weak, moderately valuable)
- Player home at military 60, economy 70, population 75 (strong, very valuable)
- Uninhabited region between Conqueror and player (maximum weakness, zero current value, strategic position based on neighbors)

Print the attractiveness score breakdown for each candidate: weakness component, value component, strategic position component, total score, ranking. Confirm the weak frontier scores highest (easy target with decent value). Confirm the uninhabited region scores based on what it borders. Confirm the strong home scores lowest (military strength suppresses weakness component).

**🛑 CHECKPOINT G1 — STOP and show output to Westley.**

---

### H — Scored Decision Selector

**H1. Implement the scored decision system with archetype weights and normalization.**
Implement the decision selector: compute raw scores for each viable action (attack, colonize, reinforce), normalize to 0–1 range, apply archetype weights, pick the highest weighted score. Accumulate is the fallback when nothing exceeds the minimum viability threshold.

**Test with Conqueror archetype (high attack_weight, high expand_weight, low defend_weight):**
Set up three scenarios:
1. Strong attack opportunity (expected_net 25) + mild border threat (ratio 1.1) → confirm attack wins
2. No viable attack + uninhabited region available + mild border threat → confirm colonize wins
3. No viable attack + no colonization target + severe border threat (ratio 2.0) → confirm reinforce wins (high threat ratio overcomes low defend_weight)

**Test with player civilization archetype (high defend_weight, low attack_weight):**
4. Moderate attack opportunity (expected_net 20) + moderate border threat (ratio 1.3) → confirm reinforce wins
5. Overwhelming attack opportunity (expected_net 50) + mild border threat (ratio 0.9) → confirm attack wins (high expected_net overcomes low attack_weight)
6. No threats, no viable attacks → confirm accumulate

For EACH scenario, print the full decision log: all raw scores, normalized scores, weighted scores, winner, and why.

**🛑 CHECKPOINT H1 — STOP and show output to Westley.**

**H2. Verify archetype personality produces different behavior on the same world state.**
Take a single world snapshot. Run the decision selector for both the Conqueror and the player's civilization against the same state. Print both decision logs side by side. Confirm they make different decisions due to weight differences. Run 5 different world snapshots covering various threat levels and confirm the pattern is consistent — Conqueror biases toward attack, player civ biases toward reinforce.

**🛑 CHECKPOINT H2 — STOP and show output to Westley.**

---

### I — Full Agent Loop (All Actions Competing)

**I1. Run the full agent decision loop for both factions over 100 ticks.**
Enable all agent actions (attack, colonize, reinforce, accumulate) for both factions. Enable border friction. Enable Stage 2 events. Enable drift and oscillation. This is the first time everything runs together.

**Test:** Run 100 ticks. Print:
- Per-tick decision log for both factions (action chosen, scores, budget)
- Action frequency summary per faction (how many ticks each action was chosen)
- Budget trajectory for both factions (graph-style: tick, budget)
- Any attacks that occurred: target, outcome, damage

Confirm:
- The Conqueror mostly accumulates in early ticks (building budget), then starts colonizing or attacking
- The player's civilization mostly accumulates and reinforces
- No faction's budget goes to zero and stays there (accumulation eventually recovers)
- The scored decision system produces different action distributions for the two archetypes
- Border friction is visible in frontier tension/economy trends

This is a **high-risk checkpoint** — this is where weight normalization and config tuning issues will surface. Expect to iterate on config values here.

**🛑 CHECKPOINT I1 — STOP and show output to Westley.**

---

### J — Attack Interactions with Stage 2 Events

**J1. Verify that attacks exploit post-event vulnerability windows.**
Run the simulation until a Stage 2 event fires in a player frontier region (e.g., a tension threshold breach that weakens the region). Check whether the Conqueror's agent sees the weakened state and evaluates it as a better attack target than before the event. Print the Conqueror's expected_net calculation for that region on the tick BEFORE the event and the tick AFTER.

If this doesn't happen naturally within 100 ticks, manually set up the scenario: fire a Stage 2 event that reduces a frontier's military by 4, then run the Conqueror's decision evaluator. Confirm expected_net increased due to reduced defender military.

**🛑 CHECKPOINT J1 — STOP and show output to Westley.**

**J2. Verify conquest consequences chain through the Stage 2 event system.**
Trigger a conquest (either naturally or by setting up an overwhelming attack). Confirm:
- Conquest event enters the pending queue on the tick the attack resolved
- On the next tick, the conquest event fires through the Stage 2 event engine
- Economy floor bypass works (economy drops below 8.0)
- Follow-up chain spawns (post-conquest instability) enter the pending queue with correct chain tags
- The full chain is visible in the event log with chain tags linking the conquest to its consequences
- Print the complete event chain: attack → conquest → follow-up events

**🛑 CHECKPOINT J2 — STOP and show output to Westley.**

---

### K — Colonization Integration

**K1. Verify early-game expansion dynamics.**
Run 200 ticks from a fresh world. Confirm:
- Both factions colonize uninhabited regions in the early ticks (when budget is low and empty regions are available)
- As empty regions fill up, factions shift toward military action
- New colonies develop through drift (economy grows, military stabilizes via baseline recruitment)
- Colonies adjacent to strong existing territory develop faster (adjacency bonus)
- Print territory ownership over time (which faction owns which regions at tick 50, 100, 150, 200)
- Print the colonization event log showing when each faction colonized which region

**🛑 CHECKPOINT K1 — STOP and show output to Westley.**

---

### L — Full Integration Test

**L1. Run a full simulation with both factions over 500 ticks.**
Generate a world from the isolated start template with both factions. Run 500 ticks with everything enabled: drift, oscillation, Stage 2 events, faction agents (all four actions), border friction. Print a comprehensive summary:

- **Territory timeline:** region ownership at tick 0, 100, 200, 300, 400, 500
- **Budget timeline:** per-faction budget at every 50 ticks
- **Action summary:** per-faction counts of each action type (accumulate, attack, colonize, reinforce)
- **Attack log:** every attack with tick, target, outcome, damage
- **Conquest log:** every conquest with tick, region, previous owner, new owner
- **Event interaction log:** any Stage 2 events that fired in regions that were subsequently attacked within 10 ticks (evidence of agents exploiting event-driven vulnerability)
- **Border friction impact:** average per-tick tension and economy friction on the most contested border region
- **Overextension check:** if any faction controls 5+ regions, print their budget growth breakdown showing maintenance costs

Confirm:
- Territory changes hands at least once (conquest occurred)
- Both factions show the expected behavioral patterns (Conqueror aggressive, player civ defensive)
- No degenerate states: no faction's budget permanently at zero, no region with all fields at zero and never recovering, no faction attacking every single tick
- Stage 2 events fire throughout the simulation alongside faction actions
- Economy floor is respected for all non-conquest events, and breached for conquest events
- The simulation tells a recognizable story: early expansion, growing contact, border friction, military buildup, eventual conflict

**🛑 CHECKPOINT L1 — STOP and show output to Westley.**

**L2. Run 5 seeds and confirm stochastic divergence.**
Run the same 500-tick simulation with 5 different random seeds. Print per-seed summary: final territory ownership, total conquests, total attacks, which faction "won" (controls more territory), budget trajectory shape. Confirm genuine divergence — different seeds produce different war stories due to attack_confidence rolls, stochastic modifiers on attacks, overreaction variance on reinforcement, event noise offsets, and oscillation phase offsets.

**🛑 CHECKPOINT L2 — STOP and show output to Westley.**

**L3. Verify the overextension arc.**
If the 500-tick run did not produce visible overextension (a faction conquering multiple regions and then stalling or declining), set up a targeted test: give the Conqueror a high attack_confidence (aggressive — low value like 8) and run until it conquers 3+ regions. Print the budget trajectory — confirm budget growth declines after each conquest due to maintenance cost on devastated territory. Confirm the Conqueror slows its attack tempo as budget growth shrinks. If the Conqueror continues attacking despite negative budget growth, flag for tuning — either maintenance_cost needs to be higher or the scored decision system isn't properly weighting budget constraints.

**🛑 CHECKPOINT L3 — STOP and show output to Westley.**

**L4. Run a 1000-tick long-run test.**
Extend the simulation to 1000 ticks. Confirm:
- The simulation doesn't degenerate (no field explosion, no permanent stuck states)
- A recognizable civilizational arc plays out (expansion → contact → conflict → outcome)
- At least one faction shows either territorial growth or decline over the full run
- Economy floors, diminishing returns, and budget constraints all function correctly at this timescale
- Print summary statistics at ticks 0, 250, 500, 750, 1000

**🛑 CHECKPOINT L4 — STOP and show output to Westley.**

---

## Done Condition

Run the Stage 3 simulation (500+ ticks, 5 seeds) and confirm:
1. Faction agents make decisions each tick using the scored selection system with archetype weights
2. Budget accumulates from owned region economy minus maintenance cost — expansion has real cost
3. The Conqueror attacks based on attractiveness scoring and expected outcome evaluation
4. Attack resolution produces breakthrough, contested, and repelled outcomes with scaled damage
5. Conquest events transfer ownership and chain through Stage 2 event system with economy floor bypass
6. Colonization initializes new regions with starter values and develops through drift
7. Reinforce uses threat-proportional spending with overreaction variance and probabilistic target rotation
8. Border friction scales with hostile neighbor military and creates visible background pressure
9. Agent decision logging shows all four scores, weighted results, and winning action per tick
10. The player's civilization behaves defensively (mostly reinforce/accumulate) while the Conqueror behaves aggressively (mostly accumulate/attack/colonize)
11. Overextension dynamics are visible — rapid conquest produces budget strain from maintenance costs
12. Different random seeds produce genuinely different war histories
13. Long-run behavior (1000 ticks) is coherent — recognizable civilizational arcs, no degenerate states

Westley signs off on the full integration test output before Stage 4 begins.

## Files Created
*(Filled in after implementation)*
