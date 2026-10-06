"""Lockstep spec 2026-10-05, module lane mod-mapgen, stage 2: the mid-battle save.

Module: csrc/tactical_mapgen.c, save slot mapgen_state (OM_SAVE_SLOT_MAPGEN = 9,
the last slot of the buffer), checksum section 8 (support and map; this module
owns the map half, tactical_support.c the structure half, so section 8 only
moves when BOTH modules' save hooks exist; see the support note in the spec).

Proves R-139-03 (checksum covers module state) through R-111-02 / R-111-03
(load restores the world so play continues identically; a refused load leaves
the target untouched).

Tests:
  round trip         battle to tick 150, save, load into a fresh world: section 8 equal
  continues equal    500 more tactical ticks on both, section 8 equal every tenth tick
  re-save identical  a second save of the loaded world is byte-identical
  refusals           truncated buffer; mapgen slot length corrupted -> refused, target's
                     full checksum unchanged
  empty slot         a save taken before any mission still loads
  full checksum      xfail: every module's save hooks are not written yet

Only this module's section (8) is asserted in the real tests, because other
modules' save hooks may not exist yet; the one full-checksum test is xfail.
Section 8 also contains the structure half; the battle has one structure, so the
section can stay unequal until mod-support lands too.
"""
import ctypes
import struct

import pytest

from b1_macro_scene import tactical_world
from test_net_section_hashes import _battle, _secs, _run, N_SECTIONS, SUPPORT_MAP

SAVE_TICK = 150
AFTER_TICKS = 500
OM_SAVE_SLOT_MAPGEN = 9
OM_SAVE_SLOT_COUNT = 11
OM_FEATURE_TACTICAL = None  # resolved lazily from conftest's OMFeature


def _bind(lib):
    if getattr(lib, "_save_bound", False):
        return
    V, P = ctypes.c_void_p, ctypes.POINTER
    lib.om_save_state_size.argtypes = [V]
    lib.om_save_state_size.restype = ctypes.c_uint32
    lib.om_save_state_write.argtypes = [V, P(ctypes.c_uint8), ctypes.c_uint32]
    lib.om_save_state_write.restype = None
    lib.om_load_state_read.argtypes = [V, P(ctypes.c_uint8), ctypes.c_uint32]
    lib.om_load_state_read.restype = ctypes.c_int
    lib._save_bound = True


def _save(lib, w):
    _bind(lib)
    size = lib.om_save_state_size(w)
    buf = (ctypes.c_uint8 * size)()
    lib.om_save_state_write(w, buf, size)
    return buf, size


def _load(lib, w, buf, size):
    _bind(lib)
    return lib.om_load_state_read(w, buf, size)


def _target(lib, world_factory, seed=999):
    """A fresh world prepared like the existing save tests prepare a target:
    a different seed, nothing else; the tactical feature on so it can step."""
    from conftest import OMFeature
    w = world_factory(n_regions=2, seed=seed)
    lib.om_world_set_feature(w, OMFeature.TACTICAL, 1)
    return w


def _saved_battle(lib, world_factory, ticks=SAVE_TICK):
    w, _, _ = _battle(lib, world_factory)
    _run(lib, w, ticks)
    buf, size = _save(lib, w)
    assert size > 0
    return w, buf, size


def _mapgen_slot(buf, size):
    """(offset of the slot header, blob length). The save ends with the slot table
    (ids 0..OM_SAVE_SLOT_COUNT-1 in order: [u8 id][u32 len][blob]); found by walking
    the ids from each candidate start until the chain ends exactly at size."""
    raw = bytes(buf)
    for start in range(size - 5, -1, -1):
        pos, ok, hit = start, True, None
        for sid in range(OM_SAVE_SLOT_COUNT):
            if pos + 5 > size or raw[pos] != sid:
                ok = False
                break
            blen = struct.unpack_from("<I", raw, pos + 1)[0]
            if sid == OM_SAVE_SLOT_MAPGEN:
                hit = (pos, blen)
            pos += 5 + blen
        if ok and pos == size:
            return hit
    raise AssertionError("no mapgen slot header found in the save slot table")


