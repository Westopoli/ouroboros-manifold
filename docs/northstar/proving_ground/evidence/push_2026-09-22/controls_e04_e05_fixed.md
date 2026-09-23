# controls e04/e05 window: dead control fix

Scope: 6 DEAD controls from /tmp/p0_scorecard.md item 2b. 4 fixed LIVE. 2 stay DEAD, can't fix in allowed files, patch reported below.

`control_liveness.py` sweep before: LIVE=14 DEAD=6 ERROR=0 total=20.
`control_liveness.py` sweep after: LIVE=18 DEAD=2 ERROR=0 total=20.

## test_control_e04_chain_counter_unsaved.py (OM_BUG_CHAIN_COUNTER_UNSAVED=207) — still DEAD, not fixable now

Cause: no fault site anywhere in csrc (grep confirms, only header enum). Control's own docstring already says why: bug is about a chain tag reused after a save/reload; `ouroboros_sim.h` has no `om_save`/`om_load` ABI yet, so no fixture in this fenced suite can round-trip a world and observe reuse. Not a fixture bug, not a missing ifdef in a core file I can touch — the feature the bug describes (save/reload) does not exist yet.

Not fixed. Needs: (1) real `om_save`/`om_load` C ABI, (2) a fault site in events.c that skips persisting/restoring `s->chain_counter` across that round-trip. Both are events.c + new-ABI work, out of my allowed files (region.c/faction.c/agent.c/resolve.c/sim.c only). Report only, per task rule (never touch events.c; report patch instead).

## test_control_e04_draw_before_condition.py (OM_BUG_DRAW_BEFORE_CONDITION=206) — FIXED, test-side only

Cause: false negative, fixture blind spot. Fault site is real and correct (`csrc/events.c:619-624`, `evt_resolve_queue`). Control forced exactly one sentinel draw for tick 4 and expected a clean build to leave it untouched. Direct instrumentation showed the sentinel gets consumed on BOTH clean and injected builds — not by the queued candidate this control targets, but by "Regional Revolt" acting as its own standalone `OM_TRIG_PROBABILITY` trigger (`evt_evaluate_triggers`), which draws once per region every non-grace tick regardless of the queued candidate's condition. One sentinel can't tell clean from buggy because something else always eats it first.

Change: force two sentinels before tick 4 instead of one. Measured directly (bug injected vs `om_debug_inject` neutralized): clean leaves 1 remaining (standalone trigger takes the first; due-queue candidate's condition fails before its own roll, second sentinel untouched); injected leaves 0 (candidate's roll happens before its condition check, wasting the first sentinel; standalone trigger still takes the second). Assertion changed from `== 1` to `== 0` after forcing 2.

Proof: `control_liveness.py` on this file alone: `LIVE as-written=passed, neutralized=failed`.

## test_control_e04_triggers_read_live.py (OM_BUG_TRIGGERS_READ_LIVE=208) — still DEAD, not fixable in allowed files

Cause: real C defect, not fixture. Read `csrc/events.c` closely. The bug's read-switch (`live` at line 755, used at line 771) only changes whether `evt_evaluate_triggers`'s phase-1 crossing check reads `w->regions[r]` live or `snap[r]` for region `r`'s OWN fields. Nothing mutates any region's live fields during phase-1 for any region (deltas accumulate in `s->applied_delta`, applied once at the very end, `om_step_events` lines 869-891) — so live vs snapshot is byte-identical there always, for any fixture. The bug's OWN companion inline-mutation block (lines 808-817, applies `t->effect` straight to `w->regions[r]` for a template that just fired) looked promising, but everything it writes gets unconditionally overwritten right after by the same end-of-function batch-apply (`om_step_events` line 875's skip-guard only excludes `OM_BUG_SEQUENTIAL_DELTAS`, not this bug) — so that mutation is erased before anything else in or out of the tick can read it. No cross-region leak is possible either: `evt_live_field(w, r, field)` only ever reads region `r`'s own array slot, never another region's.

