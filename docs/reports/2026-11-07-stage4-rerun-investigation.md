# Stage 4 re-run: L-0039 movement and L-0061 control investigation, 2026-11-07

Two read-only investigations (Sonnet 5.5) of Westley's watch notes on the re-run (main f255aae5). Hypothesis tests, all red on main for the stated reason, sit on local branches that are not merged: `s/inv2-L0039-hypothesis-tests` (commit fd6c91ff, worktree `~/Projects/om-wt/inv2-L0039`) and `s/inv2-L0061-hypothesis-tests` (commit 213313c6, worktree `~/Projects/om-wt/inv2-L0061`). Traces are tick by tick from the real fights and match the committed fight files at every snapshot.

## L-0039

Frames 8 and 9 are ticks 1600 and 1800 (`snapshot_every` 200).

### Shooting through cover: not found
- Control: 241 shots, 0 cross a built box. Sight on: 175 shots, 0 cross.
- What the picture shows is target lines. The replay draws a line from each unit to its `target`, not its shot (`scenes/proto/fight_replay/fight_replay.gd:249-252`). In the control, 13 of 14 target lines cross a box at those frames while no shot is fired that tick. The sim keeps targets it cannot shoot (`can_shoot` is 0 on all 108,237 crossing pairs when no unit stands in a cell). R-087-09 (drop a blocked-line target within 1 s) is ruled but not built.

### Units move inside the box cell: PROVEN
- Units end ticks inside a blocked cell by up to 6.5 wu (one step). Interceptor 121 unit-ticks (up to 4.5 wu), Warden 72 (up to 2.5 wu).
- Cause: `om_move_walker_step` (`csrc/tactical_move.c:2296`) has no cell guard; `om_move_terrain_guard` is called only from the steer step (line 2233). `om_move_leave_blocked` (line 2127) ejects the unit the next tick, so it saws in and out. Breaks the E-13 invariant and R-207-06/07.
- Drawing is not the cause: the drawn rectangles, `snap.built_rects` and the engine's blocked cells are the same three cells.

### Sight across a box (PROVEN)
- A unit inside a cell sees through the whole box: `om_fog_grid_blocks` (`csrc/fog.c:353-389`) skips both endpoint cells. Sight-on fight: 114,212 of 115,416 crossing pairs with an endpoint in a cell are seen; with no endpoint in a cell, 0 of 365,358.
- Sight and fire disagree: `om_move_los_clear` (`tactical_move.c:1355`) tests the endpoint cells, so the same pairs are seen but `can_shoot` is 0.

### Blue unit walking while shooting (PROVEN)
- Blue Vanguard 1, ticks 1501 to 2557: drifts 4 wu every 4 to 6 ticks, from (1896,2138) to (1606,2037), a shot every 24 ticks, `engaged` 1 and `current_speed` 0 between steps. Not a push (nothing within 100 wu), not sliding, not a manual order.
- Mechanism: the attack-move branch (`csrc/unit.c` around 2285-2300) holds while `can_shoot` is true and walks its goal when it is false. Its target, Warden 14, is pressed on the west face and steps in and out of the cell every 4 ticks (x 1892.4, 1895.6, 1899.0, 1902.4, back to 1892.4), so `can_shoot` flips with it. Vanguard 1 moved on 92 ticks, every one with `can_shoot` false.

### Red unit bouncing, blue untargeting and retargeting (PROVEN)
- Red Warden 12, ticks 664 to 12000: walks east about 40 ticks (x 1655 to 1769) toward a blue unit, then back to (1620,1965), reversing every 80 to 160 ticks; 18 reversals between ticks 700 and 1500.
- Driver: blue 1, 4 and 5 press the east face and step in and out of the cell on alternate ticks. Over ticks 700 to 899, `can_see` between blue 4 and red 14 equals "blue 4 stands in a cell" on all 200 ticks. Red acquires when it sees, chases, loses the target a tick later and walks back; blue's targets flip the same way because the side shares what it sees.
- Not the cause: no target-slot toggle, no layer crossing. In the control the same pressing gives a 4-tick, 10 wu saw-tooth on red 13 and 14.

### One root, plus separate defects
- One root cause for walking-while-shooting and the bounce: a walker pressing into a blocked cell and flipping in and out.
- Separate: sight and fire treat endpoint cells differently.
- Separate: a walker never routes around a box (`om_walk_route`, `csrc/walk_route.c:1-7`, treats a canvas with no terrain as all open). In the pair run the Vanguard never goes below x 1998 and fires nothing though the preflight says reachable. This pins units against the face.
- Separate: R-087-09 is unbuilt.

