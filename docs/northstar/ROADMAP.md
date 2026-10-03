# Roadmap

Last updated: 2026-10-03, by the planner chat (Agora-Fable-Planner).

What is being built now, what is built next, and in what order. `PLAN.md` is the method; this file is the order. One row per plan.

Rules for this file:

- Rewrite, never append. History is `git log`.
- A row points to a plan doc and never restates it. No design text here.
- A plan enters "Queued" only when it has a doc path. An idea without a doc goes in "Not planned yet".
- Whoever starts, finishes or reorders a plan updates this file in the same commit.
- File ownership stays in `plans/push/pieces.toml`. Open questions stay in `ambiguity_register.md`. Rulings stay in `plans/2026-10-01-architect-rulings-2.md`.
- A cell marked "to confirm" was not checked against the owning chat when the row was written.

## 1. Now building

| Plan | Doc | Lane | Owns | Started | Exit condition |
|---|---|---|---|---|---|
| Movement, layers and search | `plans/2026-10-02-movement-layers-and-search-plan.md` | Architect chat rules; builder chat builds; harness chat runs batches | `csrc/tactical_move.c`, fog, unit and command code (pieces `PP-*`, `SL-harness`); `scripts/skilllab/` | 2026-10-02 | Phases A to D done and Phase E (the search) run. Phase E waits on Westley's pass marks C0 to C9. Now in Phase D: small batches per skill (focus fire v3, formation v2). |
| Skill lab cascade | `plans/2026-10-02-skill-lab-cascade.md`, `plans/skilllab-harness-spec.md` | Harness chat | `scripts/skilllab/`, `tests/skilllab/` | 2026-10-02 | Serves the plan above; ends with it. |
| Mission plays | `plans/2026-09-30-mission-plays-plan.md`, `plans/2026-09-30-work-list.md` | Coordinator chat, with the Architect chat ruling | Pipe handlers, mission, macro, chronicle and chapter wiring; client gaps | 2026-09-30 | Every work-list row is wired or ruled dead. Current wave: to confirm. |
| Galaxy bubble rebuild | `plans/2026-10-02-galaxy-bubble-field-spec.md` | A separate build chat on `push/galaxy-field` | Galaxy view shader and field bake | 2026-10-02 | Steps 2 and 3 built, old and new screenshots compared, Westley views it. Branch not yet on main. |
| Space landscape mockup | `plans/2026-10-02-space-kit-mode-spec.md`, `research/space_landscape/README.md` | Design chat with a Doer | `scenes/mockups/landscape/` | 2026-10-02 | Westley flies pass 5; the camera question is designed as options. Design work, not game code. |

## 2. Queued, in order

No plan has a doc yet. The three below are proposed and sit in section 4 until their docs are written.

| # | Plan | Doc | Waits on | Ready? | Size guess | Why this position |
|---|---|---|---|---|---|---|
| | | | | | | |

## 3. Blocked on Westley

| What | Needed from Westley | Flags | Unblocks |
|---|---|---|---|
| Space landscape, pass 5 | Fly the mockup (key V, small-craft slider, sections toggle) and say yes or what to change | Q-166-02 | Writing the space stories into the bible; the space generator plan |
| Small craft size | The size of the small unit class, and so the gap it fits | Q-166-05 | The second passability class in the shared mask contract |
| Camera among five stacked sheets | Pick from options (options not yet drafted) | none yet | Space client view |
| How layouts and terrain combine | An answer | Q-191-04 | Every land terrain story (S-186 to S-192, S-197) and the rewrites of S-112 to S-119 |
| Land terrain numbers | Answers to the flag sheet (sheet not yet drafted) | Q-186-01 to Q-197-01, Q-166-04 | The land generator plan |
| Pass marks for the search | Confirm or change the draft marks C0 to C9 | none | Phase E of movement, layers and search |
| Balance items | Held until his new balance simulation | see `plans/2026-10-01-architect-rulings-2.md` | Knowledge Lost rate, collapse rate, mirror battle length |
| Guard stance | A decision after a choke defence has been looked at | Q-096-01, Q-208-01 | S-208; the landscape batch in the skill lab |

## 4. Not planned yet

Decided or partly decided in the bible, with no plan doc. Order within this table is the proposed build order.

| Group | Stories | Epic | State | Why parked |
|---|---|---|---|---|
| Proposed plan A: shared layer-mask contract | none yet (carries E-01 R-001-04, E-17 R-114-01) | E-01, E-17 | Not written | Waits for the movement and layers plan to leave `tactical_mapgen.c`, movement and fog; needs Q-166-05 |
| Proposed plan B: space generator | none in the bible yet | E-17 | Research and mockup pass 5 only | Waits on pass 5 review, the stories being written, and plan A |
| Proposed plan C: land generator | S-186 to S-192, S-195, S-197, S-200, S-201, S-207, S-221 | E-17, E-01, E-11, E-13, E-02 | Design decided, about 25 flags open | Waits on the flag sheet, Q-191-04 first, and plan A |
| Settlements and cities | S-166, S-193, S-222, S-237 | E-17, E-02, E-18 | Design decided, Q-193-01 to -06 open | After the land generator |
| Zoom and drawing | S-194, S-234, S-236, S-240 | E-17, E-16, E-18 | Blocked on Westley's budgets (Q-194-01, Q-234-01, Q-240-01) | Client work, after a generator exists |
| Strongpoints and weather | S-218, S-219 | E-15 | Design decided, flags open | After the land generator |
| Economy and bases | S-167 to S-182, S-202 to S-206, S-209 to S-217 | E-22, E-11, E-12, E-13, E-10, E-14 | Design decided, flags open; S-182 open | Largest group; needs places from a generator |
| Cross-epic follow-ons | S-220, S-223 to S-228, S-230 to S-233, S-235, S-238, S-239, S-241 to S-244 | several | Mixed; S-224, S-225, S-226 open | Each follows its parent group |
| Port parity P4, map content | none | E-17 | Held | Waits on the generator design |

## 5. Dependency notes

- Plan A after movement, layers and search: both edit `csrc/tactical_mapgen.c`, movement and fog, and one file has one owner at a time.
- Plans B and C after plan A: a contract change lands first, alone, and consumers build after it.
- Plan B before plan C: the Settled Reach is the only era that exists (Q-147-01), space has two open flags against about 25, and space output is the general form that land is a special case of.
- Both generators must use their own deterministic noise in C; the mockups use the engine's noise.
- Economy after a generator: bases, resources and expansion sites are places the generator finds (S-191).
- The landscape batch in the skill lab waits on the guard stance decision.

## 6. Recently finished

| Plan | Doc | Landed | Date |
|---|---|---|---|
| Bible rewrite: E-22 added, E-17 terrain-first | `research/epics_audit_2026-10-02/` | `6b8a6c59`, `1fe25028`, `8b5d7d07`, `424055f8` | 2026-10-02 |
| Movement and layers, Phase A (port parity) and Phase C (layers in the engine) | `plans/2026-10-02-movement-layers-and-search-plan.md` | see rulings-2 Addenda 62 to 64 | 2026-10-03 |
| Space landscape mockup, passes 1 to 5 | `research/space_landscape/README.md` | `6c2989ec` | 2026-10-03 |
