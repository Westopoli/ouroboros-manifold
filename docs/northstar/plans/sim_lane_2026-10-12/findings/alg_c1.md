# Sim lane C1: equation tests for eleven ALG rows

Test writer C1, 2026-10-13, base `origin/main` b64ff6d2. No `csrc/` change, no existing test or `pieces.toml` edit. Eleven tests fail against the C sim on purpose (nine findings below, SL-C1-02 and SL-C1-08 and SL-C1-09 in one file); each is left red. Run: `~/Projects/ouroboros-manifold/.venv/bin/python -m pytest tests/csim/test_alg_*.py -q` gives 186 passed, 11 failed (exact-midpoint delay cases are skipped inside the file).

## Coverage

| ALG | Test file (under `tests/csim/`) | Result | Positive control |
|---|---|---|---|
| ALG-16 colonize intent | `test_alg_16_colonize_intent.py` | green (2) | source moves when adjacency moves; wrong source expectation raises |
| ALG-18 reactive reinforce | `test_alg_18_reactive_reinforce.py` | red (1 of 15): SL-C1-01 | draw just above `min(1, w_defend/1.5)` removes the reinforce; wrong commit expectation raises |
| ALG-19 reinforce | `test_alg_19_reinforce.py` | green (20) | tension moves the variance interval; tension-blind expectation raises |
| ALG-25 border friction | `test_alg_25_border_friction.py` | green (3) | debug build with `OM_BUG_FRICTION_COUNTS_TRADE` makes the same assertions fail |
| ALG-28 convergence | `test_alg_28_convergence.py` | green (4) | summed-partners and rate 0.2 expectations raise; no cooperative stance gives no bonus |
| ALG-35 firing and spawning | `test_alg_35_firing_and_spawning.py` (also pins the ALG-22 unrest delay and the admin and conquest chain starts) | red (5 of 76): SL-C1-02, SL-C1-08, SL-C1-09 | debug build with `OM_BUG_CHAIN_COUNTER_UNSAVED` fails the counter check; wrong floor and wrong delay raise |
| ALG-37 mutual exclusion (with the ALG-36 sequencing around it) | `test_alg_37_mutual_exclusion.py` | red (3 of 19): SL-C1-03, SL-C1-04, SL-C1-05 | debug build with `OM_BUG_EXCLUSION_CANCELS` fails the requeue check; wrong due tick raises |
| ALG-39 peace formation | `test_alg_39_peace_formation.py` | green (12) | a draw of exactly p does not succeed; wrong disposition raises |
| ALG-41 breakaway creation | `test_alg_41_breakaway_creation.py` | red (1 of 16): SL-C1-06 | unfloored economy and uncapped tension expectations raise; chain with no takeover does split on tick 3 |
| ALG-43 latent loyalty | `test_alg_43_latent_loyalty.py` | green (10) | revert-at-age-21 and revert-at-draw-0.5 expectations raise; draw 0.4999 at age 20 does revert |
| ALG-44 lifecycle phase | `test_alg_44_lifecycle_phase.py` | red (1 of 20): SL-C1-07 | one-step input flips the phase; wrong check order raises; a quiet faction is not in conflict |

No row skipped: every function is reachable through exported symbols (`om_world_step`, `om_tick_*`, `om_faction_*`, `om_events_load`, `om_event_queue_external`, `om_intent_inject`).

Fixture note for readers: the file names `test_alg_NN_*` get the default feature set from the harness, so each test sets its own features (`isolate_agents` or `isolate_events`, then the one extra feature). Expected values are computed in each file from the algorithms.md text; no number is copied from C output.

## Findings

Class codes: C = C differs from the bible; A = bible ambiguous (Q row proposed).

### SL-C1-01 (C, high): a defender reinforces once per telegraph, not once per faction

- Rule: ALG-18 "Among telegraphs targeting this faction, take the one with the largest commit ... one RNG draw"; E-05 R-036-03 "the defender's one reactive reinforce".
- Sim: `om_step_reinforce` (`csrc/resolve.c:264`) loops over every telegraph declared this tick, takes one probability draw and one variance draw each, and spends budget each time. Two telegraphs (commits 30 and 60) against a defender with budget 100 produce two reinforce records, target 2 commit 15.0 and target 3 commit 30.0, and four draws. The rule gives one record: target 3, commit 30.0, two draws.
- Repro: `test_alg_18_reactive_reinforce.py::test_ALG_18_only_the_largest_telegraph_is_answered_with_one_draw`; failing line `assert len(got) == 1` with `[(2, 15.0), (3, 30.0)]`.
- Fix piece: group telegraphs with `declared_tick == tick` by defending faction, keep the largest commit (ties: first declared), one draw. Files: `csrc/resolve.c`. Changes RNG draw count whenever one faction is targeted twice in a tick, so golden traces move. Check owner row in `pieces.toml` first.

