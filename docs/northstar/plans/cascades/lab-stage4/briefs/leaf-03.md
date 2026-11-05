---
leaf_id: leaf-03
spec_file: docs/northstar/plans/cascades/lab-stage4/spec.md
spec_lines: 33-35
test_file: tests/skilllab/arena/test_page_stage4.py
impl_file: scripts/skilllab/arena/page.py
test_files:
  - tests/skilllab/arena/test_page_stage4.py
impl_files:
  - scripts/skilllab/arena/page.py
contract_imports:
  - build
do_not_edit:
  - scripts/skilllab/arena/run.py
  - scripts/skilllab/arena/snapshot.py
  - scripts/skilllab/arena/SNAPSHOT.md
  - tests/skilllab/arena/test_stage4_run.py
  - tests/skilllab/arena/test_stage4_snapshot.py
  - tests/skilllab/arena/h088_fixtures.py
  - scenes/proto/fight_replay/fight_replay.gd
  - tests/qa/test_fight_replay_stage4.py
  - csrc/ouroboros_sim.h
  - docs/northstar/spec_factory/signatures.toml
  - docs/bible/**
  - docs/northstar/**
  - tests/**
  - scripts/specfactory/**
  - Makefile
  - tests/csim/data/**
  - tests/skilllab/golden_hashes.json
impl_line_budget: 100
test_assertion_budget: 40
test_owned_by: parent
wave: 1
---

## Task

Implement spec criteria 10 and 11 (spec lines 33-35) in `page.py`. `build(..., stage=4)` prints the header `Stage 4, sight`. A control strip whose control document has `sight` equal to `off` while the main fight's `sight` is `on` carries the caption `control: the same fight with everyone seeing everyone (sight off)`; every other control keeps today's ground caption. Every row, rated or not, prints `first seen A <tick|never>  B <tick|never>` beside the first-shot line from `result.first_seen`, and `-` when the key is absent. Extend the existing `_row`, caption and header code in place; no new module. The existing page tests must stay green.

## Acceptance

You are working inside your own git worktree (`.swarm/lab-stage4/worktrees/leaf-03/`), your working directory; the parent manages it. Never run git. Run `cd <worktree> && /home/westopoli/Projects/ouroboros-manifold/.venv/bin/python -m pytest tests/skilllab/arena/test_page_stage4.py -q -p no:cacheprovider` (replace `<worktree>` with the absolute worktree path; the Python interpreter is the main checkout's venv). Confirm RED. Edit the impl files in place. Confirm GREEN. Also run the stage 3 tests for the files you touch (`tests/skilllab/arena/test_stage3_*.py`, `test_run.py`, `test_page.py`, `tests/qa/test_fight_replay*.py`) and keep them green. Stop. Read `docs/method/builder.md` first; its rules apply (tests are never edited; the Godot runs go under `timeout 1800`). Stop past 120k context.

## Escalation triggers

Stop and report to the parent if:
- A type the test imports is not in contract_imports.
- The impl would need to create a file not listed in `impl_files`.
- The impl would need to edit a file in do_not_edit.
- Two sibling assertions seem to require contradictory behavior.
- Impl approaches impl_line_budget with assertions still failing.
- A number nobody gave would be needed.

## Assumption log

Write every inference the brief did not specify to `docs/northstar/plans/cascades/lab-stage4/briefs/leaf-03.ASSUMPTIONS.md` (`- **<thing>**: <value> — source: <spec line / contract symbol / file, or "no source — pure guess">`). Read siblings' files before logging; adopt a compatible value, escalate a contradictory one.
