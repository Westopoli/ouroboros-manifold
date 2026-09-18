# Decisions on the harness defect investigation (Westley, 2026-09-17)

These answer the decision list that followed `README.md` in this directory. `agora-dispatcher.service` stays stopped until Westley says otherwise.

**Execution status (2026-09-18, 00:56 EDT):** both cascades are merged and verified; the queue is running again.

- Cascade 1 (ouroboros `main`, `5b0eaaa`..`e027eb9`): drift gated on `OM_FEAT_DRIFT`, drift moved after the faction/friction/admin block, DRIFT on by default in `om_world_new`, story S-160 with tests and a positive control, `scripts/specfactory/green_check.py`. Verified: S-160 7/7, E-02 baseline unchanged (same four pre-existing failures), DRIFT off leaves fields byte-identical. `csrc/faction.c`'s budget body landed as `d641ea2`; card 202b2 retired (its acceptance test also asserts on `om_step_decisions`, so it could never pass alone).
- Cascade 2 (agora `wn/qa-director`, `79f1ffd`..`12ac7f2`, run by a Gemini session): `chat_full` with `done_reason`/thinking, `shift`/`truncate` false (verified live on Ollama 0.32.14: HTTP 400 instead of silent truncation), function-level C splice, `## Header slice` card section, verbatim card briefs, `truncated`/`dlopen` reasons, `thinking-N.md`. Review found two defects, fixed in `1448de9`: the C signature check rejected whitespace variants, and `static` helpers or `#include` lines the model added were silently dropped. Replay of the 131 archived 202b2 replies: 47 now merge and compile, 0 compile errors.
- Also landed: tick step 3a budget snapshot (`54a4ec3`), which the bible lists and `sim.c` lacked; reference bodies for 203a1..203b2 under `tests/csim/references/`, all green-checked; the four cards got header slices, corrected briefs (203a2's ALG-11 table was wrong for five archetypes) and real `snippet_symbol` lists (`5013cfc`).
- First run on the fixed harness, card 203a1: qwen3-coder attempt 1, 2/2 tests, 54 s, DONE, auto-merged as `c4596ed`. The same card class took 570-980 s per attempt and never passed before.
- `agora-dispatcher.service` restarted 00:55; the release chain runs 203a2, 203b1, 203b2 tonight and stops at 204a1 (held as `.hold.unprepared` until it has a slice, a reference and a checked brief).

**Overnight result (2026-09-18, 01:00-01:50 EDT):** 203a1 DONE (attempt 1, 54 s), 203a2 DONE (16 attempts, 2 interventions), 203b1 DONE (12 attempts, landed by gpt-oss:20b medium, the first gpt-oss pass in C mode), 203b2 SPEC-INVALID because 203b1's candidate already made its two tests pass (card parked as `.satisfied-by-203b1`). The chain then halted at 204a1 as intended.

**Regression found, needs a decision (the unanswered half of C7):** `test_R_034_06_it_excluded`, 203a1's own acceptance test, passes at `c4596ed` and `4cef8e5` and fails at `718e0fd`: 203b1's accepted candidate rewrote `om_faction_candidates` and dropped the stance exclusion, and the harness only runs the current card's `checks[0]`, so nothing caught it. `test_R_034_03` regressed the same way. S-034 on `main` now reads 4 passed / 3 failed. Options: (a) `build.py` runs the acceptance commands of every DONE predecessor in `RELEASE_CHAIN` that shares the card's `snippet_file` before finalize, rejecting with a new `regression` reason; (b) each card carries a `regression:` list the author fills; (c) a full `tests/csim` run of previously-green tests after every DONE, reverting the auto-merge on any loss. The bible's "tests are the spec" rule points at (a) or (c). Until decided, `main` carries the regression and 204a1 stays held.

Flagged for Westley, not acted on: 203b1 (170 lines) and 203b2 (125 lines) exceed the 30B sizing contract; `csrc/faction.c`'s RNG step does not follow the header's PCG32 contract; `csrc/resolve.c` damage-history stubs block R-034-07; `om_step_decisions` is an `om_internal.h` hook with no public prototype, so it reaches the worker only through the extra-context file.

## Second round (Westley, 2026-09-18, 02:00-03:00 EDT)

| ID | Question | Decision | Status |
|---|---|---|---|
| Q1 | Regression gate: a later card broke an earlier card's test and merged. | (a) `build.py` re-runs the acceptance of every DONE predecessor sharing the card's `snippet_file` before finalize; failure = `regression` reject. | Done, agora `finalize_pass`, six tests. |
| Q2 | Repair the S-034 regression on `main`. | (a) Repair card 203c through the harness, acceptance on rules 01, 02, 05, 06. | Card authored, chain updated, running. |
| Q3 | Tests no card owned (R-034-03, 04, 07). | (a) Card 203d for 03 and 04; 07 waits for the damage-history card. | Card authored, chain updated. |
| Q4 | Prepare the remaining E-05 cards? | Westley challenged the cost: having Sonnet write a full reference per card is Claude doing Agora's job, against Principles 1 and 2 of `PLAN.md`. Revised procedure proposed: a mechanical dependency lint (test's symbols versus `allowed_files` and stub markers), a mechanical header-slice generator, and a Sonnet read-only brief check; references and the green check only as diagnosis after a card fails three runs. | Approved 2026-09-18 ("I definitely don't want Sonnet doing the whole implementation"). Building: `scripts/specfactory/card_lint.py`, `card_slice.py`; Sonnet reads briefs only. |
| Q5 | Sizing contract after 203b1 (170 lines) and 203b2 (125) passed over the cap. | (a) Keep the cap, split future cards, enforce it loudly. Draft: harness refuses oversize cards as SPEC-INVALID before any model call, SPEC-INVALID becomes terminal for a card in `next.py`, a suite test scans every queued card, the factory refuses to emit oversize cards, the green check reports oversize references. | Approved; building in agora (SPEC-INVALID before any model call, terminal SPEC-INVALID, queue-wide sizing test). |
| Q6 | gpt-oss rungs. | (c) Dropped. Ladder is qwen3-coder:30b, three attempts. | Done. |

