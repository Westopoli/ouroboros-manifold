# Decisions on the harness defect investigation (Westley, 2026-09-17)

These answer the decision list that followed `README.md` in this directory. `agora-dispatcher.service` stays stopped until Westley says otherwise.

**Execution status (2026-09-17, Cascade 1 of the harness-fix plan):** A1, A2, A3, and B1 are done and merged to `main` (`5b0eaaa`, `ff47fc9`, integration merges `6adf83b`/`18706ba`, records commit `df961d2`). The E-02 baseline (`tests/csim/test_E02_S0*.py` + `test_E02_gate_drift_trajectory.py`) is unchanged at 42 passed / 4 failed / 4 skipped, same four failing ids as before. `csrc/faction.c`'s budget body was hand-committed separately (`d641ea2`), ahead of the cascade, with the user's approval — its `om_faction_step_budget` assertions in `test_E05_S033_...::test_R_033_01_budget_66_8_40_8` now pass; that test's later, unrelated `om_step_decisions` assertion (a separate unimplemented `csrc/agent.c` stub, card 202a-series) stays red, out of this cascade's scope. Card 202b2's queue-side retirement and Cascade 2 (agora repo, C1/C2/C4/C5/C7) did not start this session — `~/Projects/agora` on `wn/qa-director` has ~690 lines of uncommitted/untracked state (including a deleted tracked card file), far more than the ~13 files Step 0.2 of the plan expected, and needs Westley's input before anything there is touched.

## Game side (ouroboros repo)

| ID | Question | Decision |
|---|---|---|
| A1 | Should switching `OM_FEAT_DRIFT` off actually skip the drift step, as a rule in E-02? | Yes. |
| A2 | Who builds the gate: a hand patch or an Agora card? | Both. The test and its positive control are written first, then the gate is hand-patched so the queue unblocks. |
| A3 | Tick order: `sim.c` runs drift before factions, `algorithms.md` and `tick.py` run it after. | Fix the C code to match the bible. |
| A4 | Should features default on or off in `om_world_new`? | Not decided as posed; the on-or-off framing is an oversimplification. The MVP has a carefully selected feature set, and that set is what the C library should have when the code writing is done. The defaults follow from that selection. Open: state the MVP feature set as the source of truth for the defaults and correct the header and `algorithms.md` wording to match. |
| A5 | Events, diplomacy, technology and lifecycle are not wired into `om_world_step`. | No decision needed; sequencing falls out of the roadmap. E-04 cards stay parked until their step is wired. |

## Test factory

| ID | Question | Decision |
|---|---|---|
| B1 | Add a satisfiability (green) check: a reference solution must pass the acceptance command before a card is queued. | Yes, add it. |
| B2 | The test-auditor experiment. | Tests stay unaudited. Revisit only if a consistent class of test defect shows up. |
| B3 | Sweep the existing tests for other impassable cases. | Yes, after A1 and A2 land, so the sweep measures what remains. |

## Harness (agora repo)

| ID | Question | Decision |
|---|---|---|
| C1 | Whole-file reply or function-level splice for C cards. | Function-level splice. Make the task as easy on the model as possible; adding structure on our side is little work. |
| C2 | How much of the header the worker reads, and who chooses it. | Only the relevant slice, chosen by the card author when the card is written, not by the harness. |
| C3 | Raise `num_ctx` above 16384. | Not now. Watch model performance closely after C1 and C2; raise it only if context is still a problem. |
| C4 | Turn off silent context shift so overflow fails loudly. | Yes. |
| C5 | Report truncation (`done_reason: length`) and deleted functions as their own failure types, and log thinking text. | Yes. |
| C6 | Keep, change or drop the gpt-oss rungs. | Undecided pending evidence. Re-benchmark after C1 to C4. |
| C7 | Use the card's own brief verbatim instead of a DeepSeek-regenerated brief each run. | Yes, verbatim. |

## Still open

- A4, as described above.
- The second half of C7 was not answered: whether the "earlier suites stay green" clause in card goals becomes a real harness check or is removed from the card text.
- Stage numbering. Westley's understanding is that Stage 4 is writing tests and Stage 5 is mapping cards, which was meant to be a `PLAN.md` edit made when the new card-organization strategy was defined. `CLAUDE.md` and the current northstar docs still describe Stage 4 as roadmap and sprints and Stage 5 as tests. The edit appears not to have fully landed. Worth a small investigation: what `PLAN.md`, `README.md`, `agile.md`, `spec_factory.md` and `PLAN_CARD_DECOMPOSITION.md` each say, and where they disagree. C2 above was phrased as "card author in Stage 4" under the old numbering; read it as "at the card-writing stage", whichever number that is.

## Agreed order of work

1. **[DONE]** A1 rule, then A2 test, control and hand patch; A3 alongside.
2. **[DONE]** B1 green check.
3. **[NOT STARTED]** C1, C2, C4, C5, C7 — agora repo, blocked on the uncommitted-state question above.
4. **[NOT STARTED]** B3 sweep, then the C6 re-benchmark.
5. **[NOT STARTED]** Then the high-level harness configuration comparison that prompted the investigation.
