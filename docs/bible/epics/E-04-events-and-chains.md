# E-04 — Events and Chains

## Definition-completeness gate (run 2026-09-10, flags folded 2026-09-14)

| Check | Result |
|---|---|
| Every story has at least one Given/When/Then rule with concrete values | Yes, 7 stories, 33 rules, values from `algorithms.md` ALG-32 through ALG-37 and the launch library table. |
| Every input listed with range and rejection behavior | Yes, see Inputs. |
| Every output listed with where it is observable | Yes, see Outputs. |
| Implied-but-unstated behavior turned into flags | No open flags; Q-225-01 and Q-225-02 on S-225 closed 2026-10-21 (register). |
| Every visible-surface story has a reference | Not applicable; events reach the player through the chronicle (E-09) and world view (E-16). |
| "Obviously working" in 60 seconds named | Yes, see below. |

**Gate verdict: not passed.** S-026 to S-031 have no open flags and passed 2026-09-14. S-225 (added 2026-10-02) has not been through the gate and has no open flags (Q-225-01 and Q-225-02 closed 2026-10-21, register).

## Purpose

Drift is the slow hum. Events are the things that happen. A famine, a garrison collapse, a trade boom, a revolt: each is a discrete moment that jolts a region's numbers and can set off follow-ups days or years later. Events do not roll dice out of nowhere. A new chain starts when a field crosses a threshold that region is sensitive to, so every crisis has a traceable cause. Follow-ups are scheduled with a delay, a probability, and a condition, so a chain can fizzle if the world moves on, and a mission that heals a region can stop the revolt that was coming. Same-tick events land together and compound, except when they contradict, in which case the likelier one goes first. When several regions cross thresholds on the same tick, every crossing is judged against the tick-start fields, so two crises can begin at once and neither hides the other.

This is the layer that turns graphs into history. The chronicle reads chain tags to tell cause from effect.

## Obviously working in 60 seconds

Run one home region for 100 ticks with drift disabled and economy forced from 60 down to 9 over 20 ticks. On the tick economy crosses below the region's noised infrastructure-decay threshold near 40, "Infrastructure Decay" fires once and not again while economy stays below. On the tick it crosses below the famine threshold near 10, "Famine" fires: population −3, tension +4, economy −1. Three to six ticks later a revolt may follow if tension is still above 40; five to twelve ticks later relief may follow if economy is back above 12. Push economy back to 60 and down again: the same events fire again as new chains with new tags. Same seed twice: identical event log.

## Stories

### S-026 — Crises start when a line is crossed
As a commander reading the chronicle, I want every crisis to have a cause I can point to, so that history reads as consequence and not as dice.

Rules
- R-026-01  Given a region and a threshold template with field F, direction `above`, threshold T, When the region's F was ≤ T + offset last tick and is > T + offset this tick, Then the template fires once on this tick; for direction `below` the mirror holds with <.
- R-026-02  Given F stays on the far side of the threshold for any number of ticks after firing, When ticks pass, Then the template does not fire again.
- R-026-03  Given F returns across the threshold and later crosses it again, When the second crossing happens, Then the template fires again as a new chain with a new chain tag.
- R-026-04  Given a time jump starts, When noise offsets are rolled, Then each (region, threshold template) pair gets one uniform offset in [−10, 10] that persists for the whole jump.
- R-026-05  Given ticks 1 through 3 of a run, When triggers are evaluated, Then nothing fires; the trigger state is primed from the current fields so that a field already past its threshold at tick 3 does not fire at tick 4.
- R-026-06  Given a threshold template fires, When its effects apply, Then each field delta applies with floors economy 8.0, tension 12.0, others 0, ceiling 100, and composites recompute, through the same per-region delta sum as S-028 R-028-01.
- R-026-07  Given regions A and B both cross a threshold on tick t, When triggers are evaluated, Then both are judged against the tick-start fields (A's effects never change what B's crossing reads, in either region order), both fire on tick t, and each region's fired deltas are summed with that region's due-queue deltas and applied once; a region that crosses only because a same-tick event moved its field fires on tick t + 1, not t.

Inputs: fields; template table; noise offsets; tick.
Outputs: fired event records with chain tag in the tick log; field changes.
Open flags: none.

### S-027 — One thing leads to another
As a commander, I want a crisis to spawn follow-ups that may or may not come, depending on how the region is doing when their time arrives, so that intervention matters.

