"""Lockstep spec 2026-10-05, module lane mod-mission, stage 2: the mission save hook
(slot OM_SAVE_SLOT_MISSION, mission_state; checksum section 5, mission).

Proves R-139-03 (a loaded world carries the same checkpoint state) through save/load, the
spec's "known risk" paragraph: save mid-battle, load into a fresh world, step both 500
tactical ticks, section equal at every tenth tick. Also R-111-03 (a refused load leaves
the target untouched).

Only this module's section (5) is asserted equal, because the other modules' save hooks
are not written yet; the one FULL-checksum test is xfail(strict=False) for that reason.
RED while the slot is saved empty: the loaded world has no mission state, so section 5
differs right after the load.
"""
import ctypes
import struct

import pytest

from b1_macro_scene import ENEMY_FAC, PLAYER_FAC, RAIDER, tactical_world
from test_E16_S111_saving import _bind_save, _load, _save
from test_net_section_hashes import N_SECTIONS, _battle, _run, _secs

MISSION = 5
SLOT_MISSION = 3
N_SLOTS = 11
SAVE_TICK = 150
AFTER_TICKS = 500


def _fresh_target(lib, world_factory, seed=7):
    """The target a save is loaded into: the same scene setup, no units, no battle run."""
    return tactical_world(lib, world_factory, seed=seed)


def _battle_at_save(lib, world_factory):
    w, _, _ = _battle(lib, world_factory)
    _run(lib, w, SAVE_TICK)
    return w


def _slot_blen_offset(buf, slot):
    """Offset of a slot's 4-byte length. Slots are the buffer's tail: eleven of
    (u8 id, u32 len, blob), ids 0..10 in order. Find the start whose chain ends exactly
    at the end of the buffer."""
    data = bytes(buf)
    n = len(data)
    for start in range(n - 5 * N_SLOTS, -1, -1):
        pos, offs = start, []
        for sid in range(N_SLOTS):
            if pos + 5 > n or data[pos] != sid:
                break
            blen = struct.unpack_from("<I", data, pos + 1)[0]
            offs.append((pos + 1, blen))
            pos += 5 + blen
        else:
            if pos == n:
                return offs[slot]
    raise AssertionError("could not locate the slot table at the tail of the save buffer")


def _roundtrip_pair(lib, world_factory):
    src = _battle_at_save(lib, world_factory)
    buf, size = _save(lib, src)
    dst = _fresh_target(lib, world_factory)
    rc = _load(lib, dst, buf, size)
    assert rc == 0, f"a clean save must load, rc={rc}"
    return src, dst, buf, size


def test_mission_section_equal_right_after_load(lib, world_factory):
    src, dst, _, _ = _roundtrip_pair(lib, world_factory)
    a, b = _secs(lib, src)[MISSION], _secs(lib, dst)[MISSION]
    assert a != 0, "setup: the source's mission section reads 0 at tick 150"
    assert a == b, f"mission section differs right after load: src {a:#x} dst {b:#x}"


def test_mission_section_equal_through_500_ticks(lib, world_factory):
    src, dst, _, _ = _roundtrip_pair(lib, world_factory)
    for t in range(1, AFTER_TICKS + 1):
        lib.om_tactical_step(src)
        lib.om_tactical_step(dst)
        if t % 10 == 0:
            a, b = _secs(lib, src)[MISSION], _secs(lib, dst)[MISSION]
            assert a == b, f"tick {SAVE_TICK + t}: mission section differs after load"


def test_full_checksum_equal_through_500_ticks(lib, world_factory):
    src, dst, _, _ = _roundtrip_pair(lib, world_factory)
    for t in range(1, AFTER_TICKS + 1):
        lib.om_tactical_step(src)
        lib.om_tactical_step(dst)
        if t % 10 == 0:
            assert _secs(lib, src) == _secs(lib, dst), f"tick {SAVE_TICK + t}: full checksum differs"


def test_second_save_of_loaded_world_is_byte_identical(lib, world_factory):
    _, dst, buf, size = _roundtrip_pair(lib, world_factory)
    buf2, size2 = _save(lib, dst)
    assert size2 == size, f"size differs after load: {size} vs {size2}"
    assert bytes(buf2) == bytes(buf), "second save of the loaded world is not byte-identical"


def test_truncated_buffer_refused_target_untouched(lib, world_factory):
    src = _battle_at_save(lib, world_factory)
    buf, size = _save(lib, src)
    dst = _fresh_target(lib, world_factory)
    before = _secs(lib, dst)
    blen_off, blen = _slot_blen_offset(buf, SLOT_MISSION)
    assert blen > 0, "setup: the mission slot is saved empty (hook not written)"
    cut = blen_off + 4 + blen // 2  # cut inside the mission blob
    rc = _load(lib, dst, (ctypes.c_uint8 * cut).from_buffer_copy(bytes(buf)[:cut]), cut)
    assert rc != 0, "a truncated buffer must be refused"
    assert _secs(lib, dst) == before, "a refused load changed the target's checksum"


def test_corrupt_mission_slot_length_refused_target_untouched(lib, world_factory):
    src = _battle_at_save(lib, world_factory)
    buf, size = _save(lib, src)
    dst = _fresh_target(lib, world_factory)
    before = _secs(lib, dst)
    off, blen = _slot_blen_offset(buf, SLOT_MISSION)
    assert blen > 0, "setup: the mission slot is saved empty (hook not written)"
    bad = bytearray(bytes(buf))
    struct.pack_into("<I", bad, off, blen + 1000)
    rc = _load(lib, dst, (ctypes.c_uint8 * size).from_buffer_copy(bytes(bad)), size)
    assert rc != 0, "a corrupted mission slot length must be refused"
    assert _secs(lib, dst) == before, "a refused load changed the target's checksum"


def test_save_before_any_mission_still_loads(lib, world_factory):
    """Slot empty: a world that never set up a mission saves and loads."""
    src = world_factory(n_regions=2, seed=5)
    buf, size = _save(lib, src)
    dst = world_factory(n_regions=2, seed=6)
    assert _load(lib, dst, buf, size) == 0, "a save with an empty mission slot must load"
