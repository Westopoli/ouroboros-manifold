# Proposal one: covering the lab's two blind spots (layers and vision)

One of three Fable 5.1 research agents given an identical read-only brief on 2026-10-13 by the Architect chat, at Westley's request. The brief, the rulings it rests on and the seven known gaps are in `synthesis.md`. This file is the agent's report verbatim.

## Report: covering the lab's two blind spots (layers and vision) and running the knob sweep

Everything below was read from `origin/main` at `68547f9e`. Six engine probes were run on a scratch build of that tree (`/tmp/claude-1000/-home-westopoli-Projects-ouroboros-manifold/7e9d8393-6f9a-44e1-a26b-66264f334079/scratchpad/agent-one/probe2.py` and the inline script before it; nothing in the repository was touched). Probe findings are mine, dated 2026-10-13, and are labelled as such.

### What the engine actually checks before a shot (the ground truth the count must mirror)

- Reach: `csrc/unit.c:572-577` (`om_tac_in_reach`): same layer always; another layer only within the type's `om_unit_profile_reach` up or down.
- Range at an offset: `csrc/unit.c:1716-1719` (`om_tac_in_range`): same layer at `attack_range`; another layer at `attack_range × OM_TP_RANGE_{UP,DOWN}_n` (`om_tac_offset_mult`, `:585-589`).
- Sight: `csrc/unit.c:1165-1180` (`om_tac_faction_sees`, `om_tac_may_act_on`): with `OM_TP_TARGET_BY_SIGHT` at 1 the target must be in the side's visible set, which is the union of every living friendly's `om_unit_can_see` plus live ping reveals (`csrc/fog.c:486-501`, `:882-893`). Acquisition applies it on the same layer (`:1862`, `:1998`) and across layers (`om_tac_pick_across`, `:1731-1768`, line 1750), and a held target the side stops seeing is dropped (`:2140`).
- Line of fire: `om_combat_can_shoot` (`csrc/tactical_move.c:2582-2619`) checks cover discs, blocked cells and ground only. It checks no range, no reach and no sight.
- Damage at an offset: `csrc/unit.c:1020`; area damage at an offset and by reach: `:2782-2786`.
- Transition: the row's layer flips at half the transfer (`csrc/tactical_move.c:2414`), and `om_unit_get_layer` returns that row layer (`csrc/unit.c:3057-3060`). Probe 4 confirmed it: a Raider ordered up reads layer 0 at ticks 1 to 9 and layer 1 from tick 10 of 20.
- Guard: a guard answers return fire only inside reach and range and never walks (`csrc/unit.c:2102-2104`, `:2143`); the radius guard of R-096-08 (`docs/bible/epics/E-13-movement-and-command.md:55`, 200 wu draft) is not built, as the brief says.
- Flinch: an idle unit hit by something it cannot reach moves 200 wu away (`csrc/unit.c:2085-2093`, `:1974-1981`; R-087-01). Probe 8: an idle defender one layer below a shooter took one hit and moved from x 1250 to 1450; under attack-move or guard it held and kept taking hits. So contact-by-elimination needs every unit under an order, never idle.

The lab's count today (`scripts/skilllab/firing.py:13-24`) checks same layer (`:18-19`), distance at the unit's own `attack_range` (`:21`, ranges filled at `scripts/skilllab/fight.py:54-64`) and `can_shoot`. It never asks sight. Probe 1 made the gap concrete on the same layer with roster units: a Bombard (range 1200, sensor 300) 800 wu from a Vanguard reads `can_shoot = True`, so today's count calls it able, yet the engine gives it no target and the Vanguard loses no hit points in 100 ticks; add a friendly Raider spotter 500 wu from the Vanguard and the Bombard fires (500 to 434). That is "seen by the side, not by the unit" (E-12 R-093-02, `docs/bible/epics/E-12-fog-and-sensors.md:91`).

---

## A. ABLE TO FIRE

### Candidate A1. Lab-side composition from public queries (recommended now)

Definition, per unit u of side S, per sample: u is able when it is alive and there exists a living enemy e such that
1. offset = `unit_layer(e) − unit_layer(u)` is 0, or within u's type reach (`engine.profile_reach`, read once per fight as `fight.py:182-191` already does for the weighted series);
2. `dist(u, e) ≤ attack_range(u) × m(offset)` with m(0) = 1 and m(±n) = `OM_TP_RANGE_UP_n` or `OM_TP_RANGE_DOWN_n`, read once per fight with `engine.get_param`;
3. e is in S's visible set: `e in engine.visible_enemies(w, S, enemies)` (`scripts/skilllab/engine.py:208-209`, which is `om_player_can_see`, and includes ping reveals, probe 5);
4. `engine.can_shoot(w, u, e)`;
5. once the arc lands: the bearing from u to e is inside the arc about `engine.unit_facing(w, u)` (`csrc/ouroboros_sim.h:1977`), mirrored from the engine rule by the named draft width.

