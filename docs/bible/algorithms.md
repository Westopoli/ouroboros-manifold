# Algorithms — the retained equations

This is the "what stays" contract for the C rewrite. Every formula below was read from the Python source on 2026-09-10 (Stage 1 algorithm pass), verdicted keep-verbatim, and is reproduced here with its constants and config names. The C sim must reproduce each one bit-for-bit under the same seed, the same RNG draw order, and the same command stream. Tuning a constant is normal C-rewrite validation work and changes the value here in the same PR; changing a formula's shape is a requirement change and runs the change protocol in `docs/northstar/agile.md`.

All fields are floats clamped to [0, 100] unless stated. Economy has a floor of `ECONOMY_FLOOR = 8.0` under drift, friction, and standard events; conquest bypasses it. Ticks are integers from 1. Randomness is one seeded stream per world (`random.Random(seed)`); the draw order per tick is the order the formulas appear in the tick sequence below.

Not yet inventoried here: event threshold triggers with noise (`events.py`), diplomacy timers and peace formation (`diplomacy.py`), civilizational lifecycle (`lifecycle.py`), time jump (`time_jump.py`), coherence ledger and character selector, and the whole tactical layer (`unit.py`, `movement.py`, `damage.py`, `fog_of_war.py`, `facing.py`, `ability.py`). Each gets added when its epic runs the completeness gate.

## Tick sequence (`tick.py`)

One strategic tick, in this order. Feature flags in parentheses are all true at launch.

1. Resolve pending events whose due tick has arrived (`ENABLE_EVENTS`).
2. Evaluate fresh threshold triggers on every inhabited region; fired events enqueue their chain spawns. Any event that creates a faction spawns it here.
3. Faction agents (`ENABLE_FACTIONS`):
   - 3a snapshot every region before any mutation this tick;
   - 3b every faction accumulates budget (ALG-17);
   - 3c telegraphed attacks declared `TELEGRAPH_PREP_TICKS = 1` tick ago resolve now;
   - 3d every faction decides (ALG-11 through ALG-16); an attack in telegraph mode is queued for 3c next tick, everything else is immediate;
   - 3e defenders of newly telegraphed attacks may reactive-reinforce (ALG-18);
   - 3f immediate intents resolve (ALG-19 through ALG-24), collisions first grouped by target.
4. Border friction on every region with a hostile border (ALG-25) (`ENABLE_BORDER_FRICTION`).
   - 4.1 admin revolt roll per owned region (ALG-29) (`ENABLE_ADMIN_REVOLTS`);
   - 4.25 diplomacy timers and peace formation (`ENABLE_DIPLOMACY`, not inventoried here);
   - 4.5 technology growth then convergence, per faction (ALG-26 through ALG-28) (`ENABLE_TECHNOLOGY`).
5. Passive drift on every inhabited region (ALG-01 through ALG-08), applied with clamps, composites recomputed (ALG-09, ALG-10).
6. Zombie faction cleanup; coherence ledger attachment.
7. Log.

## Per-region drift (`drift.py`)

Inputs per region: fields `military` m, `economy` e, `tension` t, `population` p, composites `stability` s, the tick number, the region's two phase offsets, the owning faction's modifiers, and the adjacency bonus. Empty-tier regions have no drift.

**ALG-01 Oscillator kernel.** `osc(A, P, φ, tick) = A · sin(2π · tick / P + φ)`. Enabled by `ENABLE_OSCILLATION` for tick > 0. Two oscillators per region: economy `A = ECON_OSCILLATION_AMPLITUDE = 6.0`, `P = ECON_OSCILLATION_PERIOD = 15`; tension `A = TENSION_OSCILLATION_AMPLITUDE = 2.0`, `P = TENSION_OSCILLATION_PERIOD = 18`. Phase offsets φ are drawn per region at world generation, uniform in [0, 2π). The previous-tick value is `osc(..., tick − 1)` for tick > 1 and 0 for tick = 1.

