---
leaf_id: leaf-03
spec_file: docs/northstar/plans/cascades/layout-kit-assault/spec.md
spec_lines: 31-91
test_files:
  - tests/layout/test_render.py
impl_files:
  - scripts/layout/render.py
contract_imports:
do_not_edit:
  - csrc/ouroboros_sim.h
  - csrc/layout_kit.h
  - csrc/layout_internal.h
  - csrc/layout_engine.c
  - csrc/mission.c
  - Makefile
  - docs/**
  - tests/**
  - scenes/**
  - autoload/**
  - scripts/specfactory/**
  - simulation/**
  - csrc/layout_drafts.h
  - csrc/layout_kit.c
  - csrc/layout_kit_pieces.c
  - csrc/layout_kit_graph.c
  - csrc/tools/layout_dump.c
impl_line_budget: 600
test_assertion_budget: 40
test_owned_by: parent
wave: 1
---

## Task

Write the renderer `scripts/layout/render.py`: `render.py map <layout.json> <out.png>` and `render.py sheet <dir> <out.png>`, as acceptance criteria 8 to 10 in the spec lines in `spec_lines` say, reading the JSON schema `om-layout-1` given in the spec's JSON section (key names, `side` as "A"/"B"/"none", numbers as plain JSON numbers). Imports allowed: the Python standard library and Pillow only (`PIL`, version 12.3.0 is in the interpreter named in the Acceptance section). The tests use a hand-written fixture `tests/layout/fixtures/layout_hand.json` (already present, do not edit it); the renderer needs no C binary and never opens a window. Draw at 2x the output size and reduce with `Image.LANCZOS`; the scale is `DRAFT_PX_WU` (20 wu per pixel, read it as a module constant named `DRAFT_PX_WU`). Print a usage line to stderr and exit 2 on bad arguments; exit 1 from `sheet` when a seed file is missing, after writing the image with a labelled empty tile. Mirror the argument-handling shape of `scripts/skilllab/arena/page.py`.

## Acceptance

You are working inside your own git worktree — a private checkout at
`.swarm/layout-kit-assault/worktrees/leaf-03/`, which is your working directory
and which the parent manages. Never run git. Nothing you do there is visible
to a sibling leaf or to the user's checkout.

Your working directory is the absolute worktree path the parent gives you; run `cd <worktree> && /home/westopoli/Projects/ouroboros-manifold/.venv/bin/python -m pytest tests/layout/test_render.py -q -p no:cacheprovider` for your test files. Confirm RED. Edit `impl_file` in
place, at its normal path inside the worktree. Confirm GREEN. Stop.

Do not stage, copy, commit, or move anything. `/manager-mode` Phase 5 commits
your declared files from the worktree onto your branch, and Phase 6 merges
that commit into the integration branch only after every gate passes.

Earlier versions of this template asked the leaf to confirm GREEN *and* write
only to a staging directory. Those two instructions could not both be
satisfied: the test imports impl at its real path, so a leaf that never wrote
there was running its test against the unmodified file and could not reach
GREEN. The worktree removes the conflict rather than picking a side — inside
it, the real path IS yours.

## Escalation triggers

Stop and report to the parent if:
- A type the test imports is not in contract_imports.
- The impl would need to create a file not listed in `impl_files`. (Creating a
  file that IS listed is ordinary — a declared impl file often does not exist
  yet.)
- The impl would need to edit a file in do_not_edit.
- Two sibling assertions seem to require contradictory behavior.
- Impl approaches impl_line_budget with assertions still failing.

## Protocols

Assumption log, sibling-assumption read, question ledger and contract-proposal protocol: follow `docs/northstar/plans/cascades/layout-kit-assault/briefs/PROTOCOL.md` (substitute your own leaf id). Briefs directory for ASSUMPTIONS files: `docs/northstar/plans/cascades/layout-kit-assault/briefs/`.
