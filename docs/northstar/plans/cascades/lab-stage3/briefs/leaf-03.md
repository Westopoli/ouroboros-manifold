---
leaf_id: leaf-03
spec_file: docs/northstar/plans/cascades/lab-stage3/spec.md
spec_lines: 37-39
test_files:
  - tests/skilllab/arena/test_page_stage3.py
impl_files:
  - scripts/skilllab/arena/page.py
contract_imports:
  - build
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
  - scripts/replay.sh
  - README.md
  - scripts/skilllab/arena/situations.py
impl_line_budget: 120
test_assertion_budget: 30
test_owned_by: parent
wave: 1
---

## Task

Implement spec criteria 10 and 11 in `page.py`. `build(d, out, control_dir=None, stage=None, sentences=None)` and the CLI flags `--stage N` and `--sentences <md>`: the header names the stage (`Stage 3, the ground pushes back`, `Stage 2, roles and ranges`, else `Stage N`; the old `DRAFT-stage2-page` header text with `not landed` goes); a sentences markdown table `| id | What to expect | Approve means | Deny means |` overrides the layout's own sentence keys per layout id; the control strip appears for every fight (rated block or unrated `_row`) whose control file exists in `control_dir`, with the caption `control: the same fight without the ground (features emptied)`; unrated rows get the three sentences and a `blocked unit-frames: n` line, n = sum of `len(frame.get("blocked", []))`; a rated block shows the same line. Existing page tests must stay green.

Test files `tests/skilllab/arena/test_page_stage3.py` are already written and failing. You are working inside your own git worktree, which is your working directory. Never run git. Edit `scripts/skilllab/arena/page.py` in place there until those tests pass. Do not modify test files, do not create files outside `impl_files`, and keep every edit to what the cited spec criteria require (no cosmetic refactoring; a doc claim your change makes wrong is rewritten in the same file). Keep the module's existing comment style and the `# See also:` traceability lines.

## Acceptance

Run `~/Projects/ouroboros-manifold/.venv/bin/python -m pytest tests/skilllab/arena/test_page_stage3.py tests/skilllab/arena/test_page.py tests/skilllab/arena/test_page_control_strip.py tests/skilllab/arena/test_page_readability.py tests/skilllab/arena/test_page_scoring.py -q -p no:cacheprovider` from the worktree root. Confirm RED. Edit the impl files. Confirm GREEN. Stop.

## Escalation triggers

Stop and report to the parent if a symbol the test imports is not in `contract_imports`, the impl needs a file not listed in `impl_files`, the impl needs a file in `do_not_edit`, two assertions require contradictory behavior, or the impl approaches `impl_line_budget` with assertions still failing.

## Assumption log

Infer nothing silently. Record any inference in `docs/northstar/plans/cascades/lab-stage3/briefs/leaf-03.ASSUMPTIONS.md` (format: `- **<thing>**: <value> - source: <spec line / file / no source>`).
