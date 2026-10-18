"""ALG-52 Selection (docs/bible/algorithms.md), rules R-065-02..R-065-06 (E-09, S-065).

Isolation: om_chronicle_add_cluster_direct builds candidate clusters of chosen type, category and
peak score; om_chronicle_select_clusters runs the selection; om_chronicle_get_cluster reads the result
in entry order. Expected order and counts are computed in the test from the row's rules, with
CHRONICLE_MAX_ENTRIES read from csrc/om_constants.h.
unstated: the "add skipped clusters in order while a category has fewer than 2" fill when fewer than
CHRONICLE_MIN_ENTRIES; a skipped cluster is by definition in a category that already has 2, so the fill
can never add one, and the ruling on Q-065-01 (2026-10-01) says the cap wins over the minimum;
not asserted beyond "the cap holds below the minimum", Westley's.
unstated: the order among equal peak scores, Westley's.
"""
import ctypes

import pytest

from alg_consts import const
from conftest import OmChronicleCluster

MAX_ENTRIES = const("CHRONICLE_MAX_ENTRIES")
MIN_ENTRIES = const("CHRONICLE_MIN_ENTRIES")
CAT_CAP = 2  # "already used twice" in the row
CONSEQUENCE, LINEAGE, CHAIN, REGIONAL = 0, 1, 2, 3


def _selected(lib, w):
    out = []
    for i in range(lib.om_chronicle_entry_count(w)):
        c = OmChronicleCluster()
        assert lib.om_chronicle_get_cluster(w, i, ctypes.byref(c)) == 1
        out.append((c.type, c.category, c.peak_score))
    return out


def _add(lib, w, ctype, cat, score):
    lib.om_chronicle_add_cluster_direct(w, cluster_type=ctype, category=cat, score=score)


def test_ALG_52_order_consequence_then_lineage_then_rest_by_descending_peak(lib, world_factory):
    """ALG-52 / R-065-02..05: consequence clusters first, lineage next, the rest by peak score descending."""
    w = world_factory(n_regions=4)
    _add(lib, w, REGIONAL, 21, 9.0)
    _add(lib, w, CHAIN, 12, 7.5)
    _add(lib, w, LINEAGE, 0, 1.0)
    _add(lib, w, CONSEQUENCE, 30, 0.5)
    _add(lib, w, REGIONAL, 22, 8.0)
    lib.om_chronicle_select_clusters(w)
    got = _selected(lib, w)
    assert [t for t, _, _ in got] == [CONSEQUENCE, LINEAGE, REGIONAL, REGIONAL, CHAIN]
    assert [s for t, _, s in got][2:] == [9.0, 8.0, 7.5]


def test_ALG_52_category_cap_two_per_category_for_the_rest(lib, world_factory):
    """ALG-52 / R-065-05: the rest skip any category already used twice."""
    w = world_factory(n_regions=4)
    for s in (9.0, 8.0, 7.0, 6.0):
        _add(lib, w, REGIONAL, 21, s)
    for s in (8.5, 7.5, 6.5):
        _add(lib, w, REGIONAL, 22, s)
    lib.om_chronicle_select_clusters(w)
    assert lib.om_chronicle_selected_category_count(w, category=21) == CAT_CAP
    assert lib.om_chronicle_selected_category_count(w, category=22) == CAT_CAP
    assert [s for _, _, s in _selected(lib, w)] == [9.0, 8.5, 8.0, 7.5]


def test_ALG_52_stops_at_max_entries(lib, world_factory):
    """ALG-52: selection ends at CHRONICLE_MAX_ENTRIES. 12 candidates, 6 categories x 2, scores 12..1."""
    w = world_factory(n_regions=4)
    cats = [10, 11, 12, 13, 14, 15]
    scores = [float(12 - i) for i in range(12)]
    for i, s in enumerate(scores):
        _add(lib, w, CHAIN, cats[i % len(cats)], s)
    lib.om_chronicle_select_clusters(w)
    assert lib.om_chronicle_entry_count(w) == MAX_ENTRIES
    assert [s for _, _, s in _selected(lib, w)] == scores[:MAX_ENTRIES]


def test_ALG_52_cap_holds_below_the_minimum(lib, world_factory):
    """ALG-52 / R-065-06 + Q-065-01 ruling: with fewer than CHRONICLE_MIN_ENTRIES reachable under the cap, the scroll is short."""
    w = world_factory(n_regions=4)
    for s in (10.0, 9.0, 8.0, 7.0, 6.0):
        _add(lib, w, REGIONAL, 21, s)
    lib.om_chronicle_select_clusters(w)
    assert lib.om_chronicle_entry_count(w) == CAT_CAP < MIN_ENTRIES


def test_ALG_52_positive_control_cap_of_three_rejected(lib, world_factory):
    """Positive control: an expectation of 3 selected from a single category (no cap) must be rejected."""
    w = world_factory(n_regions=4)
    for s in (10.0, 9.0, 8.0):
        _add(lib, w, REGIONAL, 21, s)
    lib.om_chronicle_select_clusters(w)
    got = lib.om_chronicle_selected_category_count(w, category=21)
    with pytest.raises(AssertionError):
        assert got == 3
