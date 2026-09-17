---
leaf_id: leaf-01
spec_file: docs/test_specs/drift-gate-and-green-check.md
spec_lines: 7-25
test_files:
  - tests/csim/test_E02_S160_drift_gate.py
  - tests/csim/controls/test_control_drift_gate_ignored.py
impl_files:
  - csrc/sim.c
  - csrc/region.c
contract_imports:
do_not_edit:
  - scripts/specfactory/green_check.py
  - docs/northstar/spec_factory.md
  - tests/specfactory/**
  - docs/bible/game_bible.md
  - docs/bible_history/**
  - docs/test_specs/cover_asteroid_los_spec.md
  - docs/test_specs/cover_los_rework_spec.md
  - docs/test_specs/wave_3_pre_zip_wiring.md
  - docs/test_specs/drift-gate-and-green-check.md
  - docs/phase1_ship_plan.md
  - docs/priority_queue.md
  - docs/bible/stories.md
  - docs/bible/epics/E-02-region-fields-and-drift.md
  - docs/bible/algorithms.md
  - simulation/**
  - csrc/ouroboros_sim.h
  - Makefile
  - tests/csim/**
test_owned_by: parent
impl_line_budget: 60
test_assertion_budget: 10
codebase_preconditions:
  - name: "FACTIONS/FRICTION/ADMIN_REVOLTS gates already exist in sim.c"
    verify: "grep -q 'om_world_feature(w, OM_FEAT_FACTIONS)' csrc/sim.c"
---

## Task

Fix two defects in `csrc/sim.c`'s drift loop (the `for (uint32_t i = 0; i < w->n_regions; i++)` block that computes `om_drift_row`, currently unconditional), per spec_lines 7-25:

1. Wrap the whole drift loop in `if (om_world_feature(w, OM_FEAT_DRIFT)) { ... }` — mirror the existing pattern already used for `OM_FEAT_FACTIONS`, `OM_FEAT_FRICTION`, and `OM_FEAT_ADMIN_REVOLTS` later in the same function.
2. Move the (now-gated) drift loop to run *after* the `OM_FEAT_FACTIONS` / `OM_FEAT_FRICTION` / `OM_FEAT_ADMIN_REVOLTS` blocks, not before — tick sequence step 5 runs after step 3/4, not before it (`docs/bible/algorithms.md:9-29`). The trace-row and checksum emission currently inside the per-region loop body moves with the loop; nothing about the emission logic itself changes.
3. In `csrc/region.c`'s `om_world_new`, set the new world's `OM_FEAT_DRIFT` switch on (`om_world_set_feature`-equivalent write to the same `features` array `om_world_feature` reads) — every other feature switch stays at its `calloc`-zeroed default (off).

## Acceptance

You are working inside your own git worktree — a private checkout at `.swarm/drift-gate-and-green-check/worktrees/leaf-01/`, which is your working directory and which the parent manages. Never run git. Nothing you do there is visible to a sibling leaf or to the user's checkout.

Run `.venv/bin/python -m pytest tests/csim/test_E02_S160_drift_gate.py tests/csim/controls/test_control_drift_gate_ignored.py -p no:cacheprovider -v` (rebuilds `libouroboros.so`/`libouroboros_dbg.so` automatically via a session fixture). Confirm RED first: `test_E02_S160_drift_gate.py` has 6 tests, 4 of which fail today (`test_R_160_01_drift_off_leaves_fields_unchanged`, `test_R_160_02_default_world_has_only_drift_on`, `test_R_160_03_budget_step_reads_pre_drift_economy`, `test_R_160_04_drift_off_emits_no_trace_rows`); the other 2 (`test_R_160_02_default_world_drifts`, `test_R_160_04_drift_on_checksum_cadence_still_works`) and the control test currently pass vacuously because the gate doesn't exist yet and drift runs unconditionally — that is expected pre-fix, not a bug in any of the three tests (each is commented in place explaining why). Edit `csrc/sim.c` and `csrc/region.c` in place until all 6 tests in `test_E02_S160_drift_gate.py` pass and the control test still passes (now for the real reason: with the gate implemented, injecting `OM_BUG_DRIFT_GATE_IGNORED` must still make drift run despite the switch being off). Stop.

Do not stage, copy, commit, or move anything.

## Escalation triggers

Stop and report to the parent if:
- Moving the drift loop after the faction/friction/admin block would require restructuring `w->trace_on` / checksum logic beyond relocating it with the loop.
- The fix would require touching any file outside `csrc/sim.c` and `csrc/region.c`.
- A sibling assertion in the test files seems to require contradictory behavior.

## Admission note (parent, not the leaf)

`csrc/friction.c`'s `om_step_friction`/`om_step_admin_revolts` are no-op stubs, so
no test can observe whether the relocated drift block sits after FRICTION and
ADMIN_REVOLTS specifically, only after FACTIONS (`test_R_160_03_...`). At Phase 6
admission, read the diff and confirm the gated drift loop sits below all three
`if (om_world_feature(w, OM_FEAT_...))` blocks (FACTIONS, FRICTION,
ADMIN_REVOLTS), not spliced between any two of them. See
`.swarm/drift-gate-and-green-check/audits/wave-1/default/BOUNDARIES.md`'s
"tick order (drift vs. friction/admin-revolts specifically)" row.

## Assumption log

Same protocol as the canonical brief template (`swarm-shared/references/brief-template.md`): log any inferred value to `.swarm/drift-gate-and-green-check/briefs/leaf-01.ASSUMPTIONS.md` before finishing, checking sibling ASSUMPTIONS files first.
