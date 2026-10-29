# Rule pins: R-111-03@d25a6f
"""C2 / HDR5 (gap-fix plan, "HDR5, region scale"): the save writes the region_edge matrix at
OM_MAX_REGIONS x OM_MAX_REGIONS (csrc/save.c), so 128 -> 512 changes the layout and
OM_SAVE_FORMAT_VERSION goes 4 -> 5; save.c refuses any other version cleanly (R-111-03, no migration).

Base for these tests: origin/main after B6, where the version is 4 (gen_state gained commander and lineage fields).
The version word is the u32 after the 4-byte magic, little endian (same layout as
test_E16_B5_save_version.py).
"""
import ctypes

from conftest import OMTier, set_owner, set_region

VERSION_OFFSET = 4
EXPECTED_VERSION = 13
PRE_BUMP_VERSION = 9


def _bind_save(lib):
    if getattr(lib, "_c2_save_bound", False):
        return
    V = ctypes.c_void_p
    P = ctypes.POINTER
    lib.om_save_state_size.argtypes = [V]
    lib.om_save_state_size.restype = ctypes.c_uint32
    lib.om_save_state_write.argtypes = [V, P(ctypes.c_uint8), ctypes.c_uint32]
    lib.om_save_state_write.restype = None
    lib.om_load_state_read.argtypes = [V, P(ctypes.c_uint8), ctypes.c_uint32]
    lib.om_load_state_read.restype = ctypes.c_int
    lib._c2_save_bound = True


def _world(lib, world_factory, seed):
    w = world_factory(n_regions=4, seed=seed)
    for r in range(4):
        set_region(lib, w, r, tier=OMTier.HOME, military=40.0, economy=45.0, tension=5.0, population=40.0)
        set_owner(lib, w, r, 0, held_since=-1)
    return w


def _save(lib, w):
    _bind_save(lib)
    size = lib.om_save_state_size(w)
    buf = (ctypes.c_uint8 * size)()
    lib.om_save_state_write(w, buf, size)
    return buf, size


def _version_word(buf):
    return int.from_bytes(bytes(buf[VERSION_OFFSET:VERSION_OFFSET + 4]), "little")


def _with_version(buf, size, version):
    out = (ctypes.c_uint8 * size)(*buf)
    for i, b in enumerate(version.to_bytes(4, "little")):
        out[VERSION_OFFSET + i] = b
    return out


def test_R_111_03_a_save_written_now_carries_version_5(lib, world_factory):
    """Given a world, When it is saved, Then the version word after the magic is 5 (HDR5 bumped the layout)."""
    w = _world(lib, world_factory, seed=41)
    buf, size = _save(lib, w)
    assert size > 8
    assert _version_word(buf) == EXPECTED_VERSION


def test_control_R_111_03_the_version_word_reader_sees_a_patched_word(lib, world_factory):
    """Control: the reader reports a patched word, so a failing 'carries version 5' means the save wrote another number."""
    w = _world(lib, world_factory, seed=42)
    buf, size = _save(lib, w)
    assert _version_word(_with_version(buf, size, 77)) == 77


def test_R_111_03_a_version_5_save_loads_back(lib, world_factory):
    """Positive control for the refusal: the same patch path with version 5 loads, so a refusal below is the version, not the patching."""
    src = _world(lib, world_factory, seed=43)
    buf, size = _save(lib, src)
    patched = _with_version(buf, size, EXPECTED_VERSION)
    dst = world_factory(n_regions=4, seed=44)
    assert lib.om_load_state_read(dst, patched, size) == 0
    assert lib.om_world_get_state_checksum(dst) == lib.om_world_get_state_checksum(src)


def test_R_111_03_a_version_4_save_is_refused_cleanly(lib, world_factory):
    """Given a save from before the bump (version word 4), When loaded, Then it is refused (non-zero return) and the target world is untouched."""
    src = _world(lib, world_factory, seed=45)
    buf, size = _save(lib, src)
    old = _with_version(buf, size, PRE_BUMP_VERSION)
    dst = world_factory(n_regions=4, seed=46)
    before = lib.om_world_get_state_checksum(dst)
    assert lib.om_load_state_read(dst, old, size) != 0
    assert lib.om_world_get_state_checksum(dst) == before
