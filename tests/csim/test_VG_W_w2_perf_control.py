"""Positive control for the W2 600-walker perf test (TD-VG-W-6, DRAFT-perf-repeats 7, Architect 2026-10-14): the real test
test_VG_W_w2_routes.py::test_P_a_tick_with_600_walkers_costs_less_than_the_w2_draft, run with a 5 ms busy-wait injected into
the timed step (no csrc change, no sleep), must FAIL on the 3 ms draft, and every one of its seven repeats must be over 3 ms,
so the minimum cannot slip under it. See also: test_VG_W_w1_perf_control.py (the same control on the helper itself).
"""
import pytest

import test_VG_W_w1_planner as w1
import test_VG_W_w2_routes as w2

INJECT_MS = 5.0   # clears the 3 ms draft with margin; a 5 ms wait cannot trip a threshold above it


def test_w2_perf_test_fails_with_injected_busy_wait(lib, world_factory, monkeypatch):
    seen = []
    real = w1.perf_repeats_ms

    def injected(lib_, make, repeats=w1.DRAFT_PERF_REPEATS, inject_ms=0.0):
        medians, marchings = real(lib_, make, repeats=repeats, inject_ms=INJECT_MS)
        seen.extend(medians)
        return medians, marchings

    monkeypatch.setattr(w1, "perf_repeats_ms", injected)
    with pytest.raises(AssertionError, match="DRAFT-walk-tick-ms-w2"):
        w2.test_P_a_tick_with_600_walkers_costs_less_than_the_w2_draft(lib, world_factory)
    print("control: %.1f ms injected, medians (ms): %s" % (INJECT_MS, ", ".join("%.3f" % m for m in seen)))
    assert len(seen) == w1.DRAFT_PERF_REPEATS
    assert all(m >= w2.DRAFT_WALK_TICK_MS_W2 for m in seen), seen
