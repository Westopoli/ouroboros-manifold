"""Fixture and state contract tests for E-05: region ownership, typed edges, and feature switches.
Dedicated focused tests for micro-cards 202a3 (ownership) and 202a4 (edges & features).
"""
import ctypes
import pytest
from conftest import OMEdge, OMFeature, OMTier, set_region


def test_region_ownership_setting_and_query(lib, world_factory):
    """om_region_set_owner stores faction_id and held_since_tick; om_region_owner and om_region_held_since read them."""
    w = world_factory(n_regions=4)
    # Initially region 0 has owner -1 (unowned) and held_since < 0
    assert lib.om_region_owner(w, 0) == -1

    lib.om_region_set_owner(w, 0, 3, 42)
    assert lib.om_region_owner(w, 0) == 3
    assert lib.om_region_held_since(w, 0) == 42

    lib.om_region_set_owner(w, 1, 0, -1)
    assert lib.om_region_owner(w, 1) == 0
    assert lib.om_region_held_since(w, 1) == -1


def test_region_edge_types(lib, world_factory):
    """om_region_set_edge stores undirected typed edge; om_region_edge returns 1 and writes edge_type, or 0 if none."""
    w = world_factory(n_regions=4)
    edge_out = ctypes.c_int(-1)

    # Initially no edge between 0 and 1
    assert lib.om_region_edge(w, 0, 1, ctypes.byref(edge_out)) == 0

    # Set BORDER edge between 0 and 1 (undirected)
    lib.om_region_set_edge(w, 0, 1, OMEdge.BORDER)
    assert lib.om_region_edge(w, 0, 1, ctypes.byref(edge_out)) == 1
    assert edge_out.value == OMEdge.BORDER
    assert lib.om_region_edge(w, 1, 0, ctypes.byref(edge_out)) == 1
    assert edge_out.value == OMEdge.BORDER

    # Overwrite with BOTH
    lib.om_region_set_edge(w, 0, 1, OMEdge.BOTH)
    assert lib.om_region_edge(w, 0, 1, ctypes.byref(edge_out)) == 1
    assert edge_out.value == OMEdge.BOTH


def test_world_feature_switches(lib, world_factory):
    """om_world_set_feature toggles feature flags; om_world_feature queries them."""
    w = world_factory(n_regions=2)
    lib.om_world_set_feature(w, OMFeature.FACTIONS, 1)
    assert lib.om_world_feature(w, OMFeature.FACTIONS) == 1

    lib.om_world_set_feature(w, OMFeature.FACTIONS, 0)
    assert lib.om_world_feature(w, OMFeature.FACTIONS) == 0
