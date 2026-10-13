# The visible game programme (plan, 2026-10-07; method rev 2, 2026-10-10)

**Status: IN FLIGHT, paused by Westley 2026-10-10 09:15; resumes under method rev 2 (below) on his resume command.** The lane table below is the programme's only status; ROADMAP section 1 points here, the journal is `git log` (`scripts/journal.sh`), and no chat memory carries lane state beyond a pointer. When every lane's stories are `Seen` this header becomes DONE with the date.

| Stage | State | Date |
|---|---|---|
| 1. Pre-flight (ten read-only scouts, the spec, the script) | done: reports in `preflight_2026-10-07/`, spec `2026-10-07-visible-game-spec.md` rev 1, rulebook | 2026-10-07 |
| 2. Audit loop (Opus 5.5 issues with evidence; a Sonnet parallelism audit beside it; three rounds) | done: rev 4 was the launch text; Westley's go line in "Decisions taken" | 2026-10-08 |
| 3. Execute, method rev 1 (six component lanes in flight, one gate, Fable dispatching) | 98 of 118 planned pieces landed plus 37 unplanned, 0 stories Seen, 62 test-defect rulings, 34 scripts, $1,487; every lane's first look failed with green tests. Measured in `retro_2026-10-10/` | 2026-10-07 to 10-10 |
| 4. Retrospective and method rev 2 | done: `retro_2026-10-10/README.md`; Westley picked all nine changes 2026-10-10; grafted into this file, the spec (rev 9), CLAUDE.md, `workflows_2026-10-07/rules.md` and `dispatcher.md` | 2026-10-10 |
| 5. Execute, method rev 2 (skeleton per lane, pre-gate, Sonnet Dispatcher with the Architect on call, tests on the built tree, three slots) | waits for Westley's resume; first jobs in "Stage 3" below | |

## Lane table (the one status location)

Rules for this table: the landing clerk flips the lane's row in the landing commit (sha, next piece); the Dispatcher reads it and writes nothing else about status; `scripts/specfactory/status_check.py` checks every sha here is on `origin/main` after each landing. "First look" is the date a human saw the lane's shot and what he said. "Westley row" names the row in ROADMAP section 3's "Now" table that the lane waits on.

