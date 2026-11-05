---
leaf_id: leaf-02
spec_file: docs/northstar/plans/cascades/lab-stage3/spec.md
spec_lines: 32-35
test_files:
  - tests/qa/test_fight_replay_stage3.py
impl_files:
  - scenes/proto/fight_replay/fight_replay.gd
contract_imports:
do_not_edit:
  - docs/northstar/**
  - tests/**
  - csrc/**
  - scripts/specfactory/**
  - .claude-swarm.toml
  - scripts/skilllab/arena/features.py
  - scripts/skilllab/arena/run.py
  - scripts/skilllab/arena/snapshot.py
  - scripts/skilllab/arena/SNAPSHOT.md
  - scripts/skilllab/arena/page.py
  - scripts/replay.sh
  - README.md
  - scripts/skilllab/arena/situations.py
impl_line_budget: 80
test_assertion_budget: 30
test_owned_by: parent
wave: 1
---

## Task

Implement spec criteria 7, 8 and 9 in the fight replay. Read `landscape` from the fight file and build that preset in place of the `REPLAY_LANDSCAPE` constant (a file without the key builds `small_flat`; the constant stays as the fallback); expose `landscape` and `hud_tick` (the tick line's text) in `qa_state()`; the tick line becomes `tick %d  A %d  B %d  blocked %d  frame %d/%d` using the current frame's `blocked` list length. A control fight needs no new code if its twin layout has `features == []`: `_load_features` already reads the JSON beside `layout_path`. Reuse the layout shot's `_tiered_terrain` and `_add_tier_tint` for `small_tiered`; add no second drawing.

Test files `tests/qa/test_fight_replay_stage3.py` are already written and failing. You are working inside your own git worktree, which is your working directory. Never run git. Edit `scenes/proto/fight_replay/fight_replay.gd` in place there until those tests pass. Do not modify test files, do not create files outside `impl_files`, and keep every edit to what the cited spec criteria require (no cosmetic refactoring; a doc claim your change makes wrong is rewritten in the same file). Keep the module's existing comment style and the `# See also:` traceability lines.

The existing `tests/qa/test_fight_replay.py` and `tests/qa/test_fight_replay_features.py` must stay green; one of them may assert the old tick line text, in which case stop and report `test-defect:` with the test id and line.

## Acceptance

Run `timeout 1800 xvfb-run -a -s '-screen 0 1920x1080x24' ~/Projects/ouroboros-manifold/.venv/bin/python -m pytest tests/qa/test_fight_replay_stage3.py tests/qa/test_fight_replay.py tests/qa/test_fight_replay_features.py -q -p no:cacheprovider` from the worktree root. Confirm RED. Edit the impl files. Confirm GREEN. Stop.

## Escalation triggers

Stop and report to the parent if a symbol the test imports is not in `contract_imports`, the impl needs a file not listed in `impl_files`, the impl needs a file in `do_not_edit`, two assertions require contradictory behavior, or the impl approaches `impl_line_budget` with assertions still failing.

## Assumption log

Infer nothing silently. Record any inference in `docs/northstar/plans/cascades/lab-stage3/briefs/leaf-02.ASSUMPTIONS.md` (format: `- **<thing>**: <value> - source: <spec line / file / no source>`).
