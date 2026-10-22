# SHOWCASE lane: the repo as an open-source, employer-facing project (approved by Westley 2026-10-22)

Side lane behind the beta and the skill lab. Records pieces go through records clerks; file moves and code go through gated pieces at low priority. Licence MIT (Westley 2026-10-22).

## Context

Westley wants to publish Ouroboros Manifold as open source and use it to show employers what he builds. Today the repo works but does not present itself: `README.md` is one line, past Claude sessions left orphaned folders (a 540-file legacy Python sim, tracked PyInstaller output under `build/`, swarm backups under `.swarm/`, `graphify-out/`, `tuning_output/` logs, `toys/`, nine unreferenced `scenes/debug/*.tscn`, five stale `docs/` folders), and the things that make the project run cleanly (tests are the spec, the merge gate, drift and method checks, the ledger, file ownership, the Claude rules) are real but scattered across `docs/northstar/` and `scripts/specfactory/` with no front door. The goal is a repo whose first screen explains the game, the architecture and the method, with dead material moved to a clearly labelled legacy area, without touching the beta or lab production lanes except through their normal gate. This is a side project: records and doc pieces go now through records clerks; code and file moves go through gated pieces at low priority.

Also asked in the same message: on the vision disc, the old code must be removed, not left beside the new. The `VG-A-sightdisc` paragraph already says the one-row float texture and the screen-circle path go; the plan adds one sentence making "no dead path" an explicit test (see step 0).

## Measured facts (origin/main, 2026-10-22)

- Top level: 24 entries. Tracked but not source: `build/` (326 files, PyInstaller `_pyi_dist` output), `.swarm/` (130 backup files), `graphify-out/` (4), `tuning_output/` (14 jsonl logs, already gitignored for new files), `toys/` (110, `layerlab`), `saves/autosave/sim.json`, `library/`, `data/`.
- `simulation/` 540 files: the legacy Python reference sim, "tooling only, not in the game loop" (CLAUDE.md).
- `scenes/`: 23 subfolders; `scenes/debug/` holds nine `.tscn` nothing references; `scenes/mockups/` holds the prototypes (some are live prototype bases; classify by reference, not by name).
- `docs/`: 1,923 files; `docs/northstar/` 1,540 (77 top-level entries under `plans/`); stale-looking folders `claude_exchange` (5), `random` (8), `blender_stuff` (26), `design_questions` (6), `stage_specs` (39), `test_specs` (13), `research` (137), `articles` (2), plus loose files `design_lane*.md`, `research_lane*.md`, `priority_queue.md`, `workflow.md`, `client_scene_graph.md`.
- `README.md`: 1 line. `AGENTS.md`: rules for the Antigravity CLI agent (live). `.claude/` 6 files (hooks, agents, settings). `Makefile` targets `all test clean`.
- Method machinery that exists and should be shown: `scripts/specfactory/` (136 files: merge gate, pre_gate, status_check, owner_lint, method_check, reach_lint, known-red lists, credits tools), `tests/` 1,073 files in 11 suites, `docs/northstar/plans/push/pieces.toml` (280 pieces, file ownership), the push ledger, the ambiguity register, `docs/northstar/plans/workflows_2026-10-07/` (dispatcher and method docs), `CLAUDE.md`.

## Approach (one lane, SHOWCASE, five steps; nothing moves until the inventory is measured)

### Step 0 (now, records clerk): vision-disc dead-path sentence
Append to the `VG-A-sightdisc` paragraph in `docs/northstar/plans/2026-10-07-visible-game-spec.md`: the screen-circle path (`_discs` centre+radius, the one-row float texture, the hole-punch shader branch) is deleted in the same change; a test asserts `fog_layer.gd` has no `radius` disc field and the shader has no float-texture uniform (positive control: main fails it). No code lands beside its replacement.

### Step 1 (records clerk, read-only engineer first): the inventory
A Sonnet engineer writes `docs/northstar/plans/showcase/inventory.md`: one row per top-level entry and per `docs/` and `scenes/` subfolder: path, files, last commit touching it, who references it (`git grep` of its basenames over `scenes autoload csrc scripts tests Makefile project.godot .claude docs/northstar`), and a class: **live** (referenced from the game, the tests, the gate or the current programme), **records** (ledger, register, bible, story reviews, programme files: stay where they are), **legacy** (was used, nothing references it now), **junk** (build output, backups, logs: delete). No file moves in this step. The Architect reads the table and marks each legacy row keep-in-legacy or delete; Westley sees the table once (it is the one look in this lane).