### Tests (tests/skilllab/arena/, fixtures `stage4bug_L0039_fixtures.py`), all red on main
- `test_stage4bug_L0039_blocked_cell_entry.py::test_no_unit_stands_in_a_blocked_cell_at_the_end_of_any_tick` (2 params; 40 and 193 unit-ticks inside a cell)
- `..._sight_across_box.py::test_no_side_sees_the_other_across_a_box_on_any_tick` (40 ticks)
- `..._sight_fire_agree.py::test_a_pair_that_sees_each_other_across_the_boxes_can_shoot_each_other` (80 cases)
- `..._walker_routes_around_box.py::test_a_walker_ordered_past_a_box_gets_round_it_and_fights` (no shot in 260 ticks)
- `..._unshootable_target.py::test_a_target_whose_line_stays_blocked_is_dropped_within_a_second` (holds of 397 and 400 ticks)
- `..._fire_halt_and_bounce.py` (3 tests: a firing unit stays where it halted, 23 gaps; no unit holds a target across a box, 4,375 unit-ticks; red 12 does not pace, 18 reversals)
- Four positive controls pass. DRAFT thresholds Westley owns: the 600-tick window, one reversal allowed for the bounce.

### Rulings needed
- Cover against blocked cells: R-007-06 and R-098-02 let a unit standing inside cover be seen and fired at as normal; the engine's sight does that for blocked cells, fire does not. Westley's 2026-11-06 "boxes block exactly their cells" plus the E-13 invariant says no unit stands in one. Either fire adopts the exemption (the sight-and-fire test passes, the blocked-cell test stays red) or units never enter the cell (both pass).
- Whether building the R-087-09 firing-spot search and drop is in scope.
- Whether walker routing around planar blocks is its own engine story.

## L-0061 control

### Circles: mostly by design
- The replay draws one attack-range ring per role per side by default, not per unit (H-053 item 2; `fight_replay.gd:263-273`); R shows one per living unit. A ring is drawn only while its anchor unit lives (the tick-0 unit of that role nearest the enemy, line 266). Neither H-053 nor the stage 4 spec says what happens when the anchor dies.
- Rings per frame, seed 10, identical in both files: frames 0 and 1 show 5, frame 2 shows 4, frames 3 and 4 show 3, frames 5 to 12 show 2, frame 13 on shows 1 (the A Vanguard), the last frame still shows that one ring with red dead.
- The control file has no `sights` key; spec criteria 4 and 7 say a control document has none and a file without `sights` draws none. Missing sight discs and hollow marks there are by design.

### Blue idle at the end: by order, plus one engine gap (PROVEN)
- All 24 blue units are guards (`hold:A`), max displacement 0 wu, order kind -1, no destination at any tick. Not stuck on geometry: they stand on the plateau (radius 521 to 674 wu from the hill centre, rim at 700); the last reds stand on the ramp at radius about 802 to 809, 145 to 200 wu from blue's front.
- Unit-ticks (23 blue x 1517 ticks): 32,975 with a target; idle with red layer 0 within range+200: 1,187; idle with red beyond range+200: 577; idle with red in range (re-acquiring): 344; idle with a seen same-layer red 5 to 57 wu beyond range: 288.
- At tick 1500, 19 blue fire and 4 are idle (units 1, 11, 13, 23), all Vanguards (range 300) with a seen layer-1 red 301 to 357 wu away.
- The gap: R-096-08 says a guard steps toward a seen same-layer target, at most 200 wu from its post. The engine never steps: a guard acquires only inside attack range and does not walk (`csrc/unit.c:253`, `2245-2250`). The bible itself says the step-and-return is "not yet built" (E-13 line 55). The same rule's text also says "as built 2026-10-14 the walk is toward same-layer targets only" and "holds and never steps forward": it contradicts itself.
- Sight on against control: a per-tick diff of the seed-10 runs shows 0 differing ticks out of 1517. The pre-fix run (1399 ticks, 24 against 0) also had blue at 0 displacement, so the idle blue is not new. In that run red never had a target (layer 0, reach up 0), the cause of the earlier "red never fires back" report.
- The layout (`orders = "hold:A"`, blue "firing down at red crossing the flat") is consistent with holding. The four idle units are the unbuilt step.
- Side finding, untested: red Interceptor 36 sits at x about 1190 to 1200 on the ramp midline for ticks 150 to 1377, with a destination and no target, and flipped layer 475 times. Likely a queue behind red's front rank, below the flip line with reach up 0.

### Test
- `tests/skilllab/arena/test_stage4bug_L0061_guard_step.py::test_a_guard_steps_toward_a_seen_same_layer_enemy_just_beyond_its_range[on]` and `[control]`: red on main with `{1: 30, 11: 138, 13: 90, 23: 30}` (guard units idle at least 20 ticks while a seen same-layer enemy is within weapon range + 200 wu). The 20-tick threshold is `DRAFT-guard-idle-ticks`, Westley's.

### Rulings needed
- Whether a role's ring and disc stay visible after its anchor unit dies (unspecified in H-053 and H-088 criterion 7).
- Whether the R-096-08 guard step is wanted (engine story, and the rule text rewritten either way).
