# Two things to watch: units standing inside each other, and why red wins the trap

Everything here opens in the lab's fight replay. You decide; nothing below is a verdict.

## How to open a file

From the top folder of the repository (the one that holds `scripts/` and `docs/`):

On the Mac, or on Linux:

```
scripts/replay.sh docs/northstar/story_reviews/westley/look_2026-11-19/A1-stacked-pair-near.fight.json
```

On Linux the way the earlier stage pictures were opened:

```
OM_FIGHT=$PWD/docs/northstar/story_reviews/westley/look_2026-11-19/A1-stacked-pair-near.fight.json scripts/play.sh --scene res://scenes/proto/fight_replay/fight_replay.tscn
```

(Swap the file name for any file below. `play.sh` plays the newest main, `replay.sh` plays the folder you stand in; use `replay.sh` if you are on the branch `s/overlap-look` and main does not hold this folder yet.)

To let it run by itself, put `OM_AUTOPLAY=1 OM_FPS=<frames a second>` in front of the command, for example

```
OM_AUTOPLAY=1 OM_FPS=4 scripts/replay.sh docs/northstar/story_reviews/westley/look_2026-11-19/B1-trap-L0080-whole-fight-every5.fight.json
```

### What the replay can do and cannot do

Can:

- **Space** or **Right arrow**: one frame forward. **Left arrow**: one frame back.
- **Mouse wheel**: zoom. **W A S D** (the arrow keys too): move the picture. Keep the mouse pointer away from the window edge, it also moves the picture there. The Left arrow steps back and also nudges the picture; press D to nudge it back.
- Top left: `tick N`, how many are alive on each side, and `frame i/total`. The tick is the one to go by.
- Blue is side A, red is side B. Blue is on the left, red on the right; the top of the picture is the small-y end of the field (the field is 4,000 wide and 4,000 tall).
- A thin line from a unit to its target shows while the unit fires. A grey flat unit is dead. The little white tick on each unit shows which way it faces. A unit that has been held still by the ground for two seconds wears an orange ring (the two trap fights only). `R` draws a range ring on every unit, `V` the sight circles (trap fights only).
- A big circle follows one unit on each side: that is the weapon-range ring of the role, ignore it.

Cannot:

- It cannot show unit numbers and cannot highlight a unit.
- It cannot jump to a tick or start at a chosen tick, and it cannot pause an autoplay. A file starts at its first frame, and you reach the moment you want by pressing Space; the table for each file says how many frames in it is.
- Colour and shape are all you get to tell units apart. So in the three overlap examples, **the units I name are drawn with a different shape than they really have** (every unit in the open fight is a square Vanguard): a circle or a hexagon. Nothing else was changed. Positions, ticks and movement are exactly what the engine did.

## A. Units standing inside each other (the open fight, 128 against 128, sight off, seed 1)

The rule is that no two units stand closer than 30 apart (a unit is 30 wide). In this fight about 145 pairs of the same side stand closer than 28 for more than 3 ticks. Measured on my own recording of the same fight (a frame every tick): the closest is 0.3 apart for 15 ticks. Three kinds stand out, one example each. Each has two files:

- `...-near`: only the units within 200 to 220 of the pair are in the picture, so the picture is zoomed on them. The other units of the fight are simply left out of the file. Use this one first.
- `...-whole-crowd`: the whole crowd of both sides, so you can see where the pair is.

In both, a frame counts the same number of ticks (written below).

The numbers below are positions on the field (x grows to the right, y grows downwards). Blue's block is about 250 wide and 800 tall, standing at the left, facing right; red's block mirrors it on the right.

### A1. The nearly stacked pair

- Files: `A1-stacked-pair-near.fight.json` (a frame every tick, ticks 1300 to 1500, frame number = tick minus 1300) and `A1-stacked-pair-whole-crowd.fight.json` (a frame every 2 ticks, same stretch, frame number = (tick minus 1300) divided by 2).
- Units: blue unit **82** stands still at (1795, 2208) and is drawn as a **hexagon**. Blue unit **120** walks up to it and is drawn as a **circle**. They are on the lower edge of blue's block, in its front half (lower third, right of the middle of the block).
- Go to tick **1382** (frame 82 of the near file, 41 of the crowd file), then press Space once a frame. Unit 120 walks in from the left, from (1771, 2226).
- Watch: at tick 1388 (frame 88) the two are 6.3 apart, at 1391 they are 2.5 apart, and at **tick 1396 (frame 96)** they are 0.3 apart, one glyph hiding the other. A tick later (frame 97) unit 120 is gone 72 to the east, at (1867, 2205).

