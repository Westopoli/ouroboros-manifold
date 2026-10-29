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
import re
import tomllib

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
LIB_PATH = REPO_ROOT / "libouroboros.so"
DBG_LIB_PATH = REPO_ROOT / "libouroboros_dbg.so"
CSRC_DIR = REPO_ROOT / "csrc"
MVP_FEATURES_PATH = REPO_ROOT / "docs/northstar/spec_factory/mvp_features.toml"


BUILD_ERROR = None


def _build_libs():
    """Compile the C sim libraries before loading, so any pytest run self-builds
    (mirrors the proving-ground conftest). A make failure while csrc/*.c exist is
    a real compile error: the stale libraries are removed so no test can run
    against the previous build, and the compiler output is kept so every test
    fails with it (the build harness feeds that failure text back to the worker).
    With no csrc/*.c there is nothing to build yet and the fixtures skip."""
    global BUILD_ERROR
    import subprocess
    try:
        res = subprocess.run(["make", "-s", "libouroboros.so", "libouroboros_dbg.so"],
                             cwd=str(REPO_ROOT), capture_output=True, text=True, timeout=180)
    except Exception as exc:  # make missing or timed out: same treatment as a failed build
        res = None
        BUILD_ERROR = f"make could not run: {exc}"
    if res is not None and res.returncode != 0:
        BUILD_ERROR = (res.stderr or res.stdout)[-4000:]
    if BUILD_ERROR:
        for lib_path in (LIB_PATH, DBG_LIB_PATH):
            try:
                lib_path.unlink()
            except FileNotFoundError:
                pass


_HAS_CSRC = CSRC_DIR.exists() and any(CSRC_DIR.glob("*.c"))
_build_libs()

# The header (csrc/ouroboros_sim.h) does not pin a literal integer anywhere;
# it only says the harness "asserts this matches what it was written against."
# Bumped to 2 at freeze/F2 (OM_FEAT_TACTICAL, the E-06/E-07/E-11 tick-order
# bug ids, and om_world_get_state_checksum / om_world_set_tick /
# om_abi_layout_check are new since version 1).
EXPECTED_ABI_VERSION = 9


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
    DRIFT_GATE_IGNORED = 6
    LIBM_POW = 7
    RNG_UNSEEDED = 8


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

    h.om_tactical_step.argtypes = [OMWorldP]
    h.om_tactical_step.restype = ctypes.c_uint64

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

    h.om_world_get_state_checksum.argtypes = [OMWorldP]
    h.om_world_get_state_checksum.restype = ctypes.c_uint64

    h.om_world_set_tick.argtypes = [OMWorldP, ctypes.c_uint64]
    h.om_world_set_tick.restype = None

    h.om_abi_layout_check.argtypes = [ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32]
    h.om_abi_layout_check.restype = ctypes.c_int

    h.om_checksum_cadence.argtypes = []
    h.om_checksum_cadence.restype = ctypes.c_uint32

    h.om_sin.argtypes = [ctypes.c_double]
    h.om_sin.restype = ctypes.c_double

    h.om_pow.argtypes = [ctypes.c_double, ctypes.c_double]
    h.om_pow.restype = ctypes.c_double

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


def load_lib():
    if not LIB_PATH.exists() and _HAS_CSRC:
        raise RuntimeError(
            "COMPILE ERROR: csrc/*.c present but libouroboros.so did not build:\n"
            + (BUILD_ERROR or "(no compiler output captured; run `make`)")
        )
    handle = ctypes.CDLL(str(LIB_PATH))
    _configure_common(handle)
    _bind_generated(handle)
    version = handle.om_abi_version()
    assert version == EXPECTED_ABI_VERSION, (
        f"om_abi_version() returned {version}, expected {EXPECTED_ABI_VERSION} "
        "(this suite's contract version of csrc/ouroboros_sim.h)"
    )
    return handle


@pytest.fixture(scope="session")
def lib():
    if not LIB_PATH.exists():
        if _HAS_CSRC:
            pytest.fail("COMPILE ERROR: csrc/*.c present but libouroboros.so did not build:\n"
                        + (BUILD_ERROR or "(no compiler output captured; run `make`)"))
        pytest.skip("no csrc/*.c implementation yet; nothing to build")
    return load_lib()


@pytest.fixture(scope="session")
def dbg():
    if not DBG_LIB_PATH.exists():
        if _HAS_CSRC:
            pytest.fail("COMPILE ERROR: csrc/*.c present but libouroboros_dbg.so did not build:\n"
                        + (BUILD_ERROR or "(no compiler output captured; run `make`)"))
        pytest.skip("no csrc/*.c implementation yet; nothing to build")
    handle = ctypes.CDLL(str(DBG_LIB_PATH))
    _configure_common(handle)
    _configure_debug(handle)
    _bind_generated(handle)
    version = handle.om_abi_version()
    assert version == EXPECTED_ABI_VERSION, (
        f"om_abi_version() returned {version}, expected {EXPECTED_ABI_VERSION} "
        "(this suite's contract version of csrc/ouroboros_sim.h)"
    )
    return handle


_MVP_FEATURES = None


def _mvp_features():
    global _MVP_FEATURES
    if _MVP_FEATURES is None:
        with open(MVP_FEATURES_PATH, "rb") as f:
            _MVP_FEATURES = tomllib.load(f)
    return _MVP_FEATURES


_EPIC_RE = re.compile(r"^test_e(\d+)_", re.IGNORECASE)
_EPIC_CONTROL_RE = re.compile(r"^test_control_e(\d+)_", re.IGNORECASE)


def _epic_for_module(stem):
    """D1 (mvp_features.toml): the epic a test module's world_factory /
    dbg_world_factory calls apply the [isolation] set for, derived from the
    module's own filename -- `test_E##_...` (the story modules) or
    `test_control_e##_...` (the per-epic positive controls). An un-prefixed
    `test_control_...` file is one of the original E-02 drift/oscillator bug
    controls (test_control_osc_as_level.py and friends, predating the E-03+
    per-epic control naming), so it falls to E-02. Anything else gets no
    epic and falls to [default]."""
    m = _EPIC_RE.match(stem) or _EPIC_CONTROL_RE.match(stem)
    if m:
        return f"E-{int(m.group(1)):02d}"
    if stem.startswith("test_control_"):
        return "E-02"
    return None


def _feature_names_for_epic(epic):
    cfg = _mvp_features()
    isolation = cfg.get("isolation", {})
    if epic and epic in isolation:
        return isolation[epic]
    return cfg.get("default", {}).get("features", [])


def _apply_epic_features(handle, w, epic):
    """D1: om_world_new() sets no feature any more; apply the calling test's
    epic set (or [default]) on top of the raw world, mirroring what the
    DRIFT-on default used to do globally, now scoped per epic."""
    for name in _feature_names_for_epic(epic):
        handle.om_world_set_feature(w, getattr(OMFeature, name), 1)


def _world_factory_for(handle, epic):
    created = []

    def _make(n_regions=1, seed=1):
        w = handle.om_world_new(ctypes.c_uint32(n_regions), ctypes.c_uint64(seed))
        assert w, "om_world_new returned NULL"
        created.append(w)
        _apply_epic_features(handle, w, epic)
        return w

    return _make, created


@pytest.fixture
def world_factory(lib, request):
    epic = _epic_for_module(pathlib.Path(request.module.__file__).stem)
    make, created = _world_factory_for(lib, epic)
    yield make
    for w in created:
        lib.om_world_free(w)


@pytest.fixture
def dbg_world_factory(dbg, request):
    epic = _epic_for_module(pathlib.Path(request.module.__file__).stem)
    make, created = _world_factory_for(dbg, epic)
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


# ======================================================================
# ---- E-05: faction agents and conflict (appended 2026-09-14) ----
# Mirrors the E-05 block of csrc/ouroboros_sim.h exactly. Nothing above changes.
# ======================================================================

OM_MAX_FACTIONS = 64
OM_MAX_COLLIDERS = 8
UINT32_NONE = 0xFFFFFFFF


class OMFeature:
    EVENTS = 0
    FACTIONS = 1
    FRICTION = 2
    ADMIN_REVOLTS = 3
    DIPLOMACY = 4
    TECHNOLOGY = 5
    DRIFT = 6
    LIFECYCLE = 7
    TACTICAL = 8


class OMArchetype:
    PLAYER = 0
    CONQUEROR = 1
    FORTIFIER = 2
    OPPORTUNIST = 3
    WARLORD = 4
    SCHISM = 5
    BREAKAWAY = 6
    DEFAULT = 7


class OMStance:
    HOSTILE = 0
    NEUTRAL = 1
    COOPERATIVE = 2


class OMEdge:
    BORDER = 0
    TRADE = 1
    BOTH = 2


class OMAction:
    ACCUMULATE = 0
    ATTACK = 1
    COLONIZE = 2
    REINFORCE = 3


class OMMode:
    TELEGRAPH = 0
    SURPRISE = 1


class OMOutcome:
    BREAKTHROUGH = 0
    CONTESTED = 1
    REPELLED = 2


class OMCandKind:
    ATTACK = 0
    COLONIZE = 1


class OMTacParam:
    PURSUE_BY_STEERING = 0
    ROUTE_AROUND_TERRAIN = 1
    LEASH_BEFORE_DAMAGE = 2
    TARGET_POLICY = 3
    TARGET_BY_SIGHT = 4
    ROUTE_ACROSS_LAYERS = 5
    ATTACK_MOVE_LEASH = 6
    RETURN_FIRE_FLEE_DIST = 7
    UNIT_COLLISION_RADIUS = 8
    VANTAGE_MULT = 9
    AOE_DAMAGE_CAP = 10
    TARGETING_COHORTS = 11
    CATMULT_LINE_LINE = 12
    CATMULT_LINE_SIEGE = 13
    CATMULT_LINE_STRIKE = 14
    CATMULT_SIEGE_LINE = 15
    CATMULT_SIEGE_SIEGE = 16
    CATMULT_SIEGE_STRIKE = 17
    CATMULT_STRIKE_LINE = 18
    CATMULT_STRIKE_SIEGE = 19
    CATMULT_STRIKE_STRIKE = 20
    EMIT_SIGHT_MULT = 21
    EMIT_SEEN_MULT = 22
    PING_RADIUS = 23
    PING_REVEAL_TICKS = 24
    PING_COOLDOWN_TICKS = 25
    PING_REACH = 26
    VISION_UP_1 = 27
    VISION_UP_2 = 28
    VISION_UP_3 = 29
    VISION_UP_4 = 30
    VISION_DOWN_1 = 31
    VISION_DOWN_2 = 32
    VISION_DOWN_3 = 33
    VISION_DOWN_4 = 34
    RANGE_UP_1 = 35
    RANGE_UP_2 = 36
    RANGE_UP_3 = 37
    RANGE_UP_4 = 38
    RANGE_DOWN_1 = 39
    RANGE_DOWN_2 = 40
    RANGE_DOWN_3 = 41
    RANGE_DOWN_4 = 42
    DAMAGE_UP_1 = 43
    DAMAGE_UP_2 = 44
    DAMAGE_UP_3 = 45
    DAMAGE_UP_4 = 46
    DAMAGE_DOWN_1 = 47
    DAMAGE_DOWN_2 = 48
    DAMAGE_DOWN_3 = 49
    DAMAGE_DOWN_4 = 50
    AREA_UP_1 = 51
    AREA_UP_2 = 52
    AREA_UP_3 = 53
    AREA_UP_4 = 54
    AREA_DOWN_1 = 55
    AREA_DOWN_2 = 56
    AREA_DOWN_3 = 57
    AREA_DOWN_4 = 58
    TARGET_POLICY_FACTION_1 = 59
    PING_ALERT = 60
    TERRAIN_STEEP_DEG = 61
    SLOPE_UP_DIV = 62
    SLOPE_DOWN_MULT = 63
    SIGHT_EYE_HEIGHT = 64
    GROUND_FLYER_SEEN_MULT = 65
    FIRING_ARC_DEG = 66
    _COUNT = 67


class OMEmission:
    SILENT = 0
    ACTIVE = 1


class OMEvent:
    CONQUEST_UNREST = 100
    ADMIN_SEPARATIST = 101


class OMBugE05:
    AGENT_READS_LIVE = 100
    TELEGRAPH_AFTER_REINFORCE = 101
    SURPRISE_ON_DEFENSE = 102
    ENTRENCH_CURRENT_TICK = 103
    COLLISION_MAX_STRENGTH = 104
    CONQUEST_ON_BAND = 105
    GARRISON_BEFORE_DAMAGE = 106
    ADMIN_ROLL_PER_FACTION = 107
    FRICTION_COUNTS_TRADE = 108
    E05_SLOW = 109
    SAME_TICK_REDECLARE = 110
    INJECT_IGNORED = 111
    COLLISION_AFTER_RESOLVE = 112


class OmCandidate(ctypes.Structure):
    _fields_ = [
        ("region_idx", ctypes.c_uint32),
        ("kind", ctypes.c_uint32),
        ("weakness", ctypes.c_double),
        ("value", ctypes.c_double),
        ("position", ctypes.c_double),
        ("attractiveness", ctypes.c_double),
        ("entrenchment", ctypes.c_double),
        ("net", ctypes.c_double),
        ("viable", ctypes.c_uint32),
        ("_pad", ctypes.c_uint32),
    ]


class OmDecision(ctypes.Structure):
    _fields_ = [
        ("tick", ctypes.c_uint64),
        ("faction_id", ctypes.c_int32),
        ("action", ctypes.c_uint32),
        ("target_idx", ctypes.c_uint32),
        ("source_idx", ctypes.c_uint32),
        ("commit", ctypes.c_double),
        ("mode", ctypes.c_uint32),
        ("_pad", ctypes.c_uint32),
        ("attack_score", ctypes.c_double),
        ("colonize_score", ctypes.c_double),
        ("effective_confidence", ctypes.c_double),
        ("break_even", ctypes.c_double),
        ("telegraph_preference", ctypes.c_double),
    ]


class OmTelegraph(ctypes.Structure):
    _fields_ = [
        ("declared_tick", ctypes.c_uint64),
        ("attacker", ctypes.c_int32),
        ("target_idx", ctypes.c_uint32),
        ("source_idx", ctypes.c_uint32),
        ("_pad", ctypes.c_uint32),
        ("commit", ctypes.c_double),
    ]


class OmAttackResult(ctypes.Structure):
    _fields_ = [
        ("tick", ctypes.c_uint64),
        ("attacker", ctypes.c_int32),
        ("defender", ctypes.c_int32),
        ("target_idx", ctypes.c_uint32),
        ("mode", ctypes.c_uint32),
        ("outcome", ctypes.c_uint32),
        ("conquest", ctypes.c_uint32),
        ("commit", ctypes.c_double),
        ("effective_attack", ctypes.c_double),
        ("effective_defense", ctypes.c_double),
        ("stochastic", ctypes.c_double),
        ("net", ctypes.c_double),
        ("d_military", ctypes.c_double),
        ("d_economy", ctypes.c_double),
        ("d_tension", ctypes.c_double),
        ("garrison", ctypes.c_double),
        ("budget_spent", ctypes.c_double),
        ("collision", ctypes.c_uint32),
        ("_pad", ctypes.c_uint32),
    ]


class OmCollision(ctypes.Structure):
    _fields_ = [
        ("tick", ctypes.c_uint64),
        ("target_idx", ctypes.c_uint32),
        ("n_colliders", ctypes.c_uint32),
        ("faction", ctypes.c_int32 * OM_MAX_COLLIDERS),
        ("commit", ctypes.c_double * OM_MAX_COLLIDERS),
        ("economy_factor", ctypes.c_double * OM_MAX_COLLIDERS),
        ("strength", ctypes.c_double * OM_MAX_COLLIDERS),
        ("winner", ctypes.c_int32),
        ("_pad", ctypes.c_uint32),
        ("margin", ctypes.c_double),
        ("retention_ceiling", ctypes.c_double),
        ("refund", ctypes.c_double),
        ("loser_tension", ctypes.c_double * OM_MAX_COLLIDERS),
    ]


class OmReinforce(ctypes.Structure):
    _fields_ = [
        ("tick", ctypes.c_uint64),
        ("faction_id", ctypes.c_int32),
        ("target_idx", ctypes.c_uint32),
        ("commit", ctypes.c_double),
        ("headroom", ctypes.c_double),
        ("base", ctypes.c_double),
        ("variance", ctypes.c_double),
        ("d_military", ctypes.c_double),
    ]


class OmColonizeResult(ctypes.Structure):
    _fields_ = [
        ("tick", ctypes.c_uint64),
        ("faction_id", ctypes.c_int32),
        ("target_idx", ctypes.c_uint32),
        ("start_military", ctypes.c_double),
        ("budget_spent", ctypes.c_double),
    ]


class OmFriction(ctypes.Structure):
    _fields_ = [
        ("region_idx", ctypes.c_uint32),
        ("hostile_neighbors", ctypes.c_uint32),
        ("d_tension", ctypes.c_double),
        ("d_economy", ctypes.c_double),
    ]


class OmAdminRoll(ctypes.Structure):
    _fields_ = [
        ("tick", ctypes.c_uint64),
        ("faction_id", ctypes.c_int32),
        ("region_idx", ctypes.c_uint32),
        ("chance", ctypes.c_double),
        ("draw", ctypes.c_double),
        ("triggered", ctypes.c_uint32),
        ("_pad", ctypes.c_uint32),
    ]


class OmQueuedEvent(ctypes.Structure):
    _fields_ = [
        ("due_tick", ctypes.c_uint64),
        ("region_idx", ctypes.c_uint32),
        ("template_id", ctypes.c_uint32),
        ("probability", ctypes.c_double),
        ("chain_tag", ctypes.c_int32),
        ("source_faction", ctypes.c_int32),
        ("chain_length", ctypes.c_uint32),
        ("cond_kind", ctypes.c_uint32),
        ("cond_field", ctypes.c_uint32),
        ("exclusion_tag", ctypes.c_uint32),
        ("cond_value", ctypes.c_double),
    ]


def _bind_e05(lib):
    """Declare argtypes/restypes for the E-05 block. Called lazily by the E-05
    helpers so a library built before E-05 (missing symbols) turns E-05 tests
    red at first use, exactly like the E-02 block does."""
    if getattr(lib, "_e05_bound", False):
        return
    P = ctypes.POINTER
    V = ctypes.c_void_p
    lib.om_world_set_feature.argtypes = [V, ctypes.c_int, ctypes.c_int]; lib.om_world_set_feature.restype = None
    lib.om_world_feature.argtypes = [V, ctypes.c_int]; lib.om_world_feature.restype = ctypes.c_int
    lib.om_faction_set.argtypes = [V, ctypes.c_int32, ctypes.c_int, ctypes.c_double, ctypes.c_double, ctypes.c_double]
    lib.om_faction_set.restype = ctypes.c_int
    lib.om_faction_set_stance.argtypes = [V, ctypes.c_int32, ctypes.c_int32, ctypes.c_int]
    lib.om_faction_set_stance.restype = None
    lib.om_faction_set_tech_multipliers.argtypes = [V, ctypes.c_int32, ctypes.c_double, ctypes.c_double, ctypes.c_double]
    lib.om_faction_set_tech_multipliers.restype = None
    lib.om_faction_count.argtypes = [V]; lib.om_faction_count.restype = ctypes.c_uint32
    lib.om_faction_archetype.argtypes = [V, ctypes.c_int32]; lib.om_faction_archetype.restype = ctypes.c_int
    lib.om_faction_budget.argtypes = [V, ctypes.c_int32]; lib.om_faction_budget.restype = ctypes.c_double
    lib.om_faction_confidence.argtypes = [V, ctypes.c_int32]; lib.om_faction_confidence.restype = ctypes.c_double
    lib.om_faction_tech.argtypes = [V, ctypes.c_int32]; lib.om_faction_tech.restype = ctypes.c_double
    lib.om_faction_stance.argtypes = [V, ctypes.c_int32, ctypes.c_int32]; lib.om_faction_stance.restype = ctypes.c_int
    lib.om_faction_territory.argtypes = [V, ctypes.c_int32]; lib.om_faction_territory.restype = ctypes.c_uint32
    lib.om_region_set_owner.argtypes = [V, ctypes.c_uint32, ctypes.c_int32, ctypes.c_int64]; lib.om_region_set_owner.restype = None
    lib.om_region_owner.argtypes = [V, ctypes.c_uint32]; lib.om_region_owner.restype = ctypes.c_int32
    lib.om_region_held_since.argtypes = [V, ctypes.c_uint32]; lib.om_region_held_since.restype = ctypes.c_int64
    lib.om_region_set_edge.argtypes = [V, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_int]; lib.om_region_set_edge.restype = None
    lib.om_region_edge.argtypes = [V, ctypes.c_uint32, ctypes.c_uint32, P(ctypes.c_int)]; lib.om_region_edge.restype = ctypes.c_int
    lib.om_rng_force.argtypes = [V, P(ctypes.c_double), ctypes.c_uint32]; lib.om_rng_force.restype = None
    lib.om_region_add_damage.argtypes = [V, ctypes.c_uint32, ctypes.c_double, ctypes.c_double, ctypes.c_uint64]; lib.om_region_add_damage.restype = None
    lib.om_region_damage_history.argtypes = [V, ctypes.c_uint32]; lib.om_region_damage_history.restype = ctypes.c_double
    lib.om_rng_forced_remaining.argtypes = [V]; lib.om_rng_forced_remaining.restype = ctypes.c_uint32
    lib.om_faction_candidates.argtypes = [V, ctypes.c_int32, P(OmCandidate), ctypes.c_uint32]; lib.om_faction_candidates.restype = ctypes.c_uint32
    lib.om_intent_inject.argtypes = [V, ctypes.c_int32, ctypes.c_int, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_double, ctypes.c_int]; lib.om_intent_inject.restype = ctypes.c_int
    for name, st in (("om_tick_decisions", OmDecision), ("om_pending_telegraphs", OmTelegraph),
                     ("om_tick_attacks", OmAttackResult), ("om_tick_collisions", OmCollision),
                     ("om_tick_reinforces", OmReinforce), ("om_tick_colonizations", OmColonizeResult),
                     ("om_tick_friction", OmFriction), ("om_tick_admin_rolls", OmAdminRoll),
                     ("om_event_queue", OmQueuedEvent)):
        fn = getattr(lib, name)
        fn.argtypes = [V, P(st), ctypes.c_uint32]
        fn.restype = ctypes.c_uint32
    lib._e05_bound = True


