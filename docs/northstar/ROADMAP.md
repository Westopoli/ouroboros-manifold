# Roadmap

Last updated: 2026-10-03 (fourth update): W1 to W5 recorded in rulings-2 Addendum 68; L1 partly answered in the register.

What is being built now, what is built next, and in what order. `PLAN.md` is the method; this file is the order. One row per plan.

Rules for this file:

- Rewrite, never append. History is `git log`.
- A row points to a plan doc and never restates it. No design text here.
- A plan enters "Queued" only when it has a doc path. An idea without a doc goes in "Not planned yet".
- Whoever starts, finishes or reorders a plan updates this file in the same commit.
- File ownership stays in `plans/push/pieces.toml`. Open questions stay in `ambiguity_register.md`. Rulings stay in `plans/2026-10-01-architect-rulings-2.md`.
- A cell marked "to confirm" was not checked against the owning chat when the row was written.

## 1. Now building

All lanes were paused by Westley on 2026-10-03. Nothing is running. The stage 0 audit (2026-10-03, origin/main `1c2d4494`) is the source for the mission-plays row.

| Plan | Doc | Lane | Owns | State | Exit condition |
|---|---|---|---|---|---|
| Movement, layers and search | `plans/2026-10-02-movement-layers-and-search-plan.md` | Architect chat rules; builder and harness chats | `csrc/tactical_move.c`, fog, unit and command code (pieces `PP-*`, `SL-harness`); `scripts/skilllab/` | Paused. Phases A, C and S landed. Phase D: formation and focus-fire batches run; matchup, landscape, layers, enemy position and combinations not run. `push/pa-impl` pushed but unverified; `push/sl-land-11` not landed. | Phase D batches done and Phase E (the search) run |
| Mission plays | `plans/2026-09-30-mission-plays-plan.md`, `plans/2026-09-30-work-list.md` | Coordinator chat | Pipe handlers, mission, macro, chronicle and chapter wiring; client gaps | Paused. Waves A and B mostly landed. Left: B1 (8 enemy state-machine symbols), B6 (9 chapter and selector symbols), B7 (3 commander-death symbols), C3 (legacy SimBridge autoload still in `project.godot`), C4 E1 unverified, C6 sweep not started (32 rows need a wire-or-dead ruling, plus 4 client gaps). Work-list rows still unreachable: 48 of 89. | Every work-list row wired or ruled dead, and the loop plays end to end |
| Galaxy bubble rebuild | `plans/2026-10-02-galaxy-bubble-field-spec.md` | A separate build chat on `push/galaxy-field` | Galaxy view shader and field bake | Not on main; the build chat has not reported | Steps 2 and 3 built, screenshots compared, Westley views it |
| Space landscape mockup | `plans/2026-10-02-space-kit-mode-spec.md`, `research/space_landscape/README.md` | Design chat (Mac) with a Doer | `scenes/mockups/landscape/` | Pass 5 built; pass 6 spec written (`1c2d4494`) | Westley approves a pass; the camera question is designed as options |

## 2. Queued, in order

The agreed order of work (2026-10-03). Rows 1 to 3 have no plan doc yet; each gets one when it starts.

| # | Plan | Doc | Waits on | Why this position |
|---|---|---|---|---|
| 1 | Playthrough gate: a scripted end-to-end run in the merge gate | to write | nothing | Every later landing is checked against it. `tests/qa/desktop` flow test is the base: 29 of 30 pass. |
| 2a | Loop fix workflow: chronicle and jump, fresh-checkout boot, 30B reaches the galaxy | `plans/2026-10-03-loop-fix-workflow-brief.md` | Westley pastes the brief into a Sonnet chat | The three known breaks; run by a Sonnet chat as a workflow, reports to the planner chat. |
| 2b | Finish the MVP loop | `plans/2026-09-30-mission-plays-plan.md` | Row 1 | Westley: the MVP works 100 percent end to end before large new work. Known breaks (stage 0): the chronicle shows 0 entries after a mission in the Godot flow and the jump does not advance the shared world; a fresh checkout boots to the error screen through the legacy SimBridge autoload; the 30B QA sticks on NEW GAME (IndexError) and has 0 full loops since 2026-10-01; 9 Godot test scripts abort headless. |
| 3 | Baseline playthrough by Westley or the 30B | none | Row 2 | The line every addition is compared with |
| 4 | Land generator, part 1: the ground (S-186, S-188, S-189, S-190) | to write | Row 3; decisions L1 below | First new system; fills the layer-mask stub both generators share. Runs as a measured pilot workflow, under 10 agents, Sonnet builders (A202) |

