"""Positive control for OM_BUG_COND_AT_SPAWN (om_bug_e04 = 203).

Watch-for (docs/bible/epics/E-04-events-and-chains.md, "Ways this could be
wrong"): "Spawn conditions checked at spawn time instead of at resolution
time." (R-027-02.)

Reuses the exact fixture from test_E04_S027_one_thing_leads_to_another.py's
test_R_027_02_it_dropped_without_firing_without: "Border Incursion" fires
unconditionally on tick 1 and spawns "Regional Revolt" (condition: tension
above 40.0) with its delay drawn to land on tick 4. At spawn time (tick 1)
tension is 50.0, satisfying the condition; by tick 4's tick-start fields,
tension has been moved to 30.0, failing it. Against the debug build with
OM_BUG_COND_AT_SPAWN injected, asserts the detector now trips: Regional
Revolt fires at tick 4 anyway, which R-027-02 forbids of a correct build
(the condition must be read at resolution, not carried from spawn time).
"""
from conftest import (
    OMBugE04,
    OMTier,
    force_draws,
    isolate_events,
    load_launch_events,
    queue_external,
    read_events,
    set_owner,
    set_region,
    set_tech_multipliers,
    template_id,
    zero_all_noise,
)


def test_control_cond_at_spawn_trips_the_detector(dbg, dbg_world_factory):
    w = dbg_world_factory(n_regions=1)
    isolate_events(dbg, w)
    load_launch_events(dbg, w)
    zero_all_noise(dbg, w)

    tid_border = template_id(dbg, w, "Border Incursion")  # spawns Regional Revolt [3,6] 0.60 tension above 40
    tid_revolt = template_id(dbg, w, "Regional Revolt")

    set_region(dbg, w, 0, tier=OMTier.HOME, military=50.0, economy=50.0, tension=50.0, population=50.0)
    set_owner(dbg, w, 0, 0, held_since=-1)
    set_tech_multipliers(dbg, w, 0, 1.0, 1.0, 1.0)
    dbg.om_debug_inject(w, OMBugE04.COND_AT_SPAWN)

    queue_external(dbg, w, 0, tid_border, due_tick=1, probability=1.0)

    # Tick 1: Border Incursion fires unconditionally (tension 50.0, above the
    # 40.0 the spawned Regional Revolt will require) and spawns Regional
    # Revolt with delay drawn to 3 (due tick 4), carrying that condition.
    force_draws(dbg, w, [0.1, 0.00])
    dbg.om_world_step(w)

    # Between spawn and resolution, tension drops below the condition's
    # threshold -- the field the condition must be read against at tick 4.
    set_region(dbg, w, 0, tier=OMTier.HOME, military=50.0, economy=50.0, tension=30.0, population=50.0)
    for _ in range(2):
        dbg.om_world_step(w)  # ticks 2 and 3

    # Tick 4: due tick. tension is 30.0 <= 40.0, so a clean build (checking
    # the condition against the tick-start field at resolution) drops this
    # without firing and without a probability roll (R-027-02).
    force_draws(dbg, w, [0.1])
    dbg.om_world_step(w)

    fired = [e for e in read_events(dbg, w) if e.template_id == tid_revolt]
    assert len(fired) == 1, (
        "OM_BUG_COND_AT_SPAWN injected but Regional Revolt still did not fire "
        "at tick 4 -- it should fire only if the condition is (incorrectly) "
        "read from the spawn-time field (tension 50.0, still above 40.0) "
        "instead of the tick-start field at resolution (tension 30.0) -- the "
        "condition-at-resolution detector did not trip"
    )
