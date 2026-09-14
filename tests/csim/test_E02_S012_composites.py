"""S-012 -- Every region has four fields and two composites.

R-012-01 .. R-012-07 (docs/bible/epics/E-02-region-fields-and-drift.md).
Composite formulas: ALG-09 (stability), ALG-10 (capacity) in algorithms.md.
"""
from conftest import OMComposite, OMField, OMTier, read_drift, set_region


def _rounded2(value):
    return abs(value - round(value, 2)) < 1e-9


def test_R_012_01_fields_ranged_and_composites_rounded(lib, world_factory):
    w = world_factory(n_regions=1)
    set_region(lib, w, 0, tier=OMTier.HOME, military=42.0, economy=66.0,
               tension=18.0, population=60.0)

    for field in (OMField.MILITARY, OMField.ECONOMY, OMField.TENSION, OMField.POPULATION):
        value = lib.om_region_field(w, 0, field)
        assert 0.0 <= value <= 100.0

    stability = lib.om_region_composite(w, 0, OMComposite.STABILITY)
    capacity = lib.om_region_composite(w, 0, OMComposite.CAPACITY)
    assert _rounded2(stability), f"stability {stability} not rounded to 2dp"
    assert _rounded2(capacity), f"capacity {capacity} not rounded to 2dp"


def test_R_012_02_stability_exact(lib, world_factory):
    w = world_factory(n_regions=1)
    set_region(lib, w, 0, tier=OMTier.HOME, military=40.0, economy=50.0,
               tension=20.0, population=60.0)
    stability = lib.om_region_composite(w, 0, OMComposite.STABILITY)
    assert stability == 59.00


def test_R_012_03_stability_military_penalty(lib, world_factory):
    w = world_factory(n_regions=1)
    set_region(lib, w, 0, tier=OMTier.HOME, military=8.0, economy=50.0,
               tension=20.0, population=60.0)
    stability = lib.om_region_composite(w, 0, OMComposite.STABILITY)
    assert stability == 32.34


def test_R_012_04_stability_both_penalties(lib, world_factory):
    w = world_factory(n_regions=1)
    set_region(lib, w, 0, tier=OMTier.HOME, military=8.0, economy=50.0,
               tension=20.0, population=15.0)
    stability = lib.om_region_composite(w, 0, OMComposite.STABILITY)
    assert stability == 18.35


def test_R_012_05_capacity_exact(lib, world_factory):
    w = world_factory(n_regions=1)
    set_region(lib, w, 0, tier=OMTier.HOME, military=30.0, economy=60.0,
               tension=0.0, population=50.0)
    capacity = lib.om_region_composite(w, 0, OMComposite.CAPACITY)
    assert capacity == 52.00


def test_R_012_06_capacity_both_penalties(lib, world_factory):
    w = world_factory(n_regions=1)
    set_region(lib, w, 0, tier=OMTier.HOME, military=30.0, economy=15.0,
               tension=0.0, population=10.0)
    capacity = lib.om_region_composite(w, 0, OMComposite.CAPACITY)
    assert capacity == 7.05


def test_R_012_07_empty_region_zeroed_and_never_drifts(lib, world_factory):
    w = world_factory(n_regions=2)
    set_region(lib, w, 0, tier=OMTier.EMPTY, military=0.0, economy=0.0,
               tension=0.0, population=0.0)
    # A booming inhabited neighbor to prove the empty region draws nothing
    # from its surroundings either (paired with S-015 R-015-04).
    set_region(lib, w, 1, tier=OMTier.HOME, military=80.0, economy=90.0,
               tension=10.0, population=80.0)

    for field in (OMField.MILITARY, OMField.ECONOMY, OMField.TENSION, OMField.POPULATION):
        assert lib.om_region_field(w, 0, field) == 0.0
    assert lib.om_region_composite(w, 0, OMComposite.STABILITY) == 0.0
    assert lib.om_region_composite(w, 0, OMComposite.CAPACITY) == 0.0

    rc, _ = read_drift(lib, w, 0)
    assert rc != 0, "om_region_drift must report non-zero for an empty region"

    lib.om_world_step(w)
    for field in (OMField.MILITARY, OMField.ECONOMY, OMField.TENSION, OMField.POPULATION):
        assert lib.om_region_field(w, 0, field) == 0.0
