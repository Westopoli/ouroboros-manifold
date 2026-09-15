"""Positive control for OM_BUG_NOISE_REROLLED (om_bug_e04 = 201).

Watch-for (docs/bible/epics/E-04-events-and-chains.md, "Ways this could be
wrong"): "Noise re-rolled every tick or never rolled, so all regions share
one personality." (R-026-04, ALG-32.)

Reuses the exact fixture from test_E04_S026_crises_start_when_a_line_is_crossed.py's
test_R_026_04_each_region_threshold_template_pair (roll noise once at jump
start, then confirm every (region, template) offset persists unchanged across
ten ticks) against the debug build with OM_BUG_NOISE_REROLLED injected, and
asserts the detector now trips: at least one (region, template) offset
changes value on some tick after the initial roll, which R-026-04 forbids of
a correct build.
"""
from conftest import (
    OMBugE04,
    OMTier,
    isolate_events,
    load_launch_events,
    set_owner,
    set_region,
    set_tech_multipliers,
    template_id,
)


def test_control_noise_rerolled_trips_the_detector(dbg, dbg_world_factory):
    w = dbg_world_factory(n_regions=3, seed=42)
    isolate_events(dbg, w)
    load_launch_events(dbg, w)

    tid = template_id(dbg, w, "Garrison Collapse")  # a threshold template

    for r in range(3):
        set_region(dbg, w, r, tier=OMTier.HOME, military=40.0, economy=48.0, tension=20.0, population=45.0)
        set_owner(dbg, w, r, 0, held_since=-1)
    set_tech_multipliers(dbg, w, 0, 1.0, 1.0, 1.0)
    dbg.om_debug_inject(w, OMBugE04.NOISE_REROLLED)

    # When noise offsets are rolled at time jump start.
    dbg.om_event_roll_noise(w)
    initial = {r: dbg.om_event_noise(w, r, tid) for r in range(3)}

    # A clean build holds these offsets fixed for the whole jump (R-026-04).
    # A build with OM_BUG_NOISE_REROLLED injected changes at least one of
    # them on a later tick (re-rolled every tick instead of once per jump).
    changed = False
    for _ in range(10):
        dbg.om_world_step(w)
        for r in range(3):
            if abs(dbg.om_event_noise(w, r, tid) - initial[r]) > 1e-9:
                changed = True

    assert changed, (
        "OM_BUG_NOISE_REROLLED injected but every (region, template) noise "
        "offset still matched its value from the start of the jump after ten "
        "ticks -- the noise-persistence detector did not trip"
    )
