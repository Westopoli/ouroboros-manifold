# The visible game programme (plan, 2026-10-07)

**Status: IN FLIGHT. Stage 1 (pre-flight) started 2026-10-07.** Stage markers below are updated as each stage completes; the ROADMAP section 1 row points here. When every lane's stories are `Seen` this header becomes DONE with the date.

| Stage | State | Date |
|---|---|---|
| 1. Pre-flight (ten read-only scouts, the spec, the script) | done: reports in `preflight_2026-10-07/`, spec `2026-10-07-visible-game-spec.md` rev 1, rulebook | 2026-10-07 |
| 2. Audit loop (Opus 5.5 issues with evidence; a Sonnet parallelism audit beside it; up to three rounds) | in flight, round 1 | 2026-10-07 |
| 3. Execute (lanes A to F, guards first, story plays, drift checks) | not started | |

Lane state (updated at each landing): A battle screen: not started · B galaxy: awaiting Westley's look · C ground: stage 3 built on `push/terrain3-land-2`, 3D not started · D space landscape: not started · E settlement and economy: not started · F Steam phase B: phase A landing on `push/land-1007b`, B not started.

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
| A. Battle screen | Per-type unit shapes and tiers, layer rings and dimming, fog, cover and obstacles, objective beacons, selection and control groups, the HUD (minimap, selection panel, objectives, events, reinforcements, ability ring, layer selector), shots/hits/deaths, camera (pan, zoom to map view) | Legacy `scenes/tactical/` at `009c99ac^` (4,682 lines, as the feature inventory, re-derived on the C pipe); `push/tv-read` (built 2026-10-07: unit_visuals, map_layer); E-16/E-18 `references/` | S-104, S-105, S-009, S-010, S-005, S-007, S-075, S-132, S-133, S-134, S-136, S-101, S-234, S-096 | 10–12 (+1 contract: frame fields for structures and tactical events) | First; lanes C's view work and F's W5 follow it |
| B. Galaxy | Bubble field, territory glow, borders, war flashes, pan/zoom/orbit/focus, mission-to-galaxy transition | `push/galaxy-field` (4,658 GDScript + 554 shader lines, built 2026-10-02); `scenes/shared/world_view/` shell renderer | S-106, S-107, S-108 | 3–4 | Independent; starts on Westley's look approval |
| C. Ground | Stage 3 (built on `push/terrain3-land-2`, two small reds) landed first; then the 3D land landscape: camera, picking, box-select, height array in the frame (contract), mesh from the mockup; walkers and flyers drawn as the mockup draws them | `push/proto-land-iter` (8,634 lines), `push/proto-walkers` (1,071 lines), stage 3 spec rev 3 | S-236, S-001, S-004, S-207, S-132 (walkers), stage 3's era toggle | 6–8 (+1 contract) | Stage 3 lands first; the 3D view after lane A's view structure |
| D. Space landscape | The space kit generator in the sim (Q-STAGE3-03 → yes) and the client drawing it for space missions, with the vision-tube note (Q-S3-01) recorded as a later item | space-kit mode spec `2026-10-02-space-kit-mode-spec.md`, `scenes/mockups/` space landscape | E-17 space stories (S-166 group), S-007 | 5–6 (+1 contract) | After A (shares the view) |
| E. Settlement and economy | The economy play from E-22 and the answered batches: lots and placement, workers walking and gathering, buildings rising stage by stage, strongpoints, weather, the economy player's screen and the solo dial (S-230, S-231, S-233, S-235), the settlement look; sim systems first (contract: structures, workers, lots in the frame), then client | `scenes/mockups/settlement` (1,099 lines), E-22, E-15 (strongpoints, weather), batches 9 to 12 | S-209, S-210, S-211, S-212, S-230, S-231, S-233, S-235, S-237, S-238, E-22's 16 stories | 12–16 (+2 contracts) | Sim pieces now (disjoint from A); client after A |
| F. Steam phase B + shipping | Pipe frame flag, bridge wrappers, lobby + menu, tactical hookup, pipe per OS (W8), Steam depot upload script | Steam spec rev 6 | S-141/S-142 group (E-19), tester guide | 6 + 2 | W5 after A; the rest now |

