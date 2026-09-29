# E-10 — Missions

## Definition-completeness gate (run 2026-09-10)

| Check | Result |
|---|---|
| Every story has at least one Given/When/Then rule with concrete values | Yes, 9 stories, 44 rules, numbers from `algorithms.md` ALG-54 through ALG-59 and config tables. |
| Every input listed with range and rejection behavior | Yes, see Inputs. |
| Every output listed with where it is observable | Yes, see Outputs. |
| Implied-but-unstated behavior turned into flags | 7 new flags, Q-072-01, Q-074-01, Q-076-01, Q-077-01, Q-078-01, Q-079-01, Q-080-01. |
| Every visible-surface story has a reference | **No.** S-079 (briefing and debrief screens) has a visible surface and no reference. |
| "Obviously working" in 60 seconds named | Yes, see below. |

**Gate verdict: not passed.** Blocked on 7 open flags and one missing reference. Q-076-01 (the live time limits are 250 to 450 tactical ticks, 12 to 22 seconds, because a second config table overrides the first) is a real defect, not a design question, but it needs Westley to confirm the intended minutes.

## Purpose

A mission is the one place the player touches the galaxy. The civilization looks at where the world hurts, at who this commander is, and at what the player likes to do, and hands down orders: hold this region, break this siege, take that one back, get these people out. Ten archetypes, each a different military problem, each triggered only by something really happening in the simulation. The player reads the briefing and accepts; there is no shopping for forces. The mission plays in real time to a deadline. At the end, how well it went and how much of the force came home become one of five outcome bands, and the band becomes proportional changes to the mission region's numbers. That is how a battle becomes history.

Force size is set by parity: the enemy's strength comes from the simulation, the player's is a fraction of it that shrinks as the civilization weakens, never below 0.75, so a skilled commander can always win.

## Obviously working in 60 seconds

Put the player's frontier under a telegraphed attack and run the generator. The candidate pool contains (frontier, defensive_stand); its urgency is high; it is selected. The briefing has three sections and names the attacker. Forces: an enemy force worth the attacker's budget × 300 in power, a player force at parity 0.90 of that for capacity 0.5 on medium. Play it out: hold the zone for the required time, lose a third of the force. Final score 0.75 · 1.0 + 0.25 · 0.67 = 0.917, band total_success, region military +15 percent of its deficit, tension −10 percent of current. Same seed, same mission, same forces.

## Stories

### S-072 — Orders come from where the world hurts
As a commander, I want my missions to come from real trouble in the galaxy, weighted toward where I belong and what I do best, so that every order has a reason and the world does not revolve around me.

Rules
- R-072-01  Given the player's regions and every region adjacent to them, When the candidate pool is built, Then each (region, archetype) pair whose trigger condition holds enters the pool; a region with no trigger produces nothing.
- R-072-02  Given a candidate, When urgency is computed, Then urgency = clamp(0.4 · deficit + 0.4 · conflict + 0.2 · chain, 0, 1), where deficit = mean of (100 − military, 100 − economy, 100 − stability)/100, conflict = clamp(min(1, max hostile neighbor military/70) + 0.5 · min(1, 0.5 · recent attacks + Σ attack budget/600) + 0.3 · min(1, 0.5 · adjacent regions lost), 0, 1), chain = min(1, 0.3 · recent revolt events in the region).
- R-072-03  Given a candidate, When relevance is computed, Then relevance = clamp(0.4 · lineage + 0.3 · proximity + 0.3 · fit, 0, 1), lineage = 1.0 if a lineage member lives in the region, 0.5 if the lineage ever operated there, else 0; proximity = 1 − hops from the lineage home/5 (capped at 5 hops); fit = min(1, times the lineage has run this archetype/3).
- R-072-04  Given a candidate, When preference is computed, Then it is 0.1 for an archetype the player marked rare, else the player's weight, default 0.5.
- R-072-05  Given scored candidates, When one is selected, Then score = 0.5 · urgency + 0.3 · relevance + 0.2 · preference, the top 5 by score form the draw pool, and one weighted draw proportional to score picks the mission.
- R-072-06  Given a region with stability 15 under attack by a neighbor at military 80, When scored, Then urgency ≥ 0.8 and it beats any quiet region regardless of relevance and preference.
- R-072-07  Given no candidate in the pool, When selection runs, Then [Q-072-01].

