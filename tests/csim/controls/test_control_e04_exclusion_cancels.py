"""Positive control for OM_BUG_EXCLUSION_CANCELS (om_bug_e04 = 205).

Watch-for (docs/bible/epics/E-04-events-and-chains.md, "Ways this could be
wrong"): "Exclusion loser cancelled instead of delayed." (R-028-02,
R-028-03.)

Reuses the exact fixture from test_E04_S028_disasters_stack_contradictions_do_not.py's
test_R_028_02_entrenched_kept_crushed_re_queued: "Revolt Crushed" (p 0.45)
and "Revolt Entrenched" (p 0.55) both due the same tick in the same region.
A clean build keeps Entrenched and re-queues Crushed for tick + 1 or tick + 2
(one draw); it never disappears. Against the debug build with
OM_BUG_EXCLUSION_CANCELS injected, asserts the detector now trips: Revolt
Crushed appears in neither the `delayed` log nor the pending queue after
losing the exclusion tie -- it was cancelled outright instead of delayed.
"""
from conftest import (
    OMBugE04,
    OMTier,
    force_draws,
    isolate_events,
    load_launch_events,
    queue_external,
    read_delayed,
    read_event_queue,
    read_events,
    set_owner,
    set_region,
    set_tech_multipliers,
    template_id,
    zero_all_noise,
)


def test_control_exclusion_cancels_trips_the_detector(dbg, dbg_world_factory):
    w = dbg_world_factory(n_regions=1)
    isolate_events(dbg, w)
    load_launch_events(dbg, w)
    zero_all_noise(dbg, w)

    tid_crushed = template_id(dbg, w, "Revolt Crushed")
    tid_entrenched = template_id(dbg, w, "Revolt Entrenched")

    set_region(dbg, w, 0, tier=OMTier.HOME, military=50.0, economy=50.0, tension=50.0, population=50.0)
    set_owner(dbg, w, 0, 0, held_since=-1)
    set_tech_multipliers(dbg, w, 0, 1.0, 1.0, 1.0)
    dbg.om_debug_inject(w, OMBugE04.EXCLUSION_CANCELS)

    queue_external(dbg, w, 0, tid_crushed, due_tick=1, probability=0.45)
    queue_external(dbg, w, 0, tid_entrenched, due_tick=1, probability=0.55)

    # Draw 0.2: tie-break < 0.5 would decide by queue order, but Crushed and
    # Entrenched have unequal probability so R-028-02's higher-probability
    # rule (not the tie-break) keeps Entrenched outright. Draw 0.1: the kept
    # Entrenched's own probability roll passes (0.1 <= 0.55).
    force_draws(dbg, w, [0.2, 0.1])
    dbg.om_world_step(w)

    events = read_events(dbg, w)
    assert any(e.template_id == tid_entrenched for e in events), (
        "Revolt Entrenched did not fire -- exclusion resolution is not "
        "isolating the winner, so this control cannot isolate "
        "OM_BUG_EXCLUSION_CANCELS on the loser"
    )

    still_tracked = (
        any(d.template_id == tid_crushed for d in read_delayed(dbg, w))
        or any(q.template_id == tid_crushed for q in read_event_queue(dbg, w))
    )
    assert not still_tracked, (
        "OM_BUG_EXCLUSION_CANCELS injected but Revolt Crushed still appears "
        "in the delayed log or the pending queue after losing the exclusion "
        "tie -- the loser-cancelled-instead-of-delayed detector did not trip"
    )