Order of landing: A, C, B, F, D, E (E's sim pieces run from the start). Estimated: ~50 pieces, ~160–190 agents, ~8–10M tokens, two to three weeks wall with 6 lanes running and gates serialised. No date is promised; the programme ends when the stories are Seen.

## Guards (written into CLAUDE.md as the programme's first commit)

1. **Visual definition of done.** A player-facing piece ships with (a) a deterministic element inventory from `qa_state()` asserted in its tests (which nodes exist, counts, presence of fog/markers), and (b) a screenshot set attached to its landing report, taken by the desktop driver at the story's moment, and seen by a human before "done". The gate gains a `look` stage: rejects a blank or near-uniform frame (colour histogram), attaches the screenshots to the report.
2. **Stories acted out.** Every lane names the stories it serves. For each story a `story play` exists: a scripted scenario for the desktop driver (`tests/qa/desktop`, `daemon_client.py`) that reaches the story's moment, captures `qa_state()` and a screenshot, and a model reviewer (30B through Agora when the CPU is free; else a Sonnet/Haiku agent) is given the story's words plus the bible `references/E-##/` images and answers "does the player see this? evidence". Answers land in a review queue Westley approves. The story's status in `stories.md` moves to `Seen` only on his approval. (Reuses the mission-plays harness of 2026-09-30 and the QA daemon.)
3. **No deletion without parity.** Removing a working feature requires a test that lists what it showed, green on the replacement first.
4. **Approved means scheduled.** The day a mockup is approved, ROADMAP section 1 gets its integration lane with position and owner; "approved, not integrated" is a visible state in every status report.
5. **Reporting.** Every status carries two columns: works (tests) and what the player sees (stories Seen). "Stub" is said when it is one.
6. **Play it.** The 30B plays current main nightly after each landing (screenshots to the review queue); Westley or the Architect looks weekly at minimum.
7. **Drift check (CLAUDE.md rule).** After every landing round, and at least weekly, a fresh Sonnet drift auditor checks the record against Westley's rulings and the plan: promises vs artifacts, rulings propagated to every epic they touch, ROADMAP rows vs branches, scope added nobody asked for, 'stub' states still open. Its report goes to Westley unedited; drift found is fixed before new lanes launch. (Today's audit found the stale alert rules and the missing integration rows; this makes it routine.)

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
- A stage red on one test that passes alone twice: re-run once (flake rule); a second red is real.
- Main moved: the clerk merges main before every gate (the merge-base harness fix is landing).
- A lane fails its check twice: dropped and listed; dependents skipped, not attempted.
- Budget: per-lane and whole-run token ceilings read from the journals; kill rule writes "finished / not finished" and stops.
- Resume: landed steps hard-coded on relaunch so a prompt edit never re-runs them.

## Stage 2: the audit loop

1. An Opus 5.5 agent (`model: opus`) reads the spec, the script, the pre-flight reports and the lane sources, and returns a numbered list of potential issues, each with evidence (file:line, a measured number, or a quoted contradiction) and a severity.
2. The Architect investigates each issue with a read-only scout where needed; true issues change the spec/script; false ones are answered in the spec with the evidence.
3. Repeat with a fresh Opus auditor until an audit returns no blocking issue, at most three rounds; the final audit report is attached to the spec.
4. Westley reads the spec's one-page summary (lanes, stories, dates, what he must do) and gives the go.

## Stage 3: execute

- Guards commit first (CLAUDE.md, ROADMAP section 1 lanes, `stories.md` gains the `Seen` status).
- Baseline: today's screenshots and `qa_state` inventories of every screen, committed under `docs/northstar/baselines/2026-10-07_visible/`.
- Lanes launched as separate workflows in the order A, B, C(stage 3 landing), F(non-view pieces); C(3D), D, E, F(W5) after A lands. Each clerk lands on a clean gate plus the `look` stage; the story plays for the lane run after landing and go to the review queue.
- The lab runs beside: re-spec (placed formations, "decided by survivors"), run 1, chart with Westley, D1 + categories, run 2. Lab reports are answered first.
- Westley's steps: approve the galaxy field look (run line in the spec); review the story queue; the Mac build and codesign run; the Spacewar test; Steam dashboard (store page, keys, depots).

## Decisions taken 2026-10-07 (Westley)

1. Settlement: economy play too, from the answered batches; small open rules may be Architect liberties, documented.
2. The 3D landscape: in.
3. Date: none; done right; efficiency, parallelism and no drift are the measures. A drift-check rule joins CLAUDE.md.

## Verification (how we know the programme worked)

- Every lane's stories marked `Seen` by Westley from the review queue.
- The gate green including the `look` stage on main after the last landing.
- A full campaign chapter played by Westley on the beta build on Linux, Windows and Mac, with screenshots in the baseline folder.
- Every liberty taken on an economy rule is listed in the spec and the register, with the Architect named as decider and the date.
- The drift auditor's last report before the beta finds nothing blocking.
- Lab: run 1 and run 2 charts delivered during the programme, not after.
