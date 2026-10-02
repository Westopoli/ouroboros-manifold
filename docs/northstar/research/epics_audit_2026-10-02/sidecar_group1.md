# Sidecar for group 1: E-01, E-11, E-12, E-13 and algorithms.md

Drafter: Engineer tier, 2026-10-02. Story numbers S-200 to S-209 are all used. Files changed: `docs/bible/epics/E-01-layer-system.md`, `E-11-units-and-combat.md`, `E-12-fog-and-sensors.md`, `E-13-movement-and-command.md`, `docs/bible/algorithms.md`. Nothing else was touched.

## 1. Catalog rows for `stories.md`

No story was retitled. Ten stories are new.

| Story | Epic | Summary | Status | File and anchor |
|---|---|---|---|---|
| S-200 | E-01 | "On a land map the height of the ground decides which layers are rock and which are air, and what walkers can climb." | Design decided 2026-10-02, not scheduled (Q-166-04, Q-189-02; space is Q-166-02) | `epics/E-01-layer-system.md` S-200 |
| S-201 | E-11 | "The land era has units that walk, so slopes and strongpoints at slopes decide where an army can go." | Design decided 2026-10-02, not scheduled (Q-201-01) | `epics/E-11-units-and-combat.md` S-201 |
| S-202 | E-11 | "Workers are real units that cannot fight, can be killed, and count in the population cap and the unit budgets." | Design decided 2026-10-02, not scheduled (Q-167-03, Q-159-10) | `epics/E-11-units-and-combat.md` S-202 |
| S-203 | E-11 | "Every unit type costs the three resources by its category and takes its share of the population cap." | Design decided 2026-10-02, not scheduled (Q-159-08, Q-169-01, Q-167-01) | `epics/E-11-units-and-combat.md` S-203 |
| S-204 | E-11 | "Walls, gates, towers and production buildings are things on the map that block, are seen and can be attacked." | Design decided 2026-10-02, not scheduled (Q-204-01, Q-204-02, Q-174-02) | `epics/E-11-units-and-combat.md` S-204 |
| S-205 | E-12 | "An enemy building appears when my units see it and shows what it is doing, so scouting reads a base and hiding a building is a play." | Design decided 2026-10-02, not scheduled (Q-205-01, Q-172-01, Q-159-09, Q-204-01) | `epics/E-12-fog-and-sensors.md` S-205 |
| S-206 | E-12 | "My side remembers which kinds of enemy unit it has seen, and nothing about where." | Design decided 2026-10-02, not scheduled (Q-206-02, Q-181-02) | `epics/E-12-fog-and-sensors.md` S-206 |
| S-207 | E-13 | "Routes follow the buildings that rise and fall, the slopes and the steep ground, and no unit is stuck in terrain or walks off the map." | Buildings, slopes, steep ground: design decided 2026-10-02, not scheduled (Q-207-01, Q-207-02, Q-204-01). Push-out and clamp (R-207-06, R-207-07): ruled, built with the tactical port | `epics/E-13-movement-and-command.md` S-207 |
| S-208 | E-13 | "I can put units on guard at a post so a choke or a slope top holds without them running out." | Decided in principle 2026-10-01, mechanism open (Q-096-01, Q-208-01) | `epics/E-13-movement-and-command.md` S-208 |
| S-209 | E-13 | "Workers walk the same ground and take the same room as soldiers, and count among the live units." | Design decided 2026-10-02, not scheduled | `epics/E-13-movement-and-command.md` S-209 |

Rows to update by hand, not retitled: S-006 (E-01) is kept with "pulse not built, ping takes its place, Q-005-04 part (3) open". S-084, S-086, S-087, S-096, S-097, S-100 carry a "Direction changed" line (section 4).

## 2. Register rows

Thirteen new flags.

