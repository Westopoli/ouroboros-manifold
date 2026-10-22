# E-10 — Missions

## Definition-completeness gate (run 2026-09-10, extended 2026-10-02)

| Check | Result |
|---|---|
| Every story has at least one Given/When/Then rule with concrete values | S-072 to S-080: yes, 9 stories, 48 rules, numbers from `algorithms.md` ALG-54 through ALG-59 and config tables. S-210 to S-214: 5 stories, 22 rules, design decided 2026-10-02 and not scheduled for building; where Westley has not given a number the rule carries a flag instead. |
| Every input listed with range and rejection behavior | Yes, see Inputs. |
| Every output listed with where it is observable | Yes, see Outputs. |
| Implied-but-unstated behavior turned into flags | 1 open flag on S-072 to S-080, Q-080-03, and 15 on S-210 to S-214 (Q-210-03, Q-210-04, Q-210-06, Q-211-02 to Q-211-04, Q-212-04, Q-212-05, Q-173-01, Q-214-02), plus Q-159-12 and Q-177-07 carried from E-22. |
| Every visible-surface story has a reference | **No.** S-079 (briefing and debrief screens) has a visible surface and no reference. |
| "Obviously working" in 60 seconds named | Yes, see below. |

**Gate verdict: not passed.** Blocked on Q-080-03 (S-080), on the open flags of S-210 to S-214, and on one missing reference (S-079). S-072 to S-078 have no open flags; gate to be rerun. Missions run 30 to 60 minutes; `om_mission_get_time_limit` computes the R-076-01 limit from the R-076-02 minutes table (clock rewire landed, 53101e2).

## Purpose

A mission is the one place the player touches the galaxy. The civilization looks at where the world hurts, at who this commander is, and at what the player likes to do, and hands down orders: hold this region, break this siege, take that one back, get these people out. Ten archetypes, each a different military problem, each triggered only by something really happening in the simulation. The player reads the briefing and accepts; there is no shopping for forces. Each side also starts with a base of operations whose kind follows from the archetype and the simulation (S-210), fights over resources that are as scarce or as plentiful as the simulation's situation says (S-211), and can lose that base without the mission always ending (S-212). The mission plays in real time to a deadline. At the end, how well it went and how much of the force came home become one of five outcome bands, and the band becomes proportional changes to the mission region's numbers. That is how a battle becomes history.

Force size is set by parity: the enemy's strength comes from the simulation, the player's is a fraction of it that shrinks as the civilization weakens, never below 0.75, so a skilled commander can always win.

## Obviously working in 60 seconds

Put the player's frontier under a telegraphed attack and run the generator. The candidate pool contains (frontier, defensive_stand); its urgency is high, so it is in the top-5 draw pool, and the weighted draw (R-072-05) picks it on the example seed; another seed may draw a different candidate from the pool. The briefing has three sections and names the attacker. Forces: an enemy force worth the attacker's budget × 300 in power, a player force at parity 0.90 of that for capacity 0.5 on medium. Play it out: hold the zone for the required time, lose a third of the force. Final score 0.75 · 1.0 + 0.25 · 0.67 = 0.917, band total_success, region military +15 percent of its deficit, tension −10 percent of current. Same seed, same mission, same forces.

Decided, not built (S-210 to S-214): in an Assault the player's base is a forward base and is its original main base; let the enemy occupy it and a result that would classify as strong_success is classified partial_failure, while a held expansion becomes the base and the mission goes on.

## Stories

### S-072 — Orders come from where the world hurts
As a commander, I want my missions to come from real trouble in the galaxy, weighted toward where I belong and what I do best, so that every order has a reason and the world does not revolve around me.

