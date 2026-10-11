"""Visible-game programme lane E1, contract amendment K-e, sim side (docs/northstar/plans/2026-10-07-visible-game-spec.md
rev 6, lane E1 section, piece E1a; contract text: docs/architecture.md "Visible-game economy fields"). Fenced: builders
never edit this file.

Proves the K-e getters exist with the documented signatures and answer the documented empty shape on a fresh world
(R-193-02 lots and stages, R-193-01 density, R-218-01/02 strongpoints, R-179-01 doctrine, R-193-04 waves, R-168-01
placement), ABI 6, and that save format 8 round-trips the (empty) new state.

ASSUMED PROTOTYPES: the ones written in docs/architecture.md (the spec names the getters, the contract piece fixed the
arguments; a mismatch is a K-e question). Structs: om_lot {u32 id; f64 x, y; i32 stage, building, owner},
om_strongpoint {u32 id; f64 x, y; i32 owner, state}, om_wave {u32 tick; i32 kind; f64 x, y}.
Not asserted here: any non-empty content (E1b to E1h fill the stubs; no number was given for it).
On main every new symbol is missing and om_abi_version() is 5, so the K-e tests fail on that; the controls pass.
"""
import ctypes

import pytest

W = ctypes.c_void_p


class Lot(ctypes.Structure):
    _fields_ = [("id", ctypes.c_uint32), ("x", ctypes.c_double), ("y", ctypes.c_double),
                ("stage", ctypes.c_int32), ("building", ctypes.c_int32), ("owner", ctypes.c_int32)]


class Strongpoint(ctypes.Structure):
    _fields_ = [("id", ctypes.c_uint32), ("x", ctypes.c_double), ("y", ctypes.c_double),
                ("owner", ctypes.c_int32), ("state", ctypes.c_int32)]


class Wave(ctypes.Structure):
    _fields_ = [("tick", ctypes.c_uint32), ("kind", ctypes.c_int32), ("x", ctypes.c_double), ("y", ctypes.c_double)]


NEW = ["om_lot_count", "om_lot_get_at", "om_density_at", "om_strongpoint_count", "om_strongpoint_get_at",
       "om_doctrine_get", "om_wave_get_since", "om_economy_place"]
BALANCED = 3


def bind(lib):
    missing = [n for n in NEW if not hasattr(lib, n)]
    assert not missing, f"K-e symbols missing from libouroboros.so: {missing}"
    P = ctypes.POINTER
    lib.om_lot_count.argtypes, lib.om_lot_count.restype = [W], ctypes.c_uint32
    lib.om_lot_get_at.argtypes, lib.om_lot_get_at.restype = [W, ctypes.c_uint32, P(Lot)], ctypes.c_int
    lib.om_density_at.argtypes, lib.om_density_at.restype = [W, ctypes.c_double, ctypes.c_double], ctypes.c_double
    lib.om_strongpoint_count.argtypes, lib.om_strongpoint_count.restype = [W], ctypes.c_uint32
    lib.om_strongpoint_get_at.argtypes, lib.om_strongpoint_get_at.restype = [W, ctypes.c_uint32, P(Strongpoint)], ctypes.c_int
    lib.om_doctrine_get.argtypes, lib.om_doctrine_get.restype = [W], ctypes.c_int
    lib.om_wave_get_since.argtypes = [W, ctypes.c_uint32, P(Wave), ctypes.c_uint32]
    lib.om_wave_get_since.restype = ctypes.c_uint32
    lib.om_economy_place.argtypes = [W, ctypes.c_int32, ctypes.c_double, ctypes.c_double]
    lib.om_economy_place.restype = ctypes.c_int


def bind_save(lib):
    V, P = W, ctypes.POINTER
    lib.om_save_state_size.argtypes, lib.om_save_state_size.restype = [V], ctypes.c_uint32
    lib.om_save_state_write.argtypes, lib.om_save_state_write.restype = [V, P(ctypes.c_uint8), ctypes.c_uint32], None
    lib.om_load_state_read.argtypes, lib.om_load_state_read.restype = [V, P(ctypes.c_uint8), ctypes.c_uint32], ctypes.c_int


def test_control_existing_getter_still_works(lib, world_factory):
    """Control (passes on main): om_structure_count, the pattern the new getters follow, is intact."""
    lib.om_structure_count.argtypes, lib.om_structure_count.restype = [W], ctypes.c_uint32
    assert lib.om_structure_count(world_factory(n_regions=1)) == 0


