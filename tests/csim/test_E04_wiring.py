"""E-04 wiring: the events step (tick steps 1-2, ALG-32..37) runs before
step 3 (factions), not after (docs/bible/algorithms.md:13-14).

Unlike the S-039 collision wiring test, this cannot yet assert on a real
step-order side effect: every csrc/events.c function is presently a STUB
(the whole E-04 card set is unbuilt -- see the R14 note in DECISIONS.md on
the E-04 re-cut), so `om_step_events` does nothing on either side of the
fault. This test proves only that the call exists and does not crash with
`OM_FEAT_EVENTS` on; the real tick-order assertion (a region's fields
reflecting a fired event's delta before step 3 ever reads them) has to wait
for a card that actually implements `om_step_events`. `control_liveness.py`
should report the control below PENDING until then, same as
`OM_BUG_COLLISION_AFTER_RESOLVE` in test_E05_S039_wiring.py.
"""
from conftest import OMBugE04, OMFeature, OMTier, set_faction, set_region


def test_R026_wiring_events_step_runs(lib, world_factory):
    w = world_factory(n_regions=1)
    lib.om_world_set_feature(w, OMFeature.EVENTS, 1)
    lib.om_world_set_feature(w, OMFeature.FACTIONS, 0)
    lib.om_world_set_feature(w, OMFeature.DRIFT, 0)
    set_region(lib, w, 0, tier=OMTier.HOME, military=50.0, economy=50.0,
               tension=0.0, population=50.0)
    tick = lib.om_world_step(w)
    assert tick == 1, "om_world_step must run with OM_FEAT_EVENTS on and return the new tick"


def test_control_events_after_factions_trips_the_detector(dbg, dbg_world_factory):
    w = dbg_world_factory(n_regions=1)
    dbg.om_debug_inject(w, OMBugE04.EVENTS_AFTER_FACTIONS)
    dbg.om_world_set_feature(w, OMFeature.EVENTS, 1)
    dbg.om_world_set_feature(w, OMFeature.FACTIONS, 1)
    dbg.om_world_set_feature(w, OMFeature.DRIFT, 0)
    set_faction(dbg, w, 0, 0, budget=0.0, confidence=5.0)
    set_region(dbg, w, 0, tier=OMTier.HOME, military=50.0, economy=50.0,
               tension=0.0, population=50.0, faction_id=0)
    tick = dbg.om_world_step(w)
    assert tick == 1, "om_world_step must still complete with the fault injected"