Rules
- R-072-01  Given the player's regions and every region adjacent to them, When the candidate pool is built, Then each (region, archetype) pair whose trigger condition holds enters the pool; a region with no trigger produces nothing.
- R-072-02  Given a candidate, When urgency is computed, Then urgency = clamp(0.4 · deficit + 0.4 · conflict + 0.2 · chain, 0, 1), where deficit = mean of (100 − military, 100 − economy, 100 − stability)/100, conflict = clamp(min(1, max hostile neighbor military/70) + 0.5 · min(1, 0.5 · recent attacks + Σ attack budget/600) + 0.3 · min(1, 0.5 · adjacent regions lost), 0, 1), chain = min(1, 0.3 · recent revolt events in the region).
- R-072-03  Given a candidate, When relevance is computed, Then relevance = clamp(0.4 · lineage + 0.3 · proximity + 0.3 · fit, 0, 1), lineage = 1.0 if a lineage member lives in the region, 0.5 if the lineage ever operated there, else 0; proximity = 1 − hops from the lineage home/5 (capped at 5 hops); fit = min(1, times the lineage has run this archetype/3).
- R-072-04  Given a candidate, When preference is computed, Then it is 0.1 for an archetype the player marked rare, else the player's weight, default 0.5.
- R-072-05  Given scored candidates, When one is selected, Then score = 0.5 · urgency + 0.3 · relevance + 0.2 · preference, the top 5 by score form the draw pool, and one weighted draw proportional to score picks the mission.
- R-072-06  Given a region with stability 15 and an active revolt chain (two revolt events) under attack by a neighbor at military 80, When scored, Then urgency ≥ 0.8 and it beats any quiet region regardless of relevance and preference (Q-072-02, Architect 2026-10-19).
- R-072-07  Given no candidate in the pool, When selection runs, Then the sim runs another 20-tick jump and rebuilds the pool, up to 5 times; if the pool is still empty, the mission is a Defensive Stand on the player's weakest region: the player region with the lowest stability composite (ALG-09, the value E-10 reads everywhere as "stability"), ties to the lowest region index. (Q-072-01, Westley 2026-09-13 and 2026-09-30.)
- R-072-08  Given the fallback of R-072-07, When its forces are composed, Then the enemy is the non-player faction nearest the region by connection hops (ties to the faction with the highest total military across its regions, then the lowest faction id); its power P is that faction's strongest region's military × 2000 (the R-074-01 default form), raised if needed so the enemy fields at least one unit; the player's force is P · parity as in R-074-04; and the fallback being reached at all is a simulation-health warning (`quiet_world` in the mission frame), because a tuned galaxy always has an attack somewhere. (Westley 2026-09-30: "this situation should never happen if we tune the simulation right.")

Inputs: world; registry; event, action, conquest logs; ledger; onboarding preferences.
Outputs: mission setup record (region, archetype, trigger context, scores) in the save file and T1 trace.
Open flags: none.

### S-073 — Ten kinds of trouble

Direction changed 2026-10-02, rewrite pending: the layout library of R-073-03 stays, and terrain-first generation is added to it, so the terrain engine accounts for the layouts (E-17 S-166 R-166-03, S-191 R-191-10: the layout calls for places and the landscape engine must produce them, and the archetype also biases the landform). Suppression and Counterinsurgency no longer have a small canvas: they take one drawn from medium and large, with a compact play area (E-17 R-188-06). The rules below are what the game does today.
As a commander, I want every mission to be a recognizable military situation with its own trigger, shape, and map, so that I learn the grammar of orders and still never see the same mission twice.

Rules
- R-073-01  Given the launch library, When loaded, Then it contains exactly these archetypes with these triggers, base canvas, objective types, and transfer outcomes, and a contract test checks the table:

| Archetype | Trigger | Canvas | Primary objective | Region transfers to player on |
|---|---|---|---|---|
| Defensive Stand | player region targeted by an enemy attack this window | medium | hold_zone | never |
| Siege Breaking | player region with a hostile neighbor above military 50, held long enough, own military ≤ 40 or economy ≤ 40 | large | destroy_targets | never |
| Reconquest | region the player lost by conquest this window | medium | hold_zone or destroy_targets | total, strong, partial success |
| Assault | hostile neighbor region the player's faction has scored as an attack target | large | destroy_targets | total, strong success |
| Suppression | region held by a breakaway created this window, adjacent to the player | small | eliminate_force | total, strong success |
| Multi-Front Defense | player region attacked by two or more factions this window | large | hold_zone ×2 | never |
| Interception | enemy attack declared against a player region, force in transit | medium | destroy_targets | never |
| Rear Guard / Evacuation | player region with military, economy, and stability all collapsed | medium | escort_to_extraction | never |
| Containment | hostile faction expanding along the player's border, two or more colonizations | large | hold_zone across a line | never |
| Counterinsurgency | player region with an active revolt chain | small | eliminate_force without destroying the region | never |