A unit in transition is on `om_unit_get_layer`'s layer, which is the effective layer of R-004-02 (old layer until the cross-over, new layer after; `docs/bible/epics/E-01-layer-system.md:84`), so the count needs no transition special case; it reads the same getter it reads today.

Engine queries: `om_unit_alive`, `om_unit_get_pos`, `om_unit_get_layer`, `om_unit_profile_reach`, `om_tactical_get_param` (eight RANGE values), `om_player_can_see`, `om_combat_can_shoot`, later `om_unit_get_facing`. All are bound already except that the RANGE reads are new per-fight reads.

Pros: no contract change; every knob of the sweep enters the count through the engine's own numbers; the per-sample cost is the same shape as today (one `visible_enemies` call per side per sample, then pair tests). Probe 9 (16 v 16, side 0 one layer up, same units with reach 1 up 1 down both sides, both attack-moving to one point) shows it moves with every knob while today's count stays at 0 for the whole fight:

| Setting (my probe, one seed) | ticks | survivors 0 v 1 | today's count, unit-seconds | A1 count, side 0 / side 1 | engine-target count, side 0 / side 1 |
|---|---|---|---|---|---|
| vision 0.5, range up 1.0, damage up 1.0 | 6000 (cap) | 2 v 6 | 0 / 0 | 1008 / 1120 | 1003 / 1115 |
| vision 0.0 both ways | 6000 (cap) | 16 v 16 | 0 / 0 | 0 / 0 | 0 / 0 |
| vision 0.5, range up 0.5 | 1734 | 14 v 0 | 0 / 0 | 1272 / 254 | 1250 / 252 |
| vision 0.5, damage up 0.5 | 2960 | 11 v 0 | 0 / 0 | 1276 / 1018 | 1270 / 1014 |
| vision 0.25 | 6000 (cap) | 14 v 14 | 0 / 0 | 156 / 154 | 152 / 147 |

Cons: the count re-states engine rules in Python, so it can drift from the engine (the arc and the cone are exactly the kind of rule that will land in C after the count is written). Risks: a Python mirror of the arc that disagrees with the engine's by a degree or a sign; `visible_enemies` is per enemy per side, so a 48-enemy scan costs more per sample than today (measure it in the pre-flight; the sample interval is already a Setup field).

### Candidate A2. One engine query, `om_combat_can_engage(w, a, b)` returning a reason code (recommended as the end state, landed with the arc piece)

Definition: the count asks the engine, per pair, "may a fire at b now", with a reason code (0 ok; 1 out of reach; 2 out of range at this offset; 3 not seen by the side; 4 line blocked; 5 outside the arc). The lab records the first failing reason per unit (which also gives `unit_states` of `firing.py:27-46` its "blocked / unseen / out of reach" states for free).

Pros: a single source of truth, the arc and the cone enter the count on the day they enter the engine, no Python mirror to drift. Cons: a contract piece (header, `signatures.toml`, ABI bump; CLAUDE.md "Contracts are frozen and minimal"), so it cannot be the first change; the count then depends on the engine piece's schedule. Risk: the query is written from the acquisition path rather than the fire path and the two differ (today they already differ in one way: acquisition runs on the cohort tick, `csrc/unit.c:2164-2165`, while fire checks range and `can_shoot` every tick, `:2256-2258`). Evidence that it is cheap to get right: probe 9's engine-target count (units whose engine target is alive, in range at its offset and shootable) agrees with A1 within about 1 percent on every row.

### Candidate A3. Count units whose engine target passes the test (what the weighted series does today, `firing.py:62-74`)

Definition: able = `om_unit_get_target` is a living enemy within reach and range at its offset and shootable. Pros: cannot disagree with the engine about who is a target; already built for the weighted series. Cons: it is "has a target", not "can get shots off": it lags acquisition by up to the cohort stagger (every 4th tick, `csrc/unit.c:2165`), it reads 0 for a unit with an enemy in reach whose chosen target just died, and it ignores sight only because the engine already did; it also fails the spec's hand-built AC 24 case (`docs/northstar/plans/skilllab-harness-spec.md:49`), where idle units with no acquisition yet must read 2 and 1 at tick 0. Not recommended as the count; keep it as the control series that A1 is checked against (the "a detector that cannot fire is caught" line in every batch).

### The toy's definition, for the record

