"""S-079 / R-079-01 and R-075-02 (A4 ruling 6): om_objective_get_node and
om_objective_get_radius describe the primary objective (index 0) the mission
frame sends; out of range is -1 and 0.0. Every archetype places the same
objective spine node and cover disc (OM_MISSION_OBJECTIVE_COVER_RADIUS, the
radius the hold-zone check counts enemies in), so radius > 0 is asserted for
all ten archetypes.

om_mission_get_commander_unit: R-077-05 assigns the commander by a later verb;
only the default (no assignment, 0) is asserted here.
"""
import ctypes

import pytest
from conftest import OMTier, set_region

SPINE_NODE_OBJECTIVE = 0  # csrc/mission.c OM_MISSION_SPINE_NODE_OBJECTIVE


def _setup(lib, w, archetype=1):
    set_region(lib, w, 0, tier=OMTier.HOME, military=10.0, economy=40.0,
               tension=20.0, population=50.0, faction_id=0)
    lib.om_mission_setup(w, 0, archetype, 0)


def test_R_079_01_objective_node_is_the_primary_spine_node(lib, world_factory):
    w = world_factory(n_regions=1)
    _setup(lib, w)
    assert lib.om_map_count_nodes_of_type(w, SPINE_NODE_OBJECTIVE) >= 1
    want = lib.om_map_get_nth_node_of_type(w, SPINE_NODE_OBJECTIVE, 0)
    node = lib.om_objective_get_node(w, 0)
    assert node >= 0
    assert node == want


def test_R_079_01_objective_node_out_of_range_is_minus_one(lib, world_factory):
    w = world_factory(n_regions=1)
    _setup(lib, w)
    assert lib.om_objective_get_node(w, 1) == -1
    assert lib.om_objective_get_node(w, 9999) == -1


def test_R_079_01_control_objective_node_minus_one_without_a_mission(lib, world_factory):
    w = world_factory(n_regions=1)
    assert lib.om_objective_get_node(w, 0) == -1
    assert lib.om_objective_get_radius(w, 0) == 0.0


@pytest.mark.parametrize("archetype", range(10))
def test_R_079_01_objective_radius_positive_for_every_archetype(lib, world_factory, archetype):
    w = world_factory(n_regions=1)
    _setup(lib, w, archetype)
    assert lib.om_objective_get_radius(w, 0) > 0.0


def test_R_079_01_objective_radius_is_the_placed_cover_disc(lib, world_factory):
    w = world_factory(n_regions=1)
    _setup(lib, w)
    assert lib.om_map_cover_count(w) >= 1
    # TD-VG-D-5: in a space era cover index 0 is a rubble disc; find the cover at the objective's position.
    class OMVec2(ctypes.Structure):
        _fields_ = [("x", ctypes.c_double), ("y", ctypes.c_double)]
    ctr = OMVec2()
    assert lib.om_objective_get_center(w, 0, ctypes.byref(ctr)) == 1
    radii = []
    for i in range(lib.om_map_cover_count(w)):
        x, y, r, h = (ctypes.c_double() for _ in range(4))
        assert lib.om_map_cover_at(w, i, ctypes.byref(x), ctypes.byref(y), ctypes.byref(r), ctypes.byref(h)) == 1
        if x.value == ctr.x and y.value == ctr.y:
            radii.append(r.value)
    assert radii, "no cover disc at the objective's position"
    assert lib.om_objective_get_radius(w, 0) in radii


def test_R_079_01_objective_radius_out_of_range_is_zero(lib, world_factory):
    w = world_factory(n_regions=1)
    _setup(lib, w)
    assert lib.om_objective_get_radius(w, 1) == 0.0
    assert lib.om_objective_get_radius(w, 9999) == 0.0


def test_R_077_05_commander_unit_defaults_to_zero(lib, world_factory):
    w = world_factory(n_regions=1)
    _setup(lib, w)
    assert lib.om_mission_get_force_count(w) > 0
    assert lib.om_mission_get_commander_unit(w) == 0


def test_R_077_05_commander_unit_zero_without_a_mission(lib, world_factory):
    w = world_factory(n_regions=1)
    assert lib.om_mission_get_commander_unit(w) == 0