### A2. The unit stuck behind the firing line

- Files: `A2-wedged-second-rank-near.fight.json` and `A2-wedged-second-rank-whole-crowd.fight.json` (both a frame every 2 ticks, ticks 380 to 640, frame number = (tick minus 380) divided by 2).
- Units: blue unit **20**, a **circle**, at (1832, 2041). In front of it, standing and shooting, blue units **7** and **8**, both **hexagons**, at (1852, 2020) and (1852, 2060). That is the middle of blue's front, just behind its first line.
- Go to tick **430** (frame 25). Unit 20 has crept up to the gap between 7 and 8 from tick 426 (frame 23); the gap is 40 wide between centres and a unit needs 30, so it sits about 27 from each, about 3 inside both.
- Watch: from tick 430 on nothing changes: the three stand there, 20 jammed in the gap behind the line, to tick 640 at the end of the file. In the full fight it stays until tick 1527, about 1,100 ticks.

### A3. The idle unit squeezed between two friends

- Files: `A3-idle-between-walkers-near.fight.json` and `A3-idle-between-walkers-whole-crowd.fight.json` (both a frame every 2 ticks, ticks 2440 to 2740, frame number = (tick minus 2440) divided by 2).
- Units: blue unit **118**, standing without a target, drawn as a **hexagon**, at (1782, 2128). Beside it blue units **81** at (1787, 2115) and **93** at (1801, 2141), both **circles**. They still carry an order to walk but do not move at all in this stretch. This is in the middle of blue's block, a little in front of the centre line, a little below it.
- Go to tick **2480** (frame 20). Unit 118 is at (1774, 2136) and 25 from unit 81.
- Watch: between tick 2480 and 2492 (frames 20 to 26) unit 118 shifts into the middle of the two and ends 13.7 from unit 81 and 23.4 from unit 93, nearly half a body inside 81. It stays that way until tick 2728, about 250 ticks.

### A4. The trap fight that has pairs close inside the red crowd

- File: `A4-trap-L0083-close-pairs.fight.json` (the trap L-0083, sight on, seed 10; a frame every tick, ticks 740 to 960, frame number = tick minus 740; the whole field, 72 units; this one shows the orange rings and `V` the sight circles).
- Units: red units **47** (a **circle**) and **71** (a **hexagon**), two Raiders walking through each other in the red crowd, near (2042, 2758), the upper quarter of the red crowd and in the middle sideways.
- Go to tick **825** (frame 85).
- Watch: at tick 828 they are 9.5 apart, at **tick 829 (frame 89)** only 3.4 apart, at 832 apart again. The same crowd has more shallow overlaps around ticks 835 to 865: red units 35 and 60 come as close as 7.1 (tick 859), and 48 and 71 as close as 7.7 (tick 832).

A4 is the walking kind: two walkers pass through each other for a few ticks. The long ones, the ones that stay for seconds, are A2 and A3.

## B. Why red wins the trap (L-0080, sight on, seed 1)

You expected blue to win. Red wins with 25 of 32 left at tick 1540.

Files (both of the whole field, 48 units):

- `B1-trap-L0080-whole-fight-every5.fight.json`: the whole fight, a frame every 5 ticks (309 frames, frame number = tick divided by 5).
- `B2-trap-L0080-ticks100-1000-every2.fight.json`: ticks 100 to 1000, a frame every 2 ticks (451 frames, frame number = (tick minus 100) divided by 2).

The picture. The walled pocket is at the upper middle: walls left and right (about x 1600 and 2400) and across the top, open at the bottom, the mouth at about y 2800. Red (32) starts inside it. The meeting point the trap watches is at (2000, 2898), just below the mouth. Blue has three groups: **hill west** (4 units on the hill at (1150, 2750), left), **hill east** (4 units on the hill at (2850, 2750), right), and the **low arc** (8 units on the flat ground at (2000, 3195), below the mouth). Each side got one order at the start: red walks to the meeting point; the blue groups hold until the trap springs.

What to watch, in time order (B1 frame in brackets; in B2 the frame is (tick minus 100) divided by 2):

