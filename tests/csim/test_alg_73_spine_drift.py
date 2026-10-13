"""ALG-73 Spine drift (docs/bible/algorithms.md; E-15 R-130-01).

ALG-73: "A drifting node (types objective, reinforcement_structure) with waypoints w[0..n-1], period P, mode: at
t = tick mod P, ping-pong splits P into 2(n-1) equal segments out and back, loop into n segments around, and the
position is the linear interpolation within the current segment."

The expected position is computed in the test from that sentence (the same arithmetic as simulation/spine_drift.py,
which the C port keeps verbatim per docs/northstar/PLAN.md Stage 1) and compared with om_drift_interpolate at every
quarter of the period, for 2, 3 and 4 waypoints. Positive control: a deliberately wrong reference (loop computed as a
sawtooth over n-1 segments) disagrees with the right reference at a sampled tick, so the grid can tell the two apart.
Finding SL-C3-07 (loop mode) is in docs/northstar/plans/sim_lane_2026-10-12/findings/alg_c3.md.
"""
import ctypes

import pytest

PING_PONG, LOOP = 0, 1


class _Vec2(ctypes.Structure):
    _fields_ = [("x", ctypes.c_double), ("y", ctypes.c_double)]


WAYPOINTS = {
    2: [(0.0, 0.0), (100.0, 100.0)],
    3: [(0.0, 0.0), (300.0, 0.0), (300.0, 600.0)],
    4: [(0.0, 0.0), (400.0, 0.0), (400.0, 400.0), (0.0, 800.0)],
}


def _expected(wps, period, mode, tick):
    t = tick % period
    n = len(wps)
    if mode == PING_PONG:
        segs = 2 * (n - 1)
        seg_len = period / segs
        i = min(int(t / seg_len), segs - 1)
        f = (t - i * seg_len) / seg_len
        if i < n - 1:
            a, b = wps[i], wps[i + 1]
        else:
            back = i - (n - 1)
            a, b = wps[n - 1 - back], wps[n - 2 - back]
    else:
        seg_len = period / n
        i = min(int(t / seg_len), n - 1)
        f = (t - i * seg_len) / seg_len
        a, b = wps[i], wps[(i + 1) % n]
    return a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f


def _c_position(lib, wps, period, mode, tick):
    arr = (_Vec2 * len(wps))(*[_Vec2(x, y) for x, y in wps])
    out = _Vec2()
    lib.om_drift_interpolate(arr, len(wps), period, mode, tick, ctypes.byref(out))
    return out.x, out.y


def _grid(period):
    return [0, period // 8, period // 4, period // 2 - 1, period // 2, 3 * period // 4, period - 1, period + 37, 3 * period + 5]


@pytest.mark.parametrize("n", [2, 3, 4])
def test_ALG_73_ping_pong_splits_the_period_into_2_n_minus_1_segments_out_and_back(lib, n):
    period = 240
    for tick in _grid(period):
        assert _c_position(lib, WAYPOINTS[n], period, PING_PONG, tick) == pytest.approx(
            _expected(WAYPOINTS[n], period, PING_PONG, tick)), f"n={n} tick={tick}"


@pytest.mark.parametrize("n", [2, 3, 4])
def test_ALG_73_loop_splits_the_period_into_n_segments_around_and_closes_on_the_first_waypoint(lib, n):
    period = 240
    for tick in _grid(period):
        assert _c_position(lib, WAYPOINTS[n], period, LOOP, tick) == pytest.approx(
            _expected(WAYPOINTS[n], period, LOOP, tick)), f"n={n} tick={tick}"


def test_control_ALG_73_the_reference_tells_loop_from_a_sawtooth_and_from_ping_pong(lib):
    wps, period = WAYPOINTS[2], 100
    right_loop = _expected(wps, period, LOOP, 50)
    sawtooth = (50.0, 50.0)  # w0 + (w1 - w0) * t / P: the wrong (n-1)-segment reading
    assert right_loop == pytest.approx((100.0, 100.0))
    assert right_loop != pytest.approx(sawtooth)
    # ping-pong and loop coincide for two waypoints, so both modes are expected to agree there:
    assert _expected(wps, period, PING_PONG, 25) == pytest.approx(_expected(wps, period, LOOP, 25))
