"""ALG-51 Clustering (docs/bible/algorithms.md), proving R-065-04 and R-067-02 .. R-067-05 (S-067, E-09).

Category rules: lineage (R-067-02), chain (R-067-04), regional (R-067-05), evaluated here by an
independent implementation of the text over a grid that straddles every threshold, compared by
category NAME (om_chronicle_category_name), not by numeric id. Chain clustering: events with one
chain tag form one cluster, clusters with equal (primary region, category) merge, primary region is
the most common region in the cluster. Lineage quiet cluster: placed in the lineage's first active
member's region, else its last history region.
"""
import ctypes
import itertools

from conftest import OmChronicleCluster

CHAIN, REGIONAL = 2, 3


def _name(lib, category):
    return ctypes.string_at(lib.om_chronicle_category_name(category)).decode()


def _ref_lineage(template, net_eco, net_mil, net_ten, eco_min=2, mil_min=2):
    if "succession" in template or "death" in template:
        return "lineage_succession"
    if "military" in template or "revolt" in template:
        return "lineage_military_action"
    if net_eco > eco_min or net_mil > mil_min:
        return "lineage_thrived"
    if net_eco < -3 or net_ten > 5:
        return "lineage_suffered"
    return "lineage_quiet"


def _ref_chain(template, n_events, net_mil, net_eco, net_ten, cascade_min=4):
    if "revolt" in template:
        return "chain_revolt_spawned"
    if "expansion" in template or "coloniz" in template:
        return "chain_expansion"
    if n_events >= cascade_min:
        return "chain_cascade"
    if net_mil > 2 and net_ten < 3:
        return "chain_conflict_victory"
    if net_mil < -2 and net_ten > 3:
        return "chain_conflict_defeat"
    if abs(net_mil) <= 2 and net_ten > 2:
        return "chain_conflict_stalemate"
    if net_eco > 0 and net_ten <= 0:
        return "chain_crisis_resolved_well"
    return "chain_crisis_resolved_badly"


def _ref_regional(has_conquest_or_revolt, net_eco_pop, growth_min=3):
    if has_conquest_or_revolt:
        return "regional_faction_shift"
    if net_eco_pop > growth_min:
        return "regional_growth"
    if net_eco_pop < -3:
        return "regional_decline"
    return "regional_stable"


NETS = [-6.0, -3.5, -3.0, -2.01, -2.0, 0.0, 2.0, 2.01, 3.0, 3.01, 5.0, 5.01, 8.0]


def _lineage_all(lib, templates, eco_min=2, mil_min=2):
    return [
        (t, e, m, n, _name(lib, lib.om_chronicle_categorize_lineage_cluster(None, template_name=t.encode(), net_eco=e, net_mil=m, net_ten=n)),
         _ref_lineage(t, e, m, n, eco_min, mil_min))
        for t in templates for e, m, n in itertools.product(NETS, repeat=3)
    ]


def test_control_ALG_51_a_wrong_threshold_or_precedence_is_detected(lib):
    """Positive control: a reference with thrived at > 3 instead of > 2, or the cascade threshold at 5 instead of 4 events, disagrees with the C categorizers somewhere on the grid."""
    rows = _lineage_all(lib, ["", "evt_succession"], eco_min=3, mil_min=3)
    assert any(got != ref for *_, got, ref in rows)
    n_bad = 0
    for n_events in (3, 4, 5):
        got = _name(lib, lib.om_chronicle_categorize_chain_cluster(None, template_name=b"", n_events=n_events, net_mil=0.0, net_eco=0.0, net_ten=0.0))
        n_bad += got != _ref_chain("", n_events, 0.0, 0.0, 0.0, cascade_min=5)
    assert n_bad > 0


def test_ALG_51_lineage_categories_R_067_02(lib):
    """ALG-51 step 2 / R-067-02: succession/death > military/revolt > thrived (eco > 2 or mil > 2) > suffered (eco < -3 or tension > 5) > quiet, with every threshold strict."""
    templates = ["", "evt_succession_crisis", "evt_death_of_leader", "evt_military_buildup", "evt_revolt_rising", "evt_death_military", "evt_quiet_trade"]
    wrong = [(t, e, m, n, got, ref) for t, e, m, n, got, ref in _lineage_all(lib, templates) if got != ref]
    assert not wrong, f"{len(wrong)} mismatches, first: {wrong[0]}"


