# Targeting rulings of 2026-11-17: where the documents, tests, checker and engine still say the old thing

Read-only audit of worktree `rulings-1117` at df7314753. Nothing was built or run, so every "red" below is a reading of the setup against the new rule text, not a test result. Verdict words: **red** (the assertion asserts the old behaviour or a number the old behaviour produced), **likely red** (depends on fight dynamics or a recorded number; not run), **may shift** (could move, could not), **stale text** (green, but the words quote the old rule). Basis column: **read** means I opened the lines; **grep only** means the line came from a search and I did not open the surrounding test.

The five changes, as numbered in the brief: 1 acquire only within the notice distance (own attack range plus one tenth), never the sensor radius; 2 a lock also ends when the target leaves the notice distance (return-fire targets excepted); 3 after the 200 wu move away from unseen fire the unit holds, an attack-mover still on its way included; 4 two units on one slope collide across the layer line; 5 slant reach between two walking units only.

Totals: A 11 rows (no other document in scope disagrees). B 62 rows: 16 individual tests red or likely red by reading, 2 more that may shift on timing, 20 rows of recorded hashes and pinned fight numbers that will move, the rest green or stale text. C 5 predicates or pins. D 7 sites. E 0 layouts without an approach order, 2 groups layouts and 4 large layouts worth a first look.

## A. Documentation that still states the old behaviour

| Path | Line | What it says | Change | Basis |
|---|---|---|---|---|
| `docs/bible/epics/E-11-units-and-combat.md` | 183 | "The rules below are what the game does today, including that acquiring, pursuing and firing use the side's visible set". Line 209 says the three rulings are not built, so line 183 now overstates. | 1, 2, 3 | read |
| `docs/bible/epics/E-13-movement-and-command.md` | 268 (Invariants) | "No two same-layer units within 30 wu after the collision pass, except when the pass hits its iteration cap." R-097-05 (line 92) now also pushes two units on one slope. | 4 | read |
| `docs/bible/epics/E-14-enemy-macro-behavior.md` | 36 (R-120-02) | defend: "units engage what they see under the 200 wu leash of R-087-04". They engage what is inside the notice distance; R-087-04 no longer carries a 200 wu leash (R-087-05 is the leash). | 1 | read |
| `docs/bible/algorithms.md` | 266 (ALG-62), 268 | "an attack-moving unit with sensor radius > attack range acquires the nearest visible same-layer enemy within sensor radius and moves toward it"; flinch "moves 200 wu away" with no hold. Line 268 says "The text above is what the game does today." | 1, 3 | read |
| `docs/bible/algorithms.md` | 288 (ALG-68) | "After movement, same-layer pairs closer than 2 times 15 are pushed apart". Same sentence says "Attack-move leash 200 wu", already stale against R-087-05 and not one of the five. | 4 | read |
| `docs/stories/H-057.md` | 3, 15, 17, 23, 27-33, 40 | Banner at line 3 already marks the acquisition distance as superseded; the body still states "within its sensor radius" (line 15), tests at 400 wu off the path (lines 30-33), and the defend consequence (line 17). Kept as a record. | 1 | read |
| `docs/northstar/story_reviews/westley/beta-staircase.md` | 34 (B8) | "fights under the lab's engine rules (H-057 engage-on-sight and the per-type leash)" | 1 | read |
| `docs/northstar/plans/engine-rules-2026-11-08/spec.md` | 15, 52, 75-78 | F3 and the R-087-03 check: a target changes only when it died, left sight, a new order, the leash or R-087-09; "keeps chasing its locked target ... walks until in range". No notice distance. Dated plan. | 2 | read |
| `docs/northstar/plans/engine-rules-2026-11-08/spec.md` | 99 (F7) | "apply the one metric to attack range, sensor radius, leash and area radius" and "every range and radius test". R-087-10 now says weapon reach only, and walking units only. Already stale since 2026-11-11. | 5 | read |
| `docs/northstar/research/layer_dynamics/README.md` | 112, 138 | "re-engage is a lab stand-in for the engine's pending sight-engagement rule". The rule is no longer pending; Westley overruled it. The sentence is pinned verbatim by tests (section B, row 41). | 1 | read |
| `docs/northstar/research/layer_dynamics/INVENTORY_2026-10-30.md` | 70 | "R9 sight-engagement engine rule (Starcraft rule set, approved), then retire the re-engage stand-in." Dated inventory. | 1 | grep only |

