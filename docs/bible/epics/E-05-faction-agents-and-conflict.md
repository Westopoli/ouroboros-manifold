# E-05 — Faction Agents and Conflict

## Definition-completeness gate (run 2026-09-10, flags folded 2026-09-14)

| Check | Result |
|---|---|
| Every story has at least one Given/When/Then rule with concrete values | Yes, 11 stories, 62 rules, numbers from `algorithms.md` ALG-11 through ALG-25 and ALG-29. |
| Every input listed with range and rejection behavior | Yes, see Inputs. |
| Every output listed with where it is observable | Yes, see Outputs. |
| Implied-but-unstated behavior turned into flags | 2 open flags on S-226, Q-226-01 and Q-226-02; Q-228-02 (E-08 S-228) is cited and held elsewhere. |
| Every visible-surface story has a reference | Not applicable; conflict reaches the player through the world view (E-16), chronicle (E-09), and missions (E-10). |
| "Obviously working" in 60 seconds named | Yes, see below. |

**Gate verdict: not passed.** S-032 to S-041 have no open flags and passed 2026-09-14. S-226 (added 2026-10-02) has not been through the gate and is blocked only on the parked Q-226-02.

## Purpose

Fifteen factions share the galaxy and none of them is the protagonist. Every faction, the player's included, runs the same agent: each tick it looks at its neighbors, scores them, and either saves its budget, attacks the most attractive enemy region it can beat, or colonizes the most attractive empty one. Attacks are telegraphed three ticks ahead at full strength or sprung at once at half strength. Defenders who see an attack coming may reinforce. When two or more factions want the same region on the same tick, they collide and the stronger economy usually wins, but not always.

Conflict has consequences that outlast the battle: a conquered region seethes, an overextended empire fractures, and a hostile border wears both sides down every tick. Faction personality is a roll at birth, so the same archetype fights a different war every campaign. The player's civilization is cautious by design; it fights back far more often than it starts fights.

## Obviously working in 60 seconds

Generate seed 7 and run 300 ticks. By tick 100 at least one attack has resolved and the log shows telegraphed attacks resolving three ticks after declaration and surprise attacks resolving at once with half strength. By tick 300 at least one region has changed hands, its new owner placed a garrison, and a Conquest Unrest event fired there a few ticks later. Some faction with more than four regions has had an admin separatist chain start. Same seed twice: identical intents, identical outcomes.

## Stories

### S-032 — Every faction is a person
As a commander, I want every faction, including my own civilization, to run the same decision loop with its own personality, so that the galaxy is a fair free-for-all with no scripted villain.

Rules
- R-032-01  Given any faction, When it is created, Then it has an id, an archetype, a budget starting at 0, a growth rate of 0.025, a tech level, a stance toward every other faction, and an attack confidence drawn once, uniform in its archetype's range (conqueror [2, 6], fortifier [4, 10], player [3, 8], breakaway [2, 5], others [4, 8]).
- R-032-02  Given a faction's attack confidence, When any number of ticks pass, Then it never changes.
- R-032-03  Given the player civilization, When it decides, Then it uses attack weight 0.3, expand weight 0.5, defend weight 1.5, and attractiveness weights weakness 0.60, value 0.25, position 0.15.
- R-032-04  Given a starting faction, When stances are set, Then it is hostile toward every other faction.

Inputs: archetype; RNG.
Outputs: faction entry in the strategic snapshot.
Open flags: none.

### S-033 — Territory pays, or costs
As a commander, I want each region to pay for itself before it feeds my war chest, so that conquering rubble is a burden and holding a rich core is a strength.

Rules
- R-033-01  Given a faction owning regions with economy 66, 40, and 9, When budget accumulates for one tick, Then Δbudget = ((66 − 8) + (40 − 8) + (9 − 8)) · 0.025 · economy multiplier (E-06 R-046-05), which is 2.275 at multiplier 1.0 (DEC-C15-2026-10-22).
- R-033-02  Given a faction owning one region at economy 8.0, When budget accumulates, Then Δbudget = 0 and budget never goes below 0.
- R-033-03  Given a faction owning no regions, When budget accumulates, Then Δbudget = 0.

Inputs: owned regions' economy.
Outputs: budget in the faction entry.
Open flags: none.

### S-034 — Who looks worth taking
As a commander, I want factions to weigh weakness, wealth, and position differently by personality, so that a conqueror and a fortifier want different things from the same map.

