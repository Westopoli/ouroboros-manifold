# Cross-check: Westley's words against what was written (2026-10-01)

Auditor: Sonnet 5.5 (Engineer tier). Nothing outside this file was edited.

## Scope, method, abbreviations

SOURCE A: Westley's verbatim messages M0 to M10 of 2026-10-01 (`scratchpad/westley_2026-10-01_stage1.txt`), plus his 2026-09-30 prompt as quoted in README section 2 (lines 11 to 19). While auditing I found two more verbatim sources of his inside TEXT B: his 2026-09-30 messages quoted at README:304 to 308 (section 6.1, on choke breadth and "units firing"), and the register's quotes of 2026-10-01 answers "1:", "3:", "5: a" and "7:" (REG:33, REG:198, REG:201). They are not in SOURCE A, so I could not check them character for character; I say so wherever it matters.

TEXT B is the list in the brief. File abbreviations: README = `docs/northstar/research/layer_dynamics/README.md`; HUB = `docs/bible/game_bible.md`; E01 = `docs/bible/epics/E-01-layer-system.md`; E12 = `docs/bible/epics/E-12-fog-and-sensors.md`; E17 = `docs/bible/epics/E-17-map-generation.md`; REG = `docs/northstar/ambiguity_register.md`; STO = `docs/bible/stories.md`. Line numbers are as of the audit (main, 1d6c16f).

Status words, Table 1: landed; landed weakened; landed overstated; MISSING. "n/a" marks a question or instruction that needed no text. "Not audited" marks prompt content that lives in sections outside TEXT B.

Source words, Table 2: an M-id; (a) = CLAUDE ADDITION that follows from an existing bible or register rule (named and checked to exist); (b) = CLAUDE ADDITION with no source. Flags: OVERSTATED, CONTRADICTS, or blank.

### Quote check (done with python)

I extracted every quotation of Westley in TEXT B and tested it, as an exact substring, against SOURCE A plus README section 2 (scripts: `scratchpad/qcheck.py`, `q2.py`, `q3.py`). Results:

- Exact, character for character, including his typos: M2 (README:64), M3 twice (README:55, 56), M4 (README:284), M5 whole message (REG:34, equal to M5 as a whole), M6 (README:136; REG:34), M7 seer sentence (REG:35, REG:201), M7 lanes message (REG:204), M8 (README:93), M9 Q3 (README:132), M9 Q4 (README:106), M10 (README:104), "Otherwise your list looks good" (README:136), "quality of the choke" (README:110), "I like C" (README:138). The three 2026-09-30 prompt quotes in REG:198 are exact against README section 2.
- Mismatch 1: README:44 and REG:198 (the "restated" target). Original M1: `"players with better ... much larger force". The goal is to create ... becomes a reality.` The text puts all of it inside one pair of quote marks, with `force. The goal` where the original has `force". The goal`. His closing quote mark is dropped and a sentence he spoke outside his own quote marks is merged into the quotation. He also introduced the quoted part as "something along the lines of", a hedge the text does not carry.
- Mismatch 2: REG:198 dates the "strategic depth" quote (`We'll need to clearly define ...`) as "same date" as the 2026-10-01 items before it. README section 2 dates it 2026-09-30. The words themselves are exact.
- Not checkable against SOURCE A (earlier or other messages): E01:111 and REG:33 (the "going asymmetic" quote; the two copies agree with each other exactly), REG:198 quotes "1:" and "3: a but ...", REG:201 first quote (2026-09-23) and the mention of "5: a".
- Not his words, only scare-quoted: README:102 "side that holds still wins"; README:416 "largest force beaten"; STO:168 to 171 story one-liners.

## Table 1: his words to the text

