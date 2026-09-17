# Plan-consistency — drift-gate-and-green-check

| # | check | finding | artifact + line | resolution |
|---|-------|---------|-----------------|------------|
| — | (none — all five checks below are clean) | | | |

## Checks with no finding

1. **AC ↔ AC.** No two ACs set conflicting values or behavior for the same thing. AC1–AC3 describe one gate/order fix from independent angles (off-behavior, default-state, cross-step read order); AC4 is a downstream consequence of AC3, not a restatement; AC5–AC6 are the unrelated green_check leaf. No contradiction.
2. **AC ↔ contract.** `type_contract_path = csrc/ouroboros_sim.h`. Every C symbol ACs 1–4 name (`OM_FEAT_DRIFT`, `om_world_new`, `om_world_feature`/`om_world_set_feature`, `om_faction_budget`) already exists in the locked header. AC5–AC6 (green_check.py) are Python tooling with no C contract symbol to resolve against — brief L2 will carry an empty or Python-only `contract_imports`, which is valid (no requirement that a brief use the shared contract file).
3. **AC ↔ umbrella.** `umbrella_test_cmd` runs `tests/csim/test_E02_S160_drift_gate.py`, which directly asserts AC1 (`test_R_160_01`), AC2 (`test_R_160_02_default_world_has_only_drift_on`, `test_R_160_02_default_world_drifts`), and AC3 (`test_R_160_03_budget_step_reads_pre_drift_economy`). No assertion contradicts an AC. AC4 (S-033 regression) and AC5–AC6 (green_check) are outside the umbrella's scope by design — two different leaves, two different kinds of test — and are covered instead by `apex_test_cmd` and Phase 7's targeted verification list respectively; noted here so the gap is explicit, not silent.
4. **Observability.** Every AC names an outcome something can assert on: field bytes unchanged, feature-switch integer reads, a budget-delta float, `green_check.py`'s exit code and stderr text, a doc-table row's presence. No AC is untestable.
5. **Named-entity resolution.** Every entity an AC names resolves inside this repo: `OM_FEAT_DRIFT`, `om_world_new`, `om_faction_budget` (existing header symbols), `csrc/faction.c`'s committed budget body (`d641ea2`), `green_check.py` (this wave's own deliverable, not an external dependency), `git worktree` (already the mechanism `worktree_ops.py` uses throughout this skill), `docs/northstar/spec_factory.md` (existing doc). No external, unverified capability is assumed anywhere in this spec.

**Verdict: clean, no open findings. Phase 2 proceeds.**