Rules
- R-034-01  Given a conqueror evaluating an enemy region with military 30, economy 60, population 50, whose non-owned neighbors are one enemy region (economy 40, population 50) and one empty region, When attractiveness is computed, Then weakness = 0.70, value = ((36 + 20)/100) · 2 = 1.12, position = mean(0.44, 0.15) = 0.295, score = 0.40·0.70 + 0.25·1.12 + 0.35·0.295 = 0.66325.
- R-034-02  Given the same region evaluated by a fortifier, When computed, Then score = 0.25·0.70 + 0.20·1.12 + 0.55·0.295 = 0.56125.
- R-034-03  Given a schism evaluating an enemy region with tension 80, When computed, Then factor one is 0.80 (tension), not weakness, and an empty region is never a candidate for it.
- R-034-04  Given an enemy region with economy 3 and population 4, When evaluated, Then value = ((1.8 + 1.6)/100) · 2 = 0.068 and it is a candidate; Given economy 2 and population 2, Then value = 0.040 and it is not a candidate (minimum attack value 0.05).
- R-034-05  Given a region adjacent to two of the faction's owned regions, When candidates are gathered, Then it is scored once.
- R-034-06  Given an enemy region whose owner is neutral or cooperative with the faction and the faction is neutral or cooperative back, When candidates are gathered, Then it is excluded.
- R-034-07  Given an opportunist evaluating an enemy region that lost 20 military and 10 economy to attacks within the last 150 ticks, When attractiveness is computed, Then the score is multiplied by 1 + (30/100) · 1.5 = 1.45; losses older than 150 ticks count for nothing, and every other archetype multiplies by 1.

Inputs: snapshot fields of neighbors; stances; archetype weights.
Outputs: candidate scores in the decision diagnostics.
Open flags: none.

### S-035 — Attack only when it adds up
As a commander, I want a faction to attack only when the numbers say it will win by its own margin of comfort, so that wars are choices and not spasms.

Rules
- R-035-01  Given a faction with budget 100 and an enemy target with military 40 held since the world began, When viability is checked, Then potential commit = 70, net = 70 − 40·0.55·2.0 = 26, and the target is viable if 26 exceeds effective confidence.
- R-035-02  Given the same faction and a target conquered 50 ticks ago, When checked, Then entrenchment = 1.5 and net = 70 − 33 = 37.
- R-035-03  Given budget 100, the weakest candidate at military 20, and attack confidence 5, When budget pressure is computed, Then break-even = 20·0.55/0.70 = 15.714, ratio = 6.364, pressure = 0.8/6.364, effective confidence = 5 · 0.1257 = 0.6286.
- R-035-04  Given budget 10 and the same target, When computed, Then ratio = 0.636 < 0.8 and effective confidence stays 5.
- R-035-05  Given best viable net 26 and a conqueror, When scored, Then attack score = clamp(26/40, 0, 1) · 1.2 = 0.78.
- R-035-06  Given best colonize attractiveness 0.30 and a conqueror, When scored, Then colonize score = 0.30 · 1.0 = 0.30, so attack wins.
- R-035-07  Given both scores below 0.05, When decided, Then the faction accumulates.
- R-035-08  Given colonize wins with budget 15, When decided, Then the faction accumulates (colonize costs 20).

Inputs: budget; candidate fields; entrenchment; archetype weights.
Outputs: intent record (action, target, commit, source, mode) in the tick log.
Open flags: none.

### S-036 — Declared or sprung
Q-036-02 (b), Westley 2026-09-16: no reservation across factions or ticks, so attacks from different factions may stack on one target and a faction re-decides every tick; R-036-07 is the narrower guard that one faction resolves at most one attack against a target per tick (Architect 2026-10-21, implementation reading; Westley may veto). The rule below is what the tests read today.
As a commander, I want some attacks announced a tick ahead at full strength and others sprung at once at half strength, so that a methodical neighbor and a raider feel different to live beside.

