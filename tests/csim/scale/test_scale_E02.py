"""E-02 (docs/bible/epics/E-02-region-fields-and-drift.md), "## Scale requirements":
"Confirmed by Westley 2026-09-14: 60 regions drift in under 50 µs per tick
total; 5,000 ticks of drift alone for 60 regions in under 0.5 s; memory per
region under 2,048 bytes, with the region connection table (a fixed 1 MB)
counted separately (raised from 256 bytes by Westley 2026-10-02, after the
audit measured about 1,609 bytes of which 1,536 are damage history). Not
loosened by Agora; a miss is escalated."

The 2,048-byte figure is a threshold change by its owner (Westley, relayed as
rulings-2 A113), not a test-defect. The memory test measures the marginal
per-region save-state cost between a 60- and a 512-region world, which cancels
the fixed 512x512 connection table (1,048,576 B) and every other fixed cost.

tests/csim/test_E02_gate_drift_trajectory.py already asserts the 5,000-tick
bulk budget as part of its combined scale/speed/behavior/determinism gate;
this file is the dedicated OM_SCALE=1 scale-suite entry for the same epic,
independent of that gate (never edited -- tests/**, other than this
directory, is fenced).
"""
import random

from ._scale_helpers import (
    OMFeature,
    OMTier,
    assert_budget,
    assert_control_violates_budget,
    median_ns,
    raw_world,
    set_region,
)

N_REGIONS = 60
CONTROL_N_REGIONS = 512
SEED = 2026091460
PER_TICK_BUDGET_NS = 50_000  # 50 us/tick total, all regions
BULK_BUDGET_NS = 500_000_000  # 0.5 s for 5,000 ticks
BYTES_PER_REGION_BUDGET = 2048


def _build(lib, n_regions, seed):
    w = raw_world(lib, n_regions, seed, features=[OMFeature.DRIFT])
    rng = random.Random(seed)
    for idx in range(n_regions):
        tier = OMTier.HOME if rng.random() < 0.5 else OMTier.FRONTIER
        set_region(
            lib, w, idx, tier=tier,
            military=rng.uniform(5.0, 90.0), economy=rng.uniform(10.0, 95.0),
            tension=rng.uniform(0.0, 80.0), population=rng.uniform(5.0, 95.0),
            econ_phase=rng.uniform(0.0, 6.28), tension_phase=rng.uniform(0.0, 6.28),
        )
    return w


def test_e02_60_regions_drift_per_tick(lib):
    w = _build(lib, N_REGIONS, SEED)
    med = median_ns(lambda: lib.om_world_step(w))
    lib.om_world_free(w)
    assert_budget(med, PER_TICK_BUDGET_NS, f"E-02 {N_REGIONS}-region drift, om_world_step")


def test_e02_5000_tick_bulk_run_under_budget(lib):
    w = _build(lib, N_REGIONS, SEED)
    import time
    t0 = time.perf_counter_ns()
    ran = lib.om_world_run(w, 5000)
    t1 = time.perf_counter_ns()
    lib.om_world_free(w)
    assert ran == 5000
    assert_budget(t1 - t0, BULK_BUDGET_NS, "E-02 5,000-tick bulk om_world_run, 60 regions")


def test_e02_memory_per_region_under_2048_bytes(lib):
    w_small = _build(lib, N_REGIONS, SEED)
    w_big = _build(lib, CONTROL_N_REGIONS, SEED)
    size_small = lib.om_save_state_size(w_small)
    size_big = lib.om_save_state_size(w_big)
    lib.om_world_free(w_small)
    lib.om_world_free(w_big)
    marginal = (size_big - size_small) / float(CONTROL_N_REGIONS - N_REGIONS)
    print(f"[scale] E-02 memory: {N_REGIONS}r={size_small}B {CONTROL_N_REGIONS}r={size_big}B marginal={marginal:.1f}B/region")
    assert marginal < BYTES_PER_REGION_BUDGET, (
        f"marginal save-state cost per region {marginal:.1f}B exceeds the {BYTES_PER_REGION_BUDGET}B budget "
        "(om_save_state_size delta between a 60- and 512-region world, divided by 452)"
    )


def test_control_e02_10x_regions_violates_tightened_budget(lib):
    w = _build(lib, CONTROL_N_REGIONS, SEED)
    med = median_ns(lambda: lib.om_world_step(w))
    lib.om_world_free(w)
    assert_control_violates_budget(med, PER_TICK_BUDGET_NS, f"E-02 control, {CONTROL_N_REGIONS} regions")
