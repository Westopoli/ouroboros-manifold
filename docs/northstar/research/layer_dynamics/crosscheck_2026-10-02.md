# Cross-check, 2026-10-02: Westley's words against the layer-dynamics README and the skill-lab brief

Audited text (read from origin/main, not the working tree): `docs/northstar/research/layer_dynamics/README.md` (all), `docs/northstar/plans/2026-10-02-skill-lab-cascade.md` (sections 0, 1, 2, 4, 5 decided/said sentences, wave order and invariant paragraph, 6, 7). Source: his messages M0 to M19 of 2026-10-01, the 2026-09-30 prompts quoted in the history file section 2, and the existing bible and register where a rule is cited. Line numbers are lines of those files on origin/main.

Quote check, by script: every sentence in quotation marks that the text attributes to Westley was compared character for character against his messages (and, for earlier messages that are not in the 2026-10-01 file, against the verbatim quotations in `history_2026-09-30_to_10-01.md`). 31 quoted strings checked in the README, 8 in the brief that matter. Zero mismatches on anything attributed to him. Two README quotes (line 15 "the number that we really care about ..." and line 17 "a number that's off") are not in the 2026-10-01 file; they match the history file's verbatim quotations of his 09-30 and early 10-01 messages (history lines 385 and 320), which could not be re-checked against his original text. One quoted string is not his and has no source: README line 56 "16 beat 17 and lose to 18." (see T2-A20).

## Table 1: his words to the text (M11 to M19, plus earlier items the text now drops or weakens)