Checked and found consistent or silent, no row: `docs/bible/game_bible.md`, `docs/bible/stories.md` (S-087 line 93 "shoots the nearest thing in range"), E-01 (R-008-01, R-004-06, R-004-08 say nothing about collision), E-12 R-093-02 (visible is a precondition, not a distance), E-15, E-22, `docs/architecture.md` (no targeting or collision text), `docs/stories/` other than H-057, `lab-staircase.md` (line 44 "acquires and fires at any enemy in range" agrees), the layer_dynamics documents other than the two above. Change 5 agrees everywhere it is stated: R-087-10 only; the engine already does it (unit.c 626-630).

Outside the list I was given, same old wording, not audited: `docs/northstar/ROADMAP.md:24`, `docs/northstar/story_reviews/westley/thresholds_batch_2026-11-01.md` rows 5 to 9, `docs/northstar/story_reviews/westley/arena_stage3/README.md:5`.

## B. Tests

### B1. The two hand-checked files

| Path | Line | What it asserts | Change | Verdict | Basis |
|---|---|---|---|---|---|
| `tests/csim/test_E11_S087_engage_on_sight.py` | 53 | two idle Vanguards 400 wu apart both hold a target within 200 ticks (notice 330) | 1 | red | read |
|  | 98 | lone attack-mover passes an enemy 400 wu off its path, acquires it | 1 | red | read |
|  | 156 | group of 8 engages a lone enemy 400 wu off the line | 1 | red | read |
|  | 209 | idle Vanguard acquires an enemy 400 wu off, chases to its leash | 1 | red | read |
|  | 238 | idle Raider (range 200, notice 220) acquires at gap 400 | 1 | red | read |
|  | 254 | idle Vanguard walks to and shoots a standing enemy 400 wu off | 1 | red | read |
|  | 358 | two 16-unit blobs attack-moved to one point end by elimination, not stand-off. Survivors of the H-057 stall sat 305 to 453 wu apart, partly beyond 330. | 1 | likely red | read |
|  | 72, 118, 177, 266, 278, 310, 370, 383 | controls: 900 wu apart stay apart; marches with no enemy; Bombard keeps its target to 1200 (150 wu away, in notice, leash unchanged); plain move never acquires; baseline switch 0 | none | green; docstrings quote "within its sensor radius" | read |
| `tests/csim/test_PP_unit_leash.py` | all 7 tests | leash before or after damage; every enemy is 150 to 250 wu from the unit, inside notice 330; leash is the sensor radius, unchanged | none | green, nothing stale | read |

So the file that cites R-087-05 and R-096-03 is untouched by the rulings, and the file whose id table row looks the same is half red. A table built from rule ids alone would put both in the same column.

### B2. Tests that assert the old acquisition or lock (changes 1 and 2)

