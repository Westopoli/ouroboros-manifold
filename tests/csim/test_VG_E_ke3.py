# Rule pins: R-111-03@d25a6f, R-168-01@c6cd6c
"""VG-CONTRACT-E3 (K-e3): density_economy is set at init, hashed by checksum_full and saved; save format 9.

Spec: docs/northstar/plans/2026-10-07-visible-game-spec.md rev 8, "Lane E1 part a3" (Part a3 rulings, Q-222-01 a).
Rules: R-168-01/05 (determinism: new world state is hashed and saved), R-111-03 (older saves refused).
"""
import ctypes

from test_VG_E_e1b import scene
from conftest import OMTier, set_region

W = ctypes.c_void_p
P = ctypes.POINTER


def _full(lib, w):
    lib.om_world_checksum_full.restype = ctypes.c_uint64
    lib.om_world_checksum_full.argtypes = [W, P(ctypes.c_uint64), ctypes.c_uint32]
    return lib.om_world_checksum_full(w, None, 0)


def _econ_section(lib, w):
    """Section 1 (factions) of checksum_full: ck_economy hashes the economy state inside it (csrc/checksum_full.c).
    The whole-world value also moves with the region economy through the mission's units (section 3), so
    only this section isolates density_economy."""
    sec = (ctypes.c_uint64 * 16)()
    lib.om_world_checksum_full.argtypes = [W, P(ctypes.c_uint64), ctypes.c_uint32]
    lib.om_world_checksum_full(w, sec, 16)
    return sec[1]


def _neutral(lib, econ, world_factory):
    """Scene with region economy econ at setup, then region 0 economy reset to 10.0, so the region's own
    hashed economy cannot tell two scenes apart; only the value sampled at init (density_economy) can."""
    w = scene(lib, world_factory, economy=econ)
    set_region(lib, w, 0, tier=OMTier.HOME, military=10.0, economy=10.0, population=10.0, faction_id=0)
    return w


def _save(lib, w):
    lib.om_save_state_size.argtypes = [W]
    lib.om_save_state_size.restype = ctypes.c_uint32
    lib.om_save_state_write.argtypes = [W, P(ctypes.c_uint8), ctypes.c_uint32]
    lib.om_save_state_write.restype = None
    n = lib.om_save_state_size(w)
    buf = (ctypes.c_uint8 * n)()
    lib.om_save_state_write(w, buf, n)
    return buf, n


def test_ke3_control_same_economy_same_checksum(lib, world_factory):
    """Positive control: two scenes with the same economy hash identically right after setup + begin."""
    assert _full(lib, _neutral(lib, 40.0, world_factory)) == _full(lib, _neutral(lib, 40.0, world_factory))


def test_ke3_density_economy_is_hashed(lib, world_factory):
    """K-e3: scenes differing only in region economy (1.0 vs 40.0, region economy reset to 10.0 after setup so only density_economy differs) differ in checksum_full with no step
    (red before K-e3: density_economy does not exist, so the hashes are equal)."""
    lo_w, hi_w = _neutral(lib, 1.0, world_factory), _neutral(lib, 40.0, world_factory)
    lo, hi = _full(lib, lo_w), _full(lib, hi_w)
    assert _econ_section(lib, lo_w) != _econ_section(lib, hi_w), "economy section equal for 1.0 and 40.0 (density_economy not set at init or not hashed)"
    assert lo != hi, "economy 1.0 and 40.0 hash the same after setup (density_economy not set at init or not hashed)"


def test_ke3_density_economy_is_saved(lib, world_factory):
    """K-e3: a save written after setup loads into a fresh world with the same checksum_full; the two
    economies stay distinguishable through save and load (red before K-e3: the economies hash equal)."""
    lib.om_load_state_read.argtypes = [W, P(ctypes.c_uint8), ctypes.c_uint32]
    lib.om_load_state_read.restype = ctypes.c_int
    sums = []
    for econ in (1.0, 40.0):
        src = _neutral(lib, econ, world_factory)
        buf, n = _save(lib, src)
        # a fresh world with the same shape but the OTHER economy, so only the loaded field can supply the value
        dst = _neutral(lib, 40.0 if econ == 1.0 else 1.0, world_factory)
        assert lib.om_load_state_read(dst, buf, n) == 0
        assert _full(lib, dst) == _full(lib, src), f"economy {econ}: loaded world hashes differently (density_economy not saved)"
        assert _econ_section(lib, dst) == _econ_section(lib, src)
        sums.append(_econ_section(lib, dst))
    assert sums[0] != sums[1], "loaded economy sections for 1.0 and 40.0 are equal"


def test_ke3_save_format_version_is_10(lib, world_factory):
    """K-e3 added the density_economy and lot_hit_tick fields (format 9); K-e5 moved the pin to 10 (TD-VG-E-16); W2 moved it to 11 (TD-VG-W-1): E7 moved it to 12 (TD-VG-E-27); LAB-REV2 E0 moved it to 13: OM_SAVE_FORMAT_VERSION is 13 (header bytes 4..8, the pin the save-pin tests use); red: 12."""
    buf, _ = _save(lib, scene(lib, world_factory))
    assert int.from_bytes(bytes(buf[4:8]), "little") == 12
