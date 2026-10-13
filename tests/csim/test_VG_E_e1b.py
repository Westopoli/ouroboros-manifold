"""Visible-game lane E1, piece E1b: the settlement density field (docs/northstar/plans/2026-10-07-visible-game-spec.md rev 6,
lane E1 and section 7 liberties; pre-flight preflight_2026-10-07/6-economy.md; bible R-193-01, R-193-06, R-193-08, Q-222-01 a;
mockup scenes/mockups/settlement/settlement_sim.gd, read-only). Fenced: builders never edit this file.

Proves: the density field lives in the sim (om_density_at, csrc/economy_density.c) and, once a mission world holds terrain,
grows from the core, at least one cell per 3 s tick (60 ticks at OM_TACTICAL_TICK_RATE 20; TD-VG-E-18), decays (factor 0.99 per
ring at most, mockup BASE_DECAY), is eased toward the region economy x maturity (Q-222-01 a: economy and the mission clock only), is deterministic
and is hashed. Isolation (fresh world, no terrain) and integration (mission world, terrain, stepping) cases; every detector has a
positive control that passes on main.

RED on main: the stub om_density_at answers 0.0 everywhere, so every growth test fails on "no density anywhere". The controls
and the fresh-world cases pass on main by design.

PROVISIONAL DEFINITIONS (test drafts 2026-10-09; the spec gives none, so each is a named draft for the builder to confirm):
 - Grid: the tests sample on 120 x 120 points 200 wu apart over the 24000 wu canvas; point centre = (i+0.5)*200. Since E1q the
   field is a 100 wu cell grid (240 x 240, TD-VG-E-18), so each sample reads one cell of every other row and column. A "ring"
   is one Chebyshev step on the sample grid, 200 wu = 2 cells.
 - Setup: ground era (om_set_era_kind 1), om_terrain_generate(seed, 24000, 24000), om_mission_setup on region 0, then
   om_world_step. The core is not named by any contract, so it is found as the cell of maximum density (ties: lowest index).
 - Density tick = 60 om_world_step calls (3 s x 20 Hz). Growth may start on the first or the second tick: reach bound is
   rings <= ticks + 1.
 - Decay bound: density at Chebyshev distance r from the core <= 0.99**r (+1e-9). Holds because every mockup factor is <= 0.99
   and the eased value never exceeds min(1, P x maturity) with maturity <= 1.
 - Q16: density x 65536 is an integer (spec: "deterministic integer/Q16 math").
 - Not asserted (no contract): the steepness term (the sim's slopes are segments, not a per-cell scalar, so the mockup's
   1 - 0.25 x slope has no sim definition yet), water crossing 0.85, the climb term, numbers of cells, the Q-168-05 base cap.
"""
import ctypes

import pytest

from conftest import (
    OMArchetype, OMEdge, OMFeature, OMTier,
    set_edge, set_faction, set_owner, set_region,
)

W = ctypes.c_void_p
SIDE = 120
CELL_WU = 200.0
CANVAS = 24000.0
TICK = 60
DECAY = 0.99
EPS = 1e-9
PLAYER_FAC, ENEMY_FAC = 0, 1


def bind(lib):
    assert hasattr(lib, "om_density_at"), "om_density_at missing"
    lib.om_density_at.restype = ctypes.c_double
    lib.om_density_at.argtypes = [W, ctypes.c_double, ctypes.c_double]
    lib.om_terrain_generate.argtypes = [W, ctypes.c_uint64, ctypes.c_double, ctypes.c_double]
    lib.om_world_step.argtypes = [W]
    lib.om_world_get_state_checksum.restype = ctypes.c_uint64
    lib.om_world_get_state_checksum.argtypes = [W]


