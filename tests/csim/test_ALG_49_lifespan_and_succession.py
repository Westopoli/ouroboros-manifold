"""ALG-49 Lifespan and succession (docs/bible/algorithms.md), rules R-060-01..R-060-05 (E-08, S-060).

Isolation: lifespan roll at creation, om_process_natural_deaths at a hand-chosen tick,
successor placement, name-reuse cooldown, event attachment tier. Constants are read from
csrc/om_constants.h by name.
Unstated: the row's "faction's first region" is taken literally as the faction's lowest-index
owned region (the test that reads it that way is the one to look at if it is red), Westley's.
"""
import ctypes

import pytest

from alg_consts import const
from conftest import OmCharacterRecord, force_draws, set_owner

LMIN = const("LIFESPAN_MIN")
LMAX = const("LIFESPAN_MAX")
COOL = const("NAME_REUSE_COOLDOWN_TICKS")
COOL_MAIN = const("NAME_REUSE_COOLDOWN_TICKS_MAIN")
ATTACH = const("CHARACTER_ATTACHMENT_TIER_THRESHOLD")
SUPREME, REGIONAL, MEMBER = 0, 1, 3
ACTIVE, HISTORICAL = 0, 1


def _rec(lib, w, cid):
    r = OmCharacterRecord()
    assert lib.om_character_get_record(w, cid, ctypes.byref(r)) == 0
    return r


@pytest.mark.parametrize("draw", [0.0, 0.25, 0.5, 0.999999])
def test_ALG_49_lifespan_is_randint_min_max_at_creation(lib, world_factory, draw):
    """ALG-49 / R-060-02: lifespan = randint(LIFESPAN_MIN, LIFESPAN_MAX) at creation; draws are
    [name, lifespan] in om_character_create_random order (name first, then the lifespan roll
    is the first draw in the C; the forced list gives both the same value to stay order-proof)."""
    w = world_factory(n_regions=2)
    force_draws(lib, w, [draw, draw])
    cid = lib.om_character_create_random(w, faction_id=0, region_idx=0)
    assert _rec(lib, w, cid).lifespan == LMIN + int(draw * (LMAX - LMIN + 1))


def test_ALG_49_lifespan_positive_control(lib, world_factory):
    """Positive control: draw 0.999999 lands on LIFESPAN_MAX; an exclusive-upper-bound expectation must fail."""
    w = world_factory(n_regions=2)
    force_draws(lib, w, [0.999999, 0.999999])
    cid = lib.om_character_create_random(w, faction_id=0, region_idx=0)
    got = _rec(lib, w, cid).lifespan
    assert got == LMAX
    with pytest.raises(AssertionError):
        assert got == LMAX - 1


def test_ALG_49_death_exactly_when_age_reaches_lifespan(lib, world_factory):
    """ALG-49: tick - born >= lifespan -> historical, death_tick = tick; one tick short stays active."""
    w = world_factory(n_regions=2)
    cid = lib.om_character_create(w, character_id=50, lineage_id=1, region_idx=0, rank=MEMBER, birth_tick=10, lifespan=200)
    lib.om_process_natural_deaths(w, tick=10 + 200 - 1)
    assert _rec(lib, w, 50).status == ACTIVE
    lib.om_process_natural_deaths(w, tick=10 + 200)
    r = _rec(lib, w, 50)
    assert (r.status, r.death_tick) == (HISTORICAL, 210)


def test_ALG_49_regional_commander_succeeded_in_region_if_still_owned(lib, world_factory):
    """ALG-49 / R-060-03: a regional commander is succeeded in its region if the faction still owns it, and not otherwise."""
    w = world_factory(n_regions=3)
    set_owner(lib, w, 0, faction_id=1)
    set_owner(lib, w, 1, faction_id=1)
    lib.om_character_create_with_rank(w, faction_id=1, region_idx=0, rank=REGIONAL, birth_tick=0, lifespan=150)
    lib.om_character_create_with_rank(w, faction_id=1, region_idx=1, rank=REGIONAL, birth_tick=0, lifespan=150)
    lib.om_region_assign_regional_commander(w, region_idx=0, faction_id=1)
    lib.om_region_assign_regional_commander(w, region_idx=1, faction_id=1)
    old0 = lib.om_region_regional_commander(w, region_idx=0)
    old1 = lib.om_region_regional_commander(w, region_idx=1)
    set_owner(lib, w, 1, faction_id=2)  # region 1 lost before the deaths are processed
    lib.om_world_set_strategic_tick(w, LMAX + 1)  # successors are born at the world tick, as in a jump end
    lib.om_process_natural_deaths(w, tick=LMAX + 1)
    new0 = lib.om_region_regional_commander(w, region_idx=0)
    assert new0 != old0 and _rec(lib, w, new0).status == ACTIVE and _rec(lib, w, new0).region == 0
    assert lib.om_region_regional_commander(w, region_idx=1) == old1  # not replaced: no longer owned