## 3. Blocked on Westley

Every decision waiting on Westley, in the order that unblocks the most work. Candidates for each `Q-` flag are in `ambiguity_register.md`. An answer is recorded in the register and the epic, and its row is deleted here.

### Land generator

| # | Decision | Flags | Unblocks |
|---|---|---|---|
| L1 | Part 1, the ground, what is left (answers 2026-10-03 in the register): the minimum height variance; a small canvas (his question answered, waiting for his pick); the exact steepness limit inside 30 to 35 degrees, after his visual pass; what counts as unreasonably hard to reach on foot | Q-188-01, Q-188-02, Q-189-02, Q-189-04 | Queue row 4 |
| L2 | How layouts and terrain combine | Q-191-04 | Every place story (S-191, S-192, S-197) and the rewrites of S-112 to S-119 |
| L3 | Part 2, the places: how sites are found, counts, "opposite the objective", strongpoint count, choke width, vantage reach, how many plays a map must offer, raid lanes, fairness on a slanted map | Q-191-01 to -03, Q-192-01 to -05, Q-197-01 | Land generator part 2 |
| L4 | Landforms that ship, and how "variety packed in" is measured | Q-187-01, Q-187-02 | S-187 |
| L5 | Canvas: largest present size; region modifier at 64,000 wu | Q-195-01, Q-195-02 | S-195 |
| L6 | Smaller land choices: cover height source, region climate draw order, empty regions, when a building blocks | Q-190-01, Q-221-01, Q-221-02, Q-207-01 | S-190, S-221, S-207 |
| L7 | Placeholder ground units: confirm the reading "the same six unit types with the space era's numbers, drawn as placeholders" | Q-201-01 | S-201; closes the flag |
| L8 | Was land mockup pass 3 (2026-09-21) approved? The record still says "awaiting Westley's third look" | none | The record only |
| L9 | Name and scope of the land era | Q-147-01 | S-147; a second era to play |

### Space generator

| # | Decision | Flags | Unblocks |
|---|---|---|---|
| S1 | Approve a space kit pass (5 built, 6 specified) | Q-166-02 | Writing the space stories into the bible |
| S2 | Small craft size and the gap it fits | Q-166-05 | The second passability class |
| S3 | Camera among five stacked sheets | options not yet drafted | Space client view |
| S4 | Shared density on by default; the layer gap for space eras; how the small-craft sections are chosen | under Q-166-02 | Space generator plan |

### Movement, layers and search (held by the Architect chat)

| # | Decision | Reference |
|---|---|---|
| M1 | Pass marks C0 to C9 and the 0.05 win margin | rulings-2 A174; unblocks Phase E |
| M2 | Variant B scale miss: keep red, drop the 1.35 factor for that scene, or change the pass rule | A193 |
| M3 | Confirm the leash rewrite and attack-move holding formation until in range | A188, A199 |
| M4 | Scattered-group rule (450 wu) collapses a 32-wide line | R-095-03 |
| M5 | Leash before or after damage | Q-087-01 |
| M6 | Guard stance | Q-096-01, Q-208-01; unblocks the landscape batch |
| M7 | Same-spot fling; concentration of fire | Q-097-02, Q-008-05 |
| M8 | Should the gate run the scale suite; should the tactical rule bound the worst step | rulings-2 |
| M9 | Fight length | R-085-02, R-085-04 |
| M10 | Height-band numbers scaling with step height | Q-166-04 (the skill lab measures first) |

### Balance and housekeeping (not urgent)

| # | Decision | Reference |
|---|---|---|
| B1 | Knowledge Lost rate, player-collapse rate, mirror battle length | held for the new balance simulation |
| B2 | E-17 reds: field sampling 9.5 ms against 7.4 ms; map generator and objective drift | held on the map design |
| B3 | Galaxy stack; the galaxy build chat has not reported | `plans/2026-10-02-galaxy-bubble-field-spec.md` |
| B4 | Constants promotion to `algorithms.md`; snapshot fixture policy; world-generation speed target at 400 regions | rulings-2 |

### Needed for the two-week scope, not yet sorted

