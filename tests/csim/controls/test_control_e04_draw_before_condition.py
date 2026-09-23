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
fails at resolution.

Original version of this control forced exactly one sentinel draw for tick 4
and expected it to survive untouched on a clean build. Dead as written
(control_liveness: both the as-written and neutralized runs passed): "Regional
Revolt" is itself a standalone `OM_TRIG_PROBABILITY` trigger
(evt_evaluate_triggers, csrc/events.c), independent of the due-queue spawn
this control targets, and it draws one RNG value for region 0 on every
non-grace tick regardless of the queued candidate's own condition -- so the
lone sentinel was always consumed at tick 4 by that unrelated roll, clean or
not, and the assertion could never tell the two builds apart. Confirmed by
direct instrumentation: forcing two sentinels before tick 4 and reading
`om_rng_forced_remaining` after leaves 1 remaining on a clean build (the
standalone trigger takes the first; the due-queue candidate's condition fails
before its own probability roll, so the second is never drawn) and 0 on the
debug build with OM_BUG_DRAW_BEFORE_CONDITION injected (the candidate's own
roll is now made before its condition is checked, consuming the first
sentinel for a result it discards; the standalone trigger still takes the
second). Two sentinels isolate the queued candidate's own draw-before-check
fault from the unrelated per-tick standalone roll that was masking it.
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

    # Two sentinels forced for tick 4: region 0's standalone "Regional
    # Revolt" OM_TRIG_PROBABILITY roll (evt_evaluate_triggers) always takes
    # one, clean or not -- the second is the one that isolates the due-queue
    # candidate's own draw-before-check fault (see module docstring).
    force_draws(dbg, w, [0.99, 0.98])
    assert dbg.om_rng_forced_remaining(w) == 2, (
        "the two sentinel draws for tick 4 were not queued as forced RNG "
        "input -- this control's own setup is broken, not the detector"
    )

    dbg.om_world_step(w)  # tick 4: condition check should fail before any roll

    assert dbg.om_rng_forced_remaining(w) == 0, (
        "OM_BUG_DRAW_BEFORE_CONDITION injected but only the standalone "
        "Regional Revolt trigger's own roll consumed a sentinel (1 left, same "
        "as a clean build) -- the due-queue candidate's probability roll was "
        "not made ahead of its condition check -- the draw-before-condition "
        "detector did not trip"
    )