Inputs: world; registry; event, action, conquest logs; ledger; onboarding preferences.
Outputs: mission setup record (region, archetype, trigger context, scores) in the save file and T1 trace.
Open flags: Q-072-01 (what happens when nothing in the galaxy triggers any archetype).

### S-073 — Ten kinds of trouble
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
Open flags: none. Full per-archetype prose from the Stage 1 KEEP rows (A-441 through A-450) moves into the library's archetype entries in E-21.

### S-074 — You get what the civilization can spare
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
Open flags: Q-074-01 (the power-rating currency is deferred, A-279; what interim measure sizes forces).

### S-075 — Hold, destroy, escort, survive, eliminate
As a commander, I want a mission to have one primary objective I can see progressing and up to three secondary ones, so that I always know what done looks like.

Rules
- R-075-01  Given a mission, When objectives are built, Then there is exactly one primary objective and 0 to 3 secondary ones, weights summing to 1.0, the primary carrying at least 0.6.
- R-075-02  Given hold_zone, When evaluated per tick, Then the hold timer advances only while no enemy unit is inside the zone radius; completion = elapsed/required.
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
- R-076-02  Given base times, When read, Then they are the minutes in the table [Q-076-01: the bible's table (3 to 4.5 minutes) is overridden in config by 250 to 450 ticks, 12 to 22 seconds].
- R-076-03  Given the deadline passes, When the mission ends, Then the current objective completion values are final; finishing early never raises the score.

Inputs: archetype; urgency.
Outputs: time limit in the mission setup; HUD clock.
Open flags: Q-076-01.

### S-077 — Five ways it can go
As a commander, I want the result to be a spectrum weighing what I achieved and who I brought home, judged by what is reasonable for that kind of mission, so that a costly win and a clean win are not the same.

Rules
- R-077-01  Given objective score o (weighted completion, failed objectives count 0) and retention r (surviving unit power/deployed power, capped at 1, with damaged units counted by HP fraction), When the final score is computed, Then final = 0.75 · o + 0.25 · r.
- R-077-02  Given the archetype's thresholds [t1, t2, t3, t4], When classified, Then final < t1 is total_failure, < t2 partial_failure, < t3 partial_success, < t4 strong_success, else total_success; thresholds: defensive_stand, siege_breaking, suppression, interception, containment, counterinsurgency [0.20, 0.40, 0.60, 0.80]; reconquest and assault [0.25, 0.45, 0.65, 0.82]; multi_front_defense [0.15, 0.35, 0.55, 0.75]; evacuation [0.30, 0.50, 0.65, 0.80].
- R-077-03  Given the mission ends, When the commander's unit is dead, Then commander fate is killed, else survived [Q-077-01: the hub also names wounded].
- R-077-04  Given the result, When shown, Then the band is revealed only at mission end, never during play.
- R-077-05  Given a mission starts, When the player's force is spawned, Then it includes exactly one commander unit, tied to the lineage character the HUD shows, and that unit's id is held in mission state for the whole mission; R-077-03 reads commander fate from this unit [Q-077-02: the commander's unit type and on-screen marker]. (Westley, 2026-09-28: a dedicated unit.)

Inputs: objectives; unit store; initial power; commander unit id.
Outputs: mission result (band, objective score, retention, per-objective, commander fate, ticks elapsed) in the save file and debrief.
Open flags: Q-077-01, Q-077-02.

### S-078 — A battle becomes history
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
Open flags: Q-078-01 (targets `home` and `exposed` in the tables resolve to the mission region in code; the tables mean the faction's home region and its exposed border regions).

### S-079 — Orders, not menus
As a commander, I want to receive my orders as a superior officer would give them, three parts and no haggling, and to see afterward how it went and what it cost, so that the civilization feels like a chain of command.

Rules
- R-079-01  Given a mission setup, When the briefing is assembled, Then it has exactly Situation, Objective, and Assets, in that order, each from authored fragments with slots filled from the trigger context, ledger, and force composition; Assets states parity in prose and names shortfall types.
- R-079-02  Given the briefing, When shown, Then the only controls are Accept and Refuse; there is no loadout or force editing.
- R-079-03  Given the mission ends, When the debrief is shown, Then it shows the band, the objectives with completion, force retention, and commander fate.
- R-079-04  Given any briefing or debrief text, When rendered, Then it contains no raw field numbers.

Inputs: mission setup; result.
Outputs: briefing and debrief screens.
Open flags: none beyond the missing reference. Reference required: `references/E-10/notes.md`, missing.

### S-080 — Difficulty is scarcity, not stronger enemies
As a commander, I want hard mode to give me less to work with, never to give the enemy better units, so that I always lose to my own limits.

Rules
- R-080-01  Given any difficulty, When forces are generated, Then both sides draw from the same unit profiles; no stat differs by difficulty.
- R-080-02  Given easy, medium, hard, When a mission is generated, Then difficulty sets parity (R-074-03), time width, resource generosity, and the complication odds, and how fast those compress across generations [Q-080-03: the values].
- R-080-04  Given a mission is generated, When the complication roll fires (about 1 percent of missions, a celebrated rarity), Then one complication is fixed at generation and never live: a report, a status, or an expected friendly asset turns out false mid-mission (Crossed Signals); it never changes an enemy stat, is never foreshadowed, and at most one fires per mission; the debrief names it apart from the tallies and the chronicle gives it one entry when it changed the region's fate.
- R-080-03  Given a mission preference marked rare, When the world has no other viable candidate, Then the rare archetype can still be chosen (preference 0.1, never 0).

Inputs: difficulty; onboarding.
Outputs: parity; candidate scores.
Open flags: Q-080-03 (the compression values). Q-080-01 is closed: the full ramp ships. Q-080-02 is closed: Crossed Signals, chosen through the options pass, `docs/northstar/research/options/complications/`. Q-079-01 is closed: single-player team model, the host owns difficulty and preferences.

## Inputs

| Input | Source | Range | Rejection |
|---|---|---|---|
| World, registry, logs | E-02 through E-08 | | |
| Ledger, lineage id | E-08 | | missing lineage gives relevance 0 |
| Onboarding | E-08 | difficulty; per-archetype preference or rare | invalid rejected at save |
| Archetype library | E-21 | 10 archetypes with the S-073 table | malformed fails load |
| Unit roster | E-11 | the era's roster with power | |
| Accept or refuse | Player | | |
| Tactical result | E-11 through E-15 | objectives, unit store, commander unit | |

## Outputs

| Output | Observable where |
|---|---|
| Mission setup (region, archetype, forces, objectives, time limit, map params, reinforcement spec) | Save file; briefing; T1 trace |
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
- Time limit uses the overridden 250-tick table.
- Refusal deploys a force.

## Open ambiguity flags

Q-072-01, Q-074-01, Q-076-01, Q-077-01, Q-078-01, Q-079-01, Q-080-01. Details in `docs/northstar/ambiguity_register.md`.

## Depends on

- E-02 through E-07 (world state and logs that trigger missions).
- E-08 Generational structure (lineage, onboarding, chapter loop).
- E-09 Chronicle (consequence flags).
- E-11 Units (roster, power, HP), E-13 Movement, E-15 Reinforcement structures, E-17 Map generation (mission map), E-16 Client (briefing, HUD objectives, debrief).
- E-21 Offline AI pipeline (archetype and briefing fragment libraries).
