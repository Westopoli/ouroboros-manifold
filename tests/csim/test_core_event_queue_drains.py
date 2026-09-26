"""Core invariant: event queue drains under the launch feature set.

Verifies the defect fixed by EVT-1: om_step_events returned early when no
template library was loaded, so om_step_admin_revolts entries (template_id
OM_EVT_ADMIN_SEPARATIST=101, written directly to w->event_queue) accumulated
to OM_EVT_QUEUE_CAP=64 by ~tick 220 for seed 12345.  Once full, every
om_event_queue_external call returned -1 and blocked external-queued events.

Two assertions:

1. Queue depth never reaches cap (64) over 500 ticks.
   RED on main (queue fills to 64 at tick ~220), GREEN after fix (drain loop
   in om_step_events removes due entries even without a template library).

2. At least one event fires in 500 ticks when the launch library is loaded.
   Always GREEN: with the launch library om_step_events takes its normal path
   and threshold triggers fire immediately.  This assertion guards that the
   fix does not silently break normal event flow.  Both seeds must fire; a
   seed that does not is a regression.

Both parametrised over two seeds to guard against seed-specific flukes.
"""
import pytest

from conftest import (
    OMFeature,
    gen_set_faction_count,
    gen_set_region_range,
    generate,
    load_launch_events,
    read_event_queue,
    read_events,
)

_OM_EVT_QUEUE_CAP = 64  # OM_EVT_QUEUE_CAP (csrc/events.c); never widen


@pytest.mark.parametrize("seed", [12345, 99999])
def test_core_event_queue_drains_before_cap(lib, world_factory, seed):
    """R-EVT-1-01: queue depth stays below cap for 500 ticks under launch features."""
    w = world_factory(n_regions=0, seed=seed)
    gen_set_faction_count(lib, w, 50)
    gen_set_region_range(lib, w, 100, 150)
    assert generate(lib, w) == 1

    for _ in range(500):
        lib.om_world_step(w)
        depth = len(read_event_queue(lib, w))
        assert depth < _OM_EVT_QUEUE_CAP, (
            f"seed {seed}: queue saturated at {depth} == cap"
        )


@pytest.mark.parametrize("seed", [12345, 99999])
def test_core_event_queue_events_observable(lib, world_factory, seed):
    """R-EVT-1-02: at least one event fires in 500 ticks with the launch library loaded.

    Guards that the EVT-1 fix does not break normal event flow: with the
    launch library loaded om_step_events runs its full path, threshold and
    probability triggers fire, and om_tick_events returns records.
    """
    w = world_factory(n_regions=0, seed=seed)
    gen_set_faction_count(lib, w, 50)
    gen_set_region_range(lib, w, 100, 150)
    assert generate(lib, w) == 1
    load_launch_events(lib, w)

    total_events = 0
    for _ in range(500):
        lib.om_world_step(w)
        total_events += len(read_events(lib, w))

    assert total_events > 0, (
        f"seed {seed}: no events fired in 500 ticks with launch library loaded"
    )
