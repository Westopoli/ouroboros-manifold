# Rule enforcement in the simulation: why rules break, how wide it is, how to fail louder (2026-11-07)

Requested by Westley after the stage 4 re-run: units walk while shooting, stand inside cover, jitter at its edge, and keep targets they cannot shoot. He asked whether the architecture allows rules to be broken, whether a small patch would hide the problem, and what the cascade's tests did. Three read-only investigations ran against main `53c25f5b`; nothing in the repository was edited.

The detail is in three appendices beside this file. This page is the synthesis.

- Appendix A, `appendix-a-code-architecture.md`: how movement, targeting and firing are built in `csrc/` (read from source; nothing was compiled or run).
- Appendix B, `appendix-b-test-forensics.md`: the tests the manager-mode cascades wrote, a mutation check on a scratch copy, rule pins, coverage.
- Appendix C, `appendix-c-invariant-sweep.md` with scripts in `sweep/`: 199 lab fights (23.9 million unit-ticks) checked after every tick against 30-odd invariants.

Earlier evidence this builds on: `docs/reports/2026-11-07-stage4-rerun-investigation.md`.

## Answer in one paragraph

Yes. The rules are written once, in the bible, and implemented many times, with no shared enforcement point and no runtime check. "A unit never stands in a blocked cell" is enforced on one of about fourteen paths that move a unit; the others rely on a repair that runs the next tick, which is the saw-tooth Westley saw. Sight and fire answer the same geometric question with different code, so they disagree. The tests prove that the rules work in small staged scenes, never that they hold through a whole fight in the shipped configuration, and several were accepted because the new code matched the old Python or a recorded hash. A patch to the one walker step would remove the symptom and leave the class: the sweep found at least ten other kinds of rule break, some in layouts with no cover at all.

## What is broken, measured

From the sweep (Appendix C; counts are unit-ticks over 199 fights; "clean" means not found, not proof):

| Finding | Scale | Where |
| --- | --- | --- |
| Unit ends a tick inside a blocked cell | 1.16 million | 19 of 28 layouts with blocks |
| Unit holds a target it cannot shoot, and does not close in, for over 20 ticks | 3.5 million | 20 of 67; only layouts with blocks, hills or slopes |
| Ejected out of a blocked cell by a jump of 9 to 24 wu (a step is at most 2 to 7.5) | 19.8 thousand | 15 of 28 |
| Layer flicker 0,1,0 within 4 ticks at hill rims; jumps of 24 to 78 wu with a layer change | 31.8 thousand; 951 | 13 of 14 hill and slope layouts |
| Sees an enemy 338 to 348 wu below but cannot shoot it | 185 thousand | 11 of 14 hill and slope layouts |
| Warden heal and damage reduction match neither the bible (no stacking, Q-084-01 closed 2026-10-20) nor ALG-60 | 860 thousand | 52 of 55 Warden layouts |
| Moved within 1 to 9 ticks after firing (backswing) | 786 | 30 layouts; most are a Bombard killing its target, then marching |
| Pacing: six reversals in 600 ticks | 1.2 thousand | 36 of 67, open fields included |
| Fires facing more than 90 degrees off its target | 881 | 35 (the firing arc is draft and unbuilt) |
| Dead units keep a stale target id | 8.2 million | harmless in the replay today |

Clean in this sweep: fire at a dead target, out of range, beyond layer reach, with `can_shoot` false, or across a blocked cell; units outside the canvas; dead units moving or firing; hp rising with no Warden near; turn rate; fire cadence; guard leash. Determinism: 28 layout and sight pairs run twice gave identical per-tick hashes. Seeds change nothing in these fights (the tactical sim draws no random numbers), so a second seed adds no coverage.

Not testable through the engine interface: anything outside the tactical engine, command validation, plain-move and attack-target orders, formation slots, the flinch rule, abilities, layer-transition timing, fog memory.

Two of Westley's specific observations, checked directly:

