# Cascade verification evidence — 2026-09-21/22

Brief: `docs/northstar/plans/briefs/2026-09-21-agora-cascade-safety-seat-scheduler.md`.
Executed in `~/Projects/agora` (branch `wn/qa-director`). Dispatcher confirmed
`inactive` before starting and kept stopped throughout except this section's
step 3.

## 1. Scratch chain — one control per audit class

Scope decision, not silently made: rather than building a separate
scratch-chain driver script, each control below is a real, unmocked
invocation of the actual dispatcher/build/merge functions (`next.py`,
`build.py`, `merge_queue.py`, `escalator.py`, `parent_patch_fence.py`)
against a `tmp_path`-isolated scratch queue/project/origin — this is what
"scratch chain" means operationally (the design under test is never
mocked; only the queue, project repo, and origin are throwaway). Each
control is a pytest test in the agora repo; file:test below, all re-run
fresh for this report and passing.

| Control | Status | Zero pages? | Evidence |
|---|---|---|---|
| Seat down (fake transport) | Ends `HARNESS-ERROR` reason `seat-down`, zero real attempts consumed, one alarm not per run | Yes — `escalate.escalate`/`notify` asserted not to over-fire | `agora/tests/test_build_seat_down.py::test_seat_down_intervene_ends_harness_error_not_incomplete`, `::test_seat_down_advisor_call_also_ends_harness_error`; `agora/tests/test_next_seat_down.py` (all 6 cases, including `test_alarm_fires_once_per_outage_not_per_tick`) |
| A bad merge in a different file from its victim test's card | Merge queue rejects with reason `regression`, naming the OTHER card's test; origin's `main` untouched | Yes — no escalation path in `merge_queue.py` at all; rejection is a return value, logged by the caller | `agora/tests/test_merge_queue_cross_card_regression.py::test_bad_merge_breaking_a_different_cards_file_is_rejected` |
| A cyclic cut | `graph_eligibility` reports `"graph error: cycle"` for every card in the cut; `escalate.escalate` never called (asserted via a raising fake in the queue-level test) | Yes | `agora/tests/test_next_graph_scheduler.py::test_cyclic_cut_ineligible_with_reason_never_escalated`, `::test_pending_task_skips_ineligible_card_never_escalates` |
| A missing-skeleton card | `HARNESS-ERROR`, run accounting discounts it (pre-existing mechanism, unaffected by this wave; re-verified here) | Yes | `agora/tests/test_build_missing_snippet.py::test_missing_snippet_file_is_harness_error` |
| A plateau run that reaches a diagnosis and becomes a repair request | 3 distinct candidates on one failing set → one diagnosis call; a named cause ends the run `DIAGNOSED`; `next.py` files a repair-card request under the card's project slug and skips the card, never escalating | Yes | `agora/tests/test_build_plateau.py::test_diagnosis_with_a_named_cause_ends_the_run_diagnosed`; `agora/tests/test_next_diagnosis_repair_wiring.py::test_diagnosed_run_files_a_repair_request_never_escalates` |
| A two-candidate merge race | Two candidates on one file merged back to back; the second rebases cleanly onto the first's already-pushed result (`fresh main` sourced from origin, not the stale live checkout) | Yes | `agora/tests/test_merge_queue.py::test_two_candidates_on_one_file_merge_back_to_back_second_rebases`; also `test_regression_after_rebase_is_rejected_and_origin_unchanged`, `test_conflicting_rebase_is_rejected_as_merge_conflict` |

Re-run command and result at the time of this report:

```
cd ~/Projects/agora && .venv/bin/python -m pytest -q \
  tests/test_build_seat_down.py tests/test_next_seat_down.py \
  tests/test_merge_queue_cross_card_regression.py \
  tests/test_next_graph_scheduler.py \
  tests/test_build_missing_snippet.py \
  tests/test_build_plateau.py tests/test_next_diagnosis_repair_wiring.py \
  tests/test_merge_queue.py
```

