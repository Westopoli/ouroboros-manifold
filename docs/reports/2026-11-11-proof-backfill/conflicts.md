# Conflicts collected from the backfill files

Text kept as written; numbering C-<epic>-<n> follows the order in the input file(s) (E-16 and E-17: part a, then part b).

## E-01

- C-E-01-1: R-007-05 vs E-13 R-207-06: "Given cover in a unit's path, When it moves, Then movement is unaffected; cover never blocks movement" / E-13 R-207-06 and its test make a walker go round a box, and E-17 R-190-07 "an obstacle is a small annoyance and never a complete blocker"; E-01 Invariant 7 "Cover never changes damage or movement" inherits the same split (C4 note 2)
- C-E-01-2: R-164-01 vs csim test: "the first reading (Line its own layer, Raider one layer either way, Interceptor two up and one down, Siege two down) is replaced as it [the lab] does" / test_R_164_01_built_in_default_reach_is_zero_up_zero_down pins zero up, zero down; staircase stage 4 says "reach 0 up 1 down so the high ground fires down" (C4 note 1)
- C-E-01-3: R-163-01 vs test_R_163_01_default_multipliers_make_emitting_a_no_op: "it sees other layers further than passive vision allows, and units on every layer ... see it from further away" / "engine default of both multipliers is 1.0 ... Emitting with the defaults leaves 600 unseen"
- C-E-01-4: R-163-02 vs test_R_163_02_both_silent_is_unchanged_even_with_both_multipliers_set: "Then it is harder to see from other layers and gives up the extra sight that emitting gives" / "Silent is today's behaviour" (the test treats silent as the unchanged baseline, so nothing is harder to see)
- C-E-01-5: R-006-03 vs test_R_006_03_a_second_ping_inside_the_cooldown_is_refused_and_leaves_the_cooldown_alone: "Given a pulse fired on tick T ... the command is rejected" / the test casts a ping ("R-006-03 analogue") while the epic says "The pulse is not built: the targeted ping of S-162 takes its place"
- C-E-01-6: R-002-08 vs R-105-06 handling in tactical_view.gd:1206: "presses Alt plus a layer number (Cmd on macOS) and then clicks the map, Then the whole selection receives a hard transfer" / "A modifier held does nothing here (Alt+N is narrowing's, R-105-06, G7)"

## E-02

- C-E-02-1: R-160-02 vs test_E02_S160_no_default_features.py: R-160-02 "Given a world made by `om_world_new`, ... Then `OM_FEAT_DRIFT` is on; every other feature switch is off" (csrc/ouroboros_sim.h:268 says the same: "om_world_new() switches only DRIFT on by default (S-160)") / the test's docstring "om_world_new() itself sets no feature any more; the DRIFT-on default that used to live in csrc/region.c is gone" and test_R_160_raw_world_has_every_feature_off asserts all nine switches are 0 (csrc/region.c has no feature set).
- C-E-02-2: R-015-01 and R-015-02 vs docs/bible/algorithms.md ALG-06: "regardless of the edge types joining them" / "For every inhabited neighbor across a trade edge that is same-faction, or whose faction ... cooperative stance".
- C-E-02-3: R-018-04 vs R-018-02: R-018-04 "summed over any 15 consecutive ticks, ... within 1e-6 of 0" / R-018-02 "Given tick 1, ... the previous oscillator value is taken as 0"; the window starting at tick 1 sums to osc(15) minus 0, so the test excludes it (test_R_018_04 comment).
- C-E-02-4: Epic "Obviously working in 60 seconds" vs its gate test: "Economy climbs toward the mid-50s then oscillates" / test_E02_gate_drift_trajectory.py comment "it does not settle in the mid-50s ... probe economy ... ranges ~81.5 to 100.0" and it asserts probe_max == 100.0.
- C-E-02-5: Invariant 6 vs the same gate test: "none diverges to a corner" and "no field of a home region leaves [8, 100]" / the gate test asserts the probe economy hits 100.0 and population saturates at 100 (its own comment), and R-019-04 plus the S-019 open flag "drift alone floors it at 0" let tension fall below 8.
- C-E-02-6: R-220-02 and R-220-03 vs the S-220 open-flags line: Thens still read "[Q-220-01: ...]" and "[Q-220-02: ...]" / "Q-220-01 and Q-220-02 closed 2026-10-21 (register: no contract change; mission-only for now)".
- C-E-02-7: R-015-03 skip reason vs conftest: skip reason "needs a diplomacy stance setter that csrc/ouroboros_sim.h does not expose" / tests/csim/conftest.py defines set_stance (om_faction_set_stance) and the E-06 test uses it.
- C-E-02-8: Id collision, not a rule conflict: tests/csim/test_E02_S160_om_pow.py names R_160_01 to R_160_03 for om_pow checks, and test_E02_S020_abi.py names R_020_* for ABI checks, ids that mean other things in the epic; a proof pointer must not point at them.

## E-03

- C-E-03-1: R-021-08 vs R-025-02: "exactly max(1, floor(0.12 · N)) extra edges are attempted between distinct non-adjacent regions, never between two home regions" / "NPC-to-NPC home regions may be adjacent". Extra edges are the only way two homes of different factions could touch, so the permission in R-025-02 can never occur under R-021-08. Soft conflict, not a contradiction.

