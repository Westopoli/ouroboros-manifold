# A9 — Where the 20+ hours went (Agora dispatcher, 2026-09-18 13:01 → 2026-09-19 23:20 local/EDT)

Sources: `agora/runs/cron.log` (line 110771 = 2026-09-18 13:01:04 through EOF), `agora/runs/metrics.jsonl`
(90 rows in window, 74 `kind:"build"` rows used for wall time), `journalctl --user -u agora-dispatcher.service`
(27 Started/Stopped events), `agora` git log (`queue:` commits), `queue/parked/*` mtimes, and the executor
transcript `02c3c4f9-...jsonl` (5690 lines; timestamps there are UTC = EDT+4h, verified against a matching
systemctl stop/start pair at 2026-09-19 08:06:30 EDT / 12:06:30 UTC).

The window Westley asked about (13:00 Sep 18 → ~09:00 Sep 19) is the first ~20 hours of a longer 34h19m
stretch that runs to "now" (23:20 EDT Sep 19); this memo covers the full 34h19m span so the "onward to now"
part isn't lost, and calls out the 09:00 boundary explicitly where it matters.

## Headline number

Of 34.32 hours elapsed:

| State | Hours | % |
|---|---|---|
| BUILDING (a worker/driver process actually running) | 11.21 h | 32.7% |
| IDLE (dispatcher running, `driver: idle`, nothing eligible) | 19.81 h | 57.7% |
| STOPPED (human ran `systemctl --user stop`) | 3.30 h | 9.6% |

Of the 11.21 h of BUILDING, only **18.5 minutes** produced a card that shipped (the final, successful attempt
on each of 9 DONE cards, 5 of them substantive: 204a1, 204a2, 204a3, 204b2, 204b3, plus 4 near-instant gate
checks). The other 10h54m of BUILDING was spent on attempts later discarded — most of it (338.8 min / 5.6h) on
a single card, `204b1-e05-conquest-garrison`, that never went DONE through Agora at all: it was hand-implemented
directly in `ouroboros-manifold` and the queue entry retired.

**IDLE, not BUILDING, is the dominant cost.** The dispatcher spent more clock time doing nothing (because the
one card at the head of the queue was stuck) than it spent building anything, successful or not.

## Stacked time budget

| Bucket | Hours | Detail |
|---|---|---|
| BUILDING — productive (ended DONE) | 0.31 h | 9 attempts, 18.5 min total |
| BUILDING — wasted (later discarded) | 10.90 h | 65 attempts, 654.1 min; 338.8 min of it is 204b1 alone |
| IDLE — blocked on 204b1 (retired, no successor released) | 4.35 h | 03:45–08:15 Sep 19 |
| IDLE — blocked on 204b3 UNSATISFIABLE (no auto-diagnosis) | 5.90 h | 08:20–14:14 Sep 19 |
| IDLE — blocked on 204b2 (needed 206b recut) | 3.92 h | 17:14–20:26 Sep 19 (plus a 42.9 min lead-in before the Jarvis/Agora GPU swap) |
| IDLE — smaller stretches (recuts landing, gate re-checks) | 5.64 h | several 20–95 min gaps around 18:13, 22:14 Sep 18 and 20:30 Sep 19 |
| STOPPED — Westley: "pause agora cards, wait for further instructions" | 1.85 h | 14:51–16:42 Sep 18, explicit business decision, not a defect |
| STOPPED — executor: diagnose/recut cycles (each <30 min) | 1.28 h | 11 short stop/start pairs while fixing 204a1/204a2/204a3 fixtures, a Jarvis/GPU swap, and one 204b1 hand-fix bracket (08:06–08:15 Sep 19) |
| STOPPED — instant restart (config reload) | ~0 h | 20:25:11 Sep 19, same-second stop+start |

Full per-state-change breakdown: `A9-timeline.csv` (157 rows, one per contiguous BUILDING/IDLE/STOPPED segment).

## Per-DONE-card wall time (release → DONE)