`toys/layerlab/SPEC.md:163-168` (5.11a): a unit can fire when alive, not winding, and acquisition (5.4, `:104-116`) gave it a target that is in range, seen by the side (`side_sees`, 5.2 `:97`), eligible under the halfway rule, inside the arc when the gate is on, and the unit not under an unarrived move; independent of cooldown; `firing_weight` summed the category multiplier of the unit against its target. So the toy already had sight, reach and the arc in the count; the harness spec's AC 10 (`skilllab-harness-spec.md:25`, "its own layer until the engine cascade lands") and the cascade brief's own bullet (`docs/northstar/plans/2026-10-02-skill-lab-cascade.md:95`, "After engine step G3 also: the enemy is seen by the unit's side") both promised what A1 restores. The toy's vision sweeps (X2 to X4, `docs/northstar/research/layer_dynamics/history_2026-09-30_to_10-01.md:251-253`, results `:444-455` and `:524`) found a cliff: B's upward sight 0.0 gives A every fight whatever B's numbers; 0.05 already lets 12 beat 10; "a layer alone gives nothing" under symmetric sight (`:449`). Those are the leads the real-engine sweep re-measures.

### Should both predictions change, and how to weight by type without the trap

Both change: the count-only series and the type-weighted series must use the same eligibility (A1), otherwise a disagreement between them would measure the eligibility gap, not unit type.