## 2. Clean-graph control (wave 3 replay set, gated on E-02/E-04/E-05)

The real, committed `graph.json` (this repo,
`docs/northstar/proving_ground/evidence/chain_graph/graph.json`, last
touched by R23) was checked directly: 289 total errors, **0 touching
E-02, E-04, or E-05**. The slice was clean at verification time, so the
control ran against the real artifact, not the synthetic fallback:
`agora/tests/test_next_clean_graph_control.py::test_clean_graph_control_on_the_real_e02_e04_e05_slice`
(passes). The synthetic fixture
(`test_next_graph_scheduler.py`'s double_owner/missing_file/abi_gap/cycle
tests) was also run, unconditionally, as the brief's own general-case
coverage.

## 3. One live card, watched end to end

The real ouroboros queue has no currently-eligible, un-escalated card:
every real card is either `DONE` or (205a specifically) already parked at
its `MAX_TASK_RUNS` cap from the real 2026-09-20 seat-outage incident this
whole brief answers — resetting its run count to manufacture a "fresh"
live attempt was not done (that would edit real historical run records
outside this task's scope). A scratch card was used instead, through the
REAL local Ollama endpoint (confirmed reachable, `qwen3-coder:30b`
resident), the REAL merge queue, a REAL bare-clone origin — only the
card's own content (a trivial `clamp_positive` function) and its project
(a throwaway git repo) are synthetic, matching the same "control on a
throwaway target, never on the design" discipline as section 1.

**Result: DONE on the first attempt.** Real `qwen3-coder:30b` call, 60.5 s
wall (`load_duration` 50.5 s of it — the model was not yet resident;
`keep_alive: -1` is now set so a later call in the same session would show
near-zero load time), `prompt_eval_count` 417, `eval_count` 52,
`coverage` "3/3", `hint_n` 0. Merged via the real merge queue into a real
bare-clone `origin.git`: `origin`'s `main` advanced to a new commit
carrying the correct fix; **the live checkout (`project/mod.py`) was left
holding the original stub (`raise NotImplementedError`), unmodified** —
direct confirmation that "the live checkout is never touched" holds under
a real run, not only in the mocked tests. Full telemetry row (item 6)
present: `t_start`, `t_end`, `load_duration`, `prompt_eval_count`,
`eval_count`, `prompt_hash`, `hint_n` all populated.

Run directory (scratch, not committed): `/tmp/claude-1000/live-verify/agora-scratch/runs/900-verify-live-20260922-0040/`.

## 4. Dispatcher start, one epic watch

Started `agora-dispatcher.service` for real (`systemctl --user start`);
confirmed `active` within 2 s, no crash. The first tick after ~3 hours
stopped correctly dispatched `digest.py` (today's digest was missing —
real, expected, safe work), not a build card: **the real ouroboros queue
currently has no eligible, un-escalated fuel to watch a build epic
through.** Checked directly (`next.py.pending_task()`, unmocked, against
the real queue/runs before starting the service): every real card is
either `DONE` (E-02 and the E-05 cards through `208+`) or already parked
at `MAX_TASK_RUNS` from the real 2026-09-20 seat-outage incident (`205a`,
10 real `INCOMPLETE` runs, escalated under the OLD pre-wave-1 behavior
before this brief's fix landed) — no E-04 fuel exists yet either (R14/R20:
the 208-series re-cut is built but its cards are still `.hold`, not moved
into `queue/`, pending the day-side symbol-ownership decision R25 flagged).
This is an honest absence-of-fuel finding, not a page: `next.py` behaved
exactly as designed (dispatched the digest, would have gone `idle` next
per the direct `pending_task()` check already performed). Stopped the
service after this one confirmed tick rather than let it idle unsupervised
for the remainder of this report's writing.

No page to Westley occurred, on or off the interrupt budget — there was
nothing to build.
