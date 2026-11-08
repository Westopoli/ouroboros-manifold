# Test forensics: why the movement/targeting tests let the L-0039 faults through

Read-only investigation, main 53c25f5b, 2026-11-07. Nothing in `~/Projects/ouroboros-manifold` was edited. All experiments ran on `git archive HEAD` copies under `.../scratchpad/mut/` (base, m1..m7). Baseline: 137 test files (tests/csim PP, E13, E11 S08x, E01 T2/R00x, VG W/D, core, F1-F3), 1750 pass, 12 red on HEAD itself (all already in `scripts/specfactory/gd_tests_known_red.txt`: A99 hash tests, W7 probe, S-085 x2, F2 budget).

## 1. The cascades and stories that made this code

Movement, terrain guard, walker, targeting, fire:
- B12 movement port, manager-mode cascade leaves "rebuilt on main": 28e69ddb (tactical_move.c, 2026-09-24), f929ef48 (shot LOS blocked by cover/terrain R-095-04 R-098-02), c082decf, cc1547cc, c8d47cd2, c225a302 (perf, "bit-identical"), 7ed6836f (arrival).
- Python-parity push "plan P" (2026-10-02, docs/northstar/plans/2026-10-02-tactical-port-parity-requirements.md; Westley: "use the same exact logic from the python"). Tests first by a separate writer: aa920cee (PP-move tests), 9f7c0124 (PP-unit tests), 48368ec1, 12b7bd48, b97c5368 (A171 blocked-target), 544dbbf3 (G4), 62361c37 (G5), 7964a6bb (G3). Builders: a47c9876/766890d4/1d085a74/c5418f05 (M1-M5), fdc064e0 (R2 route grid), **a4b5236a (R3: "unit never enters a blocked cell, one inside is moved out")**, 13d2cfab (R4 fire side), 682464d6 (A5 stationary/push), e086a290 (U3 pursuit), 7b19a3e0 (U2 return fire), 28433813 (A171: halts only when it can shoot), 7e7b0f83 (guard), 3e17a6e6 (G3 acquire by side sight), 87bc4caa + 788ad366 (fog.c blocked cell blocks sight, corner clip).
- Walker / terrain stage 2: tests 6da22acd (2026-10-06), builder **23b37f82** (walkers steer om_walk_route; om_move_walker_step has no cell guard), 973bbd2f + 67957c10 (no corner cutting, waypoint arrival), bd169a90 (walker push slides on walk mask), VG-W1/W2 6621ef96, fd4e3cbd.
- Engage on sight, per-type leash: H-057, fb7be351 (2026-11-01), tests e13ffdd9/eda4bde3/576b5954, re-pin storm 5cee9e8e..d38ffd0d (2026-11-01/02).
- Later: E1 e721da83 (attack-move group resumes), E1b f26fe93f, H-041 892f15ca/84bb2269.

## 2. Test-by-test classification and what each would have caught

Legend: SCEN = scenario (few units, fixed ticks, one outcome); INV = assertion inside a per-tick loop; GOLD = hash of a whole run.

