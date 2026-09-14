"""Positive control for OM_BUG_OSC_AS_LEVEL.

Watch-for (docs/northstar/e2e/E-02.md QA table): "Oscillator drift -- net
oscillator contribution over any 15-tick window != 0 within 1e-6 (R-018-04);
or field drifts upward by the amplitude (oscillator added as a level)."

Reuses the exact detector from test_E02_S018_oscillation.py's
test_R_018_04_oscillator_nets_zero_over_every_15_tick_window, against the
debug build with OM_BUG_OSC_AS_LEVEL injected, and asserts the detector now
trips (finds a window whose net is not ~0).
"""
from conftest import OMBug, OMTier, OmTraceRow, set_region


def test_control_osc_as_level_trips_the_oscillator_window_detector(dbg, dbg_world_factory):
    w = dbg_world_factory(n_regions=1)
    set_region(dbg, w, 0, tier=OMTier.HOME, military=50.0, economy=50.0,
               tension=50.0, population=50.0, econ_phase=0.4, tension_phase=0.9)
    dbg.om_debug_inject(w, OMBug.OSC_AS_LEVEL)

    dbg.om_trace_enable(w, 1)
    ran = dbg.om_world_run(w, 150)
    assert ran == 150

    n = dbg.om_trace_len(w)
    rows = (OmTraceRow * n)()
    got = dbg.om_trace_read(w, 0, n, rows)
    assert got == n

    rows_sorted = sorted(rows, key=lambda r: r.tick)
    deltas = [r.drift.economy_osc_delta for r in rows_sorted]

    tripped = any(
        abs(sum(deltas[k:k + 15])) >= 1e-6
        for k in range(0, len(deltas) - 15 + 1)
    )
    assert tripped, (
        "OM_BUG_OSC_AS_LEVEL injected but every 15-tick window still nets to "
        "~0 -- the oscillator-window detector did not trip"
    )
