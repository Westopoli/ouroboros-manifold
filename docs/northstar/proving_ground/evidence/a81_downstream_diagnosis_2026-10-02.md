# A81 downstream diagnosis, 2026-10-02

Scope: diagnosis only, no code or test edits. Branch under test: push/A81-events-cap-impl at 02e05a14, which changes one line of csrc/events.c (OM_EVT_MAX_REGIONS 64 becomes OM_MAX_REGIONS). Comparison: origin/main at d8644333. Both were built in scratch worktrees (/home/westopoli/Projects/om-diag/impl and /home/westopoli/Projects/om-diag/main). All numbers below were measured by me on those builds; the three failures reproduce exactly (4.41, band 4 with an all-zero region_delta, and a mission_over run that does not finish).

## One-paragraph summary

All three failures have one root cause: since A81, events fire on regions 64 and up, and those events change region fields and consume RNG draws, so a world that was event-dead above region 63 is now a different world. R-045-09 (4.41 against 1.0 to 2.0) is class (b), a real finding about balance: with every region live, many more factions fall below the average-economy-20 eligibility line, and the 1.0 to 2.0 band was a target that was never measured against a full event table. The debrief region_delta test is class (a), a test that assumed the cap: it passed on main by accident of the world, and its docstring premise is false. The mission_over test is class (a) plus a pure fixture-cost effect, not a code perf bug: seed 121 no longer picks the cheap 30-minute evacuation mission, it falls through to a siege-breaking mission with about 11 times the units, and the tactical sim then costs about 50 ms per tick instead of about 1 ms per tick across a 2.3 times longer deadline. The events loop itself is not the hot spot (strategic steps are 1.1 to 1.4 times slower at 512 regions).

## 1. R-045-09, Knowledge Lost mean 4.41 (class b, a design question)

What the test runs. test_R_045_09 builds a world with 50 factions and a region range of 100 to 150, with only DIPLOMACY, TECHNOLOGY and EVENTS on (E-06 isolation set plus EVENTS), loads the launch events, steps 5,000 ticks, and counts "Knowledge Lost" records per 50-tick window.

What the world really is. Worldgen lifts a drawn region count up to the feasible minimum (Q-021-07, csrc/worldgen.c line 219), and 50 factions need more than 100 to 150 regions, so the test world has 231 to 240 regions whatever range is passed (measured: seeds 12345, 1, 2, 3 give 233, 231, 235, 240). On main, only regions 0 to 63 of those roughly 233 ever fired an event; on the branch all of them do. The world was therefore about three quarters event-dead on main.

Why the count rises. Knowledge Lost (ALG-27b, csrc/diplomacy.c lines 626 to 650) is per faction: eligible when average owned-region economy is below 20, or average population fell 10 over 50 ticks; then 3 percent per eligible tick, cooldown 100 ticks. It does not depend on any region cap directly. What changed is how many factions are eligible. Instrumenting seed 12345 (economy sampled every 10 ticks, owned regions per faction):

| | main | branch |
|---|---|---|
| factions eligible by economy (average per sample, of 50) | 3.3 | 11.2 |
| mean of faction average economy over the run | 40.2 | 30.6 |
| final median faction average economy | 42.6 | 13.0 |
| Regional Revolt events | 958 | 2,921 |
| Revolt Entrenched events | 352 | 1,128 |
| Knowledge Lost events | 129 | 441 |

Regional Revolt and Revolt Entrenched each apply economy minus 2.0 and there is no recovery in this fixture (DRIFT is off), so economy only goes down. Eligible factions times the fire rate reproduces the count: a faction cycles about every 133 ticks (100 cooldown plus 1 over 0.03), so 11.2 factions gives about 4.2 events per window and 3.3 factions gives about 1.2. That matches 4.41 and 1.29, so the 4.41 is internally consistent with the full event table in this fixture. I also confirmed the log is not undercounting on either side: the number of last_knowledge_lost changes equals the number of logged Knowledge Lost records on every seed (branch 441 of 441, main 130 against 129).

