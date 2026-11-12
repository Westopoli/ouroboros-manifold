# Lab stage 4: sight (H-088), re-run 2026-11-11 on the engine with both rounds of rule fixes

Your stage 4 pictures from 2026-11-06 were made before the engine rule fixes. This run makes them again on the engine that has both rounds of them. Round 1: no unit ends a tick inside an obstacle (a box, wall or building cell); no unit fires on a tick it moved; a unit keeps its target until it dies, leaves sight or is out of reach (the target lock, which includes a unit that halts to fire keeping its lock); Wardens do not stack. Round 2: a unit whose line to its target is blocked looks for a firing spot and gives the target up after 1 second; a guard steps toward an enemy it sees within 200 wu of its post and returns; the high ground can fire down, so sight and fire agree on hills; weapon reach on the ground includes the height difference (between two walking units; a flyer is measured flat); a unit changing layer no longer jumps; an attack-moving unit hit by something it cannot see moves 200 wu away.

The fights are the same four layouts with the same settings as before (sight on, 20 seeds each, each beside the same fight with targeting by sight off, the holder of a `hold:` layout on guard). Every seed of a fight comes out the same, so a rate is 0% or 100%. Seed 10 is the seed the page shows. The page with every strip is `index.html` in this directory; its frames (`L-0061-s10/` and so on, each fight with its `-control-s10/`) sit beside it. Blue is side A, red is side B.

Against the Round 1 run made earlier today (main, before Round 2) the winners are the same and the fights are longer, except L-0039: L-0061 blue wins with 19 left in 2234 ticks (was 18 left, 1693), first seen by red at tick 80 (was 120); L-0080 red wins with 22 left in 2365 ticks (was 24 left, 1934); L-0083 red wins with 30 left in 2839 ticks (was 32 left, 1998); L-0039 with sight on is unchanged (red, 3 left, 2314 ticks) and so is its control (blue with 2 left, 2858 ticks). Against 2026-11-06: L-0039 sight on was a draw at the cap (5 against 8) and is a red win; L-0061 blue left 23 then, 19 now; the traps left 19 and 36 red units then, 22 and 30 now.

## Results (seed 10; the same in every seed, from the fight files)

Winner and survivors are blue:red. "First seen" is the first sampled tick at which that side sees an enemy (blue / red); the control has none because targeting by sight is off there.

| Fight | With sight | Same fight, targeting by sight off | Your guess |
|---|---|---|---|
| Vantage L-0061 (24 against 24, blue in an arc on the hill) | Blue wins, 19:0 left, 2234 ticks. First seen: blue 0, red 80. Blue 20 of 20 seeds. | Blue wins, 19:0, 2234 ticks. | Blue 98%. |
| Trap L-0080 (16 against 32) | Red wins, 0:22 left, 2365 ticks. First seen: blue 80, red 40. Blue 0 of 20 seeds. | Red wins, 0:22, 2365 ticks. | Blue 75%. |
| Trap L-0083 (24 against 48) | Red wins, 0:30 left, 2839 ticks. First seen: blue 60, red 40. Blue 0 of 20 seeds. | Red wins, 0:30, 2839 ticks. | Blue 75%. |
| Cover L-0039 (as you drew it) | Red wins, 0:3 left, 2314 ticks. First seen: blue 60, red 80. Blue 0 of 20 seeds. | Blue wins, 2:0, 2858 ticks. | Red 75%. |

No fight stalls or ends at the cap in this run; every one ends with a side wiped out.

## What the rule checker checked

Every fight (sight on and control, all 20 seeds, 160 fight files) was checked after every tick by `scripts/skilllab/invariants.py`. It judges eleven rules: R-207-06 (no unit ends a tick inside a blocked cell), R-207-07 (inside the canvas), R-087-04 (no fire on a tick the unit moved), R-084-04 (no move in the ticks after a shot), R-087-03 (target lock and acquisition: the nearest seen enemy, at the unit's turn), R-087-09 (a held target the unit cannot shoot and does not close in on, within attack range), R-083-03 (no healing above one Warden's rate on a tick nothing hit the unit), continuity (no jump between ticks, which is where a layer-change jump would show), R-093-02 (fire only at what the side saw in the previous frame), R-096-08 (a guard stays inside its 200 wu leash) and R-087-10 (a shot is within spherical weapon reach). The thresholds in it are DRAFT constants, yours to set.