| Card | Released | DONE | Elapsed | Attempts | Building min | Recut or upstream fix needed? |
|---|---|---|---|---|---|---|
| 204a3-e05-core-attack | Sep18 13:01:04 | Sep18 19:41:56 | 6h41m | 10 (7 wasted) | 107.8 | Yes — dropped an unsatisfiable test control (`agent_reads_live`) at 19:14 |
| 204a1-e05-telegraph-maturation | Sep18 13:33:43 | Sep18 16:59:18 | 3h26m | 2 (1 wasted) | 10.2 | Yes — circular-dependency fix + RELEASE_CHAIN reorder, waited on 204a2's escalation to clear |
| 204a2-e05-reactive-reinforcement | Sep18 13:45:10 | Sep18 16:52:25 | 3h07m | 4 (3 wasted) | 38.1 | Yes — a real test-fixture bug (escalated, then fixed, R7f) |
| 204b3-e05-damage-history | Sep19 08:14:49 | Sep19 14:41:41 | 6h27m | 2 (1 wasted) | 6.5 | Yes — needed Westley's parallel sub-agent "audit for unsatisfaction" effort before the retry passed |
| 204b2-e05-unrest-colonize | Sep19 14:43:44 | Sep19 20:30:18 | 5h47m | 11 (10 wasted) | 99.5 | Yes — recut with 206b (`R_040_04` needed 206b's own function built first) |
| 204b1-e05-conquest-garrison | Sep18 19:45:00 | **never** (retired Sep19 08:14:44) | 12h30m to resolution | 30, all wasted | 338.8 | Hand-implemented directly in `ouroboros-manifold` main; Agora never produced a passing candidate |
| 207-e05-step-order-fault | Sep19 21:51:33 | **still running** as of 23:12 | 1h21m and counting | 10, all INCOMPLETE so far | 71.7 | Not yet — same compile error (`OM_BUG_TELEGRAPH_AFTER_REINFORCE` undeclared) on every attempt |

Average BUILDING time on the 5 substantive cards that did succeed: **52.4 min/card** — close to Westley's own
20–30-min/60-min-for-hard-ones expectation. The blowup to a multi-hour wall time per card is not the local
models being slow; it's everything *around* the build (IDLE + human-required STOPPED).

## Longest idle stretches

| Start | End | Duration | Cause | What would have unblocked it without a human |
|---|---|---|---|---|
| Sep19 03:45:19 | Sep19 08:06:30 | 4h21m | `204b1` had stopped attempting (last of 30 runs) but no successor was released; the queue head stayed blocked until Westley wrote "complete 204b1 yourself inline, and then resume the queue" at 08:05:32 EDT | A plateau/stagnation detector that fires an escalation with full context after N non-improving attempts, instead of silently going quiet, would have surfaced this at ~22:30 Sep18 while Westley was still awake, not at 08:00 the next morning |
| Sep19 08:20:09 | Sep19 14:14:09 | 5h54m | `204b3` came back UNSATISFIABLE on its first attempt after release; nothing else was eligible, so the dispatcher idled until Westley explicitly asked for parallel sub-agents to "audit the card for unsatisfaction" (13:25:41 EDT) and that audit landed a fix | RELEASE_CHAIN releasing the *next independent* card instead of blocking the whole chain on one UNSATISFIABLE result; separately, an automated root-cause pass on UNSATISFIABLE (the same audit Westley had to ask for by hand) |
| Sep19 17:13:59 | Sep19 20:26:12 | 3h12m | `204b2` had exhausted 10 INCOMPLETE attempts by 16:28 and sat blocked until the human recut it together with `206b` (`206b` needed its own function built first — a missed dependency) | Dependency validation at queue-cut time (an epic's cards checked for build-order gaps before being queued) so the missing `206b` prerequisite was caught before release, not after 10 failed attempts |
| Sep18 22:13:58 | Sep18 23:48:27 | 1h35m | Early overnight stretch of `204b1` — dispatcher running, driver idle, no successor because 204b1 was still "in progress" per the log but not producing ticks worth logging as separate build attempts in this stretch | Same plateau detector as above |

## Counterfactuals

Assumptions stated where the data can't fully settle them.

**(a) Chain never idles on a blocked head — releases the next independent card instead.**
This removes essentially all of the 19.81 h of IDLE (it assumes the queue had independent work available to
pull forward instead, which — given `queue/` held 20+ un-started cards spanning multiple epics at any point in
this window — is a reasonable but not certain assumption). Window collapses to roughly BUILDING (11.21h) +
STOPPED (3.30h) ≈ **14.5 h** to reach the same 9 DONE cards plus the 30 wasted 204b1 attempts and 10 (and
counting) 207 attempts. That's still ~1h37m/card average across 9 cards, not 20–30 min, because it does nothing
about wasted rebuild attempts.

**(b) A run stops at plateau diagnosis instead of the 10-run cap.**
204b1 (30 attempts, best_failed never converging below 1–5) and 207 (10 attempts, identical `baseline_failed=1`
compile error every single time) are textbook plateaus visible after 2–3 non-improving attempts, not 10. Cutting
each stuck card's attempts to ~3 (≈30 min for 204b1's cadence, ≈20 min for 207's) instead of running to (and, for
204b1, past) the cap saves an estimated **~330 min (5.5h)** off 204b1 and **~50 min** off 207 so far, and — more
importantly — converts a silent multi-hour stall into a same-session escalation. Combined with (a), most of the
window compresses toward **8–10 h** for the same output.

**(c) No human stop needed at all.**
Saves the full 3.30h of STOPPED, but 1.85h of that was Westley's own deliberate "pause and wait for instructions"
(a business decision, not a defect) and the remainder was the executor's required diagnose-and-recut cycles,
which CLAUDE.md's own "sub-agents implement, never design" rule makes a human decision point by design — this
counterfactual mostly isn't available without also changing that rule.

Combining (a)+(b): plausible best case for this window is roughly **9–10 hours of wall time for the 5 substantive
DONE cards**, i.e. ~110 min/card average — still 2-4x Westley's 20–60 min expectation, but the gap would then be
attributable to genuine build/QA cost per card, not to the queue sitting idle or grinding a dead card.

## Five one-line design-property gaps

1. **No fallback past a blocked queue head** — RELEASE_CHAIN blocks the entire queue on one card; `driver: idle`
   fired every minute for 4h21m (2026-09-19 03:45–08:15) and again for 5h54m (2026-09-19 08:20–14:14) and again
   for 3h12m (2026-09-19 17:14–20:26) with independent work sitting unreleased behind the stuck head.
2. **No stagnation/plateau detector inside a build's own retry loop** — `207-e05-step-order-fault` reran the
   identical failing approach 10 times with an unchanged `baseline_failed=1` compile error (2026-09-19 21:51–23:12,
   ongoing), and `204b1-e05-conquest-garrison` ran 30 non-converging attempts (2026-09-18 19:45–2026-09-19 03:45).
3. **The 10-attempt cap doesn't stop the loop, only announces it** — three "204b1 hit the 10-attempt cap (10 runs)"
   monitor events fired at 2026-09-19 01:43:53–01:45:33 EDT, then 11 more attempts ran anyway through 03:45:19.
4. **No unattended overnight escalation path** — between the last 204b1 attempt and Westley's "complete 204b1
   yourself inline" instruction (2026-09-19 03:57–08:05, ~4h08m), the executor transcript is silent: a stuck head
   card can only be resolved by a human waking up and typing, not by a queued escalation ticket.
5. **UNSATISFIABLE has no automated root-cause path** — `204b3-e05-damage-history` sat UNSATISFIABLE from
   2026-09-19 08:20 until Westley personally asked for parallel audit sub-agents at 13:25:41 EDT; the fix only
   landed once a human designed that investigation, matching CLAUDE.md's "ambiguity is flagged, never guessed"
   rule for design decisions but leaving the queue with no automatic diagnose-and-retry step of its own.
