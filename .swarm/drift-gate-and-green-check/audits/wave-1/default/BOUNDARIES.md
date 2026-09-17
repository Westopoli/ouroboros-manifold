# Boundary sweep — wave 1, shard default (drift-gate-and-green-check)

Revised after the first test-quality audit pass (`TEST-AUDIT.md`, 1 🔴 + 8 🟡). Rows
below reflect the post-fix state; see "Audit round 1 resolution" at the bottom for
what changed and why.

| symbol | axis | boundary | spec says | disposition |
|---|---|---|---|---|
| `OM_FEAT_DRIFT` | Range | off (0), every region | AC1: "skips the drift step entirely"; epic R-160-01: "every region" | test written, `test_R_160_01_drift_off_leaves_fields_unchanged` (now 3 regions, distinct values, all asserted frozen) |
| `OM_FEAT_DRIFT` | Range | on (1), fresh world | AC2: "returns a world with OM_FEAT_DRIFT on" | test written, `test_R_160_02_default_world_has_only_drift_on` + `test_R_160_02_default_world_drifts` |
| `OM_FEAT_DRIFT` | Existence | non-0/1 value written via `om_world_set_feature` | not spec'd; pre-existing symbol/API, unchanged by this leaf | out of scope — this leaf only gates and relocates the drift loop, never changes how the switch is stored or read |
| tick order (drift vs. factions) | Ordering | drift step relative to faction budget step, same tick | AC3: budget reads pre-drift economy | test written, `test_R_160_03_budget_step_reads_pre_drift_economy` |
| tick order (drift vs. friction/admin-revolts specifically) | Ordering | drift step relative to `om_step_friction`/`om_step_admin_revolts` | spec line 7: "after factions/friction/admin-revolts" | **deferred, reason stated** — `csrc/friction.c`'s `om_step_friction` and `om_step_admin_revolts` are both unimplemented no-op stubs today (card 206, a separate build card outside leaf-01's `csrc/sim.c` + `csrc/region.c` scope). With both steps genuine no-ops, no fixture can observe which side of drift they ran on — any assertion built on their effect (a first attempt tried this: a border-friction economy delta engineered to land exactly on the overcap boundary) fails identically whether drift runs before or after them, because friction never actually applies its -0.05. That first attempt was removed rather than kept as a weak/vacuous smoke test (a test that cannot fail under a wrong implementation is the same defect class as a detector that cannot fail at all). The real enforcement for this specific sub-ordering is Phase 6 admission-time code review: leaf-01's brief instructs one atomic relocation of the whole drift loop below the entire FACTIONS/FRICTION/ADMIN_REVOLTS block, not between any two of them. `csrc/sim.c` already ends in three separate `if (om_world_feature(...))` blocks (FACTIONS, then FRICTION, then ADMIN_REVOLTS), so a wrong placement needs only one misplaced relocation — e.g. dropping the gated drift loop between the FACTIONS block and the FRICTION block — not a deliberate restructure. The admission-time reviewer's job is exactly this: confirm the drift block sits below *all three* `if` blocks, not between any two of them. Revisit with a real runtime assertion once card 206 implements friction/admin-revolts for real. |
| region count | Cardinality | 60 regions / 5,000 ticks | E-02 epic "Scale requirements", pre-existing scale gate | not a new algorithmic path — this leaf gates+reorders an existing O(n) loop, no growth-claim change; covered by the pre-existing `test_E02_gate_drift_trajectory.py` via `apex_test_cmd` |
| S-033 regression (AC4) | Conformance | committed `om_faction_step_budget` body produces ALG-17's answer once AC3 holds | AC4 | **fixed from audit 🔴** — `apex_test_cmd` now includes `tests/csim/test_E05_S033_territory_pays_or_costs.py::test_R_033_01_budget_66_8_40_8` explicitly (`.claude-swarm.toml`) |
| trace/checksum emission | Existence | DRIFT off → no trace rows emitted at all | spec Constraints: emission "moves with the loop" | test written, `test_R_160_04_drift_off_emits_no_trace_rows` |
| trace/checksum emission | Cardinality | DRIFT on → checksum only on cadence boundary | spec Constraints; pre-existing contract (`om_checksum_cadence`) | test written, `test_R_160_04_drift_on_checksum_cadence_still_works` (vacuous-today, commented as such — current bug makes DRIFT-on behavior identical pre/post fix; holds for the right reason once the gate is real) |
| `green_check.py` card arg | Existence | card file missing | brief leaf-02 Task | test written, `test_green_check_exits_3_on_a_missing_card` |
| `green_check.py` reference arg | Existence | reference file missing | brief leaf-02 Task | test written, `test_green_check_exits_3_on_a_missing_reference` |
| `green_check.py` acceptance result | Range/Conformance | stub already passes | AC5 | test written, `test_green_check_refuses_a_reference_that_also_passes_on_the_stub` (tightened: exact phrase "already passes" only, no `or "cannot"` escape hatch) |
| `green_check.py` acceptance result | Range/Conformance | reference fails | AC5 | test written, `test_green_check_fails_a_reference_that_does_not_pass` |
| `green_check.py` project checkout | Reference | worktree must not leak into caller's checkout | AC5 | test written, merged into `test_green_check_passes_on_a_real_reference` |
| `green_check.py` worktree cleanup | Reference | scratch worktree removed after every run | brief leaf-02 Task: "Always remove the scratch worktree before returning" | **fixed from audit finding #6** — `test_green_check_passes_on_a_real_reference` now also asserts `git worktree list` shows exactly one entry (no leftover) after a run |
| `green_check.py` acceptance parsing | Conformance | actually parses+runs the card's `acceptance:` list, not a hardcoded pytest call | AC5: "runs the card's acceptance command" | **fixed from audit finding #7** — default fixture now uses a non-pytest sentinel command (`check_value.py`); a second fixture variant keeps the pytest shape for coverage of both command styles |
| `green_check.py` acceptance list | Existence | empty `acceptance:` list in card | brief leaf-02 Task: "no acceptance commands" is a named exit-3 case | **fixed from audit finding #8** — test written, `test_green_check_exits_3_on_empty_acceptance_list` |
| `green_check.py` `project` arg | Existence | `project` path is not a directory | brief leaf-02 Task: "`project` not a directory" is a named exit-3 case | **fixed from audit finding #8** — test written, `test_green_check_exits_3_when_project_is_not_a_directory` |
| `green_check.py` `project` arg | Reference | `project` path is not a git repo | not spec'd | not tested — every real card in `~/Projects/agora/queue/` names an already-initialized project repo; lower value than the two cases above, which the brief explicitly names |
| `green_check.py` external call budget | Cardinality | one `git worktree add`, acceptance list run at most twice per invocation | spec line 34 (corrected in audit round 2: was "once each", actually "acceptance runs at most twice — baseline, then reference") | not directly counted by a spy/call-count assertion; implicitly exercised by every exit-0/1/2 test (each requires both the baseline and, where reached, the reference run to actually execute in sequence for the test's own assertions to hold) — a spy-based call-count assertion is deferred as lower value than the exit-3/cleanup gaps already fixed this round |
| AC6 doc row | Existence | `docs/northstar/spec_factory.md` gains a `green_check.py` pipeline row + reference-body path | AC6 | **fixed from audit finding #4** — test written, `test_spec_factory_doc_documents_green_check` |

Growth claim: none set on either leaf (`scale_assertions` not set) — the spec's Scale
& Boundary Profile states `unbounded-unknown — assert growth only, no absolutes` for
the drift gate's hot path, but this wave does not change that path's asymptotic
shape (gate + reorder only), and green_check runs O(1) shell-outs per invocation.
Confirmed by the audit round: no leaf here owns a hot path whose growth changed.

## Audit round 1 resolution

`TEST-AUDIT.md` findings #1 (🔴 AC4 uncovered), #5 (🟡 refusal-reason escape hatch),
and the "card ID" vs. "card file path" spec-wording note under #7 were fixed
directly by the parent (trivial: a config-file line, a quoted-string removal, a
spec-doc wording correction — no new assertion, no new test file).

Findings #2, #4, #6, #7, #8, #9 were fixed by three test-fixer sub-agents (Sonnet),
run sequentially where they touched the same file (never two fixers on one file at
once): one on `tests/csim/test_E02_S160_drift_gate.py` for #2 (later revised further
by the parent — see the ordering row above) and #9, one on
`tests/specfactory/test_green_check.py` for #4/#6/#7/#8, and one more on
`tests/csim/test_E02_S160_drift_gate.py` for #3.

During independent verification of the #2 fix, the parent found the fixer's
friction-ordering test could never pass under ANY implementation leaf-01 could
produce (it asserted a value that only friction's actual -0.05 effect could
produce, but friction is a no-op stub) — a test-cannot-pass defect, not caught by
the fixer's own RED check because "still red" was consistent with both "correctly
detects the bug" and "can never detect anything." The parent replaced it with the
explicit deferral row above rather than shipping an unsatisfiable test on leaf-01.