| Path | Line | What it asserts | Change | Verdict | Basis |
|---|---|---|---|---|---|
| `tests/csim/test_PP_unit_pursuit.py` | 59 | Raider holds a target, target teleported to 350 (notice 220), "the march goes on toward it", goal stays 350,0 and the unit walks back into range | 2 | red | read |
|  | 90 | idle Raider keeps a target moved 300 wu out (range 200) for a whole cohort cycle: "kept at any distance" | 2 | red | read |
|  | 140 | Raider (range 200) whose friend sees an enemy 600 wu away "walks toward the enemy its friend sees (east)" | 1 | red | read |
|  | 123 | stealthed enemy in range not acquired | none | green | read |
| `tests/csim/test_PP_C_g3_pursuit_by_sight.py` | 53, 75 | Raider marching west with an enemy 700 east: "a seen enemy out of attack range is chased", distance shrinks (both carry `Test-defect, H-057` comments that undo the A199 pin) | 1 | red | read |
|  | 38 and the tests after 106 | hidden enemy not pursued, nothing reacts beyond sensor, no holding against a hidden enemy, holding against a visible one in range | none | green | read |
| `tests/csim/test_PP_attack_move_no_sight_pursuit.py` | 145 | Vanguard acquires a Raider 250 ahead; Raider moved to 350 (notice 330); target "kept on every tick of the next 10" and walked back into range | 2 | red | read |
|  | 183 | baseline switch 0 steps toward a seen enemy | none unless the baseline arm is changed (D2) | green | read |
|  | 132, 171, 194 | in-range halt and fire, resume route, blocked cell | none | green | read |
| `tests/csim/test_E13_R096_08_guard_steps_and_returns.py` | 154 | control: an unguarded idle Vanguard walks out past 200 wu for an enemy at +690 (seen, 390 beyond range) | 1 | red | read |
|  | rest of file | guard scenes (guard engages within radius plus range, not notice) | none | green | read |
| `tests/csim/test_E11_R087_03_target_lock.py` | 78, 92 | Raider locks a Vanguard walking away at 3.5 wu a tick; lock must hold past range 200. The 10-tick backswing after a shot lets it reach about 235 (notice 220) before the Raider can walk. | 2 | may shift (probably red) | read |
|  | 104-156 | controls: nearest of three, nearer enemy appears, new order, dead target, sight loss | none | green | read |
| `tests/csim/test_E11_S087_every_unit_thinks_the_same_way.py` | 100 | "attack-moving unit with no enemy in attack range but a visible one within sensor range moves toward it". Passes anyway: the unit marches toward x 1000 whatever it sees. | 1 | stale text, green | read |
| `tests/csim/test_core_macro_group_orders.py` | 148 | contact at 500 wu; docstring "H-057: idle units engage on sight". The macro re-targets on contact and the squad walks in. | 1 | stale text; probably green | read |
| `tests/csim/test_E13_S096_four_commands.py`, `test_PP_unit_leash_anchor.py`, `test_PP_leash_own_distance.py`, `test_E11_S087_redirect_resumes_original_point.py`, `test_PP_unit_return_fire.py`, `test_E11_R087_04_chase_resumes_after_the_pause.py`, `test_E11_R087_09_blocked_line_gives_up.py`, `test_PP_unit_blocked_target.py`, `test_PP_unit_attack_move_group.py`, `test_E13_S096_attack_move_resumes.py`, `test_PP_unit_guard.py`, `test_PP_unit_target_policy.py` | all | targets inside 330 or on the march line, return-fire pursuit (exempt from the distance break), leash tests (leash unchanged) | none | green | read (setups), docstrings quote the old rule in the leash files |

### B3. Tests that assert the old move away (change 3)

| Path | Line | What it asserts | Change | Verdict | Basis |
|---|---|---|---|---|---|
| `tests/csim/test_E11_R087_01_unseen_attacker_moves_the_unit.py` | 305 | after the move away the attack-mover that had not arrived has its original point as destination again and walks 40 wu nearer it | 3 | red | read |
|  | 326 | repeat hit moves it again; starts from the first stop, not the first hit | 3 | likely green | read |
|  | 275, 286, 187-260, 341-449 | first move 150 to 250 wu; controls; wall and canvas edge | none | green | read |
| `tests/csim/test_E11_R087_01_move_away_completes.py` | 116 | control "completes the move away and resumes its attack-move": destination is the original point again, 40 wu nearer after 20 ticks. Header quotes the old rule word for word. | 3 | red | read |
|  | 136, 151, 166 | move away covered 150 wu for group members and a pursuing unit | none | green | read |
| `tests/skilllab/arena/engine_rules_unseen_oracle.py` | 1-15 header | quotes "an attack-mover then resumes"; the measure (stands more than 60 ticks in unseen fire) still works | 3 | stale text | read |

### B4. Tests that assert the old slope collision (change 4)

| Path | Line | What it asserts | Change | Verdict | Basis |
|---|---|---|---|---|---|
| `tests/csim/test_PP_move_collision.py` | 104 | units on layer 0 and layer 1 do not collide. No terrain, no slope, so the new rule does not apply. | 4 | green; title and docstring "same-layer pairs only" stale | read |
| `tests/csim/test_E01_R004_layer_change_is_continuous.py` | 102 (6 roles) | walker climbs a ramp into 8 friends standing on the ramp's upper part: flips layer, pushed back, flips again, jumps. This is the pile-up change 4 removes. | 4 | may shift (expected to stay or turn green) | read |
| `tests/skilllab/arena/test_engine_rules_f8_continuity.py`, `tests/skilllab/arena/test_invariants_continuity_sight_wiring.py` (81) | 78-130, 81 | hill-fight continuity counts and the dense-blob 15 violations | 4 | may shift | grep only |
| `tests/csim/test_collision_radius.py`, `test_E13_R097_10_idle_own_units_yield.py`, `test_E13_S097_around_not_through.py` | 13, 9, 141 | quote "same layer" in R-097-05 or ALG-68 | 4 | stale text | grep only |

### B5. Recorded hashes and pinned fight numbers that will move

These pin a whole run, so they go red on any change of target choice or movement inside the run. Earlier engine rounds re-recorded each of them (their comments say so).

