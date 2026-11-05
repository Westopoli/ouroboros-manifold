---
leaf_id: leaf-01
spec_file: docs/northstar/plans/cascades/lab-stage3/spec.md
spec_lines: 20-30
test_files:
  - tests/skilllab/arena/test_stage3_reach.py
  - tests/skilllab/arena/test_stage3_control.py
impl_files:
  - scripts/skilllab/arena/features.py
  - scripts/skilllab/arena/run.py
  - scripts/skilllab/arena/snapshot.py
  - scripts/skilllab/arena/SNAPSHOT.md
contract_imports:
  - NAV_CELL
  - first_unreachable
  - control_twin
do_not_edit:
  - docs/northstar/**
  - tests/**
  - csrc/**
  - scripts/specfactory/**
  - .claude-swarm.toml
  - scenes/proto/fight_replay/fight_replay.gd
  - scripts/skilllab/arena/page.py
  - scripts/replay.sh
  - README.md
  - scripts/skilllab/arena/situations.py
standalone_symbols:
  - frame_ticks
  - example
impl_line_budget: 200
test_assertion_budget: 40
test_owned_by: parent
wave: 1
---

## Task

Implement spec criteria 1, 3, 4, 5 and 6 (criterion 2 is docs-only: keep the `features.py` docstring true). In `features.py`, `first_unreachable(engine, w, layout, preset, point, sides)` builds its open-cell grid on `NAV_CELL` (50 wu) cells from the engine's rules: every rectangle of `_engine_boxes(layout)` rounded out to whole cells, and for a layout with a slope the engine's `terrain_walk_mask` per layer (a cell is open when any layer's mask is non-zero at the cell centre's 100 wu terrain cell); `apply` must already have run on `w`. In `run.py`, `unreachable(layout)` builds a throwaway world, calls `features.apply`, calls the new `first_unreachable`, and frees the world (the CLI REJECT line stays `REJECT <id> R8 unreachable: <unit>`). Add `control_twin(layout, layout_path, control_dir)` writing `<id>-control.toml` and `<id>-control.json`, make `fight()` call `features.walk_on_ground` when `features.apply` returned True or `layout.get("movement") == "walk"`, add the document keys `landscape` and `movement_kind`, make `--control-dir` run the control through the twin and name the twin TOML as its `layout_path`, and add the `blocked` column to `results.md`. In `snapshot.py`, `validate` accepts `landscape` and `movement_kind` on `om-fight-2` only. In `scripts/skilllab/arena/SNAPSHOT.md`, document `landscape`, `movement_kind` and the control twin files. Match the structure of the existing functions in each file.

Test files `tests/skilllab/arena/test_stage3_reach.py`, `tests/skilllab/arena/test_stage3_control.py` are already written and failing. You are working inside your own git worktree, which is your working directory. Never run git. Edit `scripts/skilllab/arena/features.py`, `scripts/skilllab/arena/run.py`, `scripts/skilllab/arena/snapshot.py`, `scripts/skilllab/arena/SNAPSHOT.md` in place there until those tests pass. Do not modify test files, do not create files outside `impl_files`, and keep every edit to what the cited spec criteria require (no cosmetic refactoring; a doc claim your change makes wrong is rewritten in the same file). Keep the module's existing comment style and the `# See also:` traceability lines.

The route check is a hot path: `linear-ish` in cells plus units (80 x 80 cells on a 4000 x 4000 field); no per-unit grid rebuild.

## Acceptance

Run `~/Projects/ouroboros-manifold/.venv/bin/python -m pytest tests/skilllab/arena/test_stage3_reach.py tests/skilllab/arena/test_stage3_control.py -q -p no:cacheprovider` from the worktree root. Confirm RED. Edit the impl files. Confirm GREEN. Stop.

## Escalation triggers

Stop and report to the parent if a symbol the test imports is not in `contract_imports`, the impl needs a file not listed in `impl_files`, the impl needs a file in `do_not_edit`, two assertions require contradictory behavior, or the impl approaches `impl_line_budget` with assertions still failing.

## Assumption log

Infer nothing silently. Record any inference in `docs/northstar/plans/cascades/lab-stage3/briefs/leaf-01.ASSUMPTIONS.md` (format: `- **<thing>**: <value> - source: <spec line / file / no source>`).
