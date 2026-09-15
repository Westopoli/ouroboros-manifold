"""Positive control for OM_BUG_NO_GRACE_PERIOD (om_bug_e04 = 202).

Watch-for (docs/bible/epics/E-04-events-and-chains.md, "Ways this could be
wrong"): "Grace period dropped, so half the map fires on tick 1."

Reuses the exact fixture from test_E04_S026_crises_start_when_a_line_is_crossed.py's
test_R_026_05_nothing_fires_trigger_state_primed (one region whose military
and economy already sit past their thresholds before the run starts) against
the debug build with OM_BUG_NO_GRACE_PERIOD injected, and asserts the
detector now trips: at least one event fires during ticks 1 through 3, which
R-026-05 forbids of a correct build (ticks 1..3 only prime trigger state).
"""
from conftest import (
    OMBugE04,
    OMTier,
    force_draws,
    isolate_events,
    load_launch_events,
    read_events,
    set_owner,
    set_region,
    set_tech_multipliers,
    zero_all_noise,
)


def test_control_no_grace_period_trips_the_detector(dbg, dbg_world_factory):
    w = dbg_world_factory(n_regions=1)
    isolate_events(dbg, w)
    load_launch_events(dbg, w)
    zero_all_noise(dbg, w)

    # Fields already past threshold at run start: military 25.0 < Garrison
    # Collapse's 30.0, economy 60.0 > Trade Boom's 55.0.
    set_region(dbg, w, 0, tier=OMTier.HOME, military=25.0, economy=60.0, tension=20.0, population=45.0)
    set_owner(dbg, w, 0, 0, held_since=-1)
    set_tech_multipliers(dbg, w, 0, 1.0, 1.0, 1.0)
    force_draws(dbg, w, [1.0] * 50)
    dbg.om_debug_inject(w, OMBugE04.NO_GRACE_PERIOD)

    # A clean build fires nothing on ticks 1 through 3 (R-026-05): it only
    # primes the breached flags from the current fields. A build with
    # OM_BUG_NO_GRACE_PERIOD injected fires immediately instead.
    fired_during_grace = False
    for _ in range(3):
        dbg.om_world_step(w)
        if read_events(dbg, w):
            fired_during_grace = True

    assert fired_during_grace, (
        "OM_BUG_NO_GRACE_PERIOD injected but ticks 1 through 3 still logged "
        "zero events even though military and economy started past their "
        "thresholds -- the grace-period detector did not trip"
    )