The trap, verbatim from the transcript the brief cites (`docs/legacy/claude_exchange/transcripts/2026-09-30_dd1ff47b_layer-lab-design-and-plan.jsonl` line 704, Westley's "yes write it up as a hypothesis" at line 712): "If the metric is 'units firing × their damage, against the enemy's health', it will always agree with the result." Today's weight is `base_damage / attack_interval` (`firing.py:55-59`), a unit value, not a type: it carries the Bombard's 17.5 damage into the prediction, which is the trap's first factor. Westley's words (history `:326`): "not just unit values but their type as well".

Recommended weighting (register Q-008-07 candidate (a), `docs/northstar/ambiguity_register.md:284`): weight(u) = M[category(u)][category(t)], the category multiplier of E-11 R-081-01 (`docs/bible/epics/E-11-units-and-combat.md:33`), read from the engine at run time with `om_tactical_category_multiplier` (`csrc/ouroboros_sim.h:2091`, so it follows `OM_TP_CATMULT_*` when swept), where t is u's target of record: the engine target when it passes A1's test, else the nearest enemy that passes it (the engine's own nearest rule, `csrc/unit.c:1827`). The weighted series then contains only the rock-paper-scissors table, no damage, interval, health or cross-layer damage multiplier, so "count-only wrong, type-weighted right" means type decided it, and "both wrong" means a number overrode position (the brief's approved reading; history `:347-353`). Alternative: weight by catmult of the nearest able enemy only, ignoring the engine target (simpler, but it can disagree with what the unit actually shoots under `OM_TP_TARGET_POLICY` 1). Rejected: anything that multiplies in damage or divides by health.

Cone area damage in the count: a cone unit counts as one able unit (count-only) and is weighted by the catmult of its target of record; the number of enemies inside its cone per sample is recorded as its own column (`cone_victims`), never folded into either prediction. Folding it in would import the area cap (4 × base, `csrc/unit.c:2775`), a stat.

---

## B. THE SWEEP

### Knobs and parameters (all in `csrc/ouroboros_sim.h:1009-1077`; defaults and refusal bounds in `docs/northstar/plans/push/pp_contract.md:92-160`, which says at `:90` the bounds "are not game values")

| Westley's knob | Engine parameters | Base value and its source |
|---|---|---|
| vision only | `OM_TP_VISION_UP_1..2`, `OM_TP_VISION_DOWN_1..2` (3 and 4 stay 0: R-005-05, `E-01:104`) | 0.50 and 0.20, E-01 R-005-02 to R-005-04 (`E-01:101-103`), provisional and "not his" (Q-005-07, register `:60`, Westley 2026-10-07: "#4: A, architect decision. Should be close to what it was for the python version") |
| vision and reach | the reach table through `om_roster_set_reach` (R-164-01, `E-01:241`: Line own layer, Raider one either way, Interceptor two up one down, Siege two down), plus `OM_TP_RANGE_UP_n` ("shorter firing up", history `:399`) | reach table as the bible gives it; range multiplier base 1.0 (cascade brief `:311`, "swept by the lab") |
| plus a damage penalty for firing up | `OM_TP_DAMAGE_UP_n` | base 1.0 (brief `:311`) |
| emitting (S-163) | `OM_TP_EMIT_SIGHT_MULT`, `OM_TP_EMIT_SEEN_MULT`, `om_command_set_emission` per group | starting pair sight 2.0, seen 3.0 (ruling 2026-10-13, README `:92`); seen always above sight (R-163-01, `E-01:227`) |
| firing arc | pending engine piece (Q-100-01, register `:516`); until then no parameter | named draft DRAFT-firing-arc-deg 120 (register candidate (a)) |
| cone area damage | pending engine piece (Q-082-06, register `:210`); today only `OM_TP_AREA_UP/DOWN_n` and the Bombard's disc | named drafts DRAFT-aoe-cone-range 300, DRAFT-aoe-cone-deg 45 (register candidate (a)) |
| ping (contact source in space) | `OM_TP_PING_RADIUS/REACH/REVEAL_TICKS/COOLDOWN_TICKS`, `om_command_ping` | 500 / 2000 / 100 ticks / 400 ticks (R-162-01, `E-01:211`; contract table rows 23 to 26) |

Not a knob of this sweep: `OM_TP_UNIT_COLLISION_RADIUS` (inert, gap 2, `docs/northstar/plans/archive/2026-10-06-unit-size-runtime-spec.md:15`), `OM_TP_VANTAGE_MULT` (vantage nodes are retired for ground and untouched by the plays).

### Values inside the bounded band (ruling: start at the bible's value, step by a named factor inside 0.25x to 4x, three to five points, coarse first)

| Parameter | Coarse points (named draft, factor 2) | Note |
|---|---|---|
| `VISION_UP_1` = `VISION_DOWN_1` | 0.125, 0.25, 0.5, 1.0 | 2.0 is clipped to 1.0 by `csrc/fog.c:733`, so the band's top is 1.0; offset 2 moves with it at the bible's 0.4 ratio (0.05, 0.1, 0.2, 0.4) |
| `RANGE_UP_1` (and `_2` at the same value) | 0.25, 0.5, 1.0, 2.0 | 2.0 is a control point that must flip the sign (the toy read the lever "decisive within 20 percent", README `:192`, so refinement will be needed between 0.5 and 1.0); `RANGE_DOWN_n` stays 1.0 |
| `DAMAGE_UP_1` (and `_2`) | 0.25, 0.5, 1.0, 2.0 | same shape; `DAMAGE_DOWN_n` stays 1.0 |
| emitting (sight, seen) | sight 1, 2, 4 crossed with seen 1.5, 3, 6, keeping seen > sight | run at a vision base where base × seen < 1: probe 7 shows that at the bible's 0.5 both multipliers saturate at the 1.0 cap (`fog.c:749`) and emitting reads the same as full sight both ways; at base 0.25 an emitting unit at 450 wu is seen (0.75 × 700) and does not see (0.5 × 700), which is the rule |
| arc width (after the engine piece) | 60, 120, 240, 360 | 360 is the no-arc control |
| cone range, cone angle (after the engine piece) | 150, 300, 600, 1200 and 22.5, 45, 90, 180 | cone off is the control |

Refinement only around a crossing the coarse grid showed: halve the step between the two coarse points where the gain changes sign, twice at most (so 0.5 to 1.0 refines to 0.75 then 0.625 or 0.875), as `scan.py:75-84` already refines headcount cells. A point outside the band needs a written reason in the batch spec (ruling, README `:93`).

### Scenes and plays, both sides on different layers where that is the point (space lab first, since ground eras have no ping, R-162-01)

Under the 2026-10-13 ruling the skill is "arrangement, orders and which roster types stand where", so every play below uses the same units with the same values on both sides, and the reach table is set on the built-in types for both sides (today `batches.py:32-34` sets Vanguard reach 0,0 and `plays_space.py:58` gives a Vanguard reach 0,1, which R-164-01 forbids):

1. `s3_layer_above` (new, the sweep's primary scene): 16 units one layer above the enemy's 16, same mix; the knob is what makes the layer worth something. Needs a mix whose reach crosses layers (Raider one either way, or Interceptor two up one down), else nobody fires under R-164-02. Probe 9 is this scene with a reach-1 Vanguard stand-in.
2. `s3_types_by_reach` (corrected): side 0 puts its Interceptors one layer up and its Vanguards on the enemy's layer; side 1 fields the identical 8 + 8 all on one layer. The asymmetry is only where each type stands.
3. `s3_ping_then_commit` (new; closes gap 6 in a fight): the attacker on a layer the defender cannot see passively; the attacker pings the attack-move point on the defender's layer every cooldown (the `ahead` policy of `search_policies.py`), so sight comes from the ping (R-008-04, "revealed by a ping may be fired at", `E-01:157`); control: the same scene with pings off, where the A1 count must read 0 for the blind side.
4. `s3_dark_striker` (new): the README's "silent striking force with an emitting decoy" (README `:42`) under the emitting pair; control: everyone silent.
5. Existing S1, S2, S4, S5 plays on `placed_scene` (`scenes.py:147-211`), corrected for the rulings (the stat variants `_LONG`, `_TOUGH`, `_FRAIL`, `_OUT` at `plays_space.py:55-59` retired; `s2_screen` becomes Vanguards in front of Bombards, `s5_vulnerable_away` keeps the Raiders back, `s1_outrange` uses Bastions).

Naive baseline both ways (ruling): against a naive attacker, and against a naive defender at the same post. For a layer play "the same post" is ambiguous (the layer is part of the arrangement), so run the naive defender twice: on the attacker's layer and on the play's layer in a naive blob (section F, question 2); both are cheap.

Ground lab's first scene (after the space batch): `s1_slope_top`: defenders on guard on the upper band at the top of a generated slope (`engine.terrain_generate` with `field_seed`, era kind 1, `fight.py:158-160`), attackers walking (`set_movement_kind` walking) attack-moving up it; knobs `OM_TP_SIGHT_EYE_HEIGHT`, `OM_TP_SLOPE_UP_DIV`, `OM_TP_GROUND_FLYER_SEEN_MULT` (one flyer group as the counter), `OM_TP_TERRAIN_STEEP_DEG`. The ground vision model is fixed by rule (high ground sees down, low never sees up; `fog.c:730`, R-005-09 `E-01:115`), so the sweep there is eye height and the flyer multiplier, not the factors. Pre-flight need: bind `om_terrain_slope_count` and `om_terrain_slope_get` (`csrc/ouroboros_sim.h:2071-2072`, unbound in `engine.py`) to place the defender at a real slope's upper edge.

### Placement and contact under the ruling

- Both sides attack-move to one point (the choke centre, or the defender's anchor), every unit under an order (never idle: probe 8's flinch), the defender on guard only where the play holds a feature and then with the attacker's point inside the defender's reach, as ruled.
- Fit: `placed_scene` records `placement_shift = None` past ±800 wu (`scenes.py:58-59`, `:178-187`) and still builds the fight (gap 5). The sweep must refuse the cell (no fight, a row saying "does not fit") rather than fight from inside a wall; a fit failure is a layout defect to list, not a result.
- Contact at low cross-layer sight is not guaranteed by the order alone. Probe 9: at vision 0.0 both ways 16 v 16 sat at the same point for 6000 ticks with no shot; at 0.25 (175 wu of sight against a 300 wu weapon) 14 v 14 survived the cap with 156 unit-seconds of fire. The attack-moving units halt at their slots once an enemy is in attack range (R-087-04) and never close the last 125 wu. So for any cross-layer cell the pre-flight checks that effective sight at the fight's offset (sensor × factor, or the ping) is at least the weapon range, or the cell is reported as "blind, no contact" with its count and no break-even (section F, question 1).
- The tick cap stays as the bug detector; a cap in a cell whose sight passes the check above is a defect to trace.

### Controls (a changed knob must change a known fight)

| Knob | Positive control (must change) | Null control (must not change) |
|---|---|---|
| vision factors | `s3_layer_above` at `VISION_*_1` 0 reads 0 able both sides and 16 v 16 at the cap; at 0.5 both sides fire (probe 9 rows 1 and 2) | the same mix on one layer: the factors do not touch same-layer sight (`fog.c:771`), so its rows are byte-identical across the vision points |
| range up | `RANGE_UP_1` 0.5 in `s3_layer_above` takes the lower side's count from 1120 to 254 unit-seconds and the fight from a cap to 14 v 0 (probe 9 row 3); the single-unit case: at 250 wu the shooter has a target at 1.0 and none at 0.5 (probe 3) | `RANGE_DOWN_1` left at 1.0 leaves the upper side's engagement distance unchanged |
| damage up | `DAMAGE_UP_1` 0.5: 11 v 0 instead of 2 v 6, counts nearly unchanged (probe 9 row 4): this is the knob that must show "count-only wrong, both wrong" in the predictions, the planted "number that is off" | damage down 1.0 |
| emitting | at base 0.25 and 450 wu, an emitting unit is seen and does not see (probe 7) | at base 0.5 the pair saturates: report it, do not sweep there |
| ping | `s3_ping_then_commit` with pings on: the blind side's count rises from 0 on the first reveal (probe 5: a ping on a layer-0 enemy 1500 wu away puts it in side 0's visible set and not in `seen_by_sight`) | pings off |
| the count itself | the AC 24 hand-built case (`tests/skilllab/integration/test_firing_real.py:80-110`) plus probe 1 as a new case: Bombard 800 wu from a Vanguard reads 0 without a spotter and 1 with one | A1 against the engine-target series (A3) within a stated tolerance on every fight; a gap above it is a defect |
| the planted advantage | the existing 20 percent damage control (`skilllab-harness-spec.md:48`), the one asymmetry the ruling allows | `damage_play(16, factor=1.0)` equals the identical scan |

Candidates for the sweep's shape: (i) one knob at a time on `s3_layer_above` and the corrected S3 plays, then pairs on a region map (`charts.py:73-117` already draws it); (ii) all knobs at once by seeded sample (`sample.py`) over every play. Recommendation: (i) first, exactly the order Westley gave ("all 3 of these knobs 'turned'": vision; vision and reach; plus damage), each table on the layered scene, then the emitting pair, then arc and cone when their engine piece lands; (ii) only after (i) has shown a crossing, as the README's two-track plan says (history `:294-308`). Reason: tables LA, LB, LC in `batches.py:203-253` are the right shape and only lacked a layered scene and a count that could see it; and "LA: vision only" there never varied vision at all (`_layer_settings()` with no arguments writes the defaults, `:205-209`), which is fixed by the value list above.

---

## C. READING A BATCH

### C1, skill wins the firing count, per layout and knob setting

Today (`scripts/skilllab/conditions.py:37-51`) C1 reads the skilled cell at equal numbers only, against the mirror's largest absolute whole-fight advantage as noise. Under elimination-only fights with the scan to 48, compute per (layout, setting, play): the firing advantage from the A1 series, reported two ways: (a) whole-fight unit-seconds (today's `evidence.py:44-46`), kept for continuity; (b) the sustained form, the mean over consecutive windows (the toy's windowed exchange, history `:404`, `:496`: windows of 20 ticks from first contact, per window each side's share of units able) of the skilled side's share minus one half. C1 holds for a play at a setting when (b) exceeds the mirror's window-noise by more than Westley's minimum on at least his share of the layouts that offer the play (both marks are his and stay as drafts in `Thresholds`, `evidence.py:10-25`). Compute it against both naive baselines (ruling) and report both rows; a play that beats 48 against a baseline is a ceiling hit, not a gain of zero (`depth.py:50` treats a `None` break-even as no gain and must change).

