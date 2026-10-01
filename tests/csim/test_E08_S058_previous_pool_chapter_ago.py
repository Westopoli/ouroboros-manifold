"""R-058-02 -- the previous-descendant pool only holds lineages last played at least 1 chapter ago.

Ruling A26 (architect-rulings-2.md, Addendum 11): the pool ignoring this condition is a defect,
fixed in piece B6-collapse-pick as a second unit with its own test.

The lineage's chapter counter (om_lineage_chapter_count) is the pool's "chapters ago"
(om_selector_score_previous_lineage takes it as chapters_ago): a lineage whose counter is 0 was
not played 1 or more chapters ago and is not in the pool; counter 1 or more is. The pool is
driven through om_character_selector_force_rotate with the PREVIOUS pool rolled, so a rolled
previous pool that is empty falls through nemesis, then unrelated (R-058-01).
"""
import ctypes

from conftest import OmSelectionRecord, set_edge

GEN_RANK_LINEAGE_MEMBER = 3
POOL_PREVIOUS = 0
REASON_FORCED = 0
N = 4
MEMBER = 100


def _complete_graph(lib, w):
    for a in range(N):
        for b in range(a + 1, N):
            set_edge(lib, w, a, b)


def _lineage(lib, w, lineage, chapters, member_id, region=0):
    lib.om_lineage_create(w, lineage_id=lineage, home_region=region)
    lib.om_lineage_set_chapter_count(w, lineage_id=lineage, chapters=chapters)
    lib.om_character_create(w, character_id=member_id, lineage_id=lineage, region_idx=region,
                            rank=GEN_RANK_LINEAGE_MEMBER, birth_tick=0, lifespan=10_000_000)


def _nemesis_descendant(lib, w, region=0, rival_id=200, commander_id=201, child_id=202):
    lib.om_character_create(w, character_id=commander_id, lineage_id=0, region_idx=region,
                            rank=GEN_RANK_LINEAGE_MEMBER, birth_tick=0, lifespan=1)
    lib.om_character_kill(w, commander_id, 1)
    lib.om_character_create(w, character_id=rival_id, lineage_id=0, region_idx=region,
                            rank=GEN_RANK_LINEAGE_MEMBER, birth_tick=0, lifespan=10_000_000)
    lib.om_character_tag_rival(w, character_id=rival_id, rival_of_character_id=commander_id)
    lib.om_character_create_child(w, child_id=child_id, parent_id=rival_id, region_idx=region,
                                  birth_tick=10, lifespan=10_000_000)
    return child_id


def _rotate_previous(lib, w):
    rec = OmSelectionRecord()
    lib.om_character_selector_force_rotate(w, lineage_id=99, mission_region=0,
                                           reason=REASON_FORCED,
                                           pool=POOL_PREVIOUS,
                                           out_record=ctypes.byref(rec))
    return rec


def test_R_058_02_a_lineage_not_played_a_chapter_ago_is_not_in_the_previous_pool(lib, world_factory):
    """Given a lineage with chapter counter 0 and a nemesis descendant, When the previous pool is rolled, Then the nemesis descendant is chosen, not the lineage member."""
    for seed in (1, 2, 3, 4):
        w = world_factory(n_regions=N, seed=seed)
        _complete_graph(lib, w)
        _lineage(lib, w, lineage=7, chapters=0, member_id=MEMBER)
        nemesis = _nemesis_descendant(lib, w)
        rec = _rotate_previous(lib, w)
        assert rec.commander_id == nemesis, f"seed {seed}: a 0-chapter lineage must not be in the previous pool, fell through to nemesis expected"
        assert lib.om_character_lineage_id(w, MEMBER) == 7, f"seed {seed}: the member must stay in its lineage"


def test_R_058_02_a_lineage_not_played_a_chapter_ago_falls_through_to_unrelated(lib, world_factory):
    """Given only a lineage with chapter counter 0 and no nemesis descendant, When the previous pool is rolled, Then the pool is empty and the unrelated pool creates a new character."""
    for seed in (1, 2, 3, 4):
        w = world_factory(n_regions=N, seed=seed)
        _complete_graph(lib, w)
        _lineage(lib, w, lineage=7, chapters=0, member_id=MEMBER)
        rec = _rotate_previous(lib, w)
        assert rec.commander_id != MEMBER, f"seed {seed}: a 0-chapter lineage member was drawn from the previous pool"
        assert lib.om_character_lineage_id(w, MEMBER) == 7


def test_R_058_02_control_a_lineage_played_one_chapter_ago_is_in_the_previous_pool(lib, world_factory):
    """Positive control: the same fixture with chapter counter 1 puts the member in the pool, so it is chosen over the nemesis descendant."""
    for seed in (1, 2, 3, 4):
        w = world_factory(n_regions=N, seed=seed)
        _complete_graph(lib, w)
        _lineage(lib, w, lineage=7, chapters=1, member_id=MEMBER)
        _nemesis_descendant(lib, w)
        rec = _rotate_previous(lib, w)
        assert rec.commander_id == MEMBER, f"seed {seed}: a 1-chapter lineage must be in the previous pool"


def test_R_058_02_only_the_lineage_played_a_chapter_ago_is_drawn_when_another_was_not(lib, world_factory):
    """Given lineage 7 with counter 0 and lineage 8 with counter 3, each with a living member nearby, When the previous pool is drawn over seeds, Then the member of lineage 8 is always the one drawn."""
    for seed in range(1, 17):
        w = world_factory(n_regions=N, seed=seed)
        _complete_graph(lib, w)
        _lineage(lib, w, lineage=7, chapters=0, member_id=MEMBER, region=0)
        _lineage(lib, w, lineage=8, chapters=3, member_id=MEMBER + 1, region=1)
        rec = _rotate_previous(lib, w)
        assert rec.commander_id == MEMBER + 1, f"seed {seed}: drew {rec.commander_id}, the 0-chapter lineage's member must not be in the pool"