| id | his words (short quote) | where it landed | status |
|---|---|---|---|
| M0.1 | "why does chaning the seed only change the positions and attack timing?" | README:97 (no dice), README:278 (drops "the proposed randomness knob"). The question itself is never answered or recorded. | landed weakened |
| M0.2 | "shuffle *every* variable, vision, damange, range, literally everything" | README:290 ("Sample every knob together"), README:405 (K1 samples maps from presets), README:410 (K6a samples rule sets). Unit stats (damage, health, range per type) are not named as sampled in K1 or K6a. | landed weakened |
| M0.3 | "find the configurations that lead to the forces winning that align with the pillars/principals" | README:262 to 266 (crossing = region where C0 to C9 hold), README:290 | landed |
| M0.4 | "meausring the margin works" | README:97, README:404 (K0 signed margin) | landed |
| M1.1 | "re-write the plan correctly this time, but use what was built as a starting point" | README:274 (Kept and reused) | landed |
| M1.2 | "Stage 1: re-read the original prompt and clearly define the conditions we're looking for" | README:44 to 46 | landed |
| M1.3 | "players with better understanding of the landscape, unit formation, layer awareness/intentionality, and the other players current position can defeat a much larger force" | README:44 (quote spliced, see Quote check), HUB:76, REG:198. HUB drops "intentionality" and "awareness" ("of the layers"). | landed |
| M1.4 | "The goal is to create a game with significant strategic depth. We get to this goal by tuning all the variables we laid out such that that sentence becomes a reality." | README:44, HUB:76 last sentence | landed |
| M1.5 | "However long we need to clearly define that ... I'm ok with that ... the most important/distinctive part of the game" | Nowhere in TEXT B. (REG:198 carries his 2026-09-23 "most important/unique" in the Q-008-02 question cell, a different message.) | MISSING |
| M1.6 | "Stage 2: assess the current prototype ... 'lines crossing' ... too abstract, we need to make it concrete" | README:258 to 280 | landed |
| M1.7 | "stage 3: modify the prototype accordingly" | README:400 to 412 | landed |
| M2.1 | "Scripted plays (for each skill a skilled play and a naive play)" | README:61, 68, 72 to 89 | landed |
| M2.2 | "About 2x" | README:62 ("First answer: about 2x"); README:138 omits it | landed |
| M2.3 | "Larger force wins, but this is only if both players have exactly the same units, unit formation, vision, layer organization" | README:64. Note C0 (README:117) tests equal-size mirrors, not "identical play, unequal size, larger wins"; R* = 1.0 covers it by implication only. | landed |
| M2.4 | "Hypothetically this situation would *never* happen in the real game ... landscape will be autogenerated and not symmetrical" | README:64 (quoted), README:100 (R0 and premium) | landed |
| M2.5 | "Combinations (each skill alone gives a modest edge)" | README:63, 120 (C3), 121 (C4) | landed |
| M3.1 | "S2 is not just about more units firing at once, it's also about the rock-paper-scissors" | README:56 (quoted), README:53 (S2 row still says "more of them fire at once") | landed |
| M3.2 | "Yes expand this to an S5" | README:56, 87 to 89, HUB:76 | landed |
| M3.3 | "(mark this in memory: ... a "reactive" aspect, have one team or both ...)" | README:58 ("a side re-forms ..."; "one team or both" dropped). Memory file `project_layer_lab_reactive_followup.md` exists and carries "one team or both". | landed |
| M3.4 | "S4 not only shoots first, but induces traps, shoots on purpose with a lesser force to bring the enemies force into a trap" | README:55 (quoted), README:85 (bait) | landed |
| M4.1 | "I like C" (C = singles at 30% or so, full mastery 3x or more) | README:62 ("he chose"), README:138 ("Settled"), README:124 (C7) | landed overstated |
| M4.2 | "but this is abstract and not very functional, and I don't want to have too much of a hard time finding the place where the *lines cross*" | Only inside the quote at README:284. README:62 and 138 present C as a settled choice without it. | landed weakened |
| M4.3 | "start the prototype with 2 variables, tune them ... keep iteratively adding and tuning" | README:290, 294, 411 (adds "and one skill") | landed |
| M4.4 | "I'm ok with implementing two prototypes, one all at once and the other with this strategy" | README:282 to 296, 410, 411 | landed |
| M4.5 | "we can move forward with the plan after that's documented" | README:400 onward | n/a |
| M5.1 | "If both units have the "same" compositions and the vision is constant, both units can just fire back at each other" | REG:34 (quoted), README:136 | landed |
| M5.2 | "units with higher range ... should be weaker to certain things, thus making the advantage temporary" | E01:228 (R-164-03, widened to reach across layers), REG:35 item 6 | landed |
| M5.3 | "the layer system needs to be *utilized* somehow, not just static" | README:136, REG:34 | landed |
| M5.4 | "players have to actively ping specific layers to see vision on that layer" | E01:200 | landed |
| M5.5 | "For eras that don't have technology, we could have them send out little scouts that cost nothing." | E01:203 (R-162-04, as a rule), REG:34 (inside option (a), closed), REG:35 item 2. He said "could"; M6 does not mention scouts. | landed overstated |
| M5.6 | "select specific units, select a "ping" ability, press a layer number and click where they want it to go ... short burst of vision ... for a very short time" | E01:200, 206 | landed |
| M5.7 | "making sure that the *lines cross* when a player effectively uses the pings and swamps a smaller force" | README:136, 276 say the layer actions are needed to measure S3. Nowhere does TEXT B tie the lines-crossing target to effective ping use. | landed weakened |
| M5.8 | "Otherwise your list looks good" | README:66, 136 | landed |
| M5.9 | "Research similar systems ... come up with 2-3 other options other than radar" | README:136 ("After research (queue Q78)"), REG:34 options (b) to (e) | landed |
| M6.1 | "give players all 3: going dark, reach by unit type, and the pinging" | E01:196 to 232, REG:34 answer, README:136 | landed |
| M6.2 | "these options will be free, we want to induce strategic depth" | E01:201, 216, REG:34 ("All three cost the player no resource"). R-164-03 says "no type's reach is free" in another sense (trade-off), which collides with his word. | landed |
| M6.3 | "units will still see others passively, just a shorter range, the pinging can have a much longer range" | E01:200, E01:111, REG:34. REG:35 item 5 reads "shorter" as shorter than today's 0.50 and 0.20, which his words do not say. | landed overstated |
| M6.4 | "alert that they were pinged, and a ~60 degree direction that they were pinged from (like the direction indicator skill from World of Warships)" | E01:202 | landed |
| M6.5 | "Record these as decicions" | REG:34 status closed; E01 S-162 to S-164 | landed |
| M6.6 | "what's next in the plan after that bunny trail" | n/a | n/a |
| M7.1 | ""Mass on one end and roll the line up" idk what this means ... Use a simple text diagram." | README:78 rewords the row ("so only the few defenders at that end can fire, and work along it"). No diagram. No record that he could not picture it. | landed weakened |
| M7.2 | "the pinging should replace the seer, or make the seer really expensive ... record that decision" | REG:201, REG:35 item 7, E12:41, README:91 | landed |
| M7.3 | "Everything else looks good" | README:66 ("accepted by Westley") | landed |
| M7.4 | "mark a potential idea in the bible, not a decision but a potential gamemode ... lanes ... 1.3x ... slowdowns ... 1x ... Only an idea" | E17:129 to 137, REG:204, STO:171 | landed |
| M7.5 | "What's next in the plan?" | n/a | n/a |
| M8.1 | "Yes refusing a fight counts as a counter" | README:93, 123, HUB:76 | landed |
| M8.2 | "a skilled player only takes a battle that they can win, skilled players make it so that the opponent doesn't have a choice" | README:93 (quoted, then "the mark of skill is leaving the opponent no choice") | landed |
| M8.3 | "must have a counter only on most, some situations are unbeatable (like a full surround or a trap where the door gets closed)" | README:93, 123. HUB:76 says "each has an answer on most maps" and drops the unbeatable exception. | landed |
| M8.4 | "1: ending ahead by a margin" | README:99 | landed overstated |
| M8.5 | "2: headcount" | README:98 | landed |
| M8.6 | "3: I'm confused, not enough context" / "4: also confused" | Not recorded as decisions; correctly left to M9. | n/a |
| M9.1 | "Q3: C" (space must pass; land reported, does not block) | README:132 | landed |
| M9.2 | "space doesn't have ramps but it does have very free layers that can be taken advantage of" | README:132 (quoted) | landed |
| M9.3 | "it depends on the number of units that can get shots, not a basic ratio" | README:106, 108, 118, 119, HUB:76 | landed |
| M9.4 | "capture and track the number of units that are able to get shots off on each side, and compare the about of time and number for both" | README:108, 110, 118 | landed |
| M9.5 | "not just that they should do *1.3x* better because it's not as simple as that" | README:106 (quoted). Fixed ratios and bands survive at README:99, 100, 102, 124, 128. | landed weakened |
| M10.1 | "yes it matches, proceed" (to: skill wins the firing count; result follows it; 30% and 3x as rough sizes only) | README:104 (heading), README:42, REG:198. Scope of the confirmation stretched to all of C0 to C9. | landed overstated |
| M10.2 | "30% and 3x as rough sizes only" (in his question, confirmed) | README:128 says so; README:124 (C7) and README:416, HUB:76, E01:150 treat 3x as a bar | landed weakened |
| P1 | 09-30 para 1: player owns the layer; terrain forces auto-transition; "Record that decision." | README:29 (section 3), E01 R-001-05. Outside TEXT B. | not audited |
| P2 | 09-30 para 2: toy prototype, all C, fast, bare minimum visuals, runs unit combinations (position, orientation, damage, health, anything varied in an RTS) | README:7, 398, 144 to 185. Outside TEXT B except README:402 to 412 (K1, K6a sample "every knob"). | not audited |
| P3 | 09-30 para 2: use it as "a map for tuning units across different eras" | Nowhere in TEXT B. README:132 and 4.4 cover only space (Settled Reach) and land maps. | landed weakened |
| P4 | 09-30 para 2: "lines cross" in more than one place gives depth "from two configurations of variables instead of one" | README:262 to 264 redefines crossing as a region and depth as "non-empty and not a knife-edge". The two-configurations idea is not carried. | landed weakened |
| P5 | 09-30 para 2: "algorithms need to be fast"; "just an idea ... verify it works with a simple prototype before we commit" | README:404 (fights per second), README:5 | landed |
| P6 | 09-30 para 3: define strategic depth from SC2: layer advantage shoots unanswered; concave surround wins; formations by unit vulnerabilities and abilities | README:52 to 56, 72 to 89 (layer, concave, formation). Abilities: see P7. | landed |
| P7 | 09-30 para 3: templar "very weak and slow and expensive" but storm devastates low-health units; "A player that effectively protects them has a higher chance of winning" | README:79 (screen of tough units) only. E01:150 puts abilities "outside this bar". README:140 defers P3. His probabilistic "higher chance" is replaced by deterministic margin (README:97). | landed weakened |
| P8 | 09-30 para 3: "map all these dimensions out before we build anything" | README section 5 (outside TEXT B) | not audited |
| P9 | 09-30 para 4: plan "to document the idea in the bible" with "a pass after ... for missed information or hallucinations" | E01:150, 196 to 232, E17:129, REG; this file is the pass | landed |
| P10 | 09-30 para 4: find whether "lines crossing" is evident "(configurations that produce victory from the expected player given the conditions of the engagement)" | README:260 to 266. Expected-winner scenarios live in section 5 (outside TEXT B). | landed |
| P11 | 09-30 para 4: "We don't need to do a large batch of thousands of "runs" ... iteratively try small things, check the output, and tune repetatively." | README:290 (K6a all-at-once), 410 (K6a), 411 (K6b). K6a is the large-batch form; it is licensed by M0 and M4, and README:411 (K6b) carries his iterative form. | landed weakened |
| P12 | 09-30 para 1+: 3D surround theory, aerial-battle research (README:21) | Not in TEXT B | not audited |

