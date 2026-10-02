"""A81 (docs/northstar/plans/2026-10-01-architect-rulings-2.md): events cover every region.

csrc/events.c sizes its per-region tables by OM_EVT_MAX_REGIONS (64) while OM_MAX_REGIONS is
512, and every events loop stops at 64. The tests below ask the library, on a 400-region world,
whether an event actually reaches region ids at and above 64. Regions below 64 are the positive
control: the same mechanism must detect an event there, so a red result at 64+ is the cap and
not a broken probe. Related: E-04 rules R-026-01 (a crossed line starts a crisis) and
R-030-02 (external firing); see also the save round trip tests at the bottom (state size at
high region ids).
"""
import ctypes

import pytest

from conftest import (
    OMField,
    OMTier,
    isolate_events,
    load_launch_events,
    queue_external,
    read_event_delta,
    read_events,
    set_region,
    template_id,
    zero_all_noise,
)

N_REGIONS = 400
TRIGGER_TEMPLATE = "Diplomatic Incident"  # ABOVE tension 35, no cooldown, fires from a crossed line
SPAWN_TEMPLATE = "Border Incursion"       # no trigger: fires only when queued
HIGH_IDS = [64, 65, 200, 399]
CONTROL_IDS = [0, 1, 63]


def _flat_world(lib, world_factory, templates):
    w = world_factory(n_regions=N_REGIONS, seed=7)
    isolate_events(lib, w)
    load_launch_events(lib, w)  # the full library: om_events_load rejects a subset whose spawns dangle
    for r in range(N_REGIONS):
        set_region(lib, w, r, tier=OMTier.HOME, military=40.0, economy=45.0, tension=0.0, population=45.0)
    zero_all_noise(lib, w)
    return w


def _prime_then_cross(lib, w, regions, ticks=6):
    """R-026-01 is a rising edge: the grace period (3 ticks) primes the unbreached state,
    then the fields are raised across the line and the world runs on."""
    for _ in range(3):
        lib.om_world_step(w)
    for r in regions:
        set_region(lib, w, r, tier=OMTier.HOME, military=40.0, economy=45.0, tension=60.0, population=45.0)
    return _run_collect(lib, w, ticks)


def _run_collect(lib, w, ticks):
    seen = []
    for _ in range(ticks):
        lib.om_world_step(w)
        seen.extend(read_events(lib, w))
    return seen


@pytest.mark.parametrize("region", CONTROL_IDS + HIGH_IDS)
def test_R_026_01_a_crossed_line_fires_on_this_region(lib, world_factory, region):
    """Given a 400-region world where only this region's tension is above the
    Diplomatic Incident threshold, When the world runs past the grace period, Then
    exactly this region fires it. Ids 0, 1, 63 are the positive control (below the
    cap); 64 and up are what A81 is about."""
    w = _flat_world(lib, world_factory, [TRIGGER_TEMPLATE])
    tid = template_id(lib, w, TRIGGER_TEMPLATE)
    fired = [e for e in _prime_then_cross(lib, w, [region]) if e.template_id == tid]

    assert fired, f"no {TRIGGER_TEMPLATE} fired anywhere; region {region} never reached"
    assert {e.region_idx for e in fired} == {region}


@pytest.mark.parametrize("region", CONTROL_IDS + HIGH_IDS)
def test_R_030_02_a_queued_event_fires_on_this_region(lib, world_factory, region):
    """Given an external spawn queued on this region of a 400-region world, When its
    due tick resolves, Then it fires on this region. Control ids below 64 prove the
    probe sees an event when one is there."""
    w = _flat_world(lib, world_factory, [SPAWN_TEMPLATE])
    tid = template_id(lib, w, SPAWN_TEMPLATE)
    for _ in range(4):
        lib.om_world_step(w)

    tag = queue_external(lib, w, region_idx=region, tid=tid, due_tick=5, probability=1.0)
    lib.om_world_step(w)  # tick 5
    fired = [e for e in read_events(lib, w) if e.template_id == tid]

    assert tag >= 0, f"queue_external refused region {region}"
    assert [e.region_idx for e in fired] == [region]


@pytest.mark.parametrize("region", CONTROL_IDS + HIGH_IDS)
def test_R_026_06_the_applied_event_delta_is_reported_for_this_region(lib, world_factory, region):
    """Given an event fired on this region, Then om_region_event_delta reports a nonzero
    applied sum for it (R-026-06: a once-applied sum per field). Control below 64."""
    w = _flat_world(lib, world_factory, [SPAWN_TEMPLATE])
    tid = template_id(lib, w, SPAWN_TEMPLATE)
    for _ in range(4):
        lib.om_world_step(w)
    queue_external(lib, w, region_idx=region, tid=tid, due_tick=5, probability=1.0)
    lib.om_world_step(w)

    rc, delta = read_event_delta(lib, w, region)

    assert rc == 0
    assert any(d != 0.0 for d in delta), f"no applied delta on region {region}: {delta}"