### SL-C1-02 (C, medium-high): an event that fires in a region lifts every field to its floor, including fields the event does not change

- Rule: ALG-36 "each nonzero summed delta applies once against the tick-start field with the ALG-35 floors". A field with a zero summed delta is not applied. E-02 R-019-04 floors tension at 12.0 only when "an event effect would lower it further"; drift alone may leave tension below 12.0, and conquest may leave economy below 8.0 (R-019-02).
- Sim: `om_step_events` (`csrc/events.c`, the `s->touched[r]` block) clamps all four fields of any touched region. A military-only event (+5) on a region with economy 3.0 and tension 5.0 leaves military 55.0, economy 8.0, tension 12.0. Rule result: economy 3.0, tension 5.0.
- Repro: `test_alg_35_firing_and_spawning.py::test_ALG_35_a_field_with_zero_delta_is_not_touched`; failing line `assert lib.om_region_field(w, 0, OMField.TENSION) == pytest.approx(5.0)`, got 12.0 (economy got 8.0).
- Effect in play: a quiet region (tension drifted under 12) or a conquered region (economy under 8) is silently lifted by any unrelated event. Small per case, systematic across a long run.
- Fix piece: apply the clamp per field only where the summed delta is nonzero. Files: `csrc/events.c` (about 6 lines). Confidence medium-high; if Westley prefers the lift, the bible sentence changes instead (Q row below).
- Q-row proposal if he wants it kept (A): "Does an event that touches a region lift an already-below-floor field it does not change?" (a) no, only nonzero summed deltas apply (bible text today); (b) yes, any event touching the region re-floors all four fields; (c) yes for tension only.

### SL-C1-03 (C, medium): exclusion and probability rolls are sequenced across all regions, not per region

- Rule: ALG-36 "Per region: exclusion pass (ALG-37); then for each surviving entry in queue order ... one draw". Region 0's loser draw and roll come before region 1's draws. Region order is assumed ascending (the rule says "grouped by region").
- Sim: `evt_resolve_queue` (`csrc/events.c`) runs every region's exclusion pass first (tag-major, then region), then rolls all survivors. Draw order for two regions each holding a p 0.3 / p 0.7 pair: sim `[loser0, loser1, roll0, roll1]`, rule `[loser0, roll0, loser1, roll1]`. With forced draws `[0.25, 0.1, 0.75, 0.9]` the rule fires region 0's survivor (0.1 <= 0.7) and delays region 1's loser to tick + 2; the sim fires nothing and delays both to tick + 1 (observed `[] == [(0, 1)]`).
- Repro: `test_alg_37_mutual_exclusion.py::test_ALG_36_37_exclusion_pass_then_rolls_per_region`.
- Effect: byte-level RNG order differs from the bible's contract ("same seed, same draw order") whenever two regions have exclusion pairs due on the same tick; rare, but it breaks the equivalence promise.
- Fix piece: restructure `evt_resolve_queue` phase 1 and 2 into one per-region loop. Files: `csrc/events.c`. Moves goldens. Pair with SL-C1-04 and SL-C1-05 (same function, same piece).

### SL-C1-04 (C, high): conditions are checked before mutual exclusion; the rule checks them after

- Rule: ALG-36 order (exclusion pass, then "if conditions fail skip with no draw ... else one draw") and `docs/northstar/e2e/E-04.md` "Order of operations" (2) exclusion, (3) condition check. A high-probability entry whose condition fails still wins its tag, so a lower-probability entry that would pass is delayed one or two ticks.
- Sim: the condition test runs while candidates are collected, so a failing entry is pruned before the exclusion pass and never competes. Fixture: p 0.6 entry with condition "military above 90" (region has 50) against a p 0.4 entry, same tag, due tick 3. Rule: loser p 0.4 re-queued to tick 4 (draw 0.25), winner pruned, one draw consumed. Sim: nothing delayed (`[] == [(2, 1, 4)]`), the p 0.4 entry rolls instead.
- Repro: `test_ALG_36_37_exclusion_runs_before_conditions`.
- Real case: "Revolt Crushed" (military above 35, p 0.45) against "Revolt Entrenched" (tension above 40, p 0.55), tag REVOLT_OUTCOME, when only Crushed's condition holds. Rule: Entrenched wins, is pruned, Crushed waits. Sim: Crushed fires at once.
- Fix piece: as SL-C1-03; also record the SL-C1-05 coupling. Files: `csrc/events.c`.

