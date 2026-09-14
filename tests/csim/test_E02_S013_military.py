"""S-013 -- Armies cost money and grow in peace.

R-013-01 .. R-013-06. Formulas: ALG-02 (decay), ALG-03 (recruitment),
ALG-04 (faction modifier) in algorithms.md.

All single-leg tests step the world exactly once (tick 1), where the primed
(de-oscillated) trend equals the raw field (previous oscillator value is 0
per R-018-02), so the given "military X, economy Y" numbers apply directly
with no oscillator contamination.
"""
import pytest

from conftest import OMField, OMTier, read_drift, set_region


def test_R_013_01_decay_leg_exact(lib, world_factory):
    w = world_factory(n_regions=1)
    set_region(lib, w, 0, tier=OMTier.HOME, military=50.0, economy=0.0,
               tension=0.0, population=0.0)
    lib.om_world_step(w)
    _, row = read_drift(lib, w, 0)
    assert row.military_decay == pytest.approx(-0.300, abs=1e-9)


def test_R_013_02_decay_leg_zero_at_full_economy(lib, world_factory):
    w = world_factory(n_regions=1)
    set_region(lib, w, 0, tier=OMTier.HOME, military=50.0, economy=100.0,
               tension=0.0, population=0.0)
    lib.om_world_step(w)
    _, row = read_drift(lib, w, 0)
    assert row.military_decay == 0.0


def test_R_013_03_recruit_leg_within_tolerance(lib, world_factory):
    w = world_factory(n_regions=1)
    set_region(lib, w, 0, tier=OMTier.HOME, military=50.0, economy=60.0,
               tension=20.0, population=50.0)
    lib.om_world_step(w)
    _, row = read_drift(lib, w, 0)
    assert row.military_recruit == pytest.approx(1.5186, abs=1e-3)


def test_R_013_04_recruit_threshold_strictly_greater(lib, world_factory):
    # At economy exactly 20.0 the eco-scaled term must be excluded (threshold
    # is "> 20", not ">= 20"). Baseline-only recruit (economy 0, same military
    # and population) is the value expected at exactly 20.0; a economy value
    # just above 20 must recruit strictly more.
    w = world_factory(n_regions=3)
    set_region(lib, w, 0, tier=OMTier.HOME, military=50.0, economy=0.0,
               tension=0.0, population=50.0)
    set_region(lib, w, 1, tier=OMTier.HOME, military=50.0, economy=20.0,
               tension=0.0, population=50.0)
    set_region(lib, w, 2, tier=OMTier.HOME, military=50.0, economy=20.5,
               tension=0.0, population=50.0)
    lib.om_world_step(w)
    _, baseline = read_drift(lib, w, 0)
    _, at_threshold = read_drift(lib, w, 1)
    _, above_threshold = read_drift(lib, w, 2)

    assert at_threshold.military_recruit == pytest.approx(baseline.military_recruit, abs=1e-9)
    assert above_threshold.military_recruit > at_threshold.military_recruit + 1e-9


def test_R_013_05_recruit_zero_at_and_above_ceiling(lib, world_factory):
    w = world_factory(n_regions=2)
    set_region(lib, w, 0, tier=OMTier.HOME, military=90.0, economy=60.0,
               tension=20.0, population=50.0)
    set_region(lib, w, 1, tier=OMTier.HOME, military=95.0, economy=60.0,
               tension=20.0, population=50.0)
    lib.om_world_step(w)
    _, at_ceiling = read_drift(lib, w, 0)
    _, above_ceiling = read_drift(lib, w, 1)
    assert at_ceiling.military_recruit == 0.0
    assert above_ceiling.military_recruit == 0.0


def test_R_013_06_conqueror_faction_modifier(lib, world_factory):
    conqueror_faction = 7
    w = world_factory(n_regions=1)
    lib.om_region_set_faction_modifier(w, conqueror_faction, OMField.MILITARY, 0.05)
    set_region(lib, w, 0, tier=OMTier.HOME, military=50.0, economy=60.0,
               tension=20.0, population=50.0, faction_id=conqueror_faction)
    lib.om_world_step(w)
    _, row = read_drift(lib, w, 0)
    headroom = 1.0 - 50.0 / 90.0
    expected = 0.05 * headroom
    assert row.military_modifier == pytest.approx(expected, abs=1e-9)
