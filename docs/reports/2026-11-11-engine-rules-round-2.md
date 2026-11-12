# Engine rule fixes, both rounds: what landed, what it measured, what is open (2026-11-11)

Bug fixes, not a story. Spec: `docs/northstar/plans/engine-rules-2026-11-08/spec.md`. Evidence behind it: `docs/reports/2026-11-07-rule-enforcement.md`. Method throughout: one agent writes the failing tests, a different agent builds, a third verifies; every fix was then broken on purpose to see its tests go red. Round 1 landed as `53f6b053`; Round 2 is this landing.

## What units now do

Round 1
- Never enter an obstacle; walkers route around them.
- Do not fire on a tick they moved; group members keep the pause after a shot.
- Keep a target lock; a unit halting to fire no longer loses it to a false "arrived".
- Wardens do not stack.

Round 2
- A unit whose target is in range with the line blocked walks to a spot with a clear line; with none within 1 second it gives the target up and does not take it again for 100 ticks or until the line clears (R-087-09).
- A guard steps toward a seen enemy it can engage from within 200 wu of its post, fires when stopped, and returns; a push never carries it past the radius (R-096-08, R-208-01).
- High ground can fire down: fire and sight now answer the hill geometry the same way (R-098-02). Before, a unit on a hill saw an enemy below in range and could not shoot it.
- Weapon reach on the ground counts the height difference (R-087-10, provisional scope, Q-087-03).
- A unit changing layer no longer jumps (R-004-08 as the spec reads it).
- An attack-moving unit hit by something it cannot see or reach moves 200 wu away, then resumes (R-087-01, ruled 2026-11-06, the unbuilt half).

The lab's rule checker (`scripts/skilllab/invariants.py`) judges eleven rules after every tick and now runs on every lab path (fight, search, scan, probe, sweep rows), not only arena fights. A fight that breaks a rule is marked invalid; a rule that cannot be judged in a run is listed as suspended with the reason; a run nobody judged reads "not judged", never clean.

## Measured

Sweep of 199 lab fights (counts are unit-ticks):

| Rule break | 2026-11-07 | After Round 1 | After Round 2 |
|---|---|---|---|
| Unit inside an obstacle | 1,159,428 | 0 | 0 |
| Fired after moving | 1,168 | 0 | 0 |
| Moved inside the pause after a shot | 786 | 0 | 0 |
| Wardens stacking | 859,729 | 0 | 0 |
| Holds a target it cannot shoot, not closing in | 3,547,771 | 314,851 | 2,312 |
| Sees across layers, cannot shoot | 184,976 | 171,364 | 0 |
| Jump at a layer change | 951 | 910 | 0 |

Determinism: 28 pairs run twice, 0 mismatches.

The four stage 4 fights, 20 seeds each with sight-off controls (160 fight files): the checker reports nothing. Cover: red wins, 3 left. Vantage: blue wins, 19 left. Both traps: red wins (22 and 30 left).

Suites on the landed tip: `tests/csim` 134 failed against a baseline of 159, none new; `tests/skilllab`, `tests/qa`, `tests/method` none new. Recordings that moved were re-recorded only after the new fight passed the checker; each re-record names the fix that moved it.

Not done: the play proof. `scripts/play.sh --check` under a virtual display starts the game and reaches its first scene, then rejects on a blank screen capture; main before these landings rejects the same way. Westley playing main is the proof.

## What the work found beyond the fixes

- The checker was wrong three times in ways its own tests did not show: it excused any jump beside a friendly unit (hiding 500 real jumps in one fight); it reported every unit of a terrain-less fight as outside the map (30,536 reports in one small fight); it read the layer heights before the engine filled them, so every fight was judged flat. Each was found by running it on fights it was not designed around.
- Fixing "cannot fire down" stalled a trap fight until the unseen-fire rule was built: one unbuilt ruled rule was hiding behind another defect.
- Nine tests are red on main on no known-red list (two detector controls, one protocol-version case, six for a client seam never built).

## Open after this landing

1. **Westley's answer to the StarCraft 2 report** (`2026-11-11-starcraft2-movement-targeting.md`): notice distance, whether a lock ends when the target leaves weapon range, threat first. Units still walk toward enemies beyond weapon range and keep a lock when another enemy walks closer.
2. **Spherical reach in the air** (Q-087-03).
3. **Slope layouts pile up.** In the sweep, walkers standing still with a destination rose from 95,380 to 395,318 and units closer than 20 wu from 420 to 19,862, mostly on L-0084 and L-0063. Suspected, not shown: the layer-change clamp cutting collision pushes on slopes. Needs a trace.
4. **Twelve guards drop one target at once** (L-0084 seed 1, tick 1776): the target alive, seen and in range. Unexplained. Needs a trace.
5. **A unit does not close its last step:** it stood still for 20 ticks with its target 1.3 wu out of range until the give-up dropped it (cover close-up, tick 356, unit 13). Held open by a marked test.
6. **Checker gaps with a known cause** (8 reports on L-0084): the nearest-pick check does not yet know a guard's reach from its post, nor slant range.
7. **Idle units moving:** 126,746 unit-ticks in the sweep where a unit with no order and no target moved, 88% within 2 seconds of taking damage. Expected from the guard step and the move away from unseen fire; not confirmed case by case.
8. **Not saved:** the give-up count and exclusion list are not in save files; a loaded game restarts them. Saving them is a contract story.
9. **Draft readings** made where the rule text was silent: `DEC-engine-rules-round2-2026-11-11`, nine items, each Westley's to veto.
10. **Both traps are still won by red**, against Westley's 75% for blue. With every ruled rule built this is the traps' result under the current rules; item 1 is the pending change that bears on it.

## Draft numbers (Westley's to change)

Give-up after 20 ticks (from the rule); exclusion 100 ticks, 4 targets remembered; guard radius 200 wu; slope step slack 1.0 wu; checker: obstacle depth 1 wu, push radius 40 wu, step slack 1.3 wu, nearest tolerance 1.0 wu, return-fire window 4 ticks, unseen-fire window 60 ticks.
