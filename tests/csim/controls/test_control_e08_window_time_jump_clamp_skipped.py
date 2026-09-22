"""F5 window control for csrc/generational.c (E-08, wave 1/2 card B7).

Rule (docs/bible/algorithms.md ALG-45 "Time jump"): "Length n = clamp(requested,
TIME_JUMP_MIN_TICKS = 20, TIME_JUMP_MAX_TICKS = 100)." A requested length of
150 (above the 100 ceiling) must be clamped down to 100.

PLANT: under OM_BUG_TIME_JUMP_CLAMP_SKIPPED, om_time_jump_choose_length
returns the requested length verbatim, with no clamp at all, so a request of
150 comes back as 150 instead of 100.
"""
from conftest import OMBugE08


def test_control_time_jump_clamp_skipped_trips_the_detector(dbg, dbg_world_factory):
    w = dbg_world_factory(n_regions=1)
    dbg.om_debug_inject(w, OMBugE08.TIME_JUMP_CLAMP_SKIPPED)

    chosen = dbg.om_time_jump_choose_length(w, requested=150)

    assert chosen == 150, (
        "OM_BUG_TIME_JUMP_CLAMP_SKIPPED injected but a requested length of "
        "150 still came back clamped to the correct TIME_JUMP_MAX_TICKS (100) "
        "instead of the unclamped 150 -- the detector did not trip"
    )
