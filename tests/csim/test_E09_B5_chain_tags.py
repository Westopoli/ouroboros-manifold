"""B5 (mission-plays plan): a time jump's chronicle runs chain clustering
(R-067-03: events sharing a chain tag form one chain cluster spanning every
region the chain touched). C-level, seeded world; the pipe jump is a different
owner.
"""
import ctypes

from conftest import (
    OMTier,
    OmChronicleCluster,
    load_launch_events,
    queue_external,
    set_owner,
    set_region,
    template_id,
)

CTYPE_CHAIN = 2


def _world(lib, world_factory):
    w = world_factory(n_regions=4, seed=7)
    for r in range(4):
        set_region(lib, w, r, tier=OMTier.HOME, military=50.0, economy=50.0, tension=50.0, population=50.0)
        set_owner(lib, w, r, 0, held_since=-1)
    return w


def _clusters(lib, w):
    out = []
    for i in range(lib.om_chronicle_entry_count(w)):
        c = OmChronicleCluster()
        assert lib.om_chronicle_get_cluster(w, i, ctypes.byref(c)) == 1
        out.append(c)
    return out


def test_R_067_03_a_seeded_jump_leaves_at_least_one_chain_cluster(lib, world_factory):
    """Given a seeded world where a Border Incursion spawns tagged follow-ups, When a time jump runs, Then the scroll has at least one chain cluster carrying a chain tag the event system assigned."""
    w = _world(lib, world_factory)
    load_launch_events(lib, w)
    tid = template_id(lib, w, "Border Incursion")
    assert queue_external(lib, w, 1, tid, due_tick=3, probability=1.0) > 0

    assert lib.om_time_jump_run(w, 30, None) == 0

    assert lib.om_chain_counter(w) > 0  # fixture check: chains really were assigned during the jump
    chains = [c for c in _clusters(lib, w) if c.type == CTYPE_CHAIN]
    assert chains, "no chain cluster after a jump that ran tagged events"
    assert all(0 < c.chain_tag <= lib.om_chain_counter(w) for c in chains)


def test_R_067_03_no_chain_events_means_no_chain_cluster(lib, world_factory):
    """Given a world with no events queued or loaded, When a time jump runs, Then no chain cluster exists (the detector does not invent chains)."""
    w = _world(lib, world_factory)

    assert lib.om_time_jump_run(w, 30, None) == 0

    assert lib.om_chain_counter(w) == 0
    assert all(c.type != CTYPE_CHAIN for c in _clusters(lib, w))


def test_control_R_067_03_hand_fed_chain_events_make_one_chain_cluster(lib, world_factory):
    """Positive control: two events with one chain tag in two regions, fed by hand with no jump, build and distill to a chain cluster with that tag. Proves _clusters() and the CHAIN type check can see a chain cluster, so the jump test's red is the jump not feeding chain events."""
    w = _world(lib, world_factory)
    CATEGORY_CHAIN_CASCADE = 12
    lib.om_chronicle_add_chain_event(w, 5, 1, CATEGORY_CHAIN_CASCADE)
    lib.om_chronicle_add_chain_event(w, 5, 3, CATEGORY_CHAIN_CASCADE)
    assert lib.om_chronicle_build_chain_clusters(w) == 1
    lib.om_chronicle_distill_and_assemble(w)

    chains = [c for c in _clusters(lib, w) if c.type == CTYPE_CHAIN]
    assert len(chains) == 1
    assert chains[0].chain_tag == 5
