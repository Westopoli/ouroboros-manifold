# Sidecar: simulation epics (E-02 to E-08), 2026-10-02

Stories used: S-220 to S-228. S-229 unused.

## 1. Catalog rows for `stories.md`

| S-220 | E-02 | "What I did in a mission shows in the region when I come back." | Direction decided in part 2026-10-02, not scheduled; Q-220-01, Q-220-02, Q-159-13 | `epics/E-02-region-fields-and-drift.md` S-220 |
| S-221 | E-02 | "Each region has its own climate, landform and trouble, derived from the seed, with no change to the region record." | Design decided 2026-10-02, not scheduled; Q-221-01, Q-221-02 | `epics/E-02-region-fields-and-drift.md` S-221 |
| S-222 | E-02 | "A settlement grows in step with how its region is doing." | Decided in part 2026-10-02, not scheduled; Q-222-01, Q-166-03 | `epics/E-02-region-fields-and-drift.md` S-222 |
| S-223 | E-03 | "The galaxy says how far a mission's region lies from the civilization." | Term undefined, not scheduled; Q-159-14 | `epics/E-03-world-generation.md` S-223 |
| S-224 | E-03 | "A 400-region galaxy starts within a time Westley has confirmed." | Open; Q-224-01 | `epics/E-03-world-generation.md` S-224 |
| S-225 | E-04 | "The history I read agrees with the ground I fight on." | Open; Q-225-01, Q-225-02 | `epics/E-04-events-and-chains.md` S-225 |
| S-226 | E-05 | "A faction's standing in the galaxy carries into the economy it fights with." | Open; Q-226-01, Q-226-02 | `epics/E-05-faction-agents-and-conflict.md` S-226 |
| S-227 | E-06 | "A mission starts from the faction's technology, only slightly." | Decided in part 2026-10-02, not scheduled; Q-227-01 to Q-227-03, Q-159-12 | `epics/E-06-diplomacy-and-technology.md` S-227 |
| S-228 | E-08 | "My pair is part of the chapter, the ledger and the world." | Direction decided 2026-10-02, not scheduled; Q-228-01, Q-228-02 | `epics/E-08-generational-structure.md` S-228 |

## 2. Register rows for new flags

| Q-220-01 | E-02 / S-220 | When a side's base of operations is occupied in a mission, or its original main base is lost (E-19 R-159-14), what does the simulation record, if anything? Today a mission changes a region only through four field deltas and, for a transfer band, ownership (E-10 R-078-01, R-078-04). | (a) nothing beyond the field deltas and ownership already there, the outcome resolver encodes the result in them; (b) the region record gains base state, a contract change first, counted against the 2,048-byte region budget; (c) recorded in the ledger and chronicle only, not in the region | open | |
| Q-220-02 | E-02 / S-220 | Where does a populace contested in a mission (E-19 R-159-10) end up in the simulation? | (a) it moves the region's population or tension fields; (b) it changes the region's ownership; (c) nowhere, it is mission-only | open | |
| Q-221-01 | E-02 / S-221 | Deriving a region's climate, landform and trouble from the seed: does it draw from the world generation's random stream, which would extend the draw order of R-022-04, or is it derived on its own from the seed? | (a) derived on its own, the draw order and R-021-10 are untouched; (b) drawn after the last existing draw, the order is extended by contract; (c) decided with the E-17 generator | open | |
| Q-221-02 | E-02 / S-221 | Do empty-tier regions have a climate, landform and trouble, or only inhabited ones? | (a) every region has them; (b) inhabited regions only; (c) decided with the mission generator, since a mission region may be empty | open | |
| Q-222-01 | E-02 / S-222 | Which simulation numbers beyond the region's economy feed the density target of self-built settlements: the region's population, the owning faction's age (the phase label, E-07 S-053), anything else? | (a) economy only (as option 3A reads it) and the mission clock; (b) economy and population; (c) economy, population and age | open | |
| Q-224-01 | E-03 / S-224 | What is the generation time budget at 400 regions? 5 ms was confirmed at 110 regions; the range is now [250, 400]; the governing budget (a 150-tick jump at 400 regions under 2 s) stands separately. | (a) scale linearly, about 18 ms; (b) keep 5 ms at 400; (c) drop the micro budget and fold generation under the governing figure | open | |
| Q-225-01 | E-04 / S-225 | Does a region's environmental trouble (E-19 R-159-12) have any effect in the strategic simulation, such as an event template or trigger, or is it tactical only? The launch library is closed at 26 templates. | (a) tactical only; (b) a new template family that reads the trouble; (c) decided with E-17 and the weather design | open | |
| Q-225-02 | E-04, E-17 / S-225 | Do the "events" that time settlement growth in waves (E-17 R-166-03) mean E-04 events (strategic, one chain per region-year) or in-mission events (a shipment arrives, an expansion is founded, a season turns)? | (a) in-mission events only; (b) E-04 events only; (c) both | open | |
| Q-226-01 | E-05, E-22 / S-226 | Does a faction's strategic budget, economy or technology tier set the economy a side fights with in a mission, and if so how? The budget today sets only the enemy's power (E-10 R-074-01). Includes whether the economy multiplier of E-06 S-046 is read. | (a) not at all, the mission's economy is set by the mission alone; (b) the faction's economy and tier set the starting scale; (c) other, with the economy design | open | |
| Q-226-02 | E-05, E-22 / S-226 | Does a faction's archetype, weights or confidence link to the doctrine that runs its economy (E-19 R-159-18, R-159-21), for the enemy and for the player's civilization? | (a) no link, doctrine is chosen apart from archetype; (b) archetype sets the enemy's default doctrine; (c) other, with the doctrine design | open | |
| Q-227-01 | E-06 / S-227 | How is a mission's starting technology derived "only slightly" from the faction's technology level (DECISIONS H4)? | (a) a fixed small offset in the era's levels; (b) a proportion of the faction's number that moves the starting level by at most one; (c) decided with what technology does (Q-159-12) | open | |
| Q-227-02 | E-06 / S-227 | Does anything the pair reaches in a mission flow back into the faction's technology number, and does Knowledge Lost (R-045-07) touch a mission's technology? | (a) nothing flows back, the two are independent; (b) the mission's result nudges the faction's number; (c) decided with Q-159-12 | open | |
| Q-227-03 | E-06 / S-227 | How do the three tiers of R-048-01 relate to an era's range of levels (for example 1 to 5)? | (a) tiers stay the sim's coarse reading, levels are the mission's finer scale; (b) the tiers become the levels; (c) decided with Q-159-12 | open | |
| Q-228-01 | E-08 / S-228 | In a team, how do the second player, the economy seat of a pair, and each sub-commander enter the chapter record, the ledger and the character selector, given one commander per chapter today? | (a) only the commanding seat of a pair has a ledger character, the economy seat has none; (b) every player has a ledger character and a lineage; (c) other | open | |
| Q-228-02 | E-08, E-05 / S-228 | How does a pair, a sub-civilization inside the over-arching civilization (DECISIONS H7), map onto a simulation that has one faction per civilization? | (a) onto the chapter only, the simulation keeps one faction; (b) onto a set of regions of the faction; (c) onto its own faction | open | |

