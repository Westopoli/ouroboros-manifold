# PX-04 — T1 detectors on the C trace (proving the factory)

Run 2026-09-21 (`tests/qa/t1/detectors.py`, `tests/qa/t1/run_trace.py`, `tests/qa/t1/test_detectors.py`, 16 tests, whole `tests/qa/t1/` 20 tests green). Claim (Factory, "Oracles"): T1 trace detectors and invariants over the trace API are an oracle class for the sim from rung P0, with `OM_BUG_*` builds as positive controls.

Result: **pass**, with two real defects found and fixed in the detectors themselves before trusting either control — the process the "no stink" and "a check that cannot fail is a defect" rules exist for.

## Two detectors, over `om_trace_row` (`csrc/ouroboros_sim.h:81-95`)

1. **`empty_region_drifted`**: a region the caller built EMPTY (fixture ground truth, not the trace's own `tier` field — see below) whose fields moved. R-012-07's clean-build guarantee; `OM_BUG_EMPTY_DRIFTS`'s positive control.
2. **`oscillator_as_level`**: some `period`-tick window of `drift.<field>_osc_delta` sums to more than `1e-6` away from zero — the oscillator behaving as a level shift instead of a zero-mean delta (ALG-01, `docs/bible/algorithms.md:35`). `OM_BUG_OSC_AS_LEVEL`'s positive control.

`Finding`/`fingerprint`/`run_all` mirror the archived probe-C RTS suite's own shape (`~/Projects/agora/runs/101-probe-a-toy-drift-20260910-1521/worktree/probe_c/detectors/rts.py:21,99` — `Finding(kind, id, tick, detail)`, `fingerprint()` strips digits from `"kind:sorted(detail keys)"` for stable dedup, `run_all()` returns `{detector_name: [Finding, ...]}`), not its movement rules — the C sim has no units yet, so rubberband/stuck/backwards/dropped_order have no equivalent; these two are what the trace API actually supports today.

`run_trace.py` builds a real 60-region world through ctypes (`om_world_new`/`om_region_set`, mirroring `tests/csim/test_E02_gate_drift_trajectory.py`'s own `_build_60_region_world` fixture shape, plus one region forced EMPTY and one forced HOME with a live oscillator phase for the two controls), enables the trace, steps a fixed tick count, reads rows, and calls `run_all()`. Works both as a pytest fixture consumer and standalone (`python run_trace.py --bug empty_drifts`).

## Two real defects found while building this, both fixed before trusting the controls

**1. Reusing economy's 15-tick window for tension is a false positive — tension's own oscillator period is 18, not 15.** `oscillation_as_level`'s first draft hardcoded the window size from `tests/csim/controls/test_control_osc_as_level.py`'s own inline check (which only ever tests `economy_osc_delta`). Generalizing it naively to `tension_osc_delta` fired on **every single region of a genuinely clean, un-injected release build** (59/59 in a 60-region run) — not a sim defect: ALG-01 (`docs/bible/algorithms.md:35`) states economy's period is `ECON_OSCILLATION_PERIOD = 15` and tension's is `TENSION_OSCILLATION_PERIOD = 18`; a 15-tick window over an 18-tick sine cycle does not sum to zero even under correct code. Fixed by parameterizing `period` per field (`_OSC_FIELDS = {"economy_osc_delta": 15, "tension_osc_delta": 18}`) and adding a unit test (`test_oscillation_as_level_period_must_match_the_fields_own_period`) that proves the same clean signal is a false positive under period=15 and silent under period=18 — a positive control for the detector's own correctness, not just for the sim bug.

**2. `OM_BUG_EMPTY_DRIFTS` promotes the region's live tier from EMPTY to FRONTIER within its first drifting tick — gating on `row.tier == EMPTY` misses the bug entirely, on BOTH builds.** Confirmed directly: `om_region_tier(w, 0)` reads `0` (EMPTY) immediately after `om_debug_inject`, then `1` (FRONTIER) after exactly one `om_world_step`. Worse, on the **clean** release build an EMPTY-tier region produces **zero trace rows at all** — the trace simply never records it (confirmed: `om_trace_len` for 60 regions × 1 tick is 59, not 60). So a detector filtering `if row.tier != EMPTY: continue` sees nothing to check on the clean build (vacuously silent — looks like a pass) and, once the bug promotes the tier mid-run, ALSO sees nothing to check on the planted build (the one row that exists no longer matches the filter — also silent). **This is exactly the "a check that cannot fail is a defect" failure mode the project's Tests-are-the-spec rule warns about**, caught empirically before it shipped: the first version of `empty_region_drifted` reported **zero findings on the planted `OM_BUG_EMPTY_DRIFTS` build**. Fixed by gating on the caller's own fixture ground truth (`empty_region_indices`, supplied by whoever built the world) instead of the trace's own `tier` field, and using row PRESENCE as the first signal (a clean build's known-empty region has no rows to iterate at all; that absence is itself the correct, unremarkable state, not something this function needs to further assert).

## Results (`docs/northstar/proving_ground/evidence/px04/`)

500 ticks, 60 regions (region 0 forced EMPTY, region 1 forced HOME with a live oscillator phase, the rest a random HOME/FRONTIER mix seeded like the E-02 gate test):

| Build | `empty_region_drifted` | `oscillator_as_level` | wall |
|---|---|---|---|
| clean (release lib, no injection) | 0 findings | 0 findings | 0.0122–0.0157s |
| `OM_BUG_EMPTY_DRIFTS` (debug lib) | 2 findings, both region 0 (`economy`: tick 1 and tick 500 both happen to read 8.0, but `frozen_field` correctly flags it non-constant — the value moves throughout, e.g. ~9.7 by tick 3, per the evidence JSON's full row set, not just the endpoints the Finding's `detail` records; `tension`: 0.86→74.04, unambiguous) | 1 finding, region 0 `tension_osc_delta` (a real side effect: once the empty region starts drifting, its tension oscillator activates too, from the same root cause) | 0.0126–0.0161s |
| `OM_BUG_OSC_AS_LEVEL` (debug lib) | 0 findings | 118 findings = every non-empty region (59) × both oscillator fields | 0.0123–0.0168s |

Each detector: **fires on its own planted build, silent on the clean build, silent on the OTHER bug's build** (`test_control_empty_drifts_does_not_falsely_trip_oscillator_control`, `test_control_osc_as_level_does_not_falsely_trip_empty_region_control` — both real cross-checks, not assumed). All three cases run in ~0.01–0.02s traced-step time, ~0.04–0.08s harness time including world construction; both well under the 2s/run budget.

## Argues against the claim: R11's shadow follows the region even after tier promotion

`OM_BUG_OSC_AS_LEVEL = 0` collides with the debug build's "no bug" default (`w->inject = 0`, `csrc/region.c:17` — PX-15's finding, R11, still open). This did not corrupt PX-4's own controls (each bug is injected explicitly, and the release-lib clean baseline has no `OM_DEBUG_INJECT` code path to default at all), but it is worth restating here because `empty_region_drifted`'s finding #2 (`OM_BUG_EMPTY_DRIFTS` promoting an empty region's tier to FRONTIER) means the region also starts being subject to `OM_BUG_OSC_AS_LEVEL`'s default-active state within the SAME debug build, for the SAME region, from the SAME root cause tick — which is exactly why `oscillator_as_level` also fires once, on region 0, under `OM_BUG_EMPTY_DRIFTS` alone. Until R11 is fixed, any future T1 detector built against a debug-build world with no explicit injection is not testing a clean baseline, no matter what its own test claims to isolate.

## Trace-schema finding

Neither detector needed anything the trace API doesn't already expose (tick, region_idx, tier, the four fields, the drift sub-struct's `*_osc_delta` fields). The one real gap found is not in the schema, it's in what the schema's own `tier` field means once a bug is running: it reflects LIVE state, not the fixture's original intent, so any future trace-based detector that wants to classify rows by "what kind of region is this" must carry its own ground truth rather than trusting `row.tier` — noted here for the design lane, not fixed in the trace API (out of scope; `csrc/` is untouched by this probe).

## Design consequences

Filled by the design lane, 2026-09-21.

1. T1 detectors over `om_trace_row` are an oracle class from rung P0, as designed; the two built here join the P0 gate with their planted builds as controls.
2. R11 (bug id 0 means both "no bug" and `OSC_AS_LEVEL`) is fixed before any detector control runs on a debug build; until then the clean baseline is the release library.
3. Detector constants come from one source: the oscillator periods (15 and 18 ticks, ALG-01) are read from `algorithms.md`'s constants table by the test template, never hard-coded in a detector; the tension false positive was a constant copied from the wrong field.
4. A detector's gate condition must be shown non-vacuous on the clean build (a row it could match exists) before its planted control counts; the tier gate that was silent on both builds is the standing example.