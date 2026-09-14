"""S-020 -- Same seed, same galaxy.

R-020-01 .. R-020-03. Determinism contract: docs/northstar/research/c_rewrite.md;
checksum contract: header comment above om_world_checksum (FNV-1a 64-bit over
the little-endian IEEE-754 bits of every inhabited region's six numbers,
folded with the tick).

R-020-02 (cross-platform checksum match) genuinely cannot be exercised by a
single-machine pytest run -- it requires the same seed run through Linux,
Windows, and macOS builds and their checksums compared out of band (the CI
matrix in docs/northstar/research/c_rewrite.md). This module tests the
necessary-but-not-sufficient same-machine proxy (repeat-run determinism) and
flags the true cross-platform claim as a skip with that reasoning.
"""
import ctypes

import pytest

from conftest import OMTier, OmTraceRow, set_region


def _build_and_run(lib, world_factory, seed, n_ticks):
    w = world_factory(n_regions=3, seed=seed)
    set_region(lib, w, 0, tier=OMTier.HOME, military=42.0, economy=66.0,
               tension=18.0, population=60.0, econ_phase=0.3, tension_phase=1.1,
               faction_id=1)
    set_region(lib, w, 1, tier=OMTier.FRONTIER, military=20.0, economy=35.0,
               tension=55.0, population=30.0, econ_phase=2.5, tension_phase=4.2)
    set_region(lib, w, 2, tier=OMTier.HOME, military=80.0, economy=90.0,
               tension=5.0, population=70.0, econ_phase=5.9, tension_phase=0.1,
               faction_id=1)
    lib.om_trace_enable(w, 1)
    ran = lib.om_world_run(w, n_ticks)
    assert ran == n_ticks
    n = lib.om_trace_len(w)
    rows = (OmTraceRow * n)()
    got = lib.om_trace_read(w, 0, n, rows)
    assert got == n
    return w, rows


def test_R_020_01_two_runs_same_seed_byte_identical(lib, world_factory):
    _, rows_a = _build_and_run(lib, world_factory, seed=99999, n_ticks=50)
    _, rows_b = _build_and_run(lib, world_factory, seed=99999, n_ticks=50)

    bytes_a = ctypes.string_at(ctypes.addressof(rows_a), ctypes.sizeof(rows_a))
    bytes_b = ctypes.string_at(ctypes.addressof(rows_b), ctypes.sizeof(rows_b))
    assert bytes_a == bytes_b


def test_R_020_01_same_machine_checksum_repeat(lib, world_factory):
    w_a, _ = _build_and_run(lib, world_factory, seed=42, n_ticks=50)
    w_b, _ = _build_and_run(lib, world_factory, seed=42, n_ticks=50)
    assert lib.om_world_checksum(w_a) == lib.om_world_checksum(w_b)


def test_R_020_02_same_machine_proxy_repeat_determinism(lib, world_factory):
    # Necessary-but-not-sufficient for R-020-02: two runs on this one Linux
    # machine must at least agree. Does not prove the real claim (Linux,
    # Windows, macOS binaries agreeing); see the skip below.
    w_a, rows_a = _build_and_run(lib, world_factory, seed=7, n_ticks=40)
    w_b, rows_b = _build_and_run(lib, world_factory, seed=7, n_ticks=40)
    checksums_a = [r.checksum for r in rows_a if r.checksum != 0]
    checksums_b = [r.checksum for r in rows_b if r.checksum != 0]
    assert checksums_a == checksums_b


@pytest.mark.skip(
    reason="R-020-02 (identical 10-tick checksums across Linux, Windows, and "
           "macOS builds from one seed) requires a CI matrix running the "
           "same seed through binaries built on all three platforms -- a "
           "single-machine pytest process cannot exercise cross-platform "
           "agreement. See docs/northstar/research/c_rewrite.md for the "
           "intended matrix; test_R_020_02_same_machine_proxy_repeat_"
           "determinism above covers the necessary same-machine precondition."
)
def test_R_020_02_cross_platform_checksums_match():
    pass


def test_R_020_03_checksum_cadence_is_ten(lib):
    assert lib.om_checksum_cadence() == 10


def test_R_020_03_checksum_emitted_only_on_cadence(lib, world_factory):
    w = world_factory(n_regions=1)
    set_region(lib, w, 0, tier=OMTier.HOME, military=50.0, economy=60.0,
               tension=20.0, population=50.0)
    lib.om_trace_enable(w, 1)
    ran = lib.om_world_run(w, 25)
    assert ran == 25
    n = lib.om_trace_len(w)
    rows = (OmTraceRow * n)()
    got = lib.om_trace_read(w, 0, n, rows)
    assert got == n

    for row in sorted(rows, key=lambda r: r.tick):
        if row.tick % 10 == 0:
            assert row.checksum != 0, f"tick {row.tick} should carry a checksum"
        else:
            assert row.checksum == 0, f"tick {row.tick} should not carry a checksum"
