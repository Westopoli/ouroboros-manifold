"""E-07 wiring: the lifecycle step (tick step 6, "zombie faction cleanup",
docs/bible/algorithms.md:28) runs after drift (step 5), not before it.

Like the E-04 wiring test, `om_step_lifecycle` (csrc/lifecycle.c) is presently
a STUB -- the whole E-07 card set is unbuilt -- so the call has no observable
side effect on either side of the fault. This test proves only that the call
exists and does not crash with OM_FEAT_LIFECYCLE on; the real tick-order
assertion (a faction's state reflecting drift before lifecycle ever reads it)
has to wait for card B6. `control_liveness.py` should report the control
below PENDING until then, same as OM_BUG_EVENTS_AFTER_FACTIONS in
test_E04_wiring.py.
"""
from conftest import OMBugE07, OMFeature, OMTier, set_region


def test_R_wiring_lifecycle_step_runs(lib, world_factory):
    w = world_factory(n_regions=1)
    lib.om_world_set_feature(w, OMFeature.LIFECYCLE, 1)
    lib.om_world_set_feature(w, OMFeature.DRIFT, 0)
    set_region(lib, w, 0, tier=OMTier.HOME, military=50.0, economy=50.0,
               tension=0.0, population=50.0)
    tick = lib.om_world_step(w)
    assert tick == 1, "om_world_step must run with OM_FEAT_LIFECYCLE on and return the new tick"


def test_control_lifecycle_before_drift_trips_the_detector(dbg, dbg_world_factory):
    w = dbg_world_factory(n_regions=1)
    dbg.om_debug_inject(w, OMBugE07.LIFECYCLE_BEFORE_DRIFT)
    dbg.om_world_set_feature(w, OMFeature.LIFECYCLE, 1)
    dbg.om_world_set_feature(w, OMFeature.DRIFT, 1)
    set_region(dbg, w, 0, tier=OMTier.HOME, military=50.0, economy=50.0,
               tension=0.0, population=50.0)
    tick = dbg.om_world_step(w)
    assert tick == 1, "om_world_step must still complete with the fault injected"
