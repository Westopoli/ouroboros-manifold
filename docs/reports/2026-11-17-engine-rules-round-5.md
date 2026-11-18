# Engine rule fixes, Round 5 (2026-11-17)

Builds Westley's rulings of 2026-11-17 into the engine and the lab checker, and leaves the stage 4 fights re-made on an engine that obeys them. Spec and the Architect's rulings pass by pass: `docs/northstar/plans/engine-rules-2026-11-08/round5.md`. Branch `s/engine-rules-r5`, about 105 commits, built by four workflows of Sonnet 5.5 agents (30 agents; test writers and builders never the same agent).

## What was built

1. **Notice distance** (R-087-04, R-096-02). A unit acquires an enemy its side sees only within its weapon's reach to that enemy plus one tenth (`OM_NOTICE_MARGIN` 0.1, `csrc/notice_internal.h`, DRAFT-notice-margin). The sensor radius no longer decides it.
2. **The lock ends at the notice distance** (R-087-03). A target that leaves it is dropped; a target taken by return fire is kept, up to the leash.
3. **Guard** (R-096-08, R-208-01). A guard notices as every unit does and follows no farther than 200 wu from its post.
4. **Unseen fire** (R-087-01). An attack-mover still on its way keeps walking; an idle unit and one that has arrived move 200 wu away and hold.
5. **Slope collision** (R-097-05, R-097-03). Two units on one slope collide whichever side of the midline each is on; the steering probe sees them (`csrc/move_slope.c`).
6. **Hill layouts.** A lint over the 84 catalogue layouts: nine have a side that must climb; eight already had its attack-move point past the midline; L-0045 was 353 wu short and was given `orders_point = [2230.0, 2002.0]`.
7. **The lab checker** judges thirteen rules: the eleven of Round 4, unseen fire (R-087-01) and slope collision (R-097-05); its acquire and lock checks follow the notice distance.
8. **Found on the way and fixed:** a walker under a group order never "arrived" (the walker step had no arrival radius; two units sent to one slot stood 16 wu from it with the order still set for a whole fight); a group member hit after arriving was walked back to its point.

## Measured

Each piece G1 to G5 and each new checker predicate was taken out on a scratch copy and turned named tests red. Determinism: 28 pairs, 0 mismatches. Suites at the tip against the baselines: `tests/csim`, `tests/transport`, `tests/skilllab` (top level, arena, integration, ground), `tests/qa`, `tests/method` show no red outside them and outside the two below; 16 csim hashes and about 30 lab pins that moved with the behaviour were re-pinned, each lab pin only after the checker reported nothing on the new fight.

Two tests are red on the landed tip and are Westley's thresholds, not changed:

- `tests/skilllab/integration/test_speed.py`, one 16 against 48 fight: 1.6 s against the mark of 1.5 s. The engine's cost per tick is unchanged (0.78 ms against 0.80 ms). The same fight now lasts 1,981 ticks where it lasted 1,104, and 86% of the time is the lab's own per-tick checker in Python.
- `tests/skilllab/test_umbrella.py`, the controls command: about 597 to 600 s against its 600 s timeout, for the same reason.

### Stage 4 fights (20 seeds each, identical; seed 10 shown), Round 4 against Round 5

| Fight | Round 4 | Round 5 | His guess |
|---|---|---|---|
| Cover L-0039, sight on | red wins, 3 left, 2,314 ticks | blue wins, 3 left, 2,213 ticks | red 75% |
| Vantage L-0061 | blue wins, 18 left, 2,136 | blue wins, 23 left, 1,415 | blue 98% |
| Trap L-0080 | red wins, 26 left, 1,726 | red wins, 23 left, 1,844 | blue 75% |
| Trap L-0083 | red wins, 40 left, 1,728 | red wins, 38 left, 2,332 | blue 75% |

Every stage 4 fight ends with one side wiped out. The checker reports nothing on L-0039, L-0061 and L-0080. On L-0083 it reports one thing in every seed: at tick 1,735 two units stand 18.3 wu apart for a few ticks where two of the layout's hill records overlap and give opposite layers; the engine compares hill records, so it does not treat them as one slope. The page marks L-0083 "invalid, not ranked" for that one report.

### The 199-fight sweep

| How a fight ends | Round 4 | Round 5 |
|---|---|---|
| One side wiped out | 169 | 156 |
| Stand-off (both sides alive, nobody firing) | 26 | 33 |
| Time cap | 4 | 10 |

With sight on, stand-offs went from 6 to 11 and caps from 0 to 3. In every sight-on stand-off the nearest surviving enemies stand 276 to 1,410 wu apart, beyond each other's notice distance: both sides have arrived, nobody is ordered, nobody fires. This is R-087-04 as ruled, and what the csim scene of two 16-unit groups attack-moved to one point shows in small: 3 against 3 left, 547 wu apart, for ever.

