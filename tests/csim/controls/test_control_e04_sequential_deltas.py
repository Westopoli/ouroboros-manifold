"""Positive control for OM_BUG_SEQUENTIAL_DELTAS (om_bug_e04 = 204).

Watch-for (docs/bible/epics/E-04-events-and-chains.md, "Ways this could be
wrong"): "Same-tick deltas applied sequentially so the second event reads
the first's result." (R-028-01.)

Adapts the fixture shape of test_E04_S028_disasters_stack_contradictions_do_not.py's
test_R_028_01_each_delta_computed_against_tick (two due events resolving in
the same region on the same tick, deltas summed once against tick-start
fields with floors/ceilings applied to the sum, not to each step). "Admin
Military Defection" (military -3) and "Emergency Levy" (military +3) are
queued due the same tick in a region starting at military 2.0 -- a net
military delta of 0.0, so a correct build (R-028-01: each delta computed
against the tick-start field, summed, then clamped once) never touches the
military floor and leaves military at 2.0. Applied sequentially, the first
delta alone (2.0 - 3.0 = -1.0) clamps to the 0.0 floor before the second
delta's +3.0 is added, landing at 3.0 instead. Against the debug build with
OM_BUG_SEQUENTIAL_DELTAS injected, asserts the detector now trips: military
lands at 3.0, not 2.0.
"""
import pytest

from conftest import (
    OMBugE04,
    OMField,
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


def test_control_sequential_deltas_trips_the_detector(dbg, dbg_world_factory):
    w = dbg_world_factory(n_regions=1)
    isolate_events(dbg, w)
    load_launch_events(dbg, w)
    zero_all_noise(dbg, w)

    tid_defection = template_id(dbg, w, "Admin Military Defection")  # effects: -3, 0, +2, 0
    tid_levy = template_id(dbg, w, "Emergency Levy")  # effects: +3, -2, +2, 0

    set_region(dbg, w, 0, tier=OMTier.HOME, military=2.0, economy=50.0, tension=50.0, population=50.0)
    set_owner(dbg, w, 0, 0, held_since=-1)
    set_tech_multipliers(dbg, w, 0, 1.0, 1.0, 1.0)
    dbg.om_debug_inject(w, OMBugE04.SEQUENTIAL_DELTAS)

    # Queued in this order so a sequential-application bug dips below the
    # military floor (0.0) on the first delta before the second delta is
    # added. The two templates carry no shared exclusion tag, so both
    # resolve on the same tick without either being delayed.
    queue_external(dbg, w, 0, tid_defection, due_tick=1, probability=1.0)
    queue_external(dbg, w, 0, tid_levy, due_tick=1, probability=1.0)
    force_draws(dbg, w, [0.1, 0.1])
    dbg.om_world_step(w)

    assert dbg.om_region_field(w, 0, OMField.MILITARY) == pytest.approx(3.0, abs=1e-6), (
        "OM_BUG_SEQUENTIAL_DELTAS injected but region 0's military still "
        "landed at 2.0, the tick-start value a once-summed-then-clamped "
        "application (net delta 0.0) leaves untouched -- the "
        "sequential-application detector did not trip"
    )
