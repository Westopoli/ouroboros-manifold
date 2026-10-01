# alg_constants.py --emit: the 20 UNPARSED names, and the emitter-only names

Docs only, for the Architect's per-name decision under ruling A31. Nothing was changed. The run was `scripts/specfactory/alg_constants.py --emit <scratch file>` against the 2026-10-01 bible (algorithms.md at origin/main 63ab025e); `csrc/om_constants.h` was not touched. The run reported 422 emitted constants, no CONFLICTS, and 20 UNPARSED names.

## How the parser decides

UNPARSED means: the name appears as an `UPPER_SNAKE` identifier in an ALG block, and no emitted constant is named it or starts with `<name>_`. The emitter only extracts a value from one of these shapes (`alg_constants.py`):

- Scalar `IDENT = NUM` (`SCALAR_RE`), skipped when the number is followed by an operator and another number (`looks_ambiguous_after`, e.g. `= 8 / 100`).
- Range `IDENT = (a, b)`, bracket pairs `IDENT = [(a, b), ...]`, keyed paren list, keyed colon list `IDENT[key]: k1 v1, k2 v2`, brace matrix, markdown pipe table with all-numeric columns.
- Formula backtick span followed directly by `, label \`v\`` clauses (`FORMULA_THEN_LABELS_RE`), the label matched to an identifier by whole underscore components. A `v1 / v2 / v3` value is matched by position and only when the count equals the number of identifiers in the formula.
- Formula span then `, \`= NUM\``.

Two reason codes below. NOVAL: the paragraph gives the name but no number next to it (the data lives in a table, a prose list, an epic, or the name is a flag or a template id). MISSED: a number is in the paragraph but no pattern ties it to the name.

## The 20 names

Header column: the hand constant in `csrc/om_constants.h`. C column: where `csrc/*.c` already carries the value.

