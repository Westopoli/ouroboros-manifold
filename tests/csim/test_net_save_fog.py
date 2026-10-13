"""Lockstep spec 2026-10-05, module lane mod-fog, stage 2: the fog save hooks.

Proves R-139-03 (the checkpoint checksum covers fog state) and R-111-02/R-111-03
(save and load round trip; a refused load leaves the target untouched) for the
fog_state slot (OM_SAVE_SLOT_FOG = 4), checksum section 6 (fog).

Section-only note: the other modules' save hooks are not written yet, so the
loaded world's FULL checksum cannot match the source's. Every test but the last
asserts only section 6 (FOG). test_full_checksum_equal_500_ticks asserts all
nine sections and is xfail until every module's hooks land.

Red now: fog_state is saved empty (length 0), so the loaded world's fog section
differs from the source's.
"""
import ctypes
import struct

import pytest

from b1_macro_scene import tactical_world
from test_net_section_hashes import FOG, N_SECTIONS, _battle, _run, _secs

OM_SAVE_SLOT_FOG = 4
SLOT_COUNT = 11


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


def _fog_slot(buf, size):
    """(offset of the fog slot's u32 length, its length). The eleven slots are the
    last thing in a save: id u8, length u32 LE, blob; ids 0..10 in order."""
    raw = bytes(buf)
    for start in range(size - 5, -1, -1):
        pos, ok, fog = start, True, None
        for sid in range(SLOT_COUNT):
            if pos + 5 > size or raw[pos] != sid:
                ok = False
                break
            (blen,) = struct.unpack_from("<I", raw, pos + 1)
            if sid == OM_SAVE_SLOT_FOG:
                fog = (pos + 1, blen)
            pos += 5 + blen
        if ok and pos == size:
            return fog
    raise AssertionError("could not find the eleven save slots at the end of the buffer")


def _saved_at_150(lib, world_factory):
    w, _, _ = _battle(lib, world_factory)
    _run(lib, w, 150)
    buf, size = _save(lib, w)
    return w, buf, size


def _target(lib, world_factory):
    return tactical_world(lib, world_factory, seed=99)


def test_fog_round_trip_section_equal_after_load(lib, world_factory):
    w1, buf, size = _saved_at_150(lib, world_factory)
    w2 = _target(lib, world_factory)
    assert _load(lib, w2, buf, size) == 0, "a save from a real battle must load"
    a, b = _secs(lib, w1)[FOG], _secs(lib, w2)[FOG]
    assert a == b, f"fog section differs right after the load: {a:#x} vs {b:#x}"


def test_fog_section_equal_every_tenth_tick_for_500_ticks(lib, world_factory):
    w1, buf, size = _saved_at_150(lib, world_factory)
    w2 = _target(lib, world_factory)
    assert _load(lib, w2, buf, size) == 0
    for t in range(1, 501):
        lib.om_tactical_step(w1)
        lib.om_tactical_step(w2)
        if t % 10 == 0:
            a, b = _secs(lib, w1)[FOG], _secs(lib, w2)[FOG]
            assert a == b, f"tick +{t} after load: fog section differs"


def test_fog_second_save_of_loaded_world_is_byte_identical(lib, world_factory):
    _, buf, size = _saved_at_150(lib, world_factory)
    w2 = _target(lib, world_factory)
    assert _load(lib, w2, buf, size) == 0
    buf2, size2 = _save(lib, w2)
    assert size2 == size, f"second save is {size2} bytes, first was {size}"
    assert bytes(buf2) == bytes(buf), "second save differs from the first"


def test_fog_truncated_buffer_refused_target_unchanged(lib, world_factory):
    _, buf, size = _saved_at_150(lib, world_factory)
    w2 = _target(lib, world_factory)
    before = list(_secs(lib, w2))
    cut = size - 7
    short = (ctypes.c_uint8 * cut)(*bytes(buf)[:cut])
    assert _load(lib, w2, short, cut) != 0, "a truncated buffer must be refused"
    assert _secs(lib, w2) == before, "a refused load changed the target's checksum"


@pytest.mark.parametrize("delta", [1, -1])
def test_fog_slot_length_corrupted_refused_target_unchanged(lib, world_factory, delta):
    _, buf, size = _saved_at_150(lib, world_factory)
    off, blen = _fog_slot(buf, size)
    assert blen > 0, "fog slot is saved empty (length 0); the fog hooks are not written"
    bad = (ctypes.c_uint8 * size)(*bytes(buf))
    struct.pack_into("<I", bad, off, blen + delta)
    w2 = _target(lib, world_factory)
    before = list(_secs(lib, w2))
    assert _load(lib, w2, bad, size) != 0, f"fog slot length {blen}{delta:+d} must be refused"
    assert _secs(lib, w2) == before, "a refused load changed the target's checksum"


def test_fog_save_before_any_mission_still_loads(lib, world_factory):
    w1 = world_factory(n_regions=2, seed=5)  # no tactical feature, no mission: fog slot empty
    buf, size = _save(lib, w1)
    w2 = world_factory(n_regions=2, seed=6)
    assert _load(lib, w2, buf, size) == 0, "a save with an empty fog slot must load"
    assert _secs(lib, w1)[FOG] == _secs(lib, w2)[FOG]


def test_full_checksum_equal_500_ticks(lib, world_factory):
    w1, buf, size = _saved_at_150(lib, world_factory)
    w2 = _target(lib, world_factory)
    assert _load(lib, w2, buf, size) == 0
    for t in range(1, 501):
        lib.om_tactical_step(w1)
        lib.om_tactical_step(w2)
        if t % 10 == 0:
            a, b = _secs(lib, w1), _secs(lib, w2)
            assert a == b, f"tick +{t}: sections differ at {[i for i in range(N_SECTIONS) if a[i] != b[i]]}"
