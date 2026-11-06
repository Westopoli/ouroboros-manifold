---
leaf_id: leaf-01
spec_file: docs/northstar/plans/cascades/layout-kit-assault/spec.md
spec_lines: 27-98
test_files:
  - tests/csim/test_layout_kit_engine.py
  - tests/csim/test_layout_kit_header.py
impl_files:
  - csrc/layout_drafts.h
  - csrc/layout_kit.c
  - csrc/layout_kit_pieces.c
  - csrc/layout_kit_graph.c
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
  - scripts/layout/render.py
  - csrc/tools/layout_dump.c
impl_line_budget: 1500
test_assertion_budget: 40
test_owned_by: parent
wave: 1
growth_claim: quadratic-ok
---

## Task

Implement the layout kit engine in the four files in `impl_files`, behind the frozen header `csrc/layout_kit.h` (read it in full first; never edit it). `csrc/layout_kit.c` already exists as a sentinel (every entry point returns -1, NULL or 0): replace its body. Read the spec at the lines in `spec_lines` and follow its algorithm section, checks section, determinism section and the engine acceptance criteria 1 to 4 exactly. Entry points to implement, all declared in `csrc/layout_kit.h`: `om_lk_generate`, `om_lk_run_checks`, `om_lk_name`, `om_lk_draft_count`, `om_lk_draft_name`, `om_lk_draft_value`. Put every figure in `csrc/layout_drafts.h` as a `DRAFT_` macro and list the macros in one X-macro table named `LK_DRAFT_TABLE(X)`; the spec names the required drafts and their values; add the further drafts you need with a one-line reason each in your ASSUMPTIONS file. Put the splitmix64 constants as `LK_RNG_` macros beside the table. Assign the code to the files by responsibility: `layout_kit.c` holds the splitmix64 stream, the district grid and the driver (`om_lk_generate`, candidates, sides modes, `om_lk_name`, the draft accessors); `layout_kit_pieces.c` holds the six kit pieces and the request list; `layout_kit_graph.c` holds the route graph, Dijkstra, the fairness numbers and `om_lk_run_checks`. Share helpers between the files through declarations at the top of `layout_drafts.h` or through static-free internal functions prefixed `lk_`; keep every name prefixed `om_lk_` or `lk_` so nothing collides with `csrc/layout_engine.c`. Determinism rules (spec determinism paragraph) are mandatory: no `qsort`, no `atan2`, no `sin`/`cos`/`pow`/`exp`/`log`, only `sqrt fabs floor fmin fmax`; angles from `om_tn_sin_q16`/`om_tn_cos_q16` (declare them with a local prototype); no heap; the struct is zeroed first. Include `<stdint.h>` and `layout_kit.h` only; do not include `layout_internal.h`. The tests build `csrc/layout_kit*.c` and `csrc/terrain_noise.c` together with a parent-owned probe driver `tests/csim/layout_kit_probe.c`; do not edit the probe.

## Acceptance

You are working inside your own git worktree — a private checkout at
`.swarm/layout-kit-assault/worktrees/leaf-01/`, which is your working directory
and which the parent manages. Never run git. Nothing you do there is visible
to a sibling leaf or to the user's checkout.

Your working directory is the absolute worktree path the parent gives you; run `cd <worktree> && /home/westopoli/Projects/ouroboros-manifold/.venv/bin/python -m pytest tests/csim/test_layout_kit_engine.py tests/csim/test_layout_kit_header.py -q -p no:cacheprovider` for your test files. Confirm RED. Edit `impl_file` in
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
