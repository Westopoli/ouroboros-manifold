"""ALG-48 Lineage generation (docs/bible/algorithms.md), rules R-059-01..R-059-05 (E-08, S-059).

Isolation: om_lineage_generate_descendants on hand-built lineages. Count formula
n = max(1, floor(living * LINEAGE_FERTILITY_RATE * jump_ticks)); per descendant the draw
order parent, spread roll, (neighbor draw), name, lifespan, driven with forced draws.
Constants are read from csrc/om_constants.h by name.
Unstated: the row says the parent is a uniform draw; with a single living member the C skips
the draw (so the first forced draw is the spread roll), Westley's.
"""
import ctypes
import math

import pytest

from alg_consts import const
from conftest import OmCharacterRecord, OMTier, force_draws, set_edge, set_region

RATE = const("LINEAGE_FERTILITY_RATE")
SPREAD = const("LINEAGE_SPREAD_PROBABILITY")
LMIN = const("LIFESPAN_MIN")
LMAX = const("LIFESPAN_MAX")
N = 5


def expected_n(living, ticks):
    return max(1, math.floor(living * RATE * ticks))


def _members(lib, w, count, region=0, lineage=1):
    lib.om_lineage_create(w, lineage_id=lineage, home_region=region)
    for i in range(count):
        lib.om_character_create(w, character_id=100 + i, lineage_id=lineage, region_idx=region, rank=3,
                                birth_tick=0, lifespan=10_000_000)


def _rec(lib, w, cid):
    r = OmCharacterRecord()
    assert lib.om_character_get_record(w, cid, ctypes.byref(r)) == 0
    return r


def _new_ids(lib, w, before):
    return [lib.om_character_id_at(w, i) for i in range(before, lib.om_character_count(w))]


@pytest.mark.parametrize("living,ticks", [(1, 20), (1, 33), (1, 34), (5, 70), (10, 100), (20, 100), (7, 50)])
def test_ALG_48_descendant_count_formula(lib, world_factory, living, ticks):
    """ALG-48 / R-059-01: n = max(1, floor(living * 0.03 * jump_ticks)) descendants, all appended to the lineage."""
    w = world_factory(n_regions=N)
    _members(lib, w, living)
    before = lib.om_character_count(w)
    got = lib.om_lineage_generate_descendants(w, lineage_id=1, jump_ticks=ticks)
    assert got == expected_n(living, ticks)
    assert lib.om_character_count(w) - before == expected_n(living, ticks)


def test_ALG_48_count_positive_control(lib, world_factory):
    """Positive control: 1 living at 20 ticks floors to 0 but the row says at least 1; an unfloored-at-1 expectation must fail."""
    w = world_factory(n_regions=N)
    _members(lib, w, 1)
    got = lib.om_lineage_generate_descendants(w, lineage_id=1, jump_ticks=20)
    assert math.floor(1 * RATE * 20) == 0
    with pytest.raises(AssertionError):
        assert got == math.floor(1 * RATE * 20)


def test_ALG_48_no_living_member_generates_nothing(lib, world_factory):
    """ALG-48: n counts living members; with none there is no parent and nothing is generated."""
    w = world_factory(n_regions=N)
    _members(lib, w, 1)
    lib.om_character_kill(w, character_id=100, tick=5)
    assert lib.om_lineage_generate_descendants(w, lineage_id=1, jump_ticks=50) == 0


def test_ALG_48_same_region_rank_generation_and_lifespan_draw(lib, world_factory):
    """ALG-48 / R-059-02..04: spread roll >= 0.1 keeps the parent's region; rank lineage_member (3);
    generation = parent + 1; lifespan = LIFESPAN_MIN + floor(d * (MAX - MIN + 1))."""
    for life_draw in (0.0, 0.5, 0.999999):
        w = world_factory(n_regions=N)
        _members(lib, w, 1, region=2)
        lib.om_character_set_generation(w, character_id=100, generation=4)
        before = lib.om_character_count(w)
        force_draws(lib, w, [SPREAD, 0.3, life_draw])  # spread == 0.1 is not < 0.1 -> no spread; name 0.3; lifespan
        assert lib.om_lineage_generate_descendants(w, lineage_id=1, jump_ticks=20) == 1
        (cid,) = _new_ids(lib, w, before)
        r = _rec(lib, w, cid)
        assert r.region == 2 and r.rank == 3 and r.generation == 5 and r.parent_id == 100
        assert r.lineage_id == 1 and r.birth_tick == 0
        assert r.lifespan == LMIN + int(life_draw * (LMAX - LMIN + 1))


def test_ALG_48_spread_picks_uniformly_among_inhabited_neighbors(lib, world_factory):
    """ALG-48 / R-059-03: spread roll < 0.1 -> uniform draw among the parent's inhabited neighbors (all edge types).
    Region 0 neighbours 1, 2, 3; region 2 is empty (population 0) so the draw is over [1, 3]."""
    for nd, expected_region in ((0.0, 1), (0.49, 1), (0.5, 3), (0.999999, 3)):
        w = world_factory(n_regions=N)
        for nb in (1, 2, 3):
            set_edge(lib, w, 0, nb)
        for idx, pop in ((0, 50.0), (1, 50.0), (2, 0.0), (3, 50.0), (4, 50.0)):
            set_region(lib, w, idx, tier=OMTier.HOME, military=10.0, economy=10.0, tension=10.0, population=pop, faction_id=0)
        _members(lib, w, 1, region=0)
        before = lib.om_character_count(w)
        force_draws(lib, w, [SPREAD - 1e-9, nd, 0.5, 0.5])  # spread, neighbor, name, lifespan
        lib.om_lineage_generate_descendants(w, lineage_id=1, jump_ticks=20)
        (cid,) = _new_ids(lib, w, before)
        assert _rec(lib, w, cid).region == expected_region, f"neighbor draw {nd}"


def test_ALG_48_spread_with_no_inhabited_neighbor_keeps_parent_region(lib, world_factory):
    """ALG-48: spread roll fires but the neighbor set is empty -> the parent's region."""
    w = world_factory(n_regions=N)
    set_edge(lib, w, 0, 1)
    set_region(lib, w, 1, tier=OMTier.HOME, military=10.0, economy=10.0, tension=10.0, population=0.0, faction_id=0)
    _members(lib, w, 1, region=0)
    before = lib.om_character_count(w)
    force_draws(lib, w, [0.0, 0.5, 0.5])
    lib.om_lineage_generate_descendants(w, lineage_id=1, jump_ticks=20)
    (cid,) = _new_ids(lib, w, before)
    assert _rec(lib, w, cid).region == 0


def test_ALG_48_parent_is_a_uniform_draw_among_living_members(lib, world_factory):
    """ALG-48 / R-059-02: with k living members the parent is member floor(d * k) in table order; the per-descendant
    draw order is parent, spread, name, lifespan. 4 living, ticks 34 -> n = floor(4*0.03*34) = 4 descendants."""
    w = world_factory(n_regions=N)
    _members(lib, w, 4)
    assert expected_n(4, 34) == 4
    before = lib.om_character_count(w)
    parent_draws = [0.0, 0.3, 0.6, 0.999999]  # members 100, 101, 102, 103
    seq = []
    for pd in parent_draws:
        seq += [pd, 0.9, 0.5, 0.5]  # parent, spread (no spread), name, lifespan
    force_draws(lib, w, seq)
    assert lib.om_lineage_generate_descendants(w, lineage_id=1, jump_ticks=34) == 4
    parents = [_rec(lib, w, c).parent_id for c in _new_ids(lib, w, before)]
    assert parents == [100, 101, 102, 103]
