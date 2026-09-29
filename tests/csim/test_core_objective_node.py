"""Backing HDR4-2's om_objective_get_node accessor (docs/northstar's
gap-fix-and-migration-plan.md): for objective_idx == 0 (the primary
objective, always present after om_mission_setup /
om_mission_build_objectives), it returns the map-node index of that
objective's spine node -- the same value
om_map_get_nth_node_of_type(w, OM_MISSION_SPINE_NODE_OBJECTIVE, 0) already
gives (csrc/mission.c's om_objective_get_center does this exact lookup
today for its own fallback path). For any objective_idx with no real
objective (e.g. 1 -- only one objective exists today), it returns -1.

OM_MISSION_SPINE_NODE_OBJECTIVE is 0 -- csrc/mission.c line 272,
`#define OM_MISSION_SPINE_NODE_OBJECTIVE 0`. Hardcoded below since neither
a conftest symbolic binding nor a header enum exists for it (it's a #define
private to mission.c); this test uses the same integer om_mission.c's own
om_objective_get_center passes to om_map_get_nth_node_of_type.

om_objective_get_node does not exist yet (not in csrc/ouroboros_sim.h / not
bound in conftest.py), so both tests are RED: the first call raises
AttributeError (undefined symbol in libouroboros.so). Called bare and
unbound, matching this suite's other not-yet-added test_core_* symbols.

Does NOT test om_objective_get_radius -- that accessor is held pending a
design ruling, out of scope for this piece.
"""
import ctypes

from conftest import OMTier, set_region

OM_MISSION_SPINE_NODE_OBJECTIVE = 0  # csrc/mission.c line 272
OM_MISSION_ARCH_SIEGE_BREAKING = 1  # csrc/mission.c OM_MISSION_ARCH_SIEGE_BREAKING


def _setup_mission(lib, w, region_idx, military, archetype=OM_MISSION_ARCH_SIEGE_BREAKING):
    set_region(lib, w, region_idx, tier=OMTier.HOME, military=military, economy=40.0,
               tension=20.0, population=50.0, faction_id=0)
    lib.om_mission_setup(w, region_idx, archetype, 0)


def test_objective_get_node_matches_spine_node_lookup(lib, world_factory):
    """After om_mission_setup, om_objective_get_node(w, 0) is a non-negative
    value equal to om_map_get_nth_node_of_type(w, OM_MISSION_SPINE_NODE_OBJECTIVE, 0)."""
    w = world_factory(n_regions=1)
    _setup_mission(lib, w, 0, military=10.0)

    assert lib.om_map_count_nodes_of_type(w, OM_MISSION_SPINE_NODE_OBJECTIVE) >= 1
    expected_node = lib.om_map_get_nth_node_of_type(w, OM_MISSION_SPINE_NODE_OBJECTIVE, 0)

    node = lib.om_objective_get_node(w, 0)
    assert node >= 0
    assert node == expected_node


def test_objective_get_node_returns_minus_one_for_missing_objective(lib, world_factory):
    """om_objective_get_node(w, 1) returns -1 -- only one objective exists today."""
    w = world_factory(n_regions=1)
    _setup_mission(lib, w, 0, military=10.0)

    assert lib.om_objective_get_node(w, 1) == -1
