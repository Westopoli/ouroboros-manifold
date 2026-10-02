"""Q-021-08 (docs/northstar/ambiguity_register.md, closed 2026-09-28) and E-03 "Scale requirements":
"a time jump of 150 ticks at 400 regions completes in under 2 s". HDR5 acceptance test.

Convention (tests/csim/scale/README.md): gated behind OM_SCALE=1; the median of several runs is
compared to budget / OM_SCALE_CPU_FACTOR (the 2 s budget is for the min-spec machine; this machine
is faster by the factor, default 1.35). The budget is not widened here; a slow or loaded machine is
handled by the factor the README documents, never by editing the number.
The jump runs the real path, om_time_jump_run, the call handle_jump in csrc/pipe/om_pipe.c makes,
with the launch feature set (c_bridge.gd DEFAULT_FEATURES, ids 0-7).
"""
import ctypes
import time

from ._scale_helpers import (
    assert_budget,
    assert_control_violates_budget,
    gen_set_region_range,
)

N_REGIONS = 400
JUMP_TICKS = 150
BUDGET_NS = 2_000_000_000  # 2 s
SEED = 2026100101


def _jump_world(lib, seed):
    w = lib.om_world_new(0, seed)
    assert w, "om_world_new returned NULL"
    for feat in range(8):
        lib.om_world_set_feature(w, feat, 1)
    gen_set_region_range(lib, w, N_REGIONS, N_REGIONS)
    lib.om_world_generate(w)
    assert lib.om_world_generated(w), "400-region generation failed"
    assert lib.om_region_count(w) == N_REGIONS
    buf = (ctypes.c_uint32 * 512)()
    lib.om_region_neighbors.restype = ctypes.c_uint32
    for r in range(N_REGIONS):
        assert lib.om_region_neighbors(w, r, buf, 512) >= 1, (
            f"region {r} has no neighbors: the edge matrix is smaller than the world (HDR5 not landed)"
        )
    return w


def _timed_jump(lib, ticks, seed):
    w = _jump_world(lib, seed)
    report = ctypes.create_string_buffer(65536)
    t0 = time.perf_counter_ns()
    rc = lib.om_time_jump_run(w, ticks, report)
    dt = time.perf_counter_ns() - t0
    lib.om_world_free(w)
    assert rc == 0, "om_time_jump_run refused"
    return dt


def test_q_021_08_150_tick_jump_at_400_regions_under_2s(lib):
    """Given a 400-region world with the launch features, When 150 ticks are jumped, Then the median wall time is under 2 s (scaled by OM_SCALE_CPU_FACTOR)."""
    samples = sorted(_timed_jump(lib, JUMP_TICKS, SEED + i) for i in range(5))
    assert_budget(float(samples[len(samples) // 2]), BUDGET_NS, "Q-021-08 150-tick jump at 400 regions")


def test_control_q_021_08_the_jump_exceeds_a_hundredth_of_the_budget(lib):
    """Control: the same timer on the same jump exceeds budget/100, so the clock and the 2 s check above are live."""
    dt = _timed_jump(lib, JUMP_TICKS, SEED + 999)
    assert_control_violates_budget(float(dt), BUDGET_NS, "Q-021-08 control, 150-tick jump")