| Flag | Where | Question | Candidates | Status | Answer |
|---|---|---|---|---|---|
| Q-007-01 | E-01 / S-007 (R-007-07) | Does cover or ground between an observer and a target on different layers block the sight line or the line of fire, and how? E-01 R-007-01 and R-007-02 cover only units on the same layer, and on land maps the ground now fills layers, so ridges are most of the occlusion. | (a) the same rule as the same-layer case, with the line's height interpolated between the two layers; (b) ground blocks, cover blocks only up to its own height; (c) decided by the skill lab | open | |
| Q-162-01 | E-01 / S-162 | Does a ping see behind cover or ground between the caster and the pinged place? The layer-dynamics README lists "ping behind the cover" as a counter to fighting from behind tall cover, but no decision says a ping passes cover. | (a) a ping ignores cover and ground, which is what makes it the counter; (b) it is blocked as sight is; (c) it passes cover but not ground | open | |
| Q-163-01 | E-01 / S-163 (R-163-01) | Does "units on every layer see it from further away" include the emitter's own layer, or is same-layer sight unchanged in both directions, as the engine brief proposes? | (a) cross-layer only, same-layer sight unchanged (the brief's G6); (b) every layer including the emitter's own | open | |
| Q-087-01 | E-11 / S-087, E-13 / S-096 | Is the 200 wu attack-move leash (R-087-05, R-096-03) tested before or after damage? Before, an attack-moving unit with range over 200 never shoots a target more than 200 from its anchor. Plan decision: a switch; the lab runs both; Westley picks. | (a) before damage, as the Python; (b) after damage; (c) decided from the lab's chart | open | |
| Q-091-01 | E-12 / S-091 (R-091-02) | How do the elevation tiers of the elevation sensor bonus (steps of 0.25, closed in Q-092-01) relate to the five height-band layers, now that on land maps elevation and layers come from one height field (E-17 S-190), and is the bonus symmetric? The sign of the tier difference is not stated, and cross-layer vision is symmetric by layer distance (Q-005-02). | (a) drop the tiers: the layers are the only elevation, the bonus goes; (b) keep them, derived from the height field, bonus for the higher observer only (asymmetric vision, which Westley allowed only with a counter); (c) keep them, bonus symmetric by absolute tier difference | open | |
| Q-201-01 | E-11 / S-201 | Which unit types does the land era have, and what are their statistics, reach and speeds? Decided: units and rules are essentially the same as the space era's. | (a) the same six types, re-skinned, with the space era's table; (b) the same categories and roles with land-specific statistics; (c) decided with Q-082-03 and the roster | open | |
| Q-204-01 | E-11 / S-204 (also E-12 S-205, E-13 S-207) | Which layers does a structure occupy and block: only the layer of the ground it stands on, that layer and those above up to a height as cover does (E-01 R-007-01), or every layer? | (a) the layer of the ground it stands on only; (b) a height in layers, as cover has; (c) set per kind of structure | open | |
| Q-204-02 | E-11 / S-204 (R-204-03) | Does an idle or attack-moving unit target an enemy structure in reach, and before or after units? | (a) the nearest enemy of any kind, structures included; (b) units first, structures only when no unit is in reach; (c) structures only on an attack-target order | open | |
| Q-205-01 | E-12 / S-205 (R-205-02) | Does a building once seen stay on the player's map after it leaves sight, and in what form? Units vanish (R-089-04). | (a) it vanishes as units do; (b) it stays shown as last seen, with no activity; (c) its position stays and what it was doing is dropped | open | |
| Q-206-02 | E-12 / S-206 (R-206-01) | Does the record of enemy unit types seen keep how many of each were seen, and does it ever forget? | (a) types only, kept for the mission; (b) types with the largest count seen at once; (c) types with a count that decays | open | |
| Q-207-01 | E-13 / S-207 (R-207-01) | When does a building block movement: from placement, while under construction, or only when finished? Buildings start under construction (E-17 S-193). | (a) from placement; (b) from the start of construction, with a footprint smaller than the finished one; (c) only when finished | open | |
| Q-207-02 | E-13 / S-207 (R-207-04) | How does a gate pass units? | (a) it passes its owner's side and stops the enemy's; (b) it opens and closes by an order; (c) set with Q-174-02 | open | |
| Q-208-01 | E-13 / S-208 (R-208-02) | Can a unit be ordered to hold fire so that a force waits unseen for an ambush? Q-096-01 describes a guard that steps up and returns, not a hold-fire order. Not decided. | (a) a hold-fire setting on the guard stance; (b) a separate order; (c) no hold fire: the ambush is made by silence (E-01 S-163) alone | open | |