def test_R_026_01_the_boundary_regions_63_and_64_both_fire_in_one_run(lib, world_factory):
    """Given tension above threshold on regions 63 and 64 together, When the world runs,
    Then both fire Diplomatic Incident: the cap must not split a pair of neighbours."""
    w = _flat_world(lib, world_factory, [TRIGGER_TEMPLATE])
    tid = template_id(lib, w, TRIGGER_TEMPLATE)
    fired = [e for e in _prime_then_cross(lib, w, [63, 64]) if e.template_id == tid]

    assert {e.region_idx for e in fired} == {63, 64}


def test_R_026_01_noise_offsets_are_stored_for_a_high_region(lib, world_factory):
    """Given a noise offset set on region 200, Then it reads back (set/get round trip);
    region 3 is the control."""
    w = _flat_world(lib, world_factory, [TRIGGER_TEMPLATE])
    tid = template_id(lib, w, TRIGGER_TEMPLATE)
    for r in (3, 200):
        lib.om_event_set_noise(w, r, tid, 1.25)
    lib.om_event_noise.restype = ctypes.c_double

    assert lib.om_event_noise(w, 3, tid) == 1.25
    assert lib.om_event_noise(w, 200, tid) == 1.25


# ---- save and restore of the events state at high region ids ----

def _bind_save(lib):
    if getattr(lib, "_a81_save_bound", False):
        return
    V, P = ctypes.c_void_p, ctypes.POINTER
    lib.om_save_state_size.argtypes = [V]
    lib.om_save_state_size.restype = ctypes.c_uint32
    lib.om_save_state_write.argtypes = [V, P(ctypes.c_uint8), ctypes.c_uint32]
    lib.om_save_state_write.restype = None
    lib.om_load_state_read.argtypes = [V, P(ctypes.c_uint8), ctypes.c_uint32]
    lib.om_load_state_read.restype = ctypes.c_int
    lib.om_event_last_fired.restype = ctypes.c_int64
    lib.om_event_noise.restype = ctypes.c_double
    lib._a81_save_bound = True


def _save(lib, w):
    _bind_save(lib)
    size = lib.om_save_state_size(w)
    buf = (ctypes.c_uint8 * size)()
    lib.om_save_state_write(w, buf, size)
    return buf, size


def test_R_111_01_noise_at_a_high_region_survives_a_save_round_trip(lib, world_factory):
    """Given a noise offset on region 200 (control: region 3), When the world is saved and
    loaded into a fresh world of the same size, Then both offsets are restored."""
    w = _flat_world(lib, world_factory, [TRIGGER_TEMPLATE])
    tid = template_id(lib, w, TRIGGER_TEMPLATE)
    for r in (3, 200):
        lib.om_event_set_noise(w, r, tid, 2.5)
    buf, size = _save(lib, w)

    w2 = world_factory(n_regions=N_REGIONS, seed=7)
    isolate_events(lib, w2)
    assert lib.om_load_state_read(w2, buf, size) == 0

    assert lib.om_event_noise(w2, 3, tid) == 2.5
    assert lib.om_event_noise(w2, 200, tid) == 2.5


def test_R_111_01_last_fired_at_a_high_region_survives_a_save_round_trip(lib, world_factory):
    """Given an event fired on region 200 (control: region 3) at tick 5, When saved and loaded,
    Then om_event_last_fired reports tick 5 for each on the restored world."""
    w = _flat_world(lib, world_factory, [SPAWN_TEMPLATE])
    tid = template_id(lib, w, SPAWN_TEMPLATE)
    for _ in range(4):
        lib.om_world_step(w)
    for r in (3, 200):
        queue_external(lib, w, region_idx=r, tid=tid, due_tick=5, probability=1.0)
    lib.om_world_step(w)
    _bind_save(lib)
    before = {r: lib.om_event_last_fired(w, r, tid) for r in (3, 200)}
    buf, size = _save(lib, w)

    w2 = world_factory(n_regions=N_REGIONS, seed=7)
    isolate_events(lib, w2)
    assert lib.om_load_state_read(w2, buf, size) == 0

    assert before[3] == 5
    assert before[200] == 5, "the live world already lost the firing on region 200"
    assert lib.om_event_last_fired(w2, 3, tid) == 5
    assert lib.om_event_last_fired(w2, 200, tid) == 5


def test_R_111_01_a_save_with_events_used_loads_back_byte_identically(lib, world_factory):
    """Given a 400-region world with events fired on high regions, When saved, loaded and
    saved again, Then the second save equals the first byte for byte (nothing in the events
    state is dropped or invented across the round trip)."""
    w = _flat_world(lib, world_factory, [TRIGGER_TEMPLATE])
    _prime_then_cross(lib, w, [10, 100, 300])
    buf, size = _save(lib, w)

    w2 = world_factory(n_regions=N_REGIONS, seed=7)
    isolate_events(lib, w2)
    assert lib.om_load_state_read(w2, buf, size) == 0
    buf2, size2 = _save(lib, w2)

    assert size2 == size
    assert bytes(buf2) == bytes(buf)