### C2, the result follows the firing count

Today's C2 (`conditions.py:80-94`) ranks whole-fight firing advantage against margin. The toy showed the whole-fight form "partly restates the outcome" (history `:460`: 98 of 100 agreement in a mirror with no positional edge) and that the opening window and the windowed exchange do not. So C2 should be computed on the two trap-safe predictions: (1) the opening-window prediction (first 40 ticks after first contact, count-only and type-weighted) against the winner, and (2) the per-window agreement between the share of units able and the share of damage dealt (a window where they disagree is a number overriding position). The margin against the whole-fight advantage stays on the page as a chart, not as the pass test. The knob rows that must fail C2 by design are the damage-up rows (probe 9 row 4: counts nearly level, result 11 v 0); if they pass, the detector is broken.

### Finding and showing "the lines cross"

Per knob, the gain curve is break-even(skilled) − break-even(naive) at each coarse point, for each layout; a crossing is where the curve changes sign, or where a play stops beating its counter. Coarse first (four points), then refine by halving between the two points that bracket the sign change, as section B says. With two knobs, the region map of `charts.region_map_html` (`charts.py:73-117`): cells shaded where C0 to C2 hold, numbered regions, a plain-words table "x from … to …". Westley, 2026-10-01: "The *lines* can cross in multiple locations" (README `:11`), so every region is listed, not the first.

