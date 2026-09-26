"""Enemy external reinforcement wave: scheduling and arrival (R-124-01/02).

Stage A only: om_macro_tick at the 40-tick evaluation boundary rolls the wave
once; om_mission_check_external_reinforcements is called every tick so the wave
arrives at its computed arrival tick. Wave UNIT SPAWN is held pending Q-124-02
(wave size open); these tests verify scheduling and flag only.
"""
import ctypes

import pytest

from conftest import OMFeature, force_draws


# ---- helpers ---------------------------------------------------------------

def _tactical_world(lib, world_factory, seed=1):
    w = world_factory(n_regions=1, seed=seed)
    lib.om_world_set_feature(w, OMFeature.TACTICAL, 1)
    return w


def _bind_rng_remaining(lib):
    if getattr(lib, "_rng_remaining_bound", False):
        return
    lib.om_rng_forced_remaining.argtypes = [ctypes.c_void_p]
    lib.om_rng_forced_remaining.restype = ctypes.c_uint32
    lib._rng_remaining_bound = True


# ---- Stage A: enemy wave scheduling and arrival ----------------------------

def test_wave_scheduled_and_arrives_via_macro_tick(lib, world_factory):
    """R-124-01/02: with forced roll=0.10 (< 0.21) and arrival offset=0.0,
    the wave is scheduled at tick 40 (first evaluation) and the arrival flag
    fires at tick 41 (arrival_tick = 40 + 0 + 1), all automatically through
    om_tactical_tick_to (no direct schedule/check calls)."""
    w = _tactical_world(lib, world_factory)
    lib.om_mission_set_phase(w, 1)  # tactical phase

    # 3 draws: roll=0.10 < 0.21 (scheduled), direction=2 (S), arrival_offset=0.0
    force_draws(lib, w, [0.10, 0.5, 0.0])

    lib.om_tactical_tick_to(w, 41)

    assert lib.om_mission_is_reinforcement_spawned(w) == 1, (
        "R-124-02: arrival flag must be set after om_tactical_tick_to reaches the "
        "wave's arrival tick -- the wiring of om_mission_check_external_reinforcements "
        "inside om_macro_tick is not firing"
    )
    assert lib.om_macro_bus_get_flag(w, b"reinforcements_arrived") == 1, (
        "R-124-02: bus flag 'reinforcements_arrived' must be set when the wave arrives"
    )


def test_wave_not_scheduled_when_roll_above_threshold(lib, world_factory):
    """R-124-01: forced roll=0.30 (>= 0.21) -- wave not scheduled; arrival
    flag stays 0 after stepping past the evaluation tick."""
    w = _tactical_world(lib, world_factory)
    lib.om_mission_set_phase(w, 1)

    force_draws(lib, w, [0.30])

    lib.om_tactical_tick_to(w, 41)

    assert lib.om_mission_is_reinforcement_spawned(w) == 0, (
        "R-124-01: wave not scheduled when roll >= 0.21; flag must stay 0"
    )
    assert lib.om_macro_bus_get_flag(w, b"reinforcements_arrived") == 0


def test_wave_rolled_exactly_once_per_mission(lib, world_factory):
    """R-124-01 once-per-mission: after the first evaluation the wave_set flag
    prevents a second roll. Two forced draws are loaded; only the first is
    consumed across two evaluation boundaries (40 and 80)."""
    _bind_rng_remaining(lib)
    w = _tactical_world(lib, world_factory)
    lib.om_mission_set_phase(w, 1)

    # load 2 draws; only the first (the roll) should be consumed at tick 40
    force_draws(lib, w, [0.30, 0.10])

    lib.om_tactical_tick_to(w, 81)

    remaining = lib.om_rng_forced_remaining(w)
    assert remaining == 1, (
        "R-124-01 once-per-mission: only 1 draw consumed across 2 evaluation "
        f"intervals (40, 80); {2 - remaining} consumed instead of 1"
    )


def test_wave_not_rolled_in_recon_phase(lib, world_factory):
    """R-124-01: the roll fires only in the tactical phase; phase 0 (recon)
    must not consume any forced draws."""
    _bind_rng_remaining(lib)
    w = _tactical_world(lib, world_factory)
    lib.om_mission_set_phase(w, 0)  # recon phase

    force_draws(lib, w, [0.10])

    lib.om_tactical_tick_to(w, 81)

    remaining = lib.om_rng_forced_remaining(w)
    assert remaining == 1, (
        "R-124-01: no roll in recon phase; forced draw must remain unconsumed"
    )
