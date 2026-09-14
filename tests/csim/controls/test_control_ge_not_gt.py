"""Positive control for OM_BUG_GE_NOT_GT.

Watch-for: "Threshold direction -- a boundary case decided with >= where the
source uses > (economy 20.0, 11.0, 15.0)." Uses the R-013-04 recruitment
threshold (economy strictly greater than 20.0, ALG-03).

Reuses the R-013-04 differential fixture (economy exactly 20.0 must recruit
the same as economy 0.0, since the eco-scaled term must be excluded) against
the debug build with OM_BUG_GE_NOT_GT injected, and asserts the detector now
trips: at economy 20.0 the eco-term is wrongly included, so recruit no
longer matches the baseline-only expectation.
"""
from conftest import OMBug, OMTier, read_drift, set_region


def test_control_ge_not_gt_trips_the_threshold_detector(dbg, dbg_world_factory):
    w = dbg_world_factory(n_regions=2)
    set_region(dbg, w, 0, tier=OMTier.HOME, military=50.0, economy=0.0,
               tension=0.0, population=50.0)
    set_region(dbg, w, 1, tier=OMTier.HOME, military=50.0, economy=20.0,
               tension=0.0, population=50.0)
    dbg.om_debug_inject(w, OMBug.GE_NOT_GT)
    dbg.om_world_step(w)

    _, baseline = read_drift(dbg, w, 0)
    _, at_threshold = read_drift(dbg, w, 1)

    assert abs(at_threshold.military_recruit - baseline.military_recruit) > 1e-9, (
        "OM_BUG_GE_NOT_GT injected but recruit at economy==20.0 still matches "
        "the baseline-only expectation -- the >=-vs-> threshold detector did "
        "not trip"
    )
