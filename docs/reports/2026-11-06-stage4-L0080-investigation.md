# Stage 4, L-0080 (trap) investigation, 2026-11-06

Investigator: Sonnet 5.5 sub-agent, read-only. Seed 10 re-run, sight on and control, byte-identical to the committed files; then the sim probed directly. Westley's report: in the control, blue's units are attack-moved into the middle of the trap box so the vantage units do not engage; the vantage units stay put and do not come down; red starts near the exit and moves farther in, the opposite of the intent (red should start in the red walls box and move outward, and blue springs the trap when red enters the centre between the three blue forces). In the sight-on fight red shows translucent like blue, unlike the control.

## Intended setup (PROVEN from `catalogue/L-0080.toml`)

- The layout was authored by Claude, not Westley: `trap()` in `scripts/skilllab/catalogue/round3.py` at commit 016b36f0. Westley never recorded a verdict on it.
- Red (32) starts outside the pocket, south of the mouth at (2000,2900). Blue has 8 on two hills (layer 1) and an 8-unit arc at y about 3190.
- Orders are `both_same_point` to (2000,1950), inside the pocket, guard false. Every unit of both sides is attack-moved there. The runner has only layout-wide orders, so "spring the trap" cannot be expressed.

## What happens

The real fight is all 32 red against the 8-unit arc, ticks 0 to 1000. Red enters the pocket at tick 1080 and the fight freezes. The blue hill units never had a target in any sampled tick.

## Symptoms

- (a) PROVEN: the hill units' destination is (2000,1950), checked at tick 0.
- (b) PROVEN: they move but stall at the south face of the pocket's side walls, around (1550,2507) and (2550,2505), by about tick 150. A lone unit stalls at the same point on layer 0 or 1, and reaches the pocket with the walls removed. Any route needing a detour round a wall corner stalls; routes with a clear straight line work. Why the engine's route-around does not engage is UNPROVEN (needs C instrumentation). The hills are not built in the sim (a layer-1 flag only) and nothing orders a unit down.
- (c) PROVEN: this is the authored move, not a conversion bug, guard or flip. Attack-move makes red fight the arc first. Side gap: 5 reds lose their destination when the target they were chasing dies, idle at y about 3000 and never resume the attack-move, unlike SC2 (why only some units: UNPROVEN).
- (d) PROVEN: hollow means a living unit that no enemy lists in `seen` (`scenes/proto/fight_replay/fight_replay.gd:446-461`). The control file has no `seen` keys, so nothing is hollow there. In the sight-on file 8 blue hill units are hollow from tick 0 (red cannot see up); from tick 1600, 24 of 29 red are also hollow because they sit inside the pocket and the stuck blue units outside the walls cannot see them. Radius plus wall LOS recomputed for 464 pairs: 462 agree with `seen`. A correct reading of the file, not a drawing or recording bug.

## Classification

- Layout authoring: one order for everyone drives all blue into the box; the lead-in direction is opposite to what Westley describes now; the arc sits inside red's sight and range from tick 0; the hills are not real terrain.
- Runner capability: no per-group orders or triggers. The R8 reachability preflight passes a layout whose units then cannot route.
- Engine movement gaps against the SC2 model: walkers do not route round planar block corners; attack-move is not resumed after a kill for some units.
- Shared with L-0083: same `trap()` producer, same `orders_point`.
- The stage 4 README says "red is held by the walls"; it is actually the blue hill units that are stuck.

## Smallest candidate fixes (words only)

Settle the intent with Westley and redraw. Add per-group orders (hills hold, arc moves on a trigger). Stop sending blue into the pocket. File separate engine stories for corner routing and the attack-move resume, and for R8 using the engine's own planner.

## Open questions

Does red start inside the box and move out (Westley's words today), or start outside and get led in (the layout text and his 2026-11-01 verdict wording)? Does he want a "when red reaches the centre" trigger in the lab? Why does the engine report 2 of 464 pairs unseen at 772 wu when the Warden sensor is 800? What in the C code stops the corner routing?
