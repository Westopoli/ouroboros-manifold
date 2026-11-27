# L-0084 (slope): who had the firing advantage, and why blue's win was close (2026-11-27)

LAB stage 5 follow-up. Westley, 2026-11-27: "Small regression in L0084, red almost wins when blue should win easily, I'd like to understand the ratio between either side for the whole fight of which units had the firing advantage most of the time ... My theory is that blue is too far back to really take advantage of the choke, and red is clearing the choke as it's reaching the top and starting to fire, so they can spread out."

Read-only investigation by one engineer agent; seed 1, every tick. Scripts, fight files and probe layouts: `~/Projects/om-wt/engine-rules-baseline/l84/` (not in git). No tracked file was changed by it.

## Answer

Blue had the firing advantage: 700 shots to red's 364 (1.92 to 1). In the ticks where anyone fired, blue had more units firing in 60 percent, fewer in 35, equal in 5. It did not become an easy win because only blue's 12 Bombards can reach the ramp. Blue's 14 Wardens (range 350) and 14 Vanguards (range 300) stand 350 to 417 wu from the ramp's top edge and cannot reach red's firing line; red's 18 Bombards fire from that line at about 400 wu, outside their reach. The Bombard duel was 94 percent of blue's damage and 93 percent of red's, and blue lost all 28 Wardens and Vanguards.

His theory: half holds. Blue stands too far back: supported. Red clears the choke and spreads out: not supported; red's spread past the top never exceeded 140 wu against a ramp 200 wu wide, and at most 8 red units were past the top at once.

## Is it a stage 5 regression

No. The arc and the facing at spawn change nothing in this fight.

| Run | Winner | Left, blue:red | Last tick |
|---|---|---|---|
| Stage 3 record (older engine, all 20 seeds) | red | 0:6 | 2268 |
| Facing off, sight off | blue | 18:0 | 2097 |
| Facing off, sight on | blue | 12:0 | 1987 |
| Facing on, arc 360, sight on | blue | 12:0 | 1987 |
| Facing on, arc 90, sight on (the clip) | blue | 12:0 | 1987 |
| Facing on, arc 90, sight off | blue | 18:0 | 2097 |

Only the stage 4 sight rules move it (18 left to 12). Why sight costs six was not traced: blue Vanguard shots fall from 256 to 62 and red Bombard shots rise from 137 to 201. The lab has never given blue an easy win on this layout.

## Firing advantage by phase (the clip run)

| Phase | Ticks | Shots, blue:red | Blue more / fewer / equal units firing |
|---|---|---|---|
| Before red's first shot | 384 | 24:0 | 4 / 0 / 96 percent |
| Red's first shot until half of red is on the upper band | 104 | 117:21 | 51 / 8 / 41 percent |
| After that, to the end | 1499 | 559:343 | 18 / 13 / 69 percent |

Shots by role: blue 345 Bombard, 293 Warden, 62 Vanguard; red 201, 34, 129. Blue's Vanguards fired a median of 4 shots each.

## Geometry

Ramp: foot x 1700, top x 2300, 200 wu wide. A walker changes band at x 2200, and all 42 red units that fired did so from the upper band, 98 percent of red's shots from x 2200 to 2400.

| Blue role | Distance to the top edge's centre | Can reach the top edge | The ramp's middle | The foot |
|---|---|---|---|---|
| Warden, 14 | 350 to 378 | only its nearest corner | none | none |
| Vanguard, 14 | 390 to 417 | none | none | none |
| Bombard, 12 | 430 to 456 | all | all | all |

Blue holds: the largest movement of any blue unit is 32 wu. Red deaths: 26 on the ramp, 24 within 100 wu past the top, 6 beyond.

## Probes: blue's arc moved toward the ramp top (scratch copies, not catalogue layouts)

| Probe | Winner, blue left | Last tick | Shots, blue:red | Red deaths: ramp / top / beyond |
|---|---|---|---|---|
| Arc moved 120 wu closer | blue, 30 | 1927 | 1040:267 | 55 / 1 / 0 |
| Arc moved 160 wu closer | blue, 31 | 1619 | 1513:216 | 55 / 1 / 0 |
| 120 wu closer and centred across the ramp | blue, 32 | 1815 | 1246:233 | 51 / 5 / 0 |

With blue's short-range units able to reach the top 100 wu of the ramp, red dies on the ramp and blue keeps 30 to 32 of 40. The arc cannot move more than about 160 wu before its ends reach the cliff beside the ramp. The layout is his to change.

## Not done

Why the sight rules cost blue six survivors; which engine change turned the stage 3 red win into a blue win.
