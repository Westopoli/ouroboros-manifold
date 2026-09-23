# P0 rung gate scorecard

Repo: origin/main @ c6b343c (worktree /tmp/p0, detached, throwaway)
Run: 2026-09-22

## 1. E-02 / E-04 / E-05 suites

### tests/csim/test_E02_*.py
`72 passed, 4 skipped in 1.27s`
Skips (none are R_039_05/R_040_04 — those live in E-05, not E-02):
- test_E02_S015_adjacency.py:52 — R-015-03 cooperative-stance half, ABI gap (stance setter not exposed, E-06 scope)
- test_E02_S019_floor.py:29 — R-019-02 conquest-apply entry point not exposed (E-04/E-05 scope)
- test_E02_S019_floor.py:49 — R-019-04 event-apply entry point not exposed (E-04 scope)
- test_E02_S020_determinism.py:68 — R-020-02 cross-platform CI matrix, cannot run on one machine
No FAILED. **PASS** (0 failures; 4 pre-existing ABI-gap skips, unrelated to Q-039-01/Q-040-02, not flagged by the task but not failures either).

### tests/csim/test_E04_*.py
`31 passed in 0.32s`
No skips, no failures, no xfail. **PASS**.

### tests/csim/test_E05_*.py
`2 failed, 60 passed, 2 skipped, 1 xfailed in 0.58s`
Skips match expectation:
- test_E05_S039_when_everyone_wants_the_same_region.py:224 — Q-039-01 (expected)
- test_E05_S040_empires_fracture.py:150 — Q-040-02 (expected)
Xfail (documented, expected):
- test_R_040_05_e_07_creates_new_faction — "E-07 owns faction creation; turns real when E-07 block lands"

FAILED (unexpected, 2):
1. `tests/csim/test_E05_S032_every_faction_is_a_person.py::test_R_032_03_it_uses_attack_weight_0`
   First assertion line: `assert cand_1.position == pytest.approx(0.295, abs=1e-6)` — obtained 0.44, expected 0.295. position-weight blend (mean of region-value-style position score 0.44 and the fixed 0.15 term) is not being applied; raw 0.44 passed through unweighted.
