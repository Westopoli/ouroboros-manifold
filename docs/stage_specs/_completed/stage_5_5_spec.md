# Stage 5.5 — Mission Generation Pipeline

## Goal

Prove that the simulation produces playable missions: a scored candidate pool selects the right (region, archetype) pair from real simulation pressure, the force allocation algorithm assembles winnable forces from the power rating system, the outcome resolver translates tactical results back into proportional simulation consequences, and mission briefings read like orders from a living civilization. The entire pipeline is validated headless — mock outcome bands stand in for the tactical engine so that Stage 5.5 and Stage 6 can be built and tested in parallel.

This is the stage where the simulation starts producing *gameplay hooks* rather than just *narrative*. Stages 1–5 proved that the world evolves, factions fight, characters live and die, and time jumps produce chronicle prose. Stage 5.5 proves that when a time jump ends, the simulation identifies the most urgent and relevant pressure point, assembles a mission the player can fight, and — after the fight — folds the result back into the world so the next time jump inherits real consequences.

**Architecture: thin interface with Stage 6.** Stage 5.5 *creates* missions and *processes* their results. Stage 6 *runs* them. The contract between the two stages is a shared data module (`mission_contracts.py`) defining the exact data structures that cross the boundary. Stage 5.5 emits a `MissionSetup` (map parameters, player force, enemy forces with behavior scripts, objectives). Stage 6 emits a `MissionResult` (outcome band, objective scores, force retention, per-objective details). Both stages import from the same contracts module — if either side drifts, the import breaks immediately.

## Bible References

Read these spoke sections before implementing:

