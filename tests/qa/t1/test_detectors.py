"""PX-4: tests for detectors.py and run_trace.py.

Two layers: pure-Python unit tests over hand-built row fixtures (no .so
needed, fast, isolate the detector math itself), then real positive/negative
controls against the actual debug/release C libraries through run_trace.py
(csrc/ouroboros_sim.h's OM_BUG_EMPTY_DRIFTS and OM_BUG_OSC_AS_LEVEL), which
is what the brief's Pass criteria actually ask for: each detector fires on
its planted build and stays silent on the clean build, over 500 ticks at 60
regions, under 2s per run.
"""
from __future__ import annotations

import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import detectors as det  # noqa: E402
import run_trace as rt  # noqa: E402


# ---------------------------------------------------------------- fixtures (pure Python) --

@dataclass
class _Drift:
    economy_osc_delta: float = 0.0
    tension_osc_delta: float = 0.0


@dataclass
class _Row:
    tick: int
    region_idx: int
    military: float = 0.0
    economy: float = 0.0
    tension: float = 0.0
    population: float = 0.0
    drift: _Drift = field(default_factory=_Drift)


def _osc_rows(region_idx: int, n_ticks: int, amplitude: float, period: int, phase: float,
              *, level_bias: float = 0.0) -> list[_Row]:
    """ALG-01's own kernel (docs/bible/algorithms.md:35): osc(tick) =
    A*sin(2*pi*tick/period + phase), previous-tick value 0 at tick 1
    (R-018-02). A pure zero-mean delta sequence is provably ~0 over ANY
    `period`-consecutive-tick window regardless of phase (discrete full-
    period symmetry) -- confirmed empirically while writing this test: even
    "add the raw instantaneous osc(tick) on top of the correct delta" is
    STILL exactly zero-mean over a full-period window, because osc(tick)
    itself has the same symmetry, so that shape does not actually
    reproduce OM_BUG_OSC_AS_LEVEL's effect (the real C bug's mechanism
    plainly does break the window sum -- see the dbg-build control below,
    which reproduces it directly rather than guessing at its internals).
    `level_bias` is a deliberately simple, honest stand-in: a nonzero
    constant added to every tick's delta, which any window-sum check must
    catch by construction, without claiming to be a bit-for-bit model of
    the real bug."""
    import math
    rows = []
    prev = 0.0
    for t in range(1, n_ticks + 1):
        cur = amplitude * math.sin(2 * math.pi * t / period + phase)
        delta = (cur - prev) + level_bias
        rows.append(_Row(tick=t, region_idx=region_idx, drift=_Drift(economy_osc_delta=delta)))
        prev = cur
    return rows


# ---------------------------------------------------------------- frozen_field --

def test_frozen_field_true_when_constant():
    rows = [_Row(tick=t, region_idx=0, economy=8.0) for t in range(1, 20)]
    assert det.frozen_field(rows, "economy", window=0) is True


def test_frozen_field_false_when_it_moves():
    rows = [_Row(tick=t, region_idx=0, economy=8.0 + t) for t in range(1, 20)]
    assert det.frozen_field(rows, "economy", window=0) is False


def test_frozen_field_window_only_checks_the_tail():
    rows = [_Row(tick=t, region_idx=0, economy=(100.0 if t < 15 else 8.0)) for t in range(1, 20)]
    assert det.frozen_field(rows, "economy", window=5) is True  # last 5 rows are all 8.0
    assert det.frozen_field(rows, "economy", window=0) is False  # whole sequence moves


# ---------------------------------------------------------------- oscillation_as_level --

def test_oscillation_as_level_silent_on_a_true_zero_mean_oscillator():
    rows = _osc_rows(0, 200, amplitude=6.0, period=15, phase=0.7)
    assert det.oscillation_as_level(rows, "economy_osc_delta", period=15) is False


def test_oscillation_as_level_fires_on_a_biased_non_zero_mean_delta():
    rows = _osc_rows(0, 200, amplitude=6.0, period=15, phase=0.7, level_bias=0.05)
    assert det.oscillation_as_level(rows, "economy_osc_delta", period=15) is True


def test_oscillation_as_level_period_must_match_the_fields_own_period():
    """The real defect this probe found and fixed while building the
    detector: a period-15 window against a genuinely clean period-18
    oscillator (tension's own ALG-01 period) is a false positive, because a
    15-tick window over an 18-tick sine cycle does not sum to zero even
    when the implementation is correct. Confirms the fix -- period=18 is
    silent on the same clean signal that period=15 falsely flags."""
    rows = _osc_rows(0, 200, amplitude=2.0, period=18, phase=0.9)
    assert det.oscillation_as_level(rows, "economy_osc_delta", period=15) is True  # wrong period: false positive
    assert det.oscillation_as_level(rows, "economy_osc_delta", period=18) is False  # right period: clean


# ---------------------------------------------------------------- fingerprint --

def test_fingerprint_strips_digits_for_stable_dedup():
    a = det.Finding("empty_region_drifted", 0, 12, {"field": "economy", "first": 8.0, "last": 9.0})
    b = det.Finding("empty_region_drifted", 5, 340, {"field": "economy", "first": 1.0, "last": 2.0})
    assert det.fingerprint(a) == det.fingerprint(b)


