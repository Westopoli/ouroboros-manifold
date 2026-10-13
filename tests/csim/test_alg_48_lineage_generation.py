"""ALG-48 Lineage generation (docs/bible/algorithms.md), proving R-059-01 .. R-059-03 (S-059, E-08).

At jump end: n = max(1, floor(living * 0.03 * jump_ticks)) descendants; each: parent = uniform draw
among living members; with probability 0.1 the region is a uniform draw among the parent's
inhabited neighbors (all edge types), else the parent's region; rank lineage_member, generation
parent + 1. Draw order per descendant: parent, spread roll, (neighbor draw), name, lifespan. The
lifespan (ALG-49) is randint(150, 350), i.e. 150 + floor(d * 201) for a uniform draw d.
Expectations are computed here from those lines; draws are pinned with om_rng_force.
"""
import ctypes
import math

from conftest import OMTier, force_draws, set_edge, set_region

RANK_LINEAGE_MEMBER = 3
FERTILITY, SPREAD_P = 0.03, 0.1
LIFE_MIN, LIFE_MAX = 150, 350


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


def _ids(lib, w):
    return [lib.om_character_id_at(w, i) for i in range(lib.om_character_count(w))]


def _lineage(lib, w, members, lineage=1):
    """members: (id, region, faction, generation)."""
    lib.om_lineage_create(w, lineage_id=lineage, home_region=members[0][1])
    for cid, region, faction, gen in members:
        lib.om_character_create(w, character_id=cid, lineage_id=lineage, region_idx=region,
                                rank=RANK_LINEAGE_MEMBER, birth_tick=0, lifespan=10_000_000)
        lib.om_character_set_faction(w, cid, faction_id=faction)
        lib.om_character_set_generation(w, cid, generation=gen)


def _new_descendants(lib, w, before):
    return [_record(lib, w, i) for i in _ids(lib, w) if i not in before]