Feedback isolation: all drift terms read the de-oscillated trend `e' = e − osc_econ(tick − 1)`, `t' = t − osc_tension(tick − 1)`, and a de-oscillated stability computed from (m, t', p) by ALG-09. The delta added to the field is `osc(tick) − osc(tick − 1)`, never the raw oscillator value. Military and population use the same primed inputs; only economy and tension receive an oscillator delta.

**ALG-02 Military decay.** `Δm_decay = −(m · MILITARY_DECAY_RATE) · (1 − e'/100)`, `MILITARY_DECAY_RATE = 0.006`.

**ALG-03 Recruitment** (`ENABLE_RECRUITMENT`). `headroom = max(0, 1 − m / RECRUITMENT_CEILING)`, `RECRUITMENT_CEILING = 90.0` (reads raw m, not primed). `eco_term = RECRUITMENT_RATE · (e'/100) · (p'/100) · (1 − t/100)^TENSION_RECRUITMENT_SCALE` if `e' > RECRUITMENT_THRESHOLD` else 0; `RECRUITMENT_RATE = 12`, `RECRUITMENT_THRESHOLD = 20.0`, `TENSION_RECRUITMENT_SCALE = 0.3` (reads raw t). `Δm_recruit = (RECRUITMENT_BASELINE · p'/100 + eco_term) · headroom`, `RECRUITMENT_BASELINE = 0.1`.

**ALG-04 Faction modifier.** A faction may carry per-field modifiers (launch: conqueror `{"military": 0.05}`, all others empty). Each modifier adds its value to that field's delta; the military modifier is multiplied by the recruitment headroom when recruitment is enabled.

**ALG-05 Economy growth, drag, overcapacity.** `growth = ECONOMY_BASE_GROWTH · (p'/100)`, `ECONOMY_BASE_GROWTH = 2.0`. `drag = (t'/100) · ECONOMY_TENSION_PENALTY_RATE`, `= 0.40`. `capacity = p' · ECO_POP_RATIO`, `= 0.85`. `overcap = ECO_OVERCAPACITY_DECAY · (e' − capacity)/100` if `e' > capacity` else 0, `ECO_OVERCAPACITY_DECAY = 15.0`. `Δe = growth − drag − overcap + adjacency_bonus + Δosc_econ`.

**ALG-06 Adjacency bonus** (`ENABLE_ADJACENCY_BONUS`, computed in `tick.py`). For every inhabited neighbor across a trade edge that is same-faction, or whose faction this region's faction holds a cooperative stance toward: `adjacency_bonus += NEIGHBOR_ECONOMY_BONUS · (neighbor.e / 100)`, `NEIGHBOR_ECONOMY_BONUS = 0.05`. Reads the neighbor's raw economy.

**ALG-07 Tension drift.** `economic = ((TENSION_ECONOMY_MIDPOINT − e')/100) · TENSION_ECONOMY_RATE · (p'/100)`, midpoint `50.0`, rate `0.5`. `stress = max(0, TENSION_STRESS_THRESHOLD − s') · TENSION_STRESS_RATE`, threshold `40.0`, rate `0.008`. `decay = TENSION_NATURAL_DECAY_RATE · (t'/100)`, rate `0.20`. Subsistence crisis: with `thresh = ECONOMY_FLOOR + SUBSISTENCE_CRISIS_RANGE = 8.0 + 3.0`, if `e' < thresh` then `severity = (thresh − e') / 3.0` and `subsistence = SUBSISTENCE_TENSION_RATE · severity · (p'/100)`, rate `0.15`; else 0. `Δt = economic + stress + subsistence − decay + Δosc_tension`.

**ALG-08 Population drift.** If `e' > POPULATION_SUBSISTENCE = 15.0`: `base = POPULATION_GROWTH_RATE · ((e' − 15)/(100 − 15)) · (1 − p'/100)`, rate `2.0`. Else `base = −(15 − e') · POPULATION_DECLINE_RATE`, rate `0.2`. Subsistence crisis as in ALG-07: if `e' < 11.0`, `base −= SUBSISTENCE_POP_RATE · severity`, rate `0.08`. `Δp = base`.

**Apply.** Each field becomes `max(floor, min(100, field + Δ))` with floor `ECONOMY_FLOOR = 8.0` for economy and 0 for the rest. Then composites recompute.

## Composites (`region.py`)

**ALG-09 Stability.** `s = m · W_STAB_MILITARY + (100 − t) · W_STAB_TENSION + p · W_STAB_POPULATION`, weights `0.40 / 0.35 / 0.25`. Then `s *= STAB_MILITARY_PENALTY = 0.70` if `m < STAB_MILITARY_THRESHOLD = 10.0`; `s *= STAB_POPULATION_PENALTY = 0.75` if `p < STAB_POPULATION_THRESHOLD = 20.0`. Stored rounded to 2 decimals.

**ALG-10 Capacity.** `c = e · W_CAP_ECONOMY + p · W_CAP_POPULATION + m · W_CAP_MILITARY`, weights `0.50 / 0.35 / 0.15`. `c *= CAP_ECONOMY_PENALTY = 0.65` if `e < CAP_ECONOMY_THRESHOLD = 20.0`; `c *= CAP_POPULATION_PENALTY = 0.70` if `p < CAP_POPULATION_THRESHOLD = 15.0`. Stored rounded to 2 decimals.

## Faction decisions (`faction.py`)

Per faction per tick, reading the 3a snapshot only. Archetypes at launch: `player_civilization`, `conqueror`, `fortifier`, `opportunist`, plus `warlord`, `schism`, `breakaway` for factions created mid-game. Starting faction archetypes cycle conqueror, fortifier, opportunist for factions 1 through 14; faction 0 is the player civilization. Every starting stance is hostile.

**ALG-11 Attractiveness** of a neighbor region n not owned by this faction. Weights per archetype from `ARCHETYPE_ATTRACT_WEIGHTS` (weakness, value, position):

| Archetype | weakness | value | position | tension-primary | can colonize | recent-damage boost |
|---|---|---|---|---|---|---|
| conqueror | 0.40 | 0.25 | 0.35 | no | yes | 0 |
| warlord | 0.20 | 0.35 | 0.45 | no | yes | 0 |
| fortifier | 0.25 | 0.20 | 0.55 | no | yes | 0 |
| opportunist | 0.35 | 0.30 | 0.35 | no | yes | 1.5 over a 150-tick window |
| schism | 0.20 | 0.30 | 0.50 | yes | no | 0 |
| player_civilization | 0.60 | 0.25 | 0.15 | no | yes | 0 |
| breakaway | 0.45 | 0.30 | 0.25 | no | yes | 0 |
| default | 0.40 | 0.30 | 0.30 | no | yes | 0 |

`factor_1 = t_n / 100` if tension-primary else `1 − m_n / 100`. `current_value = 0` if n is unowned, else `((e_n · 0.60 + p_n · 0.40) / 100) · ATTRACT_VALUE_MULTIPLIER`, multiplier `2.0`, subweights `ATTRACT_ECONOMY_SUBWEIGHT = 0.60`, `ATTRACT_POPULATION_SUBWEIGHT = 0.40`. `strategic_position` = mean over n's neighbors not owned by this faction of `(e · 0.60 + p · 0.40)/100` for owned ones and `EXPANSION_POTENTIAL = 0.15` for unowned ones; 0 if none. `attractiveness = w_weakness · factor_1 + w_value · current_value + w_position · strategic_position`, then `×(1 + damage_history[n] · boost)` if the archetype has a boost. Unowned n with can-colonize goes to the colonize candidates. Owned n goes to the attack candidates only if either side's stance is hostile and `current_value ≥ MIN_ATTACK_VALUE = 0.05`. Each neighbor is scored once even if adjacent to several owned regions.

**ALG-12 Budget pressure.** `potential_commit = budget · ATTACK_COMMIT_FRACTION`, fraction `0.70`. With `weakest = min m_n over attack candidates`, `break_even = (weakest · RESISTANCE_FACTOR) / (ATTACK_COMMIT_FRACTION · ATTACK_EFFICIENCY)`, `RESISTANCE_FACTOR = 0.55`, `ATTACK_EFFICIENCY = 1.0`. If `break_even > 0` and `budget / break_even > BUDGET_PRESSURE_THRESHOLD = 0.8`: `effective_confidence = attack_confidence · (0.8 / (budget / break_even))`; else `effective_confidence = attack_confidence`. `attack_confidence` is rolled once at faction creation, uniform in `ATTACK_CONFIDENCE_RANGE[archetype]`: conqueror (2.0, 6.0), fortifier (4.0, 10.0), player_civilization (3.0, 8.0), breakaway (2.0, 5.0), otherwise `ATTACK_CONFIDENCE_DEFAULT_RANGE = (4.0, 8.0)`.

**ALG-13 Entrenchment** of a target region. If never conquered (`held_since_tick` unset): `ENTRENCHMENT_MAX = 2.0`. Else `ratio = min(1, (tick − held_since) / ENTRENCHMENT_RAMP_TICKS)`, ramp `100`; `entrenchment = ENTRENCHMENT_BASE + (ENTRENCHMENT_MAX − ENTRENCHMENT_BASE) · ratio`, base `1.0`.

**ALG-14 Viability and scoring.** For each attack candidate: `net = potential_commit · ATTACK_EFFICIENCY − m_n · RESISTANCE_FACTOR · entrenchment(n)`; viable if `net > effective_confidence`. Best attack = the viable candidate with the highest attractiveness; its value is its `net`. Best colonize = the colonize candidate with the highest attractiveness. `norm(v, lo, hi) = clamp((v − lo)/(hi − lo), 0, 1)`. `attack_score = norm(best_net, ATTACK_NORM_RANGE = (0, 40)) · w_attack`; `colonize_score = norm(best_attract, COLONIZE_NORM_RANGE = (0, 1)) · w_expand`; decision weights from `ARCHETYPE_DECISION_WEIGHTS` (attack, expand, defend): conqueror 1.2/1.0/0.4, warlord 1.4/0.6/0.3, fortifier 0.8/0.8/1.5, opportunist 1.0/0.7/0.6, schism 1.3/0.0/0.5, player_civilization 0.3/0.5/1.5, default 0.8/0.6/0.8. Highest score wins; below `MIN_ACTION_THRESHOLD = 0.05` or no candidates: accumulate. Colonize with `budget < COLONIZE_COST = 20.0`: accumulate.

**ALG-15 Attack intent.** Commit `potential_commit`; source region = the owned region with the highest military. Telegraph preference `ARCHETYPE_TELEGRAPH_PREFERENCE`: conqueror 0.7, warlord 0.3, fortifier 0.8, opportunist 0.4, schism 0.3, player_civilization 0.6, default 0.5; `+0.2` if `m_target > 60`, `−0.2` if `m_target < 30`, clamped [0, 1]. One RNG draw: telegraph if `rng.random() < pref`, else surprise. A telegraphed attack is declared now and resolves at `tick + TELEGRAPH_PREP_TICKS = 1`.

**ALG-16 Colonize intent.** Commit `COLONIZE_COST = 20.0`; source = the first owned region adjacent to the target.

**ALG-17 Budget accumulation.** `Δbudget = Σ over owned inhabited regions of (e − REGION_MAINTENANCE_COST) · budget_growth_rate`, cost `8.0`, rate `BUDGET_GROWTH_RATE = 0.025`; `budget = max(0, budget + Δbudget)`.

**ALG-18 Reactive reinforce.** Among telegraphs targeting this faction, take the one with the largest commit. `reinforce_prob = min(1, w_defend / 1.5)`; one RNG draw, act if `draw ≤ reinforce_prob`. `commit = min(budget · REACTIVE_REINFORCE_BUDGET_FRACTION, telegraph_commit · 0.5)`, fraction `0.30`; no intent if `commit < 1.0`.

## Intent resolution (`intent_resolver.py`)

Intents are grouped by target region. Targets with two or more intents are collisions (ALG-23); the rest resolve individually in intent order.

**ALG-19 Reinforce.** `tier_cap = REINFORCE_MIL_CAP[tier]`: home 100, frontier 60. `headroom = max(0, (tier_cap − m)/tier_cap)`. `base = commit · REINFORCE_EFFICIENCY · headroom`, efficiency `0.5`. Variance uniform in `[0.85 − (t/100) · 0.20, 1.15 + (t/100) · 0.20]` (`REINFORCE_VARIANCE_BASE = (0.85, 1.15)`, `REINFORCE_VARIANCE_TENSION_SCALE = 0.20`). `Δm = base · variance`. Budget spent = commit.

**ALG-20 Attack.** `effective_attack = commit · ATTACK_EFFICIENCY · tech_attack(attacker) · surprise`, surprise `SURPRISE_EFFICIENCY_MULT = 0.5` in surprise mode else 1. `effective_defense = m · RESISTANCE_FACTOR · tech_defense(defender) · entrenchment` (ALG-13). `net = (effective_attack − effective_defense) · U(STOCHASTIC_RANGE)`, range `(0.7, 1.3)`, one RNG draw.

**ALG-21 Damage split.** Breakthrough if `net > BREAKTHROUGH_THRESHOLD = 15.0`: `Δm = −0.8 net`, `Δe = −0.3 net`, `Δt = +min(0.5 net, 30.0)`. Contested if `0 < net ≤ 15`: `Δm = −0.5 net`, `Δe = −0.2 net`, `Δt = +0.4 net`. Repelled if `net ≤ 0`: `Δm = −0.10 · effective_attack`, `Δe = 0`, `Δt = +2.0`. Budget spent = commit.

**ALG-22 Conquest.** Not repelled and `m + Δm < CONQUEST_THRESHOLD = 5.0`: the region changes owner; garrison `= commit · CONQUEST_GARRISON_FRACTION = 0.65` is added to military after damage; extra `Δe −= CONQUEST_ECONOMY_DISRUPTION = 5.0`, `Δt += CONQUEST_TENSION_SPIKE = 8.0`, `Δp −= CONQUEST_POPULATION_LOSS = 2.0`; the economy floor is bypassed. One RNG draw: with probability 0.60 a `CONQUEST_UNREST` chain is queued after a delay of `round(triangular(4, 8, mode 6))` ticks (second draw).

**ALG-23 Multi-faction collision.** For each colliding intent i of faction f: `eco_f = Σ economy of f's regions`; `max_eco = max over colliders` (1 if all zero); `factor_i = COLLISION_ECONOMY_FLOOR + (COLLISION_ECONOMY_CEILING − COLLISION_ECONOMY_FLOOR) · eco_f / max_eco`, floor `0.4`, ceiling `1.0`. `strength_i = commit_i · ATTACK_EFFICIENCY · factor_i · tech_attack(f) · surprise_i`. Winner is drawn once with probability `strength_i / Σ strength` (equal shares if the sum is 0). `second = max loser strength`; `margin = winner / (winner + second)`; `opp = Σ losers / winner`. `ret_ceiling = COLLISION_RETENTION_MAX · max(0, 1 − opp · COLLISION_RETENTION_OPPOSITION_SCALE)`, max `0.4`, scale `0.6`; `refund = winner_commit · U(0, ret_ceiling)` (one draw); winner spends `commit − refund`.

Then, if the target is owned by a faction that is not a collider, or is owned by a collider: every collider's strength is applied against the defender as in ALG-20/21 with the same defense value and a fresh stochastic draw each, damage summed; conquest per ALG-22 goes to the winner. If the target is unowned: the winner colonizes with `COLONY_START_*` (ALG-24), except military `×U(COLLISION_NARROW_MIL_PENALTY = 0.5, 0.70)` when `margin < COLLISION_NARROW_MARGIN = 0.6`. Each loser spends its full commit and takes `Δt = COLLISION_LOSER_TENSION_BASE · commit / budget` on its highest-military region, base `5.0`.

**ALG-24 Colonize.** Target fields become `COLONY_START_MILITARY = 10.0`, `COLONY_START_ECONOMY = 20.0`, `COLONY_START_TENSION = 20.0`, `COLONY_START_POPULATION = 25.0`; budget spent `COLONIZE_COST = 20.0`.

## Border friction (`border_friction.py`)

**ALG-25.** For each region with an owner, over every neighbor across a border edge owned by a different faction where either side's stance is hostile: `tension_f = BORDER_FRICTION_TENSION · (m_neighbor/100)`, `economy_f = BORDER_FRICTION_ECONOMY · (m_neighbor/100)`, constants `0.15` and `0.05`. Sum over hostile edges; `t = min(100, t + Σ tension_f)`, `e = max(ECONOMY_FLOOR, e − Σ economy_f)`; composites recompute.

## Technology (`technology.py`)

**ALG-26 Multipliers.** `mult_axis = 1 + (tech/100) · ARCHETYPE_TECH_MULTIPLIERS[archetype][axis]` for attack, defense, economy:

| Archetype | attack | defense | economy |
|---|---|---|---|
| conqueror | 0.16 | 0.02 | 0.02 |
| fortifier | 0.03 | 0.09 | 0.08 |
| warlord | 0.14 | 0.04 | 0.02 |
| opportunist | 0.10 | 0.05 | 0.05 |
| schism | 0.12 | 0.04 | 0.04 |
| player_civilization | 0.06 | 0.07 | 0.07 |
| breakaway | 0.06 | 0.08 | 0.06 |

**ALG-27 Growth.** Over owned inhabited regions: `growth = BASE_TECH_RATE · (avg_e/100) · max(TECH_POPULATION_FLOOR, avg_p/100)`, rate `0.35`, floor `0.3`; `tech = min(100, tech + growth)`. Starting tech = `avg starting population · STARTING_TECH_RATIO = 0.25`; `ARCHETYPE_STARTING_TECH` ranges apply only to factions created mid-game.

**ALG-28 Convergence.** Among factions this faction holds a cooperative stance toward, take the one with the highest tech above its own; `bonus = TECH_CONVERGENCE_RATE · max(0, partner_tech − tech)/100`, rate `0.1`; `tech = min(100, tech + bonus)`.

## Administrative revolts (`admin_revolt.py`)

**ALG-29.** Per faction: `excess = max(0, territory_count − ADMIN_REVOLT_INFLECTION_POINT = 4)`; `chance = ADMIN_REVOLT_BASE_RATE + ADMIN_REVOLT_SCALING_RATE · excess²`, base `0.001`, scaling `0.0005`. One RNG draw per owned region per tick; a draw below `chance` queues an `evt_admin_separatist` chain on that region for the next tick.

## World generation (`world.py`)

**ALG-30 Starting fields.** Population uniform in `HOME_POPULATION_RANGE = (55, 75)` or `FRONTIER_POPULATION_RANGE = (25, 50)`. Then, each with its own uniform jitter in `±STARTING_FIELD_JITTER = 5.0` and clamped [0, 100]: `e = p · STARTING_ECO_RATIO = 1.1 + jitter`, `m = p · STARTING_MIL_RATIO = 0.7 + jitter`, `t = p · STARTING_TENSION_RATIO = 0.3 + jitter`. Two phase offsets uniform in [0, 2π). Draw order: population, economy jitter, military jitter, tension jitter, economy phase, tension phase.

**ALG-31 Graph.** `n_regions` uniform integer in `WORLD_REGION_COUNT_RANGE = (40, 60)`; `WORLD_FACTIONS_PER_GAME = 15`. For each faction in order: one home and one frontier region, linked. Remaining regions are empty, shuffled. Each faction's frontier gets a corridor of `WORLD_MIN_FACTION_SEPARATION = 1` empties; corridor ends are chained in faction order. Every unassigned empty links to a random already-connected region, re-rolling up to 20 times to avoid homes. Then `max(1, floor(0.12 · n_regions))` extra edges (`WORLD_EXTRA_EDGE_RATIO`) between random distinct non-adjacent regions, never home-to-home, at most 10× that many attempts. Edge type is `both` between two regions of the same faction, else `border`. The world's RNG is reseeded from one final draw.

`bible_world.md`'s three named starting templates are not implemented; this generic generator is what runs (Stage 1 audit A-374, A-375).
