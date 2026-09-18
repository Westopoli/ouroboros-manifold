# Decisions on the harness defect investigation (Westley, 2026-09-17)

These answer the decision list that followed `README.md` in this directory. `agora-dispatcher.service` stays stopped until Westley says otherwise.

**Execution status (2026-09-18, 00:56 EDT):** both cascades are merged and verified; the queue is running again.

- Cascade 1 (ouroboros `main`, `5b0eaaa`..`e027eb9`): drift gated on `OM_FEAT_DRIFT`, drift moved after the faction/friction/admin block, DRIFT on by default in `om_world_new`, story S-160 with tests and a positive control, `scripts/specfactory/green_check.py`. Verified: S-160 7/7, E-02 baseline unchanged (same four pre-existing failures), DRIFT off leaves fields byte-identical. `csrc/faction.c`'s budget body landed as `d641ea2`; card 202b2 retired (its acceptance test also asserts on `om_step_decisions`, so it could never pass alone).
- Cascade 2 (agora `wn/qa-director`, `79f1ffd`..`12ac7f2`, run by a Gemini session): `chat_full` with `done_reason`/thinking, `shift`/`truncate` false (verified live on Ollama 0.32.14: HTTP 400 instead of silent truncation), function-level C splice, `## Header slice` card section, verbatim card briefs, `truncated`/`dlopen` reasons, `thinking-N.md`. Review found two defects, fixed in `1448de9`: the C signature check rejected whitespace variants, and `static` helpers or `#include` lines the model added were silently dropped. Replay of the 131 archived 202b2 replies: 47 now merge and compile, 0 compile errors.
- Also landed: tick step 3a budget snapshot (`54a4ec3`), which the bible lists and `sim.c` lacked; reference bodies for 203a1..203b2 under `tests/csim/references/`, all green-checked; the four cards got header slices, corrected briefs (203a2's ALG-11 table was wrong for five archetypes) and real `snippet_symbol` lists (`5013cfc`).
- First run on the fixed harness, card 203a1: qwen3-coder attempt 1, 2/2 tests, 54 s, DONE, auto-merged as `c4596ed`. The same card class took 570-980 s per attempt and never passed before.
- `agora-dispatcher.service` restarted 00:55; the release chain runs 203a2, 203b1, 203b2 tonight and stops at 204a1 (held as `.hold.unprepared` until it has a slice, a reference and a checked brief).

Flagged for Westley, not acted on: 203b1 (170 lines) and 203b2 (125 lines) exceed the 30B sizing contract; `csrc/faction.c`'s RNG step does not follow the header's PCG32 contract; `csrc/resolve.c` damage-history stubs block R-034-07; `om_step_decisions` is an `om_internal.h` hook with no public prototype, so it reaches the worker only through the extra-context file.

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
3. **[DONE]** C1, C2, C4, C5, C7 (agora `12ac7f2` + `1448de9`).
4. **[IN PROGRESS]** B3 sweep runs card by card through the green check as cards are prepared; C6 data accrues from tonight's ladder runs.
5. **[NOT STARTED]** Then the high-level harness configuration comparison that prompted the investigation.