# ---- E-05 helpers (plain functions, imported by the E-05 story test modules) ----

def isolate_agents(lib, w, *, friction=False, admin=False):
    """Leave only the faction step (3a-3f) on, plus friction / admin rolls when
    asked, so a single om_world_step reads as pure E-05 behavior: no drift,
    no events, no diplomacy, no technology, no lifecycle."""
    _bind_e05(lib)
    for feat in (OMFeature.EVENTS, OMFeature.DIPLOMACY, OMFeature.TECHNOLOGY,
                 OMFeature.DRIFT, OMFeature.LIFECYCLE):
        lib.om_world_set_feature(w, feat, 0)
    lib.om_world_set_feature(w, OMFeature.FACTIONS, 1)
    lib.om_world_set_feature(w, OMFeature.FRICTION, 1 if friction else 0)
    lib.om_world_set_feature(w, OMFeature.ADMIN_REVOLTS, 1 if admin else 0)


def set_faction(lib, w, faction_id, archetype, *, budget=0.0, tech=0.0, confidence=-1.0):
    _bind_e05(lib)
    rc = lib.om_faction_set(w, faction_id, archetype, budget, tech, confidence)
    assert rc == 0, f"om_faction_set failed for faction {faction_id}: rc={rc}"


def set_stance(lib, w, a, b, stance, *, both_ways=True):
    _bind_e05(lib)
    lib.om_faction_set_stance(w, a, b, stance)
    if both_ways:
        lib.om_faction_set_stance(w, b, a, stance)


def set_tech_multipliers(lib, w, faction_id, attack=1.0, defense=1.0, economy=1.0):
    _bind_e05(lib)
    lib.om_faction_set_tech_multipliers(w, faction_id, attack, defense, economy)


def set_owner(lib, w, idx, faction_id, held_since=-1):
    _bind_e05(lib)
    lib.om_region_set_owner(w, idx, faction_id, held_since)


def set_edge(lib, w, a, b, edge=OMEdge.BOTH):
    _bind_e05(lib)
    lib.om_region_set_edge(w, a, b, edge)


def add_damage(lib, w, idx, military_loss, economy_loss, tick):
    """Plant an attack loss on a region as if resolved on `tick` (ALG-11 damage history)."""
    _bind_e05(lib)
    lib.om_region_add_damage(w, idx, military_loss, economy_loss, tick)


def force_draws(lib, w, draws):
    _bind_e05(lib)
    arr = (ctypes.c_double * len(draws))(*draws)
    lib.om_rng_force(w, arr, len(draws))


def inject_intent(lib, w, faction_id, action, target_idx, source_idx, commit, mode=OMMode.SURPRISE):
    """Place an intent into the next step as if the faction decided it (the
    faction then skips its own 3d decision this tick)."""
    _bind_e05(lib)
    rc = lib.om_intent_inject(w, faction_id, action, target_idx, source_idx, commit, mode)
    assert rc == 0, f"om_intent_inject failed for faction {faction_id}: rc={rc}"


def _read_records(lib, w, name, struct_type, max_records=256):
    _bind_e05(lib)
    buf = (struct_type * max_records)()
    n = getattr(lib, name)(w, buf, max_records)
    return [buf[i] for i in range(n)]


def read_candidates(lib, w, faction_id, max_records=256):
    _bind_e05(lib)
    buf = (OmCandidate * max_records)()
    n = lib.om_faction_candidates(w, faction_id, buf, max_records)
    return [buf[i] for i in range(n)]


def read_decisions(lib, w):
    return _read_records(lib, w, "om_tick_decisions", OmDecision)


def read_telegraphs(lib, w):
    return _read_records(lib, w, "om_pending_telegraphs", OmTelegraph)


def read_attacks(lib, w):
    return _read_records(lib, w, "om_tick_attacks", OmAttackResult)


def read_collisions(lib, w):
    return _read_records(lib, w, "om_tick_collisions", OmCollision)


def read_reinforces(lib, w):
    return _read_records(lib, w, "om_tick_reinforces", OmReinforce)


def read_colonizations(lib, w):
    return _read_records(lib, w, "om_tick_colonizations", OmColonizeResult)


def read_friction(lib, w):
    return _read_records(lib, w, "om_tick_friction", OmFriction)


def read_admin_rolls(lib, w):
    return _read_records(lib, w, "om_tick_admin_rolls", OmAdminRoll)


def read_event_queue(lib, w):
    return _read_records(lib, w, "om_event_queue", OmQueuedEvent)


# ======================================================================
# ---- E-04: events and chains (appended 2026-09-14) ----
# Mirrors the E-04 block of csrc/ouroboros_sim.h exactly.
# ======================================================================

OM_MAX_TEMPLATES = 64
OM_MAX_SPAWNS = 2
OM_TEMPLATE_NAME = 32


class OMTrigger:
    NONE = 0
    ABOVE = 1
    BELOW = 2
    PROBABILITY = 3


class OMCond:
    NONE = 0
    ABOVE = 1
    BELOW = 2


class OMExcl:
    NONE = 0
    MILITARY_RELIEF = 1
    POLITICAL_RESOLUTION = 2
    REVOLT_OUTCOME = 3


class OMSource:
    TRIGGER = 0
    SPAWN = 1
    EXTERNAL = 2


class OMBugE04:
    FIRES_EVERY_TICK = 200
    NOISE_REROLLED = 201
    NO_GRACE_PERIOD = 202
    COND_AT_SPAWN = 203
    SEQUENTIAL_DELTAS = 204
    EXCLUSION_CANCELS = 205
    DRAW_BEFORE_CONDITION = 206
    CHAIN_COUNTER_UNSAVED = 207
    TRIGGERS_READ_LIVE = 208
    E04_SLOW = 209
    EVENTS_AFTER_FACTIONS = 210


class OmSpawn(ctypes.Structure):
    _fields_ = [
        ("template_id", ctypes.c_uint32),
        ("delay_min", ctypes.c_uint32),
        ("delay_max", ctypes.c_uint32),
        ("cond_kind", ctypes.c_uint32),
        ("cond_field", ctypes.c_uint32),
        ("_pad", ctypes.c_uint32),
        ("probability", ctypes.c_double),
        ("cond_value", ctypes.c_double),
    ]


class OmEventTemplate(ctypes.Structure):
    _fields_ = [
        ("id", ctypes.c_uint32),
        ("name", ctypes.c_char * OM_TEMPLATE_NAME),
        ("trigger_kind", ctypes.c_uint32),
        ("trigger_field", ctypes.c_uint32),
        ("threshold", ctypes.c_double),
        ("prob_base", ctypes.c_double),
        ("prob_exponent", ctypes.c_double),
        ("cooldown_ticks", ctypes.c_uint32),
        ("n_spawns", ctypes.c_uint32),
        ("effect", ctypes.c_double * OMField.COUNT),
        ("spawns", OmSpawn * OM_MAX_SPAWNS),
        ("exclusion_tag", ctypes.c_uint32),
        ("creates_faction", ctypes.c_uint32),
        ("admin_chain_step", ctypes.c_uint32),
        ("_pad", ctypes.c_uint32),
    ]


class OmFiredEvent(ctypes.Structure):
    _fields_ = [
        ("tick", ctypes.c_uint64),
        ("region_idx", ctypes.c_uint32),
        ("template_id", ctypes.c_uint32),
        ("chain_tag", ctypes.c_int32),
        ("source", ctypes.c_uint32),
        ("delta", ctypes.c_double * OMField.COUNT),
        ("draw", ctypes.c_double),
        ("creates_faction", ctypes.c_uint32),
        ("n_spawned", ctypes.c_uint32),
    ]


class OmPrunedEvent(ctypes.Structure):
    _fields_ = [
        ("tick", ctypes.c_uint64),
        ("region_idx", ctypes.c_uint32),
        ("template_id", ctypes.c_uint32),
        ("chain_tag", ctypes.c_int32),
        ("cond_kind", ctypes.c_uint32),
        ("cond_field", ctypes.c_uint32),
        ("_pad", ctypes.c_uint32),
        ("cond_value", ctypes.c_double),
        ("field_value", ctypes.c_double),
    ]


class OmDelayedEvent(ctypes.Structure):
    _fields_ = [
        ("tick", ctypes.c_uint64),
        ("region_idx", ctypes.c_uint32),
        ("template_id", ctypes.c_uint32),
        ("chain_tag", ctypes.c_int32),
        ("exclusion_tag", ctypes.c_uint32),
        ("kept_template_id", ctypes.c_uint32),
        ("_pad", ctypes.c_uint32),
        ("new_due", ctypes.c_uint64),
    ]


def _bind_e04(lib):
    if getattr(lib, "_e04_bound", False):
        return
    _bind_e05(lib)
    P = ctypes.POINTER
    V = ctypes.c_void_p
    lib.om_events_load_launch.argtypes = [V]; lib.om_events_load_launch.restype = None
    lib.om_events_load.argtypes = [V, P(OmEventTemplate), ctypes.c_uint32]; lib.om_events_load.restype = ctypes.c_int
    lib.om_event_template_count.argtypes = [V]; lib.om_event_template_count.restype = ctypes.c_uint32
    lib.om_event_template_get.argtypes = [V, ctypes.c_uint32, P(OmEventTemplate)]; lib.om_event_template_get.restype = ctypes.c_int
    lib.om_event_template_by_name.argtypes = [V, ctypes.c_char_p]; lib.om_event_template_by_name.restype = ctypes.c_int32
    lib.om_event_roll_noise.argtypes = [V]; lib.om_event_roll_noise.restype = None
    lib.om_event_set_noise.argtypes = [V, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_double]; lib.om_event_set_noise.restype = None
    lib.om_event_noise.argtypes = [V, ctypes.c_uint32, ctypes.c_uint32]; lib.om_event_noise.restype = ctypes.c_double
    lib.om_event_breached.argtypes = [V, ctypes.c_uint32, ctypes.c_uint32]; lib.om_event_breached.restype = ctypes.c_int
    lib.om_event_last_fired.argtypes = [V, ctypes.c_uint32, ctypes.c_uint32]; lib.om_event_last_fired.restype = ctypes.c_int64
    lib.om_chain_counter.argtypes = [V]; lib.om_chain_counter.restype = ctypes.c_int32
    lib.om_region_faction_creation_pending.argtypes = [V, ctypes.c_uint32]; lib.om_region_faction_creation_pending.restype = ctypes.c_uint32
    lib.om_event_queue_external.argtypes = [V, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint64, ctypes.c_double, ctypes.c_int32, ctypes.c_uint32]
    lib.om_event_queue_external.restype = ctypes.c_int
    lib.om_region_event_delta.argtypes = [V, ctypes.c_uint32, ctypes.c_double * OMField.COUNT]; lib.om_region_event_delta.restype = ctypes.c_int
    for name, st in (("om_tick_events", OmFiredEvent), ("om_tick_pruned", OmPrunedEvent), ("om_tick_delayed", OmDelayedEvent)):
        fn = getattr(lib, name)
        fn.argtypes = [V, P(st), ctypes.c_uint32]
        fn.restype = ctypes.c_uint32
    lib._e04_bound = True


# ---- E-04 helpers ----

def isolate_events(lib, w):
    """Only tick steps 1 and 2 (the event queue and fresh triggers) run; no
    drift, agents, friction, admin rolls, diplomacy, technology, lifecycle."""
    _bind_e04(lib)
    for feat in (OMFeature.FACTIONS, OMFeature.FRICTION, OMFeature.ADMIN_REVOLTS,
                 OMFeature.DIPLOMACY, OMFeature.TECHNOLOGY, OMFeature.DRIFT, OMFeature.LIFECYCLE):
        lib.om_world_set_feature(w, feat, 0)
    lib.om_world_set_feature(w, OMFeature.EVENTS, 1)


def load_launch_events(lib, w):
    _bind_e04(lib)
    lib.om_events_load_launch(w)


def load_only_templates(lib, w, *names):
    """Load just the named launch templates (their real values, pulled off the
    full launch library) so a queued-event test never shares the region with
    the other 25 templates' own thresholds -- the E-04 Testing Rigor
    Directive's "fields, external spawns, and noise offsets hard-fixtured"
    isolation, extended to which templates exist at all. Every id an E-07
    fixture resolves by name still resolves after this (position in the
    smaller array, not the launch library's row)."""
    _bind_e04(lib)
    lib.om_events_load_launch(w)
    picked = [get_template(lib, w, template_id(lib, w, name)) for name in names]
    arr = (OmEventTemplate * len(picked))(*picked)
    rc = lib.om_events_load(w, arr, len(picked))
    assert rc == 0, f"om_events_load failed loading {names}: rc={rc}"


def template_id(lib, w, name):
    _bind_e04(lib)
    tid = lib.om_event_template_by_name(w, name.encode("utf-8"))
    assert tid >= 0, f"no template named {name!r}"
    return tid


def get_template(lib, w, tid):
    _bind_e04(lib)
    t = OmEventTemplate()
    rc = lib.om_event_template_get(w, tid, ctypes.byref(t))
    assert rc == 0, f"om_event_template_get({tid}) rc={rc}"
    return t


def register_external_template(lib, w, name, significance_tier=0):
    """F2h: om_event_register_external. Bound (guarded) in the generated
    _bind_e06 block, not the legacy _bind_e04 -- events.c already has a
    hand-written legacy _bind_e04 for its 27 pre-existing symbols, and a
    generated _bind_e04 for this new events.c row would shadow it (last
    def wins), silently dropping those 27 bindings. Undefined until B1-4
    lands events.c -- calling this before then raises AttributeError, which
    is the point (test_E04_S030_external_templates wants a clean red, not a
    skip)."""
    _bind_e06(lib)
    return lib.om_event_register_external(w, name.encode("utf-8"), significance_tier)


def template_name(lib, w, tid):
    """F2h: om_event_template_name. Same _bind_e06 placement and
    AttributeError-until-B1-4 contract as register_external_template above."""
    _bind_e06(lib)
    name = lib.om_event_template_name(w, tid)
    return name.decode("utf-8") if name is not None else None


def set_noise(lib, w, region_idx, tid, offset):
    _bind_e04(lib)
    lib.om_event_set_noise(w, region_idx, tid, offset)


def zero_all_noise(lib, w):
    """Pin every (region, template) offset to 0 so thresholds read as the table."""
    _bind_e04(lib)
    n_regions = lib.om_region_count(w)
    n_templates = lib.om_event_template_count(w)
    for r in range(n_regions):
        for tid in range(n_templates):
            lib.om_event_set_noise(w, r, tid, 0.0)


def queue_external(lib, w, region_idx, tid, due_tick, probability=1.0, source_faction=-1, chain_length=0):
    _bind_e04(lib)
    return lib.om_event_queue_external(w, region_idx, tid, due_tick, probability, source_faction, chain_length)


def read_events(lib, w):
    _bind_e04(lib)
    return _read_records(lib, w, "om_tick_events", OmFiredEvent)


def read_pruned(lib, w):
    _bind_e04(lib)
    return _read_records(lib, w, "om_tick_pruned", OmPrunedEvent)


def read_delayed(lib, w):
    _bind_e04(lib)
    return _read_records(lib, w, "om_tick_delayed", OmDelayedEvent)


def read_event_delta(lib, w, region_idx):
    _bind_e04(lib)
    out = (ctypes.c_double * OMField.COUNT)()
    rc = lib.om_region_event_delta(w, region_idx, out)
    return rc, list(out)


# ======================================================================
# ---- E-03: world generation and topology (appended 2026-09-15) ----
# Mirrors the E-03 block of csrc/ouroboros_sim.h exactly. Nothing above changes.
# World generation has no "other tick steps to switch off": a test sets the
# generation config, calls generate(), checks it succeeded, then reads the graph
# with region_neighbors / faction_template / the E-02 and E-05 readers
# (om_region_tier, om_region_field, om_region_owner, om_region_edge). The E-02
# om_world_new(n_regions, seed) still applies: pass n_regions=0 to draw the count
# from the configured range, or a positive count to pin it.
# ======================================================================


class OMTemplate:
    ISOLATED = 0
    TWIN_COLONY = 1
    ARCHIPELAGO = 2
    NONE = 3


class OMBugE03:
    RNG_ORDER_SWAPPED = 300
    EXTRA_EDGE_TO_PLAYER = 301
    HOME_TO_HOME_EDGE = 302
    CORRIDOR_SKIPPED = 303
    EMPTY_EDGE_BOTH = 304
    FRONTIER_FROM_HOME = 305
    RESEED_PER_REGION = 306
    TWIN_SECOND_HOME_LOW = 307
    ARCHIPELAGO_DENSE = 308
    BUDGET_DRIFT = 309
    ARCHETYPE_RANGE_MISS = 310
    E03_SLOW = 311
    STARTING_RATIO_SWAPPED = 312


def _bind_e03(lib):
    """Declare argtypes/restypes for the E-03 block. Called lazily by the E-03
    helpers so a library built before E-03 (missing symbols) turns E-03 tests
    red at first use, exactly like the E-02 and E-05 blocks do."""
    if getattr(lib, "_e03_bound", False):
        return
    P = ctypes.POINTER
    V = ctypes.c_void_p
    lib.om_gen_set_region_range.argtypes = [V, ctypes.c_uint32, ctypes.c_uint32]; lib.om_gen_set_region_range.restype = None
    lib.om_gen_set_faction_count.argtypes = [V, ctypes.c_uint32]; lib.om_gen_set_faction_count.restype = None
    lib.om_gen_set_extra_edge_ratio.argtypes = [V, ctypes.c_double]; lib.om_gen_set_extra_edge_ratio.restype = None
    lib.om_gen_set_player_preference.argtypes = [V, ctypes.c_int32, ctypes.c_int]; lib.om_gen_set_player_preference.restype = None
    lib.om_gen_set_preference_weight.argtypes = [V, ctypes.c_double]; lib.om_gen_set_preference_weight.restype = None
    lib.om_gen_set_extra_edges_enabled.argtypes = [V, ctypes.c_int]; lib.om_gen_set_extra_edges_enabled.restype = None
    lib.om_gen_set_home_range.argtypes = [V, ctypes.c_int, ctypes.c_double, ctypes.c_double, ctypes.c_double, ctypes.c_double]
    lib.om_gen_set_home_range.restype = None
    lib.om_world_generated.argtypes = [V]; lib.om_world_generated.restype = ctypes.c_int
    lib.om_world_seed.argtypes = [V]; lib.om_world_seed.restype = ctypes.c_uint64
    lib.om_world_edge_count.argtypes = [V]; lib.om_world_edge_count.restype = ctypes.c_uint32
    lib.om_faction_template.argtypes = [V, ctypes.c_int32]; lib.om_faction_template.restype = ctypes.c_int
    lib.om_region_neighbors.argtypes = [V, ctypes.c_uint32, P(ctypes.c_uint32), ctypes.c_uint32]
    lib.om_region_neighbors.restype = ctypes.c_uint32
    lib._e03_bound = True


# ---- E-03 helpers (plain functions, imported by the E-03 story test modules) ----

def gen_set_region_range(lib, w, lo, hi):
    _bind_e03(lib)
    lib.om_gen_set_region_range(w, lo, hi)


def gen_set_faction_count(lib, w, n):
    _bind_e03(lib)
    lib.om_gen_set_faction_count(w, n)


def gen_set_extra_edge_ratio(lib, w, ratio):
    _bind_e03(lib)
    lib.om_gen_set_extra_edge_ratio(w, ratio)


def gen_set_player_preference(lib, w, template, faction_id=0):
    _bind_e03(lib)
    lib.om_gen_set_player_preference(w, faction_id, template)


def gen_set_preference_weight(lib, w, preferred):
    _bind_e03(lib)
    lib.om_gen_set_preference_weight(w, preferred)


def gen_set_extra_edges_enabled(lib, w, on):
    """Fixture isolation: pass 0 to skip the extra-edge step entirely (it cannot be
    turned off via ratio, whose floor is 1), so placement / empty-attachment tests
    read a graph with no stray extra edges. Default on."""
    _bind_e03(lib)
    lib.om_gen_set_extra_edges_enabled(w, 1 if on else 0)


def gen_set_home_range(lib, w, archetype, mil_lo, mil_hi, eco_lo, eco_hi):
    _bind_e03(lib)
    lib.om_gen_set_home_range(w, archetype, mil_lo, mil_hi, eco_lo, eco_hi)


def generate(lib, w):
    """Run world generation and return 1 on success, 0 on a failed feasibility
    check (om_world_generated). Force draws with force_draws (E-05 helper) before
    calling this when a rule pins a stochastic value in the generation draw order."""
    _bind_e03(lib)
    lib.om_world_generate(w)
    return lib.om_world_generated(w)


def faction_template(lib, w, faction_id):
    _bind_e03(lib)
    return lib.om_faction_template(w, faction_id)


def world_seed(lib, w):
    _bind_e03(lib)
    return lib.om_world_seed(w)


def world_edge_count(lib, w):
    _bind_e03(lib)
    return lib.om_world_edge_count(w)


def region_neighbors(lib, w, idx, max_records=256):
    """Neighbor ids of region idx in ascending order. Pair each with the E-05
    om_region_edge reader for its type."""
    _bind_e03(lib)
    buf = (ctypes.c_uint32 * max_records)()
    n = lib.om_region_neighbors(w, idx, buf, max_records)
    return [buf[i] for i in range(min(n, max_records))]


# ======================================================================
# ---- E-06 / E-07 / E-11: tick-order wiring only (freeze/F2, 2026-09-22) ----
# Mirrors the om_bug_e06 / om_bug_e07 / om_bug_e11 blocks appended to
# csrc/ouroboros_sim.h. Each epic's real symbols (stance and tech growth for
# E-06, zombie cleanup for E-07, units and combat for E-11) land with their
# own build card; only the tick-order wiring exists today.
# ======================================================================


