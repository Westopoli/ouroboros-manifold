# B1 six red E-04 tests — rebudget to Draw order contract (push 2026-09-22)

Verification lane traced 6 red tests on branch `origin/push/B1` (piece B1,
`csrc/events.c`). Root causes: forced-draw budgets predate the "Draw order"
paragraph landed in `docs/northstar/e2e/E-04.md` today (regional-revolt roll
draws once per inhabited, off-cooldown, post-grace region every tick,
regardless of p — ALG-34), so budgets undercounted; some fixture fields also
crossed Garrison Collapse's fresh-trigger threshold (military < 30) by
accident. Fixed both classes here, tests only, no impl touched. Branch's
`events.c` still interleaves the revolt roll in template-id order instead of
the contract's per-region order (crossings, then revolt roll, then fired
threshold spawns, then revolt's own spawns) — M1's leaf job. 3 of 6 rows are
order-blind (fix alone clears them); 1 row (R-027-06) is order-sensitive and
stays red on the branch on purpose, at the exact assertion the wrong order
breaks.

Scratch build: detached worktree `/tmp/b1t/wt` off `origin/push/B1`
(`c1f06bb`), `make -s libouroboros.so libouroboros_dbg.so`, worktree removed
after. Main-build check ran against the live `libouroboros.so` already built
at repo root (`events.c` stub, unrelated working-tree diff to
`ouroboros_sim.h` not touched).

## Files changed

`tests/csim/test_E04_S026_crises_start_when_a_line_is_crossed.py`,
`tests/csim/test_E04_S027_one_thing_leads_to_another.py`,
`tests/csim/test_E04_S029_some_pressures_never_stop.py`. No assertion
removed or weakened; two field-value assertions updated to match a changed
fixture field (see R-027-07 row); several `om_rng_forced_remaining`
assertions added (strengthening, not weakening).

## Per-test table

### 1. `test_R_026_06_each_field_delta_applies_with` (R-026-06, R-028-01)

- **Old budget:** `[1.0] * 50`, blanket over-provision, tick 4 only needed 6
  (never checked exactly).
- **New budget:** unchanged (`[1.0] * 50` already covers the true 6-draw
  need: 3 revolt-roll draws region 0/1/2 + 1 Military Buildup spawn (region
  2) + 2 Famine spawns (region 0); Cultural Renaissance has 0 spawns). No
  force_draws edit needed — this row's defect was field-only.
- **Field change:** Region 1's grace-period economy 50.0 -> 56.0. At 50.0,
  jumping to 65.0 on tick 4 crosses BOTH Trade Boom (economy > 55) and
  Cultural Renaissance (economy > 60) as fresh rising edges, so the test's
  own no-fire assumption for Trade Boom was false — branch fired both,
  deltas summed to economy +3.0 not the asserted +1.0. Priming Trade Boom's
  breached flag during grace (56.0 > 55.0, still < 60.0) keeps only Cultural
  Renaissance crossing fresh at tick 4, per R-026-02/R-026-05.
- **Order-sensitivity:** none. Every fired threshold template here (Famine
  id 17, Military Buildup id 14) has a table id > the revolt's id 3, so the
  branch's per-template-id interleave and the contract's per-region order
  produce the identical draw sequence.
- **Branch result:** PASS.
- **Main (stub) result:** FAIL, `assert deltas0[OMField.ECONOMY] ==
  pytest.approx(-0.5)` gets `0.0` — stub fires nothing, red for the stub, not
  this fix.

### 2. `test_R_027_02_it_dropped_without_firing_without` (R-027-02, R-027-07)

- **Old budget:** tick 4 `[0.99, 0.99, 0.50, 0.50]` (4), asserted remaining
  4 -> 2 (2 consumed).
