# Requirement audit, slice 3: E-01 Layer System (rotating epic, whole)

Read tree origin/main 2845f88f7 (worktree ~/Projects/om-wt/rulings-1117, content identical). Card: docs/method/requirement_audit.md. 87 rules + 7 Invariants = 94 items. Line numbers are of docs/bible/epics/E-01-layer-system.md (E-01:n) at that sha. Not committed.

Row kinds: PROVEN 0, WEAK 1, MISSING 73 (Proof MISSING) + 20 (Proof unbuilt, marked `unbuilt`), STALE, BIBLE-CONFLICT as listed. A rule may have one proof row plus extra Half 1 rows.

## Half 2: the one named proof

```
WEAK | E-01 Invariant 4 (E-01:397-398) | tests/csim/test_E13_R207_06_never_enter_blocked.py::test_R_207_06_twelve_attack_moving_walkers_never_end_a_tick_in_a_blocked_cell | qualification 1 (also 4, 5, 3; see below)
```
Pointer resolves; test runs green on 2845f88f7 from ~/Projects/ouroboros-manifold: `1 passed in 0.10s` (existing build; pipe/ exists). Verified sha 53f6b053 exists; test file last changed in 8a5a76b91 (before it), so the `verified` sha is not stale for the file; csrc/tactical_move.c changed after it (F5 to F8 commits), re-run green.
1. FAILS. Names R-207-06 (E-13), not E-01 Invariant 4. Module docstring quotes E-13's Invariant "A unit never enters a blocked cell.", not E-01's "No unit ever occupies a position and layer the mask marks blocked." The test's own docstring quotes no rule text beyond "R-207-06: a blob of 12 walkers ...". E-13 R-207-06 as written today (E-13:207) is the ejection rule ("moved to the nearest open cell"), which the docstring calls a control.
2. Holds for what it checks: asserts no unit-tick ends inside a blocked cell (engine oracle om_navmesh_is_cell_blocked), not a hash. Only layer 0 is read (`_blocked(..., layer=0)` default) although the Invariant says "position and layer"; all 12 units stay on layer 0.
3. DIFFERS from shipped config. Test: walkers (om_roster_set_movement_kind, Raider and Vanguard), one box on layers 0-4, no terrain, no enemies (so sight never matters), default era kind (space, 0), default reach. Lab (scripts/skilllab/engine.py:152-153,144,117; DEC-stage4-sight-bundle-2026-11-05 decisions.md:287): ground era (set_era_kind 1), every role walks on a canvas with terrain, sight on, reach 0 up 1 down. Switches that differ: era kind, terrain_generate, sight (targeting by sight), reach. A separate test in the same file covers terrain (test_R_207_06_a_walker_on_a_terrain_world_does_not_walk_through_a_box) but is not the named proof. scripts/play.sh sets no sim switch (grep sight/era/walk/OM_ found none); the beta's switches come from the client, not read here.
4. FAILS. Invariant demands a whole-run test over every unit (fliers, walkers, all writers, all layers). Test checks each tick (good) but only 12 walking Raiders attack-moving at one face on layer 0; fliers, kiting, flinch, push into canvas edge, other layers are in sibling tests or in the lab checker, not this proof.
5. Recorded break only, no filled control. Docstring records the unfixed-tree run ("1271 unit-ticks inside in 400 ticks", 2026-11-08); the file's `control_` tests are for other tests. Not re-run (brief).
6. Holds: no skip, xfail or known-red marker in the file.
7. Holds: spawns, attack_move and step through the tick (tests/csim/test_PP_unit_support helpers, om_tick path), not an inner function.
Lab whole-run checker: scripts/skilllab/invariants.py carries R-207-06 (tests/skilllab/test_invariants.py:129 plants a violation and flags it). Its latest result on main was not located in this slice; not quoted.

## Header and foot of the epic (Half 1, not rule rows)

