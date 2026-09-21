# PX-16 — Graph-scheduler simulation (proving the factory)

Run 2026-09-21. Claim (`docs/northstar/PLAN.md`, "The Factory" > QA architecture > "Pipelining (the drive-thru rule)"): if the release chain were a dependency graph with escalate-and-continue instead of a serial list, most of the idle time measured on 2026-09-18/19 (`research/factory/A9-throughput-timeline.md`, 34h19m: idle 19.81h, building 11.21h, stopped 3.30h) disappears. Prototype module `scripts/specfactory/chain_sim.py`, tests `tests/specfactory/test_chain_sim.py` (16 new, specfactory suite 138 total, all green).

Result: **pass on the E-05 cards that were actually attempted in the window; not obviously true for the E-04 slice, which needs a recut before scheduling can help it.**

## Part 1 — the dependency graph

Reused, not re-derived: `card_lint.py`'s static symbol collector (`collect_acceptance_symbols`) and `tick_closure.py`'s tick-stage hook expansion (`expand_closure`, `relevant_hooks`, `hooks_in_order`), both from PX-08. `chain_sim.build_dag` adds one rule on top: card B depends on card A when a symbol B's acceptance closure reaches is A's own `snippet_symbol` claim, **and that symbol is presently a stub**. Gate cards (`kind: gate`) instead depend on every non-gate card in the slice sharing their story number (from the gate's own "story S-0NN gate" goal text, matched against the S-number encoded in each other card's `test_file`).

Stub-ness has to be read from the repo as it stood **before** these cards ran, not today's `HEAD` — most of this slice has since landed on `main`, and reading live `csrc/` would silently erase the very edges this experiment exists to find (a symbol a since-merged card now implements reads as "already real" and the dependency vanishes). `chain_sim.py` reads `csrc/*.c` via `git show` at `e024dde` (2026-09-18 13:00:01, one minute before the A9 window opens, the commit right after `208+e05-spawn-fault-branches` landed).

Slice: `203e-e05-telegraph-declare-draw-queue` through `210-e04-fault-injection` in agora's current `RELEASE_CHAIN` (27 cards: the rest of E-05, then E-04). **27 nodes, 56 real edges, vs. 26 a plain serial list implies** — more edges than a line, not fewer, because the edges are not a clean superset of the list order:

- `204a2 -> 204a1 -> {204a3, 204b2}` (204a2's `om_tick_reinforces`; 204a1's `om_tick_attacks`) — this is the real, already-known R7 recut (`om_tick_attacks`/`om_tick_reinforces` circularity), reproduced mechanically rather than asserted from memory.
- Two duplicate-ownership pairs, both same-file same-symbol extensions, not accidents: `om_step_resolve` claimed by both `204a3` and `204b2` (204b2 extends attack resolution onto conquest/colonize), and `om_tick_collisions` claimed by both `205a` and `205b` (205b extends the lottery onto owned-target combat). `build_dag` reports these as `duplicate_owners` rather than silently picking one; in both cases the two cards' own file order (204a3 before 204b2, 205a before 205b) happens to match the real dependency, but the tool does not assume that — it is a report, not a guess.
- The E-04 sub-slice (`208a1, 208a2, 208b1, 208b2, 208b3, 209a, 209b, 209c, 210`) is where the "not list order" finding is sharpest and least comfortable: `208a2 -> 208a1` (208a1's own test reads `om_events_load_launch`, which is 208a2's function — the reverse of RELEASE_CHAIN's order), `208b1 -> 208a1` (`om_event_set_noise`), and `209c -> 208a1`/`209c -> 208a2` (`om_event_queue_external`). Three of the five foundational E-04 cards read through each other's stubs in both directions. This is the same class of same-cut hazard R7 found and fixed for 204a1/204a3 — it has not been fixed here, because this experiment is read-only and the E-04 cards have never run.

**The DAG is not nearly linear here — but not in the helpful direction for E-04.** Almost every one of the 9 E-04 cards' own fixtures reaches through the same handful of foundational helpers (the template registry, the loader, the noise setter, the tick dispatcher, the external queue) regardless of which specific rule that card tests, producing a dense near-complete graph where `210-e04-fault-injection` alone has 4 separate real prerequisites. A graph scheduler cannot parallelize this slice as cut today: most of it is still serialized behind whichever of the 5 foundational cards finishes last, and 3 of those 5 mutually depend on each other, which is a real same-cut problem (needs a recut and re-verification with `card_lint.py`, the same fix class as R7) — not something better scheduling can route around. The E-05 portion of the slice, by contrast, is close to what the claim needs: one real fork after `204a2`, one same-file extension pair, and gates that fan in cleanly.

## Part 2 — replay

Simulated with `chain_sim.simulate` (`Cycle` = one real Agora run directory: `agora/runs/metrics.jsonl`'s own `wall_minutes` per build cycle — not `candidates.jsonl`'s summed `wall_s`, which excludes worktree/baseline/gate overhead and undercounted a cycle by roughly half in an earlier draft of this tool — with `candidates.jsonl`'s per-candidate `failing_ids`/`wall_s` attached by nearest-timestamp match, 69 of 74 cycles matched within 5 minutes, for the plateau mechanism only).

**Scope, stated plainly, not guessed:** the replay's node set is the 9 cards that both belong to the requested slice *and* have real run history inside the A9 window (2026-09-18 13:01:04 -> 2026-09-19 23:20:00): `204a1, 204a2, 204a3, 204b3, 204b2` plus their 4 story gates. `203e`/`208+` are treated as already `DONE` at t=0 (they finished just before the window opens). `205a` onward were never attempted under the real serial chain in this window — no real run history exists to replay for them, so they are covered by Part 1 (the DAG) but out of scope for Part 2. Two cards that were later hand-retired from `RELEASE_CHAIN` (`204b1-e05-conquest-garrison`, `207-e05-step-order-fault`) real-run inside the window and are responsible for most of its measured idle and wasted building time, so they are kept as phantom nodes with their own real cycles — but excluded from gate-dependency computation (retiring them, not finishing them, is what actually unblocked the gates) and set to retire permanently on hitting the cap or a terminal marker (nothing in the slice depends on them; their real resolution was a hand commit outside Agora, not a tracked fix landing).

Four policies, same real per-cycle data, replayed by a single-GPU-slot discrete-event scheduler (`MAX_TASK_RUNS = 10`, `next.py`'s own cap, enforced identically in S1-S3):

| Policy | finish | building | idle | all targets DONE |
|---|---|---|---|---|
| **S0** (serial, literal history — validates the simulator) | 34h11m | **11h13m** | 22h59m | yes (it's what happened) |
| **S1** (DAG + escalate-and-continue) | 11h30m | 7h37m | 3h53m | yes |
| **S2** (S1 + plateau diagnosis, K=3) | 10h08m | 5h53m | 4h15m | yes |
| **S3** (S2 + autonomous fix, 15 min) | 4h01m | 4h01m | **0h00m** | yes |
| **S3** (S2 + autonomous fix, 30 min) | 4h15m | 4h15m | 0h00m | yes |
| **S3** (S2 + autonomous fix, 60 min) | 5h41m | 5h41m | 0h00m | yes |

S0's building total (672.6 min) matches A9's headline BUILDING number (11.21h = 672.6 min) exactly — the simulator is reading the same real data A9 mined by hand. S0's idle (1378.9 min = 22.98h) sits within 8 minutes of A9's IDLE+STOPPED sum (19.81h + 3.30h = 23.11h); S0 has no STOPPED concept, so a human `systemctl stop` reads as ordinary idle. That's a stated simplification, not an error: this experiment is about the scheduler, and CLAUDE.md's own "sub-agents implement, never design" rule makes most of the real STOPPED time a human decision point by design (A9's counterfactual (c) already found the same thing) — a graph scheduler can't remove it either.

**S1's building drop (672.6 -> 457.2 min, -215.4) is entirely the cap.** `204b1-e05-conquest-garrison` ran 30 real cycles (338.8 min) and never went DONE; enforcing the already-documented 10-attempt cap stops it at 123.4 min, saving exactly 215.4 — `207-e05-step-order-fault` had exactly 10 real cycles in the window already, so the cap doesn't touch it here. **S2's further drop (457.2 -> 352.9, -104.3) is plateau shortening** inside cycles that ran their full candidate budget without converging (biggest contributors: `204a3` -49.9 min, `204b1` -30.7 min, `204a2` -21.3 min). This inherits PX-08's own finding that K=3 plateau diagnosis produces some false stops (a run that would have broken through gets cut anyway) — not re-measured for this specific card set, so S2/S3's building reduction is an upper bound, not a re-verified one.

**S1/S2's two residual idle stretches are both real, not scheduling gaps**, confirmed from the event log:

1. **~118 min** (S1) / **~125 min** (S2), right after `207` exhausts its cap: `204a1`'s first attempt came back `UNSATISFIABLE` and nothing else was ready — `204a3`, `204b2`, and phantom `204b1` all need `204a1` first, `204b3` is separately blocked (below), and `207` just retired. This is A9's own idle cause #1 (the circular-dependency fix + `RELEASE_CHAIN` reorder), reproduced mechanically: the graph scheduler correctly keeps the GPU busy on `207` *up to the cap*, then has nothing left, exactly matching "idle because the dependency is real."
2. **~115 min** (S1) / **~130 min** (S2), after phantom `204b1` exhausts its own cap: `204b2` has run out its own attempts and needs the `206b` recut (A9's idle cause #3) before its next real cycle can land. Nothing else is ready.

`204b3`'s real ~5h54m stall (A9's idle cause #2, needing Westley's fixture audit) **never shows up as idle at all** under S1-S3 — the scheduler fills that entire stretch with `207`'s cycles instead, which is the core mechanism the claim describes.

**S3 (autonomous fixes) removes both residual stretches at every delay tested.** Even a 60-minute autonomous fix — 40x slower than a plausible fast turnaround, and still far slower than deriving the real fix mechanically — never re-idles the GPU in this window, because there is always a lower-priority phantom cycle (`207`, `204b1`) available as filler while the real fix lands. The bottleneck moves entirely from "the GPU has nothing to do" to "how fast can a fix land," which is exactly the shape the plan's design predicts.

## Answering the brief directly

The claim holds for the cards that were actually attempted in this window: idle drops from ~23h (S0, includes STOPPED) to under 4h (S1/S2) to 0h (S3), and building drops too, from cap enforcement and plateau diagnosis rather than from scheduling alone. Both residual idle stretches under S1/S2 are genuine — real human-latency dependencies (204a1's recut, 204b2's need for 206b) that no amount of reordering removes, matching A9's own account card for card. The claim does **not** obviously extend to the E-04 slice as currently cut: its DAG is denser than a line (56 real edges over 27 nodes vs. 26 implied) but the extra edges are concentrated in a small mutually-tangled core (`208a1`/`208a2`/`208b1`/`209c`) that needs a recut, the same class of fix R7 already did for 204a1/204a3 — for E-04, the gain has to come from fixing the cut before scheduling can do anything with it.

## Method notes and limitations

- `MAX_TASK_RUNS = 10` and `TERMINAL_MARKERS` are reused verbatim from `agora/scripts/next.py`, not restated.
- `HARNESS-ERROR` cycles are excluded from the replay, matching `next.py`'s own cap accounting (a dead-input run never reaches the card).
- A blocked card's "fix landed" timestamp is the real next historical cycle's start time for that same task — derived mechanically, not hand-mined from A9's prose, and it lines up with A9's own account because `next.py`'s own terminal-marker design means no cycle ever follows a terminal marker without a human renaming the card first.
- Ready-card tiebreaks use `RELEASE_CHAIN`'s own list order — a tiebreak only, never treated as an implied dependency — with the two retired phantoms placed last.

## RED, then green

```
$ /home/westopoli/Projects/agora/.venv/bin/python -m pytest -q tests/specfactory/test_chain_sim.py
...F...F.......                                                          [100%]
=================================== FAILURES ===================================
________________ test_build_dag_edge_from_stub_owner_to_reader _________________
    assert ("card-a", "card-b") in pairs
E   AssertionError: assert ('card-a', 'card-b') in set()
________________ test_edge_stats_counts_real_vs_serial_implied _________________
E   Differing items:
E   {'real_edges': 0} != {'real_edges': 1}
2 failed, 13 passed in 0.06s
```

Cause: the synthetic fixture's `om_tick_alpha` reader wasn't marked `STUB`, so `find_symbol_stub` correctly refused to manufacture an edge to already-real code — the fixture, not `build_dag`, was wrong. Fixed the fixture; full suite green (16 chain_sim tests, 138 specfactory tests total).
