# HANDOFF BRIEF — executor lane: ouroboros-side fixes the audit put before any Agora cascade

Self-contained. Source: `docs/northstar/research/factory/audit_2026-09-21/README.md` (23 findings both reviewers flagged, verified) and Round 9 in `docs/northstar/research/harness_defects_2026-09-17/DECISIONS.md` (E1 Windows weekly, E2 four interrupts automated, E3 Westley authors the day side). This brief is the ouroboros half; the Agora cascade (seat, merge queue, scheduler) is a separate brief and does not start until items 1 to 5 here are on `main`.

- If you are an Opus or Fable chat: plan and review, Sonnet sub-agents build; ask Westley about his Claude usage before a batch of more than two doers. If you are a Sonnet chat: do the work yourself, spawn no sub-agents.
- This is executor work under the standing rules of `continuation-2026-09-18-harness-fix-handoff` (memory) and CLAUDE.md: tests first in fenced paths, no hand-written card implementations, protected-equation changes only under the change protocol with the reason stated, commit and push per item, never stage files you did not change, `git add` by path. Bible and northstar docs: rewrite, never append. Each item ends with an `R-` row in DECISIONS.md.
- The dispatcher: `systemctl --user stop agora-dispatcher.service` before item 1 (the chain head is unsatisfiable, so nothing is lost) and leave it stopped; the cascade brief restarts it. Do not edit `~/Projects/agora` except the card files named in items 1 and 2 (they are data).
- Python: `~/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider`. E-02 baseline 52 passed / 4 skipped on `tests/csim/test_E02_S0*.py tests/csim/test_E02_gate_drift_trajectory.py tests/csim/test_E02_S160_drift_gate.py` must hold after every item.

## 1. S-039 collisions: a wiring card and a re-cut of 205a/205b (audit: B F-1-1, blocker)

**The defect.** `csrc/collision.c:39` `om_tick_collisions(const om_world *w, om_collision *out, uint32_t max)` is a read-back with a signature fence; card `205a` (`~/Projects/agora/queue/205a-e05-collision-lottery.md`) tells the worker to group intents, run the lottery and write `w->collisions`, which that function cannot do; no collision step exists in `om_world_step` (`csrc/sim.c:110-130` runs 3a, 3b, 3c, 3d, 3e, 3f only); `resolve.c` sets `r->collision = 0` unconditionally. `card_lint` says OK. 205a escalated on 2026-09-20 after ten runs. 205b has the same symbol.

**The design (decided by the design lane; not yours to change, ask if it cannot work):** collisions are their own tick step, `om_step_collisions(om_world *w)` in `collision.c`, called from `om_world_step` between 3e and 3f under `OM_FEAT_FACTIONS`. It groups this tick's pending intents by target (`w->decisions[]`, `om_internal.h:66-67`), resolves every target with two or more intents per ALG-23 and ALG-24 (`docs/bible/algorithms.md`, S-039 R-039-01..06 in `docs/bible/epics/E-05-faction-agents-and-conflict.md:134-146`), writes `w->collisions[]` and `w->collisions_n` (`om_internal.h:72-73`), and removes the colliding intents from `w->decisions[]` (compacting) so 3f never sees them. `om_tick_collisions` stays a read-back of this tick's records. Owned-target collisions (R-039-05) are the same step; the damage math reuses the resolve helpers through the header.

