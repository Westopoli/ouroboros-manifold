# Rule pins: R-126-02@741af4
"""W-1e: om_structure_set_position sets x/y; read back via om_structure_get_position.

(a) Set position on a fresh structure; read back through om_structure_get_position.
(b) Out-of-range slot: same convention as om_structure_set_owner / om_structure_set_timer
    (om_sup_structure_at clamps idx to OM_SUP_MAX_STRUCTURES-1; returns 0, no crash).
(c) Setting position does not change last_spawn_distance before any production tick runs
    (assert om_structure_get_last_spawn_distance still returns its init value 0.0).
"""
import ctypes
import math

from conftest import OMFeature, OMVec2


OM_SUP_MAX_STRUCTURES = 64   # csrc/om_constants.h OM_SUP_MAX_STRUCTURES


def _tactical_world(lib, world_factory, *, seed=1):
    w = world_factory(n_regions=1, seed=seed)
    lib.om_world_set_feature(w, OMFeature.TACTICAL, 1)
    return w


# ---- (a) set position and read back ----

def test_structure_set_position_readback(lib, world_factory):
    """om_structure_set_position returns 0 and the written x/y are visible
    through om_structure_get_position."""
    w = _tactical_world(lib, world_factory, seed=30)
    lib.om_structure_init(w, 0, 0, ctypes.c_double(10.0))

    ret = lib.om_structure_set_position(w, 0, ctypes.c_double(400.0), ctypes.c_double(200.0))
    assert ret == 0, (
        "om_structure_set_position must return 0 on success, got %d" % ret)

    out = OMVec2()
    lib.om_structure_get_position(w, 0, ctypes.byref(out))
    assert math.isclose(out.x, 400.0, abs_tol=1e-9), (
        "om_structure_get_position x must be 400.0 after set, got %.6f" % out.x)
    assert math.isclose(out.y, 200.0, abs_tol=1e-9), (
        "om_structure_get_position y must be 200.0 after set, got %.6f" % out.y)


# ---- (b) out-of-range slot: clamp convention, no crash ----

def test_structure_set_position_out_of_range(lib, world_factory):
    """Out-of-range slot idx is clamped by om_sup_structure_at to
    OM_SUP_MAX_STRUCTURES-1 (same convention as set_owner/set_timer).
    Returns 0; no crash or UB."""
    w = _tactical_world(lib, world_factory, seed=31)
    # Slot OM_SUP_MAX_STRUCTURES is one past the end.
    ret = lib.om_structure_set_position(w, OM_SUP_MAX_STRUCTURES, ctypes.c_double(1.0), ctypes.c_double(2.0))
    assert ret == 0, (
        "om_structure_set_position must return 0 even for out-of-range slot, got %d" % ret)


# ---- (c) position change does not touch last_spawn_distance ----

def test_structure_set_position_does_not_alter_last_spawn_distance(lib, world_factory):
    """Setting position must not change last_spawn_distance (set only by
    om_structure_tick_production, from the lattice slot it picks: R-126-02 as rewritten, TD-VG-E-29; no RNG draw). After init and set_position,
    last_spawn_distance must still be its init value 0.0."""
    w = _tactical_world(lib, world_factory, seed=32)
    lib.om_structure_init(w, 0, 0, ctypes.c_double(10.0))
    lib.om_structure_set_position(w, 0, ctypes.c_double(500.0), ctypes.c_double(500.0))

    dist = lib.om_structure_get_last_spawn_distance(w, 0)
    assert math.isclose(dist, 0.0, abs_tol=1e-9), (
        "last_spawn_distance must remain 0.0 after set_position (no production tick ran), "
        "got %.6f" % dist)