| Behaviour | Test | Kind | Catches blocked-cell / walk-while-fire / target flip? |
|---|---|---|---|
| walker step vs blocked cells | test_E01_R001_07_walking_kind.py:66 (2000 ticks, random orders) | INV, 1 unit, no enemy | No: tests the terrain *walk mask* (`om_terrain_walk_mask`), with a generated terrain. Lab boxes are `om_map_block_rect` cells (mapgen), walkers with no terrain fall back to them (tactical_move.c:1276-1280). No box in the scene. |
| same | test_E01_T2_walker_no_corner_cut.py:143 (16-walker blob, 600 ticks) | INV, mask only | No, same reason; no enemy, no fire. |
| same | test_E01_T2_collision_mask.py | SCEN/INV, mask | No (push result only). |
| steer unit never enters wall | test_PP_move_route.py:131, :157, :177, :253; test_PP_C_g4_routing.py | INV (per tick), 1 unit, plain move, `OM_TP_ROUTE_AROUND_TERRAIN=1` | No for walkers (fliers path only). Also **does not exercise the guard**: the unit is routed round the wall so the guard never fires; deleting it (mutation M1) leaves this test green. |
| found inside cell is moved out (R-207-06, test cites old R-097-09) | test_PP_move_route.py:214, test_PP_collision_radius_runtime.py:336, test_VG_D_d7.py | SCEN: unit spawned inside, one tick | No: proves the eject helper exists (killed by M2), not that nothing re-enters; the eject masks the bug (unit saws in/out). |
| blocked target does not halt march (A171) | test_PP_unit_blocked_target.py:96-170 | SCEN, 1 attacker vs 1 stationary Supply (target "never fires so it cannot change what the attacker does") | No. And A171 itself (walk while `can_shoot` is 0, hold when 1) is the mechanism of the L-0039 drift once the target oscillates; no test has a target that moves across the face. |
| halts-to-fire R-087-04 / R-096-02 | test_E11_S087_engage_on_sight.py:53,254; test_PP_unit_pursuit.py:59; test_PP_attack_move_no_sight_pursuit.py | SCEN, 2 units, sight OFF ("every scene runs sight off"), no terrain; asserts `hp(target)` fell and final distance <= range | No. Liveness ("it closed and fired"), not "stays put while firing". |
| nearest / kept target R-087-03 | test_PP_unit_target_policy.py:40, test_E11_S087_every_unit_thinks_the_same_way.py:77 | SCEN, 1 unit vs 3 static dummies; "kept" = teleport one enemy, `step` once, compare | No flip-flop catch: one tick, static targets, no cell boundary. Result depends on cohort phase (test-defect A163/A164 changed 1 step to 4). |
| stationary never pushed R-097-10 | test_PP_move_collision.py:72, test_PP_move_collision_a5.py:61-139, test_E13_S097:190 | SCEN (one pass or 200-tick pair), plus INV test_PP_move_collision_a5.py:139 (min pair distance over 200 ticks) | Pair-level only; no push into a cell during a fight. |
| E-13 invariants | bible E-13 line 211-217: 5 invariants | 3 have a scenario test, none is checked over a fight; "unit never enters blocked cell" only as above | No. |
| R-207-06/07 | named only in tests/test_vg_c4_ground_pick.gd and tests/qa/desktop/plays/C/s207.py (not in any csim test) | GD/QA | No. |
| sight vs fire LOS | test_PP_move_cover.py:79 (8 disc scenes, includes endpoint-inside exemption; asserts `fire == see`), test_PP_move_route.py:294, test_E01_R001_07_walking_kind.py:188 (100 seeded sampled pairs, ground terrain) | SCEN/property-ish | Closest to a property test, but for discs and terrain height. The planar blocked-cell case with an endpoint inside the cell (fog.c:353-389 skips endpoint cells, tactical_move.c los_clear does not) has no test. |
| attack-move resume | test_E13_S096_attack_move_resumes.py (lone, group, "integration whole scene ticked to wipe-out") | SCEN with end-state asserts | No: asserts end state, not path legality. |
| whole fights | test_E13_A99_tactical_equivalence.py, F1/F2/F3 goldens, PP_C_g3_hash_invariant, baseline_hashes | GOLD | Freeze output; illegal behaviour inside the hash is baked in. 5 of the A99 fight/idle cases and the G3 ones are already RED on HEAD and known-red-listed (TD-VG-E-26), so this layer is partly off. |
| live-run detectors | scripts/qa/rts_detectors.py (rubberband, stuck, backwards, dropped_order) | detector on planted traces | The only integration test on the real sim is `skipif(no om_tactical_trace_read)`; that symbol is not in the header (0 hits), so it never runs. No detector for in-cell, fire-while-moving, target flip. Not run on lab fights. |

Verdict per fault: unit ending a tick inside a blocked cell: no existing test (walker + box + fight absent). Firing unit drifting: no existing test (`halted` is observed only through hp falling). Target flip across a box: no existing test (the only multi-tick target tests use static targets).

Demonstration (scratch, `scratchpad/demo/test_demo_invariants.py`, ~60 lines, 6 v 6 Vanguards, one 100 x 800 wu box, attack-move through it, 1500 ticks):
- walkers: "no unit ends a tick inside the box" FAILS on HEAD, 2794 unit-ticks, first at tick 52. Fliers (default kind): passes.
- Run on mutant M1 (steer guard deleted) the same test fails for fliers too (10 unit-ticks) although test_PP_move_route.py stays green.
- "A unit in range that can shoot its target does not move" passes on HEAD in this layout (the L-0039 drift needs the oscillating target at a face, not reproduced by 6 v 6) and fails on M3 (2083 / 7243 unit-ticks).

