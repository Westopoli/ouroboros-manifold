---
leaf_id: leaf-05
spec_file: docs/northstar/plans/cascades/lab-stage3/spec.md
spec_lines: 45-47
test_files:
  - tests/skilllab/arena/test_situations_slope.py
impl_files:
  - scripts/skilllab/arena/situations.py
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
  - scenes/proto/fight_replay/fight_replay.gd
  - scripts/skilllab/arena/page.py
  - scripts/replay.sh
  - README.md
impl_line_budget: 40
test_assertion_budget: 30
test_owned_by: parent
wave: 1
---

## Task

Implement spec criteria 14 and 15 in the situation converter: a Features table row with `kind = slope` and `size = <length> x <width>` converts to the H-025 round-two feature `{kind: slope, x, y, length, width, heading: 0.0, from_band: 0, to_band: 1}` (numbers, not strings); every other kind keeps today's `{kind, x, y, size, notes}` row. `docs/northstar/research/layer_dynamics/situations/SIT-0109-slope.md` must convert, pass `check_layout`, bind (`features.bound`), and run through `run.py` without a REJECT. Reject a slope `size` that is not `<number> x <number>` with the converter's `Reject`.

Test files `tests/skilllab/arena/test_situations_slope.py` are already written and failing. You are working inside your own git worktree, which is your working directory. Never run git. Edit `scripts/skilllab/arena/situations.py` in place there until those tests pass. Do not modify test files, do not create files outside `impl_files`, and keep every edit to what the cited spec criteria require (no cosmetic refactoring; a doc claim your change makes wrong is rewritten in the same file). Keep the module's existing comment style and the `# See also:` traceability lines.

## Acceptance

Run `~/Projects/ouroboros-manifold/.venv/bin/python -m pytest tests/skilllab/arena/test_situations_slope.py tests/skilllab/arena/test_situations.py -q -p no:cacheprovider` from the worktree root. Confirm RED. Edit the impl files. Confirm GREEN. Stop.

## Escalation triggers

Stop and report to the parent if a symbol the test imports is not in `contract_imports`, the impl needs a file not listed in `impl_files`, the impl needs a file in `do_not_edit`, two assertions require contradictory behavior, or the impl approaches `impl_line_budget` with assertions still failing.

## Assumption log

Infer nothing silently. Record any inference in `docs/northstar/plans/cascades/lab-stage3/briefs/leaf-05.ASSUMPTIONS.md` (format: `- **<thing>**: <value> - source: <spec line / file / no source>`).