- R-073-02  Given an archetype, When its forces are allocated, Then its asset profile (ratio per unit type) is read from the library, not hard-coded.
- R-073-03  Given an archetype, When its map is generated, Then its compatibility filters select layouts from the shared library (E-17).
- R-073-04  Given "inheritance" framing, When the ledger finds a lineage connection to the mission region, Then the briefing notes it and nothing mechanical changes.

Inputs: library tables.
Outputs: loaded archetype table; contract test.
Open flags: none. Full per-archetype prose from the Stage 1 KEEP rows (A-441 through A-450) moves into the library's archetype entries in E-21. See also: S-210 (the base kind each archetype carries), S-214 (the canvas for 4 to 6 players), E-17 R-191-10.

### S-074 — You get what the civilization can spare
Flag closed, rule text pending: Q-074-01, power is (HP * base_damage) / attack_interval, normalized so Vanguard = 100.0. The rule below is what the tests read today.
As a commander, I want my force sized to the enemy and shaved by how weak my civilization is, but never so small I cannot win, so that scarcity is the difficulty and the enemy is never simply stronger.

Rules
- R-074-01  Given an archetype driven by an attack, When enemy power is set, Then it is the attacker's committed budget × 300; given an insurgent archetype (suppression, counterinsurgency), Then it is a rolled insurgent military × 2000, where the roll is uniform in a range interpolated by population from [20, 50] at population ≤ 25 to [40, 70] at ≥ 70; otherwise it is the region's military × 2000.
- R-074-02  Given the mission region's capacity c in [0, 1], When parity is computed, Then base parity is piecewise linear through (0, 0.80), (0.3, 0.85), (0.5, 0.90), (0.7, 0.95), (1.0, 1.00).
- R-074-03  Given difficulty easy, When parity is computed, Then it is max(base, 0.95); hard: min(base, 0.85); medium: base; and never below 0.75.
- R-074-04  Given the enemy force total power P, When the player's force is filled, Then its budget is P · parity, filled per unit type in descending profile ratio, adding units while a unit's power ≤ 1.15 × remaining budget.
- R-074-05  Given capacity below 0.4, When shortfall applies, Then 20 percent of the player's units are removed, spread across types from the most numerous, never below 1 unit, and the briefing names what could not be spared.
- R-074-06  Given a unit's power, When read, Then it comes from the interim total-strength measure [Q-074-01].

Inputs: trigger context; region fields; difficulty; unit roster.
Outputs: force compositions (both sides) in the mission setup; briefing assets section.
Open flags: none here. See also: S-211 and Q-211-02 (how a shortfall of units sits beside the player always having the means to do the mission).

### S-075 — Hold, destroy, escort, survive, eliminate

Direction changed 2026-10-02, rewrite pending: a base is occupied, not destroyed, and a side that holds an expansion or forward works falls back to it, so a fallen base does not by itself end the mission (S-212). The rules below are what the game does today.
As a commander, I want a mission to have one primary objective I can see progressing and up to three secondary ones, so that I always know what done looks like.

Rules
- R-075-01  Given a mission, When objectives are built, Then there is exactly one primary objective and 0 to 3 secondary ones, weights summing to 1.0, the primary carrying at least 0.6.
- R-075-02  Given hold_zone, When evaluated per tick, Then the hold timer advances only while no enemy unit is inside the zone radius; required = 10 minutes of battle time (12,000 base ticks, Westley 2026-09-30; it was the whole time limit, so the zone could only complete on the final tick); completion = elapsed/required, and the mission ends on completion (R-075-07).
- R-075-03  Given destroy_targets, When evaluated, Then completion = destroyed designated targets/total.
- R-075-04  Given escort_to_extraction, When evaluated, Then completion = escort units that reached the extraction point alive/total escort units.
- R-075-05  Given survive_duration, When evaluated, Then completion = elapsed/required, and 0 if every player unit is dead before the time.
- R-075-06  Given eliminate_force, When evaluated, Then completion = enemy HP destroyed/initial enemy HP.
- R-075-07  Given the mission, When it ends, Then it ends on the first of: every primary objective complete or failed; the time limit reached; the player's force eliminated.

