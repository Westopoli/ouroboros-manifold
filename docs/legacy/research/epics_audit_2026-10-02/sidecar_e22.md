# Sidecar for E-22, Economy and Bases

Drafted 2026-10-02 by the E-22 drafter. File: `docs/bible/epics/E-22-economy-and-bases.md`. 16 stories (S-167 to S-182), 83 rules, 39 new flags. E-19 was not edited.

## 1. Catalog rows for `stories.md`

The S-159 row is the E-19 drafter's to retitle. The rows for S-167 to S-182 are new.

| S-167 | E-22 | "I train workers who walk to a source and bring back one of three resources." | Design decided 2026-10-01, not scheduled (Q-159-08, Q-167-01 to -03) | `epics/E-22-economy-and-bases.md` S-167 |
| S-168 | E-22 | "I place buildings where I choose and the city reshapes around them." | Design decided 2026-10-01 and 10-02, not scheduled (Q-168-01 to -04) | `epics/E-22-economy-and-bases.md` S-168 |
| S-169 | E-22 | "Workers and soldiers share one population cap that I can raise a very long way." | Design decided 2026-10-01, not scheduled (Q-169-01) | `epics/E-22-economy-and-bases.md` S-169 |
| S-170 | E-22 | "I run the production buildings and plan what they make, and changing a building's focus takes a while." | Design decided 2026-10-01, not scheduled (Q-159-08, Q-170-01 to -03) | `epics/E-22-economy-and-bases.md` S-170 |
| S-171 | E-22 | "Strike, Line and Siege counter each other, and what a side gathers shows what it is making." | Design decided 2026-10-01, not scheduled (Q-159-08, Q-171-01) | `epics/E-22-economy-and-bases.md` S-171 |
| S-172 | E-22 | "I can hide what my production is doing from an enemy who sees my buildings." | Design decided 2026-10-01, not scheduled (Q-159-09, Q-172-01) | `epics/E-22-economy-and-bases.md` S-172 |
| S-173 | E-22 | "I choose the technology my side goes for, and a normal match has time to go up one or two levels." | Design decided in part 2026-10-02, not scheduled (Q-159-12, Q-173-01, Q-173-02) | `epics/E-22-economy-and-bases.md` S-173 |
| S-174 | E-22 | "I build walls, gates and towers to cover the lanes raiders take to my workers and shipments." | Design decided 2026-10-01, not scheduled (Q-174-01, Q-174-02) | `epics/E-22-economy-and-bases.md` S-174 |
| S-175 | E-22 | "I grow settlements into new bases and build production forward, and a side that stays home is overrun." | Design decided 2026-10-01, not scheduled (Q-175-01 to -03) | `epics/E-22-economy-and-bases.md` S-175 |
| S-176 | E-22 | "Shipments come from the civilization and I cannot see them on the road." | Design decided 2026-10-01, not scheduled (Q-176-01, Q-176-02) | `epics/E-22-economy-and-bases.md` S-176 |
| S-177 | E-22 | "Every side has a base to protect, and the rich resources lie away from the objective." | Design decided 2026-10-02, not scheduled (Q-159-14, Q-177-01 to -04) | `epics/E-22-economy-and-bases.md` S-177 |
| S-178 | E-22 | "A fallen base is occupied, not destroyed, and I fall back to an expansion or forward base." | Design decided 2026-10-02, not scheduled (Q-178-01 to -05) | `epics/E-22-economy-and-bases.md` S-178 |
| S-179 | E-22 | "When nobody holds the economy seat, rules run it well by a doctrine I can change on the fly." | Design decided 2026-10-02, not scheduled (Q-179-01, Q-179-02) | `epics/E-22-economy-and-bases.md` S-179 |
| S-180 | E-22 | "Alone I have one dial and I ask for things by pointing at the map." | Design decided 2026-10-02, not scheduled (Q-180-01 to -04) | `epics/E-22-economy-and-bases.md` S-180 |
| S-181 | E-22 | "The enemy's economy runs on the same rules, and I choose whether it also scouts, counters and disguises." | Design decided 2026-10-02, not scheduled (Q-181-01, Q-181-02) | `epics/E-22-economy-and-bases.md` S-181 |
| S-182 | E-22 | "I carry something forward between missions, without the fifteenth mission becoming lopsided." | Open (Q-159-07, Q-159-13) | `epics/E-22-economy-and-bases.md` S-182 |

## 2. Register rows

New flags:

| Q-167-01 | E-22 / S-167 | Worker training time, cost, and the load a worker carries. | (a) set with the roster of E-11; (b) set with the three resources (Q-159-08); (c) set in the lab by feel | open | |
| Q-167-02 | E-22 / S-167 | How the yield falls as the walk to a drop-off gets longer. | (a) a straight fall per distance; (b) steps by distance band; (c) set in the lab | open | |
| Q-167-03 | E-22 / S-167 | Worker statistics, and whether workers belong to the 20 to 40 roster of E-11 S-082. | (a) in the roster as non-combat units; (b) a separate list outside the roster; (c) set with Q-082-03 | open | |
| Q-168-01 | E-22 / S-168 | What a lot is, how many a base has, where a building may not be placed, and how "lots are limited" meets E-17 R-166-01 "the player can place buildings wherever they want". | (a) lots are fixed spots, and free placement means choosing among them; (b) lots are a count limit on buildings, placed anywhere legal; (c) free placement, with limits only from terrain | open | |
| Q-168-02 | E-22 / S-168 | Which buildings change the yield of which, by how much, and within what range. | (a) a small table per era; (b) a radius rule on building kinds; (c) set in the lab | open | |
| Q-168-03 | E-22 / S-168 | Construction time, who builds a building, and what it costs. | (a) workers build, resource cost; (b) the building builds itself, resource cost; (c) set per building kind | open | |
| Q-168-04 | E-22 / S-168, E-20 | The full building set per era, and the names. | (a) a small fixed set per era pack (E-20 R-146-01 structures); (b) a larger set set with Q-159-08 and the roster; (c) decided with the era packs | open | |
| Q-169-01 | E-22 / S-169 | Population weight per unit type, the starting cap, what raises the cap and by how much, and the ceiling. | (a) one unit one point; (b) weight by category; (c) set in the lab | open | |
| Q-170-01 | E-22 / S-170 | How long changing a building's family takes, and whether it makes nothing meanwhile. | (a) a fixed time, nothing made; (b) a time scaled by the building's queue; (c) set in the lab | open | |
| Q-170-02 | E-22 / S-170 | How far ahead the production timeline reaches, and what changing a slot costs. | (a) near slots cost more than far slots; (b) one flat change time; (c) set in the lab | open | |
| Q-170-03 | E-22 / S-170 | Build time per unit, and how many a building makes at once. | (a) set by the unit's power as E-15 R-126-02 does; (b) a time per role in the roster; (c) set in the lab | open | |
| Q-171-01 | E-22 / S-171 | What shows heavy gathering to the other side, and how heavy counts as heavy. | (a) workers seen at the sources through the fog; (b) a coarse reading of the enemy's income; (c) both | open | |
| Q-172-01 | E-22 / S-172 | What a seen production building reveals, and what a building shows from a distance. | (a) its focus family only; (b) its focus family and its next scheduled slots; (c) only that it is producing | open | |
| Q-173-01 | E-22 / S-173 | The formula that derives a mission's starting technology from the simulation's technology level, and what "only slightly" means. | (a) the level is lowered or raised by at most one step; (b) a band around the level; (c) set in the lab | open | |
| Q-173-02 | E-22 / S-173 | The number of technology levels per era, and the resource cost and time per level so a normal timed match fits one or two. | (a) 5 levels per era, as Westley's example; (b) set per era pack; (c) set by playtest | open | |
| Q-174-01 | E-22 / S-174, E-17 | Where raid lanes come from, and how a side sees its own lanes and the enemy's. | (a) an output of the map generator; (b) read from the route grid of E-13; (c) both, shown on the map view (E-16) | open | |
| Q-174-02 | E-22 / S-174, E-11 | What a wall, a gate and a tower each do (block, fire, see), and their statistics. | (a) wall blocks, gate blocks and opens for its owner, tower fires; (b) all three also give sight; (c) set with the E-11 roster | open | |
| Q-175-01 | E-22 / S-175 | What "worked hard enough" means for a settlement to grow into a base. | (a) a count of workers held there; (b) a time of presence; (c) a resource spent | open | |
| Q-175-02 | E-22 / S-175 | What makes a side that stays home lose, when its main base never runs dry. | (a) the main base's income has a ceiling and the enemy's grows past it; (b) the main base's sources yield less over time though they do not run out; (c) the enemy's expansions only | open | |
| Q-175-03 | E-22 / S-175 | What a forward base consists of, and its cost and build time. | (a) production buildings only; (b) a small base with drop-off, housing and workers; (c) the same as an expansion | open | |
| Q-176-01 | E-22 / S-176 | What a shipment carries, how often one is sent, and whether it is earned or called in. | (a) a deck chosen before the mission and called in (links to Q-159-07); (b) sent by the civilization on a rhythm; (c) earned by what the side does | open | |
| Q-176-02 | E-22 / S-176, E-12 | Is a shipment a unit, so that E-12 R-089-05 applies; where does it start and how long does it take. | (a) not a unit, an event carried by a lane; (b) a unit marked as unseen by its receiver; (c) decided with E-12 | open | |
| Q-177-01 | E-22 / S-177, E-10 | How archetype and supply distance together decide the kind of base. | (a) the archetype gives the role and the supply distance gives the supply; (b) supply distance overrides the table; (c) the table where it exists, supply distance elsewhere | open | |
| Q-177-02 | E-22 / S-177, E-02 | What the situation gives a mission (richness, limited or abundant, slant to the defender) and how it is read. | (a) two new region numbers; (b) derived from the existing fields and composites; (c) set by the archetype table of E-10 | open | |
| Q-177-03 | E-22 / S-177 | What winning a settlement's populace means and gives. | (a) holding its ground gives it; (b) fought for by units present; (c) a trading post gives what the settlement has (Q-159-10) | open | |
| Q-177-04 | E-22 / S-177, E-19 | How much more a 4 to 6 player match has (resources, enemies), and what a pair's economy shares with the other pairs of its team. | (a) each pair has its own base and cap and shares nothing; (b) pairs share shipments and technology; (c) one economy for the team | open | |
| Q-178-01 | E-22 / S-178 | What occupying a base is: how many forces, for how long, what ends it. | (a) enemy forces hold the base's central zone for a time; (b) the main building is destroyed or captured; (c) set per archetype | open | |
| Q-178-02 | E-22 / S-178, E-10 | The region follows whoever holds the base at the end: how that meets the "Region transfers to player on" column of E-10 R-073-01. | (a) the holder decides the transfer, replacing the column; (b) the column holds and holding the base adds to the score; (c) set per archetype | open | |
| Q-178-03 | E-22 / S-178 | The cost of falling back to an expansion or forward base. | (a) a lost time before production restarts; (b) lost resources; (c) a lower cap | open | |
| Q-178-04 | E-22 / S-178, E-10 | A side with nothing to fall back to: does the mission end for it, or does the fight go on with what is on the field. | (a) the mission ends and is scored; (b) cut off, production and shipments stop, the fight goes on to the clock; (c) by archetype | open | |
| Q-178-05 | E-22 / S-178, E-10 | Does retaking the original main base lift the partial failure limit. | (a) the limit stays once the base was lost; (b) retaking lifts it | open | |
| Q-179-01 | E-22 / S-179 | The list of doctrines, and what sets the first doctrine. | (a) boom, fortify, press, balanced, set by the player in the lobby; (b) the same list, set by the archetype; (c) the same list, set by the civilization's state | open | |
| Q-179-02 | E-22 / S-179 | The standing habits on a doctrine's checklist and the weights per doctrine. | (a) a short fixed list, weights per doctrine; (b) a list per era pack; (c) set in the lab | open | |
| Q-180-01 | E-22 / S-180, E-16 | The form of the dial and how far it moves spending. | (a) three positions per axis; (b) a continuous slider; (c) one point in a triangle of economy, technology, army | open | |
| Q-180-02 | E-22 / S-180, E-16 | The kinds of request by pointing, and what the rules do with one they cannot carry out. | (a) a fixed list of requests, a ticker line refuses; (b) an open set read by what is at the point; (c) the three examples only at launch | open | |
| Q-180-03 | E-22 / S-180, E-10 | The unit mix per archetype that the rules produce. | (a) a table in the archetype library (E-21); (b) a column in E-10 R-073-02's asset profile; (c) set by the doctrine | open | |
| Q-180-04 | E-22 / S-180, E-16 | When the two switches can be changed, and who picks the mix when the rules do not. | (a) set before the mission only, the commander picks at the building when off; (b) changeable during the mission; (c) set at onboarding and changeable in settings | open | |
| Q-181-01 | E-22 / S-181, E-14 | Whether the enemy-foresight choice is one switch or three (scout, counter, disguise), whether difficulty sets its start, and where it is set. | (a) one switch, in the lobby; (b) three switches; (c) one switch whose default follows difficulty | open | |
| Q-181-02 | E-22 / S-181, E-14 | Whether E-14 R-125-02 ("the macro layer never sees what a player could not see") binds the enemy economy's scouting and counters. | (a) yes, fog-limited like the player's rules; (b) no, the enemy economy reads the true state at higher difficulty; (c) yes, with a limit that widens with difficulty | open | |