## E-04

- C-E-04-1: E-04 Invariant 6 vs csrc/events.c:25: "Over 5,000 ticks with 60 regions, the pending queue never exceeds 2,000 entries" / `#define OM_EVT_QUEUE_CAP 64`. The code cap is far below the Invariant's bound; what happens to an entry past 64 (dropped?) is not stated in the epic.
- C-E-04-2: R-225-01 vs the epic's flag lines: "Then [Q-225-01: whether the trouble has any strategic effect ...]" (placeholder text in the rule) / "Q-225-01 and Q-225-02 closed 2026-10-21 (register: tactical only, the 26 templates stay closed; in-mission events)". Same for R-225-02. Also the "Open ambiguity flags" section still lists "Q-225-01, Q-225-02 (S-225)".
- C-E-04-3: R-031-01 vs the epic gate and the register: "(Q-031-01: measure first)" in the rule text / "S-026 to S-031 have no open flags" and Q-031-01 closed (c), 2026-09-12.

## E-05

- C-E-05-1: S-036 story line vs R-036-03: "I want some attacks announced a tick ahead at full strength" / "Given a telegraphed attack declared on tick t, When tick t + 3 runs, Then it resolves in step 3c" (Purpose: "telegraphed three ticks ahead").
- C-E-05-2: S-039 open-flags note vs R-039-06: "R-039-05 and R-039-06 are not built, the resolver skips owned targets" / in the same note "The multi-faction collision resolver is built"; test_R_039_06 (three colliders, empty target) is not skipped and csrc/collision.c resolves groups.
- C-E-05-3: S-039 note vs R-036-03: "collisions are grouped across matured telegraphs and immediate attacks in one resolution list, and step 3c only matures (this changes R-036-03)" / R-036-03 "it resolves in step 3c before any new decisions"; the test asserts the rule as written.
- C-E-05-4: R-040-03 vs its test: rule "L in [3, 4] runs the short chain (Separatist, Military Defection, Breakaway) ... the Breakaway fires on tick t + L" / test comment "E-05's own ABI only queues ONE marker entry ... expanding L into the named chain steps ... is E-04's chain resolution".
- C-E-05-5: R-033-01 vs its test docstring: rule "... · 0.025 · economy multiplier (E-06 R-046-05), which is 2.275 at multiplier 1.0 (DEC-C15-2026-10-22)" / docstring "... · 0.025 = 2.275".
- C-E-05-6: R-040-05 vs its test: rule "E-07 creates a new faction holding the region" (csrc/lifecycle.c builds it) / test xfail strict "E-07 owns faction creation; this rule turns real when the E-07 block lands".
- C-E-05-7: Epic gate text vs rule count: e2e file docs/northstar/e2e/E-05.md says "58 Given/When/Then rules" / epic says 62.

## E-06

- C-E-06-1: R-046-05 vs its test: rule "Then the gain is scaled by it (DEC-C15-2026-10-22)" / test docstring "Then [Q-048-01: nothing in the sim consumes it today]" and its closing assert expects the economy field to differ from 50 * 1.048 (also S-046 header: "the economy multiplier is wired into ALG-05 growth").
- C-E-06-2: R-044-07 vs S-044 header vs its test: rule "current code commits the betrayer's entire budget at full efficiency; the bible says a surprise attack" / header "commits the betrayer's full budget at surprise efficiency (half efficiency, 0 defender warning window)" / test asserts effective_attack >= 42.5 with commit 43.55 ("full efficiency").
- C-E-06-3: R-042-05 internal: "hostile if their archetype pair is in the override table ... and neutral otherwise" / same rule "at launch every starting pair is hostile" (test asserts all 15 starting pairs hostile, including pairs outside the table).
- C-E-06-4: R-227-03 and R-227-04 vs the S-227 Open flags line: rules still read "[Q-227-02: whether anything flows back ...]" and "[Q-227-03: how the three tiers relate ...]" / "Q-227-02 and Q-227-03 closed 2026-10-21 (register: nothing flows back; tiers stay the coarse sim reading)".
- C-E-06-5: test_R_042_06 comment vs R-049-05: comment says "Breakaway creation hook (E-06 R-042-06 / E-07 R-049-05)" / R-049-05 is "Admin Breakaway fires ... success rate is 1.0".

## E-07

- C-E-07-1: R-049-05 vs test_R_042_06 comment: R-049-05 is "Given Admin Breakaway fires ... success rate is 1.0" / the comment in tests/csim/test_E06_S042 cites "E-07 R-049-05" as the breakaway creation hook for stances.
- C-E-07-2: R-049-04 vs R-042-06: R-049-04 "stance hostile with every faction both ways" / R-042-06 "hostile toward every existing faction and every existing faction is hostile toward it" (same Then stated twice, proved by different tests).
- C-E-07-3: S-049 header vs rules: header "the parent faction's budget gains the stolen economy" / no R-049-xx rule and no test states or asserts a budget gain.
- C-E-07-4: S-051 header vs R-051-05: header "a starting faction with no regions is kept forever and marked as fallen" / R-051-05 "it is never removed" (no rule or test covers "marked as fallen").

## E-08

