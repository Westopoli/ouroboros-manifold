# Lab stage 4: sight (H-088), re-run 2026-11-17 on the engine with five rounds of rule fixes

Your stage 4 pictures from 2026-11-06 were made before the engine rule fixes. This run makes them again on the engine that has all five rounds of them. Round 1: no unit ends a tick inside an obstacle (a box, wall or building cell); no unit fires on a tick it moved; a unit keeps its target until it dies, leaves sight or is out of reach (the target lock, which includes a unit that halts to fire keeping its lock); Wardens do not stack. Round 2: a unit whose line to its target is blocked looks for a firing spot and gives the target up after 1 second; a guard steps toward an enemy it sees within 200 wu of its post and returns; the high ground can fire down, so sight and fire agree on hills; weapon reach on the ground includes the height difference (between two walking units; a flyer is measured flat); a unit changing layer no longer jumps; an attack-moving unit hit by something it cannot see moves 200 wu away. Round 3: a unit's lock is judged against its side's sight once per tick before anything moves (before, a unit could lose a target a tick early or keep it a tick late); a unit that picks a target just out of range during the pause after its own shot now walks to it (before, it stood until it gave the target up); a unit moving away from fire it cannot see is no longer stopped halfway by its own return order. Round 4: an idle unit steps aside for a moving unit of its own side (before, the mover was pushed back and stood still for the rest of the fight). Round 5: a unit notices an enemy only within its weapon range plus a tenth (before, it noticed anything its side saw within its leash); it drops a target that leaves that distance (a target that shot it is kept until the lock ends some other way); a unit on guard does the same and follows no farther than 200 wu from its post; a unit attack-moving somewhere is not stopped by fire it cannot see; units on one ramp bump each other, whichever side of the ramp's middle line each stands on.

The fights are the same four layouts with the same settings as before (sight on, 20 seeds each, each beside the same fight with targeting by sight off, the holder of a `hold:` layout on guard). Every seed of a fight comes out the same, so a rate is 0% or 100%. Seed 10 is the seed the page shows. The page with every strip is `index.html` in this directory; its frames (`L-0061-s10/` and so on, each fight with its `-control-s10/`) sit beside it. Blue is side A, red is side B.

Against the Round 4 run made on 2026-11-12 the winners are the same in three fights and different in one. L-0039 with sight on is now a blue win with 3 left in 2213 ticks (was a red win, 3 left, 2314 ticks), and its control is still a blue win, 4 left in 2102 ticks (was 2 left, 2730). L-0061 is still a blue win, 23 left in 1415 ticks (was 18 left, 2136), first seen by red at tick 120 (was 80). The traps are still red wins: L-0080 with 23 left in 1844 ticks (was 26 left, 1726), L-0083 with 38 left in 2332 ticks (was 40 left, 1728).

## Results (seed 10; the same in every seed, from the fight files)

Winner and survivors are blue:red. "First seen" is the first sampled tick at which that side sees an enemy (blue / red); the control has none because targeting by sight is off there.

| Fight | With sight | Same fight, targeting by sight off | Your guess |
|---|---|---|---|
| Vantage L-0061 (24 against 24, blue in an arc on the hill) | Blue wins, 23:0 left, 1415 ticks. First seen: blue 0, red 120. Blue 20 of 20 seeds. | Blue wins, 23:0, 1415 ticks. | Blue 98%. |
| Trap L-0080 (16 against 32) | Red wins, 0:23 left, 1844 ticks. First seen: blue 100, red 40. Blue 0 of 20 seeds. | Red wins, 0:23, 1844 ticks. | Blue 75%. |
| Trap L-0083 (24 against 48) | Red wins, 0:38 left, 2332 ticks. First seen: blue 80, red 40. Blue 0 of 20 seeds. The checker reports a rule here (below). | Red wins, 0:38, 2332 ticks. The same report. | Blue 75%. |
| Cover L-0039 (as you drew it) | Blue wins, 3:0 left, 2213 ticks. First seen: blue 60, red 100. Blue 20 of 20 seeds. | Blue wins, 4:0, 2102 ticks. | Red 75%. |

No fight stalls or ends at the cap in this run; every one ends with a side wiped out.

## What the rule checker checked

Every fight (sight on and control, all 20 seeds, 160 fight files) was checked after every tick by `scripts/skilllab/invariants.py`. It now judges thirteen rules: R-207-06 (no unit ends a tick inside a blocked cell), R-207-07 (inside the canvas), R-087-04 (no fire on a tick the unit moved; a unit notices an enemy only within weapon range plus a tenth), R-084-04 (no move in the ticks after a shot), R-087-03 (target lock and acquisition: the nearest seen enemy, at the unit's turn, and no pick or kept lock beyond the notice distance), R-087-09 (a held target the unit cannot shoot and does not close in on, within attack range), R-083-03 (no healing above one Warden's rate on a tick nothing hit the unit), continuity (no jump between ticks, which is where a layer-change jump would show), R-093-02 (fire only at what the side saw in the previous frame), R-096-08 (a guard stays inside its 200 wu leash), R-087-10 (a shot is within spherical weapon reach), and two new in Round 5: R-087-01 (an attack-moving unit is not stopped by fire it cannot see; a unit moves away from unseen fire once per hit) and R-097-05 (two units on one ramp stand apart by 30 wu within a few ticks of meeting). The thresholds in it are DRAFT constants, yours to set.