Inputs: objective specs; tactical state per tick.
Outputs: per-objective completion in the tick delta; HUD objective list; mission result.
Open flags: none.

### S-076 — The clock
As a commander, I want a deadline that tightens when the situation is urgent, so that time is a pressure and never a score.

Rules
- R-076-01  Given an archetype base time B in tactical ticks and urgency u, When the limit is set, Then limit = max(B · (1 − 0.2 · u), 0.6 · B).
- R-076-02  Given base times, When read, Then B by archetype is: siege breaking 60, multi-front defense 60, assault 52.5, containment 52.5, reconquest 45, defensive stand 37.5, interception 37.5, counterinsurgency 37.5, suppression 30, rear guard/evacuation 30 minutes of battle time (Q-076-01 and Q-076-02, Westley 2026-09-29); the R-076-01 floor of 0.6·B stands, so the shortest possible mission is 18 minutes.
- R-076-03  Given the deadline passes, When the mission ends, Then the current objective completion values are final; finishing early never raises the score.

Inputs: archetype; urgency.
Outputs: time limit in the mission setup; HUD clock.
Open flags: none.

### S-077 — Five ways it can go

Direction changed 2026-10-02, rewrite pending: once the player's side has lost its original main base, the best band it can get is partial_failure (S-212). The rules below are what the game does today.
As a commander, I want the result to be a spectrum weighing what I achieved and who I brought home, judged by what is reasonable for that kind of mission, so that a costly win and a clean win are not the same.

Rules
- R-077-01  Given objective score o (weighted completion, failed objectives count 0) and retention r (surviving unit power/deployed power, capped at 1, with damaged units counted by HP fraction), When the final score is computed, Then final = 0.75 · o + 0.25 · r.
- R-077-02  Given the archetype's thresholds [t1, t2, t3, t4], When classified, Then final < t1 is total_failure, < t2 partial_failure, < t3 partial_success, < t4 strong_success, else total_success; thresholds: defensive_stand, siege_breaking, suppression, interception, containment, counterinsurgency [0.20, 0.40, 0.60, 0.80]; reconquest and assault [0.25, 0.45, 0.65, 0.82]; multi_front_defense [0.15, 0.35, 0.55, 0.75]; evacuation [0.30, 0.50, 0.65, 0.80].
- R-077-03  Given the mission ends, When the commander's unit is dead, Then commander fate is killed; when the commander's unit ended alive but below 30 percent HP, Then fate is wounded (cosmetic and chronicle only, no mechanical impact); else fate is survived.
- R-077-04  Given the result, When shown, Then the band is revealed only at mission end, never during play.
- R-077-05  Given a mission starts, When the player's force is spawned, Then the player assigns the commander to one of their deployed units and may reassign them to another unit during the mission; the assigned unit's id is held in mission state for the whole mission; R-077-03 reads commander fate from this unit. The commander's chance-based fate — probability of being wounded or killed rising with fire the assigned unit takes, not the unit's own survival — is to be determined after the MVP.