| Lane | On main | Next piece | First look | Westley row |
|---|---|---|---|---|
| Contracts | K0, K-a (sim, pipe, bridge, split), K-f, K-h, K-d, K-e (ABI 6), K-e2, K-e3 (save 9), K-e5 (save 10, ABI 7) at 8bdb64f, K-e6 (lots on full frames) at 3a2ffd9a landed; K-e4 red tests on `push/vg-k-e4-tests` | K-e4 lands in the E1 skeleton batch | n/a | none |
| Harness, method rev 2 | `pre_gate.sh`, `status_check.py`, `journal.sh` at f089fccb; spec_provenance.py at 573d00c | none | n/a | none |
| A battle screen | A1 to A21 at 4d4babf8; twelve plays pass in both eras in the gate | one fix piece per verdict, nothing until then | 2026-10-08 22:30, 11 of 12 "no"; A19 to A21 since, not yet seen | 2 |
| B galaxy | landing 12 at 5333e1a0; B22 and B23 landed (below); three plays pass | Westley's verdict on the new B look rows (S-106, S-107, S-108); further B look work waits on it | reviewer unclear, no, unclear (`story_reviews/B.md`, run 20261012-1716-33e3bc2); Westley 2026-10-12 as relayed: S-106 approved, S-107 rejected (lacks the galaxy-bubble spec Step 5, to be built as VG-B25-vast-space), S-108 pending | 1 |
| B galaxy, B22 (`VG-B22`) | B22 at a4573fec (ball layout, camera, field grid; TD-VG-B-12, TD-VG-B-13), landed with shots and review rows at 5ad4e7df; three plays pass | none; its looks were rejected as not matching the prototype and are fixed by B23 (next row) | reviewer no, no, unclear (`story_reviews/B.md`, run 20261011-1505-a4573fe); Westley: rejected, does not match the prototype, fixed by B23 | 1 |
| B galaxy, B23 (`VG-B23`) | B23 at 33e3bc2: the prototype's numbers (ball 50, camera 25, bands 37.5 / 32.5 / 20 / 12.5, dots, filaments, labels, environment); TD-VG-B-14 | Westley's verdict on the new B look rows (S-106, S-107, S-108); further B look work waits on it | reviewer unclear, no, unclear (`story_reviews/B.md`, run 20261012-1716-33e3bc2); Westley: S-106 approved, S-107 rejected, S-108 pending | 1 |
| C ground 3D | C1 to C11, VG-C-wire, K-c6, C6b at bcad1954; S-236 and S-001 plays pass | nothing until verdicts; S-004 is a spec gap, S-132 a finding | reviews on `push/vg-c-reviews-2` (run before the fixes) | 4, 5 |
| D space landscape | landing 4 at 1fdeb1c0 (D2 to D8, the pipe-field fix); rulings TD-VG-D-6 to D-11 | E-17 and S-007 plays (no eyes until the shots exist); the D view hook after E1p | none yet | none |
| E settlement and economy | part a at 8f76be4d (K-e2, K-e3, E1b to E1h, E1i; TD-VG-E-2 to E-12); part b records on main (spec section, VG-CONTRACT-E4, TD-VG-E-13); skeleton K-e4 + E1k-skel + E1p-a at c9c7545f; S-193 re-shot (VG-E1-SHOT) at b5024dc9; four part b test branches on origin (E1k, E1l, E1o, E1p-b); settlement port (K-e5 39927051, E1q-field, E1q-lots) at f79f91c; K-e6 (full frames carry lots, closes `FINDING-lots-full-frame`) at 26d0a3bf; S-237 re-shot into the same row after K-e6 (Westley pending); E1k settlement look (S-237 re-run, Westley pending) at bb6d652 | Westley's verdict on the E1k S-237 re-run; then fan-out (E1l, E1o, E1p-b) on the S-237 verdict (Now row 6) | 2026-10-10 S-237 rejected ("far too circular") | 6; Q-235-01 is row 3 (E1m, E1n, S-235 held) |
| E settlement and economy, part c (`VG-CONTRACT-E5`, K-e5 contract piece) | K-e5 (save 10, ABI 7) at 8bdb64f; spec lane E1 part c (rev 10e) on main; settlement port (K-e5 39927051, E1q-field, E1q-lots) at f79f91c; K-e6 (full frames carry lots) at 26d0a3bf; the first post-port S-237 shot (run at 03:16, built on 34bbc3b) was a stop (the play saw 4 of 263 lots) and is retired by the K-e6 re-shot | Westley's verdict on the S-237 re-shot (Now row 6) | S-237 re-shot after K-e6, Westley pending | 6 |
| F Steam phase B | 1398ba16 (F5 match mode); phase A e63483f6 | E-19 plays; lobby and depot script | none yet | none |
| Contracts, K-e6 (`VG-CONTRACT-E6`, lots on full frames) | in flight (spec rev 11, lane E1 part d; its pieces.toml row is added by another clerk) | K-e6 pipe frame change, second-Fable audit, then the S-237 re-take | n/a | none |
| Contracts, K-d1 (`VG-K-D1`, non-stepping full request keeps state bit 1) | K-d1 at daf6234 (`ev_reset()` now runs only when n > 0 in `handle_tactical_step`; finding `FINDING-delta-death-unit` closed) | none | n/a | none |
| A battle screen, A18 (`VG-A18`, opening frame fits every own unit) | nothing yet; queued (Architect ruling 2026-10-12; finding `FINDING-camera-start-framing`) | `_framing_zoom` in `tactical_view.gd` (:978-995) fits all own units inside the viewport with one tenth of the viewport as margin, [DRAFT-a18-margin], clamp at ZOOM_MAX/ZOOM_STEP, `[B R-103-01]`; after A16, before VG-E1's remaining pieces (re-sequenced 2026-10-12, spec rev 12d: the opening frame is the player's home, `[B R-103-01]`); `tests/test_tactical_camera.gd` is the red test (the three framing groups: live, top-edge, bottom-right-corner; the four edge-scroll cases are `FINDING-edge-scroll-xvfb`); `tests/test_tactical_view.gd` :309/:314 are stale pins re-pinned under TD-VG-A-13 (`FINDING-view-c53-framing-pin`) | none yet | none |
| W walk routes (`VG-W1`, `VG-W2`) | W1 planner at 6621ef96 (scratch reuse, height, mask and edge caches, `gen_id`; 600-walker tick median 64 ms to 10 ms, routes byte-identical); W2 queued (spec rev 12, Lane W; Westley's go 2026-10-11) | W2 stored routes (save 10 to 11, contract piece, second-Fable audit); the 600-walker tick time is the shot | n/a, sim only | none |
| F Steam phase B, part 1 (`VG-F-SKEL-A`, `VG-F-SKEL-B`) | F-SKEL-A/B at dbe480a: Steam-less lobby skeleton (UDP transport, local lobby backend, --net-local), two-process S-141 and S-142 green, S-140 red under FINDING-net-first-tick until VG-F-NETTICK, S-143 and S-241 red until their later F pieces; works: tests and plays pass, sees: shots queued, not Seen | VG-F-NETTICK (net first tick), then Westley verdict on the F.md row S-141; lane F fan-out waits on it | S-141 shot queued (`story_reviews/F.md`), Westley pending | none |
| F Steam phase B, part 1b, net first tick (`VG-F-NETTICK`) | F-NETTICK at b12b47a | A16 (depends on F-NETTICK) | none yet | none |
| E settlement and economy, part e (`VG-E1R`, `VG-CONTRACT-E7`) | nothing yet; queued (spec rev 12; Westley 2026-10-11 on the starting force) | E7 contract piece (starting force by strongpoint share), E1r placement clears; order against W2 by the Dispatcher; K-e6 is its own row above | none yet | none |
| A battle screen, A16 and A17 (`VG-A16`, `VG-A17`) | A16 at b7ea389: To-layer buttons in the strip, Q/E, qa_state focus_layer; A17 at 9c690a0: scroll helper measures game ticks and zooms out; S-134, S-136 green on the hand runs (S-134 182.97 s, S-136 113.86 s); A17 still queued | Westley's verdict on the S-002 row (story_reviews/A.md); A18 (VG-A18) next, same file | S-002 re-shot 20261013-0103-00d5637 (reviewer yes, Westley pending) | none |
| C ground 3D, S-004 play fix (`VG-C-s004`) | S-004 play fix at bfd7f1c: green, the play now aims at the top edge of the nearest slope and a walker reaches the upper layer past the midline (TD-VG-C-4); no finding | none for the play; if red, the finding goes to the Architect (no shot queued: no C.md, no owner row) | none yet | none |
| Harness, method rev 3 (`HARNESS-provenance`) | nothing yet; queued (spec rev 12, lane H part 3; Westley 2026-10-11: "#14: approved"); rules.md sections (c) and (d) updated | `spec_provenance.py` lint and its test, then the Architect tags the whole spec (rev 13) | n/a | none |
| E settlement and economy, E1k look (`VG-E1K`) | nothing yet; queued (spec rev 12d/12e) | the settlement look from the mockup (heights, footprints, jitter, yaw, cliffs, hidden street mesh), then the S-237 re-run for Westley | none yet | none |
| E settlement and economy, prototype (`PROTO-settlement-banding`) | nothing yet; queued (spec rev 12d; prototype gate) | the banded contour look as a prototype under `scenes/mockups/settlement/`, after E1k; Westley approves before any plan | none yet | none |
| C ground 3D, unit scale (`VG-C-unitscale`) | VG-C-unitscale at 53ede72 (`BODY_RADIUS_WU` 20 to 11.5, `SHADOW_RADIUS_WU` 18 to 10; `tests/test_vg_c_unitscale.gd` green; `FINDING-unit-draw-overlap` closed) | none; no look of its own, rides on E1k's S-237 re-run | none yet | none |
| B galaxy, dot colour (`VG-B23b-dotcolour`) | VG-B23b-dotcolour at 5f3ee95: the dots take main's colouring back; FINDING-dot-colour-pixels closed; TD-VG-B-15 | Westley's verdict on the S-106 dot-colour row; VG-B24 follows | S-106 queued (`story_reviews/B.md`, run 20261013-0216-5f3ee95), Westley pending | 1 |
| E settlement and economy, production slots (`VG-E-prodslot`) | nothing yet; queued (spec rev 12d) | after `VG-CONTRACT-E7`: production places each new unit in the nearest free 30 wu slot (finding `FINDING-production-stack`, `TD-VG-E-29`) | n/a, sim only | none |
| B galaxy, B24 layout (`VG-B24`) | nothing yet; queued (spec rev 12d/12e) | after B23 and the dot colour: placement follows the sim graph; density question `Q-B24-01` is Westley's | none yet | none |
| B galaxy, B25 vast space (`VG-B25`) | nothing yet; queued (spec rev 12d/12e) | after B24: dim wash, four star layers, wrapping motes; GPU check on the RTX 3060 | none yet | none |
| B galaxy, B26 chronicle one entry at a time (`VG-B26-chronicle-serial`) | nothing yet; queued (Westley's S-108 verdict 2026-10-13, R-069-03 rewritten, `FINDING-chronicle-concurrent-print`) | independent of B24/B25 (different files): the scroll panel prints the next entry only when the previous has finished; then the S-108 re-run | S-108 approved with this note (`story_reviews/B.md`, run 20261012-1716-33e3bc2) | none |
| Harness, gate user directory (`HARNESS-userdir`) | nothing yet; queued (spec rev 12e) | a gate, a test run and a desktop play never read or write the machine's user directory | n/a | none |
| V sim viewer (SV-1..SV-3 landed; SV-0 retention override queued behind VG-CONTRACT-E7, VG-W2, VG-E1R) | SV-1 `pipe_session.py`, SV-2 `history.py`, SV-3 `viewer.py` at d7d01f40 (new files under `scripts/simviewer/`, spec `2026-10-12-simviewer-spec.md`); works: `tests/simviewer/` 67 passed, 1 xfailed (pick 0 / total failure, expected until SV-0); sees: tooling; first-look shots queued (`story_reviews/V.md`) | SV-0 (mission_end retention override on the pipe), queued behind VG-CONTRACT-E7, VG-W2 and VG-E1R | none yet | V.md rows pending |

## Method rev 2 (Westley picked all nine, 2026-10-10)

The three-day record and the comparison with how large organisations build are in `retro_2026-10-10/README.md`. The rules, each with the measure that shows it working:

1. **Skeleton per lane before fan-out.** A lane's first piece is the thinnest path in the real scene from the real frame, screenshot queued, Westley sees it; contracts freeze after it runs; fan-out waits for his verdict. Measure: hours from launch to a seen pixel (was about 28), contract amendments after freeze (were 4), look-fix pieces after fan-out (were 10).
2. **Two-tier gate.** `scripts/specfactory/pre_gate.sh` (about one minute: make, every lint, footprint, owner rows, noise, the piece's own tests) runs in the builder's worktree before the push and in the clerk's before it takes the lock; the full gate (25 to 55 minutes measured) runs once per landing batch. Measure: landing attempts per landing (were up to 14), non-semantic full-gate rejects (were about 15 of 37).
3. **Dispatcher and Architect on call.** A Sonnet 5.5 chat runs `workflows_2026-10-07/dispatcher.md`: launches, waits on the Workflow notification, lands through clerks, keeps this table, queues shots. Judgement comes from the Architect: a Fable chat that restarts past about 150k context, or the read-only `architect` agent spawned by the Dispatcher with a one-page brief. No dollar cap (Westley 2026-10-10); costs are recorded per lane run. Measure: Fable turns per day (were about 340), Fable dollars per day (were about $375).
4. **Tests on the built tree, ruler in the script.** The test writer runs its red test on the branch holding the stub or the previous piece, pastes the failing assertion line, shows the positive control green, and for scene tests dumps the qa_state keys it relies on from one real run. A builder that meets a test that looks wrong stops with `test-defect:` and the script's ruler (Sonnet, the rulebook's decision procedure) rules it under a ledger row or hands the Architect a brief. Measure: rulings per landed piece (were 0.46), builders stopped by test defects (part a: 6 of 7).
5. **WIP capped at three slots.** Two build workflows and one landing at any time; the next lane starts when a slot frees. Measure: concurrent workflows (were 5), resume events (were about 35).
6. **One status location.** This table; ROADMAP row points here; `scripts/journal.sh` is the journal; memory holds a pointer and the last three steps; `status_check.py` after every landing; a Sonnet auditor weekly for rulings against epics; `method_check.py` at every compaction of either chat (Westley 2026-10-10: the rules must hold through compaction after compaction, not only the week they were written). Measure: stale-copy drift findings per check (were 5 to 8); DRIFT lines per compaction report (target 0).
7. **Shot per piece.** Every player-facing piece's clerk report carries its screenshot path and the clerk adds the queue row; the lane's next look piece waits for the verdict on the previous one. Measure: pieces built before the first human look (were 11 to 18 per lane).
8. **Pace to Westley.** ROADMAP section 3 "Now" holds at most six items ordered by what they unblock; the "No eyes needed" list below runs while he is away; nothing else does. Measure: items waiting on him (were 23), look passes without a verdict (were 4).
9. **Keep.** One owner per file, tests first, the determinism stages, fresh-context auditors, `rules.md` cited by every brief, the flock line, `.wt-done`, the review queue format, the rulebook rows.

Scorecard, filled by the record clerk after each lane run (first column is the three-day value):

| Metric | Rev 1 | E1 skeleton | E1q port | E1 fan-out | next |
|---|---|---|---|---|---|
| Hours to first seen pixel | about 28 | |  | | |
| Landing attempts per landing | up to 14 | |  | | |
| Non-semantic full-gate rejects | about 15 | | 0 (gate clean) | | |
| Rulings per landed piece | 0.46 | | 1.0 (TD-VG-E-23, TD-VG-E-24 over E1q-field and E1q-lots) | | |
| Pieces built before first look | 11 to 18 | | 2 (E1q-field, E1q-lots) | | |
| Fable consults | about 340 turns per day | |  | | |
| Concurrent workflows | 5 | |  | | |
| Drift findings per check | 5 to 8 | |  | | |

E1 skeleton column: no run data was handed to the record clerk, left blank. E1q port column (`wf_3253958a-378`): 10 agents first pass, 6 second pass; subagent tokens 972,567 + 283,153; the join check failed first time on 11 unexpected reds (an argtypes leak and two superseded K-e5 pins), ruled as TD-VG-E-23 and TD-VG-E-24, landed at f79f91c1; gate clean; the play found the full-frame lot gap (`FINDING-lots-full-frame`). Other cells need data the clerk was not given.

**No eyes needed** (runs while Westley is away, in this order): the three harness pieces (`vg-harness-method.js`); a worktree cleanup clerk (465 worktrees under `~/Projects/om-push/wt/`, 98 with `.wt-done`); a branch triage clerk (26 unmerged `push/vg-*` branches: landed, superseded or pending, one line each, no deletions); the 31 `pieces.py --check` owner overlaps without `depends_on` (record clerk, rows only); lane D and lane F story plays run and queued; the walk-route fix piece (FINDING-walk-route-replan) once the Architect specs it; lab runs in the night slot.

---

## Context

On 2026-10-07 Westley played main and found the tactical view is 24 px squares on grey: no objective marker, no cover, no fog, no unit shapes, a toy galaxy. The accounting (same night) showed why: the 22–28 Sep push ported the whole simulation to C (2,203 → 31,832 C lines, +88k test lines, the pipe, the loop, the gate) and built a 672-line "minimal tactical view" as a stub; the Python-era battle screen (21 files, 4,682 lines: per-type units, layer rings, fog, cover, objective beacons, an 802-line HUD, effects, 3D camera) was deleted on 1 Oct and never replaced. Every approved mockup (galaxy field, walkers, land landscape, space landscape, settlement) sat on a branch with no integration row. The playthrough gate checks that screens open and a mission ends, never what the player sees. The 30B QA ran one night and never reached a fight.

Westley's direction (2026-10-07): all approved prototypes go into the beta ("we're not launching a half-baked beta"); strategic depth (the simulation lab) stays the priority and keeps moving; the guards against this happening again are accepted; the programme runs in three stages: (1) a pre-flight that looks as far ahead as possible with self-healing options, (2) an Opus 5.5 audit of the workflow plan with evidence, investigated by the Architect, iterated until solid, (3) execution. The bible's user stories (239 in `docs/bible/stories.md`) are the "player sees X" spec and are acted out by the 30B, or a Sonnet/Haiku agent when the CPU is busy with lab runs.

This file is the programme design. Stages 1 and 2 produce the workflow spec and script; stage 3 runs it. Nothing is spawned while plan mode is on; stage 1 starts on approval.

## Decisions carried in

| Decision | Source |
|---|---|
| All five approved prototypes in the beta, the settlement with its economy play (lots, workers, placement, the economy screens); Westley answered the economy questions in batches 1 to 12 (on main: e.g. 464c2505 settlements, 829f2444 strongpoints and weather, b928b937, a3d15377); small open rules may be decided by the Architect in the interest of time, each documented as a liberty in the spec's "Liberties taken" table and the register | Westley 2026-10-07 |
| No date deadline: "done right than fast"; efficiency, parallelism and staying on the goal outrank any date; the beta ships when every lane's stories are Seen | Westley 2026-10-07 |
| Lab stays first: its reports are answered before integration's; lab runs at 8 workers by day, 12 by night | this plan |
| Stories are the acceptance spec; a lane is done when its stories are acted out and seen | Westley 2026-10-07 |
| Multiplayer stays in the beta (Steam phase B runs as lane F; its tactical hookup follows lane A) | existing spec |
| Tests first for every piece, by a different agent; builders never edit tests; a test is changed only under a ledger row | CLAUDE.md |

## The lanes (what gets built)

Each lane is a workflow stream with its own clerk; lanes share no files except through sequencing noted below. Sizes are pieces (one file, about 100 lines each); each piece is tests → build → check.

| Lane | Delivers | Source material | Stories acted out (acceptance) | Pieces | Sequencing |
|---|---|---|---|---|---|
| A. Battle screen | Per-type unit shapes, HP bars and layer rings, layer strip and dimming, fog, cover and obstacles, objective beacons, selection and control groups 1–0 with the Comb, the HUD (objectives, selection, four-beat ticker, reinforcements, ability ring, layer strip), shots/hits/deaths, abilities, camera (pan, zoom to the map band) | Legacy `scenes/tactical/` at `009c99ac^` (the feature inventory, re-derived on the C pipe); `push/tv-read` as source; E-16/E-18 `references/` | Seen-reachable and blocked lists in the spec (rev 4) | 20 per-file pieces (+ the contract gates K0, K-a, K-f, K-h) | First after the contracts; the view chain A12 → F5 → C5 → E1p → D hook |
| B. Galaxy | Bubble field, territory glow, borders, war flashes, pan/zoom/orbit/focus, mission-to-galaxy transition | `push/galaxy-field` (4,658 GDScript + 554 shader lines, built 2026-10-02; look approved by Westley 2026-10-07); `scenes/shared/world_view/` shell renderer | S-106, S-107, S-108 | 3–4 | Independent; approved, starts with the first lane wave |
| C. Ground | Stage 3 (built on `push/terrain3-land-2`, two small reds) landed first; then the 3D land landscape: camera, picking, box-select, height array in the frame (contract), mesh from the mockup; walkers and flyers drawn as the mockup draws them | `push/proto-land-iter` (8,634 lines), `push/proto-walkers` (1,071 lines), stage 3 spec rev 3 | S-236, S-001, S-004, S-207, S-132 (walkers), stage 3's era toggle | 6–8 (+1 contract) | Stage 3 lands first; the 3D view after lane A's view structure |
| D. Space landscape (HELD until Westley's routed answers: Q-STAGE3-03, Q-166-02, R-188-05, S-246, the kit questions) | The space kit generator in the sim and the client drawing it for space missions, with the vision-tube note (Q-S3-01) recorded as a later item | space-kit mode spec `2026-10-02-space-kit-mode-spec.md`, `scenes/mockups/` space landscape | E-17 space stories (S-166 group), S-007 | 5–6 (+1 contract) | After A (shares the view) |
| E. Settlement and economy | The economy play from E-22 and the answered batches: lots and placement, workers walking and gathering, buildings rising stage by stage, strongpoints, weather, the economy player's screen and the solo dial (S-230, S-231, S-233, S-235), the settlement look; sim systems first (contract: structures, workers, lots in the frame), then client | `scenes/mockups/settlement` (1,099 lines), E-22, E-15 (strongpoints, weather), batches 9 to 12 | S-209, S-210, S-211, S-212, S-230, S-231, S-233, S-235, S-237, S-238, E-22's 16 stories | 12–16 (+2 contracts) | Sim pieces now (disjoint from A); client after A |
| F. Steam phase B + shipping | Pipe frame flag, bridge wrappers, lobby + menu, tactical hookup, pipe per OS (W8), Steam depot upload script | Steam spec rev 6 | S-141/S-142 group (E-19), tester guide | 6 + 2 | W5 after A; the rest now |

Order and sizes: the spec (rev 3) planned about 103 per-file pieces, 103M tokens and an 18 h critical path; reality was 135 pieces, 847M raw tokens and 63 h (`retro_2026-10-10/plan_vs_reality.md`). Rev 9 of the spec carries no token cap (Westley 2026-10-10); costs are recorded per lane run in the scorecard above. The economy's second half (E2) waits on Westley's answers. No date is promised; the programme ends when the stories are Seen.

## Guards (written into CLAUDE.md as the programme's first commit)

1. **Visual definition of done.** A player-facing piece ships with (a) a deterministic element inventory from `qa_state()` asserted in its tests (which nodes exist, counts, presence of fog/markers), and (b) a screenshot set attached to its landing report, taken by the desktop driver at the story's moment, and seen by a human before "done". The gate gains a `look` stage: rejects a blank or near-uniform frame (colour histogram), attaches the screenshots to the report. Rev 2: per piece, not per lane; the landing clerk copies the shot into `docs/northstar/story_reviews/<lane>.md` with a queue row, and the lane's next look piece waits for Westley's verdict on it.
2. **Stories acted out.** Every lane names the stories it serves. For each story a `story play` exists: a scripted scenario for the desktop driver (`tests/qa/desktop`, `daemon_client.py`) that reaches the story's moment, captures `qa_state()` and a screenshot, and a model reviewer (30B through Agora when the CPU is free; else a Sonnet/Haiku agent) is given the story's words plus the bible `references/E-##/` images and answers "does the player see this? evidence". Answers land in a review queue Westley approves. The story's status in `stories.md` moves to `Seen` only on his approval. (Reuses the mission-plays harness of 2026-09-30 and the QA daemon.)
3. **No deletion without parity.** Removing a working feature requires a test that lists what it showed, green on the replacement first.
4. **Approved means scheduled.** The day a mockup is approved, ROADMAP section 1 gets its integration lane with position and owner; "approved, not integrated" is a visible state in every status report.
5. **Reporting.** Every status carries two columns: works (tests) and what the player sees (stories Seen). "Stub" is said when it is one.
6. **Play it.** The 30B plays current main nightly after each landing (screenshots to the review queue); Westley or the Architect looks weekly at minimum.
7. **Drift check (CLAUDE.md rule).** Rev 2: status lives only in the lane table above; after every landing `scripts/specfactory/status_check.py` diffs that table, `pieces.toml` and the review queue against git and fails on a mismatch; at least weekly a fresh Sonnet drift auditor checks rulings against every epic they touch and scope nobody asked for. Its report goes to Westley unedited; drift found is fixed before new lanes launch. The method itself: at every compaction a hook runs `scripts/specfactory/method_check.py` on the chat's transcript (`workflows_2026-10-07/method_check.md`) and the chat quotes its DRIFT lines to Westley before other work. (Rev 1 ran four auditor checks in three days at about 400k tokens each; three of them found stale copies of status, which the one-table rule removes.)

## Stage 1: pre-flight (look as far ahead as possible)

Read-only Sonnet scouts, one question each, evidence with file and line; the spec is written from what they find, never from memory. A failed precondition changes the spec, not the run.

| Scout | Question |
|---|---|
| Legacy inventory | Every drawn element and HUD control of `scenes/tactical/` at `009c99ac^`: which data field it read from the Python frame, and which C pipe frame field (or none) carries it today (`docs/architecture.md` frames). The "none" list is lane A's contract piece |
| Frame budget | Cost of adding structures, tactical events, height array, space-kit geometry to the frames at 20 Hz (full/delta period), measured with the probe plumbing |
| Galaxy field | `push/galaxy-field` vs main's `scenes/galaxy/`: what the branch replaces, what the game scene must keep (picking, MISSION button, plants), the shader cost on the RTX box and on an iGPU |
| Land 3D | `push/proto-land-iter`: the mesh builder's inputs (height field shape, cell size), its camera and picking; what `tactical_view.gd` must become (Node3D or SubViewport) and what breaks (box-select, QA driver's screen coordinates, `qa_state`) |
| Space kit | The space-kit spec's generator: does it exist in GDScript only; what a C port needs (determinism, Q16, the lint); whether the lab's `maps.py` sampler is the same thing |
| Settlement and economy | The full list of E-22, E-15 and economy-related rules now closed by batches 1 to 12 (grep the register for closed rows naming Westley since 2026-10-04 and the epics they folded into), the ones still open (candidates for Architect liberties), the sim's existing structure/lot/worker code (`mission.c` structure slots, `om_client_snapshot_read`, any `economy`/`worker` symbols), the mockup's inputs, and the pieces the economy play needs in sim, pipe and client |
| Story plays | Which of the 239 stories lane A–F serve; which already have a play in the 2026-09-30 mission-plays specs; what the desktop driver can drive (era arg, scripted clicks, screenshots) and what it cannot (3D picking) |
| Owners and collisions | Every file each lane touches, its owner row in `pieces.toml`, pairs that collide (expect `tactical_view.gd`, `c_bridge.gd`, `om_pipe.c`, `ouroboros_sim.h`, main menu), and the sequencing that keeps one owner per file at a time |
| Harness capacity | The gate's wall time per run today; how many gates per day the box can serialise; whether `regression_lab` and `playthrough` can run in parallel; the token spend per agent from the last four workflows (journals) for the budget |
| The stale-test rulebook | Every existing test that pins today's stub look (the 24 px squares, five menu entries, "no fog", etc.) so the script can rule them test-defects without a hop |

Output: `docs/northstar/plans/2026-10-07-visible-game-spec.md` (lanes, contracts, interfaces fixed, story list per lane, the rulebook, budget, kill rule) and the workflow script(s).

**Self-healing written into the script** (from today's stop causes):
- A test writer or builder stops on "existing test looks wrong": an in-script ruling agent (Sonnet) applies the rulebook; a test that pins a line the spec explicitly replaces (it must quote the spec line) is ruled a test defect with a ledger row and updated; anything else stops the lane and is listed for the Architect.
- "File outside my list": the script re-checks the lane's allowed file set from the pre-flight owner map; if the file is in it, the builder continues; else stop.
- Footprint REJECT on a new, unowned file: the clerk adds the owner row (new files only) and re-runs the gate once.
- A stage red on one test id: re-run that id up to twice; real only when it reds on a full-stage re-run (flake rule).
- Main moved: the clerk merges main before every gate (the merge-base harness fix is landing).
- A lane fails its check twice: dropped and listed; dependents skipped, not attempted.
- Budget: per-lane and whole-run token ceilings read from the journals; kill rule writes "finished / not finished" and stops.
- Resume: landed steps hard-coded on relaunch so a prompt edit never re-runs them.

## Stage 2: the audit loop

1. An Opus 5.5 agent (`model: opus`) reads the spec, the script, the pre-flight reports and the lane sources, and returns a numbered list of potential issues, each with evidence (file:line, a measured number, or a quoted contradiction) and a severity.
2. The Architect investigates each issue with a read-only scout where needed; true issues change the spec/script; false ones are answered in the spec with the evidence.
Auditor checklist line: every client piece names the live scene node that adds it and the qa_state key that proves it, and ships an integration test that reads that key from the running scene, not from a fresh instance; a piece without an attach point is a stub and is listed as one (attach point rule, rev 5, from the 2026-10-09 drift check).
3. Repeat with a fresh Opus auditor until an audit returns no blocking issue, at most three rounds; the final audit report is attached to the spec.
4. Westley reads the spec's one-page summary (lanes, stories, dates, what he must do) and gives the go.

## Stage 3: execute

Rev 1 (2026-10-07 to 10-10, history): guards and baseline first; lanes by the spec's dependency edges (GUARD, K0, K-a, A; B0 and the F scripts early; C after A; E1 from K-e; D on Westley's answers; the view chain A12, F5, C5, E1p, D hook); six lanes in flight; the lab beside. What landed is in the lane table.

Rev 2 (from the resume): the Dispatcher runs `workflows_2026-10-07/dispatcher.md` with three slots (two build workflows, one landing).
- Slot order on resume: (1) the harness pieces `vg-harness-method.js` (no eyes); (2) the E1 skeleton `vg-wave5-laneE1b-r2.js` stage `skeleton` (K-e4, E1k-skel, E1p-a, one landing, one shot to the queue); (3) a worktree cleanup clerk at once, beside them.
- Then: E1 fan-out (stage `fanout`) on Westley's approval of the skeleton shot; A, B and C fix pieces one per verdict as his verdicts arrive, each spec'd by the Architect; D and F plays when a slot frees; E2 when his answers land; the D view hook after E1p.
- The lab runs beside in the night slot; lab reports are answered first.
- Westley's steps are the "Now" table in ROADMAP section 3 (at most six), plus the Mac build and codesign, the Spacewar test and the Steam dashboard when lane F's plays are queued.

## Decisions taken 2026-10-07 (Westley)

1. Settlement: economy play too, from the answered batches; small open rules may be Architect liberties, documented.
2. The 3D landscape: in.
3. Date: none; done right; efficiency, parallelism and no drift are the measures. A drift-check rule joins CLAUDE.md.
4. Go (Westley, 2026-10-07, confirmed in the Westley chat after the Architect chat relayed it; verbatim): "The visible game programme builds Spec'd stories; the Definition of Ready and the open-flag rule are waived for the visual layer (E-16, E-18, E-12, E-22's open flags listed); blocked stories stay listed and are not claimed Seen."

## Verification (how we know the programme worked)

- Every lane's stories marked `Seen` by Westley from the review queue.
- The gate green including the `look` stage on main after the last landing.
- A full campaign chapter played by Westley on the beta build on Linux, Windows and Mac, with screenshots in the baseline folder.
- Every liberty taken on an economy rule is listed in the spec and the register, with the Architect named as decider and the date.
- The drift auditor's last report before the beta finds nothing blocking.
- Lab: run 1 and run 2 charts delivered during the programme, not after.
