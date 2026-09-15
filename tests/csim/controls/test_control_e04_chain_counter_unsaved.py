"""Positive control for OM_BUG_CHAIN_COUNTER_UNSAVED (om_bug_e04 = 207).

Watch-for (docs/bible/epics/E-04-events-and-chains.md, "Ways this could be
wrong"): "Chain tag counter not saved, so loading a save reuses tags."
(R-027-06.)

NOTE (see NOTES.md for the full gap writeup): `ouroboros_sim.h` has no
om_save/om_load ABI yet, so there is no way to actually round-trip a world
through a save and reload from this fenced suite and observe a reused chain
tag after reload -- the literal watch-for this bug describes. This control
is the closest available proxy: it reuses the fixture shape of
test_E04_S027_one_thing_leads_to_another.py's
test_R_027_06_its_chain_tag_equals_root (two distinct threshold crossings in
one region start two distinct chains) and checks `om_chain_counter`
continuity across those two chain starts within a single session -- the
counter must advance by exactly one per chain start and never repeat a tag.
Once om_save/om_load exists, this control should be replaced with a real
save-reload-reuse test; until then, injecting OM_BUG_CHAIN_COUNTER_UNSAVED
may not be observable here at all, since the bug only manifests across a
reload this suite cannot perform.
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
    template_id,
    zero_all_noise,
)


def test_control_chain_counter_unsaved_trips_the_detector(dbg, dbg_world_factory):
    w = dbg_world_factory(n_regions=1)
    isolate_events(dbg, w)
    load_launch_events(dbg, w)
    zero_all_noise(dbg, w)

    tid_collapse = template_id(dbg, w, "Garrison Collapse")
    tid_boom = template_id(dbg, w, "Trade Boom")

    set_region(dbg, w, 0, tier=OMTier.HOME, military=40.0, economy=48.0, tension=20.0, population=45.0)
    set_owner(dbg, w, 0, 0, held_since=-1)
    set_tech_multipliers(dbg, w, 0, 1.0, 1.0, 1.0)
    force_draws(dbg, w, [1.0] * 50)
    dbg.om_debug_inject(w, OMBugE04.CHAIN_COUNTER_UNSAVED)

    for _ in range(3):
        dbg.om_world_step(w)

    # First chain start: military crosses below Garrison Collapse's 30.0 on tick 4.
    set_region(dbg, w, 0, tier=OMTier.HOME, military=25.0, economy=48.0, tension=20.0, population=45.0)
    dbg.om_world_step(w)
    first = [e for e in read_events(dbg, w) if e.template_id == tid_collapse]
    assert len(first) == 1, "Garrison Collapse did not fire at tick 4 to start the first chain"
    tag1 = first[0].chain_tag
    counter_after_first = dbg.om_chain_counter(w)

    # Second chain start: economy crosses above Trade Boom's 55.0 on tick 5.
    set_region(dbg, w, 0, tier=OMTier.HOME, military=40.0, economy=60.0, tension=20.0, population=45.0)
    dbg.om_world_step(w)
    second = [e for e in read_events(dbg, w) if e.template_id == tid_boom]
    assert len(second) == 1, "Trade Boom did not fire at tick 5 to start the second chain"
    tag2 = second[0].chain_tag

    assert tag2 == counter_after_first + 1 and tag2 != tag1, (
        "OM_BUG_CHAIN_COUNTER_UNSAVED injected but the second chain's tag "
        "still advanced cleanly past the first chain's tag and the counter "
        "read after the first chain -- within a single session this control "
        "cannot reproduce the reuse-after-reload bug (no om_save/om_load in "
        "ouroboros_sim.h yet); see NOTES.md"
    )
