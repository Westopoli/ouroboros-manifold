# I1: is the target the nearest one? L-0039 seed 10, engine-rules Round 1 tip (94c2fb5d)

Measured, not read. Script `nearest_run.py` runs `arena.run.fight` for `L-0039` seed 10 with `Engine.step` wrapped to record every tick (positions, hp, target, the side's seen set, fire events); `nearest_analyse.py` and `nearest_report.py` derive everything below from that trace. Runs: **on** = `fight(..., 'on')` (targeting by sight, the stage 4 rule set), **control** = `fight(..., 'control')` (same, `OM_TP_TARGET_BY_SIGHT` 0). Both are the `--sight on` / `--control sight` setups of `arena/run.py`. Side A is blue, side B is red. Ticks are 1-indexed step numbers; 'state at tick t' is the state before step t.

**Distance.** Planar hypot(dx, dy), the engine's metric today. Every unit stayed on layer 0 for the whole of both runs (checked on all 2314 + 2618 ticks), so spherical (R-087-10) would give the same numbers.

**Eligible set (measured, not assumed).** Alive enemy, within the reach rule (0 up, 1 down, immaterial here), within `max(sensor_radius, attack_range)` of the unit, and (on only) in the side's seen set (`om_player_can_see`) at the state before the step. The wider 'sensor radius only' set does not fit the engine: Bombards (sensor 300, range 1200) and Bastions (sensor 300, range 800) acquire at up to about 1000 wu. In the on run 30 of 61 acquisitions are farther than the unit's own sensor radius (21 Bombard, 6 Bastion, 3 Vanguard return-fire); in the control run 34 of 65. R-087-04 says 'within its sensor radius'; the engine reaches to the attack range as well (reported, not judged). Control run: no sight condition (sight off for targeting). 'NEAREST' = the chosen enemy is in the set and within 1 wu of the nearest member. The raw nearest (any living enemy) is also kept; for every shot the two agree.

**Cohort.** Acquisition tick mod 4 equals (unit id + 3) mod 4 (measured from the data). All on-cohort acquisitions (57 in on, 62 in control) were NEAREST; every off-cohort acquisition (4 in on, 3 in control) was return fire.

## 1. Acquisitions (target field goes from none or another id to an id)

Classes, in this order of precedence: NEAREST; RETURN-FIRE (R-087-06: unit had no target, the chosen enemy damaged it, directly or by splash, in the 4 ticks up to and including the acquisition tick; damage and shots read from the fire events and hp drops, every hp drop in both runs is attributed); TIMING (chosen was nearest in the post-step state, or in any state 1 to 5 ticks old, or with sight from an older tick: a cohort delay would show here); LOWEST-HP (chosen has the lowest hp of the eligible set); UNEXPLAINED. Classes TIMING and LOWEST-HP and UNEXPLAINED are empty in both runs.

| run | side | total | NEAREST | NOT-NEAREST: RETURN-FIRE | cohort delay (TIMING) | most-damaged / policy | eligibility difference | UNEXPLAINED |
|---|---|---|---|---|---|---|---|---|
| on | blue (A) | 16 | 13 | 3 | 0 | 0 | 0 | 0 |
| on | red (B) | 45 | 42 | 3 | 0 | 0 | 0 | 0 |
| on | both | 61 | 55 | 6 | 0 | 0 | 0 | 0 |
| control | blue (A) | 28 | 24 | 4 | 0 | 0 | 0 | 0 |
| control | red (B) | 37 | 37 | 0 | 0 | 0 | 0 | 0 |
| control | both | 65 | 61 | 4 | 0 | 0 | 0 | 0 |

('Eligibility difference' is 0 by construction of the table: the eligible set above is the one the data fitted; unit-level `can_see` / `can_shoot` sets fit worse, 28 of 61 against 55.)

Fresh target from none vs switch from another id (a switch is also an acquisition):

| run | none to id | id to id | of the switches: old target dead | old target alive, lock ended by the leash (R-087-05) | old target alive and nearer-chosen (lock broken) |
|---|---|---|---|---|---|
| on | 53 | 8 | 8 | 0 | 0 |
| control | 51 | 14 | 12 | 2 | 0 |

The two leash switches (control run, blue Vanguards 2 at tick 165 and 1 at tick 176) are worked example 3. Their old target was alive and seen; the unit had walked about 700 wu (its own sensor radius, R-087-05) and dropped the lock. The anchor point is not in my data, so 'about 700' is 697 wu from the unit's position at the acquisition step and 724 wu from its start. No switch in either run happened while the old target was alive, seen and the unit within its leash.

RETURN-FIRE acquisitions, all of them (chosen, nearest eligible, raw nearest, the hit that explains it):

| run | tick | unit | role | side | chosen at wu | nearest eligible at wu | raw nearest at wu | chosen in unit's set | hit by chosen |
|---|---|---|---|---|---|---|---|---|---|
| on | 82 | 3 | Vanguard | blue (A) | 10: 773 | none in range | 11: 749 | no (beyond its sensor and attack range) | tick 81, direct |
| on | 83 | 1 | Vanguard | blue (A) | 15: 882 | none in range | 9: 800 | no (beyond its sensor and attack range) | tick 82, splash |
| on | 83 | 2 | Vanguard | blue (A) | 15: 923 | none in range | 9: 841 | no (beyond its sensor and attack range) | tick 82, splash |
| on | 1880 | 9 | Bastion | red (B) | 8: 299 | 7: 293 | 7: 293 | yes | tick 1879, direct |
| on | 1880 | 10 | Bastion | red (B) | 8: 325 | 7: 305 | 7: 305 | yes | tick 1879, splash |
| on | 1880 | 15 | Bombard | red (B) | 8: 418 | 7: 410 | 7: 410 | yes | tick 1879, splash |
| control | 15 | 1 | Vanguard | blue (A) | 15: 1192 | none in range | 11: 1107 | no (beyond its sensor and attack range) | tick 14, splash |
| control | 15 | 2 | Vanguard | blue (A) | 15: 1200 | none in range | 11: 1117 | no (beyond its sensor and attack range) | tick 14, splash |
| control | 15 | 3 | Vanguard | blue (A) | 15: 1190 | none in range | 9: 1108 | no (beyond its sensor and attack range) | tick 14, direct |
| control | 1484 | 5 | Interceptor | blue (A) | 16: 381 | 9: 228 | 9: 228 | yes | tick 1483, direct |

## 2. Shots (every fire event)

'Not at nearest' = the target is more than 1 wu farther than the nearest eligible enemy at the state before the shot step. Lock age = ticks since the acquisition that set this target. In both runs every shot was at the held target or at one acquired in the same step (22 and 12 shots, age 0).

| run | side | shots | not at nearest | share | median lock age (ticks) | median gap (wu) | max gap (wu) | of these, acquisition NEAREST | acquisition RETURN-FIRE | acquisition UNEXPLAINED |
|---|---|---|---|---|---|---|---|---|---|---|
| on | blue (A) | 217 | 188 | 86.6% | 653.0 | 91.2 | 128.8 | 168 | 20 | 0 |
| on | red (B) | 334 | 168 | 50.3% | 164.0 | 16.3 | 78.0 | 155 | 13 | 0 |
| control | blue (A) | 267 | 142 | 53.2% | 843.5 | 107.8 | 125.6 | 142 | 0 | 0 |
| control | red (B) | 324 | 113 | 34.9% | 208.0 | 12.5 | 29.0 | 113 | 0 | 0 |

One tick is 0.05 s, so a median blue lock age of 653 ticks is about 33 s.

## 3. Blue units that fired at a non-nearest enemy

### on run (blue = side A)

| unit | role | locked target | acquired at tick | acquisition class | shots at non-nearest / all shots at that target | ticks (first..last) | distance to target (wu) | the nearer enemy | nearer by (wu) | lock age at those shots |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Vanguard | 15 | 83 | RETURN-FIRE | 14 / 14 | 367..679 | 299..299 | 14 | 128.8..128.8 | 284..596 |
| 3 | Vanguard | 10 | 82 | RETURN-FIRE | 6 / 6 | 193..313 | 300..300 | 14 | 96.5..96.5 | 111..231 |
| 4 | Interceptor | 11 | 51 | NEAREST | 28 / 28 | 187..727 | 247..247 | 14 | 91.2..91.2 | 136..676 |
| 5 | Interceptor | 11 | 56 | NEAREST | 41 / 41 | 750..1550 | 250..250 | 14 | 88.2..88.2 | 694..1494 |
| 6 | Interceptor | 9 | 49 | NEAREST | 51 / 51 | 159..1159 | 245..248 | 14 | 64.6..68.4 | 110..1110 |
| 7 | Bombard | 11 | 50 | NEAREST | 24 / 25 | 151..1531 | 872..876 | 14 | 97.9..101.9 | 101..1481 |
| 8 | Bombard | 11 | 51 | NEAREST | 24 / 25 | 158..1538 | 902..906 | 14 | 97.9..101.9 | 107..1487 |

Blue units that fired only at the nearest: none.

### control run (blue = side A)

| unit | role | locked target | acquired at tick | acquisition class | shots at non-nearest / all shots at that target | ticks (first..last) | distance to target (wu) | the nearer enemy | nearer by (wu) | lock age at those shots |
|---|---|---|---|---|---|---|---|---|---|---|
| 4 | Interceptor | 11 | 47 | NEAREST | 43 / 43 | 448..1288 | 241..247 | 14 | 107.8..113.8 | 401..1241 |
| 5 | Interceptor | 11 | 56 | NEAREST | 31 / 31 | 862..1462 | 248..250 | 14 | 97.2..99.1 | 806..1406 |
| 6 | Interceptor | 9 | 49 | NEAREST | 21 / 21 | 440..840 | 245..245 | 14 | 88.6..88.6 | 391..791 |
| 7 | Bombard | 11 | 14 | NEAREST | 23 / 24 | 150..1470 | 903..911 | 14 | 117.4..125.6 | 136..1456 |
| 8 | Bombard | 11 | 15 | NEAREST | 24 / 24 | 98..1478 | 933..941 | 14 | 1.2..125.6 | 83..1463 |

Blue units that fired only at the nearest: 1, 2, 3.

## 4. Three worked examples

**Example 1: a lock doing its job (on run, blue Interceptor 5, shots 750 to 1550).** Tick 56 is unit 5's cohort turn (56 mod 4 = 0 = (5+3) mod 4). Unit 5 stands at (2144, 2011) with no target. Red Bastion 11 is at (1155, 2056), 989.8 wu away. Red Warden 14 is at (1112, 2055), 1033.0 wu away, and has been in blue's seen set since tick 55. Nearest eligible is 11 by 43.2 wu; the unit takes 11 (acquisition class NEAREST). From then on it keeps 11. At tick 300 the Warden has walked to (1312, 2061), 185.2 wu from unit 5 against 277.6 to 11. At tick 750 unit 5 is at (1452, 1980) and fires its first shot at 11 (249.9 wu, Interceptor range 250) while 14 stands 161.7 wu away, 88.2 wu nearer, and the lock is 694 ticks old. Its 41 shots (ticks 750 to 1550) all go to 11 at that gap, until 11 dies. That is a shot at a unit that is not the nearest, caused by the lock; at the tick of acquisition it was the nearest.

**Example 2: return fire beats nearest (on run, red Bastions 9 and 10 and Bombard 15, tick 1880).** Blue Bombards 7 and 8 stand at (1678.1, 2028.7) and (1692.4, 1985.6). At tick 1879 blue Bombard 8 fires at red Bastion 9 (1395.4, 1950.1); the shell takes 17.5 hp off 9 and, by splash, the same 17.5 off red Bastion 10 (1374.1, 2049.3) and red Bombard 15 (1275.6, 1950.1) (hp 113.0 to 95.5, 294.9 to 277.4, 400.0 to 382.5). At tick 1880, each of their cohort turns, 9, 10 and 15 have no target and each takes 8: 9 at 299.1 wu (blue 7 is 293.4 wu, 5.7 wu nearer), 10 at 324.6 (7 at 304.6, 20.0 nearer), 15 at 418.3 (7 at 410.1, 8.2 nearer). Not the nearest at that tick, and exactly what R-087-06 says: a unit with no target that is hit targets the attacker. All 3 are in the table above.

**Example 3: the only way a lock ended with the target alive (control run, blue Vanguard 2, tick 165).** The Vanguard took return fire (splash from red Bombard 15) at tick 14 and in the next step (tick 15) acquired 15, 1200 wu away. It walked toward it for 150 ticks. At tick 165 it stands at (1489, 1933), 503.4 wu from 15 (alive, seen) and 224.7 wu from red Warden 14. It has covered 697 wu from where it acquired (724 wu from where it started); its sensor radius, the R-087-05 leash, is 700. At tick 165 it drops 15 and takes 14, the nearest (class NEAREST). Vanguard 1 does the same at tick 176 (492.4 wu from 15, 189.7 from 14) and Vanguard 3 drops to no target at tick 165. In no case did something nearer simply come along and take the lock away.

## 5. Side observations (not asked, not judged)

- Locks ended with the target alive and in the side's seen set, not by the leash: on run, red Warden 14 at tick 1706 (lock on blue Bombard 7, 763.6 wu, one tick old); control run, blue Interceptor 5 at ticks 1485 (target 16, 381 wu, one tick old) and 2321 (target 15, 277 wu, one tick old). These units did not fire. The rule list for a lock ending (R-087-03) names death, sight and orders only; the leash is R-087-05. Not about nearest.
- Acquisitions beyond the unit's own sensor radius (30 of 61 on, 34 of 65 control) are Bombards and Bastions reaching to their attack range, plus Vanguards answering fire from beyond their own sensor radius (return fire).
- Every shot has the held target or one set the same step as its target; the lock was never silently swapped for another on a shot tick.

## 6. Answer

**Not a break of 'nearest at acquisition' in either run; the lock working as written.** Of 61 acquisitions in the sight-on run, 55 chose the nearest eligible enemy (within 1 wu), the other 6 were return fire (R-087-06; 3 of them blue Vanguards answering Bastion and Bombard fire from beyond their own sensor radius, 3 red units answering blue Bombard 8); none is cohort delay, a most-damaged policy, an eligibility difference or unexplained. The control run is the same: 61 of 65 nearest, 4 return fire, 0 unexplained. What Westley saw is real and measured: 188 of blue's 217 shots in the sight-on run (86.6%) went to an enemy that was not the nearest at the shot, a median 91 wu nearer (up to 129), at locks a median 653 ticks (33 s) old; every one of those locks was set on the nearest enemy (168) or by return fire (20). The same holds, less strongly, for red (168 of 334, median gap 16 wu) and in the control run (blue 142 of 267, red 113 of 324). In this layout the nearer enemy is red Warden 14, which was farther away or unseen when blue's Interceptors and Bombards took their targets (ticks 47 to 56 (49 to 56 in the sight-on run)) and then stood nearer. Under R-087-03 as written (and Westley's 2026-11-08 sentence it quotes) that is a lock; to make blue shoot the nearest in play, the rule would have to change, not the engine. UNEXPLAINED acquisitions: none, so no reproduction is needed.

