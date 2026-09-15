"""Positive control for OM_BUG_ADMIN_ROLL_PER_FACTION.

Watch-for (docs/northstar/e2e/E-05.md QA watch-fors table, "Per-faction
admin revolt roll"): "Faction with N > 4 regions generates only 1 admin
revolt roll in tick log rather than N distinct rolls (one per region) in
`admin_revolt` log." Enum: OMBugE05.ADMIN_ROLL_PER_FACTION
(OM_BUG_ADMIN_ROLL_PER_FACTION = 107 in csrc/ouroboros_sim.h), "one roll per
faction, not per region".

No filled story test exists to reuse: S-040 ("Empires fracture", R-040-01
.. R-040-05) has no filled test yet in FILLED_DIR (only its prompt and two
empty raw-response files). Built fresh from R-040-01
("Given a faction with 4 regions, When the admin revolt roll runs, Then
each region rolls at chance 0.001",
docs/bible/epics/E-05-faction-agents-and-conflict.md) using the
isolate_agents(..., admin=True) and read_admin_rolls helpers conftest
already provides for exactly this isolation. One faction owns 5 regions (N
> 4, matching the watch-for's own wording); every draw is forced to 1.0 so
no roll actually triggers (chance is on the order of 0.001-0.02), keeping
the control to the roll count alone and out of the untested admin chain /
breakaway machinery (E-07, not built by E-05).
"""
from conftest import (
    OMArchetype,
    OMBugE05,
    OMTier,
    force_draws,
    isolate_agents,
    read_admin_rolls,
    set_faction,
    set_owner,
    set_region,
)


def test_control_admin_roll_per_faction_trips_the_detector(dbg, dbg_world_factory):
    w = dbg_world_factory(n_regions=5)
    isolate_agents(dbg, w, admin=True)
    dbg.om_debug_inject(w, OMBugE05.ADMIN_ROLL_PER_FACTION)

    set_faction(dbg, w, 0, OMArchetype.DEFAULT, budget=0.0)
    for idx in range(5):
        set_region(dbg, w, idx, tier=OMTier.HOME, military=50.0, economy=50.0,
                   tension=0.0, population=50.0, faction_id=0)
        set_owner(dbg, w, idx, 0, held_since=-1)

    # One forced draw per region roll, all held well above any admin-revolt
    # chance (~0.001-0.02), so nothing actually triggers.
    force_draws(dbg, w, [1.0, 1.0, 1.0, 1.0, 1.0])
    dbg.om_world_step(w)

    rolls = read_admin_rolls(dbg, w)
    assert len(rolls) > 0, "admin revolt roll never ran -- no records in the tick log"

    # Clean build: one distinct roll per region, five total. Inverted: one
    # roll per faction collapses this to a single record.
    assert len(rolls) != 5, (
        "OM_BUG_ADMIN_ROLL_PER_FACTION injected but the admin_revolt log "
        "still shows 5 distinct rolls, one per region, for the single "
        "5-region faction -- the per-faction-admin-roll detector did not "
        "trip"
    )