### SL-C1-05 (A, low-medium): a re-queued exclusion loser loses its condition

- Rule text: ALG-35 entries are `{template, region, due, probability, conditions, chain_tag}`; ALG-37 says "re-queue each other one with due = tick + randint(1, 2)". Reading it as the same entry, the conditions travel with it. It does not say so outright.
- Sim: the loser is re-enqueued with `OM_COND_NONE` (`csrc/events.c`, phase 1 `evt_enqueue(... OM_COND_NONE, 0, 0.0 ...)`). Fixture: both entries "military above 40", loser re-queued to tick 4, military set to 20 before tick 4. Rule (conditions kept): pruned at tick 4. Sim: the loser fires (queue shows `(2, 4, cond_kind 0)`).
- Repro: `test_ALG_36_37_requeued_entry_keeps_its_conditions`.
- Coupling: under the sim's own order (conditions first, SL-C1-04) dropping the condition is defensible because it already passed. If SL-C1-04 is fixed (exclusion first) the condition has not been checked yet, so dropping it would let the entry skip its condition forever; the two must be settled together.
- Q-row proposal: "When an exclusion loser is re-queued, does it keep its spawn condition?" (a) yes, re-checked at the new due tick (the entry is unchanged); (b) no, the condition was checked once when it first came due; (c) checked once at the original due tick, then dropped (needs the SL-C1-04 order to change too).

### SL-C1-06 (C, medium-high): an admin chain is not pruned when the region changes hands mid-chain

- Rule: ALG-41 "Admin revolt: pruned if the region's owner differs from the chain's source faction or the region changed hands after the chain started."
- Sim: the owner-versus-source check in `evt_resolve_queue` (`csrc/events.c`, the `cur_src[i] == OM_SRC_EXTERNAL` guard) runs only for externally queued entries. Chain steps spawned by `evt_admin_chain_spawn` carry `OM_SRC_SPAWN`, and the admin revolt roll in `csrc/friction.c:162-173` queues without marking the source, so the check never runs on the real path. Launch library, short chain (L = 3, source faction 0, ticks 1 to 3); faction 1 takes the region before tick 3. Rule: no breakaway, region stays with faction 1. Sim: region 0 becomes new faction 2 (owner read back as 2, expected 1; 3 factions, expected 2).
- Repro: `test_alg_41_breakaway_creation.py::test_ALG_41_admin_chain_is_pruned_when_the_region_changes_hands_mid_chain`; control `test_control_ALG_41_the_admin_chain_reaches_its_breakaway_on_tick_3` is green. The direct external path (`source_faction` differs from owner) is pruned correctly and tested green.
- Fix piece: apply the owner check to every `creates_faction` entry that carries a `source_faction >= 0`, and for "changed hands after the chain started" compare the region's held-since to the chain's start tick (needs the start tick stored on the chain entry, a small queue-struct change, so a contract check on `om_queued_event`). Files: `csrc/events.c`, possibly `csrc/om_internal.h`. Confidence medium-high on the owner half; the held-since half needs the layout change decided.

### SL-C1-07 (C plus A, high on the wiring, open on the window): the lifecycle phase has no input in play

- Rule: ALG-44 evaluates "a faction's recent event list"; E-07 S-053 outputs a "phase label in the faction entry" consumed by E-09 and E-10, with the window "whatever the caller passes; the chronicle passes the time-jump window". CLAUDE.md "Wired, not just tested".
- Sim: `faction_window_*` is written only by `om_faction_set_event_window_counts`, which only tests call (grep of `csrc/`, `autoload/`, `scenes/`, `scripts/`: no other writer, no caller of `om_faction_phase` apart from tests). In play the window is all zero, so a faction that attacked eight ticks running reads equilibrium (5), never conflict (2), fragmentation, or consolidation. The equation itself (sixteen scenarios, boundaries and order) is green.
- Repro: `test_alg_44_lifecycle_phase.py::test_ALG_44_phase_follows_what_the_faction_actually_did`; fixture check shows faction 0 really attacked (at least two attack records); failing line `assert lib.om_faction_phase(w, 0) == CONFLICT`, got 5.
- Q-row proposal (A): "What is a faction's recent event window and who feeds it?" (a) the tick log of the last time jump, filled by the sim at the end of each jump and read by the chronicle and mission generator; (b) a rolling last-N-ticks ring per faction maintained every tick (N a named draft, 50 matching the Knowledge Lost window); (c) computed on demand by each caller from the delta stream, `om_faction_phase` takes counts as arguments.
- Fix piece after the answer: new file `csrc/lifecycle_window.c` (feed) plus a wiring piece in `csrc/sim.c` and the readers in E-09 and E-10. Not buildable before the Q row is answered.

