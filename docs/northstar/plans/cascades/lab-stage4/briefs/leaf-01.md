---
leaf_id: leaf-01
spec_file: docs/northstar/plans/cascades/lab-stage4/spec.md
spec_lines: 20-26
test_file: tests/skilllab/arena/test_stage4_run.py
impl_file: scripts/skilllab/arena/run.py
test_files:
  - tests/skilllab/arena/test_stage4_run.py
  - tests/skilllab/arena/test_stage4_snapshot.py
  - tests/skilllab/arena/h088_fixtures.py
impl_files:
  - scripts/skilllab/arena/run.py
  - scripts/skilllab/arena/snapshot.py
  - scripts/skilllab/arena/SNAPSHOT.md
contract_imports:
  - fight
  - validate
  - CHECK_EVERY
do_not_edit:
  - scenes/proto/fight_replay/fight_replay.gd
  - tests/qa/test_fight_replay_stage4.py
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
impl_line_budget: 220
test_assertion_budget: 40
test_owned_by: parent
wave: 1
---

## Task

Implement spec criteria 1 to 6 (spec lines 20-26) in `run.py`, `snapshot.py` and `SNAPSHOT.md`. With `--sight on` the runner applies the stage 4 rule set: targeting by sight left on, `engine.set_era_kind(w, 1)`, a canvas and walking units for every layout, `engine.set_reach(w, type_id, 0, 1)` for every registered role, `engine.order_guard` on the holder's units after spawning for `hold:A` and `hold:B`, and the fight document keys `movement_kind`, `orders.guard`, per-unit `seen`, `sights` and `result.first_seen`. `first_seen` is sampled every `CHECK_EVERY` ticks starting at tick 0 with `engine.seen_by_sight`. With `--sight off` the output is byte-identical to main `240773dd`, including `results.md`. Add `--control ground|sight` (default `ground`): `sight` writes `<control-dir>/<id>-control-s<n>.fight.json` as the same layout and seed run with the stage 4 rule set except targeting by sight off (internal `sight` value `"control"` of `fight`: ground era, walking, reach 0 up 1 down, holder guarded; document `sight` `"off"`, `movement_kind` 1, `orders.guard` as applied, no `seen`/`sights`/`first_seen`), for every layout, with no twin layout files; `--control sight` without `--control-dir` writes nothing; `--control ground` stays allowed with `--sight on`; `--control sight` with `--sight off` exits 2. With `--sight on` `results.md` gains the columns `first seen A` and `first seen B`. `snapshot.validate` accepts the new optional keys on `om-fight-2` and rejects each on `om-fight-1`, naming the key. `SNAPSHOT.md` documents the keys and the sight control. Match the existing structure of `run.py`: extend `fight`, `_frame`, `_document` and `main` in place; no new module. Keep the `--sight off` code path as it is, so the stage 3 tests stay green.

## Acceptance

You are working inside your own git worktree (`.swarm/lab-stage4/worktrees/leaf-01/`), your working directory; the parent manages it. Never run git. Run `cd <worktree> && /home/westopoli/Projects/ouroboros-manifold/.venv/bin/python -m pytest tests/skilllab/arena/test_stage4_run.py tests/skilllab/arena/test_stage4_snapshot.py -q -p no:cacheprovider` (replace `<worktree>` with the absolute worktree path; the Python interpreter is the main checkout's venv). Confirm RED. Edit the impl files in place. Confirm GREEN. Also run the stage 3 tests for the files you touch (`tests/skilllab/arena/test_stage3_*.py`, `test_run.py`, `test_page.py`, `tests/qa/test_fight_replay*.py`) and keep them green. Stop. Read `docs/method/builder.md` first; its rules apply (tests are never edited; the Godot runs go under `timeout 1800`). Stop past 120k context.

## Escalation triggers

Stop and report to the parent if:
- A type the test imports is not in contract_imports.
- The impl would need to create a file not listed in `impl_files`.
- The impl would need to edit a file in do_not_edit.
- Two sibling assertions seem to require contradictory behavior.
- Impl approaches impl_line_budget with assertions still failing.
- A number nobody gave would be needed.

## Assumption log

Write every inference the brief did not specify to `docs/northstar/plans/cascades/lab-stage4/briefs/leaf-01.ASSUMPTIONS.md` (`- **<thing>**: <value> — source: <spec line / contract symbol / file, or "no source — pure guess">`). Read siblings' files before logging; adopt a compatible value, escalate a contradictory one.
