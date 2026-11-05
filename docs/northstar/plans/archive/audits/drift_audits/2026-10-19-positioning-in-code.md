# Setup audit: does "only numbers decide before contact" live in the code?

Auditor: Opus, independent, read-only. 2026-10-19.
Sources: `origin/main` 86510b1f (bible, csrc, docs) and the lab integration branch `origin/push/labrev2-lab` c2d9bce8 (scripts/skilllab, lab README), worktree `~/Projects/om-push/wt/setup-audit`. On the lab branch, csrc differs from main only in `unit.c` and `tactical_move.c` (E1 attack-move resume, 81+/47-). Engine line numbers below are `origin/main` line numbers. Lab line numbers are c2d9bce8 line numbers.

The sentence under audit ("before the first shot nobody can fire, so the setup alone says nothing about which side's arrangement is better, only which side is bigger") does not appear in any committed file. I searched both refs with `git grep` for twelve phrasings ("only which side", "setup alone", "nobody can fire", "before the first shot", "numbers decide", "until contact", "arrangement is better" and others). It was said in chat, not written down.

---

## A. Positional advantages: promised, built, wired, measured

Key to the columns:
- **Wired** means the mechanism runs in `om_tactical_step` (unit.c:2298-2328) or is reachable from a pipe verb (`csrc/pipe/om_pipe.c:1567-1608`: move, attack_move, attack_target, activate_ability, set_layer, ping, place, hold) or from the lockstep stream (`cmd_stream.c:251-254`: set_layer, set_emission, ping, guard).
- **Count sees it** means one of the five gates in `firing.py:60-83` reads it: reach, side's sight, range at the layer offset, arc, line blocked.
- **Engine defaults that matter:** `OM_TP_TARGET_BY_SIGHT` = 1 (tactical_move.c:383). Every RANGE_/DAMAGE_/AREA_ offset multiplier = 1.0 (tactical_move.c:400). Vision factors are 0.5, 0.2, 0, 0 (tactical_move.c:376). EMIT_SIGHT and EMIT_SEEN = 1.0 (tactical_move.c:394). Every unit type's reach = (0 up, 0 down) unless `om_roster_set_reach` is called (tactical_move.c:3382-3392).