- C-E-08-1: R-060-04 vs S-060 header and register: R-060-04 "it happens once at the end of each time jump, not every tick [Q-060-01]" / S-060 header "Q-060-01, natural deaths are processed per tick" and register Q-060-01 closed "(b), 'B.' Per tick, build it that way in C. Answered by Westley, 2026-09-13."
- C-E-08-2: R-056-01 vs S-056 header and tests: rule "[Q-056-01: code uses a fixed 50]" / header "the jump length is uniform random in [20, 100] with no state input"; tests/transport/test_pipe_chapter_lifecycle.py jumps COLLAPSE_JUMP_TICKS = 1500 ticks, outside [20, 100], and om_time_jump_choose_length has no caller.
- C-E-08-3: R-063-03 and S-063 header vs hub and test: header "difficulty and preferences are set once at campaign creation and fixed for the whole campaign, with no mid-campaign change" / hub game_bible.md "both can be changed later" and story text "change my mind later" / test_R_063_03 asserts om_onboarding_update_choices succeeds mid-campaign.
- C-E-08-4: R-063-01 vs its test: rule "a preference" per archetype / test docstring "a preference weight with a 'rare' mark; at least one archetype must stay unmarked [Q-063-01 ...]" (rule has no rare mark; Inputs table says "rare marks < 10").
- C-E-08-5: R-064-03 vs its test: rule "era unlocks (E-20) at launch and trait cards (E-11 S-083) after launch" / test docstring "the only unlock type at launch is era unlocks (E-20)".
- C-E-08-6: R-057-03 vs code: rule "home region's total field delta over the jump is D" / csrc/generational.c passes delta = 0.0 ("not wired to this call site").
- C-E-08-7: R-062-02 vs stale test: rule runs the R-058 pools restricted to survivors / test_R_062_02_q_062_01_code_picks docstring "code picks the surviving faction with the most regions ... the bible says prefer narrative connections".

## E-09

- C-E-09-1: Invariant 3 vs R-065-06: "5 ≤ entries ≤ 10 for any jump with events (3 to 5 for the opening jump)" / "the cap wins over the minimum, so a quiet jump may show 4 entries" (csim test_R_065_05_they_taken_in_descending_peak asserts exactly 4).
- C-E-09-2: R-065-03 vs S-070 header: "every lineage cluster is included regardless of score, one per region the lineage touched" / "lineage clusters are capped at 2, merging the rest into the highest-scoring one (R-065-03 still reads one per region)".
- C-E-09-3: R-066-02 vs the jump path: "the context multiplier gains +0.5 ... +0.3 ... +0.1 · min(L, 5) ... +0.8" / tests/transport/test_pipe_u_observable.py: "the mission-region, character and chain terms need context the jump does not pass: csrc/chronicle.c chron_score_event, so they add nothing".
- C-E-09-4: R-069-03 vs its csim test: "The map holds at an entry's keyframe until that entry has printed and its hold has passed" / test_R_069_03 docstring "the map never waits for the scroll"; tests/test_vg_b_b26.gd quotes "Whether the map holds at that entry's keyframe until it has printed is open (Q-069-03)".
- C-E-09-5: "Obviously working" vs R-068-02: "none over 90 words in base form" / "base form under 90 words".
- C-E-09-6: R-067-06 vs S-067 header: "the consequence categories [Q-067-01: 3 in code, 4 in the bible]" / "the list has 21 categories with consequence_ripple built" (5+8+4+4); the csim test asserts only 5, 8, 4.

## E-10

- C-E-10-1: R-072-06 vs its test: rule "Given a region with stability 15 and an active revolt chain (two revolt events) under attack by a neighbor at military 80 ... (Q-072-02, Architect 2026-10-19)" / test skip reason "Q-072-02 open: R-072-06's scenario cannot reach urgency 0.8 under R-072-02's weights" (register: Q-072-02 closed, option (a) revolt chain).
- C-E-10-2: R-080-02 vs its test: rule "difficulty sets parity (R-074-03), time width, resource generosity, and the complication odds" / test docstring "R-074-03 applies and nothing else changes at launch [Q-080-01]" (register Q-080-01 closed (c), full ramp).
- C-E-10-3: R-078-04 vs R-212-05: "the region's owner becomes the player's faction" on a transfer band / "the region follows the side that holds the base at the end ... R-078-04 are superseded" (epic says to be rewritten).
- C-E-10-4: S-210 story line vs R-210-01: "from how far the region lies from the civilization's supply" / "decided by the mission archetype ... alone ... does not change with how far into foreign ground the mission lies".
- C-E-10-5: R-077-03 vs its quoting test: rule has killed, wounded (below 30 percent HP), survived / test docstring "killed, else survived [Q-077-01: the hub also names wounded]" (register Q-077-01 closed (b)).
- C-E-10-6: R-212-07 vs RET1 test and code: "every unit made counts in both deployed power and surviving power" / test header "Units made during the mission are left out of these tests (Q-212-04 is open)"; om_mission_end_retention counts only spawned force units.
- C-E-10-7: R-074-04 vs hub line 106 (possible): "its budget is P · parity" with parity 0.75 to 1.0 / "The civilization allocates a starting force ... about a fifth of what a full mission can field."
- C-E-10-8: R-074-05 vs R-211-02: "20 percent of the player's units are removed" below capacity 0.4 / "the player has the means to accomplish it even when it is hard" (epic points to Q-211-02).