| Tick | Where to look | What happens |
|---|---|---|
| 0 (0) | upper middle and the three blue groups | 32 red packed in the pocket (centre at (2006, 1966)), blue waiting in three groups. |
| 40 and 100 | whole field | Red first sees a blue unit at tick 40; blue first sees red at tick 100. Nobody moves for it. |
| 101 (20) | pocket | Red is walking down the pocket; centre (2022, 2355). Still inside the walls. |
| **131 (26)** | the pocket mouth | **The trap springs.** The first red unit is within 300 of the meeting point; red's centre (2022, 2473) is still 426 from it. All three blue groups are released and start walking toward red. |
| 164 (33) | below the mouth | The low arc fires first. It has walked up to (2000, 3074) by tick 180. It meets red alone, the hills are still on their way. |
| 200 to 240 (40 to 48) | left and right of the mouth | The hill groups come in along the flat at y 2750: hill west from x 1150 to 1520, hill east from 2850 to 2510. Hill east fires at 223, hill west at 239. |
| about 290 (58) | left and right of the mouth | **Each hill group stops** at (1564, 2742) and (2505, 2758): red's first units are within their reach there, about 450 from red's centre (2016, 2793). They fire at red's fringe from there and do not come closer. |
| 300 to 900 (60 to 180) | the whole fight | A long exchange. Red never fires at a unit on a hill: its shots go to the low arc. Red goes 32 to 27, the arc 8 to 1: 8 until tick 470, 6 at 500, 5 at 600, 4 at 660, 3 at 820, 1 at 860. |
| 932 (186) | below the mouth | **The low arc is dead.** |
| about 940 to 980 (188 to 196) | left and right of the mouth | The hill groups walk down from the hills toward red now that nothing else is in the fight. |
| 1001 (200) | the meeting point | Red's centre has reached (1999, 2897); the hill groups are close, at (1731, 2769) and (2302, 2810). 27 red, 8 blue. |
| 1101 (220) | the meeting point | Hills at (1853, 2822) and (2210, 2896), a few hundred from red, close combat. 25 red. |
| 1201 to 1501 (240 to 300) | the meeting point | Hill units fall one by one: east 3 at tick 1201, 2 at 1401, 1 at 1501; west 2 at 1301, 1 at 1401. |
| 1492 (298) | left of the meeting point | **Hill west is dead.** |
| 1540 (308) | the meeting point | **Hill east is dead.** 25 red left. |

The numbers behind it, measured on this recording:

- Damage dealt: blue 3,260 in all (hill west 1,106, hill east 764, the arc 1,390); red 7,281.
- Strength: blue about 71 damage a second and 7,000 hit points together; red about 252 a second and 11,500. One red Raider deals 11.3 a second, one blue Warden 2.7.
- The three blue groups never fight together: the arc fights alone from tick 164 to 932, and the hills only walk in after that.

## Files

| File | Frames | Size |
|---|---|---|
| `A1-stacked-pair-near.fight.json` | 201 (every tick) | 1.8 MB |
| `A1-stacked-pair-whole-crowd.fight.json` | 101 (every 2 ticks) | 3.5 MB |
| `A2-wedged-second-rank-near.fight.json` | 131 (every 2 ticks) | 1.5 MB |
| `A2-wedged-second-rank-whole-crowd.fight.json` | 131 (every 2 ticks) | 4.5 MB |
| `A3-idle-between-walkers-near.fight.json` | 151 (every 2 ticks) | 1.5 MB |
| `A3-idle-between-walkers-whole-crowd.fight.json` | 151 (every 2 ticks) | 5.2 MB |
| `A4-trap-L0083-close-pairs.fight.json` | 221 (every tick) | 2.7 MB |
| `B1-trap-L0080-whole-fight-every5.fight.json` | 309 (every 5 ticks) | 2.4 MB |
| `B2-trap-L0080-ticks100-1000-every2.fight.json` | 451 (every 2 ticks) | 3.7 MB |

Every file was loaded in the replay once and wrote all its frames. The files of the open fight (A1 to A3) and of L-0083 (A4) are stretches of a longer fight; their last frame says `end: window` and `winner -`, which is not the fight's result. B1 is the whole fight and ends `end: B wins (wipe)`.

To make another stretch: `python -m scripts.skilllab.arena.closeup --layout docs/northstar/research/layer_dynamics/catalogue/L-0054.toml --seed 1 --sight off --every-ticks 2 --from-tick 380 --to-tick 640 --out <folder>` (this makes the plain file: no shapes changed, every unit in it, and the fight is run to its end first, which takes a few minutes and a lot of memory at every tick).