def _ref_count(living, jump_ticks):
    """The rule as written, evaluated in exact arithmetic: floor(living * 3 * jump_ticks / 100)."""
    return max(1, (living * 3 * jump_ticks) // 100)


def _world_with_neighbors(lib, world_factory):
    """Region 0 (parent) with neighbors 1 and 2 inhabited (population > 0) and 3 empty, all faction 2."""
    w = world_factory(n_regions=4)
    set_region(lib, w, 0, tier=OMTier.HOME, military=50.0, economy=50.0, tension=20.0, population=50.0, faction_id=2)
    set_region(lib, w, 1, tier=OMTier.FRONTIER, military=30.0, economy=30.0, tension=20.0, population=30.0, faction_id=2)
    set_region(lib, w, 2, tier=OMTier.FRONTIER, military=30.0, economy=30.0, tension=20.0, population=40.0, faction_id=2)
    set_region(lib, w, 3, tier=OMTier.EMPTY, military=0.0, economy=0.0, tension=0.0, population=0.0, faction_id=-1)
    for b in (1, 2, 3):
        set_edge(lib, w, 0, b)
    return w


def test_control_ALG_48_wrong_rate_or_order_is_detected(lib, world_factory):
    """Positive control: with 5 living members and a 40-tick jump the rule gives 6; a rate of 0.04 (8) or 0.02 (4) disagrees with the C count, and a draw order that starts with the spread roll puts the spread on a different draw."""
    w = world_factory(n_regions=2)
    _lineage(lib, w, [(i, 0, 0, 0) for i in range(1, 6)])
    n = lib.om_lineage_generate_descendants(w, lineage_id=1, jump_ticks=40)
    assert n == _ref_count(5, 40) == 6
    assert n != max(1, math.floor(5 * 0.04 * 40)) and n != max(1, math.floor(5 * 0.02 * 40))
    # draw order control: forced [parent, spread] = [0.0, 0.5] spreads nobody; [0.5, 0.05] would spread if swapped.
    w2 = _world_with_neighbors(lib, world_factory)
    _lineage(lib, w2, [(1, 0, 2, 0), (2, 0, 2, 0)])
    before = set(_ids(lib, w2))
    force_draws(lib, w2, [0.0, 0.5, 0.0, 0.0, 0.0])
    lib.om_lineage_generate_descendants(w2, lineage_id=1, jump_ticks=20)  # 2 living * 0.03 * 20 = 1.2 -> 1
    assert _new_descendants(lib, w2, before)[0].region == 0


def test_ALG_48_count_floor_of_living_times_rate_times_ticks_with_a_minimum_of_one(lib, world_factory):
    """ALG-48 / R-059-01: n = max(1, floor(living * 0.03 * T)) wherever the product is not an exact integer boundary."""
    for living in (1, 2, 3, 5, 8, 13, 21):
        for ticks in (20, 33, 47, 51, 77, 99, 100):
            if (living * 3 * ticks) % 100 == 0:
                continue  # exact-integer products are the boundary test below
            w = world_factory(n_regions=2)
            _lineage(lib, w, [(i, 0, 0, 0) for i in range(1, living + 1)])
            assert lib.om_lineage_generate_descendants(w, lineage_id=1, jump_ticks=ticks) == _ref_count(living, ticks), (living, ticks)


def test_ALG_48_count_at_exact_integer_products_the_live_jump_length(lib, world_factory):
    """ALG-48 / R-059-01: at the live jump length 50 a lineage of 22 living members gives floor(22 * 0.03 * 50) = floor(33.0) = 33 descendants, and 30 members give 45. Evaluated in IEEE double the product is 32.99999999999999 and 44.99999999999999, so the C count is one short."""
    wrong = []
    for living in (22, 30, 38, 44):
        w = world_factory(n_regions=2)
        _lineage(lib, w, [(i, 0, 0, 0) for i in range(1, living + 1)])
        got = lib.om_lineage_generate_descendants(w, lineage_id=1, jump_ticks=50)
        if got != _ref_count(living, 50):
            wrong.append((living, got, _ref_count(living, 50)))
    assert not wrong, f"(living, C count, rule count): {wrong}"


def test_ALG_48_each_descendant_is_a_lineage_member_one_generation_down_in_the_parents_faction(lib, world_factory):
    """ALG-48 / R-059-02, R-059-03: rank lineage_member, generation parent + 1, parent's faction and lineage, lifespan in [150, 350], active, born at the world tick."""
    w = world_factory(n_regions=2)
    _lineage(lib, w, [(1, 0, 3, 4)])
    before = set(_ids(lib, w))
    n = lib.om_lineage_generate_descendants(w, lineage_id=1, jump_ticks=100)
    kids = _new_descendants(lib, w, before)
    assert n == len(kids) == _ref_count(1, 100) == 3
    for k in kids:
        assert k.rank == RANK_LINEAGE_MEMBER and k.generation == 5 and k.faction == 3
        assert k.lineage_id == 1 and k.parent_id == 1 and k.status == 0
        assert LIFE_MIN <= k.lifespan <= LIFE_MAX and len(k.name) > 0


def test_ALG_48_draw_order_parent_spread_neighbor_name_lifespan(lib, world_factory):
    """ALG-48 / R-059-02: with draws [parent 0.9, spread 0.05, neighbor 0.6, name 0.0, lifespan 0.5], two living members: parent index floor(0.9*2) = 1, spread (0.05 < 0.1), neighbor index floor(0.6*2) = 1 among the two inhabited neighbors (the empty one is excluded), lifespan 150 + floor(0.5*201) = 250."""
    w = _world_with_neighbors(lib, world_factory)
    _lineage(lib, w, [(1, 0, 2, 0), (2, 0, 2, 7)])
    before = set(_ids(lib, w))
    force_draws(lib, w, [0.9, 0.05, 0.6, 0.0, 0.5])
    assert lib.om_lineage_generate_descendants(w, lineage_id=1, jump_ticks=20) == 1
    (kid,) = _new_descendants(lib, w, before)
    assert kid.parent_id == 2 and kid.generation == 8  # parent index 1 is the second living member
    assert kid.region == 2  # inhabited neighbors in id order [1, 2]; index 1 is region 2; region 3 is empty
    assert kid.lifespan == LIFE_MIN + math.floor(0.5 * (LIFE_MAX - LIFE_MIN + 1)) == 250


def test_ALG_48_spread_threshold_is_below_one_tenth_and_no_neighbor_draw_without_spread(lib, world_factory):
    """ALG-48 / R-059-02: a spread roll of 0.099 spreads, 0.1 does not; without a spread the neighbor draw is not consumed (the next draw is the name, then the lifespan 0.5 -> 250)."""
    for roll, spreads in ((0.099, True), (0.1, False), (0.5, False)):
        w = _world_with_neighbors(lib, world_factory)
        _lineage(lib, w, [(1, 0, 2, 0), (2, 0, 2, 0)])
        before = set(_ids(lib, w))
        draws = [0.0, roll, 0.0, 0.0, 0.5] if spreads else [0.0, roll, 0.0, 0.5]
        force_draws(lib, w, draws)
        lib.om_lineage_generate_descendants(w, lineage_id=1, jump_ticks=20)
        (kid,) = _new_descendants(lib, w, before)
        assert (kid.region != 0) == spreads, roll
        assert kid.lifespan == 250, (roll, kid.lifespan)


def test_ALG_48_parent_draw_is_taken_even_for_a_single_living_member(lib, world_factory):
    """ALG-48 / R-059-02: 'Draw order per descendant: parent, spread roll, (neighbor draw), name, lifespan' holds for a lineage of one living member too. Draws [parent 0.99, spread 0.05, neighbor 0.6, name 0.0, lifespan 0.5] must give region 2 (neighbor index floor(0.6*2) = 1) and lifespan 250; the C batch generator skips the parent draw when only one member lives, so every later draw shifts one place."""
    w = _world_with_neighbors(lib, world_factory)
    _lineage(lib, w, [(1, 0, 2, 0)])
    before = set(_ids(lib, w))
    force_draws(lib, w, [0.99, 0.05, 0.6, 0.0, 0.5])
    assert lib.om_lineage_generate_descendants(w, lineage_id=1, jump_ticks=20) == 1
    (kid,) = _new_descendants(lib, w, before)
    assert kid.region == 2 and kid.lifespan == 250, (kid.region, kid.lifespan)