class OMBugE06:
    DIPLOMACY_AFTER_DRIFT = 400
    TECHNOLOGY_BEFORE_ADMIN = 401
    TECH_GROWTH_TERMS_SWAPPED = 402


class OMBugE07:
    LIFECYCLE_BEFORE_DRIFT = 500
    ZOMBIE_PASS1_GE_NOT_GT = 501


class OMBugE08:
    TIME_JUMP_CLAMP_SKIPPED = 600


class OMBugE09:
    SIGNIFICANCE_CAP_SKIPPED = 700


class OMBugE10:
    URGENCY_DEFICIT_DIVISOR_WRONG = 800


class OMBugE11:
    TACTICAL_BEFORE_STRATEGIC = 900
    BRACE_REDUCTION_WRONG_CONSTANT = 901


class OMBugE12:
    INTERFERENCE_IGNORES_INTENSITY = 1000


class OMBugE13:
    MOVE_RUBBERBAND = 1100
    NAVMESH_CELL_SIZE_WRONG_CONSTANT = 1101


class OMBugE15:
    STRUCTURE_MAX_HP_WRONG_CONSTANT = 1300


class OMBugSave:
    SAVE_SKIPS_RNG_STATE = 1600
    SAVE_SKIPS_TICK = 1601


# ======================================================================
# ---- E-06..E-17: bindings from signatures.toml (freeze F1b, 2026-09-22) ----
# The story tests call lib.om_*(...) on the handle directly, many with
# keyword arguments, so every table symbol is bound at fixture time by
# _bind_generated: _bind sets argtypes/restype and, for a row with kwargs,
# swaps in a paramflags prototype so keywords reach the C side (a raw
# ctypes function drops them silently). A symbol the library lacks stays
# unbound and fails red at its first call site, like the lazy E-03/E-04/
# E-05 binders above. The _wrap_* adapters are the `wrapper` field of
# docs/northstar/spec_factory/signatures.toml; each keeps .argtypes/.restype
# and the raw function on .raw.
# ======================================================================


def _bind(lib, name, argtypes, restype, params, kw=False):
    if not hasattr(lib, name):
        return
    fn = getattr(lib, name)
    fn.argtypes = argtypes
    fn.restype = restype
    if kw:
        proto = ctypes.CFUNCTYPE(restype, *argtypes)
        setattr(lib, name, proto((name, lib), tuple((1, p) for p in params)))


def _replace(lib, name, call):
    raw = getattr(lib, name)
    call.argtypes = raw.argtypes
    call.restype = raw.restype
    call.raw = raw
    setattr(lib, name, call)


def _ids_group(ids, rest):
    """(ids, rest) as the test wrote them -> (uint32 array, n, remaining args).
    A list/tuple/array is the group form and carries its count next; a bare
    id is the single-unit form."""
    if isinstance(ids, ctypes.Array):
        return ids, rest[0], rest[1:]
    if isinstance(ids, (list, tuple)):
        ids = list(ids)
        return (ctypes.c_uint32 * max(len(ids), 1))(*ids), rest[0], rest[1:]
    return (ctypes.c_uint32 * 1)(ids), 1, rest


def _wrap_ids_list_or_single(lib, name):
    if not hasattr(lib, name):
        return
    raw = getattr(lib, name)

    def call(w, ids, *rest):
        arr, n, rest = _ids_group(ids, rest)
        return raw(w, arr, n, *rest)

    _replace(lib, name, call)


def _wrap_ids_list_optional_target(lib, name):
    if not hasattr(lib, name):
        return
    raw = getattr(lib, name)

    def call(w, ids, *rest):
        arr, n, rest = _ids_group(ids, rest)
        if not rest:
            rest = (math.nan, math.nan)
        return raw(w, arr, n, *rest)

    _replace(lib, name, call)


def _wrap_optional_trailing_null(lib, name):
    if not hasattr(lib, name):
        return
    raw = getattr(lib, name)

    def call(w, n_ticks, report=None):
        return raw(w, n_ticks, report)

    _replace(lib, name, call)


def _wrap_out_pair(lib, name):
    """(w, *args) -> (x, y): the two trailing double* out-params become the
    return value, so om_unit_get_pos(w, unit) and any row with more leading
    inputs (an interpolation alpha, say) share one adapter."""
    if not hasattr(lib, name):
        return
    raw = getattr(lib, name)

    def call(w, *args):
        x = ctypes.c_double()
        y = ctypes.c_double()
        raw(w, *args, ctypes.byref(x), ctypes.byref(y))
        return (x.value, y.value)

    _replace(lib, name, call)


def _wrap_records(lib, name, struct_type):
    """(w, max_records=256) -> [record, ...]: the (out, max) reader pair
    becomes a buffer the adapter owns, so om_tick_read_ability_events(w)
    returns the list the tests iterate (the _read_records shape)."""
    if not hasattr(lib, name):
        return
    raw = getattr(lib, name)

    def call(w, max_records=256):
        buf = (struct_type * max_records)()
        n = raw(w, buf, max_records)
        return [buf[i] for i in range(n)]

    _replace(lib, name, call)


def _wrap_client_snapshot(lib, name, struct_type):
    """(w) -> view whose .units is units[:unit_count] of the returned
    om_client_snapshot*, [] when the C side returns NULL (the STUB), so
    client_data.units iterates either way."""
    if not hasattr(lib, name):
        return
    raw = getattr(lib, name)
    raw.restype = ctypes.POINTER(struct_type)

    class Snapshot:
        def __init__(self, p):
            self.unit_count = p.contents.unit_count if p else 0
            self.units = list(p.contents.units[:self.unit_count]) if p else []

    def call(w):
        return Snapshot(raw(w))

    _replace(lib, name, call)


def _bind_generated(lib):
    for binder in _GENERATED_BINDERS:
        binder(lib)


# ---- generated from signatures.toml ----
# Written by scripts/specfactory/sig_table.py --emit from
# docs/northstar/spec_factory/signatures.toml; edit the table, not this region.
# Struct pointers bind as c_void_p (V): the story tests carry their own
# ctypes.Structure classes, so a typed POINTER() would reject them. The
# mirrors below serve the wrappers and future tests; STRUCT_C_NAMES maps
# each Python name to its C typedef.

class OMAbilityEvent(ctypes.Structure):
    _fields_ = [
        ("tick", ctypes.c_uint64),
        ("unit_id", ctypes.c_uint32),
        ("ability_id", ctypes.c_int32),
        ("target_x", ctypes.c_double),
        ("target_y", ctypes.c_double),
        ("duration", ctypes.c_uint32),
        ("telegraph_ticks", ctypes.c_uint32),
        ("cue_id", ctypes.c_uint32),
        ("radius", ctypes.c_double),
    ]


class OmAbsorptionRecord(ctypes.Structure):
    _fields_ = [
        ("tick", ctypes.c_uint64),
        ("absorbed_faction", ctypes.c_int32),
        ("absorbing_faction", ctypes.c_int32),
        ("region_idx", ctypes.c_uint32),
    ]


om_absorption_record = OmAbsorptionRecord


class OMArchetypeMetadata(ctypes.Structure):
    _fields_ = [
        ("id", ctypes.c_uint32),
        ("canvas_category", ctypes.c_uint32),
        ("primary_objective", ctypes.c_uint32),
        ("transfer_on_total", ctypes.c_uint32),
        ("transfer_on_strong", ctypes.c_uint32),
        ("transfer_on_partial", ctypes.c_uint32),
    ]


om_archetype_metadata = OMArchetypeMetadata


class OMBriefing(ctypes.Structure):
    _fields_ = [
        ("situation_text", ctypes.c_char * 1024),
        ("objective_text", ctypes.c_char * 1024),
        ("assets_text", ctypes.c_char * 1024),
        ("has_situation", ctypes.c_uint32),
        ("has_objective", ctypes.c_uint32),
        ("has_assets", ctypes.c_uint32),
    ]


om_briefing = OMBriefing


class OmCharacterRecord(ctypes.Structure):
    _fields_ = [
        ("id", ctypes.c_uint32),
        ("name", ctypes.c_char * 32),
        ("faction", ctypes.c_int32),
        ("region", ctypes.c_uint32),
        ("rank", ctypes.c_uint32),
        ("birth_tick", ctypes.c_uint64),
        ("lifespan", ctypes.c_uint32),
        ("status", ctypes.c_uint32),
        ("death_tick", ctypes.c_uint64),
        ("lineage_id", ctypes.c_uint32),
        ("parent_id", ctypes.c_uint32),
        ("generation", ctypes.c_uint32),
        ("n_rival_tags", ctypes.c_uint32),
        ("n_children", ctypes.c_uint32),
    ]


class OmChronicleCluster(ctypes.Structure):
    _fields_ = [
        ("type", ctypes.c_uint32),
        ("category", ctypes.c_uint32),
        ("region", ctypes.c_uint32),
        ("peak_score", ctypes.c_double),
        ("chain_tag", ctypes.c_int32),
        ("start_tick", ctypes.c_uint64),
        ("end_tick", ctypes.c_uint64),
    ]


om_chronicle_cluster = OmChronicleCluster


class OmChronicleEntry(ctypes.Structure):
    _fields_ = [
        ("id", ctypes.c_uint32),
        ("category", ctypes.c_uint32),
        ("region", ctypes.c_uint32),
        ("base_text", ctypes.c_char * 512),
        ("expanded_text", ctypes.c_char * 1024),
        ("start_tick", ctypes.c_uint64),
        ("end_tick", ctypes.c_uint64),
        ("fragment_ids", ctypes.c_int32 * 3),
        ("region_ref", ctypes.c_int32),
        ("faction_ref", ctypes.c_int32),
        ("lineage_ref", ctypes.c_int32),
    ]


om_chronicle_entry = OmChronicleEntry


class OmChronicleMention(ctypes.Structure):
    _fields_ = [
        ("start", ctypes.c_uint32),
        ("len", ctypes.c_uint32),
        ("kind", ctypes.c_uint32),
        ("id", ctypes.c_int32),
    ]


om_chronicle_mention = OmChronicleMention


class OmClientUnit(ctypes.Structure):
    _fields_ = [
        ("id", ctypes.c_uint32),
        ("faction_id", ctypes.c_int32),
    ]


om_client_unit = OmClientUnit


class OMCompositionRatio(ctypes.Structure):
    _fields_ = [
        ("line", ctypes.c_double),
        ("strike", ctypes.c_double),
        ("siege", ctypes.c_double),
    ]


om_composition_ratio = OMCompositionRatio


class OMDebrief(ctypes.Structure):
    _fields_ = [
        ("band", ctypes.c_int32),
        ("objective_score", ctypes.c_double),
        ("retention", ctypes.c_double),
        ("commander_fate", ctypes.c_int32),
        ("text", ctypes.c_char * 2048),
    ]


om_debrief = OMDebrief


class OMFairnessScore(ctypes.Structure):
    _fields_ = [
        ("route_count_balance", ctypes.c_double),
        ("travel_time_balance", ctypes.c_double),
        ("vantage_accessibility_balance", ctypes.c_double),
        ("hazard_symmetry", ctypes.c_double),
        ("composite_score", ctypes.c_double),
    ]


class OmFragmentPoolCounts(ctypes.Structure):
    _fields_ = [
        ("openings", ctypes.c_uint32),
        ("details", ctypes.c_uint32),
        ("closings", ctypes.c_uint32),
    ]


om_fragment_pool_counts = OmFragmentPoolCounts


class OMGradientProperties(ctypes.Structure):
    _fields_ = [
        ("obstacle_density", ctypes.c_double),
        ("cover_density", ctypes.c_double),
        ("sensor_interference", ctypes.c_double),
        ("elevation", ctypes.c_double),
        ("layer_accessibility_0", ctypes.c_uint32),
        ("layer_accessibility_1", ctypes.c_uint32),
    ]


class OMMissionCandidate(ctypes.Structure):
    _fields_ = [
        ("region_idx", ctypes.c_uint32),
        ("archetype", ctypes.c_uint32),
        ("urgency", ctypes.c_double),
        ("relevance", ctypes.c_double),
        ("preference", ctypes.c_double),
        ("score", ctypes.c_double),
    ]


om_mission_candidate = OMMissionCandidate


class OMNetCommand(ctypes.Structure):
    _fields_ = [
        ("tick", ctypes.c_uint64),
        ("seq", ctypes.c_uint32),
        ("arg", ctypes.c_uint32),
        ("x", ctypes.c_double),
        ("y", ctypes.c_double),
        ("peer", ctypes.c_uint8),
        ("verb", ctypes.c_uint8),
        ("layer", ctypes.c_uint8),
        ("n_units", ctypes.c_uint8),
    ]


class OMObjectiveSpec(ctypes.Structure):
    _fields_ = [
        ("id", ctypes.c_uint32),
        ("kind", ctypes.c_uint32),
        ("is_primary", ctypes.c_uint32),
        ("weight", ctypes.c_double),
        ("completion", ctypes.c_double),
        ("is_complete", ctypes.c_uint32),
        ("is_failed", ctypes.c_uint32),
    ]


om_objective_spec = OMObjectiveSpec


class OmOnboardingConfig(ctypes.Structure):
    _fields_ = [
        ("difficulty", ctypes.c_uint32),
        ("weights", ctypes.c_double * 10),
        ("rare_marks", ctypes.c_uint32 * 10),
    ]


class OMPingAlert(ctypes.Structure):
    _fields_ = [
        ("tick", ctypes.c_uint64),
        ("faction", ctypes.c_int32),
        ("sector", ctypes.c_int32),
    ]


class OMReinforcementWave(ctypes.Structure):
    _fields_ = [
        ("is_scheduled", ctypes.c_uint32),
        ("direction", ctypes.c_uint32),
        ("arrival_tick", ctypes.c_uint64),
        ("is_spawned", ctypes.c_uint32),
    ]


class OMReplayCommand(ctypes.Structure):
    _fields_ = [
        ("tick", ctypes.c_uint64),
        ("force_id", ctypes.c_uint32),
        ("command_type", ctypes.c_uint32),
        ("target_x", ctypes.c_double),
        ("target_y", ctypes.c_double),
        ("target_id", ctypes.c_uint32),
    ]


class OmReversionRecord(ctypes.Structure):
    _fields_ = [
        ("tick", ctypes.c_uint64),
        ("region_idx", ctypes.c_uint32),
        ("original_faction", ctypes.c_int32),
        ("restored_faction", ctypes.c_int32),
        ("military_stolen", ctypes.c_double),
        ("economy_stolen", ctypes.c_double),
    ]


om_reversion_record = OmReversionRecord


class OmRevoltRecord(ctypes.Structure):
    _fields_ = [
        ("tick", ctypes.c_uint64),
        ("region_idx", ctypes.c_uint32),
        ("original_faction", ctypes.c_int32),
        ("success_rate", ctypes.c_double),
        ("draw", ctypes.c_double),
        ("faction_created", ctypes.c_uint32),
        ("new_faction_id", ctypes.c_int32),
        ("military_stolen", ctypes.c_double),
        ("economy_stolen", ctypes.c_double),
        ("reverted_faction", ctypes.c_int32),
    ]


om_revolt_record = OmRevoltRecord


class OmSelectionRecord(ctypes.Structure):
    _fields_ = [
        ("rotated", ctypes.c_uint32),
        ("reason", ctypes.c_uint32),
        ("pool", ctypes.c_uint32),
        ("new_lineage_id", ctypes.c_uint32),
        ("commander_id", ctypes.c_uint32),
        ("chapters_in_lineage", ctypes.c_uint32),
        ("home_region_idx", ctypes.c_uint32),
        ("_pad", ctypes.c_uint32),
    ]


class OMSlope(ctypes.Structure):
    _fields_ = [
        ("x0", ctypes.c_double),
        ("y0", ctypes.c_double),
        ("x1", ctypes.c_double),
        ("y1", ctypes.c_double),
        ("mx", ctypes.c_double),
        ("my", ctypes.c_double),
        ("length", ctypes.c_double),
        ("lower_band", ctypes.c_int32),
        ("upper_band", ctypes.c_int32),
    ]


class OMStructureHUD(ctypes.Structure):
    _fields_ = [
        ("timer_progress", ctypes.c_double),
        ("next_unit_type", ctypes.c_uint32),
        ("hp", ctypes.c_double),
        ("max_hp", ctypes.c_double),
    ]


om_structure_hud = OMStructureHUD


class OmTimeJumpReport(ctypes.Structure):
    _fields_ = [
        ("start_tick", ctypes.c_uint64),
        ("end_tick", ctypes.c_uint64),
        ("jump_ticks", ctypes.c_uint32),
        ("n_territory_changes", ctypes.c_uint32),
        ("n_faction_births", ctypes.c_uint32),
        ("n_faction_deaths", ctypes.c_uint32),
        ("n_conquests", ctypes.c_uint32),
        ("n_colonizations", ctypes.c_uint32),
        ("n_revolts", ctypes.c_uint32),
        ("n_chronicle_entries", ctypes.c_uint32),
        ("n_snapshots", ctypes.c_uint32),
    ]


class OMUnitProfile(ctypes.Structure):
    _fields_ = [
        ("unit_type", ctypes.c_uint32),
        ("hp", ctypes.c_double),
        ("base_damage", ctypes.c_double),
        ("attack_interval", ctypes.c_double),
        ("power", ctypes.c_double),
    ]


om_unit_profile = OMUnitProfile


class OMVec2(ctypes.Structure):
    _fields_ = [
        ("x", ctypes.c_double),
        ("y", ctypes.c_double),
    ]


om_vec2 = OMVec2


class OmClientSnapshot(ctypes.Structure):
    _fields_ = [
        ("unit_count", ctypes.c_uint32),
        ("units", OmClientUnit * 256),
    ]


om_client_snapshot = OmClientSnapshot


STRUCT_C_NAMES = {
    "OMAbilityEvent": "om_ability_event",
    "OmAbsorptionRecord": "om_absorption_record",
    "om_absorption_record": "om_absorption_record",
    "OMArchetypeMetadata": "om_archetype_metadata",
    "om_archetype_metadata": "om_archetype_metadata",
    "OMBriefing": "om_briefing",
    "om_briefing": "om_briefing",
    "OmCharacterRecord": "om_character_record",
    "OmChronicleCluster": "om_chronicle_cluster",
    "om_chronicle_cluster": "om_chronicle_cluster",
    "OmChronicleEntry": "om_chronicle_entry",
    "om_chronicle_entry": "om_chronicle_entry",
    "OmChronicleMention": "om_chronicle_mention",
    "om_chronicle_mention": "om_chronicle_mention",
    "OmClientUnit": "om_client_unit",
    "om_client_unit": "om_client_unit",
    "OMCompositionRatio": "om_composition_ratio",
    "om_composition_ratio": "om_composition_ratio",
    "OMDebrief": "om_debrief",
    "om_debrief": "om_debrief",
    "OMFairnessScore": "om_fairness_score",
    "OmFragmentPoolCounts": "om_fragment_pool_counts",
    "om_fragment_pool_counts": "om_fragment_pool_counts",
    "OMGradientProperties": "om_gradient_properties",
    "OMMissionCandidate": "om_mission_candidate",
    "om_mission_candidate": "om_mission_candidate",
    "OMNetCommand": "om_net_command",
    "OMObjectiveSpec": "om_objective_spec",
    "om_objective_spec": "om_objective_spec",
    "OmOnboardingConfig": "om_onboarding_config",
    "OMPingAlert": "om_ping_alert",
    "OMReinforcementWave": "om_reinforcement_wave",
    "OMReplayCommand": "om_replay_command",
    "OmReversionRecord": "om_reversion_record",
    "om_reversion_record": "om_reversion_record",
    "OmRevoltRecord": "om_revolt_record",
    "om_revolt_record": "om_revolt_record",
    "OmSelectionRecord": "om_selection_record",
    "OMSlope": "om_slope",
    "OMStructureHUD": "om_structure_hud",
    "om_structure_hud": "om_structure_hud",
    "OmTimeJumpReport": "om_time_jump_report",
    "OMUnitProfile": "om_unit_profile",
    "om_unit_profile": "om_unit_profile",
    "OMVec2": "om_vec2",
    "om_vec2": "om_vec2",
    "OmClientSnapshot": "om_client_snapshot",
    "om_client_snapshot": "om_client_snapshot",
}


def _bind_e01(lib):
    if getattr(lib, "_e01_bound", False):
        return
    P = ctypes.POINTER
    V = ctypes.c_void_p
    W = OMWorldP
    _bind(lib, "om_command_ping", [W, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_double, ctypes.c_double], ctypes.c_int, ("w", "caster", "layer", "x", "y"))
    _bind(lib, "om_command_set_emission", [W, P(ctypes.c_uint32), ctypes.c_uint32, ctypes.c_int], ctypes.c_int, ("w", "unit_ids", "n_units", "mode"))
    _bind(lib, "om_command_set_layer", [W, P(ctypes.c_uint32), ctypes.c_uint32, ctypes.c_uint32], ctypes.c_int, ("w", "unit_ids", "n_units", "layer"))
    _bind(lib, "om_era_kind", [W], ctypes.c_int, ("w",))
    _bind(lib, "om_ping_alert_count", [W, ctypes.c_int32], ctypes.c_uint32, ("w", "faction"))
    _bind(lib, "om_ping_alert_get", [W, ctypes.c_int32, ctypes.c_uint32, V], ctypes.c_int, ("w", "faction", "index", "out"))
    _bind(lib, "om_roster_set_movement_kind", [W, ctypes.c_int, ctypes.c_int], ctypes.c_int, ("w", "type", "kind"))
    _bind(lib, "om_roster_set_reach", [W, ctypes.c_int, ctypes.c_uint32, ctypes.c_uint32], ctypes.c_int, ("w", "unit_type", "layers_up", "layers_down"))
    _bind(lib, "om_set_era_kind", [W, ctypes.c_int], ctypes.c_int, ("w", "kind"))
    _bind(lib, "om_space_field_get_mask", [W, ctypes.c_uint32, P(ctypes.c_uint8), ctypes.c_uint32], ctypes.c_uint32, ("w", "layer", "out", "cap"))
    _bind(lib, "om_terrain_clear", [W], None, ("w",))
    _bind(lib, "om_terrain_nearest_walkable", [W, ctypes.c_double, ctypes.c_double, P(ctypes.c_double), P(ctypes.c_double)], ctypes.c_int, ("w", "x", "y", "ox", "oy"))
    _bind(lib, "om_unit_get_emission", [W, ctypes.c_uint32], ctypes.c_int, ("w", "unit"))
    _bind(lib, "om_unit_get_target_layer", [W, ctypes.c_uint32], ctypes.c_uint32, ("w", "unit"))
    _bind(lib, "om_unit_profile_movement_kind", [W, ctypes.c_int], ctypes.c_int, ("w", "type"))
    _bind(lib, "om_unit_profile_reach", [W, ctypes.c_int, P(ctypes.c_uint32), P(ctypes.c_uint32)], ctypes.c_int, ("w", "unit_type", "up", "down"))
    _bind(lib, "om_unit_transition_progress", [W, ctypes.c_uint32], ctypes.c_double, ("w", "unit"))
    lib._e01_bound = True