| # | Name | ALG | Reason | Hand constant in om_constants.h | In csrc/*.c |
|---|---|---|---|---|---|
| 1 | ABILITY_MAP | 63 | NOVAL | 22 hand `OM_ABILITY_<TYPE>_*` (lines 535-556); values match the prose. `INTERCEPT_DETECTION_RADIUS = 350` and `WARDEN_AURA_REPAIR_RATE = 0.075` are emitted | none needed |
| 2 | ARCHETYPE_STARTING_TECH | 27 | NOVAL | none (`OM_STARTING_TECH_RATIO 0.25` is emitted) | none found; used by no code (mid-game faction creation) |
| 3 | ARCHETYPE_STRUCTURE_SPLIT | 75 | NOVAL | none | none found |
| 4 | BETRAYAL_OPPORTUNITY_CAP | 40 | MISSED | `OM_BETRAYAL_OPPORTUNITY_CAP 3.0` (line 302), hand | none |
| 5 | CONQUEST_UNREST | 22 | NOVAL (a template id, not a constant) | `OM_EVENT_TIER_CONQUEST_UNREST 4` (line 356) | `events.c:291` bare literals `3, 6, 0.60` in `evt_spawn`; `resolve.c:516` uses `OM_EVT_CONQUEST_UNREST` |
| 6 | CONSEQUENCE_TABLES | 59 | NOVAL | none | `mission.c:828` constants-table fence (cites ALG-59 / config.py) |
| 7 | ENABLE_ADJACENCY_BONUS | 06 | NOVAL (boolean flag) | none | none |
| 8 | ENABLE_OSCILLATION | 01 | NOVAL (boolean flag) | none | none |
| 9 | ENABLE_RECRUITMENT | 03 | NOVAL (boolean flag) | none | none |
| 10 | FORMATION_MOVE_ENABLED | 66 | NOVAL (boolean flag) | none | none |
| 11 | OUTCOME_THRESHOLDS | 58 | NOVAL (names E-10 R-077-02) | 16 hand `OM_MISSION_BAND_THRESHOLDS_*` (e.g. `..._RECONQUEST_ASSAULT_T1 0.25`, line 462) | read in `mission.c:1343` |
| 12 | REFUSAL_TENSION_PENALTY_PCT | 59 | MISSED (`= 8 / 100` trips the operator guard) | none under this name; `OM_MISSION_REFUSAL_TENSION_DEFICIT_PCT 8.0` (line 476) is the same value, other name | used in `mission.c:2067` through the other name |
| 13 | REGION_TRANSFER_OUTCOMES | 59 | NOVAL (bands listed as words) | none | `mission.c:987` static `om_mission_transfer_*` arrays |
| 14 | RELEVANCE_ARCHETYPE_WEIGHT | 55 | MISSED (0.3 in `weights 0.4 / 0.3 / 0.3`) | none under this name | `mission.c:117` local `OM_MISSION_RELEVANCE_ARCHETYPE_WEIGHT 0.3` |
| 15 | RELEVANCE_LINEAGE_WEIGHT | 55 | MISSED (0.4, same clause) | none | `mission.c:115` local `OM_MISSION_RELEVANCE_LINEAGE_WEIGHT 0.4` |
| 16 | RELEVANCE_PROXIMITY_WEIGHT | 55 | MISSED (0.3, same clause) | none | `mission.c:116` local `OM_MISSION_RELEVANCE_PROXIMITY_WEIGHT 0.3` |
| 17 | SIGNIFICANCE_MISSION_REGION_BONUS | 50 | MISSED (0.5 is inside the context formula) | `OM_SIGNIFICANCE_MISSION_REGION_BONUS 0.5` (line 387), hand | none |
| 18 | STARTING_STANCE_OVERRIDES | 38 | NOVAL (a prose list of hostile pairs) | none | none found by name; `diplomacy.c:704` handles stance edges |
| 19 | STRUCTURE_COUNT_RANGE | 75 | NOVAL (`[canvas]` index, no values anywhere in the bible) | none | `tactical_support.c:335-336` static `OM_SUP_STRUCT_COUNT_MIN {2,3,4}` / `MAX {4,6,8}` |
| 20 | UNIT_STATS | (line 256, the section intro under ALG-59's block; no ALG id of its own) | NOVAL (points at E-11 S-082) | none | `unit.c` / `diplomacy.c` / `enemy_macro.c` carry their own lookups |

### Verbatim text per name

Each quote is the exact line from `docs/bible/algorithms.md` (the whole paragraph is one line). Where one paragraph holds several names it is quoted once and the names are listed.

**ALG-63, line 264 (#1 ABILITY_MAP):**

> **ALG-63 Abilities.** One per type (`ABILITY_MAP`). Surge: duration `60` ticks, speed × `2.5`, damage × `2.0`, cooldown `1500`. Intercept: passive; when cooldown is 0 and an enemy Strike unit is within `INTERCEPT_DETECTION_RADIUS = 350` on the same layer, activate for the first engagement with speed × `1.8`, damage × `1.5`, cooldown `600`. Brace: windup `40` ticks immobile without bonus, then active with reduction `0.50` and damage × `1.3`; toggling off repeats the windup; cooldown `700` from activation. Rally: instant `112` HP to every friendly within `400`, capped at max HP; cooldown `1500`. Barrage: `30`-tick telegraph, then ALG-61 at the target with base × `3.0` within radius `100`; cooldown `1800`. Fortify: `400` ticks, reduction `0.20` within `350`, Bastion speed × `0.4`; cooldown `1400`. Warden aura (passive): friendlies within `300` regain `WARDEN_AURA_REPAIR_RATE = 0.075` HP per tick. Cooldowns tick down every tick; activation on cooldown is rejected.

Rejected: `ABILITY_MAP` is a bare name in parentheses. The per-ability numbers are unlabelled bare backtick spans, so no pattern fits. Resolved today by the 22 hand `OM_ABILITY_*` names.

**ALG-27, line 132 (#2 ARCHETYPE_STARTING_TECH):**

> **ALG-27 Growth.** Over owned inhabited regions: `growth = BASE_TECH_RATE · (avg_e/100) · max(TECH_POPULATION_FLOOR, avg_p/100)`, rate `0.35`, floor `0.3`; `tech = min(100, tech + growth)`. Starting tech = `avg starting population · STARTING_TECH_RATIO = 0.25`; `ARCHETYPE_STARTING_TECH` ranges apply only to factions created mid-game.

Rejected: name appears with no value; the ranges are not in the bible text at all (they live in the legacy config). Note the paragraph's own "rate `0.35`, floor `0.3`" does parse through the formula-then-labels pattern.

**ALG-75, line 303 (#3 ARCHETYPE_STRUCTURE_SPLIT, #19 STRUCTURE_COUNT_RANGE):**

> **ALG-75 Capture and production.** Each structure: capture radius `REINFORCEMENT_CAPTURE_RADIUS = 300`, HP `REINFORCEMENT_STRUCTURE_HP = 3000`. Per tick: factions present = factions of living units within the radius; if no non-owner faction, progress = 0; if exactly one non-owner faction and the owner absent, progress += `dt / REINFORCEMENT_CAPTURE_DURATION_SEC = 10`; at ≥ 1.0 ownership flips and progress resets. Owned structures advance a production timer; interval = `BASE_PRODUCTION_TIME_SEC = 30 · power(type) / POWER_NORMALIZATION = 100`; on expiry a unit spawns at a random point within half the capture radius (currently from an unseeded RNG; Q-126-02). Count = clamp(floor(region military · `MILITARY_TO_STRUCTURES_SCALE = 0.06`), `STRUCTURE_COUNT_RANGE[canvas]`); split by `ARCHETYPE_STRUCTURE_SPLIT`. Enemy production target: if any player category share ≥ `COMPOSITION_SKEW_THRESHOLD = 0.70`, shift `COMPOSITION_SHIFT_MAGNITUDE = 0.15` of the target toward the counter category (Strike→Line, Line→Siege, Siege→Strike) proportionally from the others, renormalize; produce the category most below target.

Rejected: both names appear with no value; the bible gives neither the per-canvas range nor the split. The code's `{2,3,4}` / `{4,6,8}` have no bible source line, so that is a gap in the bible, not only the emitter.

**ALG-40, line 166 (#4 BETRAYAL_OPPORTUNITY_CAP):**

> **ALG-40 Betrayal.** For each cooperative pair, for (A as betrayer, B as victim) then (B, A): `opportunity = min(BETRAYAL_OPPORTUNITY_CAP, max(1, border_mil_A / border_mil_B))` with border military the mean military of the betrayer's regions bordering the victim (cap `3.0` when the victim's is 0); `pressure = max(1, avg_tension_A / 50)`; `p = clamp(BASE_BETRAYAL_RATE · weight_A · opportunity · pressure, 0, 1)`, base `0.005`, weights `ARCHETYPE_BETRAYAL_WEIGHT`: conqueror 2.5, fortifier 0.3, warlord 2.0, opportunist 2.0, schism 1.5, player_civilization 0.5, breakaway 1.0. One draw; betray if `draw < p`: stance hostile, shared edges `border`, and an attack intent on the victim's lowest-military region bordering the betrayer with `commit = betrayer's entire budget`, no attack mode (full efficiency), resolved immediately by ALG-20 through ALG-22. At most one betrayal per pair per tick.

Rejected: the label "cap `3.0`" sits in a prose parenthetical, not in a `, label \`v\`` clause that directly follows the formula span, so the formula-then-labels pattern never fires. The `0.005` ("base") does parse; this one does not. The one-line "when the victim's is 0" also means the cap value `3.0` is used for two things in the text.

**ALG-22, line 104 (#5 CONQUEST_UNREST):**

> **ALG-22 Conquest.** Not repelled and `m + Δm < CONQUEST_THRESHOLD = 5.0`: the region changes owner; garrison `= commit · CONQUEST_GARRISON_FRACTION = 0.65` is added to military after damage; extra `Δe −= CONQUEST_ECONOMY_DISRUPTION = 5.0`, `Δt += CONQUEST_TENSION_SPIKE = 8.0`, `Δp −= CONQUEST_POPULATION_LOSS = 2.0`; the economy floor is bypassed. One RNG draw: with probability 0.60 a `CONQUEST_UNREST` chain is queued after a delay of `round(triangular(4, 8, mode 6))` ticks (second draw).

Rejected: it is an event template id, not a constant. The probability `0.60` and the delay `4, 8, mode 6` are bare prose with no identifier, so the real tuning values (`events.c:291` carries them as bare literals) are invisible to the emitter and to the bible's named-constant scheme.

**ALG-59, line 252 (#6 CONSEQUENCE_TABLES, #12 REFUSAL_TENSION_PENALTY_PCT, #13 REGION_TRANSFER_OUTCOMES):**

> **ALG-59 Consequences.** For each row of `CONSEQUENCE_TABLES[archetype][band]`: `delta = (100 − v) · pct/100` for form `deficit`, `v · pct/100` for `current`; targets `mission`, `home`, `exposed` resolve to the mission region (see Q-078-01), `adjacent_player` to player-owned neighbors; clamp [0, 100]. Ownership transfers to the player for bands in `REGION_TRANSFER_OUTCOMES`: reconquest {total, strong, partial success}, assault and suppression {total, strong success}. Refusal: `tension += (100 − tension) · REFUSAL_TENSION_PENALTY_PCT = 8 / 100`. Commander death emits `evt_commander_killed_in_action` flagged as a mission consequence.

Rejected: #6 and #13 have no values here (the table is in `simulation/config.py`, cited in `mission.c:828`; the transfer set is words). #12: `SCALAR_RE` matches `REFUSAL_TENSION_PENALTY_PCT = 8`, but `looks_ambiguous_after` sees ` / 100` and discards it as a compound expression. Trivially fixable by writing `= 8.0` and a separate "/ 100".

**ALG-06, line 47 (#7 ENABLE_ADJACENCY_BONUS):**

> **ALG-06 Adjacency bonus** (`ENABLE_ADJACENCY_BONUS`, computed in `tick.py`). For every inhabited neighbor across a trade edge that is same-faction, or whose faction this region's faction holds a cooperative stance toward: `adjacency_bonus += NEIGHBOR_ECONOMY_BONUS · (neighbor.e / 100)`, `NEIGHBOR_ECONOMY_BONUS = 0.05`. Reads the neighbor's raw economy.

**ALG-01, line 35 (#8 ENABLE_OSCILLATION):**

> **ALG-01 Oscillator kernel.** `osc(A, P, φ, tick) = A · sin(2π · tick / P + φ)`. Enabled by `ENABLE_OSCILLATION` for tick > 0. Two oscillators per region: economy `A = ECON_OSCILLATION_AMPLITUDE = 6.0`, `P = ECON_OSCILLATION_PERIOD = 15`; tension `A = TENSION_OSCILLATION_AMPLITUDE = 2.0`, `P = TENSION_OSCILLATION_PERIOD = 18`. Phase offsets φ are drawn per region at world generation, uniform in [0, 2π). The previous-tick value is `osc(..., tick − 1)` for tick > 1 and 0 for tick = 1.

**ALG-03, line 41 (#9 ENABLE_RECRUITMENT):**

> **ALG-03 Recruitment** (`ENABLE_RECRUITMENT`). `headroom = max(0, 1 − m / RECRUITMENT_CEILING)`, `RECRUITMENT_CEILING = 90.0` (reads raw m, not primed). `eco_term = RECRUITMENT_RATE · (e'/100) · (p'/100) · (1 − t/100)^TENSION_RECRUITMENT_SCALE` if `e' > RECRUITMENT_THRESHOLD` else 0; `RECRUITMENT_RATE = 12`, `RECRUITMENT_THRESHOLD = 20.0`, `TENSION_RECRUITMENT_SCALE = 0.3` (reads raw t). `Δm_recruit = (RECRUITMENT_BASELINE · p'/100 + eco_term) · headroom`, `RECRUITMENT_BASELINE = 0.1`.

**ALG-66, line 274 (#10 FORMATION_MOVE_ENABLED):**

> **ALG-66 Group move.** For a selection of 2+ living units with `FORMATION_MOVE_ENABLED`: centroid c; scattered if any unit is farther than `MAGIC_BOX_SPREAD_RADIUS = 450` from c; each unit's slot = click + (unit − c), or the click point if scattered or the slot cell is unwalkable; the group is registered and terminated when the centroid arrives or every unit is within `ARRIVAL_TOLERANCE_MULT = 1.5 · UNIT_COLLISION_RADIUS = 15` of its slot. Slowest-unit pace (A-557) is not implemented (Q-095-01).

Rejected (#7 to #10): the four are boolean feature switches from the legacy config. The paragraph states no value for them (their value is "on"), so there is nothing numeric to extract. Side note: line 274 also yields one compound, `ARRIVAL_TOLERANCE_MULT = 1.5 · UNIT_COLLISION_RADIUS = 15`, which the emitter reads as two scalars; that is correct.

**ALG-58, line 250 (#11 OUTCOME_THRESHOLDS):**

> **ALG-58 Outcome.** `objective_score = Σ weight · (0 if failed else completion)`; `retention = min(1, Σ surviving unit power (HP-scaled) / initial power)`; `final = OUTCOME_WEIGHT_OBJECTIVE = 0.75 · objective_score + OUTCOME_WEIGHT_RETENTION = 0.25 · retention`; band by `OUTCOME_THRESHOLDS[archetype]` (E-10 R-077-02), strict less-than. Terminal: every primary complete or failed, or `tick ≥ limit`, or no living player unit. Commander survived = commander unit alive.

Rejected: no values; they sit in epic E-10 R-077-02. Hand `OM_MISSION_BAND_THRESHOLDS_*` already carry them.

**ALG-55, line 244 (#14, #15, #16 RELEVANCE_*_WEIGHT):**

> **ALG-55 Scoring and selection.** `urgency = clamp(URGENCY_FIELD_WEIGHT · deficit + URGENCY_CONFLICT_WEIGHT · conflict + URGENCY_CHAIN_WEIGHT · chain)`, weights `0.4 / 0.4 / 0.2`; `deficit = ((100 − m) + (100 − e) + (100 − stability))/300`; `conflict = clamp(min(1, max_hostile_neighbor_m/70) + 0.5 · min(1, 0.5 · n_attacks + Σ budget/600) + 0.3 · min(1, 0.5 · adjacent_regions_lost))`; `chain = min(1, 0.3 · n_revolt_events_in_region)`. `relevance = clamp(RELEVANCE_LINEAGE_WEIGHT · lineage + RELEVANCE_PROXIMITY_WEIGHT · (1 − hops/RELEVANCE_MAX_HOPS) + RELEVANCE_ARCHETYPE_WEIGHT · min(1, archetype_count/RELEVANCE_ARCHETYPE_FIT_THRESHOLD))`, weights `0.4 / 0.3 / 0.3`, max hops `5`, fit threshold `3`; lineage = 1.0 if a member lives in the region, 0.5 if the region is in the lineage history, else 0; hops from the lineage's first history region by BFS over all edges, capped at 5. `preference = GENERATOR_RARE_PREFERENCE = 0.1` if rare, else the player's weight, default `GENERATOR_DEFAULT_PREFERENCE = 0.5`. `score = 0.5 · urgency + 0.3 · relevance + 0.2 · preference` (`GENERATOR_*_WEIGHT`). Sort descending; pool = top `GENERATOR_TOP_N_CANDIDATES = 5`; one draw `r = U(0, Σ score)`, first candidate whose cumulative score ≥ r.

Rejected: the `/`-list rule matches positionally and only if the value count equals the identifier count in the formula span. The relevance formula holds five identifiers, the list holds three. The urgency weights `0.4 / 0.4 / 0.2` do parse, because that formula span holds exactly three identifiers. `RELEVANCE_MAX_HOPS 5` and `RELEVANCE_ARCHETYPE_FIT_THRESHOLD 3` do emit through the labelled clauses. The `GENERATOR_URGENCY/RELEVANCE/PREFERENCE_WEIGHT` names (`score = 0.5 ...`) are not emitted either; `mission.c:110-112` has `OM_MISSION_SCORE_*_WEIGHT` locals for them, and they are not on the UNPARSED list because the text writes them as `GENERATOR_*_WEIGHT`.

**ALG-50, line 199 (#17 SIGNIFICANCE_MISSION_REGION_BONUS):**

> **ALG-50 Significance.** `base = tier + min(|Δ|_sum / SIGNIFICANCE_DELTA_SCALE, SIGNIFICANCE_DELTA_CAP)`, scale `50.0`, cap `3.0`, tier from the template (default 2). `context = 1.0 + 0.5·[region == last mission region] + 0.3·[character attached] + 0.1·min(chain_length, CHAIN_LENGTH_CAP = 5)·[chain_length > 1] + 0.8·[a lineage member lives in the region]` (`SIGNIFICANCE_MISSION_REGION_BONUS`, `_CHARACTER_BONUS`, `_CHAIN_LENGTH_BONUS`, `_LINEAGE_REGION_BONUS`). `score = base · context`.

Rejected: the four bonus names are in a trailing parenthetical (the last three as `_SUFFIX` fragments), the values are the coefficients inside the `context` formula, and no pattern ties them. Only the first name is long enough to be flagged. The other three (`OM_SIGNIFICANCE_CHARACTER_BONUS 0.3`, `..._CHAIN_LENGTH_BONUS 0.1`, `..._LINEAGE_REGION_BONUS 0.8`) are also hand-only and unflagged. `CHAIN_LENGTH_CAP = 5` does parse.

**ALG-38, line 162 (#18 STARTING_STANCE_OVERRIDES):**

> **ALG-38 Starting stance and timers.** Starting stance per archetype pair from `STARTING_STANCE_OVERRIDES` (conqueror hostile to every archetype; fortifier hostile to player and opportunist; opportunist hostile to player; schism hostile to player, fortifier, opportunist, warlord), else neutral. Each tick, for each neutral pair that shares at least one border edge: counter = 0 if an attack between them appears in this tick's actions, else counter + 1.

Rejected: a category table in words (stances are not numbers); no numeric value to extract.

**Line 256 (#20 UNIT_STATS), the intro of the "Tactical: units, damage, abilities" section; the parser files it under ALG-59's block:**

> Added in Stage 2 from source (2026-09-10). Tactical ticks run at `TACTICAL_TICK_RATE = 20` per second. Unit stats are the table in `epics/E-11-units-and-combat.md` S-082 (`UNIT_STATS`).

Rejected: points at the E-11 epic table; the emitter reads algorithms.md only, and the epic is out of its scope.

### Candidate resolutions per name

Options: P = add a parseable form in the bible (the same fact, restated as `IDENT = value`); H = hand constant in the extra header (A31 piece 1); D = drop (name is not a constant; remove the backticks or reword so it stops matching, or leave it as an accepted known name); B = bible gap (a value the bible does not pin at all, needs a Westley/Architect source first).

| # | Name | Candidates |
|---|---|---|
| 1 | ABILITY_MAP | H (keep the 22 `OM_ABILITY_*`), or P (restate each as `ABILITY_SURGE_DURATION_TICKS = 60` etc., a large rewrite of ALG-63). D for the name itself |
| 2 | ARCHETYPE_STARTING_TECH | B (ranges not in the bible), then P; or D if mid-game factions stay unbuilt |
| 3 | ARCHETYPE_STRUCTURE_SPLIT | B (no values anywhere), then P as a keyed list |
| 4 | BETRAYAL_OPPORTUNITY_CAP | P: `BETRAYAL_OPPORTUNITY_CAP = 3.0` (smallest change, header already has it, so the move to emitted is value-neutral); or H |
| 5 | CONQUEST_UNREST | D for the name (template id); P for the unnamed `0.60` and `4, 8, mode 6` by naming them, e.g. `CONQUEST_UNREST_PROBABILITY = 0.60`; H as fallback. This also removes the `events.c:291` bare literals from the lint |
| 6 | CONSEQUENCE_TABLES | H or a fenced constants-table in the C (already there); D for the name. Not a scalar |
| 7-10 | ENABLE_* x3, FORMATION_MOVE_ENABLED | D (switches, always on; reword to drop the backticked identifier), or H as `#define OM_ENABLE_X 1` if code ever needs a switch |
| 11 | OUTCOME_THRESHOLDS | P: restate in ALG-58 as a keyed table (`OUTCOME_THRESHOLDS[archetype]` pipe table) so the 16 hand constants become emitted; or H (keep); D for the name |
| 12 | REFUSAL_TENSION_PENALTY_PCT | P: write `= 8.0` (the ` / 100` is in the formula already); this also forces a clash decision with hand `OM_MISSION_REFUSAL_TENSION_DEFICIT_PCT 8.0` (same value, other name): rename one or alias |
| 13 | REGION_TRANSFER_OUTCOMES | D (a set of bands, not a number), or H as a bitmask next to the C arrays |
| 14-16 | RELEVANCE_*_WEIGHT | P: one `RELEVANCE_LINEAGE_WEIGHT = 0.4` style clause per name; this also settles the `OM_MISSION_RELEVANCE_*` locals in mission.c (same value, other prefix) |
| 17 | SIGNIFICANCE_MISSION_REGION_BONUS | P: `SIGNIFICANCE_MISSION_REGION_BONUS = 0.5` in the context formula (and the three siblings, which the list does not flag); or H (header already has all four) |
| 18 | STARTING_STANCE_OVERRIDES | D (categorical, not numeric); the C handles it in code |
| 19 | STRUCTURE_COUNT_RANGE | B first (the `{2,3,4}`/`{4,6,8}` in `tactical_support.c` are unsourced in the bible), then P as `STRUCTURE_COUNT_RANGE[canvas]: small (2, 4), medium (3, 6), large (4, 8)` which the keyed-colon pattern parses |
| 20 | UNIT_STATS | D for the emitter (the epic table is out of scope); the real question is whether units get a header at all (they use `unit.c` lookups) |

## Emitter-only names (the emitted file has them, the committed header does not)

Using a proper sorted comparison there are 12 names, not 10: ten `OM_TACTICAL_TICK_RATE_*` and two `OM_OM_MACRO_*`. The earlier diagnosis counted the same 12. Both source lines are ALG-56 and ALG-76. `OM_CHRONICLE_MAX_ENTRIES` and `OM_CHRONICLE_MIN_ENTRIES` are in both files with equal values (10, 5) and are not clashes.

| Emitted name | Emitted value | Source | Same name in hand header | Same value under another hand name |
|---|---|---|---|---|
| OM_TACTICAL_TICK_RATE_ASSAULT | 52.5 | ALG-56 line 246 | no | none; the 52.5 appears only in `mission.c:705` as a literal minutes table |
| OM_TACTICAL_TICK_RATE_CONTAINMENT | 52.5 | ALG-56 | no | none (as above) |
| OM_TACTICAL_TICK_RATE_COUNTERINSURGENCY | 37.5 | ALG-56 | no | none (as above) |
| OM_TACTICAL_TICK_RATE_DEFENSIVE | 37.5 | ALG-56 | no | none (as above) |
| OM_TACTICAL_TICK_RATE_EVACUATION | 30 | ALG-56 | no | numeric coincidences only: `OM_CHRON_CAPACITY_LOW`, `OM_CHRON_STABILITY_LOW` 30.0, `OM_ABILITY_BARRAGE_TELEGRAPH_TICKS` 30, `OM_BASE_PRODUCTION_TIME_SEC` 30; none mean minutes |
| OM_TACTICAL_TICK_RATE_FRONT | 60 | ALG-56 ("multi-front 60") | no | coincidences only (`OM_REINFORCE_MIL_CAP_FRONTIER` 60, `OM_ABILITY_SURGE_DURATION_TICKS` 60, others) |
| OM_TACTICAL_TICK_RATE_INTERCEPTION | 37.5 | ALG-56 | no | none |
| OM_TACTICAL_TICK_RATE_RECONQUEST | 45 | ALG-56 | no | coincidence only (`OM_OPPORTUNIST_HOME_RANGE_*_LO` 45) |
| OM_TACTICAL_TICK_RATE_SIEGE | 60 | ALG-56 | no | coincidences only |
| OM_TACTICAL_TICK_RATE_SUPPRESSION | 30 | ALG-56 | no | coincidences only |
| OM_OM_MACRO_ROUT_HP_THRESHOLD | 0.35 | ALG-76 line 299 | no | yes: hand `OM_MACRO_ROUT_HP_THRESHOLD 0.35` (line 630), the intended name |
| OM_OM_MACRO_EXTERNAL_REINFORCEMENT_PROB | 0.21 | ALG-76 | no | yes: hand `OM_MACRO_EXTERNAL_REINFORCEMENT_PROB 0.21` (line 629), the intended name |

The `OM_TACTICAL_TICK_RATE_*` names are a real parse error, not a feature. ALG-56 reads "B the archetype's base time in minutes × 60 × `TACTICAL_TICK_RATE`: siege 60, multi-front 60, ...". The keyed-colon pattern takes `TACTICAL_TICK_RATE` as the table head, so the ten archetype minutes become keys under a name that is really the tick rate. The values are minutes of battle time, not a rate. The emitted names are wrong; the hand header correctly has none of them, and `mission.c:705` carries the minutes in a constants-table fence (its comment says the emitter never lands them in the header).

Name or value clashes (reported, not resolved):

- `OM_WORLD_REGION_COUNT_RANGE_LO` / `_HI`: hand header 60 / 110 versus emitted 250 / 400. The bible now says (250, 400) (2026-10-01); the header is stale. This is the intended change and the only shared-name value difference. `csrc/om_internal.h:12` has a comment that still says `_HI = 110`.
- `OM_TACTICAL_TICK_RATE`: hand 20, emitted 20 (equal). It is the same name as the prefix of the ten bogus names, so emitted `OM_TACTICAL_TICK_RATE_SIEGE` reads as a sub-rate of it.
- `OM_OM_MACRO_*` versus hand `OM_MACRO_*`: same values, different names (a double prefix from the ALG-76 text writing `OM_` in the identifier). Listing both would define each value twice under two names; the fix is to drop the leading `OM_` in the bible or to teach the emitter not to double it.

No shared name carries a differing value other than the region count pair.

## Notes for the decision

- Five of the twenty have a hand constant of the same value (some under another name): BETRAYAL_OPPORTUNITY_CAP, SIGNIFICANCE_MISSION_REGION_BONUS, OUTCOME_THRESHOLDS (16 names), ABILITY_MAP (22 names), CONQUEST_UNREST (tier only); REFUSAL_TENSION_PENALTY_PCT has one under another name. Moving them to the extra header loses nothing.
- Six are pure parser misses with the value right there (BETRAYAL_OPPORTUNITY_CAP, REFUSAL_TENSION_PENALTY_PCT, RELEVANCE x3, SIGNIFICANCE_MISSION_REGION_BONUS): a one-clause bible edit each makes them emit.
- Three have no bible value at all (ARCHETYPE_STARTING_TECH, ARCHETYPE_STRUCTURE_SPLIT, STRUCTURE_COUNT_RANGE). The C already has `{2,3,4}` / `{4,6,8}` for the last one; the other two have no code. Those need a source before any form.
- The `--check` mode of piece 2 will see the ten wrong `OM_TACTICAL_TICK_RATE_*` names as drift on day one, so the ALG-56 parse must be fixed (or its text reworded) before `--check` lands.
