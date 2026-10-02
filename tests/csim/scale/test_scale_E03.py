"""E-03 (docs/bible/epics/E-03-world-generation.md), "## Scale requirements":
"Confirmed by Westley, 2026-09-15 (never loosened by Agora; a miss is
escalated): generate a 110-region world in under 5 ms; generation is O(N + E).
Re-timed from the original 60-region figure (2026-09-14) after the
region-count range widened to [60, 110] folding Q-021-04 ... 110 is the new
range's max, per Q-021-05."
"""
from ._scale_helpers import (
    assert_budget,
    scaled_budget_ns,
    gen_set_faction_count,
    gen_set_region_range,
    median_ns,
    raw_world,
)

N_REGIONS = 110
PLANTED_DELAY_NS = 10_000_000  # 10 ms, twice the unscaled budget
BUDGET_NS = 5_000_000  # 5 ms
SEED = 2026091501


def _timed_generate(lib, n_regions, seed, planted_delay_ns=0):
    w = raw_world(lib, 0, seed, features=[])
    gen_set_region_range(lib, w, n_regions, n_regions)
    gen_set_faction_count(lib, w, 15)
    import time
    t0 = time.perf_counter_ns()
    lib.om_world_generate(w)
    if planted_delay_ns:
        end = t0 + planted_delay_ns
        while time.perf_counter_ns() < end:
            pass
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


def test_control_e03_planted_delay_violates_tightened_budget(lib):
    """Positive control: a known delay (PLANTED_DELAY_NS busy-wait inside the timed
    window, around the same 110-region generate call) must push the measured median over
    the scaled budget the real test asserts against, proving the clock and the assertion
    are live.

    Test-defect (premise change, Architect rulings 2, A37): this control used to build
    ten times the regions (1100) and expect the clock to trip. Since the OM_MAX_REGIONS
    512 cap (A27) that world cannot exist, and at 512 the generate time sits at the
    floor and fails under load. The budget, the real workload and the helper floor are
    unchanged."""
    samples = []
    for i in range(15):
        ok, dt = _timed_generate(lib, N_REGIONS, SEED + 9999 + i, PLANTED_DELAY_NS)
        assert ok, "world generation failed (feasibility) for the planted-delay control"
        samples.append(dt)
    samples.sort()
    med = samples[len(samples) // 2]
    scaled = scaled_budget_ns(BUDGET_NS)
    print(
        f"[scale-control] E-03 planted delay: raw_median={med / 1000.0:.3f}us "
        f"scaled_budget={scaled / 1000.0:.3f}us planted={PLANTED_DELAY_NS / 1000.0:.3f}us"
    )
    assert med > scaled, (
        f"E-03 control: median {med / 1000.0:.3f}us with a planted {PLANTED_DELAY_NS / 1000.0:.3f}us "
        f"delay did not exceed the scaled budget {scaled / 1000.0:.3f}us -- the clock or the assertion is not live"
    )