def _bind_e06(lib):
    if getattr(lib, "_e06_bound", False):
        return
    P = ctypes.POINTER
    V = ctypes.c_void_p
    W = OMWorldP
    _bind(lib, "om_archetype_betrayal_weight", [ctypes.c_int], ctypes.c_double, ("archetype",))
    _bind(lib, "om_archetype_peace_disposition", [ctypes.c_int], ctypes.c_double, ("archetype",))
    _bind(lib, "om_breakaway_create", [W, ctypes.c_int32, ctypes.c_uint32], ctypes.c_int32, ("w", "parent", "region_idx"))
    _bind(lib, "om_chronicle_distill_candidates", [W, P(ctypes.c_uint32), ctypes.c_uint32], ctypes.c_uint32, ("w", "out", "max"))
    _bind(lib, "om_debug_inject", [W, ctypes.c_int], None, ("w", "bug"))
    _bind(lib, "om_diplomacy_init", [W], None, ("w",))
    _bind(lib, "om_diplomacy_step", [W], None, ("w",))
    _bind(lib, "om_event_register_external", [W, ctypes.c_char_p, ctypes.c_int32], ctypes.c_int32, ("w", "name", "significance_tier"))
    _bind(lib, "om_event_template_name", [W, ctypes.c_uint32], ctypes.c_char_p, ("w", "template_id"))
    _bind(lib, "om_faction_betrayal_chance", [W, ctypes.c_int32, ctypes.c_int32], ctypes.c_double, ("w", "betrayer", "partner"))
    _bind(lib, "om_faction_betrayal_opportunity", [W, ctypes.c_int32, ctypes.c_int32], ctypes.c_double, ("w", "betrayer", "partner"))
    _bind(lib, "om_faction_cooperative_since", [W, ctypes.c_int32, ctypes.c_int32], ctypes.c_uint64, ("w", "p0", "p1"))
    _bind(lib, "om_faction_count", [W], ctypes.c_uint32, ("w",))
    _bind(lib, "om_faction_create_breakaway", [W, ctypes.c_int32, ctypes.c_uint32], None, ("w", "parent", "p1"))
    _bind(lib, "om_faction_last_knowledge_lost", [W, ctypes.c_int32], ctypes.c_int64, ("w", "faction_id"))
    _bind(lib, "om_faction_next_mission_unit_tier", [W, ctypes.c_int32], ctypes.c_uint32, ("w", "faction_id"))
    _bind(lib, "om_faction_set_last_knowledge_lost", [W, ctypes.c_int32, ctypes.c_int64], None, ("w", "faction_id", "tick"))
    _bind(lib, "om_faction_set_stance_counter", [W, ctypes.c_int32, ctypes.c_int32, ctypes.c_uint32], None, ("w", "p0", "p1", "counter"))
    _bind(lib, "om_faction_stance", [W, ctypes.c_int32, ctypes.c_int32], ctypes.c_int, ("w", "from", "toward"))
    _bind(lib, "om_faction_stance_counter", [W, ctypes.c_int32, ctypes.c_int32], ctypes.c_uint32, ("w", "p0", "faction"))
    _bind(lib, "om_faction_tech", [W, ctypes.c_int32], ctypes.c_double, ("w", "faction_id"))
    _bind(lib, "om_faction_tech_attack", [W, ctypes.c_int32], ctypes.c_double, ("w", "faction_id"))
    _bind(lib, "om_faction_tech_defense", [W, ctypes.c_int32], ctypes.c_double, ("w", "faction_id"))
    _bind(lib, "om_faction_tech_economy", [W, ctypes.c_int32], ctypes.c_double, ("w", "faction_id"))
    _bind(lib, "om_faction_tech_multipliers", [W, ctypes.c_int32, P(ctypes.c_double), P(ctypes.c_double), P(ctypes.c_double)], None, ("w", "faction_id", "attack", "defense", "economy"))
    _bind(lib, "om_faction_tech_tier", [W, ctypes.c_int32], ctypes.c_uint32, ("w", "faction_id"))
    _bind(lib, "om_faction_tier_transition_candidate", [W, ctypes.c_int32], ctypes.c_int, ("w", "faction_id"))
    _bind(lib, "om_faction_unit_tier", [W, ctypes.c_int32], ctypes.c_uint32, ("w", "faction_id"))
    _bind(lib, "om_gen_set_faction_count", [W, ctypes.c_uint32], None, ("w", "n"))
    _bind(lib, "om_gen_set_region_range", [W, ctypes.c_uint32, ctypes.c_uint32], None, ("w", "lo", "hi"))
    _bind(lib, "om_mission_start", [W, ctypes.c_int32], ctypes.c_uint32, ("w", "faction_id"))
    _bind(lib, "om_mission_unit_tier", [W, ctypes.c_uint32], ctypes.c_uint32, ("w", "mission_id"))
    _bind(lib, "om_region_count", [W], ctypes.c_uint32, ("w",))
    _bind(lib, "om_region_edge", [W, ctypes.c_uint32, ctypes.c_uint32, P(ctypes.c_int)], ctypes.c_int, ("w", "a", "b", "out"))
    _bind(lib, "om_region_field", [W, ctypes.c_uint32, ctypes.c_int], ctypes.c_double, ("w", "idx", "f"))
    _bind(lib, "om_region_owner", [W, ctypes.c_uint32], ctypes.c_int32, ("w", "idx"))
    _bind(lib, "om_tech_step", [W], None, ("w",))
    _bind(lib, "om_tech_tier", [ctypes.c_double], ctypes.c_uint32, ("tech",))
    _bind(lib, "om_tick_events", [W, V, ctypes.c_uint32], ctypes.c_uint32, ("w", "out", "max"))
    _bind(lib, "om_tick_friction", [W, V, ctypes.c_uint32], ctypes.c_uint32, ("w", "out", "max"))
    _bind(lib, "om_tier_transition_candidate_exists", [W, ctypes.c_int32], ctypes.c_int, ("w", "faction_id"))
    _bind(lib, "om_world_generated", [W], ctypes.c_int, ("w",))
    _bind(lib, "om_world_set_feature", [W, ctypes.c_int, ctypes.c_int], None, ("w", "f", "on"))
    _bind(lib, "om_world_set_tick", [W, ctypes.c_uint64], None, ("w", "tick"))
    _bind(lib, "om_world_step", [W], ctypes.c_uint64, ("w",))
    lib._e06_bound = True


def _bind_e07(lib):
    if getattr(lib, "_e07_bound", False):
        return
    P = ctypes.POINTER
    V = ctypes.c_void_p
    W = OMWorldP
    _bind(lib, "om_faction_archetype", [W, ctypes.c_int32], ctypes.c_int, ("w", "faction_id"))
    _bind(lib, "om_faction_budget", [W, ctypes.c_int32], ctypes.c_double, ("w", "faction_id"))
    _bind(lib, "om_faction_confidence", [W, ctypes.c_int32], ctypes.c_double, ("w", "faction_id"))
    _bind(lib, "om_faction_is_active", [W, ctypes.c_int32], ctypes.c_int, ("w", "faction_id"))
    _bind(lib, "om_faction_mark_conquered_this_tick", [W, ctypes.c_int32], None, ("w", "faction_id"))
    _bind(lib, "om_faction_phase", [W, ctypes.c_int32], ctypes.c_int, ("w", "faction_id"))
    _bind(lib, "om_faction_remove", [W, ctypes.c_int32], None, ("w", "faction_id"))
    _bind(lib, "om_faction_set_created_tick", [W, ctypes.c_int32, ctypes.c_uint64], None, ("w", "faction_id", "tick"))
    _bind(lib, "om_faction_set_event_window_counts", [W, ctypes.c_int32, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32], None, ("w", "faction_id", "total_events", "revolts", "attacks", "colonizations"), kw=True)
    _bind(lib, "om_faction_territory", [W, ctypes.c_int32], ctypes.c_uint32, ("w", "faction_id"))
    _bind(lib, "om_player_faction_collapsed", [W, ctypes.c_int32], ctypes.c_int, ("w", "faction_id"))
    _bind(lib, "om_region_held_since", [W, ctypes.c_uint32], ctypes.c_int64, ("w", "idx"))
    _bind(lib, "om_region_previous_owner", [W, ctypes.c_uint32], ctypes.c_int32, ("w", "idx"))
    _bind(lib, "om_region_set_previous_owner", [W, ctypes.c_uint32, ctypes.c_int32], None, ("w", "idx", "faction_id"))
    _bind(lib, "om_tick_absorptions", [W, V, ctypes.c_uint32], ctypes.c_uint32, ("w", "out", "max"))
    _bind(lib, "om_tick_reversions", [W, V, ctypes.c_uint32], ctypes.c_uint32, ("w", "out", "max"))
    _bind(lib, "om_tick_revolts", [W, V, ctypes.c_uint32], ctypes.c_uint32, ("w", "out", "max"))
    _bind(lib, "om_world_is_terminal", [W], ctypes.c_int, ("w",))
    lib._e07_bound = True


def _bind_e08(lib):
    if getattr(lib, "_e08_bound", False):
        return
    P = ctypes.POINTER
    V = ctypes.c_void_p
    W = OMWorldP
    _bind(lib, "om_campaign_check_surviving_factions", [W], ctypes.c_int, ("w",))
    _bind(lib, "om_campaign_commander", [W], ctypes.c_uint32, ("w",))
    _bind(lib, "om_campaign_lineage", [W], ctypes.c_uint32, ("w",))
    _bind(lib, "om_campaign_needs_onboarding", [W], ctypes.c_int, ("w",))
    _bind(lib, "om_campaign_opening_jump_length", [W], ctypes.c_uint32, ("w",))
    _bind(lib, "om_campaign_start", [W, ctypes.c_uint32], None, ("w", "chapter"), kw=True)
    _bind(lib, "om_campaign_trigger_terminal_restart", [W], None, ("w",))
    _bind(lib, "om_chapter_advance_phase", [W], None, ("w",))
    _bind(lib, "om_chapter_current_phase", [W], ctypes.c_int, ("w",))
    _bind(lib, "om_chapter_end_reason_for_collapse", [W, ctypes.c_int32], ctypes.c_int, ("w", "player_faction"), kw=True)
    _bind(lib, "om_chapter_get_number", [W], ctypes.c_uint32, ("w",))
    _bind(lib, "om_chapter_last_end_reason", [W], ctypes.c_int, ("w",))
    _bind(lib, "om_chapter_mission_realtime", [W], ctypes.c_int, ("w",))
    _bind(lib, "om_chapter_recon_has_clock", [W], ctypes.c_int, ("w",))
    _bind(lib, "om_chapter_set_phase", [W, ctypes.c_int], None, ("w", "p0"))
    _bind(lib, "om_chapter_start", [W, ctypes.c_uint32], None, ("w", "chapter"), kw=True)
    _bind(lib, "om_chapter_transition_complete", [W], None, ("w",))
    _bind(lib, "om_chapter_transition_start", [W], None, ("w",))
    _bind(lib, "om_character_count", [W], ctypes.c_uint32, ("w",))
    _bind(lib, "om_character_create", [W, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint64, ctypes.c_uint32], None, ("w", "character_id", "lineage_id", "region_idx", "rank", "birth_tick", "lifespan"), kw=True)
    _bind(lib, "om_character_create_child", [W, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint64, ctypes.c_uint32], None, ("w", "child_id", "parent_id", "region_idx", "birth_tick", "lifespan"), kw=True)
    _bind(lib, "om_character_create_random", [W, ctypes.c_int32, ctypes.c_uint32], ctypes.c_uint32, ("w", "faction_id", "region_idx"), kw=True)
    _bind(lib, "om_character_create_with_rank", [W, ctypes.c_int32, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint64, ctypes.c_uint32], ctypes.c_uint32, ("w", "faction_id", "region_idx", "rank", "birth_tick", "lifespan"), kw=True)
    _bind(lib, "om_character_faction", [W, ctypes.c_uint32], ctypes.c_int32, ("w", "character"))
    _bind(lib, "om_character_get_record", [W, ctypes.c_uint32, V], ctypes.c_int, ("w", "character", "out"))
    _bind(lib, "om_character_has_event_history", [W, ctypes.c_uint32], ctypes.c_int, ("w", "character"))
    _bind(lib, "om_character_has_rival_tag", [W, ctypes.c_uint32, ctypes.c_uint32], ctypes.c_int, ("w", "character_id", "target_commander_id"), kw=True)
    _bind(lib, "om_character_id_at", [W, ctypes.c_uint32], ctypes.c_uint32, ("w", "index"))
    _bind(lib, "om_character_is_main_character", [W, ctypes.c_uint32], ctypes.c_int, ("w", "character_id"), kw=True)
    _bind(lib, "om_character_kill", [W, ctypes.c_uint32, ctypes.c_uint64], None, ("w", "character_id", "tick"), kw=True)
    _bind(lib, "om_character_lineage_id", [W, ctypes.c_uint32], ctypes.c_uint32, ("w", "character"))
    _bind(lib, "om_character_name_reuse_cooldown", [W, ctypes.c_uint32], ctypes.c_uint32, ("w", "character_id"), kw=True)
    _bind(lib, "om_character_selector_confirm_commander", [W, ctypes.c_uint32], None, ("w", "character_id"), kw=True)
    _bind(lib, "om_character_selector_force_rotate", [W, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_int, ctypes.c_int, V], None, ("w", "lineage_id", "mission_region", "reason", "pool", "out_record"), kw=True)
    _bind(lib, "om_character_selector_input_region", [W], ctypes.c_uint32, ("w",))
    _bind(lib, "om_character_selector_resolve_commander_death", [W, ctypes.c_uint32, ctypes.c_uint32, V], None, ("w", "lineage_id", "mission_region", "out_record"), kw=True)
    _bind(lib, "om_character_selector_run", [W], None, ("w",))
    _bind(lib, "om_character_selector_run_for_lineage", [W, ctypes.c_uint32, ctypes.c_uint32, V], None, ("w", "lineage_id", "mission_region", "out_record"), kw=True)
    _bind(lib, "om_character_set_faction", [W, ctypes.c_uint32, ctypes.c_int32], None, ("w", "character_id", "faction_id"), kw=True)
    _bind(lib, "om_character_set_generation", [W, ctypes.c_uint32, ctypes.c_uint32], None, ("w", "character_id", "generation"), kw=True)
    _bind(lib, "om_character_tag_rival", [W, ctypes.c_uint32, ctypes.c_uint32], None, ("w", "character_id", "rival_of_character_id"), kw=True)
    _bind(lib, "om_chronicle_consequence_entry_count", [W], ctypes.c_uint32, ("w",))
    _bind(lib, "om_chronicle_entry_count", [W], ctypes.c_uint32, ("w",))
    _bind(lib, "om_chronicle_has_faction_fall_entry", [W, ctypes.c_int32], ctypes.c_int, ("w", "old_faction"), kw=True)
    _bind(lib, "om_chronicle_lineage_entry_count", [W], ctypes.c_uint32, ("w",))
    _bind(lib, "om_event_attached_character_count", [W, ctypes.c_uint32], ctypes.c_uint32, ("w", "event"))
    _bind(lib, "om_event_fire_manual", [W, ctypes.c_uint32, ctypes.c_uint32], ctypes.c_uint32, ("w", "region_idx", "tier"), kw=True)
    _bind(lib, "om_event_get_attached_character", [W, ctypes.c_uint32, ctypes.c_uint32], ctypes.c_uint32, ("w", "event", "p1"))
    _bind(lib, "om_event_template_significance_tier", [W, ctypes.c_uint32], ctypes.c_int32, ("w", "template_id"))
    _bind(lib, "om_faction_create_named", [W, ctypes.c_int32, ctypes.c_uint32], None, ("w", "faction_id", "first_region"), kw=True)
    _bind(lib, "om_faction_supreme_commander", [W, ctypes.c_int32], ctypes.c_uint32, ("w", "faction_id"), kw=True)
    _bind(lib, "om_force_allocated_unit_count", [W, ctypes.c_uint32], ctypes.c_uint32, ("w", "mission_id"), kw=True)
    _bind(lib, "om_force_allocator_run", [W, ctypes.c_uint32, ctypes.c_double], None, ("w", "mission_id", "budget"), kw=True)
    _bind(lib, "om_force_set_surviving_units", [W, ctypes.c_uint32, ctypes.c_uint32], None, ("w", "mission_id", "n_survivors"), kw=True)
    _bind(lib, "om_ledger_commander_death_outcome_band", [W, ctypes.c_uint32], ctypes.c_int, ("w", "commander_id"), kw=True)
    _bind(lib, "om_ledger_commander_death_region", [W, ctypes.c_uint32], ctypes.c_uint32, ("w", "commander_id"), kw=True)
    _bind(lib, "om_lineage_chapter_count", [W, ctypes.c_uint32], ctypes.c_uint32, ("w", "lineage_id"))
    _bind(lib, "om_lineage_count", [W], ctypes.c_uint32, ("w",))
    _bind(lib, "om_lineage_create", [W, ctypes.c_uint32, ctypes.c_uint32], None, ("w", "lineage_id", "home_region"), kw=True)
    _bind(lib, "om_lineage_first_member_region", [W, ctypes.c_uint32], ctypes.c_int32, ("w", "lineage_id"))
    _bind(lib, "om_lineage_generate_descendants", [W, ctypes.c_uint32, ctypes.c_uint32], ctypes.c_uint32, ("w", "lineage_id", "jump_ticks"), kw=True)
    _bind(lib, "om_lineage_history_region", [W, ctypes.c_uint32, ctypes.c_uint32], ctypes.c_int32, ("w", "lineage_id", "idx"))
    _bind(lib, "om_lineage_home_region", [W, ctypes.c_uint32], ctypes.c_uint32, ("w", "lineage_id"), kw=True)
    _bind(lib, "om_lineage_id_at", [W, ctypes.c_uint32], ctypes.c_uint32, ("w", "index"))
    _bind(lib, "om_lineage_member_in_region", [W, ctypes.c_uint32, ctypes.c_uint32], ctypes.c_int, ("w", "lineage_id", "region_idx"))
    _bind(lib, "om_lineage_record_history_region", [W, ctypes.c_uint32, ctypes.c_uint32], None, ("w", "lineage_id", "region_idx"), kw=True)
    _bind(lib, "om_lineage_set_chapter_count", [W, ctypes.c_uint32, ctypes.c_uint32], None, ("w", "lineage_id", "chapters"), kw=True)
    _bind(lib, "om_lineage_spawn_descendant_at_tick", [W, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint64], ctypes.c_uint32, ("w", "lineage_id", "parent_id", "tick"), kw=True)
    _bind(lib, "om_lineage_spawn_single_descendant", [W, ctypes.c_uint32], ctypes.c_uint32, ("w", "lineage_id"), kw=True)
    _bind(lib, "om_load_state_read", [W, P(ctypes.c_uint8), ctypes.c_uint32], ctypes.c_int, ("w", "buffer", "length"))
    _bind(lib, "om_mission_generator_chosen_archetype", [W], ctypes.c_int32, ("w",))
    _bind(lib, "om_mission_generator_chosen_region", [W], ctypes.c_uint32, ("w",))
    _bind(lib, "om_mission_generator_run", [W], None, ("w",))
    _bind(lib, "om_mission_tag_rivals", [W, ctypes.c_uint32, ctypes.c_uint32], None, ("w", "mission_region", "commander_id"), kw=True)
    _bind(lib, "om_onboarding_load_from_slot", [W, ctypes.c_uint32, V], None, ("w", "slot_id", "out_cfg"), kw=True)
    _bind(lib, "om_onboarding_save_to_slot", [W, ctypes.c_uint32, V], None, ("w", "slot_id", "cfg"), kw=True)
    _bind(lib, "om_onboarding_update_choices", [W, ctypes.c_uint32, V], ctypes.c_int, ("w", "slot_id", "new_cfg"), kw=True)
    _bind(lib, "om_onboarding_validate", [V], ctypes.c_int, ("cfg",))
    _bind(lib, "om_outcome_apply_consequences", [W, ctypes.c_uint32, ctypes.c_double, ctypes.c_double], None, ("w", "target_region", "delta_military", "delta_economy"), kw=True)
    _bind(lib, "om_outcome_record_commander_death", [W, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_int], None, ("w", "commander_id", "mission_region", "outcome_band"), kw=True)
    _bind(lib, "om_player_faction_check_collapse", [W, ctypes.c_int32], ctypes.c_int, ("w", "player_faction"), kw=True)
    _bind(lib, "om_player_faction_reassign_on_collapse", [W, ctypes.c_int32], ctypes.c_int32, ("w", "player_faction"), kw=True)
    _bind(lib, "om_player_faction_record_reassignment", [W, ctypes.c_int32, ctypes.c_int32], None, ("w", "old_faction", "new_faction"), kw=True)
    _bind(lib, "om_process_natural_deaths", [W, ctypes.c_uint64], None, ("w", "tick"), kw=True)
    _bind(lib, "om_progression_carried_commander_stats_count", [W], ctypes.c_uint32, ("w",))
    _bind(lib, "om_progression_has_player_level", [W], ctypes.c_int, ("w",))
    _bind(lib, "om_progression_supports_era_unlocks", [W], ctypes.c_int, ("w",))
    _bind(lib, "om_region_assign_regional_commander", [W, ctypes.c_uint32, ctypes.c_int32], None, ("w", "region_idx", "faction_id"), kw=True)
    _bind(lib, "om_region_regional_commander", [W, ctypes.c_uint32], ctypes.c_uint32, ("w", "region_idx"), kw=True)
    _bind(lib, "om_rng_force_descendant_spread", [W, ctypes.c_double], None, ("w", "spread_draw"), kw=True)
    _bind(lib, "om_rng_force_selector_draw", [W, ctypes.c_double], None, ("w", "forced"))
    _bind(lib, "om_save_state_size", [W], ctypes.c_uint32, ("w",))
    _bind(lib, "om_save_state_write", [W, P(ctypes.c_uint8), ctypes.c_uint32], None, ("w", "out", "capacity"))
    _bind(lib, "om_selector_base_rotation_prob", [W, ctypes.c_double], ctypes.c_double, ("w", "delta"), kw=True)
    _bind(lib, "om_selector_clear_pools", [W], None, ("w",))
    _bind(lib, "om_selector_decayed_rotation_prob", [W, ctypes.c_double, ctypes.c_uint32], ctypes.c_double, ("w", "base_p", "chapters"), kw=True)
    _bind(lib, "om_selector_draw_unrelated", [W, ctypes.c_uint32], ctypes.c_uint32, ("w", "mission_region"), kw=True)
    _bind(lib, "om_selector_gather_nemesis_candidates", [W, ctypes.c_uint32], ctypes.c_uint32, ("w", "mission_region"), kw=True)
    _bind(lib, "om_selector_get_nemesis_candidate", [W, ctypes.c_uint32], ctypes.c_uint32, ("w", "candidate"))
    _bind(lib, "om_selector_resolve_fallback_pool", [W, ctypes.c_int], ctypes.c_int, ("w", "initial_pool"), kw=True)
    _bind(lib, "om_selector_roll_pool", [W, ctypes.c_double], ctypes.c_int, ("w", "draw"), kw=True)
    _bind(lib, "om_selector_score_previous_lineage", [W, ctypes.c_uint32, ctypes.c_uint32], ctypes.c_double, ("w", "chapters_ago", "living_nearby"), kw=True)
    _bind(lib, "om_tactical_step", [W], ctypes.c_uint64, ("w",))
    _bind(lib, "om_time_jump_choose_length", [W, ctypes.c_uint32], ctypes.c_uint32, ("w", "requested"), kw=True)
    _bind(lib, "om_time_jump_choose_opening_length", [W], ctypes.c_uint32, ("w",))
    _bind(lib, "om_time_jump_death_pass_count", [W], ctypes.c_uint32, ("w",))
    _bind(lib, "om_time_jump_death_processing_tick", [W], ctypes.c_uint64, ("w",))
    _bind(lib, "om_time_jump_interrupt", [W], ctypes.c_int, ("w",))
    _bind(lib, "om_time_jump_lineage_generation_tick", [W], ctypes.c_uint64, ("w",))
    _bind(lib, "om_time_jump_report_faction_field_deltas_count", [W, V], ctypes.c_uint32, ("w", "report"))
    _bind(lib, "om_time_jump_run", [W, ctypes.c_uint32, V], ctypes.c_int, ("w", "n_ticks", "report"))
    _wrap_optional_trailing_null(lib, "om_time_jump_run")
    _bind(lib, "om_time_jump_run_tracked", [W, ctypes.c_uint32], None, ("w", "jump"))
    _bind(lib, "om_time_jump_start_tick", [W], ctypes.c_uint64, ("w",))
    _bind(lib, "om_world_checksum", [W], ctypes.c_uint64, ("w",))
    _bind(lib, "om_world_set_strategic_tick", [W, ctypes.c_uint64], None, ("w", "tick"))
    _bind(lib, "om_world_strategic_tick", [W], ctypes.c_uint64, ("w",))
    lib._e08_bound = True