Existing flags to re-home in the register (the Epic / Story column changes, nothing else):

| Flag | Now | New home |
|---|---|---|
| Q-159-07 | E-19 / S-159 | E-22 / S-182 |
| Q-159-08 | E-19 / S-159 | E-22 / S-167, S-171 |
| Q-159-09 | E-19 / S-159 | E-22 / S-172 |
| Q-159-10 | E-19 / S-159 | E-22 (listed in the epic's open flags, with the story where each piece would land) |
| Q-159-12 | E-22 | E-22 / S-173 |
| Q-159-13 | E-22, E-02 | E-22 / S-182, E-02 |
| Q-159-14 | E-22, E-10 | E-22 / S-177, E-10 |

## 3. Flags to close

None closed by this epic. Decisions used and already recorded: DECISIONS H2, H4, H5, H6, H7, H11, H13 (the last two live in E-19 and E-17). Q-159-12, Q-159-13 and Q-159-14 stay open; their text carries the story homes above. The closed rows Q-159-01, -02, -03, -04, -05, -06 and -11 cite "E-19 R-159-nn": their cited rule numbers (R-159-03 to R-159-21) no longer exist once E-19 is rewritten. They should cite E-22 stories, for example Q-159-11 should cite E-22 S-177 and S-178, Q-159-02 E-22 S-179 to S-181, Q-159-03 E-22 S-168 and S-180. The same applies to `current_system.md`, which says the epic wins.

## 4. Needs a ledger row

None. `grep -rl "R-159-\|S-159\|Q-159" tests/ csrc/ scripts/` found nothing, so no rule was left untouched. All of R-159-02 to R-159-21 are rewritten into E-22 outright. E-19 S-159 keeps R-159-01 only.

## 5. Findings resolved

From the "Decisions with no home" sections of the four group files. Set L bullets are not economy and were left to their owners.

Group 1 (layers and combat):
- One population cap, workers against unit budgets: done, E-22 S-169, S-167 R-167-04. E-11 and E-13 still need a pointer and the per-unit weight (their drafters).
- Literal workers as units: done, E-22 S-167. E-11 roster membership: flagged Q-167-03.
- Unit roles needing specific resources: flagged Q-159-08, carried in S-167 and S-171.
- Counters between families ("family" undefined): done, S-171 R-171-01, family is the category (DECISIONS H6).
- Production buildings and defenses as things on the map: done for the economy side, S-170 and S-174. Defenses as combatants and blockers: flagged Q-174-02. The route grid changing: S-174 R-174-05, rule in E-13 is left to its drafter.
- Strongpoints at slopes, height bands fitted, ground filling layers, steep ground: cited as living in E-15 (strongpoints) and E-17 (terrain). S-177 points at them.
- Judge items: shipment as unit, flagged Q-176-02. Enemy economy fog, flagged Q-181-02. Workers in "live units" of E-13 R-099-03: S-167 R-167-04 states workers count in the unit budgets, and the E-13 rule is left to its drafter. Family: done.

Group 2 (missions and maps):
- Base kind per archetype and supply distance: done, S-177 R-177-02 and R-177-03, flagged Q-159-14 and Q-177-01. E-10 owns its own table column.
- Original main base caps the result: done, S-178 R-178-06, R-178-07. E-10 S-077 rule left to its drafter. Attacker's original main base: decided (H11) and written. Retaking: flagged Q-178-05.
- What ends or continues a mission when a base falls, fall-back: done, S-178 R-178-04, flagged Q-178-04 for the no-fall-back case.
- Occupying a base: done, S-178 R-178-01, flagged Q-178-01. E-15 S-127 covers structures only, left to E-15.
- Resources limited or abundant, slant, means to do the mission: done, S-177 R-177-06, flagged Q-177-02. "Resource generosity" in E-10 R-080-02 is E-10's.
- Significant resources and economic locations opposite the objective: done, S-177 R-177-04. E-17 placement is E-17's.
- Expansions and forward bases: done, S-175. E-17 sites are E-17's.
- Strongpoints replacing garrisons: cited in E-15 (R-159-17 moved there).
- Blind shipments: done, S-176. Lane output of E-17: flagged Q-174-01.
- Raid lanes: done, S-174, flagged Q-174-01.
- Moving weather: cited in E-15.
- Enemy economy on shared rules: done, S-181. E-14 story for enemy macro around bases, expansions and raids: cited as living in E-14.
- Terrain, bands, landforms, canvas, density field: cited as E-17. Density field Q-166-03 stays E-17's.
- Judge item, workers and shipments home: they are E-22 (S-167, S-176).

Group 3 (simulation):
- Region climate, landform and trouble: derived from the seed for now (H9). Not an E-22 story. Moving trouble is E-15.
- Supply distance: flagged Q-159-14 (S-177).
- Region's situation handed to a mission (richness, base kind, slant): done, S-177 R-177-06, flagged Q-177-02. The E-02 record is E-02's.
- Density inputs from the sim: E-17.
- Shipments whose contents follow the civilization's state: flagged Q-176-01 (not a decision, per the group's note).
- What a mission leaves in the region: S-178 R-178-03 (region follows the holder), flagged Q-178-02. Damage and rebuild: flagged Q-159-13 (S-182). Populace's landing place: flagged Q-177-03.
- Technology choice against the faction's tech number: done, S-173, flagged Q-159-12 (includes the E-06 R-048-02 tension).
- What a pair carries forward: done, S-182, Q-159-07.
- Doctrines against faction archetype: flagged Q-179-01. Doctrines from the civilization's character (E2) were not picked, so S-181 says same rules.

