"""S-039 wiring: the collision step runs between 3e (reinforce) and 3f
(resolve), and its results replace what 3f would otherwise have done alone.

This is a tick-order proof, not a re-test of the collision math itself
(tests/csim/test_E05_S039_when_everyone_wants_the_same_region.py owns that).
`om_step_collisions` is presently a STUB (csrc/collision.c) -- these
assertions are expected red until card 205a implements it, per the audit
fix (docs/northstar/research/factory/audit_2026-09-21/README.md B F-1-1):
the old chain-head card ordered `om_tick_collisions` (a const read-back) to
mutate the world, which it cannot do. The wiring itself -- the one-line call
`om_step_collisions(w)` in `om_world_step` between `om_step_reinforce` and
`om_step_resolve`, and the OM_BUG_COLLISION_AFTER_RESOLVE fault branch that
moves it after `om_step_resolve` instead -- is hand-written in csrc/sim.c
(parent-owned orchestration, like every other tick-step gate in that file),
not built by an Agora card.

The positive control below (OM_BUG_COLLISION_AFTER_RESOLVE = 112) is
expected DEAD/ERROR against today's STUB build: with no real collision
resolution on either side of `om_step_resolve`, reordering it changes
nothing observable yet. `control_liveness.py` should report it PENDING
until 205a lands, then LIVE -- stated in the audit fix brief, not a defect
here.
"""
from conftest import (
    OMArchetype,
    OMBugE05,
    OMEdge,
    OMStance,
    OMTier,
    force_draws,
    inject_intent,
    isolate_agents,
    read_collisions,
    read_colonizations,
    read_decisions,
    set_edge,
    set_faction,
    set_owner,
    set_region,
    set_stance,
    set_tech_multipliers,
)
from conftest import OMAction


def _two_colonizers_on_one_empty_region(lib, world_factory):
    """Factions 0 and 1 both inject a colonize intent on empty region 3 --
    the same fixture shape as test_E05_S039's _two_colliders_on_empty, kept
    local and minimal since this module only proves ordering."""
    w = world_factory(n_regions=4)
    isolate_agents(lib, w)
    set_faction(lib, w, 0, OMArchetype.CONQUEROR, budget=200.0, confidence=5.0)
    set_faction(lib, w, 1, OMArchetype.CONQUEROR, budget=200.0, confidence=5.0)
    set_stance(lib, w, 0, 1, OMStance.HOSTILE)
    set_tech_multipliers(lib, w, 0, 1.0, 1.0, 1.0)
    set_tech_multipliers(lib, w, 1, 1.0, 1.0, 1.0)
    set_region(lib, w, 0, tier=OMTier.HOME, military=30.0, economy=100.0, tension=0.0, population=50.0, faction_id=0)
    set_region(lib, w, 1, tier=OMTier.HOME, military=60.0, economy=100.0, tension=0.0, population=50.0, faction_id=0)
    set_region(lib, w, 2, tier=OMTier.HOME, military=30.0, economy=100.0, tension=0.0, population=50.0, faction_id=1)
    set_region(lib, w, 3, tier=OMTier.EMPTY, military=0.0, economy=0.0, tension=0.0, population=0.0, faction_id=-1)
    for idx, fid in ((0, 0), (1, 0), (2, 1)):
        set_owner(lib, w, idx, fid, held_since=-1)
    set_edge(lib, w, 1, 3, OMEdge.BOTH)
    set_edge(lib, w, 2, 3, OMEdge.BOTH)
    inject_intent(lib, w, 0, OMAction.COLONIZE, 3, 1, 40.0)
    inject_intent(lib, w, 1, OMAction.COLONIZE, 3, 2, 20.0)
    return w


def test_R_039_wiring_collisions_run_before_resolve(lib, world_factory):
    w = _two_colonizers_on_one_empty_region(lib, world_factory)
    force_draws(lib, w, [0.1, 0.0])  # winner draw, refund draw
    lib.om_world_step(w)

    owner = lib.om_region_owner(w, 3)
    assert owner in (0, 1), "region 3 must have exactly one owner after the collision resolves"

    pending = [d for d in read_decisions(lib, w) if d.target_idx == 3]
    assert pending == [], (
        "om_tick_decisions still reports a pending intent for region 3 -- the "
        "colliding intents were not removed from w->decisions[] before 3f "
        "(om_step_resolve) ran"
    )

    collisions = [c for c in read_collisions(lib, w) if c.target_idx == 3]
    assert len(collisions) == 1, (
        "expected exactly one collision record for region 3 from the collision "
        "step running between 3e and 3f"
    )

    colonizations = [c for c in read_colonizations(lib, w) if c.target_idx == 3]
    assert len(colonizations) == 1, (
        "3f (om_step_resolve) resolved region 3's solo-colonize path independently "
        "of the collision step"
    )


def test_control_collision_after_resolve_trips_the_detector(dbg, dbg_world_factory):
    w = _two_colonizers_on_one_empty_region(dbg, dbg_world_factory)
    dbg.om_debug_inject(w, OMBugE05.COLLISION_AFTER_RESOLVE)
    force_draws(dbg, w, [0.1, 0.0])
    dbg.om_world_step(w)

    pending = [d for d in read_decisions(dbg, w) if d.target_idx == 3]
    collisions = [c for c in read_collisions(dbg, w) if c.target_idx == 3]
    assert pending != [] or len(collisions) != 1, (
        "OM_BUG_COLLISION_AFTER_RESOLVE injected but region 3's decisions/"
        "collisions still read as if the collision step ran before 3f -- the "
        "after-resolve reorder detector did not trip"
    )