| Group | Flags | Notes |
|---|---|---|
| Multiplayer | Q-140-01, Q-141-01, Q-142-01, Q-144-01, Q-214-01, Q-241-02, Q-242-01 to -03 | Blocks S-140 to S-144 and the pair stories |
| Economy and bases | Q-159-07 to -13, Q-167-01 to Q-181-02, Q-177-01 to -05, Q-178-01 to -05 | E-22; the largest set. An ordered answer sheet is not yet drafted |
| Settlements | Q-193-01 to -06, Q-222-01 | After the land generator |
| Strongpoints and weather | Q-218-01 to -06, Q-219-01 to -04 | After the land generator |
| Client budgets | Q-194-01, Q-234-01, Q-240-01, Q-236-01 | Zoom and drawing |

## 4. Not planned yet

Decided or partly decided in the bible, with no plan doc. Order within this table is the proposed build order.

| Group | Stories | Epic | State | Why parked |
|---|---|---|---|---|
| Land terrain visual pass for Westley | none | E-17 | Not written; where it is built is to confirm (the land prototype is in `research/landscape_design/mockup/`) | Westley asked for two things to look at: the landscape engine's output with ground steeper than 35 degrees clearly marked, so he sees where players can and cannot go (Q-189-02, Q-189-04); and the benched and natural ratio varying per map (Q-189-03, answered). Comes before land part 1 because Q-189-02's exact figure waits on it |
| Shared layer-mask contract | none yet (carries E-01 R-001-04, E-17 R-114-01) | E-01, E-17 | Not written | Lands first inside land part 1 as its own contract piece; written so space can use it; the small-craft class needs Q-166-05 |
| Space generator | none in the bible yet | E-17 | Research and mockup passes 1 to 5; pass 6 specified | Waits on decisions S1 to S4, the stories being written, and the mask contract |
| Land generator, part 2: the places | S-187, S-191, S-192, S-195, S-197, S-200, S-201, S-207, S-221 | E-17, E-01, E-11, E-13, E-02 | Design decided, about 25 flags open | Waits on the flag sheet, Q-191-04 first, and plan A |
| Settlements and cities | S-166, S-193, S-222, S-237 | E-17, E-02, E-18 | Design decided, Q-193-01 to -06 open | After the land generator |
| Zoom and drawing | S-194, S-234, S-236, S-240 | E-17, E-16, E-18 | Blocked on Westley's budgets (Q-194-01, Q-234-01, Q-240-01) | Client work, after a generator exists |
| Strongpoints and weather | S-218, S-219 | E-15 | Design decided, flags open | After the land generator |
| Economy and bases | S-167 to S-182, S-202 to S-206, S-209 to S-217 | E-22, E-11, E-12, E-13, E-10, E-14 | Design decided, flags open; S-182 open | Largest group; needs places from a generator |
| Cross-epic follow-ons | S-220, S-223 to S-228, S-230 to S-233, S-235, S-238, S-239, S-241 to S-244 | several | Mixed; S-224, S-225, S-226 open | Each follows its parent group |
| Port parity P4, map content | none | E-17 | Held | Waits on the generator design |

## 5. Dependency notes

- The mask contract and the generators' wiring pieces touch `csrc/tactical_mapgen.c`, movement and fog, which the movement and layers plan owns today: one owner at a time, wiring pieces queued.
- Both generators after the mask contract: a contract change lands first, alone, and consumers build after it. New code goes in new files behind the frozen header (`CLAUDE.md`, Architecture rules).
- Land before space (Westley, 2026-10-03): the land design is further along and space is still in his design loop. Space output is the general form that land is a special case of, so the mask contract is written for both.
- Both generators must use their own deterministic noise in C; the mockups use the engine's noise.
- Economy after a generator: bases, resources and expansion sites are places the generator finds (S-191).
- The landscape batch in the skill lab waits on the guard stance decision.

## 6. Recently finished

| Plan | Doc | Landed | Date |
|---|---|---|---|
| Bible rewrite: E-22 added, E-17 terrain-first | `research/epics_audit_2026-10-02/` | `6b8a6c59`, `1fe25028`, `8b5d7d07`, `424055f8` | 2026-10-02 |
| Movement and layers, Phase A (port parity) and Phase C (layers in the engine) | `plans/2026-10-02-movement-layers-and-search-plan.md` | see rulings-2 Addenda 62 to 64 | 2026-10-03 |
| Space landscape mockup, passes 1 to 5 | `research/space_landscape/README.md` | `6c2989ec` | 2026-10-03 |