| # | Advantage | Bible promise | Engine mechanism, file:line | Wired? | Lab play or knob that exercises it; can the count see it? | Verdict |
|---|---|---|---|---|---|---|
| 1 | Bigger force | Hub game_bible.md:95 (the result follows how many can fire); README (main):16 (with everything identical, the larger force wins) | Headcount alone. No code favours size; more units means more able shooters. | yes | Control `mirror` and `numbers` (sweep.py:27, `default_control_builds` sweep.py:362). The count sees it directly. | REAL AND MEASURED |
| 2 | Layer above (being on another layer from the enemy) | E-01:18 (terrain blocks layers; cross-layer vision is worse); R-008-02 E-01:157; R-164-01..02 E-01:243-244 (reach by type decides who can fire); hub:24 and :95 | Reach gate `om_tac_in_reach` unit.c:572. Range, damage and area multipliers by signed offset unit.c:579-589 (default 1.0, so above and below are symmetric). Cross-layer vision fog.c:722-740 (space: symmetric 0.5/0.2). Ground: `up ? 0.0 : 1.0` fog.c:730. **But the bible's reach table is never set in the game.** `om_roster_set_reach` (tactical_move.c:3305) has one caller, unit.c:2488, which only re-applies values across a reset. No pipe verb or pack loader sets it (`git grep` on csrc, csrc/pipe, autoload, scenes). So in the shipped game every type has reach (0,0) and fires on its own layer only. | Mechanism wired; **reach table not wired** (it is reachable only from the lab: engine.py:184; lab table plays_space.py:48) | `s3_layer_above`, `s3_types_by_reach`, `s3_over_the_choke` (plays_space.py:127-143). Families vision, range_up, damage_up, sign_flip (sweep.py:30). Gates 1, 2 and 3 of firing.py:65-72. | REAL AND MEASURED in the lab. **PROMISED BUT NOT WIRED** in the game (reach table missing). |
| 3 | Layer below (firing up) | R-164-01 E-01:243 (Interceptor reaches two up); Westley 2026-10-13: firing up is a penalty (README main:94) | Same code as row 2. `OM_TP_RANGE_UP_n` and `DAMAGE_UP_n` default 1.0 (tactical_move.c:400), so no penalty exists until the lab sets one. | Same as row 2 | `s3_types_by_reach` (Interceptor 2 up). The range_up and damage_up families sweep 1.0 down to 0.25 (sweep.py:34-35). Gate 3 reads the multiplier (firing.py:51-58). | REAL AND MEASURED in the lab; numbers open (Q-008-03); not wired in the game (row 2) |
| 4 | Surround and flank | Hub:24 and :61; E-11:18 ("Strike flanks Siege"); R-081-02/03 E-11:34-35 ("from the flank"); R-099-01 E-13:97 (flanking comes from speed); S-100 E-13:109 (firing arc, Q-100-01) | No directional damage anywhere. ALG-60 (algorithms.md:258) has no facing term. The firing arc is not built: `OM_TP_FIRING_ARC_DEG` is absent from ouroboros_sim.h:1010-1076 on main and on the lab branch. The fire pass (unit.c:2246-2269) has no arc gate. Facing turn rates exist (ALG-69). A flank pays only through the count: more of your units in range of fewer of theirs. | Arc **not built** (E0/E2 pending) | Arc family on `s2_concave` and `s2_mass_one_end` is skipped while the parameter is missing (sweep.py:177-182). Gate 4 is composed in the lab (firing.py:73-80) but the engine fires at 360 degrees. No surround play exists. | Geometric part (more guns in range) REAL AND MEASURED. Arc PROMISED BUT NOT BUILT. "Surround" as a play: REAL BUT UNMEASURED. |
| 5 | Trap and ambush (stealth, emission) | R-163-01..03 E-01:229-231 (going dark); README main:47 (S4 ambush, "later"); R-120-02 (enemy ambush) | Emission: fog.c:742-750, set by `om_command_set_emission` fog.c:856, reachable only from the lockstep stream cmd_stream.c:252 (**no single-player pipe verb**, om_pipe.c:1567-1608). Default state is silent (fog.c:206, zeroed) and both multipliers default to 1.0, so emitting does nothing at defaults. Stealth flag unit.c:260 is honoured at unit.c:1166, 1780 and others, but `om_unit_set_stealth` (unit.c:2970) has **no caller** outside tests. Enemy-macro ambush waits until contact (enemy_macro.c:483), wired via `om_macro_tick` unit.c:2318. | Emission: net stream only. Stealth: test only. Macro ambush: wired. | `s3_dark_striker` (plays_space.py:145-148) only **sets side 0 silent, which is already the default**, and never sets anyone emitting. Its description, "the enemy keeps emitting" (plays_space.py:219), is not what it does. **Measured:** the emitting family point (sight 2/seen 3, and 4/8) gives a byte-identical fight to defaults (side0, 1669 ticks, survivors 14:0, firing 701.25:155.25). `positions.ambush_play` (positions.py:54) is idle-then-attack-move; no stealth. Gate 2 would see stealth or emission if either were on. | Emission: REAL BUT UNMEASURED (the lab knob is dead). Stealth: PROMISED BUT NOT WIRED. Ambush timing: REAL BUT UNMEASURED. |
| 6 | Choke hold | E-17 R-113-03, R-113-05 (E-17:61, :63, width = w x 200 wu); R-192-02 and R-192-04 E-17:302, :304; README main:35 | Blocked cells and routing ALG-67 (tactical_move.c); line of fire through blocked cells `om_combat_can_shoot` tactical_move.c:2707-2740. **The game's choke generator is a stub:** `om_map_compute_chokepoint_width` returns 0 (tactical_mapgen.c:418-422) and `om_map_has_flank_bypass` returns 0 (tactical_mapgen.c:579-583). | Blocking and routing wired. Choke **generation not built** in the game. | `s1_hold_choke`, `s3_over_the_choke`, `s1_outrange` (plays_space.py:103, 137, 192). Layout feature `choke_width_bodies` (maps.py, depth.py:65). Gates 3 and 5. On layout 192 `s1_hold_choke` is refused `no_fit` by pre-flight (measured below). | Mechanics REAL AND MEASURED in the lab. Choke generation PROMISED BUT NOT BUILT in the game. |
| 7 | Vision and spotting | E-12 R-093-02 (E-12:91, a side fires at what any of its units sees); R-008-04 E-01:159; S-162 ping E-01:213; S-005 | `om_tac_faction_sees` unit.c:1165-1171. `om_fog_faction_sees` fog.c:486-506 (the side's union plus ping discs). Sight gate in acquisition and fire `om_tac_may_act_on` unit.c:1178. Ping fog.c:939, pipe verb om_pipe.c:1594. | yes | `s3_ping_then_commit` (plays_space.py:151-154). The vision family. Bombard/Bastion with a spotter (M3b, spec:45). Gate 2 (firing.py:67). | REAL AND MEASURED |
| 8 | Cover | E-01 S-007 E-01:140-146 (blocks sight and fire by height; **R-007-04: never a damage reduction**); E-17 R-190-05 E-17:266 | `om_fog_cover_blocks` fog.c:311-332 (by height when ROUTE_AROUND_TERRAIN is 1, the default). Fire side `om_combat_can_shoot` tactical_move.c:2726-2729. | yes | Cover discs from the `cover_field` map kind and `cover_density_corridor` (maps.py:87-105, :131-132). Anchor "behind_cover" for the s3 layer plays (plays_space.py:246-247). Gate 5 sees it. The lab's paper sightline probe `scenes.sight_clear` (scenes.py:277-290) reads **blocks only, not cover discs**. | REAL AND MEASURED (the layout features). The "fight from behind tall cover" play itself is a ground play, not measured. |
| 9 | High ground and slope | Hub:24, :61; R-005-09..11 E-01:117-119 (ground: high sees down, low never sees up); R-004-06..07 E-01:90-91 (midline; slope speed /1.1 up); R-084-06 E-11:96 and R-091-03 E-12:67 (**no elevation damage bonus**); E-12 R-091-02 (space elevation sensor bonus) | Ground vision `return up ? 0.0 : 1.0` fog.c:730. Terrain blocks sight `om_terrain_sight_blocks` terrain.c:1298-1314, used in fog.c:767, :779 and tactical_move.c:2733. Slope speed tactical_move.c:2265-2266. Era kind set from `mission_start` om_pipe.c:1219, :1309. Space elevation sensor bonus fog.c:461-466, but its tier is set only by `om_unit_spawn_with_elevation` fog.c:800, which **has no caller** in csrc or the pipe. | Ground model wired (era_kind 1 with terrain). Space elevation bonus: test only. | Ground lab `scripts/skilllab/ground/scenes_ground.py:12-14` (`s1_slope_top` plus two variants). The README (lab branch):64 says its eye-height and flyer knobs are inert in the natural scene. Decision 45 D2 (decisions.md) moves the ground scene to batch two. Batch one runs space layouts 81, 78 and 192 only (decisions.md:166). | REAL BUT UNMEASURED (batch one) |
| 10 | Facing and arc | S-100 E-13:107-118; R-100-04 DRAFT 120 degrees; spec ruling 8 (spec:20) | Facing and turn rate exist (ALG-69). Arc gate not built (row 4). | Facing wired; arc not built | Arc family skipped (sweep.py:177-182). | PROMISED BUT NOT BUILT |
| 11 | Area denial | R-084-03 E-11:93 (Bombard disc); R-086-05 and R-086-06 E-11:127-128 (Barrage telegraph, Fortify zone); R-082-10 E-11:61 (cone, ruled 2026-10-15) | Disc AoE unit.c:1966-1968 calls `om_unit_fire_aoe_attack` unit.c:2766. Abilities `om_ability_advance_all` unit.c:2316. Cone not built (`om_roster_set_cone` is absent on both refs). | Disc and abilities wired. Cone not built. | Bombard disc is present in M3 mixes (`s2_screen`, `s3_over_the_choke`). The lab disables abilities (fight.py:174-175). Cone family skipped (sweep.py:181). The count sees only the direct shooter, not splash victims. | Disc: REAL BUT UNMEASURED as a positional play. Cone: PROMISED BUT NOT BUILT. |
| 12 | Unit-type positioning (which type stands where) | Hub:95 ("which unit types beat which"); README main:48-50 (S5); E-11 R-081-01 E-11:33; R-164-01 (reach by type) | Category multiplier `om_resolve_hit_multiplier` unit.c:984-988, applied in `om_tactical_apply_hit` unit.c:1016-1029. Sensor shorter than range: a Bombard fires past 300 wu only on a friend's sight (E-12:91, via unit.c:1165). | Category wired. Reach by type not wired (row 2). | `s2_screen`, `s5_vulnerable_away`, `s3_types_by_reach` (plays_space.py:122, 170, 132). Type weight `count_weighted` firing.py:119-127. | REAL AND MEASURED (category and sight). Reach part not in the game (row 2). |
| 13 | Concave and focus fire | README main:38 (S2 concave); Q-008-05 E-01:165 (focus fire is a lab-only setting; the game rule stays nearest enemy) | Concave: no mechanic; it is geometry (how many are in range at once). Focus fire: `OM_TP_TARGET_POLICY` with most-damaged policy at unit.c:1722-1726, default 0 (nearest) at tactical_move.c:382. | Concave: n/a. Policy: wired as a setting, off by default. | `s2_concave`, `s2_spread_line`, `s2_mass_one_end`. The focus_fire batch (batches.py:83-100) runs nearest against most-damaged. Gate 3 sees range geometry. On layout 192 `s2_concave` is refused `no_fit` (measured below). | Concave: REAL AND MEASURED. Focus fire: REAL AND MEASURED (lab batch), not a game rule. |
| 14 | Terrain blocking lines of fire | R-007-07 E-01:146; E-13 R-098-02 E-13:87; R-087-09 E-11:151 (seek a firing spot within 1 s) | `om_combat_can_shoot` tactical_move.c:2707-2745 (blocked cells by layer, cover discs, ground terrain), checked in the fire pass unit.c:2259. Seek-a-firing-spot: no `R-087-09` reference in unit.c or tactical_move.c. Steering in R-087-04 (E-11:146) walks the route and fires when the line clears. | Blocking wired. The 1 s seek-and-give-up is not found. | Every terrain layout (blocks, lanes, walls; maps.py). Gate 5 (firing.py:81). Paper probe `scenes.sight_clear` (scenes.py:277). | Blocking: REAL AND MEASURED. R-087-09's seek: PROMISED, not found in code. |

---

## B. The misperception: sentences that say or imply that position does not matter before contact

| Where | Quote | Kind |
|---|---|---|
| (chat only) | "before the first shot nobody can fire, so the setup alone says nothing about which side's arrangement is better, only which side is bigger" | **Design claim.** Not in any committed file on either ref. |
| docs/bible/game_bible.md:95 | "What decides an engagement is how many units on each side can get shots off, and for how long: skill is arranging that count in your favour, and the result follows it." | Design claim. **Positional by its own words** ("arranging that count"). Not a headcount claim. |
| docs/bible/game_bible.md:24 | "A smaller force that understands surrounds, high ground, and the 2.5D layer and vision system beats a larger force that does not." | Design claim. The opposite of the misperception. |
| layer_dynamics/README.md (lab):15 | "It is the advantage over the whole fight that counts, not only the opening" | Westley's design claim. **It conflicts with the lab's primary prediction form** (next rows). |
| layer_dynamics/README.md (lab):16 | "With everything identical, the larger force wins ... So it is a control, not a scenario." | Design claim about controls only. It explicitly limits "numbers win" to identical arrangement. |
| layer_dynamics/README.md (lab):74; spec ruling 5 (2026-10-14-skill-lab-rev2-spec.md:17); contract.py:159 | "Two predictions per fight, both from the opening window after first contact." `OPENING_WINDOW_TICKS = 40  # DRAFT ... the primary prediction window after first contact` | **Measurement-timing choice.** It came from the toy lab ("the whole-fight form partly restates the outcome": transcript 2026-09-30_ab897d80, line 1264). The prediction starts at the first sample where any unit is able (fight.py:371) and spans 40 ticks (2 s; fight.py:209-214). Nothing before contact enters the prediction. |
| decisions.md:93 (2026-10-14-skill-lab-rev2-decisions.md) | "The opening window is the default basis of the C2 agreement (ruling 5 makes it the primary prediction form)" | Measurement-timing choice. |
| layer_dynamics/README.md (lab):165 (main:141) | "Plays start the sides at contact distance ... two armies walked straight at each other from far apart collapse into flat rows, and the number measured is the walk's." | Limitation statement about the instrument. |
| layer_dynamics/README.md (lab):230, :232 | "A layer alone gives nothing under symmetric vision." "Holding a choke gave nothing, for three reasons ..." | Limitation statements: toy results, filed as "leads, to be re-measured on the real engine" (README main:195). The closest written text to "position does not matter", but scoped and caveated. |
| docs/bible/epics/E-01-layer-system.md:166 | "The prototype is same-layer only until the lab reports." | Limitation statement. **The code matches it:** the game never sets reach (A row 2). |
| layer_dynamics/ping_definition_and_measurement.md:39 | "Its whole value is that it lets a player choose a better play before contact" | Design claim. The opposite of the misperception: information before contact has value. |
| csrc/enemy_macro.c:483 | "ambush holds until contact, then becomes advance_aggressive" | Behaviour comment. Neutral. |
| toys/layerlab/tests/test_seer.py:150, :219 | "No side sees any unit, nobody can fire" | Limitation statement about a blind test case. Toy only. |

No engine comment and no lab docstring says that headcount alone decides a fight, or that a setup carries no information. The engine computes positional gates on every tick. Where the idea does show up in the lab, it shows up through timing, not through any written claim: the prediction is only formed after first contact, over 2 s.

---

## C. The prediction

### What it uses (lab branch c2d9bce8)

- **Per unit, per sample.** Every `sample_every` = 5 ticks (contract.py:87), each living unit gets a code against its target of record: the engine's target if able, else the nearest able enemy, else the nearest enemy (firing.py:91-107). The code comes from five gates in diagnostic order (firing.py:60-83):
  1. reach at the layer offset;
  2. the side's sight (`visible_enemies`);
  3. range times the offset multiplier;
  4. arc (lab-composed only);
  5. `can_shoot` (blocked line).
- **Count.** `count_able` (firing.py:113-116) counts code-0 units. `count_weighted` (firing.py:119-127) sums the category multiplier against each unit's target of record.
- **Moment.** `contact` is the first sample with any able unit (fight.py:371). `_window_seconds` sums [contact, contact + 40) (fight.py:209-214). `_predict` takes the larger total (fight.py:217-218). Whole-fight totals are kept beside it (fight.py:370), not used as the prediction.

So the count itself is positional. But it is read only after contact, and over only 2 s.

### Could a prediction be made from the Setup alone? Yes, partly.

A `Setup` (contract.py:82-96) carries every group's type, count, formation, anchor, facing and layer, the unit_types reach, `settings` (vision, range and damage multipliers, emission), the timeline (ping, emission, layer orders), and `terrain.blocks` and `terrain.covers`. The lab already does geometry on a setup with no engine: `scenes.sight_clear` (scenes.py:277) and the `preflight` refusals `no_reach` and `blind_post` (scenes.py:452-468).

| Table row | Paper-scorable from Setup data today? | What it needs |
|---|---|---|
| 1 bigger force | yes | Group counts |
| 2, 3 layer above or below | yes | Group.layer, reach, `OM_TP_RANGE/DAMAGE/VISION_*` in settings or defaults |
| 4 flank angle | partly | Formation, anchor and facing give angles. Needs the arc (not built). Who reaches the flank first needs engine movement (R-099-01). |
| 5 emission and stealth | yes, as flags | Timeline steps and multipliers. When the hider is found needs engine state. |
| 6 choke width | yes | Gap in terrain.blocks plus attack range; the toy formula D(D+1)/(2c) (README lab:233) is paper-only. |
| 7 sight lines | yes, for blocks and range | `sight_clear` plus sensor and vision factors. Ping timing needs the engine. |
| 8 cover | yes | terrain.covers (height, radius). The existing probe ignores covers, so it would need extending. |
| 9 high ground and slope | no (ground) | The field is generated by the engine from `field_seed` (fight.py:186-188). |
| 11 area denial | partly | Disc radius and density at contact need where the units bunch: engine state. |
| 12 type placement | yes | Types, positions, category matrix, reach |
| 13 concave | yes | Formation geometry against the expected arrival point |
| 14 terrain lines of fire | yes, for blocks and cover | `sight_clear` |

Needs engine state in every case: the path each side takes (routing ALG-67, steering ALG-68, collision), where and when contact happens, target choice and leash over time, attrition order, and transition timing.

### Experiment (layout 192, 16 v 16, the real engine)

Commands, from the scratchpad (script `exp/setup_score.py`; lab tree `~/Projects/om-push/wt/setup-audit` at c2d9bce8, built with `make`; about 25 s wall in total):

```
timeout 600 ~/Projects/ouroboros-manifold/.venv/bin/python exp/setup_score.py ~/Projects/om-push/wt/setup-audit s3_layer_above,s1_hold_choke,s2_concave 2
timeout 600 ~/Projects/ouroboros-manifold/.venv/bin/python exp/setup_score.py ~/Projects/om-push/wt/setup-audit s3_layer_above:reach_zero,s3_layer_above:naive_defender_attacker_layer,s3_types_by_reach,s1_hold_choke:naive_defender 2
timeout 300 ~/Projects/ouroboros-manifold/.venv/bin/python exp/emit.py ~/Projects/om-push/wt/setup-audit
timeout 600 ~/Projects/ouroboros-manifold/.venv/bin/python exp/dbg.py ~/Projects/om-push/wt/setup-audit
```

**How the paper score works (crude, setup only).** For each side, each unit counts if some enemy unit is at a layer offset inside its type's reach (reach from `Setup.unit_types`, else plays_space.py:48) and `scenes.sight_clear` finds a straight line through the blocks. A counting unit adds the best category multiplier it has against those enemies (engine matrix). Range and movement are ignored.

**Measured.** `scan.cell(build, 16, replicates=2)` gives 4 fights: seeds 0 and 1, each with swap off and on. Layout 192 is blocked_layer_top 0, choke_width_bodies 8, detour 1.5, lanes 0, start_distance 2800.

| Play (role) | Pre-flight | Paper score s0 : s1 | Headcount | Paper sign | Measured outcomes | Mean margin | Window prediction |
|---|---|---|---|---|---|---|---|
| s3_layer_above (play) | ok | 20.0 : 16.0 | tie | side0 | side0 x4 | +0.500 | side0 x4 |
| s3_types_by_reach (play) | ok | 20.0 : 16.0 | tie | side0 | side0 x3, side1 x1 | +0.195 | side0 x4 |
| s1_hold_choke (play) | **no_fit** | 16.0 : 16.0 | tie | tie | side1 x4 | -0.460 | side0 x4 (all wrong) |
| s2_concave (play) | **no_fit** | 16.0 : 16.0 | tie | tie | side1 x4 | -0.465 | side1 x3, side0 x1 |
| s1_hold_choke (naive_defender) | ok | 14.0 : 16.0 (2 holders blind) | tie | side1 | side1 x4 | -0.541 | side1 x4 |
| s3_layer_above (naive_defender_attacker_layer) | ok | 20.0 : 20.0 | tie | tie | side1 x4 | -0.424 | side0 x4 (all wrong) |
| s3_layer_above (reach_zero, null control) | ok | 12.0 : 14.0 | tie | side1 | cap x4 (expected: nobody can reach the layer-1 Raiders) | +0.072 | side0 x4 |

What the numbers show:

1. **Where the paper score is not a tie, its sign matched the measured winner** in 3 of 3 decided cases (s3_layer_above, s3_types_by_reach, and the hold-choke naive defender). For s3_types_by_reach that held in 3 of its 4 fights. Headcount predicted a tie in every row.
2. **Where the paper score is a tie, the fight was decided by contact geometry the crude score does not model** (the choke gap and the concave's arc against the arrival point). Both of those plays were refused `no_fit` on this layout, yet `scan.cell` still fights them.
3. **The opening window cannot see the layer arrangement on this layout.** Three setups give the identical window (10.5 : 3.0 unit-seconds) and identical firing samples from contact at tick 315: (315,3,0) (320,3,0) (325,5,0) (330,6,1) ... Those setups are:
   - the play: Raiders on layer 1, reach (1,1);
   - reach_zero: Raiders reach (0,0);
   - the naive defender: Raiders moved to layer 0.

   They ended side0, cap and side1. The front Vanguards, identical in all three, are the only units firing in the first 2 s; the Raiders stand 150 wu behind. Whole-fight totals separate the three: 709.0 : 565.2 (side0), 289.5 : 565.2 (cap), 297.8 : 776.8 (side1).
4. **The emitting family is dead on its only play.** The s3_dark_striker fight is identical at defaults, at sight 2 / seen 3, and at sight 4 / seen 8: side0, 1669 ticks, 14:0, 701.25 : 155.25. The play silences side 0, which is already silent, and no unit is ever set emitting (plays_space.py:148 against its description at :219).

---

## D. Verdict for the designer

**Did the misperception get into the code? Partly, and not as a written rule.**

- **The bible says the opposite** (hub lines 24 and 95). The engine computes position on every tick:
  - the side's sight through fog, cover and blocked cells;
  - line of fire;
  - the reach gate and offset multipliers;
  - ground high-sees-down;
  - slope speed;
  - category multipliers.
- **No code comment or doc says that headcount alone decides a fight.**
- **Where it did get in is the lab's prediction timing.** The firing-count prediction is formed only from the 2 s after first contact (contract.py:159, fight.py:209-218, spec ruling 5). That is against Westley's own line, "the advantage over the whole fight that counts, not only the opening" (README lab:15). On layout 192 that window gave the same number for three arrangements that won, stalled and lost.
- **Nothing in the lab predicts from the setup.** Yet a crude setup-only score called the winner wherever it was not a tie, while headcount called a tie every time.

**What the engine honours today, wired into play:**
- sight (including friendly spotting and the ping, which has a pipe verb);
- cover and blocked cells for both sight and fire;
- the category triangle;
- sensor-shorter-than-range spotting;
- the ground model (high sees down, terrain blocks sight, slope speed);
- the enemy macro ambush;
- the Bombard disc and the abilities.

**Built but not wired for the player:**
- **Reach by type** (R-164-01): no game path sets it, so every type fires on its own layer only. The layer play the lab measures cannot happen in the game today.
- **Emitting:** lockstep stream only, no pipe verb, and the multipliers are 1.0.
- **Stealth:** no caller.
- **Space elevation sensor bonus:** no caller sets a tier.

**Promised and not built:**
- the firing arc (flank by facing);
- the cone;
- the game's choke generator (stubs at tactical_mapgen.c:418 and :579);
- R-087-09's seek-a-firing-spot (not found);
- the cross-layer numbers (Q-008-03 open).

**What the lab can see:**
- layer and reach;
- sight and ping;
- category weight;
- choke and concave geometry through range and line of sight, during the fight.

**What it cannot see today:**
- anything before contact;
- anything that pays off after the first 2 s (the primary prediction);
- the arc and the cone (skipped);
- emitting (its play is a no-op);
- high ground and slopes (the ground scene is batch two);
- splash victims (the count sees the shooter only);
- cover discs in its own paper sightline probe.
