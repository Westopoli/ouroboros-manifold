"""E-11 wiring: the tactical orchestrator (decision 3, two-day-push brief)
runs once, after every strategic step, when OM_FEAT_TACTICAL is on -- never
before them.

Like the E-04 wiring test, `om_tactical_step` (csrc/unit.c) is presently a
STUB -- the whole E-11 card set (B10) is unbuilt -- so the call has no
observable side effect on either side of the fault. This test proves only
that the call exists, is reachable both directly and through
`om_world_step`, and does not crash with OM_FEAT_TACTICAL on (with every
strategic feature also on, so "after every strategic step" is exercised, not
just the drift-only path); the real tick-order assertion (tactical state
reflecting the strategic tick's own writes) has to wait for card B10.
`control_liveness.py` should report the control below PENDING until then,
same as OM_BUG_EVENTS_AFTER_FACTIONS in test_E04_wiring.py.
"""
from conftest import OMBugE11, OMFeature, OMTier, set_region


def test_R_wiring_tactical_step_is_callable(lib, world_factory):
    w = world_factory(n_regions=1)
    tick = lib.om_tactical_step(w)
    assert tick == 0, "the STUB om_tactical_step must not crash and returns 0 until card B10 lands"


def test_R_wiring_tactical_step_runs_after_strategic(lib, world_factory):
    w = world_factory(n_regions=1)
    for feat in (OMFeature.EVENTS, OMFeature.FACTIONS, OMFeature.FRICTION,
                 OMFeature.ADMIN_REVOLTS, OMFeature.DIPLOMACY, OMFeature.TECHNOLOGY,
                 OMFeature.DRIFT, OMFeature.LIFECYCLE, OMFeature.TACTICAL):
        lib.om_world_set_feature(w, feat, 1)
    set_region(lib, w, 0, tier=OMTier.HOME, military=50.0, economy=50.0,
               tension=0.0, population=50.0)
    tick = lib.om_world_step(w)
    assert tick == 1, "om_world_step must run with every strategic feature plus OM_FEAT_TACTICAL on"


def test_control_tactical_before_strategic_trips_the_detector(dbg, dbg_world_factory):
    w = dbg_world_factory(n_regions=1)
    dbg.om_debug_inject(w, OMBugE11.TACTICAL_BEFORE_STRATEGIC)
    dbg.om_world_set_feature(w, OMFeature.TACTICAL, 1)
    dbg.om_world_set_feature(w, OMFeature.DRIFT, 1)
    set_region(dbg, w, 0, tier=OMTier.HOME, military=50.0, economy=50.0,
               tension=0.0, population=50.0)
    tick = dbg.om_world_step(w)
    assert tick == 1, "om_world_step must still complete with the fault injected"