- Sustained target lines while moving were mostly a drawing artifact: the replay drew a line for every unit with a target. In L-0039, 7,167 unit-frames had a target but only 175 shots were fired. Fixed on main (`53c25f5b`): the replay draws a line only for a unit that fired.
- Real walking while shooting exists, but through a different mechanism than "firing units may move" (next section).
- Shots to a farther enemy: 11 of about 104 shots went to a visible enemy that was not the nearest, all by two units keeping an earlier target. That follows R-087-03 (an engaged target in range is kept). Whether keeping is the intended behaviour is Westley's ruling.

## Why the architecture allows it

From Appendix A, in order of weight:

1. No single enforcement point. Entry into a blocked cell is prevented only in the steer step (`csrc/tactical_move.c:2233`). The walker step (`:2296`), the kiting move (`:2414`), the flinch step (`csrc/unit.c:1914`) and spawn have no cell guard. `om_move_leave_blocked` (`:2127`) ejects a unit one tick after it has entered; that repair is the saw-tooth. Five different functions answer "is this cell blocked", and the router never sees boxes (`walk_route.c:3`).
2. Rules are switchable. Whole families (pursue by steering, route around terrain, target by sight) are parameters, and about thirteen "baseline only" branches are still compiled. An invariant holds only in configurations that enable its code. There are no asserts and no violation counters anywhere in `csrc/`.
3. Decide, then move, then shoot, with no hold. The AI decides on last tick's positions, then movement runs, then the fire pass tests the shot without checking `halted`, `engaged`, or whether the unit moved this tick (`csrc/unit.c:2427`, `:2348`, `:2356`). A unit released because its line was blocked walks one step and fires if the line has cleared. The bible says "halts and fires" (R-087-04) but nothing says "does not fire in a tick it moved".
4. Sight and fire disagree beyond endpoint cells: corner touches, canvas edge, ground band, obstacle discs (block fire, not sight). The cover test is a hand copy kept in step by a comment.
5. Duplicated state. Position lives in four copies; `halted` and `engaged` are set together but cleared in different places; a player order is recognised by float equality of two destinations; backswing is written in four places with an off-by-one between paths, and group members skip it (a likely real R-084-04 break).
6. Target drop and re-acquire are out of step: the sight check drops a target every tick, re-acquiring happens only on the unit's own cohort turn, every 4th tick.

Unverified in Appendix A (source read only): the decide, move, fire order needs a one-unit trace; the group backswing bypass and the `halted`/`engaged` desync were not shown reachable in play; layer cross-over rechecks of the unit's cell were not read.

## Why the tests let it through

From Appendix B:

1. No whole-run invariant harness. No test runs a whole fight and checks every tick that no unit is in a blocked cell, a firing unit holds still, or a held target stays held.
2. The shipped setup is never the test world. Tests use few units, no terrain, sight off; the lab uses walkers, boxes, sight on, dozens of units.
3. Acceptance by parity and by hash. The "plan P" push accepted code as "same as the Python plus fight hashes", so the code's behaviour was the oracle; hashes were re-recorded after H-057. Commit `24c0dc57` (A172) replaced a per-tick "never inside the wall" loop with a final-position check.
4. Placeholder controls: 92 of 130 files in `tests/csim/controls` fail with `AttributeError` or `NotImplementedError` and are tolerated by `placeholder_controls.txt`.
5. Pins prove the wording, not the behaviour. A pin is the first six hex digits of the rule line's sha256; it shows the rule text has not changed since the test was written. Any mention of an R-id counts as coverage, and a test can cite a stale number (a test cites R-097-09 for the rule now numbered R-207-06).
6. Coverage gaps: 11 of 53 E-13 rules, 16 of 63 E-11 rules (R-087-09 has neither code nor test) and R-207-06/07 in no csim test.

A mutation check on a scratch copy (7 mutations): deleting the steer-step terrain guard turned no movement-rule test red (only one incidental routing test and five hash tests); re-acquiring a held target every cohort turn turned no rule test red (only hash tests). Mutations to `halted`, nearest-target, the stationary rule and cover-in-fire were caught. A 60-line whole-run invariant test with 6 v 6 Vanguards and one box fails on HEAD for walkers (2,794 unit-ticks inside the box from tick 52), so the invariant style works and is cheap. It did not reproduce walk-while-shooting in that layout.