Group 4 (client and hub):
- Economy player's screen, solo commander's controls, choices outside a mission: the rules and the inputs they need are in S-168 to S-181. The screens are E-16's and the lobby and universe lock are E-19's.
- Continuous world and zoom stop: E-16 and E-18.
- Thousands of units: Scale requirements of E-22 state the direction only. E-16 and E-18 budgets are theirs.
- Self-built settlements as spectacle: S-179 R-179-02 states it, drawing is E-18.
- Workers gathering, shipments, weather fronts, disguised buildings drawn: E-18. Weather on the map view: E-16.
- Era pack contents for the economy: flagged Q-168-04 (building set). The rest is E-20.
- Library content for the economy: flagged Q-180-03 (the unit mix per archetype in the library) and Q-179-01.
- Paired mode inside E-19 (shared vision, command set, checksum scope, universe lock, drop-out, team sizes, co-op or versus): E-19's. In E-22: Inputs table says the command set is E-19's to fix. S-181 R-181-05 cites the drop-out.
- Economy seat's identity in the hub and its chronicle character: hub and E-09, left.
- Judge item, the dial against hub principle 6: left, a call for Westley (see section 6).

## 6. Could not do, and notes for the architect

- A tension in the decisions, not resolved. B3 says the rules "do not read the enemy", and D3 says the rules shift production toward what counters enemy units the fog has revealed. S-179 R-179-06 reads B3 as holding "apart from the unit counter shift" of S-180. If D3 was meant to be a separate thing, the architect should confirm.
- Hub principle 6 (opt-in assistive toggles) against the dial, the doctrine switch and the default-on unit-mix behaviours: left for Westley.
- The hub "The Player's Toolkit" paragraph and "Reference Hardware" cite "E-19 S-159"; they should cite E-22 and S-159 for the paired mode.
- E-17 R-166-03 is the source of S-168 R-168-01 (the city reshapes around a placed building). The E-17 drafter should point at E-22 S-168 instead of keeping the rule.
- E-15 R-129-01 is cited from S-167 for workers that cannot fight. If the E-15 drafter renumbers that rule, update the citation.
- B3 and B4 of the base options (a base that travels, the pair's posture) and C3 (a rich resource as a second objective) were not picked and are not in the epic. A4 and A6 likewise. I did not list them under Q-159-10, which the register defines as the build-ons and thinking-ahead options only.
- R-159-01 speed of hand (Q-159-05) stays in E-19 S-159. S-170 lists "a return-to-base ability" as unpicked, which is how the baseline ties to the 1.1x to 1.2x edge.
- The archetype table in R-177-02 is the B1 table as written in `base_and_objective_options.md`. If Westley meant B1 to be only a table form and not those cell contents, the table needs his review.
- "Forward base" is used for two things that the decisions use one word for: a base built near the front (S-175) and the attacker's original main base (S-177, S-178). The epic treats them as one concept. If they are two, one needs a name.
- I did not add the 4-peer scale against teams of 6 (group 4); that is E-19.
