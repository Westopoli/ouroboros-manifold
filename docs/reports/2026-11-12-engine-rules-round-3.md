# Engine rule fixes, Round 3: three defects the checker exposed after Round 2 (2026-11-12)

Follows `2026-11-11-engine-rules-round-2.md`. Same method: an investigator traced each defect by log, one agent wrote the failing tests, a different agent built, a third verified. The slope trace is beside this file, `2026-11-12-engine-rules-round-3/appendix-slope-pileup.md`; the second trace (lock, chase, checker eligibility) is summarised under Fixed.

## Fixed

1. **A lock judged on half-moved positions** (R-087-03, R-087-08). Each unit asked "does my side still see my target" inside its own turn, when some units had already moved that tick and others had not. A pair that was visible before and after the tick could be hidden in between, so a unit dropped its target one tick early (twelve guards at once on L-0084, tick 1776), or kept it one tick late. The side's sight of every held target is now answered once per tick, before anything moves.
2. **A chase ordered while the unit could not move was never ordered again** (R-087-04, R-084-04). A unit that took a target just out of range during the pause after its own shot had its route refused, and then stood until the 1-second give-up dropped the target. The chase is now re-ordered whenever the unit holds a target out of range and has no destination.
3. **The move away from unseen fire was cancelled halfway** (R-087-01). While a unit moved away, the pursuit-end check sent it back toward its order point, and the two steps cancelled: the unit stood still with a destination. That check is now skipped during the move away.

The lab checker's nearest-pick check now applies the engine's own two-stage eligibility (in range from where the unit stands; for a guard with nothing in range, reachable from within 200 wu of its post), so eight legal picks on L-0084 are no longer reported.

## Measured

Suites on the landed tip: `tests/csim`, `tests/skilllab`, `tests/qa`, `tests/method` show no failure outside the baselines. Each fix was reverted alone and its tests went red. The checker reports nothing on the 160 stage 4 fight files, nor on L-0084, L-0081, L-0050 or a terrain-less blob.

Stage 4 (20 seeds each, identical): cover, red wins with 3 left; vantage, blue wins with 18 left; trap L-0080, red wins with 26 left in 1,731 ticks (22 left in 2,365 after Round 2); trap L-0083, red wins with 41 left in 1,516 ticks (30 left in 2,839).

Sweep of 199 fights (unit-ticks):

| Measure | 2026-11-07 | Round 1 | Round 2 | Round 3 |
|---|---|---|---|---|
| Holds a target it cannot shoot, not closing in | 3,547,771 | 314,851 | 2,312 | 2,435 |
| Sees across layers, cannot shoot | 184,976 | 171,364 | 0 | 0 |
| Jump at a layer change | 951 | 910 | 0 | 0 |
| Walker with a destination and no target standing still | 73,402 | 95,380 | 395,318 | 146,664 |
| Two units closer than 20 wu | 2,264 | 420 | 19,862 | 24,893 |
| Idle unit with no order and no target moved | 0 | 0 | 126,746 | 230,793 |

Determinism: 28 pairs, 0 mismatches.

## Open

Items 1, 2, 8, 9 and 10 of the Round 2 report stand. Items 4, 5 and 6 are fixed by this round. New or changed:

- **Idle units moving, unexplained.** 230,793 unit-ticks, double Round 2, largest on four open-field layouts (L-0004, L-0005, L-0006, L-0025) where fire from an unseen attacker should be rare. Needs a trace before it is called expected.
- **Stalled walkers, residue.** 146,664, down 63% from Round 2 and still above the starting figure; L-0045 rose from 1,844 to 9,299. Not traced.
- **Units pile up on ramps.** A walker that crosses a ramp's midline changes layer and arrives inside units of the new layer, because units collide only with their own layer; the collision then tries to throw it clear, the jump rule cuts that short, and it flips back and forth. A trial where units on adjacent layers collide while both stand on a slope removed the pile-up on all six hill fights with every winner unchanged, at the cost of queues on narrow ramps. It changes the collision rule (R-097-05) and touches the layer rules, so it waits on Westley.
- **Checker reports on fights outside stage 4** (seed 1, sight on): L-0063 three and L-0062 one "not the nearest" picks, each by 2 to 4 wu; L-0064 one layer-change step of 6.88 wu. No test asserts these fights clean.
- **Tests that pass without meeting their case.** The fixes removed the situations three tests were built on (the one-tick sight lag on L-0084, the cover give-up at tick 376, two continuity premises); they pass and no longer prove what their names say. The new move-away stall detector never fires on the fixed engine, because a unit moving away has no destination. Each needs a planted case to stay able to fail.
- **A braced unit with its target out of range** is ordered to move every tick and refused every tick; it stands. No rule says what it should do.
- **Both traps are won by red by more than before.** With units no longer freezing mid-retreat or standing short of a target, the larger force brings its numbers to bear sooner.
