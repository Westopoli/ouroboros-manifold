"""E-03 (docs/bible/epics/E-03-world-generation.md), "## Scale requirements":
"Confirmed by Westley, 2026-09-15 (never loosened by Agora; a miss is
escalated): generate a 110-region world in under 5 ms; generation is O(N + E).
Re-timed from the original 60-region figure (2026-09-14) after the
region-count range widened to [60, 110] folding Q-021-04 ... 110 is the new
range's max, per Q-021-05."
"""
from ._scale_helpers import (
    assert_budget,
    assert_control_violates_budget,
    gen_set_faction_count,
    gen_set_region_range,
    median_ns,
    raw_world,
)

N_REGIONS = 110
CONTROL_N_REGIONS = 1100
BUDGET_NS = 5_000_000  # 5 ms
SEED = 2026091501


def _timed_generate(lib, n_regions, seed):
    w = raw_world(lib, 0, seed, features=[])
    gen_set_region_range(lib, w, n_regions, n_regions)
    gen_set_faction_count(lib, w, 15)
    import time
    t0 = time.perf_counter_ns()
    lib.om_world_generate(w)
    t1 = time.perf_counter_ns()
    ok = lib.om_world_generated(w)
    lib.om_world_free(w)
    return ok, t1 - t0


def test_e03_generate_110_region_world_under_5ms(lib):
    samples = []
    for i in range(105):
        ok, dt = _timed_generate(lib, N_REGIONS, SEED + i)
        assert ok, f"world generation failed (feasibility) for seed {SEED + i}"
        if i >= 5:
            samples.append(dt)
    samples.sort()
    med = samples[len(samples) // 2]
    assert_budget(med, BUDGET_NS, f"E-03 generate({N_REGIONS} regions)")


def test_control_e03_10x_regions_violates_tightened_budget(lib):
    ok, dt = _timed_generate(lib, CONTROL_N_REGIONS, SEED + 9999)
    assert ok, "world generation failed (feasibility) for the 10x control"
    assert_control_violates_budget(dt, BUDGET_NS, f"E-03 control, generate({CONTROL_N_REGIONS} regions)")