### The page

Keep the form he approved (README `:96-106`): a heading in soldiers, the line of fights by enemy size with the break-even marked, the two firing lines with the gap shaded, a plain-words table. Add, per notable layout (a crossing, a ceiling hit, a C2 failure), a top-down diagram: the canvas, the wall blocks and the choke gap from `layout.blocks`, cover discs, both plays' formation points coloured by layer and filled or hollow by side, the attack-move point, and arrows from the group that is firing to the group it fires at, labelled with the count at that sample ("12 of 16 able, 3 of 16 answer"), one diagram per assertion on the page. No drawing helper exists today (`mapreport.py` is numeric; `report.py:62-130` draws scans and firing lines), so this is a new module beside `charts.py`. This is Westley's 2026-10-13 requirement as relayed in the brief; I found no repo text for it.

Candidates for the reading: (i) keep whole-fight advantage as the one measure and add the diagrams; (ii) add the windowed and opening forms as the pass tests and keep whole-fight as a chart. Recommendation: (ii), because (i) is the recorded trap in a milder form.

---

## D. WHERE THE TEXT GOES

| Change | Document and section | Must not change |
|---|---|---|
| The count definition (A1), the arc clause, the transition reading, the type weight | `docs/northstar/plans/skilllab-harness-spec.md` AC 10 (line 25) rewritten; AC 24 (line 49) gains the spotter case; the cascade brief's bullet at `2026-10-02-skill-lab-cascade.md:95` marked superseded by AC 10 | AC 21 to 23 thresholds (mirror 0.10, 17 v 16, planted 20 percent): Westley's |
| The measure, the two predictions and the trap | `docs/northstar/research/layer_dynamics/README.md` section 4 "The measure" (lines 62 to 67), replacing "Weighted by unit type where types differ" with the catmult definition; section 7's gap table rows at lines 131 to 132 ("Targeting ignores fog", "same-layer fire only") deleted as landed | sections 1 to 3 (his words), the draft pass marks (lines 71 to 82) |
| The sweep: knobs, values, scenes, controls, contact check, reading | a new batch spec beside the layout search spec: `docs/northstar/plans/2026-10-1x-layer-vision-sweep-spec.md`, in the layout spec's shape (pieces, tests first, pre-flight) | `2026-10-06-layout-search-spec.md` stays as run 1's record; Rev 4's hold condition is retired by the ruling and the retirement is a line in the new spec, not an edit of the old one |
| Retired code paths (hold, draw band, blind window, stat variants) | `scripts/skilllab/contract.py:102-106`, `fight.py:211-224`, `:335-340`, `scenes.py:209`, `plays_space.py:55-59` listed in the spec with the ruling that retires each (CLAUDE.md "existing tests that encode a superseded ruling listed") | nothing is deleted without the parity test the guards require |
| Register | `Q-008-03` (row 228): the parameter families gain the arc and cone cross-references; `Q-008-07` (row 284): the recommendation is candidate (a), for Westley to close; `Q-LAB-03` (row 58): the retired end rules are already there; two new rows from section F below | the bible rules the lab feeds: E-01 S-005, S-007, S-008, S-162 to S-164 and E-11 S-082, S-085 stay as they are until the lab reports; the end-state paragraph of S-008 (`E-01:159`) is the acceptance bar and is not edited |
| The stale sentence "The prototype is same-layer only until the lab reports" (`E-01:164`) | a bible correction for Westley's approval, not the lab's edit | |

