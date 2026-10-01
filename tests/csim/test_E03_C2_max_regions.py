"""C2 / HDR5 (docs/northstar/plans/2026-09-28-gap-fix-and-migration-plan.md, "HDR5, region scale";
mission-plays plan item C2): OM_MAX_REGIONS goes 128 -> 512 so the E-03 range [250, 400] (R-021-01)
fits every region-sized array. Past the cap a world is refused cleanly, never overrun.

The refusal shape is not written in any rule (see Q-candidate in the C2 report): these tests pin
om_world_new(n > cap) -> NULL and om_world_generate with a range above the cap -> om_world_generated == 0.
"""
import ctypes
import pathlib
import re

from conftest import gen_set_region_range, generate

REPO = pathlib.Path(__file__).resolve().parents[2]
CAP = 512


def _header_cap():
    text = (REPO / "csrc" / "om_internal.h").read_text()
    m = re.search(r"^#define OM_MAX_REGIONS (\d+)", text, re.M)
    return int(m.group(1)) if m else None


def _features_on(lib, w):
    for feat in range(8):
        lib.om_world_set_feature(w, feat, 1)


def test_control_C2_header_reader_sees_a_define():
    """Control: the header reader returns a number, so a failing 'is 512' below means the value is wrong, not the parse."""
    assert isinstance(_header_cap(), int)


def test_R_021_01_om_max_regions_is_512():
    """Given HDR5, When csrc/om_internal.h is read, Then OM_MAX_REGIONS is 512 (E-03's top of range is 400)."""
    assert _header_cap() == CAP


def test_R_021_01_a_400_region_world_generates_and_steps(lib):
    """Given a range pinned to 400, When the world is generated and stepped 20 ticks, Then it has 400 regions and every region has an edge (no edge lost past index 127)."""
    w = lib.om_world_new(0, 3)
    assert w
    _features_on(lib, w)
    gen_set_region_range(lib, w, 400, 400)
    assert generate(lib, w) == 1, "generation failed at 400 regions"
    assert lib.om_region_count(w) == 400
    for _ in range(20):
        lib.om_world_step(w)
    buf = (ctypes.c_uint32 * 512)()
    lib.om_region_neighbors.restype = ctypes.c_uint32
    for r in range(400):
        n = lib.om_region_neighbors(w, r, buf, 512)
        assert n >= 1, f"region {r} has no neighbors: the edge matrix lost its row (cap 128 overran)"
    lib.om_world_free(w)


def test_R_021_01_a_512_region_world_is_accepted(lib):
    """Positive control for the refusal below: exactly OM_MAX_REGIONS regions is a valid explicit world and steps."""
    w = lib.om_world_new(CAP, 5)
    assert w, "om_world_new(512) must succeed (the cap itself is allowed)"
    lib.om_world_step(w)
    lib.om_world_free(w)


def test_R_021_01_513_regions_is_refused_cleanly(lib):
    """Given a count one past the cap, When om_world_new is called, Then it returns NULL (no world, no overrun)."""
    w = lib.om_world_new(CAP + 1, 5)
    assert not w, "om_world_new(513) must return NULL"


def test_R_021_01_a_generation_range_past_the_cap_does_not_generate(lib):
    """Given a generation range pinned to 513, When the world is generated, Then om_world_generated is 0 and the world is still freeable."""
    w = lib.om_world_new(0, 6)
    assert w
    gen_set_region_range(lib, w, CAP + 1, CAP + 1)
    assert generate(lib, w) == 0, "a 513-region generation must fail feasibility, not write past the arrays"
    lib.om_world_free(w)