| Q7 | Do isolation-green cards compose, and do speed/scale hold at story and epic level? | Yes, enforced: per story, after its last micro-card, one gate card runs the story's whole test file plus the epic's scale/speed gate test together; per epic, one gate card runs every story file. Gate cards run no model: green = DONE, red = escalation. (`PLAN.md` Principle 5, which no card had exercised.) | Harness `kind: gate` being built; gate cards for S-032..S-035 next. |
| Q8 | Auditor experiment ratio. | Cards run so far: 10 on audited files, 2 on the fixtures file, 0 on unaudited story files. No control data yet. Leave B2 (no new audits); 204b/205 (S-037, S-038, unaudited) supply the control arm; read the comparison after 205. | Waiting on the chain. |

## Third round (Claude, 2026-09-18 afternoon): E-05 re-cut

The executor chat prepared 204-207 with `card_lint.py`; six cards failed SPANS_ANOTHER_CARD. A dependency map (`evidence/recut/`, tables 01-05) shows why: the micro-cards were cut by rule pair, so their tests reach stubs in other files, and `203b2` was parked as satisfied while `om_pending_telegraphs` (its real job) stayed a stub. Decisions, mine unless marked:

| ID | Decision |
|---|---|
| R1 | Re-cut the E-05 remainder by file and algorithm family in the order of `evidence/recut/04_proposed_recut.md`: 203e agent.c telegraph declare/draw/queue (replaces 203b2, retired); 204a3 resolve.c core attack; 204a2 reactive reinforce; 204a1 telegraph maturation; 204b1 conquest; 204b3 damage history (`om_region_add_damage`, `om_region_damage_history`, acceptance R-034-07; the map's "dead ABI" claim is wrong, `test_R_034_07` calls `add_damage`); 204b2 conquest-unrest queue and solo colonize; 207 sim.c step-order fault only; 205a collision lottery and unowned colonize; 205b owned-target combat; 206a border friction; 206b admin revolts. Story gates: S-037 after 204a3, S-036 after 204a1, S-034 after 204b3, S-038 after 204b2, S-039 after 205b, S-041 after 206a, S-040 after 206b. |
| R2 | Storage prerequisite: `om_internal.h` gains event queue, friction log, admin-roll log and per-region damage history (parent patch, no logic), because a one-file card cannot add struct fields. |
| R3 | Assertion cap (5-15) is advisory for E-05: its test functions bundle several scenarios per rule and predate the contract; splitting fenced tests is Stage 5 work, not a card re-cut. Symbol and line caps stay hard. |
| R4 | `card_lint.py` blind spots fixed: conftest resolution for `controls/`, test-local helpers, dynamic `getattr` through helpers. Known remaining blind spot: it sees STUB markers, not functional incompleteness (card 207 read clean while three E-05 controls fail). |
| R5 | Flags for Westley, not acted on: no test exercises the solo (non-collision) colonize path of `om_tick_colonizations`; R-040-05 stays xfail until E-07. |

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
4. **[DONE]** C6 decided (gpt-oss dropped). B3 sweep folds into the Q4 dependency lint once approved.
5. **[NOT STARTED]** Then the high-level harness configuration comparison that prompted the investigation.
