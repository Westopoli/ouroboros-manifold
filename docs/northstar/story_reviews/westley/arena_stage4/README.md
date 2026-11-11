# Lab stage 4: sight (H-088), re-run 2026-11-11 on the engine with the Round 1 rule fixes

Your stage 4 pictures from 2026-11-06 were made before the engine rule fixes. This run makes them again on the engine that has them: no unit enters an obstacle (a box, wall or building cell), no unit fires on a tick it moved, a unit keeps its target until it dies, leaves sight or is out of reach, and Wardens do not stack. The fights are the same four layouts with the same settings as before (sight on, 20 seeds each, each beside the same fight with targeting by sight off, the holder of a `hold:` layout on guard). Every seed of a fight comes out the same, so a rate is 0% or 100%. Seed 10 is the seed the page shows. The page with every strip is `index.html` in this directory; its frames (`L-0061-s10/` and so on, each fight with its `-control-s10/`) sit beside it. Blue is side A, red is side B.

What changed in the outcomes against the 2026-11-06 run: L-0039 sight on was a draw at the cap (5 against 8) and is now a red win (0 against 3); L-0061 blue still wins, now with 18 left instead of 23; the two traps are still won by red, now with 25 and 35 red units left instead of 19 and 36.

## Results (seed 10; the same in every seed, from the fight files)

Winner and survivors are blue:red. "First seen" is the first sampled tick at which that side sees an enemy (blue / red); the control has none because targeting by sight is off there.

| Fight | With sight | Same fight, targeting by sight off | Your guess |
|---|---|---|---|
| Vantage L-0061 (24 against 24, blue in an arc on the hill) | Blue wins, 18:0 left, 1663 ticks. First seen: blue 0, red 120. Blue 20 of 20 seeds. | Blue wins, 18:0, 1663 ticks. | Blue 98%. |
| Trap L-0080 (16 against 32) | Red wins, 0:25 left, 1597 ticks. First seen: blue 80, red 40. Blue 0 of 20 seeds. | Red wins, 0:25, 1597 ticks. | Blue 75%. |
| Trap L-0083 (24 against 48) | Red wins, 0:35 left, 1622 ticks. First seen: blue 60, red 40. Blue 0 of 20 seeds. | Red wins, 0:35, 1622 ticks. | Blue 75%. |
| Cover L-0039 (as you drew it) | Red wins, 0:3 left, 2314 ticks. First seen: blue 60, red 80. Blue 0 of 20 seeds. | Blue wins, 2:0, 2618 ticks. | Red 75%. |

No fight stalls or ends at the cap in this run.

## What the rule checker checked

Every fight (sight on and control, all 20 seeds, 160 fight files) was checked after every tick by `scripts/skilllab/invariants.py` for: R-207-06 (no unit ends a tick inside a blocked cell), R-207-07 (inside the canvas), R-087-04 (no fire on a tick the unit moved), R-084-04 (no move in the ticks after a shot), R-087-03 (target lock), R-087-09 (a held target the unit cannot shoot and does not close in on), R-083-03 (no healing above one Warden's rate on a tick nothing hit the unit) and continuity (no jump between ticks). The thresholds in it are DRAFT constants, yours to set. R-087-03 is checked in the controls too.

| Fight | Rules reported (sight on) | Rules reported (control) |
|---|---|---|
| L-0039 | none | none |
| L-0061 | none | none |
| L-0080 | R-087-09: 2 reports a seed, first at tick 293 (unit 7, target 23, 236 wu away), then tick 310 (unit 4, target 38, 287 wu away); 20 of 20 seeds | the same, 20 of 20 seeds |
| L-0083 | R-087-09: 1 report a seed, tick 249 (unit 15, target 60, 251 wu away); R-087-03: 6 reports a seed, ticks 753 to 852 (units 53, 35, 60); 20 of 20 seeds | the same, 20 of 20 seeds |

R-087-09 (a blocked target is given up) is expected until Round 2. The R-087-03 reports on L-0083 are not: they read "target 10 -> 13 while 10 was alive and seen", six times in the fight (units 53, 35, 60), so a unit changed target while its old target was alive and seen. They are a finding for the engine, not explained here. The runner printed the `INVALID` line for each of these (120 `INVALID` lines for L-0080 and L-0083 together: one per rule, fight and seed) and the invalid fights carry `invalid: true`; the page marks each invalid row with its earliest rule only (R-087-09 on both traps; the R-087-03 reports are in the fight files' `violations`).

## Watching it

Watch one: on the Mac `scripts/replay.sh docs/northstar/research/layer_dynamics/arena/stage4/L-0061-s10.fight.json`, on Linux `OM_FIGHT=$PWD/docs/northstar/research/layer_dynamics/arena/stage4/L-0061-s10.fight.json scripts/play.sh --scene res://scenes/proto/fight_replay/fight_replay.tscn`. Space steps forward; V switches the faint sight discs between one per role and one per unit; a hollow unit is one the other side does not see. The control fight (`.../stage4/control/L-0061-control-s10.fight.json`) is the same fight with targeting by sight off.

| What to look at | Approve means | Deny means |
|---|---|---|
| Vantage, then its control | The high ground sees first and fires first, and red sees up only from the halfway line. | Red sees blue before the halfway line, or hits blue unseen; name the frame. |
| Traps, then their controls | The trap springs together and red does not see the hills until a hill force has come down. | The forces do not attack together, or red sees them first; say so. |
| Cover (as you like) | The boxes hide units. | A unit is hollow with a clear line, or fires through a box. |

## Close-up files

For L-0039 (cover, seed 10) four denser files in `closeup/`: a frame every 10 ticks (half a second; 233 frames with sight on, 263 with it off) and every 7 ticks (about a third of a second; 332 and 375 frames), with sight on and the same fight with targeting by sight off. The results are the ones in the table above. `OM_FPS` is the replay's speed in frames a second (default 1); a half-second file at `OM_FPS=2` runs in real time, at `OM_FPS=1` at half speed, and a third-of-a-second file at `OM_FPS=3` runs in real time. Space still steps by hand.

On the Mac: `OM_AUTOPLAY=1 OM_FPS=2 scripts/replay.sh docs/northstar/story_reviews/westley/arena_stage4/closeup/L-0039-s10-every10.fight.json`. On Linux: `OM_AUTOPLAY=1 OM_FPS=2 OM_FIGHT=$PWD/docs/northstar/story_reviews/westley/arena_stage4/closeup/L-0039-s10-every10.fight.json scripts/play.sh --scene res://scenes/proto/fight_replay/fight_replay.tscn`. The files are `L-0039-s10-every10`, `L-0039-s10-every7`, `L-0039-control-s10-every10` and `L-0039-control-s10-every7` (`.fight.json`); use `OM_FPS=3` for the `every7` ones.

To make another: `python3 -m scripts.skilllab.arena.closeup --layout docs/northstar/research/layer_dynamics/catalogue/L-0039.toml --seed 10 --sight on --every-ticks 10 --out <dir>` (`--sight control` for the sight-off twin; `--from-tick A --to-tick B` keeps only that stretch).
