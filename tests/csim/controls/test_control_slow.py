"""Positive control for OM_BUG_SLOW.

Watch-for / scale gate (docs/northstar/e2e/E-02.md): the 60-region,
5,000-tick bulk run must finish under 0.5s total and 50 us/tick average.
This control proves the speed leg of test_E02_gate_drift_trajectory.py can
actually fail: with OM_BUG_SLOW injected, the same run must miss the budget.
"""
import time

from conftest import OMBug, OMTier, set_region


def test_control_slow_trips_the_speed_gate(dbg, dbg_world_factory):
    n_regions = 60
    n_ticks = 5000
    w = dbg_world_factory(n_regions=n_regions, seed=1)
    for idx in range(n_regions):
        set_region(dbg, w, idx, tier=OMTier.HOME, military=40.0, economy=50.0,
                   tension=20.0, population=50.0)
    dbg.om_debug_inject(w, OMBug.SLOW)

    start = time.perf_counter()
    ran = dbg.om_world_run(w, n_ticks)
    elapsed = time.perf_counter() - start
    assert ran == n_ticks

    per_tick_us = (elapsed * 1_000_000.0) / n_ticks
    assert elapsed >= 0.5 or per_tick_us >= 50.0, (
        "OM_BUG_SLOW injected but the run still finished inside the speed "
        f"budget ({elapsed:.3f}s total, {per_tick_us:.2f} us/tick) -- the "
        "speed gate did not trip"
    )
