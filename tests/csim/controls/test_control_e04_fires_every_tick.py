"""Positive control for OM_BUG_FIRES_EVERY_TICK (om_bug_e04 = 200).

Watch-for (docs/bible/epics/E-04-events-and-chains.md, "Ways this could be
wrong"): "Fires every tick while past the threshold instead of on the
crossing." (R-026-02.)

Reuses the exact fixture from test_E04_S026_crises_start_when_a_line_is_crossed.py's
test_R_026_02_template_does_not_fire_again (one region whose economy crosses
above Trade Boom's 55.0 threshold once on tick 4 and then stays above it for
six more ticks) against the debug build with OM_BUG_FIRES_EVERY_TICK injected,
and asserts the detector now trips: at least one of ticks 5 through 10 logs a
second Trade Boom trigger firing for the same region, which R-026-02 forbids
of a correct build.
"""
from conftest import (
    OMBugE04,
    OMSource,
    OMTier,
    force_draws,
    isolate_events,
    load_launch_events,
    read_events,
    set_owner,
    set_region,
    set_tech_multipliers,
    template_id,
    zero_all_noise,
)


def test_control_fires_every_tick_trips_the_detector(dbg, dbg_world_factory):
    w = dbg_world_factory(n_regions=1)
    isolate_events(dbg, w)
    load_launch_events(dbg, w)
    zero_all_noise(dbg, w)

    tid_boom = template_id(dbg, w, "Trade Boom")  # economy above 55.0

    set_region(dbg, w, 0, tier=OMTier.HOME, military=40.0, economy=48.0, tension=20.0, population=45.0)
    set_owner(dbg, w, 0, 0, held_since=-1)
    set_tech_multipliers(dbg, w, 0, 1.0, 1.0, 1.0)
    force_draws(dbg, w, [1.0] * 50)
    dbg.om_debug_inject(w, OMBugE04.FIRES_EVERY_TICK)

    # Grace period: ticks 1 through 3 prime trigger state without firing.
    for _ in range(3):
        dbg.om_world_step(w)

    # Tick 4: the crossing. A clean build fires Trade Boom exactly once here.
    set_region(dbg, w, 0, tier=OMTier.HOME, military=40.0, economy=60.0, tension=20.0, population=45.0)
    dbg.om_world_step(w)

    # Ticks 5 through 10: economy stays on the far side of the threshold. A
    # clean build (R-026-02) never fires Trade Boom again while it stays past
    # threshold; a build with OM_BUG_FIRES_EVERY_TICK injected fires it every
    # tick it remains past threshold instead of only on the crossing.
    fired_again = False
    for _ in range(6):
        set_region(dbg, w, 0, tier=OMTier.HOME, military=40.0, economy=60.0, tension=20.0, population=45.0)
        dbg.om_world_step(w)
        events = read_events(dbg, w)
        if any(e.template_id == tid_boom and e.source == OMSource.TRIGGER for e in events):
            fired_again = True

    assert fired_again, (
        "OM_BUG_FIRES_EVERY_TICK injected but Trade Boom never fired a second "
        "time in region 0 while economy stayed past its threshold on ticks 5 "
        "through 10 -- the persistent-firing detector did not trip"
    )
