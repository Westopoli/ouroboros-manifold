# Proposal two: covering the lab's two blind spots (layers and vision)

One of three Fable 5.1 research agents given an identical read-only brief on 2026-10-13 by the Architect chat, at Westley's request. The brief, the rulings it rests on and the seven known gaps are in `synthesis.md`. This file is the agent's report verbatim.

## Evidence base

Everything below was read from `origin/main` at `68547f9e`. Paths are given in full at first mention and shortened after; all are under `/home/westopoli/Projects/ouroboros-manifold/`. Six probes ran on a scratch copy of `csrc/` built in the scratchpad (`.../scratchpad/agent-two/probe1.py` to `probe6.py`); the repository was not touched. Probe results quoted here are from those runs.

Key probe results (scratch library, `scripts/skilllab/fight.py` unchanged):
- P1: side 0 = 16 Vanguard clones with reach (0, 1) on layer 1, side 1 = 16 Vanguards on layer 0, `OM_TP_VISION_UP_1 = 0`. Outcome side0, survivors (16, 0), 2,115 ticks. The current count read `first_contact_tick = -1`, `firing_unit_seconds = (0.0, 0.0)`; the weighted count read (7760.9, 0.0). The measure saw nothing of a 16-to-0 wipe.
- P2: a Vanguard ordered from layer 0 to 1 reads layer 1 from tick 25 of a 50-tick transfer: `om_unit_get_layer` is the effective layer (`csrc/tactical_move.c:2413`, `if (2 * mu->lay_t >= mu->lay_dur ...) om_tac_unit_set_layer`).
- P3: two Bombards 600 wu apart (sensor 300, range 1,200), idle: the count reads (1, 1) at tick 0; no damage in 100 ticks. Add one Raider spotter on side 0: side 0 fires (enemy strength 0.912), side 1 still cannot; the count still reads (1, 1).
- P4: same pair, side 0 pings the enemy at tick 0: `om_unit_can_see` False, `om_player_can_see` True, `seen_by_sight` empty, and the engine fires (enemy strength 0.956 after 60 ticks). "Seen by the side" is `om_player_can_see`, not `seen_by_sight`.
- P5: emitting target one layer up at 420 wu, base vision 0.2, sensor 700: seen only when `OM_TP_EMIT_SEEN_MULT` = 3.0 (0.2 x 3 x 700 = 420); not at 1.0; the observer emitting with sight x2.0 does not see it (0.4 x 700 = 280). The knob works; the control is a `can_see` at a known distance.
- Candidate count (section A, A1) on P1 reads (1279.8, 0.0) unit-seconds beside the engine's own target set (1267.0, 0.0); on P3 it reads (0, 0) without the spotter and (5.0, 0.0) with it.
- Vision sweep on a corrected layer play (both sides 8 Raiders with reach (1, 1) plus 8 Vanguards; the skilled side's Raiders one layer up; both sides attack-move to one point; 2 seeds x 2 spawn orders): against 24 the mean margin ran +0.42 (vision 0), +0.42 (0.0625), +0.37 (0.125), +0.01 (0.1875), -0.03 (0.25); against 32: +0.18, +0.18, -0.03, -0.25, -0.43. The crossing for this play sits between 0.125 and 0.25 (the Raider sees up to 800 x factor; its range is 200).
- P3/P6 (contact): after the first exchange, surviving Vanguards of both sides stood 316 wu apart (range 300) with no target and no destination for 400 ticks ("stalemate"). P6 confirmed the cause: four Vanguards attack-moved 1,200 wu past a Raider killed it at tick 153 and never moved again (x stayed at 1,315; `order_ends` at tick 154). That is E-13 R-096-02 as built: "once every member of the group has engaged, the group ends and its members do not resume the march" (`docs/bible/epics/E-13-movement-and-command.md:49`; `csrc/unit.c:1943-1960`, `om_tac_release` -> `om_tac_am_group_done` -> `om_tac_drop_orders`).

---

## A. ABLE TO FIRE

### What the toy measured (the definition that was lost)
`toys/layerlab/SPEC.md:164` (5.11a): a unit can fire on a tick when it is alive, not winding, and acquisition gave it a target "in range, seen when `fire_requires_vision` is on, eligible under the halfway rule, inside the arc when the gate is on"; it does not depend on cooldown. `SPEC.md:167`: `firing_weight` = sum over able units of `category_mult[unit category][target category]`. So the toy's count had sight, the halfway rule, the arc and type-against-type weighting. The X2 to X4 scenes (`docs/northstar/research/layer_dynamics/history_2026-09-30_to_10-01.md:444-451`) were 10 v 10 Raiders, A on layer 4, B on layer 3; X2 B blind up (A wins 100 of 100), X3 B sees but cannot fire up (100), X4 both answer (43 of 100: "a layer alone gives nothing"). The vision cliff (`history:455`): at factor 0.05 "12 units already win 90 percent".

The harness regressed to same layer only, line of fire only, and own damage rate as the weight: `scripts/skilllab/firing.py:17-27` (`if elayer != layer: continue`; `ranges[u]` with no offset multiplier; `can_shoot`), `firing.py:54-58` (`unit_weight` = `base_damage / attack_interval`), `firing.py:61-73` (the weighted count: engine target, reach, base range, `can_shoot`). `docs/northstar/plans/skilllab-harness-spec.md` clause 10 still says "its own layer until the engine cascade lands reach".

### What the engine itself requires before a shot
- Reach by type and the offset range multiplier: `csrc/unit.c:1716-1719` (`om_tac_in_range`: same layer at plain range; other layer only within reach at `attack_range * offset mult`), `unit.c:571-576` (`om_tac_in_reach`), `unit.c:579-588` (`OM_TP_RANGE/DAMAGE/AREA_UP|DOWN_n`, offsets above 4 read 1.0).
- Side sight: `unit.c:1165-1180` (`om_tac_faction_sees` = own `om_unit_can_see` or `om_fog_faction_sees`; `om_tac_may_act_on` gated by `OM_TP_TARGET_BY_SIGHT`, default 1 per `docs/northstar/plans/push/pp_contract.md:98`); acquisition at `unit.c:1996-2000`, a held target the side no longer sees dropped at `unit.c:2140`; `csrc/fog.c:486-503` (`om_fog_faction_sees`: any living friendly's sight, then live ping reveals), `fog.c:610-617` (`om_player_can_see_unit` = that, or omniscient when player fog is explicitly off).
- Line of fire only: `csrc/tactical_move.c:2582-2620` (`om_combat_can_shoot` samples cover, blocked cells, ground; no range, no sight, no reach).
- The fire pass: `unit.c:2256-2259` (in range, cooldown or first shot, `can_shoot`).
- Cross-layer sight factor: `fog.c:719-740` (parameter per offset, capped at 1.0, 0 beyond offset 4; ground era: up 0, down 1), emitting `fog.c:742-749`, ping reveal `fog.c:874-890`.
- Effective layer in transition: `tactical_move.c:2413`; E-01 R-004-02 (`docs/bible/epics/E-01-layer-system.md:84`) matches: the unit attacks as a unit of the layer it is leaving until the cross-over.

### Candidates

**A1. Composed from public engine queries (per unit, per sample).** A living unit is able when some living enemy e satisfies all of: (1) the side sees e, `om_player_can_see(side, e)` (`engine.visible_enemies`, `scripts/skilllab/engine.py` ~196), which carries vision factors, emitting, cover, terrain and pings in one call; (2) the signed layer offset `layer(e) - layer(u)` (both `om_unit_get_layer`, effective layers) is within the type's reach (`om_unit_profile_reach`; offset 0 always); (3) distance <= `attack_range x OM_TP_RANGE_{UP,DOWN}_|offset|` (read once per fight through `get_param`); (4) `om_combat_can_shoot(u, e)`; (5) once the arc lands: the bearing to e lies within half the arc of `om_unit_get_facing(u)` (bound already). Cooldown is ignored, as the toy did. Transition needs no special case: the effective layer is what the engine fires from (R-004-02, P2).
- Pros: no engine change, so the sweep can run now; independent of the engine's target choice, so it keeps the AC 24 style of positive control (hand-built geometry with a known answer catches an engine fault); every knob enters by construction (vision, emitting and ping through the side set; reach and range multipliers through 2 and 3; arc through 5).
- Cons: duplicates `om_tac_in_range` in Python; a drift between the two is a silent lie. Cost about one `visible_enemies` per side per sample on top of today's loop.
- Risks: `om_player_can_see_unit` returns omniscient if a caller ever sets player fog off (`fog.c:614`); the lab must assert it never does. The arc rule in Python must match the C arc exactly (same half-angle test, same facing source), which argues for A3 when the arc lands.
- Evidence: probe outputs above (reads the P1 wipe, reads 0 for the unseen Bombard pair, 5/0 with the spotter; within 1 percent of the engine's target set).

**A2. The engine's own target (what `count_able_weighted` already does, unweighted).** Count units whose `om_unit_get_target` is a living enemy.
- Pros: no duplicated arithmetic; the arc, cone and any future gate come for free; cheapest.
- Cons: it is "is targeting", not "able": targets are refreshed by cohort every 4 ticks (`unit.c:2164`, `OM_TARGETING_COHORT_COUNT`), so a unit is counted late; it cannot catch an engine fault (if the engine wrongly refuses a target, the count agrees); as built it ignores the range multiplier (`firing.py:70` tests `rng * rng` with the base range, against `unit.c:1718`).
- Evidence: 1267.0 against A1's 1279.8 on P1 (the lag).

**A3. One public engine query, a contract piece: `om_combat_can_engage(w, a, b)`** in `csrc/unit.c`, applying reach, offset range, side sight, line of fire and the arc, used by the fire pass itself and bound by the lab; declared in `csrc/ouroboros_sim.h` and `signatures.toml` (CLAUDE.md: a contract change lands first as its own piece).
- Pros: one truth; the arc and cone piece must touch `unit.c` anyway, so the gate goes in with it; cheap in C.
- Cons: waits for a contract landing; the lab's hand-built geometry tests must stay as the independent check.

**Recommendation.** A1 now, with a parity assertion in every fight (per sample `|A1 - A2| <= headcount lag`, reported as a lab defect when broken); A3 as the contract of the arc-and-cone engine piece, after which A1's Python arithmetic is replaced by the one call and the hand-built tests pin it. Both predictions change, as follows.

### The two predictions and the weighting that avoids the trap
The recorded trap (`docs/claude_exchange/transcripts/2026-09-30_dd1ff47b_layer-lab-design-and-plan.jsonl` line 704, approved at 712: "If the metric is 'units firing x their damage, against the enemy's health', it will always agree with the result"). The weighting as built (own damage rate, `firing.py:54-58`) is halfway into the trap: it carries a magnitude, not a type.

Proposed: count-only = A1 per side. Type-weighted = sum over A1-able units of `M[cat(u)][cat(t)]`, with M the category triangle of E-11 R-081-01 (`docs/bible/epics/E-11-units-and-combat.md:33`; Siege to Strike 0.20 per Q-081-01), read from `OM_TP_CATMULT_*` so a matchup sweep moves it; t is the unit's engine target when that target is A1-able, else the nearest A1-able enemy. The weight carries no hit points, no base damage, no interval and no cross-layer damage multiplier: the triangle is the only thing added. Then the four readings are: both right (position decided); count wrong, type right (the triangle decided it, acceptable, Q-008-07 candidate a); both wrong (a magnitude overrode position: a layer damage multiplier, health or range, Westley's "a number that's off", 2026-10-01); count right, type wrong (the weighting is wrong, a lab finding). `OM_TP_DAMAGE_UP/DOWN` must stay out of the weight: in table LC it is the knob under test, and folding it in would make the predictor agree by construction. Prediction form: the toy's `strength = f x n0^2` (`toys/layerlab/SPEC.md:213`), primary on the opening window (first 40 ticks after first contact; `history:461`: it "cannot leak the ending"), secondary on whole-fight unit-seconds.

---

## B. THE SWEEP

### Knobs and parameters, values and their source
Band rule (Westley, 2026-10-13, README section 4): start at the bible's value, step by a named factor inside 0.25x to 4x, three to five points, coarse first. Engine refusal ranges: `pp_contract.md:94-159`. Every value below that is not a bible number is a draft and says so.

| Knob | Parameters | Base and source | Coarse points | Note |
|---|---|---|---|---|
| Vision only (LA) | `OM_TP_VISION_UP_1`, `DOWN_1`; `UP_2`, `DOWN_2` | 0.50 and 0.20 (E-01 R-005-02, R-005-04; provisional, Q-005-07; symmetric up = down, Q-005-02 (a)) | 0.125, 0.25, 0.5, 1.0 and 0.05, 0.1, 0.2, 0.4 | x4 of 0.5 is capped to 1.0 by `fog.c:733`, so 1.0 is the top. Arithmetic to confirm: a type answers across one layer only when sensor x factor >= range x range multiplier: Vanguard 300/700 = 0.43, Raider 200/800 = 0.25, Interceptor 250/1000 = 0.25, Bombard 1200/300 = 4 and Bastion 800/300 = 2.7 (never by passive sight: spotter or ping only, R-093-02). The probe's crossing (0.125 to 0.25) fits the Raider line. |
| Vision and reach (LB) | reach table fixed (R-164-01: Line own layer, Raider 1/1, Interceptor 2 up 1 down, Siege 2 down), carried by derived types with `"reach"` and no stat change; `OM_TP_RANGE_UP_1`, `UP_2` | 1.0 (G5; Q-008-03 open) | up: 1.0, 0.75, 0.5, 0.25 (the A174 drafts at `scripts/skilllab/batches.py:214-216` sit inside) | "shorter firing up than firing down" is the stated LB meaning (`history:399`). Down stays 1.0 in the first pass; a down bonus is a second pass. 4.0 up is outside sense (a 1,200 wu shot). |
| Plus a damage penalty up (LC) | `OM_TP_DAMAGE_UP_1`, `UP_2` | 1.0 | 1.0, 0.75, 0.5, 0.25 | the draft convention `dmg2 = dmg1 / 2` (`batches.py:216`) is nobody's number; flag it |
| Emitting | `OM_TP_EMIT_SIGHT_MULT`, `OM_TP_EMIT_SEEN_MULT` | 2.0 and 3.0 (Westley 2026-10-13); seen > sight always (R-163-01) | sight 1.0, 2.0, 4.0; seen = sight x 1.5 and x 3 | bites only where base vision x seen < 1: sweep it jointly with vision at 0.125 to 0.25, else it is capped and inert (`fog.c:749`). Control: P5. |
| Ping | `OM_TP_PING_RADIUS` 500, `REVEAL_TICKS` 100, `REACH` 2000, `COOLDOWN_TICKS` 400 | R-162-01, R-162-02 (provisional) | not swept in this batch (Stage A has its own sweep) | enters the count through the side set; cast as a `Step.ping` at tick 0 in the S-L3 and S-L5 plays below |
| Firing arc (engine piece first) | named by the piece; draft `OM_TP_FIRING_ARC_DEG` (Q-100-01 (a): DRAFT-firing-arc-deg 120); a mode parameter for the flanked case | 360 = today (R-100-01 to R-100-03 are cosmetic) | 360 (control), 180, 120, 90, 60 | orientation returns as a play variable (`Group.facing_deg` exists) |
| Cone area damage (engine piece first) | shape, range, half-angle, share: Q-082-06 (a) DRAFT-aoe-cone-range 300, DRAFT-aoe-cone-deg 45 | today a disc of `aoe_radius` about the target on any type whose profile has it (`unit.c:1967-1968`, `unit.c:2771-2795`, reach-gated, `OM_TP_AREA_*` applied) | disc radius 0 (control), 75, 150, 300 now via `unit_types` `set: {"aoe_radius": r}` on both sides' type; cone 22.5, 45, 90 degrees after the piece | the disc on "any unit" is sweepable today without an engine change |
| Category triangle (type matchup, gap 3) | `OM_TP_CATMULT_*` | R-081-01 | each off-diagonal cell at x0.5, x1, x2 of its base, one family at a time (draft) | |
| Unit size | `OM_TP_UNIT_COLLISION_RADIUS` | 15 | excluded until D1 lands (gap 2); when it lands, the control is a 2-body choke changing at 10 against 30 | |

`OM_TP_TARGET_BY_SIGHT` is a baseline switch, never a knob (Q-008-04 closed (a); `toys/layerlab/SPEC.md:106` "never swept").

### Scenes and plays (space lab first)
Every scene: same roster mix on both sides (the ruling), 16 against 8 to 48, both naive baselines, both spawn orders, both sides attack-moved to one point or the attacker's point inside the defender's vision and fire.

- S-L0 mirror: 8 Raider-reach types + 8 Vanguards per side, all on layer 0. C0 at every setting.
- S-L1 Raiders up (replaces `s3_types_by_reach`, `scripts/skilllab/plays_space.py:105-110`, whose `_HIGH` at line 59 gives a Vanguard reach (0, 1) against R-164-01): the skilled side's Raiders stand one layer above the point; naive stands flat. Probed above; the vision knob moves it.
- S-L2 the answer from below: the enemy's Interceptors (2 up) against Raiders held two layers up; the counter R-164-03 names ("a unit that works particularly well at destroying units from above", Westley 2026-10-01, Q-005-02).
- S-L3 Siege over the choke: a layout with `blocked_layer_top` 2 (`scripts/skilllab/maps.py:110-117`); the skilled side's Bombards stand on layer 3 above the wall (reach 2 down) with a Raider spotter past the choke or a ping on layer 0 at the enemy's point; exercises R-093-02 shared sight and R-007-07 cover across layers.
- S-L4 dark approach: sides on adjacent layers; skilled silent, naive emitting, then both toggled (`Step.set_emission`); reads each side's first-contact tick and the opening-window count.
- S-L5 ping then place: `Step.ping` at tick 0 on the enemy's layer at its anchor, then `Step.set_layer` moves the Raiders to reach +1 of the revealed layer; the timeline's `"seen"` trigger uses `engine.can_see` (`scripts/skilllab/timeline.py` ~80), which excludes pings, and must read `visible_enemies` for this play.
- Existing plays corrected to roster types with identical mixes both sides: screen = Vanguards in front, Bombards behind (not `_TOUGH`/`_LONG`, `plays_space.py:56-57`); vulnerable away = Raiders behind Vanguards (not `_FRAIL`, line 58); outrange = Bastions (800) standing off Vanguards (300) (not `_OUT`, line 60). Retired per the 2026-10-13 ruling.
- Ground lab, first scene (no spec exists; `scripts/skilllab/ground/README.md`): terrain seed 11, walkers, the two flat band-3 and band-2 squares at (8150, 6050) and (8550, 6050) and the slope at (6550, 4050) that `tests/skilllab/integration/test_ground_scene_real.py:28-33` already asserts; defenders guard the slope top (R-096-08), attackers attack-move to a point at the top inside the defenders' vision and fire; knobs `OM_TP_SIGHT_EYE_HEIGHT` (50 base, 25 to 200), `OM_TP_GROUND_FLYER_SEEN_MULT` (1.5 base; 1.25, 1.5, 2, 3; never below 1, R-005-11), `OM_TP_SLOPE_UP_DIV` (1.1, Westley 2026-10-06; a 0.25x band is meaningless for a divisor near 1, so draft points 1.0, 1.1, 1.3, 2.0, flagged); no ping (R-162-01). Negative control: `OM_TP_VISION_UP_1` must not change a ground fight (`fog.c:731`: ground era returns up 0, down 1).

### Placement and contact under the ruling
- Fit: `scenes.placed_scene` records `placement_shift = None` past 800 wu and fights anyway (`scripts/skilllab/scenes.py`, `FIT_LIMIT`); a cell whose formation does not fit is reported "not placed" and never fought.
- Contact: as built the engine ends an attack-move group once every member has engaged and nobody marches again (R-096-02; P6), so two remnants can stand 316 wu apart with no target (P3): a tie that the ruling ("unless there's a bug it's not possible for a tie (eventually)") does not allow. Two candidates: (B-c1) after placement, issue each attacker's attack-move singly, one unit per order, so no group forms and the game's own rule resumes the march after every fight (R-096-02 last sentence); (B-c2) a lab re-issue every `REISSUE_TICKS` (200, `scripts/skilllab/contract.py`) sending any group with no living target and no destination to the common point again, regardless of sight (the mop-up rule, `scripts/skilllab/mopup.py:1-7`, re-orders only toward a seen enemy, so a side that sees nothing never moves; Rev 4's `reissue` in `fight.py` is tied to `decided_by_survivors` and `hold_anchor`). Recommend B-c1 for the attacker (the game's rule, no lab invention), B-c2 as the safety net, with any cap or stalemate written as a defect row. The defender's point for a guard play is its anchor, which is inside its 200 wu guard radius and its vision.
- Fight end: `scenes.placed_scene` must stop setting `decided_by_survivors=True`, `silence_ticks`, `hold_anchor` (the last lines of `scenes.py`); `fight.py` keeps elimination, draw-on-one-tick, and the cap as a detector only.

### Controls (a changed knob must change a known fight)
1. Vision: the X2 scene (blind up) reads 16 to 0 (P1). 2. Range multiplier: `OM_TP_RANGE_UP_1 = 0` zeroes the up-firing side's count in a Raiders-below scene. 3. Damage: `OM_TP_DAMAGE_UP_1` 0.25 against 1.0 moves that scene's break-even by at least one unit. 4. Emitting: the `can_see` at 420 wu (P5). 5. Arc: 360 against 60 on a flank scene (attacker from behind, defenders facing away) changes both predictions. 6. Cone: a three-unit cluster's hit count. 7. The planted 20 percent damage scan (existing, spec AC 23). 8. Ground negative control above. 9. The count itself: the Bombard pair without and with a spotter (0/0 then 5/0) and the A1-A2 parity.

---

## C. READING A BATCH

- C1 per layout and setting: the equal-numbers cell (16 v 16), skilled against naive both ways; firing advantage `(f0 - f1) / (f0 + f1)` (`scripts/skilllab/evidence.py`, `firing_advantage`) on the new count, primary over the opening window after first contact, secondary over unit-seconds; "wins the count" as `scripts/skilllab/conditions.py` `check_c1` has it (exceeds the mirror cell's largest absolute advantage by Westley's minimum; share of maps). Both the count-only and the type-weighted series are recorded (run 1 recorded neither weighted column: `docs/northstar/research/layer_dynamics/runs/2026-10-08_layout_run1/depth.csv.gz` header has no `weighted_unit_seconds_*`; `scripts/skilllab/depth.py` never sets `weighted=True`).
- C2 per layout and setting: under elimination the margin is the winner's remaining strength share, so `check_c2`'s Spearman over pooled fights stands; add the toy's agreement table per fight (`toys/layerlab/SPEC.md:213`, `check`): predicted winner from `f x n0^2` count-only and type-weighted against the actual, in the four classes of section A; the "both wrong" rows, listed with their setting, are the findings.
- Lines crossing: per scene and knob, the break-even of the skilled play and of each naive baseline as the knob moves; a crossing is the interval where their difference changes sign or the skilled play hits 48 (reported as a ceiling hit); two knobs at a time on `scripts/skilllab/charts.py` `region_map_html` shaded where C0, C1 and C2 hold, regions numbered, `scripts/skilllab/tree.py` in words; coarse 3 to 5 points, then one midpoint per bracketing pair, at most two rounds (the probe's 0.125 to 0.25 is the worked case). `scan.py`'s `refine_factor` refines headcounts only; the knob refinement is a small new loop in a batch spec runner.
- The page (README section 5 form, the sample Westley called "much better"): a heading in soldiers per setting ("With its Raiders a layer up and sight across layers at 0.125, 16 beat 24; at 0.25 they beat 16"); fights by enemy size as small multiples per setting (`charts.small_multiples_html`, 2 to 12 panels); units able to fire through one fight per coarse setting, both lines labelled and the gap shaded, with the type-weighted pair beside; the agreement table with an "In words" column; the region map. Per notable layout, a top-down diagram: a new `scripts/skilllab/diagram.py` writing inline SVG from the `Setup` and layout (wall rectangles, cover discs, the choke centre, the attack-move point, each group's footprint with its layer written, the guard radius) and the first-contact sample from `FightResult.states` and `trace` (units coloured able, blocked, unseen, out of reach), with arrows whose text is the row value they come from ("8 of 24 attackers able at the choke mouth, tick 212"; "Raiders on layer 1: 8 able, 0 able to answer: 0.125 x 800 = 100 wu < 200"). `scripts/skilllab/mapreport.py` is numbers only; nothing draws today. This requirement is in the brief as Westley's of 2026-10-13; I found no repo text for it, so it goes into README section 5 before it is built.

Candidates for the C1/C2 predictor: whole-fight unit-seconds (today) versus the opening window. Recommend the window as primary: whole-fight unit-seconds grow with survival time and lean toward the winner, the weaker form of the trap; the window cannot leak the ending (`history:461`).

---

## D. WHERE THE TEXT GOES

| Change | Document and place |
|---|---|
| The definition of able to fire (A1 now, A3 later), the parity assertion, the type weighting and the two predictions | `docs/northstar/plans/skilllab-harness-spec.md` clause 10 (rewrite; retire "its own layer until the engine cascade lands reach"), clause 24 gains the Bombard-spotter and cross-layer hand-built cases; `scripts/skilllab/contract.py` docstring of `count_able`; `docs/northstar/research/layer_dynamics/README.md` section 4 (the measure: "Weighted by unit type" becomes the triangle definition) and section 7 (the gap table, stale: G3 to G7 landed) |
| Tests that encode the superseded rule, with the ruling that retires them | `tests/skilllab/test_firing.py:66-73` (`test_ac24_different_layers_do_not_count`: retired by R-008-02 and the landed G5), `tests/skilllab/integration/test_firing_weighted_real.py:2` docstring ("without the side-sight engine rule", G3 landed); `tests/skilllab/test_firing_weighted.py` where it pins damage rate; ledger rows `TD-SKILLLAB-*` in `docs/northstar/plans/push_ledger_2026-09-22.md` |
| The sweep: knobs, values, scenes, controls, contact rule, refinement, page | a new batch spec beside the layout search spec: `docs/northstar/plans/2026-10-14-layer-sweep-spec.md` (table of section B, drafts marked, owner rows); owner rows in `docs/northstar/plans/push/pieces.toml` (today `SL-harness` at line 1165-1172 owns `scripts/skilllab/**` by glob and `LAB-SEARCH` at 1366-1376 owns `scenes.py`, `fight.py`, `batches.py`, `plays_space.py` explicitly: the new piece must take those rows over) |
| The contact rule and the retired end rules in code | `scenes.py` `placed_scene`, `fight.py` outcomes; register `Q-LAB-03` row (already carries the ruling) |
| Corrected plays | `scripts/skilllab/plays_space.py` (stat variants replaced by roster types; `_HIGH` removed), `docs/northstar/research/layer_dynamics/plays_drafts.md` regenerated, README section 3 play table |
| The ground lab's first scene | the same batch spec, section "ground"; `scripts/skilllab/ground/README.md` loses "parked" |
| The diagram requirement | README section 5 (form), then the batch spec |
| Register | `Q-008-03` (the families actually swept; drop "fire-requires-vision flag" and "halfway rule mode", both closed by Q-008-04 (a) and R-004-02); `Q-008-07` closes to (a) once Westley confirms the triangle weighting; `Q-100-01` and `Q-082-06` gain the engine-piece parameter names; a new row for the contact rule under R-096-02 (section F) |
| Stale plan text | `docs/northstar/plans/2026-10-02-skill-lab-cascade.md` section 6 table (emitting 2.0 / 2.0) and `pp_contract.md:115-116` ("lab 2.0") against R-163-01 and the 2026-10-13 pair 2.0 / 3.0 |

Must not change: the bible numbers the lab feeds (R-005-02/04, R-164-01, R-162-01/02, R-163-01's ordering, R-096-08's 200 wu, R-081-01), the draft pass marks of README section 4 and `evidence.Thresholds` (Westley's), `WIN_MARGIN` and the cap (Q-LAB-03 drafts until he sets them), `OM_TP_TARGET_BY_SIGHT` as a switch.

---

## E. CONTRADICTIONS (beyond the two blind spots and the seven gaps)

1. `scripts/skilllab/firing.py:54-58` weights by own damage rate; README section 2 ("Unit type also weights each shot"), section 4 ("Weighted by unit type where types differ"), `toys/layerlab/SPEC.md:167` and Q-008-07 (a) all say type against type.
2. `firing.py:70` tests the cross-layer pair at the base range; `csrc/unit.c:1718` multiplies it by `OM_TP_RANGE_*`; the weighted count mis-reads any LB cell.
3. E-13 R-096-02 (`E-13-movement-and-command.md:49`) plus `csrc/unit.c:1943-1960`: an engaged attack-move group never resumes the march; Westley 2026-10-13 (Q-LAB-03): "unless there's a bug it's not possible for a tie (eventually)". Probes P3 and P6: a tie happens with no bug.
4. `scripts/skilllab/scenes.py` (`placed_scene`, last lines): `decided_by_survivors=True`, `silence_ticks`, `hold_anchor` still set; the ruling retired them.
5. `docs/northstar/plans/2026-10-02-skill-lab-cascade.md` section 6 (emitting seen-from 2.0) and `pp_contract.md:116` ("lab 2.0") against R-163-01 ("by more than it widens how far it sees") and the 2026-10-13 pair.
6. README section 7 gap table lists "Targeting ignores fog and line of sight" and "No layer changes ... same-layer fire only" as open; `csrc/unit.c:1174` (G3), `csrc/tactical_move.c:3132` (G4), `csrc/unit.c:568` (G5), `csrc/fog.c:742` (G6), `fog.c:874` (G7) are built.
7. `scripts/skilllab/batches.py:33-34` (`REACH_NOTE`: "every unit is on layer 0, so the layer settings have no effect in this scene") was written beside the LA/LB/LC tables that then ran; `docs/northstar/research/layer_dynamics/runs/2026-10-06c_layers/layers_run.md` prints the 57 cells with no such line.
8. `scripts/skilllab/timeline.py` ~80: the `"seen"` trigger uses `engine.can_see` (unit sight), so a bait that is pinged-only never springs; R-093-02 counts pings as sight.
9. Register `Q-008-03` candidate (a) lists "fire-requires-vision flag" and "halfway rule mode" as sweep families; Q-008-04 is closed (a) and R-004-02 fixes the halfway rule.
10. `tests/skilllab/integration/test_firing_weighted_real.py:2`: "Asserts only what holds without the side-sight engine rule"; the rule landed (`unit.c:1174`).
11. `scripts/skilllab/mopup.py:1-7` re-orders a side only when "it sees at least one enemy": under side sight a blind side never moves, so the mop-up cannot deliver the ruling's "no units will be left standing around".
12. E-11 R-082-05 ("only the Bombard has an area attack") against `csrc/unit.c:1967-1968`: any type with `aoe_radius > 0` splashes, which `om_roster_register_custom_unit` allows the lab to set; the rule's own text already says "Direction changed 2026-10-13, rewrite pending".

---

## F. OPEN FOR WESTLEY (no rule or quote answers these)

1. The tie under R-096-02 in lab fights: (a) attackers attack-moved singly so the game's own resume rule runs; (b) a lab re-issue to the point every 200 ticks regardless of sight; (c) change R-096-02 for the game so a group resumes after every fight.
2. A unit whose target is outside its arc but turnable (R-100-02 rates): (a) not able until it has turned; (b) able if it can turn within one tick; (c) able if within the arc plus one tick of turning.
3. The type weight's target: (a) the engine's actual target when able, else the nearest able enemy; (b) always the nearest able enemy; (c) the best matchup among able enemies (an upper bound, further from the game).
4. The opening window for C1 and C2: (a) 40 ticks after first contact as the toy used; (b) 100 ticks; (c) both reported, whole-fight beside.
5. Asymmetric vision in the sweep (up differs from down): (a) symmetric only, as Q-005-02 (a); (b) also sweep down at 1.0 with up at 0.125 to 0.5 now that the Interceptor is the named counter; (c) after the symmetric batch is read.
6. The down-side range and damage bonus (firing down longer or harder than on the same layer): (a) out of this batch; (b) one point each at 1.25; (c) a band 1.0 to 2.0.
7. The cone's share of damage and whether the cone replaces or adds to the direct hit (Q-082-06 does not say): (a) the cone is the attack, share 1.0 on every unit in it, capped as ALG-61; (b) direct hit plus a cone at a share; (c) per type.

---

## G. CONFIDENCE

- A1 as the definition: high. Rests on the engine's own gates read at `unit.c:1716-1719`, `1165-1180`, `2140`, `fog.c:486-503` and the probes reading 1279.8 against the engine's 1267.0, 0/0 then 5/0 on the Bombard pair. Would change my mind: an engine gate I did not find that the fire pass applies and A1 does not (the parity assertion is the detector).
- Type-against-type weighting: medium-high. Rests on the toy's `firing_weight` (`SPEC.md:167`), the trap at transcript line 704 and 712, Q-008-07 (a). Would change: Westley reading C2 and wanting magnitude in it.
- The crossing arithmetic and the vision points: medium. Rests on one probe (4 fights per point, two seeds) and the sensor/range table of R-082-01; the refine band is where a full scan may move it. Would change: scans at 10 replicates placing the crossing elsewhere.
- The contact finding: high. Two probes and the rule text agree (R-096-02, `unit.c:1943-1960`). Would change: nothing short of a different engine path for attack-move groups that I missed.
- Emitting as capped and inert at base vision 0.5: high (`fog.c:749`, P5). Would change: a cap removal.
- The stale-doc and contradiction rows: high, each is a quoted line.
- The ground scene: low-medium. Rests on one test's coordinates on seed 11 and the stage-2 spec; nothing has fought on ground yet, and the slope-divisor band is my draft.