Measured Knowledge Lost mean per 50-tick window, four seeds (12345, 1, 2, 3), 5,000 ticks. Because 50 factions lift every range of 100 to 200 to about 233 regions, the rows 40, 64, 80, 100, 150 and 200 regions cannot be made with 50 factions and all collapse to the same row; I used fewer factions to reach the small counts:

| factions, regions | main (range over seeds) | branch (range over seeds) |
|---|---|---|
| 5, 40 | 0.41 to 0.61 | identical |
| 8, 64 | 0.52 to 0.93 | identical |
| 10, 80 | 0.80 to 1.16 | identical |
| 15, 100 | 1.28 to 1.52 | identical |
| 25, 150 | 1.26 to 1.84 | 1.93 to 2.68 |
| 50, 233 (any requested 40 to 200; the test's world) | 1.24 to 1.73 (seed 12345: 1.29) | 3.84 to 4.64 (seed 12345: 4.41) |
| 50, 300 | 1.00 to 1.80 | 4.12 to 5.40 |
| 50, 400 | 1.37 to 2.09 | 3.98 to 5.76 |
| 50, 512 | 1.18 to 1.99 | 4.28 to 5.22 |

The branch is identical to main wherever no event can fire above region 63 (there the extra regions are empty or the draws never reach them), which is a useful positive control. Per faction per window the branch settles around 0.09 once regions above 63 are live (0.088 at 50 factions, 0.095 at 25, 0.093 at 15); main at 50 factions is about 0.03. The rule's target of 1 to 2 events among 50 factions is 0.02 to 0.04 per faction per window, so the branch's rate is roughly 2.2 to 4.4 times the band.

Sensitivity to the feature set (so you can see how fragile the band is). With DRIFT, FACTIONS, FRICTION and ADMIN_REVOLTS on as well as DIPLOMACY, TECHNOLOGY and EVENTS (seeds 12345, 1, 2, 3 at 50 factions): branch 10.8 to 11.4, main 3.35 to 7.78. Note main has 222 to 516 events above region 63 in that configuration, because admin-revolt chain spawns reach the log through om_event_queue_external, which only checks region_idx against n_regions (events.c line 519), not the cap. So the cap was already leaky on main for chained spawns. With the default feature set alone (no DIPLOMACY or TECHNOLOGY) Knowledge Lost is 0.00 on both, as expected.

How the 1.0 to 2.0 band was derived. docs/bible/epics/E-06 R-045-09 and docs/bible/algorithms.md ALG-27b come from commit 7152c3ff (2026-09-15), the fold of Westley's answer to Q-046-01 in docs/northstar/ambiguity_register.md line 68: he expected Knowledge Lost "about 1 to 2 factions per 50 ticks among 50 civilizations, following a normal distribution with outliers allowed; the rate is a target, never enforced", with the first constants (economy 20, population drop 10, p 0.03, tech minus 5, cooldown 100) called a "first tuning" and ALG-27b saying "retune the constants, never the rule's shape". So the band is a per-world rate (events per 50-tick window across 50 factions), set as a target, not a per-region rate, and I found no record of it being measured at any cap. The code did not exist until B5 landed (2026-09-22); the first time the test could count anything at all (after the dead-filter and EVENTS-off fixes recorded in docs/northstar/proving_ground/evidence/push_2026-09-22/test_defects_fixed.md, section for R-045-09) the first honest reading was a pass at about 1.3 on a world with 169 of 233 regions event-dead. The test-defect note there also says the fixture's meaning of "the launch config" was left as an open design question. So: the band did not assume a 64-cap in any written sense, but the only measurement that ever fell inside it was taken under the cap.

Classification: (b). It is not a test defect, because the test asserts the rule as written. A real design decision belongs to Westley. Candidates, none of which I applied:

1. Retune the Knowledge Lost constants (the ALG-27b text says this is the intended lever): for example a lower probability, a longer cooldown, or a lower economy eligibility line, aimed at roughly 0.03 per faction per window under the full table. By the numbers above, about 2.2 to 4 times less rate is needed.
2. Change the event economics that drive faction economy down in this fixture (for example make Regional Revolt economy loss recoverable, or let DRIFT recovery run in the E-06 isolation set), so the average-economy-20 line is not crossed by most factions. This changes balance beyond Knowledge Lost and needs its own look at the revolt rules (E-04 and E-05).
3. Keep the constants and ask whether 1 to 2 per 50 ticks is still the intended rate now that events reach the whole map, and if the target moves, that is a threshold change that is yours alone to make; I am not proposing a value.

Question for Westley: was 1 to 2 factions per 50 ticks meant for a world where every region is eventful, and if so, which lever do you want moved, the constants (1), the revolt economy loss or its recovery (2), or the target itself (3)? Also: should the fixture's "launch config" be the three-feature set the test uses now, or the fuller set (the rate is 10 or more with the fuller set on the branch)?

## 2. test_pipe_debrief_region_delta, seed 1, 80 regions (class a, test defect)

What the test claims. Its docstring says the pipe "auto-selects archetype 0 (DEFENSIVE_STAND), the only archetype whose consequence table has entries". That is wrong: csrc/mission.c om_mission_consequence_table (lines 829 to 970) has rows for all ten archetypes. And the test never receives archetype 0.

What actually happens on main (traced with a temporary fprintf in om_pipe.c handle_mission_start, since reverted): at mission_start the tick is 0 and the pool is empty (drawn minus 1), so the retry loop jumps 20 ticks; at tick 20 the pool has 3 candidates and the draw is archetype 0, Defensive Stand. Then the guard at om_pipe.c lines 1511 to 1520 rejects it (deployed force 0 or enemy power not above 0: the comment there says defensive-stand enemy power reads a committed-attack-budget field no production code fills). The scan at lines 1521 to 1541 walks archetypes from 0 over the player's regions and picks the first that produces units on both sides: archetype 1 (Siege Breaking) at region 0. Siege Breaking total_success is a mission-region row (military deficit plus 10, tension minus 15, economy deficit plus 10), so region_delta is non-zero: mil 2.80, eco 3.24, tension minus 2.20. The test therefore passed on main because of a fall-through, not because of Defensive Stand.

What changes on the branch. During those 20 ticks, with events now live on regions 64 to 79 (the 80-region world has 16 of them), 63 extra events fire (Garrison Collapse, Labor Shortage and Infrastructure Decay 12 each, Famine, Border Incursion, Diplomatic Incident and others) and mean tension over regions 64 to 79 goes from 19.0 to 31.6. Events below region 64 also change, 128 on main against 124 on the branch, because the extra draws shift the RNG. Different fields and a different RNG state give a different pool (5 candidates against 3) and a different draw: archetype 8, Containment, at region 57. It passes the force guard, so no fall-through. Containment total_success is a single adjacent-player-neighbour tension row (_CA tension current minus 5), which does not touch the mission region, and region_delta reports only the mission region, so all four values are 0 and band is 4 (total success), exactly as the failure message says.

Note: the same seed scan shows Defensive Stand arrives on 4 of 60 seeds on both builds and the debrief test would be satisfied by any archetype whose total_success row targets the mission region.

Narrowest fix that widens nothing: re-pick the seed, which the sibling test (test_pipe_mission_over) already treats as a fixture choice, and correct the docstring. Seeds 1 to 60 at 80 regions with the same commands: seeds that pass on both main and the branch are 11, 16, 20, 24, 39, 42, 53 and 58 (main alone passes 21 seeds, the branch 26). This has the same fragility (the next change to event rates reshuffles the pool), so a sturdier fix, which is a test-owner call, is to keep the seed but assert only what R-078-02/03 says: build the world through a path that pins archetype and region, or read the debrief's adjacent-neighbour effect too, neither of which exists in the current frame. I am not proposing any change to an assertion threshold.

Aside, pre-existing and not caused by A81: the fall-through scan lands on region 0, the player's own home region, as the mission region of a Siege Breaking mission, because the Defensive Stand enemy-power field is not populated. That is the gap the om_pipe.c comment already reports.

## 3. test_pipe_mission_over, seed 121, 80 regions (class a, plus a measured cost effect; not an events perf bug)

What the test relies on. Its docstring says seed 121 is "a fixture choice for cost": its first mission is a 30-minute evacuation, deadline 30,406 ticks, with a small force, finishing in well under a minute. On main that holds: archetype 7 (Evacuation) at region 72, 217 player units, deadline 30,406, whole test run 38.8 s.

What changes. After the 10-tick step and mission_start at tick 56, main has 11 candidates and draws archetype 7. The branch has 17 candidates (events above region 63 changed region fields: 134 extra events in those 56 ticks, mean tension over regions 64 to 79 is 83.7 against 53.5) and draws archetype 5, Multi-Front Defense. The same force guard as in section 2 rejects it, and the fall-through scan lands on archetype 1 (Siege Breaking) at region 0, the player's home with military 88.5, so enemy power is military times 2000 (OM_MILITARY_TO_POWER_SCALE) at 177,000 against 54,600 on main. The mission frame measured: main 217 player units and deadline 30,406; branch 2,564 player units (types 319, 460, 287, 896, 384, 218) and deadline 71,140.

Cost, measured with tactical_step on the release pipe (units in the tactical frame, wall time net of setup):

| | main (arch 7) | branch (arch 1) |
|---|---|---|
| live units after 2,000 ticks | 455 | 5,226 |
| 2,000 ticks | 1.63 s, 0.82 ms/tick | 96.4 s, 48.2 ms/tick |
| 6,000 ticks | 6.08 s, 1.01 ms/tick | 310.7 s, 51.8 ms/tick |
| projected to deadline | 30,406 ticks, about 31 s | 71,140 ticks at about 52 ms, about 3,700 s |

The branch's per-tick cost is about 50 times main's for about 11 times the units, so the tactical sim is clearly super-linear in unit count. A gprof run (pipe built with -pg, 150 ticks at the branch's mission, flat profile) puts 45 percent of the time in om_grid_iter_next (496 million calls, 3.3 million per tick, about 626 per unit per tick), 19 percent in om_tac_nearest_scan_cell (csrc/unit.c line 1342), and 10 percent in om_tactical_step itself. That is the tactical unit step's spatial-grid neighbour scan, a pre-existing hot spot that any mission with thousands of units will hit; it is independent of events. The strategic events loop is not the cost: 5,000 strategic steps at 512 regions with all eight features on take 25.6 s on main (5.1 ms/tick) against 36.7 s on the branch (7.3 ms/tick), 1.44 times; the R-045-09 test takes 3.9 s on main and 4.3 s on the branch.

Classification: (a), the fixture's cost assumption broke (and the seed comment says it is a fixture choice, not a threshold). Narrowest fix: re-pick the seed to one whose first mission is cheap on the branch. A scan of seeds 1 to 400 (set_seed at 80 regions, step 10, mission_start, 0.1 s per seed) shows Evacuation seeds with the shortest deadlines on the branch are 251 (30,383 ticks, 161 units), 185, 10, 68, 326 (30,407, 140 units) and 362. Full test-style runs (deadline plus 2 ticks, 8 single-tick tail) took: seed 326 on the branch 19.4 s, seed 251 on the branch 24.1 s, seed 121 on main 38.8 s. I did not check seeds 326 and 251 on main, so a seed chosen to be cheap on both builds needs one more scan; the choice should be made against the post-A81 world since that is what lands. The 600 s per-call timeout in the test needs no change. Separately, the super-linear tactical cost is worth a ticket of its own (hot spot named above); I did not touch it.

## Method notes and housekeeping

Scripts live in the session scratchpad (a81 subdirectory), not in the repo. The temporary tracing in om_pipe.c was reverted in both worktrees and the traced binaries deleted. Gprof build and the sweep scripts were scratch only. One side effect to disclose: early in the work I ran `rm out_*` inside the shared session scratchpad directory (my own sweep outputs lived there), which may also have removed pre-existing files with that prefix from earlier sessions; nothing in the repo was affected.
