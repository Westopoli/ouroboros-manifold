# Stage 4 findings: sight, the results against his expectation, seeds, overlap (2026-11-19)

Asked for by Westley, 2026-11-19: "yes trace sight, examine the non-expected results to see if there's any obvious reasons. - Our goal is to work toward starting stage 5". Four Sonnet tracers, read-only, on main `f89939b4a`; scripts and per-tick records under `~/Projects/om-wt/engine-rules-baseline/` (`r6-s1/` sight, `r6-x1/` traps, `r6-x2/` cover and SIT-0106, `r6-ov/` overlap). Nothing was built.

## 1. Sight decides nothing in three of the four stage 4 fights

L-0061 (vantage), L-0080 and L-0083 (traps) are identical tick for tick with sight on and with targeting by sight switched off. In all three there is no tick on which a unit has an enemy inside its notice distance and its reach that its side does not see.

Why, by the numbers:
- Every role in those fights sees at least 2.3 times as far as it shoots (Vanguard range 300, sensor 700; Warden 350 and 800; Raider 200 and 800; Interceptor 250 and 1000), and a unit reacts only within weapon range plus a tenth. Whatever a unit could shoot, its side already sees.
- Reach is 0 layers up, 1 down. The low side cannot shoot up at all, so being blind to the hill changes no shot. In L-0061 red first sees blue at tick 120, after blue's first hit at about tick 100, and could not have answered either way.

In L-0039 (cover) sight decides a great deal: 18,838 unit-ticks with a hidden enemy in notice and reach, all of them Bombards (range 1200, sensor 300) and Bastions (800, 300). Sight matters for a role that out-ranges its own eyes, and for no other.

What would make it matter in a vantage or a trap: such a role placed in it; or a reach of one layer up; or a sensor shorter than 1.1 times the range. His notes say blue is "unseen on the high ground" in the traps; red sees blue from tick 40 in both.

## 2. The seed changes nothing

Seeds 1, 2 and 3 of L-0080, L-0039 and SIT-0106 are identical tick for tick. The seed feeds the world's random stream, which the tactical code never draws from, and the terrain generator, whose heights the layout then overwrites. Every lab fight has exactly one outcome. An expectation such as "blue wins 75 percent" cannot be measured as the lab stands; it reads as win or lose. A rate would need something varied between runs (placements moved by a few wu, for example: in two fights below, moving one unit 10 wu flips the winner).

## 3. The results against his expected winner

| Fight | He expected | Result | Reason | Stable? |
|---|---|---|---|---|
| L-0080 trap (16 v 32) | blue, 75% | red, 25 left | arithmetic, then the layout | yes |
| L-0083 trap (24 v 48) | blue, 75% | red, 39 left | the same | yes |
| L-0039 cover, stage 3 | red (blue 25%) | blue, 2 left | the role triangle | no: a coin toss leaning blue |
| L-0039 cover, stage 4 | red (blue 25%) | blue, 3 left | the role triangle | yes |
| SIT-0106, stage 2 | (list said red) | blue, 5 left | the list was wrong | thin |

**The traps.** Red has about 3.5 times blue's damage per second and 1.6 times its hit points (L-0080: blue 71 a second and 7,000; red 252 and 11,500). A red Raider deals 11.3 a second, a blue Warden 2.7. Blue would need about 160 s of full fire to kill red; red needs about 28 s. The layout also differs from his words in ways that hurt blue but do not decide it: the trap springs when the first red unit is within 300 wu of the centre point, about 430 wu before red's centre arrives, so the low arc meets red alone from tick 164 and is dead by tick 932; the hill groups stand 863 wu from the centre point and stop at the first red unit inside their notice, about 450 wu from red's centre, hitting the fringe (they hold a target 81 to 88 percent of the time; they are not idle); red fires nothing at layer 1 and kills the hill units when they walk down late. What-ifs on scratch copies of the layout, red left of 32 and of 48: as built 25 and 39; released when red's centre is within 100 wu, 20 and 37; hill units on the rim facing the point, 20 and 27; a larger hill 218 wu from the point, 17 and 27. Blue never wins. No rule is broken. For blue to win, the roster has to change.

**The cover fight.** Raw strength is level (damage per second times hit points: 158 thousand against 159 thousand). His reason (blue has fewer firing angles) holds at the start: with sight off blue has 2 to 6.5 units in range against 5 to 8 for the first hundred ticks, then 8 against 8; with sight on, 3.5 to 4.6 against 7.4 to 7.8 until tick 600, and blue's three Vanguards die first. What turns it is the role triangle: red's five siege units deal one fifth damage to blue's Interceptors, which deal one and a half times to them, and blue's Bombards fire from 435 to 900 wu back. The boxes are walls only: they split blue into two groups and delay the first shot from tick 12 to tick 236. Stage 3: moving one blue unit 10 wu gives the fight to red; 4 of 5 such moves stay blue. Stage 4: blue in 4 of 4.

**SIT-0106.** He approved blue winning it on 2026-11-02 ("this one also had the correct outcome, approved"). The expected winner "B" in the approved-fights list was taken from the Architect's draft text in the situation file. It has not flipped: blue 11 left then, blue 5 left now. The list is corrected (below). Thin: one of six 10 wu moves gives it to red.

## 4. Overlap (Q-097-04): a study of the push pass, with trials

Mechanism, in stage 1: a unit in the second rank steps 4 wu toward its goal each tick into a gap too narrow for it, between units standing to shoot about 40 wu apart, which give no ground; it takes every push, its neighbours are pushed too, each pair is settled in its turn and broken by the next, and after ten rounds pairs sit 26 to 29.9 wu apart; the next tick repeats it, for a thousand ticks and more. The nearly stacked pairs (under 7 wu) are an idle unit that yields fully to every walker of its side and is shoved into its own neighbours. Of the stage 1 pairs none is an enemy pair: 85 walker with walker, 39 standing-to-shoot with walker, 69 idle with walker.

Trials on a scratch copy (pairs under 28 wu for more than 3 ticks; every fight kept its winner):

| Rule tried | Stage 1 pairs | Stage 1 end | Small fights | Cost |
|---|---|---|---|---|
| as on main | 145, closest 2.4 wu | apart 14:22 | L-0055 1, L-0080 4, L-0083 21 | |
| A: a walker takes no step that ends within 30 wu of a unit that gives no ground and nearer to it than it stood | 84, closest 1.9 | apart 22:23 | 0, 7, 15 | traps run 18 to 33 percent longer; no unit test red |
| E: A, and an idle unit that already has a neighbour within 30 wu gives no ground | 14, closest 21.3 | time cap, 18:18 | 0, 0, 17 | stage 1 no longer ends; one unit test red |
| every unit gives no ground | 0 | time cap, 29:7 | not run | fights freeze |

No small rule both keeps the Invariant and lets crowded fights finish. A halves the overlap and costs nothing measurable but fight length; what remains under it is idle units squeezed between walkers. Clearing those means an idle unit stops stepping aside for a walker of its own side, which is his rule (Round 4) and which froze or stretched fights when tried.

## What this means for stage 4 and stage 5

- No unit behaviour was found that breaks a rule he has ruled, other than the overlap inside a crowd.
- As a stage about sight, stage 4 measures sight in one fight of four. The vantage and the traps measure height and numbers.
- The traps cannot go blue's way on this roster; the 75 percent cannot be measured on any roster until something varies between runs.
- Decisions for him are listed in the chat of 2026-11-19 and, when ruled, in `decisions.md`.