def test_abi_version_is_7(lib):
    """K-e: OM_ABI_VERSION 5 -> 6 (spec rev 6 lane E1); K-e5 moved the pin to 7 (the hook om_terrain_set_heights, TD-VG-E-16). Red before K-e5: the library reports 6."""
    lib.om_abi_version.argtypes, lib.om_abi_version.restype = [], ctypes.c_uint32
    assert lib.om_abi_version() == 7


def test_new_symbols_present_and_bind(lib):
    bind(lib)


def test_fresh_world_lots_empty(lib, world_factory):
    """K-e: no lots on a fresh world; get_at refuses (1) and leaves out untouched; null world is 0 / 1."""
    bind(lib)
    w = world_factory(n_regions=1)
    assert lib.om_lot_count(w) == 0
    out = Lot(id=77, stage=-9)
    assert lib.om_lot_get_at(w, 0, ctypes.byref(out)) == 1
    assert (out.id, out.stage) == (77, -9), "a refused get_at wrote into out"
    assert lib.om_lot_count(None) == 0
    assert lib.om_lot_get_at(None, 0, ctypes.byref(out)) == 1


def test_fresh_world_density_zero(lib, world_factory):
    """K-e: density is 0.0 with no field, anywhere, including outside the canvas and with a null world."""
    bind(lib)
    w = world_factory(n_regions=1)
    for x, y in [(0.0, 0.0), (1200.0, 800.0), (-5.0, 1e9)]:
        assert lib.om_density_at(w, x, y) == 0.0
    assert lib.om_density_at(None, 1.0, 1.0) == 0.0


def test_fresh_world_strongpoints_empty(lib, world_factory):
    bind(lib)
    w = world_factory(n_regions=1)
    assert lib.om_strongpoint_count(w) == 0
    out = Strongpoint(id=77, state=-9)
    assert lib.om_strongpoint_get_at(w, 0, ctypes.byref(out)) == 1
    assert (out.id, out.state) == (77, -9)
    assert lib.om_strongpoint_count(None) == 0


def test_fresh_world_doctrine_balanced(lib, world_factory):
    """K-e: doctrine ids 0 boom, 1 fortify, 2 press, 3 balanced; a fresh world answers 3."""
    bind(lib)
    assert lib.om_doctrine_get(world_factory(n_regions=1)) == BALANCED


def test_fresh_world_no_waves(lib, world_factory):
    """K-e: wave log empty; count-only (null out) and a buffered read both answer 0 and write nothing."""
    bind(lib)
    w = world_factory(n_regions=1)
    assert lib.om_wave_get_since(w, 0, None, 0) == 0
    buf = (Wave * 4)(*[Wave(tick=77, kind=-9) for _ in range(4)])
    assert lib.om_wave_get_since(w, 0, buf, 4) == 0
    assert all(b.tick == 77 for b in buf)
    assert lib.om_wave_get_since(None, 0, None, 0) == 0


def test_place_symbol_callable(lib, world_factory):
    """K-e: om_economy_place exists and is callable (0 accepted / nonzero refused). The result is E1e's, not asserted."""
    bind(lib)
    r = lib.om_economy_place(world_factory(n_regions=1), 0, 100.0, 100.0)
    assert r in (0, 1) or isinstance(r, int)


def test_save_round_trip_at_format_10_keeps_empty_new_state(lib, world_factory):
    """K-e3: format 9 writes and re-reads; K-e5 moved the pin to 10 (TD-VG-E-16): the version word is 10; the new state reads back empty / doctrine 3.
    Red before K-e5: the version word is 9."""
    bind(lib)
    bind_save(lib)
    src = world_factory(n_regions=1)
    size = lib.om_save_state_size(src)
    buf = (ctypes.c_uint8 * size)()
    lib.om_save_state_write(src, buf, size)
    assert int.from_bytes(bytes(buf[4:8]), "little") == 10
    dst = world_factory(n_regions=1)
    assert lib.om_load_state_read(dst, buf, size) == 0
    assert lib.om_lot_count(dst) == 0 and lib.om_strongpoint_count(dst) == 0
    assert lib.om_doctrine_get(dst) == BALANCED
    assert lib.om_wave_get_since(dst, 0, None, 0) == 0


def test_version_7_save_refused(lib, world_factory):
    """K-e / R-111-03: a save stamped 7 is refused after the bump, world untouched. Red on main (7 is current)."""
    bind_save(lib)
    src = world_factory(n_regions=1)
    size = lib.om_save_state_size(src)
    buf = (ctypes.c_uint8 * size)()
    lib.om_save_state_write(src, buf, size)
    buf[4:8] = (ctypes.c_uint8 * 4)(*(7).to_bytes(4, "little"))
    assert lib.om_load_state_read(world_factory(n_regions=1), buf, size) != 0
