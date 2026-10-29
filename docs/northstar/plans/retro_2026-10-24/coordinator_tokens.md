# Coordinator tokens, 2026-10-19 and 10-20 (audit of 2026-10-27)

Record for the rule change DEC-coordinator-wakeups-2026-10-27. Full numbers: `plans/2026-10-27-lab-only-programme-spec.md` section 8.

- The Dispatcher (513 turns, 185.5 M) and the Architect (507 turns, 169.7 M) spent 99% of their tokens re-reading their own context; new content entering each chat was about 0.4 M tokens over two days.
- Dispatcher: 51% of tokens were text-only turns after events (252 of 513); 26% spawns; 13% messages to the Architect. Architect: 49% were answers to the Dispatcher (87 messages in two days).
- A one-line screener would have saved 1% (strict) to 9% (upper bound). Context caps: 200k halves both chats, 150k cuts to 40%.
- Sub-agents on the two days: 227 agents, 710 M; "fix pass" re-runs 28% (201 M); the dearest single agent ran 118 calls (28 M).
- 15 pieces attached in the window: about 71 M per landed piece all in.

Rule changes landed with this file: `dispatcher.md` step 3 (one wakeup per event, status after each landing, Fable by one batched brief, call caps, one fix pass); brief templates under `method_rev3_2026-10-26/briefs/` (STOP at N calls). Metrics M27 to M29 are HARNESS-mm-12 (spec A10). Not taken: compaction at 150k.


Correction, 2026-10-29: the 252 text-only Dispatcher turns were the closing turns of 252 wakeups (one per episode), not avoidable status lines. The saving is in fewer wakeups and a smaller context per call (the 150k compaction counterfactual), not in dropping the closing line. `dispatcher.md` step 3 reworded; M27 redefined (spec A17).