Inputs: objectives; unit store; initial power; commander unit id.
Outputs: mission result (band, objective score, retention, per-objective, commander fate, ticks elapsed) in the save file and debrief.
Open flags: none here (the retention question is S-212's, Q-212-04).

### S-078 — A battle becomes history
Flag closed, rule text pending: Q-078-01, the targets `home` and `exposed` stay and both resolve to the mission region, so consequences apply to the mission region itself. The rule below is what the tests read today.
As a commander, I want the outcome to change the region in proportion to how it was doing, so that saving a desperate region matters more than polishing a strong one.

Rules
- R-078-01  Given the archetype's consequence table row for the band, When applied, Then each delta is either deficit form, (100 − current) · pct/100, or current form, current · pct/100, applied to the named target regions and clamped to [0, 100].
- R-078-02  Given defensive_stand total_success on a region with military 20 and tension 50, When applied, Then military +12.0, tension −5.0, economy −2 percent of current.
- R-078-03  Given the same band on military 80, When applied, Then military +3.0.
- R-078-04  Given a transfer band for the archetype (S-073 table), When applied, Then the region's owner becomes the player's faction with held-since reset and edges updated (E-03 R-024-03).
- R-078-05  Given the player refuses the mission, When resolved, Then the band is refusal, no force is deployed, and the region's tension rises by 8 percent of its deficit.
- R-078-06  Given the applied deltas, When the time jump starts, Then the resulting events carry the mission-consequence flag for the chronicle (E-09).
- R-078-07  Given a target of `adjacent_player`, When applied, Then the delta applies to every player-owned neighbor of the mission region.

Inputs: mission result; consequence tables; world.
Outputs: applied deltas in the T1 trace; region fields; ownership.
Open flags: none here. See also: S-212 R-212-05 (the region follows whoever holds the base at the end, superseding R-078-04's transfer band).

### S-079 — Orders, not menus
As a commander, I want to receive my orders as a superior officer would give them, three parts and no haggling, and to see afterward how it went and what it cost, so that the civilization feels like a chain of command.

Rules
- R-079-01  Given a mission setup, When the briefing is assembled, Then it has exactly Situation, Objective, and Assets, in that order, each from authored fragments with slots filled from the trigger context, ledger, and force composition; Assets states parity in prose and names shortfall types.
- R-079-02  Given the briefing, When shown, Then the only controls are Accept and Refuse; there is no loadout or force editing.
- R-079-03  Given the mission ends, When the debrief is shown, Then it shows the band, the objectives with completion, force retention, and commander fate.
- R-079-04  Given any briefing or debrief text, When rendered, Then it contains no raw field numbers.

Inputs: mission setup; result.
Outputs: briefing and debrief screens.
Open flags: none beyond the missing reference. Reference required: `references/E-10/notes.md`, missing. The briefing states each side's base kind and the resource situation inside Situation (Westley, 2026-10-07), and the economy settings are chosen live, per setting, so Accept and Refuse stay the only controls.

### S-080 — Difficulty is scarcity, not stronger enemies
As a commander, I want hard mode to give me less to work with, never to give the enemy better units, so that I always lose to my own limits.

Rules
- R-080-01  Given any difficulty, When forces are generated, Then both sides draw from the same unit profiles; no stat differs by difficulty.
- R-080-02  Given easy, medium, hard, When a mission is generated, Then difficulty sets parity (R-074-03), time width, resource generosity, and the complication odds, and how fast those compress across generations [Q-080-03: the values].
- R-080-04  Given a mission is generated, When the complication roll fires (about 1 percent of missions, a celebrated rarity), Then one complication is fixed at generation and never live: a report, a status, or an expected friendly asset turns out false mid-mission (Crossed Signals); it never changes an enemy stat, is never foreshadowed, and at most one fires per mission; the debrief names it apart from the tallies and the chronicle gives it one entry when it changed the region's fate.
- R-080-03  Given a mission preference marked rare, When the world has no other viable candidate, Then the rare archetype can still be chosen (preference 0.1, never 0).

Inputs: difficulty; onboarding.
Outputs: parity; candidate scores.
Open flags: Q-080-03 (the compression values; Westley 2026-09-30: stays open past the MVP, so R-080-02's compression is a no-op until it closes and no piece builds it).
The full difficulty ramp ships. The complication, Crossed Signals, was chosen through the options pass, `docs/northstar/research/options/complications/`. The host owns difficulty and preferences (single-player team model). Difficulty acts on the player's side through parity only; the situation's slant (S-211) and the enemy's prosperity (E-14 S-215) are separate (Westley, 2026-10-07).

### S-210 — Each side starts from the base its situation calls for
As a commander, I want the kind of base each side begins with to follow from the kind of mission and from how far the region lies from the civilization's supply, so that a defender, an attacker and a relief force each fight from a place that makes sense.

Status: design decided 2026-10-02, not scheduled for building.

Rules
- R-210-01  Given a mission, When its setup is built, Then each side is given one base of operations at the start, and the kind of base is decided by the mission archetype (S-073) alone, from the table below; it does not change with how far into foreign ground the mission lies (Westley, 2026-10-06).
- R-210-02  Given an archetype, When its entry is read, Then it carries a base kind for each side, read from the library as the asset profile is (R-073-02) and not hard-coded. The approach is decided (Westley, 2026-10-02: "B1+2") and the table below, taken from `docs/northstar/research/economy_design/base_and_objective_options.md` part B1, stands as written (Westley, 2026-10-02: "looks good, no changes needed").

| Archetype | Player's base | Enemy's base |
|---|---|---|
| Defensive Stand, Multi-Front Defense | home city, generating on site | forward base, supplied from elsewhere |
| Siege Breaking | relief camp outside, supplied; the city inside is the objective | siege camp |
| Assault, Reconquest | forward base, supplied | the city or fortress being taken |
| Containment, Interception | field camp on the enemy's path | column or staging camp |
| Suppression, Counterinsurgency | garrison in a city | hidden cells among the settlements |
| Rear Guard / Evacuation | the place being left | pursuing forward base |

- R-210-03  Given a side that the archetype makes the attacker, When its base is given, Then it is a forward base from which the side produces; supply lines, the shipments of E-22 S-176, are not an attacker-only rule and either side may have them (Westley, 2026-10-07) [Q-210-03: which side attacks in each archetype; Westley, 2026-10-07: named per mission type by him].
- R-210-04  Given the base a side is given at the start, When the mission runs, Then that base is the side's original main base for S-212, and a forward base given to an attacker by R-210-03 is its original main base (Westley, 2026-10-02: "attackers get a *forward* base from which they produce and recieve resources from supply lines"); expansions and forward works built later are not for the beta only mission types in which the sides start with a base launch, and there the base a side starts with is its original main base (Westley, 2026-10-07; which types launch is Q-210-07).

Inputs: archetype library; the mission's region.
Outputs: each side's base kind and original main base in the mission setup.
Where a base stands is whatever the terrain gives (E-17 R-166-03).

### S-211 — The resources fit the situation
As a commander, I want the resources on the map to be scarce or plentiful as the simulation's situation says, tilted toward the side with the better position, and never so thin that I cannot do the job, so that the economy is part of the mission and never a trap.

Status: design decided 2026-10-02, not scheduled for building.

Rules
- R-211-01  Given a mission, When its resources are set, Then they are limited or abundant consistent with the situation the simulation gives the mission's region, and slanted by it (a defender has the better position); the richness is derived from the simulation's existing region fields and composites (Westley, 2026-10-06).
- R-211-02  Given any mission, When it is generated, Then the player has the means to accomplish it even when it is hard (Westley, 2026-10-02: "the player always has the means to do the mission") [Q-211-02: how the means are guaranteed; Westley wants option (a), a generator check, written up before deciding].
- R-211-03  Given a mission, When base, objective and significant resources are placed, Then they are usually three separate places and not always, and the significant resources sit opposite the objective, so a side picks one or fights for both (E-22 S-177 holds the rule; E-17 places them) (left to the generator, Westley, 2026-10-07).
- R-211-04  Given the final score, When the result is classified (S-077), Then the resources are not scored separately: a side that ignores them is overrun unless it rushes and finishes fast.

Inputs: the region's simulation situation; the archetype; difficulty.
Outputs: the resource situation in the mission setup, for the briefing to state inside Situation.
Open flags: Q-211-02.

### S-212 — When a base falls
As a commander, I want losing my main base to cost me the result but not always the fight, so that I can fall back to what I still hold and save something.

Status: design decided 2026-10-02, not scheduled for building. Occupying and retaking a base is E-22 S-178's; this story holds what it does to a mission's end and result.

Rules
- R-212-01  Given the player's side has lost its original main base (S-210), When the result is classified (R-077-02), Then the best band it can get is partial_failure: a final score that would classify higher is classified partial_failure (Westley, 2026-10-02: "at the point they've lost their original main base it's partial failure at maximum"). The cap concerns a forward base only when it is the side's original main base (R-210-04), never forward works.
- R-212-02  Given a side loses its base of operations while it holds an expansion or forward works, When the loss is applied, Then that expansion or forward works becomes its base of operations and the mission goes on (E-22 S-178, S-175).
- R-212-03  Given a side loses its base of operations and holds no expansion and no forward works, When the loss is applied, Then the mission ends for that side and is scored (Westley, 2026-10-06; to be checked archetype by archetype against R-075-07 and S-077).
- R-212-04  Given a side has lost its original main base and retakes it before the mission ends, When the result is classified, Then the cap of R-212-01 lifts (Westley, 2026-10-06).
- R-212-05  Given the mission ends while a base is held by the other side, When the region's ownership is set (R-078-04), Then the region follows the side that holds the base at the end (Westley, 2026-10-06); the transfer column of R-073-01 and R-078-04 are superseded and are to be rewritten to follow base ownership.
- R-212-06  Given the end conditions of R-075-07, When the player's force is judged eliminated, Then it is eliminated when no units remain; buildings do not keep a side alive and any unit that remains does (Westley, 2026-10-07).
- R-212-07  Given workers and units made during the mission, When retention is computed (R-077-01), Then every unit made counts in both deployed power and surviving power (Westley, 2026-10-07).

Inputs: base ownership during the mission (E-22 S-178); the result of S-077.
Outputs: the band cap and the mission end in the mission result.
Open flags: none.

### S-213 — The technology a mission starts with
As a commander, I want the technology each side starts a mission with to follow, only slightly, from how advanced the civilization is, so that a mission feels of its time and there is still room to climb during it.

Status: design decided in part 2026-10-02, not scheduled for building. What technology does is E-22 S-173 (Q-159-12).

Rules
- R-213-01  Given a mission, When its setup is built, Then each side's starting technology level is derived from the simulation's technology level (E-06 S-045), and only slightly [Q-173-01: how slight, and how the faction's 0 to 100 number maps to the era's levels].
- R-213-02  Given an era with a wide range of technology levels (for example 1 to 5), When a normal timed single match is played, Then there is time to go up one or two levels, as in a StarCraft 2 tech-up (Westley, 2026-10-02), so the starting level shifts a mission only a little.
- R-213-03  Given a technology level, When a mission uses it, Then what it does is E-22 S-173 and nothing in this story decides it.

Inputs: the faction's technology level (E-06 S-045); the era pack's range of levels.
Outputs: each side's starting technology level in the mission setup.
Open flags: Q-173-01, Q-159-12.

### S-214 — More players, a bigger fight
As a member of a team of 2 or 4, I want the map, the enemies and the resources to grow with the number of players, so that each of us is a sub-commander and each pair a sub-civilization inside a larger war.

Status: design decided 2026-10-02, not scheduled for building. The team sizes and the sub-civilization pairing are E-19 S-159's, and teams of 6 are a desired future feature (E-19 S-241).

Rules
- R-214-01  Given a mission with 4 to 6 players, When the canvas is chosen (E-17 S-116), Then its dimension is 64,000 wu (Westley, 2026-10-02: "64k if there's 4-6 players").
- R-214-02  Given a mission with fewer than 4 players, When the canvas is chosen, Then it keeps the sizes of the S-073 table.
- R-214-03  Given more players on a team, When the mission is built, Then there are more enemies and more to do, and the player units rise with the players and are never fewer than in single player (E-19 R-141-02) Enemy force and the amount to do scale in step with the number of pairs (Westley, 2026-10-06) the team has one shared objective and parity, and the enemies scale (Westley, 2026-10-07).
- R-214-04  Given more players on a team, When the resources are set (S-211), Then there are more of them, in step with the number of pairs (Westley, 2026-10-06).

Inputs: the team's player count (E-19 S-159).
Outputs: canvas size, enemy forces and resources in the mission setup.
Open flags: none.

## Inputs

| Input | Source | Range | Rejection |
|---|---|---|---|
| World, registry, logs | E-02 through E-08 | | |
| Ledger, lineage id | E-08 | | missing lineage gives relevance 0 |
| Onboarding | E-08 | difficulty; per-archetype preference or rare | invalid rejected at save |
| Archetype library | E-21 | 10 archetypes with the S-073 table | malformed fails load |
| Unit roster | E-11 | the era's roster with power | |
| Accept or refuse | Player | | |
| Team's player count | E-19 S-159 | 2 or 4 (6 is a desired future feature, E-19 S-241) | |
| Technology level of the faction | E-06 S-045 | 0 to 100 | |
| Economy settings (doctrine, dial, unit-mix toggles) | Player, live, per setting (E-19 S-159, E-22 S-180) | | |
| Enemy foresight | Difficulty (E-22 S-181) | | |
| Tactical result | E-11 through E-15 | objectives, unit store, commander unit | |

## Outputs

| Output | Observable where |
|---|---|
| Mission setup (region, archetype, forces, objectives, time limit, map params, strongpoints (E-15 S-218), each side's base kind and original main base, resource situation, starting technology) | Save file; briefing; T1 trace |
| Mission result | Save file; debrief; chronicle input |
| Applied consequences and transfer | T1 trace; region fields; world view |
| Refusal | Save file; region tension |

## Invariants

- A mission is generated only from a fired trigger.
- Parity never below 0.75.
- Exactly one primary objective; weights sum to 1.0.
- Band determined once, at mission end.
- Consequence deltas never leave [0, 100].
- Same seed, same mission and forces.
- Every side has exactly one base of operations at the start, and it is that side's original main base.
- A player's side that has lost its original main base never classifies above partial failure.

## Scale requirements

Confirmed by Westley, 2026-09-14 (never loosened by Agora; a miss is escalated): candidate pool and scoring over 60 regions × 10 archetypes in under 20 ms; force allocation for 100-unit forces in under 5 ms.

## Look and behavior references

`references/E-10/notes.md`, missing: briefing and debrief screens (2 to 5 screenshots from games whose orders screens read the way Westley wants).

## Ways this could be wrong

- Pool includes regions two hops away, or excludes adjacent enemy regions, so assault never triggers.
- Weighted draw uses rank instead of score.
- Parity computed from the faction's capacity instead of the region's.
- Retention computed from unit count instead of power.
- Band thresholds applied inclusively.
- Deficit and current forms swapped for negative deltas.
- Transfer applied on partial success for assault.
- Time limit on a minutes-scale table (3 to 4.5 minutes, or seconds) instead of 30 to 60 minutes.
- Refusal deploys a force.
- The partial-failure cap applied to the enemy's side, or applied when only an expansion or forward works was lost.
- Base kind changed by how far into foreign ground the mission lies.
- An attacker given a home city instead of a forward base.
- Resources scored as a separate objective.
- The 64,000 wu canvas used for matches of fewer than 4 players, or today's canvas used for 4 to 6.
- Starting technology copied from the simulation's level instead of derived only slightly.

## Open ambiguity flags

Q-080-03, Q-159-12, Q-177-07, Q-210-03, Q-210-04, Q-210-06, Q-211-02 to Q-211-04, Q-212-04, Q-212-05, Q-173-01, Q-214-02. Details in `docs/northstar/ambiguity_register.md`.

## Depends on

- E-02 through E-07 (world state and logs that trigger missions; E-06 S-045 for the technology level).
- E-08 Generational structure (lineage, onboarding, chapter loop).
- E-09 Chronicle (consequence flags).
- E-11 Units (roster, power, HP), E-13 Movement, E-15 Reinforcement structures (strongpoints), E-17 Map generation (mission map and canvas), E-16 Client (briefing, HUD objectives, debrief).
- E-19 S-159 (team sizes, the paired mode) and E-22 Economy and bases (S-175 expansions and forward works, S-176 shipments, S-177 bases, resources and the situation, S-178 when a base falls, S-173 technology, S-181 the enemy's economy).
- E-21 Offline AI pipeline (archetype and briefing fragment libraries).