def _bind_e09(lib):
    if getattr(lib, "_e09_bound", False):
        return
    P = ctypes.POINTER
    V = ctypes.c_void_p
    W = OMWorldP
    _bind(lib, "om_chronicle_add_chain_event", [W, ctypes.c_int32, ctypes.c_uint32, ctypes.c_uint32], None, ("w", "chain_tag", "region_idx", "category"), kw=True)
    _bind(lib, "om_chronicle_add_cluster_direct", [W, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_double], None, ("w", "cluster_type", "category", "score"), kw=True)
    _bind(lib, "om_chronicle_add_consequence_event", [W, ctypes.c_uint32, ctypes.c_uint32], None, ("w", "region_idx", "outcome"), kw=True)
    _bind(lib, "om_chronicle_add_event", [W, ctypes.c_uint32, ctypes.c_double], None, ("w", "region_idx", "score"), kw=True)
    _bind(lib, "om_chronicle_add_lineage_event", [W, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_double], None, ("w", "lineage_id", "region_idx", "category", "score"), kw=True)
    _bind(lib, "om_chronicle_add_mock_entry", [W, ctypes.c_uint32, ctypes.c_uint64, ctypes.c_uint64], None, ("w", "entry_id", "start_tick", "end_tick"), kw=True)
    _bind(lib, "om_chronicle_add_ownership_change_event", [W, ctypes.c_uint32, ctypes.c_uint64], None, ("w", "region_idx", "tick"), kw=True)
    _bind(lib, "om_chronicle_add_raw_entry", [W, ctypes.c_uint32, ctypes.c_char_p], None, ("w", "entry_id", "text"), kw=True)
    _bind(lib, "om_chronicle_add_regional_event", [W, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_double], ctypes.c_int, ("w", "region_idx", "category", "score"))
    _bind(lib, "om_chronicle_apply_slot_echo_anaphora", [W, ctypes.c_char_p, ctypes.c_char_p], ctypes.c_char_p, ("w", "fragment1_slot", "fragment2_slot"), kw=True)
    _bind(lib, "om_chronicle_apply_word_echo_synonym", [W, ctypes.c_char_p], ctypes.c_char_p, ("w", "text"), kw=True)
    _bind(lib, "om_chronicle_assemble_cluster_entry", [W, ctypes.c_uint32, ctypes.c_uint32, V], ctypes.c_int, ("w", "category", "region_idx", "out_entry"), kw=True)
    _bind(lib, "om_chronicle_assemble_with_seed", [W, ctypes.c_uint64], None, ("w", "seed"), kw=True)
    _bind(lib, "om_chronicle_build_chain_clusters", [W], ctypes.c_uint32, ("w",))
    _bind(lib, "om_chronicle_build_opening_scroll", [W], None, ("w",))
    _bind(lib, "om_chronicle_calculate_score", [W, ctypes.c_uint32, ctypes.c_double, ctypes.c_int, ctypes.c_int, ctypes.c_uint32, ctypes.c_int], ctypes.c_double, ("w", "tier", "delta_sum", "in_mission_region", "has_character", "chain_length", "has_lineage_member"), kw=True)
    _bind(lib, "om_chronicle_categorize_chain_cluster", [W, ctypes.c_char_p, ctypes.c_uint32, ctypes.c_double, ctypes.c_double, ctypes.c_double], ctypes.c_uint32, ("w", "template_name", "n_events", "net_mil", "net_eco", "net_ten"), kw=True)
    _bind(lib, "om_chronicle_categorize_lineage_cluster", [W, ctypes.c_char_p, ctypes.c_double, ctypes.c_double, ctypes.c_double], ctypes.c_uint32, ("w", "template_name", "net_eco", "net_mil", "net_ten"), kw=True)
    _bind(lib, "om_chronicle_categorize_regional_cluster", [W, ctypes.c_int, ctypes.c_double], ctypes.c_uint32, ("w", "has_conquest_or_revolt", "net_eco_pop"), kw=True)
    _bind(lib, "om_chronicle_category_name", [ctypes.c_uint32], ctypes.c_char_p, ("category",))
    _bind(lib, "om_chronicle_chain_category_count", [W], ctypes.c_uint32, ("w",))
    _bind(lib, "om_chronicle_context_multiplier", [W, ctypes.c_int, ctypes.c_int, ctypes.c_uint32, ctypes.c_int], ctypes.c_double, ("w", "in_mission_region", "has_character", "chain_length", "has_lineage_member"), kw=True)
    _bind(lib, "om_chronicle_count_by_type", [W, ctypes.c_uint32], ctypes.c_uint32, ("w", "cluster"))
    _bind(lib, "om_chronicle_dedup_content_words", [W, ctypes.c_double], None, ("w", "threshold"), kw=True)
    _bind(lib, "om_chronicle_dismiss_expanded", [W], None, ("w",))
    _bind(lib, "om_chronicle_distill_and_assemble", [W], None, ("w",))
    _bind(lib, "om_chronicle_entry_get", [W, ctypes.c_uint32, V], ctypes.c_int, ("w", "index", "out"))
    _bind(lib, "om_chronicle_entry_is_retained", [W, ctypes.c_uint32], ctypes.c_int, ("w", "entry_id"), kw=True)
    _bind(lib, "om_chronicle_fragment_batch_exceeds_rejection_limit", [W, ctypes.c_uint32, ctypes.c_uint32], ctypes.c_int, ("w", "rejected_count", "total_count"), kw=True)
    _bind(lib, "om_chronicle_fragment_category_count", [W], ctypes.c_uint32, ("w",))
    _bind(lib, "om_chronicle_fragment_check_near_duplicate", [W, ctypes.c_char_p, ctypes.c_char_p], ctypes.c_int, ("w", "p0", "p1"))
    _bind(lib, "om_chronicle_fragment_inject_invalid_slot", [W, ctypes.c_uint32, ctypes.c_char_p], None, ("w", "category", "invalid_slot"), kw=True)
    _bind(lib, "om_chronicle_fragment_library_load_launch", [W], None, ("w",))
    _bind(lib, "om_chronicle_fragment_library_validate", [W], ctypes.c_int, ("w",))
    _bind(lib, "om_chronicle_fragment_pool_counts", [W, ctypes.c_uint32, V], ctypes.c_int, ("w", "category", "out"))
    _bind(lib, "om_chronicle_generate_map_keyframes", [W], None, ("w",))
    _bind(lib, "om_chronicle_get_cluster", [W, ctypes.c_uint32, V], ctypes.c_int, ("w", "entry", "out"))
    _bind(lib, "om_chronicle_get_full_scroll_text", [W], ctypes.c_char_p, ("w",))
    _bind(lib, "om_chronicle_get_keyframe", [W, ctypes.c_uint32, P(ctypes.c_uint64)], ctypes.c_int, ("w", "i", "tick_out"))
    _bind(lib, "om_chronicle_handle_click", [W, ctypes.c_uint32], ctypes.c_int, ("w", "entry_id"), kw=True)
    _bind(lib, "om_chronicle_has_keyframe_at_tick", [W, ctypes.c_uint64], ctypes.c_int, ("w", "p0"))
    _bind(lib, "om_chronicle_has_keyframe_in_range", [W, ctypes.c_uint64, ctypes.c_uint64], ctypes.c_int, ("w", "p0", "p1"))
    _bind(lib, "om_chronicle_is_lineage_event", [W, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32], ctypes.c_int, ("w", "lineage_id", "region_idx", "attached_character_id", "mission_region"), kw=True)
    _bind(lib, "om_chronicle_is_paused", [W], ctypes.c_int, ("w",))
    _bind(lib, "om_chronicle_keyframe_count", [W], ctypes.c_uint32, ("w",))
    _bind(lib, "om_chronicle_lineage_category_count", [W], ctypes.c_uint32, ("w",))
    _bind(lib, "om_chronicle_map_is_master_clock", [W], ctypes.c_int, ("w",))
    _bind(lib, "om_chronicle_mention_count", [W, ctypes.c_uint32, ctypes.c_int], ctypes.c_uint32, ("w", "index", "expanded"))
    _bind(lib, "om_chronicle_mention_get", [W, ctypes.c_uint32, ctypes.c_int, ctypes.c_uint32, V], ctypes.c_int, ("w", "index", "expanded", "mention_idx", "out"))
    _bind(lib, "om_chronicle_mock_populate_events", [W, ctypes.c_uint32], None, ("w", "n_events"), kw=True)
    _bind(lib, "om_chronicle_presentation_entry_hold_sec", [W], ctypes.c_double, ("w",))
    _bind(lib, "om_chronicle_presentation_map_width_ratio", [W], ctypes.c_double, ("w",))
    _bind(lib, "om_chronicle_presentation_slide_in_sec", [W], ctypes.c_double, ("w",))
    _bind(lib, "om_chronicle_presentation_slide_out_sec", [W], ctypes.c_double, ("w",))
    _bind(lib, "om_chronicle_presentation_word_cadence_sec", [W], ctypes.c_double, ("w",))
    _bind(lib, "om_chronicle_presentation_word_fade_sec", [W], ctypes.c_double, ("w",))
    _bind(lib, "om_chronicle_regional_category_count", [W], ctypes.c_uint32, ("w",))
    _bind(lib, "om_chronicle_render_character_rank", [W, ctypes.c_uint32], ctypes.c_char_p, ("w", "character_id"), kw=True)
    _bind(lib, "om_chronicle_render_region_mention", [W, ctypes.c_uint32, ctypes.c_int], ctypes.c_char_p, ("w", "region_idx", "is_first_mention"), kw=True)
    _bind(lib, "om_chronicle_rendered_entry_count", [W], ctypes.c_uint32, ("w",))
    _bind(lib, "om_chronicle_score_base", [W, ctypes.c_uint32, ctypes.c_double], ctypes.c_double, ("w", "tier", "delta_sum"), kw=True)
    _bind(lib, "om_chronicle_score_event", [W, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_double], ctypes.c_double, ("w", "region_idx", "tier", "delta_sum"), kw=True)
    _bind(lib, "om_chronicle_select_clusters", [W], None, ("w",))
    _bind(lib, "om_chronicle_selected_category_count", [W, ctypes.c_uint32], ctypes.c_uint32, ("w", "category"), kw=True)
    _bind(lib, "om_chronicle_set_entry_state", [W, ctypes.c_uint32, ctypes.c_int], None, ("w", "entry_id", "is_printing"), kw=True)
    _bind(lib, "om_chronicle_validate_event_template_prose", [W], ctypes.c_int, ("w",))
    _bind(lib, "om_event_template_chronicle_prose", [W, ctypes.c_uint32], ctypes.c_char_p, ("w", "template"))
    _bind(lib, "om_event_template_count", [W], ctypes.c_uint32, ("w",))
    _bind(lib, "om_events_load_launch", [W], None, ("w",))
    _bind(lib, "om_mission_last_region", [W], ctypes.c_uint32, ("w",))
    _bind(lib, "om_time_jump_get_ownership_snapshot", [W, ctypes.c_uint32, P(ctypes.c_int32), ctypes.c_uint32], ctypes.c_uint32, ("w", "k", "owners_out", "cap"))
    _bind(lib, "om_time_jump_ownership_snapshot_count", [W], ctypes.c_uint32, ("w",))
    lib._e09_bound = True


