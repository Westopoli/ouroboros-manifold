"""F2d: om_world_new(0, seed) defers the region count to generation
(csrc/ouroboros_sim.h ~line 693-694) instead of failing. Pinned so the
zero-region path (w->n_regions == 0, w->regions == NULL) stays safe through
om_world_step / om_world_checksum / om_world_free without a future change
reintroducing the old `if (n_regions == 0) return NULL;` guard."""
import ctypes


def test_zero_regions_is_valid_and_safe(lib):
    w = lib.om_world_new(ctypes.c_uint32(0), ctypes.c_uint64(1))
    assert w, "om_world_new(0, seed) must return a valid world, not NULL"
    assert lib.om_region_count(w) == 0

    tick = lib.om_world_step(w)
    assert tick == 1

    lib.om_world_free(w)


def test_zero_regions_checksum_stable_across_two_identical_worlds(lib):
    w1 = lib.om_world_new(ctypes.c_uint32(0), ctypes.c_uint64(1))
    w2 = lib.om_world_new(ctypes.c_uint32(0), ctypes.c_uint64(1))
    assert w1 and w2

    lib.om_world_step(w1)
    lib.om_world_step(w2)

    assert lib.om_world_checksum(w1) == lib.om_world_checksum(w2)

    lib.om_world_free(w1)
    lib.om_world_free(w2)
