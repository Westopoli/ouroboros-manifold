"""B5 (mission-plays plan): the scroll a time jump builds never holds more than
2 entries of one category (R-065-05/06; the cap wins over the 5-entry minimum,
Q-065-01 ruling 2026-10-01). C-level, seeded world.
"""
import ctypes
from collections import Counter

from conftest import (
    OMTier,
    OmChronicleEntry,
    load_launch_events,
    queue_external,
    set_owner,
    set_region,
    template_id,
)


def test_R_065_05_a_busy_jump_never_shows_three_entries_of_one_category(lib, world_factory):
    """Given a jump where the same event template fires in every region, When the scroll is built, Then no category has more than 2 entries."""
    w = world_factory(n_regions=6, seed=7)
    for r in range(6):
        set_region(lib, w, r, tier=OMTier.HOME, military=50.0, economy=50.0, tension=50.0, population=50.0)
        set_owner(lib, w, r, 0, held_since=-1)
    load_launch_events(lib, w)
    tid = template_id(lib, w, "Border Incursion")
    for r in range(6):
        assert queue_external(lib, w, r, tid, due_tick=3 + r, probability=1.0) > 0

    assert lib.om_time_jump_run(w, 30, None) == 0

    n = lib.om_chronicle_entry_count(w)
    assert n >= 3, "fixture check: the jump must produce a scroll to cap"
    cats = Counter()
    for i in range(n):
        e = OmChronicleEntry()
        if lib.om_chronicle_entry_get(w, i, ctypes.byref(e)) == 1:
            cats[e.category] += 1
    assert cats and max(cats.values()) <= 2, dict(cats)