**Do, tests first.**
- Add `om_step_collisions` to `csrc/ouroboros_sim.h` beside the other step hooks and a STUB body in `collision.c`; document the step in the header's tick-order comment block and in `docs/architecture.md` if it lists the tick order.
- Wiring card `205w-e05-collision-step-wiring` (`snippet_file: csrc/sim.c`, `snippet_symbol: om_world_step`, one-line insert): acceptance is a fenced tick-order test (`tests/csim/test_E05_S039_wiring.py`): with FACTIONS on and two factions targeting one empty region, after one `om_world_step` the region has exactly one owner, `om_tick_decisions` reports no pending intent for that target, `om_tick_collisions` reports one record, and 3f resolved nothing for it; plus a control `OM_BUG_COLLISION_AFTER_RESOLVE` (add the id, 112, with its C branch in `sim.c` written with the control, never by the card) where the step runs after 3f and the test's control trips. Run `control_liveness.py` on it: PENDING until 205a lands, then LIVE.
- Re-cut: `205a` becomes `om_step_collisions` (grouping, factors, lottery, retention, loser tension, unowned colonize dispatch: R-039-01..04, 06) with its existing tests; `205b` becomes the owned-target branch inside the same function (R-039-05) as a second card on the same symbol only if `card_lint` accepts a function-level split; otherwise fold R-039-05 into 205a and retire 205b (`.retired`), and say which. `om_tick_collisions` (read-back) joins 205a's symbols. Re-lint, re-slice (`card_slice.py --write`), read-only brief check against ALG-23/24 numbers; briefs carry no worked example numbers beyond the rules' own.
- `card_lint.py` gains `FAIL CONST_ONLY`: a card whose every `snippet_symbol` takes `const om_world *` while its acceptance tests call `om_world_step` and assert on world state afterwards. Positive control: the old 205a card must fail; negative: 204a3 must pass.

## 2. E-04 re-cut (PX-16; audit item 17)