Layouts whose end changed for the worse: L-0004, L-0013, L-0035, L-0036, L-0045, L-0046 (sight on) to a stand-off; L-0031, L-0043 (all three modes) and L-0054 (sight on) to the cap. For the better: L-0066 (stand-off to a wipe), L-0046 sight off. Of the nine hill layouts only L-0045 worsened (a red win became a stand-off, 19 against 3, 926 wu apart), and it is the one layout whose order point this round moved. Both traps still end in a wipe.

Rule breaks across the sweep (unit-ticks), 2026-11-07, Round 4, Round 5:

| Rule break | Nov 7 | Round 4 | Round 5 |
|---|---|---|---|
| Unit inside an obstacle | 1,159,428 | 0 | 0 in 198 fights; one unit at the map corner for 3,326 ticks in one cap fight (L-0005 control) |
| Fired after moving | 1,168 | 0 | 0 |
| Wardens stacking | 859,729 | 0 | 0 |
| Holds a target it cannot shoot | 3,547,771 | 1,920 | 545 |
| Sees across layers, cannot shoot | 184,976 | 0 | 0 |
| Jump at a layer change | 951 | 0 | 0 |
| Layer flicker on a slope | 31,839 | 37,981 | 29 |
| Walker standing still with a destination | 73,402 | 12,353 | 1,796,027 |

The last row is three layouts that now run to the 12,000-tick cap (L-0054 758,160; L-0043 196,678; L-0057 89,222): walkers that still hold an attack-move order stand behind friends for the rest of the fight while the enemy is beyond their notice distance. Under Round 4 they would have seen the enemy and fought. Not traced further.

## Proof lines written

Three stage 4 rules now name a test: R-093-02 and R-084-04 (whole-run, lab configuration, filled controls) and R-007-01 (scenario; the lab's box cannot show the rule's height clause, so the proof uses a cover disc and says so). Written and not yet named as proof, each for a stated reason: R-008-04 (pings are not exercised in the ground-era lab), R-083-03 (the visible circle is the client's; a Warden heals itself, which the rule's wording does not settle), R-096-08 (the whole-run fight never baits a guard out; the stepping clauses are proved by scenarios in another file), R-097-10 (four functions, one per clause, where the method asks for one). The rules this round built (R-087-01, R-087-03, R-087-04, R-097-05, R-096-08) have per-clause scenario and whole-run tests with controls; their Proof lines stay `MISSING` until the weekly audit reads them against the seven qualifications.

## Open

For Westley:
- **Stand-offs.** 33 of 199 lab fights end with both sides alive and out of notice range, 10 more at the cap. The rule is his; whether lab fights need something that sends idle survivors forward is his call.
- **The speed mark** and the controls timeout: raise them, or a piece that makes the lab checker read the engine once per tick instead of once per unit.
- **A pursuer never fires at a target that walks away,** however slowly: it stops at exactly its range, may not fire on a tick it moved, and the target is out of range again the next tick. Older than this round.
- **L-0083** has two overlapping hill records; **L-0045**'s moved order point; the one-tenth margin; "firing radius" read as the notice distance for the guard; the unseen-fire rule being the engine's for every map.
- **Order of work inside a tick.** The engine works unit by unit, so a unit reads some enemies one step old; the side with the higher unit ids sees its enemies one step fresher. Older than this round; invisible at one step; recorded.

Not traced:
- R-087-03 lock swaps reported in five sweep fights outside stage 4 (L-0006 15, L-0004 7, L-0035 5, L-0036 3, L-0025 1), and R-087-01 "moved again with no new hit" twice (L-0006, L-0005).
- The unit at the map corner (4000, 4000) inside a blocked cell for 3,326 ticks (L-0005 control).
- A unit moving away that is blocked by a guard presses against it and the move away never ends.
- L-0079: two units 17.2 wu apart on one slope at tick 276.
- R-087-09: one unit holds a target 178 wu away that it does not fire at (L-0046, tick 3,130).

Tests and method:
- No csim test covers a walker's arrival at a group slot, or the unseen-attacker case with sight on; the checker's two excuses of the third pass have planted cases, the eight-reading pick path has none that is wrong by more than both units' steps.
- `tests/qa/desktop/test_flow_spine.py` is order-dependent under two workers; `tests/csim/scale/` (five hashes) and four `tests/transport` tests are red on main before this round; nine `tests/qa` tests likewise.
- The 120k context stop in the agents' rules made verifiers and fixers return half done in the first pass; later passes cut the work smaller. The first pass's work list missed about forty test scenes that relied on acquiring by sight without citing the rule.
- The Architect's ruling in the third pass (judge a pick on the end-of-tick frame) was wrong; it came from one tracer's reading of the tick and was corrected in the fourth pass after a second agent measured the mixed state.

Play proof: not possible from the agent session (no display that passes `play.sh --check`); Westley plays main.