2. `tests/csim/test_E05_S037_battles_have_a_shape.py::test_R_037_07_attacker_s_committed_budget_spent`
   First assertion line: `assert lib.om_faction_budget(w_tele, 0) == pytest.approx(9.0, abs=1e-6)` — obtained 30.0, expected 9.0. The same-tick re-declare (second telegraph re-evaluated after the first breakthrough within the same 3d pass) is not spending its committed budget — budget sits at 30.0 (post first attack) instead of 9.0 (post second attack's spend), i.e. the second attack in the chain never debits the faction budget.

**FAIL** — item 1 overall is FAIL because of these two unexpected E-05 failures.

## 2. E-02 controls (empty_drifts / osc_as_level) + control_liveness E-04/E-05

`tests/csim/controls/test_control_empty_drifts.py .` — **LIVE** (passed as run; catches OM_BUG_EMPTY_DRIFTS)
`tests/csim/controls/test_control_osc_as_level.py .` — **LIVE** (passed as run; catches OM_BUG_OSC_AS_LEVEL)
Both: `2 passed in 0.05s`. **PASS**.

`control_liveness.py` has no module/epic filter flag (positional file list only, default = every `test_control_*.py`). Ran it against the E-04 and E-05 control files explicitly:

```
DEAD  test_control_e04_chain_counter_unsaved.py bug=OMBugE04.CHAIN_COUNTER_UNSAVED -- both runs passed
LIVE  test_control_e04_cond_at_spawn.py bug=OMBugE04.COND_AT_SPAWN
DEAD  test_control_e04_draw_before_condition.py bug=OMBugE04.DRAW_BEFORE_CONDITION -- both runs passed
LIVE  test_control_e04_exclusion_cancels.py bug=OMBugE04.EXCLUSION_CANCELS
LIVE  test_control_e04_fires_every_tick.py bug=OMBugE04.FIRES_EVERY_TICK
LIVE  test_control_e04_no_grace_period.py bug=OMBugE04.NO_GRACE_PERIOD
LIVE  test_control_e04_noise_rerolled.py bug=OMBugE04.NOISE_REROLLED
LIVE  test_control_e04_sequential_deltas.py bug=OMBugE04.SEQUENTIAL_DELTAS
DEAD  test_control_e04_triggers_read_live.py bug=OMBugE04.TRIGGERS_READ_LIVE -- both runs failed
LIVE  test_control_e05_admin_roll_per_faction.py bug=OMBugE05.ADMIN_ROLL_PER_FACTION
DEAD  test_control_e05_agent_reads_live.py bug=OMBugE05.AGENT_READS_LIVE -- both runs failed
LIVE  test_control_e05_collision_max_strength.py bug=OMBugE05.COLLISION_MAX_STRENGTH
LIVE  test_control_e05_conquest_on_band.py bug=OMBugE05.CONQUEST_ON_BAND
LIVE  test_control_e05_entrench_current_tick.py bug=OMBugE05.ENTRENCH_CURRENT_TICK
LIVE  test_control_e05_friction_counts_trade.py bug=OMBugE05.FRICTION_COUNTS_TRADE
DEAD  test_control_e05_garrison_before_damage.py bug=OMBugE05.GARRISON_BEFORE_DAMAGE -- both runs failed
LIVE  test_control_e05_inject_ignored.py bug=OMBugE05.INJECT_IGNORED
LIVE  test_control_e05_same_tick_redeclare.py bug=OMBugE05.SAME_TICK_REDECLARE
LIVE  test_control_e05_surprise_on_defense.py bug=OMBugE05.SURPRISE_ON_DEFENSE
DEAD  test_control_e05_telegraph_after_reinforce.py bug=OMBugE05.TELEGRAPH_AFTER_REINFORCE -- both runs failed
LIVE=14 DEAD=6 ERROR=0 total=20 elapsed=0.6s mean=31ms/control
```

6 DEAD, two flavors:
- "both runs passed" (control does NOT catch its planted bug — false negative): chain_counter_unsaved, draw_before_condition — 2 controls
- "both runs failed" (control itself is broken regardless of the bug — test defect, not a live/dead-detector question): triggers_read_live, agent_reads_live, garrison_before_damage, telegraph_after_reinforce — 4 controls

**FAIL** on the E-04/E-05 control-liveness sub-item — 6/20 controls are not doing their job (2 false-negative, 4 broken-as-written). The named empty_drifts/osc_as_level pair itself is clean (PASS).

## 3. Trace budget

Runner: `scripts/specfactory/checksum_trace.py` (the closest match — `tests/qa/t1/run_trace.py` exists but has no `--seed` flag and is PX-4's bug-detector runner, not a general seed/region/tick trace tool; `checksum_trace.py`'s `run` subcommand is built for exactly this: `--lib --seed --regions --ticks`, prints a checksum every cadence tick plus a final line).

Command: `checksum_trace.py --lib libouroboros.so --seed 1 --regions 60 --ticks 5000`
Wall time (GNU time): `0:00.15` (150 ms)
Final checksum: `8710676069373506828`

**PASS** — 150ms, far under the 60s target.

## 4. Compiler variance (O0 vs O2)

Built `build/O0/libouroboros.so` and `build/O2/libouroboros.so` via the Makefile's dedicated targets (always -O0 / always -O2 regardless of top-level OPT).
Task line omitted `--regions`, which the script requires; used `--regions 60` (same value as item 3) for both.

`checksum_trace.py --lib build/O0/libouroboros.so --seed 1 --regions 60 --ticks 500` -> final `12966767929705903382`
`checksum_trace.py --lib build/O2/libouroboros.so --seed 1 --regions 60 --ticks 500` -> final `12966767929705903382`
`checksum_trace.py --compare` -> `MATCH IDENTICAL (50 cadence rows, final=12966767929705903382)`

**PASS**.

## 5. Determinism (repeat run, same seed)

Two invocations of `checksum_trace.py --lib libouroboros.so --seed 1 --regions 60 --ticks 5000`:
Run 1 final: `8710676069373506828`
Run 2 final: `8710676069373506828`
`checksum_trace.py --compare` -> `MATCH IDENTICAL (500 cadence rows, final=8710676069373506828)`

**PASS**.

## 6. Lint gates

`alg_constants.py --lint csrc` -> `CONSTANTS LINT OK (100 table literals exempted)` exit 0
`libm_lint.py csrc` -> `LIBM LINT OK` exit 0

**PASS**.

---

## Scorecard summary

| # | Item | Result | Evidence |
|---|------|--------|----------|
| 1 | E-02/E-04/E-05 suites | **FAIL** | E-05: 2 unexpected FAILED (test_R_032_03, test_R_037_07); E-02 31/31 clean; E-04 31/31 clean |
| 2 | E-02 controls (empty_drifts/osc_as_level) LIVE | PASS | both `.` / LIVE, 2 passed in 0.05s |
| 2b | control_liveness E-04/E-05 | **FAIL** | LIVE=14 DEAD=6 (2 false-negative, 4 broken-as-written) of 20 |
| 3 | Trace budget (seed 1, 60 regions, 5000 ticks) | PASS | 0.15s wall, final checksum 8710676069373506828 |
| 4 | Compiler variance O0 vs O2 | PASS | both finals 12966767929705903382, MATCH IDENTICAL |
| 5 | Determinism (repeat same seed) | PASS | both finals 8710676069373506828, MATCH IDENTICAL |
| 6 | alg_constants + libm_lint | PASS | CONSTANTS LINT OK / LIBM LINT OK |

**Gate 2 is not clean.** Two real regressions in E-05 (S-032 position weighting, S-037 same-tick re-declare budget spend) and 6 dead controls in the E-04/E-05 control set block attach.
