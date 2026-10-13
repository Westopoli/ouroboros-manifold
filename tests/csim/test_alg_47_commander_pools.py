"""ALG-47 Commander pools (docs/bible/algorithms.md), proving R-058-01 .. R-058-04 (S-058, E-08).

One draw selects the pool: previous-descendant 0.70, nemesis-descendant 0.20, unrelated 0.10; the
search order is the rolled pool then the others in the order previous, nemesis, unrelated.
Previous: lineages played in an earlier chapter with a living member within 2 hops, score =
0.6 * min(chapters_ago, 4)/4 + 0.4 * min(living_nearby, 5)/5, every nearby member carrying its
lineage's score, one weighted draw. Nemesis: living descendants within 2 hops of any character
tagged rival of a previous commander, excluding the rivals, one uniform draw. Unrelated: a new
lineage_member in the mission region's owning faction and a new lineage. Reference values below
come from those lines. 'chapters_ago' is read as the lineage's chapter counter, as the repo rules
(A26, test_E08_S058_previous_pool_chapter_ago.py) and the register do.
"""
import ctypes

from conftest import OmSelectionRecord, OMTier, set_edge, set_region

POOL_PREVIOUS, POOL_NEMESIS, POOL_UNRELATED = 0, 1, 2
REASON_FORCED = 0
RANK_LINEAGE_MEMBER = 3
N = 5


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


def _ref_pool(draw, prev=0.70, nem=0.20):
    if draw < prev:
        return POOL_PREVIOUS
    if draw < prev + nem:
        return POOL_NEMESIS
    return POOL_UNRELATED


def _ref_score(chapters_ago, nearby, gap_w=0.6, dens_w=0.4, gap_peak=4, dens_peak=5):
    return gap_w * min(chapters_ago, gap_peak) / gap_peak + dens_w * min(nearby, dens_peak) / dens_peak


def _complete(lib, w, n=N):
    for a in range(n):
        for b in range(a + 1, n):
            set_edge(lib, w, a, b)


def _lineage(lib, w, lineage, chapters, ids, region=0):
    lib.om_lineage_create(w, lineage_id=lineage, home_region=region)
    lib.om_lineage_set_chapter_count(w, lineage_id=lineage, chapters=chapters)
    for cid in ids:
        lib.om_character_create(w, character_id=cid, lineage_id=lineage, region_idx=region,
                                rank=RANK_LINEAGE_MEMBER, birth_tick=0, lifespan=10_000_000)


def _rival_family(lib, w, region, n_desc, rival_id=500, commander_id=501, first_child=510):
    """A previous commander, a character tagged as its rival, and n_desc living descendants of that rival."""
    lib.om_character_create(w, character_id=commander_id, lineage_id=0, region_idx=region,
                            rank=RANK_LINEAGE_MEMBER, birth_tick=0, lifespan=1)
    lib.om_character_kill(w, commander_id, 1)
    lib.om_character_create(w, character_id=rival_id, lineage_id=0, region_idx=region,
                            rank=RANK_LINEAGE_MEMBER, birth_tick=0, lifespan=10_000_000)
    lib.om_character_tag_rival(w, character_id=rival_id, rival_of_character_id=commander_id)
    kids = []
    for i in range(n_desc):
        kid = first_child + i
        lib.om_character_create_child(w, child_id=kid, parent_id=rival_id, region_idx=region,
                                      birth_tick=10, lifespan=10_000_000)
        kids.append(kid)
    return rival_id, kids


def _rotate(lib, w, pool, mission_region=0, draws=()):
    if draws:
        from conftest import force_draws
        force_draws(lib, w, list(draws))
    rec = OmSelectionRecord()
    lib.om_character_selector_force_rotate(w, lineage_id=99, mission_region=mission_region,
                                           reason=REASON_FORCED, pool=pool, out_record=ctypes.byref(rec))
    return rec


def test_control_ALG_47_wrong_probabilities_and_scores_are_detected(lib):
    """Positive control: a reference with 0.6/0.3 pool split, gap weight 0.5, or density peak 4 disagrees with the C result."""
    assert lib.om_selector_roll_pool(None, 0.65) != _ref_pool(0.65, prev=0.60, nem=0.30)
    assert lib.om_selector_roll_pool(None, 0.85) != _ref_pool(0.85, prev=0.60, nem=0.20)
    assert abs(lib.om_selector_score_previous_lineage(None, 2, 3) - _ref_score(2, 3, gap_w=0.5, dens_w=0.5)) > 1e-3
    assert abs(lib.om_selector_score_previous_lineage(None, 2, 3) - _ref_score(2, 3, dens_peak=4)) > 1e-3


def test_ALG_47_pool_roll_is_70_20_10(lib):
    """ALG-47 / R-058-01: one draw gives previous below 0.70, nemesis below 0.90, else unrelated."""
    for i in range(0, 1000):
        d = i / 1000.0
        if abs(d - 0.7) < 1e-9 or abs(d - 0.9) < 1e-9:
            continue  # the cumulative sums 0.7 and 0.9 are not exact in binary floating point; the boundary draws are not asserted
        assert lib.om_selector_roll_pool(None, d) == _ref_pool(d), d


def test_ALG_47_previous_score_formula(lib):
    """ALG-47 / R-058-02: score = 0.6 * min(chapters_ago, 4)/4 + 0.4 * min(living_nearby, 5)/5."""
    for ago in range(0, 9):
        for nearby in range(0, 9):
            got = lib.om_selector_score_previous_lineage(None, ago, nearby)
            assert abs(got - _ref_score(ago, nearby)) <= 1e-12, (ago, nearby)


