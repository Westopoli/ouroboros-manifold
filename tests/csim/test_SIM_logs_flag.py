"""SIM-LOGS, the faction-shift flag: generational.c's regional cluster is classified with the flag set when the
log holds, inside the jump's own tick range, a conquest of any kind, a revolt-set event or an event that creates a
faction, in a region the jump also fired an event in (spec rev 4, "Faction shift", R-067-05).

Fixture: the B5 world (test_E09_B5_chain_tags.py: four regions, seed 7, Border Incursion queued in region 1 for
tick 3, a 30-tick jump), plus faction 1 so a conquest can name it. The region keeps its owner at both ends of the
jump (the only owner is faction 0), so it reaches the categorizer call. The conquest entries are spliced into the
saved log block before the jump, dated inside the jump's range (ticks 1 to 30): they stand for a conquest and a
retaking that the jump's own steps would append. The splice helpers are test_SIM_logs_readers.py's.

Decision the spec leaves to the tests: the observable is the chapter's scroll clusters (om_chronicle_get_cluster):
a REGIONAL cluster (type 3) of category 20 (regional_faction_shift) in region 1. Today's call site adds a regional
event only for growth or decline (generational.c:2082-2083), so a shift category also needs that condition to admit
CAT_REGIONAL_FACTION_SHIFT; the spec says the class "appears", which needs it. The builder should say so in the report.

RED today: no log block in the save (the splice finds no header).
"""
import ctypes

import pytest

from conftest import (
    OMArchetype,
    OMFeature,
    OMTier,
    OmChronicleCluster,
    load_launch_events,
    queue_external,
    set_faction,
    set_owner,
    set_region,
    template_id,
)
from test_SIM_logs_readers import with_logs
from test_SIM_logs_ring import (
    OM_CONQ_ABSORPTION,
    OM_CONQ_ATTACK,
    OM_CONQ_MISSION,
    OM_CONQ_REVERSION,
    OM_CONQ_REVOLT,
)

CTYPE_REGIONAL = 3
CAT_REGIONAL_FACTION_SHIFT = 20
JUMP = 30
REGION = 1


def _fixture(lib, world_factory):
    w = world_factory(n_regions=4, seed=7)
    lib.om_world_set_feature(w, OMFeature.EVENTS, 1)
    set_faction(lib, w, 0, OMArchetype.DEFAULT, budget=0.0)
    set_faction(lib, w, 1, OMArchetype.DEFAULT, budget=0.0)
    for r in range(4):
        set_region(lib, w, r, tier=OMTier.HOME, military=50.0, economy=50.0, tension=50.0, population=50.0)
        set_owner(lib, w, r, 0, held_since=-1)
    load_launch_events(lib, w)
    assert queue_external(lib, w, REGION, template_id(lib, w, "Border Incursion"), due_tick=3, probability=1.0) > 0
    return w


def _clusters(lib, w):
    out = []
    for i in range(lib.om_chronicle_entry_count(w)):
        c = OmChronicleCluster()
        assert lib.om_chronicle_get_cluster(w, i, ctypes.byref(c)) == 1
        out.append(c)
    return out


def _shifts(lib, w):
    return [c for c in _clusters(lib, w) if c.type == CTYPE_REGIONAL and c.category == CAT_REGIONAL_FACTION_SHIFT
            and c.region == REGION]


def _jump(lib, w):
    lib.om_world_set_feature(w, OMFeature.EVENTS, 1)
    assert lib.om_time_jump_run(w, JUMP, None) == 0
    assert lib.om_region_owner(w, REGION) == 0, "fixture: the owner is the same at both ends of the jump"


def _retaken(kind, first=15, second=18):
    """Region 1 conquered by faction 1, then retaken by faction 0."""
    return [(first, REGION, 0, 1, kind), (second, REGION, 1, 0, kind)]


def test_no_log_no_shift_CONTROL(lib, world_factory):
    """Positive control, green today: the fixture fires an event in region 1 and the jump classifies it as something
    other than a faction shift, so the shift tests below fail for the log and not for the fixture."""
    w = _fixture(lib, world_factory)
    _jump(lib, w)
    assert lib.om_chain_counter(w) > 0, "fixture: the Border Incursion fired and tagged a chain"
    assert [c for c in _clusters(lib, w) if c.region == REGION and c.type == CTYPE_REGIONAL], \
        "fixture: the region reached the regional categorizer (this fails if the chapter has no regional entry for it)"
    assert _shifts(lib, w) == []


@pytest.mark.parametrize("kind", [OM_CONQ_ATTACK, OM_CONQ_MISSION, OM_CONQ_REVOLT, OM_CONQ_REVERSION, OM_CONQ_ABSORPTION],
                         ids=["attack", "mission", "revolt", "reversion", "absorption"])
def test_conquered_and_retaken_within_the_jump_with_an_event_is_a_faction_shift(lib, world_factory, kind):
    w = with_logs(lib, world_factory, _fixture(lib, world_factory), 4, seed=7, conquests=_retaken(kind))
    _jump(lib, w)
    assert len(_shifts(lib, w)) == 1


def test_the_flag_reads_the_jump_range_not_the_mission_window(lib, world_factory):
    """window_start 20 sits between the two entries (15, 18 are before it); the flag still sets."""
    w = with_logs(lib, world_factory, _fixture(lib, world_factory), 4, seed=7, conquests=_retaken(OM_CONQ_ATTACK),
                  window_start=20)
    _jump(lib, w)
    assert len(_shifts(lib, w)) == 1


def test_a_conquest_outside_the_jump_is_not_a_shift(lib, world_factory):
    """Entries dated at tick 0, before the jump's first tick (1): the region changed nothing inside the jump."""
    w = with_logs(lib, world_factory, _fixture(lib, world_factory), 4, seed=7, conquests=_retaken(OM_CONQ_ATTACK, 0, 0))
    _jump(lib, w)
    assert _shifts(lib, w) == []


def test_a_conquest_in_another_region_is_not_this_regions_shift(lib, world_factory):
    w = with_logs(lib, world_factory, _fixture(lib, world_factory), 4, seed=7,
                  conquests=[(15, 3, 0, 1, OM_CONQ_ATTACK), (18, 3, 1, 0, OM_CONQ_ATTACK)])
    _jump(lib, w)
    assert _shifts(lib, w) == []


def test_a_revolt_set_event_in_the_log_is_a_faction_shift(lib, world_factory):
    """R-067-05: a revolt-set event inside the jump's range sets the flag with no conquest."""
    w = with_logs(lib, world_factory, _fixture(lib, world_factory), 4, seed=7, events=[(15, REGION, 3, 0, 0)])
    _jump(lib, w)
    assert len(_shifts(lib, w)) == 1


def test_an_event_that_creates_a_faction_is_a_faction_shift(lib, world_factory):
    w = with_logs(lib, world_factory, _fixture(lib, world_factory), 4, seed=7, events=[(15, REGION, 0, 0, 1)])
    _jump(lib, w)
    assert len(_shifts(lib, w)) == 1