- **New budget:** tick 4 `[0.99] * 8` (8), asserted remaining 8 -> 0. Draw
  list in order: pending-queue probability roll for region 2's Regional
  Revolt spawn (condition met, tension 41 > 40), pending-queue probability
  roll for region 5's Border Incursion spawn (condition met, military 17 <
  18), then the fresh-trigger phase's regional-revolt roll for regions 0-5
  in index order (6 draws, e2e "Draw order" / ALG-34) — none of the six
  regions has a fresh threshold crossing this tick so no spawn draws follow.
- **Field change:** regions 3, 4, 5 primed to military 25.0 during the grace
  period (was 50.0, uniform with the others). The rule's own boundary values
  at tick 4 (19.0, 18.0, 17.0, testing Border Incursion's spawn condition
  military < 18) are themselves below Garrison Collapse's fresh-trigger
  threshold (30.0) and unavoidably so — the fix primes Garrison Collapse's
  breached flag during grace instead, so it doesn't fire fresh at tick 4
  (R-026-02, R-026-05); "stay above 30" isn't available here since the rule
  under test needs values near 18.
- **Order-sensitivity:** none. After the field fix, no threshold template
  fires for any of the 6 regions at tick 4 — the only draws are the 2
  pending-queue rolls and the 6 revolt rolls, none interleaved with a
  fired-template's own spawn draws.
- **Branch result:** PASS.
- **Main (stub) result:** FAIL, `assert lib.om_rng_forced_remaining(w) == 8`
  gets `23` (the stub never consumes tick 1's 15 forced draws either, they
  pile up) — red for the stub.

### 3. `test_R_027_04_regional_revolt_may_fire_with` (R-027-01, R-027-04)

- **Old budget:** tick 50 `[0.00, 0.50, 1.00, 0.50]` (4).
- **New budget:** tick 50 `[0.99, 0.00, 0.50, 0.99, 1.00, 0.50]` (6). Per
  region (0 then 1): revolt-roll (0.99, safe) first, then Famine's own two
  spawn delays in spawn-table order (Regional Revolt delay, Famine Relief
  delay) — unchanged values, just no longer absorbing the missing
  revolt-roll draw ahead of them.
- **Field change:** none needed.
- **Order-sensitivity:** none. Famine (id 17) is the only fired template
  here and its id is greater than the revolt's id 3 in both the branch's
  per-template-id order and the contract's per-region order, so the revolt
  roll lands before Famine's spawn draws either way. (Old budget's bug was
  a pure missing-draw undercount: the intended "0.00" spawn-delay value was
  getting consumed by the un-budgeted revolt roll instead, and 0.00 < p
  fired Regional Revolt as an unintended fresh trigger — 3 events instead
  of 2 was the original red.)
- **Branch result:** PASS.
- **Main (stub) result:** FAIL, `assert len(events_50) == 2` gets `0` — red
  for the stub.

### 4. `test_R_027_06_its_chain_tag_equals_root` (R-027-01, R-027-06)

- **Old budget:** tick 4 `[0.00, 1.00, 0.00]` (3).
- **New budget:** tick 4 `[0.99, 0.00, 1.00, 0.99, 0.00]` (5). Region 0:
  revolt-roll (0.99), then Garrison Collapse's (fresh trigger, template id
  0) two spawns in spawn-table order (Border Incursion delay 0.00 -> due 7,
  Emergency Levy delay 1.00 -> due 9). Region 1: revolt-roll (0.99), then
  Trade Boom's one spawn (Prosperity Unrest delay 0.00 -> due 12). Same
  due-ticks the original comment already named (7, 9, 12) — the fix only
  adds the two missing revolt-roll draws at their contract position, ahead
  of each region's fired-template spawns.
