# Legacy pass, 2026-11-05

Branch `s/legacy-pass-2026-11-05`. Goal: the repo reads as a project in motion, not a pile of everything it ever was. History is kept (every move is `git mv`, so `git log --follow` works) and every destination has an index row.

## How each folder was judged

Evidence per path: last commit touching it, commits in the last 30 days, and which live files name it (code, tests, `docs/method`, `docs/bible`, the README, `pieces.toml`). No live reference and no commits for weeks meant move. A live reference meant either repoint the citation (comment-only edits; test files carry `Test-defect:`) or keep the file where it is.

## Moved (three commits)

| From | To | Why |
|---|---|---|
| `northstar/stage1_*.md`, `qa_backlog.md`, `backlog*.md`, `principles.md`, `vision_v2.md` | `docs/legacy/agora_era/` | First method; stage 1 finished 2026-09-10; QA list all fixed |
| `northstar/mvp/` | `docs/legacy/mvp/` | Lean-MVP/playtest rounds; replaced by the story loop |
| `stage_specs/`, `test_specs/` | `docs/legacy/` | Python-era; only code comments cited them |
| `design_lane.md`, `priority_queue.md`, `workflow.md` | `docs/legacy/method_era1/` | Earlier methods |
| `architecture/c4/` | `docs/legacy/architecture_c4/` | C4 model retired 2026-09-28 |
| `research/{settlement_mockup,walkers,epics_audit_2026-10-02,escalation,qa_driving,rts_bug_catalog}` | `docs/legacy/research/` | Finished or superseded |
| 19 dated plan specs, `audits_*`, `branch_triage_*`, `drift_checks`, `drift_audits`, `sim_lane_*`, one handoff | `northstar/plans/archive/{specs,audits,lanes,handoffs}/` | Work landed or dropped |
| three answered hand-over docs from `story_reviews/westley/` | `docs/legacy/westley_hand_overs/` | Row 7 of his waiting list |
| `build/` (PyInstaller output, friends-build files) | `legacy/build/` | Python-era packaging, 17 MB |

## Kept on purpose, with the reason

- `northstar/e2e/`: cited by `csrc/ouroboros_sim.h` (frozen contract).
- `northstar/baselines/`, `regression.md`: `scripts/integration_check.py` writes and reads them.
- `northstar/PLAN.md`, `spec_factory.md`: the README, `method_metrics.py` and four tests cite them.
- `research/harness_defects_2026-09-17`, `research/mockups`: scripts and scene checklists cite them.
- `research/layout_engine`: current work.
- `plans/decision_pack_2026-10-18`: `pieces.py` and `test_record_files.py` name it.
- `plans/retro_*`: linked from the repository README and `docs/METHOD.md`.
- `westley/method_retro_2026-10-24.md`: linked from the README.
- `plans/2026-10-27-lab-*`, `2026-11-02-*-context`, `plans/harness`, `plans/editor_debug`: lab and beta are current; the gate/mail-era ones belong to the cleanup branch.
- `story_reviews/{A..V}.md`: scripts read them by name; the lane key in `story_reviews/README.md` now says what each is.

## Held back for a later pass (size or code dependence)

`simulation/` (540 files, about a dozen scripts and tests import it), `story_reviews/shots/` (54 MB), `research/layer_dynamics` (83 MB, active), `research/landscape_design` (66 MB), `docs/legacy/claude_exchange` (17 MB).

## Not touched

Westley's uncommitted files in the main checkout, `.claude/settings*.json` (its line citing `docs/stage_specs` is his), frozen fixtures, `.patch` salvage, historic `scripts/specfactory/workflows/vg-*.js`.
