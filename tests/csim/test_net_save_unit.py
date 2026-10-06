"""Lockstep spec 2026-10-05, module lane mod-unit, stage 2: the save hooks of csrc/unit.c.

Proves R-139-03 for the units module: slot OM_SAVE_SLOT_TACTICAL (slot 0, tactical_state)
carries the units (and so the per-unit hashes) through om_save_state_write /
om_load_state_read, so a world loaded mid-battle keeps playing the same battle.
Style follows tests/csim/test_E16_S111_saving.py; the battle is built as in
tests/csim/test_net_section_hashes.py.

Tests:
  1 round trip at tick 150: units section (3) equal right after the load
  2 the real test: both worlds step 500 more ticks, units section equal every tenth tick
  3 a second save of the loaded world is byte-identical to the first
  4 a truncated buffer and a corrupted tactical slot length are refused, target's full
    checksum unchanged
  5 a save taken before any mission (slot empty) still loads
  6 xfail: the FULL checksum for 500 ticks (needs every module's save hooks)

Only this module's section is asserted in tests 1 and 2, because the other modules'
save hooks are not written yet (their sections would differ after a load).
RED while the slot is saved empty: the loaded world has no units, so section 3 differs.
"""
import ctypes

import pytest

from b1_macro_scene import tactical_world
from test_net_section_hashes import UNITS, N_SECTIONS, _battle, _run, _secs

SAVE_TICK = 150
MORE_TICKS = 500
OM_SAVE_SLOT_TACTICAL = 0
OM_SAVE_SLOT_COUNT = 11


def _bind(lib):
    if getattr(lib, "_net_save_bound", False):
        return
    V, P = ctypes.c_void_p, ctypes.POINTER
    lib.om_save_state_size.argtypes = [V]
    lib.om_save_state_size.restype = ctypes.c_uint32
    lib.om_save_state_write.argtypes = [V, P(ctypes.c_uint8), ctypes.c_uint32]
    lib.om_save_state_write.restype = None
    lib.om_load_state_read.argtypes = [V, P(ctypes.c_uint8), ctypes.c_uint32]
    lib.om_load_state_read.restype = ctypes.c_int
    lib._net_save_bound = True


def _save(lib, w):
    _bind(lib)
    size = lib.om_save_state_size(w)
    buf = (ctypes.c_uint8 * size)()
    lib.om_save_state_write(w, buf, size)
    return buf, size


def _load(lib, w, buf, size):
    _bind(lib)
    return lib.om_load_state_read(w, buf, size)


def _target(lib, world_factory):
    """A fresh tactical world, prepared as the battle's own world is, no units yet."""
    return tactical_world(lib, world_factory, seed=999)


def _battle_saved(lib, world_factory):
    w, _, _ = _battle(lib, world_factory)
    _run(lib, w, SAVE_TICK)
    buf, size = _save(lib, w)
    return w, buf, size


def _slot0_len_offset(buf, size):
    """Offset of the u32 length of the tactical slot: the one place from which the eleven
    slot headers (id u8, len u32 LE, blob) 0..10 in order end exactly at the buffer end."""
    raw = bytes(buf)
    for t in range(0, size - 4):
        pos, ok = t, True
        for sid in range(OM_SAVE_SLOT_COUNT):
            if pos + 5 > size or raw[pos] != sid:
                ok = False
                break
            pos += 5 + int.from_bytes(raw[pos + 1:pos + 5], "little")
        if ok and pos == size:
            return t + 1
    raise AssertionError("setup: could not locate the slot table at the end of the save")


def test_unit_save_round_trip_section_equal_after_load(lib, world_factory):
    w1, buf, size = _battle_saved(lib, world_factory)
    w2 = _target(lib, world_factory)
    assert _load(lib, w2, buf, size) == 0
    a, b = _secs(lib, w1)[UNITS], _secs(lib, w2)[UNITS]
    assert a != 0, "setup: units section reads 0 at the save"
    assert a == b, f"units section differs right after the load: {a:#x} vs {b:#x}"


def test_unit_save_500_ticks_after_load_section_equal_every_tenth(lib, world_factory):
    w1, buf, size = _battle_saved(lib, world_factory)
    w2 = _target(lib, world_factory)
    assert _load(lib, w2, buf, size) == 0
    for t in range(1, MORE_TICKS + 1):
        lib.om_tactical_step(w1)
        lib.om_tactical_step(w2)
        if t % 10 == 0:
            a, b = _secs(lib, w1)[UNITS], _secs(lib, w2)[UNITS]
            assert a == b, f"{t} ticks after the load: units section differs"


def test_unit_save_second_save_byte_identical(lib, world_factory):
    _, buf1, size1 = _battle_saved(lib, world_factory)
    w2 = _target(lib, world_factory)
    assert _load(lib, w2, buf1, size1) == 0
    buf2, size2 = _save(lib, w2)
    assert size1 == size2
    assert bytes(buf1) == bytes(buf2)


def test_unit_save_truncated_and_corrupt_slot_length_refused(lib, world_factory):
    _, buf, size = _battle_saved(lib, world_factory)
    off = _slot0_len_offset(buf, size)
    slot_len = int.from_bytes(bytes(buf[off:off + 4]), "little")
    assert slot_len > 0, "the tactical slot is saved empty (units are not saved)"

    target, _, _ = _battle(lib, world_factory, seed=31)
    _run(lib, target, 40)
    before = (list(_secs(lib, target)), lib.om_world_get_state_checksum(target))

    half = size // 2
    truncated = (ctypes.c_uint8 * half)(*buf[:half])
    assert _load(lib, target, truncated, half) != 0, "truncated buffer was accepted"
    assert (list(_secs(lib, target)), lib.om_world_get_state_checksum(target)) == before

    for bad in (slot_len + 1, slot_len - 1, 0xFFFFFFF0):
        corrupt = (ctypes.c_uint8 * size)(*buf)
        corrupt[off:off + 4] = list(bad.to_bytes(4, "little"))
        assert _load(lib, target, corrupt, size) != 0, f"slot length {bad} was accepted"
        assert (list(_secs(lib, target)), lib.om_world_get_state_checksum(target)) == before


def test_unit_save_before_any_mission_loads(lib, world_factory):
    w = world_factory(n_regions=2, seed=5)
    buf, size = _save(lib, w)
    target = _target(lib, world_factory)
    assert _load(lib, target, buf, size) == 0


def test_unit_save_full_checksum_equal_500_ticks(lib, world_factory):
    w1, buf, size = _battle_saved(lib, world_factory)
    w2 = _target(lib, world_factory)
    assert _load(lib, w2, buf, size) == 0
    for t in range(1, MORE_TICKS + 1):
        lib.om_tactical_step(w1)
        lib.om_tactical_step(w2)
        if t % 10 == 0:
            assert _secs(lib, w1) == _secs(lib, w2), f"{t} ticks after the load: full checksum differs"