| id | his words | where it landed | status |
|---|---|---|---|
| T1-01 | M11: "it doesn't read well, I had to stare at it to figure out what it meant, research similar data sets and find out how they visualize it, research/scientific papers might be a good source." | README:79 (quote), README:87 (research file); brief:119 | landed |
| T1-02 | M12: "looks much better, especially the top graphic that makes it very clear." | README:79 (quote cut after "top graphic"); brief:119 "Form approved by Westley" with five bullets | landed overstated: he praised the redraw and named only the top graphic; "approved" and the full bullet list (light and dark, table under each chart, plain-words column, no scatter plot) are not in his words |
| T1-03 | M12: "make sure it's not doing too much all at once (small batches of iteration from original plan), and have it send you a report when it's done." | README:77 "Small batches", README:9, README:126 | landed (the message-the-lab-chat part was superseded by M13) |
| T1-04 | M13: "the relaying between the two of you is less efficient than you just running the tests yourself and reporting directly back to me ... Take over the testing" | brief:7 "runs the experiments", brief:135 | landed |
| T1-05 | M13: "if you need anything built you can message the other chat" | brief:7 "It does not build", brief:8 | landed (route to builder is now via Westley and a conducting chat, M19) |
| T1-06 | M14: "yes get the lab chat to make solid terrain block sight." | README:113 to 114, brief:172 (G2), brief:186 (G3) | landed |
| T1-07 | M14: units "constantly attempt to find the shortest path forward to a unit in it's vision ... This will effect the outcome ... we should just build the full blown prototype, render an assessment of that opinion." | README:105 to 107 (real engine, acquire, anchor, leash), README:148 | landed |
| T1-08 | M14: "Yes a guard stance is fine" | nowhere in README or brief as an instruction; README:148 only lists "no stance between never moving and chasing" as a toy lesson | MISSING (low: the toy is frozen and the real engine has its own anchor and leash; but his yes is not recorded) |
| T1-09 | M14: "I'm confused about your reach question, are you saying the range isn't long enough for a lot of units to attack?" | README:148 states "reach of only four unit-widths, so few units can focus one spot" | landed |
| T1-10 | M15: "yes to the real engine, so long as we can accomplish the original goal from the original plan." | README:105 (exact quote) | landed |
| T1-11 | M15: "Go back and re-read our conversation, the core pillars of what we decided with regards to unit firing, and what actions a skilled player can take and what the result should be." | README:13 to 51 (principle, five skills, plays, counters) | landed |
| T1-12 | M15: "The *lines* can cross in multiple locations, there may be configurations where health/range/vision/ping distance is much higher/lower but the expected behavior is exhibited." | README:11 (exact), README:18, README:127 | landed |
| T1-13 | M15: small batches "that produce output that both of us can read (using the visual artifact style you produced and more if the type of data we're looking at changes)" | README:77 to 87 (adds more forms at 85); brief:117 to 125 pins one form | landed weakened in the brief: no allowance for a new chart form when the data type changes |
| T1-14 | M15: "Use TDD, manager-mode methods." | brief:11 to 19, README:123, README:125 | landed |
| T1-15 | M15: "we need to condense the main points into the plan and record them to the repo so that they persist for future chats." | README (whole), history file, this brief | landed |
| T1-16 | M16: "Build the gaps into the real engine, in order." | README:109 to 118, README:125 (G0 to G7 in order), brief:137 to 139 | landed |
| T1-17 | M16: "Accept the recommended starting values as provisional" | brief:261, README:161, register Q-001-05 and Q-005-04 | landed overstated in brief:261 to 278: the specific numbers in the table are presented under his acceptance (see T2-B17) |
| T1-18 | M16: project.godot change: "Discard it." | brief:38 "Westley restores the stray `project.godot` change himself" | landed weakened: he decided it is discarded; the brief makes the action his chore, which he did not say |
| T1-19 | M16: naive play: "Both, reported side-by-side." | README:30 (blob and line abreast, side by side); brief:102 (plays.py ladder) | landed (blob / line abreast are the option labels; not in his typed words) |
| T1-20 | M16: Mac and Linux "easily portable ... our branches can effectively be merged without too much of a mess ... accounts for the disparity in operating systems and git worktrees/branches." | README:131 to 140, brief:30 to 38 | landed |
| T1-21 | M17: "Every G doesn't need it's own cascade, it can be done all in one." | brief:139 (exact), README:125 | landed |
| T1-22 | M17: "Use manager-mode-lite (sonnet subagents for everything, shard test writers and auditors)." | brief:13 (exact), brief:15 to 19 | landed (the bullets beneath add more than he said; see T2-B7) |
| T1-23 | M17: "Why do you have part 4 (small batches) before part 5 (fixing the engine gaps)? I would think the small batches would happen after the engine has been fixed." | README:124 to 126; brief:133 to 135 | landed |
| T1-24 | M17: "Pop out of plan mode to answer it, do'nt write the answer into the plan" | No rationale for the order is written in either file. README:124 gives a one-clause purpose for the controls batch ("to prove the harness and keep a before-picture") | landed (borderline: that clause is a purpose, not the answer to his question) |
| T1-25 | M18: "yes reorder it" (skill batches after the engine cascade, only a controls batch before it) | README:124 to 126; brief:133 to 135 | landed |
| T1-26 | M19: "I want you to do the designing/documenting part" | brief:7 | landed |
| T1-27 | M19: "when we're ready for the cascade I want you to pass me the plan file and I'll have another chat conduct the cascade and report to you." | brief:3, brief:8, brief:286 to 288, README:129 | landed (the brief says the conducting chat "runs two cascades"; he said "the cascade"; see T2-B4) |
| T1-28 | M2: larger force for all skills together: "About 2x." | README:16 and README:71 say "about three times"; no 2x anywhere in README or brief | MISSING (his M2 figure is dropped; M4 "I like C" and M10 "yes it matches" moved the rough size to 3x or more, and the history records the 2x, but the current-state README does not) |
| T1-29 | M2: with equal play "Larger force wins, but this is only if both players have exactly the same units, unit formation, vision, layer organization. Hypothetically this situation would *never* happen in the real game ..." | README:15 last sentence (contradicts, see T2-A8); README:64 C0 band | MISSING (the larger-force-wins rule and his "never happens" remark are not stated; history:64 has them) |
| T1-30 | M4: "I'm ok with implementing two prototypes, one all at once and the other with this strategy and see which one performs better for our goals." | README:127 (two ways side by side) | landed weakened: "see which performs better for our goals" is dropped |
| T1-31 | M7: "'Mass on one end and roll the line up' idk what this means, I can't picture what the formation you're thinking of is. Use a simple text diagram." and "Everything else looks good." | README:30 "accepted in outline"; README:38 keeps the mass-on-one-end counter | landed overstated: no later acceptance of that counter is in his words |
| T1-32 | M9 Q3 C: "a rule set must pass on space maps; land maps are reported but don't block" (option text; his reply "Q3: C") | README:58 "Land maps ... are measured and reported"; brief:284 puts land eras, walking units and slopes out of scope | landed weakened: nothing in the plan measures land maps; the gap is not stated |
| T1-33 | M5/M6: scouts "that cost nothing" for eras without the technology | brief:256 (proposal, out of cascade); not in README | landed (brief only) |