## Table 2: the text to his words

| id | claim | location | source | flag |
|---|---|---|---|---|
| T1 | "Stage 1, confirmed by Westley 2026-10-01" | README:42 | M10, which confirmed only the three-part restatement | OVERSTATED |
| T2 | Target sentence given as verbatim | README:44 | M1 (spliced; see Quote check) | |
| T3 | Replaces four test patterns; defined in batches; two numbers remain drafts (share of maps in C8, winning margin) | README:46 | (b) process statement | |
| T4 | S1 landscape: choke, far side of midline, tall cover | README:52 | M1 ("landscape") + (b) examples | |
| T5 | S2 formation: concave, screen | README:53 | 09-30 prompt (surround, protect templar) + M3 | |
| T6 | S3: three layer actions on purpose | README:54 | M6 | |
| T7 | S3: striking force silent, a decoy emits | README:54 | (b); the decoy is not in any of his words | |
| T8 | S4: finds enemy with pings, shoots first, sets traps | README:55 | M3, M6 | |
| T9 | S5 unit-type matchup | README:56 | M3 | |
| T10 | Reactive version wanted after the prototype, if it succeeds; not in this build | README:58 | M3 | |
| T11 | Skill by scripted plays | README:61 | M2 | |
| T12 | Every skill together beats a much larger force; first answer about 2x | README:62 | M2 | |
| T13 | "on seeing that advantages multiply (five skills at 1.3x each combine to 3.7x), he chose to keep each skill at about 30 percent and accept full mastery worth 3x or more" | README:62 | M4 "I like C" ("but this is abstract and not very functional"); the reason "on seeing ..." is Claude's inference; 1.3^5 = 3.71 is correct arithmetic | OVERSTATED |
| T14 | Big upsets need combinations; each skill alone a modest edge | README:63 | M2 | |
| T15 | Identical units, formation, vision, layers: larger wins; "a control, not a scenario" | README:64 | M2 (verified exact) | |
| T16 | Heading "accepted by Westley" for the whole play and counter tables | README:66 | M5 ("list looks good", for the four other skills' plays), M7 ("Everything else looks good"); but in M7 he said he could not picture one row | OVERSTATED |
| T17 | Naive play defined: line abreast, one layer, nearest target, types mixed evenly, no ping, all emitting, same cost, stops at own range | README:68 | M2 asked for a naive play per skill; the content is (b) | |
| T18 | A counter is what the larger side does to pull the edge back; "Later" marks mid-fight orders | README:70 | (b) | |
| T19 | Table rows S1 to S5, skilled plays and counters | README:74 to 89 | M5, M7 acceptance of a draft not in SOURCE A; content (b) | |
| T20 | Row "Mass the whole force on one end of the line ... and work along it" | README:78 | M7: he could not picture it; the reworded row has no recorded acceptance | |
| T21 | Ambush: wait unseen, hold fire till enemy inside concave | README:86 | (b); M3 gave baiting traps only | |
| T22 | "Almost every counter is another skill, which is hub principle 5" | README:91 | (a) HUB:77 principle 5 "counters have counters" exists; "almost every" is (b) | |
| T23 | "The seer is no longer the scouting tool: the ping replaces it, or it stays only at a very high cost" | README:91 | M7 gave "replace" or "really expensive" as an open either-or. A seer kept at high cost is still a scouting tool, so the first clause decides the fork. | OVERSTATED |
| T24 | Refusing the fight counts; mark of skill is leaving the opponent no choice; counter on most maps, not all; closed trap or full surround may have none | README:93 | M8 | |
| T25 | "In the lab the larger side is made to attack ... whether the fight could have been refused is recorded per situation" | README:93, 102 | (b). Conflicts with C6 (README:123, "refusing the fight counts" as a counter that takes the firing advantage back), since the lab never lets the larger side refuse, and no measure of "could have been refused" is defined | CONTRADICTS |
| T26 | Bait and ambush expected to have no counter once sprung | README:93 | M8 (trap, full surround) + (b) for ambush | |
| T27 | Margin = share of A's strength left minus B's; replaces win rate | README:97 | M0 ("margin works") + (b) definition | |
| T28 | R* = enemy force as multiple at which fight is even; 1.3 means 30 percent more army | README:98 | (b) definition | |
| T29 | "The multiple is by headcount (Westley, 2026-10-01)" | README:98 | M8 "2: headcount" | |
| T30 | Both sides field the same mix; cost reported beside | README:98 | (b) | |
| T31 | "The skilled side beats a force when it ends ahead by a margin, not when it wipes the enemy out (Westley, 2026-10-01)" | README:99 | M8 "1: ending ahead by a margin". "Not when it wipes the enemy out" is not in his words. | OVERSTATED |
| T32 | "The size of the margin that counts is set with the bands"; "The bands below are judged on the premium"; "Bands are judged against the line abreast" | README:99, 100, 102 | Stale. M9 Q4 answered the "exact bands" question by rejecting fixed ratios; README:108 says "a skill has no fixed worth"; no bands exist below | CONTRADICTS |
| T33 | Premium = R* / R0 | README:100 | M2 (asymmetry) + (b) | |
| T34 | Skill profile: 5 singles, 10 pairs, 10 triples, 5 fours, full set, plus controls and counters | README:101 | M2 (combinations) + (b) | |
| T35 | Naive ladder: blob, line abreast, "a line that holds still"; this "isolates the "side that holds still wins" effect found in pass 1" | README:102 (and README:298 "the side that holds still wins") | (b). Contradicts the run log: README:440 (A attack-moving against holding B won 60 of 60) and README:455 (with B holding, A wins 200 of 200). The side that held still lost. | CONTRADICTS |
| T36 | "confirmed by Westley 2026-10-01: "yes it matches, proceed"" over the whole of C0 to C9 | README:104 | M10 confirmed the restatement only. C5 "noticeably", C8, C9 and the margin were not put to him | OVERSTATED |
| T37 | Fixed pass marks per skill do not exist; position decides worth | README:106 | M9 | |
| T38 | "a wide choke is worth little, a narrow one a great deal" | README:108 | M9 inference; (b) | |
| T39 | Firing advantage per head, window by window; unit-seconds of fire | README:110 | M9 "amount of time and number" + (b) operationalisation | |
| T40 | A rule set passes when all of C0 to C9 hold across sampled maps | README:113 | (b) | |
| T41 | C0 control: identical forces, mirrored map: R* = 1.0 | README:117 | (b) | |
| T42 | C1 each skilled play wins the firing count | README:118 | M10; README:304 to 308 (09-30). For S5 (type matchup) the effect is damage per hit, not who can fire; see Needs a fix 8 | |
| T43 | C2 result follows firing count; "three times as many units fire holds about three times the force" | README:119 | M10; his 09-30 words at README:304 ("they can take on 3x the force") | |
| T44 | C2: "a damage multiplier, health, raw range" deciding against the firing count fails | README:119 | his 09-30 words at README:308 (a mismatch means "there's a number that's off"). Tension with M3 (S5 is a damage-multiplier effect) is left to Westley | |
| T45 | C3 skills stack | README:120 | M2 | |
| T46 | C4 no dominant skill; C5 no dead skill ("noticeably") | README:121, 122 | (b); "noticeably" is undefined | |
| T47 | C6 counters exist on most maps; refusing counts; sprung trap may have none | README:123 | M8; HUB:77 | |
| T48 | C7 "the skilled side beats three times its number or more (Westley's choice on the band arithmetic)", as a passing condition | README:124 | M4, M10: "30% and 3x as rough sizes only". README:128 itself says "not pass marks" | CONTRADICTS |
| T49 | C8 robust in 80 percent of situations | README:125 | (b), labelled draft at README:46, 128 | |
| T50 | C9 fight length inside E-11 S-085's window | README:126 | (a) E-11 S-085 R-085-01 to 03 exist | |
| T51 | Rough sizes: single skill about 30 percent, full set 3x or more, "not pass marks"; margin a few percent | README:128 | M10 (the sizes); (b) the margin, labelled draft | |
| T52 | Space maps must pass; land maps reported, do not block; space has five free layers | README:132 | M9 | |
| T53 | "Space maps (the launch era: every unit flies, no ramps)" | README:132 | (a) E01 R-001-07 every Settled Reach type flies. But HUB:131 says there are three launch eras (past, present, future) with identical mechanics, so "the launch era" is wrong | CONTRADICTS |
| T54 | Space maps contain obstacles, lanes between obstacles, cover fields | README:132 | (b); M9 said only "very free layers" | |
| T55 | S3 decided 2026-10-01; three actions chosen; lab needs "an emit or silent state per group" | README:136 | M5, M6; "per group" is (b) and is open at REG:35 item 4 | |
| T56 | "Settled 2026-10-01, the band arithmetic ... Westley: "I like C"" | README:138 | M4 "I like C, but this is abstract ...", M10 "rough sizes only". "Settled" overstates | OVERSTATED |
| T57 | Option wording (a) to (c); square law makes advantages multiply | README:138 | (b); header of M4 gives C as "30% or so ... 3x or more" | |
| T58 | P3 "waits until abilities are in scope" | README:140 | (b); his templar example (P7) is deferred without his word | OVERSTATED |
| T59 | "Lines crossing" was his first name; stated as win probability it does not fit; "it never said what a good result looks like" | README:260 | M1 ("too abstract"). His 09-30 text did give a gloss ("configurations that produce victory from the expected player") | |
| T60 | Line, crossing and depth redefined | README:262 to 264 | (b); departs from his two-configurations reading (P4) | |
| T61 | Deliverables (1) to (4) | README:266 | (b) | |
| T62 | Runs so far: "the ramp goes from a win to a wipe-out between slope lengths 150 and 200" | README:268, 280 | (b) from README:513. Pass 5 (README:529 to 536) shows the crossing moves from 162 to beyond 400 with attacker number and defender distance | OVERSTATED |
| T63 | Controls: negative R* = 1.0 within one unit; positive R* well above 1 | README:270 | (b) | |
| T64 | Kept, missing, dropped lists; "Dropped: ... the crossing search built on it; the proposed randomness knob" | README:274 to 278 | (b). The drop of the randomness knob answers M0 only by implication | |
| T65 | Layer actions missing; "the layer skill cannot be measured at all" | README:276 | M6 | |
| T66 | Two searches side by side; quote of M4 | README:282 to 284 | M4 (exact) | |
| T67 | "Start with two variables and one skill" ... "re-measure everything tuned so far" ... "re-tune the smallest set of knobs" | README:290 | M4 gave "2 variables"; the rest is (b) | |
| T68 | Draft order of the incremental track | README:294 | (b), labelled draft | |
| T69 | How the two are compared: passes C0 to C9, fight count, unseen situations, explainability | README:296 | (b); he said "which one performs better for our goals" | |
| T70 | E1, E2 confounded "(the side that holds still wins)" | README:298 | see T35 | CONTRADICTS |
| T71 | Stage 3 table K0 to K7 | README:402 to 412 | (b); K6a and K6b follow M4 | |
| T72 | K2, K3 "Engine change: none" while K2 builds the five slots (where, shape, layer, info, matchup) and README:136 and 276 say the engine needs the ping, emit state and reach table before S3 can be measured. No rung builds them. | README:406, 407 | M5, M6 (the layer actions are his central decision of the day) | CONTRADICTS |
| T73 | "With a 3x-plus target the scan must reach well past 3" | README:416 | (b) from M4; M10 made 3x a rough size | OVERSTATED |
| T74 | Two force sizes per cell; scouting skill given the answer until K5; no cross-layer fire in base rules | README:417 to 419 | (b); (a) Q-008-01 closed in E01:154 | |
| T75 | Guards and guard cells | README:420, 421 | (b) | |
| T76 | HUB: first half of principle 4 (judged by letting better-positioned player beat bigger force; abilities never outrank positioning) | HUB:76 | (a) Q-083-02 (REG:207) exists and says this | |
| T77 | HUB: depth means better understanding of landscape, formation, layers, where the other player is, and which unit types beat which can defeat a much larger force | HUB:76 | M1, M3. "awareness/intentionality" reduced to "of the layers" | |
| T78 | HUB: "What decides an engagement is how many units on each side can get shots off, and for how long: skill is arranging that count in your favour, and the result follows it" | HUB:76 | M9, M10, README:306 ("the differentiator is **can your unit get shots off**"). Tension with M3 (S5 is not about count) is left to Westley | |
| T79 | HUB: "No one kind of understanding is enough. Each is worth what the situation makes it worth" | HUB:76 | M2, M9 | |
| T80 | HUB: "they add up when used together" | HUB:76 | M2; README:62 and 138 say they multiply | |
| T81 | HUB: "each has an answer on most maps (refusing the fight is one)" | HUB:76 | M8 | |
| T82 | HUB: "together, in the best situations, they beat three times the numbers or more" | HUB:76 | M4 and M10: "rough sizes only"; M1 said "a much larger force"; M2 first said "About 2x". A rough size stated as a sacred principle. | OVERSTATED |
| T83 | HUB: "The rules are tuned until this is true" | HUB:76 | M1 | |
| T84 | S-008 end-state: principle 4 holds in the lab before any cross-layer rule enters the sim | E01:150 | (b) | |
| T85 | S-008 end-state: across space maps; each skilled play wins the firing count; result follows; five skills stack, none dominant, none dead; each has an answer on most maps | E01:150 | M9, M10, M8, M2 | |
| T86 | S-008 end-state: "the best situations let a side beat three times its number or more" | E01:150 | see T82 | OVERSTATED |
| T87 | S-008 end-state: "Abilities are outside this bar until they are in scope" | E01:150 | (b); no word from him defers the templar example (P7) | OVERSTATED |
| T88 | S-005 flag: vision symmetric, asymmetry a candidate "on one condition" with quote | E01:111 | REG:33 (agrees exactly); not in SOURCE A | |
| T89 | S-005 flag: passive cross-layer vision stays, shorter than the ping | E01:111 | M6 | |
| T90 | S-006 flag: whether the pulse stays beside the ping | E01:125 | (b); raised as a question, not decided | |
| T91 | S-162 title, story | E01:196, 197 | M5, M6 | |
| T92 | R-162-01: select units, press layer number, click place, see that layer for a very short time, reach much longer than passive | E01:200 | M5, M6 | |
| T93 | R-162-02: costs no resource | E01:201 | M6 | |
| T94 | R-162-03: alert and a sector of about 60 degrees toward where the ping came from, "and nothing more precise" | E01:202 | M6; "nothing more precise" is (b) | |
| T95 | R-162-04: era without technology: small scouts that cost nothing are sent and give the same short view | E01:203 | M5 "we could have them ..."; no word from him confirms; "the same short view" is (b) | OVERSTATED |
| T96 | R-162-05: revealed units are hidden again when the ping ends | E01:204 | (b), follows from "very short time" | |
| T97 | S-162 Outputs: "cooldown state" | E01:207 | (b). Cooldown is only a recommended default at REG:35 (a); not decided | OVERSTATED |
| T98 | S-163 going dark: emitting forces see other layers further and are seen from further; silent forces the reverse | E01:211, 214, 215 | M6 chose "going dark" by name; mechanism is Claude's option (b) at REG:34 | |
| T99 | R-163-03: switch costs no resource | E01:216 | M6 | |
| T100 | S-163 Outputs: on-screen mark of emitting forces | E01:219 | (b) | |
| T101 | S-164 reach by type: layer offsets named per type; no fire outside reach | E01:223, 226, 227 | M6 by name; mechanism (b) from REG:34 option (d) | |
| T102 | R-164-03: "no type's reach is free ... and at least one type fires upward well" | E01:228 | M5 (higher range weaker) concerns range; his "unit ... destroying units from above it" is an example attached to the asymmetric-vision condition (E01:111). Stated as an unconditional rule | OVERSTATED |
| T103 | S-165 travel lanes: tree-like lanes, 1.3 times speed, slowdowns at high ground, 1.0 elsewhere, an idea not a decision | E17:129 to 137 | M7 (all details match) | |
| T104 | Q-165-01 options: separate mode, part of the standard generator, dropped; "as a mode or as part of every map" | REG:204, E17:137 | M7 said "potential gamemode"; options (b) and (c) are (b) | |
| T105 | Q-E12-01 closed: ping is how a player sees far; seer dropped or very costly | E12:41, REG:201 | M7. The either-or stays open at REG:35 item 7 | |
| T106 | Q-005-03 question and options (a) to (e), with precedents | REG:34 | M5 (quote exact) + (b); the research file `docs/legacy/topics/active_layer_vision_mechanics.md` exists | |
| T107 | Q-005-03 answer: (a), (b), (d) together; free; passive stays shorter; alert and 60-degree sector; pickets not chosen | REG:34 | M6 (exact quote) | |
| T108 | Q-005-03 answer: option (a) "eras without the technology send small free scouts" counted as chosen | REG:34 | see T95 | OVERSTATED |
| T109 | Q-005-04 item 5: "how much shorter passive cross-layer vision becomes than today's 0.50 and 0.20" while recommended default (a) says "passive factors start at today's values" | REG:35 | M6 ("just a shorter range", unspecified). Item 5 presupposes a cut from today; default (a) assumes none | CONTRADICTS |
| T110 | Q-005-04 items 1 to 7, recommended defaults (a) | REG:35 | (b), labelled open and recommended | |
| T111 | Q-005-04 item 7 quote "or make the seer really expensive" | REG:35 | M7 (exact) | |
| T112 | Q-E12-01 answer: quote of M7; "Earlier ... ("5: a")" | REG:201 | M7 (exact); the "5: a" reference is not in SOURCE A | |
| T113 | Q-165-01 quote | REG:204 | M7 (exact) | |
| T114 | Q-008-02 Answer cell: 09-30 prompt quotes | REG:198 | README section 2 (exact) | |
| T115 | Q-008-02 Answer cell: "On what strategic depth is ..., same date, verbatim" with "same date" = 2026-10-01 | REG:198 | README:15 to 17 dates the quote 2026-09-30 | CONTRADICTS |
| T116 | Q-008-02 Answer cell: "Its conditions, confirmed the same day, are in the lab README section 4" | REG:198 | M10 (restatement only) | OVERSTATED |
| T117 | Q-008-02 Answer cell: quotes "1:" and "3: a ..." | REG:198 | not in SOURCE A; README:371, 373 repeat them | |
| T118 | STO rows S-162 to S-164: one-liners, "Spec'd, blocked on Q-005-04"; S-165 "Deferred (Q-165-01)" | STO:168 to 171 | (a) matches E01:14, E01:208, 220, 232, E17:137 | |

## Summary

Table 1 (70 rows): landed 45 (of which 4 are prompt rows); landed weakened 11; landed overstated 5; MISSING 1 (M1.5); n/a 4 (conversational); not audited 4 (prompt content outside TEXT B).

Table 2 (118 rows): OVERSTATED 18; CONTRADICTS 9; blank 91. Of the blanks, 44 carry a (b) CLAUDE ADDITION source with no flag because they are labelled drafts, definitions or method, or are open questions.

Quote check: no word changed in any verbatim quote; two mismatches in quote marks or dating (README:44 and REG:198 splice the target quote; REG:198 misdates the strategic-depth quote), several quotes not checkable against SOURCE A.

Worst findings:
1. The 3x figure is stated as a sacred principle (HUB:76), an acceptance bar (E01:150) and a passing condition (README:124, C7), while M10 confirmed "30% and 3x as rough sizes only" and README:128 itself says "not pass marks".
2. No rung in the Stage 3 table builds the three layer actions (README:406, 407 say "Engine change: none"), although README:136 and 276 say the layer skill cannot be measured without them.
3. "Confirmed" and "Settled" are stretched beyond what he said: M10 confirmed only the restatement, M4 was "I like C, but this is abstract and not very functional"; and scouts (a suggestion, "we could") are written as rule R-162-04 and counted as chosen in the closed Q-005-03.

## Needs a fix

1. HUB:76, last-but-one sentence. "together, in the best situations, they beat three times the numbers or more" turns a rough size into a sacred principle. M10 confirmed "30% and 3x as rough sizes only"; M1 said "a much larger force". Replace with: "together, in the best situations, they beat a much larger force. About three times the numbers is a rough size to aim at, not a pass mark."

2. README:124 (C7), E01:150, README:416. 3x used as a bar or target. C7 also contradicts README:128 ("not pass marks"). Replace C7 with: "The ceiling is high: in the best situations, with every skill used, the skilled side beats a much larger force (about three times its number is a rough size, not a pass mark)." E01:150: "...and the best situations let a side beat a much larger force." README:416: "With a high ceiling as the target (about 3x as a rough size) the scan must reach well past 3."

3. README:62 and README:138 ("he chose", "Settled 2026-10-01"). Replace the README:62 clause with: "Asked about the band arithmetic he answered "I like C" (singles of about 30 percent, full mastery worth 3x or more), added "but this is abstract and not very functional", and then confirmed 30 percent and 3x as rough sizes only." In README:138 replace "Settled" with "Answered", and end with: Westley: "I like C", with the qualification quoted at README:284.

4. README:42, README:104, REG:198 ("confirmed"). The confirmation (M10) covered only: skill wins the firing count, the result follows it, 30 percent and 3x as rough sizes only. Replace README:42 with "(Stage 1; the restatement around units firing confirmed by Westley 2026-10-01)", README:104 with "(restated around units firing; the restatement confirmed by Westley 2026-10-01: "yes it matches, proceed")", and REG:198 "Its conditions, confirmed the same day" with "Its conditions, of which the restatement around units firing was confirmed the same day, are in the lab README section 4."

5. README:99. Delete ", not when it wipes the enemy out". His words were "1: ending ahead by a margin". Replacement: "The skilled side beats a force when it ends ahead by a margin (Westley, 2026-10-01: "ending ahead by a margin")."

6. README:99, 100, 102 (stale "bands"). M9 Q4 removed fixed bands. Replace README:99 last sentence with "The size of the margin that counts is a draft (section 4.3)." README:100 last sentence with "The premium is reported beside the firing advantage (section 4.3)." README:102 last sentence of the ladder with "Conditions are judged against the line abreast."

7. README:102 and README:298 ("the side that holds still wins"). The run log says the opposite: README:440 (the attack-moving side won 60 of 60 against a holding line) and README:455 (A wins 200 of 200 with B holding). Replace with: "the last isolates the effect found in pass 1, where a line that holds still is out-shot by a line that converges on it" and, at README:298, "(a holding side is out-shot by a converging one)".

8. README:118 and README:119 against M3 (S5). Not a wording fix: C1 and C2 say every skill is judged by units firing, but S5 (rock-paper-scissors) acts through damage per hit, and the last sentence of C2 fails a rule set whose result is decided by "a damage multiplier". His 09-30 "units firing" message and his M3 both stand. Needs a Westley ruling; add a register row and until then mark C1 and C2 "for S5: open" rather than guessing.

9. README:93, 102, 123 (refusing the fight). Replace the README:93 sentence "In the lab the larger side is made to attack ... recorded per situation" with: "In the lab the larger side is made to attack, so refusing the fight cannot be played as a counter there; C6 is checked for the other counters, and how refusal is to be checked is open." Then add a register row.

10. README:91, last sentence. Replace with: "The ping is the way to see far; the seer is dropped, or stays only at a very high cost (Westley, 2026-10-01, 7: "the pinging should replace the seer, or make the seer really expensive"; `Q-005-04`)."

11. E01:203 (R-162-04), REG:34 answer, REG:35 item 2. Scouts were a suggestion ("we could have them send out little scouts that cost nothing"). Replace R-162-04 with: "Given an era without the technology for a ping, When the player pings, Then, if the era uses scouts (proposed, not decided; Westley, 2026-10-01: "we could have them send out little scouts that cost nothing"), small scouts that cost nothing carry the ping [Q-005-04]." In REG:34 change "eras without the technology send small free scouts" in the answer text to say scouts are a proposal that stays open in Q-005-04.

12. E01:207. Delete "cooldown state" from the S-162 Outputs, or write "cooldown state, if Q-005-04 adopts one".

13. E01:228 (R-164-03). Replace with: "Given the roster, When reach is assigned, Then a type that reaches further is weaker to something another type does, so its advantage is temporary (Westley, M5), [Q-005-04: the weaknesses]. Whether one type must fire upward well is open; Westley raised it as an example, conditional on asymmetric vision (E01:111)." Change "no type's reach is free" so it does not collide with his "free" (M6).

14. README:91, README:66 (T16, T20, M7.1). README:66 heading: replace "accepted by Westley" with "accepted by Westley in outline, 2026-10-01 (M5, M7)". README:78: keep the gloss and add the simple text diagram he asked for in M7, or record that the diagram was shown in chat and which version he accepted.

15. README:268 and 280 (ramp). Replace "the ramp goes from a win to a wipe-out between slope lengths 150 and 200" with "for ten attackers against ten defenders the ramp goes from a win to a wipe-out between slope lengths 150 and 200, and the crossing moves with attacker number and defender distance (pass 5)".

16. README:406, 407 (K2, K3). Add a rung, or change "none" in K2, so the ping, the emit or silent state and the per-type reach table are built before the layer skill is measured. Wording: "K2: engine change: the aimed ping, emit or silent state, and reach by unit type (E-01 S-162 to S-164, `Q-005-04`)." Without it, the layer skill (and the S4 ping half) cannot be measured, as README:276 itself says.

17. README:132 ("the launch era"). Replace with "(the Settled Reach: every unit flies, no ramps)". HUB:131 has three launch eras.

18. README:58. Add "one team or both" to match M3: "a side, or both, re-forms during the fight ...".

19. REG:198 dates. Replace "same date" before the strategic-depth quote with "2026-09-30". Fix quote splice at README:44 and REG:198: put the closing quote mark after "much larger force" and the next two sentences as a second quotation, and keep his words "something along the lines of" with the first.

20. REG:35 item 5 versus its default (a). Item 5 reads "shorter" as shorter than today. His M6 words were "units will still see others passively, just a shorter range, the pinging can have a much longer range". Replace item 5 with: "(5) how short passive cross-layer vision is, against the ping's reach, and whether it changes from today's 0.50 and 0.20".

21. README:140, E01:150 ("Abilities are outside this bar", "P3 waits"). He gave the templar example as part of what strategic depth looks like. Replace with: "Abilities (the templar example) are not yet in the lab; whether they are in the acceptance bar is open for Westley." Add a register row if wanted.

22. HUB:76, "they add up when used together" against README:62, 138 ("multiply"). Low priority. Pick one word; his words were "Combinations" (M2).

23. Lower-priority gaps (Table 1): M1.5 (his license to take as long as needed, "most important/distinctive part of the game") is nowhere; M0.1 and M0.2 (his wish to shuffle every variable, vision, damage, range, and the seed question) are met only by README:290 and K1 and K6a; P3 and P4 (tuning across eras; more than one crossing gives depth) are weakened. Suggested: add one sentence at README:46 recording M1.5 and one at README:290 saying the all-at-once search varies unit stats (damage, health, range, vision) as well as map and rule knobs, if that is what he meant.
