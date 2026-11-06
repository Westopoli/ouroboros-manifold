# Westley's answers to the audit's holes, 2026-10-02

Verbatim:

"H1: I haven't designed how we're going to resolve the landscape engine against space eras, but it's going to be a sister system, same generative style just different objects/outcome. Asteroid fields, open sections, places where you can cross over from upper to lower layers like an ice lake, this needs more design work so we can't write stories for it. Mark it in the repo/memory as something we need to design after we finish this story/epic round. H2: Yes, we're going to start with 2 simple factions/eras, one in space and one on land, the units and rules for them will be essentially the same, but the landscape/visuals will be different. H4: missions starting tech is derived from the simulations tech level, but only slightly. We'll have a wide range of different tech levels per-era, but if it's a range between 1 and 5 in a normal timed single match you'll only have the time to go up 1-2 levels. (starcraft 2 equivalent tech-up across tech levels), what tech will do exactly is undecided, mark that as something that needs designing. H3: idk in what *supply distance* is. H5: Yes, this is already recorded/decided somewhere in the repo, find it. H6: yes the three categories. H7: Yes, more teammates = bigger maps and more to do, more resources, more enemies, each player is their own "sub-commander" and we can fabricate "alliances" where each pair of players is their own "sub-civlization" inside the over-arching civlization. essentially the game turned up to 11. H8: Depends on the situation, this is simulation work that is tbd, mark it as such. H9: derived from seed for now. H10: attackers get a *forward* base from which they produce and recieve resources from supply lines, this is documented/decided already somewhere. H12: confused about this question. H13: 64k if there's 4-6 players. H14: Yes, subject to change. - Old epics should be updated to be consistent with the new decisions."

## Recorded as

| Hole | Answer | Status |
|---|---|---|
| H1 space maps | The space landscape is a sister system: the same generative style with different objects and outcome (asteroid fields, open sections, places to cross between upper and lower layers, like an ice lake). Not designed yet. No stories are written for it in this round. | To design after this round: Q-166-02 |
| H2 walking units | Two simple factions and eras at the start, one in space and one on land. Units and rules essentially the same; landscape and visuals differ. | Decided |
| H3 supply distance | Westley does not know the term. It came from option B2, which he picked with B1. Definition offered to him; until he confirms, it is a flag. | Q-159-14 |
| H4 technology | A mission's starting technology is derived from the simulation's technology level, only slightly. An era has a wide range of levels (for example 1 to 5); a normal timed single match has time to go up one or two. What technology does is undecided. | Decided in part; what technology does: Q-159-12 |
| H5 workers | Found: workers count against the one population cap (E-19 R-159-05, 2026-10-01, "thousands of units/workers") and are units that cannot fight (E-15 S-129). They are units, counted in the cap and the unit budgets. | Decided |
| H6 unit families | The three categories: Strike, Line, Siege. | Decided |
| H7 team sizes | Teams of 2, 4 and 6 stand. More teammates means bigger maps, more to do, more resources and more enemies. Each player is a sub-commander; each pair is a sub-civilization inside the over-arching civilization. | Decided; lockstep's peer count must follow |
| H8 damage across time jumps | Depends on the situation. Simulation work, to be decided. | Q-159-13 |
| H9 region climate, landform, trouble | Derived from the seed for now. No change to the simulation's region record. | Decided |
| H10 density field in the sim or on screen | Not answered: the reply under "H10" answers H11. | Q-166-03 |
| H11 original main base for an attacker | Attackers get a forward base, from which they produce and to which resources come by supply lines. That forward base is the attacker's original main base. | Decided |
| H12 fitted bands and fixed numbers | He asked for the question to be explained. | Q-166-04 |
| H13 canvas | 64,000 wu when there are 4 to 6 players. Smaller matches keep today's sizes. | Decided |
| H14 asking by pointing from the map view | Yes, allowed; subject to change. | Decided |
| The rewrite | "Old epics should be updated to be consistent with the new decisions." | Go |

# Second set of answers, 2026-10-02

Verbatim:

"1: keep 2: affects play, but we need to be careful for it not to be annoying for the player, let's make sure there are natural paths through it for armies/units. 3: scales with height and let's measure it with the lab. 4: Yes 5: two things two names 6: looks good, no changes needed 7: not necessarily replaces the layout library. The terrain engine will need to account for the layouts, the layout design we have is good, especially the moving objectives. The new ideas add on to the old, not necessarily remove. Both can be built at the same time, it's just a slightly more complex system that needs the rules defined before it can be built. 8: your side can't see it's own shipment on the way, no vision at all, no indiciation it was killed 9: we can keep 4, so long as more is marked as a desired future feature. 10: $15 gets you 3-5 eras to start of, each new era is $3-5."

## Recorded as

| # | Question | Decision | Flag |
|---|---|---|---|
| 1 | Supply distance | Kept. It is the number of regions between the mission's region and the nearest region the civilization owns. With the archetype it decides the kind of base: in an owned region a base that generates on site, next to one a base with both, deep in foreign ground a base that lives on shipments. | Q-159-14 closed. The thresholds in regions are not given and stay a flag where the rule sits. |
| 2 | Self-built city | It affects play: dense districts slow units and give cover. It must not be annoying: there are natural paths through a settlement for armies and units. | Q-166-03 closed |
| 3 | Fitted bands | The cost of a layer step scales with its height, and the skill lab measures it. | Q-166-04 stays open as a lab measurement: how each number scales |
| 4 | Counter what has been seen | Yes. It is the one exception to the rules having no foresight. | none |
| 5 | Forward base | Two things, two names. The attacker's starting base, supplied by supply lines, is the **forward base** (Westley's word, DECISIONS H10). Production an economy builds near the front or at an expansion is **forward works** (the name the option had when he picked it). The partial-failure cap concerns the forward base when it is a side's original main base, never forward works. | names are the architect's choice from words already used; Westley may rename |
| 6 | Archetype-to-base table | Confirmed as written. | Q-210-01 closed |
| 7 | Layout library | Not replaced. The terrain engine accounts for the layouts; the layout design is good, the moving objectives especially. The new ideas add to the old. Both can be built together. The rules for how terrain and layouts combine must be defined before building. | Q-119-02 closed with this answer; how they combine is Q-191-04 |
| 8 | Blind shipments | A side cannot see its own shipment on the way. No vision at all, and no indication that it was killed. | Q-238-02 closed |
| 9 | Peers | 4 stays. More than 4 is a desired future feature. | Q-241-03 closed |
| 10 | Price | $15 buys 3 to 5 eras to start. Each new era is $3 to $5. The first build still starts with two eras, one in space and one on land (H2). | Q-149-03 closed |