Rules
- R-027-01  Given a fired event with a chain spawn (template X, delay range [a, b], probability p, condition C), When it fires on tick t, Then one delay d = clamp(round(triangular(a, b, mode (a + b)/2)), a, b) is drawn (one uniform draw, the contract in `ouroboros_sim.h`) and X is queued for tick t + d with probability p, condition C, and the parent's chain tag.
- R-027-02  Given a queued event whose tick arrives and whose condition is not met (for `above` v: field ≤ v; for `below` v: field ≥ v), When resolved, Then it is dropped without firing and without a probability roll.
- R-027-03  Given a queued event whose condition is met, When resolved, Then one RNG draw r is made and it fires only if r ≤ p.
- R-027-04  Given "Famine" fires on tick 50 in a region, When tick 53 to 56 arrives with tension above 40, Then "Regional Revolt" may fire with probability 0.5 carrying Famine's chain tag.
- R-027-05  Given an admin-revolt chain of length L in [3, 8] (E-05 R-040-03), When each event fires, Then the next queues with probability 1.0 and no condition, at a delay of 1 tick plus one surplus tick for the earliest gaps until the surplus L minus the step count is spent, so the Breakaway fires exactly L ticks after the roll; the short chain skips Political Crisis and Popular Support, the medium chain skips Popular Support.
- R-027-06  Given any spawned event, When it is read from the log, Then its chain tag equals the root event's tag, and the tag is unique per chain start (`chain_NNNN`, sequential).
- R-027-07  Given a queued event dropped by R-027-02, When the tick log is read, Then it holds a `pruned` record with the template, region, tick, chain tag, and the condition that failed, so the chronicle (E-09) can tell the revolt that almost happened.

Inputs: template chain spawns; region fields at resolution time.
Outputs: pending queue; fired records; pruned records.
Open flags: none.

### S-028 — Disasters stack, contradictions do not
As a commander, I want two blows landing the same day to hurt together, but a resolution and a crisis never to both happen at once, so that the world compounds without contradicting itself.

Rules
- R-028-01  Given two queued events due the same tick in the same region, both passing conditions and probability, When they resolve, Then each delta is computed against the tick-start fields, the deltas sum, and the sum applies once with floors and ceilings.
- R-028-02  Given "Revolt Crushed" (p 0.45) and "Revolt Entrenched" (p 0.55) both due the same tick in the same region, When resolved, Then Entrenched is kept and Crushed is re-queued for tick + 1 or tick + 2 (one draw).
- R-028-03  Given two mutually exclusive events with equal probability, When resolved, Then one uniform draw decides: below 0.5 the earlier-queued one is kept, otherwise the later one; the other is re-queued as in R-028-02.
- R-028-04  Given two same-tick events with no shared exclusion tag, When resolved, Then both fire and neither is delayed.
- R-028-05  Given exclusion tags are evaluated, When multiple tags are present, Then they are processed in sorted tag order, and an event removed by one tag is not considered for later tags.

Inputs: queued events due this tick; exclusion tags.
Outputs: fired and delayed records.
Open flags: none.

### S-029 — Some pressures never stop
As a commander, I want a tense region to face a rising chance of revolt every tick rather than a single trip-wire, so that unrest feels like a fever, not a switch.

Rules
- R-029-01  Given a region with tension 64, When the regional revolt roll runs, Then p = 0.007 · 0.64^0.8, within 1e-6 of 0.004898.
- R-029-02  Given tension 0, When the roll runs, Then p = 0 and the revolt never fires.
- R-029-03  Given a revolt fired on tick t in a region, When ticks t + 1 through t + 11 run, Then no revolt roll is made for that region; the roll resumes on tick t + 12.
- R-029-04  Given a revolt fires, When effects apply, Then military −2, economy −2, tension +4, and follow-ups "Revolt Crushed" [2, 5] at 0.45 if military above 35 and "Revolt Entrenched" [3, 8] at 0.55 if tension above 40 are queued.
- R-029-05  Given "Revolt Entrenched" fires, When resolved, Then it marks the region for faction creation (E-07 decides whether a breakaway forms).

Inputs: tension; cooldown state; RNG.
Outputs: fired revolt records; cooldown in trigger state.
Open flags: none.

### S-030 — The launch event library
As a commander, I want the galaxy's crises and booms to come from a fixed, authored set, so that the same causes produce the same kinds of history in every campaign.