```
BIBLE-CONFLICT | E-01 header | E-01:7 and E-01:14 vs E-01:432-434 and docs/northstar/ambiguity_register.md | "15 stories, 82 rules" / the file holds 87 rules (7 invariants besides); "the 12 flags still open are listed at the foot" (E-01:10) / foot lists 8
BIBLE-CONFLICT | E-01 open flags | E-01:14, 213-224, 434 and docs/northstar/ambiguity_register.md:229,282,284,344,285 | E-01 lists Q-008-03, Q-008-05, Q-008-07, Q-189-02, Q-166-02 as open (and S-008 "blocked" on them); register: Q-008-03 closed, Q-008-05 closed, Q-008-07 closed, Q-189-02 closed (exact figure inside 30-35 still open until Westley's visual pass), Q-166-02 closed. Q-008-02, Q-008-06, Q-166-04 are open in the register, as E-01 says. docs/bible/stories.md:14 S-008 "blocked on Q-008-02, Q-008-03" likewise
STALE | E-01 header | E-01:14 and docs/northstar/ambiguity_register.md:227 | "S-009 on Q-009-02" blocked; Q-009-02 closed (vision tube, no mark), and R-009-06 says so
BIBLE-CONFLICT | E-01 references | E-01:11,262,410-412 and docs/northstar/ambiguity_register.md:67 (Q-E01-08) | "Reference required: references/E-01/notes.md, missing", "Stub"; Q-E01-08 closed, resolved by the options pass (E-01:247 says Godot renders fill the notes)
STALE          | S-002/S-003/S-162/S-163/S-164 open flags | E-01:77,102,298,315 | "Open flags: none" / R-002-08 cites open Q-003-02 and R-162-04, R-163-02/03, R-164-03 cite Q-162-06, Q-005-04 in brackets as open (both closed in the register, so the 'none' is right and the brackets are stale)
BIBLE-CONFLICT | Purpose | E-01:22 and docs/bible/epics/E-17-map-generation.md:497 | "The space landscape is not designed (Q-166-02), so this epic writes no landscape rules for it" / S-246 "Design decided 2026-10-07 and approved as written" (see R-010-01 row)
BIBLE-CONFLICT | Outputs table | E-01:383 and docs/bible/game_bible.md:167 | the Ping row names the setting OM_TP_PING_ALERT ("unless OM_TP_PING_ALERT is 1, default 0"); hub: rules never carry data shapes or settings names
```

## Rows