## Table 2: the text to his words

Source codes: M-id = his message; EARLIER = 2026-09-30 prompts; R = bible or register rule (verified with git show); CA = CLAUDE ADDITION. Flag column: OVERSTATED, CONTRADICTS, or blank.

| id | claim | location | source | flag |
|---|---|---|---|---|
| T2-A1 | Goal sentence "players with better understanding ... much larger force" | README:7 | M1 (verbatim; he introduced it as "something along the lines of") | |
| T2-A2 | "The goal is to create a game with significant strategic depth ..." | README:7 | M1 (verbatim) | |
| T2-A3 | Original request: simulator varying position, orientation, damage, health, vision, landscape; "lines cross"; small steps; quote "I think it'd be much faster ..." | README:9 | EARLIER (verbatim) | |
| T2-A4 | "The *lines* can cross in multiple locations ..." | README:11 | M15 (verbatim) | |
| T2-A5 | What decides a fight is units able to fire, and for how long | README:15 | EARLIER; M9 ("the about of time and number") | |
| T2-A6 | "the differentiator is **can your unit get shots off**" | README:15 | EARLIER (verbatim) | |
| T2-A7 | "the number that we really care about is number of units firing, if A and B both have the same number of units firing than the engagement ends up even" | README:15 | history:385 (his early 10-01 words); not in the M0 to M19 file | |
| T2-A8 | "An even exchange is not an even outcome when one side has more in reserve." | README:15 | CA (toy finding, history:496); sits directly after his quote that even firing means an even engagement | CONTRADICTS |
| T2-A9 | "A skill has no fixed worth"; quote "it depends on the number of units that can get shots ..." | README:16 | M9 Q4 (verbatim, ellipsis skips one sentence); M10 | |
| T2-A10 | About 30 percent for one skill, about three times for all five, rough sizes not pass marks | README:16 | M4 "I like C", M10 "yes it matches"; M2 said "About 2x" and it is not mentioned | OVERSTATED (presents 3x as the settled size, drops his first answer 2x; see T1-28) |
| T2-A11 | "Unit type is the one other factor", quote "not just unit values but their type as well" | README:17 | EARLIER (quote verbatim); "the one other factor" is CA | OVERSTATED |
| T2-A12 | Any other number deciding a fight against the firing count, "such as a damage bonus for height or raw health", is "a number that's off" | README:17 | history:320 "there's a number that's off" (his words); the examples are CA; M15 lists health, range, vision as knobs to tune | OVERSTATED (examples are not his; health is one of his tuning knobs) |
| T2-A13 | More than one configuration can work | README:18 | M15; EARLIER | |
| T2-A14 | Five skills table and its quoted sources | README:22 to 28 | M1, M3 (verbatim; S3 three actions from M6) | |
| T2-A15 | Naive play measured two ways, blob and a line abreast, "(Westley, 2026-10-01)" | README:30 | M16 "Both, reported side-by-side"; labels from the options he was shown | |
| T2-A16 | Plays and counters "accepted in outline" | README:30 | M5 and M7 "Everything else looks good"; but M7 "idk what this means" for README:38 and no later yes | OVERSTATED |
| T2-A17 | S2 counter "Mass the whole force on one end of the line ..." | README:38 | M7 (he could not picture it); CA | OVERSTATED (listed as accepted) |
| T2-A18 | Refusing a fight is a counter, quote; counter needed on most maps not all, quote | README:51 | M8 (verbatim) | |
| T2-A19 | After the prototype, if it works, a reactive version | README:51, README:101 | M3 | |
| T2-A20 | Break-even "16 beat 17 and lose to 18." in quotation marks | README:56 (and chart label README:82) | CA: an invented example in quote marks, in a file where quote marks otherwise mean his words; not in his messages or the history | OVERSTATED |
| T2-A21 | Beating means "ending ahead by a margin", by headcount | README:56 | M8 Q1 and Q2 (verbatim); "same mix of unit types" and "not a wipe-out" are CA | |
| T2-A22 | Units firing recorded per side, weighted by type | README:57 | EARLIER; M9 | |
| T2-A23 | Space maps must pass, land maps measured and reported | README:58 | M9 Q3 C; but brief:284 excludes what land maps need | OVERSTATED (see T1-32) |
| T2-A24 | Draft pass marks "that Westley has not yet confirmed" | README:60, README:161 | honest; matches that none were confirmed (history:140 lists only C8 80 percent and the winning margin as drafts shown to him) | |
| T2-A25 | C0: mirrored fight even, break-even between 0.9 and 1.1 of equal numbers | README:64 | CA draft; M2 Q3 says the larger force wins when sides are equal (history C0 was R* = 1.0) | CONTRADICTS (band lets 14 beat 16 or 17 lose to 16 and still pass) |
| T2-A26 | C1: firing advantage of at least 1.2 on at least 80 percent of maps | README:65 | CA draft; M9 Q4 "not a basic ratio ... not just that they should do *1.3x* better"; README:16 "no fixed worth" | CONTRADICTS (a fixed 1.2 floor for every skill is a fixed ratio) |
| T2-A27 | C2: rank agreement 0.8; one fight in five more than 25 percent off | README:66 | CA draft | |
| T2-A28 | C3 5 percent, C4 60 percent, C5 10 percent, C6 half and 60 percent | README:67 to 70 | CA draft; none of these numbers is in the history or his words | |
| T2-A29 | C7 reported against the rough size of three times | README:71 | M10 (rough size); M2 "About 2x" not mentioned | |
| T2-A30 | C8 80 percent of space maps; C9 against E-11 S-085 | README:72 to 73 | history:140 (80 percent shown as draft); E-11 | |
| T2-A31 | "Lines crossing" made concrete | README:75 | M1 asked for it to be made concrete; definition is CA | |
| T2-A32 | Chart form "Westley approved on 2026-10-01"; quotes "I had to stare ..." and "looks much better, especially the top graphic" | README:79 | M11, M12 (quotes verbatim); "approved" is not his word | OVERSTATED |
| T2-A33 | Five chart-form bullets (heading in soldiers, line of fights, units firing lines, plain-words table, map of two settings, decision tree) | README:81 to 85 | CA (describes the sample; the last bullet is not shown to be in it) | |
| T2-A34 | Layer rulings: five layers always; symmetric vision; three actions free; ping alert about 60 degrees; seer replaced; never fire unseen; shortest route; flying vs walking; slope cross-over; abilities out; no faster descent | README:93 to 100 | Q-E01-01, Q-005-02, Q-005-03, Q-E12-01, R-008-04, Q-001-04, R-001-07, Q-004-05, EARLIER, history:374 (his "skip faster descending ... For space battles"). All verified | |
| T2-A35 | "The ping replaces the seer, 'or make the seer really expensive'" | README:95 | M7 (verbatim); register Q-005-04 provisional text drops the seer from launch | |
| T2-A36 | Ideas recorded, not decided: travel lanes, reactive formation | README:101 | M7 and M3; Q-165-01 | |
| T2-A37 | Quote "yes to the real engine, so long as ..." | README:105 | M15 (verbatim) | |
| T2-A38 | Six engine gaps | README:109 to 118 | CA (engineering; rules cited exist: E-13 R-097-01, E-12 R-093-02, E-01 R-008-04) | |
| T2-A39 | Plan: controls batch, then engine cascade, then small batches one skill at a time, then search | README:122 to 128 | M17, M18 (order); skill order and contents CA | |
| T2-A40 | Sonnet sub-agents with separate test writers and auditors | README:125 | M17 | |
| T2-A41 | Search two ways, quote "start the prototype with 2 variables ..." | README:127 | M4 (verbatim) | |
| T2-A42 | Two-machines rules (no machine paths, hash file, workers, merge never rebase, per-run files, nothing generated committed) | README:133 to 140 | M16 asks for portability; rules are CA or CLAUDE.md. README:136 "committed file of result hashes" sits against README:140 "Nothing generated is committed" | |
| T2-A43 | Open items; "Not yet ruled by Westley: the draft pass marks" | README:161 | accurate | |
| T2-B1 | Brief written by the design chat for the conducting chat | brief:3 | M19 | |
| T2-B2 | Design chat "owns this brief, the bible text, the provisional numbers, and runs the experiments. It does not build." | brief:7 | M13, M19; "owns ... the provisional numbers" is CA (his: "Westley owns every threshold and tolerance", CLAUDE.md) | |
| T2-B3 | Conducting chat "decides nothing about game behaviour", questions come back | brief:8 | M19; CLAUDE.md sub-agent rule | |
| T2-B4 | Conducting chat "runs two cascades" (A harness, B engine), reports after each | brief:8 | M17 "all in one", M19 "the cascade" (singular); the harness as a separate cascade is CA | |
| T2-B5 | Westley owns every threshold and tolerance | brief:9 | CLAUDE.md | |
| T2-B6 | Quote "Use manager-mode-lite (sonnet subagents for everything, shard test writers and auditors)." | brief:13 | M17 (verbatim) | |
| T2-B7 | Under "Method: manager-mode-lite": a different-agent auditor checks tests before any code; implementer never edits a test; nobody grades own tests; caveman; no sub-sub-agents | brief:15 to 19 | M17 gives only Sonnet, shard test writers and auditors; the rest is CLAUDE.md and design-chat sequencing | OVERSTATED (presented as the content of his term "lite") |
| T2-B8 | Repo rules that bind the cascade (contract first, one owner per file, wired, tests in tests/csim, determinism, frames untouched) | brief:21 to 28 | CLAUDE.md, PLAN.md; "ABI bumped once" and "If a wave decomposes into more than 16 parts, split the wave" (brief:139) are CA | |
| T2-B9 | Two machines: no machine paths, entry guard, "macOS starts workers fresh; Linux forks", merge never rebase, branches local and removed at end, nothing generated committed | brief:32 to 37 | M16; CLAUDE.md. "Linux forks" is wrong for Python 3.14 (CLAUDE.md names it; the Linux default there is forkserver) | |
| T2-B10 | "Westley restores the stray `project.godot` change himself"; tree must be clean before starting | brief:38 | M16 "Discard it." only | OVERSTATED |
| T2-B11 | Controls batch run by the design chat on today's engine and read with Westley; engine cascade after | brief:135 | M13, M18 | |
| T2-B12 | Quote "Every G doesn't need it's own cascade, it can be done all in one." | brief:139 | M17 (verbatim, his typo kept) | |
| T2-B13 | Waves W0 to W4 in dependency order | brief:139 | M16 "in order"; wave grouping CA | |
| T2-B14 | "The one invariant ... with no new call made and every setting at its default, the engine behaves exactly as it does today" | brief:141 | CA; contradicted by G3 (brief:186 to 189, unconditional visible-set targeting, "today it steps toward any enemy"), G2 (brief:170, sampling the unit's own layer), README:114 (a gap to be closed is a default change) | CONTRADICTS |
| T2-B15 | Signatures are proposals; names may change, behaviour may not | brief:143 | CA | |
| T2-B16 | "Westley, 2026-10-01, accepted the recommended starting values as provisional so the stories can be built; every one is a runtime setting (G1)" | brief:261 | M16 (the choice); "every one is a runtime setting" is CA | |
| T2-B17 | The numbers: emitting multipliers 2.0, ping radius 500, reveal 40, cooldown 400, reach 2,000, reach table (Raider 1/1, Interceptor 2 up 1 down, Siege 0 up 2 down) | brief:263 to 278 | Radius, reveal, cooldown verified as the unused OM_PULSE constants (500, 40, 400). 2.0 follows the vantage multiplier (R-005-06). Register Q-005-04 option (a), which he accepted, has no numbers: only "reach starts as own layer only for Line types, one layer either way for Strike types, downward only for Siege types, with one type that fires upward well". 2,000, 2.0, "2 up 1 down", "2 down" are CA | OVERSTATED (framed under his acceptance in brief:261) |
| T2-B18 | Ping reach 2,000: "much longer range" than passive sight "(at most 500)" | brief:271 | M6 quote verbatim; 500 is the one-layer cross-layer reach; same-layer passive sight can be 1,000 (R-005-01) | |
| T2-B19 | Interceptor "the type that fires upward well" | brief:274 | his "a unit that works particularly well at destroying units from above it" (Q-005-02); choice of Interceptor and 2 up 1 down is CA | |
| T2-B20 | Sensor pulse not built, ping takes its place (provisional) | brief:280 | Q-005-04 option (a) | |
| T2-B21 | Out of scope: Godot, pipe frames, land eras, abilities, layer preference, map generator, toy, alert display | brief:284 | EARLIER (abilities out); the rest CA. Land eras and walking units conflict with M9 Q3 reporting land maps (T1-32) | |
| T2-B22 | Report to the design chat after each cascade, under 300 words | brief:288 | M19 | |

## Summary

Table 1: 33 rows. landed 23 (T1-24 borderline); landed weakened 4 (T1-13, T1-18, T1-30, T1-32); landed overstated 3 (T1-02, T1-17, T1-31); MISSING 3 (T1-08, T1-28, T1-29).

Table 2: 65 rows. 15 flagged, 50 clean. CONTRADICTS 4 (T2-A8, T2-A25, T2-A26, T2-B14). OVERSTATED 11 (T2-A10, T2-A11, T2-A12, T2-A16, T2-A17, T2-A20, T2-A23, T2-A32, T2-B7, T2-B10, T2-B17).

Quotation check: 0 character mismatches on attributed quotations; 1 unattributed invented quotation (README:56); 2 quotations verifiable only against the history file.

Unverifiable from his messages: the chart-form bullets (README:81 to 85, brief:119 to 125) describe a sample page whose contents are not in his words; the option labels "blob" and "line abreast" are not in his typed answer.

## Needs a fix

1. README:15, last sentence "An even exchange is not an even outcome when one side has more in reserve." It contradicts the quotation just before it ("if A and B both have the same number of units firing than the engagement ends up even") and is the author's finding, not his. Replace with: "It is the firing count over the whole fight that counts, not only the opening."
2. README:64, C0. "break-even between 0.9 and 1.1 of equal numbers" lets a mirrored fight pass when a smaller force wins. His rule (M2): with identical units, formation, vision and layer organisation the larger force wins. Replace with: "Control: a mirrored fight; the larger force wins and break-even sits at equal numbers (tolerance to be set by Westley)". Add a README bullet in section 2: with exactly the same units, formation, vision and layer organisation the larger force wins; "Hypothetically this situation would *never* happen in the real game, given there are 5 different layers, different vision, the landscape will be autogenerated and not symmetrical."
3. README:65, C1. A fixed "at least 1.2" firing-advantage floor for every skill is the fixed ratio he rejected in M9 and that README:16 disclaims. Replace the mark with: "firing advantage above the naive side's on the maps that offer the play; size set by Westley, not a fixed ratio".
4. README:16 and README:71. Add his first answer. Replacement: "For all five skills together his first answer was 'About 2x'; he then said 'I like C' (singles of about 30 percent, full mastery 3x or more) and confirmed these as rough sizes only." C7 should read "reported: the best situations, against the rough sizes of 2x and 3x".
5. README:56 and README:82. Remove the quotation marks round the invented example. Replacement: "Break-even, in whole units: for example, 16 units beat 17 enemies and lose to 18."
6. README:79 and brief:119. "approved" and the five-bullet form attributed to him. Replacement: "the form of the sample Westley, 2026-10-01, called 'much better' ('looks much better, especially the top graphic that makes it very clear') after the first draft read badly". Brief:119 should say "Form of the sample he called much better; only the top graphic was named; the bullets below describe that sample". Brief:117 to 125 should add: "a different chart form is allowed when the data type changes (his M15)".
7. README:30 and README:38. "accepted in outline" covers a counter he said he could not picture. Replacement: "accepted in outline, except S2's mass-on-one-end counter, which he said he could not picture and has not yet confirmed".
8. README:17. "Unit type is the one other factor" and the examples "damage bonus for height or raw health". Replacement: "Unit type also weights each shot ('not just unit values but their type as well'). When the result does not follow the firing count, 'there's a number that's off'." Delete the examples; he lists health, range, vision and ping distance as knobs to tune.
9. README:58 and brief:284. Land maps are said to be measured and reported; the cascade excludes walking units, slopes and land eras. Replacement for README:58: "Land maps (ramps, walking units) are to be reported and do not block; the engine cascade does not build walking units or slopes (brief section 7), so they are not measured until a later cascade."
10. README:127. Add his comparison aim: "... see which one performs better for our goals (M4)".
11. Brief:261 to 278 and, outside the audited scope but the same text, register Q-005-04 resolution. Replacement for brief:261: "Westley, 2026-10-01, accepted the recommended starting values (Q-005-04 option a) as provisional. The numbers in the right-hand column were chosen by the design chat from existing constants and design judgement (ping radius, reveal and cooldown are the unused pulse constants); he has not set or confirmed them. Every one is a runtime setting (G1)." Mark ping reach 2,000, emitting 2.0 and 2.0, Interceptor 2 up 1 down, Siege 0 up 2 down as "design chat proposal".
12. Brief:38. Replacement: "Westley decided to discard the stray `project.godot` change. The guard blocks agents from discarding files, so he runs `git restore project.godot`, or asks the design chat to request it." Delete "himself" as a stated fact about him and "the working tree must be clean" unless the design chat adds it as its own rule.
13. Brief:11 to 19. Replacement for the lead-in under the heading: "Westley's definition: Sonnet sub-agents for everything, shard test writers and auditors. The bullets below add repo rules (CLAUDE.md, PLAN.md) and the design chat's sequencing."
14. Brief:141, invariant. It is not true as written: G3 changes targeting in every fight without any new call or setting, and G2 changes layer sampling. Replacement: "With no new call made and every setting at its default, the engine behaves exactly as it does today, except where a step is stated to change default behaviour (G3 does; G2 may). The hash file records before and after for those; the design chat decides whether G3 gets a switch." This is a question for the design chat, not a choice for the conducting chat.
15. Brief:35. "Linux forks" is wrong for Python 3.14. Replacement: "macOS starts workers by spawn; do not rely on fork on either machine."
16. README:136 against README:140, and brief:111 against brief:37. A committed hash file sits against "Nothing generated is committed". Add "except the control hash file" to both "Nothing generated" lines.
17. Brief:8, "runs two cascades". He said "the cascade" (M19) and "all in one" (M17). Replacement: "runs the cascades below (Cascade A, the harness, is the design chat's own split; he asked for the engine gaps as one cascade)".
18. T1-08, M14 "Yes a guard stance is fine" is not recorded anywhere. Add to README section 7 or 12: "Westley, 2026-10-01: a guard stance is fine; the real engine's anchor and leash (G1) serve this."