Existing flags the drafts cite and carry, not reopened: Q-005-04, Q-008-05, Q-008-06, Q-008-07, Q-096-01, Q-159-08, Q-159-09, Q-159-10, Q-165-01, Q-166-02, Q-166-04, Q-167-01, Q-167-03, Q-169-01, Q-172-01, Q-174-02, Q-176-02, Q-181-02, Q-189-02, Q-082-03.

## 3. Flags to close

None closes on this round's decisions alone. Two need a note in the register:

- **Q-E01-01** (closed, "fixed globally ... 0-30, 30-100, 100-300 wu"): superseded. Westley, 2026-10-02, verbatim in Q-166-01: "fitted, if a layer step is only a meadow slope than there's a problem with the landscape generation system." E-17 S-188 and S-190 (R-190-04) already say the mapping is fitted per map and the global mapping is replaced. Mark Q-E01-01 superseded by that answer and point at E-01 R-010-01 and S-200.
- **Q-001-01** (closed, "all 5 are open at every position"): still right for space maps. On land maps the ground fills the layers below its surface (E-01 S-200, E-17 S-190). Add "on space maps" to the answer.
- **Q-096-01** stays open: Westley decided a guard stance is fine (2026-10-01), but the mechanism and the hold-fire question are not decided. Add the row Q-208-01 beside it.
- **Q-088-01** is closed (b); the plan records the visible-but-unreachable flinch as not built. E-11 S-087 now says so. No register change.

## 4. Needs a ledger row

Tested rules (something in `tests/`, `csrc/` or `scripts/` cites them) whose text was left untouched, with a "Direction changed 2026-10-02, rewrite pending" line under the story heading:

| Rule | Story | Cited by | Direction |
|---|---|---|---|
| R-084-03 | E-11 S-084 | 1 file | area damage reaches the layer offsets its type's reach includes (E-01 S-164, R-008-03) |
| R-086-05 | E-11 S-086 | 2 files | the same, for Barrage |
| R-087-03 | E-11 S-087 | 1 file | engage the nearest enemy within reach that the unit's side sees, on its own layer or another |
| R-096-02 | E-13 S-096 | 3 files | the same, for attack-move |
| R-096-06 | E-13 S-096 | 3 files | a guard stance joins the commands (S-208); "hold" is no longer simply rejected |
| R-097-01 | E-13 S-097 | 3 files | the route grid follows buildings and slopes (S-207) |
| R-097-02 | E-13 S-097 | 1 file | cached routes are recomputed through changed cells (S-207) |
| R-097-03 | E-13 S-097 | 4 files | the probe reads start-of-tick positions (parity P8) |
| R-100-01 | E-13 S-100 | 4 files | facing: engaged target only within 1.5 times range, else move target, else velocity; stationary firing units turn (parity P7) |
| ALG-60 | algorithms.md | tests and C | first attack ready on the tick the target is first in range |
| ALG-61 | algorithms.md | C | area attack by reach offsets |
| ALG-62 | algorithms.md | C | pursuit through movement, return fire for attack-moving units, side sight, reach |
| ALG-65 | algorithms.md | tests and C | ping replaces pulse, emit and silent, side's visible set, cover height and endpoint exemption |
| ALG-66 | algorithms.md | C | attack-move is a group order, slowest-member pace, detach on a movement ability |
| ALG-68 | algorithms.md | tests and C | six-angle sweep, same-layer blockers, start-of-tick probe, leash switch |

The ALG notes sit as one paragraph under each entry. They carry no identifiers or assignments, so `scripts/specfactory/alg_constants.py --emit` writes the same header before and after (checked by diff), and `tests/specfactory/test_alg_constants.py` passes (64).

Tested rules left with no note because only a flag or a pointer was added in an Open flags line: R-087-05 and R-096-03 (leash, Q-087-01), R-089-04 (S-206 is a record of types, not positions), R-089-05 (shipment, Q-176-02), R-090-04 (weather pointer), R-091-02 (Q-091-01), R-099-03 (S-209 R-209-02 counts workers as live units), R-087-07 (workers, S-202), R-097-06 (Q-165-01). Rules rewritten outright because nothing cites them: E-01 R-001-07 (first sentence), R-004-01, R-010-01, R-010-03, R-162-01 and R-163-01 (inline flags), E-11 R-082-07.