def _bind_e10(lib):
    if getattr(lib, "_e10_bound", False):
        return
    P = ctypes.POINTER
    V = ctypes.c_void_p
    W = OMWorldP
    _bind(lib, "om_archetype_base_time_ticks", [ctypes.c_uint32], ctypes.c_uint64, ("archetype",))
    _bind(lib, "om_chronicle_has_mission_consequence_flag", [W], ctypes.c_int, ("w",))
    _bind(lib, "om_consequence_apply_clamped", [ctypes.c_double, ctypes.c_double], ctypes.c_double, ("current", "delta"))
    _bind(lib, "om_consequence_eval_delta_current", [ctypes.c_double, ctypes.c_double], ctypes.c_double, ("current", "pct"))
    _bind(lib, "om_consequence_eval_delta_deficit", [ctypes.c_double, ctypes.c_double], ctypes.c_double, ("current", "pct"))
    _bind(lib, "om_mission_allocate_force_profile", [W, ctypes.c_uint32, ctypes.c_double, P(ctypes.c_double)], None, ("w", "archetype", "total_power", "out_ratios"))
    _bind(lib, "om_mission_apply_capacity_shortfall", [W, ctypes.c_double], None, ("w", "capacity"))
    _bind(lib, "om_mission_apply_consequences", [W, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_int32], None, ("w", "region_idx", "archetype", "band"))
    _bind(lib, "om_mission_apply_target_adjacent_player", [W, ctypes.c_uint32, ctypes.c_int, ctypes.c_double], None, ("w", "region_idx", "field", "delta"))
    _bind(lib, "om_mission_archetype_count", [W], ctypes.c_uint32, ("w",))
    _bind(lib, "om_mission_assemble_briefing", [W, V], ctypes.c_int, ("w", "out"))
    _bind(lib, "om_mission_assign_commander", [W, ctypes.c_uint32], ctypes.c_int, ("w", "unit_id"))
    _bind(lib, "om_mission_build_candidate_pool", [W], None, ("w",))
    _bind(lib, "om_mission_build_objectives", [W, ctypes.c_uint32], None, ("w", "archetype"))
    _bind(lib, "om_mission_can_edit_loadout", [W], ctypes.c_int, ("w",))
    _bind(lib, "om_mission_candidate_score", [ctypes.c_double, ctypes.c_double, ctypes.c_double], ctypes.c_double, ("urgency", "relevance", "preference"))
    _bind(lib, "om_mission_candidates", [W, V, ctypes.c_uint32], ctypes.c_uint32, ("w", "out", "max"))
    _bind(lib, "om_mission_check_terminated", [W, ctypes.c_uint32], ctypes.c_int, ("w", "p1"))
    _bind(lib, "om_mission_classify_band", [ctypes.c_uint32, ctypes.c_double], ctypes.c_int32, ("archetype", "final"))
    _bind(lib, "om_mission_compute_base_parity", [ctypes.c_double], ctypes.c_double, ("c",))
    _bind(lib, "om_mission_compute_difficulty_parity", [ctypes.c_double, ctypes.c_int], ctypes.c_double, ("base", "difficulty"))
    _bind(lib, "om_mission_compute_enemy_power", [W, ctypes.c_uint32, ctypes.c_double, ctypes.c_double, ctypes.c_double], ctypes.c_double, ("w", "archetype", "committed_budget", "military", "population"))
    _bind(lib, "om_mission_compute_final_score", [ctypes.c_double, ctypes.c_double], ctypes.c_double, ("o", "r"))
    _bind(lib, "om_mission_compute_parity", [ctypes.c_double, ctypes.c_int], ctypes.c_double, ("p0", "p1"))
    _bind(lib, "om_mission_compute_preference", [W, ctypes.c_uint32], ctypes.c_double, ("w", "archetype"))
    _bind(lib, "om_mission_compute_relevance", [W, ctypes.c_uint32, ctypes.c_uint32], ctypes.c_double, ("w", "region_idx", "archetype"))
    _bind(lib, "om_mission_compute_retention", [ctypes.c_double, ctypes.c_double], ctypes.c_double, ("deployed_power", "surviving_power"))
    _bind(lib, "om_mission_compute_time_limit", [ctypes.c_uint64, ctypes.c_double], ctypes.c_uint64, ("B", "u"))
    _bind(lib, "om_mission_compute_urgency", [W, ctypes.c_uint32, ctypes.c_uint32], ctypes.c_double, ("w", "region_idx", "archetype"))
    _bind(lib, "om_mission_end", [W], None, ("w",))
    _bind(lib, "om_mission_eval_commander_fate", [ctypes.c_double, ctypes.c_double], ctypes.c_int32, ("hp", "max_hp"))
    _bind(lib, "om_mission_eval_destroy_targets", [W, ctypes.c_uint32, ctypes.c_uint32], ctypes.c_double, ("w", "objective_idx", "destroyed"))
    _bind(lib, "om_mission_eval_eliminate", [W, ctypes.c_uint32, ctypes.c_double], ctypes.c_double, ("w", "objective_idx", "hp_destroyed"))
    _bind(lib, "om_mission_eval_escort", [W, ctypes.c_uint32, ctypes.c_uint32], ctypes.c_double, ("w", "objective_idx", "reached_alive"))
    _bind(lib, "om_mission_eval_hold_zone", [W, ctypes.c_uint32, ctypes.c_uint32], None, ("w", "objective_idx", "enemies_inside"))
    _bind(lib, "om_mission_eval_survive", [W, ctypes.c_uint32, ctypes.c_uint64, ctypes.c_int], ctypes.c_double, ("w", "objective_idx", "elapsed_ticks", "player_alive"))
    _bind(lib, "om_mission_fallback_archetype", [W], ctypes.c_uint32, ("w",))
    _bind(lib, "om_mission_fallback_enemy", [W, ctypes.c_uint32], ctypes.c_int32, ("w", "region_idx"))
    _bind(lib, "om_mission_fallback_region", [W], ctypes.c_uint32, ("w",))
    _bind(lib, "om_mission_fill_player_force", [W, ctypes.c_double, ctypes.c_double], ctypes.c_double, ("w", "P", "parity"))
    _bind(lib, "om_mission_get_archetype_metadata", [W, ctypes.c_uint32, V], ctypes.c_int, ("w", "archetype", "out"))
    _bind(lib, "om_mission_get_archetype_preference_weight", [W, ctypes.c_uint32, ctypes.c_int], ctypes.c_double, ("w", "archetype", "is_rare"))
    _bind(lib, "om_mission_get_band", [W], ctypes.c_int32, ("w",))
    _bind(lib, "om_mission_get_briefing_controls", [W], ctypes.c_uint32, ("w",))
    _bind(lib, "om_mission_get_briefing_text", [W, ctypes.c_char_p, ctypes.c_uint32], None, ("w", "out", "cap"))
    _bind(lib, "om_mission_get_candidate_score", [W, ctypes.c_uint32, ctypes.c_uint32], ctypes.c_double, ("w", "region_idx", "archetype"))
    _bind(lib, "om_mission_get_commander_unit", [W], ctypes.c_uint32, ("w",))
    _bind(lib, "om_mission_get_compatible_layouts", [W, ctypes.c_uint32, P(ctypes.c_uint32), ctypes.c_uint32], ctypes.c_uint32, ("w", "archetype", "out", "max"))
    _bind(lib, "om_mission_get_debrief", [W, V], ctypes.c_int, ("w", "out"))
    _bind(lib, "om_mission_get_deployed_force_count", [W], ctypes.c_uint32, ("w",))
    _bind(lib, "om_mission_get_enemy_power", [W], ctypes.c_double, ("w",))
    _bind(lib, "om_mission_get_force_count", [W], ctypes.c_uint32, ("w",))
    _bind(lib, "om_mission_get_force_group", [W, ctypes.c_uint32], ctypes.c_int32, ("w", "i"))
    _bind(lib, "om_mission_get_force_unit", [W, ctypes.c_uint32, P(ctypes.c_int32), P(ctypes.c_int32)], ctypes.c_int, ("w", "i", "type", "tier"))
    _bind(lib, "om_mission_get_objective_completion", [W, ctypes.c_uint32], ctypes.c_double, ("w", "objective_idx"))
    _bind(lib, "om_mission_get_objective_score", [W], ctypes.c_double, ("w",))
    _bind(lib, "om_mission_get_objectives", [W, V, ctypes.c_uint32], ctypes.c_uint32, ("w", "out", "max"))
    _bind(lib, "om_mission_get_player_parity", [W, ctypes.c_int32], ctypes.c_double, ("w", "faction_id"))
    _bind(lib, "om_mission_get_player_units", [W, ctypes.c_int32, P(ctypes.c_uint32), ctypes.c_uint32], None, ("w", "faction_id", "out", "max"))
    _bind(lib, "om_mission_get_region_delta", [W, P(ctypes.c_double), P(ctypes.c_double), P(ctypes.c_double), P(ctypes.c_double)], ctypes.c_int, ("w", "military", "economy", "tension", "population"))
    _bind(lib, "om_mission_get_shortfall_text", [W, ctypes.c_char_p, ctypes.c_uint32], None, ("w", "out", "cap"))
    _bind(lib, "om_mission_get_time_limit", [W], ctypes.c_uint64, ("w",))
    _bind(lib, "om_mission_has_ended", [W], ctypes.c_int, ("w",))
    _bind(lib, "om_mission_inject_candidate", [W, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_double], None, ("w", "region_idx", "archetype", "score"))
    _bind(lib, "om_mission_is_ended", [W], ctypes.c_int, ("w",))
    _bind(lib, "om_mission_load_launch_library", [W], None, ("w",))
    _bind(lib, "om_mission_objective_count", [W], ctypes.c_uint32, ("w",))
    _bind(lib, "om_mission_refresh_context", [W, ctypes.c_int32], None, ("w", "region"))
    _bind(lib, "om_mission_resolve_refusal", [W, ctypes.c_uint32], None, ("w", "region_idx"))
    _bind(lib, "om_mission_select", [W], ctypes.c_uint32, ("w",))
    _bind(lib, "om_mission_select_candidate", [W], ctypes.c_uint32, ("w",))
    _bind(lib, "om_mission_select_layout", [W, ctypes.c_uint32, ctypes.c_uint32], ctypes.c_uint32, ("w", "archetype", "p2"))
    _bind(lib, "om_mission_set_archetype_profile", [W, ctypes.c_uint32, P(ctypes.c_double), ctypes.c_uint32], None, ("w", "archetype", "profile", "n_types"))
    _bind(lib, "om_mission_set_candidate_viable", [W, ctypes.c_uint32, ctypes.c_int], None, ("w", "archetype", "viable"))
    _bind(lib, "om_mission_set_conflict_context", [W, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_double, ctypes.c_uint32], None, ("w", "region_idx", "recent_attacks", "attack_budget_sum", "adjacent_lost"))
    _bind(lib, "om_mission_set_lineage_context", [W, ctypes.c_uint32, ctypes.c_double, ctypes.c_uint32, ctypes.c_uint32], None, ("w", "region_idx", "lineage", "hops", "times_run"))
    _bind(lib, "om_mission_set_objective_completion", [W, ctypes.c_uint32, ctypes.c_double], None, ("w", "objective_idx", "completion"))
    _bind(lib, "om_mission_set_player_units", [W, ctypes.c_int32, P(ctypes.c_uint32), ctypes.c_uint32], None, ("w", "faction_id", "counts", "n_types"))
    _bind(lib, "om_mission_set_preference", [W, ctypes.c_uint32, ctypes.c_double], None, ("w", "archetype", "weight"))
    _bind(lib, "om_mission_set_revolt_events", [W, ctypes.c_uint32, ctypes.c_uint32], None, ("w", "region_idx", "recent_revolt_events"))
    _bind(lib, "om_mission_setup", [W, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_int], None, ("w", "p1", "archetype", "lineage_connection"))
    _bind(lib, "om_mission_setup_destroy_targets", [W, ctypes.c_uint32, ctypes.c_uint32], None, ("w", "objective_idx", "total"))
    _bind(lib, "om_mission_setup_eliminate", [W, ctypes.c_uint32, ctypes.c_double], None, ("w", "objective_idx", "initial_hp"))
    _bind(lib, "om_mission_setup_escort", [W, ctypes.c_uint32, ctypes.c_uint32], None, ("w", "objective_idx", "total"))
    _bind(lib, "om_mission_setup_fallback", [W, ctypes.c_uint32, ctypes.c_int32], None, ("w", "region_idx", "enemy_faction"))
    _bind(lib, "om_mission_setup_hold_zone", [W, ctypes.c_uint32, ctypes.c_uint64], None, ("w", "objective_idx", "required_ticks"))
    _bind(lib, "om_mission_setup_survive", [W, ctypes.c_uint32, ctypes.c_uint64], None, ("w", "objective_idx", "required_ticks"))
    _bind(lib, "om_mission_setup_tactical", [W, ctypes.c_uint32, ctypes.c_uint64], None, ("w", "p1", "time_limit"))
    _bind(lib, "om_mission_setup_termination", [W, ctypes.c_uint32, ctypes.c_int, ctypes.c_int, ctypes.c_uint64, ctypes.c_uint64, ctypes.c_int], None, ("w", "p1", "primary_complete", "p3", "tick", "time_limit", "player_alive"))
    _bind(lib, "om_objective_get_node", [W, ctypes.c_uint32], ctypes.c_int32, ("w", "objective_idx"))
    _bind(lib, "om_objective_get_radius", [W, ctypes.c_uint32], ctypes.c_double, ("w", "objective_idx"))
    _bind(lib, "om_objective_set_center", [W, ctypes.c_uint32, ctypes.c_double, ctypes.c_double], ctypes.c_int, ("w", "objective_idx", "x", "y"))
    _bind(lib, "om_player_faction", [W], ctypes.c_int32, ("w",))
    _bind(lib, "om_region_get_held_since", [W, ctypes.c_uint32], ctypes.c_int64, ("w", "idx"))
    _bind(lib, "om_region_get_owner", [W, ctypes.c_uint32], ctypes.c_int32, ("w", "idx"))
    _bind(lib, "om_region_set_owner", [W, ctypes.c_uint32, ctypes.c_int32, ctypes.c_int64], None, ("w", "idx", "faction_id", "held_since_tick"))
    _bind(lib, "om_set_neighbors", [W, ctypes.c_uint32, ctypes.c_uint32], None, ("w", "a", "b"))
    _bind(lib, "om_tactical_tick", [W], ctypes.c_uint64, ("w",))
    _bind(lib, "om_unit_get_profile", [ctypes.c_uint32, ctypes.c_int, V], ctypes.c_int, ("unit_type", "difficulty", "out"))
    _bind(lib, "om_unit_power", [ctypes.c_uint32], ctypes.c_double, ("unit_type",))
    lib._e10_bound = True


def _bind_e11(lib):
    if getattr(lib, "_e11_bound", False):
        return
    P = ctypes.POINTER
    V = ctypes.c_void_p
    W = OMWorldP
    _bind(lib, "om_command_activate_ability", [W, P(ctypes.c_uint32), ctypes.c_uint32, ctypes.c_double, ctypes.c_double], ctypes.c_int, ("w", "unit_ids", "n_units", "target_x", "target_y"))
    _wrap_ids_list_optional_target(lib, "om_command_activate_ability")
    _bind(lib, "om_command_attack_move", [W, P(ctypes.c_uint32), ctypes.c_uint32, ctypes.c_double, ctypes.c_double], ctypes.c_int, ("w", "unit_ids", "n_units", "x", "y"))
    _wrap_ids_list_or_single(lib, "om_command_attack_move")
    _bind(lib, "om_command_attack_target", [W, P(ctypes.c_uint32), ctypes.c_uint32, ctypes.c_uint32], ctypes.c_int, ("w", "unit_ids", "n_units", "target_unit"))
    _wrap_ids_list_or_single(lib, "om_command_attack_target")
    _bind(lib, "om_command_move", [W, P(ctypes.c_uint32), ctypes.c_uint32, ctypes.c_double, ctypes.c_double], ctypes.c_int, ("w", "unit_ids", "n_units", "x", "y"))
    _wrap_ids_list_or_single(lib, "om_command_move")
    _bind(lib, "om_cue_lookup", [ctypes.c_char_p], ctypes.c_uint32, ("name",))
    _bind(lib, "om_era_elevation_damage_bonus_enabled", [W], ctypes.c_int, ("w",))
    _bind(lib, "om_map_add_cover", [W, ctypes.c_double, ctypes.c_double, ctypes.c_double, ctypes.c_double], ctypes.c_uint32, ("w", "x", "y", "radius", "height"))
    _bind(lib, "om_roster_register_custom_unit", [W, ctypes.c_uint32, ctypes.c_int, ctypes.c_char_p, ctypes.c_double, ctypes.c_double, ctypes.c_double, ctypes.c_double, ctypes.c_double, ctypes.c_double, ctypes.c_double, ctypes.c_double, ctypes.c_int], ctypes.c_int, ("w", "type_id", "category", "role", "max_hp", "base_damage", "attack_interval", "attack_range", "speed", "sensor_radius", "layer_transition_time", "aoe_radius", "ability_id"))
    _bind(lib, "om_roster_set_cone", [W, ctypes.c_int, ctypes.c_double, ctypes.c_double, ctypes.c_double], ctypes.c_int, ("w", "unit_type", "range", "half_angle_deg", "share"))
    _bind(lib, "om_tactical_category_multiplier", [W, ctypes.c_int, ctypes.c_int], ctypes.c_double, ("w", "attacker_category", "target_category"))
    _bind(lib, "om_tactical_disable_abilities", [W], None, ("w",))
    _bind(lib, "om_tactical_get_param", [W, ctypes.c_int], ctypes.c_double, ("w", "p"))
    _bind(lib, "om_tactical_reset", [W], None, ("w",))
    _bind(lib, "om_tactical_run", [W, ctypes.c_uint64], ctypes.c_uint64, ("w", "n_ticks"))
    _bind(lib, "om_tactical_run_until_eliminated", [W], ctypes.c_uint64, ("w",))
    _bind(lib, "om_tactical_run_until_engagement_ends", [W, ctypes.c_uint32], ctypes.c_uint64, ("w", "unit_id"))
    _bind(lib, "om_tactical_set_param", [W, ctypes.c_int, ctypes.c_double], ctypes.c_int, ("w", "p", "value"))
    _bind(lib, "om_tactical_spawn_force_composition", [W, ctypes.c_int32, ctypes.c_uint32, ctypes.c_char_p], None, ("w", "faction_id", "count", "composition"))
    _bind(lib, "om_tactical_target_validation_runs_every_tick", [W], ctypes.c_int, ("w",))
    _bind(lib, "om_tactical_telegraph_active", [W, ctypes.c_double, ctypes.c_double], ctypes.c_int, ("w", "x", "y"))
    _bind(lib, "om_tactical_zone_visible_to_enemy", [W, ctypes.c_uint32], ctypes.c_int, ("w", "unit_id"))
    _bind(lib, "om_tick_read_ability_events", [W, V, ctypes.c_uint32], ctypes.c_uint32, ("w", "out", "max"))
    _wrap_records(lib, "om_tick_read_ability_events", OMAbilityEvent)
    _bind(lib, "om_unit_ability_active", [W, ctypes.c_uint32], ctypes.c_int, ("w", "unit_id"))
    _bind(lib, "om_unit_ability_cooldown", [W, ctypes.c_uint32], ctypes.c_double, ("w", "unit_id"))
    _bind(lib, "om_unit_alive", [W, ctypes.c_uint32], ctypes.c_int, ("w", "unit_id"))
    _bind(lib, "om_unit_apply_trait_modifier", [W, ctypes.c_uint32, ctypes.c_int, ctypes.c_double], None, ("w", "unit_id", "stat_field", "delta"))
    _bind(lib, "om_unit_damage_reduction", [W, ctypes.c_uint32], ctypes.c_double, ("w", "unit_id"))
    _bind(lib, "om_unit_deal_damage", [W, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_double], None, ("w", "p1", "p2", "p3"))
    _bind(lib, "om_unit_effective_speed", [W, ctypes.c_uint32], ctypes.c_double, ("w", "unit_id"))
    _bind(lib, "om_unit_fire_aoe_attack", [W, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_double], None, ("w", "attacker_id", "target_id", "radius"))
    _bind(lib, "om_unit_get_engaged", [W, ctypes.c_uint32], ctypes.c_int, ("w", "unit"))
    _bind(lib, "om_unit_get_group_id", [W, ctypes.c_uint32], ctypes.c_uint32, ("w", "unit"))
    _bind(lib, "om_unit_get_leash_anchor", [W, ctypes.c_uint32, P(ctypes.c_double), P(ctypes.c_double)], ctypes.c_int, ("w", "unit", "x", "y"))
    _bind(lib, "om_unit_hp", [W, ctypes.c_uint32], ctypes.c_double, ("w", "unit_id"))
    _bind(lib, "om_unit_in_backswing", [W, ctypes.c_uint32], ctypes.c_int, ("w", "unit_id"))
    _bind(lib, "om_unit_in_flinch", [W, ctypes.c_uint32], ctypes.c_int, ("w", "unit_id"))
    _bind(lib, "om_unit_order_speed", [W, ctypes.c_uint32], ctypes.c_double, ("w", "unit_id"))
    _bind(lib, "om_unit_output_multiplier", [W, ctypes.c_uint32], ctypes.c_double, ("w", "unit_id"))
    _bind(lib, "om_unit_position_x", [W, ctypes.c_uint32], ctypes.c_double, ("w", "unit_id"))
    _bind(lib, "om_unit_position_y", [W, ctypes.c_uint32], ctypes.c_double, ("w", "unit_id"))
    _bind(lib, "om_unit_profile_ability_count", [W, ctypes.c_int], ctypes.c_uint32, ("w", "unit_type"))
    _bind(lib, "om_unit_profile_aoe_radius", [W, ctypes.c_int], ctypes.c_double, ("w", "unit_type"))
    _bind(lib, "om_unit_profile_attack_interval", [W, ctypes.c_int], ctypes.c_double, ("w", "unit_type"))
    _bind(lib, "om_unit_profile_attack_range", [W, ctypes.c_int], ctypes.c_double, ("w", "unit_type"))
    _bind(lib, "om_unit_profile_base_damage", [W, ctypes.c_int], ctypes.c_double, ("w", "unit_type"))
    _bind(lib, "om_unit_profile_category", [W, ctypes.c_int], ctypes.c_int, ("w", "unit_type"))
    _bind(lib, "om_unit_profile_dps", [W, ctypes.c_int], ctypes.c_double, ("w", "unit_type"))
    _bind(lib, "om_unit_profile_layer_transition_time", [W, ctypes.c_int], ctypes.c_double, ("w", "unit_type"))
    _bind(lib, "om_unit_profile_max_hp", [W, ctypes.c_int], ctypes.c_double, ("w", "unit_type"))
    _bind(lib, "om_unit_profile_sensor_radius", [W, ctypes.c_int], ctypes.c_double, ("w", "unit_type"))
    _bind(lib, "om_unit_profile_speed", [W, ctypes.c_int], ctypes.c_double, ("w", "unit_type"))
    _bind(lib, "om_unit_profile_trait_count", [W, ctypes.c_int], ctypes.c_uint32, ("w", "unit_type"))
    _bind(lib, "om_unit_render_craft_count", [W, ctypes.c_int], ctypes.c_uint32, ("w", "unit_type"))
    _bind(lib, "om_unit_render_silhouette_size", [W, ctypes.c_int], ctypes.c_double, ("w", "unit_type"))
    _bind(lib, "om_unit_set_ability_cooldown", [W, ctypes.c_uint32, ctypes.c_double], None, ("w", "unit_id", "ticks"))
    _bind(lib, "om_unit_set_brace_active", [W, ctypes.c_uint32, ctypes.c_int], None, ("w", "unit_id", "on"))
    _bind(lib, "om_unit_set_elevation_tier", [W, ctypes.c_uint32, ctypes.c_int], None, ("w", "unit_id", "tier"))
    _bind(lib, "om_unit_set_fortify_active", [W, ctypes.c_uint32, ctypes.c_int], None, ("w", "unit_id", "on"))
    _bind(lib, "om_unit_set_hp", [W, ctypes.c_uint32, ctypes.c_double], None, ("w", "p0", "p1"))
    _bind(lib, "om_unit_set_stealth", [W, ctypes.c_uint32, ctypes.c_int], None, ("w", "unit_id", "on"))
    _bind(lib, "om_unit_set_warden_aura_active", [W, ctypes.c_uint32, ctypes.c_int], None, ("w", "unit_id", "on"))
    _bind(lib, "om_unit_spawn", [W, ctypes.c_int, ctypes.c_int32, ctypes.c_double, ctypes.c_double, ctypes.c_uint32], ctypes.c_uint32, ("w", "unit_type", "faction_id", "x", "y", "layer"))
    _bind(lib, "om_unit_spawn_for_category", [W, ctypes.c_int, ctypes.c_int32, ctypes.c_double, ctypes.c_double, ctypes.c_uint32], ctypes.c_uint32, ("w", "category", "faction_id", "x", "y", "layer"))
    _bind(lib, "om_unit_target", [W, ctypes.c_uint32], ctypes.c_int32, ("w", "unit_id"))
    _bind(lib, "om_unit_targeting_cohort", [W, ctypes.c_uint32], ctypes.c_uint32, ("w", "unit_id"))
    _bind(lib, "om_unit_teleport", [W, ctypes.c_uint32, ctypes.c_double, ctypes.c_double, ctypes.c_uint32], None, ("w", "unit", "x", "y", "layer"))
    lib._e11_bound = True