def test_ALG_49_supreme_commander_succeeded_in_factions_first_region(lib, world_factory):
    """ALG-49 / R-060-03: a supreme commander is succeeded in the faction's first region.
    Faction 1 owns regions 0 and 1; its supreme commander sits in region 1; the row puts the successor in region 0."""
    w = world_factory(n_regions=3)
    set_owner(lib, w, 0, faction_id=1)
    set_owner(lib, w, 1, faction_id=1)
    lib.om_character_create_with_rank(w, faction_id=1, region_idx=1, rank=SUPREME, birth_tick=0, lifespan=150)
    old = lib.om_faction_supreme_commander(w, faction_id=1)
    lib.om_world_set_strategic_tick(w, LMAX + 1)  # successors are born at the world tick, as in a jump end
    lib.om_process_natural_deaths(w, tick=LMAX + 1)
    succ = lib.om_faction_supreme_commander(w, faction_id=1)
    r = _rec(lib, w, succ)
    assert succ != old and r.rank == SUPREME and r.faction == 1 and r.status == ACTIVE
    assert r.region == 0


def test_ALG_49_successor_gets_a_fresh_lifespan_in_range(lib, world_factory):
    """ALG-49 / R-060-03: the successor's lifespan is in [LIFESPAN_MIN, LIFESPAN_MAX]."""
    w = world_factory(n_regions=2)
    set_owner(lib, w, 0, faction_id=1)
    lib.om_character_create_with_rank(w, faction_id=1, region_idx=0, rank=SUPREME, birth_tick=0, lifespan=LMIN)
    lib.om_world_set_strategic_tick(w, LMIN)
    lib.om_process_natural_deaths(w, tick=LMIN)
    r = _rec(lib, w, lib.om_faction_supreme_commander(w, faction_id=1))
    assert LMIN <= r.lifespan <= LMAX


def test_ALG_49_name_reuse_cooldown_ordinary_and_main(lib, world_factory):
    """ALG-49 / R-060-02: the name returns to the pool after NAME_REUSE_COOLDOWN_TICKS; 4500 for a main character."""
    w = world_factory(n_regions=2)
    lib.om_character_create(w, character_id=60, lineage_id=1, region_idx=0, rank=MEMBER, birth_tick=0, lifespan=200)
    lib.om_character_create(w, character_id=61, lineage_id=1, region_idx=0, rank=MEMBER, birth_tick=0, lifespan=200)
    lib.om_character_selector_confirm_commander(w, character_id=61)
    assert lib.om_character_name_reuse_cooldown(w, character_id=60) == COOL
    assert lib.om_character_name_reuse_cooldown(w, character_id=61) == COOL_MAIN


def test_ALG_49_event_attachment_threshold(lib, world_factory):
    """ALG-49 / R-060-05: events of tier >= CHARACTER_ATTACHMENT_TIER_THRESHOLD attach the region's characters; below it they do not."""
    w = world_factory(n_regions=2)
    cid = lib.om_character_create_with_rank(w, faction_id=0, region_idx=0, rank=REGIONAL, birth_tick=0, lifespan=200)
    low = lib.om_event_fire_manual(w, region_idx=0, tier=ATTACH - 1)
    high = lib.om_event_fire_manual(w, region_idx=0, tier=ATTACH)
    assert lib.om_event_attached_character_count(w, low) == 0
    assert lib.om_event_attached_character_count(w, high) >= 1
    assert lib.om_event_get_attached_character(w, high, 0) == cid