## E-11

- C-E-11-1: R-084-04 vs its test and the checker: "the unit pauses movement for 0.5 s (backswing)" / S-084 test asserts in_backswing 1 and effective_speed 0 after each of 10 steps and 0 on the 11th; inv.py BACKSWING_TICKS 10, ticks 1 to 9 after a shot are the pause, tick 10 free.
- C-E-11-2: R-084-01 vs R-083-03: "capped at 0.9" / "a second Warden in range adds nothing": Brace 0.50 + Fortify 0.20 + Warden 0.10 sum to 0.80, so the 0.9 cap can never bind.
- C-E-11-3: R-087-03 vs inv.py: "until the target dies, leaves its side's sight, or the player gives the unit a new order" / the checker also excuses leash drops (R-087-05), layer-reach loss (R-164-02) and order re-issues.
- C-E-11-4: R-087-03 and R-087-10 vs code: "Distance is spherical, layer height included (R-087-10)" / R-087-10 "The engine measures flat today" and inv.py _disp is flat.
- C-E-11-5: R-087-06 vs its test: "The engine today overwrites the ordered point with the attacker's position" / test_E11_S087_redirect_resumes_original_point.py asserts the unit resumes toward the original point and is green at baseline.
- C-E-11-6: R-087-01: "an idle or attack-moving unit" / "Not built for an attack-mover"; the one test covers an idle unit.
- C-E-11-7: R-081-04 vs R-081-01: "1.5x advantage" read by the test as 15 v 10 units / 1.5 as a damage multiplier.
- C-E-11-8: R-085-02 vs its test: "150 to 230 s" / test named 150_to_200 asserting 2850..4830 ticks (142.5 to 241.5 s).
- C-E-11-9: R-082-01 vs its test: "at least these six types" / docstring "exactly this table".
- C-E-11-10: R-087-04 test vs the lab: test_E11_S087_engage_on_sight.py header "every scene sight off" / the lab runs sight on.
- C-E-11-11: R-088-01 vs code and tests: "a squad of 5 to 10 small craft" (Raider) / csrc/unit.c OM_RENDER_CRAFT_COUNT_STRIKE 4 for Raider and Interceptor, S088 test asserts 3 to 5, tests/test_vg_a_unit_squads.gd cites R-132-03 "3 to 5 small models".
- C-E-11-12: S-086 preamble vs R-086-05: "the Bombard's Barrage reaches enemies on the layer offsets its type's reach includes, not only its own layer" / R-086-05 "every enemy within 100 wu of the position on the Bombard's layer" (the preamble says the rules below are what the game does today).
- C-E-11-13: R-204-04 has no Then clause: "Then (closed 2026-10-21, Q-174-02: a named draft, Westley tunes it by feel)."

## E-12

- C-E-12-1: R-090-03 vs the S-090 preamble: "only the observer's own interference applies" / "detection range is also scaled by (1 - interference at the target)"; the code samples the observer only and the test pins R-090-03.
- C-E-12-2: R-091-02 vs R-091-03: "the elevation bonus is retired for ground eras" and "no spawn path sets a tier yet" / "Given the Settled Reach, When elevation is read, Then it affects sensors only"; its test sets only the era name and asserts 1040, while csrc/fog.c:462 returns no bonus when era_kind is 1. Whether the Settled Reach is a ground era decides which stands.
- C-E-12-3: Epic header vs foot: "the 9 flags still open are listed at the foot" / the foot lists Q-091-01 and Q-159-09 and Q-091-01 is "closed 2026-10-21" in S-091; R-089-04 and R-090-02 still carry [Q-...] tags beside preambles that say the flag is closed.
- C-E-12-4: R-093-02 vs its test: "the union of what that side's living units see ... and what its pings reveal" / the E-12 R-093-02 test quotes "uses its own visible set" and exercises om_unit_acquire_target (observer only), while the tick uses om_tac_faction_sees (side union plus pings plus stealth).
- C-E-12-5: R-092-03 vs code: "terrain stays visible" / om_recon_is_feature_visible returns 1 in every phase (csrc/fog.c:630).

## E-13

- C-E-13-1: R-097-05 vs R-097-10: "over up to 3 iterations per tick" / "the push pass repeats up to 10 times a tick".
- C-E-13-2: Epic line 14 vs the tests: "S-207 and S-209 are design decided, not scheduled for building, apart from ... R-207-06 and R-207-07" / tests/csim/test_E13_R207_05_walker_routes.py exercises R-207-05 slope routes for walking units.
- C-E-13-3: R-207-06 vs its tests: the tests word it "never inside a blocked cell at the end of a tick (a unit placed inside one ... is ejected)" / the epic "Given a unit found inside a blocked cell ... Then it is moved to the nearest open cell and is not left stalled"; the never-enter words are the Invariant 3 text.
- C-E-13-4: R-096-08 vs itself: "stepping toward it no farther than GUARD_RADIUS = 200 wu" / the same line "The engine's guard today (A170) holds and never steps forward"; PP_unit_guard.py tests the hold under the id R-096-05.
- C-E-13-5: R-097-09 id reuse: PP_move_route.py:214, PP_collision_radius_runtime and VG_D_d7 cite R-097-09 for what is now R-207-06.
- C-E-13-6: R-101-01 vs its test: "units arrive within 2 s of each other" / the test only reports it (A161) and asserts a 29 wu pair floor against the rule's 30 wu.

