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
CSRC_DIR = REPO_ROOT / "csrc"


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
    DRIFT_GATE_IGNORED = 6


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
        if _HAS_CSRC:
            pytest.fail("COMPILE ERROR: csrc/*.c present but libouroboros.so did not build:\n"
                        + (BUILD_ERROR or "(no compiler output captured; run `make`)"))
        pytest.skip("no csrc/*.c implementation yet; nothing to build")
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
        if _HAS_CSRC:
            pytest.fail("COMPILE ERROR: csrc/*.c present but libouroboros_dbg.so did not build:\n"
                        + (BUILD_ERROR or "(no compiler output captured; run `make`)"))
        pytest.skip("no csrc/*.c implementation yet; nothing to build")
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
    lib.om_gen_set_player_preference.argtypes = [V, ctypes.c_int]; lib.om_gen_set_player_preference.restype = None
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


def gen_set_player_preference(lib, w, template):
    _bind_e03(lib)
    lib.om_gen_set_player_preference(w, template)


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
