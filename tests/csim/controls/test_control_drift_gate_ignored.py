# spec: docs/legacy/test_specs/drift-gate-and-green-check.md::Acceptance criteria::AC-1
"""Positive control for OM_BUG_DRIFT_GATE_IGNORED.

Watch-for: "Drift runs regardless of the OM_FEAT_DRIFT switch" (E-02 epic,
"Ways this could be wrong"), the exact card-202b2 / 2026-09-17 harness
defect: sim.c ran the drift loop unconditionally.

Clean expectation: R-160-01, a region with DRIFT off is byte-identical
after one tick.

Reuses the R-160-01 fixture against the debug build with
OM_BUG_DRIFT_GATE_IGNORED injected, and asserts the detector now trips: at
least one field moves even though the switch is off.
"""
from conftest import OMBug, OMFeature, OMField, OMTier, set_region


def test_control_drift_gate_ignored_trips_the_gate_detector(dbg, dbg_world_factory):
    w = dbg_world_factory(n_regions=1)
    dbg.om_world_set_feature(w, OMFeature.DRIFT, 0)
    set_region(dbg, w, 0, tier=OMTier.HOME, military=42.0, economy=66.0,
               tension=18.0, population=60.0)
    dbg.om_debug_inject(w, OMBug.DRIFT_GATE_IGNORED)
    dbg.om_world_step(w)

    fields_changed = any(
        dbg.om_region_field(w, 0, f) != v
        for f, v in ((OMField.MILITARY, 42.0), (OMField.ECONOMY, 66.0),
                     (OMField.TENSION, 18.0), (OMField.POPULATION, 60.0))
    )
    assert fields_changed, (
        "OM_BUG_DRIFT_GATE_IGNORED injected but the region's fields are "
        "unchanged -- the drift-gate detector did not trip"
    )