## E-14

- C-E-14-1: R-120-03 vs its test: "Given cautious, When executed, Then the force moves at baseline speed and it transitions to retreat or defend when force HP lost since state entry exceeds the contact threshold" / test docstring "Given cautious, ... the force's move speed is x 0.6, spacing wider ... aggressive, Then speed x 1.2, spacing tighter" (the test body asserts 1.0 per Q-120-01).
- C-E-14-2: R-121-01 vs R-121-05 and the S-121 header: R-121-01 lists "player force in zone, enemy in range" among the threshold conditions / header "Q-121-01, both conditions, player force in zone and enemy in range, are dropped (R-121-01, R-121-05)"; R-121-05 "[Q-121-01: code returns constants 1.0 and False; the real evaluation must be defined]".
- C-E-14-3: R-120-02 vs R-123-03 and R-125-02: "once the force has contact ... it re-targets the nearest player unit group centroid" (code: centroid of all player units, enemy_macro.c om_macro_centroid) / "it never reads the player's visible set" and "the macro layer never sees what a player could not see".
- C-E-14-4: R-125-01 vs its test: "two things scale: its economic prosperity ... and its multi-layer intelligence" / test_R_125_01_only_force_parity_e_10 "only force parity (E-10 R-074-03) changes at launch" and asserts hard parity 0.85.
- C-E-14-5: R-124-01 vs the wave tests: "Given mission generation, When the external-reinforcement roll is made ... its arrival tick is fixed at generation" / test_core_reinforcement_wave.py "the wave is scheduled at tick 40 (first evaluation)"; test_core_tick_period_modules.py::test_R_124_01_arrival_window_is_period_invariant assertion message names "OM_MACRO_EXTERNAL_REINFORCEMENT_PROB=0.07" where the rule and csrc/om_constants.h say 0.21.
- C-E-14-6: R-215-06 vs Invariant 2, the Inputs table and Ways this could be wrong: R-215-06 "the player has no switch for it ... Foresight is off on easy only and on at medium and hard" / Invariant 2 "The enemy's economy never scouts, counters or disguises unless the player turned foresight on", Inputs "Enemy foresight choice | Player (E-10) | on or off | [Q-215-01: where chosen]", Ways: "Enemy foresight scaled by difficulty instead of left to the player."
- C-E-14-7: R-120-02 defend vs code: "given defend, Then it holds position and units engage what they see under the 200 wu leash" / enemy_macro.c comment "Hold: move to the objective and stay there".

## E-15

- C-E-15-1: R-126-06 vs R-218-03: "units have no cost, and a player holding zero structures receives no trickle" / "the production is paid for by the holder's economy (E-22 S-167 and S-170), not free"; the epic Ways-could-be-wrong lists "Strongpoint production free of cost, or switched at once".
- C-E-15-2: R-218-06 vs its tests and code: "the player starts with a quarter of F when they hold half of the contested strongpoints, sliding down to a fifth when they hold none and up to four fifths when they hold them all" / test_R_218_06_starting_force_at_half_share_is_600 (om_mission_compute_starting_force(1000.0, 0.5) == 600.0; knee 0.25 gives 500.0).
- C-E-15-3: R-128-02 vs R-215-05 (E-14) and the S-128 header: R-128-02 "Given the player's composition has a category at 70 percent or more, ... Then 15 percent of the target shifts to the counter category" / R-215-05 "When foresight is off, Then production follows the target ratio and never shifts toward a counter"; header "R-128-02 and R-128-03 hold with foresight off only".
- C-E-15-4: R-131-02 vs R-219-01 and the S-131 header: "it is exactly one type, sensor interference" / "different regions have different troubles" and "R-131-02's single type goes".
- C-E-15-5: R-130-01 vs R-218-07: "Given a spine node of type objective or reinforcement_structure with waypoints, ... its position is the interpolation along its waypoints" / "a strongpoint does not drift: it is fixed at its slope for now" (the epic notes this in S-130 See also).
- C-E-15-6: R-126-04 vs R-218-06: R-126-04 "the starting force is the fraction of F that R-218-06 gives" / R-218-06 "the split of R-126-04 (a fifth at the start, the rest from structures) is dropped"; R-126-04 also carries "Westley to confirm with that row".
- C-E-15-7: R-127-03 vs its test: "at 0 HP it is destroyed and stays listed as rubble, and the place command at its cell refounds it for the placer at full HP" / test docstring "at 0 HP it stays listed at 0 HP (R-218-05)" (no refound clause).

## E-16

