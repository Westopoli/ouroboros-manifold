"""Lockstep spec 2026-10-05, lane mod-move, stage 2: the movement save slot
(csrc/tactical_move.c, save slot OM_SAVE_SLOT_MOVE = 6, checksum section 4).

Proves R-139-03: a mid-battle save loaded into a fresh world carries the
movement state, so both worlds stay equal after the load. RED while the slot is
saved empty (the loaded world's movement section differs from the source's).

Only section 4 is asserted, because the other modules' save hooks are not
written yet and the full checksum cannot be equal until they are; the one
full-checksum test is xfail for that reason.
"""
import ctypes

import pytest

from b1_macro_scene import tactical_world
from test_E16_S111_saving import _load, _save
from test_net_section_hashes import MOVEMENT, _battle, _run, _secs

SAVE_TICK = 150
AFTER_TICKS = 500
SLOT_MOVE_ID = 6
SLOT_COUNT = 11


def _target(lib, world_factory):
    """A fresh world prepared like the battle's world, minus the units."""
    return tactical_world(lib, world_factory, seed=99)


def _saved_battle(lib, world_factory):
    w, _, _ = _battle(lib, world_factory)
    _run(lib, w, SAVE_TICK)
    buf, size = _save(lib, w)
    return w, buf, size


def _full(lib, w):
    return list(_secs(lib, w))


def _move_slot_len_offset(buf, size):
    """Offset of the u32 length of slot 6. Slots are the last part of the
    buffer: find the start p where eleven (id, u32 len, blob) records chain
    exactly to the end, ids 0..10 in order."""
    b = bytes(buf)
    for p in range(size):
        q, ok, off = p, True, None
        for sid in range(SLOT_COUNT):
            if q + 5 > size or b[q] != sid:
                ok = False
                break
            if sid == SLOT_MOVE_ID:
                off = q + 1
            q += 5 + int.from_bytes(b[q + 1:q + 5], "little")
        if ok and q == size:
            return off
    raise AssertionError("could not find the slot table at the end of the save")


def test_move_round_trip_section_equal_after_load(lib, world_factory):
    w1, buf, size = _saved_battle(lib, world_factory)
    assert _secs(lib, w1)[MOVEMENT] != 0, "setup: movement section reads 0 mid-battle"
    w2 = _target(lib, world_factory)
    assert _load(lib, w2, buf, size) == 0
    assert _secs(lib, w2)[MOVEMENT] == _secs(lib, w1)[MOVEMENT], \
        "movement section differs right after the load"


def test_move_section_equal_every_tenth_tick_for_500_ticks(lib, world_factory):
    w1, buf, size = _saved_battle(lib, world_factory)
    w2 = _target(lib, world_factory)
    assert _load(lib, w2, buf, size) == 0
    for t in range(1, AFTER_TICKS + 1):
        lib.om_tactical_step(w1)
        lib.om_tactical_step(w2)
        if t % 10 == 0:
            a, b = _secs(lib, w1)[MOVEMENT], _secs(lib, w2)[MOVEMENT]
            assert a == b, f"tick {SAVE_TICK + t}: movement section differs after load"


def test_full_checksum_equal_every_tenth_tick_for_500_ticks(lib, world_factory):
    w1, buf, size = _saved_battle(lib, world_factory)
    w2 = _target(lib, world_factory)
    assert _load(lib, w2, buf, size) == 0
    for t in range(1, AFTER_TICKS + 1):
        lib.om_tactical_step(w1)
        lib.om_tactical_step(w2)
        if t % 10 == 0:
            assert _full(lib, w1) == _full(lib, w2), f"tick {SAVE_TICK + t}: full checksum differs"


def test_move_second_save_of_loaded_world_is_byte_identical(lib, world_factory):
    w1, buf, size = _saved_battle(lib, world_factory)
    w2 = _target(lib, world_factory)
    assert _load(lib, w2, buf, size) == 0
    buf2, size2 = _save(lib, w2)
    assert size2 == size
    assert bytes(buf2) == bytes(buf), "save of the loaded world differs from the first save"


def test_move_truncated_buffer_refused_target_unchanged(lib, world_factory):
    _, buf, size = _saved_battle(lib, world_factory)
    cut = size - 3
    short = (ctypes.c_uint8 * cut)(*bytes(buf)[:cut])
    w2 = _target(lib, world_factory)
    before = _full(lib, w2)
    assert _load(lib, w2, short, cut) != 0, "a truncated buffer must be refused"
    assert _full(lib, w2) == before, "a refused load changed the target"


def test_move_slot_length_corrupted_refused_target_unchanged(lib, world_factory):
    _, buf, size = _saved_battle(lib, world_factory)
    off = _move_slot_len_offset(buf, size)
    bad = (ctypes.c_uint8 * size)(*bytes(buf))
    old = int.from_bytes(bytes(buf)[off:off + 4], "little")
    bad[off:off + 4] = (ctypes.c_uint8 * 4)(*(old + 7).to_bytes(4, "little"))
    w2 = _target(lib, world_factory)
    before = _full(lib, w2)
    assert _load(lib, w2, bad, size) != 0, "a corrupted move-slot length must be refused"
    assert _full(lib, w2) == before, "a refused load changed the target"


def test_move_save_before_any_mission_still_loads(lib, world_factory):
    w1 = world_factory(n_regions=2, seed=5)
    buf, size = _save(lib, w1)
    w2 = world_factory(n_regions=2, seed=6)
    assert _load(lib, w2, buf, size) == 0