def test_ALG_51_chain_categories_R_067_04(lib):
    """ALG-51 step 3 / R-067-04: revolt > expansion/coloniz > 4 or more events > victory > defeat > stalemate > resolved well > resolved badly."""
    wrong = []
    for t in ("", "evt_revolt_x", "evt_expansion_x", "evt_colonization", "evt_coloniz", "evt_border_clash", "evt_revolt_expansion"):
        for n_events in (1, 3, 4, 6):
            for mil, eco, ten in itertools.product((-5.0, -2.01, -2.0, 0.0, 2.0, 2.01, 5.0), (-1.0, 0.0, 1.0), (-1.0, 0.0, 2.0, 2.5, 3.0, 3.5)):
                got = _name(lib, lib.om_chronicle_categorize_chain_cluster(None, template_name=t.encode(), n_events=n_events, net_mil=mil, net_eco=eco, net_ten=ten))
                ref = _ref_chain(t, n_events, mil, eco, ten)
                if got != ref:
                    wrong.append((t, n_events, mil, eco, ten, got, ref))
    assert not wrong, f"{len(wrong)} mismatches, first: {wrong[0]}"


def test_ALG_51_regional_categories_R_067_05(lib):
    """ALG-51 step 4 / R-067-05: a conquest, revolt or faction-creating event gives faction_shift; else net economy + population > 3 growth, < -3 decline, else stable."""
    wrong = []
    for flag in (0, 1):
        for net in (-9.0, -3.01, -3.0, -2.99, 0.0, 2.99, 3.0, 3.01, 9.0):
            got = _name(lib, lib.om_chronicle_categorize_regional_cluster(None, has_conquest_or_revolt=flag, net_eco_pop=net))
            ref = _ref_regional(flag, net)
            if got != ref:
                wrong.append((flag, net, got, ref))
    assert not wrong, wrong


def _clusters(lib, w):
    lib.om_chronicle_select_clusters(w)
    out = []
    for i in range(lib.om_chronicle_entry_count(w)):
        c = OmChronicleCluster()
        lib.om_chronicle_get_cluster(w, i, ctypes.byref(c))
        out.append(c)
    return out


def test_ALG_51_chain_events_with_one_tag_form_one_cluster_and_equal_region_category_merge(lib, world_factory):
    """ALG-51 step 3 / R-067-03: three events of tag 7 are one cluster; tag 8 in the same primary region and category merges into it (one cluster in all); tag 9 in another region stays separate."""
    w = world_factory(n_regions=4)
    for tag, region in ((7, 1), (7, 1), (7, 1), (8, 1), (9, 2)):
        lib.om_chronicle_add_chain_event(w, chain_tag=tag, region_idx=region, category=10)
    assert lib.om_chronicle_build_chain_clusters(w) == 2
    assert sorted(c.region for c in _clusters(lib, w)) == [1, 2]


def test_ALG_51_primary_region_is_the_most_common_region_in_the_cluster(lib, world_factory):
    """ALG-51: 'Primary region = most common region in the cluster'. One chain of tag 7 touches region 1 once and region 2 three times: the cluster's region must be 2 (the C code takes the first region seen, 1)."""
    w = world_factory(n_regions=4)
    for region in (1, 2, 2, 2):
        lib.om_chronicle_add_chain_event(w, chain_tag=7, region_idx=region, category=10)
    assert lib.om_chronicle_build_chain_clusters(w) == 1
    (cluster,) = _clusters(lib, w)
    assert cluster.region == 2, f"primary region {cluster.region}; regions seen [1, 2, 2, 2]"


def test_ALG_51_quiet_lineage_cluster_goes_to_the_first_active_member_else_last_history_region(lib, world_factory):
    """ALG-51 step 2: with no lineage event, one lineage_quiet cluster in the lineage's first active member's region, else its last history region."""
    w = world_factory(n_regions=5)
    lib.om_lineage_create(w, lineage_id=1, home_region=0)
    lib.om_lineage_record_history_region(w, lineage_id=1, region_idx=3)
    lib.om_character_create(w, character_id=10, lineage_id=1, region_idx=2, rank=3, birth_tick=0, lifespan=10_000)
    lib.om_chronicle_add_cluster_direct(w, cluster_type=CHAIN, category=10, score=1.0)
    lib.om_chronicle_select_clusters(w)
    lineage = [c for c in _clusters(lib, w) if c.type == 1]
    assert len(lineage) == 1 and lineage[0].region == 2
    assert "quiet" in _name(lib, lineage[0].category)
    w2 = world_factory(n_regions=5)
    lib.om_lineage_create(w2, lineage_id=1, home_region=0)
    lib.om_lineage_record_history_region(w2, lineage_id=1, region_idx=3)
    lib.om_chronicle_add_cluster_direct(w2, cluster_type=CHAIN, category=10, score=1.0)
    lineage2 = [c for c in _clusters(lib, w2) if c.type == 1]
    assert len(lineage2) == 1 and lineage2[0].region == 3