### Step 2 (records clerks, no gate): docs front door
- `README.md`: the game in three sentences; the architecture (C sim with the stochastic equations kept verbatim, Godot 4 client over a JSON pipe, byte-identical determinism across platforms); how it is built (tests first in fenced paths, the merge gate stages, the playthrough gate, drift and method checks, one owner per file, the ledger); how to run (Makefile, `run_godot_tests.sh`, the desktop driver); where to read next (links). Screenshots: the approved galaxy and lobby frames from `docs/northstar/story_reviews/` (already on main).
- `docs/METHOD.md` (new, short, links not copies): the method as a reader sees it: `CLAUDE.md` rules, `pieces.toml` ownership, the gate (`scripts/specfactory/merge_gate.sh` stages named), `status_check.py` and `method_check.py` (drift lines), the known-red lists, the ledger and register, Workflow vs manager-mode (the tool-split spec), the credits tools, the retro pages with measured numbers.
- `docs/README.md` (new): map of `docs/` after step 3.
- `LICENSE`: Westley's pick (question below). `CONTRIBUTING.md`: three paragraphs pointing at METHOD.md (tests first, one owner per file, the gate).
- Secrets and personal data pass before any public push: a Sonnet engineer runs a history scan (`gitleaks` or `git log -p | grep` over key patterns, the api key file name, emails) and reports; a hit in history means the repo is published from a fresh history (squash export), not by rewriting the working repo. Steam app id in `steam_appid.txt` and the `.vdf` are public identifiers and stay.

### Step 3 (gated pieces, low priority, one per move): legacy and junk
Order by risk, each its own piece with the full gate (the godot import and the test suites catch broken paths):
1. Delete junk from git: `build/_pyi_dist`, `.swarm/backups`, `tuning_output/*.jsonl`, `graphify-out/` (keep nothing; `.gitignore` gains the paths). No references expected; the inventory proves it.
2. `legacy/` at the root with `legacy/README.md` (one line per entry: what it was, when it was retired, the commit that retired it, why it is kept): `simulation/` moves to `legacy/simulation/` with the one or two tools still used by `scripts/` (the inventory names them) re-pointed; `toys/`; `scenes/debug/`; unreferenced `scenes/mockups/*` (referenced prototype bases stay).
3. `docs/legacy/` with an index: `claude_exchange`, `random`, `blender_stuff`, `design_questions`, `stage_specs`, `test_specs`, the loose lane files; `docs/research` split by the inventory (live research stays). `docs/northstar/plans/` gains `archive/` for dated plans the current programme no longer points at; ROADMAP and the programme file keep their links (each move runs `status_check.py`, which fails on a broken pointer).
4. `docs/bible_history/` stays (the bible's own history rule).
Rule carried from CLAUDE.md: "no deletion without parity" is about player-facing features; a legacy move of unreferenced files needs the inventory row, not a parity test. A move of anything referenced is a finding, not a move.

### Step 4 (audit, Sonnet, measured): code quality page
`docs/northstar/plans/showcase/code_quality.md`: per directory, counts and findings with file:line: dead code (`reach_lint.py` for C; GDScript files with no scene or preload reference; Python modules nothing imports), duplicated helpers, stale comments naming retired rulings, TODO/FIXME, files over the size rule, test files whose docstring names no `S-`/`R-` id. Each finding becomes a small fix piece or a legacy row; nothing is fixed inside the audit.

### Step 5: what employers see first
After steps 2 and 3, a fresh Sonnet reader opens the repo cold and writes a one-page "first ten minutes" report (what it understood, what it could not find); its gaps become the last records batch.

## Files

- New: `README.md` (rewrite), `docs/METHOD.md`, `docs/README.md`, `CONTRIBUTING.md`, `LICENSE`, `legacy/README.md`, `docs/legacy/README.md`, `docs/northstar/plans/showcase/{inventory,code_quality,first_look}.md`.
- Edited: `.gitignore`, `CLAUDE.md` "Where things are" (adds `legacy/`), `docs/northstar/plans/push/pieces.toml` (SHOWCASE rows: SHOWCASE-inventory, SHOWCASE-front-door, SHOWCASE-junk, SHOWCASE-legacy-sim, SHOWCASE-legacy-scenes, SHOWCASE-docs-legacy, SHOWCASE-quality-audit, SHOWCASE-first-look), the spec paragraph for VG-A-sightdisc.
- Moved: per the inventory, never before it.

## Reuse

- `scripts/specfactory/reach_lint.py` (C reachability) for the dead-code audit; `status_check.py` for broken pointers after doc moves; `owner_lint.py` for the new rows; the merge gate as the only path for file moves.
- Existing approved shots in `docs/northstar/story_reviews/` for the README.

## Verification

- Step 1: the inventory's reference column is reproducible (`git grep` commands listed in the page).
- Steps 2 and 3: full merge gate per piece (build, csim, transport, godot tests, playthrough); `status_check.py` and `owner_lint.py` green; `project.godot` opens with no missing-resource errors (the gate's import stage).
- Secrets scan report attached to the front-door landing; no public push before it reads clean.
- Step 5: the cold reader finds the game, the architecture and the method within the README's links.

## Decided

- Licence: MIT (Westley, 2026-10-22). `LICENSE` is the MIT text with his name and the year.
