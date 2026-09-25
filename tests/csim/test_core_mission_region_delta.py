"""test_core_mission_region_delta.py
om_mission_get_region_delta accessor (T1-8, S-078 accessor path).

Returns 1 with per-field deltas after om_mission_apply_consequences is called;
0 before any consequence; second call overwrites, does not accumulate.
Local argtypes setup: do not edit conftest.py for this symbol.
"""
import ctypes
import pytest

from conftest import OMField, OMWorldP, set_region

OM_ARCH_DEFENSIVE_STAND = 0
OM_BAND_TOTAL_SUCCESS = 4


def _bind_region_delta(lib):
    """Set argtypes/restype for om_mission_get_region_delta on lib, once."""
    if getattr(lib, "_region_delta_bound", False):
        return
    P = ctypes.POINTER
    W = OMWorldP
    lib.om_mission_get_region_delta.argtypes = [
        W,
        P(ctypes.c_double),
        P(ctypes.c_double),
        P(ctypes.c_double),
        P(ctypes.c_double),
    ]
    lib.om_mission_get_region_delta.restype = ctypes.c_int
    lib._region_delta_bound = True


@pytest.fixture(autouse=True)
def _bind(lib):
    _bind_region_delta(lib)


def test_returns_0_before_any_consequence(lib, world_factory):
    """Before any consequence, om_mission_get_region_delta returns 0."""
    w = world_factory(n_regions=1)
    mil = ctypes.c_double()
    econ = ctypes.c_double()
    tens = ctypes.c_double()
    pop = ctypes.c_double()
    rc = lib.om_mission_get_region_delta(
        w,
        ctypes.byref(mil), ctypes.byref(econ),
        ctypes.byref(tens), ctypes.byref(pop),
    )
    assert rc == 0


def test_returns_1_with_correct_deltas_after_consequence(lib, world_factory):
    """After defensive_stand total_success, returns 1; deltas == after - before via om_region_field."""
    w = world_factory(n_regions=1)
    set_region(lib, w, 0, military=20.0, economy=50.0, tension=50.0, population=50.0)

    before_mil = lib.om_region_field(w, 0, OMField.MILITARY)
    before_econ = lib.om_region_field(w, 0, OMField.ECONOMY)
    before_tens = lib.om_region_field(w, 0, OMField.TENSION)
    before_pop = lib.om_region_field(w, 0, OMField.POPULATION)

    lib.om_mission_apply_consequences(
        w, 0, OM_ARCH_DEFENSIVE_STAND, OM_BAND_TOTAL_SUCCESS
    )

    after_mil = lib.om_region_field(w, 0, OMField.MILITARY)
    after_econ = lib.om_region_field(w, 0, OMField.ECONOMY)
    after_tens = lib.om_region_field(w, 0, OMField.TENSION)
    after_pop = lib.om_region_field(w, 0, OMField.POPULATION)

    mil = ctypes.c_double()
    econ = ctypes.c_double()
    tens = ctypes.c_double()
    pop = ctypes.c_double()
    rc = lib.om_mission_get_region_delta(
        w,
        ctypes.byref(mil), ctypes.byref(econ),
        ctypes.byref(tens), ctypes.byref(pop),
    )

    assert rc == 1
    assert mil.value != 0.0, "military delta must be non-zero (deficit form, 20->32)"
    assert econ.value != 0.0, "economy delta must be non-zero (current form, 50->49)"
    assert tens.value != 0.0, "tension delta must be non-zero (current form, 50->45)"
    assert mil.value == pytest.approx(after_mil - before_mil, abs=1e-9)
    assert econ.value == pytest.approx(after_econ - before_econ, abs=1e-9)
    assert tens.value == pytest.approx(after_tens - before_tens, abs=1e-9)
    assert pop.value == pytest.approx(after_pop - before_pop, abs=1e-9)


def test_population_delta_is_zero(lib, world_factory):
    """Population is not in any consequence table row; its delta must be 0."""
    w = world_factory(n_regions=1)
    set_region(lib, w, 0, military=20.0, economy=50.0, tension=50.0, population=50.0)
    lib.om_mission_apply_consequences(
        w, 0, OM_ARCH_DEFENSIVE_STAND, OM_BAND_TOTAL_SUCCESS
    )
    pop = ctypes.c_double()
    rc = lib.om_mission_get_region_delta(w, None, None, None, ctypes.byref(pop))
    assert rc == 1
    assert pop.value == pytest.approx(0.0, abs=1e-9)


def test_null_out_params_tolerated(lib, world_factory):
    """All-NULL out params: returns 1 without crash when consequence applied."""
    w = world_factory(n_regions=1)
    set_region(lib, w, 0, military=20.0, economy=50.0, tension=50.0, population=50.0)
    lib.om_mission_apply_consequences(
        w, 0, OM_ARCH_DEFENSIVE_STAND, OM_BAND_TOTAL_SUCCESS
    )
    rc = lib.om_mission_get_region_delta(w, None, None, None, None)
    assert rc == 1


def test_second_consequence_overwrites_not_accumulates(lib, world_factory):
    """Second apply_consequences overwrites stored delta; does not accumulate."""
    w = world_factory(n_regions=1)
    set_region(lib, w, 0, military=20.0, economy=50.0, tension=50.0, population=50.0)

    # First consequence.
    lib.om_mission_apply_consequences(
        w, 0, OM_ARCH_DEFENSIVE_STAND, OM_BAND_TOTAL_SUCCESS
    )

    # State after first consequence becomes 'before' for the second.
    before2_mil = lib.om_region_field(w, 0, OMField.MILITARY)
    before2_econ = lib.om_region_field(w, 0, OMField.ECONOMY)
    before2_tens = lib.om_region_field(w, 0, OMField.TENSION)
    before2_pop = lib.om_region_field(w, 0, OMField.POPULATION)

    # Second consequence (same archetype/band, different field starting values).
    lib.om_mission_apply_consequences(
        w, 0, OM_ARCH_DEFENSIVE_STAND, OM_BAND_TOTAL_SUCCESS
    )

    after2_mil = lib.om_region_field(w, 0, OMField.MILITARY)
    after2_econ = lib.om_region_field(w, 0, OMField.ECONOMY)
    after2_tens = lib.om_region_field(w, 0, OMField.TENSION)
    after2_pop = lib.om_region_field(w, 0, OMField.POPULATION)

    mil = ctypes.c_double()
    econ = ctypes.c_double()
    tens = ctypes.c_double()
    pop = ctypes.c_double()
    rc = lib.om_mission_get_region_delta(
        w,
        ctypes.byref(mil), ctypes.byref(econ),
        ctypes.byref(tens), ctypes.byref(pop),
    )
    assert rc == 1
    # Delta must match the SECOND call's changes only.
    assert mil.value == pytest.approx(after2_mil - before2_mil, abs=1e-9)
    assert econ.value == pytest.approx(after2_econ - before2_econ, abs=1e-9)
    assert tens.value == pytest.approx(after2_tens - before2_tens, abs=1e-9)
    assert pop.value == pytest.approx(after2_pop - before2_pop, abs=1e-9)
    # Sanity: second delta must be distinct from first (field values changed).
    # If the two deltas were equal this test would be vacuous; but arithmetic
    # on changed field values produces different deficit/current-form results.