Existing flags cited, no new row: Q-159-07 (E-22 S-182), Q-159-12 (E-22 S-173), Q-159-13 (S-220, E-22 S-182), Q-159-14 (S-223, E-22 S-177), Q-166-03 (S-222).

## 3. Flags to close

None of the flags already in the register closes by this pass. For the register's own tidying (not decided by me): Q-048-01, Q-056-01 and others listed under "Could not do" are marked closed in the register while their epics still show them open.

## 4. Needs a ledger row

Tested rules whose direction changed (note added under the story heading, text untouched):
- R-048-01, R-048-02, R-048-03 (E-06 S-048): tier is a pure function of the faction's technology number and units use the tier profile when the next mission generates its forces. Direction changed by DECISIONS H4 and Q-159-12 (a mission's starting technology is derived only slightly from the simulation's; what technology does is undecided). Tests: `tests/csim/test_E06_S048_three_tiers_of_technology.py`, `csrc/diplomacy.c` cites R-048-02.

Tested rules watched, no direction change decided, so no note of that form (a plain pointer line added instead, rule text untouched): R-064-02, R-064-03 (E-08 S-064, true while Q-159-07 is open; if (a) or (b) is chosen they need a ledger row then), R-055-02 and R-055-03 (E-08 S-055), R-046-05 (E-06 S-046, Q-048-01), R-012-01 (E-02 S-012, "exactly" stands per DECISIONS H9), R-021-10 and R-022-04 (E-03, unchanged unless Q-221-01 is answered (b)). The E-03 scale line (a 110-region timing, tested in `tests/csim/scale/test_scale_E03.py`) keeps its number; its flag is Q-224-01.

## 5. Findings resolved (group_3_simulation.md rows)