- C-E-16-1: R-104-01 vs tests/test_vg_a_events_feed.gd header and scenes/tactical_c/hud/events_feed.gd line 3: "the ticker names six beats: structure captured, structure lost, force routed, objective threshold crossed, the economy beat ..., and a strongpoint taken or lost" / "a quiet ticker of four beats and nothing else at launch" (force routed absent in code).
- C-E-16-2: R-104-02 vs the test and code: "clears within 5 s" / "A8: the banner clears after 4 s (R-104-02: within 5 s)", BANNER_S := 4.0 (not contradictory, the test pins 4 s).
- C-E-16-3: R-104-10 vs tests/test_vg_a_unit_visuals.gd line 215: "a layer-color ring beneath it in the space era only (on land there is no ring ...)" / "A1: R-104-10 a layer-colour ring sits beneath the unit".
- C-E-16-4: R-105-06 vs scenes/tactical_c/tactical_view.gd:1206 and tests/test_vg_a_layer_view.gd header: "a layer transfer to that layer is armed for the whole selection ... Narrowing a selection to one layer is not in the beta" / "Alt+N is narrowing's, R-105-06" and "Narrowing (R-105-06) ... not tested".
- C-E-16-5: R-104-06 vs tests/csim/test_E15_S126_most_of_my_force_is_out_there.py::test_R_126_05_player_sees_timer_bar_next docstring: "Given player-owned reinforcement structures, When the structure panel is read, Then one row per owned structure shows ..." / "Given a structure, When its production is read on the HUD, Then the player sees the timer bar, next unit, and HP (E-16 R-104-06)" (old text).
- C-E-16-6: R-106-03 vs tests/test_vg_b_b23.gd header: "When d >= 37.5 (Overview) ... 20 <= d < 32.5 ... d < 12.5" / "the bible text still carries the pre-rescale 75 / 65 / 40 / 25" (header text is stale against the epic).
- C-E-16-7: R-103-01 vs tests/test_tactical_camera.gd header: "the classic view has one auto-anchor home the player returns to by key" / "The bible has NO rule that names the margin or the home key" (the test pins KEY_HOME, DRAFT-a18-home-key); R-103-07 now says "the flip is a modifier plus the anchor key" and R-103-05 "a home key returns to the classic view".
- C-E-16-8: S-107 and S-103 are "Seen" in docs/bible/stories.md while R-103-05, R-103-06, R-103-07, R-107-03 have no code found (grep).
- C-E-16-9: R-232-04 vs stories.md S-232: "Given the player's units are pinged (E-01 R-162-03), When the ping lands, Then nothing is drawn: the alert is switched off for now (Westley, 2026-10-05)" / catalog row "I see my ping and my emitting forces, I am told when I am pinged and from which way, and told when a unit cannot reach a layer."
- C-E-16-10: R-111-01 vs R-111-04: "an autosave is written before the player can continue" at "a mission start" / "there is no save of any kind during a mission". Mission start is not during a mission only if the start moment counts as before it; the catalog row for S-111 says "Saved at every chapter boundary without asking", which names neither mission start nor time jump end.
- C-E-16-11: R-111-01 vs tests/transport/test_pipe_shapes.py docstring: "a mission start, a mission end, or a time jump end" / "after mission/debrief/chronicle frames, never mid-mission".
- C-E-16-12: R-245-01 vs R-245-02: "a capture of the last 5 to 10 seconds of the simulation" / "the window is 10 s".
- C-E-16-13: R-110-02 vs tests/qa/desktop/plays/B/S-110.py docstring: current rule adds the Compatibility-renderer stand-in clause, the once-at-launch fallback and "the Settings row shows the value chosen"; the play quotes the rule "word for word" without them (stale quote).
- C-E-16-14: R-111-02 vs tests/csim/test_E16_S111_saving.py docstring: "Given a load, When the campaign resumes" / "Given a save and load between chapters".
- C-E-16-15: R-232-01 vs R-103-05 pointer in the epic (line 100): R-232-01 says the ping takes "a layer number" and a click; tactical_view.gd PING_KEY = KEY_P then a click with no layer key (code draft, not a text conflict, noted for the later ruling).

## E-17

