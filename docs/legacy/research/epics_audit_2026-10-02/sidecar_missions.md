# Sidecar: E-10, E-14, E-15 (drafter for missions)

Files written: `docs/bible/epics/E-10-missions.md`, `E-14-enemy-macro-behavior.md`, `E-15-reinforcement-supply-and-hazards.md`. Stories S-210 to S-219 are all used. Every existing rule in the three epics is cited by a test, by `csrc/` or by `scripts/` (checked with the brief's grep for every rule id), so no existing rule text was changed. Direction changes are one-line notes under the story heading, and the decided behaviour is in new stories.

## 1. Catalog rows for `stories.md`

| S-210 | E-10 | "Each side starts from the base its situation calls for: the archetype and the supply distance decide it, and an attacker gets a supplied forward base." | Design decided 2026-10-02, not scheduled (Q-159-14, Q-210-01 to Q-210-06) | `epics/E-10-missions.md` S-210 |
| S-211 | E-10 | "The resources on the map fit the situation, tilted toward the better position, and I always have the means to do the job." | Design decided 2026-10-02, not scheduled (Q-211-01 to Q-211-04) | `epics/E-10-missions.md` S-211 |
| S-212 | E-10 | "Losing my main base costs me the result, never better than partial failure, but I can fall back to what I still hold." | Design decided 2026-10-02, not scheduled (Q-212-01 to Q-212-05) | `epics/E-10-missions.md` S-212 |
| S-213 | E-10 | "A mission starts with technology that follows the civilization only slightly, so there is still room to climb." | Design decided in part 2026-10-02, not scheduled (Q-213-01, Q-159-12) | `epics/E-10-missions.md` S-213 |
| S-214 | E-10 | "More players on the team means a bigger map, more enemies and more resources: 64,000 wu for 4 to 6." | Design decided 2026-10-02, not scheduled (Q-214-01, Q-214-02) | `epics/E-10-missions.md` S-214 |
| S-215 | E-14 | "The enemy runs an economy on my rules, richer by difficulty, farsighted only if I choose." | Design decided 2026-10-02, not scheduled (Q-125-03, Q-215-01 to Q-215-04) | `epics/E-14-enemy-macro-behavior.md` S-215 |
| S-216 | E-14 | "The enemy defends its bases, falls back to what it holds and raids my workers and shipments." | Design decided 2026-10-02, not scheduled (Q-216-01 to Q-216-03) | `epics/E-14-enemy-macro-behavior.md` S-216 |
| S-217 | E-14 | "The enemy moves between layers, pings and goes quiet as I can." | Design decided 2026-10-02, not scheduled (Q-217-01) | `epics/E-14-enemy-macro-behavior.md` S-217 |
| S-218 | E-15 | "Strongpoints stand at the slopes between height bands; hold one and I hold the way up or down and produce on that band, paid for by my economy." | Design decided 2026-10-02, not scheduled, land maps only (Q-218-01 to Q-218-06, Q-166-02) | `epics/E-15-reinforcement-supply-and-hazards.md` S-218 |
| S-219 | E-15 | "My region's trouble travels across the map where both sides see it and shuts down what it passes over." | Design decided 2026-10-02, not scheduled (Q-219-01 to Q-219-04) | `epics/E-15-reinforcement-supply-and-hazards.md` S-219 |

Status annotations for existing rows (stories keep their titles; the catalog status can say "Spec'd; direction changed 2026-10-02, rewrite pending"): S-073 (map from terrain, not library), S-075, S-077, S-120, S-125, S-126 (its quote, "A fifth of my force is given; the rest I take from the region's garrisons and hold", describes today's built rules; S-218 holds the direction), S-128, S-131.

## 2. Register rows for new flags

| Q-210-01 | E-10 / S-210 | Which cells of the base-kind table (option B1, `economy_design/base_and_objective_options.md`) are confirmed? Westley picked the approach "B1+2"; no cell was confirmed individually. | (a) confirm the table as offered; (b) confirm row by row; (c) replace it | open | |
| Q-210-02 | E-10 / S-210 | How do the archetype and the supply distance together decide a side's base kind? | (a) the archetype table gives the kind and the supply distance only chooses whether the base generates on site, is supplied or both; (b) the supply distance picks among alternatives inside the archetype's row; (c) other | open | |
| Q-210-03 | E-10 / S-210 | Which side attacks in each archetype, and what is the original main base of a side that neither attacks nor defends (Siege Breaking, Interception, Containment, Suppression, Counterinsurgency, Rear Guard / Evacuation)? Only "attackers get a forward base, and it is their original main base" is decided. | (a) the base each side starts with is its original main base in every archetype; (b) only attackers have one, and a defender's original main base is its home city; (c) Westley names it per archetype | open | |
| Q-210-04 | E-10 / S-210, S-211, S-079 | Does the briefing tell the player each side's base kind and the resource situation, and where, given that S-079 has exactly Situation, Objective and Assets and the controls Accept and Refuse? | (a) inside Situation; (b) inside Assets; (c) S-079 changes | open | |
| Q-210-05 | E-10 / S-073, S-210 | With no skeleton library, how does an archetype shape a map generated terrain-first (R-073-03)? | (a) the archetype sets only objectives, base kinds and forces and the terrain comes from the region; (b) the archetype adds conditions the generator must meet (a choke, a slope); (c) the archetype biases the landform | open | |
| Q-210-06 | E-10 / S-079, E-19 S-159 | Which economy settings (doctrine, the economy-military dial, the two unit-mix toggles, enemy foresight) are chosen per campaign, per mission or live, and where does E-10 receive them? | (a) campaign start, with difficulty; (b) per mission at the briefing; (c) live, per setting | open | |
| Q-211-01 | E-10 / S-211 | Which parts of the simulation's situation decide limited or abundant resources, and how large is the slant toward the better position? | (a) the region's deficit fields of S-072; (b) the supply distance only; (c) a new region field | open | |
| Q-211-02 | E-10 / S-211, S-074 | How is "the player always has the means" guaranteed, and how does it sit beside the 20 percent unit shortfall of R-074-05 and the parity floor of 0.75? | (a) the generator checks that the starting force plus reachable resources can reach the objective; (b) a floor on the player's share of the resources; (c) the parity floor alone | open | |
| Q-211-03 | E-10 / S-211 | For each archetype, where does the objective sit against each side's base and the significant resources? | (a) as option C2 of `base_and_objective_options.md`; (b) a table per archetype from Westley; (c) left to the generator | open | |
| Q-211-04 | E-10 / S-211, S-080 | Who owns "resource generosity" in R-080-02: difficulty, the situation's slant (S-211), or the enemy's prosperity (E-14 S-215)? | (a) difficulty acts through parity only (Q-080-03 (a)), the slant and prosperity are separate; (b) difficulty also scales the player's resources; (c) other | open | |
| Q-212-01 | E-10 / S-212 | If a side retakes its original main base before the mission ends, does the partial-failure cap lift? | (a) never, the cap holds once the base is lost; (b) lifts if the side holds it at the end; (c) lifts on retaking | open | |
| Q-212-02 | E-10 / S-212, E-14 S-216 | When a side loses its base and holds no expansion or forward base, does the mission end at once and get scored, or go on with what is on the field? Option A3 says "with none, A1 or A2 applies"; the pick was "A3+5" and did not choose. | (a) ends at once (A1); (b) goes on, cut off from production and shipments (A2); (c) depends on the archetype | open | |
| Q-212-03 | E-10 / S-212, S-078 | How does a base held by the other side at mission end relate to the region's ownership (R-078-04, which follows the archetype's transfer column)? Option A5 says the region follows whoever holds the base at the end. | (a) the holder of the base decides and the transfer column goes; (b) the transfer column decides and the base only caps the band; (c) both are needed | open | |
| Q-212-04 | E-10 / S-212, S-077 | Do workers and units made during the mission count in deployed power and surviving power for retention (R-077-01)? | (a) only the starting force counts; (b) every unit made counts in both; (c) workers are excluded, made units counted | open | |
| Q-212-05 | E-10 / S-212, S-075 | What is "the player's force eliminated" (R-075-07) when units are gone but a base with production and workers remains? | (a) eliminated only when no units, workers or producing buildings remain; (b) field units only, as today; (c) no units and no base | open | |
| Q-213-01 | E-10 / S-213 | How slightly is a mission's starting technology derived from the faction's 0 to 100 technology level (E-06 S-045), and how does that number map to the era's levels (for example 1 to 5)? | (a) start at the era's lowest level and add one for the most advanced factions; (b) a small bounded offset from the era's middle level; (c) Westley sets a table | open | |
| Q-214-01 | E-10 / S-214 | How do enemy force, the amount to do and the resources scale with the player count (2, 4, 6)? | (a) in step with the player count; (b) in step with the number of pairs; (c) set by the simulation | open | |
| Q-214-02 | E-10 / S-214, E-19 | In a team of 4 or 6, does each pair have its own objective and parity, or does the team share one? | (a) one shared objective, enemies scale; (b) each pair has its own objective (a pair as a sub-civilization); (c) the archetype decides, as Multi-Front Defense has two | open | |
| Q-215-01 | E-14 / S-215 | What is the default of the enemy-foresight choice, and is it made per mission, per campaign or live, and where does E-10 receive it? | (a) off by default, set at campaign start; (b) per mission at the briefing; (c) live like the doctrine | open | |
| Q-215-02 | E-14 / S-215, E-15 S-128 | Which doctrine does the enemy's economy run and who picks it, and how do the doctrine and the script's target ratio (E-15 S-128) together decide its unit mix? | (a) the script names a doctrine per archetype and the target ratio gives the mix; (b) the doctrine decides the mix and the ratio goes; (c) difficulty picks the doctrine | open | |
| Q-215-03 | E-14 / S-215, S-125 | How do enemy foresight (the player's choice) and the enemy's multi-layer intelligence (scaled by difficulty, R-125-01) relate? | (a) independent; (b) hard difficulty turns foresight on; (c) one scale | open | |
| Q-215-04 | E-14 / S-215 | Does the macro evaluation budget (10 forces, 1,000 units, 1 ms) hold when the enemy also runs an economy and thousands of workers? | (a) keep it and count the economy apart; (b) set a new budget; (c) run the economy on a slower period | open | |
| Q-216-01 | E-14 / S-216 | Are defending a base, founding an expansion and raiding among the five behaviours of R-120-01, new behaviours, or the economy rules' business? | (a) the five stay and the economy rules own expansions and raids; (b) new behaviours are added; (c) defend a base uses the existing defend | open | |
| Q-216-02 | E-14 / S-216 | Who decides where and when the enemy expands and builds production forward? | (a) the economy rules by doctrine; (b) the behaviour script per archetype; (c) both, the script naming the push and the rules the site | open | |
| Q-216-03 | E-14 / S-216 | Does enemy raiding on workers and shipments need foresight on, since shipments are blind? | (a) raids are scripted and independent of foresight; (b) raiding needs foresight on; (c) workers can be raided without it, shipments only with it | open | |
| Q-217-01 | E-14 / S-217, E-13 | How do the economy's orders (build, train, gather) enter the command vocabulary and the replay stream? | (a) added to the player command set; (b) a separate economy channel logged in the same stream; (c) other | open | |
| Q-218-01 | E-15 / S-218 | How many strongpoints, at which slopes and with which starting owners, when the fitted relief gives few or many slopes, and do R-126-01's count and archetype split still apply? | (a) one per slope; (b) R-126-01's count capped by the slopes there are; (c) a fixed number per pair of bands | open | |
| Q-218-02 | E-15 / S-218 | What does holding a strongpoint do to passage at its slope, beyond giving production on that band? | (a) nothing beyond a position to fight from and production; (b) the holder crosses freely and the other side must fight to; (c) other | open | |
| Q-218-03 | E-15 / S-218, S-127 | Can the economy rebuild a destroyed strongpoint, against R-127-03 "never rebuilt"? | (a) never; (b) rebuilt at a speed that follows the economy; (c) it falls to rubble and can be refounded | open | |
| Q-218-04 | E-15 / S-218, S-126 | Does the split of R-126-04 (a fifth given at the start, the rest from structures; Q-127-01) survive now that the economy makes units? | (a) kept; (b) dropped, with the situation (S-211) deciding; (c) Westley sets a new split | open | |
| Q-218-05 | E-15 / S-218, S-130 | May a strongpoint drift off its slope (R-130-01 lists the reinforcement structure as a drifting node)? | (a) no; (b) only along its slope; (c) yes | open | |
| Q-218-06 | E-15 / S-218, S-131 | What is the name and the silhouette of a strongpoint, given Q-131-01 settled on "Settlement" and E-17 and E-22 use "settlement" for the neutral populace and for self-built cities? | (a) strongpoint; (b) Settlement; (c) strongpoint for the mechanic with an era-skinned visual | open | |
| Q-219-01 | E-15 / S-219 | Which environmental troubles exist, which region gets which, in each era (the space era included, Q-166-02), and what do seasons add? | (a) one per climate and landform pairing, authored per era pack; (b) a small fixed list; (c) generated from the seed | open | |
| Q-219-02 | E-15 / S-219 | What is a trouble's path and speed, is its path shown ahead, and does fog hide it? | (a) ping-pong or loop on a drift spec (E-17 R-118-01); (b) a one-way front across the map; (c) other | open | |
| Q-219-03 | E-15 / S-219 | What does "shut down" mean for a unit, worker, shipment, building and production site, and what keeps working? | (a) movement and production stop, sight stays; (b) everything stops; (c) it differs per trouble | open | |
| Q-219-04 | E-15 / S-219, E-12 | Is the sensor interference zone one of the troubles or a separate hazard that stays? | (a) one of the troubles; (b) a separate hazard that stays; (c) it goes | open | |

Carried, already in the register: Q-159-14 (supply distance), Q-159-12 (what technology does), Q-125-03 (see section 3).

## 3. Flags to close or update

- Q-125-03 (E-14): not closed. Its candidate (a), "prosperity through reinforcement structures and rate", is stale because prosperity is now the enemy economy's resources (E-14 S-215). Update the candidate. Its second half, which layer-aware behaviours the macro layer may use per difficulty, is still open and now also governs which layer commands S-217 allows.
- Q-127-01 (closed, 20 percent start): still stands as the answer for today's built rules; whether it survives is the new Q-218-04.
- Q-131-01 (closed, one structure called Settlement): still stands for today's rules; the new Q-218-06 asks about the name "strongpoint".
- Q-119-02 (E-17, open): the landscape design's second mockup review answers it (no skeleton library). This belongs to the E-17 drafter; E-10 S-073's note depends on it.
- Q-159-11 is closed already; E-10 S-210 and S-212 are where its answer lands.
- Q-129-01, Q-131-01 (E-15), Q-120-01, Q-125-01 (E-14) are closed in the register but still sit in the epics' "Open ambiguity flags" lines. I left them (outside the findings rows).

## 4. Needs a ledger row (tested rules whose direction changed; text left untouched, note under the story heading)

- E-10 R-073-03 (layout library against terrain-first generation).
- E-10 R-075-07 (mission end; a fallen base does not always end it).
- E-10 R-077-02 (the cap at partial failure after the original main base is lost).
- E-14 R-120-02 (retreat to a held base, not always the spawn edge) and R-120-04 with its invariant line (layer and economy commands).
- E-14 R-125-01 and R-125-02 (a third difference, the player's foresight choice).
- E-15 R-126-01, R-126-02, R-126-03, R-126-04, R-126-06 (strongpoints, paid production, retooling takes time, the 20 and 80 split).
- E-15 R-128-02 and R-128-03 (counter-shift only with foresight on, reading only what was seen).
- E-15 R-131-02 (one hazard type against several region troubles).

Tested, flagged only, no decided direction yet: E-15 R-127-03 (Q-218-03), R-130-01 and R-130-03 (Q-218-05), E-10 R-077-01 (Q-212-04), R-078-04 (Q-212-03), R-080-02 (Q-211-04), R-074-05 (Q-211-02).

## 5. Findings resolved (`group_2_missions_maps.md`)

E-10
- S-077 cap: done (S-212 R-212-01; note under S-077); flagged Q-210-03, Q-212-01.
- S-075 R-075-07 mission end: done (S-212 R-212-02, R-212-03, R-212-06; note under S-075); flagged Q-212-02, Q-212-05.
- S-073 R-073-01 base column: done as S-210 R-210-02, with the table flagged Q-210-01 (the tested table is untouched).
- S-072 to S-073 supply distance: flagged Q-159-14 (carried) and Q-210-02; stated in S-210 R-210-01.
- S-073 R-073-03 layout library: note under S-073; flagged Q-210-05; Q-119-02 left to E-17.
- Base against objective: done (S-211 R-211-03); flagged Q-211-03.
- S-079 briefing: flagged Q-210-04, Q-210-06 (S-079's rules are tested and unchanged).
- Inputs, onboarding row: new input rows added; the onboarding row is E-08's; flagged Q-210-06.
- S-080 R-080-02 generosity: done as a pointer; flagged Q-211-04.
- S-074 R-074-05: done as a pointer in S-074 and S-211; flagged Q-211-02.
- S-077 R-077-01 retention: flagged Q-212-04 (S-212 R-212-07).
- S-078 R-078-02, R-078-04: pointer; flagged Q-212-03.
- Outputs, mission setup row: done (rewritten).
- Purpose and Depends on: done (a sentence on bases; E-19 S-159 and E-22 added). "No shopping for forces" left, still true.

E-14
- No enemy economy story: done (S-215).
- S-125 R-125-01, R-125-02, Q-125-03: note under S-125; done in S-215 R-215-02 to R-215-04; flagged Q-215-03, Q-125-03 (see section 3).
- S-120 behaviours without a base: done (S-216); flagged Q-216-01 to Q-216-03.
- S-120 R-120-04 and invariant: done (S-217, note under S-120, the invariant line rewritten); flagged Q-217-01.
- S-123 R-123-03 wrong-ways line: done as a pointer (E-12 R-093-02) on that line.
- S-120 R-120-02 re-targeting: done as a See also (E-11 R-087-04, E-13 R-096-02).
- S-120 defend and the guard stance: done as a See also; no flag, the movement plan holds the question.
- Depends on, E-15 ratios: done in Depends on; flagged Q-215-02.
- Gate table counts: corrected to the actual rule counts.

E-15
- S-126 free garrisons (known): done (note updated; S-218 R-218-03, R-218-04).
- S-126 R-126-01 count and placement: S-218 R-218-01; flagged Q-218-01.
- S-126 R-126-04 split: S-218 R-218-06; flagged Q-218-04.
- S-126 R-126-03 retooling: note and S-218 R-218-04.
- Purpose and Obviously working: done (the Purpose rewritten; Obviously working keeps "built today" and adds "decided, not built").
- S-127 R-127-03 rebuild: See also; flagged Q-218-03.
- S-127 capture of a base: left, E-22 S-178 owns occupying a base (pointer in S-127).
- Expansions and forward bases: left, E-22 S-175 owns the rule (pointer in Depends on).
- Blind shipments: done as a pointer (S-129 R-129-06; E-22 S-176 owns the rule).
- Moving regional weather (known): done (S-219); R-131-02 note under S-131; flagged Q-219-01 to Q-219-04.
- S-131 R-131-02 and Purpose: note under S-131; Purpose rewritten.
- S-130 drifting structures: flagged Q-218-05 (R-218-07, See also in S-130).
- S-128 counter-shift: note under S-128; E-14 S-215 R-215-05.
- S-129 workers: done (R-129-05).
- S-131 readability and naming: done (R-218-08, R-219-06); flagged Q-218-06.
- Depends on, E-19: done.
- Cross-cutting parity P4 against terrain-first: left (the tactical-port plan and the E-17 drafter own it; the S-073 note points to terrain-first).

## 6. Could not do

- The old gate-table counts (E-10 44 rules, E-14 30, E-15 33) did not match the files (48, 22, 25). I wrote the real counts and did not hunt for the cause.
- Q-121-01 is closed in the register but E-14 R-121-01 and R-121-05 still carry it. Both rules are tested, so I left them; the findings file noted it as outside the brief.
- Where the briefing and the settings choices live (Q-210-04, Q-210-06) could not be written as rules because S-079 is tested and its controls are decided as Accept and Refuse only.
- E-22 does not exist yet, so every E-22 story is cited by number only (S-167, S-169, S-170, S-173 to S-181) and not checked against its text.
- I did not add the stories-catalog or register rows to their files (not mine to touch); they are above.
