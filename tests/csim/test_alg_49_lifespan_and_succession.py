"""ALG-49 Lifespan and succession (docs/bible/algorithms.md), proving R-060-02, R-060-03, R-060-04, R-060-05 (S-060, E-08).

lifespan = randint(150, 350) at creation. At jump end every active character with tick - born >=
lifespan becomes historical with death_tick = tick; its name returns to the pool after 500 ticks
(4500 for a main character); a supreme commander is succeeded in the faction's first region and a
regional commander in its region if still owned. Events of significance tier >= 3 attach the
region's characters. Expectations are computed here from those lines.
"""
import ctypes
import math

from conftest import OMTier, force_draws, set_region

SUPREME, REGIONAL, GARRISON, LINEAGE_MEMBER = 0, 1, 2, 3
ACTIVE, HISTORICAL = 0, 1
LIFE_MIN, LIFE_MAX = 150, 350
COOLDOWN, COOLDOWN_MAIN = 500, 4500
TIER_THRESHOLD = 3


class _Rec(ctypes.Structure):
    _fields_ = [
        ("id", ctypes.c_uint32), ("name", ctypes.c_char * 32), ("faction", ctypes.c_int32),
        ("region", ctypes.c_uint32), ("rank", ctypes.c_uint32), ("birth_tick", ctypes.c_uint64),
        ("lifespan", ctypes.c_uint32), ("status", ctypes.c_uint32), ("death_tick", ctypes.c_uint64),
        ("lineage_id", ctypes.c_uint32), ("parent_id", ctypes.c_uint32), ("generation", ctypes.c_uint32),
        ("n_rival_tags", ctypes.c_uint32), ("n_children", ctypes.c_uint32),
    ]


def _record(lib, w, cid):
    rec = _Rec()
    assert lib.om_character_get_record(w, cid, ctypes.byref(rec)) == 0
    return rec


def _own(lib, w, idx, faction):
    set_region(lib, w, idx, tier=OMTier.HOME, military=50.0, economy=50.0, tension=20.0, population=50.0, faction_id=faction)


def test_control_ALG_49_off_by_one_and_wrong_range_are_detected(lib, world_factory):
    """Positive control: a character one tick short of its lifespan is still active, so an expectation of 'dead at lifespan - 1' (or a lifespan range of [150, 349]) disagrees with the C result."""
    w = world_factory(n_regions=1)
    cid = lib.om_character_create_with_rank(w, faction_id=0, region_idx=0, rank=LINEAGE_MEMBER, birth_tick=100, lifespan=200)
    lib.om_process_natural_deaths(w, tick=299)
    assert _record(lib, w, cid).status == ACTIVE
    force_draws(lib, w, [0.999999, 0.999999])
    top = lib.om_character_create_random(w, faction_id=0, region_idx=0)
    assert _record(lib, w, top).lifespan == LIFE_MAX != 349


def test_ALG_49_lifespan_is_a_uniform_integer_150_to_350(lib, world_factory):
    """ALG-49 / R-060-02: for a pinned draw d the lifespan is 150 + floor(d * 201); d = 0 gives 150 and d just below 1 gives 350 (both ends reachable, 201 values)."""
    seen = set()
    for i in range(0, 201):
        d = (i + 0.5) / 201.0  # the middle of each of the 201 equal bins
        w = world_factory(n_regions=1)
        force_draws(lib, w, [d, d])  # lifespan and name consume one draw each; either order reads the same d
        cid = lib.om_character_create_random(w, faction_id=0, region_idx=0)
        life = _record(lib, w, cid).lifespan
        assert life == LIFE_MIN + math.floor(d * (LIFE_MAX - LIFE_MIN + 1)) == LIFE_MIN + i, (i, life)
        seen.add(life)
    assert seen == set(range(LIFE_MIN, LIFE_MAX + 1))