def test_fingerprint_distinguishes_different_kinds():
    a = det.Finding("empty_region_drifted", 0, 1, {"field": "economy"})
    b = det.Finding("oscillator_as_level", 0, 1, {"osc_field": "economy_osc_delta"})
    assert det.fingerprint(a) != det.fingerprint(b)


# ---------------------------------------------------------------- run_all: empty_region_drifted --

def test_run_all_silent_when_empty_region_never_appears_in_rows():
    """The clean-build shape: an EMPTY-tier region produces zero trace rows
    at all (confirmed empirically -- see detectors.empty_region_drifted's
    own docstring), so it's simply absent from `rows`."""
    rows = [_Row(tick=t, region_idx=1, economy=50.0) for t in range(1, 10)]
    findings = det.run_all(rows, empty_region_indices=(0,))
    assert findings["empty_region_drifted"] == []


def test_run_all_fires_when_a_known_empty_region_drifted():
    rows = [_Row(tick=t, region_idx=0, economy=8.0 * t) for t in range(1, 10)]
    findings = det.run_all(rows, empty_region_indices=(0,))
    assert len(findings["empty_region_drifted"]) == 1
    assert findings["empty_region_drifted"][0].region_idx == 0


# ================================================================== real C-build controls ==
# tests/qa/t1/conftest.py loads tests/csim/conftest.py's session-scoped lib/dbg fixtures;
# these skip (not fail) if libouroboros[.so/_dbg.so] hasn't been built, same as tests/csim/.

N_REGIONS = 60
N_TICKS = 500
WALL_BUDGET_S = 2.0


def test_control_clean_release_build_is_silent(lib):
    result = rt.run_case(bug=None, n_regions=N_REGIONS, ticks=N_TICKS)
    n_findings = sum(len(v) for v in result["findings"].values())
    assert n_findings == 0, f"clean build should be silent, found: {result['findings']}"
    assert result["wall_s"] < WALL_BUDGET_S


def test_control_empty_drifts_trips_empty_region_drifted(dbg):
    result = rt.run_case(bug="empty_drifts", n_regions=N_REGIONS, ticks=N_TICKS)
    assert result["wall_s"] < WALL_BUDGET_S
    hits = result["findings"]["empty_region_drifted"]
    assert hits, "OM_BUG_EMPTY_DRIFTS injected but empty_region_drifted found nothing"
    assert all(region == 0 for _, region, _ in hits)


def test_control_osc_as_level_trips_oscillator_as_level(dbg):
    result = rt.run_case(bug="osc_as_level", n_regions=N_REGIONS, ticks=N_TICKS)
    assert result["wall_s"] < WALL_BUDGET_S
    hits = result["findings"]["oscillator_as_level"]
    assert hits, "OM_BUG_OSC_AS_LEVEL injected but oscillator_as_level found nothing"
    # every non-empty region (region 0 is the fixture's empty one) x both oscillator fields
    assert len(hits) == (N_REGIONS - 1) * 2


def test_control_empty_drifts_does_not_falsely_trip_oscillator_control(dbg):
    """Negative control the other direction: OM_BUG_EMPTY_DRIFTS is not
    OM_BUG_OSC_AS_LEVEL: the wholesale 118-hit oscillator signature from the
    osc control above must not appear here."""
    result = rt.run_case(bug="empty_drifts", n_regions=N_REGIONS, ticks=N_TICKS)
    hits = result["findings"]["oscillator_as_level"]
    assert len(hits) < 5, f"unexpectedly broad oscillator_as_level signature under empty_drifts: {hits}"


def test_control_osc_as_level_does_not_falsely_trip_empty_region_control(dbg):
    result = rt.run_case(bug="osc_as_level", n_regions=N_REGIONS, ticks=N_TICKS)
    assert result["findings"]["empty_region_drifted"] == []


def test_wall_time_budget_report(lib, dbg, capsys):
    """Not an assertion beyond the 2s budget each case already checks above
    -- prints the wall times the write-up reports, so a `-s` run surfaces
    them without re-deriving from the other tests' pass/fail alone."""
    t0 = time.perf_counter()
    clean = rt.run_case(bug=None, n_regions=N_REGIONS, ticks=N_TICKS)
    t1 = time.perf_counter()
    empty = rt.run_case(bug="empty_drifts", n_regions=N_REGIONS, ticks=N_TICKS)
    t2 = time.perf_counter()
    osc = rt.run_case(bug="osc_as_level", n_regions=N_REGIONS, ticks=N_TICKS)
    t3 = time.perf_counter()
    print(f"\nPX-4 wall times ({N_REGIONS} regions, {N_TICKS} ticks): "
          f"clean={clean['wall_s']}s (harness {t1 - t0:.3f}s), "
          f"empty_drifts={empty['wall_s']}s (harness {t2 - t1:.3f}s), "
          f"osc_as_level={osc['wall_s']}s (harness {t3 - t2:.3f}s)")
    assert clean["wall_s"] < WALL_BUDGET_S
    assert empty["wall_s"] < WALL_BUDGET_S
    assert osc["wall_s"] < WALL_BUDGET_S