- C-E-17-1: Epic line 24 vs csrc: "S-114 to S-119 describe the older generator that is built and tested today" (and S-114/S-115 notes "The rules below are what the game does today") / csrc/tactical_mapgen.c: om_map_generate, om_map_generate_gradients, om_fairness_evaluate, om_gradient_sample_single and 40 more bodies are `/* STUB */`, and the header says "every body below is a STUB the build card replaces". Rows R-114-02 to R-119-02 are unbuilt on that evidence.
- C-E-17-2: R-116-01 vs csrc and Q-118-01: "its dimension is drawn from small [8,000, 12,000], medium [12,000, 20,000], large [20,000, 28,000] wu square [Q-118-01: bible says fixed 8/16/24k ± 30 percent]" / om_map_get_canvas_base_dimension returns the fixed 8000/16000/24000 and om_map_compute_modified_canvas applies +-30 percent (the Q-118-01 bible reading, which R-116-02 also assumes). Not picked.
- C-E-17-3: R-116-01 vs R-166-05: "dimension is drawn from small [8,000, 12,000] ..." / "the canvas stays at its present sizes for now". Not picked.
- C-E-17-4: R-116-01 vs R-188-06: "its base category is the E-10 S-073 table" (mission.c:2038 puts Suppression in small, 0) / "the canvas is drawn from medium and large like any other" for Suppression and Counterinsurgency. Not picked.
- C-E-17-5: R-117-02 internal: "[Q-113-01: the map is regenerated with a new seed up to 5 times (bible), or accepted and logged (code, A-393)]"; the test asserts the logger-only reading. Open flag, not picked.
- C-E-17-6: R-112-04 vs R-186-03: "the layout is never bent to suit the landscape" / "the terrain is generated from the seed and accounts for the layouts of S-112". Not a hard contradiction; the direction of influence should be named when R-186-03 is built.
- C-E-17-7: R-190-07 vs R-007-05 (E-01): "an obstacle is a small annoyance and never a complete blocker" / "cover never blocks movement" (C4 note 2: E-13 R-207-06 and its test make a walker go round a box; lab ruling 'cover boxes as blocks')
- C-E-17-8: R-193-01 vs tests/csim/test_VG_E_e1q_lots.py: "Lanes follow contour lines and rivers (R-193-09), not a fixed grid" / the test (and csrc/economy_lots.c) buildable rule "lane == 0 (gx % 4 == 3 or gy % 4 == 3)", a fixed grid
- C-E-17-9: R-193-05 vs tests/csim/test_VG_E_e1c.py: "the thresholds come from the lab's layout search" and five stages "empty, staked, scaffold, small and large" / the test: thresholds 0.10/0.22/0.38/0.58 "the Q-193-02 liberty", "empty is no lot and stage 5 is reserved"
- C-E-17-10: R-191-03 vs csrc/layout_engine.c and test_at_most_six_settlements_and_home_bases: "in numbers that scale with the players and the canvas" / DRAFT-towns-max 6 (a flat cap) and a 24000 wu canvas cap
- C-E-17-11: R-191-04 vs test_resource_sites_are_equidistant: "measured along the walking route" / the test measures the straight line |p-B0| - |p-B1| within 600 wu (module docstring: Q-191-15 open)
- C-E-17-12: R-195-01 / R-195-02 vs csrc/om_constants.h: "it is 64,000 wu" and "the largest at 32,000 wu" / OM_CANVAS_SIZE_RANGES_LARGE_HI 28000 (rule 195-02 itself says it changes in a contract piece)
- C-E-17-13: R-246-09 vs csrc/mission.c:2762: "no default density and no per-region class sets it" / OM_SPACE_FIELD_DENSITY_DEFAULT 35.0 passed to om_space_field_generate_nodes
- C-E-17-14: R-246-07 ("Given a mission in any era") vs tests/csim/test_VG_D_d8.py: the tests assert the space era only and the header says 'in a space-era mission'
- C-E-17-15: R-193-02 vs tests/transport/test_pipe_vg_e.py and tests/csim/test_VG_E_contract.py: "Given difficult terrain, When density reaches it, Then the field never gives up ..." / the pins cite R-193-02 as "lots and stages" (old text of the rule)

## E-18