One question the repository cannot answer: whether manager-mode's saboteur phase ran for the movement and targeting cascades.

## Options to fail louder

Appendix A, with costs. All respect the contracts: the header and pipe frames do not change, and the checker touches neither determinism nor the save or checksum.

- O1. Lab-side per-tick invariant checker (new `scripts/skilllab/invariants.py`, called after `step(w)` in the fight loop). Rule-id'd checks; a run that trips one is tainted, dropped from aggregates, and shown as "INVALID: R-207-06 tick N unit U". A check whose rule depends on a switch reports "suspended: sight off", never silently passes. The predicates already exist in the six `test_stage4bug_*` files and in the sweep's `inv_check.py`. Cost small, no C change. It detects; it does not prevent.
- O2. C-side read-only checker in a new `csrc/invariants.c`, off by default, with a log or abort flag for debug and lab builds. Sees mid-step state and catches desync between the four position copies. Medium cost; must stay out of the save and hash.
- O3. One position-commit function that every mover goes through (clamp, cell guard, slide, a reason code). The only option that removes the class instead of detecting it. High cost; re-records goldens. A guard alone leaves units pressed on box faces, so walker routing around boxes ships with it.
- O4. One line-of-sight primitive for sight and fire, the decision stored once per tick, and the fire pass respecting hold. High cost and risk; needs Westley's ruling on the endpoint-cell exemption first.
- O5. Delete the compiled baseline branches, `am_engaged` and the duplicate `halted` flag. Cheap but bumps the save format; batch after O3 and O4.

Test architecture to go with them (Appendix B):

- Whole-run invariant tests in the csim helpers, using the shipped configuration as the default world, and property tests over seeded random layouts.
- Write each epic's Invariants section as its first failing whole-run test, so a story cannot land without them.
- A rule: a `Test-defect` commit may not weaken a per-tick assertion unless it names the replacement invariant.
- Fill the 92 placeholder controls; run the mutation list nightly.
- Pins that check behaviour: the test must name the rule and assert on a rule-specific outcome, not just mention it.

## Recommendation

A small patch to the walker step is not enough: it leaves kiting, flinch and spawn unguarded, and sight and fire still disagree. Order:

1. O1, with taint and reject in the lab batch path. It needs no C change and no ruling, turns the six red tests into a standing gate, and is the oracle that makes O3 and O4 safe. Every lab run from then on states which rules it checked and whether it was clean. Treat existing fight data from layouts with blocks, hills or slopes as suspect until re-run through it.
2. Westley's rulings (below).
3. O3 with walker routing as one cascade, then O4.
4. O2 and the test-architecture changes alongside, then O5.

## Rulings needed from Westley

1. Cover against blocked cells: units never enter a blocked cell (recommended; also stops the jitter) or fire adopts an exemption for a unit standing inside one.
2. Sticky targeting (R-087-03): keep an engaged target while it stays alive and in range, or always shoot the nearest.
3. Fire after moving: may a unit fire on a tick it moved? Recommended: no (a hold flag the fire pass respects), which writes "a firing unit does not move" into the rules.
4. Scope: build R-087-09 (give up a blocked target after 1 s) and walker routing around planar blocks, as one cascade or separately.
5. Warden numbers: the engine's heal and damage reduction match neither the bible nor ALG-60; which is right?
6. Layers at hill rims: whether flicker and the 24 to 78 wu layer jumps are acceptable behaviour or a defect, and whether seeing 340 wu down a slope without being able to shoot is intended.
7. Thresholds for the checker (Westley owns them): the one-metre depth for "inside a cell", the 20-tick window for a stuck target, the 28 wu overlap slack.

## Caveats

- The sweep is the lab's own configuration, 67 catalogue layouts; "clean" results are not proof. Some invariants (overlap, pacing, stuck walkers) are soft and flagged as such in Appendix C.
- Appendix A is source reading only.
- I10s (Warden) was measured on single-hit samples; the bible and ALG-60 should be re-read before changing either side.
