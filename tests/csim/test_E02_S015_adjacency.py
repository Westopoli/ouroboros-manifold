"""S-015 -- Friendly neighbors make you richer.

R-015-01 .. R-015-04. Formula: ALG-06 (adjacency bonus) in algorithms.md.
Q-015-01 resolved (b): every edge type counts, so this ABI's
om_region_set_adjacency takes no edge-type parameter at all -- there is no
way to represent one, which is itself the fix for R-015-02's point that edge
type must never gate the bonus.

R-015-03's cooperative-stance half cannot be fixtured through this header:
the E-02 ABI has no stance setter (stances belong to E-06 diplomacy, out of
this epic's scope). Its hostile/no-relationship half is testable, since
ALG-38 defines a missing pair as reading hostile by default.
"""
import ctypes

import pytest

from conftest import OMTier, read_drift, set_region


def _adjacency(lib, w, subject_idx, neighbor_indices):
    arr = (ctypes.c_uint32 * len(neighbor_indices))(*neighbor_indices)
    lib.om_region_set_adjacency(w, subject_idx, arr, len(neighbor_indices))


def test_R_015_01_two_friendly_neighbors_sum(lib, world_factory):
    w = world_factory(n_regions=3)
    set_region(lib, w, 0, tier=OMTier.HOME, military=0.0, economy=50.0,
               tension=0.0, population=50.0, faction_id=5)
    set_region(lib, w, 1, tier=OMTier.HOME, military=0.0, economy=80.0,
               tension=0.0, population=50.0, faction_id=5)
    set_region(lib, w, 2, tier=OMTier.HOME, military=0.0, economy=40.0,
               tension=0.0, population=50.0, faction_id=5)
    _adjacency(lib, w, 0, [1, 2])
    lib.om_world_step(w)
    _, row = read_drift(lib, w, 0)
    assert row.economy_adjacency == pytest.approx(0.060, abs=1e-9)


def test_R_015_02_single_friendly_neighbor_edge_type_irrelevant(lib, world_factory):
    w = world_factory(n_regions=2)
    set_region(lib, w, 0, tier=OMTier.HOME, military=0.0, economy=50.0,
               tension=0.0, population=50.0, faction_id=5)
    set_region(lib, w, 1, tier=OMTier.HOME, military=0.0, economy=40.0,
               tension=0.0, population=50.0, faction_id=5)
    _adjacency(lib, w, 0, [1])
    lib.om_world_step(w)
    _, row = read_drift(lib, w, 0)
    assert row.economy_adjacency == pytest.approx(0.020, abs=1e-9)


@pytest.mark.skip(
    reason="R-015-03's cooperative-stance half needs a diplomacy stance "
           "setter that csrc/ouroboros_sim.h does not expose (stances are "
           "E-06 scope); cannot be hard-fixtured at the E-02 isolation "
           "layer. See the ABI-gap note in this module's docstring."
)
def test_R_015_03_cooperative_neighbor_contributes():
    pass


def test_R_015_03_hostile_default_contributes_nothing(lib, world_factory):
    w = world_factory(n_regions=2)
    set_region(lib, w, 0, tier=OMTier.HOME, military=0.0, economy=50.0,
               tension=0.0, population=50.0, faction_id=5)
    # Different faction, no stance ever configured -> ALG-38 default hostile.
    set_region(lib, w, 1, tier=OMTier.HOME, military=0.0, economy=90.0,
               tension=0.0, population=50.0, faction_id=6)
    _adjacency(lib, w, 0, [1])
    lib.om_world_step(w)
    _, row = read_drift(lib, w, 0)
    assert row.economy_adjacency == 0.0


def test_R_015_04_empty_neighbor_contributes_nothing(lib, world_factory):
    w = world_factory(n_regions=2)
    set_region(lib, w, 0, tier=OMTier.HOME, military=0.0, economy=50.0,
               tension=0.0, population=50.0, faction_id=5)
    set_region(lib, w, 1, tier=OMTier.EMPTY, military=0.0, economy=0.0,
               tension=0.0, population=0.0)
    _adjacency(lib, w, 0, [1])
    lib.om_world_step(w)
    _, row = read_drift(lib, w, 0)
    assert row.economy_adjacency == 0.0