def scene(lib, world_factory, *, seed=7, economy=10.0, population=10.0, terrain_seed=None, terrain=True, archetype=3, setup=True):
    bind(lib)
    w = world_factory(n_regions=2, seed=seed)
    lib.om_world_set_feature(w, OMFeature.TACTICAL, 1)
    set_faction(lib, w, PLAYER_FAC, OMArchetype.PLAYER)
    set_faction(lib, w, ENEMY_FAC, OMArchetype.CONQUEROR)
    set_owner(lib, w, 0, PLAYER_FAC, held_since=-1)
    set_owner(lib, w, 1, ENEMY_FAC, held_since=-1)
    set_edge(lib, w, 0, 1, OMEdge.BOTH)
    set_region(lib, w, 0, tier=OMTier.HOME, military=10.0, economy=economy, population=population, faction_id=PLAYER_FAC)
    set_region(lib, w, 1, tier=OMTier.HOME, military=10.0, faction_id=ENEMY_FAC)
    assert lib.om_set_era_kind(w, 1) == 0
    if terrain:
        assert lib.om_terrain_generate(w, terrain_seed if terrain_seed is not None else seed, CANVAS, CANVAS) in (0, 1)
    if not setup:
        return w  # TD-VG-E-6: a fresh world before om_mission_setup
    lib.om_mission_setup(w, 0, archetype, 0)
    lib.om_mission_begin.argtypes, lib.om_mission_begin.restype = [W], None
    lib.om_mission_begin(w)  # TD-VG-E-5: R-092 recon stops the clock until begin
    return w


def ticks(lib, w, n_density_ticks):
    for _ in range(n_density_ticks * TICK):
        lib.om_world_step(w)


