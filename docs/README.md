# Map of `docs/`

Start with [`METHOD.md`](METHOD.md) (how the repo is run) and [`bible/game_bible.md`](bible/game_bible.md) (what the game is). Folder by folder, as of 2026-10-22:

| Path | What is in it |
|---|---|
| `bible/` | The source of truth for the game: hub, story catalog, one file per epic, references, `algorithms.md` |
| `bible_history/` | Snapshots of retired bible text; the bible itself is rewrite-not-append |
| `northstar/` | The development method and its records: plan, roadmap, agile rules, ambiguity register, specs, plans, research, story reviews |
| `northstar/plans/` | Specs, the programme file and its lane table, the push ledger, `pieces.toml` file ownership, retros, workflow scripts |
| `northstar/story_reviews/` | A picture per player-facing piece, the review queue, and the page of shots waiting on Westley |
| `northstar/research/` | Research briefs and results (lab, landscape, layers, economy, and more) |
| `northstar/proving_ground/` | The toy-task probes that proved the harness before building began |
| `architecture/` | C4 diagrams of the system |
| `architecture.md` | The pipe frames and cross-stage contracts |
| `research/` | Early research dump: game analyses, topic notes, tool findings |
| `articles/` | Two short explainers on the engine and the galaxy |
| `blender_stuff/` | Model prompts and Blender notes for era art |
| `claude_exchange/` | Notes and transcripts passed between early Claude sessions |
| `design_questions/` | Early era and design question notes |
| `random/` | Reference images and early scratch files |
| `stage_specs/` | Specs from the earlier Python-era stages |
| `test_specs/` | Test write-ups from the earlier Python-era stages |
| `client_scene_graph.md`, `design_lane*.md`, `research_lane*.md`, `priority_queue.md`, `workflow.md` | Loose files from earlier methods; `northstar/` wins where they disagree |

## Scheduled to move

Under the SHOWCASE lane, the stale folders and loose files above (`claude_exchange`, `random`, `blender_stuff`, `design_questions`, `stage_specs`, `test_specs`, the loose lane and queue files, and the parts of `research/` nothing references) are scheduled to move to `docs/legacy/` with an index, each move its own gated piece. Dated plans that the current programme no longer points at move to `northstar/plans/archive/`. The inventory that decides each row is [`northstar/plans/showcase/inventory.md`](northstar/plans/showcase/inventory.md); the plan is [`northstar/plans/showcase/README.md`](northstar/plans/showcase/README.md). Nothing has moved yet, so every path above still works.