| Path | Line | What is pinned | Change | Verdict | Basis |
|---|---|---|---|---|---|
| `tests/csim/test_F2_nearest_hostile_search.py` | 439-461 (GOLDEN) | state hash of a 600-raider clash and spread, attack-moving, 400 ticks; idle enemies sit beyond 220 | 1, 2, 3 | likely red | read |
| `tests/csim/test_F3_macro_contact_skip.py` | ~245-260 | clash and spread golden | 1, 2, 3 | likely red | grep only |
| `tests/csim/test_F1_fog_per_faction_observers.py` | ~301-310 | clash and spread state hash | 1, 2, 3 | likely red | grep only |
| `tests/csim/test_PP_C_g3_hash_invariant.py` | 134-151 | reuses the three goldens above with sight off | 1, 2, 3 | likely red | read |
| `tests/csim/test_E13_A99_tactical_equivalence.py`, `scale/test_scale_A99_tactical_equivalence.py`, `data/a99_tactical_hashes.json` | whole | per-step hash of idle and fight runs (gaps 100 to 3000) | 1, 2, 3 | likely red for the fight runs | grep only |
| `tests/csim/test_PP_portability.py` | 41-47 | seed-3 checksums at ticks 100, 500, 1000, 2000 (tick 2000 moved at H-057) | 1, 2 | may shift | read |
| `tests/csim/test_collision_radius.py` (344), `test_PP_collision_radius_runtime.py` | 58, 344 | save bytes of a 100-tick mixed scene | 1, 4 | may shift | grep only |
| `tests/csim/test_E01_T2_collision_mask.py` (30), `test_E01_T2_walker_waypoint_arrival.py` (49) | | flyer section hashes | any new hashed field | may shift | grep only |
| `tests/csim/test_E11_S085_long_enough_to_think.py` | 39, 68 | fight length windows (known red since H-057) | 1 | may shift | grep only |
| `tests/csim/test_F2_nearest_hostile_search.py` | 539 | distance-test budget 8604, measured 34228 since H-057 widened the radius | 1 | may turn green | grep only |
| `tests/transport/test_pipe_tactical_delta_frame.py` | 356 | first death inside ticks 1600 to 1800 (now about 1690) | 1, 2 | may shift | read |
| `tests/transport/test_pipe_assign_commander.py` | 42 | `CLASH_STEPS` 5900 with first loss at about 5765 | 1, 2 | may shift | read |
| `tests/skilllab/arena/test_invariants_round2_wiring.py` | 53 | L-0039 seed 10 runs 2314 ticks | 1, 2 | likely red | read |
| `tests/skilllab/arena/test_invariants_continuity_sight_wiring.py` | 121, 136 | L-0039 seed 1 2314 ticks, control 2730 | 1, 2 | likely red | read |
| `tests/skilllab/arena/test_invariants_round2b_wiring.py` | 62 | L-0061 2136, L-0084 3923, cover fixture 801 | 1, 2 | likely red | read |
| `tests/skilllab/arena/test_engine_rules_r3_sight_lock.py` | 151 | L-0084 seed 1 3923 ticks | 1, 2 | likely red | read |
| `tests/skilllab/arena/test_engine_rules_r3_move_away.py` | 106 | L-0081 seed 1 741 ticks | 3 | likely red | read |
| `tests/skilllab/arena/test_engine_rules_r4_idle_yield.py` | 172-211 | L-0028 and L-0045 premises (12,000-tick cap, 41 runs, 10,840 unit-ticks) | 1, 2 | likely red | read |
| `tests/skilllab/arena/test_engine_rules_f9_unseen_fire.py` | 92 | L-0080 has 494 unseen hits | 3 | may shift | read |
| `tests/skilllab/arena/test_engine_rules_f3_lock.py` | 27 (3 fights) | `oracle.lock_swaps` is empty over L-0039 and L-0050, which is the old lock text | 2 | likely red | read |

### B6. Lab tests that quote or pin old wording

