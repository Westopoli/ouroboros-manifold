"""F5 window control for csrc/lifecycle.c (E-07, wave 1 card B6).

Rule (docs/bible/algorithms.md ALG-42 "Zombie cleanup", pass 1): "every
breakaway_* faction with zero regions whose creation tick is >= 5 ticks ago
is removed." Fixture: a lone OM_ARCH_BREAKAWAY faction with zero owned
regions, created at tick 10; the world tick is moved to 14 with
om_world_set_tick (a fixture setter with no other side effect), so the next
om_world_step lands on tick 15 -- exactly 15-10 = 5 ticks since creation, the
rule's own inclusive boundary. Only OM_FEAT_LIFECYCLE is on (E-07's own
mvp_features.toml isolation row), so no other tick step can touch the
faction list.

PLANT: under OM_BUG_ZOMBIE_PASS1_GE_NOT_GT, pass 1 only removes a faction
when tick - created_tick > 5 (strictly greater), so the exact-5-ticks case
is left active instead of removed.
"""
from conftest import OMArchetype, OMBugE07, set_faction


def test_control_zombie_ge_not_gt_trips_the_detector(dbg, dbg_world_factory):
    w = dbg_world_factory(n_regions=1)
    dbg.om_debug_inject(w, OMBugE07.ZOMBIE_PASS1_GE_NOT_GT)

    set_faction(dbg, w, 1, OMArchetype.BREAKAWAY, budget=0.0, tech=0.0, confidence=1.0)
    dbg.om_faction_set_created_tick(w, 1, 10)
    dbg.om_world_set_tick(w, 14)

    tick = dbg.om_world_step(w)
    assert tick == 15, "fixture setup: om_world_set_tick(14) then one step must land on tick 15"

    assert dbg.om_faction_is_active(w, 1) == 1, (
        "OM_BUG_ZOMBIE_PASS1_GE_NOT_GT injected but the zero-region breakaway "
        "faction, created exactly 5 ticks ago, was still removed at the "
        ">= 5 boundary -- the off-by-one detector did not trip"
    )
