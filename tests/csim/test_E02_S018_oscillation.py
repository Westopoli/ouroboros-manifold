"""S-018 -- Boom and bust.

R-018-01 .. R-018-05. Formula: ALG-01 (oscillator kernel) in
algorithms.md, plus the de-oscillation contract (R-018-03, the epic
invariant "Drift reads de-oscillated trend values for cross-field coupling").

Oracle oscillator values in this module are computed by calling the sim's
own om_sin (via the conftest `osc` helper), not Python's math.sin, so these
tests check the ALG-01 wiring -- delta-not-level, correct previous-tick
value, trend-not-raw coupling -- rather than sine-implementation agreement.
"""
import math

import pytest

from conftest import (
    ECON_AMPLITUDE, ECON_PERIOD, OMField, OMTier, OmTraceRow,
    TENSION_AMPLITUDE, TENSION_PERIOD, osc, read_drift, set_region,
)


def test_R_018_01_oscillator_delta_at_tick_two(lib, world_factory):
    econ_phase = 0.7
    tension_phase = 1.3
    w = world_factory(n_regions=1)
    set_region(lib, w, 0, tier=OMTier.HOME, military=50.0, economy=30.0,
               tension=20.0, population=50.0,
               econ_phase=econ_phase, tension_phase=tension_phase)
    lib.om_world_step(w)  # tick 1
    lib.om_world_step(w)  # tick 2
    _, row = read_drift(lib, w, 0)

    expected_econ = (osc(lib, ECON_AMPLITUDE, ECON_PERIOD, econ_phase, 2)
                      - osc(lib, ECON_AMPLITUDE, ECON_PERIOD, econ_phase, 1))
    expected_tension = (osc(lib, TENSION_AMPLITUDE, TENSION_PERIOD, tension_phase, 2)
                          - osc(lib, TENSION_AMPLITUDE, TENSION_PERIOD, tension_phase, 1))

    assert row.economy_osc_delta == pytest.approx(expected_econ, abs=1e-9)
    assert row.tension_osc_delta == pytest.approx(expected_tension, abs=1e-9)


def test_R_018_02_tick_one_previous_oscillator_is_zero(lib, world_factory):
    econ_phase = 2.1
    w = world_factory(n_regions=1)
    set_region(lib, w, 0, tier=OMTier.HOME, military=50.0, economy=30.0,
               tension=20.0, population=50.0, econ_phase=econ_phase)
    lib.om_world_step(w)  # tick 1
    _, row = read_drift(lib, w, 0)

    expected = osc(lib, ECON_AMPLITUDE, ECON_PERIOD, econ_phase, 1) - 0.0
    assert row.economy_osc_delta == pytest.approx(expected, abs=1e-9)


def test_R_018_03_coupling_reads_trend_not_raw(lib, world_factory):
    # Advance to tick 1 first, then hard-set a known raw economy right before
    # tick 2 so the trend e' = raw - osc(tick 1) is exactly 60 -- the raw
    # field itself is well away from 60. If overcap were computed from the
    # raw field instead of the trend, it would not match -2.625.
    econ_phase = 0.0
    w = world_factory(n_regions=1)
    set_region(lib, w, 0, tier=OMTier.HOME, military=50.0, economy=50.0,
               tension=0.0, population=50.0, econ_phase=econ_phase)
    lib.om_world_step(w)  # tick 1

    osc_prev = osc(lib, ECON_AMPLITUDE, ECON_PERIOD, econ_phase, 1)
    raw_at_tick_two = 60.0 + osc_prev
    set_region(lib, w, 0, tier=OMTier.HOME, military=50.0, economy=raw_at_tick_two,
               tension=0.0, population=50.0, econ_phase=econ_phase)

    lib.om_world_step(w)  # tick 2: trend e' = raw_at_tick_two - osc_prev = 60.0
    _, row = read_drift(lib, w, 0)

    # population 50 -> capacity 42.5; overcap = 15*(60-42.5)/100 = 2.625, signed negative.
    assert row.economy_overcap == pytest.approx(-2.625, abs=1e-6)


def test_R_018_04_oscillator_nets_zero_over_every_15_tick_window(lib, world_factory):
    w = world_factory(n_regions=1)
    set_region(lib, w, 0, tier=OMTier.HOME, military=50.0, economy=50.0,
               tension=50.0, population=50.0, econ_phase=0.4, tension_phase=0.9)
    lib.om_trace_enable(w, 1)
    ran = lib.om_world_run(w, 150)
    assert ran == 150

    n = lib.om_trace_len(w)
    assert n == 150
    rows = (OmTraceRow * n)()
    got = lib.om_trace_read(w, 0, n, rows)
    assert got == n

    rows_sorted = sorted(rows, key=lambda r: r.tick)
    deltas = [r.drift.economy_osc_delta for r in rows_sorted]

    # The window starting at tick 1 is skipped: R-018-02 (tested above) fixes
    # ALG-01's previous-tick value at 0 rather than the true osc(tick 0), so
    # that window's telescoping sum is osc(15) - 0 instead of osc(15) -
    # osc(0), off by exactly A*sin(econ_phase) regardless of implementation.
    # Every later window's endpoints are both real oscillator evaluations, so
    # the period-15 cancellation the rule is checking applies to them.
    for k in range(1, len(deltas) - 15 + 1):
        window_sum = sum(deltas[k:k + 15])
        assert abs(window_sum) < 1e-6, (
            f"15-tick window starting at tick {rows_sorted[k].tick} "
            f"sums to {window_sum}, not ~0"
        )


def test_R_018_05_different_phases_peak_on_different_ticks(lib, world_factory):
    w = world_factory(n_regions=2)
    set_region(lib, w, 0, tier=OMTier.HOME, military=50.0, economy=50.0,
               tension=20.0, population=50.0, econ_phase=0.0)
    set_region(lib, w, 1, tier=OMTier.HOME, military=50.0, economy=50.0,
               tension=20.0, population=50.0, econ_phase=math.pi)

    history_a = []
    history_b = []
    for _ in range(ECON_PERIOD):
        lib.om_world_step(w)
        history_a.append(lib.om_region_field(w, 0, OMField.ECONOMY))
        history_b.append(lib.om_region_field(w, 1, OMField.ECONOMY))

    peak_a = history_a.index(max(history_a))
    peak_b = history_b.index(max(history_b))
    assert peak_a != peak_b