def _bind_e12(lib):
    if getattr(lib, "_e12_bound", False):
        return
    P = ctypes.POINTER
    V = ctypes.c_void_p
    W = OMWorldP
    _bind(lib, "om_client_snapshot_read", [W], V, ("w",))
    _wrap_client_snapshot(lib, "om_client_snapshot_read", OmClientSnapshot)
    _bind(lib, "om_fog_get_drawn_sensor_circle_radius", [W, ctypes.c_uint32], ctypes.c_double, ("w", "unit"))
    _bind(lib, "om_fog_get_treatment_at", [W, ctypes.c_double, ctypes.c_double, ctypes.c_uint32], ctypes.c_int, ("w", "x", "y", "layer"))
    _bind(lib, "om_map_add_hazard_zone", [W, ctypes.c_double, ctypes.c_double, ctypes.c_double], ctypes.c_uint32, ("w", "x", "y", "p2"))
    _bind(lib, "om_map_add_interference_zone", [W, ctypes.c_double, ctypes.c_double, ctypes.c_uint32, ctypes.c_double, ctypes.c_double], None, ("w", "x", "y", "layer", "intensity", "radius"))
    _bind(lib, "om_map_add_moving_interference_zone", [W, ctypes.c_double, ctypes.c_double, ctypes.c_uint32, ctypes.c_double, ctypes.c_double, ctypes.c_double, ctypes.c_double], None, ("w", "x", "y", "layer", "intensity", "radius", "vx", "vy"))
    _bind(lib, "om_map_add_obstacle", [W, ctypes.c_double, ctypes.c_double, ctypes.c_double], ctypes.c_uint32, ("w", "x", "y", "radius"))
    _bind(lib, "om_map_add_spawn_point", [W, ctypes.c_double, ctypes.c_double, ctypes.c_int32], ctypes.c_uint32, ("w", "x", "y", "faction_id"))
    _bind(lib, "om_map_add_spine_node", [W, ctypes.c_double, ctypes.c_double, ctypes.c_int], ctypes.c_uint32, ("w", "x", "y", "p2"))
    _bind(lib, "om_map_add_structure", [W, ctypes.c_double, ctypes.c_double, ctypes.c_int32], ctypes.c_uint32, ("w", "x", "y", "owner_faction"))
    _bind(lib, "om_map_add_vantage_node", [W, ctypes.c_double, ctypes.c_double, ctypes.c_double], None, ("w", "x", "y", "radius"))
    _bind(lib, "om_map_get_obstacle_at", [W, ctypes.c_uint32, P(ctypes.c_double), P(ctypes.c_double), P(ctypes.c_double)], ctypes.c_int, ("w", "i", "x", "y", "r"))
    _bind(lib, "om_map_obstacle_count", [W], ctypes.c_uint32, ("w",))
    _bind(lib, "om_mission_begin", [W], None, ("w",))
    _bind(lib, "om_mission_get_clock", [W], ctypes.c_uint64, ("w",))
    _bind(lib, "om_mission_get_phase", [W], ctypes.c_int, ("w",))
    _bind(lib, "om_mission_is_started", [W], ctypes.c_int, ("w",))
    _bind(lib, "om_mission_set_phase", [W, ctypes.c_int], None, ("w", "phase"))
    _bind(lib, "om_objective_get_done", [W, ctypes.c_uint32], ctypes.c_int, ("w", "idx"))
    _bind(lib, "om_player_can_see", [W, ctypes.c_int32, ctypes.c_uint32], ctypes.c_int, ("w", "faction_id", "unit"))
    _bind(lib, "om_player_can_see_friendly", [W, ctypes.c_int32, ctypes.c_uint32], ctypes.c_int, ("w", "faction_id", "unit"))
    _bind(lib, "om_player_can_see_unit", [W, ctypes.c_int32, ctypes.c_uint32], ctypes.c_int, ("w", "p0", "unit"))
    _bind(lib, "om_recon_get_terrain_visibility_ratio", [W], ctypes.c_double, ("w",))
    _bind(lib, "om_recon_is_enemy_visible", [W, ctypes.c_uint32], ctypes.c_int, ("w", "unit"))
    _bind(lib, "om_recon_is_feature_visible", [W, ctypes.c_uint32], ctypes.c_int, ("w", "feature_id"))
    _bind(lib, "om_recon_is_spawn_point_visible", [W, ctypes.c_uint32], ctypes.c_int, ("w", "spawn_id"))
    _bind(lib, "om_recon_is_structure_ownership_visible", [W, ctypes.c_uint32], ctypes.c_int, ("w", "structure_id"))
    _bind(lib, "om_set_era_flag", [W, ctypes.c_char_p, ctypes.c_int], None, ("w", "name", "on"))
    _bind(lib, "om_set_era_name", [W, ctypes.c_char_p], None, ("w", "name"))
    _bind(lib, "om_strategic_agent_read_region_field", [W, ctypes.c_int32, ctypes.c_uint32, ctypes.c_int], ctypes.c_double, ("w", "p0", "region_idx", "field"))
    _bind(lib, "om_structure_count", [W], ctypes.c_uint32, ("w",))
    _bind(lib, "om_structure_get_at", [W, ctypes.c_uint32], ctypes.c_uint32, ("w", "i"))
    _bind(lib, "om_tactical_event_count", [W], ctypes.c_uint32, ("w",))
    _bind(lib, "om_tactical_event_get_at", [W, ctypes.c_uint32, P(ctypes.c_int32), P(ctypes.c_uint32), P(ctypes.c_int32), P(ctypes.c_uint64)], ctypes.c_int, ("w", "i", "kind", "a", "b", "tick"))
    _bind(lib, "om_terrain_get_heights", [W, P(ctypes.c_int32), ctypes.c_uint32], ctypes.c_uint32, ("w", "out", "cap"))
    _bind(lib, "om_unit_acquire_target", [W, ctypes.c_uint32], None, ("w", "unit"))
    _bind(lib, "om_unit_attack", [W, ctypes.c_uint32, ctypes.c_uint32], None, ("w", "attacker", "target"))
    _bind(lib, "om_unit_brace_phase", [W, ctypes.c_uint32], ctypes.c_int32, ("w", "unit_id"))
    _bind(lib, "om_unit_can_see", [W, ctypes.c_uint32, ctypes.c_uint32], ctypes.c_int, ("w", "observer", "target"))
    _bind(lib, "om_unit_count", [W], ctypes.c_uint32, ("w",))
    _bind(lib, "om_unit_get_cross_layer_factor", [W, ctypes.c_uint32, ctypes.c_uint32], ctypes.c_double, ("w", "unit", "p0"))
    _bind(lib, "om_unit_get_effective_sensor_radius_to_target_elevation", [W, ctypes.c_uint32, ctypes.c_uint32], ctypes.c_double, ("w", "unit", "target_elevation_tier"))
    _bind(lib, "om_unit_get_faction", [W, ctypes.c_uint32], ctypes.c_int32, ("w", "unit_id"))
    _bind(lib, "om_unit_get_hp", [W, ctypes.c_uint32], ctypes.c_double, ("w", "unit"))
    _bind(lib, "om_unit_get_layer", [W, ctypes.c_uint32], ctypes.c_int32, ("w", "unit_id"))
    _bind(lib, "om_unit_get_pos", [W, ctypes.c_uint32, P(ctypes.c_double), P(ctypes.c_double)], ctypes.c_int, ("w", "unit", "out_x", "out_y"))
    _wrap_out_pair(lib, "om_unit_get_pos")
    _bind(lib, "om_unit_get_target", [W, ctypes.c_uint32], ctypes.c_uint32, ("w", "unit"))
    _bind(lib, "om_unit_get_unit_type", [W, ctypes.c_uint32], ctypes.c_int32, ("w", "unit_id"))
    _bind(lib, "om_unit_id_at", [W, ctypes.c_uint32], ctypes.c_uint32, ("w", "index"))
    _bind(lib, "om_unit_spawn_with_elevation", [W, ctypes.c_int, ctypes.c_int32, ctypes.c_double, ctypes.c_double, ctypes.c_uint32, ctypes.c_uint32], ctypes.c_uint32, ("w", "unit_type", "faction_id", "x", "y", "layer", "elevation_tier"))
    _bind(lib, "om_visibility_compute", [W], None, ("w",))
    _bind(lib, "om_visibility_set_player_fog", [W, ctypes.c_int], None, ("w", "on"))
    _bind(lib, "om_world_get_state_checksum", [W], ctypes.c_uint64, ("w",))
    _bind(lib, "om_zone_sample_interference", [W, ctypes.c_double, ctypes.c_double, ctypes.c_uint32], ctypes.c_double, ("w", "x", "y", "layer"))
    lib._e12_bound = True


def _bind_e13(lib):
    if getattr(lib, "_e13_bound", False):
        return
    P = ctypes.POINTER
    V = ctypes.c_void_p
    W = OMWorldP
    _bind(lib, "om_collision_pass", [W], None, ("w",))
    _bind(lib, "om_combat_can_engage", [W, ctypes.c_uint32, ctypes.c_uint32], ctypes.c_int, ("w", "attacker", "target"))
    _bind(lib, "om_combat_can_shoot", [W, ctypes.c_uint32, ctypes.c_uint32], ctypes.c_int, ("w", "p0", "p1"))
    _bind(lib, "om_command_attack_target_kiting", [W, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_double, ctypes.c_double], None, ("w", "p0", "p1", "p2", "p3"))
    _bind(lib, "om_command_direct_move", [W, ctypes.c_uint32, ctypes.c_double, ctypes.c_double], None, ("w", "p0", "p1", "p2"))
    _bind(lib, "om_command_group_move", [W, P(ctypes.c_uint32), ctypes.c_uint32, ctypes.c_double, ctypes.c_double], ctypes.c_uint32, ("w", "p0", "n", "p2", "p3"))
    _bind(lib, "om_command_guard", [W, P(ctypes.c_uint32), ctypes.c_uint32], ctypes.c_int, ("w", "unit_ids", "n_units"))
    _bind(lib, "om_command_issue_named", [W, ctypes.c_char_p, ctypes.c_uint32, ctypes.c_double, ctypes.c_double], ctypes.c_int, ("w", "p0", "p1", "p2", "p3"))
    _bind(lib, "om_command_queue_attack_move", [W, ctypes.c_uint32, ctypes.c_double, ctypes.c_double], None, ("w", "p0", "p1", "p2"))
    _bind(lib, "om_command_queue_move", [W, ctypes.c_uint32, ctypes.c_double, ctypes.c_double], None, ("w", "p0", "p1", "p2"))
    _bind(lib, "om_group_is_active", [W, ctypes.c_uint32], ctypes.c_int, ("w", "p0"))
    _bind(lib, "om_map_block_rect", [W, ctypes.c_double, ctypes.c_double, ctypes.c_double, ctypes.c_double, ctypes.c_uint32, ctypes.c_uint32], ctypes.c_int, ("w", "x0", "y0", "x1", "y1", "layer_lo", "layer_hi"))
    _bind(lib, "om_map_set_canvas", [W, ctypes.c_double, ctypes.c_double], ctypes.c_int, ("w", "width", "height"))
    _bind(lib, "om_map_set_obstacle_density", [W, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_double], None, ("w", "p0", "p1", "p2", "p3"))
    _bind(lib, "om_navmesh_find_path", [W, ctypes.c_double, ctypes.c_double, ctypes.c_double, ctypes.c_double, ctypes.c_uint32], ctypes.c_uint32, ("w", "p0", "p1", "p2", "p3", "p4"))
    _bind(lib, "om_navmesh_get_cache_hits", [W], ctypes.c_uint32, ("w",))
    _bind(lib, "om_navmesh_get_cell_size", [W], ctypes.c_double, ("w",))
    _bind(lib, "om_navmesh_is_cell_blocked", [W, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32], ctypes.c_int, ("w", "p0", "p1", "p2"))
    _bind(lib, "om_navmesh_is_path_straightened", [W], ctypes.c_int, ("w",))
    _bind(lib, "om_renderer_interpolate_facing", [W, ctypes.c_uint32, ctypes.c_double], ctypes.c_double, ("w", "p0", "p1"))
    _bind(lib, "om_renderer_interpolate_position", [W, ctypes.c_uint32, ctypes.c_double, P(ctypes.c_double), P(ctypes.c_double)], ctypes.c_int, ("w", "p0", "p1", "p2", "p3"))
    _wrap_out_pair(lib, "om_renderer_interpolate_position")
    _bind(lib, "om_replay_get_command_count_at_tick", [W, ctypes.c_uint64], ctypes.c_uint32, ("w", "p0"))
    _bind(lib, "om_steering_get_obstacle_repulsion", [W, ctypes.c_uint32, P(ctypes.c_double), P(ctypes.c_double)], ctypes.c_int, ("w", "p0", "p1", "p2"))
    _wrap_out_pair(lib, "om_steering_get_obstacle_repulsion")
    _bind(lib, "om_steering_get_sweep_angle_at", [W, ctypes.c_uint32], ctypes.c_double, ("w", "p0"))
    _bind(lib, "om_steering_get_sweep_angle_count", [W], ctypes.c_uint32, ("w",))
    _bind(lib, "om_tactical_base_tick", [W], ctypes.c_uint64, ("w",))
    _bind(lib, "om_tactical_tick_period", [W], ctypes.c_uint32, ("w",))
    _bind(lib, "om_unit_clear_orders", [W, ctypes.c_uint32], None, ("w", "p0"))
    _bind(lib, "om_unit_compute_terrain_speed", [W, ctypes.c_uint32, ctypes.c_double], ctypes.c_double, ("w", "p0", "p1"))
    _bind(lib, "om_unit_engage", [W, ctypes.c_uint32, ctypes.c_uint32], None, ("w", "p0", "p1"))
    _bind(lib, "om_unit_get_current_speed", [W, ctypes.c_uint32], ctypes.c_double, ("w", "p0"))
    _bind(lib, "om_unit_get_destination", [W, ctypes.c_uint32, P(ctypes.c_double), P(ctypes.c_double)], ctypes.c_int, ("w", "p0", "p1", "p2"))
    _wrap_out_pair(lib, "om_unit_get_destination")
    _bind(lib, "om_unit_get_facing", [W, ctypes.c_uint32], ctypes.c_double, ("w", "p0"))
    _bind(lib, "om_unit_get_order_kind", [W, ctypes.c_uint32], ctypes.c_int, ("w", "p0"))
    _bind(lib, "om_unit_has_active_buff", [W, ctypes.c_uint32, ctypes.c_char_p], ctypes.c_int, ("w", "p0", "p1"))
    _bind(lib, "om_unit_is_braced", [W, ctypes.c_uint32], ctypes.c_int, ("w", "p0"))
    _bind(lib, "om_unit_set_facing", [W, ctypes.c_uint32, ctypes.c_double], None, ("w", "p0", "p1"))
    _bind(lib, "om_unit_set_pos", [W, ctypes.c_uint32, ctypes.c_double, ctypes.c_double], None, ("w", "p0", "p1", "p2"))
    _bind(lib, "om_unit_set_visible_to_faction", [W, ctypes.c_uint32, ctypes.c_int32, ctypes.c_int], None, ("w", "p0", "p1", "p2"))
    lib._e13_bound = True


def _bind_e14(lib):
    if getattr(lib, "_e14_bound", False):
        return
    P = ctypes.POINTER
    V = ctypes.c_void_p
    W = OMWorldP
    _bind(lib, "om_macro_bind_hook_flag", [W, ctypes.c_uint32, ctypes.c_char_p], None, ("w", "p1", "p2"))
    _bind(lib, "om_macro_bus_get_active_flags_count", [W], ctypes.c_uint32, ("w",))
    _bind(lib, "om_macro_bus_get_flag", [W, ctypes.c_char_p], ctypes.c_int, ("w", "p1"))
    _bind(lib, "om_macro_bus_register_vocab", [ctypes.c_char_p], None, ("p0",))
    _bind(lib, "om_macro_bus_set_flag", [W, ctypes.c_char_p, ctypes.c_int], None, ("w", "p1", "p2"))
    _bind(lib, "om_macro_enemy_leaves_trigger", [W, ctypes.c_uint32], None, ("w", "p1"))
    _bind(lib, "om_macro_eval_hook_flag", [W, ctypes.c_uint32, ctypes.c_char_p], ctypes.c_int, ("w", "p1", "p2"))
    _bind(lib, "om_macro_eval_timer_transition", [ctypes.c_uint64, ctypes.c_uint64, ctypes.c_double], ctypes.c_int, ("p0", "p1", "p2"))
    _bind(lib, "om_macro_eval_transitions", [W, ctypes.c_uint32], ctypes.c_int, ("w", "p1"))
    _bind(lib, "om_macro_evaluation_interval_ticks", [], ctypes.c_uint32, ())
    _bind(lib, "om_macro_execute_behavior", [W, ctypes.c_uint32, ctypes.c_int, ctypes.c_int], ctypes.c_int, ("w", "p1", "p2", "p3"))
    _bind(lib, "om_macro_get_behavior", [W, ctypes.c_uint32], ctypes.c_int, ("w", "p1"))
    _bind(lib, "om_macro_get_eval_interval", [ctypes.c_int], ctypes.c_uint32, ("p0",))
    _bind(lib, "om_macro_get_last_issued_command_type", [W, ctypes.c_uint32], ctypes.c_int, ("w", "p1"))
    _bind(lib, "om_macro_get_modifier", [W, ctypes.c_uint32], ctypes.c_int, ("w", "p1"))
    _bind(lib, "om_macro_get_phased_subgroups", [W, ctypes.c_uint32], ctypes.c_uint32, ("w", "p1"))
    _bind(lib, "om_macro_get_speed_multiplier", [ctypes.c_int], ctypes.c_double, ("p0",))
    _bind(lib, "om_macro_get_threshold_noise", [W, ctypes.c_uint32], ctypes.c_double, ("w", "p1"))
    _bind(lib, "om_macro_get_timer_noise", [W, ctypes.c_uint32], ctypes.c_double, ("w", "p1"))
    _bind(lib, "om_macro_has_evaluated", [W], ctypes.c_int, ("w",))
    _bind(lib, "om_macro_init_force", [W, ctypes.c_uint32, ctypes.c_int32], None, ("w", "p1", "p2"))
    _bind(lib, "om_macro_is_hidden", [W, ctypes.c_uint32], ctypes.c_int, ("w", "p1"))
    _bind(lib, "om_macro_issues_illegal_command", [W], ctypes.c_int, ("w",))
    _bind(lib, "om_macro_mutates_unit_stats", [W], ctypes.c_int, ("w",))
    _bind(lib, "om_macro_player_enter_objective", [W, ctypes.c_uint32], None, ("w", "p1"))
    _bind(lib, "om_macro_reads_player_visibility_set", [W], ctypes.c_int, ("w",))
    _bind(lib, "om_macro_resolve_conflict", [ctypes.c_int, ctypes.c_int], ctypes.c_int, ("p0", "p1"))
    _bind(lib, "om_macro_resolve_conflict_types", [ctypes.c_int, ctypes.c_int], ctypes.c_int, ("p0", "p1"))
    _bind(lib, "om_macro_set_base_transition_true", [W, ctypes.c_uint32, ctypes.c_int], None, ("w", "p1", "p2"))
    _bind(lib, "om_macro_set_force_hp_pct", [W, ctypes.c_uint32, ctypes.c_double], None, ("w", "p1", "p2"))
    _bind(lib, "om_macro_set_hook_true", [W, ctypes.c_uint32, ctypes.c_int], None, ("w", "p1", "p2"))
    _bind(lib, "om_macro_set_state", [W, ctypes.c_uint32, ctypes.c_int, ctypes.c_int], None, ("w", "p1", "p2", "p3"))
    _bind(lib, "om_macro_tick", [W, ctypes.c_uint64], None, ("w", "p1"))
    _bind(lib, "om_macro_trigger_ambush", [W, ctypes.c_uint32], None, ("w", "p1"))
    _bind(lib, "om_macro_update_bus_runner", [W], None, ("w",))
    _bind(lib, "om_macro_validate_bus_flag", [ctypes.c_char_p], ctypes.c_int, ("p0",))
    _bind(lib, "om_macro_validate_condition_name", [ctypes.c_char_p], ctypes.c_int, ("p0",))
    _bind(lib, "om_macro_validate_state", [ctypes.c_int, ctypes.c_int], ctypes.c_int, ("p0", "p1"))
    _bind(lib, "om_map_is_edge_coord", [W, ctypes.c_double, ctypes.c_double], ctypes.c_int, ("w", "p1", "p2"))
    _bind(lib, "om_mission_check_external_reinforcements", [W], None, ("w",))
    _bind(lib, "om_mission_get_enemy_faction", [W], ctypes.c_int32, ("w",))
    _bind(lib, "om_mission_get_external_reinforcement_prob", [], ctypes.c_double, ())
    _bind(lib, "om_mission_get_reinforcement_foreshadow_text", [W, ctypes.c_char_p, ctypes.c_uint32], ctypes.c_uint32, ("w", "p1", "p2"))
    _bind(lib, "om_mission_get_reinforcement_spawn_pos", [W, P(ctypes.c_double), P(ctypes.c_double)], None, ("w", "p1", "p2"))
    _bind(lib, "om_mission_init_seed", [W, ctypes.c_uint64], None, ("w", "p1"))
    _bind(lib, "om_mission_is_reinforcement_spawned", [W], ctypes.c_int, ("w",))
    _bind(lib, "om_mission_schedule_external_reinforcement", [W, V], None, ("w", "p1"))
    _bind(lib, "om_mission_set_external_reinforcement", [W, V], None, ("w", "p1"))
    _bind(lib, "om_replay_command_count", [W], ctypes.c_uint32, ("w",))
    _bind(lib, "om_replay_get_commands", [W, V, ctypes.c_uint32], ctypes.c_uint32, ("w", "p1", "p2"))
    _bind(lib, "om_replay_log_command", [W, ctypes.c_uint64, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_double, ctypes.c_double, ctypes.c_uint32], None, ("w", "p1", "p2", "p3", "p4", "p5", "p6"))
    _bind(lib, "om_session_capture_enable", [W, ctypes.c_int], None, ("w", "p1"))
    _bind(lib, "om_session_capture_get_size", [W], ctypes.c_uint32, ("w",))
    _bind(lib, "om_session_capture_is_enabled", [W], ctypes.c_int, ("w",))
    _bind(lib, "om_session_capture_read", [W, ctypes.c_char_p, ctypes.c_uint32], ctypes.c_uint32, ("w", "p1", "p2"))
    _bind(lib, "om_tactical_tick_to", [W, ctypes.c_uint64], ctypes.c_uint64, ("w", "tick"))
    _bind(lib, "om_unit_get_base_hp", [ctypes.c_uint32, ctypes.c_int], ctypes.c_double, ("p0", "p1"))
    _bind(lib, "om_unit_get_decision_loop_ptr", [ctypes.c_uint32, ctypes.c_int], V, ("p0", "p1"))
    lib._e14_bound = True


