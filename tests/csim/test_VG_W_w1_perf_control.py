"""Positive control for the 600-walker perf test (TD-VG-W-5, DRAFT-perf-repeats 7, Architect 2026-10-14): the min-of-7
measurement of test_VG_W_w1_planner.py::test_C_a_tick_with_600_walkers_costs_less_than_the_draft still catches a real
slowdown. A busy-wait is injected into the timed step (no csrc change, no sleep); every repeat must come out above the
threshold, so the minimum cannot slip under it. 5 ms against 3 ms (the W2 draft); 10 ms against the W1 draft (10 ms)
because the W1 draft is 10 ms, not 3 ms, and a 5 ms wait cannot trip it.
"""
import pytest

import test_VG_W_w1_planner as w1
from test_VG_W_w2_routes import DRAFT_WALK_TICK_MS_W2


@pytest.mark.parametrize("inject_ms, threshold_ms", [
    (5.0, DRAFT_WALK_TICK_MS_W2),
    (w1.DRAFT_WALK_TICK_MS_W1, w1.DRAFT_WALK_TICK_MS_W1),
])
def test_perf_minimum_of_seven_fails_with_injected_busy_wait(lib, world_factory, inject_ms, threshold_ms):
    medians, marchings = w1.perf_repeats_ms(lib, world_factory, inject_ms=inject_ms)
    print("control: %.1f ms injected, medians (ms): %s" % (inject_ms, ", ".join("%.3f" % m for m in medians)))
    assert len(medians) == w1.DRAFT_PERF_REPEATS
    over = [m for m in medians if m >= threshold_ms]
    assert len(over) == len(medians), "only %d of %d repeats exceed %.1f ms: %s" % (len(over), len(medians), threshold_ms, medians)
    assert min(medians) >= threshold_ms
