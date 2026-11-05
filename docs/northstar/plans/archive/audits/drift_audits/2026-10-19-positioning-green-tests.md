# Green tests on the positioning defects (read-only investigation, 2026-10-19)

Refs: origin/main 5c8fcc86 (audit read 86510b1f; no csrc change affects it), lab branch origin/push/labrev2-lab c2d9bce8.
Worktrees (detached, clean apart from build outputs, nothing pushed, for a clerk to remove): ~/Projects/om-push/wt/greentests (main), ~/Projects/om-push/wt/greentests-lab (lab).

Classes: (i) pins the defective behaviour as correct (breaks when the defect is fixed); (ii) covers the feature but lets the defect pass (isolation only, never a game path, or a default that is the defect); (iii) the test that should exist and does not.

## Method and baseline

- Ran `pytest tests/csim/test_*.py` on main (305 files; tests/csim/scale and tests/csim/controls NOT run): 32 failed, rest pass or skip. None of the 32 is a reach, emission, stealth, elevation, arc, cone or R-087-09 test. The ones tied to the defects are the choke generator reds (see D5c): E17 S113 R_113_01..05, S114 R_114_01..04, S115, S117.
- EXPERIMENT A (scratch copy in the scratchpad, repo untouched): made `om_unit_profile_reach` return the bible/lab table (Raider 1/1, Interceptor 2/1, Bombard 0/2, Bastion 0/2, Vanguard and Warden 0/0) for any type not explicitly set, then reran the same csim files. This is an upper bound on "tests that assume reach 0": exactly 12 tests go red (listed in D1). A fix that sets reach only inside `mission_start` would not break the bare-world ones; the mission-world ones are the ones to watch.
- `git grep -E "skip|xfail|known.red"` on the named files: tests/csim/conftest.py hits are only "skip when the .so is unbuilt" (lines 7, 37, 272, 282) and two docstrings (816, 1080, 1223 are the word "skip" in prose); gd_tests_known_red.txt lists test_time_jump_replay.gd and test_vg_e_e1p.gd; lane_plays_known_red.txt lists s132, s218, S-143, S-241; playthrough_known_red.txt is empty. NO entry relates to any of the seven defects. The gate compares failing-id sets against a baseline (merge_gate.sh:199), so the S113/S114 choke reds are tolerated by baseline, not by any named entry.
- Gate-level finding (class ii, not a test): `reach_lint` (scripts/specfactory/reach_lint.py) lists `om_unit_set_stealth`, `om_unit_spawn_with_elevation`, `om_unit_set_elevation_tier`, `om_map_compute_chokepoint_width` as UNREACHABLE (baseline, regression mode only), but does NOT list `om_roster_set_reach`, because unit.c:2488 (`om_tactical_reset` re-applies kept reach) makes it "reachable". So the wired-not-just-tested check passes for reach with no game path that ever supplies a non-zero value. `om_command_set_emission` is allowlisted (reach_allowlist.toml:79-81, "pipe handler not wired yet").

## D1. Reach by unit type is never set by any game path

Where stored: csrc/tactical_move.c:325-329 (`reach_n`, `reach_up`, `reach_down` in `om_move_state`); set by `om_roster_set_reach` (tactical_move.c:3305); read by `om_unit_profile_reach` (:3382), used at unit.c:575 (`om_tac_in_reach`), :1737, :2474. Callers of set: unit.c:2488 (reset re-apply only), the lab (engine.py:184), tests. The pipe sets movement kinds (om_pipe.c:1308, from `mission_start.movement_kinds`, autoload/era_config.gd:42) but has no reach counterpart.

