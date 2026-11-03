# Roadmap

Last updated: 2026-11-02 (Architect, Westley's question "Is all that's blocked on me listed in roadmap?"): section 1 is the two staircases on two gate channels, brought up to current state, with a first row pointing to the one list of what waits on Westley (`story_reviews/westley/README.md`, section Waiting on you); sections 0 (run a prototype), 2b (after the beta workflow), 3 (blocked on Westley) and 3b (parallel work) are removed, their method not enforced or their items answered or old; section 2 keeps the Steam rows only.

What is being built now, what is built next, and in what order. `PLAN.md` is the method; this file is the order. One row per plan.

Rules for this file:

- Rewrite, never append. History is `git log`.
- A row points to a plan doc and never restates it. No design text here.
- A plan enters "Queued" only when it has a doc path. An idea without a doc goes in "Not planned yet".
- Whoever starts, finishes or reorders a plan updates this file in the same commit; whoever starts or ends a plan also edits `docs/method/reading_list.toml` in the same commit as the ROADMAP row.
- File ownership stays in `plans/push/pieces.toml`. Open questions stay in `ambiguity_register.md`. Rulings stay in `plans/2026-10-01-architect-rulings-2.md` and, for the programme, in the spec's `[W ...]` tags.
- Lane status lives in one place, the lane table of `plans/2026-10-07-visible-game-programme.md`; this file never copies it.

## 1. Now building: two staircases, two gate channels

Westley 2026-10-31 and 2026-11-02: everything is built one verified step at a time, each step ending in something he looks at in a scene he plays, approve or deny, before the next starts. Two staircases run side by side on separate gate channels (DEC-two-gate-channels-2026-11-02, H-059): the **simulation lab** (`plans/2026-10-31-lab-staircase.md`, DEC-lab-staircase-2026-10-31; stories H-039, H-040, H-052, H-053) and the **beta** (`plans/2026-11-02-beta-staircase.md`; stories H-028, H-059, H-060, H-061, then one per stage). Each row is one story; its words and done-when live in the story file; this table is the order and the state only. Whoever moves a stage rewrites its row in the same commit.

| Staircase | Stage | Story | State (2026-11-02) | Next |
|---|---|---|---|---|
| Westley | waiting on you | story_reviews/westley/README.md (section Waiting on you) | seven items, none blocks a Dispatcher except the B0 editor check for closing B0 | your answers |
| lab | 1 two blobs on a flat field | H-040 (+H-039, H-052) | Seen 2026-11-01; built; lands in the stack gate after H-057 (stack of H-040, H-053 and H-063 gated once, three merges: DEC-stack-gating-2026-11-02) | land; L-0054 record run on main |
| lab | engine rule from stage 1: engage on sight, per-type leash | H-057 | built, re-pins and goldens done; slow gate passed every stage except lane_plays, which failed on GPU memory held by a local ollama model (unloaded 2026-11-02 evening); rerun next | land |
| lab | 2 roles, ranges, win rates over seeds | H-053 | Seen 2026-11-02 (per-picture verdicts in `docs/northstar/story_reviews/westley/crossings.md`); stacked behind stage 1 | land; fixed pictures go under `research/layer_dynamics/arena/stage2/` (not his directory) |
| lab | catalogue round three (arcs, mouth coverage, priority kinds) | H-025 round three | batch 1 pushed c5fddbc9 (29 pictures) and waiting on his verdicts | his verdicts |
| lab | 3 the ground pushes back | H-063 | built, tests green; in the stack | land, then four fights for his verdicts |
| lab | 4 sight; 5 facing, arcs, bands; 6 the scan; 7 objectives, hazards, time, space | | plan only | one at a time |
| lab | after the lab: piecemeal, then whole | none yet (plan in `research/layer_dynamics/decomposition.md`) | Decided 2026-11-02 as a plan; built after the lab is finished | specified then |
| harness | two gate channels | H-059 | landed 2026-11-02 (e23c303f) with H-062 (plan re-read check) and H-066 (qa port self-connect fix); Ready, landing after the stack, H-068 first: H-068 (shell port waiters), H-071 (review apply words), H-073 (GPU preflight), H-074 (gate scratch on disk) | H-068, H-071, H-073, H-074 after the stack lands |
| beta | B0 the build exists (`om-beta`) | H-028 (+H-038 part 2), H-067 | Seen 2026-11-02 for om-beta; the editor route (H-067) built, landing queued | his editor check (`story_reviews/westley/beta_stage0/editor-setup.md`) |
| beta | B1 the approved screens | H-060 | build done (17 tests green), landing queued on the beta gate | his verdicts on the B1 pictures |
| beta | unit scale | H-041 (+H-023 Seen 2026-11-02) | contract built, consumers after; Westley's per-role sizes in `data/unit_scale.toml` | consumers, then the sizes in the beta |
| beta | B2 the layout, no units, five kinds | H-061 | Ready | after B1 Seen |
| beta | B3 landscape engine; B4 places; B5 one role in groups; B6 vision; B7 layers (land); B8 all roles, real fights; B9+ economy in pieces | ids when written (H-062 is the plan re-read check) | plan table only; story written one stage ahead | one at a time |

Channels: lab = `gate-lab.lock`, Dispatcher chat `ouroboros-manifold-lab` (today `ouroboros-manifold-90`); beta = `gate-beta.lock`, Dispatcher chat `ouroboros-manifold-beta` (Westley opens it; first brief in the beta plan). H-059 landed 2026-11-02: the two channels gate at the same time, one landing in flight per channel (`docs/method/gate.md`). The Architect chat `rewrite-method-git-record` briefs both and rules; Westley vetoes by a word.

Held behind nothing now: the 2026-10-30 "no scene story until proof by eyes" gate is answered by H-031 pieces one and two (landed) plus the wake rule; piece three (crop to the window) is a Spec'd harness improvement, not a B0 precondition.

Not in a staircase, still owed: the thresholds batch (`story_reviews/westley/thresholds_batch_2026-11-01.md`, ten rows); H-042/H-043 findings; H-044, H-046, H-048, H-049, H-051, H-054, H-055, H-056 Spec'd harness stories; the earlier programme rows below are history until a staircase reaches them.

## 1b. Westley's log: what he pointed out, and what became of it

Method (Westley, 2026-10-27, `story_reviews/westley/Answers.md`): every bug, issue or request Westley points out is logged here the day he says it, with a status, a pointer to where it is being worked on, and whether he has signed off on a revised version that is in the beta. Nothing he points out is acted on without a row here, and no row closes without his sign-off. The beta is paused for the simulation lab; when beta work resumes, the Architect reminds him of this section in chat before anything starts, and the first work items are the rows below in order, beginning with W0.

Statuses: `logged` (recorded, nobody on it) · `investigating` (someone is finding out what happened; pointer names them) · `W-look` (a prototype or scene Westley can pan is owed before anyone builds; he rules on it, then it moves on) · `in progress` (pointer names the piece) · `built` (on main, waiting for his sign-off) · `signed off` (his word, with the date) · `dropped` (his word).

| # | Date | What Westley said | Status | Pointer | Sign-off |
|---|---|---|---|---|---|
| W0 | 2026-10-27 | "My requests frequently don't appear to go anywhere." Investigate every request of the last few weeks that was not done (the map-edge request is the known case), and list each as its own row here with status and pointer, before any other beta work. | logged | first beta work item; a fresh Sonnet engineer reads `verdicts_2026-10.md`, `decisions.md`, the programme file lane notes and the Westley chat memory for every ask, and checks each against main | |
| W1 | before 2026-10-22 | The player should not so easily see the edge of the map: a cut-off and a void look unpolished. Investigate what was done with that request. | logged | part of W0; answer owed to him with the commit or the reason nothing landed | |
| W2 | 2026-10-27 | `C-S132` sight discs: the lit disc still reads as a flat circle from the player's view, not following the ground; if this is the "fixed" version it is not approved, it looks the same as the flawed one he pointed out before. | logged | VG-A-sightdisc on main; the disc must follow the ground (DEC-S004 vision discs); re-shot owed as a scene he can pan, not a still | |
| W3 | 2026-10-27 | `C-S132` facing triangles: approved, specifically those, not every feature of the picture. | signed off | VG-C unit marks | Westley 2026-10-27 |
| W4 | 2026-10-27 | `C-S132` run line shows no landscape: white space and units only. Big bug; fix and hand back. | logged | the README's run line for the C lane scene; find the regression on main | |
| W5 | 2026-10-27 | `C-S132` whether units sit on the ground or float or draw through the hill: cannot be told from a still; movement is the tell. | W-look | a scene he can pan, with the units moving over the hill; rule then | |
| W6 | 2026-10-27 | `C-S140` land march: rejected. Unit placeholders are 2D (same shape at every angle); placeholders must be 3D like the beta's (a plain box is fine). No colour change with distance, so distance cannot be read; the bunching may be slope or broken scale. The landscape looks fine. | W-look | a pannable prototype of this scene before anything is built; Westley rules on the prototype, then the row moves to in progress | |
| W7 | 2026-10-27 | `F-S140` click-move order: rejected. Does not read as an order obeyed; shot predates the facing-triangle change, so directions cannot be read; perfectly top-down and 2D with no landscape, marks against it since the beta is 3D. Unit movement needs a prototype he can play with, not a still. | W-look | a pannable prototype of a two-player order in the space era; the re-shot after the facing triangles | |
| W8 | 2026-10-27 | Method: "maybe we should amend the screenshot rule to a prototype/scene rule." His rule to make; nothing changes until he says so. | logged | Architect, to put to him with the W0 report: the look rule (Visible-game guard 1) would read "a scene he can pan" for motion and depth questions, a still for layout | |

## 2. The beta critical path

Superseded for the build order by the beta staircase (`plans/2026-11-02-beta-staircase.md`, section 1 above): B0 to B8 assemble the game; rows 5 to 8 below (Steam) follow B8. The landed rows 1 to 4 (terrain stages 2 and 3, unit size, Steam phase A) are removed; git log has them.

Target: a private Steam beta with multiplayer and every approved prototype integrated. Westley 2026-10-07: no date; "done right than fast"; efficiency, parallelism and no drift are the measures. Steps 1 to 5 are carried by the programme; this table keeps the Steam-side steps.

| # | Step | State (2026-10-13) | Gate | Then |
|---|---|---|---|---|
| 5 | Steam wiring phase B: pipe frame flag, bridge wrappers, lobby, tactical hookup | lane F: skeleton lobby (dbe480a) and net first tick (b12b47a) on main; S-141 reviewer yes, S-140 unclear, both pending Westley | gate plus a two-process loopback match (S-141, S-142 green) | 6 |
| 6 | Shipping the C pipe on Windows, macOS, Linux (static pipe per OS, mingw-w64 cross build, client path fix, signing) | Windows: first probe matched byte for byte under wine (2026-10-06). macOS: done 2026-10-18 on the Mac, `scripts/build_pipe_macos.sh` static ad-hoc-signed pipe, full checksums equal the Linux pins at ticks 100 to 2000 (`plans/2026-10-18-macos-pipe-probe.md`); notarisation and a signing identity are Westley's | a build per OS runs the probe and matches checksums (Q-NET-05) | 7 |
| 7 | First real-Steam test: Westley's two accounts on Spacewar 480, Linux + Mac | after 5 and 6 | a match to its end, a stall, a leave | 8 |
| 8 | Beta build on Westley's app id, Dev Comp keys, tester guide (`docs/northstar/beta/`) | guide and store copy drafted; app id is Westley's, by hand | one tester plays a mission and files an F12 report | public track |

## 4. Not planned yet

Decided or partly decided in the bible, with no plan doc. Groups that entered the programme are gone from here (settlements, economy and bases, zoom and drawing, strongpoints and weather are lane E and C pieces; the layer mask is the terrain contract).

| Group | Stories | Epic | State | Why parked |
|---|---|---|---|---|
| Layout library audit and archetype pairing | none | E-17, E-10, E-21 | Not written | Westley 2026-10-03: the eight old layouts (`simulation/layout_library/`) predate the game's change; audited against the lab's layout search before any pairing |
| Land generator, part 2: the places | S-187, S-191, S-192, S-195, S-197, S-200, S-201, S-207, S-221 | E-17, E-01, E-11, E-13, E-02 | Design decided; towns rulings 2026-10-13 (R-191-06, R-193-01, R-177-02); spec next (Architect), launch on Westley's go | The lane that builds economic locations, neutral towns grown to a seeded age, resources and the base kinds in the sim; lane E's settlement look follows it |
| Space generator in C | none in the bible yet | E-17 | Mockup pass 6 approved; lane D holds the sim side (D2 to D8 on main) | Waits on S1 to S4, the space stories, lane D's resume |
| The land era's identity and the era roster | S-147, S-151 | E-20 | Both packs exist (Settled Reach; Greek placeholder, the era named Greek, reached by the era toggle); Q-147-01 open for the name, brief and ordered roster; the era pack form (3b T9); S-151's values come from the lab's crossings | Design, not build: Westley writes the brief and roster; the Climate of War values wait on the lab reporting more than one crossing |
| Cross-epic follow-ons | S-220, S-223 to S-228, S-239, S-241 to S-244 | several | Q-220-01/02, Q-224-01, Q-225-01/02, Q-226-02, Q-227-02/03, Q-228-01/02 open | Each follows its parent group; the simulation lane reads the sim-side ones |
| Port parity P4, map content | none | E-17 | Held | Waits on the generator design |

## 4b. Prototype state

Per `agile.md`, Prototype gate. A group marked "needed" is not planned until its prototype is approved. Integration state is the programme's lane table.

| Group | Prototype | State |
|---|---|---|
| Land generator | Mockup `scenes/mockups/landscape/` | Approved 2026-10-06; integrated (terrain stages 1 to 3, lane C) |
| Walking and flying units on land | Mockup `scenes/mockups/walkers/` | Approved final 2026-10-06; integrated (terrain stage 2, lane C, lane W routes) |
| Galaxy | `push/galaxy-field` | Look approved 2026-10-07; integrated by lane B (B22, B23) |
| Settlements | Mockup `scenes/mockups/settlement/` | Pass 1 approved 2026-10-06; integrated by lane E (port E1q, look E1k); a banded-contour prototype is queued after E1k (`PROTO-settlement-banding`) |
| Space generator | Mockup, space kit mode | Pass 6 approved 2026-10-06 (vision-tube note Q-S3-01); lane D held |
| High ground worth | Instrument retired: `scripts/skilllab/ground/highground.py` deleted by LAB-REV2-L6; the ground scene `s1_slope_top` replaces it | Built 2026-10-05 as a space-lab stand-in; retired under R-005-09 and S-164 |
| Movement and layers | Instrument, skill lab | Phase D pages; pass marks open (M1) |
| Economy and bases, rules | Instrument, needed | None exists; the number flags are asked piece by piece in lane E |
| Economy and bases, look | In the game, not a mockup | Lane E (E1k, the economy screens); Westley judges shots per piece |
| Layout engine | No prototype (Westley 2026-10-06) | The lab's layout search supplies the data; `push/proto-layout` is reference only |
| Mission-to-galaxy transition (S-108) | Mockup `scenes/mockups/transition/` on `push/proto-transition` | Needed (Westley, 2026-10-15); spec `plans/2026-10-15-transition-mockup-spec.md`; a Doer builds it on the Mac |
| Multiplayer lobby | Mockup needed for the lobby screens | Lane F's skeleton lobby (S-141 shot) stands in; Westley's verdict pending |
| Simulation | The sim viewer (`plans/2026-10-12-simviewer-plan.md`) | Specced 2026-10-12, not built |

## 5. Dependency notes

- **Layout before landscape (Westley, 2026-10-04, verbatim: "layout comes before landscape. The layout engine should be prototyped and integrated before the landscape engine.").** Order: prototype the layout engine and get his approval; integrate it (the C layout generator of S-112 to S-119 exists and is tested, but no live mission calls `om_map_generate`, so today's missions have no layout); then the landscape engine, which takes the layout as its input (option A). The layout library is audited and paired with archetypes first (Q-192-04).

- The mask contract and the generators' wiring pieces touch `csrc/tactical_mapgen.c`, movement and fog, which the movement and layers plan owns today: one owner at a time, wiring pieces queued.
- Both generators after the mask contract: a contract change lands first, alone, and consumers build after it. New code goes in new files behind the frozen header (`CLAUDE.md`, Architecture rules).
- Land before space (Westley, 2026-10-03): the land design is further along and space is still in his design loop. Space output is the general form that land is a special case of, so the mask contract is written for both.
- Both generators must use their own deterministic noise in C; the mockups use the engine's noise.
- Economy after a generator: bases, resources and expansion sites are places the generator finds (S-191).
- The guard stance is ruled (R-096-08, 2026-10-13); the landscape batch runs on the built guard until the step-and-return engine piece lands.

## 6. Recently finished

| Plan | Doc | Landed | Date |
|---|---|---|---|
| Restart point 400k context; ROADMAP rewritten; galaxy density and S-132 shots committed for Westley | CLAUDE.md, `workflows_2026-10-07/`, `story_reviews/westley/2026-10-13/` | bb30cd9c, 7ccc8dbe, 26cdb319 | 2026-10-13 |
| Sim viewer spec SV-0 to SV-3 and owner rows; the simulation lane context | `plans/2026-10-12-simviewer-plan.md`, `plans/2026-10-12-sim-lane-context.md` | dc7da0ac, c4d3d939, c7961d75 | 2026-10-12 |
| Programme landings of 2026-10-11 to 10-13: K-e5/K-e6 contracts, settlement port E1q, F-SKEL lobby, F-NETTICK, K-d1, A16, A17, VG-C-unitscale, VG-B23b dot colour, S-004 play fix, W1 planner | `plans/2026-10-07-visible-game-programme.md` lane table | `scripts/journal.sh` | 2026-10-11 to 13 |
| Retrospective and method rev 2: Sonnet Dispatcher, Architect on call, skeleton first, pre-gate, tests on the built tree, method check at every compaction | `plans/retro_2026-10-10/README.md`, `workflows_2026-10-07/dispatcher.md`, `method_check.md` | 393a1d04 and the rev 9 spec | 2026-10-10 |
| Programme stage 3 under method rev 1: lanes A to F first pieces (98 planned plus 37 unplanned), guard pieces (reach lint, lane plays, play split, daemon verb) | programme file, `retro_2026-10-10/` | fc986411, 7bb1f5a2, f37a926f and the lane table | 2026-10-07 to 10-10 |
| Terrain stages 2 and 3; Steam phase A | `plans/2026-10-06-terrain-stage2-spec.md`, `-stage3-spec.md`, `2026-10-06-steam-multiplayer-wiring-spec.md` | 008de465, 0304d821, e63483f6 | 2026-10-06 to 07 |
| Refuse fix; long-mission suite; Agora QA plays loops | `plans/2026-10-03-finish-loop-rulings.md` | a136e3c0 | 2026-10-04 |
| Finish-the-loop batch; MVP loop plays end to end; playthrough stage in the gate | `plans/2026-10-03-finish-loop-rulings.md`, `plans/2026-10-03-loop-fix-workflow-brief.md` | 0d4006fd, 465d7145 | 2026-10-03 |
| Bible rewrite: E-22 added, E-17 terrain-first; movement phases A and C; space landscape passes 1 to 5 | `research/epics_audit_2026-10-02/`, rulings-2 Addenda 62 to 64, `research/space_landscape/README.md` | 6b8a6c59, 1fe25028, 8b5d7d07, 424055f8, 6c2989ec | 2026-10-02 to 03 |
