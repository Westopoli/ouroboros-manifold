"""ALG-52 Selection (docs/bible/algorithms.md), proving R-065-01, R-065-02, R-065-03, R-065-05, R-065-06 (S-065, E-09).

Order: consequence clusters, then lineage clusters, then the rest by peak score descending (ties in
arrival order), skipping any category already used twice, until CHRONICLE_MAX_ENTRIES = 10; if
fewer than CHRONICLE_MIN_ENTRIES = 5, skipped clusters are added in order while their category has
fewer than 2 entries. The reference below implements those sentences literally and is compared
with the clusters the sim keeps, entry by entry (type, category, peak score, region).
"""
import ctypes

from conftest import OmChronicleCluster

CONSEQUENCE, LINEAGE, CHAIN, REGIONAL = 0, 1, 2, 3
MAX_ENTRIES, MIN_ENTRIES, CATEGORY_CAP = 10, 5, 2


def _ref_select(consequence, lineage, rest, max_entries=MAX_ENTRIES, cap=CATEGORY_CAP):
    """consequence: [(category, region)], lineage: [(category, region, score)], rest: [(type, category, score)] in arrival order."""
    out = [("c", cat, 0.0) for cat, _ in consequence] + [("l", cat, score) for cat, _, score in lineage]
    ordered = sorted(enumerate(rest), key=lambda p: -p[1][2])  # Python's sort is stable: ties keep arrival order
    used, skipped = {}, []
    for _, (ctype, cat, score) in ordered:
        if len(out) >= max_entries:
            break
        if used.get(cat, 0) >= cap:
            skipped.append((ctype, cat, score))
            continue
        used[cat] = used.get(cat, 0) + 1
        out.append(("r", cat, score))
    if len(out) < MIN_ENTRIES:
        for ctype, cat, score in skipped:
            if len(out) >= max_entries:
                break
            if used.get(cat, 0) < cap:
                used[cat] = used.get(cat, 0) + 1
                out.append(("r", cat, score))
    return out


def _run(lib, world_factory, consequence=(), lineage=(), rest=(), n_regions=6):
    w = world_factory(n_regions=n_regions)
    for cat, region in consequence:
        lib.om_chronicle_add_consequence_event(w, region_idx=region, outcome=cat)
    for lid, (cat, region, score) in enumerate(lineage, start=1):
        lib.om_lineage_create(w, lineage_id=lid, home_region=region)
        lib.om_chronicle_add_lineage_event(w, lineage_id=lid, region_idx=region, category=cat, score=score)
    for ctype, cat, score in rest:
        lib.om_chronicle_add_cluster_direct(w, cluster_type=ctype, category=cat, score=score)
    lib.om_chronicle_select_clusters(w)
    got = []
    for i in range(lib.om_chronicle_entry_count(w)):
        c = OmChronicleCluster()
        lib.om_chronicle_get_cluster(w, i, ctypes.byref(c))
        got.append(c)
    return got


def _as_tuples(clusters):
    kind = {CONSEQUENCE: "c", LINEAGE: "l", CHAIN: "r", REGIONAL: "r"}
    return [(kind[c.type], c.category, c.peak_score if c.type != CONSEQUENCE else 0.0) for c in clusters]


# Scenario: 3 consequence-or-lineage entries first, then chain and regional clusters over several categories.
REST_A = [
    (CHAIN, 10, 9.0), (CHAIN, 10, 8.0), (CHAIN, 10, 7.0), (REGIONAL, 20, 6.5), (CHAIN, 11, 6.0),
    (CHAIN, 11, 5.5), (CHAIN, 11, 5.0), (REGIONAL, 21, 4.0), (REGIONAL, 22, 3.0), (REGIONAL, 23, 2.0),
    (CHAIN, 12, 1.5), (CHAIN, 13, 1.0), (CHAIN, 14, 0.5),
]


def test_control_ALG_52_wrong_cap_or_order_is_detected(lib, world_factory):
    """Positive control: a reference with a per-category cap of 3, a limit of 11 entries, or consequence/lineage clusters ranked by score instead of first disagrees with the sim on the same input."""
    got = _as_tuples(_run(lib, world_factory, consequence=[(0, 1)], lineage=[(4, 2, 0.1)], rest=REST_A))
    assert got != _ref_select([(0, 1)], [(4, 2, 0.1)], REST_A, cap=3)
    assert got != _ref_select([(0, 1)], [(4, 2, 0.1)], REST_A, max_entries=11)
    ranked_by_score = sorted(_ref_select([(0, 1)], [(4, 2, 0.1)], REST_A), key=lambda t: -t[2])
    assert got != ranked_by_score


def test_ALG_52_consequence_then_lineage_then_rest_by_score_with_category_cap_and_ten_entries(lib, world_factory):
    """ALG-52 / R-065-02, R-065-03, R-065-05: consequence entry 1, lineage entry 2 (both ahead of far higher scores), then the rest by descending peak score, at most two per category, 10 entries in all."""
    got = _as_tuples(_run(lib, world_factory, consequence=[(0, 1)], lineage=[(4, 2, 0.1)], rest=REST_A))
    want = _ref_select([(0, 1)], [(4, 2, 0.1)], REST_A)
    assert len(want) == 10
    assert [g[0] for g in got[:2]] == ["c", "l"]
    assert got == want


def test_ALG_52_ties_keep_arrival_order(lib, world_factory):
    """ALG-52: equal peak scores are taken in the order they arrived (stable), so the category cap lands on the later cluster: of three category-20 clusters (chain, regional, regional) the first two stay, then the category-10 cluster."""
    rest = [(CHAIN, 20, 5.0), (REGIONAL, 20, 5.0), (REGIONAL, 20, 5.0), (CHAIN, 10, 5.0)]
    got = _run(lib, world_factory, rest=rest)
    assert [(c.type, c.category) for c in got] == [(CHAIN, 20), (REGIONAL, 20), (CHAIN, 10)]


def test_ALG_52_cap_beats_the_minimum_of_five(lib, world_factory):
    """ALG-52 / R-065-06: two categories of three clusters each give 4 entries; the minimum of 5 does not break the per-category cap (a skipped cluster's category is already full, so the refill adds nothing)."""
    rest = [(REGIONAL, 20, 10.0), (REGIONAL, 20, 9.0), (REGIONAL, 20, 8.0), (CHAIN, 10, 9.5), (CHAIN, 10, 8.5), (CHAIN, 10, 7.5)]
    got = _as_tuples(_run(lib, world_factory, rest=rest))
    assert got == _ref_select([], [], rest)
    assert len(got) == 4


def test_ALG_52_at_most_ten_entries_with_fourteen_categories_available(lib, world_factory):
    """ALG-52 / R-065-01: fourteen single clusters of distinct categories, no consequence or lineage: exactly the ten best by score."""
    rest = [(CHAIN if cat < 18 else REGIONAL, cat, 20.0 - i) for i, cat in enumerate([10, 11, 12, 13, 14, 15, 16, 17, 20, 21, 22, 23, 24, 25])]
    got = _as_tuples(_run(lib, world_factory, rest=rest))
    assert len(got) == 10
    assert got == _ref_select([], [], rest)
