# PX-08 — Tick-stage closure and plateau early-stop (proving the factory)

Run 2026-09-19 on real Round 5 data (`research/factory/A8-runs.csv`, 74 runs with candidates) and the three real `RELEASE_CHAIN` orderings from agora's history. Prototype module `scripts/specfactory/tick_closure.py` (45 specfactory tests green, 8 new). The analysis scripts stayed in the session scratchpad; the numbers are below.

## H1 — a card's closure must include the hooks `om_world_step` runs

Claim: with orchestrator hooks in the closure, lint rejects both circular cuts of 204a1/204a3 and accepts the final order.

Result: **pass**, with one useful residual.

| Chain order | Verdict |
|---|---|
| R1 (204a3 before 204a1) | 204a3 rejected: needs `om_step_telegraphs`, owned by 204a1, not done |
| R7b interim (204a1 before 204a2) | 204a1 rejected: needs `om_step_reinforce`, owned by 204a2; also flags `om_step_resolve` (204a3) because both write the shared `attacks`/`attacks_n` buffer |
| Final (204a2 → 204a1 → 204a3) | 204a2 and 204a3 accepted; 204a1 keeps the shared-buffer flag |
| 203e, 203a1, 203c | accepted (they read through `om_faction_candidates`, not a tick reader) |

The residual flag is the hazard 204a3's brief had to spell out by hand ("must not reset `attacks_n`"); the checker cannot know a stub is harmless. Design consequence: the residual is a WARN naming the shared buffer, not a block, and the brief generator quotes it.

Mechanism kept discriminative by narrowing to hooks whose array-plus-counter buffer overlaps a buffer the card's acceptance test reads (`om_tick_*`, `om_pending_*`); expanding on every shared scalar would flag every hook against every card.

## H2 — stopping after K identical failing sets ends wasted cycles with no false stops

Claim as stated: **fails**. Every K has false stops.

| K | fired | false stops (later DONE) | candidates saved | recall on the 15 upstream-blocked runs |
|---|---|---|---|---|
| 2 | 55 | 4 | 124 | 14/15 |
| 3 | 29 | 3 | 57 | 9/15 |
| 4 | 19 | 3 | 32 | 6/15 |

Requiring distinct `diff_sha` changes almost nothing. The false stops are real cards that plateaued for 2-4 candidates and then broke through (203a2, 203b1, 208+, and 204a2 at K=2).

Design change (recorded in `DECISIONS.md` and PLAN.md): a plateau does not stop the run; it forces an escalator **diagnosis** call whose reply is either a named cause (upstream defect, unsatisfiable fixture, contradiction) that ends the run and routes the finding, or "continue" with a hint. K=3. This uses the signal A8 found already accurate (the advisor's abort text when it fires) and removes the false-stop cost.
