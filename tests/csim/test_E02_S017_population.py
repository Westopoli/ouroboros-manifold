"""S-017 -- Population grows slowly and starves slowly.

R-017-01 .. R-017-04. Formula: ALG-08 (population drift) in algorithms.md.
Tested at tick 1 (primed trend == raw field, R-018-02).
"""
import pytest

from conftest import OMTier, read_drift, set_region


def test_R_017_01_growth_branch_exact(lib, world_factory):
    w = world_factory(n_regions=1)
    set_region(lib, w, 0, tier=OMTier.HOME, military=0.0, economy=66.0,
               tension=0.0, population=60.0)
    lib.om_world_step(w)
    _, row = read_drift(lib, w, 0)
    assert row.population_base == pytest.approx(0.480, abs=1e-9)
    assert row.population_subsist == pytest.approx(0.0, abs=1e-9)


def test_R_017_02_decline_branch_with_subsistence(lib, world_factory):
    w = world_factory(n_regions=1)
    set_region(lib, w, 0, tier=OMTier.HOME, military=0.0, economy=10.0,
               tension=0.0, population=60.0)
    lib.om_world_step(w)
    _, row = read_drift(lib, w, 0)
    assert row.population_base == pytest.approx(-1.0, abs=1e-9)
    assert row.population_subsist == pytest.approx(-0.026667, abs=1e-6)
    assert (row.population_base + row.population_subsist) == pytest.approx(-1.0267, abs=1e-3)


def test_R_017_03_growth_threshold_at_15(lib, world_factory):
    w = world_factory(n_regions=2)
    set_region(lib, w, 0, tier=OMTier.HOME, military=0.0, economy=15.0,
               tension=0.0, population=60.0)
    set_region(lib, w, 1, tier=OMTier.HOME, military=0.0, economy=15.01,
               tension=0.0, population=60.0)
    lib.om_world_step(w)
    _, at_threshold = read_drift(lib, w, 0)
    _, above_threshold = read_drift(lib, w, 1)
    assert at_threshold.population_base == 0.0
    assert above_threshold.population_base > 0.0


def test_R_017_04_growth_zero_at_population_ceiling(lib, world_factory):
    w = world_factory(n_regions=1)
    set_region(lib, w, 0, tier=OMTier.HOME, military=0.0, economy=50.0,
               tension=0.0, population=100.0)
    lib.om_world_step(w)
    _, row = read_drift(lib, w, 0)
    assert row.population_base == 0.0