| Fight | Judged and suspended (sight on) | Judged and suspended (control) | Rules reported |
|---|---|---|---|
| L-0039 | all thirteen judged; none suspended | eleven judged; R-087-03 and R-093-02 suspended | none, sight on or control |
| L-0061 | the same | the same | none, sight on or control |
| L-0080 | the same | the same | none, sight on or control |
| L-0083 | the same | the same | R-097-05 in every seed, sight on and control: one report a fight (40 fights, 40 reports) |

The control suspends the two sight rules, R-087-03 and R-093-02, because targeting by sight is off there (switch `OM_TP_TARGET_BY_SIGHT`) and the checker has nothing to judge them against. The runner printed eight `SUSPENDED` lines (the two rules above, one pair for each of the four controls) and forty `INVALID` lines, all the same: `INVALID L-0083 R-097-05 tick 1735 unit 2` (twenty, sight on) and `INVALID L-0083-control R-097-05 tick 1735 unit 2` (twenty, control). The 40 L-0083 fight files carry `invalid: true`, and the page shows L-0083 as "invalid, not ranked". The report reads: units 2 and 4 stand 18.3 wu apart on one slope (on layers 1 and 0), under 30 wu after the collision pass. It is the same in every seed because every seed of a fight comes out the same. Every other count of rules reported is zero, in every fight, sight on and control.

## Still open, and visible in these fights

- Units 2 and 4 of L-0083 stand 18.3 wu apart on one ramp at tick 1735: the ramp bump of this round does not part them. The Round 5 spec notes that L-0083 has two overlapping hill records that give opposite layers at one point, which looks like a defect in the layout; it waits on your word.
- A unit moving away from fire that is blocked by a standing friend that does not yield (a guard) presses against it, and the move away never ends.
- A unit chasing a target that walks away never fires at it, however slowly it walks: it stops at exactly its range, may not fire on a tick it moved, and the target is out of range again the next tick.
- Inside one tick the engine moves units one by one, so a unit reads some enemies at this tick's position and some at the last tick's; the side with the higher unit ids sees its enemies one step fresher. This is older than this round and is not changed.

Both traps are still won by red.

## Watching it

Watch one: on the Mac `scripts/replay.sh docs/northstar/research/layer_dynamics/arena/stage4/L-0061-s10.fight.json`, on Linux `OM_FIGHT=$PWD/docs/northstar/research/layer_dynamics/arena/stage4/L-0061-s10.fight.json scripts/play.sh --scene res://scenes/proto/fight_replay/fight_replay.tscn`. Space steps forward; V switches the faint sight discs between one per role and one per unit; a hollow unit is one the other side does not see. The control fight (`.../stage4/control/L-0061-control-s10.fight.json`) is the same fight with targeting by sight off.

| What to look at | Approve means | Deny means |
|---|---|---|
| Vantage, then its control | The high ground sees first and fires first, and red sees up only from the halfway line. | Red sees blue before the halfway line, or hits blue unseen; name the frame. |
| Traps, then their controls | The trap springs together and red does not see the hills until a hill force has come down. | The forces do not attack together, or red sees them first; say so. |
| Cover (as you like) | The boxes hide units. | A unit is hollow with a clear line, or fires through a box. |

## Close-up files

For L-0039 (cover, seed 10) four denser files in `closeup/`: a frame every 10 ticks (half a second; 223 frames with sight on, 212 with it off) and every 7 ticks (about a third of a second; 318 and 302 frames), with sight on and the same fight with targeting by sight off. The results are the ones in the table above. `OM_FPS` is the replay's speed in frames a second (default 1); a half-second file at `OM_FPS=2` runs in real time, at `OM_FPS=1` at half speed, and a third-of-a-second file at `OM_FPS=3` runs in real time. Space still steps by hand.

On the Mac: `OM_AUTOPLAY=1 OM_FPS=2 scripts/replay.sh docs/northstar/story_reviews/westley/arena_stage4/closeup/L-0039-s10-every10.fight.json`. On Linux: `OM_AUTOPLAY=1 OM_FPS=2 OM_FIGHT=$PWD/docs/northstar/story_reviews/westley/arena_stage4/closeup/L-0039-s10-every10.fight.json scripts/play.sh --scene res://scenes/proto/fight_replay/fight_replay.tscn`. The files are `L-0039-s10-every10`, `L-0039-s10-every7`, `L-0039-control-s10-every10` and `L-0039-control-s10-every7` (`.fight.json`); use `OM_FPS=3` for the `every7` ones.

To make another: `python3 -m scripts.skilllab.arena.closeup --layout docs/northstar/research/layer_dynamics/catalogue/L-0039.toml --seed 10 --sight on --every-ticks 10 --out <dir>` (`--sight control` for the sight-off twin; `--from-tick A --to-tick B` keeps only that stretch).
