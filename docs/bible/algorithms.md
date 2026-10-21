# Algorithms — the retained equations

This is the "what stays" contract for the C rewrite. Every formula below was read from the Python source on 2026-09-10 (Stage 1 algorithm pass), verdicted keep-verbatim, and is reproduced here with its constants and config names. The C sim must reproduce each one bit-for-bit under the same seed, the same RNG draw order, and the same command stream. Tuning a constant is normal C-rewrite validation work and changes the value here in the same PR; changing a formula's shape is a requirement change and runs the change protocol in `docs/northstar/agile.md`.

All fields are floats clamped to [0, 100] unless stated. Economy has a floor of `ECONOMY_FLOOR = 8.0` under drift, friction, and standard events; conquest bypasses it. Ticks are integers from 1. Randomness is one seeded stream per world (`random.Random(seed)`); the draw order per tick is the order the formulas appear in the tick sequence below.

Not inventoried here: the renderer (E-16, E-18), which owns no gameplay equations.

## Tick sequence (`tick.py`)

One strategic tick, in this order. Feature flags in parentheses are all true at launch.

1. Resolve pending events whose due tick has arrived (`ENABLE_EVENTS`).
2. Evaluate fresh threshold triggers on every inhabited region; fired events enqueue their chain spawns. Any event that creates a faction spawns it here.
3. Faction agents (`ENABLE_FACTIONS`):
   - 3a snapshot every region before any mutation this tick;
   - 3b every faction accumulates budget (ALG-17);
   - 3c telegraphed attacks declared `TELEGRAPH_PREP_TICKS = 3` ticks ago resolve now;
   - 3d every faction decides (ALG-11 through ALG-16); an attack in telegraph mode is queued for 3c next tick, everything else is immediate;
   - 3e defenders of newly telegraphed attacks may reactive-reinforce (ALG-18);
   - 3f immediate intents resolve (ALG-19 through ALG-24), collisions first grouped by target.
   - 3.5 betrayal checks on cooperative pairs (ALG-40); a betrayal resolves as an attack at once.
4. Border friction on every region with a hostile neighbor (ALG-25) (`ENABLE_BORDER_FRICTION`).
   - 4.1 admin revolt roll per owned region (ALG-29) (`ENABLE_ADMIN_REVOLTS`);
   - 4.25 diplomacy timers then peace formation (ALG-38, ALG-39) (`ENABLE_DIPLOMACY`);
   - 4.5 technology growth then convergence, per faction (ALG-26 through ALG-28) (`ENABLE_TECHNOLOGY`).
5. Passive drift on every inhabited region (ALG-01 through ALG-08), applied with clamps, composites recomputed (ALG-09, ALG-10).
6. Zombie faction cleanup (ALG-42); coherence ledger attachment.
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

`factor_1 = t_n / 100` if tension-primary else `1 − m_n / 100`. `current_value = 0` if n is unowned, else `((e_n · 0.60 + p_n · 0.40) / 100) · ATTRACT_VALUE_MULTIPLIER`, multiplier `2.0`, subweights `ATTRACT_ECONOMY_SUBWEIGHT = 0.60`, `ATTRACT_POPULATION_SUBWEIGHT = 0.40`. `strategic_position` = mean over n's neighbors not owned by this faction of `(e · 0.60 + p · 0.40)/100` for owned ones and `EXPANSION_POTENTIAL = 0.15` for unowned ones; 0 if none. `attractiveness = w_weakness · factor_1 + w_value · current_value + w_position · strategic_position`, then `×(1 + (damage_history[n] / 100) · boost)` if the archetype has a boost, where `damage_history[n]` is the military plus economy region n lost to attack resolutions (ALG-21, ALG-22 damage deltas, not friction or drift) in the last `DAMAGE_HISTORY_WINDOW = 150` ticks (Q-035-01, 2026-09-12; the Python code never fed it). Unowned n with can-colonize goes to the colonize candidates. Owned n goes to the attack candidates only if either side's stance is hostile and `current_value ≥ MIN_ATTACK_VALUE = 0.05`. Each neighbor is scored once even if adjacent to several owned regions.

**ALG-12 Budget pressure.** `potential_commit = budget · ATTACK_COMMIT_FRACTION`, fraction `0.70`. With `weakest = min m_n over attack candidates`, `break_even = (weakest · RESISTANCE_FACTOR) / (ATTACK_COMMIT_FRACTION · ATTACK_EFFICIENCY)`, `RESISTANCE_FACTOR = 0.55`, `ATTACK_EFFICIENCY = 1.0`. If `break_even > 0` and `budget / break_even > BUDGET_PRESSURE_THRESHOLD = 0.8`: `effective_confidence = attack_confidence · (0.8 / (budget / break_even))`; else `effective_confidence = attack_confidence`. `attack_confidence` is rolled once at faction creation, uniform in `ATTACK_CONFIDENCE_RANGE[archetype]`: conqueror (2.0, 6.0), fortifier (4.0, 10.0), player_civilization (3.0, 8.0), breakaway (2.0, 5.0), otherwise `ATTACK_CONFIDENCE_DEFAULT_RANGE = (4.0, 8.0)`.

**ALG-13 Entrenchment** of a target region. If never conquered (`held_since_tick` unset): `ENTRENCHMENT_MAX = 2.0`. Else `ratio = min(1, (tick − held_since) / ENTRENCHMENT_RAMP_TICKS)`, ramp `100`; `entrenchment = ENTRENCHMENT_BASE + (ENTRENCHMENT_MAX − ENTRENCHMENT_BASE) · ratio`, base `1.0`.

**ALG-14 Viability and scoring.** For each attack candidate: `net = potential_commit · ATTACK_EFFICIENCY − m_n · RESISTANCE_FACTOR · entrenchment(n)`; viable if `net > effective_confidence`. A candidate whose target this faction already has a resolved attack against this same tick is excluded from viability (C3, DECISIONS.md Seventh round, 2026-09-19: at most one resolved attack per attacker-target pair per tick — a failed attack may be repeated against the same target on the next tick, not the same one). Best attack = the viable candidate with the highest attractiveness; its value is its `net`. Best colonize = the colonize candidate with the highest attractiveness. `norm(v, lo, hi) = clamp((v − lo)/(hi − lo), 0, 1)`. `attack_score = norm(best_net, ATTACK_NORM_RANGE = (0, 40)) · w_attack`; `colonize_score = norm(best_attract, COLONIZE_NORM_RANGE = (0, 1)) · w_expand`; decision weights from `ARCHETYPE_DECISION_WEIGHTS` (attack, expand, defend): conqueror 1.2/1.0/0.4, warlord 1.4/0.6/0.3, fortifier 0.8/0.8/1.5, opportunist 1.0/0.7/0.6, schism 1.3/0.0/0.5, player_civilization 0.3/0.5/1.5, default 0.8/0.6/0.8. Highest score wins; below `MIN_ACTION_THRESHOLD = 0.05` or no candidates: accumulate. Colonize with `budget < COLONIZE_COST = 20.0`: accumulate.