| Test | file:line | Asserts | Class | Required rewrite |
|---|---|---|---|---|
| built_in_default_reach_is_zero_up_zero_down[6 types] | tests/csim/test_PP_C_g5_reach_api.py:26 | `read_reach(w, utype) == (0,0,0)` for Raider, Interceptor, Vanguard, Warden, Bombard, Bastion in a bare world | (i) (red under Exp A for 4 of 6: Raider, Interceptor, Bombard, Bastion) | Split: bare world with no mission keeps (0,0); a world after the game's own start path reads the bible table (R-164-01: Line own layer, Raider 1 either way, Interceptor 2 up 1 down, Siege 2 down). Ledger: test-defect assumption-changed on the existing assertion plus a new test for the started world. |
| reach_belongs_to_the_world_it_was_set_in | same file:93 | world B Raider reads (0,0,0) | (i) (red under Exp A) | Same split: B is a bare world; keep the isolation claim but set the "other world" explicitly, not by default. assumption-changed. |
| no_reach_set_means_todays_same_layer_rule_unchanged | tests/csim/test_PP_C_g5_direct_fire.py:87,94,95 | Vanguard (0,0) default; same-layer enemy hit, enemies on layers 0,1,3,4 untouched | (ii) (green under Exp A only because Vanguard is the one type whose table value is 0/0) | Add the same scene with a Raider as the attacker, run through the game's start path: the layer 1 and 3 enemies ARE hit. New test (below). |
| splash_hits_only_the_offsets_the_bombards_reach_includes[reach0] | tests/csim/test_PP_C_g5_area_return_fire.py:83 (read default), :44 (helper skips set_reach when (0,0)), param at :76 | Bombard default (0,0,0); splash only same layer | (i) (red under Exp A) | Helper must set (0,0) explicitly when it means "no reach". assumption-changed. |
| `duel` helper | tests/csim/test_PP_C_g5_support.py:155-156 | calls set_reach only when reach != (0,0), so every "reach 0" case relies on the default | (ii) helper | Same: set explicitly. Prevents the whole g5 family hiding the default. |
| R-004-02 transition timing (3 tests) | tests/csim/test_PP_C_g4_transfer.py:114 (docstring "reach is 0 by default"), :141, :162-163 | Raiders 100 wu apart on layers 2/3: `held["N"]` never targets T before halfway; `held["O"][11:]` never targets T after | (i) (3 tests red under Exp A: old_layer_may_attack_until_halfway, the_transitioning_unit_attacks_as_a_unit_of..., control_a_unit_that_never_transitions...) | The scene tests transition timing, not reach: set Raider reach (0,0) explicitly in `_acquire_scene`. assumption-changed. |
| G3 A99 recorded hashes | tests/csim/test_PP_C_g3_hash_invariant.py:66 | per-step state hash of the three recorded fights equals the frozen reference | (i) (3 red under Exp A: fight_990_gap300, gap1500, gap3000) | Reference hashes encode "same-layer fire only"; if the table changes the default they re-record (ledger, TD-style re-record) or the scene pins reach (0,0) explicitly. Note test_E13_A99_tactical_equivalence.py already fails 3 on main (baseline). |
| E11 S081 spotter scene | tests/csim/test_E11_S081_three_categories_a_soft_triangle.py:95 (comment "Vanguards' reach 0 cannot touch it") | Siege wins with >=30% hp; Raider spotter one layer above | (ii) not red under Exp A | None needed; mention only. |
| lab reach readbacks | tests/skilllab/integration/test_reach_real.py:30 ("vanguard": (0,0)), :48 (custom type without key reads (0,0)); tests/skilllab/test_reach_binding.py (fake engine) | built-in unchanged, custom default (0,0) | (ii): proves only that the LAB path sets reach (engine.py:184); (i) for :48 if the library default moves | assumption-changed only if the default moves into the library. |
| movement kinds (the sibling that IS wired) | tests/specfactory/test_pack_validate_movement.py:206-225, tests/transport/test_pipe_mission_start_ground.py, tests/test_era_toggle.gd | pipe parses `movement_kinds`, applies before `om_set_era_kind` | context | There is no reach equivalent anywhere. |
| NO TEST: reach through a game path | none (grep "reach" in tests/transport, tests/*.gd, tests/qa: no reach test; no S-164 story play in tests/qa/desktop/plays) | | (iii) | See New test N1. |

New test N1 (RED today, green when fixed), through pipe `mission_start` then `mission_begin` then `tactical_step` (a pipe handler, plus the tick), using the shipped space era:
- put one player Raider on layer L+1 and an enemy Vanguard group on layer L within Raider range and sight (via `command set_layer` and `attack_move` as the player would), step N ticks, read the tactical frame hp of the enemy: assert the enemy loses hp while attacker.layer != target.layer. Today it loses none (reach 0,0).
- positive controls (green today): same scene with a Vanguard attacker on the other layer: no hp loss (Line reach 0); same scene on the same layer: hp loss.
- one case per bible row: Raider +1 and -1 fire, +2 does not; Interceptor +2 and -1 fire, +1 down... -2 does not; Bombard -2 fires, +1 does not.
- A second csim variant through `om_mission_start` (no pipe) is acceptable, but the pipe variant is the one that proves the wiring.
Ledger class: new test (N1) plus test-defect assumption-changed on the six rewrites above.

## D2. Emitting (S-163) only on the multiplayer stream; multipliers default 1.0

Where: `om_command_set_emission` (fog.c:856), reached only from cmd_stream.c:252 (verb `OM_NET_VERB_SET_EMISSION`=5, ouroboros_sim.h:293). The pipe `command` handler (om_pipe.c:1567-1608) has verbs move, attack_move, attack_target, activate_ability, set_layer, ping, place, hold: no emission. Multipliers `OM_TP_EMIT_SIGHT_MULT` and `OM_TP_EMIT_SEEN_MULT` default 1.0 (tactical_move.c OM_PP_MULT(1.0) pair, pp_contract.md:115-116). Client: autoload/c_bridge.gd and scenes have no emission command (grep).

| Test | file:line | Asserts | Class | Required rewrite |
|---|---|---|---|---|
| default_multipliers_make_emitting_a_no_op | tests/csim/test_PP_C_g67_emission.py:175-181 | emitting at defaults (both multipliers 1.0) leaves an enemy on layer 3, 600 wu away, unseen | (i) | Replace with: at defaults (no `set_param`), an emitting unit is seen from further than a silent one, and the seen multiplier is above the sight multiplier (R-163-01 "by more than"). The numbers are Westley's; the test asserts the inequality and that default > 1.0, and pins the lab start 2.0/3.0 only as a named DRAFT. assumption-changed; Westley sign-off for the number. |
| every G1 default, rows 21 and 22 | tests/csim/test_PP_settings.py:104 (`test_G1_every_parameter_defaults_to_its_documented_value`, parametrised from pp_contract.md:115-116) | `OM_TP_EMIT_SIGHT_MULT`/`EMIT_SEEN_MULT` default == 1.0 | (i), reads the doc table | The doc row and the engine row change together (pp_contract.md + tactical_move.c row); the test follows the doc. assumption-changed. |
| the other 20 emission tests | tests/csim/test_PP_C_g67_emission.py:55-300 (`set_param(...,2.0)` at :131,:142,:152,:193,:194,:204,:221,:234,:256,:257,:270,:290,:291; `set_emission` direct) | emission mode readback, sight arithmetic at hand-set multipliers | (ii): C function called directly with hand-set multipliers, so the unset-default and the missing command are invisible | Keep as isolation; add N2. |
| lockstep verb | none: grep SET_EMISSION/NET_VERB in tests finds only the enum; tests/net/* send verb 1 only (tests/net/test_lockstep_equal.py:30, test_single_peer_equiv.py:25) | | (iii) | New test N3 below (the existing multiplayer path is also untested). |
| pipe verb | none (tests/transport/test_pipe_vg_contract.py:214 covers set_layer only) | | (iii) | N2. |
| client command | none (tests/test_c_bridge_vg.gd:142 covers set_layer only) | | (iii) | N2b (GDScript, only once the client sends it). |
| story play | none for S-163 in tests/qa/desktop/plays | | (iii) | After N2, per CLAUDE.md "Stories acted out". |

New tests, RED today:
- N2 (pipe): start a space mission, send the player command that turns a unit group to emitting through `command` (verb name is the spec's to fix), assert `ack` (today: `error` unknown verb), then `tactical_step` N and assert the enemy side sees the emitting unit from a distance where a silent one is unseen, using what the frame already exposes (enemy rows present in the player's frame, or the enemy-facing `sees` readout); positive control: silent twin at the same distance is not seen. Also: switching back to silent restores unseen (R-163-03) and costs no resource.
- N3 (lockstep): `net_submit` verb 5 with `arg=1` from tests/net/driver.py, same observable; byte-identical to N2's pipe result on the same seed (single-peer equivalence like test_single_peer_equiv.py).
- N2c: at engine defaults (no set_param), emitting must change visibility (replacement for :175).
Ledger: new tests; assumption-changed for :175 and the G1 rows.

## D3. Stealth never enabled outside tests

Where: flag `stealth` (unit.c:260), honoured at unit.c:1166, 1748, 1780, 1801, 1860, 1878, 1995, 2104, 2105, 2143; set only by `om_unit_set_stealth` (unit.c:2970), zero callers outside tests. IMPORTANT: no bible rule names "stealth" (grep -i stealth over docs/bible and the register: no hits; only R-163-02 silent and R-120-02 enemy ambush). There is nothing to assert against yet.

| Test | file:line | Asserts | Class | Required rewrite |
|---|---|---|---|---|
| stealthed enemy not acquired | tests/csim/test_PP_unit_pursuit.py:184-196 | stealthed enemy in range not acquired, un-stealthed is | (ii) (direct setter; tests the gate not the source) | none to fix; keep |
| unseen attacker flinch | tests/csim/test_E11_S087_every_unit_thinks_the_same_way.py:31,49 | `om_unit_set_stealth(attacker,1)` used as "unseen", victim flinches 200 wu | (ii), uses the flag as a fixture for "unseen" | If a rule later makes stealth come from play, the fixture should use that source. |
| nearest-hostile fixture | tests/csim/test_F2_nearest_hostile_search.py:136-142, 219-251, 301 | stealthy rows excluded as candidates | (ii) | none |
| reach gate | scripts reach_lint: `om_unit_set_stealth` UNREACHABLE (baseline) | | (ii) | none |
| NO TEST: any game path enabling stealth | none | | (iii), BLOCKED | A rule (new `Q-` row with candidates) must say who gets stealth and how (going dark R-163-02 silent? an ability? era pack?). Until then no honest test can be written; a test of "stealth set by X" would invent X. |

Required (once ruled): a pipe-driven test in which the ruled trigger is used by the player (or the enemy macro) and the affected unit stops being acquired by the other side, positive control: same scene without the trigger acquires it. The audit's row 5 merges "stealth" and "emission silent"; the bible only has the second.

## D4. Space elevation sight bonus needs a tier no in-game spawn sets

Where: `elevation_tier` per unit in fog.c:146 (a tracked list, cap 512 `OM_FOG_MAX_TRACKED_UNITS`); written only by `om_unit_spawn_with_elevation` (fog.c:800); `om_unit_set_elevation_tier` (unit.c:2952) is a STUB (`/* STUB */ (void)...`). Read at fog.c:398, 413-414, 462-466, 777. Bonus `1 + 0.15 d` (om_constants.h:562) applies in space only (fog.c:462 skips when `era_kind==1`); fog.c:451 notes the era flag "elevation_sensor_bonus" is stored but not consulted. Open flag Q-091-01 (E-12) on how tiers relate to the five layers: the epic with an open flag is not built.

| Test | file:line | Asserts | Class | Required rewrite |
|---|---|---|---|---|
| R-091-02 effective radius | tests/csim/test_E12_S091_standing_high.py:52-79 | `spawn_with_elevation(...,3)` observer, target tier 1: radius 910.0; 909/910 seen, 911 not | (ii): direct spawn call; passes with the era flag unset too, so "when the era enables" is untested; docstring says "nothing in code reads this", stale | Keep as isolation; add N4. Fix the flag claim separately. |
| R-091-03 sensors only | same file:82-105 | damage flat 9.0, radius gets the bonus | (ii) | none |
| flat damage | tests/csim/test_E11_S084_flat_damage.py:144-160 (setter at :153, :156) | calls the STUB `om_unit_set_elevation_tier`, asserts dmg == 9.0 | (ii) vacuous: passes for any tier because the setter stores nothing | Replace the setter with `spawn_with_elevation` (the working path) so the test could fail. assumption-changed. |
| table binds 512 | tests/csim/scale/test_PP_tables.py:489-511 | 512 elevated units each read their bonus; docstring "no game path calls today" | (ii) | none (scale dir not run here) |
| ground era skips bonus | tests/csim/test_E01_R005_09_high_ground_sees_down.py:122-137 | ground era: elevation bonus does nothing | consistent with R-091-02 retirement; keep | none |
| NO TEST: a mission-spawned unit has a tier | none | | (iii) BLOCKED on Q-091-01 | N4 below. |

New test N4 (RED today): after the game's own mission start (pipe `mission_start` + `mission_begin`, space era), a unit the player controls on higher ground/elevation tier than a target sees it from `sensor * (1 + 0.15 d)` where today every in-game unit has tier 0 so the radius equals the plain sensor radius. Observable: enemy rows present in the player's frame at a distance between plain and elevated radius; positive control: same distance with equal tiers is unseen. Needs the ruling on where tiers come from (Q-091-01) before the scene can be built.

## D5. Promised, not built: arc, cone, choke generator, R-087-09

On main there is no test asserting the stub behaviour for arc or cone (class i: none found). Arc/cone tests exist ONLY on unlanded branches.

a) Firing arc (R-100-04 DRAFT, Q-100-01)
| Test | file:line | Asserts | Class | Required |
|---|---|---|---|---|
| facing tests | tests/csim/test_E13_S100_facing.py:24-56, 59-92, 95-116 | R-100-01..03 face target, turn caps, retreat faces pursuer | compatible (not a pin of 360 fire) | none |
| arc tests | origin/push/labrev2-e2-tests: tests/csim/test_E13_S100_firing_arc.py (e.g. :209 flanked_unit_turns_then_fires_on_the_derived_tick, :189 control arc 360 fires on the acquisition tick), test_PP_can_engage.py, tests/specfactory/test_pp_contract_lab_rev2.py on labrev2-e0-tests | arc gate in the fire pass at arc 90..270 (csim tick, no pipe) | (iii) on main: not landed; tick-level only | Landing them is the rewrite. Gap: they set the arc by `set_param`; no test that a pipe-started mission fires with the ruled arc (E0 spec default is 360 = no arc, so a built E2 would still do nothing in the game). N5 below. |
| lab skip of the arc family | tests/skilllab/test_sweep.py:290-296 and :1001-1005 (fake world, library lacks param -> skipped with reason); tests/skilllab/integration/test_sweep_real.py:171-175 asserts the skip on the real library, :139 and :152 `pytest.skip` the null controls; tests/skilllab/test_charts.py:425,436, test_report.py:1051 | the arc family is skipped with "LAB-REV2-E0 not built" | (i)-lite, self-retiring: :171-175 and :178-182 skip themselves once the library has the symbol; the fake-world ones stay green by design | none beyond landing E0/E2 |
N5 (RED today, tick plus pipe): through pipe `mission_start`/`tactical_step`, a unit facing away from an in-range enemy does not fire until it has turned (shot tick = acquisition + turn steps), using the ruled `FIRING_ARC_DEG`; today it fires on the acquisition tick. Control: arc 360 fires on the acquisition tick.

b) Cone (R-082-10 ruled shape, Q-082-06): same shape. Branch tests: origin/push/labrev2-e2-tests tests/csim/test_E11_S082_cone.py. No game-path setter for cone exists (like reach: `om_roster_set_cone` would be called by lab/tests only); main has none of the symbols (`om_roster_set_cone` absent). N6: through pipe, a unit type with the ruled cone hits every enemy inside the sector once, not outside; control: Bombard disc on the same geometry (green today).

c) Choke generator (tactical_mapgen.c:418 `om_map_compute_chokepoint_width` returns 0; :579 `om_map_has_flank_bypass` returns 0)
| Test | file:line | Asserts | Class | Required |
|---|---|---|---|---|
| R-113-03 flank route | tests/csim/test_E17_S113_nine_kinds_of_place.py:75-76 | every chokepoint node has `om_map_has_flank_bypass == 1` (guarded by `choke_count > 0`) | correct, RED today (spine generator returns 0 nodes, test_R_113_01 asserts `10 <= node_count <= 30` fails at :33) | none; keep red, not in any known-red list |
| R-113-05 width | same file:106-111 | `om_map_compute_chokepoint_width(1.5) == 300`, `(0.8) == 160` | correct, RED today | none |
| S114 R_114_03 obstacle density anchors at chokepoints | tests/csim/test_E17_S114_texture_from_gradients.py (R_114_03) | red today | correct, RED | none |
| class (i): none found | grep of tests for the two symbols: only S113 and conftest bindings | | | |
| N7 gap (iii): the played map | none runs a generated game map through the pipe and checks a choke exists with the ruled width (R-192-02/04) | | | pipe `mission_start` on a choke layout; read the terrain frame/`terrain` verb; assert a choke of width w x 200 wu with a flank bypass. Lab layouts (maps.py choke_width_bodies) are lab-made, so tests/skilllab layout tests are (ii) for this defect. |

d) R-087-09 (steer to a clear line; give up after 20 ticks and re-acquire)
| Test | file:line | Asserts | Class | Required |
|---|---|---|---|---|
| A171 blocked target (4 tests) | tests/csim/test_PP_unit_blocked_target.py:96-105, 107-122, 124-136, 138-148 (helper `_advances_then_fires` :71-93) | attack-moving unit with a blocked held target keeps walking its ROUTE (moves >= 75 wu in 20 ticks or advances 5 consecutive ticks) and fires once the line clears | (ii): labelled R-087-05/A171, not R-087-09; satisfied by route-walking, says nothing about steering to a clear line, the 20-tick give-up, or re-acquiring another target | Keep; add N8. |
| guard stays put, idle blocked | stated in docstring :1-26 ("Guard half ... not tested here"); no idle case | | (iii) | N8 idle case. |
| naming hazard | tests/csim/test_PP_unit_giveup.py is R-099-05 (formation slot give-up at 75 wu), not R-087-09; no test file names R-087-09 | | (iii) | |
N8 (RED today): idle or attack-moving unit, target in range, line blocked by a wall with no gap reachable within 20 ticks, a second visible enemy with a clear line: assert the unit drops the first target and targets the second no later than tick 20 after the block; control: a gap reachable in <20 ticks, unit steers to it and fires at the first target. Via `tactical_step` (pipe or csim tick).

## D6. Lab: s3_dark_striker is a no-op (lab branch c2d9bce8)

Play: scripts/skilllab/plays_space.py:145-148 sets `Step.set_emission(0, False)` and `(1, False)` (both silent, already the default); description at :218-219 says the enemy keeps emitting.

| Test | file:line | Asserts | Class | Required rewrite |
|---|---|---|---|---|
| dark striker steps | tests/skilllab/test_plays_space.py:366-371 | every side-0 group has set_emission on=False at tick 0; no side-1 group has on=False | (i): pins the silent-only timeline; nothing requires any `on=True`, docstring says "naive emitting" | Add: side 1 has set_emission on=True at tick 0 (the description), or the description is changed by ruling. assumption-changed. |
| placed keeps its steps | tests/skilllab/test_scenes_mix.py:137-142 | placed play's timeline equals the play's own and touches side 0 only | (i): asserts "silence only side 0" | assumption-changed with the same ruling. |
| emitting family points | tests/skilllab/test_sweep.py:134-146 (points), :854-863 (rows carry vision/sight), :872-875 (saturated at 0.5) | six grid points; rows exist for s3_dark_striker | (ii): fake World; cannot see that the fight is identical across points | N9. |
| emitting never refines | tests/skilllab/test_sweep.py:719-730 | no refinement with a hand-built gain | (ii) | none |
| family plumbing | test_charts.py:426,437; test_diagram.py:470; test_plays_space_scan.py:21-40; test_drift_fix_holder.py:46; test_placed_by_feature.py:58; integration/test_contact_real.py:210 | builds, roles, anchors, placement for the play | (ii) | none |
| the emission step itself (real) | tests/skilllab/integration/test_timeline_orders_real.py:150-165; test_bindings_real.py:136 | on a synthetic Interceptor/dummy scene `Step.set_emission(0,True)` makes the force seen at 600 | proves the machinery works; the PLAY never calls it with True | |
| NO TEST (iii) | none runs s3_dark_striker on the real engine and reads emission | | | N9. |

N9 (RED today, real engine, `integration/`): build `plays_space.PLAYS["s3_dark_striker"]`, run `fight()` N ticks past tick 0, read `om_unit_get_emission` per unit: every side-0 unit SILENT, every side-1 unit ACTIVE (RED: all silent). Positive control: the existing timeline test machinery. Second assertion: the same play at emitting points sight/seen (1.0,1.0) and (2.0,3.0) at vision 0.125 gives different fights (firing_window or outcome) (RED: audit measured byte-identical: side0, 1669 ticks, 14:0, 701.25:155.25). Ledger: new test plus the two assumption-changed rows.

## D7. Lab prediction only in the opening window

Source: contract.py:159 `OPENING_WINDOW_TICKS = 40`, fight.py:209-218 (`_window_seconds`, `_predict`), :371-374 (contact = first sample with an able unit).

Tests that pin the window as THE prediction (class i; they stay correct for a window prediction, none says "no other prediction"):
| Test | file:line | Asserts |
|---|---|---|
| window covers 40 ticks, excludes tick after | tests/skilllab/test_fight_outcomes.py:287-288 | firing_window == (6.0, 2.0) |
| half-open edge | :296-300 | window = [contact, contact+40) |
| predictions name the window total and ignore the later fight | :336-337 | count side0 although side1 leads after tick 50 |
| type from the window weighted total | :344-347 | predicted_type side0 against a whole-fight side1 |
| agreement table | :370-371 | agreement computed from the window predictions |
| constant | :219-221 | OPENING_WINDOW_TICKS == 40 |
| default basis | tests/skilllab/test_conditions.py:441 (`DEFAULT_BASIS == "window"`), :448-449, :556-560, :664-672 | C1 and C2 default to the window |
| report | tests/skilllab/test_report.py:1246-1260 | DRAFT-opening-window-ticks listed |
| real engine | tests/skilllab/integration/test_sweep_real.py:119-123 | damage_up 0.5 changes the result and NOT the window count (documents the blindness) |
Class (ii) real: nothing real asserts that the window prediction is right on a layer arrangement; layout 192 (play, reach_zero, naive_defender_attacker_layer) gives an identical window yet outcomes side0, cap, side1 (audit C item 3).
Class (iii): no test of any prediction made before contact or over the whole fight as a primary form; no test that a Setup alone can be scored.

Would break if a setup-time prediction were added (none of the window pins should): the window/prediction pins above are additive and stay green. They break ONLY if the setup score were added as a new CSV column or row key: tests/skilllab/test_rows.py:60 (`list(row) == ["play","enemy_heads"] + FIXED`, "nothing else"), tests/skilllab/test_reengage_rows.py:55, :73, :90 (exact header/key lists), and the three controls' golden row hashes (tests/skilllab/golden_hashes.json via integration/test_cross_machine.py). `FightResult` field additions are safe (test_fight_outcomes.py:198-203 is a subset check). So the setup prediction must be a separate function/field kept out of the fixed CSV row, or those four files get ledger assumption-changed rows.

N10 (RED today): a pure function (no engine tick) over a `Setup` returns a predicted side; on layout 192, 16 v 16, three setups: play (`s3_layer_above`), `reach_zero`, `naive_defender_attacker_layer`: assert the prediction for `naive_defender_attacker_layer` is NOT side0 (measured outcomes side1 x4; today's window prediction says side0 x4) and the three predictions are not all equal. RED today because no such function exists (and the window prediction is side0 for all three). Real-engine variant: `fight()` result for those three has `predicted_count` differing or a whole-fight prediction present (contact-independent). Ledger: new test (not a test-defect).

## Tests to rewrite first (landing order) with ledger class

1. D1: `test_PP_C_g5_support.py:155` (`duel`) and `test_PP_C_g5_area_return_fire.py:44` (`_splash`): set reach explicitly even when (0,0). Row: test-defect assumption-changed (no assertion changes; removes the default dependence so every later move is visible). 
2. D1: `test_PP_C_g4_transfer.py:114,141,162-163` (`_acquire_scene` sets Raider reach (0,0)). assumption-changed.
3. D1: `test_PP_C_g3_hash_invariant.py:66` and the A99 builders: pin reach (0,0) or re-record. assumption-changed (re-record needs a ledger row, Westley's hash policy).
4. D1: `test_PP_C_g5_reach_api.py:26,93` split bare-world vs started-world. assumption-changed + new N1 (pipe mission_start cross-layer fire). Order: N1 lands RED in the same piece as items 1-4 (tests first, red on the built tree).
5. D2: `test_PP_C_g67_emission.py:175-181` and `test_PP_settings.py:104` rows 21-22 (with pp_contract.md:115-116): assumption-changed, needs Westley's numbers (his threshold). New N2/N2c/N3 (pipe and lockstep emission command, defaults visible). 
6. D4: `test_E11_S084_flat_damage.py:153,156` switch to the working setter path (assumption-changed, makes it non-vacuous); new N4 after Q-091-01 closes.
7. D3: no test can be rewritten; first a `Q-` row for the stealth source (design), then a new test.
8. D6: `test_plays_space.py:366-371` and `test_scenes_mix.py:137-142` assumption-changed with the ruling on what the enemy does; new N9 (real engine emission readback plus emitting-point difference).
9. D7: new N10 (setup-only prediction, layout 192 triple); only if the setup prediction is a CSV column: assumption-changed on test_rows.py:60, test_reengage_rows.py:55/73/90, golden_hashes.json.
10. D5: land the existing arc/cone tests (origin/push/labrev2-e2-tests, labrev2-e0-tests) as the base; new N5 (arc through the pipe path), N6 (cone via pipe), N7 (choke on a played map), N8 (R-087-09 drop-and-reacquire, idle and attack-move); S113 R_113_03/05 and S114 R_114_03 are already correct and RED (no change; they close with the generator).