| Fight | Judged and suspended (sight on) | Judged and suspended (control) | Rules reported |
|---|---|---|---|
| L-0039 | all eleven judged; none suspended | nine judged; R-087-03 and R-093-02 suspended | none, sight on or control |
| L-0061 | the same | the same | none, sight on or control |
| L-0080 | the same | the same | none, sight on or control |
| L-0083 | the same | the same | none, sight on or control |

The control suspends the two sight rules, R-087-03 and R-093-02, because targeting by sight is off there (switch `OM_TP_TARGET_BY_SIGHT`) and the checker has nothing to judge them against. The runner printed no `INVALID` line and no fight file carries `invalid: true`; it printed eight `SUSPENDED` lines (the two rules above, one pair for each of the four controls). The two traps, which the Round 1 run reported on R-087-09 (a blocked target is given up), now report nothing.

## Still open, and visible in these fights

- Units pick the nearest enemy they see and keep that lock even when another enemy walks closer.
- Units walk toward enemies beyond weapon range.

Both wait on your answer to the StarCraft 2 report, `docs/reports/2026-11-11-starcraft2-movement-targeting.md`. Both traps are still won by red.

## Watching it

Watch one: on the Mac `scripts/replay.sh docs/northstar/research/layer_dynamics/arena/stage4/L-0061-s10.fight.json`, on Linux `OM_FIGHT=$PWD/docs/northstar/research/layer_dynamics/arena/stage4/L-0061-s10.fight.json scripts/play.sh --scene res://scenes/proto/fight_replay/fight_replay.tscn`. Space steps forward; V switches the faint sight discs between one per role and one per unit; a hollow unit is one the other side does not see. The control fight (`.../stage4/control/L-0061-control-s10.fight.json`) is the same fight with targeting by sight off.

| What to look at | Approve means | Deny means |
|---|---|---|
| Vantage, then its control | The high ground sees first and fires first, and red sees up only from the halfway line. | Red sees blue before the halfway line, or hits blue unseen; name the frame. |
| Traps, then their controls | The trap springs together and red does not see the hills until a hill force has come down. | The forces do not attack together, or red sees them first; say so. |
| Cover (as you like) | The boxes hide units. | A unit is hollow with a clear line, or fires through a box. |

## Close-up files

For L-0039 (cover, seed 10) four denser files in `closeup/`: a frame every 10 ticks (half a second; 233 frames with sight on, 287 with it off) and every 7 ticks (about a third of a second; 332 and 410 frames), with sight on and the same fight with targeting by sight off. The results are the ones in the table above. `OM_FPS` is the replay's speed in frames a second (default 1); a half-second file at `OM_FPS=2` runs in real time, at `OM_FPS=1` at half speed, and a third-of-a-second file at `OM_FPS=3` runs in real time. Space still steps by hand.

On the Mac: `OM_AUTOPLAY=1 OM_FPS=2 scripts/replay.sh docs/northstar/story_reviews/westley/arena_stage4/closeup/L-0039-s10-every10.fight.json`. On Linux: `OM_AUTOPLAY=1 OM_FPS=2 OM_FIGHT=$PWD/docs/northstar/story_reviews/westley/arena_stage4/closeup/L-0039-s10-every10.fight.json scripts/play.sh --scene res://scenes/proto/fight_replay/fight_replay.tscn`. The files are `L-0039-s10-every10`, `L-0039-s10-every7`, `L-0039-control-s10-every10` and `L-0039-control-s10-every7` (`.fight.json`); use `OM_FPS=3` for the `every7` ones.

To make another: `python3 -m scripts.skilllab.arena.closeup --layout docs/northstar/research/layer_dynamics/catalogue/L-0039.toml --seed 10 --sight on --every-ticks 10 --out <dir>` (`--sight control` for the sight-off twin; `--from-tick A --to-tick B` keeps only that stretch).
