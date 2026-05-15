#!/usr/bin/env python3
"""Stage 11g Checkpoint N — chronicle mentions sim side.

assemble_scroll emits per-entry mention spans (region/faction ids + char
ranges) over base_text and expanded_text. Spans survive _apply_first_mention
text growth. Gated on config.ENABLE_CHRONICLE_MENTIONS.
"""
import os
import random
import sys

sys.path.insert(0, os.path.dirname(__file__))

import config
from chronicle_assembler import assemble_scroll, ScrollEntry
from chronicle_distiller import Cluster


class MockRegion:
    def __init__(self, rid, name, faction_id=None, tier="frontier"):
        self.id = rid
        self.name = name
        self.display_name = name
        self.faction_id = faction_id
        self.tier = tier
        self.fields = {"economy": 50, "military": 40, "tension": 25, "population": 60}
        self.composites = {"stability": 55, "capacity": 50}


class MockWorld:
    def __init__(self):
        self.regions = {
            "r_alpha": MockRegion("r_alpha", "Alpha", "f_phoenix"),
            "r_beta":  MockRegion("r_beta",  "Beta",  "f_phoenix"),
            "r_gamma": MockRegion("r_gamma", "Gamma", "f_drakkar"),
        }
        self._neighbors = {
            "r_alpha": ["r_beta", "r_gamma"],
            "r_beta":  ["r_alpha"],
            "r_gamma": ["r_alpha"],
        }

    def get_neighbors(self, rid):
        return self._neighbors.get(rid, [])


class MockFaction:
    def __init__(self, fid, name):
        self.id = fid
        self.name = name


def _registry():
    return {
        "f_phoenix": MockFaction("f_phoenix", "Phoenix"),
        "f_drakkar": MockFaction("f_drakkar", "Drakkar"),
    }


def _cluster(region_id, category="regional_growth"):
    return Cluster(
        cluster_type="regional",
        category=category,
        events=[{"template_id": "noop", "name": "noop", "region_id": region_id,
                 "field_deltas": {"economy": 5}}],
        region_id=region_id,
        peak_score=1.0,
        tick_range=(0, 5),
    )


def _assert_spans_match_text(entry, name_attr, kind_to_names):
    spans = getattr(entry, name_attr)
    text = entry.base_text if name_attr == "mentions" else entry.expanded_text
    for m in spans:
        sub = text[m["start"]:m["end"]]
        expected = kind_to_names[m["kind"]].get(m["id"])
        assert expected is not None, f"unknown id in mention: {m}"
        assert sub == expected, f"span {m} -> {sub!r}, expected {expected!r}"
    # non-overlap
    sorted_spans = sorted(spans, key=lambda s: s["start"])
    for a, b in zip(sorted_spans, sorted_spans[1:]):
        assert a["end"] <= b["start"], f"overlap {a} {b}"


def _id_to_name_maps(world, registry):
    return {
        "region": {rid: r.name for rid, r in world.regions.items()},
        "faction": {fid: f.name for fid, f in registry.items()},
    }


def test_flag_off_no_mentions():
    config.ENABLE_CHRONICLE_MENTIONS = False
    world = MockWorld()
    reg = _registry()
    entries, _ = assemble_scroll([_cluster("r_alpha")], None, None, world,
                                  seed=42, registry=reg)
    assert entries, "fixture produced no entries"
    for e in entries:
        assert e.mentions == [], "flag off: mentions must stay empty"
        assert e.expanded_mentions == [], "flag off: expanded_mentions must stay empty"
    print("ok flag_off_no_mentions")


def test_flag_on_spans_match_named_entities():
    config.ENABLE_CHRONICLE_MENTIONS = True
    world = MockWorld()
    reg = _registry()
    name_maps = _id_to_name_maps(world, reg)

    entries, _ = assemble_scroll([_cluster("r_alpha")], None, None, world,
                                  seed=42, registry=reg)
    assert entries
    for e in entries:
        _assert_spans_match_text(e, "mentions", name_maps)
        _assert_spans_match_text(e, "expanded_mentions", name_maps)
    print("ok flag_on_spans_match_named_entities")


def test_first_mention_enrich_captures_faction_span():
    """_apply_first_mention grows '... Alpha ...' -> '... Alpha, held by Phoenix ...'.
    The injected faction name must appear in mentions."""
    config.ENABLE_CHRONICLE_MENTIONS = True
    world = MockWorld()
    reg = _registry()
    entries, _ = assemble_scroll([_cluster("r_alpha")], None, None, world,
                                  seed=42, registry=reg)
    assert entries
    first = entries[0]
    # _apply_first_mention only fires when the entry doesn't already include
    # both region + faction name. If it did fire, faction span exists.
    if "held by" in first.base_text:
        kinds = {m["kind"] for m in first.mentions}
        assert "faction" in kinds, f"faction missing from {first.mentions}"
        # And the faction span resolves to the correct id.
        f_spans = [m for m in first.mentions if m["kind"] == "faction"]
        assert any(first.base_text[m["start"]:m["end"]] == "Phoenix" for m in f_spans)
    print("ok first_mention_enrich_captures_faction_span")


def test_longest_match_wins():
    """If 'Phoenix' and 'Phoenix Reach' both existed, the longer wins. We
    fake this by adding a region whose name is a prefix-collision with the
    faction name."""
    config.ENABLE_CHRONICLE_MENTIONS = True
    world = MockWorld()
    # Add a region named 'Phoenix Reach' to force prefix collision.
    world.regions["r_pr"] = MockRegion("r_pr", "Phoenix Reach", "f_phoenix")
    world._neighbors["r_pr"] = []
    reg = _registry()

    # Force assembled text to contain 'Phoenix Reach' literally.
    sample_text = "the storied lands of Phoenix Reach endured."
    entry = ScrollEntry(base_text=sample_text, expanded_text=sample_text,
                        cluster_type="regional", category="regional_growth",
                        region_id="r_pr")
    # Drive the same mentions path on this synthetic entry by calling the
    # exposed helper.
    from chronicle_assembler import _compute_mentions
    spans = _compute_mentions(sample_text, world, reg)
    assert len(spans) == 1, f"expected 1 span (longest-match wins), got {spans}"
    assert spans[0]["kind"] == "region"
    assert spans[0]["id"] == "r_pr"
    assert sample_text[spans[0]["start"]:spans[0]["end"]] == "Phoenix Reach"
    print("ok longest_match_wins")


if __name__ == "__main__":
    try:
        test_flag_off_no_mentions()
        test_flag_on_spans_match_named_entities()
        test_first_mention_enrich_captures_faction_span()
        test_longest_match_wins()
        print("all 4 pass")
    finally:
        config.ENABLE_CHRONICLE_MENTIONS = False