## 3. How the tests were written

- Rule text or Python behaviour? The movement/targeting work was a **parity port**: acceptance was "same decisions as `simulation/` Python" (parity requirements, section 1 quote), and many tests are the Python's scenes (test_PP_move_parity_rules.py, tests/csim/parity/). Acceptance by fight hash (A99, F1-F3, G3, baseline_hashes) means the code's behaviour was the spec. Invariants from the bible were not turned into whole-run checks.
- Separate writer: yes (aa920cee etc. precede the builders), correctly red first, with positive controls. The weakness is what they were asked to test, not who wrote it.
- Tests changed to fit behaviour, Test-defect commits (163 in repo; movement-relevant):
  - **24c0dc57 (A172)**: in test_PP_unit_blocked_target.py the per-tick loop `assert not (inside the wall)` over the run was deleted; replaced by `_advances_then_fires` plus a *final-position-only* wall check (line 135). "Invented detector bounds replaced" because the unit walked 52-67 wu while blocked. An INV became a SCEN.
  - bfa7fd25 / A163-A164: 1 step becomes 4 steps in first-acquisition tests (cohort phase); 24c0dc57 also sets `OM_TP_ROUTE_ACROSS_LAYERS` 0 in the route fixture to fit the builder.
  - H-057 (fb7be351 and 658a327e, 79dc2c6a, 7ed21f55, 447b349d, 417b67a0, 25145230, 085f634c, 5cee9e8e): ~15 rule tests re-pinned or retired because the rule text changed (legitimate), but also 085f634c "the old scene's Raider now engages before the wall is reached": the blocked-cell scene was changed so it no longer meets the wall.
  - Goldens re-recorded "contact verified before first divergence": a06fe1e3, 9d5c40e4, 2fca4791, 6e79746d, e98b5029, d38ffd0d, 5d05fc89, 34078b62, c11f7120. The check is "something diverged where expected", not "the new run is legal".
- Liveness over safety: S-087 tests assert `hp fell`, `acquired <= 200 ticks`, `distance closed`; none asserts nothing illegal happened between.
- Scene hygiene: engage-on-sight tests run **sight off, no terrain** (test header); lab runs sight on with boxes. The tested configuration is not the shipped one. Targets in blocked-target tests are Supply (never fire back).
- `RED now` / `Red today` strings left in docstrings: 13 `RED now`, 154 `Red today/red today` in tests/csim; they describe the state at authoring and are now false claims (stale-doc), none is a live skip.
- skip/xfail: 20 files; none on movement/targeting rules (E05/E10/E02 Q-open, scale tier, net). Known-red lists (gd_tests_known_red.txt, lane_plays_known_red.txt) contain no movement rule test except the golden hash group (TD-VG-E-26), S-085 fight length (R-085-02, R-085-04) and F2 distance-test budget.
- **Positive controls for E-13 are placeholders**: 92 of 130 files in tests/csim/controls are generated skeletons that fail with `AttributeError`/`NotImplementedError`; 8 of 9 E-13 controls (stationary rule ignored, plain move returns fire, leash from target, ...) are among them, tolerated by `docs/northstar/spec_factory/placeholder_controls.txt`. Only `navmesh_cell_size_wrong_constant` is filled. `make test` is red by design. Only `OM_BUG_NAVMESH_CELL_SIZE_WRONG_CONSTANT` is wired in tactical_move.c (line 3039).

## 4. Mutation check (HEAD copies, 7 mutations, same 137-file selection, baseline 12 reds)