def test_ALG_49_death_exactly_when_age_reaches_lifespan(lib, world_factory):
    """ALG-49 / R-060-03: tick - born >= lifespan; born 100, lifespan 200: active at 299, historical at 300 with death_tick = 300; one already historical keeps its death_tick."""
    w = world_factory(n_regions=1)
    cid = lib.om_character_create_with_rank(w, faction_id=0, region_idx=0, rank=LINEAGE_MEMBER, birth_tick=100, lifespan=200)
    lib.om_process_natural_deaths(w, tick=299)
    assert _record(lib, w, cid).status == ACTIVE
    lib.om_process_natural_deaths(w, tick=300)
    rec = _record(lib, w, cid)
    assert rec.status == HISTORICAL and rec.death_tick == 300
    lib.om_process_natural_deaths(w, tick=400)
    assert _record(lib, w, cid).death_tick == 300


def test_ALG_49_deaths_are_processed_once_at_the_end_of_the_jump(lib, world_factory):
    """ALG-49 and ALG-45 / R-060-04: a jump of 50 ticks holds one death pass, at the end tick (the text of the rule; the register row Q-060-01 says per tick, see findings)."""
    w = world_factory(n_regions=1)
    lib.om_time_jump_run_tracked(w, 50)
    assert lib.om_time_jump_death_pass_count(w) == 1
    assert lib.om_time_jump_death_processing_tick(w) == lib.om_world_strategic_tick(w)


def test_ALG_49_supreme_commander_is_succeeded_in_the_same_faction(lib, world_factory):
    """ALG-49 / R-060-03: a dying supreme commander in its faction's first region is replaced by a new active supreme commander (new id, fresh lifespan in range) in that faction and region."""
    w = world_factory(n_regions=3)
    _own(lib, w, 0, 1)
    old = lib.om_character_create_with_rank(w, faction_id=1, region_idx=0, rank=SUPREME, birth_tick=0, lifespan=150)
    lib.om_process_natural_deaths(w, tick=150)
    new = lib.om_faction_supreme_commander(w, faction_id=1)
    assert new not in (0, old)
    rec = _record(lib, w, new)
    assert rec.status == ACTIVE and rec.rank == SUPREME and rec.faction == 1 and rec.region == 0
    assert LIFE_MIN <= rec.lifespan <= LIFE_MAX
    assert _record(lib, w, old).status == HISTORICAL


def test_ALG_49_supreme_successor_is_placed_in_the_factions_first_region(lib, world_factory):
    """ALG-49: 'a supreme commander is succeeded in the faction's first region'. Faction 2 owns regions 1 and 3 (first region 1); its supreme commander stands in region 3 and dies; the successor must be in region 1. The C code places it in the dead commander's own region (csrc/generational.c om_process_natural_deaths), which R-060-03 ('same faction and region') also says: the two texts disagree when the commander is not in the first region."""
    w = world_factory(n_regions=4)
    _own(lib, w, 1, 2)
    _own(lib, w, 3, 2)
    lib.om_character_create_with_rank(w, faction_id=2, region_idx=3, rank=SUPREME, birth_tick=0, lifespan=150)
    lib.om_process_natural_deaths(w, tick=150)
    succ = _record(lib, w, lib.om_faction_supreme_commander(w, faction_id=2))
    assert succ.rank == SUPREME and succ.status == ACTIVE
    assert succ.region == 1, f"successor in region {succ.region}, the faction's first region is 1"


def test_ALG_49_regional_commander_is_succeeded_only_if_the_region_is_still_owned(lib, world_factory):
    """ALG-49 / R-060-03: a regional commander is succeeded in its region only if its faction still owns the region; after the region changes hands no successor is created."""
    w = world_factory(n_regions=2)
    _own(lib, w, 0, 1)
    _own(lib, w, 1, 1)
    owned = lib.om_character_create_with_rank(w, faction_id=1, region_idx=0, rank=REGIONAL, birth_tick=0, lifespan=150)
    lost = lib.om_character_create_with_rank(w, faction_id=1, region_idx=1, rank=REGIONAL, birth_tick=0, lifespan=150)
    _own(lib, w, 1, 2)  # region 1 now belongs to faction 2
    lib.om_process_natural_deaths(w, tick=150)
    assert lib.om_character_count(w) == 1  # om_character_count counts active characters: only the one successor
    succ = _record(lib, w, lib.om_region_regional_commander(w, region_idx=0))
    assert succ.id != owned and succ.rank == REGIONAL and succ.faction == 1 and succ.region == 0 and succ.status == ACTIVE
    assert _record(lib, w, lost).status == HISTORICAL
    assert lib.om_region_regional_commander(w, region_idx=1) == lost  # no successor for the lost region


