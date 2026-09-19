"""S-014 -- People make money, unrest and overreach cost it.

R-014-01 .. R-014-04. Formulas: ALG-05 (economy growth/drag/overcapacity) in
algorithms.md. R-014-01..03 are tested at tick 1, where primed trend equals
the raw field (R-018-02), reading the individual ALG-05 legs out of
om_drift_row -- those legs exclude the oscillator delta (ALG-01), so no
phase needs setting for them regardless of the default econ_phase. R-014-04
reads the final field instead (om_region_field), which does include the
oscillator delta, so it sets econ_phase explicitly to keep that leg from
swamping the drift under test.
"""
import math

import pytest

from conftest import OMField, OMTier, read_drift, set_region


def test_R_014_01_growth_drag_no_overcap(lib, world_factory):
    w = world_factory(n_regions=1)
    set_region(lib, w, 0, tier=OMTier.HOME, military=0.0, economy=30.0,
               tension=20.0, population=50.0)
    lib.om_world_step(w)
    _, row = read_drift(lib, w, 0)

    assert row.economy_growth == pytest.approx(1.0, abs=1e-9)
    assert row.economy_drag == pytest.approx(-0.08, abs=1e-9)
    assert row.economy_overcap == 0.0
    assert (row.economy_growth + row.economy_drag + row.economy_overcap) == pytest.approx(0.920, abs=1e-9)


def test_R_014_02_overcapacity_decay_exact(lib, world_factory):
    w = world_factory(n_regions=1)
    # tension 0 zeroes the drag leg so overcap and growth are cleanly isolated.
    set_region(lib, w, 0, tier=OMTier.HOME, military=0.0, economy=60.0,
               tension=0.0, population=50.0)
    lib.om_world_step(w)
    _, row = read_drift(lib, w, 0)

    assert row.economy_growth == pytest.approx(1.0, abs=1e-9)
    assert row.economy_drag == 0.0
    assert row.economy_overcap == pytest.approx(-2.625, abs=1e-9)


def test_R_014_03_overcapacity_zero_at_capacity_boundary(lib, world_factory):
    w = world_factory(n_regions=2)
    # population 50 => capacity = 42.5 exactly.
    set_region(lib, w, 0, tier=OMTier.HOME, military=0.0, economy=42.5,
               tension=0.0, population=50.0)
    set_region(lib, w, 1, tier=OMTier.HOME, military=0.0, economy=42.6,
               tension=0.0, population=50.0)
    lib.om_world_step(w)
    _, at_capacity = read_drift(lib, w, 0)
    _, above_capacity = read_drift(lib, w, 1)

    assert at_capacity.economy_overcap == 0.0
    assert above_capacity.economy_overcap < -1e-9


def test_R_014_04_economy_floor_holds_under_negative_drift(lib, world_factory):
    w = world_factory(n_regions=1)
    # population 0 kills growth; tension 100 maxes drag; capacity is 0 so any
    # economy above it decays hard -- net drift is sharply negative from 8.5.
    # econ_phase=pi keeps ALG-01's oscillator delta (+2.44 at the default
    # phase 0.0, which would leave economy at 9.27, never reaching the
    # floor) from working against the negative drift under test.
    set_region(lib, w, 0, tier=OMTier.HOME, military=0.0, economy=8.5,
               tension=100.0, population=0.0, econ_phase=math.pi)
    lib.om_world_step(w)
    economy = lib.om_region_field(w, 0, OMField.ECONOMY)
    assert economy == 8.0