### SL-C1-08 (C, high): admin-revolt and conquest chain starts get tag 0, not the next counter value

- Rule: ALG-35 "Every chain start, whether a fresh trigger, a conquest spawn, or an admin-revolt spawn, takes the next value of one global counter (`chain_NNNN`, saved with the world; E-04 R-027-06)".
- Sim: `csrc/friction.c:162-173` (admin roll) and `csrc/resolve.c:513-520` (conquest unrest) write the queue entry with `chain_tag = 0`, with a comment that no public counter setter exists. First chain start of a fresh world reads tag 0 and `om_chain_counter` 0; the rule gives tag 1 and counter 1. Every such chain in a world therefore shares tag 0.
- Repro: `test_alg_35_firing_and_spawning.py::test_ALG_35_an_admin_revolt_chain_start_takes_the_next_counter_value` and `::test_ALG_35_a_conquest_chain_start_takes_the_next_counter_value`; failing lines `assert q[0].chain_tag == 1` (got 0) and `assert q.chain_tag == 1` (got 0).
- Likely consequence for E-09: `csrc/chronicle.c:1608` merges raw chain events "by chain_tag" (R-067-03), so unrelated conquest-unrest and admin chains in different regions would merge into one story. The path from a fired event to `om_chronicle_add_chain_event` was not traced here; the sim lane's chronicle-source check should look for it.
- Fix piece: allocate the tag from the events state's counter at both write sites (a small exported allocator in `csrc/events.c`, declared in `csrc/om_internal.h`, called from `friction.c` and `resolve.c`). Files: `csrc/events.c`, `csrc/om_internal.h`, `csrc/friction.c`, `csrc/resolve.c`. Moves goldens and the saved counter. Confidence high.

### SL-C1-09 (C, high): the conquest-unrest delay uses only the lower half of the triangular

- Rule: ALG-22 "round(triangular(4, 8, mode 6)) ticks (second draw)"; the triangular is the one ALG-35 defines, with mode at the midpoint, so draws above 0.5 take the upper branch `b - sqrt((1 - u)(b - a)(b - mode))`.
- Sim: `csrc/resolve.c:509-511` computes `4 + 4 * sqrt(u * 0.5)` for every u. For u = 0.75 the sim gives delay 6 (rule 7: 8 - sqrt(0.25 * 4 * 2) = 6.59, rounds to 7); for u = 1.0 the sim gives 7 (rule 8). Draws 0.0 to 0.6 agree. The delay never reaches 8 and the mean is low by about 0.4 tick.
- Repro: `test_alg_35_firing_and_spawning.py::test_ALG_22_35_conquest_unrest_delay_is_round_triangular_4_8_mode_6[0.75]` (`assert 7 == (1 + 7)` reads due tick 7, wanted 8) and `[1.0]` (due 8, wanted 9).
- Fix piece: reuse the events.c `evt_delay_from_u` through the same allocator as SL-C1-08. Files: `csrc/resolve.c` (and `csrc/events.c` to export the helper). Confidence high.

## Observations (not asserted, no test)

- OBS-1, ALG-28: convergence updates tech in place in faction order, so a later faction reads an earlier faction's converged value (probe: A 90, B 50 cooperative toward A, C 10 cooperative toward B gives B 50.04, C 10.04004; a simultaneous reading gives C 10.04). E-06 R-047-04 says "reads the updated levels in faction order", which allows it. Left unasserted.
- OBS-2, ALG-44 overextension: with total economy exactly 0 the C check is skipped (division guard); the ratio is undefined in the rule. Reachable only with conquered regions at economy 0.
- OBS-3, ALG-44 expansion: "inhabited region count" is read world-wide (matches E-07 R-053-04 "all inhabited regions"); the test pins that reading.
- OBS-4, ALG-16 and ALG-39: "adjacent" and "bordering" mean any edge type, trade-only included, in `csrc/agent.c` and `csrc/diplomacy.c`; ALG-25 excludes trade-only edges for friction. The bible does not say which for colonize and peace; not asserted.
- OBS-5, ALG-18: the budget used is the tick-start snapshot taken before ALG-17 accumulation (3a, then 3b); the rule says "budget". Same value whenever economy equals the 8.0 maintenance cost (the fixtures); unasserted.
- OBS-6, ALG-35: the delay rounding is floor(x + 0.5) (half up), as the header documents; exact .5 midpoints are skipped in the delay sweep.
- OBS-7, ALG-25: the friction record reports the applied (clamped) delta, not the nominal sum, at the tension cap and the economy floor.
