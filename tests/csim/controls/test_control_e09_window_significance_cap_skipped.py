"""F5 window control for csrc/chronicle.c (E-09, wave 2 card B8).

Rule (docs/bible/algorithms.md ALG-50 "Significance"): "base = tier +
min(|delta|_sum / SIGNIFICANCE_DELTA_SCALE(50.0), SIGNIFICANCE_DELTA_CAP(3.0))."
With tier=2 and delta_sum=400.0: |delta|/50 = 8.0, capped to 3.0, so
base = 2 + 3.0 = 5.0.

PLANT: under OM_BUG_SIGNIFICANCE_CAP_SKIPPED, om_chronicle_score_base skips
the SIGNIFICANCE_DELTA_CAP clamp and uses the raw ratio: base = 2 + 8.0 = 10.0.
"""
import pytest

from conftest import OMBugE09


def test_control_significance_cap_skipped_trips_the_detector(dbg, dbg_world_factory):
    w = dbg_world_factory(n_regions=1)
    dbg.om_debug_inject(w, OMBugE09.SIGNIFICANCE_CAP_SKIPPED)

    base = dbg.om_chronicle_score_base(w, tier=2, delta_sum=400.0)

    correct = 2 + min(400.0 / 50.0, 3.0)
    buggy = 2 + (400.0 / 50.0)
    assert base == pytest.approx(buggy, abs=1e-9), (
        f"OM_BUG_SIGNIFICANCE_CAP_SKIPPED injected but base still reads the "
        f"correctly capped {correct} instead of the uncapped {buggy} -- the "
        f"detector did not trip"
    )
