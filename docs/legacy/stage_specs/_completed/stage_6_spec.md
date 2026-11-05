# Stage 6 — Tactical Simulation Engine (Headless)

## Goal

Prove that the headless tactical combat engine produces deterministic, balanced engagements: units move across continuous 2D space with vertical layers, deal damage following a soft RPS triangle, use abilities that create decisive moments, track objectives to completion, and classify outcomes into bands — all without any visual frontend. The engine is a deterministic state machine: given the same initial state and command stream, it reproduces any engagement tick-for-tick. This determinism enables the replay system (Stage 8), automated balance testing, and headless validation of hundreds of engagements per hour.

This is the stage where the simulation starts producing *gameplay* rather than just *world state*. Stages 1–5 proved that the world evolves, factions fight at the strategic level, time jumps produce narrative, and names fill the chronicle. Stage 6 proves that when a mission fires, the tactical combat that the player commands works — mechanically sound, balanced across the RPS triangle, with engagements that feel deliberate and weighty.

**Architecture: SC2-style simulation/renderer split.** The tactical engine built in this stage is the ground truth for all combat. It owns unit positions, health, damage, abilities, objectives, and outcomes. The Godot frontend (Stage 8) is a pure renderer — it reads engine state and draws it. The command interface (Stage 8) translates player inputs into engine commands. Replay files store initial state + command stream; the engine re-derives everything else. This split means all gameplay logic is testable, tunable, and validatable in Python with no visual dependencies.

**Pacing target: deliberate, not frantic.** Engagements are long enough for positioning and abilities to matter. A 5v5 force-on-force brawl with no tactical play still lasts at least 45 seconds — enough time for the player to read the situation, recognize a losing trade, and order a retreat. Tactical engagements (positioning, abilities, retreat and re-engage) last around 2 minutes. Large battles (100+ units per side) last well over 2 minutes. Mirror 50v50 with balanced composition: 150–200 seconds. The player commands heavy military assets, reads the situation, and makes committed positioning decisions — not twitch micro.

## Current Status (as of v2.07 spec rewrite)

This spec was originally authored against an early stat baseline and the v2.06 bible's ORCA/RVO movement model. Both have since changed. This section captures where the implementation actually is so future sessions don't have to reverse-engineer it.

**Implementation progress:**

- Checkpoints A through I — **PASS** (approved by Westley).
- Checkpoint J — **IN PROGRESS**. Sub-claims status:
  - L1 Strike beats Siege — **FAIL** (0% Strike wins). Root causes from diagnostic runs:
    1. Bombard AoE with `AOE_DAMAGE_CAP_MULTIPLIER = 4.0` saturates on Strike spawn formations and front-loads kills before Strike closes range. AoE saturation — not single-shot damage — is the actual killing mechanism.
    2. Bastion HP (2100) is too high for Strike effective DPS to crack inside the test window. Raider squad effective DPS against Bastion = 11.25 × 1.5 = 16.9, time-to-kill ≈ 124 sec per Bastion.
    3. The 0.20× Siege→Strike multiplier in `config.py` softens Bombard-on-Strike single-shot damage but doesn't help against the AoE saturation that does the actual killing.
  - L2 Siege beats Line — PASS.
  - L3 Line beats Strike — PASS.
  - L4 Soft RPS gradient — **FAIL**. The mechanism works: firing-percentage data from the gradient test shows Line firing % drops to ~57% in flank scenarios (T2/T3a/T3b) vs head-on baseline, which means the directional-probe + stationary-immovable rule is producing the designed concave geometry and a ~43% firing suppression on Line. The stats don't reward the geometry: Vanguard 1000 HP vs Raider 500 HP × Line→Strike 1.5× damage means Strike is out-traded even when Line is only firing 57% of the time. The HP gap eats the firing-percentage win.
- Checkpoints K and L — not started. Blocked on J.

**Movement model history:**

- v1 (original spec): hierarchical A* + simple separation steering + post-hoc push-apart. This is what landed when checkpoints A–I passed.
- v2 (Checkpoint J first attempt): added friendly line-of-fire blocking + hard collision. Friendly LOS blocking was removed when testing showed it produced perverse formation effects (flanking Strike units LOS-blocked *each other*).
- v3 (Checkpoint J / bible v2.06): full ORCA/RVO local steering replacement.
- v4 (bible v2.07): ORCA reverted (could not express the immovable engaged unit rule and produced unstable formations at our unit counts). Steering replaced with a custom **directional-probe + detour-commitment** model paired with deterministic **hard-collision push-apart** and a **stationary-immovable** rule. Plus an **engagement leash** on `attack_move`. See the bible's Pathfinding and Movement section for the design.
- v5 (current / formation_move_spec): SC2-style **formation movement** — each unit in a group order receives a personal offset slot derived from the group centroid at order time. Group terminates when the centroid reaches the click target (not when every straggler arrives). Implemented in `apply_group_move` + `_update_move_groups`. `FORMATION_MOVE_ENABLED = True` (live default). Kill switch: set `False` to restore v4 behavior bit-for-bit.

**Stat rebalance status:**

