# PX-03 — `harness-error` as a first-class session outcome (proving the factory)

Run 2026-09-19 (agora `3395489`). Claim (A4 §3, §5): a QA session whose actions never mutate observable state must end `harness-error`, never count toward campaign convergence, and never be re-triaged as a product finding.

Result: **pass**, with one finding that changes where the weight sits.

- Built: `scripts/qa_liveness.py` (state hash over the page's text, a precheck that performs one known-mutating action and compares hashes, a stall detector over N consecutive mutating actions), `FindingStatus.HARNESS_ERROR`, director verdict `harness-error` (short-circuits before any reviewer call, never files an assertion), `next.py` convergence ignores such sessions, ledger rows carry the status. Seven tests, RED first (`'MissionResult' object has no attribute 'harness_error'`), then green; full suite unchanged at the 13 pre-existing failures.
- Offline replay of the 2026-09-11/12 incident sessions: 7 of 15 director sessions and 7 of 8 coverage sessions carry the frozen-state signature and would have ended `harness-error`; 4 director sessions show the click counter genuinely advancing and stay real findings (a different, real bug: the layer key never reached `layer: 2`, the missing-verb defect PX-02 closed); the remainder were already `inconclusive`.
- **What actually catches them:** the precheck, on action one. None of the incident sessions reached four tracked state reads before a checkpoint ended them, so the mid-session detector alone would have caught nothing. The detector is a safety net for long free-roam sessions; the precheck is the control that saves short missions.
- Gating: both are opt-in through `[desktop].liveness` in the profile because most existing test fixtures use a static fake page that never changes state.

Design consequences (recorded in DECISIONS.md):
1. The input-liveness precheck is mandatory for every desktop-backend session in production: a desktop profile without `[desktop].liveness` fails profile lint. The stall detector stays as the long-session net.
2. Session logs record the state hash per action from now on, so future replays can test the detector, not only the precheck.
3. `qa_control.py`'s desktop positive control was not run live in this experiment; running it against the toy scene with the precheck wired is the remaining step before the mechanism is trusted on the game.
