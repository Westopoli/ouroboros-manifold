"""Lockstep spec 2026-10-05, module lane mod-support, stage 2: mid-battle save of
the support slot (OM_SAVE_SLOT_SUPPORT, csrc/tactical_support.c support_state).

Proves R-139-03 (the checkpoint checksum covers support state, so a loaded world
must match) and R-111-02/R-111-03 (load restores the world; a bad buffer is
refused and leaves the target untouched).

Section 8 is "support and map" but the base gives one hook slot and no shared
registration (csrc/om_internal.h net_section_hash[8]); the support hook hashes
support only and mapgen's install owns the slot after it. These tests therefore
assert section 8 as the support section, plus the other sections only where noted.
Section 8 equality is this module's check; the FULL checksum cannot be equal yet
because other modules' save hooks are not written, so one xfail test asserts it.

RED while the slot is saved empty: the loaded world's support section differs
from the source's.
"""
import ctypes

import pytest

from b1_macro_scene import tactical_world
from test_net_section_hashes import N_SECTIONS, SUPPORT_MAP, _battle, _run, _secs

SAVE_TICK = 150
FOLLOW_TICKS = 500
SLOT_SUPPORT = 8
SLOT_MAPGEN = 9
SLOT_TERRAIN = 10


def _bind_save(lib):
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
    _bind_save(lib)
    size = lib.om_save_state_size(w)
    buf = (ctypes.c_uint8 * size)()
    lib.om_save_state_write(w, buf, size)
    return buf, size


def _load(lib, w, buf, size):
    _bind_save(lib)
    return lib.om_load_state_read(w, buf, size)


def _full(lib, w):
    arr = (ctypes.c_uint64 * N_SECTIONS)()
    return lib.om_world_checksum_full(w, arr, N_SECTIONS)


def _saved_and_loaded(lib, world_factory):
    """Source battle at tick 150, its save, and a fresh tactical target loaded from it."""
    src, _, _ = _battle(lib, world_factory)
    _run(lib, src, SAVE_TICK)
    buf, size = _save(lib, src)
    dst = tactical_world(lib, world_factory, seed=99)  # different seed: load must overwrite
    rc = _load(lib, dst, buf, size)
    assert rc == 0, f"load of a mid-battle save refused, rc={rc}"
    return src, dst, buf, size


def _slot_header(buf, size):
    """Offset of the support slot header (id u8, length u32 LE). Slots 8, 9 and 10 are the
    tail of the buffer; find the unique offset where slot 8's length lands on slot 9's
    header, slot 9's length lands on slot 10's header and slot 10's length lands exactly on the end."""
    b = bytes(buf)
    hits = []
    for p in range(size - 10, 0, -1):
        if b[p] != SLOT_SUPPORT:
            continue
        l8 = int.from_bytes(b[p + 1:p + 5], "little")
        q = p + 5 + l8
        if q + 5 <= size and b[q] == SLOT_MAPGEN:
            l9 = int.from_bytes(b[q + 1:q + 5], "little")
            r = q + 5 + l9
            if r + 5 <= size and b[r] == SLOT_TERRAIN:
                l10 = int.from_bytes(b[r + 1:r + 5], "little")
                if r + 5 + l10 == size:
                    hits.append(p)
    assert len(hits) >= 1, "could not locate the support slot header in the save"
    return hits[0]


def test_R_139_03_round_trip_support_section_equal_after_load(lib, world_factory):
    src, dst, _, _ = _saved_and_loaded(lib, world_factory)
    a, b = _secs(lib, src)[SUPPORT_MAP], _secs(lib, dst)[SUPPORT_MAP]
    assert a != 0, "setup: source support section reads 0 at tick 150"
    assert a == b, f"support section differs right after load: {a:#x} vs {b:#x}"


def test_R_139_03_support_section_equal_every_tenth_tick_for_500_ticks(lib, world_factory):
    src, dst, _, _ = _saved_and_loaded(lib, world_factory)
    for t in range(1, FOLLOW_TICKS + 1):
        lib.om_tactical_step(src)
        lib.om_tactical_step(dst)
        if t % 10 == 0:
            a, b = _secs(lib, src)[SUPPORT_MAP], _secs(lib, dst)[SUPPORT_MAP]
            assert a == b, f"tick {SAVE_TICK + t}: support section differs after load"


def test_R_139_03_full_checksum_equal_every_tenth_tick_for_500_ticks(lib, world_factory):
    src, dst, _, _ = _saved_and_loaded(lib, world_factory)
    for t in range(1, FOLLOW_TICKS + 1):
        lib.om_tactical_step(src)
        lib.om_tactical_step(dst)
        if t % 10 == 0:
            assert _full(lib, src) == _full(lib, dst), f"tick {SAVE_TICK + t}: full checksum differs"


def test_R_111_02_second_save_of_loaded_world_is_byte_identical(lib, world_factory):
    _, dst, buf, size = _saved_and_loaded(lib, world_factory)
    buf2, size2 = _save(lib, dst)
    assert size2 == size, f"second save size {size2} != first {size}"
    assert bytes(buf2) == bytes(buf), "second save of the loaded world is not byte-identical"


def test_R_111_03_truncated_buffer_refused_checksum_unchanged(lib, world_factory):
    src, _, _ = _battle(lib, world_factory)
    _run(lib, src, SAVE_TICK)
    buf, size = _save(lib, src)
    dst = tactical_world(lib, world_factory, seed=99)
    before = (_full(lib, dst), _secs(lib, dst))
    half = size - 3  # cuts into the tail (support/mapgen slots)
    cut = (ctypes.c_uint8 * half)(*bytes(buf)[:half])
    assert _load(lib, dst, cut, half) != 0, "a truncated buffer must be refused"
    assert (_full(lib, dst), _secs(lib, dst)) == before, "refused load changed the target"


def test_R_111_03_corrupt_support_slot_length_refused_checksum_unchanged(lib, world_factory):
    src, _, _ = _battle(lib, world_factory)
    _run(lib, src, SAVE_TICK)
    buf, size = _save(lib, src)
    p = _slot_header(buf, size)
    bad = bytearray(bytes(buf))
    l8 = int.from_bytes(bad[p + 1:p + 5], "little")
    bad[p + 1:p + 5] = (l8 + 1).to_bytes(4, "little")  # slot length no longer matches its blob
    bad = (ctypes.c_uint8 * size)(*bad)
    dst = tactical_world(lib, world_factory, seed=99)
    before = (_full(lib, dst), _secs(lib, dst))
    assert _load(lib, dst, bad, size) != 0, "a corrupted support slot length must be refused"
    assert (_full(lib, dst), _secs(lib, dst)) == before, "refused load changed the target"


def test_R_111_02_save_before_any_mission_empty_slot_still_loads(lib, world_factory):
    src = world_factory(n_regions=2, seed=5)
    buf, size = _save(lib, src)
    dst = world_factory(n_regions=2, seed=6)
    rc = _load(lib, dst, buf, size)
    assert rc == 0, f"a save with the support slot empty must load, rc={rc}"