Confirmed by direct code trace, not guessed: this branch is a no-op under the current `om_step_events` structure, same unsatisfiable-by-construction class as R7h/R9 in DECISIONS.md.

Not fixed — events.c off limits (never events.c per task rule). Exact patch for whoever owns events.c next: add `&& w->inject != OM_BUG_TRIGGERS_READ_LIVE` to the skip-guard at line ~875, so the end-of-function batch-apply is ALSO skipped when this bug is injected (same treatment as `OM_BUG_SEQUENTIAL_DELTAS` already gets). That makes the 808-817 inline mutation the actual final state instead of a wasted write, and turns this into an observable "same-region same-tick effects compound live instead of summing against tick-start" bug. Needs a NEW fixture too (a single region with two templates crossing on the same tick, not the current cross-region-swap fixture) — the swap fixture can never observe this even with the patch, since the bug never touches a different region's fields.

## test_control_e05_agent_reads_live.py (OM_BUG_AGENT_READS_LIVE=100) — FIXED, test-side only

Cause: unsatisfiable-by-construction fixture (matches DECISIONS.md R7h exactly — this IS R7h's control). Original fixture had faction 0 surprise-attack region 1 in step 3f, then checked faction 2's step-3d weakness read for region 1. Step 3d always finishes, every faction, before 3f mutates anything — correct build or buggy — so no candidate can ever see this tick's own later 3f mutation. Also confirmed: `csrc/agent.c` `om_faction_candidates` reads region military live unconditionally for weakness, no snapshot branch exists there at all; the real `w->inject == 100` branch (agent.c:185) only gates `potential_commit` from the deciding faction's OWN budget.

Found a different, real, already-live branch of the same bug: step 3b (`om_faction_step_budget`, ALG-17) grows each faction's live budget right after the 3a snapshot is taken, every tick, for any faction whose economy is above 8.0 — so live budget and snapshotted budget diverge within the SAME tick without needing a second faction or a mid-tick mutation at all. New fixture: one conqueror (economy 50.0, confidence 200.0 — high enough that only the extra live-budget-driven `potential_commit` crosses its viability threshold) vs one target. Measured directly: clean final budget 101.05 (100 + (50-8)*0.025 growth only, nothing declared, snapshot-based potential_commit stays under confidence); injected final budget ~31.05 (same growth, then live-budget-based potential_commit crosses the threshold, declares, spends the rest).

Proof: `control_liveness.py` on this file alone: `LIVE as-written=passed, neutralized=failed`.

## test_control_e05_garrison_before_damage.py (OM_BUG_GARRISON_BEFORE_DAMAGE=106) — FIXED, core file (resolve.c)

Cause: no fault site existed at all (matches DECISIONS.md R7l). `csrc/resolve.c`'s conquest/garrison pass (~line 461) always did `target->military += garrison` unconditionally, no branch on `w->inject`. R7l's own prior finding: fixing this via a "clamp order" reconstruction needs the ORIGINAL pre-damage military, which is already gone (clamped away) by the time the garrison pass runs, spanning two separate functions (`om_step_telegraphs` at 3c, `om_step_resolve`'s garrison pass at 3f) — not reconstructable without a new persisted field.

Used the watch-for's own SECOND clause instead ("or garrison is reduced by the attack's damage calculation" — docs/northstar/e2e/E-05.md), which needs no reconstruction: `r->d_military` (the attack's own already-applied damage delta) is already stored on the attack record. Added, resolve.c only:

```c
double garrison = r->commit * 0.65;
#ifdef OM_DEBUG_INJECT
if (w->inject == OM_BUG_GARRISON_BEFORE_DAMAGE) {
    target->military = fmax(0.0, target->military + garrison + r->d_military);
} else
#endif
{
    target->military += garrison;
}
```

Re-applies the SAME damage delta to the post-garrison total, i.e. the damage calculation reduces the garrison too. No fixture change needed — the control's OWN original numbers (military 20.0, damage -16.0, garrison 27.3) already distinguish: clean 4.0+27.3=31.3, buggy fmax(0, (4.0+27.3)+(-16.0))=15.3.

Proof: `control_liveness.py` on this file alone: `LIVE as-written=passed, neutralized=failed`.

## test_control_e05_telegraph_after_reinforce.py (OM_BUG_TELEGRAPH_AFTER_REINFORCE=101) — FIXED, test-side only

Cause: unsatisfiable-by-construction fixture (matches DECISIONS.md R9 exactly — this IS R9's control). `om_step_reinforce` (3e) only reacts to telegraphs with `declared_tick == w->tick`; `om_step_telegraphs` (3c) only touches telegraphs at least 3 ticks old. Moving 3c before or after 3d/3e changes nothing about a telegraph's OWN declaration-tick reactive reinforce — confirmed by R9 with two independent scenarios, reconfirmed here.

Found the real, actually-observable seam: `om_step_reinforce`'s headroom calc (`(tier_cap - target.military) / tier_cap`) reads the target's CURRENT military. If a DIFFERENT, unrelated telegraph matures against the SAME target on the SAME tick (3c), the correct order (3c before 3e) means that damage already landed before headroom is computed for a second, freshly-declared telegraph against the same target; the buggy order computes headroom against the undamaged value instead. New fixture: two attackers (A, B) sharing one target T, owned by a fortifier. A's telegraph is injected on tick 0 (via `inject_intent`, `declared_tick=1`, matures tick 4); B's is injected right before the tick-4 step (`declared_tick=4`, fresh this tick). Both attackers get confidence 999999 so neither's own 3d recompute ever declares anything on its own — every telegraph here is `inject_intent`-controlled, no uncontrolled extra draws.

Measured directly: clean build's tick-4 reinforce record `d_military` = 3.1429309981935623; injected = 2.492991348464528. Same seed, same forced draws, same fixture, only the inject flag differs.

Proof: `control_liveness.py` on this file alone: `LIVE as-written=passed, neutralized=failed`.

## Regression check

- `control_liveness.py` on all 20 E-04/E-05 controls: LIVE=18 DEAD=2 (up from 14/20; the 2 remaining are report-only above).
- `tests/csim/test_E02_*.py`: 72 passed, 4 skipped (unchanged from scorecard).
- `tests/csim/test_E04_*.py`: 31 passed (unchanged).
- `tests/csim/test_E05_*.py`: 60 passed, 2 skipped, 1 xfailed, 2 FAILED — same 2 pre-existing, unrelated failing ids as the scorecard (`test_R_032_03_it_uses_attack_weight_0`, `test_R_037_07_attacker_s_committed_budget_spent`, both position-weighting/same-tick-budget-spend regressions the scorecard already flagged, item 1 — not touched by this card, not caused by the resolve.c garrison change).
- `test_control_empty_drifts.py` / `test_control_osc_as_level.py`: 2 passed, both LIVE (unchanged).

## Files touched

- `csrc/resolve.c` — added the `OM_BUG_GARRISON_BEFORE_DAMAGE` fault site (core file, allowed).
- `tests/csim/controls/test_control_e04_draw_before_condition.py` — fixture fix (2 sentinels).
- `tests/csim/controls/test_control_e05_agent_reads_live.py` — full fixture rewrite (budget-growth branch).
- `tests/csim/controls/test_control_e05_telegraph_after_reinforce.py` — full fixture rewrite (shared-target headroom branch).
- `tests/csim/controls/test_control_e04_chain_counter_unsaved.py` — untouched, still DEAD, report-only above.
- `tests/csim/controls/test_control_e04_triggers_read_live.py` — untouched, still DEAD, report-only above (exact events.c patch given).