1. E-02 R-012-01 climate and landform: done, E-02 S-221 and the Purpose paragraph (record unchanged per H9); flagged Q-221-01, Q-221-02.
2. E-02 mission leaves base, populace, damage: done, E-02 S-220 and the Inputs note; flagged Q-220-01, Q-220-02, Q-159-13.
3. E-02 drift and rebuild at the civilization's pace: flagged, Q-159-13 in S-220 R-220-04; no drift rule changed (no decision).
4. E-02 outputs and consumers: done, two new Outputs rows and the Depends on entries (E-10, E-17, E-22).
5. E-02 which numbers feed density: done, E-02 S-222 (economy and mission clock per option 3A); flagged Q-222-01 for population and age.
6. E-02 memory budget: done, pointer in Scale requirements (about 440 bytes of headroom, R-220-05).
7. E-03 draw order and output column: done, pointer under Outputs; flagged Q-221-01.
8. E-03 supply distance and landform relief: done, E-03 S-223 (hop count is the only measure defined; Q-159-14 held by E-22 S-177). Landform is the E-02 S-221 derivation.
9. E-04 environmental trouble as an event: flagged, Q-225-01 (S-225); library untouched.
10. E-04 "events" in R-166-03: flagged, Q-225-02.
11. E-05 conquest against base occupation: done, S-226 R-226-03 (separate today; Q-220-01 holds the link).
12. E-05 budget against mission economy: flagged, Q-226-01 (S-226); also pointer in E-06 S-046.
13. E-05 archetype against doctrine: flagged, Q-226-02.
14. E-06 R-048-02 against in-mission technology: tested, so note under S-048 plus new S-227 (R-227-01, R-227-02); what technology does is Q-159-12 via E-22 S-173; mapping flagged Q-227-01.
15. E-06 sim technology against mission technology: done, E-06 S-227; flagged Q-227-01, Q-227-02, Q-227-03.
16. E-06 R-046-05 and Q-048-01: done, pointer in S-046 Open flags (E-22 economy is a possible consumer, Q-226-01).
17. E-06 tier against the layer lab's same-mix measure: left. No rule here reads the measure, and tier profiles (E-11 R-082-08) change HP and damage, not the mix of unit types, so a pointer would assert something no decision states. The layer lab README section 4 already names its own conditions.
18. E-07 phase label and density: done, pointer in S-053 Outputs; flagged Q-222-01.
19. E-07 populace and allegiance: done, pointer in S-050 Outputs; flagged Q-220-02.
20. E-08 pair carry-forward in S-064: done, note under the S-064 heading (Q-159-07, E-22 S-182, save and trace); rule text untouched.
21. E-08 R-064-03 unlock types: done, same note.
22. E-08 R-064-02 nothing carries from surviving units: done, same note.
23. E-08 jump length "short" or "long": flagged, Q-159-13 (pointer in S-056 Open flags); no rule keyed to length (no decision). Q-056-01 is shown open in the epic but closed in the register, see Could not do.
24. E-08 R-055-03 field changes the only channel: done, pointer in S-055 Open flags to S-220.
25. E-08 R-055-02 strategic sim stopped: done, same pointer (the in-mission economy is part of the mission).
26. E-08 one commander per chapter against a pair: done, E-08 S-228; flagged Q-228-01, Q-228-02; E-05 Inputs note.

Decisions with no home, from the findings file: region climate, landform, trouble (S-221); supply distance (S-223, E-22 S-177); a region's situation handed to a mission (Outputs row, E-22 S-177 holds richness and base kind); density inputs (S-222); shipments' contents following civilization state (left, E-10 S-074 "what the civilization can spare" is the nearest home, no decision, belongs to E-22 S-176 and E-10); what a mission leaves (S-220); technology choice (S-227); what a pair carries (E-22 S-182, E-08 S-064 note); doctrines against archetype (S-226).

Also fixed in passing (untested prose): E-03 "Obviously working in 60 seconds" said 60 to 110 regions, now 250 to 400; E-03 Scale requirements lost its stale re-timing history and carries the 110-region test point with Q-224-01. Gate verdict lines of all seven epics now say the new stories have not been through the gate.

## 6. Could not do

- Folding closed register flags that the epics still show as open. The register marks these closed while E-06, E-07, E-08 and E-05 still print them as open flags or "code uses X" text: Q-042-01 (a), Q-043-01 (b, a story to add), Q-045-01 (c), Q-048-01 (a, wire the multiplier into ALG-05; R-046-05 says nothing consumes it), Q-049-01 (b), Q-050-01 (a), Q-052-01 (a), Q-054-01 (a), Q-056-01 (a, uniform [20, 100]; R-056-01 says "code uses a fixed 50"), Q-057-01 (declined), Q-058-01, Q-060-01 (b, per tick, against R-060-04 which says end of jump), Q-062-01, Q-063-01 (c), Q-063-02 (set once at campaign creation, against R-063-03), Q-036-02 (b, no reservation, epic says the tests assume (a)). Nearly all the rules involved are cited by tests, and some answers are code and test work, so this is a fold pass of its own, not part of this brief. The gate verdicts "not passed, blocked on N flags" in E-06, E-07 and E-08 are stale on that account.
- E-08 Scale requirements still time a 100-tick jump on 60 regions while the governing budget (E-03 Scale requirements, Q-021-08) is 150 ticks at 400 regions; tested thresholds, left.
- E-03 generation budget at 400 regions: needs Westley (Q-224-01).
- E-22 stories are cited by number only; E-22 does not exist yet, so S-173, S-177, S-179, S-181 and S-182 are cited from the brief's allocation table.