| Path | Line | What it says | Change | Verdict | Basis |
|---|---|---|---|---|---|
| `tests/specfactory/test_lab_docs.py` | 562 | README must contain "re-engage is a lab stand-in for the engine's pending sight-engagement rule" | 1 | stale text; red the day the README is corrected | read |
| `tests/skilllab/test_drift_fix_header_notes.py` | 30 | same sentence as `STANDIN` | 1 | stale text; same | read |
| `tests/skilllab/arena/test_invariants_round2_wiring.py` | 132 | `xfail(strict)` "R-087-04 says 'within its sensor radius'; the engine acquires out to the attack range" | 1 | stale text; remains xfail (Bombard and Bastion notice still exceeds their sensor) | read |
| `tests/skilllab/integration/test_speed_equal.py` | 159 | comment "re-pinned for H-057: on the mirror, engage on sight leaves no silent idle unit" | 1 | stale text | read |
| `tests/skilllab/arena/test_run.py` | 456 | comment "since H-057 engage-on-sight an idle unit acquires out to its type's sensor radius" | 1 | stale text | read |
| `tests/skilllab/integration/test_attackmove_idle_cap_real.py` | 98 (gated OM_LAB_SLOW) | layout-192 lone attacker ends by elimination, not the cap. The idle-short-of-the-point cap returns when nothing pulls it in. | 1 | may shift | read |

### B7. Not individually read

About 100 further files under `tests/skilllab/` (`integration/*_real.py`, `arena/test_stage*`, `ground/*`) run the real engine through `fight.fight` or `oracle.played`. I grepped them for pinned outcomes and found only the ones listed above; the rest assert rule predicates over a whole fight (cell entries, shots while moving, lock swaps) or lab plumbing. Those predicates are unchanged except the lock check (section C). Among them `test_contact_real.py:70`, `test_reengage_real.py:60`, `test_outcomes_real.py:52` and `test_ground_slope_real.py:80` assert that fights end by elimination or cap and may shift. `tests/qa/desktop/plays/A/test_S_096_commands.py`, `test_S_134_shots_and_hits.py`, `test_S_136_deaths.py` play mission fights in Godot; timing may shift. `tests/test_tactical_attack_move.gd` and `test_tactical_view.gd` cite R-096-02 only for the client command, unaffected. **grep only** for this whole row.

## C. The lab checker and its oracle

| File | Line | Predicate | What it encodes | Change |
|---|---|---|---|---|
| `scripts/skilllab/invariants.py` | 211-238 (`_Checker._lock`) | R-087-03 lock swap. Flags "target X -> Y while X was alive and seen" unless excused by a new order, sight loss, out of reach, give-up (`_gave_up`) or `walked > leash - LEASH_SLACK`. A target dropped for leaving the notice distance would be flagged. | 2 |
| `scripts/skilllab/invariants.py` | 307-359 (`_acquire`) | R-087-03 nearest: "the nearest enemy that frame's visible set of the unit's side holds", at any distance. Still correct for the nearest-pick; it never checks that the pick was inside the notice distance, so an acquisition at 400 wu raises nothing. | 1 (missing check) |
| `scripts/skilllab/invariants.py` | 440 (`self._sensor[u] = max(st["sensor_radius"], st["attack_range"])`) and 224 | the leash fed to the lock excuse. Correct for R-087-05, which is unchanged; listed because it is the only distance in `_lock`. | none |
| `tests/skilllab/arena/engine_rules_oracle.py` | 238-260 (`lock_swaps`) | "the unit's target changed from a living enemy that its side still sees to another enemy ... excused if the unit walked farther than its sensor radius plus 25 wu". Same gap as `_lock`. Used by `test_engine_rules_f3_lock.py`. | 2 |
| `tests/skilllab/arena/engine_rules_unseen_oracle.py` | 1-15 | header quotes the old R-087-01; the measure (stand within 50 wu of the first hit for more than 60 ticks) stays valid because the hold ends in a new move on the next hit | 3 (text only) |

No predicate in either file tests acquisition by sensor radius directly, and none tests collision across layers.

## D. Engine sites (locate only)

