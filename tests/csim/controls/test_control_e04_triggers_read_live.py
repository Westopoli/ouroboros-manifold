"""Positive control for OM_BUG_TRIGGERS_READ_LIVE (om_bug_e04 = 208).

Watch-for (docs/bible/epics/E-04-events-and-chains.md, "Ways this could be
wrong"): "Fresh triggers evaluated region by region against live fields, so
one region's crisis hides or causes another's on the same tick." (R-026-07;
QA signature "Live field cross-region trigger pollution": region B's outcome
differs when region evaluation order is reversed.)

Reuses the fixture shape of
test_E04_S026_crises_start_when_a_line_is_crossed.py's
test_R_026_07_both_judged_against_tick_start, specifically its "region order
independence" check (part 4): the same pair of tick-start crossings is run
twice, with which region holds which crossing swapped between runs. A clean
build judges every region against tick-start fields (R-026-07), so each
region fires its own crossing regardless of which index it occupies or which
order regions are evaluated in. Against the debug build with
OM_BUG_TRIGGERS_READ_LIVE injected, asserts the detector now trips: in at
least one of the two runs, one of the two independent tick-start crossings
fails to fire.
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


def _run(dbg, dbg_world_factory, military_region, economy_region):
    w = dbg_world_factory(n_regions=2)
    isolate_events(dbg, w)
    load_launch_events(dbg, w)
    zero_all_noise(dbg, w)

    tid_collapse = template_id(dbg, w, "Garrison Collapse")  # military below 30.0
    tid_decay = template_id(dbg, w, "Infrastructure Decay")  # economy below 40.0

    for r in range(2):
        set_region(dbg, w, r, tier=OMTier.HOME, military=40.0, economy=48.0, tension=20.0, population=45.0)
        set_owner(dbg, w, r, 0, held_since=-1)
    set_tech_multipliers(dbg, w, 0, 1.0, 1.0, 1.0)
    force_draws(dbg, w, [1.0] * 50)
    dbg.om_debug_inject(w, OMBugE04.TRIGGERS_READ_LIVE)

    for _ in range(3):
        dbg.om_world_step(w)

    # military_region crosses Garrison Collapse; economy_region crosses
    # Infrastructure Decay; both judged against the same tick-start snapshot.
    set_region(dbg, w, military_region, tier=OMTier.HOME, military=25.0, economy=48.0, tension=20.0, population=45.0)
    set_region(dbg, w, economy_region, tier=OMTier.HOME, military=40.0, economy=38.0, tension=20.0, population=45.0)
    dbg.om_world_step(w)

    events = read_events(dbg, w)
    fired_collapse = any(e.region_idx == military_region and e.template_id == tid_collapse
                          and e.source == OMSource.TRIGGER for e in events)
    fired_decay = any(e.region_idx == economy_region and e.template_id == tid_decay
                       and e.source == OMSource.TRIGGER for e in events)
    return fired_collapse, fired_decay


def test_control_triggers_read_live_trips_the_detector(dbg, dbg_world_factory):
    # Run 1: region 0 crosses military, region 1 crosses economy.
    run1 = _run(dbg, dbg_world_factory, military_region=0, economy_region=1)
    assert all(run1), (
        "the forward run did not fire both independent tick-start crossings "
        "-- this control's own setup is broken, not the detector"
    )

    # Run 2: roles swapped -- region 0 crosses economy, region 1 crosses military.
    run2 = _run(dbg, dbg_world_factory, military_region=1, economy_region=0)

    # A clean build fires both independent tick-start crossings in both runs,
    # regardless of which region index holds which crossing (R-026-07). A
    # build with OM_BUG_TRIGGERS_READ_LIVE injected loses one of them once
    # the region roles (and therefore the evaluation order) are swapped.
    assert not all(run2), (
        "OM_BUG_TRIGGERS_READ_LIVE injected but both regions still fired "
        "their independent tick-start crossings after the region roles were "
        "swapped -- the live cross-region read detector did not trip"
    )