**ALG-15 Attack intent.** Commit `potential_commit`; source region = the owned region with the highest military. Telegraph preference `ARCHETYPE_TELEGRAPH_PREFERENCE`: conqueror 0.7, warlord 0.3, fortifier 0.8, opportunist 0.4, schism 0.3, player_civilization 0.6, default 0.5; `+0.2` if `m_target > 60`, `−0.2` if `m_target < 30`, clamped [0, 1]. One RNG draw: telegraph if `rng.random() < pref`, else surprise. A telegraphed attack is declared now and resolves at `tick + TELEGRAPH_PREP_TICKS = 3` (Q-036-01, 2026-09-12; the Python code used 1).

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

Then, if the target is owned by a faction that is not a collider, or is owned by a collider: every collider's strength is applied against the defender as in ALG-20/21 with the same defense value and a fresh stochastic draw each, damage summed; conquest per ALG-22 goes to the winner. If the target is unowned: the winner colonizes with `COLONY_START_*` (ALG-24), except military `×U(COLLISION_NARROW_MIL_PENALTY = 0.5, COLLISION_NARROW_MIL_PENALTY_MAX = 0.70)` when `margin < COLLISION_NARROW_MARGIN = 0.6`. Each loser spends its full commit and takes `Δt = COLLISION_LOSER_TENSION_BASE · commit / budget` on its highest-military region, `COLLISION_LOSER_TENSION_BASE = 5.0`.

**ALG-24 Colonize.** Target fields become `COLONY_START_MILITARY = 10.0`, `COLONY_START_ECONOMY = 20.0`, `COLONY_START_TENSION = 20.0`, `COLONY_START_POPULATION = 25.0`; budget spent `COLONIZE_COST = 20.0`.

## Border friction (`tick.py`, `_apply_border_friction`)

**ALG-25.** For each inhabited region with an owner, over every neighbor across a `border` or `both` edge (trade-only edges contribute nothing; Q-041-01, 2026-09-13) that is owned by a different faction where either side's stance toward the other is hostile: `tension_f = BORDER_FRICTION_TENSION = 0.15` and `economy_f = BORDER_FRICTION_ECONOMY = 0.05`, flat per hostile neighbor, not scaled by the neighbor's military. Sum over hostile neighbors; `t = min(FIELD_MAX = 100, t + Σ tension_f)`, `e = max(ECONOMY_FLOOR, e − Σ economy_f)`; composites recompute.

The Python code counted every edge type; the dead module `simulation/border_friction.py` scaled by military. Neither is the design; the C rewrite implements the version above.

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