- **Field change:** none needed (Region 0's military 25.0 crossing Garrison
  Collapse is this rule's own intended scenario, not an accident).
- **Order-sensitivity:** YES — this is the one row that stays red on the
  branch by design. Garrison Collapse's template id (0) is less than the
  revolt's id (3), so the branch's per-region-per-template-id loop visits
  Garrison Collapse first: it fires and draws its two spawns *before* the
  loop reaches id 3's revolt roll, consuming draws in the order
  `[spawn1, spawn2, revolt-roll]` instead of the contract's `[revolt-roll,
  spawn1, spawn2]`. With the corrected 5-value list, the branch misassigns
  values: Border Incursion's spawn gets u=0.99 (delay 7, due tick 11, not
  7), Emergency Levy gets u=0.00 (delay 2, due tick 6, not 9), and the
  revolt-roll for region 0 gets u=1.00 (still safe, no accidental fire).
  Emergency Levy then resolves at tick 6 off an unforced real RNG draw
  (its own 0.40 probability), and the two leftover forced values `[0.99,
  0.00]` meant for tick 7's real Border Incursion resolution instead land on
  region 0's tick 7 revolt-roll (0.99, safe) and *region 1's* tick 7
  revolt-roll (0.00 < p, fires) — Region 1 is inhabited and past grace too,
  so its roll is drawn in the same fresh-trigger pass. Confirmed against the
  branch build twice (deterministic, same result both runs): fails cleanly
  at `assert ev_spawn1.template_id == tid_border` (line ~552, `tests/csim/
  test_E04_S027_one_thing_leads_to_another.py`), obtained `3` (Regional
  Revolt's template id) instead of `1` (Border Incursion's) — a clean
  assertion failure, not a Python exception, and full suite rerun shows
  every other test in `test_E04_*.py` still green (30 passed, 1 failed).
  This is exactly the revolt-roll-position defect M1's leaf fixes; the test
  is correct against the contract (traced the correct-order due-ticks by
  hand: 7, 9, 12, matching the original comment) and will pass once
  `events.c` draws in per-region contract order.
- **Branch result:** FAIL, at the position-sensitive assertion above, not a
  crash.
- **Main (stub) result:** FAIL, `assert len(events_4) == 2` gets `0` — red
  for the stub (same failure mode as before this rebudget; still red, still
  for the stub, not the order bug).

### 5. `test_R_027_07_it_holds_pruned_record_with` (R-027-02, R-027-07)

- **Old budget:** tick 4 none forced (0 draws expected, 0 provided).
- **New budget:** tick 4 `[0.99, 0.99]` (2), asserted remaining 2 -> 0.
  Region 0 then region 1's regional-revolt roll (both inhabited, past
  grace, off cooldown); neither region has a fresh threshold crossing this
  tick, so these are the only two tick-4 draws.
- **Field change:** Region 1's tick-4 military 25.0 -> 35.0. 25.0 satisfies
  the rule's own condition (Border Incursion's spawn wants military >= 18,
  i.e. condition fails) but also crosses Garrison Collapse's fresh-trigger
  threshold (< 30) as an unintended new edge (was unbreached at military
  50.0 during grace) — branch fired Garrison Collapse fresh, 1 extra event,
  where the test expects 0. 35.0 keeps the condition failing (>= 18) while
  staying above 30, per the "use values that keep the rule's scenario but
  stay above Garrison Collapse's 30" fix pattern — unlike row 2, this rule
  doesn't need a value near the 18 boundary, so this route is available
  here. Downstream assertion `p1.field_value == pytest.approx(25.0)` updated
  to `35.0` to match.
- **Order-sensitivity:** none. No threshold template fires for either
  region at tick 4 after the field fix, so the two revolt-roll draws are
  each the only draw in their region's pass.
- **Branch result:** PASS.
- **Main (stub) result:** FAIL, `IndexError: list index out of range` at
  `tag0 = [e for e in events_1 if e.region_idx == 0][0].chain_tag` — stub
  fires nothing at tick 1 either, so the list is empty; pre-existing stub
  artifact at this same line before this rebudget too, not a new failure
  mode from this change.

### 6. `test_R_029_03_no_revolt_roll_made_for` (R-029-01, R-029-03)

- **Old budget:** tick 4 `[0.0, 1.0, 1.0]` (unchanged, already correct: no
  other region, no other fired threshold template, so no interleave issue).
  Tick 5 `[0.0]` (1, intentionally left unconsumed — proves no roll on
  cooldown). Ticks 6-15 loop forced `[1.0, 1.0]` every tick regardless of
  whether anything was due (20 draws total), of which only 2 were ever
  actually consumed (Revolt Crushed's probability roll at tick 9, Revolt
  Entrenched's at tick 12). Tick 16 `[0.0, 0.5, 0.5]`.
- **New budget:** tick 4 unchanged. Tick 5 changed to `[0.99]` (still 1
  draw, still asserted unconsumed at remaining == 1 — value only, not the
  check). Ticks 6-15: forced only at tick 12, `[1.0]` (1 draw) — tick 9's
  Revolt Crushed roll is left to consume the tick-5 leftover instead of a
  new value (see below), and every other tick in the window forces nothing.
  Tick 16 unchanged, now preceded by `assert lib.om_rng_forced_remaining(w)
  == 0`.
- **Field change:** none.
- **Root cause (this row's real defect):** the forced-draw FIFO is global
  and append-only (`om_rng_force`, `ouroboros_sim.h:305-316`); tick 5's
  sentinel draw (`0.0`, chosen to prove non-consumption) is never consumed
  at tick 5 by design, so it sits at the head of the queue. The old loop's
  blanket `[1.0, 1.0]` every tick (20 values across 10 ticks) left 18
  surplus values in the FIFO by the time ticks 9 and 12 each drew only 1 —
  those surpluses, plus the original tick-5 leftover, were all still queued
  ahead of the tick-16 `[0.0, 0.5, 0.5]` push, so tick 16's revolt-roll
  actually consumed one of the stale `1.0` surpluses (never < p, never
  fires) instead of the intended `0.0`. Root-caused with debug prints
  (`om_rng_forced_remaining` before/after each tick, plus fields) before
  editing: confirmed Revolt Crushed fired unexpectedly at tick 9 off the
  tick-5 leftover `0.0` (`0.0 <= 0.45`), consuming the wrong queue slot at
  the wrong tick. Fix: change the tick-5 sentinel value to `0.99` (still
  unconsumed at tick 5, still proves the assertion, but harmless if it
  later gets consumed downstream), let tick 9's Revolt Crushed roll consume
  that carried-forward `0.99` (fails its 0.45 probability, no fire, and now
  the FIFO is empty), then force exactly 1 fresh value at tick 12 for
  Revolt Entrenched's roll. Added `assert ... == 0` right before tick 16 to
  prove the FIFO is drained before the fresh `[0.0, 0.5, 0.5]` push.
- **Order-sensitivity:** none between the branch's bug and the contract —
  single region, single template ever in a probability trigger role
  (Regional Revolt, id 3), nothing else fires, so there is no template-id
  interleave to get wrong. The failure this row had was purely a
  test-authored FIFO-accounting bug, unrelated to `events.c`'s revolt
  position defect.
- **Branch result:** PASS.
- **Main (stub) result:** FAIL, `assert len(fired_t) == 1` gets `0` at tick
  4 already — red for the stub.

## Summary

| # | Test | Branch (B1) | Main (stub) |
|---|---|---|---|
| 1 | R-026-06 | PASS | FAIL (stub fires nothing) |
| 2 | R-027-02 | PASS | FAIL (stub, forced draws pile up unconsumed) |
| 3 | R-027-04 | PASS | FAIL (stub fires nothing) |
| 4 | R-027-06 | FAIL — revolt-roll position, clean assertion (`template_id == tid_border`, got tid_revolt) | FAIL (stub fires nothing) |
| 5 | R-027-07 | PASS | FAIL (stub, `IndexError`, pre-existing) |
| 6 | R-029-03 | PASS | FAIL (stub fires nothing) |

5 of 6 pass on the branch build with events.c's revolt-position bug still in
place; row 4 (R-027-06) is correctly still red there, at exactly the
assertion the wrong draw order breaks, and will go green once M1's leaf
reorders `evt_evaluate_triggers` to the contract's per-region sequence
(crossings, revolt roll, fired-template spawns, revolt's own spawns). All
six are red on `main`'s `events.c` stub for the stub's own reason (fires
nothing / never consumes forced draws), confirmed by rerunning the same six
ids against the repo-root `libouroboros.so` already built there.

## Addendum 2026-09-22 (push_2026-09-22): R-027-06 tick-12 Diplomatic Incident confound

B1-1 leaf (`origin/push/B1-1`, revolt-roll order fixed) reran this suite and
found row 4 (`test_R_027_06_its_chain_tag_equals_root`) still red there for
a second, order-independent reason: Region 1's tick-12 fixture jump
(tension 20.0 -> 45.0, to satisfy Prosperity Unrest's `tension above 40`
spawn condition) also freshly crosses Diplomatic Incident's own
fresh-trigger threshold (`tension above 35`, epic table, no spawns), so
`events_12` holds 2 records (`assert len(events_12) == 1` fails) regardless
of draw order.

**Old values (Region 1 only):** initial and tick-4 `set_region` calls used
`tension=20.0, population=50.0`; tick-4 call used `economy=60.0`.

**New values:** initial and tick-4 calls now use `tension=36.0,
population=49.0`; tick-4 call uses `economy=56.0`. Tick-12's explicit
`tension=45.0` is unchanged.

**Why:** priming tension at 36.0 (above Diplomatic Incident's 35.0) from
before the grace period marks it already breached (R-026-05), so the
tick-12 rise to 45.0 is not a fresh crossing there — confirmed this alone
insufficient by direct reproduction: Trade Boom's own effects at tick 4
(economy +2, population +1) pushed the *old* economy=60.0 to 62.0 (crossing
Cultural Renaissance's `economy above 60`) and population 50.0 to 51.0
(crossing Harvest Surplus's `population above 50`) as same-tick-effect
crossings evaluated fresh at tick 5 (R-026-07); those two templates'
effects sum to tension -4, dropping tension from 37.0 back to 33.0 at tick
5 and un-breaching Diplomatic Incident before tick 12, reproducing the same
confound one tick later. Fixed by lowering Region 1's pre-effect economy to
56.0 (Trade Boom's own fresh-trigger threshold is 55.0, so 56.0 still fires
it; its +2 effect lands at 58.0, under Cultural Renaissance's 60.0) and
population to 49.0 (Trade Boom's +1 effect lands at exactly 50.0, not above
Harvest Surplus's 50.0 threshold). Traced field-by-field with a scratch
ctypes driver against the B1-1 build calling `om_event_breached` and
`om_region_field` every tick before settling on these values; confirmed no
other table threshold sits in the intervals traversed (military held at
50.0 throughout, at but not above Military Buildup's threshold; no other
tension/economy/population threshold lies between the old and new values
and their post-tick-12 endpoints). Draw budgets are unchanged (crossing
detection consumes no draws in either fixture; the same five forced values
at tick 4 and single value at tick 12 apply).

**Verification:**
1. Red at stub (main, `events.c` stub): `test_R_027_06_its_chain_tag_equals_root`
   fails at `assert len(events_4) == 2`, gets `0` (stub fires nothing) —
   same failure mode as before this fix.
2. Green on the leaf: `git worktree add --detach /tmp/b1conf
   origin/push/B1-1` (`38cd6b3`), built `libouroboros.so`/`libouroboros_dbg.so`,
   copied the edited test file over the worktree's copy. Full S027 file: 7/7
   passed. Other five E-04 files (`test_E04_S026_*`, `test_E04_S028_*`,
   `test_E04_S029_*`, `test_E04_S030_*`, `test_E04_wiring.py`): 24/24 passed,
   unchanged. Worktree removed, `git worktree prune` run.
3. Rest of the S027 file unchanged on main: same 7 tests fail before and
   after this edit (`test_R_027_01` through `test_R_027_07`), all for the
   stub's pre-existing reasons, none newly broken.

No assertion removed, weakened, or added; rule id and docstring unchanged;
only Region 1's fixture field values changed as described above.
