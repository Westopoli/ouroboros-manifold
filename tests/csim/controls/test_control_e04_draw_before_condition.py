"""Positive control for OM_BUG_DRAW_BEFORE_CONDITION (om_bug_e04 = 206).

Watch-for (docs/bible/epics/E-04-events-and-chains.md, "Ways this could be
wrong"): "Probability roll made before the condition check, consuming RNG
and breaking determinism." (R-027-02, R-027-03.)

Adapts the fixture shape of test_E04_S027_one_thing_leads_to_another.py's
test_R_027_02_it_dropped_without_firing_without and
test_R_027_03_one_rng_draw_r_made, which both watch `om_rng_forced_remaining`
to prove a draw is or is not consumed. "Border Incursion" fires
unconditionally on tick 1 and spawns "Regional Revolt" (condition: tension
above 40.0) due tick 4; tension is held at 20.0 throughout, so the condition
fails at resolution. A clean build (R-027-02) drops it without a probability
roll -- zero RNG draws consumed. Against the debug build with
OM_BUG_DRAW_BEFORE_CONDITION injected, asserts the detector now trips: the
forced sentinel draw for tick 4 is consumed even though the condition fails.
"""
from conftest import (
    OMBugE04,
    OMTier,
    force_draws,
    isolate_events,
    load_launch_events,
    queue_external,
    set_owner,
    set_region,
    set_tech_multipliers,
    template_id,
    zero_all_noise,
)


def test_control_draw_before_condition_trips_the_detector(dbg, dbg_world_factory):
    w = dbg_world_factory(n_regions=1)
    isolate_events(dbg, w)
    load_launch_events(dbg, w)
    zero_all_noise(dbg, w)

    tid_border = template_id(dbg, w, "Border Incursion")  # spawns Regional Revolt [3,6] 0.60 tension above 40

    set_region(dbg, w, 0, tier=OMTier.HOME, military=50.0, economy=50.0, tension=20.0, population=50.0)
    set_owner(dbg, w, 0, 0, held_since=-1)
    set_tech_multipliers(dbg, w, 0, 1.0, 1.0, 1.0)
    dbg.om_debug_inject(w, OMBugE04.DRAW_BEFORE_CONDITION)

    queue_external(dbg, w, 0, tid_border, due_tick=1, probability=1.0)

    # Tick 1: Border Incursion fires unconditionally and spawns Regional
    # Revolt with delay drawn to 3 (due tick 4). Tension stays at 20.0
    # (<= 40.0) through tick 4, so the spawn's condition fails at resolution.
    force_draws(dbg, w, [0.1, 0.00])
    dbg.om_world_step(w)
    for _ in range(2):
        dbg.om_world_step(w)  # ticks 2 and 3

    # One sentinel draw forced for tick 4. A clean build never touches it:
    # the condition check (R-027-02) fails before any probability roll would
    # be made, so no RNG draw is consumed.
    force_draws(dbg, w, [0.99])
    assert dbg.om_rng_forced_remaining(w) == 1, (
        "the sentinel draw for tick 4 was not queued as forced RNG input -- "
        "this control's own setup is broken, not the detector"
    )

    dbg.om_world_step(w)  # tick 4: condition check should fail before any roll

    assert dbg.om_rng_forced_remaining(w) == 0, (
        "OM_BUG_DRAW_BEFORE_CONDITION injected but the sentinel draw for tick "
        "4 is still unconsumed -- a probability roll was not made ahead of "
        "the condition check -- the draw-before-condition detector did not "
        "trip"
    )
