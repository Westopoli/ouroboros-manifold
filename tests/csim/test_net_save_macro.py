"""Lockstep spec 2026-10-05, module lane mod-macro, stage 2: the macro save hooks.

Proves R-139-03 (the checkpoint checksum covers macro state) and R-111-02/R-111-03
(save and load round trip; a refused load leaves the target untouched) for the
macro_state slot (OM_SAVE_SLOT_MACRO = 7), checksum section 7 (macro), and
section 2 (rng), which the macro noise draws advance.

Red now: macro_state is saved empty (length 0), so the loaded world's macro
section is the NULL-state constant 28001 and its rng falls out of step on the
first tick, because fresh macro state re-draws its noise.
"""
import ctypes
import struct

from b1_macro_scene import tactical_world
from test_net_section_hashes import MACRO, N_SECTIONS, _battle, _run, _secs

OM_SAVE_SLOT_MACRO = 7
SLOT_COUNT = 11
RNG = 2
NULL_MACRO = 28001


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


def _macro_slot(buf, size):
    """(offset of the macro slot's u32 length, its length). The eleven slots are the
    last thing in a save: id u8, length u32 LE, blob; ids 0..10 in order."""
    raw = bytes(buf)
    for start in range(size - 5, -1, -1):
        pos, ok, found = start, True, None
        for sid in range(SLOT_COUNT):
            if pos + 5 > size or raw[pos] != sid:
                ok = False
                break
            (blen,) = struct.unpack_from("<I", raw, pos + 1)
            if sid == OM_SAVE_SLOT_MACRO:
                found = (pos + 1, blen)
            pos += 5 + blen
        if ok and pos == size:
            return found
    raise AssertionError("could not find the eleven save slots at the end of the buffer")


def _saved_at_150(lib, world_factory):
    w, _, _ = _battle(lib, world_factory)
    _run(lib, w, 150)
    assert _secs(lib, w)[MACRO] != NULL_MACRO, "setup: the battle has no macro state at tick 150"
    buf, size = _save(lib, w)
    return w, buf, size


def _target(lib, world_factory):
    return tactical_world(lib, world_factory, seed=99)


def test_macro_round_trip_section_equal_after_load(lib, world_factory):
    w1, buf, size = _saved_at_150(lib, world_factory)
    w2 = _target(lib, world_factory)
    assert _load(lib, w2, buf, size) == 0, "a save from a real battle must load"
    a, b = _secs(lib, w1)[MACRO], _secs(lib, w2)[MACRO]
    assert a == b, f"macro section differs right after the load: {a} vs {b}"
    assert b != NULL_MACRO, "loaded world's macro section is the NULL-state constant"


def test_macro_and_rng_sections_equal_every_tenth_tick_for_500_ticks(lib, world_factory):
    w1, buf, size = _saved_at_150(lib, world_factory)
    w2 = _target(lib, world_factory)
    assert _load(lib, w2, buf, size) == 0
    for t in range(1, 501):
        lib.om_tactical_step(w1)
        lib.om_tactical_step(w2)
        if t % 10 == 0:
            a, b = _secs(lib, w1), _secs(lib, w2)
            assert a[MACRO] == b[MACRO], f"tick +{t} after load: macro section differs"
            assert a[RNG] == b[RNG], f"tick +{t} after load: rng section differs"


def test_macro_second_save_of_loaded_world_is_byte_identical(lib, world_factory):
    _, buf, size = _saved_at_150(lib, world_factory)
    w2 = _target(lib, world_factory)
    assert _load(lib, w2, buf, size) == 0
    buf2, size2 = _save(lib, w2)
    assert size2 == size, f"second save is {size2} bytes, first was {size}"
    assert bytes(buf2) == bytes(buf), "second save differs from the first"


def test_macro_truncated_buffer_refused_target_unchanged(lib, world_factory):
    _, buf, size = _saved_at_150(lib, world_factory)
    w2 = _target(lib, world_factory)
    before = list(_secs(lib, w2))
    cut = size - 7
    short = (ctypes.c_uint8 * cut)(*bytes(buf)[:cut])
    assert _load(lib, w2, short, cut) != 0, "a truncated buffer must be refused"
    assert _secs(lib, w2) == before, "a refused load changed the target's checksum"


def test_macro_slot_length_corrupted_refused_target_unchanged(lib, world_factory):
    _, buf, size = _saved_at_150(lib, world_factory)
    off, blen = _macro_slot(buf, size)
    assert blen > 0, "macro slot is saved empty (length 0); the macro hooks are not written"
    for delta in (1, -1):
        bad = (ctypes.c_uint8 * size)(*bytes(buf))
        struct.pack_into("<I", bad, off, blen + delta)
        w2 = _target(lib, world_factory)
        before = list(_secs(lib, w2))
        assert _load(lib, w2, bad, size) != 0, f"macro slot length {blen}{delta:+d} must be refused"
        assert _secs(lib, w2) == before, "a refused load changed the target's checksum"


def test_macro_save_before_any_mission_still_loads(lib, world_factory):
    w1 = world_factory(n_regions=2, seed=5)  # no tactical feature, no mission: macro slot empty
    buf, size = _save(lib, w1)
    w2 = world_factory(n_regions=2, seed=6)
    assert _load(lib, w2, buf, size) == 0, "a save with an empty macro slot must load"
    assert _secs(lib, w1)[MACRO] == _secs(lib, w2)[MACRO]


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