- **`docs/bible_history/bible_2_00_missions.md`**: Full file — mission generator algorithm (4-step candidate scoring), 10 mission archetypes (triggers, objective shapes, asset profiles, success spectrums), mission objectives, difficulty scaling, era scaling, mission preference, mission briefing structure, outcome band classification system, mission outcome resolver (proportional lookup tables), objective tracking
- **`docs/bible_history/bible_2_00_combat.md`**: "Unit Power Balancing and Force Parity" (force parity system, capacity-to-parity curve, multi-faction battles), "Force Allocation Algorithm" (4-step allocation: asset profile → parity budget → fill profile → capacity shortfalls), "Power Rating Formula" (resolved formula), "Tactical Reinforcement System" (simulation-driven capacity — reinforcement structure count is derived from mission region's military field)
- **`docs/bible_history/bible_2_00_simulation.md`**: "Coherence Ledger" (lineage history for relevance scoring), "Composite Axes" (capacity composite for force parity)
- **`game_bible.md` (hub)**: "Sacred Design Principles" (era-agnostic architecture), "The Generational Structure" (mission preference set at game start)

## Cross-Stage References

This section documents how Stage 5.5 relates to all other stages.

- **Stages 1–2** established the simulation backbone: region state model, passive drift, event chain architecture. The mission generator reads region fields (military, economy, tension, stability, population) and active event chains to evaluate trigger conditions and compute urgency scores.
- **Stage 3** established faction agents, attack/conquest resolution, and budget accumulation. A faction agent's attack decision is the primary trigger for mission generation — the committed budget from the attack event determines enemy force strength. Border friction intensity feeds urgency scoring for Siege Breaking and Containment archetypes.
- **Stage 3.5** established diplomacy and technology. Tech tiers determine which unit stat profiles the force allocator draws from. Diplomatic state (hostile/neutral/cooperative) constrains which factions can be mission opponents.
- **Stage 4** established admin revolts, lifecycle phases, time jumps, and the generational structure. Admin revolts and breakaway factions trigger Suppression and Counterinsurgency archetypes. The lifecycle phase (expansion/stability/contraction) informs urgency weighting — contraction-phase urgency scores are naturally higher because region fields are lower. Time jump duration affects how many ticks of consequence propagation the outcome resolver's field deltas experience.
- **Stage 5** established the chronicle pipeline, coherence ledger, naming system, and library builder. The coherence ledger provides lineage history for relevance scoring (Step 2 of the generator), named characters for mission briefing variable slots, and commander identity for the mission. The chronicle distiller consumes Stage 5.5's output — it reads the `mission_consequence` flag on events produced by the outcome resolver and uses the outcome band for consequence cluster categorization.
- **Stage 6** (parallel) establishes the tactical simulation engine. Stage 6 provides the `MissionResult` that the outcome resolver consumes, and the power rating formula that force allocation uses. Stage 6's `power_rating.py` is the authoritative implementation of the power rating formula — Stage 5.5 imports and calls it directly rather than reimplementing. Stage 6's outcome band thresholds and classification are self-contained; Stage 5.5 receives the classified band, not the raw score.
- **Stage 7** (future) establishes map generation and enemy macro behavior. Stage 5.5 emits map parameters (archetype, canvas size category, simulation modifiers) that Stage 7's procedural generator will consume. For Stage 5.5 validation, test maps from Stage 6 are used. Stage 7 also builds the enemy behavior scripts; Stage 5.5 selects which script template to attach based on the archetype.
- **Stage 8** (future) establishes the Godot renderer and mission briefing UI. The briefing structure produced by Stage 5.5 (situation, objective, assets) is the data model the UI renders.

## What to Build

### Files to create

**`mission_contracts.py`** — Shared data structures for the Stage 5.5 ↔ Stage 6 boundary. This file is imported by both stages. Contains:

```python
@dataclass
class ForceUnit:
    unit_type: str          # "Raider", "Interceptor", "Vanguard", "Warden", "Bombard", "Bastion"
    category: str           # "Strike", "Line", "Siege"
    stats: dict             # Full stat profile (hp, base_damage, attack_interval, etc.)
    power_rating: float     # Computed by power_rating.py
    faction_id: str
    name: str               # Display name from naming system (era-specific skin)

@dataclass
class ForceComposition:
    units: list[ForceUnit]
    total_power: float      # Sum of all unit power ratings
    faction_id: str

@dataclass
class ObjectiveSpec:
    id: str
    type: str               # "hold_zone", "destroy_targets", "escort_to_extraction",
                            # "survive_duration", "eliminate_force"
    weight: float           # Contribution to objective score (all weights sum to 1.0)
    params: dict            # Type-specific parameters
    is_primary: bool

@dataclass
class ReinforcementSpec:
    structure_count: int            # Number of reinforcement structures on the map
    player_structures: int          # Structures starting under player control
    enemy_structures: int           # Structures starting under enemy control
    neutral_structures: int         # Neutral structures
    production_rate: float          # Units per second per structure (config)
    enemy_target_ratio: dict        # Enemy AI production ratios per unit type

@dataclass
class MissionSetup:
    mission_id: str
    archetype: str                  # One of the 10 archetype keys
    region_id: str                  # Simulation region this mission takes place in
    map_params: dict                # Canvas size, archetype, simulation modifiers for map gen
    player_force: ForceComposition
    enemy_forces: list[ForceComposition]    # One per hostile faction involved
    objectives: list[ObjectiveSpec]
    reinforcements: ReinforcementSpec
    time_limit_ticks: int           # Mission deadline in tactical ticks
    behavior_script_id: str         # Enemy macro behavior script template ID
    briefing: dict                  # Structured briefing data (situation, objective, assets)
    difficulty: str                 # "easy", "medium", "hard"
    metadata: dict                  # Seed, generation timestamp, candidate scores, etc.

@dataclass
class MissionResult:
    mission_id: str
    outcome_band: str               # "total_success", "strong_success", "partial_success",
                                    # "partial_failure", "total_failure"
    objective_score: float          # 0.0–1.0
    force_retention: float          # 0.0–1.0
    per_objective: list[dict]       # Per-objective completion details
    commander_survived: bool        # Did the player's commander unit survive?
    ticks_elapsed: int              # How long the mission lasted
```

**`mission_generator.py`** — The 4-step mission generation algorithm. Contains:

- **Step 1 — Build candidate pool.** Scans all player faction regions and adjacent contested regions. For each region, evaluates each of the 10 archetype trigger conditions against the region's current simulation state. A (region, archetype) pair enters the pool only if the trigger condition is met. Trigger conditions read directly from simulation state: active attack events (Defensive Stand, Multi-Front Defense), recent conquest events (Reconquest), active revolt chains (Counterinsurgency, Suppression), sustained border friction (Siege Breaking), high-attractiveness attack targets (Assault), multiple hostile neighbors (Multi-Front Defense, Containment), enemy force in transit (Interception), critically failing region (Evacuation).
  - Multi-Front Defense requires detecting two or more simultaneous attack events or high-military hostile factions on multiple borders.
  - Evacuation requires detecting a region that is unrecoverable (military critically low, economy cratered, stability near zero, adjacent to high-military hostile faction).
  - Interception requires detecting an attack force in transit (attack event fired but not yet resolved, attacker and target are not adjacent — the force must traverse intervening space).
  - Each archetype trigger condition is a pure function: `(region_state, faction_state, event_log, world_state) → bool`.

- **Step 2 — Score candidates.** Each (region, archetype) pair receives a score: `score = (w1 × urgency) + (w2 × relevance) + (w3 × preference)`.
  - **Urgency (0–1):** Derived from region field deficits (how far military, economy, stability have dropped from 100), active conflict intensity (hostile forces at borders, recent attacks, territory lost), and event chain criticality (chains in late stages, approaching threshold triggers). Computed per-region, independent of archetype.
  - **Relevance (0–1):** Lineage connection to this region (has the player's lineage operated here? — query coherence ledger `get_lineage_history()`), regional proximity (distance from lineage home region — measured in adjacency hops on the region graph), archetype fit (has this lineage historically been assigned this archetype type? — tracked as a simple counter in the ledger). Computed per (region, archetype) pair.
  - **Preference (0–1):** Player's mission archetype weights set at game start. Preferred archetypes get the player's assigned weight. Archetypes marked "rare" get 0.1. Default (unmarked) archetypes get 0.5.
  - Weights (w1, w2, w3) are config values. Default: w1=0.5, w2=0.3, w3=0.2.

- **Step 3 — Select.** Take top N candidates by score (config, default 5). Weighted random draw from those N, using scores as weights. Highest-scored candidate usually wins but not deterministically.

- **Step 4 — Fill variable slots.** The selected archetype template has variable slots. The generator fills them from: the selected region's current field values, active event chains in that region, coherence ledger entries (named characters in the region, the player's commander, faction leaders), faction state (tech level, budget, diplomatic relations), and world state (neighboring regions, global tension). The output is a structured mission briefing and a `MissionSetup` ready for the tactical engine.

**`force_allocator.py`** — Translates mission context into concrete force compositions. Contains:

- **Step 1 — Determine enemy force strength.** For archetype triggers driven by faction attacks (Defensive Stand, Multi-Front Defense, Interception), the attacking faction's committed budget is the baseline. Budget-to-power conversion: `enemy_power_total = committed_budget × BUDGET_TO_POWER_SCALE` (config). For archetypes without an explicit attacking budget (Counterinsurgency, Evacuation, Containment), enemy force strength is derived from the threat region's military field value: `enemy_power_total = threat_military × MILITARY_TO_POWER_SCALE` (config). For Suppression, the breakaway faction's military field determines enemy strength.

- **Step 2 — Determine player force budget.** Force parity system: `player_power_budget = enemy_power_total × parity_ratio`. Parity ratio is derived from the player faction's capacity composite (from simulation state) and the difficulty setting:
  - Capacity composite → base parity: a thriving civilization (high capacity) gives ~1.0 parity. A declining civilization gives 0.80–0.90. The capacity-to-parity curve is a config lookup (linear interpolation between authored breakpoints).
  - Difficulty adjustment: Easy = parity floor of 0.95 (near-100% even when weak). Medium = no adjustment (use capacity curve directly). Hard = parity ceiling reduced to 0.85 (a declining civilization hits the penalty harder).
  - Multi-faction missions: player force is sized to match the *combined* enemy strength (with parity adjustment).

- **Step 3 — Fill asset profile.** Each archetype defines a target unit type ratio (from docs/bible_history/bible_2_00_missions.md asset profiles). The allocator spends the player's power budget filling this ratio. For each unit type slot, it selects from the available unit roster for the player's faction at the current tech tier. Units are added one at a time, each consuming its power rating from the remaining budget, until the budget is spent or the ratio is filled. Slight budget overrun is acceptable (the last unit added may push slightly over budget).
  - Unit roster: at Stage 5.5 validation time, uses Tier 2 baseline stats from Stage 6. The roster is loaded from config — no hardcoded stat values in the allocator.
  - Within each unit type, if multiple stat variants exist (future: AI-generated variants), the allocator picks randomly.

- **Step 4 — Apply capacity shortfalls.** If the player's civilization capacity is below a threshold (config), some asset profile slots go unfilled. The player receives fewer units, not weaker ones. Shortfall is applied proportionally across all unit types — no type is disproportionately cut. The briefing notes what couldn't be provided.

- **Enemy force composition.** The enemy force is assembled the same way: archetype asset profile defines the ratio, enemy faction's roster fills it, enemy power total is the budget. For multi-faction missions, each hostile faction gets its own force composition from its own roster.

- **Reinforcement spec.** The allocator computes the reinforcement structure count from the mission region's military field value: `structure_count = floor(region_military × MILITARY_TO_STRUCTURES_SCALE)` clamped to the archetype's canvas size range (config per canvas size: small 2–4, medium 3–6, large 4–8). Structures are distributed between player, enemy, and neutral based on archetype (defensive archetypes give the player more starting structures; offensive archetypes give the enemy more). Enemy production target ratio is derived from the archetype's asset profile.

**`outcome_resolver.py`** — Translates tactical results into simulation consequences. Contains:

- **Input:** A `MissionResult` from Stage 6 (or a mock during validation).
- **Consequence lookup.** Each archetype defines a consequence table: 5 outcome bands → field deltas for the mission region. Deltas are **proportional to the region's current state**, not absolute. The table is loaded from config and matches the success spectrum authored per archetype in docs/bible_history/bible_2_00_missions.md.
  - Proportional delta semantics: "+X% of deficit" means `delta = current_deficit_from_100 × X/100`. "-X% of current" means `delta = -current_value × X/100`. These two forms cover all the authored success spectrums.
  - Field deltas apply to: military, economy, tension, stability, population. Each outcome band specifies which fields change and by how much.
- **Cross-region consequences.** Some archetypes apply consequences to regions other than the mission region (e.g., Reconquest partial failure applies tension to adjacent player regions; Evacuation success applies economy/population bonuses to adjacent regions). These are also in the per-archetype consequence table.
- **Commander death.** If `MissionResult.commander_survived` is false, the outcome resolver notifies the coherence ledger (marks the commander as dead) and triggers the character selector for the next mission's commander. Commander death is logged as a special event in the event log with `mission_consequence=True`.
- **Event injection.** The outcome resolver creates one or more events in the simulation event log with `mission_consequence=True` flag. These events carry the field deltas and are processed by the simulation during the next time jump. The chronicle distiller's consequence cluster reads these flagged events.
- **Scope.** The outcome resolver does NOT propagate world-wide effects. It applies field deltas to the mission region (and specified adjacent regions for cross-region archetypes). The simulation's existing inter-region mechanics (trade, border friction, faction dynamics) propagate the effects naturally during the subsequent time jump.

**`mission_briefing.py`** — Generates the structured mission briefing from filled variable slots. Contains:

- **Three sections** per the bible:
  - **Situation** — what's happening in the world that made this mission necessary. Built from: the triggering simulation event (attack, revolt, border friction), the region's current state (field values mapped to qualitative descriptors), recent chronicle entries for context, and named characters involved (from coherence ledger).
  - **Objective** — what the commander is being sent to do. Built from: the archetype's objective shape, the specific objectives generated for this mission instance, and implicit framing of the success spectrum (the briefing never explicitly lists the 5 bands — the player reads between the lines).
  - **Assets** — what the civilization is providing. Built from: the force composition (unit counts by type, total strength relative to expected enemy strength), reinforcement expectations (from reinforcement spec), and a note on what couldn't be provided if capacity shortfalls occurred.
- **Variable slot resolution.** Same approach as the chronicle assembler (Stage 5): raw numeric values mapped to qualitative prose labels, named characters inserted by name, regions by name, factions by name. The briefing reads as if a superior officer is delivering orders.
- **Tone.** The briefing is terse, military, professional. Not flowery, not dramatic. The drama comes from the situation, not the prose style. The briefing builder uses authored template fragments per archetype (similar to chronicle fragments but simpler — fewer combinatorial pieces, more fill-in-the-blank).
- **Briefing fragments** are generated by the library builder pipeline (Stage 5) using the same infrastructure. Each archetype needs: 5–10 situation openings, 3–5 objective framings, 3–5 asset descriptions, and 2–3 capacity shortfall notes. Total: ~200 briefing fragments across all 10 archetypes. These are generated as a separate library builder batch and stored in the same JSON library structure.

**`character_selector.py`** — Determines whether to continue the current lineage or rotate to a new one, then selects the specific commander for the next mission. Runs after the time jump completes and the mission generator has already selected the next mission's region and archetype. Contains:

- **Step 1 — Rotation decision.** The coherence ledger tracks a chapter counter for the current lineage. The rotation decision evaluates four conditions in order:
  - **Forced rotation:** if the current bloodline has no living members, or the commander died and no immediate family successor exists, rotation is forced immediately regardless of all other factors.
  0. BLOODLINE SUCCESSION (pre-cascade)
   - If the current commander died and a living family member of the same
     lineage exists in or near the mission region:
     - The lineage continues with the successor as the new commander.
     - Decision: STAY (same lineage_id, new character_id).
     - rotation_reason: None (this is not a rotation).
     - pool_used: None (no pool roll).
   - This path runs before the forced rotation check. Forced rotation
     on commander KIA fires only when no successor exists.
   - Rationale: aligns with docs/bible_history/bible_2_00_chronicle.md line 66, which defines
     `lineage_succession` as a continuity beat ("a key family member
     died and was succeeded"), not a rotation event.
  - **Minimum stay:** if chapter counter is below the eligible rotation range (config, default 2), stay with the current lineage. The family's story needs at least 2 chapters to develop.
  - **Hard cap:** if chapter counter is at or above the maximum (config, default ~6), rotate regardless of delta score or crisis state. This prevents a single lineage from dominating the playthrough.
  - **Delta-based probability:** compute the total field delta in the lineage's home region (and adjacent regions) during the time jump. High delta → low rotation chance (the family's story is in motion). Low delta → high rotation chance (natural exit point). The delta maps to a rotation probability via a configurable curve. Roll against the probability. If rotation triggers, check the crisis veto: if the lineage's home region has stability below a config threshold or an active event chain in a critical stage, veto the rotation — the family stays because their story isn't done. If not vetoed, rotate.
  - The flow: forced rotation check → minimum stay check → hard cap check → delta scoring → probability roll → crisis veto → decision.

- **Step 2 — Lineage selection (on rotation).** The mission region is already decided by the mission generator. The selector finds the best lineage for that region from three priority pools:
  - **Priority 1 — Previous lineage descendant (~70%).** Check all previous lineages the player has played. Does any have living descendants in or near the mission region? If multiple qualify, score by: recency penalty (don't immediately return to a lineage you just left), number of living descendants in the region, and how many chapters ago the player last played them (moderate gap preferred). Weighted random draw from scored candidates.
  - **Priority 2 — Nemesis/rival descendant (~20%).** Check the coherence ledger for named characters who were rivals or antagonists to any previous commander. Do any have descendants in or near the mission region? If yes, select from this pool.
  - **Priority 3 — Unrelated person (~10%).** No previous lineage or nemesis connection. Generate a new character from that region.
  - The pool weights are config values. The selector rolls against the weights to pick a pool, then selects within that pool. If the selected pool has no valid candidates, it falls through to the next pool.

- **Step 3 — Commander assignment.** The selected lineage member (or newly generated character) is registered in the coherence ledger as the new commander. Their rank is set to the appropriate military rank. The chapter counter for the new lineage (or continued lineage) is incremented.

- **Cross-faction rotation.** Even when the player's civilization survives, the hard cap can move the player to a different faction. At the hard cap, the selector considers candidates across all factions, not just the player's current one. A player who has spent four chapters commanding forces for one faction might rotate to a breakaway faction born from a revolt in their former territory, or to a rival faction where a nemesis descendant now serves.

- **Faction collapse reassignment.** When the player's faction loses all regions, the selector evaluates all surviving factions using modified lineage selection logic: prefer factions with narrative connections (previous lineages with descendants in that faction's territory, nemesis connections, geographic proximity to the fallen civilization's former territory). If no narrative connection exists, select the faction whose territory overlaps most with the player's former civilization.

- **First chapter.** On the very first mission (no previous lineages exist), the selector draws from the "unrelated person" pool — generating a new character in the mission region. This is the player's first commander and first lineage.

- **Interface:**
  ```python
  class CharacterSelector:
      def select_commander(
          self,
          ledger: CoherenceLedger,
          mission_region: str,
          mission_archetype: str,
          world: World,
          current_lineage_id: str | None,
          chapter_counter: int,
          time_jump_deltas: dict[str, dict[str, float]],
          rng: random.Random,
      ) -> CommanderSelection:
          """Returns the selected commander and whether a rotation occurred."""

  @dataclass
  class CommanderSelection:
      character_id: str           # Coherence ledger character ID
      lineage_id: str             # Lineage ID (new or continued)
      faction_id: str             # Faction the commander serves
      rotated: bool               # True if lineage rotation occurred
      rotation_reason: str | None # "forced", "hard_cap", "delta_roll", None if no rotation
      pool_used: str | None       # "previous_descendant", "nemesis_descendant", "unrelated", None if continued
  ```

### Files to modify

**`coherence_ledger.py`** — Add archetype assignment tracking for relevance scoring. New field on character records: `archetype_history` — a counter dict tracking how many times a lineage has been assigned each archetype. Updated by the mission generator at Step 4. New query: `get_lineage_archetype_history(lineage_id) → dict[str, int]`. Also add `get_lineage_home_region(lineage_id) → str` if not already present (the region where the lineage was founded or has spent the most generations). Add chapter counter tracking per lineage for the character selector's rotation decision. Add nemesis/rival tagging on character records — characters on the opposing side of a mission are tagged as rivals. New queries: `get_chapter_counter(lineage_id) → int`, `increment_chapter_counter(lineage_id)`, `get_rival_descendants(mission_region, proximity_hops) → list[CharacterRecord]`.

**`time_jump.py`** — After the time jump completes and the chronicle distiller runs, invoke the mission generator to produce the next mission. The time jump function returns both the chronicle scroll and the generated `MissionSetup`. The mission is generated *after* the time jump so it reflects the post-jump world state — the player's next mission responds to what happened during the time jump, not to the pre-jump state.

**`generational.py`** — Wire the mission lifecycle into the generational loop. After a mission completes (receives a `MissionResult`), invoke the outcome resolver to apply consequences, then invoke the next time jump. After the time jump and mission generator, invoke the character selector to determine the next commander. The generational loop becomes: mission → outcome resolver → time jump (N ticks + chronicle distiller) → mission generator → character selector → next mission.

**`events.py`** — Add the `mission_consequence` flag to the event data model. Events created by the outcome resolver carry this flag. The chronicle distiller already reads this flag for consequence cluster extraction (Stage 5 spec). Also add mission-related event templates: `MISSION_VICTORY`, `MISSION_DEFEAT`, `MISSION_MIXED`, `COMMANDER_KILLED_IN_ACTION`, each with appropriate significance tiers (4–5, high significance).

**`config.py`** — Add all new config values (see Config Values to Add section).

**`sim_tuner.py`** — Add mission generation scenarios and the Mission Generation Review Report mode (see Validation section).

**`invariants.py`** — Add Group M invariants (see below).

### Files NOT to create or modify

The tactical simulation engine (tick loop, unit behavior, damage, abilities, fog of war, pathfinding, movement) is Stage 6. Enemy macro behavior scripts (the authored script content per archetype) are Stage 7 — Stage 5.5 references behavior script IDs but does not author the scripts themselves; validation uses a placeholder script ID. Map generation (spine + gradient procedural generation, Strategic Layout Authoring Framework) is Stage 7 — Stage 5.5 emits map parameters but does not generate maps; validation uses Stage 6's test maps. The Godot renderer, mission briefing UI, and command interface are Stage 8. The library builder tool itself (Stage 5) is not modified — Stage 5.5 adds a new generation batch (briefing fragments) using the existing builder infrastructure.

---

## Implementation Checkpoints

> **MANDATORY: STOP AND WAIT AT EVERY CHECKPOINT.** Each checkpoint below is a hard stop. Run the test, show the output to Westley, and **stop executing. Do not continue to the next checkpoint.** Do not evaluate the output yourself and decide to proceed. Do not batch multiple checkpoints. Present the output and wait for Westley to say "yes, continue" or "no, fix this." The next checkpoint begins only after explicit approval.
>
> **What "STOP" means:** Stop generating code. Stop running tests. Stop planning the next checkpoint. Present the output and wait for input. If you are unsure whether output is correct, that is Westley's judgment to make, not yours.

### Checkpoint A — Shared Contracts and Power Rating (Isolation)

**Build:** `mission_contracts.py` — all dataclasses. `power_rating.py` — the power rating formula (pure function, no tactical engine dependencies).

**Test:** Write a standalone test script. Construct `ForceUnit` instances for all 6 unit types using Tier 2 baseline stats from Stage 6 config. Compute power ratings for each. Print a table showing: unit type, HP, DPS, range, speed, computed power rating. Construct a `ForceComposition` and print total force power. Construct a `MissionSetup` and `MissionResult` with placeholder data — confirm they instantiate without error.

**Print:**
- Power rating table for all 6 unit types
- Total force power for a sample force
- Confirmation that all contract dataclasses instantiate cleanly

**Verify:** Power ratings should produce a reasonable ranking (Vanguard and Bastion highest due to HP, Raider high due to DPS, Warden lowest due to low damage). Exact values are less important than relative ordering making sense.

**⛔ STOP. Show output. Wait for Westley.**

---

### Checkpoint B — Trigger Conditions (Isolation)

**Build:** `mission_generator.py` — trigger condition functions only (the 10 pure functions, one per archetype). No scoring, no selection, no variable filling yet.

**Test:** Write a standalone test script. Construct mock simulation states that should activate each trigger:
- A region under attack → Defensive Stand triggers, others don't
- A region with sustained border friction → Siege Breaking triggers
- A recently conquered region → Reconquest triggers
- A region with active revolt chains → Counterinsurgency triggers
- A critically failing region → Evacuation triggers
- At least 2 triggers that should NOT fire (stable region with no pressure)

**Print:**
- For each mock state: which triggers fired (True) and which didn't (False)
- Explicit confirmation of expected vs. actual for each test case

**Verify:** Every trigger fires only when its specific simulation condition is met. No false positives on stable regions. No false negatives on regions with the right pressure.

**⛔ STOP. Show output. Wait for Westley.**

---

### Checkpoint C — Candidate Scoring (Isolation)

**Build:** `mission_generator.py` — Steps 1–2 (build candidate pool + score candidates). Urgency scoring, relevance scoring, preference scoring. No selection (Step 3) or variable filling (Step 4) yet.

**Test:** Write a standalone test script. Set up a mock world state with 4+ regions at varying levels of pressure. Set mock player preferences (2 preferred, 1 rare, rest default). Set mock lineage history (lineage has operated in 2 of the regions, has done 3 Defensive Stand missions).

**Print:**
- Full candidate pool: every (region, archetype) pair that passed trigger evaluation
- For each candidate: urgency score, relevance score, preference score, final weighted score
- Candidates sorted by final score, highest first
- The top 5 candidates highlighted

**Verify:** High-urgency regions with matching lineage history and preferred archetypes should score highest. Rare archetypes should score low unless urgency is extreme. Regions with no lineage connection should have low relevance. The ranking should feel intuitively right — "yes, this is the mission I'd expect the game to pick."

**⛔ STOP. Show output. Wait for Westley.**

---

### Checkpoint D — Force Allocation (Isolation)

**Build:** `force_allocator.py` — full allocation algorithm (enemy force determination, player parity budget, asset profile filling, capacity shortfalls).

**Test:** Write a standalone test script. Run force allocation for 3 archetypes (one defensive, one offensive, one asymmetric — e.g., Defensive Stand, Assault, Counterinsurgency) at 3 different civilization capacities (thriving=0.9, stable=0.6, declining=0.3) and all 3 difficulty settings.

**Print:**
- For each (archetype × capacity × difficulty) combination:
  - Enemy force: unit count by type, total power
  - Player force: unit count by type, total power
  - Parity ratio (player/enemy)
  - Asset profile deviation (actual ratio vs. target ratio per unit type)
  - Shortfall flag (yes/no, which types reduced)
- A comparison showing that enemy force is **identical** across difficulties for the same archetype and capacity
- Reinforcement spec: structure count, player/enemy/neutral split

**Verify:** Parity ratios fall within configured range. Asset profiles are within tolerance. Shortfalls reduce quantity, not quality (unit stats identical). Enemy force is invariant to difficulty. Defensive archetypes are heavy on Bastion/Line. Offensive archetypes are heavy on Raider/Vanguard. The forces feel right for the mission type.

**⛔ STOP. Show output. Wait for Westley.**

---

### Checkpoint E — Outcome Resolver (Isolation)

**Build:** `outcome_resolver.py` — proportional delta computation, consequence table lookup, event injection, commander death handling.

**Test:** Write a standalone test script. Set up two regions at different states:
- Region A: military=23, economy=41, tension=72, stability=18 (desperate)
- Region B: military=75, economy=82, tension=25, stability=71 (thriving)

Apply all 5 outcome bands for Defensive Stand to both regions.

**Print:**
- For each (region × outcome band): the computed field deltas (absolute values, not percentages)
- Side-by-side comparison showing that Region A gets larger absolute military boosts from success (deficit-form scaling) and Region B gets larger absolute military losses from failure (current-form scaling)
- Commander death test: mock a `MissionResult` with `commander_survived=False`, print the event log entry and ledger update

**Verify:** Proportional scaling works as designed — saving a desperate region has bigger impact than reinforcing a strong one. All 5 bands produce distinct deltas. Commander death is properly logged. The consequence magnitudes feel proportionate — total success shouldn't trivially fix everything, total failure shouldn't be world-ending for a strong region.

**⛔ STOP. Show output. Wait for Westley.**

---

### Checkpoint F — Mission Generator End-to-End (Isolation)

**Build:** `mission_generator.py` — Steps 3–4 (weighted selection + variable slot filling). `mission_briefing.py` — briefing assembly from filled slots.

**Test:** Write a standalone test script. Run the full generator 10 times from the same simulation state snapshot (same mock world, different random seeds). Also run it from a crisis state (one region at urgency >0.9) and a calm state (all regions below urgency 0.4).

**Print:**
- For each of the 10 normal runs: selected (region, archetype), final score, the full `MissionSetup` summary (archetype, region, force sizes, objective types, reinforcement spec)
- For the crisis runs: confirm high-urgency region is selected most of the time
- For the calm runs: confirm preferred archetypes appear more often
- One full briefing preview (situation + objective + assets sections as prose)

**Verify:** Selection shows stochastic variety (not the same mission 10/10 times). Crisis state produces urgency-dominant selection. Calm state shows preference influence. The briefing reads as coherent military orders — not data dumps, not generic, not repetitive. Variable slots are filled with real names and places.

**⛔ STOP. Show output. Wait for Westley.**

---

### Checkpoint G — Integration with Simulation (Wiring)

**Build:** Modifications to `coherence_ledger.py` (archetype history tracking), `time_jump.py` (invoke generator after jump), `generational.py` (wire mission lifecycle), `events.py` (mission_consequence flag + new event templates), `config.py` (all new config values).

**Test:** Run a full simulation scenario (4 factions, 1500 ticks, 3 time jumps with mock outcome bands). Use `sim_tuner.py` with the `--mission-review` flag.

**Print:**
- Full Mission Generation Review Report for each time jump (candidate pool, selected mission, force composition, briefing preview, outcome resolution preview)
- Event log showing mission_consequence-flagged events
- Coherence ledger showing archetype history updates
- Confirmation that all existing invariants (A through L) still pass

**Verify:** Missions respond to real simulation pressure (not fabricated). The generational loop works: time jump → generate mission → mock outcome → resolve consequences → next time jump → consequences are visible in the next generation's world state. No regression in existing systems.

**⛔ STOP. Show output. Wait for Westley.**

---

### Checkpoint G.5 — Character Selector (Integration)

**Build:** `character_selector.py` — full rotation decision, lineage selection, commander assignment. Wire into `generational.py` after mission generation. Add `CommanderSelection` to `mission_contracts.py`. Add chapter counter tracking to `coherence_ledger.py`. Add nemesis/rival tagging to the coherence ledger (simple tag on character records — characters on the opposing side of a mission are tagged as rivals).

**Test:** Run a full generational loop simulation (4 factions, 2000 ticks, 6 time jumps with mock outcome bands cycling through all 5 bands). Track lineage continuity across all 6 missions.

**Print:**
- For each mission: commander name, lineage ID, faction, chapter counter, rotation decision (stay/rotate + reason)
- Lineage timeline: which lineage was active for which chapters, showing the 2–4 chapter arcs
- At least one forced rotation (engineer by killing a commander via mock outcome with `commander_survived=False`)
- At least one delta-based rotation (should happen naturally in a 6-mission run)
- At least one crisis veto (if one occurs — may need specific seed selection)
- Pool selection breakdown: how many times each pool (previous/nemesis/unrelated) was used
- For any cross-faction rotation: show the old faction → new faction transition

**Verify:** Lineage persistence holds for 2+ chapters in most cases. Rotation reasons are logged and make sense. Forced rotation fires when expected. The commander selected is appropriate for the mission region (lives in or near it). No lineage persists beyond the hard cap. The first mission uses the unrelated pool. Cross-faction rotation is possible at the hard cap (may not occur every run — verify across 3 seeds).

**⛔ STOP. Show output. Wait for Westley.**

---

### Checkpoint H — Invariants and Multi-Seed Validation (Final)

**Build:** `invariants.py` — all Group M invariants. Full scenario suite (scenarios 12–16).

**Test:** Run all scenarios across 3+ seeds. Run the full invariant suite.

**Print:**
- M1–M18 pass/fail for each scenario × seed
- Any invariant failures with the specific values that violated the constraint
- Regression check: A through L invariants all passing
- Summary: total invariants checked, total passed, total failed

**Verify:** All M1–M18 pass. All prior invariants pass. If any fail, the specific failure is diagnosed before proceeding — do not patch around failures.

**⛔ STOP. Show output. Wait for Westley. This is the stage gate — Westley reviews the full Mission Generation Review Reports across 3+ seeds and signs off before Stage 5.5 is complete.**

---

## Shared Contracts Design

The `mission_contracts.py` module is the single source of truth for data crossing the Stage 5.5 ↔ Stage 6 boundary. Both stages import it. Neither stage defines its own version of these structures.

**Why a shared module:** When two workstreams are built in parallel, the risk is subtle data structure drift — one side adds a field, renames an enum value, or changes a type, and the other side doesn't notice until integration. A shared module eliminates this class of bug: if Stage 6's `objectives.py` tries to construct a `MissionResult` with a field that doesn't exist in the contract, the code fails at import time, not at integration time.

**Ownership:** The contracts module is authored during Stage 5.5 spec implementation (this stage). Stage 6's spec is updated to import from it rather than defining its own equivalent structures. Changes to the contracts require agreement from both workstreams — in practice, this means Westley reviews any proposed contract change before either side implements it.

**Stage 6 integration points:**
- `objectives.py` constructs and returns a `MissionResult` after outcome classification.
- `power_rating.py` is called by `force_allocator.py` to compute per-unit power ratings. The power rating function's signature is part of the contract: `compute_power_rating(stats: dict) → float`.
- `tactical_engine.py` accepts a `MissionSetup` to initialize a mission (map + units + objectives + reinforcements + behavior script).

---

## Mission Generator Design

### Trigger Condition Reference

Each archetype's trigger is a pure function evaluated against simulation state. The trigger functions are the only place where archetype-specific simulation logic exists — everything else (scoring, selection, allocation) is archetype-agnostic.

| Archetype | Trigger Condition |
|-----------|-------------------|
| Defensive Stand | Active attack event targeting a player region |
| Siege Breaking | Region under sustained border friction (military and economy declining, hostile high-military neighbor) for >N ticks (config) |
| Reconquest | Player region conquered within last time jump (conquest event in recent event log) |
| Assault | Player faction agent has identified an enemy region as an attack target (attack scored highest in attractiveness, passed confidence threshold) |
| Suppression | Breakaway faction holds a region adjacent to player territory, breakaway age < N ticks (config) |
| Multi-Front Defense | Two or more active attack events targeting the same player region, or high-military hostile factions on multiple borders of the same region |
| Interception | Attack event targeting a player region where the attacker must traverse intervening space (attacker and target not adjacent) |
| Evacuation | Player region with military < EVAC_MILITARY_THRESHOLD, economy < EVAC_ECONOMY_THRESHOLD, stability < EVAC_STABILITY_THRESHOLD, adjacent to high-military hostile faction |
| Containment | Rapidly expanding hostile faction (gained 2+ regions in last time jump) with territory adjacent to player borders |
| Counterinsurgency | Player-held region with active revolt event chains (tension above revolt threshold, ongoing resistance or conquest unrest) |

### Urgency Scoring

Urgency is computed per region, independent of archetype. It reflects how badly the region needs attention right now.

```
urgency = clamp(0, 1,
    w_field * field_deficit_score +
    w_conflict * conflict_intensity +
    w_chain * chain_criticality
)
```

- `field_deficit_score`: average of `(100 - military)/100`, `(100 - economy)/100`, `(100 - stability)/100`, weighted by field importance (military weighted highest for military archetypes — but this is the archetype-agnostic urgency, so equal weights).
- `conflict_intensity`: normalized count and strength of hostile actions against this region (attacks, border friction, recent territory loss). 0 = peaceful, 1 = active assault.
- `chain_criticality`: fraction of active event chains in this region that are in their final stage or approaching a threshold trigger. 0 = no critical chains, 1 = imminent collapse.

All sub-weights are config values.

### Relevance Scoring

Relevance is computed per (region, archetype) pair. It reflects how connected this commander and lineage are to this specific problem.

```
relevance = clamp(0, 1,
    w_lineage * lineage_connection +
    w_proximity * proximity_score +
    w_archetype * archetype_fit
)
```

- `lineage_connection`: 1.0 if a lineage member currently resides in this region, 0.5 if a lineage member has historically operated here (from `get_lineage_history()`), 0.0 otherwise.
- `proximity_score`: `1.0 - (hop_distance / max_hops)` where `hop_distance` is the shortest path in the region adjacency graph from the lineage home region to the candidate region. Capped at `max_hops` (config, default 5).
- `archetype_fit`: `min(1.0, archetype_count / archetype_fit_threshold)` where `archetype_count` is how many times this lineage has been assigned this archetype (from `get_lineage_archetype_history()`), and `archetype_fit_threshold` is a config value (default 3). A lineage that has done 3+ missions of this type is a perfect fit.

All sub-weights are config values.

### Asset Profile Reference

Each archetype defines a target unit type ratio. These are normalized to sum to 1.0 and represent the *desired* proportion of total force power allocated to each unit type.

| Archetype | Raider | Interceptor | Vanguard | Warden | Bombard | Bastion |
|-----------|--------|-------------|----------|--------|---------|---------|
| Defensive Stand | 0.05 | 0.10 | 0.15 | 0.15 | 0.15 | 0.40 |
| Siege Breaking | 0.15 | 0.10 | 0.25 | 0.10 | 0.20 | 0.20 |
| Reconquest | 0.20 | 0.10 | 0.30 | 0.10 | 0.20 | 0.10 |
| Assault | 0.15 | 0.15 | 0.25 | 0.10 | 0.25 | 0.10 |
| Suppression | 0.25 | 0.20 | 0.25 | 0.10 | 0.05 | 0.15 |
| Multi-Front Defense | 0.10 | 0.15 | 0.20 | 0.15 | 0.15 | 0.25 |
| Interception | 0.25 | 0.20 | 0.25 | 0.10 | 0.10 | 0.10 |
| Evacuation | 0.10 | 0.05 | 0.10 | 0.15 | 0.05 | 0.55 |
| Containment | 0.05 | 0.15 | 0.15 | 0.20 | 0.10 | 0.35 |
| Counterinsurgency | 0.25 | 0.25 | 0.20 | 0.15 | 0.05 | 0.10 |

These ratios are config values and will be tuned during playtesting.

---

## Outcome Resolver Design

### Proportional Delta Semantics

The consequence tables use two delta forms, matching the bible's authored success spectrums exactly:

- **"+X% of deficit"** — the field gains a fraction of its distance from 100. `delta = (100 - current_value) × X / 100`. A region at military 20 gets a bigger absolute boost than a region at military 80. This models "recovery" — the more damaged you are, the more impact a success has.
- **"-X% of current"** — the field loses a fraction of its current value. `delta = -(current_value × X / 100)`. A strong region loses more in absolute terms than a weak one. This models "degradation" — you lose proportional to what you have.
- **"+X% of deficit from 100"** — identical to "+X% of deficit" (the bible uses both phrasings interchangeably for tension, where higher tension is worse and "deficit from 100" clarifies that tension rising is bad).

### Consequence Table Structure

Each archetype's consequence table is a config dictionary mapping outcome band → list of field deltas. Each delta specifies: field name, delta form ("deficit" or "current"), percentage, and target region ("mission" for the mission region, "adjacent_player" for all adjacent player regions, etc.).

Example (Defensive Stand):

```python
CONSEQUENCE_TABLES = {
    "defensive_stand": {
        "total_success": [
            {"field": "military",  "form": "deficit", "pct": 15, "target": "mission"},
            {"field": "tension",   "form": "current", "pct": -10, "target": "mission"},
            {"field": "economy",   "form": "current", "pct": -2, "target": "mission"},
        ],
        "strong_success": [
            {"field": "military",  "form": "deficit", "pct": 8, "target": "mission"},
            {"field": "tension",   "form": "current", "pct": -5, "target": "mission"},
            {"field": "economy",   "form": "current", "pct": -5, "target": "mission"},
        ],
        # ... partial_success, partial_failure, total_failure
    },
    # ... all 10 archetypes
}
```

The full consequence tables for all 10 archetypes are transcribed directly from docs/bible_history/bible_2_00_missions.md's success spectrums into this config structure. No interpretation or modification — the bible values are authoritative.

### Special Case: Reconquest Region Transfer

Reconquest total success and strong success transfer the region back to the player faction. The outcome resolver sets the region's faction_id to the player's faction and applies the conquest resolution mechanics (garrison placement, tension spike) from Stage 3, then applies the Reconquest-specific field deltas on top. Partial failure and total failure leave the region under enemy control — field deltas apply to adjacent player regions instead.

### Special Case: Assault Region Conquest

Assault total success and strong success trigger a conquest event (the same conquest resolution path from Stage 3). The region transfers to the player faction. Partial success does not transfer the region but damages the defender.

---

## Force Allocation Design

### Power Rating Integration

The force allocator imports Stage 6's `power_rating.py` and calls `compute_power_rating(stats)` for every unit it considers. This means force allocation uses the exact same strength values that the tactical engine uses for outcome classification's force retention component. No separate approximation — one formula, one module, one source of truth.

During Stage 5.5 validation (before Stage 6 is complete), the power rating module is built first as a dependency. It's a pure function with no tactical engine dependencies — it takes unit stats and returns a float. Both stages can import it from day one.

### Allocation Algorithm Detail

```
1. Compute enemy_power_total (from committed budget or threat military)
2. Compute parity_ratio (from capacity composite + difficulty)
3. player_power_budget = enemy_power_total × parity_ratio
4. For each unit type in the asset profile (ordered by ratio, highest first):
   a. target_power = player_power_budget × ratio_for_this_type
   b. While allocated_power < target_power and budget remaining:
      i. Select a unit of this type from the faction roster
      ii. Compute its power rating
      iii. Add to force, subtract from budget
5. If capacity shortfall flag is set:
   a. Remove units proportionally until force total ≤ shortfall_budget
   b. Record which types were reduced for the briefing
6. Assemble ForceComposition with all selected units
```

### Enemy Force Assembly

Enemy forces follow the same algorithm but skip the parity adjustment — they get exactly their committed budget's worth of units. For multi-faction missions, each hostile faction assembles its own force independently from its own roster and budget.

### Canvas Size Determination

The allocator computes the canvas size category from the archetype's base size plus simulation modifiers, per docs/bible_history/bible_2_00_missions.md:

| Archetype | Base Size | Simulation Modifier |
|-----------|-----------|---------------------|
| Defensive Stand | Medium | Wealthier regions → larger |
| Siege Breaking | Large | Longer siege → smaller |
| Reconquest | Medium | Higher pre-conquest development → larger |
| Assault | Large | More developed enemy → larger |
| Suppression | Small | Higher pre-revolt development → slightly larger |
| Multi-Front Defense | Large | More factions involved → larger |
| Interception | Medium | Larger enemy budget → larger |
| Evacuation | Medium | Higher remaining population → larger |
| Containment | Large | More border regions at risk → larger |
| Counterinsurgency | Small–Medium | Higher tension → larger |

The modifier adjusts within the size category's range (e.g., a "medium" canvas ranges from 6000×6000 to 10000×10000, with the modifier selecting within that range). Exact breakpoints are config values.

---

## Character Selector Design

The character selector is the mechanism that makes the generational structure feel generational. It determines whether the player continues as a descendant of the same family or rotates to a new lineage, and then selects the specific commander for the next mission. The selector runs after the time jump and after the mission generator — the mission region is already decided, and the selector finds the best commander for that mission.

### Why 2–4 Chapters Per Lineage

The 2–4 chapter persistence range (soft target, hard cap at ~6) is a core design commitment. It produces the game's signature emotional arc: the player spends enough time with one family to build attachment and see consequences compound, then rotates to experience the world from a different vantage point. Too short (1 chapter per lineage) and the player never connects with anyone. Too long (10+ chapters) and the player loses the generational perspective. The 2–4 range is where the generational structure produces its best emotional beats:

- Chapter 1 with a lineage: establishment. The player meets the family, learns their region, fights their first battle.
- Chapter 2–3: investment. The player sees consequences from their first mission. The family name means something. The chronicle references their ancestor.
- Chapter 3–4: culmination or departure. Either the family's story reaches a natural climax, or the world's attention shifts. Both are meaningful.

The rotation itself is a narrative event — the chronicle frames it, the next lineage connects to the old one, and the player carries institutional memory even as their character changes.

### Rotation Decision Detail

The rotation decision is a priority cascade, not a single formula:

```
1. FORCED ROTATION
   - bloodline extinct (no living members) → rotate
   - commander KIA and no family successor in/near mission region → rotate

2. MINIMUM STAY
   - chapter_counter < SELECTOR_MIN_CHAPTERS (default 2) → stay

3. HARD CAP
   - chapter_counter >= SELECTOR_HARD_CAP (default 6) → rotate
   - (at hard cap, cross-faction candidates are eligible)

4. DELTA-BASED PROBABILITY
   - Compute region_delta = sum of abs(field changes) across lineage home
     region + adjacent regions during the time jump
   - Map to rotation_probability via interpolation:
     delta = 0   → probability = SELECTOR_MAX_ROTATION_PROB (default 0.8)
     delta = SELECTOR_DELTA_SAFE (default 200) → probability = SELECTOR_MIN_ROTATION_PROB (default 0.1)
   - Roll rng.random() < rotation_probability
   - If rotation triggered → check crisis veto:
     - If home region stability < SELECTOR_CRISIS_THRESHOLD (default 20)
       OR active event chain in critical stage → veto rotation, stay
   - If not vetoed → rotate
```

### Lineage Selection Detail

When rotation occurs, the selector picks a lineage from three pools:

```
1. Roll pool selection: rng.random() against cumulative weights
   [0, 0.7) → previous_descendant pool
   [0.7, 0.9) → nemesis_descendant pool
   [0.9, 1.0) → unrelated pool

2. PREVIOUS DESCENDANT POOL
   - For each previous lineage the player has played:
     - Find living descendants in or adjacent to mission_region
     - Score: recency_penalty × descendant_count × gap_bonus
       - recency_penalty: 0.0 if this was the immediately previous lineage,
         scaling up to 1.0 at 3+ lineages ago
       - descendant_count: count of living members in/near mission region
       - gap_bonus: peaks at 3–5 chapters ago, lower for very recent
         or very distant
     - Weighted random draw from scored candidates
   - If pool empty → fall through to nemesis pool

3. NEMESIS DESCENDANT POOL
   - Query coherence ledger for characters tagged as rivals/antagonists
     to any previous commander
   - Find their descendants in or near mission_region
   - Random selection from candidates
   - If pool empty → fall through to unrelated pool

4. UNRELATED POOL
   - Generate a new character in mission_region via coherence ledger
   - New lineage created, new family name from naming system
   - Always succeeds (fallback)
```

### Faction Collapse Reassignment

When the player's faction collapses (zero regions), the selector uses modified logic:

1. Evaluate all surviving factions.
2. Score each by narrative connection: previous lineage descendants in their territory (highest weight), nemesis connections, geographic proximity to the fallen faction's former regions.
3. If no narrative connection, select the faction with most territorial overlap with the player's former regions.
4. The selected faction becomes the player's new faction. The character selector then runs its normal lineage selection within that faction's territory.

### Integration with Generational Loop

The generational loop (in `generational.py`) becomes:

```
mission → outcome resolver → time jump (N ticks + chronicle) → mission generator → character selector → next mission
```

The character selector runs *after* the mission generator because it needs the mission region to make its selection. The mission generator doesn't care who the commander is — it selects based on simulation pressure. The character selector finds the best person to send to the already-selected mission.

---

## Behavioral Claims

### Mission Generation

**Claim M1: Every generated mission responds to a real simulation condition.** No mission is generated without at least one archetype trigger condition being met in the simulation state.
- When: Run mission generator after any time jump
- Then: The selected (region, archetype) pair's trigger condition evaluates to True against the current simulation state
- Over: 50+ generated missions across all scenarios
- Pattern: invariant
- Severity: critical

**Claim M2: Urgency dominates in crisis.** When the world's worst region urgency exceeds 0.8, the selected mission should target a high-urgency region (top 3 by urgency) in >80% of cases, regardless of relevance and preference scores.
- When: At least one region with urgency > 0.8
- Then: Selected region is in the top 3 by urgency >80% of the time
- Over: 20+ crisis-state generations
- Pattern: relational constraint
- Severity: warning (tuning target)

**Claim M3: Preference influences selection in calm periods.** When no region has urgency above 0.5, preferred archetypes should be selected at a higher rate than non-preferred archetypes.
- When: All regions with urgency < 0.5, player has set archetype preferences
- Then: Preferred archetypes appear >2× as often as non-preferred archetypes
- Over: 30+ calm-state generations
- Pattern: relational constraint
- Severity: warning (tuning target)

**Claim M4: Rare archetypes are rare but not impossible.** Archetypes marked "rare" by the player should appear in <10% of missions during calm periods but can still appear during crisis.
- When: Archetype marked rare, calm periods
- Then: Rare archetype selected <10% of the time
- Over: 50+ generations
- Pattern: threshold bound
- Severity: warning

### Force Allocation

**Claim M5: Force parity produces winnable fights.** Player force total power should be within the configured parity range of enemy force total power.
- When: Any generated mission
- Then: `parity_ratio_min ≤ player_total_power / enemy_total_power ≤ 1.05` (slight overrun from the last-unit-added tolerance)
- Over: all generated missions
- Pattern: threshold bound
- Severity: critical

**Claim M6: Asset profile is respected.** The generated force's unit type distribution should be within 15% of the archetype's target asset profile for each unit type.
- When: Any generated mission with sufficient budget to fill the profile
- Then: For each unit type, `|actual_ratio - target_ratio| < 0.15`
- Over: all generated missions
- Pattern: threshold bound
- Severity: warning (small forces may deviate more due to granularity)

**Claim M7: Capacity shortfalls reduce quantity, not quality.** When capacity is below the shortfall threshold, the force should have fewer units but each unit should have the same stats as in a full-capacity mission.
- When: Capacity composite below shortfall threshold
- Then: Individual unit stats are identical to full-capacity units. Force size is reduced.
- Over: paired comparisons (same archetype, same seed, different capacity)
- Pattern: relational constraint
- Severity: critical

**Claim M8: Difficulty affects parity, not enemy strength.** Across Easy/Medium/Hard with the same simulation state, the enemy force should be identical. Only the player's force changes.
- When: Same simulation state, same seed, different difficulty settings
- Then: Enemy force composition and total power are identical across difficulties. Player force total power varies per difficulty.
- Over: all 3 difficulties
- Pattern: relational constraint
- Severity: critical

### Outcome Resolution

**Claim M9: Proportional deltas scale with region state.** The same outcome band applied to a region at military 20 should produce a larger absolute military delta than the same band applied to a region at military 80 (for "deficit" form deltas).
- When: Same archetype, same outcome band, different region military values
- Then: Region with lower military gets larger absolute delta for deficit-form deltas
- Over: paired comparisons across all archetypes
- Pattern: relational constraint
- Severity: critical

**Claim M10: All 5 outcome bands produce distinct consequences.** For each archetype, the 5 outcome bands should produce measurably different field deltas.
- When: Same region state, all 5 outcome bands applied
- Then: No two bands produce identical field deltas
- Over: all 10 archetypes
- Pattern: invariant
- Severity: critical

**Claim M11: Commander death is logged.** When `commander_survived` is false, the coherence ledger should mark the commander as dead and a `COMMANDER_KILLED_IN_ACTION` event should appear in the event log.
- When: MissionResult with commander_survived=False
- Then: Ledger commander status is "dead", KIA event in log with mission_consequence=True
- Over: all archetypes
- Pattern: invariant
- Severity: critical

**Claim M12: Consequence events have mission_consequence flag.** All events injected by the outcome resolver must carry the mission_consequence flag so the chronicle distiller can identify them.
- When: Any mission result processed
- Then: All resolver-injected events have mission_consequence=True
- Over: all scenarios
- Pattern: invariant
- Severity: critical

### Character Selector

**Claim M14: Lineage persists for at least SELECTOR_MIN_CHAPTERS.** The player should not rotate to a new lineage before completing the minimum chapter count, unless forced by bloodline extinction or commander death with no successor.
- When: Rotation decision runs
- Then: If chapter_counter < SELECTOR_MIN_CHAPTERS, rotation does not occur (unless forced)
- Over: all rotation decisions
- Pattern: threshold bound
- Severity: critical

**Claim M15: Lineage rotates at the hard cap.** No lineage should persist beyond SELECTOR_HARD_CAP chapters.
- When: Rotation decision runs with chapter_counter >= SELECTOR_HARD_CAP
- Then: Rotation always occurs
- Over: all rotation decisions at the cap
- Pattern: threshold bound
- Severity: critical

**Claim M16: Commander is near the mission region.** The selected commander should reside in the mission region or within SELECTOR_PROXIMITY_HOPS adjacency hops.
- When: Commander selected
- Then: Commander's region is within configured hop distance of mission region
- Over: all commander selections
- Pattern: threshold bound
- Severity: warning (unrelated pool may generate in the exact mission region, but previous/nemesis pools search "near" the region)

**Claim M17: First mission uses unrelated pool.** When no previous lineages exist, the selector should always use the unrelated pool.
- When: First mission of a playthrough (no previous lineages)
- Then: pool_used == "unrelated"
- Over: all playthroughs
- Pattern: invariant
- Severity: critical

**Claim M18: Faction collapse triggers reassignment.** When the player's faction has zero regions, the selector should assign the player to a surviving faction.
- When: Player faction region count == 0
- Then: Selected commander belongs to a faction with ≥1 region
- Over: all faction collapse events
- Pattern: invariant
- Severity: critical

### Regression

**Claim M19: All Stage 5 invariants still pass.** No regression in previously validated behavior.
- Over: full run
- Pattern: regression check
- Severity: critical

---

## Validation — Mission Generation Review Report

The Mission Generation Review Report is the primary validation mechanism for mission selection quality, force composition feel, and outcome resolution correctness. Like the Chronicle Review Report (Stage 5) and Tactical Review Report (Stage 6), it is designed for human review.

### Report Generation

`sim_tuner.py` gains a `--mission-review` flag:

```bash
python sim_tuner.py --scenario 12_mission_generation --mission-review --seeds 1,2,3
```

### Report Format

```
════════════════════════════════════════════════════════════════
MISSION GENERATION: Scenario 12 / Seed 1 / Jump 3
════════════════════════════════════════════════════════════════

── Candidate Pool ──────────────────────────────────────────────
  Candidates found: 7
  1. (Region: Kepler Reach,    Archetype: Defensive Stand)   Score: 0.83  [SELECTED]
     Urgency: 0.91  Relevance: 0.72  Preference: 0.80
  2. (Region: Outer Periphery, Archetype: Containment)       Score: 0.71
     Urgency: 0.78  Relevance: 0.55  Preference: 0.50
  3. (Region: Kepler Reach,    Archetype: Multi-Front Def.)  Score: 0.68
     Urgency: 0.91  Relevance: 0.72  Preference: 0.10 (rare)
  ...

── Selected Mission ────────────────────────────────────────────
  Region: Kepler Reach (military: 23, economy: 41, tension: 72, stability: 18)
  Archetype: Defensive Stand
  Trigger: Active attack from faction "Iron Dominion" (budget: 340)

── Force Composition ───────────────────────────────────────────
  Enemy Force (Iron Dominion):
    12 Vanguard, 8 Bastion, 6 Bombard, 4 Raider | Total power: 5420

  Player Force:
    Parity ratio: 0.88 (capacity: 0.62, difficulty: medium)
    Player budget: 4770
    2 Raider, 4 Interceptor, 6 Vanguard, 6 Warden, 6 Bombard, 14 Bastion | Total power: 4740
    Asset profile deviation: max 0.08 (within tolerance)
    Shortfall: 2 Bastion slots unfilled (briefing notes: "Regional garrisons stretched thin")

  Reinforcements:
    4 structures (2 player, 1 enemy, 1 neutral)

── Briefing Preview ────────────────────────────────────────────
  SITUATION: The Iron Dominion has committed a substantial assault force
  against Kepler Reach. Regional stability is precarious — the garrison
  has been bled by months of border skirmishing. Commander Vasik Torel,
  your predecessor's protégé, held this sector for two generations. Now
  it falls to you.

  OBJECTIVE: Hold Kepler Reach against the incoming assault. The
  Dominion's force is committed — they will not withdraw until spent
  or destroyed.

  ASSETS: Command has allocated a defensive force weighted toward
  fortification. Regional garrisons are stretched thin — the full
  Bastion complement could not be assembled. Local military
  infrastructure is moderate; expect steady but limited reinforcement.

── Outcome Resolution Preview (all 5 bands) ────────────────────
  Region state: military=23, economy=41, tension=72, stability=18
  Total success:   military +11.6, tension -7.2,  economy -0.8
  Strong success:  military +6.2,  tension -3.6,  economy -2.1
  Partial success: military -1.2,  tension +1.4,  economy -4.1
  Partial failure: military -3.5,  tension +2.8,  economy -6.2
  Total failure:   military -6.9,  tension +5.6,  economy -8.2, population -4.6

════════════════════════════════════════════════════════════════
```

### Review Workflow

1. Run `sim_tuner.py --mission-review` across the scenario set.
2. Read the reports. Evaluate: Do the right missions get selected? Do urgency/relevance/preference scores feel reasonable? Does the force composition match the archetype? Do parity ratios feel fair? Does the briefing read well? Do consequence deltas feel proportionate?
3. Provide feedback. Adjust config weights, trigger thresholds, asset profiles, or consequence percentages as needed.
4. Re-run until the mission generation feels right.

---

## Scenarios

```python
"12_mission_basic": {
    "template":     "four_way",
    "ticks":        1500,
    "seed":         1,
    "description":  "Basic mission generation — 4 factions, 1500 ticks, generate missions at each time jump",
    "use_tick_engine": True,
    "features": {
        "events": True, "factions": True, "border_friction": True,
        "recruitment": True, "adjacency_bonus": True, "oscillation": True,
        "technology": True, "diplomacy": True, "admin_revolts": True,
        "chronicle": True, "coherence_ledger": True, "naming": True,
        "missions": True,
    },
    "mission_review_jumps": [1, 2, 3],
    "mock_outcome_bands": ["strong_success", "partial_success", "partial_failure"],
},

"13_mission_crisis": {
    "template":     "pressure_cooker",
    "ticks":        1000,
    "seed":         1,
    "description":  "Crisis mission generation — aggressive factions, high urgency, verify urgency dominance",
    "use_tick_engine": True,
    "features": {
        "events": True, "factions": True, "border_friction": True,
        "recruitment": True, "adjacency_bonus": True, "oscillation": True,
        "technology": True, "diplomacy": True, "admin_revolts": True,
        "chronicle": True, "coherence_ledger": True, "naming": True,
        "missions": True,
    },
    "mission_review_jumps": [1, 2, 3],
    "mock_outcome_bands": ["partial_failure", "total_failure", "partial_success"],
},

"14_mission_calm": {
    "template":     "stable_world",
    "ticks":        2000,
    "seed":         1,
    "description":  "Calm-state mission generation — stable factions, verify preference/relevance influence",
    "use_tick_engine": True,
    "features": {
        "events": True, "factions": True, "border_friction": True,
        "recruitment": True, "adjacency_bonus": True, "oscillation": True,
        "technology": True, "diplomacy": True, "admin_revolts": True,
        "chronicle": True, "coherence_ledger": True, "naming": True,
        "missions": True,
    },
    "mission_review_jumps": [1, 2, 3, 4, 5],
    "mock_outcome_bands": ["total_success", "strong_success", "strong_success", "partial_success", "strong_success"],
    "player_preferences": {"defensive_stand": 0.9, "assault": 0.8, "evacuation": "rare", "multi_front_defense": "rare"},
},

"15_outcome_resolver": {
    "template":     "four_way",
    "ticks":        500,
    "seed":         1,
    "description":  "Outcome resolver validation — apply all 5 bands to varied region states, verify proportional scaling",
    "use_tick_engine": True,
    "features": {
        "events": True, "factions": True, "border_friction": True,
        "recruitment": True, "adjacency_bonus": True, "oscillation": True,
        "chronicle": True, "coherence_ledger": True, "naming": True,
        "missions": True,
    },
    "test_all_bands": True,
    "test_all_archetypes": True,
},

"16_force_allocation_difficulty": {
    "template":     "four_way",
    "ticks":        500,
    "seed":         1,
    "description":  "Force allocation difficulty test — same state, all 3 difficulties, verify enemy invariance and player scaling",
    "use_tick_engine": True,
    "features": {
        "events": True, "factions": True, "border_friction": True,
        "recruitment": True, "adjacency_bonus": True, "oscillation": True,
        "chronicle": True, "coherence_ledger": True, "naming": True,
        "missions": True,
    },
    "test_difficulties": ["easy", "medium", "hard"],
},
```

---

## Config Values to Add

```python
# ── Mission generator (Stage 5.5) ─────────────────────────────
GENERATOR_URGENCY_WEIGHT            = 0.5     # w1 in scoring formula
GENERATOR_RELEVANCE_WEIGHT          = 0.3     # w2 in scoring formula
GENERATOR_PREFERENCE_WEIGHT         = 0.2     # w3 in scoring formula
GENERATOR_TOP_N_CANDIDATES          = 5       # candidates in final weighted draw
GENERATOR_DEFAULT_PREFERENCE        = 0.5     # preference score for unmarked archetypes
GENERATOR_RARE_PREFERENCE           = 0.1     # preference score for "rare" archetypes

# ── Urgency scoring (Stage 5.5) ───────────────────────────────
URGENCY_FIELD_WEIGHT                = 0.4     # weight of field deficit in urgency
URGENCY_CONFLICT_WEIGHT             = 0.4     # weight of conflict intensity in urgency
URGENCY_CHAIN_WEIGHT                = 0.2     # weight of chain criticality in urgency

# ── Relevance scoring (Stage 5.5) ─────────────────────────────
RELEVANCE_LINEAGE_WEIGHT            = 0.4     # weight of lineage connection
RELEVANCE_PROXIMITY_WEIGHT          = 0.3     # weight of regional proximity
RELEVANCE_ARCHETYPE_WEIGHT          = 0.3     # weight of archetype fit
RELEVANCE_MAX_HOPS                  = 5       # max adjacency hops for proximity scoring
RELEVANCE_ARCHETYPE_FIT_THRESHOLD   = 3       # missions of this type before lineage is "expert"

# ── Trigger thresholds (Stage 5.5) ────────────────────────────
SIEGE_BREAKING_MIN_TICKS            = 200     # minimum ticks of sustained border friction
SUPPRESSION_MAX_AGE                 = 300     # maximum breakaway age for Suppression trigger
EVAC_MILITARY_THRESHOLD             = 15      # military below this for Evacuation trigger
EVAC_ECONOMY_THRESHOLD              = 20      # economy below this for Evacuation trigger
EVAC_STABILITY_THRESHOLD            = 15      # stability below this for Evacuation trigger
CONTAINMENT_EXPANSION_THRESHOLD     = 2       # regions gained in last jump for Containment trigger

# ── Force allocation (Stage 5.5) ──────────────────────────────
BUDGET_TO_POWER_SCALE               = 15.0    # committed budget → enemy power total
MILITARY_TO_POWER_SCALE             = 60.0    # military field → enemy power total (non-budget archetypes)
PARITY_BREAKPOINTS                  = [       # capacity composite → base parity ratio
    (0.0, 0.80),   # collapsed civilization: 80% parity
    (0.3, 0.85),   # struggling: 85%
    (0.5, 0.90),   # declining: 90%
    (0.7, 0.95),   # stable: 95%
    (1.0, 1.00),   # thriving: 100%
]
PARITY_EASY_FLOOR                   = 0.95    # Easy difficulty: parity never below 95%
PARITY_HARD_CEILING                 = 0.85    # Hard difficulty: parity never above 85%
CAPACITY_SHORTFALL_THRESHOLD        = 0.4     # capacity below this triggers shortfall
CAPACITY_SHORTFALL_REDUCTION        = 0.20    # fraction of units removed at shortfall

# ── Canvas size ranges (Stage 5.5) ────────────────────────────
CANVAS_SIZE_RANGES = {
    "small":  (4000, 6000),     # width/height range in world units
    "medium": (6000, 10000),
    "large":  (10000, 14000),
}

# ── Reinforcement structures (Stage 5.5) ──────────────────────
MILITARY_TO_STRUCTURES_SCALE        = 0.06    # region military → structure count
STRUCTURE_COUNT_RANGE = {
    "small":  (2, 4),
    "medium": (3, 6),
    "large":  (4, 8),
}
STRUCTURE_PRODUCTION_RATE           = 0.022   # units per second per structure (~1 per 45 sec)

# ── Asset profiles (Stage 5.5) ────────────────────────────────
# See Asset Profile Reference table — stored as config dict
ASSET_PROFILES = {
    "defensive_stand":     {"Raider": 0.05, "Interceptor": 0.10, "Vanguard": 0.15, "Warden": 0.15, "Bombard": 0.15, "Bastion": 0.40},
    "siege_breaking":      {"Raider": 0.15, "Interceptor": 0.10, "Vanguard": 0.25, "Warden": 0.10, "Bombard": 0.20, "Bastion": 0.20},
    "reconquest":          {"Raider": 0.20, "Interceptor": 0.10, "Vanguard": 0.30, "Warden": 0.10, "Bombard": 0.20, "Bastion": 0.10},
    "assault":             {"Raider": 0.15, "Interceptor": 0.15, "Vanguard": 0.25, "Warden": 0.10, "Bombard": 0.25, "Bastion": 0.10},
    "suppression":         {"Raider": 0.25, "Interceptor": 0.20, "Vanguard": 0.25, "Warden": 0.10, "Bombard": 0.05, "Bastion": 0.15},
    "multi_front_defense": {"Raider": 0.10, "Interceptor": 0.15, "Vanguard": 0.20, "Warden": 0.15, "Bombard": 0.15, "Bastion": 0.25},
    "interception":        {"Raider": 0.25, "Interceptor": 0.20, "Vanguard": 0.25, "Warden": 0.10, "Bombard": 0.10, "Bastion": 0.10},
    "evacuation":          {"Raider": 0.10, "Interceptor": 0.05, "Vanguard": 0.10, "Warden": 0.15, "Bombard": 0.05, "Bastion": 0.55},
    "containment":         {"Raider": 0.05, "Interceptor": 0.15, "Vanguard": 0.15, "Warden": 0.20, "Bombard": 0.10, "Bastion": 0.35},
    "counterinsurgency":   {"Raider": 0.25, "Interceptor": 0.25, "Vanguard": 0.20, "Warden": 0.15, "Bombard": 0.05, "Bastion": 0.10},
}

# ── Consequence tables (Stage 5.5) ────────────────────────────
# Full tables transcribed from docs/bible_history/bible_2_00_missions.md — see Outcome Resolver Design section
# CONSEQUENCE_TABLES dict defined in config, one entry per archetype, 5 bands per entry

# ── Character selector (Stage 5.5) ────────────────────────────
SELECTOR_MIN_CHAPTERS               = 2       # minimum chapters before rotation is eligible
SELECTOR_HARD_CAP                   = 6       # maximum chapters before forced rotation
SELECTOR_DELTA_SAFE                 = 200     # total region delta above which rotation probability is minimal
SELECTOR_MAX_ROTATION_PROB          = 0.8     # rotation probability when delta is 0 (quiet jump)
SELECTOR_MIN_ROTATION_PROB          = 0.1     # rotation probability when delta >= DELTA_SAFE
SELECTOR_CRISIS_THRESHOLD           = 20      # stability below this vetoes rotation
SELECTOR_POOL_PREVIOUS_WEIGHT       = 0.70    # probability of drawing from previous lineage pool
SELECTOR_POOL_NEMESIS_WEIGHT        = 0.20    # probability of drawing from nemesis pool
SELECTOR_POOL_UNRELATED_WEIGHT      = 0.10    # probability of drawing from unrelated pool
SELECTOR_RECENCY_PENALTY_WINDOW     = 1       # lineages played within this many rotations get 0 recency score
SELECTOR_GAP_BONUS_PEAK             = 4       # chapters ago at which gap bonus peaks
SELECTOR_PROXIMITY_HOPS             = 2       # max adjacency hops for "near mission region" candidate search
```

---

## Stage 6 Modifications for Parallel Development

The following changes to the Stage 6 spec enable parallel development:

1. **Import `mission_contracts.py` for all shared types.** `objectives.py` constructs and returns a `MissionResult` (from contracts) instead of defining its own output structure. `tactical_engine.py` accepts a `MissionSetup` (from contracts) to initialize missions instead of an ad-hoc parameter set.

2. **`power_rating.py` becomes a shared dependency.** Its function signature `compute_power_rating(stats: dict) → float` is part of the contract. Stage 6 implements it; Stage 5.5 imports and calls it. The module has zero dependencies on the tactical engine — it's a pure function of unit stats.

3. **`tactical_engine.py` initialization from `MissionSetup`.** The engine's `initialize_mission()` method accepts a `MissionSetup` and extracts: map parameters → `tactical_map.py`, player/enemy forces → unit arrays, objectives → `objectives.py`, reinforcements → reinforcement structure placement, behavior script ID → enemy macro behavior system (Stage 7; placeholder for Stage 6). This replaces any ad-hoc initialization the Stage 6 spec may have assumed.

4. **`objectives.py` output as `MissionResult`.** At mission end, the outcome classifier packages its results into a `MissionResult` and returns it. The `commander_survived` field is computed from whether the player's designated commander unit (flagged in `MissionSetup`) has HP > 0 at mission end.

5. **Update "Files NOT to create or modify" in Stage 6.** Remove references to "mission outcome resolver" and "force allocation algorithm" from Stage 6's boundary — these are now explicitly Stage 5.5's responsibility. Stage 6's boundary statement should read: "The mission generator, mission outcome resolver, force allocation algorithm, and mission briefing templates are Stage 5.5. Stage 6 imports shared data structures from `mission_contracts.py`."

6. **Update Stage 6 Cross-Stage References.** The Stage 5.5 entry should reference the shared contracts module and clarify that `power_rating.py` is built in Stage 6 but imported by Stage 5.5.

7. **Stage 7 Cross-Stage Reference update.** Remove "per-archetype enemy scripted behaviors (advance, defend, patrol, ambush, retreat)" from Stage 7's roadmap description. Enemy macro behavior uses a shared behavior script system with reactive hooks, not per-archetype state machines. Stage 7 builds the behavior script *content* (authored scripts per archetype) using the infrastructure defined in `docs/bible_history/bible_2_00_combat.md`.

---

## Validation Criteria

- All M1–M19 invariants pass across 3+ seeds for scenarios 12–16
- All existing invariants (A through L) still pass (M19 regression check)
- Mission generation selects appropriate (region, archetype) pairs for the simulation state across all scenarios
- Urgency dominance verified in crisis scenarios (M2)
- Preference influence verified in calm scenarios (M3, M4)
- Force parity within configured range for all generated missions (M5)
- Asset profiles respected within tolerance (M6)
- Capacity shortfalls reduce quantity not quality (M7)
- Difficulty affects player force only, not enemy force (M8)
- Proportional deltas scale correctly with region state (M9)
- All 5 outcome bands produce distinct consequences per archetype (M10)
- Commander death properly logged in ledger and event log (M11, M12)
- Character selector produces 2–4 chapter lineage arcs across 3+ seeds (M14, M15)
- Forced rotation fires on bloodline extinction and commander death with no successor
- Crisis veto prevents rotation during active crises
- Cross-faction rotation occurs at the hard cap when applicable
- First mission always uses unrelated pool (M17)
- Faction collapse reassignment works (M18)
- Commander selection feels narratively appropriate (subjective — Westley's judgment)
- Mission Generation Review Reports reviewed by Westley across 3 seeds for scenarios 12–14
- Briefing prose reads as coherent military orders (subjective — Westley's judgment)
- Force compositions feel appropriate for each archetype (subjective — Westley's judgment)
- Consequence deltas feel proportionate to mission outcomes (subjective — Westley's judgment)
- Westley signs off on the Mission Generation Review Reports

## Done Condition

All validation criteria met. Westley signs off on:
1. The Mission Generation Review Reports (selection quality, force composition, briefing prose across 3+ seeds)
2. The consequence tables producing proportionate world effects
3. The force allocation producing winnable-feeling force compositions across difficulty levels
4. The final validator report (all M1–M19 invariants passing)
5. The shared contracts module (`mission_contracts.py`) reviewed and approved for Stage 6 integration
6. The character selector producing natural-feeling lineage arcs across 3+ seeds (reviewed in Mission Generation Review Reports)
