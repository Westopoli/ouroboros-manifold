"""S-016 -- Hardship breeds unrest, unrest burns itself out.

R-016-01 .. R-016-05. Formula: ALG-07 (tension drift) in algorithms.md.
Tested at tick 1 (primed trend == raw field, R-018-02). Where a rule gives
stability as an input ("Given ... stability 60"), the region's military
field is chosen so ALG-09 produces that exact stability from the region's
own (military, tension, population) -- the stress term reads the region's
own de-oscillated stability, not an independently injectable value.
"""
import pytest

from conftest import OMTier, read_drift, set_region


def test_R_016_01_full_tension_delta_below_stress_threshold(lib, world_factory):
    w = world_factory(n_regions=1)
    # military 48.75 makes stability(m, t=20, p=50) == 60.00 exactly.
    set_region(lib, w, 0, tier=OMTier.HOME, military=48.75, economy=30.0,
               tension=20.0, population=50.0)
    lib.om_world_step(w)
    _, row = read_drift(lib, w, 0)

    assert row.tension_economic == pytest.approx(0.050, abs=1e-9)
    assert row.tension_stress == pytest.approx(0.0, abs=1e-9)
    assert row.tension_subsist == pytest.approx(0.0, abs=1e-9)
    assert row.tension_decay == pytest.approx(-0.040, abs=1e-9)
    total = row.tension_economic + row.tension_stress + row.tension_subsist + row.tension_decay
    assert total == pytest.approx(0.010, abs=1e-9)


def test_R_016_02_stress_pressure_exact(lib, world_factory):
    w = world_factory(n_regions=1)
    # military 62.5, tension 100, population 20 makes stability == 30.00.
    set_region(lib, w, 0, tier=OMTier.HOME, military=62.5, economy=50.0,
               tension=100.0, population=20.0)
    lib.om_world_step(w)
    _, row = read_drift(lib, w, 0)
    assert row.tension_stress == pytest.approx(0.080, abs=1e-9)


def test_R_016_03_subsistence_pressure_exact(lib, world_factory):
    w = world_factory(n_regions=1)
    set_region(lib, w, 0, tier=OMTier.HOME, military=50.0, economy=9.5,
               tension=0.0, population=50.0)
    lib.om_world_step(w)
    _, row = read_drift(lib, w, 0)
    assert row.tension_subsist == pytest.approx(0.0375, abs=1e-9)


def test_R_016_04_subsistence_threshold_at_11(lib, world_factory):
    w = world_factory(n_regions=2)
    set_region(lib, w, 0, tier=OMTier.HOME, military=50.0, economy=11.0,
               tension=0.0, population=50.0)
    set_region(lib, w, 1, tier=OMTier.HOME, military=50.0, economy=10.99,
               tension=0.0, population=50.0)
    lib.om_world_step(w)
    _, at_threshold = read_drift(lib, w, 0)
    _, below_threshold = read_drift(lib, w, 1)
    assert at_threshold.tension_subsist == 0.0
    assert below_threshold.tension_subsist > 0.0


def test_R_016_05_prosperity_calms_tension(lib, world_factory):
    w = world_factory(n_regions=1)
    set_region(lib, w, 0, tier=OMTier.HOME, military=50.0, economy=70.0,
               tension=0.0, population=50.0)
    lib.om_world_step(w)
    _, row = read_drift(lib, w, 0)
    assert row.tension_economic == pytest.approx(-0.050, abs=1e-9)