## 5. Findings resolved

Rows are numbered in the order of the findings table of `group_1_layers_combat.md`.

| # | Row | Result |
|---|---|---|
| 1 | E-01 gate row and R-010-01, fixed global mapping | done: E-01 gate rows, R-010-01, S-200 R-200-01. Register row Q-E01-01 to supersede (section 3) |
| 2 | R-010-03, 5 percent test | done: R-010-03 names fitted bands; the 5 percent figure is unchanged |
| 3 | E-01 Purpose, five understandings | done: Purpose |
| 4 | Ground fills the layers below, ground flag | done: S-200 R-200-02, S-001 Inputs. R-001-04 untouched (tested). Reading follows E-17 R-190-01, see section 6 |
| 5 | Ground too steep to cross | done: S-200 R-200-03, R-200-04; threshold is E-17's Q-189-02 |
| 6 | Launch types all fly, strongpoints hold nothing | done: R-001-07 and Purpose (the land era has walking types), E-11 S-201 |
| 7 | Strongpoints at slopes, S-004 | done: pointer in S-004 Open flags (E-15 S-126, E-17 S-192) |
| 8 | No faster descent in space eras | done: R-004-01 |
| 9 | Cover and ground on a cross-layer line | flagged: R-007-07, Q-007-01 |
| 10 | S-006 pulse, 60-second test, tables | done: 60-second test, Inputs and Outputs rows, Look references, Ways wrong. S-006 is kept, not deleted, because Q-005-04 part (3) leaves open whether the pulse stays beside the ping |
| 11 | S-008 flags list | done: S-008 Open flags and the footer list Q-008-05, Q-008-06, Q-008-07 |
| 12 | Ping behind cover | flagged: Q-162-01 |
| 13 | R-163-01 "every layer" | flagged: Q-163-01 |
| 14 | E-11 R-084-03, R-086-05 | done by note: S-084 and S-086 direction lines (tested rules) |
| 15 | E-11 R-087-03, E-13 R-096-02 | done by note: S-087 and S-096 direction lines |
| 16 | E-11 invariant "no damage across layers" | done: Invariants |
| 17 | S-082 per-type declarations | done: R-082-09 (new), R-082-07 rewritten; R-082-06 untouched (tested) |
| 18 | No walking unit type | done: S-201, Q-201-01 |
| 19 | Workers as units | done: S-202 (statistics and roster: Q-167-03 of E-22) |
| 20 | Cost, resource, population weight | done: S-203, R-082-09. Resource is Q-159-08, weight is Q-169-01 |
| 21 | "Family" undefined | done: Purpose says the three categories are the unit families (E-22 S-171). Roles inside a category stay Q-082-03 |
| 22 | Nearest target, S5 | flagged: S-087 Open flags point at Q-008-05 and the lab-only setting |
| 23 | Leash before or after damage | flagged: Q-087-01, in S-087 and S-096 Open flags |
| 24 | S-087 stale flag line | done: S-087 Open flags (Q-088-01 closed, branch not built) |
| 25 | E-11 scale, workers | done: Scale requirements sentence, S-202 R-202-04 |
| 26 | Structures as combatants | done: S-204. Numbers and tower behaviour: Q-174-02 (E-22); layers, targeting: Q-204-01, Q-204-02 |
| 27 | E-12 pulse mentions | done: gate verdict, Purpose, Depends on |
| 28 | R-091-02 symmetry and tiers | flagged: Q-091-01 |
| 29 | R-089-04, record of types seen | done: S-206 (R-089-04 stands) |
| 30 | Structures in fog, what a seen building reveals | done: S-205. What is revealed: Q-172-01 (E-22); disguise: Q-159-09; memory of a seen building: Q-205-01 |
| 31 | R-089-05 and shipments | flagged: Q-176-02 (E-22), pointer in S-089 Open flags |
| 32 | R-090-04 and weather | done: pointer in S-090 Open flags (E-15 S-130) |
| 33 | E-12 Inputs, elevation | done: Inputs row points at E-17 S-190; the symmetry question is Q-091-01 |
| 34 | E-13 four commands | done: Purpose, S-096 note |
| 35 | Guard stance, hold fire | done: S-208 R-208-01; hold fire flagged Q-208-01; Q-096-01 carried |
| 36 | Grid and cached routes change with buildings | done: S-207 R-207-01 to R-207-04; S-097 direction line. Timing of blocking: Q-207-01; gate: Q-207-02 |
| 37 | Slope edges and walkability on the grid | done: S-207 R-207-05 |
| 38 | Push-out, clamp and slide | done: S-207 R-207-06, R-207-07 |
| 39 | R-097-03 start-of-tick, R-100-01 1.5 times range | done by note: S-097 and S-100 direction lines |
| 40 | R-099-03 live units and workers | done: S-209 R-209-02, Scale requirements, S-202 |
| 41 | R-097-06 and lanes at 1.3 | done: pointer to Q-165-01 in S-097 Open flags |
| 42 | Workers in movement at scale | done: S-209, Scale requirements |
| 43 to 48 | ALG-60, ALG-61, ALG-62, ALG-65, ALG-66, ALG-68 | done by note: one direction line under each (tested). The six angles are stated in the ALG-68 note |