def test_ALG_49_name_cooldown_is_500_ticks_and_4500_for_a_main_character(lib, world_factory):
    """ALG-49: a name returns to the pool after 500 ticks, 4500 for a main character (a confirmed commander)."""
    w = world_factory(n_regions=1)
    ordinary = lib.om_character_create_with_rank(w, faction_id=0, region_idx=0, rank=LINEAGE_MEMBER, birth_tick=0, lifespan=200)
    main = lib.om_character_create_with_rank(w, faction_id=0, region_idx=0, rank=LINEAGE_MEMBER, birth_tick=0, lifespan=200)
    lib.om_character_selector_confirm_commander(w, main)
    assert lib.om_character_name_reuse_cooldown(w, ordinary) == COOLDOWN
    assert lib.om_character_name_reuse_cooldown(w, main) == COOLDOWN_MAIN


def test_ALG_49_a_name_in_use_is_out_of_the_pool(lib, world_factory):
    """ALG-49: 'its name returns to the pool after 500 ticks' means a name leaves the pool while its holder lives (and for the cooldown after death). Twelve characters created in one faction must therefore carry twelve different names; the C name draw (csrc/generational.c gen_roll_name) is a plain uniform pick from a 16-name list with no exclusion, and nothing ever consumes om_character_name_reuse_cooldown."""
    w = world_factory(n_regions=1)
    names = []
    for _ in range(12):
        cid = lib.om_character_create_random(w, faction_id=0, region_idx=0)
        names.append(_record(lib, w, cid).name)
    assert len(set(names)) == 12, f"duplicate names among 12 living characters: {sorted(names)}"


def test_ALG_49_tier_three_events_attach_the_regions_characters(lib, world_factory):
    """ALG-49 / R-060-05: an event of tier >= 3 attaches the living characters standing in its region (regional commander, supreme commander there, lineage members); a tier-2 event attaches nobody; characters elsewhere or historical are never attached."""
    w = world_factory(n_regions=3)
    _own(lib, w, 0, 1)
    _own(lib, w, 1, 1)
    supreme = lib.om_character_create_with_rank(w, faction_id=1, region_idx=0, rank=SUPREME, birth_tick=0, lifespan=10_000)
    regional = lib.om_character_create_with_rank(w, faction_id=1, region_idx=0, rank=REGIONAL, birth_tick=0, lifespan=10_000)
    lib.om_lineage_create(w, lineage_id=5, home_region=0)
    member = 900
    lib.om_character_create(w, character_id=member, lineage_id=5, region_idx=0, rank=LINEAGE_MEMBER, birth_tick=0, lifespan=10_000)
    elsewhere = 901
    lib.om_character_create(w, character_id=elsewhere, lineage_id=5, region_idx=1, rank=LINEAGE_MEMBER, birth_tick=0, lifespan=10_000)
    dead = 902
    lib.om_character_create(w, character_id=dead, lineage_id=5, region_idx=0, rank=LINEAGE_MEMBER, birth_tick=0, lifespan=10_000)
    lib.om_character_kill(w, dead, tick=1)
    low = lib.om_event_fire_manual(w, 0, TIER_THRESHOLD - 1)
    assert lib.om_event_attached_character_count(w, low) == 0
    high = lib.om_event_fire_manual(w, 0, TIER_THRESHOLD)
    attached = {lib.om_event_get_attached_character(w, high, k) for k in range(lib.om_event_attached_character_count(w, high))}
    assert {supreme, regional, member} <= attached
    assert elsewhere not in attached and dead not in attached
