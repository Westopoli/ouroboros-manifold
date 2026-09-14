"""Positive control for OM_BUG_EMPTY_DRIFTS.

Watch-for: "Empty-region drift -- any drift delta on an empty-tier region."
Clean expectation: R-012-07, all four fields stay 0 forever.

Reuses the R-012-07 fixture against the debug build with OM_BUG_EMPTY_DRIFTS
injected, and asserts the detector now trips: at least one field moves off
zero after a tick.
"""
from conftest import OMBug, OMField, OMTier, set_region


def test_control_empty_drifts_trips_the_empty_region_detector(dbg, dbg_world_factory):
    w = dbg_world_factory(n_regions=1)
    set_region(dbg, w, 0, tier=OMTier.EMPTY, military=0.0, economy=0.0,
               tension=0.0, population=0.0)
    dbg.om_debug_inject(w, OMBug.EMPTY_DRIFTS)
    dbg.om_world_step(w)

    fields_changed = any(
        dbg.om_region_field(w, 0, f) != 0.0
        for f in (OMField.MILITARY, OMField.ECONOMY, OMField.TENSION, OMField.POPULATION)
    )
    assert fields_changed, (
        "OM_BUG_EMPTY_DRIFTS injected but the empty region's fields are "
        "still all zero -- the empty-region-never-drifts detector did not trip"
    )
