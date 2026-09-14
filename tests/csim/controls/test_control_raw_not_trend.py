"""Positive control for OM_BUG_RAW_NOT_TREND.

Watch-for: "Raw-vs-trend read -- a coupling term computed from the raw
oscillated field instead of the trend."

Reuses the exact fixture from test_E02_S018_oscillation.py's
test_R_018_03_coupling_reads_trend_not_raw (a known non-zero previous-tick
oscillator value, with the raw field engineered so the trend e' is exactly
60.0) against the debug build with OM_BUG_RAW_NOT_TREND injected, and
asserts the detector now trips: the overcap leg no longer matches the
trend-based expectation of -2.625.
"""
from conftest import ECON_AMPLITUDE, ECON_PERIOD, OMBug, OMTier, osc, read_drift, set_region


def test_control_raw_not_trend_trips_the_trend_detector(dbg, dbg_world_factory):
    econ_phase = 0.0
    w = dbg_world_factory(n_regions=1)
    set_region(dbg, w, 0, tier=OMTier.HOME, military=50.0, economy=50.0,
               tension=0.0, population=50.0, econ_phase=econ_phase)
    dbg.om_debug_inject(w, OMBug.RAW_NOT_TREND)
    dbg.om_world_step(w)  # tick 1

    osc_prev = osc(dbg, ECON_AMPLITUDE, ECON_PERIOD, econ_phase, 1)
    raw_at_tick_two = 60.0 + osc_prev
    set_region(dbg, w, 0, tier=OMTier.HOME, military=50.0, economy=raw_at_tick_two,
               tension=0.0, population=50.0, econ_phase=econ_phase)

    dbg.om_world_step(w)  # tick 2: trend e' should be 60.0 if trend is read correctly
    _, row = read_drift(dbg, w, 0)

    assert abs(row.economy_overcap - (-2.625)) > 1e-6, (
        "OM_BUG_RAW_NOT_TREND injected but overcap still matches the "
        "trend-based expectation of -2.625 -- the raw-vs-trend detector did "
        "not trip"
    )