def _bind_e15(lib):
    if getattr(lib, "_e15_bound", False):
        return
    P = ctypes.POINTER
    V = ctypes.c_void_p
    W = OMWorldP
    _bind(lib, "om_drift_interpolate", [V, ctypes.c_uint32, ctypes.c_uint64, ctypes.c_int, ctypes.c_uint64, V], None, ("p0", "waypoint", "period", "p3", "tick", "byref"))
    _bind(lib, "om_enemy_production_adapt_target", [V, V, V], None, ("target", "player", "out"))
    _bind(lib, "om_enemy_production_select_category", [V, V], ctypes.c_int, ("target", "current"))
    _bind(lib, "om_hazard_get_launch_types", [P(ctypes.c_uint32), ctypes.c_uint32], None, ("p0", "max"))
    _bind(lib, "om_hazard_is_enabled_at_launch", [ctypes.c_int], ctypes.c_int, ("p0",))
    _bind(lib, "om_hazard_launch_type_count", [], ctypes.c_uint32, ())
    _bind(lib, "om_hazard_sample_interference", [W, ctypes.c_double, ctypes.c_double], ctypes.c_double, ("w", "p1", "c_double"))
    _bind(lib, "om_hazard_spawn_moving_interference", [W, ctypes.c_double, ctypes.c_double, ctypes.c_double, ctypes.c_double, ctypes.c_uint64], ctypes.c_uint32, ("w", "p1", "p2", "p3", "c_double", "p5"))
    _bind(lib, "om_macro_set_force_fallback_point", [W, ctypes.c_uint32, ctypes.c_double, ctypes.c_double], None, ("w", "force", "x", "y"))
    _bind(lib, "om_mission_check_extraction_objectives", [W], None, ("w",))
    _bind(lib, "om_mission_compute_reinforcement_capacity", [ctypes.c_double, ctypes.c_double], ctypes.c_double, ("F", "share"))
    _bind(lib, "om_mission_compute_starting_force", [ctypes.c_double, ctypes.c_double], ctypes.c_double, ("F", "share"))
    _bind(lib, "om_mission_get_reinforcement_trickle", [W], ctypes.c_uint32, ("w",))
    _bind(lib, "om_mission_set_player_held_structures_count", [W, ctypes.c_int32, ctypes.c_uint32], None, ("w", "faction_id", "held"))
    _bind(lib, "om_mission_setup_extraction_point", [W, ctypes.c_double, ctypes.c_double, ctypes.c_double], None, ("w", "x", "y", "radius"))
    _bind(lib, "om_objective_get_center", [W, ctypes.c_uint32, V], ctypes.c_int, ("w", "objective_idx", "out"))
    _bind(lib, "om_objective_setup_drifting", [W, ctypes.c_uint32, ctypes.c_uint64], None, ("w", "objective", "period"))
    _bind(lib, "om_render_get_owner_color", [ctypes.c_int32], ctypes.c_uint32, ("owner",))
    _bind(lib, "om_render_get_structure_silhouette_id", [], ctypes.c_uint32, ())
    _bind(lib, "om_render_get_unit_silhouette_id", [ctypes.c_uint32], ctypes.c_uint32, ("unit",))
    _bind(lib, "om_render_is_volume_obscuring", [ctypes.c_int], ctypes.c_int, ("p0",))
    _bind(lib, "om_structure_apply_damage", [W, ctypes.c_uint32, ctypes.c_double, ctypes.c_uint32], None, ("w", "structure", "c_double", "attacker"))
    _bind(lib, "om_structure_assign_owners", [ctypes.c_int, ctypes.c_uint32, P(ctypes.c_uint32), P(ctypes.c_uint32), P(ctypes.c_uint32)], None, ("mission", "total", "p2", "p3", "byref"))
    _bind(lib, "om_structure_compute_count", [ctypes.c_double, ctypes.c_int], ctypes.c_uint32, ("ctypes", "p1"))
    _bind(lib, "om_structure_get_base_max_hp", [], ctypes.c_double, ())
    _bind(lib, "om_structure_get_capture_progress", [W, ctypes.c_uint32], ctypes.c_double, ("w", "structure"))
    _bind(lib, "om_structure_get_hp", [W, ctypes.c_uint32], ctypes.c_double, ("w", "structure"))
    _bind(lib, "om_structure_get_hud_data", [W, ctypes.c_uint32, V], None, ("w", "structure", "byref"))
    _bind(lib, "om_structure_get_last_spawn_distance", [W, ctypes.c_uint32], ctypes.c_double, ("w", "structure"))
    _bind(lib, "om_structure_get_matchup_multiplier", [ctypes.c_uint32], ctypes.c_double, ("attacker",))
    _bind(lib, "om_structure_get_owner", [W, ctypes.c_uint32], ctypes.c_int32, ("w", "structure"))
    _bind(lib, "om_structure_get_position", [W, ctypes.c_uint32, V], None, ("w", "structure", "byref"))
    _bind(lib, "om_structure_get_timer", [W, ctypes.c_uint32], ctypes.c_uint64, ("w", "structure"))
    _bind(lib, "om_structure_get_unit_type", [W, ctypes.c_uint32], ctypes.c_uint32, ("w", "structure"))
    _bind(lib, "om_structure_init", [W, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_double], None, ("w", "structure", "unit", "c_double"))
    _bind(lib, "om_structure_init_drifting", [W, ctypes.c_uint32, ctypes.c_uint64], None, ("w", "structure", "period"))
    _bind(lib, "om_structure_is_destroyed", [W, ctypes.c_uint32], ctypes.c_int, ("w", "structure"))
    _bind(lib, "om_structure_is_in_capture_radius", [W, ctypes.c_uint32, ctypes.c_double, ctypes.c_double], ctypes.c_int, ("w", "structure", "p2", "x"))
    _bind(lib, "om_structure_on_owner_changed", [W, ctypes.c_uint32, ctypes.c_int32, ctypes.c_int32], None, ("w", "structure", "old", "new"))
    _bind(lib, "om_structure_pop_spawned_unit", [W, ctypes.c_uint32], ctypes.c_int, ("w", "structure"))
    _bind(lib, "om_structure_production_interval_ticks", [ctypes.c_double], ctypes.c_uint32, ("c_double",))
    _bind(lib, "om_structure_set_capture_progress", [W, ctypes.c_uint32, ctypes.c_double], None, ("w", "structure", "c_double"))
    _bind(lib, "om_structure_set_capturing_faction", [W, ctypes.c_uint32, ctypes.c_int32], None, ("w", "structure", "unopposed"))
    _bind(lib, "om_structure_set_contested", [W, ctypes.c_uint32, ctypes.c_int], None, ("w", "structure", "on"))
    _bind(lib, "om_structure_set_owner", [W, ctypes.c_uint32, ctypes.c_int32], None, ("w", "structure", "owner"))
    _bind(lib, "om_structure_set_position", [W, ctypes.c_uint32, ctypes.c_double, ctypes.c_double], ctypes.c_int, ("w", "slot", "x", "y"))
    _bind(lib, "om_structure_set_timer", [W, ctypes.c_uint32, ctypes.c_uint64], None, ("w", "structure", "timer"))
    _bind(lib, "om_structure_switch_unit_type", [W, ctypes.c_uint32, ctypes.c_uint32], None, ("w", "structure", "new"))
    _bind(lib, "om_structure_tick_capture", [W, ctypes.c_uint32], None, ("w", "structure"))
    _bind(lib, "om_structure_tick_production", [W, ctypes.c_uint32], None, ("w", "structure"))
    _bind(lib, "om_structure_unit_cost", [ctypes.c_uint32], ctypes.c_uint32, ("unit",))
    _bind(lib, "om_ticker_pop_message", [W, ctypes.c_char_p, ctypes.c_uint32], None, ("w", "create_string_buffer", "buffer"))
    _bind(lib, "om_unit_can_return_fire", [W, ctypes.c_uint32], ctypes.c_int, ("w", "unit"))
    _bind(lib, "om_unit_get_order_destination", [W, ctypes.c_uint32, V], None, ("w", "unit", "byref"))
    _bind(lib, "om_unit_has_non_combat_visual_tag", [ctypes.c_int], ctypes.c_int, ("p0",))
    _bind(lib, "om_unit_is_flinching", [W, ctypes.c_uint32], ctypes.c_int, ("w", "unit"))
    _bind(lib, "om_unit_is_non_combat_supported", [ctypes.c_int], ctypes.c_int, ("p0",))
    _bind(lib, "om_unit_order_move", [W, ctypes.c_uint32, ctypes.c_double, ctypes.c_double], None, ("w", "unit", "p2", "c_double"))
    _bind(lib, "om_unit_spawn_combat", [W, ctypes.c_int32, ctypes.c_double, ctypes.c_double], ctypes.c_uint32, ("w", "p1", "p2", "x"))
    _bind(lib, "om_unit_spawn_non_combat", [W, ctypes.c_int, ctypes.c_double, ctypes.c_double], ctypes.c_uint32, ("w", "p1", "p2", "c_double"))
    _bind(lib, "om_unit_tick_decision_loop", [W, ctypes.c_uint32], None, ("w", "unit"))
    lib._e15_bound = True


def _bind_e17(lib):
    if getattr(lib, "_e17_bound", False):
        return
    P = ctypes.POINTER
    V = ctypes.c_void_p
    W = OMWorldP
    _bind(lib, "om_density_at", [W, ctypes.c_double, ctypes.c_double], ctypes.c_double, ("w", "x", "y"))
    _bind(lib, "om_doctrine_get", [W], ctypes.c_int, ("w",))
    _bind(lib, "om_economy_place", [W, ctypes.c_int32, ctypes.c_double, ctypes.c_double], ctypes.c_int, ("w", "building", "x", "y"))
    _bind(lib, "om_fairness_evaluate", [W, V], None, ("w", "byref"))
    _bind(lib, "om_fairness_force_score", [W, ctypes.c_double], None, ("w", "composite"))
    _bind(lib, "om_fairness_is_score_logged", [W], ctypes.c_int, ("w",))
    _bind(lib, "om_fairness_run_post_generation_check", [W], None, ("w",))
    _bind(lib, "om_gradient_add_moving_source", [W, ctypes.c_int, ctypes.c_double, ctypes.c_double, ctypes.c_double, ctypes.c_double, ctypes.c_uint32], None, ("w", "p1", "p2", "p3", "p4", "start", "period"))
    _bind(lib, "om_gradient_combine_overlap", [ctypes.c_double, ctypes.c_double], ctypes.c_double, ("p0", "p1"))
    _bind(lib, "om_gradient_get_anchor_intensity", [ctypes.c_int, ctypes.c_int], ctypes.c_double, ("node", "gradient"))
    _bind(lib, "om_gradient_get_anchor_radius", [ctypes.c_int, ctypes.c_int], ctypes.c_double, ("p0", "p1"))
    _bind(lib, "om_gradient_sample_single", [ctypes.c_double, ctypes.c_double, ctypes.c_double, ctypes.c_int], ctypes.c_double, ("p0", "p1", "p2", "p3"))
    _bind(lib, "om_lot_count", [W], ctypes.c_uint32, ("w",))
    _bind(lib, "om_lot_get_at", [W, ctypes.c_uint32, V], ctypes.c_int, ("w", "i", "out"))
    _bind(lib, "om_map_add_layer_restriction_zone", [W, ctypes.c_double, ctypes.c_double, ctypes.c_uint32], None, ("w", "p1", "zone", "p3"))
    _bind(lib, "om_map_archetype_canvas_category", [ctypes.c_uint32], ctypes.c_int, ("mission",))
    _bind(lib, "om_map_check_boundary_gradient_discontinuity", [W, ctypes.c_double, ctypes.c_double], ctypes.c_double, ("w", "p1", "boundary"))
    _bind(lib, "om_map_clamp_flavoring_delta", [ctypes.c_double], ctypes.c_double, ("delta",))
    _bind(lib, "om_map_clear", [W], None, ("w",))
    _bind(lib, "om_map_compute_chokepoint_width", [ctypes.c_double], ctypes.c_double, ("width",))
    _bind(lib, "om_map_compute_economy_obstacle_delta", [ctypes.c_double], ctypes.c_double, ("economy",))
    _bind(lib, "om_map_compute_modified_canvas", [ctypes.c_uint32, ctypes.c_double, ctypes.c_double], ctypes.c_double, ("archetype", "p1", "p2"))
    _bind(lib, "om_map_compute_tension_cover_delta", [ctypes.c_double], ctypes.c_double, ("tension",))
    _bind(lib, "om_map_count_distinct_routes_staging_to_objective", [W, ctypes.c_uint32], ctypes.c_uint32, ("w", "p1"))
    _bind(lib, "om_map_count_nodes_of_type", [W, ctypes.c_int], ctypes.c_uint32, ("w", "p1"))
    _bind(lib, "om_map_cover_at", [W, ctypes.c_uint32, P(ctypes.c_double), P(ctypes.c_double), P(ctypes.c_double), P(ctypes.c_double)], ctypes.c_int, ("w", "index", "x", "y", "radius", "height"))
    _bind(lib, "om_map_cover_count", [W], ctypes.c_uint32, ("w",))
    _bind(lib, "om_map_flavoring_stability_multiplier", [ctypes.c_double], ctypes.c_double, ("stability",))
    _bind(lib, "om_map_generate", [W, ctypes.c_uint32, ctypes.c_uint64], None, ("w", "p1", "p2"))
    _bind(lib, "om_map_generate_gradients", [W, ctypes.c_uint32, ctypes.c_uint64], None, ("w", "p1", "p2"))
    _bind(lib, "om_map_generate_spine", [W, ctypes.c_uint32, ctypes.c_uint64], None, ("w", "p1", "p2"))
    _bind(lib, "om_map_get_active_seed", [W], ctypes.c_uint64, ("w",))
    _bind(lib, "om_map_get_canvas_base_dimension", [ctypes.c_int], ctypes.c_double, ("p0",))
    _bind(lib, "om_map_get_compatible_layout_count", [W, ctypes.c_uint32], ctypes.c_uint32, ("w", "archetype"))
    _bind(lib, "om_map_get_compatible_layouts", [W, ctypes.c_uint32, P(ctypes.c_uint32), ctypes.c_uint32], ctypes.c_uint32, ("w", "archetype", "out", "max"))
    _bind(lib, "om_map_get_node_count", [W], ctypes.c_uint32, ("w",))
    _bind(lib, "om_map_get_node_pos", [W, ctypes.c_uint32, V], None, ("w", "node", "byref"))
    _bind(lib, "om_map_get_node_type", [W, ctypes.c_uint32], ctypes.c_int, ("w", "node"))
    _bind(lib, "om_map_get_nth_node_of_type", [W, ctypes.c_int, ctypes.c_uint32], ctypes.c_uint32, ("w", "p1", "nth"))
    _bind(lib, "om_map_get_simulation_coupling", [W], ctypes.c_int, ("w",))
    _bind(lib, "om_map_has_flank_bypass", [W, ctypes.c_uint32], ctypes.c_int, ("w", "chokepoint"))
    _bind(lib, "om_map_instantiate_zone_pos", [ctypes.c_double, ctypes.c_double, ctypes.c_double, ctypes.c_uint64, V], None, ("p0", "base_pct", "canvas_dim", "seed", "out"))
    _bind(lib, "om_map_is_reachable_from_all_spawns", [W, ctypes.c_uint32], ctypes.c_int, ("w", "node"))
    _bind(lib, "om_map_is_reachable_from_staging", [W, ctypes.c_uint32], ctypes.c_int, ("w", "node"))
    _bind(lib, "om_map_is_valid", [W], ctypes.c_int, ("w",))
    _bind(lib, "om_map_layout_check_hazard_approaches", [ctypes.c_uint32], ctypes.c_int, ("layout_id",))
    _bind(lib, "om_map_layout_check_vantage_reachability", [ctypes.c_uint32], ctypes.c_int, ("layout_id",))
    _bind(lib, "om_map_layout_file_has_forbidden_fields", [ctypes.c_uint32], ctypes.c_int, ("p0",))
    _bind(lib, "om_map_layout_file_has_required_fields", [ctypes.c_uint32], ctypes.c_int, ("p0",))
    _bind(lib, "om_map_layout_matches_archetype_filter", [ctypes.c_uint32, ctypes.c_uint32], ctypes.c_int, ("layout", "archetype"))
    _bind(lib, "om_map_library_total_layouts", [], ctypes.c_uint32, ())
    _bind(lib, "om_map_node_get_owner", [W, ctypes.c_uint32], ctypes.c_int32, ("w", "vantage"))
    _bind(lib, "om_map_sample_gradients", [W, ctypes.c_double, ctypes.c_double, V], None, ("w", "p1", "x", "byref"))
    _bind(lib, "om_map_sample_layer_accessibility", [W, ctypes.c_double, ctypes.c_double, ctypes.c_uint32], ctypes.c_int, ("w", "p1", "x", "layer"))
    _bind(lib, "om_map_sample_obstacle_density", [W, ctypes.c_double, ctypes.c_double], ctypes.c_double, ("w", "p1", "x"))
    _bind(lib, "om_map_select_layout_uniform", [ctypes.c_uint64, ctypes.c_uint32], ctypes.c_uint32, ("seed", "pool_size"))
    _bind(lib, "om_map_set_simulation_coupling", [W, ctypes.c_int], None, ("w", "on"))
    _bind(lib, "om_map_setup_drifting_node", [W, ctypes.c_uint32, ctypes.c_uint32], None, ("w", "node", "period"))
    _bind(lib, "om_map_verify_flank_connections", [W], ctypes.c_int, ("w",))
    _bind(lib, "om_proc_arch_resolve_section_piece", [ctypes.c_int, ctypes.c_int], ctypes.c_uint32, ("section_type", "era"))
    _bind(lib, "om_proc_arch_section_is_era_agnostic", [ctypes.c_int], ctypes.c_int, ("section_type",))
    _bind(lib, "om_render_detect_repeated_tile_boundary", [W], ctypes.c_int, ("w",))
    _bind(lib, "om_route_grid_is_cell_blocked", [ctypes.c_double], ctypes.c_int, ("obstacle",))
    _bind(lib, "om_space_field_clear", [W], None, ("w",))
    _bind(lib, "om_space_field_generate_nodes", [W, ctypes.c_uint32, ctypes.c_double, ctypes.c_double, ctypes.c_double, P(ctypes.c_double), P(ctypes.c_uint32), ctypes.c_uint32], ctypes.c_int, ("w", "seed", "canvas_w", "canvas_h", "density", "node_xy", "node_slots", "n_nodes"))
    _bind(lib, "om_space_field_poly_count", [W], ctypes.c_uint32, ("w",))
    _bind(lib, "om_space_field_poly_get", [W, ctypes.c_uint32, P(ctypes.c_uint32), P(ctypes.c_uint32), P(ctypes.c_double), ctypes.c_uint32], ctypes.c_uint32, ("w", "i", "layer", "kind", "xy", "cap_pts"))
    _bind(lib, "om_space_field_present", [W], ctypes.c_int, ("w",))
    _bind(lib, "om_space_hash32", [ctypes.c_int32, ctypes.c_int32, ctypes.c_int32, ctypes.c_uint32], ctypes.c_uint32, ("ix", "iy", "iz", "seed"))
    _bind(lib, "om_space_noise_layer", [ctypes.c_uint32, ctypes.c_double, ctypes.c_uint32, ctypes.c_int, P(ctypes.c_double), ctypes.c_uint32], ctypes.c_uint32, ("layer_seed", "canvas", "k", "independent", "out", "cap"))
    _bind(lib, "om_strongpoint_count", [W], ctypes.c_uint32, ("w",))
    _bind(lib, "om_strongpoint_get_at", [W, ctypes.c_uint32, V], ctypes.c_int, ("w", "i", "out"))
    _bind(lib, "om_terrain_band_at", [W, ctypes.c_double, ctypes.c_double], ctypes.c_int, ("w", "x", "y"))
    _bind(lib, "om_terrain_band_heights", [W, P(ctypes.c_double), ctypes.c_uint32], ctypes.c_uint32, ("w", "out", "cap"))
    _bind(lib, "om_terrain_cell_band", [W, ctypes.c_uint32, ctypes.c_uint32], ctypes.c_int, ("w", "cx", "cy"))
    _bind(lib, "om_terrain_cells", [W, P(ctypes.c_uint32), P(ctypes.c_uint32)], ctypes.c_uint32, ("w", "w_cells", "h_cells"))
    _bind(lib, "om_terrain_dump_bands", [W, P(ctypes.c_uint8), ctypes.c_uint32], ctypes.c_uint32, ("w", "out", "cap"))
    _bind(lib, "om_terrain_generate", [W, ctypes.c_uint64, ctypes.c_double, ctypes.c_double], ctypes.c_int, ("w", "seed", "canvas_w", "canvas_h"))
    _bind(lib, "om_terrain_ground_at", [W, ctypes.c_int, ctypes.c_double, ctypes.c_double], ctypes.c_int, ("w", "layer", "x", "y"))
    _bind(lib, "om_terrain_height_at", [W, ctypes.c_double, ctypes.c_double], ctypes.c_double, ("w", "x", "y"))
    _bind(lib, "om_terrain_present", [W], ctypes.c_int, ("w",))
    _bind(lib, "om_terrain_sight_blocks", [W, ctypes.c_int, ctypes.c_double, ctypes.c_double, ctypes.c_int, ctypes.c_double, ctypes.c_double], ctypes.c_int, ("w", "layer0", "x0", "y0", "layer1", "x1", "y1"))
    _bind(lib, "om_terrain_slope_at", [W, ctypes.c_double, ctypes.c_double, V], ctypes.c_int, ("w", "x", "y", "out"))
    _bind(lib, "om_terrain_slope_count", [W], ctypes.c_uint32, ("w",))
    _bind(lib, "om_terrain_slope_get", [W, ctypes.c_uint32, V], ctypes.c_int, ("w", "i", "out"))
    _bind(lib, "om_terrain_walk_mask", [W, ctypes.c_int, P(ctypes.c_uint8), ctypes.c_uint32], ctypes.c_uint32, ("w", "layer", "out", "cap"))
    _bind(lib, "om_terrain_walkable_at", [W, ctypes.c_double, ctypes.c_double], ctypes.c_int, ("w", "x", "y"))
    _bind(lib, "om_unit_get_position", [W, ctypes.c_uint32, V], None, ("w", "unit_id", "byref"))
    _bind(lib, "om_unit_order_hold_node", [W, ctypes.c_uint32, ctypes.c_uint32], None, ("w", "unit_id", "node_id"))
    _bind(lib, "om_wave_get_since", [W, ctypes.c_uint32, V, ctypes.c_uint32], ctypes.c_uint32, ("w", "tick", "out", "cap"))
    lib._e17_bound = True


def _bind_e19(lib):
    if getattr(lib, "_e19_bound", False):
        return
    P = ctypes.POINTER
    V = ctypes.c_void_p
    W = OMWorldP
    _bind(lib, "om_checksum_first_diff", [W, W, P(ctypes.c_uint32), P(ctypes.c_uint32)], ctypes.c_int, ("a", "b", "section", "unit_id"))
    _bind(lib, "om_checksum_section_count", [], ctypes.c_uint32, ())
    _bind(lib, "om_checksum_section_name", [ctypes.c_uint32], ctypes.c_char_p, ("section",))
    _bind(lib, "om_checksum_unit_hashes", [W, P(ctypes.c_uint64), ctypes.c_uint32], ctypes.c_uint32, ("w", "out", "cap"))
    _bind(lib, "om_cmd_log_feed", [W, P(ctypes.c_uint8), ctypes.c_uint32], ctypes.c_int, ("w", "buf", "len"))
    _bind(lib, "om_cmd_log_size", [W], ctypes.c_uint32, ("w",))
    _bind(lib, "om_cmd_log_write", [W, P(ctypes.c_uint8), ctypes.c_uint32], ctypes.c_uint32, ("w", "out", "cap"))
    _bind(lib, "om_cmd_pending_count", [W], ctypes.c_uint32, ("w",))
    _bind(lib, "om_cmd_reset", [W], None, ("w",))
    _bind(lib, "om_cmd_submit", [W, V, P(ctypes.c_uint32)], ctypes.c_int, ("w", "cmd", "unit_ids"))
    _bind(lib, "om_net_tick", [W], ctypes.c_uint64, ("w",))
    _bind(lib, "om_world_checksum_full", [W, P(ctypes.c_uint64), ctypes.c_uint32], ctypes.c_uint64, ("w", "sections", "cap"))
    lib._e19_bound = True


_GENERATED_BINDERS = (_bind_e01, _bind_e06, _bind_e07, _bind_e08, _bind_e09, _bind_e10, _bind_e11, _bind_e12, _bind_e13, _bind_e14, _bind_e15, _bind_e17, _bind_e19)
# ---- end generated ----
