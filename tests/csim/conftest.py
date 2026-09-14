"""Fenced test harness for the E-02 C sim-core ABI.

Loads libouroboros.so (release) and libouroboros_dbg.so (fault-injection build)
via ctypes, mirrors every struct and enum in csrc/ouroboros_sim.h exactly, and
exposes small fixtures/helpers the per-story test modules build on.

If a .so file has not been built yet, the corresponding fixture skips with a
clear reason -- there is nothing to link against. If the .so exists but is
missing a symbol the ABI declares (a built-but-incomplete implementation),
attribute lookup on the ctypes handle raises AttributeError uncaught, which
fails every dependent test loudly (red), per the QA plan for this suite.
"""
import ctypes
import math
import pathlib

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
LIB_PATH = REPO_ROOT / "libouroboros.so"
DBG_LIB_PATH = REPO_ROOT / "libouroboros_dbg.so"

# The header (csrc/ouroboros_sim.h) does not pin a literal integer anywhere;
# it only says the harness "asserts this matches what it was written against."
# This suite is written against the first revision of the header, version 1.
EXPECTED_ABI_VERSION = 1


# ---- enum mirrors (om_field / om_composite / om_tier / om_bug) ----

class OMField:
    MILITARY = 0
    ECONOMY = 1
    TENSION = 2
    POPULATION = 3
    COUNT = 4


class OMComposite:
    STABILITY = 0
    CAPACITY = 1
    COUNT = 2


class OMTier:
    EMPTY = 0
    FRONTIER = 1
    HOME = 2


class OMBug:
    OSC_AS_LEVEL = 0
    RAW_NOT_TREND = 1
    COMPOSITE_PRE_CLAMP = 2
    EMPTY_DRIFTS = 3
    GE_NOT_GT = 4
    SLOW = 5


# ---- struct mirrors (field order/types must match the header exactly) ----

class OmDriftRow(ctypes.Structure):
    _fields_ = [
        ("military_decay", ctypes.c_double),
        ("military_recruit", ctypes.c_double),
        ("military_modifier", ctypes.c_double),
        ("economy_growth", ctypes.c_double),
        ("economy_drag", ctypes.c_double),
        ("economy_overcap", ctypes.c_double),
        ("economy_adjacency", ctypes.c_double),
        ("economy_osc_delta", ctypes.c_double),
        ("tension_economic", ctypes.c_double),
        ("tension_stress", ctypes.c_double),
        ("tension_subsist", ctypes.c_double),
        ("tension_decay", ctypes.c_double),
        ("tension_osc_delta", ctypes.c_double),
        ("population_base", ctypes.c_double),
        ("population_subsist", ctypes.c_double),
        ("d_military", ctypes.c_double),
        ("d_economy", ctypes.c_double),
        ("d_tension", ctypes.c_double),
        ("d_population", ctypes.c_double),
    ]


class OmTraceRow(ctypes.Structure):
    _fields_ = [
        ("tick", ctypes.c_uint64),
        ("region_idx", ctypes.c_uint32),
        ("faction_id", ctypes.c_int32),
        ("tier", ctypes.c_uint32),
        ("_pad", ctypes.c_uint32),
        ("military", ctypes.c_double),
        ("economy", ctypes.c_double),
        ("tension", ctypes.c_double),
        ("population", ctypes.c_double),
        ("stability", ctypes.c_double),
        ("capacity", ctypes.c_double),
        ("drift", OmDriftRow),
        ("checksum", ctypes.c_uint64),
    ]


class OMWorld(ctypes.Structure):
    """Opaque; never dereferenced from Python, only passed as a pointer."""


OMWorldP = ctypes.POINTER(OMWorld)


