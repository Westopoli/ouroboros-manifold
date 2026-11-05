---
leaf_id: leaf-02
spec_file: docs/northstar/plans/cascades/lab-stage4/spec.md
spec_lines: 28-31
test_file: tests/qa/test_fight_replay_stage4.py
impl_file: scenes/proto/fight_replay/fight_replay.gd
test_files:
  - tests/qa/test_fight_replay_stage4.py
impl_files:
  - scenes/proto/fight_replay/fight_replay.gd
contract_imports:
  - QA_STATE_KEYS_STAGE4
do_not_edit:
  - scripts/skilllab/arena/run.py
  - scripts/skilllab/arena/snapshot.py
  - scripts/skilllab/arena/SNAPSHOT.md
  - tests/skilllab/arena/test_stage4_run.py
  - tests/skilllab/arena/test_stage4_snapshot.py
  - tests/skilllab/arena/h088_fixtures.py
  - scripts/skilllab/arena/page.py
  - tests/skilllab/arena/test_page_stage4.py
  - csrc/ouroboros_sim.h
  - docs/northstar/spec_factory/signatures.toml
  - docs/bible/**
  - docs/northstar/**
  - tests/**
  - scripts/specfactory/**
  - Makefile
  - tests/csim/data/**
  - tests/skilllab/golden_hashes.json
impl_line_budget: 160
test_assertion_budget: 40
test_owned_by: parent
wave: 1
---

## Task

Implement spec criteria 7 to 9 (spec lines 28-31) in `fight_replay.gd`: sight discs (one per role per side anchored on the tick-0 unit the role ring uses, radius `sights[role]`, side colour, alpha 0.25, through `Marks.ring_runs`; key V toggles a disc under every living unit; a fight file without `sights` draws none), hollow marks (a living unit that no living unit of the other side lists in `seen`, drawn at alpha 0.35 with its arrow kept; a frame without `seen` keys draws nobody hollow) and the HUD (tick line `tick %d  A %d  B %d  blocked %d  A sees %d  B sees %d  frame %d/%d` when the frame has `seen`, else the stage 3 line unchanged; the last frame's end line gains `first seen A <tick|never>  B <tick|never>` from `result.first_seen`). `qa_state()` gains `sight_rings`, `sight_mode`, `hollow_units`, `hud_sight`, `seen_counts`. Mirror how the role rings and key R are built in the same file (`_build_role_rings`, `_unit_rings`, `_ring_state`). Run `godot.real --headless --import --path <your worktree>` once before the tests; the console must stay free of `SCRIPT ERROR`, `ERROR:` and `Parser Error`. A `.uid` sidecar is not needed: no new script file.

## Acceptance

You are working inside your own git worktree (`.swarm/lab-stage4/worktrees/leaf-02/`), your working directory; the parent manages it. Never run git. Run `cd <worktree> && /home/westopoli/Projects/ouroboros-manifold/.venv/bin/python -m pytest tests/qa/test_fight_replay_stage4.py -q -p no:cacheprovider` (replace `<worktree>` with the absolute worktree path; the Python interpreter is the main checkout's venv). Confirm RED. Edit the impl files in place. Confirm GREEN. Also run the stage 3 tests for the files you touch (`tests/skilllab/arena/test_stage3_*.py`, `test_run.py`, `test_page.py`, `tests/qa/test_fight_replay*.py`) and keep them green. Stop. Read `docs/method/builder.md` first; its rules apply (tests are never edited; the Godot runs go under `timeout 1800`). Stop past 120k context.

## Escalation triggers

Stop and report to the parent if:
- A type the test imports is not in contract_imports.
- The impl would need to create a file not listed in `impl_files`.
- The impl would need to edit a file in do_not_edit.
- Two sibling assertions seem to require contradictory behavior.
- Impl approaches impl_line_budget with assertions still failing.
- A number nobody gave would be needed.

## Assumption log

Write every inference the brief did not specify to `docs/northstar/plans/cascades/lab-stage4/briefs/leaf-02.ASSUMPTIONS.md` (`- **<thing>**: <value> — source: <spec line / contract symbol / file, or "no source — pure guess">`). Read siblings' files before logging; adopt a compatible value, escalate a contradictory one.
