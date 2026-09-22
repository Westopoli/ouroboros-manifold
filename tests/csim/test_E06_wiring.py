"""E-06 wiring: diplomacy (tick step 4.25) and technology (tick step 4.5)
run after admin revolts (step 4.1) and before drift (step 5)
(docs/bible/algorithms.md:24-27).

Like the E-04 wiring test, `om_step_diplomacy` and `om_step_technology`
(csrc/diplomacy.c) are presently STUBs -- the whole E-06 card set is unbuilt
-- so neither call has any observable side effect on either side of a fault.
These tests prove only that the calls exist and that `om_world_step` does not
crash with OM_FEAT_DIPLOMACY / OM_FEAT_TECHNOLOGY on, including under the
order-swap fault; the real tick-order assertion (a region's or faction's
fields reflecting diplomacy/technology's own math relative to admin revolts
and drift) has to wait for card B5. `control_liveness.py` should report the
two controls below PENDING until then, same as OM_BUG_EVENTS_AFTER_FACTIONS
in test_E04_wiring.py.
"""
from conftest import OMBugE06, OMFeature, OMTier, set_region


def test_R_wiring_diplomacy_step_runs(lib, world_factory):
    w = world_factory(n_regions=1)
    lib.om_world_set_feature(w, OMFeature.DIPLOMACY, 1)
    lib.om_world_set_feature(w, OMFeature.TECHNOLOGY, 0)
    lib.om_world_set_feature(w, OMFeature.ADMIN_REVOLTS, 0)
    lib.om_world_set_feature(w, OMFeature.DRIFT, 0)
    set_region(lib, w, 0, tier=OMTier.HOME, military=50.0, economy=50.0,
               tension=0.0, population=50.0)
    tick = lib.om_world_step(w)
    assert tick == 1, "om_world_step must run with OM_FEAT_DIPLOMACY on and return the new tick"


def test_R_wiring_technology_step_runs(lib, world_factory):
    w = world_factory(n_regions=1)
    lib.om_world_set_feature(w, OMFeature.DIPLOMACY, 0)
    lib.om_world_set_feature(w, OMFeature.TECHNOLOGY, 1)
    lib.om_world_set_feature(w, OMFeature.ADMIN_REVOLTS, 0)
    lib.om_world_set_feature(w, OMFeature.DRIFT, 0)
    set_region(lib, w, 0, tier=OMTier.HOME, military=50.0, economy=50.0,
               tension=0.0, population=50.0)
    tick = lib.om_world_step(w)
    assert tick == 1, "om_world_step must run with OM_FEAT_TECHNOLOGY on and return the new tick"


def test_control_diplomacy_after_drift_trips_the_detector(dbg, dbg_world_factory):
    w = dbg_world_factory(n_regions=1)
    dbg.om_debug_inject(w, OMBugE06.DIPLOMACY_AFTER_DRIFT)
    dbg.om_world_set_feature(w, OMFeature.DIPLOMACY, 1)
    dbg.om_world_set_feature(w, OMFeature.DRIFT, 1)
    set_region(dbg, w, 0, tier=OMTier.HOME, military=50.0, economy=50.0,
               tension=0.0, population=50.0)
    tick = dbg.om_world_step(w)
    assert tick == 1, "om_world_step must still complete with the fault injected"


def test_control_technology_before_admin_trips_the_detector(dbg, dbg_world_factory):
    w = dbg_world_factory(n_regions=1)
    dbg.om_debug_inject(w, OMBugE06.TECHNOLOGY_BEFORE_ADMIN)
    dbg.om_world_set_feature(w, OMFeature.TECHNOLOGY, 1)
    dbg.om_world_set_feature(w, OMFeature.ADMIN_REVOLTS, 1)
    set_region(dbg, w, 0, tier=OMTier.HOME, military=50.0, economy=50.0,
               tension=0.0, population=50.0)
    tick = dbg.om_world_step(w)
    assert tick == 1, "om_world_step must still complete with the fault injected"