---

## E. CONTRADICTIONS (beyond the two blind spots and the seven gaps)

1. `scripts/skilllab/batches.py:203-209` and `:244-245`: table LA "vision only" sets `OM_TP_VISION_*` to 0.5 / 0.2 / 0 / 0, which are the engine defaults (`pp_contract.md:121-128`), so "vision only" never turned the vision knob even on a layered scene; against Westley, 2026-10-01: "with all 3 of these knobs 'turned'".
2. `scripts/skilllab/evidence.py:44-46` and `conditions.py:80-94`: C2 is computed on whole-fight unit-seconds, the form the toy showed restates the outcome (history `:457-462`), and against the instrument Westley accepted on 2026-10-01 as "consistent firing advantage" (history `:385`, `:404`: "the sustained form should compare rates").
3. `scripts/skilllab/firing.py:55-59`: the weight is damage per interval, a unit value; README `:66` says "Weighted by unit type"; Westley, 2026-09-30: "not just unit values but their type as well" (history `:326`).
4. `docs/northstar/plans/2026-10-02-skill-lab-cascade.md:95` promises "After engine step G3 also: the enemy is seen by the unit's side"; G3 landed (`csrc/unit.c:1171-1180`) and `firing.py` never did it; the harness spec AC 10 (`:25`) still reads "its own layer until the engine cascade lands".
5. `docs/northstar/research/layer_dynamics/README.md:131-132`: the gap table still says "Targeting ignores fog and line of sight" and "No layer changes, slopes, ping, going dark or reach by type; same-layer fire only"; all of it is in the engine (`fog.c:486-501`, `tactical_move.c:2414`, `:3179`, `fog.c:744-750`, `:882-893`).
6. `docs/bible/epics/E-01-layer-system.md:164` "The prototype is same-layer only until the lab reports" against the engine's cross-layer acquisition (`unit.c:1731-1768`); and `E-11:144` R-087-03 "within attack range on its layer" is still the rule text while `unit.c:1716-1719` fires across layers (E-11 marks it "rewrite pending" at `:139`, so it is stale, not hidden).
7. `scripts/skilllab/plays_space.py:196-197`: `s3_types_by_reach` is described as firing down "which the enemy cannot return", against R-164-03 (`E-01:243`): "a type that reaches further is weaker to something another type does, so its advantage is temporary"; the play plants an unanswerable edge instead of a temporary one.
8. `scripts/skilllab/scenes.py:209` and `contract.py:102-106`: every placed scene still ends by `decided_by_survivors`, `silence_ticks`, `hold_anchor` and the 5 percent draw band; the 2026-10-13 ruling (README `:90`, register `:58`) retires them; `scan.py:38` still scores `decided` and `held`.
9. `scripts/skilllab/depth.py:16` scans 8 to 24 and `:50` scores a missing break-even as no gain; ruling: 8 to 48, and a play that beats 48 "is a ceiling hit, never no gain".
10. `scripts/skilllab/fight.py:286-287`: the re-issue rule's docstring says "Ruled 2026-10-07 (Westley 2026-10-06, attack-move all units to the same spot)"; the register's Q-LAB-03 row (`:58`) dates that ruling 2026-10-13 and quotes it; the 2026-10-06 words are not in the repo in that form (the drift audit of 2026-10-07, `docs/northstar/plans/archive/audits/audits_2026-10-07/lab-drift.md:23`, already found two unlocatable quotes).
11. `csrc/fog.c:744-750`: the emitting multipliers are capped at 1.0 after the base factor, so at the bible's 0.5 base the ruled starting pair (2.0, 3.0) cannot be told apart (probe 6 and 7); R-163-01 (`E-01:227`) wants seen-from to grow "by more than" sight.
12. `docs/northstar/research/layer_dynamics/audits/2026-10-04_rules_against_strategic_depth.md:15` item 7 recorded on 2026-10-04 that "the firing count is binary, same-layer only and unweighted"; no ledger row or spec change followed, so the blind spots were known nine days before the 2026-10-13 audit.