def test_ALG_47_unrelated_pool_creates_a_member_and_a_new_lineage(lib, world_factory):
    """ALG-47 / R-058-04: the unrelated pool creates a lineage_member in the mission region's owning faction, in a new lineage, even when a previous lineage is available."""
    w = world_factory(n_regions=N)
    _complete(lib, w)
    set_region(lib, w, 2, tier=OMTier.HOME, military=50.0, economy=50.0, tension=20.0, population=50.0, faction_id=3)
    _lineage(lib, w, 7, 3, [100], region=2)
    rec = _rotate(lib, w, POOL_UNRELATED, mission_region=2)
    assert rec.pool == POOL_UNRELATED and rec.commander_id not in (0, 100)
    c = _record(lib, w, rec.commander_id)
    assert c.faction == 3 and c.region == 2 and c.rank == RANK_LINEAGE_MEMBER
    assert c.lineage_id == rec.new_lineage_id and c.lineage_id not in (7, 99)
    assert _record(lib, w, 100).lineage_id == 7  # the previous lineage is untouched


def test_ALG_47_nemesis_is_one_uniform_draw_over_rival_descendants_within_two_hops(lib, world_factory):
    """ALG-47 / R-058-03: with three living descendants of a rival in range, the draws 0.1, 0.5, 0.9 pick each exactly once; the rival itself and a descendant 3 hops away are never picked."""
    picks = []
    for d in (0.1, 0.5, 0.9):
        w = world_factory(n_regions=N)
        for a, b in ((0, 1), (1, 2), (2, 3), (3, 4)):
            set_edge(lib, w, a, b)
        rival, kids = _rival_family(lib, w, region=1, n_desc=3)
        lib.om_character_create_child(w, child_id=520, parent_id=rival, region_idx=4, birth_tick=10, lifespan=10_000_000)  # 4 hops from region 0
        rec = _rotate(lib, w, POOL_NEMESIS, mission_region=0, draws=[d])
        assert rec.pool == POOL_NEMESIS
        picks.append(rec.commander_id)
    assert sorted(picks) == sorted(kids), (picks, kids)
    assert rival not in picks and 520 not in picks


def test_ALG_47_search_order_is_rolled_pool_then_previous_nemesis_unrelated(lib, world_factory):
    """ALG-47 / R-058-01: an empty rolled pool falls to the others in the order previous, nemesis, unrelated."""
    # rolled nemesis, nemesis empty, previous available -> previous (before unrelated)
    w = world_factory(n_regions=N)
    _complete(lib, w)
    _lineage(lib, w, 7, 2, [100])
    assert _rotate(lib, w, POOL_NEMESIS).commander_id == 100
    # rolled unrelated -> unrelated even when both other pools have candidates
    w = world_factory(n_regions=N)
    _complete(lib, w)
    _lineage(lib, w, 7, 2, [100])
    _rival_family(lib, w, region=0, n_desc=1)
    assert _rotate(lib, w, POOL_UNRELATED).commander_id not in (100, 510)
    # rolled previous, previous empty (its only member is 3 hops away), nemesis available -> nemesis
    w = world_factory(n_regions=N)
    for a, b in ((0, 1), (1, 2), (2, 3)):
        set_edge(lib, w, a, b)
    _lineage(lib, w, 7, 2, [100], region=3)
    _, kids = _rival_family(lib, w, region=0, n_desc=1)
    assert _rotate(lib, w, POOL_PREVIOUS).commander_id == kids[0]
    # rolled previous, previous and nemesis both empty -> unrelated
    w = world_factory(n_regions=N)
    for a, b in ((0, 1), (1, 2), (2, 3)):
        set_edge(lib, w, a, b)
    _lineage(lib, w, 7, 2, [100], region=3)
    rec = _rotate(lib, w, POOL_PREVIOUS)
    assert rec.commander_id not in (0, 100)


def _previous_share_of_lineage_one(lib, world_factory, seeds):
    """Share of seeds on which the weighted previous draw lands in lineage 1 (2 members, counter 4) rather than lineage 2 (5 members, counter 1)."""
    hits = 0
    for seed in seeds:
        w = world_factory(n_regions=N, seed=seed)
        _complete(lib, w)
        _lineage(lib, w, 1, 4, [100, 101])
        _lineage(lib, w, 2, 1, [200, 201, 202, 203, 204])
        if _rotate(lib, w, POOL_PREVIOUS).commander_id in (100, 101):
            hits += 1
    return hits / len(seeds)


def test_ALG_47_previous_pool_is_one_weighted_draw_with_the_lineage_score_on_every_member(lib, world_factory):
    """ALG-47 / R-058-02: every nearby member carries its lineage's score, so P(lineage 1) = 2 s1 / (2 s1 + 5 s2) with s1 = score(4, 2), s2 = score(1, 5), about 0.356 (a per-lineage weighting would give 0.58, equal member weights 0.286)."""
    s1, s2 = _ref_score(4, 2), _ref_score(1, 5)
    expect = 2 * s1 / (2 * s1 + 5 * s2)
    got = _previous_share_of_lineage_one(lib, world_factory, range(1, 801))
    assert abs(got - expect) <= 0.05, (got, expect)
    # control inside the test: the competing readings are further than the tolerance from the measurement
    assert abs(got - s1 / (s1 + s2)) > 0.05
    assert abs(got - 2 / 7) > 0.05