Rules
- R-036-01  Given a conqueror attacking a target with military 70, When mode is chosen, Then telegraph preference = 0.7 + 0.2 = 0.9, and one draw below 0.9 selects telegraph.
- R-036-02  Given a warlord attacking a target with military 20, When chosen, Then preference = 0.3 − 0.2 = 0.1.
- R-036-03  Given a telegraphed attack declared on tick t, When tick t + 3 runs, Then it resolves in step 3c before any new decisions, at full efficiency; on ticks t + 1 and t + 2 it sits in the pending list; the defender's one reactive reinforce (R-036-05) happens in step 3e of tick t, the tick of declaration, not again on the waiting ticks.
- R-036-04  Given a surprise attack, When it resolves, Then effective attack is multiplied by 0.5 and it resolves in the same tick's step 3f.
- R-036-05  Given a telegraphed attack is pending against a faction, When that faction's reactive window runs, Then with probability min(1, defend weight / 1.5) it commits min(budget · 0.30, attacker commit · 0.5) to reinforce the target, and commits nothing if that is below 1.0.
- R-036-06  Given a reinforce of commit 10 on a frontier region with military 30 and tension 50, When resolved, Then base = 10 · 0.5 · (60 − 30)/60 = 2.5 and Δmilitary = 2.5 · U(0.75, 1.25).
- R-036-07  Given a faction already has a resolved attack against a target this tick (step 3c's telegraph maturation, or an earlier attack this same step), When step 3d evaluates its candidates, Then that target is excluded from viability and the faction does not re-declare against it; a failed attack may be repeated against the same target starting the next tick (C3, DECISIONS.md Seventh round, 2026-09-19).

Inputs: archetype preference; target military; defend weight; budget.
Outputs: attack mode; pending telegraph list; reinforce record.
Open flags: none.

### S-037 — Battles have a shape
As a commander, I want an attack's outcome to scale with how decisive it was, and a strong garrison to genuinely absorb a blow, so that fights feel like fights.

Rules
- R-037-01  Given commit 50, defender military 30 held from the start, no tech, telegraph mode, and a stochastic draw of 1.0, When resolved, Then effective attack = 50, effective defense = 30·0.55·2.0 = 33, net = 17, breakthrough: Δmilitary −13.6, Δeconomy −5.1, Δtension +8.5.
- R-037-02  Given the same with a draw of 0.7, When resolved, Then net = 11.9, contested: Δmilitary −5.95, Δeconomy −2.38, Δtension +4.76.
- R-037-03  Given commit 20 against the same defender, When resolved, Then net < 0, repelled: defender Δmilitary −2.0, Δtension +2.0, no economy change, no conquest.
- R-037-04  Given a breakthrough with net 60, When resolved, Then Δtension is capped at +30.
- R-037-05  Given a defender with military 80 and an attacker committing 50, When resolved at draw 1.0, Then net = 50 − 88 = −38 and the region loses only 5.0 military.
- R-037-06  Given a surprise attack with commit 50, When resolved, Then effective attack = 25.
- R-037-07  Given any attack, When it resolves, Then the attacker's committed budget is spent in full.
- R-037-08  Given any attack of any outcome, When it resolves, Then the attacker's own regions' fields are unchanged by the resolution; only the committed budget is spent.

Inputs: commit; defender fields; tech multipliers; entrenchment; mode; RNG.
Outputs: outcome band, net force, deltas in the tick log; region fields.
Open flags: none.

### S-038 — Taking a region
As a commander, I want a region to change hands when its defenders are gone, whoever attacked and however it went, and to be hard to hold afterward, so that conquest is a beginning and not an end.

Rules
- R-038-01  Given an attack leaves defender military below 5.0 and the outcome is not repelled, When resolved, Then the region's owner becomes the attacker, garrison = commit · 0.65 is added to military after damage, economy −5 more (may go below 8), tension +8 more, population −2 more.
- R-038-02  Given a contested attack that takes military from 6 to 4, When resolved, Then conquest happens exactly as after a breakthrough.
- R-038-03  Given a repelled attack, When resolved, Then no conquest ever happens.
- R-038-04  Given a conquest on tick t, When one draw is made, Then with probability 0.60 a Conquest Unrest event is queued for tick t + round(triangular(4, 8, 6)).
- R-038-05  Given a conquered region, When ownership changes, Then its held-since tick is t, so entrenchment restarts at 1.0 and ramps to 2.0 over 100 ticks.
- R-038-06  Given a conquest, When edges update, Then S-024 R-024-03 applies.

Inputs: post-damage military; commit; RNG.
Outputs: conquest record; ownership; garrison; queued event.
Open flags: none.

### S-039 — When everyone wants the same region
As a commander, I want a region that several factions strike at once to go to the strongest hand with room for an upset, and cost the winner more the more it was contested, so that pile-ons are a gamble.

Rules
- R-039-01  Given two factions commit 40 and 20 to the same empty region, with total economies 200 and 100, When the collision resolves, Then factors are 1.0 and 0.7, strengths 40 and 14, and the first wins with probability 40/54 on one draw.
- R-039-02  Given the first wins, When retention is computed, Then opposition = 0.35, ceiling = 0.4 · (1 − 0.35 · 0.6) = 0.316, refund = 40 · U(0, 0.316), and the loser spends all 20.
- R-039-03  Given the loser's budget was 50, When its tension hit applies, Then its highest-military region gains 5.0 · 20/50 = 2.0 tension.
- R-039-04  Given the target is empty and margin = 40/54 = 0.741 ≥ 0.6, When colonized, Then starter military is 10.0; Given margin 0.55, Then starter military = 10 · U(0.5, 0.70).
- R-039-05  Given the target is owned by a third faction with military 30, When the collision resolves, Then each collider's strength is applied against defense 33 with its own stochastic draw, damages sum, and a conquest goes to the winner if military falls below 5.
- R-039-06  Given three or more colliders, When resolved, Then the same rules apply with second-best = the strongest loser.

Inputs: colliding intents; faction economies; tech; RNG.
Outputs: collision record (strengths, winner, margin, refund) in the tick log.
Open flags: none (Q-039-01 closed, Architect 2026-10-18). Direction changed 2026-10-18, rewrite pending: collisions are grouped across matured telegraphs and immediate attacks in one resolution list, and step 3c only matures (this changes R-036-03); R-039-05 and R-039-06 are not built, the resolver skips owned targets (FINDING-sim-F-no-collisions, 2026-10-21). The multi-faction collision resolver is built and was never described in the bible before this story (Stage 1 algorithm pass finding).

### S-040 — Empires fracture
As a commander, I want a large empire to shed provinces to institutional revolt no matter how calm they are, so that no faction, mine included, can swallow the galaxy.

Rules
- R-040-01  Given a faction with 4 regions, When the admin revolt roll runs, Then each region rolls at chance 0.001.
- R-040-02  Given a faction with 10 regions, When the roll runs, Then each region rolls at chance 0.001 + 0.0005 · 36 = 0.019.
- R-040-03  Given a region's roll succeeds on tick t, When resolved, Then one integer draw L uniform in [3, 8] sets the chain length in ticks and an Admin Separatist event is queued for tick t + 1 with probability 1.0, no condition, and chain length L; L in [3, 4] runs the short chain (Separatist, Military Defection, Breakaway), L in [5, 6] the medium chain (Separatist, Political Crisis, Military Defection, Breakaway), L in [7, 8] the long chain (Separatist, Political Crisis, Popular Support, Military Defection, Breakaway); the Breakaway fires on tick t + L, with the surplus ticks beyond one per step added, one each, to the earliest gaps first.
- R-040-04  Given the chain is running, When the owner reinforces the region or its fields improve, Then the chain still completes; nothing interrupts it.
- R-040-05  Given the Admin Breakaway event fires, When resolved, Then E-07 creates a new faction holding the region.

Inputs: territory count; RNG.
Outputs: admin revolt record; queued chain.
Open flags: none.

### S-041 — Hostile borders wear you down
As a commander, I want a region on a hostile border to be chronically stressed, so that frontiers feel like frontiers and are easier to crack.

Rules
- R-041-01  Given a region with two hostile neighbors, When friction applies, Then Δtension = +0.30 and Δeconomy = −0.10, regardless of the neighbors' military.
- R-041-02  Given a hostile neighbor across a trade-only edge, When friction applies, Then it contributes nothing; a hostile neighbor across a border or both edge contributes the full amount.
- R-041-03  Given a neighbor whose faction is neutral or cooperative both ways, When friction applies, Then it contributes nothing.
- R-041-04  Given friction would push economy below 8.0, When applied, Then economy stays 8.0.
- R-041-05  Given an empty neighbor or a same-faction neighbor, When friction applies, Then it contributes nothing.

Inputs: neighbor ownership; edge types; stances.
Outputs: friction record per region in the tick log.
Open flags: none.

### S-226 — How a faction meets a mission's economy
As a commander, I want a faction's standing in the galaxy to carry into the economy it fights with in a mission, so that the strategic simulation and the mission are one story.

Direction decided in part 2026-10-02 (E-22 S-178, E-22 S-179, E-22 S-181; E-22 S-179 and S-181 hold the economy); how it meets this epic is open. Not scheduled for building.

Rules
- R-226-01  Given a mission in which a side's economy runs (E-22), When it is set up, Then the owning faction's economy and technology tier set its starting scale, and the region's situation slants it too (Westley, 2026-10-07; E-22 R-177-06); today the budget (S-033) sets only the enemy's power, E-10 R-074-01.
- R-226-02  Given a faction's archetype, attack weight, expand weight and attack confidence (S-032), When the doctrine that runs its economy is chosen (E-22 S-179, S-181), Then no link to a doctrine is made in the beta; the individual playstyles of enemy characters are post-beta (Westley, 2026-10-07) [Q-226-02: parked].
- R-226-03  Given a region is conquered here (S-038), When a base of operations is occupied in a mission (E-22 S-178), Then the two are separate: S-038 is a region-level ownership change resolved on a strategic tick, and occupation inside a mission has no stated link to it (E-02 S-220, Q-220-01).

Inputs: faction budget, archetype, tier; mission setup (E-10).
Outputs: none until the flags are answered.
Open flags: Q-226-02 (parked for the beta).

## Inputs

| Input | Source | Range | Rejection |
|---|---|---|---|
| Snapshot of all regions | Tick step 3a | as E-02 | not applicable |
| Adjacency and edge types | E-03 | | |
| Stances | E-06 | hostile, neutral, cooperative | unknown value treated as neutral |
| Archetype weight tables | Config | as `algorithms.md` | unknown archetype uses defaults |
| Tech multipliers | E-06 | ≥ 1.0 | |
| RNG | World stream | | |

No player input reaches this epic in single-player; the player's faction runs the same agent. In multiplayer, each human player's faction still runs the agent (vision_v2: the civilization has its own plans). With more players, each pair is a sub-civilization inside the over-arching civilization (E-19 S-159), which this epic has no notion of; how it maps onto factions is Q-228-02 (E-08 S-228).

## Outputs

| Output | Observable where |
|---|---|
| Intents, decisions, scores | Tick log `faction_actions`; T1 trace |
| Attack results, collisions, conquests, colonizations | Tick log; chronicle (E-09); world view border changes (E-16) |
| Budget, confidence, tech | Faction entry in the strategic snapshot; world view faction data panel |
| Pending telegraphs | Save file; T1 trace |
| Friction, admin revolts | Tick log |

## Invariants

- Budget never negative; committed budget is always spent (minus a collision refund).
- No attack on a neutral or cooperative faction's region.
- Conquest only when post-damage military < 5.0 and outcome not repelled.
- Every telegraph declared on tick t resolves on tick t + 3 or is dropped if the attacker no longer owns a region.
- Same seed, same decisions, all platforms.
- Over 5,000 ticks, no faction holds more than 20 regions for more than 500 consecutive ticks (admin revolts working).

## Scale requirements

Confirmed by Westley, 2026-09-14 (never loosened by Agora; a miss is escalated): 15 factions deciding over 60 regions in under 200 µs per tick; 5,000 ticks with full agents in under 5 s.

## Look and behavior references

None required in this epic.

## Ways this could be wrong

- Agents read live fields instead of the tick-start snapshot, so decision order leaks into outcomes.
- Telegraphs resolve before reactive reinforce instead of after.
- Surprise multiplier applied to defense instead of attack.
- Entrenchment reads the current tick instead of the snapshot's held-since.
- Collision winner chosen by max strength instead of a weighted draw.
- Conquest checked on the breakthrough band instead of on post-damage military.
- Garrison added before damage, then destroyed by it.
- Admin revolt rolled once per faction instead of once per region.
- Friction counts trade-only edges.

## Open ambiguity flags

Q-226-01, Q-226-02 (S-226), and Q-228-02 (E-08 S-228) as cited in the Inputs note.

## Depends on

- E-02 Region fields (fields, floors).
- E-03 World generation (graph, edge types, archetype assignment).
- E-04 Events (Conquest Unrest and admin chain templates).
- E-06 Diplomacy and technology (stances, tech multipliers).
- E-07 Civilizational lifecycle (breakaway creation, zombie cleanup, latent loyalty).
- E-10 Missions and E-22 Economy and bases (S-179, S-181: the economy a faction fights with, S-226).