def _configure_common(h):
    """Set argtypes/restype for every function in ouroboros_sim.h except
    om_debug_inject, which exists only in the debug-injection build."""
    h.om_abi_version.argtypes = []
    h.om_abi_version.restype = ctypes.c_uint32

    h.om_world_new.argtypes = [ctypes.c_uint32, ctypes.c_uint64]
    h.om_world_new.restype = OMWorldP

    h.om_world_free.argtypes = [OMWorldP]
    h.om_world_free.restype = None

    h.om_world_set_seed.argtypes = [OMWorldP, ctypes.c_uint64]
    h.om_world_set_seed.restype = None

    h.om_world_generate.argtypes = [OMWorldP]
    h.om_world_generate.restype = None

    h.om_region_set.argtypes = [
        OMWorldP, ctypes.c_uint32, ctypes.c_int,
        ctypes.c_double, ctypes.c_double, ctypes.c_double, ctypes.c_double,
        ctypes.c_double, ctypes.c_double, ctypes.c_int32,
    ]
    h.om_region_set.restype = ctypes.c_int

    h.om_region_set_adjacency.argtypes = [
        OMWorldP, ctypes.c_uint32, ctypes.POINTER(ctypes.c_uint32), ctypes.c_uint32,
    ]
    h.om_region_set_adjacency.restype = None

    h.om_region_set_faction_modifier.argtypes = [
        OMWorldP, ctypes.c_int32, ctypes.c_int, ctypes.c_double,
    ]
    h.om_region_set_faction_modifier.restype = None

    h.om_region_count.argtypes = [OMWorldP]
    h.om_region_count.restype = ctypes.c_uint32

    h.om_world_step.argtypes = [OMWorldP]
    h.om_world_step.restype = ctypes.c_uint64

    h.om_world_run.argtypes = [OMWorldP, ctypes.c_uint64]
    h.om_world_run.restype = ctypes.c_uint64

    h.om_region_field.argtypes = [OMWorldP, ctypes.c_uint32, ctypes.c_int]
    h.om_region_field.restype = ctypes.c_double

    h.om_region_composite.argtypes = [OMWorldP, ctypes.c_uint32, ctypes.c_int]
    h.om_region_composite.restype = ctypes.c_double

    h.om_region_tier.argtypes = [OMWorldP, ctypes.c_uint32]
    h.om_region_tier.restype = ctypes.c_int

    h.om_region_drift.argtypes = [OMWorldP, ctypes.c_uint32, ctypes.POINTER(OmDriftRow)]
    h.om_region_drift.restype = ctypes.c_int

    h.om_world_checksum.argtypes = [OMWorldP]
    h.om_world_checksum.restype = ctypes.c_uint64

    h.om_checksum_cadence.argtypes = []
    h.om_checksum_cadence.restype = ctypes.c_uint32

    h.om_sin.argtypes = [ctypes.c_double]
    h.om_sin.restype = ctypes.c_double

    h.om_trace_enable.argtypes = [OMWorldP, ctypes.c_int]
    h.om_trace_enable.restype = None

    h.om_trace_len.argtypes = [OMWorldP]
    h.om_trace_len.restype = ctypes.c_uint64

    h.om_trace_read.argtypes = [
        OMWorldP, ctypes.c_uint64, ctypes.c_uint64, ctypes.POINTER(OmTraceRow),
    ]
    h.om_trace_read.restype = ctypes.c_uint64


def _configure_debug(h):
    h.om_debug_inject.argtypes = [OMWorldP, ctypes.c_int]
    h.om_debug_inject.restype = None


@pytest.fixture(scope="session")
def lib():
    if not LIB_PATH.exists():
        pytest.skip(f"libouroboros.so not built at {LIB_PATH}; run `make` first")
    handle = ctypes.CDLL(str(LIB_PATH))
    _configure_common(handle)
    version = handle.om_abi_version()
    assert version == EXPECTED_ABI_VERSION, (
        f"om_abi_version() returned {version}, expected {EXPECTED_ABI_VERSION} "
        "(this suite's contract version of csrc/ouroboros_sim.h)"
    )
    return handle


@pytest.fixture(scope="session")
def dbg():
    if not DBG_LIB_PATH.exists():
        pytest.skip(f"libouroboros_dbg.so not built at {DBG_LIB_PATH}; run `make` first")
    handle = ctypes.CDLL(str(DBG_LIB_PATH))
    _configure_common(handle)
    _configure_debug(handle)
    version = handle.om_abi_version()
    assert version == EXPECTED_ABI_VERSION, (
        f"om_abi_version() returned {version}, expected {EXPECTED_ABI_VERSION} "
        "(this suite's contract version of csrc/ouroboros_sim.h)"
    )
    return handle


def _world_factory_for(handle):
    created = []

    def _make(n_regions=1, seed=1):
        w = handle.om_world_new(ctypes.c_uint32(n_regions), ctypes.c_uint64(seed))
        assert w, "om_world_new returned NULL"
        created.append(w)
        return w

    return _make, created


@pytest.fixture
def world_factory(lib):
    make, created = _world_factory_for(lib)
    yield make
    for w in created:
        lib.om_world_free(w)


@pytest.fixture
def dbg_world_factory(dbg):
    make, created = _world_factory_for(dbg)
    yield make
    for w in created:
        dbg.om_world_free(w)


# ---- shared helpers (plain functions, imported by the story test modules) ----

def set_region(lib, w, idx, *, tier=OMTier.HOME, military=0.0, economy=0.0,
                tension=0.0, population=0.0, econ_phase=0.0, tension_phase=0.0,
                faction_id=-1):
    rc = lib.om_region_set(
        w, idx, tier, military, economy, tension, population,
        econ_phase, tension_phase, faction_id,
    )
    assert rc == 0, f"om_region_set failed for region {idx}: rc={rc}"


def read_drift(lib, w, idx):
    row = OmDriftRow()
    rc = lib.om_region_drift(w, idx, ctypes.byref(row))
    return rc, row


def osc(lib, amplitude, period, phase, tick):
    """ALG-01 oscillator kernel, computed via the sim's own deterministic
    om_sin so oracle values in these tests use the same sine the C code does."""
    return amplitude * lib.om_sin(2.0 * math.pi * tick / period + phase)


ECON_AMPLITUDE = 6.0
ECON_PERIOD = 15
TENSION_AMPLITUDE = 2.0
TENSION_PERIOD = 18