---

## F. OPEN FOR WESTLEY (no rule or quote answers these)

1. Cross-layer sight below weapon range stalls the fight (probe 9: vision 0.0 and 0.25 both capped with units standing at the same point). Under "a capped fight is a lab defect, never a result", how is a blind cell read? (a) floor the vision band where sensor × factor equals the weapon range (about 0.43 for the Vanguard) and report lower points as "blind, no contact" with the count only; (b) read a blind stall as a result against the side that cannot find the enemy, scored by the count, no break-even; (c) make the ping the contact source for every cross-layer cell in the space lab, so blindness is measured through the ping settings.
2. The naive defender "at the same post" for a layer play: (a) on the attacker's layer (the layer is the skill); (b) on the play's layer in a naive blob (isolates arrangement from height); (c) both, reported side by side.
3. Range and damage multipliers above 1.0 for firing up: his words name a penalty ("damage penalty for firing up", "shorter firing up"); the band allows 2x and 4x. (a) include 2.0 as a sign-flip control only; (b) penalties only, 0.25x to 1.0; (c) full band.
4. The type weight (Q-008-07): (a) the category multiplier of the engine's target of record (recommended); (b) of the nearest able enemy; (c) keep a third series weighted by damage rate, labelled "unit values", for comparison.
5. The cone's victims in the measure: (a) a cone unit counts once, victims in a separate column (recommended); (b) the weighted series adds one catmult per victim, capped by the area cap.

---

## G. CONFIDENCE

| Recommendation | Rests on | What would change my mind |
|---|---|---|
| A1 now, A2 with the arc piece | the engine's own gates at `unit.c:572-577`, `:1716-1719`, `:1165-1180`, `:2140`; probes 1 to 5 and 9 (A1 within about 1 percent of the engine-target count on every row; today's count 0 on every row) | an engine piece that moves eligibility into one query sooner than the arc, or a measured per-sample cost at 48 enemies that breaks the 30 s scan gate (`skilllab-harness-spec.md:53`) |
| catmult weighting, no damage or health | transcript line 704 (approved at 712); history `:340-353`; `firing.py:55-59` as the unit-value weight; `csrc/ouroboros_sim.h:2091` exposes the table | Westley choosing (b) or (c) in F4, or a batch where the catmult series agrees with the outcome exactly as often as whole-fight unit-seconds do (then it leaks too) |
| the value lists and the emitting base | the ruling's band and factor (README `:93`); `fog.c:733` and `:749` caps; probes 6 and 7; the toy's "decisive within 20 percent" (README `:192`) | a refinement that finds the crossing outside 0.25x to 4x, which needs a written reason, not a wider band |
| `s3_layer_above` as the primary scene, contact check before every cross-layer cell | probe 9's two capped rows; R-087-04 halting at attack range; R-087-01 flinch in probe 8 | Westley choosing F1 (b) or (c), which makes a stall a reading rather than a pre-flight refusal |
| windowed and opening forms as the C2 pass tests | history `:457-462` and `:496` (measured on the toy, transfer class T2) | the real engine showing the whole-fight form does not leak at these sizes, which the first batch can test by comparing all three forms on the planted damage control |
| the page's diagrams as a new module | no drawing helper on main (`mapreport.py`, `report.py:62-130`) | none; it is a build question |

Scratch artefacts (not in the repository): `/tmp/claude-1000/-home-westopoli-Projects-ouroboros-manifold/7e9d8393-6f9a-44e1-a26b-66264f334079/scratchpad/agent-one/probe2.py`, the extracted tree under `.../agent-one/repo/`, and the exported sources under `.../agent-one/src/`.