`scripts/specfactory/chain_sim.py` found: 208a2 reads a stub owned by 208a1 (`om_events_load_launch`), 208b1 reads 208a1, 209c reads 208a1 and 208a2, in reverse of `RELEASE_CHAIN` order; and two symbols with two owning cards (`om_step_resolve`: 204a3 and 204b2; `om_tick_collisions`: 205a and 205b, resolved by item 1). Also decision A5: E-04's events step is not wired into `om_world_step`.
- Wiring card `208w-e04-events-step-wiring` in the same shape as 205w (the events hook at its ALG stage, tick-order test, a control with its own C branch).
- One owner per symbol: split or merge 204a3/204b2 so `om_step_resolve` has one card (the other card's rules move to a function the header already declares, or a new `static`-free helper the header gains); record which.
- Reorder and re-cut 208a1/208a2/208b1/209c so every card's closure over stubs points only at cards released before it. Run `chain_sim.py`'s DAG and `card_lint.py` on the whole E-04 set; both must be clean; paste the DAG summary into the R-row.

## 3. `om_pow` and a libm lint (audit item 1, blocker for the determinism contract)

`csrc/sim.c:206` calls libm `pow(1.0 - r->tension / 100.0, 0.3)`; `om_sin` at `sim.c:41` exists because platform libm differs; `pow` was missed. This is a protected-equation file (E-02 drift); the change protocol applies, the reason is the determinism contract in CLAUDE.md, and the equation's value does not change beyond rounding.
- Tests first: `tests/csim/test_E02_S160_om_pow.py` pins `om_pow(x, 0.3)` for a table of 64 inputs in [0, 1] to hex-exact doubles computed once on this machine, plus a repeat-seed determinism check; and a control that swaps `om_pow` for libm `pow` (`OM_BUG_LIBM_POW`, id 7, C branch written with the control) and asserts the table test trips on at least one input. If no input differs on this glibc, say so (the control is then PENDING until the Windows recipe exists) and keep the table.
- Implement `om_pow(double base, double exp)` beside `om_sin` with the same deterministic-polynomial approach (`om_log` and `om_exp` as fixed-coefficient polynomials with range reduction, no libm calls). Replace the call at `sim.c:206`.
- Run the E-02 baseline and `tests/csim/test_E02_gate_drift_trajectory.py`; if any exact-number assertion moves by more than its tolerance, stop and report the delta rather than widening the tolerance (invariant rule).
- `scripts/specfactory/libm_lint.py`: FAIL on any call to `pow exp log log2 log10 sin cos tan asin acos atan atan2 sinh cosh tanh exp2 cbrt` in `csrc/*.c`; allowed: `sqrt fabs floor ceil round trunc fmin fmax fmod`. Positive control: a fixture file with `pow(`; negative: `csrc/` after the change. Add it to the pre-queue checks list in `docs/northstar/spec_factory.md`.

## 4. `card_lint`: the fuel checks (audit item 2)

- `FAIL MISSING_SNIPPET_FILE` when `snippet_file` does not exist in the project; `FAIL ABI_GAP` already exists for undeclared symbols (confirm it is FAIL, not WARN). Run the lint over every `~/Projects/agora/queue/parked/*.hold`; write the counts per epic and per missing file into the R-row (expected: 142 of 169 cards, 12 modules; the exact list is in the audit README).
- A report mode `card_lint.py --fuel <queue>` printing: buildable now, blocked by missing file, blocked by ABI gap, blocked by open `Q-`, so the runway line the cascade adds has a source.

## 5. JSON DAG emitter for Agora (audit item 17)

`scripts/specfactory/chain_graph.py --queue <agora queue dir> --project . --out graph.json`: uses `chain_sim.build_dag` and `tick_closure` to emit `{"generated_at", "project", "nodes": [{"card", "kind", "file", "symbols", "epic", "story"}], "edges": [{"from", "to", "symbol"}], "errors": [{"kind": "cycle"|"double_owner"|"missing_file"|"abi_gap", "cards": [...], "symbol"}]}`. Orchestrators come from an argument (`--orchestrators om_world_step`, default from a small `specfactory.toml` in the project root so a second project can name none). Exit 1 when `errors` is non-empty. Tests with the synthetic fixtures `chain_sim` already has; a run over the real queue after items 1 and 2 must exit 0 and is committed as `docs/northstar/proving_ground/evidence/chain_graph/graph.json`. This file is the contract Agora's scheduler will read; do not change its shape after commit without a DECISIONS row.

## 6. Stale docs (audit item 23)

- CLAUDE.md "Tests are the spec": rewrite the fence sentence to what the design says: the worker never edits tests; the escalator may fix a test only when a finding is classed `test-defect`, under the test-fix gate, with a ledger row; Westley owns thresholds.
- DECISIONS.md R10.3: delete the sentence that says the escalator redesigns R7l's fixture; point at PX-18's split.
- `docs/northstar/research/factory/A9-throughput-timeline.md`: strike the "cap does not stop the loop, harness bug" claim; 204b1's cycles were re-queues (R7j, R7k).
- `agora/projects/ouroboros/README.md` and `qa.toml`: the pipe claim (Q9d-2) and the missing `scenes/harness/e02_harness.tscn` are stated as PENDING with the reason.
- `algorithms.md:11` and the header's "all features on" wording: leave for the D1 PR (its own brief), note it here as not done.

## Not in this brief

D1 (explicit feature set; own PR after the cascade), any `~/Projects/agora/scripts/` edit, the Windows build recipe (E1 says weekly gate once a recipe passes by hand; that recipe is a later brief), sanitizer and compiler gates, the 92 controls and 12 skeleton modules (Westley, E3, with a skeleton-generator run by the design lane).

## Verification and report

- `pytest tests/specfactory/` and `tests/qa/t1/` green; E-02 baseline 52 / 4 after every item; `card_lint.py` clean on 205w, 205a, 208w and the E-04 set; `chain_graph.py` exit 0 on the real queue; `libm_lint.py` clean on `csrc/`.
- R-rows in DECISIONS.md, one per item, with the numbers (fuel counts, DAG edge counts, `om_pow` table deltas).
- Finishing report for Westley: per item done or blocked, every place the design could not be followed as written and why, the fuel table from item 4, and nothing else. Dispatcher left stopped; say so in the report.