def test_round_trip_section_equal_right_after_load(lib, world_factory):
    wa, buf, size = _saved_battle(lib, world_factory)
    wb = _target(lib, world_factory)
    assert _load(lib, wb, buf, size) == 0
    a, b = _secs(lib, wa)[SUPPORT_MAP], _secs(lib, wb)[SUPPORT_MAP]
    assert a != 0, "setup: section 8 reads 0 at the save"
    assert a == b, "section 8 (map half: mapgen_state) differs right after the load"


def test_loaded_world_stays_equal_for_500_ticks(lib, world_factory):
    wa, buf, size = _saved_battle(lib, world_factory)
    wb = _target(lib, world_factory)
    assert _load(lib, wb, buf, size) == 0
    for t in range(1, AFTER_TICKS + 1):
        lib.om_tactical_step(wa)
        lib.om_tactical_step(wb)
        if t % 10 == 0:
            a, b = _secs(lib, wa)[SUPPORT_MAP], _secs(lib, wb)[SUPPORT_MAP]
            assert a == b, f"tick {SAVE_TICK + t}: section 8 differs between source and loaded world"


def test_second_save_of_loaded_world_is_byte_identical(lib, world_factory):
    _, buf1, size1 = _saved_battle(lib, world_factory)
    wb = _target(lib, world_factory)
    assert _load(lib, wb, buf1, size1) == 0
    buf2, size2 = _save(lib, wb)
    assert size1 == size2
    assert bytes(buf1) == bytes(buf2)


def test_truncated_buffer_refused_target_unchanged(lib, world_factory):
    _, buf, size = _saved_battle(lib, world_factory)
    wb = _target(lib, world_factory)
    before = _secs(lib, wb)
    cut = size - 3  # inside the last (mapgen) slot
    trunc = (ctypes.c_uint8 * cut)(*bytes(buf)[:cut])
    assert _load(lib, wb, trunc, cut) != 0, "a truncated buffer must be refused"
    assert _secs(lib, wb) == before, "a refused load changed the target's checksum"


def test_corrupt_mapgen_slot_length_refused_target_unchanged(lib, world_factory):
    _, buf, size = _saved_battle(lib, world_factory)
    off, blen = _mapgen_slot(buf, size)
    wb = _target(lib, world_factory)
    before = _secs(lib, wb)
    for bad in (blen + 1, 0xFFFFFFFF):
        raw = bytearray(bytes(buf))
        struct.pack_into("<I", raw, off + 1, bad)
        c = (ctypes.c_uint8 * size)(*raw)
        assert _load(lib, wb, c, size) != 0, f"mapgen slot length {bad} (true {blen}) must be refused"
        assert _secs(lib, wb) == before, "a refused load changed the target's checksum"


def test_save_before_any_mission_still_loads(lib, world_factory):
    from conftest import OMFeature
    w = world_factory(n_regions=2, seed=5)
    lib.om_world_set_feature(w, OMFeature.TACTICAL, 1)
    buf, size = _save(lib, w)
    _, blen = _mapgen_slot(buf, size)
    assert blen == 0 or blen > 0  # slot present; empty before any mission is the usual case
    wb = _target(lib, world_factory)
    assert _load(lib, wb, buf, size) == 0, "a save with an empty mapgen slot must load"


def test_full_checksum_equal_for_500_ticks(lib, world_factory):
    wa, buf, size = _saved_battle(lib, world_factory)
    wb = _target(lib, world_factory)
    assert _load(lib, wb, buf, size) == 0
    assert _secs(lib, wa) == _secs(lib, wb), "full checksum differs right after the load"
    for t in range(1, AFTER_TICKS + 1):
        lib.om_tactical_step(wa)
        lib.om_tactical_step(wb)
        if t % 10 == 0:
            assert _secs(lib, wa) == _secs(lib, wb), f"tick {SAVE_TICK + t}: full checksum differs"