Rules
- R-030-01  Given a new campaign, When its world is created (the pipe's `set_seed`), Then the launch library is loaded into that world, and it contains exactly the 26 templates in the table below with these triggers, effects, spawns, and exclusion tags, and a contract test compares the loaded library to the table field by field.
- R-030-02  Given a template with no trigger, When triggers are evaluated, Then it never starts a chain; it fires only as a spawn.
- R-030-03  Given every template's effects, When summed, Then every value is an integer in [−4, 6]; no launch event moves a field by more than 6 in one firing.

| Template | Trigger | Effects (m, e, t, p) | Spawns (template, delay, p, condition) | Exclusion |
|---|---|---|---|---|
| Garrison Collapse | military below 30 | −2, 0, +3, 0 | Border Incursion [3,7] 0.55 military below 18; Emergency Levy [2,5] 0.40 economy above 25 | |
| Border Incursion | spawn only | −2, −2, +2, 0 | Regional Revolt [3,6] 0.60 tension above 40 | |
| Emergency Levy | spawn only | +3, −2, +2, 0 | | military_relief |
| Regional Revolt | probability, tension, base 0.007, exponent 0.8, cooldown 12 | −2, −2, +4, 0 | Revolt Crushed [2,5] 0.45 military above 35; Revolt Entrenched [3,8] 0.55 tension above 40 | political_resolution |
| Revolt Crushed | spawn only | −1, 0, −2, 0 | | revolt_outcome |
| Revolt Entrenched | spawn only, creates faction | −4, −2, +2, −2 | | revolt_outcome |
| Trade Boom | economy above 55 | 0, +2, +1, +1 | Prosperity Unrest [8,15] 0.25 tension above 40 | |
| Prosperity Unrest | spawn only | 0, −1, +4, 0 | | |
| Population Crisis | population below 20 | −2, −2, +2, 0 | | |
| Resistance Movement | spawn only | −2, 0, +5, 0 | | |
| Conquest Unrest | spawn only (from conquest, ALG-22) | −1, −2, +6, 0 | Regional Revolt [3,6] 0.60 tension above 40 | |
| Labor Shortage | population below 40 | 0, −2, +2, 0 | Immigration Wave [5,12] 0.40 economy above 30 | |
| Immigration Wave | spawn only | 0, +1, +2, +3 | | |
| Infrastructure Decay | economy below 40 | 0, −3, +2, −1 | | |
| Military Buildup | military above 50 | +2, −2, +1, 0 | War Weariness [8,15] 0.35 tension above 30 | |
| War Weariness | spawn only | −2, −1, +3, 0 | | |
| Cultural Renaissance | economy above 60 | 0, +1, −3, +1 | | |
| Famine | economy below 10 | 0, −1, +4, −3 | Regional Revolt [3,6] 0.50 tension above 40; Famine Relief [5,12] 0.55 economy above 12 | |
| Famine Relief | spawn only | 0, +3, −3, +2 | | |
| Diplomatic Incident | tension above 35 | +1, −1, +3, 0 | | |
| Harvest Surplus | population above 50 | 0, +2, −1, +1 | | |
| Admin Separatist | spawn only (from ALG-29), carries chain length L | 0, −1, +3, 0 | next step of the L-variant chain, delay per R-027-05, 1.0 | |
| Admin Political Crisis | spawn only (medium and long chains) | −1, −2, +4, 0 | next step of the L-variant chain, delay per R-027-05, 1.0 | |
| Admin Popular Support | spawn only (long chain) | 0, 0, +2, −1 | Admin Military Defection, delay per R-027-05, 1.0 | |
| Admin Military Defection | spawn only | −3, 0, +2, 0 | Admin Breakaway, delay per R-027-05, 1.0 | |
| Admin Breakaway | spawn only, creates faction, admin revolt | −4, −3, +5, −2 | | |

Inputs: the library file.
Outputs: loaded template table; contract test.
Open flags: none. Growing the library is E-21 (offline AI pipeline) work; every new template enters this table.

### S-031 — The world moves without you
As a commander watching the chronicle scroll, I want the galaxy to have changed visibly every time I come back, so that the time jump feels like history and not a pause.

Rules
- R-031-01  Given a 5,000-tick run with the launch config and any seed, When every 30-tick window is scored, Then attacks resolve in at least as many windows as the Python reference sim's measured rate, recorded in `docs/northstar/e2e/E-04.md` from ten seeds before this story's tests are written (Q-031-01: measure first).
- R-031-02  Given the same run, When windows are scored, Then conquests or colonizations occur in at least as many windows as the measured reference rate, recorded the same way.
- R-031-03  Given the same run, When counted, Then at least one faction is created and at least one faction is absorbed or removed over the run.
- R-031-04  Given any 30-tick window, When the chronicle distiller runs on it, Then it finds at least 5 candidate entries.

Inputs: full sim run.
Outputs: window statistics in the T1 trace; trajectory invariants.
Open flags: none. The reference measurement is a Stage 3 task for this story (Round 2); until it exists S-031 is not Ready.

### S-225 — Environmental trouble and the event library
As a commander, I want the history the chronicle tells to agree with the ground I fight on, so that a region's environmental trouble is either part of both or part of one on purpose.

Direction decided in part 2026-10-02 (E-15 S-219; E-17 R-166-03; E-02 S-221 derives the trouble from the seed); whether it reaches the strategic sim is open. Not scheduled for building.

Rules
- R-225-01  Given a region has an environmental trouble (E-02 S-221), When the strategic sim runs, Then [Q-225-01: whether the trouble has any strategic effect, as an event template or a trigger, or is tactical only]; until it is decided the library stays the 26 templates of R-030-01 and no template reads a climate or trouble.
- R-225-02  Given the growth of a settlement comes "in waves tied to events" (E-17 R-166-03), When "events" is read, Then [Q-225-02: whether it means the events of this epic, one chain per region-year in the strategic sim, or events inside a mission (a shipment arrives, an expansion is founded, a season turns)].

Inputs: the region's trouble (E-02 S-221); the template table.
Outputs: none until Q-225-01 is answered.
Open flags: none. Q-225-01 and Q-225-02 closed 2026-10-21 (register: tactical only, the 26 templates stay closed; in-mission events).

## Inputs

| Input | Source | Range | Rejection |
|---|---|---|---|
| Template table | Library file | 26 templates at launch, fields as the table | Unknown field name, direction not `above`/`below`, delay range with a < 0 or b < a, probability outside [0, 1]: library fails to load |
| Region fields | E-02 | [0, 100] | not applicable |
| Noise offsets | Rolled per time jump | [−10, 10] per (region, template) | not applicable |
| Tick | Tick loop | ≥ 1 | not applicable |
| External spawns | ALG-22 conquest, ALG-29 admin revolt | template id, due tick, probability 1.0 | Unknown template id fails the tick |

## Outputs

| Output | Observable where |
|---|---|
| Fired events (template, region, tick, deltas, chain tag, spawns) | Tick log `events`; chronicle input (E-09) |
| Pending queue contents | Save file; T1 trace |
| Trigger state per region | Save file |
| Delayed and pruned entries | Tick log `delayed` and `pruned` records |
| Region field changes | E-02 outputs |

## Invariants

- A threshold template fires at most once per crossing.
- Every fired event has a chain tag; spawns share the root's tag.
- No event ever pushes a field outside [floor, 100].
- Queue entries are consumed exactly once.
- Same seed, same event log, all platforms.
- Over 5,000 ticks with 60 regions, the pending queue never exceeds 2,000 entries (guards runaway chains).

## Scale requirements

Confirmed by Westley, 2026-09-14 (never loosened by Agora; a miss is escalated): trigger evaluation for 60 regions × 26 templates in under 20 µs per tick; queue resolution O(due entries).

## Look and behavior references

None required in this epic.

## Ways this could be wrong

- Fires every tick while past the threshold instead of on the crossing.
- Noise re-rolled every tick or never rolled, so all regions share one personality.
- Grace period dropped, so half the map fires on tick 1.
- Spawn conditions checked at spawn time instead of at resolution time.
- Same-tick deltas applied sequentially so the second event reads the first's result.
- Fresh triggers evaluated region by region against live fields, so one region's crisis hides or causes another's on the same tick.
- Exclusion loser cancelled instead of delayed.
- Probability roll made before the condition check, consuming RNG and breaking determinism.
- Chain tag counter not saved, so loading a save reuses tags.

## Open ambiguity flags

Q-225-01, Q-225-02 (S-225). S-026 to S-031 have none.

## Depends on

- E-02 Region fields (fields, floors).
- E-05 Faction agents (conquest spawns Conquest Unrest; admin revolt spawns the admin chain).
- E-07 Civilizational lifecycle (what a faction-creating event does).
- E-08 Generational structure (noise offsets roll at each time jump).
- E-09 Chronicle (consumer of chain tags).
- E-02 S-221 (a region's environmental trouble, if it ever becomes an event trigger, S-225).
- E-17 Map generation (R-166-03 growth waves tied to events, S-225).
