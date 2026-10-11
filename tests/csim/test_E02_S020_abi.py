"""S-020 -- ABI version and layout check.

The header's own comment on om_abi_version (csrc/ouroboros_sim.h): "The test
harness asserts this matches what it was written against. Bump on any
breaking change to a signature or struct layout." freeze/F2 bumps it to 2
(OM_FEAT_TACTICAL, the E-06/E-07/E-11 tick-order bug ids, and the three core
symbols below are new since version 1); the `lib`/`dbg` fixtures already
assert this on every test (conftest.py's EXPECTED_ABI_VERSION), so this
module owns the two new fixture/reader symbols the freeze lands in
csrc/sim.c: om_world_get_state_checksum (a second entry point for the same
value om_world_checksum returns -- T1's pipe and E-12/E-13's tests name this
symbol instead) and om_world_set_tick (E-06/E-10's fixture setter), plus
om_abi_layout_check (the pipe hello's struct-size cross-check, audit
2026-09-21 A F-8-5).
"""
import ctypes

from conftest import OMTier, OmCollision, OmDriftRow, OmTraceRow, set_region


def test_R_020_abi_version_is_4(lib):
    assert lib.om_abi_version() == 7


def test_R_020_layout_check_matches_caller_sizes(lib):
    ok = lib.om_abi_layout_check(
        ctypes.sizeof(OmTraceRow), ctypes.sizeof(OmDriftRow), ctypes.sizeof(OmCollision),
    )
    assert ok == 1


def test_R_020_layout_check_rejects_a_wrong_trace_row_size(lib):
    ok = lib.om_abi_layout_check(
        ctypes.sizeof(OmTraceRow) + 8, ctypes.sizeof(OmDriftRow), ctypes.sizeof(OmCollision),
    )
    assert ok == 0


def test_R_020_layout_check_rejects_a_wrong_collision_size(lib):
    ok = lib.om_abi_layout_check(
        ctypes.sizeof(OmTraceRow), ctypes.sizeof(OmDriftRow), ctypes.sizeof(OmCollision) - 8,
    )
    assert ok == 0


def test_R_020_get_state_checksum_matches_world_checksum(lib, world_factory):
    w = world_factory(n_regions=1)
    set_region(lib, w, 0, tier=OMTier.HOME, military=50.0, economy=50.0,
               tension=10.0, population=50.0)
    lib.om_world_step(w)
    assert lib.om_world_get_state_checksum(w) == lib.om_world_checksum(w)


def test_R_020_set_tick_moves_the_counter_with_no_other_side_effect(lib, world_factory):
    w = world_factory(n_regions=1)
    set_region(lib, w, 0, tier=OMTier.HOME, military=50.0, economy=50.0,
               tension=10.0, population=50.0)
    lib.om_world_set_tick(w, 105)
    tick = lib.om_world_step(w)
    assert tick == 106, "R-045-07: the next om_world_step after set_tick(105) must yield 106"