```
MISSING        | R-001-01 | csrc/tactical_move.c:3177 (om_navmesh_is_cell_blocked), csrc/tactical_mapgen.c:851 (om_map_block_rect); csrc/move_commit.c | E-01:35 Proof: MISSING
MISSING        | R-001-02 | csrc/tactical_move.c:3177 (om_navmesh_is_cell_blocked), csrc/tactical_mapgen.c:851 (om_map_block_rect) | E-01:37 Proof: MISSING
MISSING        | R-001-03 | csrc/tactical_move.c:3177 (om_navmesh_is_cell_blocked), csrc/tactical_mapgen.c:851 (om_map_block_rect) | E-01:39 Proof: MISSING
MISSING        | R-001-04 | csrc/tactical_move.c:3177 (om_navmesh_is_cell_blocked), csrc/tactical_mapgen.c:851 (om_map_block_rect) | E-01:41 Proof: MISSING
MISSING        | R-001-05 | csrc/tactical_move.c:2141-2160 (route across layers), csrc/walk_route.c:205 (om_walk_route) | E-01:43 Proof: MISSING
MISSING        | R-001-06 | csrc/terrain.c:1065-1070,1269 (om_terrain_slope_count/get/at), csrc/walk_route.c:205 | E-01:45 Proof: MISSING
MISSING        | R-001-07 | csrc/walk_route.c:205; csrc/tactical_move.c (om_roster_set_movement_kind); scenes/tactical_c/tactical_view.gd:805-815 (walker layer order refused) | E-01:47 Proof: MISSING
MISSING        | R-002-01 | csrc/tactical_move.c:3474 (om_command_set_layer), :200-204 and :361 (lay_state, OM_LAY_PENDING/FLIGHT) | E-01:58 Proof: MISSING
MISSING        | R-002-02 | csrc/tactical_move.c:3474 (om_command_set_layer), :200-204 and :361 (lay_state, OM_LAY_PENDING/FLIGHT) | E-01:60 Proof: MISSING
MISSING        | R-002-03 | csrc/tactical_move.c:3474 (om_command_set_layer), :200-204 and :361 (lay_state, OM_LAY_PENDING/FLIGHT) | E-01:62 Proof: MISSING
MISSING        | R-002-04 | csrc/tactical_move.c:3474 (om_command_set_layer), :200-204 and :361 (lay_state, OM_LAY_PENDING/FLIGHT) (spot transfer: no lay_spot in csrc) | E-01:64 Proof: MISSING
BIBLE-CONFLICT | R-002-04 | E-01:63 and docs/bible/game_bible.md:167 | rule carries the command name "`set_layer`"; hub: "Rules ... never carry file paths, function signatures, or data shapes" (conceptual-rule convention, Half 1 "named thing")
MISSING        | R-002-05 | csrc/tactical_move.c:3474 (om_command_set_layer), :200-204 and :361 (lay_state, OM_LAY_PENDING/FLIGHT) | E-01:67 Proof: MISSING
MISSING        | R-002-06 | csrc/tactical_move.c:3474 (om_command_set_layer), :200-204 and :361 (lay_state, OM_LAY_PENDING/FLIGHT); scenes/tactical_c/tactical_view.gd:812 | E-01:69 Proof: MISSING
MISSING        | R-002-07 | csrc/tactical_move.c:3474 (om_command_set_layer), :200-204 and :361 (lay_state, OM_LAY_PENDING/FLIGHT) | E-01:71 Proof: MISSING
MISSING        | R-002-08 | unbuilt: partial code: scenes/tactical_c/tactical_view.gd:805-815 order_layer sends set_layer at once, no Alt+digit arm, no click, no spot; scenes/tactical_c/layer_view.gd:10-15 'To-layer buttons' (rule: no on-screen button is the control); csrc has no lay_spot though decisions.md L53 (DEC-layerspot-resume) names it; scripts/skilllab/contract.py:49 set_layer has no spot | E-01:73
BIBLE-CONFLICT | R-002-08 | E-01:72 and docs/northstar/ambiguity_register.md:27 | "R-003-07's modifier is open (Q-003-02)" / Q-003-02 closed: "Take Shift (Westley, 2026-10-13: \"shift is still free\")"; the epic never writes Shift. Also E-01:75 Inputs 'modifier key' unnamed
BIBLE-CONFLICT | R-002-08 | C-E-01-6 | already numbered (tactical_view.gd:1206 handling of Alt+N); not re-described
MISSING        | R-003-01 | unbuilt: none found (grep prefer, pref_layer, preferred_layer in csrc, scripts/skilllab, autoload, scenes) | E-01:84
MISSING        | R-003-02 | unbuilt: none found (grep prefer, pref_layer, preferred_layer in csrc, scripts/skilllab, autoload, scenes) | E-01:86
MISSING        | R-003-03 | unbuilt: none found (grep prefer, pref_layer, preferred_layer in csrc, scripts/skilllab, autoload, scenes) | E-01:88
MISSING        | R-003-04 | unbuilt: none found (grep prefer, pref_layer, preferred_layer in csrc, scripts/skilllab, autoload, scenes) | E-01:90
MISSING        | R-003-05 | unbuilt: none found (grep prefer, pref_layer, preferred_layer in csrc, scripts/skilllab, autoload, scenes) | E-01:92
MISSING        | R-003-06 | unbuilt: none found (grep prefer, pref_layer, preferred_layer in csrc, scripts/skilllab, autoload, scenes) | E-01:94
MISSING        | R-003-07 | unbuilt: none found (grep prefer, pref_layer, preferred_layer in csrc, scripts/skilllab, autoload, scenes) | E-01:96
BIBLE-CONFLICT | R-003-07 | E-01:95 and docs/northstar/ambiguity_register.md:27 | "Given the modifier key held" (no key named; E-01:72 calls it open) / Q-003-02 closed to Shift plus the number
MISSING        | R-003-08 | unbuilt: none found (grep prefer, pref_layer, preferred_layer in csrc, scripts/skilllab, autoload, scenes) | E-01:98
MISSING        | R-004-01 | csrc/tactical_move.c:2658 (transition, cross-over at half), om_unit_profile_layer_transition_time | E-01:109 Proof: MISSING
MISSING        | R-004-02 | csrc/tactical_move.c:2658 (transition, cross-over at half), om_unit_profile_layer_transition_time; csrc/unit.c:600 | E-01:111 Proof: MISSING
MISSING        | R-004-03 | csrc/tactical_move.c:2658 (transition, cross-over at half), om_unit_profile_layer_transition_time | E-01:113 Proof: MISSING
MISSING        | R-004-04 | csrc/tactical_move.c:2658 (transition, cross-over at half), om_unit_profile_layer_transition_time | E-01:115 Proof: MISSING
MISSING        | R-004-05 | csrc/tactical_move.c:2658 (transition, cross-over at half), om_unit_profile_layer_transition_time (determinism trace) | E-01:117 Proof: MISSING
MISSING        | R-004-06 | csrc/terrain.c:1065-1070,1269 (om_terrain_slope_count/get/at), csrc/walk_route.c:205; csrc/tactical_move.c | E-01:119 Proof: MISSING
MISSING        | R-004-07 | csrc/walk_route.c:205 (slope time) | E-01:121 Proof: MISSING
BIBLE-CONFLICT | R-004-07 | E-01:120 and docs/bible/epics/E-13-movement-and-command.md:205 (R-207-05), docs/bible/epics/E-11-units-and-combat.md:234 (R-201-02) | E-01: "going up the Raider takes 4.4 seconds ... (speed divided by 1.1)" / E-13 R-207-05: "crossing it takes the slope's length over the unit's speed (E-01 R-004-07)"; E-11 R-201-02: "the time the slope takes is its length over the unit's speed" (no 1.1 factor, both cite R-004-07)
MISSING        | R-004-08 | csrc/terrain.c:1065-1070,1269 (om_terrain_slope_count/get/at), csrc/walk_route.c:205 | E-01:123 Proof: MISSING
MISSING        | R-005-01 | csrc/fog.c:792 (om_unit_get_cross_layer_factor) | E-01:134 Proof: MISSING
MISSING        | R-005-02 | csrc/fog.c:792 (om_unit_get_cross_layer_factor) | E-01:136 Proof: MISSING
MISSING        | R-005-03 | csrc/fog.c:792 (om_unit_get_cross_layer_factor) | E-01:138 Proof: MISSING
MISSING        | R-005-04 | csrc/fog.c:792 (om_unit_get_cross_layer_factor) | E-01:140 Proof: MISSING
MISSING        | R-005-05 | csrc/fog.c:792 (om_unit_get_cross_layer_factor) | E-01:142 Proof: MISSING
BIBLE-CONFLICT | R-005-05 | E-01:141 and E-01:143 (R-005-06) | R-005-05: "any pair three or more layers apart in either direction ... never visible by passive detection at any distance" / R-005-06: "a three-layer enemy is visible at factor 0.20" at a vantage node (also docs/bible/stories.md:11 "nothing three layers away, unless I hold a vantage")
MISSING        | R-005-06 | csrc/fog.c:734-736 (vantage doubling, extra layer) | E-01:144 Proof: MISSING
BIBLE-CONFLICT | R-005-06 | E-01:143 and docs/bible/algorithms.md:276 (ALG-65) | "a three-layer enemy is visible at factor 0.20" / "plus VANTAGE_EXTRA_LAYER = 1 extra factor of min(0.20 · 2.0, 1)" = 0.40 (csrc/fog.c:734 returns the two-layer parameter, 0.20; algorithms.md carries no 'direction changed' note on this point)
MISSING        | R-005-07 | csrc/fog.c:279 (om_fog_zone_interference_at) | E-01:146 Proof: MISSING
MISSING        | R-005-08 | csrc/fog.c (visible set), autoload/c_bridge.gd | E-01:148 Proof: MISSING
MISSING        | R-005-09 | csrc/fog.c:419 (om_fog_ground_reach_w), :669 (om_set_era_kind) | E-01:157 Proof: MISSING
MISSING        | R-005-10 | csrc/fog.c:353 (om_fog_grid_blocks), :311 | E-01:159 Proof: MISSING
MISSING        | R-005-11 | csrc/fog.c:419 | E-01:161 Proof: MISSING
STALE | R-005-11 | E-01:160 and docs/northstar/ambiguity_register.md:38 | "[Q-005-06: which other pieces of the space model a ground-era flyer borrows]" cited as open; Q-005-06 closed (b), other pieces parked past the beta
MISSING        | R-005-12 | no unit code (E-11 R-201-01 roster only) | E-01:163 Proof: MISSING
MISSING        | R-006-01 | unbuilt: none found as a pulse command; csrc/om_constants.h:563-565 OM_PULSE_* are reused as the ping's default parameters (csrc/tactical_move.c:427-429); csrc/fog.c has no pulse state | E-01:170
BIBLE-CONFLICT | R-006-01 | E-01:169 and docs/bible/stories.md:12 | rule stands as live text ("every enemy ... within the pulse radius", radius has no value) / E-01:182 "The pulse is not built: the targeted ping of S-162 takes its place"; catalog row S-006 "I spend a pulse to see every layer around a unit for two seconds" still Spec'd (see C-E-01-5)
MISSING        | R-006-02 | unbuilt: none found as a pulse command; csrc/om_constants.h:563-565 OM_PULSE_* are reused as the ping's default parameters (csrc/tactical_move.c:427-429); csrc/fog.c has no pulse state | E-01:172
MISSING        | R-006-03 | unbuilt: none found as a pulse command; csrc/om_constants.h:563-565 OM_PULSE_* are reused as the ping's default parameters (csrc/tactical_move.c:427-429); csrc/fog.c has no pulse state | E-01:174
BIBLE-CONFLICT | R-006-03 | C-E-01-5 | already numbered
MISSING        | R-006-04 | unbuilt: none found as a pulse command; csrc/om_constants.h:563-565 OM_PULSE_* are reused as the ping's default parameters (csrc/tactical_move.c:427-429); csrc/fog.c has no pulse state | E-01:176
MISSING        | R-006-05 | unbuilt: none found as a pulse command; csrc/om_constants.h:563-565 OM_PULSE_* are reused as the ping's default parameters (csrc/tactical_move.c:427-429); csrc/fog.c has no pulse state | E-01:178
MISSING        | R-007-01 | csrc/fog.c:311 (om_fog_cover_blocks) | E-01:189 Proof: MISSING
MISSING        | R-007-02 | csrc/fog.c:311 (om_fog_cover_blocks) | E-01:191 Proof: MISSING
MISSING        | R-007-03 | csrc/fog.c:311; csrc/unit.c | E-01:193 Proof: MISSING
MISSING        | R-007-04 | csrc/unit.c (damage path unmodified) | E-01:195 Proof: MISSING
MISSING        | R-007-05 | csrc/tactical_move.c:3177 (obstacles block; see C-E-01-1) | E-01:197 Proof: MISSING
BIBLE-CONFLICT | R-007-05 | C-E-01-1 | already numbered (also C-E-17-7)
MISSING        | R-007-06 | csrc/fog.c:311 (om_fog_cover_blocks) | E-01:199 Proof: MISSING
MISSING        | R-007-07 | csrc/fog.c:311 (om_fog_cover_blocks), :353 | E-01:201 Proof: MISSING
MISSING        | R-008-01 | csrc/unit.c:1514 | E-01:212 Proof: MISSING
MISSING        | R-008-02 | csrc/tactical_move.c:3521 (om_roster_set_reach), csrc/unit.c:600 (om_tac_in_reach) | E-01:214 Proof: MISSING
MISSING        | R-008-03 | csrc/tactical_move.c:3521 (om_roster_set_reach), csrc/unit.c:600 (om_tac_in_reach); csrc/unit.c (area damage) | E-01:216 Proof: MISSING
BIBLE-CONFLICT | R-008-03 | E-01:215 and docs/bible/algorithms.md:262 (ALG-61) | "enemies stand on layers 2 and 4 ... take damage only at the layer offsets the Bombard's reach includes" / "every enemy on the attacker's layer within aoe_radius = 150 ... takes ALG-60 damage" (ALG-61 carries a 'direction changed 2026-10-02, rewrite pending' note; recorded as an unrewritten disagreement)
MISSING        | R-008-04 | csrc/unit.c:1514, csrc/fog.c | E-01:218 Proof: MISSING
MISSING        | R-009-01 | scenes/tactical_c/unit_visuals.gd:38,150 (LayerRing) | E-01:232 Proof: MISSING
MISSING        | R-009-02 | unbuilt: none found (grep chevron/spindle/target disc in scenes, autoload) | E-01:234
MISSING        | R-009-05 | unbuilt: none found (grep spindle/terrace in scenes, autoload) | E-01:236
MISSING        | R-009-06 | E-17 R-246-04 vision tube: no code found | E-01:238 Proof: MISSING
MISSING        | R-009-03 | scenes/tactical_c/tactical_view.gd:1199 (KEY_TAB), scenes/tactical_c/layer_view.gd:11 | E-01:240 Proof: MISSING
MISSING        | R-009-04 | scenes/tactical_c/unit_visuals.gd:150 | E-01:242 Proof: MISSING
MISSING        | R-010-01 | autoload/era_config.gd:10 (LAYER_HEIGHT 250.0 fixed global), csrc/terrain.c:975,1048 (om_terrain_band_at, om_terrain_band_heights) | E-01:254 Proof: MISSING
BIBLE-CONFLICT | R-010-01 | E-01:253 and docs/bible/epics/E-17-map-generation.md:497-504 (S-246, R-246-01/02), docs/northstar/ambiguity_register.md:285 | "On a space map the mapping is open (Q-166-02)" / S-246 "Design decided 2026-10-07 and approved as written", R-246-02 "layers are visibly separated"; Q-166-02 status closed, Q-STAGE3-03 closed (b) space field generator ported
MISSING        | R-010-02 | scenes/tactical_c/unit_visuals.gd | E-01:256 Proof: MISSING
MISSING        | R-010-03 | scenes/tactical_c/unit_visuals.gd | E-01:258 Proof: MISSING
BIBLE-CONFLICT | R-010-03 | E-01:257 | number "more than 5 percent of the viewport height" has no Westley source and no DRAFT- name (Half 1: every number Westley's or a named DRAFT-)
MISSING        | R-011-01 | csrc/tactical_move.c:3474 (no mask, accepts every open layer) | E-01:269 Proof: MISSING
MISSING        | R-011-02 | unbuilt: none found; csrc/tactical_mapgen.c:352 om_map_add_layer_restriction_zone is a map zone, not an era mask per unit type | E-01:271
MISSING        | R-011-03 | unbuilt: none found (same) | E-01:273
MISSING        | R-011-04 | unbuilt: none found (same) | E-01:275
MISSING        | R-162-01 | csrc/fog.c:939 (om_command_ping), csrc/cmd_stream.c:253 | E-01:286 Proof: MISSING
MISSING        | R-162-02 | csrc/fog.c:939 (om_command_ping), csrc/cmd_stream.c:253 | E-01:288 Proof: MISSING
MISSING        | R-162-03 | csrc/fog.c:939 (om_command_ping), csrc/cmd_stream.c:253 (alert off by default) | E-01:290 Proof: MISSING
BIBLE-CONFLICT | R-162-03 | C-E-16-9 | already numbered (S-232 catalog row); also docs/bible/stories.md:168 S-162 row "whoever I ping learns roughly where I am" vs E-01:289 "that player is told nothing" (same ruling, second catalog row, not in conflicts.md)
MISSING        | R-162-04 | unbuilt: none found (grep scout/seer in csrc, scripts/skilllab) | E-01:292
STALE | R-162-04 | E-01:291 and docs/northstar/ambiguity_register.md:433 | "[Q-162-06: what a scout is and what it reveals]" cited as open; Q-162-06 closed (c) "decided after players try both"
MISSING        | R-162-05 | csrc/fog.c:939 (om_command_ping), csrc/cmd_stream.c:253 | E-01:294 Proof: MISSING
MISSING        | R-163-01 | csrc/fog.c:742-747 (emit scales cross-layer factor, OM_TP_EMIT_SIGHT_MULT) | E-01:307 Proof: MISSING
BIBLE-CONFLICT | R-163-01 | C-E-01-3 | already numbered; not re-described
MISSING        | R-163-02 | csrc/fog.c:742-747 (emit scales cross-layer factor, OM_TP_EMIT_SIGHT_MULT) | E-01:309 Proof: MISSING
BIBLE-CONFLICT | R-163-02 | C-E-01-4 | already numbered
MISSING        | R-163-03 | csrc/fog.c:206,742-747; scripts/skilllab/contract.py (set_emission) | E-01:311 Proof: MISSING
MISSING        | R-164-01 | csrc/tactical_move.c:3521 (om_roster_set_reach), csrc/unit.c:600 (om_tac_in_reach) | E-01:324 Proof: MISSING
BIBLE-CONFLICT | R-164-01 | C-E-01-2 | already numbered
MISSING        | R-164-02 | csrc/tactical_move.c:3521 (om_roster_set_reach), csrc/unit.c:600 (om_tac_in_reach) | E-01:326 Proof: MISSING
MISSING        | R-164-03 | csrc/tactical_move.c:3521 (reach table is a setting; no weakness table) | E-01:328 Proof: MISSING
MISSING        | R-200-01 | csrc/terrain.c:975,1048 (om_terrain_band_at, om_terrain_band_heights) | E-01:342 Proof: MISSING
MISSING        | R-200-02 | csrc/terrain.c:975,1048 (om_terrain_band_at, om_terrain_band_heights); csrc/terrain.c | E-01:344 Proof: MISSING
MISSING        | R-200-03 | csrc/terrain.c; csrc/walk_route.c:205 | E-01:346 Proof: MISSING
MISSING        | R-200-04 | csrc/walk_route.c:205 | E-01:348 Proof: MISSING
MISSING        | Invariant 1 (unit on exactly one layer) | csrc/tactical_move.c:2658 (transit layer), csrc/fog.c:393 (om_fog_unit_layer) | E-01:392 Proof: MISSING
MISSING        | Invariant 2 (walking unit never occupies no-land, never changes layer except slope, never crosses steep) | csrc/walk_route.c:205, csrc/terrain.c:1269 | E-01:394 Proof: MISSING
MISSING        | Invariant 3 (ground fills layers below its surface) | csrc/tactical_move.c:3177, csrc/terrain.c | E-01:396 Proof: MISSING
WEAK           | Invariant 4 | tests/csim/test_E13_R207_06_never_enter_blocked.py::test_R_207_06_twelve_attack_moving_walkers_never_end_a_tick_in_a_blocked_cell | qualification 1 (also 3, 4, 5): see Half 2 above
MISSING        | Invariant 5 (visible set symmetric in rule) | csrc/fog.c:792, :419 | E-01:400 Proof: MISSING
BIBLE-CONFLICT | Invariant 5 | E-01:399 and E-01:156 (R-005-09) | "Visible set is symmetric in rule, not in outcome" / ground model: "high ground sees down", a higher enemy "never visible ... at any distance" (asymmetric in rule; Q-005-02 symmetric only for the space model)
MISSING        | Invariant 6 (same seed same traces) | csrc/sim.c tick; trace compare in tests only | E-01:402 Proof: MISSING
MISSING        | Invariant 7 (cover never changes damage or movement) | csrc/fog.c:311, csrc/unit.c | E-01:404 Proof: MISSING
BIBLE-CONFLICT | Invariant 7 | C-E-01-1 | already numbered
```