| # | Mutation | New reds (rule/behaviour tests) | New reds (hash/golden) | Verdict |
|---|---|---|---|---|
| M1 | delete the terrain guard call at the steer step (tactical_move.c:2233) | 1: PP_C_g4_routing `a_unit_goes_around...` | 5 (A99) | Killed by one incidental test. test_PP_move_route "never enters a blocked cell" stays GREEN. |
| M2 | delete `om_move_leave_blocked` call (R-207-06 eject, :2412) | 6: PP_move_route R-097-09, PP_collision_radius_runtime x3, VG_D_d7 control, VG_W_w2 N2 | 2 | Killed by scenario tests. |
| M3 | `om_tac_hold` never sets `halted` (units never halt to fire) | 8: PP_unit_blocked_target controls, PP_unit_pursuit R-087-04, PP_leash_own_distance x4, PP_attack_move_no_sight_pursuit | 26 | Killed; the halt/fire tests do work on the happy path. |
| M4 | nearest becomes farthest | 10: PP_unit_target_policy x3, E13_S096 x2, PP_unit_attack_move_group, PP_unit_first_shot, S081, S085, parity cohort | 42 | Killed (R-087-03 scenarios work). |
| M5 | stationary-push exemption removed (R-097-10) | 6: collision tests x4, E13_S097 R-097-03/-10, PP_unit_giveup | 32 | Killed. |
| M6 | held target re-acquired every cohort turn (kept-target dropped; the flip-flop shape) | **0** | 18 (A99, F1-F3, G3) | **Only whole-run hashes catch it; no rule test.** R-087-03 "engaged target still in range is kept" is protected by nothing but goldens. |
| M7 | fire LOS ignores blocked cells/cover (shot through boxes) | 9: PP_move_cover x3, PP_move_route R-098-02, S098, PP_unit_blocked_target x4 | 3 | Killed. |

Reading: scenario tests are decent at *the specific behaviour the story named*. They are blind to (a) interaction faults in the real configuration (walkers x boxes x sight on x many units), (b) any behaviour guarded by redundancy in the test scenes (M1), and (c) kept-target stability (M6). Goldens are the only whole-run net, and goldens detect change, not illegality.

## 5. Rule-pin machinery

`scripts/specfactory/rule_pins_tests.py` + `spec_provenance.rule_pin` (line 73-75): pin = first 6 hex of sha256 of the rule line text after `- R-id`. A test file with `Rule pins: R-087-04@74cc9c` is "current" while the rule text hash matches. The check:
- counts any `R-###-##` token in the file as "the test covers this rule" (docstring mention suffices), then requires a matching pin;
- fails (REJECT) only for files named in the diff; elsewhere a WARN count; the sidecar `rule_pins.toml` is empty (0 rows);
- 176 of 589 test files that mention an R-id carry a pins line. test_PP_move_route.py, test_PP_unit_blocked_target-style older files have none.
It proves **the rule text has not changed since the test was last touched** (staleness tripwire). It proves nothing about behaviour, and mentioning a rule is not covering it. Related but different: pre_gate.sh "pins" step (lines 128-155) runs the golden-value files (`PINNED_FULL|GOLDEN_|save_sha256`) on any csrc change, i.e. the hash layer. Evidence of drift: test_PP_move_route.py cites R-097-09 for "unit found inside a blocked cell moved out"; the bible now numbers that R-207-06 and gives R-097-09 to density repulsion, so the test's claim points at the wrong rule and no pin catches it (no pins line).

## 6. Coverage matrix (rule ids named in tests/**; loop = a test naming the rule has an assert inside a loop; heuristic, script scratchpad/cov.py, output scratchpad/cov_out.txt)

- E-13 (53 rules): no test names R-100-04, R-101-03, R-207-01, -02, -03, -04, R-208-01..03, R-209-01..02 (11). R-207-06 and R-207-07 are named only in a .gd test and a QA play, no csim. Scenario-only (no assert-in-loop): R-095-02..07, R-096-04/-06/-08, R-097-02/-03/-05/-07/-08/-09, R-098-01/-02, R-099-01/-02/-04, R-100-01/-03, R-101-02, R-102-02, R-207-05, R-207-06/-07. Have a loop: R-095-01, R-096-01/-02/-03/-05/-07, R-097-01/-04/-06/-10, R-099-03/-05, R-100-02, R-101-01, R-102-01.
- E-11 S-084/S-087 (R-084-01..07, R-087-01..09): R-087-09 (drop blocked-line target, steer to clear line) has **no test and no code**. Scenario-only: R-084-02/-03/-05/-06/-07, R-087-01, -03, -06, -07. Loop: R-084-01/-04, R-087-02/-04/-05/-08. Whole epic: 16 rules with no test (R-082-07/-08/-10, R-083-04, R-087-09, R-201-02, R-202-01..04, R-203-01/-02, R-204-01..04).
- E-07 (28 rules): all named, all scenario-only (lifecycle, not movement).
- E-17 (122 rules): 65 rules not named by any test; many are covered by `test_E17_S1xx` files that cite story ids, so this overstates the gap; R-186 to R-189, R-194 to R-197 are listed uncovered by id.
No whole-run invariant test exists for: unit never in blocked cell during a fight, firing unit stays put, kept target stability, sight/fire agreement over a run, stationary unit position unchanged across a fight.