**ALG-27b Knowledge Lost** (added 2026-09-15, Q-046-01; no Python precedent). After growth, per faction: eligible if `avg_e < KNOWLEDGE_LOST_ECONOMY = 20.0` or `avg_p(now) ≤ avg_p(tick − 50) − KNOWLEDGE_LOST_POP_DROP = 10.0`, and `tick − last_knowledge_lost ≥ KNOWLEDGE_LOST_COOLDOWN = 100`. One uniform draw; fire if `draw < KNOWLEDGE_LOST_P = 0.03`: `tech = max(0, tech − KNOWLEDGE_LOST_DELTA = 5.0)`, a fired-event record (template Knowledge Lost, the faction's highest-population region, next chain tag), `last_knowledge_lost = tick`. Target rate (E-06 R-045-09): mean 1 to 2 events per 50-tick window across 50 factions over a 5,000-tick run; retune the constants, never the rule's shape.

**ALG-28 Convergence.** Among factions this faction holds a cooperative stance toward, take the one with the highest tech above its own; `bonus = TECH_CONVERGENCE_RATE · max(0, partner_tech − tech)/100`, rate `0.1`; `tech = min(100, tech + bonus)`.

## Administrative revolts (`admin_revolt.py`)

**ALG-29.** Per faction: `excess = max(0, territory_count − ADMIN_REVOLT_INFLECTION_POINT = 4)`; `chance = ADMIN_REVOLT_BASE_RATE + ADMIN_REVOLT_SCALING_RATE · excess²`, base `0.001`, scaling `0.0005`. One RNG draw per owned region per tick; a draw below `chance` takes one more integer draw `L` uniform in [ADMIN_REVOLT_CHAIN_MIN = 3, ADMIN_REVOLT_CHAIN_MAX = 8] and queues an `evt_admin_separatist` chain of length `L` ticks on that region for the next tick (short chain for L in [3, 4], medium [5, 6], long [7, 8]; E-05 R-040-03, E-04 S-030; Q-040-01, 2026-09-12).

## Events (`events.py`)

Added in Stage 2 from source (2026-09-10); not part of the Stage 1 algorithm pass. Template values are in `epics/E-04-events-and-chains.md` S-030.

**ALG-32 Noise offsets.** At the start of each time jump, for every region and every template with a trigger field, one uniform draw in `[−EVENT_NOISE_RANGE, +EVENT_NOISE_RANGE]`, range `10.0`. Draw order: regions in world order, templates in library order.

**ALG-33 Threshold triggers.** For ticks `≤ EVENT_GRACE_PERIOD = 3`: no firing; the per-(region, template) breached flag is set from the current field (`field > threshold + offset` for `above`, `<` for `below`). After the grace period: `now = field > T + offset` (or `<`); fire if `now` and not `was`; store `now`. Fresh triggers are evaluated for every region against the tick-start fields after the pending queue has resolved; a fired trigger's deltas join that region's per-tick delta sum (ALG-36) and apply once at the end, so no region's firing changes what another region's crossing reads (Q-026-01, 2026-09-14; the Python code applied each region's effects before evaluating the next).

**ALG-34 Probability triggers.** Only the regional revolt uses this mode. Skip if `tick − last_fired < REVOLT_COOLDOWN_TICKS = 12`. `p = REVOLT_BASE_PROBABILITY · (tension/100)^REVOLT_TENSION_EXPONENT`, base `0.007`, exponent `0.8`. One draw; fire if `draw < p`; record `last_fired = tick`. Evaluated after the threshold templates for the same region.

**ALG-35 Firing and spawning.** Effects apply per field as `max(floor, min(100, field + delta))` with floors economy `ECONOMY_FLOOR = 8.0`, tension `TENSION_FLOOR = 12.0`, others 0; composites recompute. For each chain spawn, in template order, one delay `d = clamp(round(triangular(a, b, (a + b)/2)), a, b)` from one uniform draw (Q-027-01, 2026-09-12; the Python code drew `randint(a, b)` uniformly); queue `{template, region, due = tick + delay, probability, conditions, chain_tag}`. Every chain start, whether a fresh trigger, a conquest spawn, or an admin-revolt spawn, takes the next value of one global counter (`chain_NNNN`, saved with the world; E-04 R-027-06); the Python code used a per-template string for fresh triggers, which the C rewrite drops.

**ALG-36 Pending resolution.** All entries with `due == tick` are removed from the queue and grouped by region. Per region: exclusion pass (ALG-37); then for each surviving entry in queue order, if conditions fail (`above v` requires `field > v`, `below v` requires `field < v`) skip with no draw and write a `pruned` record to the tick log (Q-027-02, 2026-09-12); else one draw, fire if `draw ≤ probability`; a fired entry adds its deltas to a per-field sum and queues its own spawns (ALG-35 draw per spawn). After all entries, each nonzero summed delta applies once against the tick-start field with the ALG-35 floors, and composites recompute once.

**ALG-37 Mutual exclusion.** Collect every exclusion tag among the region's due entries; for each tag in sorted order, among entries still resolved that carry the tag, keep the one with the highest probability (ties: one uniform draw, below 0.5 keeps the earlier-queued entry, otherwise the later; Q-028-01, 2026-09-12) and re-queue each other one with `due = tick + randint(1, 2)` (one draw per loser).

## Diplomacy (`diplomacy.py`)

Added in Stage 2 from source (2026-09-10). Stances are stored per unordered pair with a non-aggression counter and a cooperative-since tick. A missing pair reads hostile; a faction toward itself reads cooperative. See Q-042-01: the live game never initializes the table.

**ALG-38 Starting stance and timers.** Starting stance per archetype pair from `STARTING_STANCE_OVERRIDES` (conqueror hostile to every archetype; fortifier hostile to player and opportunist; opportunist hostile to player; schism hostile to player, fortifier, opportunist, warlord), else neutral. Each tick, for each neutral pair that shares at least one border edge: counter = 0 if an attack between them appears in this tick's actions, else counter + 1.

**ALG-39 Peace formation.** For each neutral pair with counter ≥ `PEACE_FORMATION_THRESHOLD = 80`: `stab = min(avg stability of A's regions bordering B, avg of B's bordering A)`; if `stab < PEACE_STABILITY_THRESHOLD = 35.0`, counter = 0, no draw. Else `p = clamp(PEACE_BASE_PROBABILITY · (1 − |avg_e_A − avg_e_B|/100) · (stab/100) · disp_A · disp_B, 0, 1)`, base `0.5`, dispositions `ARCHETYPE_PEACE_DISPOSITION`: conqueror 0.1, fortifier 2.0, warlord 0.2, opportunist 1.0, schism 0.3, player_civilization 1.5, breakaway 0.8. One draw; success if `draw < p`: stance cooperative, cooperative-since = tick, shared edges `both`. Failure: counter = 0.

**ALG-40 Betrayal.** For each cooperative pair, for (A as betrayer, B as victim) then (B, A): `opportunity = min(BETRAYAL_OPPORTUNITY_CAP, max(1, border_mil_A / border_mil_B))` with border military the mean military of the betrayer's regions bordering the victim (cap `3.0` when the victim's is 0); `pressure = max(1, avg_tension_A / 50)`; `p = clamp(BASE_BETRAYAL_RATE · weight_A · opportunity · pressure, 0, 1)`, base `0.005`, weights `ARCHETYPE_BETRAYAL_WEIGHT`: conqueror 2.5, fortifier 0.3, warlord 2.0, opportunist 2.0, schism 1.5, player_civilization 0.5, breakaway 1.0. One draw; betray if `draw < p`: stance hostile, shared edges `border`, and an attack intent on the victim's lowest-military region bordering the betrayer with `commit = betrayer's entire budget`, no attack mode (full efficiency), resolved immediately by ALG-20 through ALG-22. At most one betrayal per pair per tick.

## Lifecycle (`tick.py`, `lifecycle.py`)

**ALG-41 Breakaway creation.** On a faction-creating event in an owned region. Admin revolt: pruned if the region's owner differs from the chain's source faction or the region changed hands after the chain started; success rate 1.0. Tension revolt: `rate = U(REVOLT_SUCCESS_RANGE = (0.50, 0.95))` (one draw), then a second draw must be `≤ rate`, and population must be `≥ REVOLT_BREAKAWAY_POP_FLOOR = 25.0`. Then `military −= military · REVOLT_MILITARY_STEAL = 0.60`, `economy −= economy · REVOLT_ECONOMY_STEAL = 0.40` (the amounts are removed, not transferred). Latent loyalty (ALG-43) may revert instead. Otherwise: new faction `breakaway_<tick>_<region>`, region `previous_faction = old owner`, `tension = min(tension, REVOLT_TENSION_CAP = 40.0)`, `population = max(population, REVOLT_BREAKAWAY_POP_FLOOR)`, `economy = max(economy, REVOLT_ECONOMY_FLOOR = 20.0)`; archetype `breakaway` for tension revolts, one draw from [conqueror, fortifier, warlord, opportunist, schism] for admin revolts; budget 0; stance hostile both ways with every faction; color drawn to avoid existing hues (up to 30 draws, hue distance > 0.08); tech = parent's current tech.

**ALG-42 Zombie cleanup.** Pass 1: every `breakaway_*` faction with zero regions whose creation tick is ≥ `ZOMBIE_GHOST_TICKS = 5` ticks ago is removed. Pass 2: every remaining `breakaway_*` with exactly one region, created ≥ `ZOMBIE_CLEANUP_TICKS = 50` ago, budget < `COLONIZE_COST = 20.0`, and not a conqueror this tick, gives its region to the bordering (border-edge) faction with the most regions (ties: first found), sets `previous_faction` = itself and held-since = tick, and is removed. Removal deletes the faction from every stance table and unowns any remaining regions.

**ALG-43 Latent loyalty.** After the split in ALG-41, if the region has a previous owner different from its current owner, `tick − held_since ≤ LATENT_LOYALTY_TICKS = 20`, one draw `< LATENT_LOYALTY_REVERT_CHANCE = 0.5`, and the previous owner still exists: the region reverts to the previous owner with held-since = tick, previous owner cleared, and the same tension cap and floors as ALG-41.

**ALG-44 Lifecycle phase.** Given a faction's recent event list: fragmentation if (admin events + revolts + reversions) / max(1, len(events)) ≥ `LIFECYCLE_FRAGMENTATION_REVOLT_RATE = 0.02`; else overextension if `regions · REGION_MAINTENANCE_COST / Σ economy > LIFECYCLE_OVEREXTENSION_DRAIN_RATIO = 0.4`; else conflict if attacks / len ≥ `LIFECYCLE_CONFLICT_ATTACK_RATE = 0.05`; else expansion if distinct empty regions bordering the faction / inhabited region count ≥ `LIFECYCLE_EXPANSION_EMPTY_THRESHOLD = 0.3`; else consolidation if any colonization and no attack; else equilibrium (also for zero regions).

## Time jump, selector, ledger (`time_jump.py`, `character_selector.py`, `generational.py`, `coherence_ledger.py`)

Added in Stage 2 from source (2026-09-10).

**ALG-45 Time jump.** Length `n = clamp(requested, TIME_JUMP_MIN_TICKS = 20, TIME_JUMP_MAX_TICKS = 100)`; the live game requests `TIME_JUMP_TICKS_PER_CHAPTER = 50` every chapter (see Q-056-01). Runs `n` full ticks from `start_tick + 1`, records an ownership snapshot every `OWNERSHIP_TIMELINE_STRIDE = 2` ticks and at the end, then once at the end tick: lineage member generation (ALG-48), natural deaths (ALG-49), territory and faction diffs, per-faction average field deltas, and the chronicle (E-09).

**ALG-46 Rotation decision.** In order: (1) forced rotation if the lineage has no living member, or the commander is dead and no living non-supreme member is within `SELECTOR_PROXIMITY_HOPS = 2` hops of the mission region; (2) stay if the lineage's chapter counter `< SELECTOR_MIN_CHAPTERS = 2`; (3) [code: rotate if counter `≥ SELECTOR_HARD_CAP = 6`; removed by Stage 1 verdict A-050, replaced by the decay in Q-057-01]; (4) `t = min(1, delta / SELECTOR_DELTA_SAFE = 200)`, `p_rotate = SELECTOR_MAX_ROTATION_PROB + t · (SELECTOR_MIN_ROTATION_PROB − SELECTOR_MAX_ROTATION_PROB)` with `SELECTOR_MAX_ROTATION_PROB = 0.8` and `SELECTOR_MIN_ROTATION_PROB = 0.1`; one draw; if `draw < p_rotate` and the lineage home region's stability `< SELECTOR_CRISIS_THRESHOLD = 20.0`, stay (veto); else rotate with reason `normal`. Home region = first region in the lineage history. Stay picks the first living member within 2 hops of the mission region, else the current commander.

**ALG-47 Commander pools.** One draw selects a pool: previous-descendant `POOL_PREVIOUS_PROB = 0.70`, nemesis-descendant `POOL_NEMESIS_PROB = 0.20`, unrelated `POOL_UNRELATED_PROB = 0.10`; search order is the rolled pool then the others in that priority order. Previous: for each lineage played in an earlier chapter with a living member within 2 hops and last played `≥ SELECTOR_RECENCY_PENALTY_WINDOW = 1` chapters ago, `score = SCORE_GAP_WEIGHT · min(chapters_ago, SELECTOR_GAP_BONUS_PEAK = 4)/SELECTOR_GAP_BONUS_PEAK + SCORE_DENSITY_WEIGHT · min(living_nearby, SCORE_DENSITY_PEAK = 5)/SCORE_DENSITY_PEAK`, `SCORE_GAP_WEIGHT = 0.6`, `SCORE_DENSITY_WEIGHT = 0.4`; every nearby member carries its lineage's score; one weighted draw. Nemesis: living descendants within 2 hops of any character tagged rival of a previous commander, excluding the rivals; one uniform draw. Unrelated: create a `lineage_member` in the mission region's owning faction and a new lineage.

**ALG-48 Lineage generation.** At jump end: `n = max(1, floor(living · LINEAGE_FERTILITY_RATE = 0.03 · jump_ticks))` descendants; each: parent = uniform draw among living members; with probability `LINEAGE_SPREAD_PROBABILITY = 0.1` region = uniform draw among the parent's inhabited neighbors (all edge types), else the parent's region; rank `lineage_member`, generation parent + 1. Draw order per descendant: parent, spread roll, (neighbor draw), name, lifespan.

**ALG-49 Lifespan and succession.** `lifespan = randint(LIFESPAN_MIN = 150, LIFESPAN_MAX = 350)` at creation. At jump end, every active character with `tick − born ≥ lifespan` becomes historical with `death_tick = tick`; its name returns to the pool after `NAME_REUSE_COOLDOWN_TICKS = 500` (`NAME_REUSE_COOLDOWN_TICKS_MAIN = 4500` for a main character); a supreme commander is succeeded in the faction's first region and a regional commander in its region if still owned. Event attachment: events of significance tier `≥ CHARACTER_ATTACHMENT_TIER_THRESHOLD = 3` attach the region's characters.


**ALG-77 Selector history decay.** A lineage's history weight in the commander pools decays by `SELECTOR_DECAY_BASE = 0.75` per generation (Westley 2026-09-26, Q-060-02).

## Chronicle (`chronicle_distiller.py`, `chronicle_assembler.py`)

Added in Stage 2 from source (2026-09-10).

**ALG-50 Significance.** `base = tier + min(|Δ|_sum / SIGNIFICANCE_DELTA_SCALE, SIGNIFICANCE_DELTA_CAP)`, scale `50.0`, cap `3.0`, tier from the template (default 2). `context = 1.0 + 0.5·[region == last mission region] + 0.3·[character attached] + 0.1·min(chain_length, CHAIN_LENGTH_CAP = 5)·[chain_length > 1] + 0.8·[a lineage member lives in the region]` (`SIGNIFICANCE_MISSION_REGION_BONUS`, `_CHARACTER_BONUS`, `_CHAIN_LENGTH_BONUS`, `_LINEAGE_REGION_BONUS`). `score = base · context`.

constants-table: simulation/events.py TEMPLATES[*]["significance_tier"], the 26 launch templates' tier, transcribed verbatim (Python dict keys shown, upper-cased)
```
EVENT_TIER_EVT_GARRISON_COLLAPSE = 4
EVENT_TIER_EVT_BORDER_INCURSION = 4
EVENT_TIER_EVT_EMERGENCY_LEVY = 3
EVENT_TIER_EVT_REGIONAL_REVOLT = 4
EVENT_TIER_EVT_REVOLT_CRUSHED = 3
EVENT_TIER_EVT_REVOLT_ENTRENCHED = 5
EVENT_TIER_EVT_TRADE_BOOM = 3
EVENT_TIER_EVT_PROSPERITY_UNREST = 2
EVENT_TIER_EVT_POPULATION_CRISIS = 4
EVENT_TIER_EVT_RESISTANCE_MOVEMENT = 3
EVENT_TIER_CONQUEST_UNREST = 4
EVENT_TIER_EVT_LABOR_SHORTAGE = 3
EVENT_TIER_EVT_IMMIGRATION_WAVE = 2
EVENT_TIER_EVT_INFRASTRUCTURE_DECAY = 3
EVENT_TIER_EVT_MILITARY_BUILDUP = 3
EVENT_TIER_EVT_WAR_WEARINESS = 3
EVENT_TIER_EVT_CULTURAL_RENAISSANCE = 2
EVENT_TIER_EVT_FAMINE = 4
EVENT_TIER_EVT_FAMINE_RELIEF = 3
EVENT_TIER_EVT_DIPLOMATIC_INCIDENT = 2
EVENT_TIER_EVT_HARVEST_SURPLUS = 2
EVENT_TIER_EVT_ADMIN_SEPARATIST = 5
EVENT_TIER_EVT_ADMIN_POLITICAL_CRISIS = 5
EVENT_TIER_EVT_ADMIN_POPULAR_SUPPORT = 5
EVENT_TIER_EVT_ADMIN_MILITARY_DEFECTION = 5
EVENT_TIER_EVT_ADMIN_BREAKAWAY = 6
```
end constants-table (`om_event_template_significance_tier` reads this table by template id, F2o/B1-8)

**ALG-51 Clustering.** (1) Events flagged `mission_consequence` form one consequence cluster, category by outcome: success, failure, else mixed. (2) Lineage events (lineage member in region, or attached character in the lineage, or region == last mission region) cluster by region; category by E-09 R-067-02; if none, one `lineage_quiet` cluster in the lineage's first active member's region, else its last history region, else the mission region. (3) Remaining events with a chain tag cluster by tag, category by R-067-04, then clusters with equal (primary region, category) merge. (4) Remaining untagged events cluster by region, category by R-067-05. Primary region = most common region in the cluster. Peak score = max event score.

**ALG-52 Selection.** Order: consequence clusters, then lineage clusters, then the rest by peak score descending, skipping any category already used twice, until `CHRONICLE_MAX_ENTRIES = 10`; if fewer than `CHRONICLE_MIN_ENTRIES = 5`, add skipped clusters in order while a category has fewer than 2.

**ALG-53 Assembly.** RNG seeded with the jump start tick. Per cluster: resolve slot values; draw opening, detail, closing uniformly from the category pools filtered to resolvable slots; slot echo (same value ≥ 6 words in adjacent fragments) replaced by an anaphoric form; word echo (4+ letters, non-stop word, second occurrence) replaced from the synonym map; first mention of a region appends ", held by <faction name>" unless the entry already names both. Then cross-entry dedup: content words (lowercase, > 3 letters, non-stop); drop a later entry whose overlap with any kept entry ≥ `0.40` of the smaller set. Warnings at base ≥ 90 words or expanded ≥ 140.

## Missions (`mission_generator.py`, `objectives.py`, `outcome_resolver.py`, `force_allocator.py`)

Added in Stage 2 from source (2026-09-10).

**ALG-54 Candidate pool.** Regions = the player's regions plus every neighbor (all edge types), excluding empty tier. For each region and each of the 10 archetypes, the archetype's trigger function returns fired plus a context; fired pairs enter the pool.

**ALG-55 Scoring and selection.** `urgency = clamp(URGENCY_FIELD_WEIGHT · deficit + URGENCY_CONFLICT_WEIGHT · conflict + URGENCY_CHAIN_WEIGHT · chain)`, weights `0.4 / 0.4 / 0.2`; `deficit = ((100 − m) + (100 − e) + (100 − stability))/300`; `conflict = clamp(min(1, max_hostile_neighbor_m/70) + 0.5 · min(1, 0.5 · n_attacks + Σ budget/600) + 0.3 · min(1, 0.5 · adjacent_regions_lost))`; `chain = min(1, 0.3 · n_revolt_events_in_region)`. `relevance = clamp(RELEVANCE_LINEAGE_WEIGHT · lineage + RELEVANCE_PROXIMITY_WEIGHT · (1 − hops/RELEVANCE_MAX_HOPS) + RELEVANCE_ARCHETYPE_WEIGHT · min(1, archetype_count/RELEVANCE_ARCHETYPE_FIT_THRESHOLD))`, weights `0.4 / 0.3 / 0.3`, max hops `5`, fit threshold `3`; lineage = 1.0 if a member lives in the region, 0.5 if the region is in the lineage history, else 0; hops from the lineage's first history region by BFS over all edges, capped at 5. `preference = GENERATOR_RARE_PREFERENCE = 0.1` if rare, else the player's weight, default `GENERATOR_DEFAULT_PREFERENCE = 0.5`. `score = 0.5 · urgency + 0.3 · relevance + 0.2 · preference` (`GENERATOR_*_WEIGHT`). Sort descending; pool = top `GENERATOR_TOP_N_CANDIDATES = 5`; one draw `r = U(0, Σ score)`, first candidate whose cumulative score ≥ r.

**ALG-56 Time limit.** `limit = max(B · (1 − urgency · TIME_PRESSURE_SCALING = 0.2), B · TIME_LIMIT_FLOOR_PCT = 0.6)`, B the archetype's base time in minutes × 60 × `TACTICAL_TICK_RATE`: siege 60, multi-front 60, assault 52.5, containment 52.5, reconquest 45, defensive 37.5, interception 37.5, counterinsurgency 37.5, suppression 30, evacuation 30 (Q-076-01, Q-076-02).

**ALG-57 Force parity.** Enemy power: attack-driven archetypes `budget_committed · BUDGET_TO_POWER_SCALE = 300`; insurgent archetypes `insurgent_m · MILITARY_TO_POWER_SCALE = 2000` with `insurgent_m = U(lo, hi)`, `lo, hi` linearly interpolated from `INSURGENT_MIL_LOW_POP_RANGE = (20, 50)` at population `≤ 25` to `INSURGENT_MIL_HIGH_POP_RANGE = (40, 70)` at `≥ 70`; others `region.m · 2000`. Parity: piecewise linear through `PARITY_BREAKPOINTS = [(0, 0.80), (0.3, 0.85), (0.5, 0.90), (0.7, 0.95), (1.0, 1.00)]` on region capacity/100; easy `max(base, 0.95)`, hard `min(base, 0.85)`; then `max(parity, PARITY_FLOOR = 0.75)`. Fill: for each unit type in descending profile ratio, add units while `allocated < budget · ratio` and `power ≤ 1.15 · remaining`. Shortfall: if capacity `< CAPACITY_SHORTFALL_THRESHOLD = 0.4`, remove `CAPACITY_SHORTFALL_REDUCTION = 0.20` of the units round-robin from the most numerous types, keeping at least 1. The insurgent population threshold (`≤ 25` above) is confirmed at 25 (Westley 2026-09-26, Q-057-02; `OM_MISSION_INSURGENT_POP_LOW_THRESHOLD`); the shortfall threshold is 0.4 of capacity, a different number.

**ALG-58 Outcome.** `objective_score = Σ weight · (0 if failed else completion)`; `retention = min(1, Σ surviving unit power (HP-scaled) / initial power)`; `final = OUTCOME_WEIGHT_OBJECTIVE = 0.75 · objective_score + OUTCOME_WEIGHT_RETENTION = 0.25 · retention`; band by `OUTCOME_THRESHOLDS[archetype]` (E-10 R-077-02), strict less-than. Terminal: every primary complete or failed, or `tick ≥ limit`, or no living player unit. Commander survived = commander unit alive.

**ALG-59 Consequences.** For each row of `CONSEQUENCE_TABLES[archetype][band]`: `delta = (100 − v) · pct/100` for form `deficit`, `v · pct/100` for `current`; targets `mission`, `home`, `exposed` resolve to the mission region (see Q-078-01), `adjacent_player` to player-owned neighbors; clamp [0, 100]. Ownership transfers to the player for bands in `REGION_TRANSFER_OUTCOMES`: reconquest {total, strong, partial success}, assault and suppression {total, strong success}. Refusal: `tension += (100 − tension) · REFUSAL_TENSION_PENALTY_PCT = 8 / 100`. Commander death emits `evt_commander_killed_in_action` flagged as a mission consequence.

## Tactical: units, damage, abilities (`damage.py`, `ability.py`, `unit.py`)

Added in Stage 2 from source (2026-09-10). Tactical ticks run at `TACTICAL_TICK_RATE = 20` per second. Unit stats are the table in `epics/E-11-units-and-combat.md` S-082 (`UNIT_STATS`).

**ALG-60 Damage.** `damage = base · CATEGORY_MULTIPLIER[attacker_cat][target_cat] · output_mult(attacker) · (1 − reduction(target))`. Matrix: Strike {Strike 1.0, Line 0.75, Siege 1.5}; Line {Strike 1.5, Line 1.0, Siege 0.75}; Siege {Strike 0.20, Line 1.5, Siege 1.0} (see Q-081-01). Output multipliers: Surge `2.0`, Intercept `1.5`, Brace `1.3` while active, else 1.0. Reduction: Brace `0.50` + Fortify `0.20` for any friendly within `FORTIFY_RADIUS = 350` of an active Bastion + Warden aura `WARDEN_AURA_DAMAGE_REDUCTION = 0.10` per Warden within `WARDEN_AURA_RADIUS = 300`. An attack fires when the unit's attack timer reaches `attack_interval · 20` ticks with a target in range; after firing the unit's movement pauses `ATTACK_BACKSWING_SEC = 0.5`. No range falloff. Damage is accumulated per target for the tick and applied at once.

Direction changed 2026-10-02, rewrite pending: a unit's first attack is ready on the tick its target is first in range, with no wait for a full interval (E-11 S-084, R-084-01). The text above is what the game does today.

**ALG-61 Area damage.** For a Bombard attack on target T: every enemy on the attacker's layer within `aoe_radius = 150` of T's position takes ALG-60 damage in unit-id order until the running total reaches `base · AOE_DAMAGE_CAP_MULTIPLIER = 4.0`; the last hit is truncated to the cap.

Direction changed 2026-10-02, rewrite pending: an area attack reaches enemies on the layer offsets its type's reach includes, not only on the attacker's own layer (E-01 S-164, R-008-03). The text above is what the game does today.

**ALG-62 Targeting.** Each tick: units under a plain move skip targeting. A unit keeps its current target if alive and within attack range. Otherwise, on its cohort tick (`uid mod TARGETING_COHORT_COUNT = 4 == tick mod 4`) it acquires the nearest same-layer enemy within attack range; failing that, an attack-moving unit with sensor radius > attack range acquires the nearest visible same-layer enemy within sensor radius and moves toward it. Return fire: an idle unit with no target and no order that takes damage targets the attacker. Flinch: a unit that cannot return fire moves `_RETURN_FIRE_FLEE_DIST = 200` wu away from the attacker.

Direction changed 2026-10-02, rewrite pending: pursuit goes through ordinary movement and holds only while the unit's own target is in range, return fire also turns attack-moving units, a unit acts only on what its side can see, and its type's reach names the layers it may fire at (E-11 S-087, E-12 S-093, E-01 S-164). The text above is what the game does today.

**ALG-63 Abilities.** One per type (`ABILITY_MAP`). Surge: duration `60` ticks, speed × `2.5`, damage × `2.0`, cooldown `1500`. Intercept: passive; when cooldown is 0 and an enemy Strike unit is within `INTERCEPT_DETECTION_RADIUS = 350` on the same layer, activate for the first engagement with speed × `1.8`, damage × `1.5`, cooldown `600`. Brace: windup `40` ticks immobile without bonus, then active with reduction `0.50` and damage × `1.3`; toggling off repeats the windup; cooldown `700` from activation. Rally: instant `112` HP to every friendly within `400`, capped at max HP; cooldown `1500`. Barrage: `30`-tick telegraph, then ALG-61 at the target with base × `3.0` within radius `100`; cooldown `1800`. Fortify: `400` ticks, reduction `0.20` within `350`, Bastion speed × `0.4`; cooldown `1400`. Warden aura (passive): friendlies within `300` regain `WARDEN_AURA_REPAIR_RATE = 0.075` HP per tick. Cooldowns tick down every tick; activation on cooldown is rejected.

**ALG-64 Squads.** A Strike unit is one entity (one HP, one position); squad membership is rendering only.

## Tactical: fog and sensors (`fog_of_war.py`)

**ALG-65 Visibility.** Per observer: `effective = sensor_radius · (1 − interference(observer position))`; at vantage (within a `vantage_point` node's `radius`, default `100`) cross-layer factors are `min(f · VANTAGE_CONE_MULTIPLIER = 2.0, 1)` for [1.0, `CONE_LAYER_1_FACTOR = 0.50`, `CONE_LAYER_2_FACTOR = 0.20`] plus `VANTAGE_EXTRA_LAYER = 1` extra factor of `min(0.20 · 2.0, 1)`. For each enemy: if the observer's pulse is active and distance ≤ `PULSE_RADIUS = 500`, visible; else `factor = factors[layer_diff]` (0 beyond the list); visible if distance ≤ `effective · factor` and no cover blocks the segment between the units' layer midpoints. Pulse: `PULSE_REVEAL_TICKS = 40`, `PULSE_COOLDOWN_TICKS = 400`. The player-visible set is the union over the player's units. `ELEVATION_SENSOR_BONUS_PER_TIER = 0.15` is defined and unused (Q-092-01).

Direction changed 2026-10-02, rewrite pending: the targeted ping replaces the pulse, a force that emits or stays silent changes how far it sees and is seen across layers, a unit acts on its side's visible set, and cover blocks only up to its height and only a line between two units outside it (E-01 S-162, S-163, S-007; E-12 S-093). The text above is what the game does today.

## Tactical: movement and command (`movement.py`, `command.py`, `facing.py`)

**ALG-66 Group move.** For a selection of 2+ living units with `FORMATION_MOVE_ENABLED`: centroid c; scattered if any unit is farther than `MAGIC_BOX_SPREAD_RADIUS = 450` from c; each unit's slot = click + (unit − c), or the click point if scattered or the slot cell is unwalkable; the group is registered and terminated when the centroid arrives or every unit is within `ARRIVAL_TOLERANCE_MULT = 1.5 · UNIT_COLLISION_RADIUS = 15` of its slot. Slowest-unit pace (A-557) is not implemented (Q-095-01).

Direction changed 2026-10-02, rewrite pending: attack-move is a group order that takes formation slots, a group moves at its slowest member's pace, and a movement ability detaches the unit from it (E-13 S-095, S-096). The text above is what the game does today.

**ALG-67 Routing.** Grid cells `NAVMESH_CELL_SIZE = 100` per layer; blocked where obstacle density > `NAVMESH_OBSTACLE_THRESHOLD = 0.7`; density is stored for every cell of the largest canvas (280 x 280 per layer), and a cell outside the canvas is blocked. A route is a breadth-first distance field from the destination cell over open cells (4 neighbours, fixed order, so ties settle the same every run, no search cap), kept for the 16 most recent destination cells and recomputed when any cell turns blocked or open; the unit aims at the farthest cell centre on the shortest path that its line of sight (exact supercover walk, a corner needs both side cells open) still reaches, or at the destination itself when that is in sight, and plans again within `2 · 15` wu of a waypoint. A destination with no route is replaced by the nearest reachable point; a unit found inside a blocked cell of its layer is moved to the nearest open cell, and a step or push that would enter one slides along it.

**ALG-68 Steering and collision.** Probe `STEERING_PROBE_DIST = 40` ahead for units on the mover's own layer (group mates and idle friends included) within blocking radius, each read at its start-of-tick position; if blocked, sweep alternate headings of +30, -30, +60, -60, +90, -90 degrees from the seek heading, in that order (fixed direction vectors, no trigonometry), take the first clear one and hold it for `STEERING_DETOUR_MIN_DIST = 60` wu of distance moved; if none is clear, continue straight. Direct-move units sample obstacle density within `STEERING_OBSTACLE_AVOIDANCE_RANGE = 50` and take a repulsion when > 0.3; waypoint followers are exempt. After movement, same-layer pairs closer than `2 · 15` are pushed apart along their axis, every unit, moving or stopped, starting pair checks, in up to `COLLISION_PASSES = 10` push passes per tick that stop early when no pair is closer than `2 · 15` or when a pass displaces no unit by more than `COLLISION_SETTLE_EPS = 0.1` wu (a unit's total move over the whole pass; that pass is applied); a unit with no move target or halted by engagement takes zero push, and two such units split the push equally; equal positions push the lower id along +x. A moved or pushed position is clamped to the map canvas (`[0, width] x [0, height]`; no clamp while no canvas is set). A route waypoint, the final one of a route that had waypoints included, is reached within `WAYPOINT_ARRIVE_MULT = 2.0` collision radii (30 wu); a direct move and a group slot keep 1.5 radii. Attack-move leash `200` wu from the acquisition anchor. A unit under a group move whose own slot it cannot reach ends its order where it stands once it has been within `GROUP_GIVEUP_RADIUS = 75` wu of its slot for `GROUP_GIVEUP_TICKS = 40` consecutive ticks without arriving; leaving the disc or arriving resets the count.

Direction changed 2026-10-02, rewrite pending: the steering sweep tries six angles in order, plus 30, minus 30, plus 60, minus 60, plus 90 and minus 90 degrees, takes the first clear one and goes straight if none is clear, only units on the same layer block, the probe reads positions as they stood at the start of the tick, and whether the leash is tested before or after damage is a switch the skill lab runs both ways (E-13 S-097; E-11 S-087). The text above is what the game does today.

**ALG-69 Facing.** Target if attacking, heading if moving, else hold; turn rate capped at `FACING_ROTATION_SPEED_STRIKE = 6.0`, `LINE = 4.0`, `SIEGE = 2.5` rad/s.

## Map generation (`map_generator.py`, `layout_instantiator.py`, `gradient_placer.py`, `layer_masks.py`, `fairness_evaluator.py`, `spine_drift.py`)

Added in Stage 2 from source (2026-09-10).

**ALG-70 Layout selection and instantiation.** Candidates = layouts whose tags satisfy any of the archetype's compatibility filters; one uniform draw. Zone positions (percent of canvas) scale to the canvas, jittered by up to `LAYOUT_JITTER_PERCENT = 0.03` of canvas per zone. Canvas dimension is a uniform draw in `CANVAS_SIZE_RANGES` (small (8000, 12000), medium (12000, 20000), large (20000, 28000)) for the archetype's base category (see Q-118-01). Shipped library on 2026-09-10: 8 layouts; per archetype: defensive_stand 3, assault 5, multi_front_defense 2, containment 2, every other archetype 1 (see Q-112-01).

**ALG-71 Gradient sources.** Per instantiated node: chokepoint obstacle (`0.85`, `600`), staging obstacle (`0.60`, `800`), vantage elevation (`0.90`, `700`), hazard anchor interference (`0.75`, `500`), flank obstacle (`0.35`, `450`) and cover (`0.40`, `450`), chokepoint cover (`0.55`, `550`), objective cover (`0.50`, `400`), hazard cover (`0.35`, `400`) (`GRADIENT_*`). Layer masks: for a zone with `layer_restrictions`, one `layer_block_N` source per layer not listed, radius `LAYER_MASK_RADIUS = 600`, intensity `1.0`; accessibility at a point is open unless the sampled block value ≥ 0.5.

**ALG-72 Fairness.** `evaluate_fairness` scores path balance (max-flow staging→objective vs spawn→objective), travel-time balance (BFS hops), vantage proximity balance, and hazard proximity balance; `is_acceptable` compares to thresholds; the live pipeline logs the score and does not regenerate (`FAIRNESS_MAX_RETRIES = 5` exists, unused; see Q-113-01).

**ALG-73 Spine drift.** A drifting node (types objective, reinforcement_structure) with waypoints w[0..n−1], period P, mode: at `t = tick mod P`, ping-pong splits P into 2(n−1) equal segments out and back, loop into n segments around, and the position is the linear interpolation within the current segment.

## Enemy macro behavior (`behavior_runner.py`, `trigger_bus.py`)

**ALG-74 Behavior runner.** Per force at mission start: for every transition and hook, one uniform draw in ±`noise_pct` (default `SCRIPT_NOISE_DEFAULT_PCT = 0.15`, timers `SCRIPT_TIMER_NOISE_DEFAULT_PCT = 0.20`). Every `SCRIPT_EVAL_INTERVAL_TICKS = 40` ticks, for each force with living units: context = force HP fraction (× (1 + noise) for threshold checks), unit count, elapsed seconds since mission start (× (1 + noise) for timers), timer expired, bus flags. Hooks evaluate first, then transitions; the target state's behavior and modifier drive the commands issued. Bus flags are plain named booleans plus named values, saved with the mission. The context functions for player force in zone and enemy in range are stubbed (return 1.0 and False; Q-121-01).


**ALG-76 Macro rout and external reinforcement.** An enemy force routs when its remaining hit points fall below `OM_MACRO_ROUT_HP_THRESHOLD = 0.35` of its starting total (Westley 2026-09-26, Q-120-03; was 0.20 unsourced). At each macro evaluation (interval: the value the enemy macro uses today, name it in the promotion leaf) an external reinforcement wave arrives with probability `OM_MACRO_EXTERNAL_REINFORCEMENT_PROB = 0.21` (Westley 2026-09-26, Q-124-03, "triple it"; was 0.07); window and size per Q-124-02. A wave is ALG-75's standard composition (50 units), arriving 1 to 40 ticks after a successful roll (Westley 2026-09-28, Q-124-02).

## Reinforcement structures (`reinforcement.py`)

**ALG-75 Capture and production.** Each structure: capture radius `REINFORCEMENT_CAPTURE_RADIUS = 300`, HP `REINFORCEMENT_STRUCTURE_HP = 3000`. Per tick: factions present = factions of living units within the radius; if no non-owner faction, progress = 0; if exactly one non-owner faction and the owner absent, progress += `dt / REINFORCEMENT_CAPTURE_DURATION_SEC = 10`; at ≥ 1.0 ownership flips and progress resets. Owned structures advance a production timer; interval = `BASE_PRODUCTION_TIME_SEC = 30 · power(type) / POWER_NORMALIZATION = 100`; on expiry a unit spawns at the first free lattice slot within half the capture radius (R-126-02); no draw. Count = clamp(floor(region military · `MILITARY_TO_STRUCTURES_SCALE = 0.06`), `STRUCTURE_COUNT_RANGE[canvas]`); split by `ARCHETYPE_STRUCTURE_SPLIT`. Enemy production target: if any player category share ≥ `COMPOSITION_SKEW_THRESHOLD = 0.70`, shift `COMPOSITION_SHIFT_MAGNITUDE = 0.15` of the target toward the counter category (Strike→Line, Line→Siege, Siege→Strike) proportionally from the others, renormalize; produce the category most below target.

## World generation (`world.py`)

**ALG-30 Starting fields.** Population uniform in `HOME_POPULATION_RANGE = (55, 75)` or `FRONTIER_POPULATION_RANGE = (25, 50)`. For a home region of a faction with its own archetype range (`CONQUEROR_HOME_RANGE`: military (50, 65), economy (40, 55); `FORTIFIER_HOME_RANGE`: military (40, 50), economy (50, 65); `OPPORTUNIST_HOME_RANGE`: military (45, 55), economy (45, 55); the player faction has no archetype range and always uses the general formula below): military and economy are each drawn directly, uniform in the archetype's own range, taking the place of the two ratio draws below. Every other region — every frontier regardless of archetype, and the player faction's home — uses the general formula: each field with its own uniform jitter in `±STARTING_FIELD_JITTER = 5.0` clamped [0, 100]: `e = p · STARTING_ECO_RATIO = 1.1 + jitter`, `m = p · STARTING_MIL_RATIO = 0.7 + jitter`. Tension always uses the general formula regardless of archetype or tier: `t = p · STARTING_TENSION_RATIO = 0.3 + jitter`. Two phase offsets uniform in [0, 2π). Draw order is the same slot count either way — population, economy slot (archetype-range draw or ratio jitter), military slot (archetype-range draw or ratio jitter), tension jitter, economy phase, tension phase — only the formula each slot feeds changes.

**ALG-31 Graph.** `n_regions` uniform integer in `WORLD_REGION_COUNT_RANGE = (250, 400)`, then raised to the feasible minimum (sum of the rolled template sizes + one corridor empty per faction) when the draw fell below it, with no extra draw (a pinned count below that minimum fails generation instead; Q-021-07); `WORLD_FACTIONS_PER_GAME = 15`. Template roll, batched before placement: for each faction in order, one weighted draw among Isolated, Twin Colony, Archipelago — equal weight (1/3 each) by default. The draw's uniform in `[0, 1)` is bucketed in fixed `om_template` enum order, half-open, cumulative: Isolated `[0, w0)`, Twin Colony `[w0, w0 + w1)`, Archipelago `[w0 + w1, 1)`. If the player faction has set a preference, that template's probability becomes `WORLD_PLAYER_PREFERENCE_WEIGHT = 0.50` (configurable) and the other two split the remainder equally (`0.25` each by default) — the bucket order is still fixed `om_template` enum order regardless of which template is preferred, only the bucket widths change; this reweight applies to the player faction's own roll only, every NPC faction always uses equal weight. Feasibility gate: if `n_regions` < (sum of every rolled faction's template size) + 1, generation fails. Per-faction placement, in faction order: Isolated is 1 home + 2 frontiers, both frontiers adjacent to the home (`ISOLATED_FRONTIER_COUNT = 2`); Twin Colony is 2 homes adjacent to each other (`TWIN_COLONY_HOME_COUNT = 2`), each home with its own count of 1 or 2 frontiers drawn uniform per home (`TWIN_COLONY_FRONTIER_RANGE = (1, 2)`), adjacent to that home; Archipelago is 1 home + 3 frontiers (`ARCHIPELAGO_FRONTIER_COUNT = 3`), arranged so at least one frontier is reachable only through another frontier — not directly adjacent to the home, and not every frontier mutually adjacent. Remaining regions are empty, shuffled. Each faction's highest-numbered frontier (Twin Colony: the second home's highest-numbered frontier) gets a corridor of `WORLD_MIN_FACTION_SEPARATION = 1` empties; corridor ends are chained in faction order. Every unassigned empty links to a random already-connected region, re-rolling up to `WORLD_EMPTY_ATTACH_REROLL_CAP = 20` times to avoid homes. Then `max(1, floor(0.12 · n_regions))` extra edges (`WORLD_EXTRA_EDGE_RATIO = 0.12`) between random distinct non-adjacent regions, never between two home regions, at most `WORLD_EXTRA_EDGE_ATTEMPT_MULTIPLIER = 10` times that many attempts. Edge type is `both` between two regions of the same faction, else `border`. The world's RNG is reseeded from one final draw.

`docs/bible_history/bible_2_00_world.md`'s three named starting templates are implemented as above (E-03 S-021, Q-021-01/03/04/05); the per-faction template roll and feasibility gate are new since the Stage 1 audit (A-374, A-375) found them missing.
