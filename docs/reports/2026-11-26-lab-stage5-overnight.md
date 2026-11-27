# LAB stage 5, overnight run: morning report (2026-11-27)

Staircase: the simulation LAB. File: `docs/northstar/story_reviews/westley/lab-staircase.md`. Stage: "Stage 5: facing, arcs and height bands". Not the beta.

For Westley. Plain words first. Page with the clips: https://claude.ai/artifact/Pcxn1WbaGdkEvfnxZtBtQM (ledger row A-011). Plan and decisions log: `docs/northstar/plans/lab-stage5-2026-11-26/`. Story: `docs/stories/H-091.md`. Branch `s/lab-stage5`; nothing merged, nothing pushed; beta B5 untouched. The branch also contains the docs-only branch `s/artifact-a009` (the ledger rows for pages A-009 and A-010 and his rulings of 2026-11-25), merged in so the ledger's ids stay in sequence; merging lab stage 5 to main lands those docs too.

## In one paragraph

Lab stage 5 is built and measurable. Units now have a front that matters: a unit cannot fire at a target outside its firing arc; it keeps the target, turns, then fires. The lab can switch this on, sets each unit's facing, and records for every shot whether it hit a front, a side or a rear and how far up a slope each unit is; the replay draws it. The finding is that the rules as they stand make neither the flank nor the climb decide a fight. A flank lands (in the pinned-flank scene 233 of 540 hits on the holders are on their rear) but costs the flanked side only a turn delay of about 12 ticks, because nothing makes a rear hit hurt more and units turn half round in under a second. The climb at the engine's own number is 7 percent slower, 8 ticks late to the fight, and cannot be seen; at a test number of 2.0 it is 113 ticks late and can.

## Done-when, honestly

"He sees a flank hit a side and the climb slow the attacker." The flank hit is visible as marks and counts. The climb slowing the attacker is visible only in the labelled 2.0 comparison. Neither changes who wins. Whether that is acceptable is his.

## What was built

1. Engine: the firing arc, E-13 R-100-04 (his ruling of 2026-10-13), read from a setting that already existed. Off by default; with it off every earlier fight is byte-identical.
2. Lab: the switch `--facing on` with `--arc-deg` and `--slope-up-div`; facing set at spawn; the fight file gains the arc, `climbing` per unit and a list of hits with front, side or rear.
3. Measures: hits by direction, the delay before a flanked unit answers, the climb's slowdown; a check that no shot leaves outside the arc.
4. Seven probe scenes (front, side, rear, pinned flank, climb flat, climb slope, a drafted objective ring), marked as drafts for his redraw.
5. Replay: arc outlines, hit rings (white front, orange side, red rear), a climb bar, band marks.
6. Thirteen clips with facts, and the arc sweep.

## Numbers (seed 1)

| Fight | Winner, survivors | Last tick | Hits on the holder, front / side / rear |
|---|---|---|---|
| Pinned flank, arc 90 | attacker, 13 | 914 | 307 / 0 / 233 |
| Pinned flank, arc off | identical, frame for frame | 914 | 307 / 0 / 233 |
| Front, arc 90 | holder, 3 | 2404 | 461 / 0 / 0 |
| Side, arc 90 | attacker, 2 | 2690 | 530 / 8 / 0 |
| Rear, arc 90 | holder, 4 | 2391 | 432 / 0 / 8 |
| Climb, flat | attacker, 6 | 2189 | first shots tick 338 |
| Climb, slope at 1.1 | attacker, 4 | 2517 | first shots tick 346 |
| Climb, slope at 2.0 | attacker, 5 | 2666 | first shots tick 451 |
| L-0084, sight on | holder, 12 | 1987 | 364 / 0 / 0 |
| L-0067 | holder, 20 | 1415 | 774 / 0 / 0 |
| Objective ring (draft) | attacker, 2 | 2570 | 527 / 5 / 4 |

Arc sweep on the rear attack: the holder's answer delay is 8, 11, 12 and 14 ticks at 180, 120, 90 and 60 degrees; survivors do not move. With the arc off the delay is 23 ticks, the slowest; not traced.

## What does not work, or is not done

- A flank does not decide a fight; the climb at 1.1 cannot be seen; "a longer sight" from height is not built beyond the one-way sight that existed.
- One arc width for every unit type, not his three per category (three new settings: a contract story).
- The cone-shaped area attack (`set_cone`, R-082-10) was left a stub; it is a different rule from the firing arc.
- One test is red: the 2.0 climb's speed tolerance (3 of 8 units at 0.553 to 0.561 against 0.55).
- The arc applies on the shipped movement path only.
- In his flank layout L-0067 nobody walks a flank route.
- Look problems: arc outlines overlap into a tangle in a crowd; hit rings are thin; units are small in the pinned and climb clips; some red units draw darker, not traced.
- Nothing was added to the approved-fights list. The known reds on main (seven lab checks) are unchanged.

## Lab stage 4 dependencies

Nothing stage 4 governs was changed: acquisition, the lock, return fire, orders and keep-walking are as on main. Flank and arc scenes run with sight off; only the L-0084 clip uses the unsigned sight rules. Every scene is hold against attack-move, so "same exact spot" does not arise. When stage 4 settles, each clip is re-recorded with one command; no stage 5 code changes.

## Decisions made alone

Twenty-three, in the decisions log. The ones that matter: the firing arc was built instead of the cone attack the staircase line names (L2); one engine change, off by default (L3); one arc width for all types (L4); the pinned flank scene was added after the first measurements (L16); the engine's climb number was kept and 2.0 shown beside it as a test (L7); the red tolerance test was left red (L20); the Architect looked at frames (L13). One process slip: the replay's tests were strengthened after the build without the required trailer, then cleaned with it (L18).

## What was verified, and what was not

- Tests: csim arc 30 passed; lab run 29, snapshot 30, measures 18, arc check 10, scenes 44, pinned 13 passed and 1 failed (the tolerance); replay stage 5 18; the stage 3 and 4 umbrellas and the older replay files pass; docs lint 179 passed, 1 skipped. Mutations turned tests red in every lane.
- Byte identity with the switch off: confirmed three times, by hash.
- Every number above was recomputed from the every-tick fight files by a second agent: no disagreement.
- By eye: seven still frames from four clips. Not done: watching any clip through; any look at the front, side, objective-ring, L-0067, arc-off or arc-60 clips; the page on a phone.

## What I need from him

1. What a flank should cost (leave; slower turning; a damage rule for side and rear hits; turn on the nearer threat). Recommendation: sweep slower turning in the lab first.
2. The climb number.
3. Whether height should see or shoot farther.
4. Yes or no to the per-category arc widths contract story.
5. A redraw of the flank layouts.
6. The tolerance for the red check.
7. Whether to merge `s/lab-stage5`.