## 7. Root causes, ranked

Structural:
1. No whole-run invariant harness. The bible lists invariants (E-13 lines 211-217) but they were turned into per-story scenarios; the one per-tick check that existed (A172) was removed by a Test-defect. The RTS detectors are unit-tested on planted traces and never run on a real fight; their only integration test is permanently skipped (API not in the header).
2. Parity-port acceptance: "same as the Python" plus fight golden hashes made the code the oracle. Goldens catch change not illegality, were re-recorded after every behaviour change ("contact verified before first divergence"), and several are red on HEAD and known-red.
3. Scenes are minimal and friendly: 1 to 3 units, a static or never-firing target (Supply), sight off, no terrain or one wall in a straight corridor, one tick or a short run. The shipped configuration (walkers, boxes, sight on, 24 units, both sides firing, targets pressed against faces) is never tested. Cascade leaves own one function and one story, so interactions (A171 walk-when-blocked x a target that steps in/out of a cell x walker step without guard) belong to nobody.
4. Positive controls are placeholders (92 of 130; 8 of 9 for E-13), so "does this test go red against wrong code" was never established for the movement rules. Whether the manager-mode saboteur phase (Phase 3.5, 'tests go red against wrong code') ran for the B12/PP work is not recorded in the repo (unverified); the movement rules have no kept saboteur artefacts.
5. Rules and pins are mention-based: pin staleness check is not coverage; renumbering (R-097-09 to R-207-06) left tests citing the wrong rule.
Incidental:
6. Redundancy in test scenes hides dead guards (M1).
7. A171's own design (walk when `can_shoot` is 0) is a rule decision whose failure mode (drift when the target oscillates) was not tested.
8. Stale "Red today / RED now" docstrings; rule R-087-09 ruled but never built or tested.

## 8. Recommendations (10 lines)

1. Add a lab-run invariant checker over the existing fight files/trace (every tick, every unit): in-blocked-cell, firing-and-moving (in range, can_shoot, target held, displacement > eps), target change count per unit per 100 ticks, sight/fire disagreement, stationary-pushed. Run it in `scripts/skilllab` after every fight and fail the run loudly; thresholds are Westley's.
2. Put the same checks in tests/csim as one fixture `assert_run_invariants(world, ticks)` applied to every scene helper, so every existing scenario test also asserts "nothing illegal on any tick" for free.
3. Property tests over seeded random layouts (N boxes, 8-256 per side, both unit kinds, walkers on/off, sight on/off), 1,500 ticks, invariants as in 1; the test_E01_R001_07 100-pair test is the template.
4. Make the shipped configuration the default test world (sight on, walkers, boxes); keep sight-off scenes as controls.
5. Fill the placeholder positive controls for E-13/E-11 (inject M1..M7-style faults via OM_BUG) and make an unfilled control a gate failure; adopt the mutation list above as a nightly job on `libouroboros_dbg.so`.
6. Forbid weakening a per-tick assertion in a Test-defect commit without the Architect naming the replacement invariant (24c0dc57 pattern).
7. Golden hashes stay as change detectors only; require a "legality" run on the new golden run before a re-record.
8. Run `rts_detectors` (extended) against the real sim in the nightly sweep; delete the permanently skipped integration test or give it the missing API.
9. Write each epic's Invariants section as the first failing whole-run test of the epic, before story scenarios.
10. Fix the cause list from the prior report (walker guard, endpoint-cell sight/fire, R-087-09) only after items 1-2 are red on main, so the fix is judged by the invariant.