- Original Tier 2 baselines (v2.02 spec) produced engagements far shorter than the bible's pacing targets.
- The current `config.UNIT_STATS` reflect a non-uniform rebalance (HP up across the board, base damage down across the board, but not at the same ratios per unit type — see the updated Tier 2 table below). The bible (Open Design Question #14) was marked resolved at v2.07, but the stat values themselves are not yet final because the L1 and L4 failures above point at further adjustment.

**Checkpoint J resume work:**

*1. Code cleanup — remove `group_move` / `fast_move`.* The bible (v2.07) dropped both commands. The command vocabulary is now four: `move`, `attack_move`, `attack_target`, `activate_ability`. `apply_group_move` was **kept** and repurposed as the formation movement entry point (v5 movement model). `apply_fast_move` and the `"group_move"` / `"fast_move"` command types still exist in `command.py` and `movement.py` — they are dead code and should be removed in a future cleanup pass. The test files that issued these commands (`test_checkpoint_6j.py`, `test_sweep_debug.py`, `test_6j_mixed.py`, `test_t2_diagnostic.py`, `test_checkpoint_6k_engine_step.py`) still use the old call sites and may need updating.

*2. Code fix — `move` command should not halt on engagement.* **DONE.** `store.plain_moving[uid]` flag added to `unit.py`. `move` commands set it `True`; `attack_move` sets it `False`. `update_targeting` in `damage.py` skips units where `plain_moving` is set, so plain-move units never acquire `auto_engage_target` and never halt mid-move. Sensor-radius pursuit logic also skips plain-moving units.

*3. Stat rebalance pass.* After the code fixes are in, run a tuning pass that:
  - Closes the L1 Strike-vs-Siege gap. Tuning surfaces include the Siege→Strike multiplier (currently 0.20, originally 0.75 — the bible treats the matrix as a tuning surface), Bastion HP, Bombard `aoe_radius`, `AOE_DAMAGE_CAP_MULTIPLIER`, Surge parameters, and Raider/Interceptor HP. Given that AoE saturation is the dominant killing mechanism per the L1 diagnosis, the AoE damage cap and Bombard AoE radius are likely the highest-leverage levers.
  - Closes the L4 flank-gradient gap. The 2× HP gap between Strike and Line is the proximate cause — options are Strike HP up, Line HP down, Line→Strike multiplier reduction, or a Strike-side burst buff (Surge multiplier/duration).
  - Preserves L5/L6/L7 duration targets and L2/L3 RPS results.

  Expect this to be iterative. Use `test_checkpoint_6j.py` for L4 gradient, `test_checkpoint_6c.py` for L1/L2/L3, `test_checkpoint_6d.py` for L5/L6/L7.

*4. Re-run all of J.* Once L1 and L4 pass alongside the still-passing L2/L3 and L5–L7, run the full Tactical Review Report for J and present to Westley.

*5. After J passes.* Proceed to Checkpoint K (performance stress test) and Checkpoint L (final invariants + Tactical Review Reports across the full scenario set).

---

## Bible References

Read these spoke sections before implementing:

- **`docs/bible_history/bible_2_00_combat.md`**: Full file — unit combat categories (Strike/Line/Siege), unit roster (6 types), abilities (one per unit), unit behavior AI (universal decision loop), roles within categories, 2.5D vertical layers, camera and player view, environmental hazards, engagement scale, tactical variety, unit power balancing and force parity, force allocation algorithm
- **`docs/bible_history/bible_2_00_world.md`**: "Map Generation System" (full section — spine + gradient hybrid, gradient property vocabulary, spine node types, generation pipeline, Strategic Layout Authoring Framework, fog of war, recon phase, canvas sizing, continuous movement, moving battlefields)
- **`docs/bible_history/bible_2_00_missions.md`**: "Outcome Band Classification System" (two-component scoring, per-archetype thresholds), "Mission Outcome Resolver" (proportional lookup tables — Stage 5.5 builds this, Stage 6 provides the outcome band it consumes)
- **`game_bible.md` (hub)**: "Force and Combat Design" (summary), "Sacred Design Principles" (era-agnostic architecture — all tactical mechanics must be abstract)

## Cross-Stage References

This section documents how Stage 6 relates to all other stages, providing a reference for future spec documents.

- **Stages 1–2** established the simulation backbone: region state model, passive drift, event chain architecture. The strategic simulation runs *between* missions during time jumps. The tactical engine runs *during* missions. They do not run simultaneously — the bible specifies the simulation is stopped during missions.
- **Stage 3** established faction agents, attack/conquest resolution, and budget accumulation. A faction agent's attack decision is what *triggers* a mission — the mission generator (Stage 5.5) reads the attack event and creates the mission. The faction's committed budget determines enemy force strength, which feeds into force parity (Stage 6's power rating system).
- **Stage 3.5** established diplomacy and technology. Tech tiers (0–33 / 34–66 / 67–100) determine which unit stat profiles are available — a Tier 1 faction fields Tier 1 units. Stage 6 defines Tier 2 baseline stats only (the middle tier); Tier 1 and Tier 3 variants are a config-level extension of the same system.
- **Stage 4** established admin revolts, lifecycle phases, time jumps, and the generational structure. Time jumps are the gaps between missions. The lifecycle phase classifier (Stage 4) informs the mission generator (Stage 5.5).
- **Stage 5** established the chronicle pipeline, coherence ledger, naming system, and library builder. Named characters from the ledger appear in mission briefings. Commander death during a mission is logged in the ledger.
- **Stage 5.5** (parallel) establishes the mission generator, outcome resolver, and force allocation algorithm. Stage 5.5 *creates* missions from simulation state and *processes* their results. Stage 6's outcome band classification feeds directly into Stage 5.5's outcome resolver. Stage 5.5's force allocation uses Stage 6's power rating system. **Both stages import shared data structures from `mission_contracts.py`** — the single source of truth for data crossing the 5.5 ↔ 6 boundary. Stage 6's `power_rating.py` is built here but imported by Stage 5.5's force allocator. Stage 6's `objectives.py` returns a `MissionResult` (from contracts). Stage 6's `tactical_engine.py` accepts a `MissionSetup` (from contracts) to initialize missions. See "Parallel Development with Stage 5.5" section below.
- **Stage 7** (future) establishes map generation and enemy macro behavior script content. Stage 7 builds the spine + gradient pipeline that produces tactical maps, and authors the per-archetype behavior scripts using the shared behavior script system with reactive hooks (defined in `docs/bible_history/bible_2_00_combat.md`). Stage 6 validates combat on hand-authored test maps; Stage 7 generates maps procedurally.
- **Stage 8** (future) establishes the Godot renderer, command interface, and replay system. Stage 8 reads Stage 6's simulation state and renders it. The command protocol defined in Stage 6 is the interface between player input and the tactical engine.

## What to Build

> **Implementation state:** All files listed under "Files to create" below **exist in `simulation/`** and have been implemented to the depth described in their sections. Checkpoints A through I were run against these implementations and approved by Westley. The descriptions here are therefore a mix of "what the system is supposed to do" (design intent) and "what it already does" (documentation of landed code). Where the two diverge — the move-halts-on-engage gap, the group_move/fast_move removal, ongoing stat tuning — the Current Status section flags the delta. Future sessions: treat this section as reference documentation, not a to-do list, except for the items explicitly called out in Current Status → Checkpoint J resume work.

### Files to create

**`tactical_engine.py`** — The core tick-based combat simulation. The top-level controller. Contains:
- Tick loop: advance simulation by one tick (1/20th of a second). Process command queue → update all units (decision loop) → resolve damage → update abilities → check objectives → emit state delta.
- Deterministic execution: fixed-point or controlled floating-point arithmetic. Same seed + same commands = same result, always.
- State snapshot emission: per-tick delta of all changed unit state (position, HP, status, ability cooldowns) for the renderer/replay system.
- Mission lifecycle: initialize from a `MissionSetup` (imported from `mission_contracts.py`) containing map parameters, player/enemy forces, objectives, reinforcement spec, and behavior script ID. Run ticks until terminal condition (all objectives resolved, time expired, or player force eliminated), classify outcome, return a `MissionResult` (from `mission_contracts.py`).
- Configuration: tick rate (20/sec default), all tuning values loaded from config.

**`unit.py`** — Unit state model and behavior. Contains:
- Unit data: id, unit_type, category (Strike/Line/Siege), faction, position (x, y), layer (int), hp, max_hp, base_damage, attack_interval, attack_range, sensor_radius, speed, layer_transition_time, aoe_radius (0 for non-AoE units), ability state (cooldown_remaining, active, duration_remaining).
- Unit storage: flat numpy arrays for all unit fields (positions, HP, cooldowns, etc.) for efficient batch operations at 200–400 unit scale. Unit ID indexes into the arrays.
- Unit decision loop — universal, priority-ordered, runs every tick for every unit:
  1. **Flinch check:** Am I taking damage from a source I cannot engage (out of sensor range or out of weapon range with no path)? If yes, move a short distance away from the damage direction and stop. Once the source is visible and in range, this check no longer triggers.
  2. **Command check:** Do I have an active command? If yes, execute it (move toward target position, attack-move toward position engaging enemies in range, attack specific target, activate ability).
  3. **Auto-engage:** Is there an enemy in my engagement range? Attack the nearest enemy. If already engaged with a living in-range target, continue (no target ping-ponging). If no enemy in range, hold position.
- Supply unit exception: no attack capability, check 3 is simply hold position. Flinch retreat is their primary survival.
- Death: when HP ≤ 0, unit is marked dead, removed from active arrays, logged in the engagement record.

**`damage.py`** — Damage resolution system. Contains:
- Damage formula: `damage = base_damage × category_multiplier × (1.0 - cover_density_at_position)`
- Category multiplier matrix (era-agnostic, uses Strike/Line/Siege categories):

```
                Target:
                Strike    Line      Siege
Attacker:
  Strike        1.0       0.75      1.5
  Line          1.5       1.0       0.75
  Siege         0.75      1.5       1.0
```

- Attack timing: each unit has an `attack_interval` (seconds between attacks, converted to ticks). Unit fires when its attack timer reaches zero, then resets.
- AoE damage (Bombard): circle centered on target position, `aoe_radius` world units. Full damage applied to every enemy unit within the circle. Damage cap: total AoE damage per attack cannot exceed `aoe_damage_cap × base_damage` (prevents a single Bombard shot from wiping an entire clustered army — config value, default 4.0×).
- Cover density sampling: query the map's `cover_density` gradient at the target unit's position. Applied as percentage damage reduction.
- Elevation damage bonus: config flag `ELEVATION_DAMAGE_BONUS_ENABLED`. When enabled, attacker at higher elevation tier gets `ELEVATION_DAMAGE_BONUS_PER_TIER` bonus per tier difference. **Disabled for space era. Enabled for future land-based eras.** The engine always computes elevation difference; the config flag determines whether it affects damage.
- Range check: damage only occurs if target is within attacker's `attack_range`. Damage is constant within range (no falloff).

**`ability.py`** — Ability system for all 6 unit types. Contains:
- Ability definitions (era-agnostic engine behaviors, theme pack provides names/visuals):
  - **Raider — Surge:** Activate → short burst of dramatically increased speed (`SURGE_SPEED_MULTIPLIER`, default 2.5×) and damage (`SURGE_DAMAGE_MULTIPLIER`, default 2.0×). Duration: `SURGE_DURATION_TICKS` (default 60 ticks = 3 sec). Cooldown: `SURGE_COOLDOWN_TICKS` (default 1500 ticks = 75 sec). One or two uses per engagement.
  - **Interceptor — Intercept:** Passive proximity trigger. When any enemy Strike unit enters `INTERCEPT_DETECTION_RADIUS`, the Interceptor gains speed boost (`INTERCEPT_SPEED_MULTIPLIER`, default 1.8×) and first-engagement damage bonus (`INTERCEPT_DAMAGE_MULTIPLIER`, default 1.5×) toward that unit. Bonus lasts until first attack lands, then enters cooldown. Cooldown: `INTERCEPT_COOLDOWN_TICKS` (default 600 ticks = 30 sec). No manual activation — triggers on proximity.
  - **Vanguard — Brace:** Activate → unit becomes immobile. After windup delay (`BRACE_WINDUP_TICKS`, default 40 ticks = 2 sec), gains damage reduction (`BRACE_DAMAGE_REDUCTION`, default 0.50 = 50% less damage taken) and damage boost (`BRACE_DAMAGE_MULTIPLIER`, default 1.3×). Same windup on deactivation. Cooldown: `BRACE_COOLDOWN_TICKS` (default 700 ticks = 35 sec) after deactivation.
  - **Warden — Rally:** Activate → burst area heal to all friendly units within `RALLY_RADIUS` (world units). Restores `RALLY_HEAL_AMOUNT` HP (flat value, config). Cooldown: `RALLY_COOLDOWN_TICKS` (default 1500 ticks = 75 sec). One, maybe two uses per engagement.
  - **Warden — Passive Aura:** Always-on. Friendly units within `WARDEN_AURA_RADIUS` receive `WARDEN_AURA_DAMAGE_REDUCTION` (default 0.10 = 10% less damage) and `WARDEN_AURA_REPAIR_RATE` HP per tick. Not an activated ability — positional benefit from being near the Warden.
  - **Bombard — Barrage:** Activate → concentrated high-damage volley at a targeted area. `BARRAGE_DAMAGE_MULTIPLIER` (default 3.0×) applied to base damage, `BARRAGE_RADIUS` (smaller than normal AoE). Brief telegraph delay (`BARRAGE_TELEGRAPH_TICKS`, default 30 ticks = 1.5 sec) before impact. Cooldown: `BARRAGE_COOLDOWN_TICKS` (default 1800 ticks = 90 sec). One use per engagement.
  - **Bastion — Fortify:** Activate → deploys defensive zone around the Bastion. All friendly units within `FORTIFY_RADIUS` gain `FORTIFY_DAMAGE_REDUCTION` (default 0.20 = 20% less damage) for `FORTIFY_DURATION_TICKS` (default 400 ticks = 20 sec). Bastion can still move (slowly — `FORTIFY_SPEED_MULTIPLIER`, default 0.4×). Zone moves with the Bastion. Cooldown: `FORTIFY_COOLDOWN_TICKS` (default 1400 ticks = 70 sec).
- Enemy ability usage: same abilities, threshold-based activation. Offensive abilities used when enemies in range. Defensive abilities used when friendlies nearby and taking damage. No sophisticated timing — simple conditions.

**`fog_of_war.py`** — Sensor and visibility system. Contains:
- Per-unit sensor radius: base value from unit stats, multiplied by `(1.0 - sensor_interference_at_position)` where sensor_interference is sampled from the map's gradient field.
- Visibility computation: union of all friendly units' sensor circles. An enemy unit is visible if it falls within any friendly unit's computed sensor circle on the same layer.
- Cross-layer visibility — combined cone + pulse model:
  - **Passive cone:** Units detect enemies on adjacent layers at degraded sensor range. Layer distance 1: sensor radius × `CONE_LAYER_1_FACTOR` (default 0.5). Layer distance 2: sensor radius × `CONE_LAYER_2_FACTOR` (default 0.2). Layer distance 3+: no passive detection.
  - **Active sensor pulse:** Command `activate_ability` on designated sensor-capable units (Interceptor by default via Intercept passive; future: dedicated sensor unit). Pulse reveals all layers within `PULSE_RADIUS` for `PULSE_REVEAL_TICKS` (default 40 ticks = 2 sec). After reveal expires, information gone. Cooldown: `PULSE_COOLDOWN_TICKS` (default 400 ticks = 20 sec).
  - **Vantage node bonus:** Units at vantage spine node positions get enhanced cross-layer visibility: cone factors doubled (effectively `CONE_LAYER_1_FACTOR × 2.0`), and passive detection extends one additional layer.
- Instant vanish: when an enemy unit leaves all friendly sensor coverage, it disappears from the visibility set immediately. No "ghost" or last-known-position tracking. (Future consideration for Stage 8 UI: the renderer may show a fading ghost for player feedback, but the engine state is binary — visible or not.)

**`movement.py`** — Unit movement and pathfinding. Contains:
- Continuous 2D coordinates (floats) per layer. Unit position = `(x: float, y: float, layer: int)`.
- Hierarchical pathfinding:
  - **Coarse layer:** A* on a precomputed navmesh per layer. Navmesh generated from the map's `obstacle_density` gradient (cells above `NAVMESH_OBSTACLE_THRESHOLD` are blocked, others walkable). Produces a sequence of waypoints from current position to target.
  - **Fine layer:** directional probe steering between waypoints (see below).
  - **Path caching:** Multiple units moving to the same destination share the coarse A* path keyed on (start_cell, goal_cell). Each unit independently steers along the shared waypoint sequence.
- **Fine-layer steering — directional probe + detour commitment.** Each moving unit seeks toward its next waypoint at its configured speed. Before applying the seek vector, the unit probes a short distance along its heading (`STEERING_PROBE_DIST`) to check whether any same-layer ally would block its forward path (collision-radius circle test). If clear, the unit moves straight — no steering force is applied at all (no separation vector, no obstacle-avoidance fudge). If blocked, the unit sweeps a fixed deterministic set of alternate angles (±30°, ±60°, ±90° from heading) and takes the first probe direction that's clear. When a deflected angle is chosen, the unit commits to traveling `STEERING_DETOUR_MIN_DIST` world units in that direction before re-probing. Commitment prevents per-tick oscillation between symmetric probe results.
- **Hard collision (deterministic push-apart).** After the per-unit movement loop, `_resolve_collisions()` runs `COLLISION_RESOLUTION_ITERATIONS` passes over same-layer unit pairs. For any pair within `2 × UNIT_COLLISION_RADIUS` of each other, the two are pushed apart along the unit-to-unit vector until separated. Push distribution depends on motion state:
  - Both moving → 50/50 split, each takes `overlap × 0.5`.
  - Only one moving → moving unit takes the full overlap, stationary unit absorbs zero push.
  - Neither moving → 50/50 split (rare; happens only if two halted units start within radius).
  A unit counts as "stationary" if it has no active move target, OR if it is held in place by attack-move engagement (`auto_engage_target` set to a live unit). The stationary-immovable rule is what produces concave formations: the front rank halts on engagement and becomes immovable, so later arrivals deflect around it via probe steering rather than shunting it out of firing position.
  Push results are clamped to map bounds and rejected if they'd land in a non-walkable navmesh cell. Deterministic tie-break for zero-distance overlap: the lower unit ID pushes left.
- **Attack-move engagement leash.** `_update_attack_move_state(store, active)` runs each tick before the movement loop. For any unit with `attack_moving=True` that has acquired a live `auto_engage_target`, the unit sets an anchor at its current position on first engagement. If the engaged target's position drifts more than `_ATTACK_MOVE_LEASH_SQ` (200 wu²) from that anchor, the unit clears its target and resumes movement toward the original commanded destination. The leash prevents an attack-moving force from peeling apart to chase fleeing targets across the map.
- **Command halting semantics.** A unit's per-tick movement is skipped if any of: no move target, the unit is immobile due to ability state (e.g., Vanguard Brace), OR the unit is `attack_moving` AND has a live `auto_engage_target` in range. **Plain `move` does not halt on engagement** — it is pure displacement. (See "Code-vs-design gaps" in Current Status — the current code does not yet honor this distinction and halts on engagement for any move command. Fix during J resume.)
- Layer transition: when a unit's command targets a position on a different layer, and the `layer_accessibility_mask` at the unit's current position permits the target layer, the unit enters a transition state. Transition takes `layer_transition_time` ticks (per-unit-type config value — Strike faster than Siege). During transition, the unit cannot attack or be targeted by same-layer units. At transition end, the unit's layer updates.
- Navmesh generation: runs once per mission at initialization. Takes the map's obstacle_density gradient, discretizes it into blocked/open cells (`NAVMESH_CELL_SIZE` per cell), and builds a per-layer grid. Target: <500ms for a large canvas.
- Combat LOS export: `has_combat_los(navmesh, x1, y1, x2, y2)` — Bresenham walk along navmesh cells, returns True if all cells along the segment are walkable. Used by `damage.py` to block shots through terrain obstacles. **Friendly unit occlusion is not checked** — units fire through allies (see bible Pathfinding and Movement section).

**`tactical_map.py`** — Map representation for the tactical engine. Contains:
- Canvas: rectangular play area defined by `(width, height)` in world units. Canvas sizes: small 4000×4000, medium 8000×8000, large 12000×12000 (config values).
- Gradient field sampling: given a position `(x, y)`, return the value of any gradient property at that point. Each gradient field source has `(position, property_type, radius, intensity, falloff_curve)`. The value at any point is the combined contribution of all overlapping sources of that property type.
  - `sensor_interference(x, y) → float [0.0, 1.0]`
  - `elevation(x, y) → float [0.0, 1.0]`
  - `obstacle_density(x, y) → float [0.0, 1.0]`
  - `cover_density(x, y) → float [0.0, 1.0]`
  - `layer_accessibility(x, y, layer) → bool`
- Spine node data: list of nodes with position, type tag (objective, staging, transit, chokepoint, flank_route, vantage, hazard_anchor, spawn_point, extraction), and property values.
- Spatial partitioning: grid-based spatial hash for efficient range queries ("find all units within R world units of position P"). Cell size tuned to typical engagement range. Rebuilt per tick from unit positions.
- Map loading: from a map seed (spine + gradient sources) or from hand-authored test maps (for Stage 6 validation).

**`objectives.py`** — Mission objective tracking and outcome classification. Contains:
- Objective data model:
```python
@dataclass
class Objective:
    id: str
    type: str               # "hold_zone", "destroy_targets", "escort_to_extraction",
                            # "survive_duration", "eliminate_force"
    weight: float           # Contribution to objective score (all weights sum to 1.0)
    params: dict            # Type-specific parameters (zone center/radius, target unit IDs,
                            # extraction point, duration in ticks, etc.)
    completion: float       # 0.0 to 1.0, updated per tick
    is_primary: bool        # Primary objective flag (carries dominant weight)
```
- Objective evaluation: per-tick completion update based on type:
  - `hold_zone`: completion = fraction of total hold duration completed while zone is under player control. Zone contested (enemy units inside) pauses the timer.
  - `destroy_targets`: completion = fraction of target units destroyed.
  - `escort_to_extraction`: completion = fraction of escort units that reached the extraction point alive.
  - `survive_duration`: completion = fraction of survival duration elapsed. Fails if all player units die before time expires.
  - `eliminate_force`: completion = fraction of enemy force HP destroyed.
- Terminal conditions: mission ends when all objectives are resolved (primary complete or failed), time deadline expires, or player force is eliminated.
- Outcome band classification (per bible spec):
  - **Component 1 — Objective score (0.0–1.0):** Weighted sum of all objective completion values.
  - **Component 2 — Force retention ratio (0.0–1.0):** Total surviving player unit power rating / total deployed player unit power rating.
  - **Final score:** `final_score = (objective_score × W_OBJ) + (retention_ratio × W_RET)` where W_OBJ = 0.75, W_RET = 0.25 (config values).
  - **Band mapping:** Final score maps to one of 5 bands (total_success, strong_success, partial_success, partial_failure, total_failure) through per-archetype threshold boundaries (config values per archetype).
- Output: a `MissionResult` (imported from `mission_contracts.py`) containing the outcome band, objective scores, force retention, per-objective completion details, commander survival status, and ticks elapsed. The `commander_survived` field is computed from whether the player's designated commander unit (flagged in `MissionSetup.metadata`) has HP > 0 at mission end. This `MissionResult` is the thin interface that Stage 5.5's outcome resolver consumes.

**`power_rating.py`** — Unit strength scoring for force parity. **This module is a shared dependency** — it is built in Stage 6 and imported by Stage 5.5's `force_allocator.py`. It has zero dependencies on the tactical engine and is a pure function of unit stats. Contains:
- Power rating formula: computes a single strength value for any unit based on its stats. Function signature is part of the cross-stage contract: `compute_power_rating(stats: dict) → float`. Used by force allocation (Stage 5.5) to ensure missions present winnable fights, and by outcome classification (Stage 6) for the force retention component.
- Formula: `power = (effective_hp × dps × range_factor × mobility_factor)` where:
  - `effective_hp = max_hp / (1.0 - average_cover_assumption)` — HP adjusted for typical cover
  - `dps = base_damage / attack_interval` — raw damage per second
  - `range_factor = log(attack_range + 1) / log(RANGE_NORMALIZATION + 1)` — logarithmic range bonus (long range is valuable but with diminishing returns)
  - `mobility_factor = speed / SPEED_NORMALIZATION` — faster units score slightly higher
- AoE bonus: Bombard's power rating includes an AoE multiplier reflecting area damage value.
- Ability bonus: each ability contributes a flat percentage bonus to the unit's power rating (config per ability, e.g., Surge adds 15%, Brace adds 20%). Approximation — ability value depends on usage, but a flat bonus captures average impact for force allocation purposes.
- Force total: sum of all unit power ratings in a force. Force parity compares player force total to enemy force total.

**`command.py`** — Command protocol and replay recording. Contains:
- Command data model:
```python
@dataclass
class Command:
    tick: int               # Tick number this command executes
    command_type: str       # "move", "attack_move", "attack_target",
                            # "activate_ability"
    unit_ids: list[int]     # Target unit(s) — single unit or a selection; multi-unit commands apply to each unit independently at its own speed
    target_position: tuple  # (x, y) for move/attack_move, None for others
    target_unit_id: int     # For attack_target, None for others
```
- Command queue: ordered by tick. The engine processes all commands for the current tick before advancing unit state.
- Replay recording: at mission start, record the complete initial state (map seed, unit positions/stats, objectives). During the mission, record every command with its tick number. At mission end, record the outcome. The replay file = initial state + command stream. To replay: load initial state, feed commands into the engine tick by tick. Determinism guarantees identical reproduction.
- Replay file format: JSON for Stage 6 (human-readable for debugging). Binary format is a future optimization.
- Script interface: for headless testing, commands are generated by test scripts instead of player input. The engine doesn't know or care about the command source.

**`test_maps.py`** — Hand-authored test maps for Stage 6 validation. Contains:
- 5–8 test maps with known tactical properties, used for all Stage 6 scenarios. Maps are authored as explicit spine + gradient data (no procedural generation — that's Stage 7).
- Test map types:
  - `open_field`: flat, no obstacles, no cover, no hazards. Pure combat test — RPS, damage, abilities.
  - `chokepoint`: single narrow passage between two open areas. Tests positioning, Brace, area denial.
  - `cover_heavy`: scattered cover zones across the map. Tests cover density damage reduction.
  - `multi_layer`: 3 layers with varying accessibility. Tests layer transitions, cross-layer visibility, fog of war.
  - `sensor_interference`: large central nebula zone with high sensor_interference. Tests fog of war, ambush gameplay.
  - `vantage_point`: elevated position with sightlines to surrounding area. Tests vantage node visibility bonus.
  - `large_operational`: medium canvas with staging, transit, chokepoints, and objective zones. Tests full mission flow with objectives.
  - `evacuation`: staging at one end, extraction at the other, enemy spawns along the route. Tests escort objectives and supply units.

### Files to modify

**`config.py`** — Add all new config values (see Config Values to Add section).

**`sim_tuner.py`** — Add tactical engine scenarios and the Tactical Review Report mode (see Validation section).

**`invariants.py`** — Add Group L invariants (see below).

### Files NOT to create or modify

The map generation pipeline (spine + gradient procedural generation, Strategic Layout Authoring Framework, archetype compatibility filters, fairness evaluator) is Stage 7. Stage 6 uses hand-authored test maps. The Godot renderer, camera system, UI, and visual feedback are Stage 8. The mission generator, mission outcome resolver, force allocation algorithm, and mission briefing templates are Stage 5.5 — Stage 6 imports shared data structures from `mission_contracts.py` (authored by Stage 5.5) but does not build the mission pipeline. Enemy macro behavior script content (the authored per-archetype scripts using the shared behavior script system with reactive hooks) is Stage 7. Moving battlefields (drifting spine nodes, moving gradient sources) are Stage 7. AI-generated unit stat variation is on hold — Stage 6 uses hand-designed baseline stats.

---

## Parallel Development with Stage 5.5

Stage 5.5 (Mission Generation Pipeline) and Stage 6 (Tactical Simulation Engine) are built in parallel by separate Claude Code sessions. This section defines the shared interface and coordination rules.

### Shared Contracts Module

`mission_contracts.py` is authored by the Stage 5.5 workstream and imported by both stages. It contains the dataclasses that cross the boundary:

- **`MissionSetup`** — emitted by Stage 5.5's mission generator, consumed by Stage 6's `tactical_engine.py` to initialize a mission. Contains: archetype, region ID, map parameters, player force composition, enemy force compositions, objectives, reinforcement spec, time limit, behavior script ID, briefing data, difficulty, and metadata.
- **`MissionResult`** — emitted by Stage 6's `objectives.py` after outcome classification, consumed by Stage 5.5's outcome resolver. Contains: outcome band (enum string), objective score, force retention ratio, per-objective completion details, commander survival status, and ticks elapsed.
- **`ForceUnit`**, **`ForceComposition`**, **`ObjectiveSpec`**, **`ReinforcementSpec`** — supporting structures used by both sides.

### What Stage 6 Imports

- **`mission_contracts.py`** — all shared dataclasses. Stage 6 constructs `MissionResult` instances and accepts `MissionSetup` instances.
- Stage 6 does NOT import anything from Stage 5.5's mission generator, force allocator, outcome resolver, or briefing builder. The dependency is one-directional through contracts only.

### What Stage 5.5 Imports from Stage 6

- **`power_rating.py`** — the `compute_power_rating(stats: dict) → float` function. This is a pure function with no tactical engine dependencies. Stage 5.5's force allocator calls it to compute unit strength values for force parity.
- Stage 5.5 does NOT import the tactical engine, damage system, abilities, or any other Stage 6 module.

### Coordination Rules

1. **The contracts module is the interface.** If a field needs to be added, renamed, or removed, Westley reviews the change before either side implements it.
2. **`power_rating.py` is built early** (Stage 6 Checkpoint A) because Stage 5.5 depends on it. It is a standalone module with no engine dependencies — it can exist before the tactical engine does.
3. **During Stage 6 validation, missions are initialized from hand-authored test setups**, not from Stage 5.5's generator. Integration testing (a real `MissionSetup` from the generator flowing into the engine) happens after both stages pass their respective stage gates.
4. **Outcome bands are the only tactical result Stage 5.5 cares about.** Stage 5.5 mocks outcome bands for its own validation. Stage 6 produces real outcome bands. Neither side needs the other to be complete for its own validation to work.

---

## Implementation Checkpoints

> **MANDATORY: STOP AND WAIT AT EVERY CHECKPOINT.** Each checkpoint below is a hard stop. Run the test, show the output to Westley, and **stop executing. Do not continue to the next checkpoint.** Do not evaluate the output yourself and decide to proceed. Do not batch multiple checkpoints. Present the output and wait for Westley to say "yes, continue" or "no, fix this." The next checkpoint begins only after explicit approval.
>
> **What "STOP" means:** Stop generating code. Stop running tests. Stop planning the next checkpoint. Present the output and wait for input. If you are unsure whether output is correct, that is Westley's judgment to make, not yours.

### Checkpoint A — Contracts, Power Rating, and Tactical Map (Isolation)

> **Status: COMPLETED.** Approved by Westley. Section retained as reference for the systems built.

**Build:** `mission_contracts.py` — all shared dataclasses (copy from Stage 5.5 spec, this is the shared source of truth). `power_rating.py` — the full power rating formula as a pure function. `tactical_map.py` — canvas, gradient field sampling, spine node data, spatial partitioning. `test_maps.py` — the `open_field` test map only (simplest possible map, no gradients, no obstacles).

**Test:** Write a standalone test script.
- Construct all contract dataclasses with placeholder data — confirm they instantiate cleanly.
- Compute power ratings for all 6 unit types using Tier 2 stats. Print a table: unit type, HP, DPS, range, speed, computed power rating.
- Load the `open_field` test map. Query gradient values at several positions — confirm all return 0 (no gradients on open field). Query the spatial hash with a test position and radius — confirm it returns empty (no units placed yet).

**Print:**
- Power rating table for all 6 unit types with relative ranking
- Contract dataclass instantiation confirmation
- Map gradient queries at 3+ positions showing expected values
- Spatial hash query results

**Verify:** Power rating ranking makes intuitive sense (Vanguard/Bastion highest, Warden lowest). Map queries return correct values for a flat open field. All dataclasses instantiate without error.

**⛔ STOP. Show output. Wait for Westley.**

---

### Checkpoint B — Unit State and Movement (Isolation)

> **Status: COMPLETED.** Approved by Westley. Movement implementation has since evolved (see Current Status → Movement model history) — the current `movement.py` reflects the v2.07 directional-probe model, not the simple separation-steering model that this checkpoint originally validated.

**Build:** `unit.py` — unit data model (numpy arrays), unit creation from stat profiles. `movement.py` — per-tick position updates, directional probe steering, hard-collision push-apart, stationary-immovable rule. No pathfinding yet — direct movement toward target position with steering + collision.

**Test:** Write a standalone test script. Place 20 units on the `open_field` map (10 per side, spread across starting positions). Issue `move` commands to all units toward the center. Run 200 ticks.

**Print:**
- Initial unit positions (all 20 units)
- Positions at tick 50, 100, 150, 200
- Speed verification: confirm each unit moved at its configured speed (distance per tick matches `speed × tick_duration`) within steering tolerance
- Separation verification: no two units closer than `2 × UNIT_COLLISION_RADIUS` at any sampled tick (hard collision must hold)
- A simple ASCII or text-based position dump showing unit spread at each sample tick

**Verify:** Units move at correct speeds. Strike units arrive first, Siege units last. Probe steering deflects units around blockers without jitter. Hard collision prevents overlap. No oscillation between probe directions (detour commitment doing its job).

**⛔ STOP. Show output. Wait for Westley.**

---

### Checkpoint C — Damage Model and RPS Triangle (Isolation)

> **Status: COMPLETED.** Approved by Westley at the time. Note: the original RPS pass had different stat values; the checkpoint will need to be re-validated as part of the J resume stat rebalance, since L1 (Strike beats Siege) currently fails under the rebalanced stats.

**Build:** `damage.py` — damage formula, category multiplier matrix, attack timing, range check. Wire into `unit.py` decision loop (auto-engage only — no commands, no flinch, no abilities yet). Wire into `tactical_engine.py` tick loop (process damage after unit updates).

**Test:** Write a standalone test script. Run all 6 RPS matchups on `open_field`: Strike vs Siege, Siege vs Line, Line vs Strike, and the 3 mirror matches. 10 units per side, equal power rating, 5 seeds each.

**Print:**
- For each matchup × seed: winner, duration (ticks and seconds), surviving unit count, force retention ratio
- Summary table: average win rate and average retention for each matchup across seeds
- Confirmation that Strike > Siege, Siege > Line, Line > Strike with >60% retention for the winner
- Mirror matches showing roughly 50/50 splits

**Verify:** The soft RPS triangle works — favored side wins consistently but not with 100% dominance. Mirror matches are close to even. Engagement durations are in the right ballpark (not instant, not infinite). The multiplier matrix is producing the expected damage relationships.

**⛔ STOP. Show output. Wait for Westley.**

---

### Checkpoint D — Engagement Duration Tuning (Tuning)

> **Status: COMPLETED at the time, partially superseded.** The original duration thresholds were 10/60/150 sec. The bible v2.07 pacing rebalance bumped the targets (L5 to 45s, L6 to 120s, L7 to 150–200s). The current stat values were chosen to hit the new targets, but the J stat rebalance pass will revisit and re-validate.

**Build:** No new systems — this is a tuning checkpoint on the existing damage model. Run the duration validation scenarios: 5v5 (all type permutations), 50v50 mirror, 100v100 mixed.

**Test:** Run engagement duration scenarios from the spec (scenario 13 structure).

**Print:**
- 5v5 results: duration for every type permutation (Strike vs Strike, Strike vs Line, etc.) — confirm all ≥ 45 seconds (L5, revised v2.07)
- 50v50 mirror: duration — confirm 150–200 seconds (L7)
- 100v100 mixed: duration — confirm > 120 seconds (L6, revised v2.07)
- Kill timeline for the 50v50 mirror: deaths per 5-second bucket showing attrition curve shape

**Verify:** All duration claims (L5, L6, L7) pass. If any fail, identify which stat needs adjustment (HP too low? DPS too high?) — but do not adjust yet. Present the failure and the diagnosis to Westley.

**⛔ STOP. Show output. Wait for Westley. If duration claims fail, Westley decides whether to adjust stats now or proceed and tune later.**

---

### Checkpoint E — Abilities (Isolation, then Integration)

> **Status: COMPLETED.** Approved by Westley. All six abilities implemented in `ability.py`. Some flat-value parameters (Rally heal, Warden aura repair) drifted from the original spec values during later tuning — the current values are documented in the Config Values section below.

**Build:** `ability.py` — all 6 ability definitions (Surge, Intercept, Brace, Rally, Warden Aura, Barrage, Fortify). Wire into `unit.py` decision loop (ability activation for player commands; threshold-based activation for enemy units).

**Test:** Run the ability impact scenarios from the spec (scenario 14 structure). Each ability tested in isolation against a control (ability used vs. not used).

**Print:**
- **Brace:** Vanguard survival time braced vs. unbraced against each attacker type. Confirm ≥ 1.5× improvement (L8).
- **Rally:** 10 Vanguards at 50% HP, Warden activates Rally. Print HP before and after. Confirm ≥ 15% of max HP restored per unit (L9).
- **Surge:** 3 Raiders vs. Bombard, with and without Surge. Print time to kill. Confirm ≥ 30% faster with Surge (L10).
- **Fortify:** Bastion activates Fortify near a group of Line units under fire. Print damage taken with and without Fortify active.
- **Intercept:** Raider enters Interceptor detection radius. Print whether Intercept triggered, speed and damage bonuses applied.
- **Barrage:** Bombard fires Barrage at clustered Line units. Print units hit, damage dealt, telegraph delay timing.
- **Warden Aura:** Units inside vs. outside aura radius under identical fire. Print damage difference and repair tick accumulation.

**Verify:** Each ability produces measurable, meaningful impact. No ability is broken (trivially overpowered or negligible). Threshold-based enemy activation fires at sensible moments.

**⛔ STOP. Show output. Wait for Westley.**

---

### Checkpoint F — Pathfinding and Navmesh (Isolation)

> **Status: COMPLETED.** Approved by Westley. Coarse A* + path caching landed and verified. Fine-layer steering description has been updated to reflect the v2.07 directional-probe model that replaced the original separation steering.

**Build:** `movement.py` — hierarchical A* pathfinding (coarse navmesh layer + the directional-probe fine-layer steering from Checkpoint B), navmesh generation from obstacle density gradients, path caching. `test_maps.py` — add `chokepoint` and `cover_heavy` maps.

**Test:** Write a standalone test script. Place units on the `chokepoint` map. Issue move commands that require pathfinding through the chokepoint. Also test a direct path on `open_field` to confirm pathfinding doesn't degrade simple cases.

**Print:**
- Navmesh generation time for each test map (target: <500ms for large canvas)
- Path from start to end on `chokepoint`: waypoint sequence, total path length, number of A* nodes explored
- Unit positions at 5 sampled ticks showing units navigating through the chokepoint (not walking through walls)
- Path on `open_field`: confirm it's a near-straight line (no unnecessary waypoints)
- Path caching: confirm 10 units moving to the same destination share the coarse path (print cache hit count)

**Verify:** Navmesh generates within time budget. Paths navigate around obstacles. Chokepoint forces units through the narrow passage. Open field produces simple paths. Path caching works.

**⛔ STOP. Show output. Wait for Westley.**

---

### Checkpoint G — Fog of War (Isolation)

> **Status: COMPLETED.** Approved by Westley.

**Build:** `fog_of_war.py` — per-unit sensor radius with interference, same-layer visibility, cross-layer cone detection, active sensor pulse, vantage node bonus. `test_maps.py` — add `sensor_interference`, `multi_layer`, and `vantage_point` maps.

**Test:** Run the fog of war scenarios from the spec (scenario 15 structure).

**Print:**
- **Interference reduction:** For each interference intensity (0.0, 0.2, 0.5, 0.8, 1.0), print base sensor radius and effective sensor radius. Confirm 0.8 interference → ~20% of base (L11).
- **Cross-layer cone:** Unit on layer 1 with enemies on layers 1, 2, 3. Print detection radius per layer. Confirm layer 2 ≈ 50% of base, layer 3 ≈ 20% (L12).
- **Vantage bonus:** Unit at vantage vs. not at vantage. Print cone factors and detection range for each. Confirm doubled factors and +1 layer extension.
- **Pulse:** Activate sensor pulse. Print revealed units before, during, and after the pulse duration. Confirm reveal expires after `PULSE_REVEAL_TICKS`.
- **Instant vanish:** Enemy exits all sensor coverage. Print visibility status on the exit tick. Confirm immediate disappearance (no ghost).

**Verify:** All fog of war claims (L11, L12) pass. Vantage bonus and pulse work as specified. Visibility is binary — no partial states.

**⛔ STOP. Show output. Wait for Westley.**

---

### Checkpoint H — Objectives and Outcome Classification (Isolation)

> **Status: COMPLETED.** Approved by Westley. `MissionResult` shape matches `mission_contracts.py` and is consumed by Stage 5.5's outcome resolver.

**Build:** `objectives.py` — objective data model, per-tick evaluation for all 5 objective types, terminal conditions, outcome band classification, `MissionResult` construction (from `mission_contracts.py`). `test_maps.py` — add `large_operational` and `evacuation` maps.

**Test:** Run the outcome band scenarios from the spec (scenario 16 structure). Scripted command sequences that produce each of the 5 outcome bands.

**Print:**
- For each scripted scenario: objective completion values per tick (sampled at key moments), final objective score, force retention ratio, final score, classified outcome band
- Confirmation that all 5 bands are produced across the scenario set (L13)
- Paired comparison: two scenarios with identical objective completion but different force retention. Print both final scores and bands (L14).
- Terminal condition tests: mission ending by objective completion, time expiry, and force elimination — one example of each, print the trigger and final state
- `MissionResult` construction: print the full dataclass for one scenario to confirm all fields are populated correctly

**Verify:** All 5 outcome bands are produced (L13). Force retention affects scoring (L14). Terminal conditions fire correctly. `MissionResult` matches the contract structure.

**⛔ STOP. Show output. Wait for Westley.**

---

### Checkpoint I — Command Protocol and Replay (Integration)

> **Status: COMPLETED.** Approved by Westley. `"group_move"` and `"fast_move"` command types removed from `command.py`; `apply_fast_move` removed from `movement.py`. All stale test callers updated.

**Build:** `command.py` — command data model, command queue, replay recording (initial state + command stream + outcome). Wire the full tick loop in `tactical_engine.py`: command processing → unit decision loop → damage → abilities → fog of war → objectives → state delta emission.

**Test:** Run a full mission on `large_operational`: two forces, scripted commands, objectives. Record the replay. Then replay it: load initial state, feed the command stream, verify identical final state.

**Print:**
- Mission summary: map, force sizes, objectives, duration
- Timeline: key events (first contact, first kill, ability activations, objective progress milestones)
- Final outcome: band, objective score, force retention, `MissionResult` fields
- Replay comparison: final state hash from the live run vs. replay run. Print tick-by-tick state hash at 5 sampled ticks to confirm identity.
- Determinism check: run the same scenario 5 times, print final state hash for each (L15)

**Verify:** The full tick loop runs end-to-end. Replay produces identical results. Determinism holds across 5 runs (L15). The `MissionResult` is correctly populated and matches contract structure. All previously validated claims (L1–L14) still hold — quick spot-check, not full re-run.

**⛔ STOP. Show output. Wait for Westley.**

---

### Checkpoint J — Soft RPS with Positioning (Integration)

> **Status: DEFERRED (L2, L3, L4).** L1 PASS (100% Strike wins). L2, L3, L4 are balance tuning failures — wrong stat ratios, not code bugs. Manually marked passing per Westley 2026-04-15; balance tuning deferred to a dedicated config pass.

**Build:** No new systems — this is a validation checkpoint combining damage, the directional-probe + hard-collision steering, the stationary-immovable rule, and map terrain. The mechanism by which flanking is supposed to produce an advantage: when Strike approaches a Line force from a flank, the Line front rank halts on engagement and becomes immovable; later-arriving Line units deflect via probe steering rather than reaching firing position; the result is reduced Line firing % compared to a head-on engagement, plus more Strike units in firing position against a smaller subset of Line units. This is the only mechanical source of flanking advantage (no friendly LOS blocking, no RPS-aware targeting, no special-case rules).

**Test:** Strike vs Line (unfavorable for Strike), equal power, 25 engagements per tier (same seeds across tiers). Four tiers: T1 (head-on, both formed), T2 (one side terrain-constrained, other has open arc), T3a (flank vs march column), T3b (flank vs Line already engaged with Siege).

**Print:**
- Per-tier: Strike win rate, TTW (mean ± stddev), TTW ratio vs T1, damage dealt ratio, firing% asymmetry, first Strike kill tick
- Gradient checks: TTW ratio T2/T1 ≥1.3, TTW ratio T3/T1 ≥1.6, T1 win rate ≤5%, monotonic increase in win rate/damage ratio/firing% from T1→T3

**Verify:** Positioning creates a measurable behavioral gradient (L4). The gradient shape — not any single win-rate number — validates that terrain + steering + collision + damage interact correctly. T1 should be near-hopeless for Strike, T3 should show meaningful Strike advantage, and all metrics should improve monotonically across tiers.

**Current state (see Status section above):** the firing% suppression mechanism works (~57% Line firing in flanks vs head-on), but the HP gap between current Strike and Line stats prevents the geometric advantage from converting to wins. Resume work needs to address the stat side of L4 before this checkpoint can pass.

**⛔ STOP. Show output. Wait for Westley.**

---

### Checkpoint K — Performance (Stress Test)

> **Status: COMPLETED.** L16 PASS — p95=10.87ms at 100v100 (budget 50ms). Return-fire mechanic added. Targeting bug fixed (nearest-enemy correctness). Pathfinding improvements (A+C: waypoint arrival radius, wall-tangential collision push).

**Build:** No new systems — performance validation on the existing engine.

**Test:** Run the performance scenario from the spec (scenario 18): 200v200 on large canvas, all units engaged, sustained for 1000+ ticks.

**Print:**
- Per-tick processing time: min, max, mean, p95, p99 across the full run
- Tick budget compliance: what percentage of ticks processed within 50ms (L16)
- Breakdown by subsystem: time spent in damage resolution, ability updates, pathfinding, fog of war, objective evaluation, state delta emission
- Memory usage: peak during the engagement

**Verify:** p95 tick time is under 50ms (L16). If it's not, the subsystem breakdown identifies the bottleneck. Do not optimize prematurely — present the bottleneck to Westley and discuss whether optimization is needed now or can wait.

**⛔ STOP. Show output. Wait for Westley.**

---

### Checkpoint L — Tactical Review Reports and Invariants (Final)

> **Status: COMPLETED** (with deferred items). L1 PASS. L2/L3/L4 deferred (balance tuning, not code). L5 FAIL (Strike fights too fast — balance). L6 PASS. L7 FAIL-warning (stalemate outliers — balance). L8–L15 PASS. L16 PASS. L17 PASS. Signed off by Westley 2026-04-15. Balance tuning (L2/L3/L4/L5/L7) deferred to a dedicated config pass before Stage 7.

**Build:** `sim_tuner.py` — tactical engine scenarios and `--tactical-review` report generation. `invariants.py` — all Group L invariants (L1–L17). Full scenario suite (scenarios 12–18).

**Test:** Run all scenarios across 3+ seeds. Run the full invariant suite. Generate Tactical Review Reports.

**Print:**
- L1–L17 pass/fail for each scenario × seed
- Any invariant failures with the specific values that violated the constraint
- Regression check: all prior invariants (A through K) passing
- Full Tactical Review Reports for scenarios 12–16 (the report format from the Validation section)
- Summary: total invariants checked, total passed, total failed

**Verify:** All L1–L17 pass. All prior invariants pass. If any fail, the specific failure is diagnosed before proceeding — do not patch around failures.

**⛔ STOP. Show output. Wait for Westley. This is the stage gate — Westley reviews the full Tactical Review Reports across 3+ seeds and signs off before Stage 6 is complete.**

---

## Unit Stat Baselines — Tier 2

All stats are hand-designed baseline values for Tier 2 ("Establishment") units. Tier 1 and Tier 3 are config-level variants of the same profiles (lower/higher stats respectively). AI-generated per-civilization variation is on hold.

The values listed below are the **current live values in `config.UNIT_STATS`** as of the v2.07 spec rewrite. They reflect the engagement-duration rebalance applied in response to bible Open Design Question #14 (now resolved). They are not final — the Strike-vs-Siege and L4 flank gradient failures noted in Current Status indicate further adjustment is needed.

**Design philosophy: A+C hybrid — long engagements with category-specific rhythm.** All fights last long enough for positioning and abilities to matter. HP pools create tempo differences: Strike fights are the fastest within the new pacing window, Line fights are the baseline, Siege fights are the longest. Large battles (100+ units per side) last well over 2 minutes. DPS is moderate across all categories; HP is the primary differentiator.

**Tuning target (per bible, v2.07):** Two equally-sized forces with mirror composition should fight for 150–200 seconds before one side is eliminated. A 5v5 force-on-force brawl in any matchup should last at least 45 seconds. A 1.5× favorable RPS matchup should reduce the losing side's fight duration by roughly 30–40%.

### Stat Profiles (Tier 2 Baseline — current live values)

All speed values assume medium canvas (8000×8000). All range/radius values are world units.

| Stat | Raider | Interceptor | Vanguard | Warden | Bombard | Bastion |
|------|--------|-------------|----------|--------|---------|---------|
| **Category** | Strike | Strike | Line | Line | Siege | Siege |
| **HP** | 500 | 650 | 1000 | 750 | 800 | 2100 |
| **Base Damage** | 9 | 6 | 7.5 | 4 | 17.5 | 7 |
| **Attack Interval (sec)** | 0.8 | 1.0 | 1.2 | 1.5 | 3.0 | 1.8 |
| **DPS** | 11.25 | 6.0 | 6.25 | 2.67 | 5.83 | 3.89 |
| **Attack Range** | 200 | 250 | 300 | 350 | 1200 | 800 |
| **Speed (wu/sec)** | 150 | 130 | 80 | 70 | 50 | 40 |
| **Sensor Radius** | 800 | 1000 | 700 | 800 | 300 | 300 |
| **Layer Trans. (sec)** | 1.0 | 1.2 | 2.5 | 2.0 | 4.0 | 5.0 |
| **AoE Radius** | — | — | — | — | 150 | — |

**Stat rationale (and where it currently breaks down):**

- **Raider:** Fastest, highest DPS, lowest HP among Strike. Glass cannon role. A Raider squad catching a Bombard alone (1.5× multiplier): effective DPS = 11.25 × 1.5 = 16.9. Bombard HP 800 / 16.9 = ~47 sec to kill. Bombard firing back at Raider (currently 0.20× multiplier — see flag below): effective DPS = 5.83 × 0.20 = 1.17. Raider HP 500 / 1.17 = ~430 sec. Raider survives the dive easily 1v1 — but Bombard AoE against multiple clustered Raiders is what ends the fight.
- **Interceptor:** Faster sensor radius (the screen), more durable than Raider, lower damage. Intercept passive makes it lethal against Raiders specifically.
- **Vanguard:** The wall. High HP, baseline DPS. Two Vanguards trading at 1.0×: 6.25 DPS each, 1000 HP each = ~160 sec per unit. With positioning and abilities, fights run well over the 2-minute target.
- **Warden:** Low damage, moderate HP, but passive aura + Rally make nearby units significantly tougher. The Warden's value is multiplicative, not direct.
- **Bombard:** Long range, high per-shot damage, slow fire rate, AoE. Against clustered Line at 1.5×: 17.5 × 1.5 × (units in AoE) per shot, capped at `AOE_DAMAGE_CAP_MULTIPLIER × base_damage` per attack. Devastating against formations.
- **Bastion:** Highest HP in the game by a wide margin (2.1× the next-highest). Low DPS but survives everything. A Raider squad against a Bastion (1.5×): 16.9 DPS effective. Bastion HP 2100 / 16.9 = ~124 sec. Strike struggles to crack a Bastion inside the test window — this is the proximate cause of the L1 (Strike beats Siege) failure.

**Open balance issues exposed by this stat table (deferred — not blocking the spec rewrite):**

1. **L1 — Strike vs Siege failing.** Bastion HP gap (2100 vs Strike's 500–650) plus Bombard AoE clustering on Strike formations. The Siege→Strike multiplier is currently 0.20 (down from the spec's 0.75) but it doesn't fully close the gap because Strike still has to break Siege HP pools.
2. **L4 — flank gradient failing.** Vanguard 1000 HP vs Raider 500 HP × Line→Strike 1.5× damage means Line out-trades Strike even when geometry cuts Line firing % to ~57%. The HP gap eats the firing-percentage win.

Both are tuning problems for the J resume pass, not design questions.

**Formation width reference:** The bible's Strategic Layout Authoring Framework references chokepoint width as a ratio to "standard unit formation width." Standard formation width = 200 world units (approximately one Vanguard's attack range). A "2.0× formation width" chokepoint allows two Vanguards abreast.

---

## Behavioral Claims

### RPS Triangle

**Claim L1: Strike beats Siege in equal-value engagements.** A force of Strike units with equal total power rating to a Siege force should win with >60% of its force surviving.
- When: Strike-only force vs Siege-only force, equal power ratings, open field
- Then: Strike force wins with >60% force retention
- Over: 20+ engagements across different seeds
- Pattern: relational constraint
- Governing configs: category multiplier matrix, all Strike and Siege stat values
- Severity: critical

**Claim L2: Siege beats Line in equal-value engagements.** Same structure as L1 with Siege vs Line.
- Then: Siege force wins with >60% force retention
- Severity: critical

**Claim L3: Line beats Strike in equal-value engagements.** Same structure as L1 with Line vs Strike.
- Then: Line force wins with >60% force retention
- Severity: critical

**Claim L4 (revised v2.06): Soft RPS — positioning creates a measurable gradient in Strike vs Line outcomes.** The soft RPS system exhibits correct behavior when outcomes improve monotonically across scenario tiers representing increasing defender disadvantage: (T1) head-on against formed Line, (T2) engagement where one side has terrain-constrained arc, (T3a) flank against Line in march column, (T3b) flank against Line already engaged with Siege. The tuning target is the gradient shape — T1 should be near-zero Strike wins, T3 should show meaningful Strike wins, and all metrics (TTW, damage ratio, firing%) should increase monotonically from T1 through T3.
- When: Strike-only vs Line-only (equal power), multiple scenario tiers with increasing defender disadvantage
- Then: Monotonic improvement in TTW ratio, damage ratio, and firing% from T1→T3. T1 win rate ≤5%. TTW ratio T2/T1 ≥1.3, T3/T1 ≥1.6.
- Over: 25 engagements per tier (same seeds across tiers for paired comparison)
- Pattern: behavioral gradient (shape of curve across tiers, not single threshold)
- Governing configs: unit speed values, map layout, RVO parameters
- Severity: warning (specific percentages are tuning targets, not hard constraints — the gradient shape is what matters)

### Engagement Duration

**Claim L5 (revised v2.07): Small skirmishes last at least 45 seconds.** A 5v5 engagement of any unit type combination should take at least 45 seconds to resolve. Threshold bumped from the original 10-second target per bible v2.07 pacing rebalance.
- When: 5 units vs 5 units, any type matchup, open field
- Then: time from first damage to last unit death ≥ 900 ticks (45 sec)
- Over: all unit type permutations (Strike vs Strike, Strike vs Line, etc.)
- Pattern: threshold bound
- Governing configs: HP values, DPS values, category multipliers
- Severity: critical

**Claim L6 (revised v2.07): Large battles last well over 2 minutes.** A 100v100 engagement with mixed composition should take more than 120 seconds.
- When: 100 units vs 100 units, balanced composition (40% Line, 30% Strike, 30% Siege per side), open field
- Then: time from first damage to last unit death ≥ 2400 ticks (120 sec)
- Over: 10+ engagements across seeds
- Pattern: threshold bound
- Severity: critical

**Claim L7: Mirror match baseline.** Two identical 50-unit balanced forces should fight for 150–200 seconds.
- When: 50v50, identical composition, open field
- Then: engagement duration between 3000 and 4000 ticks (150–200 sec)
- Over: 10+ engagements
- Pattern: threshold bound
- Severity: warning (the range is a tuning target)

### Abilities

**Claim L8: Brace significantly increases Vanguard survivability.** A braced Vanguard should survive at least 50% longer than an unbraced Vanguard against the same attacker.
- When: single Vanguard braced vs single attacker (any type), compared to unbraced
- Then: braced Vanguard survival time ≥ 1.5× unbraced survival time
- Over: all attacker types
- Pattern: relational constraint
- Governing configs: `BRACE_DAMAGE_REDUCTION`
- Severity: warning

**Claim L9: Rally provides meaningful burst healing.** A Rally heal on a group of 10 damaged Vanguards should restore at least 15% of their missing HP.
- When: 10 Vanguards at 50% HP, Warden activates Rally
- Then: each Vanguard gains ≥ 15% of max HP
- Governing configs: `RALLY_HEAL_AMOUNT`
- Severity: warning

**Claim L10: Surge enables assassination.** A Raider using Surge on an unescorted Bombard should kill the Bombard at least 30% faster than without Surge.
- When: Raider squad (3 units) attacks Bombard, Surge activated vs not
- Then: time to kill Bombard reduced by ≥ 30%
- Governing configs: `SURGE_DAMAGE_MULTIPLIER`, `SURGE_DURATION_TICKS`
- Severity: warning

### Fog of War

**Claim L11: Sensor interference reduces visibility.** A unit in a sensor_interference zone of intensity 0.8 should have its sensor radius reduced to approximately 20% of base.
- When: unit in sensor_interference 0.8 zone
- Then: effective sensor radius ≈ base × (1.0 - 0.8) = base × 0.2, ±5%
- Over: all unit types
- Pattern: threshold bound
- Severity: critical

**Claim L12: Cross-layer passive detection degrades with distance.** A unit on layer 1 should detect enemies on layer 2 at ~50% of base sensor radius, and layer 3 at ~20%.
- When: unit on layer 1, enemies on layers 2 and 3
- Then: detection radius on layer 2 ≈ base × CONE_LAYER_1_FACTOR (0.5), layer 3 ≈ base × CONE_LAYER_2_FACTOR (0.2)
- Pattern: threshold bound
- Governing configs: `CONE_LAYER_1_FACTOR`, `CONE_LAYER_2_FACTOR`
- Severity: critical

### Objectives and Outcome Classification

**Claim L13: Outcome band classification produces all 5 bands.** Across a set of scripted scenarios (some with perfect play, some with deliberate failures), all 5 outcome bands should be produced.
- When: 10+ scripted scenarios with varying performance levels
- Then: each of the 5 bands (total_success through total_failure) is produced at least once
- Over: the full scenario set
- Pattern: trajectory shape
- Severity: critical

**Claim L14: Force retention affects classification.** Two scenarios with identical objective completion but different force retention should produce different outcome bands (or at least different final scores).
- When: same objective completion, different retention ratios
- Then: higher retention → higher final score
- Over: paired scenarios
- Pattern: relational constraint
- Severity: critical

### Determinism

**Claim L15: Perfect determinism.** Running the same mission with the same initial state and same command stream must produce bit-identical results every time.
- When: same seed, same map, same units, same commands
- Then: every tick produces identical state
- Over: 5 runs of the same scenario
- Pattern: threshold bound (zero deviation)
- Severity: critical — determinism is required for the replay system

### Performance

**Claim L16: Engine handles 400 units at 20 ticks/sec.** A 200v200 engagement on a large canvas should process each tick in under 50ms (the tick budget at 20 ticks/sec).
- When: 400 active units on large canvas (12000×12000), all engaged
- Then: per-tick processing time < 50ms
- Over: sustained engagement (1000+ ticks)
- Pattern: threshold bound
- Severity: critical

### Regression

**Claim L17: All Stage 5 invariants still pass.** No regression in previously validated behavior.
- Over: full run
- Pattern: regression check
- Severity: critical

---

## Validation — Tactical Review Report

The Tactical Review Report is the primary validation mechanism for combat feel, balance, and engagement pacing. Like the Chronicle Review Report (Stage 5), it is designed for human review — the developer reads the output, evaluates feel, and provides feedback.

### Report Generation

`sim_tuner.py` gains a `--tactical-review` flag:

```bash
python sim_tuner.py --scenario 12_rps_triangle --tactical-review --seeds 1,2,3
```

### Report Format

```
════════════════════════════════════════════════════════════════
ENGAGEMENT: Scenario 12_rps_triangle / Seed 1
Map: open_field (4000×4000) | Units: 30 Strike vs 30 Siege
════════════════════════════════════════════════════════════════

── Setup ─────────────────────────────────────────────────────
  Force A (Strike): 15 Raider, 15 Interceptor | Total power: 4520
  Force B (Siege):  15 Bombard, 15 Bastion    | Total power: 4480
  Parity ratio: 1.009 (within 5% — balanced)

── Timeline ──────────────────────────────────────────────────
  0:00  First contact — Raiders close to Bombard range
  0:04  First kill — Raider squad destroys Bombard #3
  0:12  Bastions engaged — Raiders bogged down, DPS drops
  0:28  Interceptors flank remaining Bombards
  0:41  Last Bombard destroyed
  0:55  Bastion cleanup — Strike force whittles remaining Bastions
  1:12  Engagement ends — Strike wins

── Results ───────────────────────────────────────────────────
  Winner: Force A (Strike)
  Duration: 1448 ticks (72.4 sec)
  Force A survivors: 19/30 (63.3% retention)
  Force B survivors: 0/30

── Kill Timeline ─────────────────────────────────────────────
  [Graph: unit deaths over time, bucketed by 5-sec intervals]
  0-5s:   A:0  B:2
  5-10s:  A:1  B:3
  10-15s: A:2  B:2
  ...

── Ability Usage ─────────────────────────────────────────────
  Surge activations: 8 (avg tick 340, avg damage dealt during Surge: 52)
  Intercept triggers: 0 (no enemy Strike present)
  Fortify activations: 11 (avg duration held: 380 ticks)
  Barrage activations: 7 (avg units hit: 3.2, avg damage: 157)

════════════════════════════════════════════════════════════════
```

### Review Workflow

1. Run `sim_tuner.py --tactical-review` across the scenario set (RPS matchups, mixed compositions, objective missions).
2. Read the reports. Evaluate: Do engagements last the target duration? Does the RPS triangle produce the expected winners? Do abilities fire at meaningful moments? Does force retention match expectations?
3. If engagement duration is off, adjust HP or DPS values. If RPS balance is off, adjust the multiplier matrix. If abilities feel weak/strong, adjust ability parameters.
4. All adjustments are config value changes — no code changes needed for balance tuning.

---

## Scenarios

> **Status: not yet wired into `sim_tuner.py`.** The scenarios below were spec'd as the Checkpoint L scenario suite but have not been registered in the tuner. Earlier checkpoints (A–I) used standalone test scripts (`test_checkpoint_6*.py`) rather than the tuner scenario harness. Wiring these in is part of Checkpoint L work.

```python
"12_rps_triangle": {
    "description":  "RPS validation — 6 matchups (S vs L, S vs S, L vs S, etc.) on open field",
    "map":          "open_field",
    "engagements":  [
        {"force_a": {"Strike": 30}, "force_b": {"Siege": 30}},
        {"force_a": {"Siege": 30}, "force_b": {"Line": 30}},
        {"force_a": {"Line": 30}, "force_b": {"Strike": 30}},
        {"force_a": {"Strike": 30}, "force_b": {"Strike": 30}},
        {"force_a": {"Line": 30}, "force_b": {"Line": 30}},
        {"force_a": {"Siege": 30}, "force_b": {"Siege": 30}},
    ],
    "seeds":        [1, 2, 3, 4, 5],
},

"13_engagement_duration": {
    "description":  "Duration validation — small, medium, large engagements",
    "map":          "open_field",
    "engagements":  [
        {"force_a": {"mixed": 5}, "force_b": {"mixed": 5}},      # small
        {"force_a": {"mixed": 25}, "force_b": {"mixed": 25}},     # medium
        {"force_a": {"mixed": 50}, "force_b": {"mixed": 50}},     # mirror baseline
        {"force_a": {"mixed": 100}, "force_b": {"mixed": 100}},   # large
        {"force_a": {"mixed": 200}, "force_b": {"mixed": 200}},   # stress test
    ],
    "seeds":        [1, 2, 3],
},

"14_ability_impact": {
    "description":  "Ability validation — each ability tested in isolation",
    "map":          "open_field",
    "engagements":  [
        {"test": "brace_survivability", "attacker": "Raider", "defender": "Vanguard", "braced": [True, False]},
        {"test": "rally_healing", "setup": "10_vanguards_at_50pct_hp_with_warden"},
        {"test": "surge_assassination", "raider_vs_bombard": True, "surge": [True, False]},
        {"test": "fortify_zone", "bastion_with_line_vs_strike": True},
        {"test": "intercept_trigger", "interceptor_vs_raider": True},
        {"test": "barrage_cluster", "bombard_vs_clustered_line": True},
    ],
    "seeds":        [1, 2, 3],
},

"15_fog_of_war": {
    "description":  "Fog of war validation — sensor interference, cross-layer detection",
    "map":          "sensor_interference",
    "tests":        [
        {"test": "interference_reduction", "intensity": [0.0, 0.2, 0.5, 0.8, 1.0]},
        {"test": "cross_layer_cone", "layers": [1, 2, 3]},
        {"test": "vantage_bonus", "at_vantage": [True, False]},
    ],
},

"16_objective_classification": {
    "description":  "Outcome band validation — scripted scenarios producing all 5 bands",
    "map":          "large_operational",
    "missions":     [
        {"archetype": "defensive_stand", "scripted_performance": "perfect"},
        {"archetype": "defensive_stand", "scripted_performance": "strong"},
        {"archetype": "defensive_stand", "scripted_performance": "partial"},
        {"archetype": "defensive_stand", "scripted_performance": "poor"},
        {"archetype": "defensive_stand", "scripted_performance": "catastrophic"},
        {"archetype": "evacuation", "scripted_performance": "perfect"},
        {"archetype": "evacuation", "scripted_performance": "partial"},
        {"archetype": "evacuation", "scripted_performance": "catastrophic"},
    ],
    "seeds":        [1, 2, 3],
},

"17_determinism": {
    "description":  "Determinism check — same scenario run 5 times, verify identical results",
    "map":          "large_operational",
    "engagements":  [{"force_a": {"mixed": 50}, "force_b": {"mixed": 50}}],
    "seed":         42,
    "runs":         5,
    "verify":       "bit_identical_state_at_every_tick",
},

"18_performance": {
    "description":  "Performance stress test — 200v200 on large canvas",
    "map":          "open_field_large",
    "engagements":  [{"force_a": {"mixed": 200}, "force_b": {"mixed": 200}}],
    "seed":         1,
    "measure":      "per_tick_processing_time",
    "threshold":    50,  # ms per tick maximum
},
```

## Config Values (current)

> All values below exist in `simulation/config.py`. This section documents the current live values, not work to be done. Where the live value diverges from the original spec value (stat rebalance, ability flat values, the directional-probe config that replaced the RVO config, the Siege→Strike multiplier), the inline comment flags it.

```python
# ── Tactical engine core (Stage 6) ────────────────────────────────
TACTICAL_TICK_RATE                = 20      # ticks per second
TACTICAL_TICK_DURATION            = 0.05    # seconds per tick (1 / TICK_RATE)

# ── Canvas sizing (Stage 6) ───────────────────────────────────────
CANVAS_SMALL                      = (4000, 4000)    # world units
CANVAS_MEDIUM                     = (8000, 8000)
CANVAS_LARGE                      = (12000, 12000)
CANVAS_SIMULATION_MODIFIER_RANGE  = 0.30            # ±30% per bible

# ── Category multiplier matrix (Stage 6, current live values) ─────
# Indexed as CATEGORY_MULTIPLIER[attacker_category][target_category]
# NOTE: Siege→Strike is currently 0.20, deviating from the canonical 0.75
# in the original spec. This is a tuning value — the bible (v2.07) treats
# the matrix as a tuning surface, not fixed at 1.0/0.75/1.5.
CATEGORY_MULTIPLIER = {
    "Strike": {"Strike": 1.0,  "Line": 0.75, "Siege": 1.5},
    "Line":   {"Strike": 1.5,  "Line": 1.0,  "Siege": 0.75},
    "Siege":  {"Strike": 0.20, "Line": 1.5,  "Siege": 1.0},
}

# ── Unit stat baselines — Tier 2 (Stage 6, current live values) ───
# Format: {unit_type: {stat: value}}
# These are the post-rebalance values applied in response to bible
# Open Design Question #14 (resolved v2.07). Non-uniform scaling
# from the original spec values. Not final — see Current Status.
UNIT_STATS = {
    "Raider":      {"category": "Strike", "hp": 500,  "base_damage": 9,    "attack_interval": 0.8,
                    "attack_range": 200, "speed": 150, "sensor_radius": 400,
                    "layer_transition_time": 1.0, "aoe_radius": 0},
    "Interceptor": {"category": "Strike", "hp": 650,  "base_damage": 6,    "attack_interval": 1.0,
                    "attack_range": 250, "speed": 130, "sensor_radius": 500,
                    "layer_transition_time": 1.2, "aoe_radius": 0},
    "Vanguard":    {"category": "Line",   "hp": 1000, "base_damage": 7.5,  "attack_interval": 1.2,
                    "attack_range": 300, "speed": 80,  "sensor_radius": 350,
                    "layer_transition_time": 2.5, "aoe_radius": 0},
    "Warden":      {"category": "Line",   "hp": 750,  "base_damage": 4,    "attack_interval": 1.5,
                    "attack_range": 350, "speed": 70,  "sensor_radius": 400,
                    "layer_transition_time": 2.0, "aoe_radius": 0},
    "Bombard":     {"category": "Siege",  "hp": 800,  "base_damage": 17.5, "attack_interval": 3.0,
                    "attack_range": 600, "speed": 50,  "sensor_radius": 300,
                    "layer_transition_time": 4.0, "aoe_radius": 150},
    "Bastion":     {"category": "Siege",  "hp": 2100, "base_damage": 7,    "attack_interval": 1.8,
                    "attack_range": 400, "speed": 40,  "sensor_radius": 300,
                    "layer_transition_time": 5.0, "aoe_radius": 0},
}

# ── AoE damage cap (Stage 6) ─────────────────────────────────────
AOE_DAMAGE_CAP_MULTIPLIER         = 4.0    # max total AoE damage = base_damage × this

# ── Elevation (Stage 6, era-configurable) ─────────────────────────
ELEVATION_DAMAGE_BONUS_ENABLED    = False   # Disabled for space era
ELEVATION_DAMAGE_BONUS_PER_TIER   = 0.10    # +10% damage per elevation tier (when enabled)
ELEVATION_SENSOR_BONUS_PER_TIER   = 0.15    # +15% sensor radius per elevation tier (always active)

# ── Cover (Stage 6) ──────────────────────────────────────────────
# cover_density at unit position directly reduces damage: damage × (1.0 - cover_density)
# No additional config needed — the gradient value IS the reduction percentage

# ── Ability parameters (Stage 6) ─────────────────────────────────
# Raider — Surge
SURGE_SPEED_MULTIPLIER            = 2.5
SURGE_DAMAGE_MULTIPLIER           = 2.0
SURGE_DURATION_TICKS              = 60      # 3 sec
SURGE_COOLDOWN_TICKS              = 1500    # 75 sec

# Interceptor — Intercept (passive)
INTERCEPT_DETECTION_RADIUS        = 350     # world units — triggers when enemy Strike enters
INTERCEPT_SPEED_MULTIPLIER        = 1.8
INTERCEPT_DAMAGE_MULTIPLIER       = 1.5     # first engagement only
INTERCEPT_COOLDOWN_TICKS          = 600     # 30 sec

# Vanguard — Brace
BRACE_WINDUP_TICKS                = 40      # 2 sec — immobile, no bonus yet
BRACE_DAMAGE_REDUCTION            = 0.50    # 50% less damage taken while braced
BRACE_DAMAGE_MULTIPLIER           = 1.3     # 30% more damage dealt while braced
BRACE_COOLDOWN_TICKS              = 700     # 35 sec after deactivation

# Warden — Rally (active)
RALLY_RADIUS                      = 400     # world units
RALLY_HEAL_AMOUNT                 = 112     # flat HP restored (current live value)
RALLY_COOLDOWN_TICKS              = 1500    # 75 sec

# Warden — Passive Aura
WARDEN_AURA_RADIUS                = 300     # world units
WARDEN_AURA_DAMAGE_REDUCTION      = 0.10    # 10% less damage for units in aura
WARDEN_AURA_REPAIR_RATE           = 0.15    # HP per tick (3 HP/sec — current live value)

# Bombard — Barrage
BARRAGE_DAMAGE_MULTIPLIER         = 3.0
BARRAGE_RADIUS                    = 100     # world units — smaller than normal AoE
BARRAGE_TELEGRAPH_TICKS           = 30      # 1.5 sec warning
BARRAGE_COOLDOWN_TICKS            = 1800    # 90 sec

# Bastion — Fortify
FORTIFY_RADIUS                    = 350     # world units
FORTIFY_DAMAGE_REDUCTION          = 0.20    # 20% less damage for units in zone
FORTIFY_DURATION_TICKS            = 400     # 20 sec
FORTIFY_SPEED_MULTIPLIER          = 0.4     # Bastion moves at 40% speed while Fortify active
FORTIFY_COOLDOWN_TICKS            = 1400    # 70 sec

# ── Fog of war (Stage 6) ─────────────────────────────────────────
CONE_LAYER_1_FACTOR               = 0.50    # adjacent layer passive detection: 50% of base sensor
CONE_LAYER_2_FACTOR               = 0.20    # 2 layers away: 20% of base sensor
CONE_LAYER_3_FACTOR               = 0.0     # 3+ layers: no passive detection
VANTAGE_CONE_MULTIPLIER           = 2.0     # vantage nodes double cone factors
VANTAGE_EXTRA_LAYER               = 1       # vantage extends passive detection +1 layer

PULSE_RADIUS                      = 500     # world units — full-range snapshot
PULSE_REVEAL_TICKS                = 40      # 2 sec reveal duration
PULSE_COOLDOWN_TICKS              = 400     # 20 sec

# ── Pathfinding and Movement (Stage 6, rewritten v2.07) ──────────
# Coarse pathfinding (unchanged from spec original)
NAVMESH_OBSTACLE_THRESHOLD        = 0.7     # obstacle_density above this = blocked
NAVMESH_CELL_SIZE                 = 100     # world units — navmesh cell size
STEERING_OBSTACLE_AVOIDANCE_RANGE = 50      # world units — terrain obstacle detection range
UNIT_COLLISION_RADIUS             = 15      # world units — unit physical radius

# Directional probe steering (replaces ORCA from v2.06)
STEERING_PROBE_DIST               = 40      # world units — how far ahead to probe for ally blockers
STEERING_DETOUR_MIN_DIST          = 60      # world units — committed travel distance after picking a deflected angle

# Hard collision push-apart (deterministic post-movement pass)
HARD_COLLISION_ENABLED            = True
COLLISION_RESOLUTION_ITERATIONS   = 3       # iterations of pair-wise push-apart per tick

# ── Objectives and outcome classification (Stage 6) ──────────────
OUTCOME_WEIGHT_OBJECTIVE          = 0.75    # weight of objective score in final score
OUTCOME_WEIGHT_RETENTION          = 0.25    # weight of force retention in final score

# Per-archetype outcome band thresholds (final_score → band)
# Format: [total_failure_max, partial_failure_max, partial_success_max, strong_success_max]
# Scores above strong_success_max = total_success
OUTCOME_THRESHOLDS = {
    "defensive_stand":     [0.20, 0.40, 0.60, 0.80],
    "siege_breaking":      [0.20, 0.40, 0.60, 0.80],
    "reconquest":          [0.25, 0.45, 0.65, 0.82],
    "assault":             [0.25, 0.45, 0.65, 0.82],
    "suppression":         [0.20, 0.40, 0.60, 0.80],
    "multi_front_defense": [0.15, 0.35, 0.55, 0.75],
    "interception":        [0.20, 0.40, 0.60, 0.80],
    "evacuation":          [0.30, 0.50, 0.65, 0.80],  # evacuation is graded more generously
    "containment":         [0.20, 0.40, 0.60, 0.80],
    "counterinsurgency":   [0.20, 0.40, 0.60, 0.80],
}

# ── Power rating (Stage 6) ───────────────────────────────────────
RANGE_NORMALIZATION               = 600     # normalizes range factor
SPEED_NORMALIZATION               = 150     # normalizes mobility factor
ABILITY_POWER_BONUS = {
    "Raider": 0.15, "Interceptor": 0.12, "Vanguard": 0.20,
    "Warden": 0.25, "Bombard": 0.18, "Bastion": 0.20,
}
AOE_POWER_MULTIPLIER              = 1.5     # Bombard AoE value in power rating

# ── Replay (Stage 6) ─────────────────────────────────────────────
REPLAY_FORMAT                     = "json"  # "json" for debugging, "binary" future
```

## Validation Criteria

- All L1–L17 invariants pass across 3+ seeds for all scenarios
- All existing invariants (A through K) still pass (L17 regression check)
- RPS triangle produces expected winners in all 6 matchups (L1–L3) across 5 seeds
- Soft RPS validated — positioning creates measurable behavioral gradient across scenario tiers (L4)
- Small engagements (5v5) last ≥ 45 seconds in all matchups (L5, revised v2.07)
- Large engagements (100v100) last > 120 seconds (L6, revised v2.07)
- Mirror 50v50 lasts 150–200 seconds (L7)
- All 6 abilities produce measurable impact in their designed scenarios (L8–L10)
- Fog of war correctly reduces visibility in interference zones (L11)
- Cross-layer detection degrades correctly with distance (L12)
- All 5 outcome bands are produced across the scripted scenario set (L13)
- Determinism verified — 5 identical runs produce bit-identical results (L15)
- Performance: 400 units at 20 ticks/sec processes within 50ms/tick budget (L16)
- `MissionResult` output matches `mission_contracts.py` structure — all fields populated, importable by Stage 5.5 without modification
- `power_rating.py` is a standalone module with no tactical engine imports — importable by Stage 5.5's force allocator directly
- Tactical Review Reports reviewed by Westley across 3 seeds for scenarios 12–16
- Balance feel evaluated: does the RPS triangle feel right? Do fights last the right amount of time? Do abilities feel impactful?
- Westley signs off on the Tactical Review Reports and balance feel

## Done Condition

All validation criteria met. Westley signs off on:
1. The Tactical Review Reports (balance feel across scenarios and seeds)
2. The RPS triangle producing satisfying results (Strike beats Siege, Siege beats Line, Line beats Strike — but soft, not hard counters)
3. Engagement durations matching the pacing target (deliberate, not frantic; small fights ≥ 10 sec, large fights > 1 min)
4. Ability impact feeling meaningful (each ability creates a noticeable moment)
5. The final validator report (all L1–L17 invariants passing)
6. Determinism verified (replay foundation is solid)
7. Performance verified (engine handles target unit counts within tick budget)
8. The shared contracts interface (`mission_contracts.py` imported cleanly, `MissionResult` populated correctly, `power_rating.py` standalone) — ready for Stage 5.5 integration
