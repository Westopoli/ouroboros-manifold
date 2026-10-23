# Map of `docs/`

Start with [`METHOD.md`](METHOD.md) (how the repo is run) and [`bible/game_bible.md`](bible/game_bible.md) (what the game is). Folder by folder, as of 2026-10-23:

| Path | What is in it |
|---|---|
| `bible/` | The source of truth for the game: hub, story catalog, one file per epic, references, `algorithms.md` |
| `bible_history/` | Snapshots of retired bible text; the bible itself is rewrite-not-append |
| `northstar/` | The development method and its records: plan, roadmap, agile rules, ambiguity register, specs, plans, research, story reviews |
| `northstar/plans/` | Specs, the programme file and its lane table, the push ledger, `pieces.toml` file ownership, retros, workflow scripts |
| `northstar/story_reviews/` | A picture per player-facing piece, the review queue, and the page of shots waiting on Westley |
| `northstar/plans/archive/` | Dated plans and proposals the programme no longer points at |
| `northstar/research/` | Research briefs and results (lab, landscape, layers, economy, and more) |
| `northstar/proving_ground/` | The probe README, scorecard, build ledger and evidence that scripts and tests cite |
| `architecture/` | C4 diagrams of the system |
| `architecture.md` | The pipe frames and cross-stage contracts |
| `research/` | Early research dump; what is left is `graphify-out/`, a generated graph (junk, scheduled for removal) |
| `legacy/` | Retired docs with an index, [`legacy/README.md`](legacy/README.md) |
| `stage_specs/` | Specs from the earlier Python-era stages |
| `test_specs/` | Test write-ups from the earlier Python-era stages |
| `design_lane.md`, `priority_queue.md`, `workflow.md` | Loose files from earlier methods that code or the plan still cites; `northstar/` wins where they disagree |

## Still to move

Cited by code, tests or live plan files, so they stay until those pointers are fixed: `stage_specs/`, `test_specs/`, the three loose files above, and in `northstar/research/` the `layout_engine/`, `walkers/`, `settlement_mockup/` folders and `qa_driving.md`; in `northstar/plans/`, `audits_2026-10-07/` and `branch_triage_2026-10-15/`. The inventory is [`northstar/plans/showcase/inventory.md`](northstar/plans/showcase/inventory.md); the plan is [`northstar/plans/showcase/README.md`](northstar/plans/showcase/README.md).