Findings section 2, decisions with no home: guard stance, S-208. Leash and target-choice switches, Q-087-01 and the S-087 pointer. Push-out and clamp, S-207. Occlusion, Q-007-01. Ping behind cover, Q-162-01. Refusing a fight, Q-008-06 listed in S-008. Workers, cost, families, structures, walking units, fitted bands, ground filling layers, steep ground: each is a story or rule above. The reactive formation stays unwritten, as the findings say none is needed yet.

Findings section 3, could not judge: R-163-01 (Q-163-01), the scaling of fixed distances with fitted bands (Q-166-04 carried in S-004, S-005, S-164, R-200-01), R-091-02 symmetry (Q-091-01), families (resolved by H6), enemy-economy fog (Q-181-02), shipment as unit (Q-176-02), workers in "live units" (S-209), the Python stall (S-207 R-207-06 states push-out and R-097-09's repulsion text was not touched or checked against the C).

## 6. Could not do, and notes for the architect

- **R-200-02 rests on E-17's reading.** "The ground fills the layers below it" is the decision. That layer L itself and everything above it are open to a flying unit is E-17 R-190-01's reading, which E-01 now repeats so the two epics do not disagree. If Westley means otherwise, change both.
- **Duplicate id R-097-06 in E-13** (the stationary-pair rule shares the number with the terrain slowdown): left alone because both are tested. Needs a renumbering with a ledger row.
- **E-22 R-174-05** says route changes are "E-13 S-097". The rules are in E-13 S-207, and S-097 carries a line that points there. E-22's drafter should repoint the citation.
- **Tick rate and workers.** S-209 R-209-02 counts workers among the live units, so a base with workers and soldiers over 1,000 runs the sim at 10 ticks per second. That follows from "units, counted in the unit budgets" and E-22 lists it under ways this could be wrong. If Westley wants workers outside the tick-rate count, R-099-03 needs a rule.
- **Stale closed flags left inline**, outside the findings: E-12 R-094-02 and its flag Q-094-01 (closed: no sensor circles, two fog states), the "[Q-090-01 ...]" and "[Q-092-01 ...]" notes in R-090-03 and R-091-02, E-11 R-081-01's "[Q-081-01 ...]" (closed at 0.20). The Open ambiguity flags footers of E-11, E-12 and E-13 now list only open flags.
- **Gate rows.** Counts and verdicts were updated by hand. The gates were not re-run; `dor_check` reports E-12 READY and E-01, E-11, E-13 NOT READY by open register flags, as expected.
- **S-006 kept.** The pulse text stays, marked not built, because Q-005-04 part (3) is open. Deleting it is the architect's call.
- **Tower, wall and gate behaviour** is not written beyond "they exist, block, are seen, can be attacked". Whether a tower fires is Q-174-02, and R-204-04 is a rule with its content left to that flag.
- No git commands were run. Test files, code, `stories.md` and the register were not touched.