| # | File and function | Lines | What is there | Change |
|---|---|---|---|---|
| 1 | `csrc/unit.c` `om_tac_unit_ai` | 2565-2585 | acquisition radius `acq = om_tac_leash(w, u)`, raised to `attack_range`; applies to idle and attack-moving units, not to a guard or a unit on its way back (`anchor_set == 2`). Feeds `om_tac_nearest_actable` (2118), `om_tac_nearest_hostile` (1888) and `om_tac_pick_across` (1791). | 1 |
| 2 | `csrc/unit.c` `om_tac_leash` | 1045-1056 | `max(sensor_radius, attack_range)` per type. One helper serves both the acquisition radius (site 1) and the leash `om_tac_leash_broken` (1038, R-087-05, unchanged). | 1 |
| 3 | `csrc/unit.c` `om_tac_unit_ai` baseline arm | 2655-2670 | pursue-off arm: `om_tac_nearest_hostile(st, u, prof->sensor_radius)`, hold and step toward. Old engage rule kept for switch 0 and its goldens. | 1 |
| 4 | `csrc/unit.c` `om_tac_unit_ai` lock block, `om_tac_lock_sees`, `om_tactical_ai_tick` | ~2511-2555; 1231; 2702-2712 | lock drops: dead or not hostile, attack-target out of reach, sight (`om_tac_lock_sees`, read from the pre-pass), reach or stealth, `anchor_set == 2` out of range, leash, give-up. No test of distance from the unit other than the leash and range. The guard has its own copy in `om_tac_guard_tick` (2293). | 2 |
| 5 | `csrc/unit.c` `om_tac_unit_ai` flinch block and `last_attacker` branch, `om_tac_start_flinch` | 2440-2452; 2467-2480; 2086 | kinds 1 idle, 2 resume, 3 hold. Line 2471 `resume = has_dest && !arrived`; line 2479 picks kind 2; line 2448 `if (resume) om_tac_end_pursuit(...)` is where the attack-mover goes back to its point. Nothing tests "its side sees the attacker" as the end of a hold. `om_tactical_ai_tick` 2716-2726 skips flinching units in the pursuit-end check. | 3 |
| 6 | `csrc/tactical_move.c` `om_move_collide_pair` | 1763 | `if (ms->col_pursue && ms->start_layer[ia] != ms->start_layer[ib]) return 0;` The array is filled in `om_move_collision_pass_internal` (1979) and at 2798. Slope membership would come from `om_terrain_slope_at` (terrain.c 1269). | 4 |
| 7 | `csrc/tactical_move.c` blocker gather for the steering probe | 2053-2072 | the same `start_layer` array filters which units block a probe (R-097-03 "a unit on its layer"). The ruling names the collision pass only. | 4 (not named) |

Change 5 is built: `om_tac_dist_le_layers` (unit.c 628-630) measures flat unless both units are walkers.

## E. Layouts likely to end in a stand-off under change 1

The brief asked for layouts where no order brings either side within about 330 wu of the other. I read all 84 `catalogue/L-*.toml` files and the order rules in `scripts/skilllab/arena/run.py` (`_orders_point`, lines 89-100 and 201-221). Judgement: the `orders` key is `both_same_point` in 57 layouts (both sides attack-move to the midpoint of the two centroids, or to `orders_point`), `hold:A` or `hold:B` in 25 (the other side attack-moves onto the holder's centroid; the attackers' straight path to the holder's centroid passes within 196 wu of a holder unit in every one), `groups` in 2. In the first two classes the order point sits inside both forces, so the sides meet.

**Count with no approach order: 0.** The two `groups` layouts L-0080 and L-0083 (trap, 16:32 and 24:48) are the only ones where the trappers hold on the hills until a release trigger; their fight starts when red walks inside the notice distance of the hills, which the layout does not guarantee.

The realistic stand-off is late in a fight, not at the start: survivors stand idle after their attack-move arrived, with enemy survivors 330 to 700 wu away (the L-0054 stall of H-057). That cannot be read from orders. The four largest layouts are the likeliest: L-0054 (128:128 open field, centroids 2788 apart), L-0046 (64:64 city), L-0045 (40:56 slope), L-0084 (40:56 slope, hold:A). Nineteen `both_same_point` layouts have a unit more than 330 wu from its own side's centroid (among them L-0019, 0020, 0021, 0028, 0029, 0030 on large_tiered; the trap layouts L-0079, 0081, 0082, 0032, 0033; cover L-0007, 0008, 0009); their far units walk in under the order, so I did not count them.

## Notes on method and limits

- Nothing was run. Pinned fight lengths and recorded hashes are marked "likely red" because the notice distance changes who walks when, not because I measured a difference.
- Section B started from the 85 files (tests, scripts, one mockup) that cite one of the listed ids in any form, `R_087_04`, `R087_01` and `Rule pins:` headers included; files whose cited rule is unchanged (leash, plain move, return fire) got no row unless I opened them.
- The id table missed these tests because they cite other ids: `test_PP_C_g3_pursuit_by_sight.py` (R-093-02, R-089-02 in the names), `test_PP_unit_pursuit.py:90` (R-087-04 in the name only), `test_E13_R096_08_guard_steps_and_returns.py:154` (R-096-08), and the five hash-pinned files in B5, which cite no rule at all.