- C-E-18-1: R-133-06 vs csrc: "the tier it is drawn at is given by the simulation per unit, from the roster" / csrc/pipe/pipe_tactical.c:496 `cur.tier = (int32_t)om_faction_unit_tier(W, cur.faction)` (one tier per faction).
- C-E-18-2: R-134-01 vs shots.gd: "one of four categories from the manifest: projectile, volley, beam, area pulse" / shots.gd shot_category() is a fixed six-way switch by unit type, with no manifest read; R-134-05 itself assigns six units to categories.
- C-E-18-3: S-236 to S-238 headers vs code and tests: "Design decided 2026-10-02, not scheduled for building" / scenes/ground3d/*.gd, scenes/settlement/*.gd, csrc/economy_place.c and tests/test_vg_c*.gd, tests/test_vg_e_e1k.gd are built and tested for S-236 and S-237.
- C-E-18-4: Scale requirements vs E-16: "30 fps floor at 1,000 units with LOD" / the epic itself notes E-16 "states 60 fps at 1,000 units". Already acknowledged in the epic, not resolved.
- C-E-18-5: R-132-05 and R-133-05 vs hub: "an era roster of 20 to 40 types" / the baseline roster in code and tests is six types per era.
- C-E-18-6: Gate table "12 stories, 49 rules" vs the file: 50 rules and 12 stories.

## E-19

- C-E-19-1: R-140-02 vs tests/test_steam_transport.gd: "sent on a reliable channel" / `FLAG_UNRELIABLE_NO_DELAY := 13  # GodotSteam NETWORKING_SEND_UNRELIABLE_NO_DELAY`, assert "W1 send: flag is UNRELIABLE_NO_DELAY"; the session repeats each command five times (opts repeat 5) instead.
- C-E-19-2: R-140-03 vs scenes/lobby/lobby.gd:360: "the peer is dropped after 30 seconds" / `"stall_ticks": 20, "drop_ticks": 1200` with tests/test_net_match.gd "poll_accumulator_50ms" (20 polls a second, so 60 seconds); the rule itself says it supersedes the 60 second provisional setting.
- C-E-19-3: R-140-07 vs tactical_view.gd:887: "the orders a player can send in a match are move, attack-move and attack a target ... no others" / MATCH_VERBS also carries `"set_layer": 4`.
- C-E-19-4: R-143-02 vs E-20 R-148-03: "if no later era is owned by every peer the time jump is cancelled and the team stays in the current era" / "Given the last owned era, When the next time jump comes, Then history loops ... in solo campaigns and in matches alike".
- C-E-19-5: R-141-01 vs R-159-01: "Given a match, When it starts, Then it is played by teams of 2 or 4 (S-241)" / "An optional mode, entered only through the paired queue".
- C-E-19-6: R-142-04 vs R-144-03: "fixed with the universe" (the shared-vision default) / the R-144-03 lock list names player count, slots, era packs, paired economic roles and simulation switches, and no vision setting.
- C-E-19-7: tests/net/test_desync_detect.py docstring cites R-140-03 for "a checksum mismatch ... within 10 ticks of the tick it was due"; that text is R-139-04's; R-140-03 is the stall rule.
- C-E-19-8: tests/csim/test_PP_portability.py header: "E-19 R-140-02..4 (every peer's sim agrees byte for byte ...)" for the determinism contract; the determinism rules are R-139-01 and R-139-02.
- C-E-19-9: Gate table "9 stories, 33 rules" vs the file: 9 stories, 35 rules.

## E-20

- C-E-20-1: R-146-02 vs the test that cites it: "no longer byte identical, superceded" (Westley, 2026-10-05, quoted in the rule) / tests/specfactory/test_pack_validate.py module docstring "they are mechanically identical (R-146-02)" and test_greek_placeholder_mechanically_identical_to_settled_reach asserts "MECHANICAL DIFF OK" between the space and ground packs.
- C-E-20-2: S-146 header vs R-146-02: "the three launch packs carry byte-identical mechanical config for the MVP; the content diff fence asserts it" / R-146-02 "[Q-146-01 superseded ...]" and two launch eras (S-147).
- C-E-20-3: R-148-03 vs E-19 R-143-02: "history loops ... in solo campaigns and in matches alike" / "if no later era is owned by every peer the time jump is cancelled and the team stays in the current era".
- C-E-20-4: R-145-02 vs code: "no `if era ==` branch exists anywhere" / scenes/onboarding/onboarding.gd:304 `if era_id == "roman":`.
- C-E-20-5: R-146-04 and R-146-01 vs R-150-03: "a 20 to 40 type roster per era" and "one unit model per roster type per tier" / "a skin ... maps to the six abstract types and three tiers, and to the worker, ... and nothing else".
- C-E-20-6: S-243 header vs code: "Design decided 2026-10-02, not scheduled for building" / pack_validate.py already requires `buildings` and checks `movement`, and both manifests carry `buildings`.
- C-E-20-7: Gate table "8 stories, 28 rules" vs the file: 8 stories, 30 rules.

## E-21

- C-E-21-1: R-154-07 vs register Q-155-01 and the epic's own S-154 "Open flags: none. Q-155-01 closed 2026-10-21": rule text "Then [Q-155-01: reuse the oldest historical name, or generate a numbered fallback]" / register "closed ... Reuse the oldest historical name". The rule line still carries the open bracket and both candidates.
- C-E-21-2: R-153-01 vs register Q-153-02 (closed 2026-10-18, (b)): "mission archetype entries (each carrying the kind of base each side is given and the slant of its resources, E-22 S-177)" / "(b) config, beside the archetype table" (base kind and slant live in config, not in a library entry).
- C-E-21-3: R-153-01 vs register Q-153-01 (closed 2026-10-18, (b)): "behavior scripts per archetype (E-14), layout hints (E-17)" produced as libraries / "(b) scripts and layouts stay code-adjacent data".
- C-E-21-4: docs/bible/stories.md S-153 row "Spec'd, blocked on Q-153-01" vs register Q-153-01 "closed".
- C-E-21-5: R-152-04 vs the project instructions: "uses the model named in the project instructions (currently `claude-sonnet-4-20250514` for the builder)" / CLAUDE.md names no builder model (the name appears only in docs/northstar/plans/briefs/2026-09-21-px-batch-c-vision-archive.md).

## E-22

- C-E-22-1: R-179-01 vs tests/csim/test_VG_E_e1g.py: rule "Given any match, When nobody holds the economy seat, Then rules run the economy, run it well, need no intelligent agent, and call no model at play time." / test module docstring "R-179-01 (E-17 S-193): four doctrines boom, fortify, press, balanced." (the manifest-list meaning now lives in R-179-03).
- C-E-22-2: R-168-05 vs tests/csim/test_VG_E_e1f.py: rule "they include drop-off points, housing, production buildings (E-22 S-170) and defenses (E-22 S-174)" / test ROLES = {production, house, worker-hut, forward-works}.
- C-E-22-3: R-176-02 vs Invariant 2 vs Obviously working: R-176-02 "it sees it on the map like any unit, as the enemy does (it is visible to both sides)" / Invariant 2 "A side never sees a shipment on its way" / Obviously working "A shipment sent to a base never shows on the map". RPT s3.8 records this as Q-176-05, open.
- C-E-22-4: Gate table "16 stories, 83 rules" vs the file: 16 stories, 86 rule lines (85 live, R-177-03 is a tombstone).
- C-E-22-5: R-175-05 sits before R-175-04 in the file (order only; both rows kept in file order).
- C-E-22-6: R-177-03 is a tombstone line ("Removed 2026-10-06"); it has a row because it has a rule line; marked unbuilt, nothing to prove.

Total: 156 conflicts.