def grid(lib, w):
    return [lib.om_density_at(w, (i % SIDE + 0.5) * CELL_WU, (i // SIDE + 0.5) * CELL_WU) for i in range(SIDE * SIDE)]


def core_of(g):
    m = max(g)
    return g.index(m)


def ring(i, core):
    return max(abs(i % SIDE - core % SIDE), abs(i // SIDE - core // SIDE))


# ---- detectors (pure functions, each with a positive control below) ----

def reach(g, core):
    return max((ring(i, core) for i, v in enumerate(g) if v > 0.0), default=-1)


def decay_violations(g, core):
    return [i for i, v in enumerate(g) if v > DECAY ** ring(i, core) + EPS]


def non_q16(g):
    return [i for i, v in enumerate(g) if abs(v * 65536.0 - round(v * 65536.0)) > 1e-6]


# ---- controls: pass on main by design ----

def test_control_reach_detector():
    g = [0.0] * (SIDE * SIDE)
    c = 60 * SIDE + 60
    g[c] = 1.0
    g[c + 3] = 0.5
    assert reach(g, c) == 3
    assert reach([0.0] * (SIDE * SIDE), c) == -1


def test_control_decay_detector_flags_a_violation():
    g = [0.0] * (SIDE * SIDE)
    c = 60 * SIDE + 60
    g[c] = 1.0
    g[c + 2] = 0.99 ** 2
    assert decay_violations(g, c) == []
    g[c + 2] = 0.995
    assert decay_violations(g, c) == [c + 2]


def test_control_q16_detector_flags_a_float():
    assert non_q16([0.5, 1.0, 3 / 65536.0]) == []
    assert non_q16([0.1]) == [0]


def test_control_fresh_world_density_zero(lib, world_factory):
    bind(lib)
    w = world_factory(n_regions=1)
    assert all(v == 0.0 for v in grid(lib, w)[:: SIDE + 1])
    assert lib.om_density_at(w, -5.0, 1e9) == 0.0
    assert lib.om_density_at(None, 100.0, 100.0) == 0.0


# ---- isolation ----

def test_before_setup_density_reads_stay_safe(lib, world_factory):
    """TD-VG-E-6: a ground mission always generates terrain in om_mission_setup, so the no-terrain read is a fresh world
    (before setup): om_density_at is 0.0 everywhere and never faults, outside the canvas included."""
    w = scene(lib, world_factory, terrain=False, setup=False)
    for _ in range(3 * TICK):
        lib.om_world_step(w)
    for x, y in [(-1.0, -1.0), (CANVAS + 1.0, 5.0), (12000.0, 12000.0)]:
        assert lib.om_density_at(w, x, y) == 0.0


# ---- integration: mission world with terrain ----

def test_density_grows_from_a_core(lib, world_factory):
    """R-193-01: a field exists and has one peak (the core) once the mission has run a few ticks. Red on main: all 0.0."""
    w = scene(lib, world_factory)
    ticks(lib, w, 4)
    g = grid(lib, w)
    assert max(g) > 0.0, "no density anywhere after 4 density ticks (om_density_at is the K-e stub)"
    assert sum(1 for v in g if v > 0.0) >= 2, "density never left the core cell"
    assert all(0.0 <= v <= 1.0 + EPS for v in g)


def test_one_ring_per_tick(lib, world_factory):
    """R-193-01/06: the field spreads at least one cell per 3 s tick (TD-VG-E-18: was "one ring per tick, nothing beyond k+1
    rings"; the growth is in place and the cell is 100 wu, so a step can pass one 200 wu sample ring): after k ticks the reach is
    at least k cells of 100 wu, that is 2 * rings >= k, and it keeps spreading."""
    w = scene(lib, world_factory)
    prev = -1
    core = None
    for k in range(1, 9):
        ticks(lib, w, 1)
        g = grid(lib, w)
        assert max(g) > 0.0, "no density anywhere (stub)"
        if core is None:
            core = core_of(g)
        r = reach(g, core)
        assert 2 * r >= k, f"after {k} ticks the field reached {r} rings of 200 wu, fewer than {k} cells of 100 wu"
        assert r >= prev, "the field shrank"
        prev = r
    assert prev >= 4, f"after 8 ticks the field reached only {prev} rings; it should be spreading each tick"


def test_decay_bound(lib, world_factory):
    """R-193-01: density never exceeds 0.99 per ring from the core (mockup BASE_DECAY)."""
    w = scene(lib, world_factory)
    ticks(lib, w, 10)
    g = grid(lib, w)
    assert max(g) > 0.0, "no density anywhere (stub)"
    assert decay_violations(g, core_of(g)) == []


def test_q16_values(lib, world_factory):
    """Spec: deterministic integer/Q16 math. Every cell is a whole multiple of 1/65536."""
    w = scene(lib, world_factory)
    ticks(lib, w, 6)
    g = grid(lib, w)
    assert max(g) > 0.0, "no density anywhere (stub)"
    assert non_q16(g) == []


def test_deterministic_and_hashed(lib, world_factory):
    """Determinism contract: identical worlds hash identically at every tick, and growth moves the hash (density is hashed)."""
    a = scene(lib, world_factory)
    b = scene(lib, world_factory)
    h0 = lib.om_world_get_state_checksum(a)
    for _ in range(6):
        ticks(lib, a, 1)
        ticks(lib, b, 1)
        assert lib.om_world_get_state_checksum(a) == lib.om_world_get_state_checksum(b)
    assert max(grid(lib, a)) > 0.0, "no density anywhere (stub)"
    sections = (ctypes.c_uint64 * 16)()
    lib.om_world_checksum_full.restype = ctypes.c_uint64
    lib.om_world_checksum_full.argtypes = [W, ctypes.c_void_p, ctypes.c_uint32]
    full_a = lib.om_world_checksum_full(a, sections, 16)
    c = scene(lib, world_factory)
    full_c = lib.om_world_checksum_full(c, sections, 16)
    assert full_a != full_c, "six ticks of growth did not move checksum_full (density not hashed)"
    assert h0 is not None


def test_maturity_rises_with_the_clock(lib, world_factory):
    """Q-222-01 a, the mission clock: the eased value climbs toward economy x maturity, so the core density never falls and the
    field's total grows between tick 4 and tick 12."""
    w = scene(lib, world_factory)
    ticks(lib, w, 4)
    g1 = grid(lib, w)
    assert max(g1) > 0.0, "no density anywhere (stub)"
    ticks(lib, w, 8)
    g2 = grid(lib, w)
    assert g2[core_of(g1)] >= g1[core_of(g1)] - EPS
    assert sum(g2) > sum(g1)


def test_eased_toward_region_economy(lib, world_factory):
    """Q-222-01 a: the region's economy feeds the target. A rich region ends with more total density than a poor one."""
    poor = scene(lib, world_factory, economy=1.0)
    rich = scene(lib, world_factory, economy=40.0)
    ticks(lib, poor, 12)
    ticks(lib, rich, 12)
    gp, gr = grid(lib, poor), grid(lib, rich)
    assert max(gr) > 0.0, "no density anywhere (stub)"
    assert sum(gr) > sum(gp), "economy did not change the density target"


def test_population_does_not_feed_density(lib, world_factory):
    """Q-222-01 a (not b or c): economy and the mission clock only. Changing only the population leaves the field identical."""
    lo = scene(lib, world_factory, population=1.0)
    hi = scene(lib, world_factory, population=80.0)
    ticks(lib, lo, 10)
    ticks(lib, hi, 10)
    glo, ghi = grid(lib, lo), grid(lib, hi)
    assert max(glo) > 0.0, "no density anywhere (stub)"
    assert glo == ghi
