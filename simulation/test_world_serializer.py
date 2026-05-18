import json
import math
import random
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

from save.world_serializer import (
    SAVE_VERSION,
    SaveVersionError,
    serialize_world,
    deserialize_world,
)
from world import World, generate_random
from region import Region
from faction import Faction, generate_starting_factions
from chronicle_assembler import ScrollEntry
from naming_system import NamingSystem
from coherence_ledger import CoherenceLedger, CharacterRecord
from generational import GenerationalState
from events import PendingQueue


def _empty_world() -> World:
    return World(regions={}, adjacency={}, edge_types={}, seed=0)


def _two_region_world() -> World:
    fields_a = {"military": 50.0, "economy": 60.0, "tension": 20.0, "population": 40.0}
    fields_b = {"military": 30.0, "economy": 70.0, "tension": 10.0, "population": 55.0}
    a = Region("ra", "Region A", "home", fields_a, faction_id="player")
    b = Region("rb", "Region B", "frontier", fields_b, faction_id="player")
    a.econ_phase_offset = 1.234
    a.tension_phase_offset = 2.345
    a.held_since_tick = 5
    a.previous_faction_id = "faction_1"
    return World(
        regions={"ra": a, "rb": b},
        adjacency={"ra": ["rb"], "rb": ["ra"]},
        edge_types={("ra", "rb"): "both", ("rb", "ra"): "both"},
        seed=42,
    )


def _two_factions(rng: random.Random) -> dict:
    f1 = Faction("player", "Player", "player_civilization",
                 budget=12.5, modifiers={"military": 0.02},
                 diplomatic_stance={"faction_1": "hostile"},
                 color="#4a9eff", rng=rng)
    f2 = Faction("faction_1", "Faction 1", "conqueror",
                 budget=7.0,
                 diplomatic_stance={"player": "hostile"},
                 color="#ff4a4a", rng=rng)
    return {"player": f1, "faction_1": f2}


# ── 1. Version ────────────────────────────────────────────────────────────────

def test_save_version_present():
    world = _empty_world()
    payload = serialize_world(world, factions={}, chronicle_entries=[],
                              tick=0, era_id="settled_reach")
    assert "save_version" in payload
    assert payload["save_version"] == SAVE_VERSION


# ── 2. Empty world ────────────────────────────────────────────────────────────

def test_empty_world_roundtrip():
    world = _empty_world()
    payload = serialize_world(world, factions={}, chronicle_entries=[],
                              tick=0, era_id="settled_reach")
    r = deserialize_world(payload)
    assert r["world"].regions == {}
    assert r["world"].adjacency == {}
    assert r["world"].edge_types == {}
    assert r["factions"] == {}
    assert r["chronicle_entries"] == []
    assert r["tick"] == 0
    assert r["era_id"] == "settled_reach"
    assert r["stances"] == {}


# ── 3. Region fields ──────────────────────────────────────────────────────────

def test_single_region_full_fields():
    fields = {"military": 51.7, "economy": 62.3, "tension": 18.9, "population": 44.1}
    r = Region("ra", "Region A", "home", fields, faction_id="player")
    w = World(regions={"ra": r}, adjacency={"ra": []}, edge_types={}, seed=0)
    payload = serialize_world(w, factions={}, chronicle_entries=[],
                              tick=0, era_id="settled_reach")
    w2 = deserialize_world(payload)["world"]
    r2 = w2.regions["ra"]
    assert r2.fields == fields
    assert r2.id == "ra"
    assert r2.name == "Region A"
    assert r2.tier == "home"
    assert r2.faction_id == "player"


def test_region_phase_offsets_and_history_preserved():
    w = _two_region_world()
    payload = serialize_world(w, factions={}, chronicle_entries=[],
                              tick=10, era_id="settled_reach")
    w2 = deserialize_world(payload)["world"]
    r = w2.regions["ra"]
    assert r.econ_phase_offset == pytest.approx(1.234)
    assert r.tension_phase_offset == pytest.approx(2.345)
    assert r.held_since_tick == 5
    assert r.previous_faction_id == "faction_1"


# ── 4. Composites ─────────────────────────────────────────────────────────────

def test_composites_recomputed_on_load():
    w = _two_region_world()
    # Corrupt composites pre-save to prove they're recomputed not persisted.
    w.regions["ra"].composites = {"stability": -999.0, "capacity": -999.0}
    payload = serialize_world(w, factions={}, chronicle_entries=[],
                              tick=0, era_id="settled_reach")
    w2 = deserialize_world(payload)["world"]
    r = w2.regions["ra"]
    assert r.composites["stability"] != -999.0
    assert r.composites["capacity"] != -999.0
    # Composites must equal what recompute_composites would produce.
    expected = Region("ra", "Region A", "home", w.regions["ra"].fields, faction_id="player")
    assert r.composites["stability"] == pytest.approx(expected.composites["stability"])
    assert r.composites["capacity"] == pytest.approx(expected.composites["capacity"])


# ── 5. Adjacency + edge_types ─────────────────────────────────────────────────

def test_multi_region_adjacency_and_edge_types():
    w = _two_region_world()
    payload = serialize_world(w, factions={}, chronicle_entries=[],
                              tick=0, era_id="settled_reach")
    w2 = deserialize_world(payload)["world"]
    assert w2.adjacency == {"ra": ["rb"], "rb": ["ra"]}
    assert w2.edge_types == {("ra", "rb"): "both", ("rb", "ra"): "both"}


# ── 6. Factions + stances ─────────────────────────────────────────────────────

def test_multi_faction_with_diplomatic_stances():
    rng = random.Random(7)
    factions = _two_factions(rng)
    factions["player"].attack_confidence = 0.42
    factions["faction_1"].attack_confidence = 0.77
    factions["player"].tech_level = 23.5
    factions["faction_1"].tech_level = 19.1
    w = _empty_world()
    payload = serialize_world(w, factions=factions, chronicle_entries=[],
                              tick=0, era_id="settled_reach")
    f2 = deserialize_world(payload)["factions"]
    assert set(f2.keys()) == {"player", "faction_1"}
    p = f2["player"]
    assert p.archetype == "player_civilization"
    assert p.budget == 12.5
    assert p.color == "#4a9eff"
    assert p.attack_confidence == pytest.approx(0.42)
    assert p.tech_level == pytest.approx(23.5)
    assert p.modifiers == {"military": 0.02}
    assert p.diplomatic_stance == {"faction_1": "hostile"}
    assert f2["faction_1"].diplomatic_stance == {"player": "hostile"}


# ── 7. Chronicle ──────────────────────────────────────────────────────────────

def test_chronicle_entries_verbatim():
    entries = [
        ScrollEntry(
            base_text="The Quiet Reach fell to silence.",
            expanded_text="In the long quiet, the Quiet Reach fell to silence beneath drift.",
            cluster_type="fall",
            category="region",
            fragment_ids=["frag_001", "frag_002"],
            resolved_slots={"region": "ra"},
            source_events=[{"tick": 5, "kind": "tier_collapse"}],
            region_id="ra",
            tick_range=(3, 7),
            mentions=[{"kind": "region", "id": "ra", "start": 4, "end": 15}],
            expanded_mentions=[{"kind": "region", "id": "ra", "start": 16, "end": 27}],
        ),
        ScrollEntry(
            base_text="Faction 1 marched.",
            expanded_text="Faction 1 marched in winter.",
            cluster_type="advance",
            category="faction",
        ),
    ]
    w = _empty_world()
    payload = serialize_world(w, factions={}, chronicle_entries=entries,
                              tick=0, era_id="settled_reach")
    c2 = deserialize_world(payload)["chronicle_entries"]
    assert len(c2) == 2
    assert c2[0].base_text == entries[0].base_text
    assert c2[0].expanded_text == entries[0].expanded_text
    assert c2[0].cluster_type == entries[0].cluster_type
    assert c2[0].fragment_ids == entries[0].fragment_ids
    assert c2[0].resolved_slots == entries[0].resolved_slots
    assert c2[0].source_events == entries[0].source_events
    assert c2[0].tick_range == (3, 7)
    assert c2[0].mentions == entries[0].mentions
    assert c2[0].expanded_mentions == entries[0].expanded_mentions
    assert c2[1].base_text == "Faction 1 marched."


# ── 7b. Stances (full fidelity) ───────────────────────────────────────────────

def test_stances_full_fidelity_roundtrip():
    stances = {
        ("player", "faction_1"): {
            "stance": "cooperative",
            "non_aggression_ticks": 42,
            "cooperative_since_tick": 13,
        },
        ("player", "faction_2"): {
            "stance": "hostile",
            "non_aggression_ticks": 0,
            "cooperative_since_tick": None,
        },
    }
    payload = serialize_world(_empty_world(), factions={}, chronicle_entries=[],
                              tick=0, era_id="settled_reach", stances=stances)
    assert deserialize_world(payload)["stances"] == stances


def test_stances_omitted_in_payload_loads_as_empty():
    payload = serialize_world(_empty_world(), factions={}, chronicle_entries=[],
                              tick=0, era_id="settled_reach")
    assert deserialize_world(payload)["stances"] == {}


def test_stances_payload_is_json_safe():
    stances = {
        ("a", "b"): {"stance": "neutral", "non_aggression_ticks": 5,
                     "cooperative_since_tick": None},
    }
    payload = serialize_world(_empty_world(), factions={}, chronicle_entries=[],
                              tick=0, era_id="settled_reach", stances=stances)
    payload2 = json.loads(json.dumps(payload))
    assert deserialize_world(payload2)["stances"] == stances


# ── 8. RNG state ──────────────────────────────────────────────────────────────

def test_rng_state_preserved():
    w = _two_region_world()
    # Burn the RNG a bit before save so its state is non-default.
    [w.rng.random() for _ in range(50)]
    expected_next = w.rng.random()
    # Restore state-before-burn so save captures pre-burn state.
    # Actually simpler: capture state, serialize, deserialize, compare next draws.
    pre_state = w.rng.getstate()
    payload = serialize_world(w, factions={}, chronicle_entries=[],
                              tick=0, era_id="settled_reach")
    # Reset the original to pre-save state to compare apples-to-apples.
    w.rng.setstate(pre_state)
    w2 = deserialize_world(payload)["world"]
    # The two RNGs should draw identical sequences from here.
    draws_orig = [w.rng.random() for _ in range(20)]
    draws_loaded = [w2.rng.random() for _ in range(20)]
    assert draws_orig == draws_loaded
    # Unused so pyflakes doesn't complain.
    _ = expected_next


# ── 9. JSON safety ────────────────────────────────────────────────────────────

def test_payload_is_json_safe():
    rng = random.Random(9)
    factions = _two_factions(rng)
    w = _two_region_world()
    entries = [ScrollEntry(base_text="t", expanded_text="t", cluster_type="x",
                           category="region", tick_range=(0, 1))]
    payload = serialize_world(w, factions=factions, chronicle_entries=entries,
                              tick=4, era_id="settled_reach")
    # json.dumps must not raise. Round-trip through string to prove it.
    s = json.dumps(payload)
    assert isinstance(s, str)
    payload2 = json.loads(s)
    r = deserialize_world(payload2)
    assert r["world"].regions["ra"].id == "ra"
    assert set(r["factions"].keys()) == {"player", "faction_1"}
    assert r["tick"] == 4
    assert r["era_id"] == "settled_reach"
    assert r["chronicle_entries"][0].tick_range == (0, 1)


# ── 10. Version error ─────────────────────────────────────────────────────────

def test_unknown_version_raises_save_version_error():
    payload = serialize_world(_empty_world(), factions={}, chronicle_entries=[],
                              tick=0, era_id="settled_reach")
    payload["save_version"] = 999
    with pytest.raises(SaveVersionError):
        deserialize_world(payload)


# ── 11. Integration: world + ticks ────────────────────────────────────────────

def test_world_roundtrip_after_ticks():
    # Build a real world, tick a few times, save, load, verify all surface state.
    w = generate_random(seed=123)
    factions = {f.id: f for f in generate_starting_factions(rng=random.Random(123), world=w)}
    # Touch some state so it's non-default.
    factions["player"].budget = 50.0
    w.regions[list(w.regions)[0]].held_since_tick = 3

    payload = serialize_world(w, factions=factions, chronicle_entries=[],
                              tick=7, era_id="settled_reach")
    s = json.dumps(payload)
    payload2 = json.loads(s)
    result = deserialize_world(payload2)
    w2 = result["world"]
    f2 = result["factions"]

    assert result["tick"] == 7
    assert set(w2.regions.keys()) == set(w.regions.keys())
    for rid, r in w.regions.items():
        r2 = w2.regions[rid]
        assert r2.fields == r.fields
        assert r2.faction_id == r.faction_id
        assert r2.tier == r.tier
        assert r2.held_since_tick == r.held_since_tick
    assert set(f2.keys()) == set(factions.keys())
    for fid, f in factions.items():
        assert f2[fid].budget == pytest.approx(f.budget)
        assert f2[fid].archetype == f.archetype
        assert f2[fid].attack_confidence == pytest.approx(f.attack_confidence)
        assert f2[fid].tech_level == pytest.approx(f.tech_level)


# ── Helpers for new subsystem tests ──────────────────────────────────────────

def _minimal_payload(**kwargs):
    w = _empty_world()
    base = dict(naming_system=None, ledger=None, gen_state=None,
                pending_queue=None, player_lineage_id=None)
    base.update(kwargs)
    return serialize_world(w, factions={}, chronicle_entries=[],
                           tick=0, era_id="settled_reach", **base)


def _fresh_ns():
    ns = NamingSystem()
    ns.load_pool("f1", "people", ["Alice", "Bob", "Carol", "Dave", "Eve"])
    ns.load_pool("f1", "places", ["Northmark", "Southport"])
    return ns


def _fresh_ledger(ns):
    return CoherenceLedger(ns)


# ── NamingSystem isolation ────────────────────────────────────────────────────

def test_naming_system_pools_roundtrip():
    ns = _fresh_ns()
    ns.load_pool("f2", "people", ["Xavier", "Yara"])
    payload = _minimal_payload(naming_system=ns)
    restored = deserialize_world(payload)["naming_system"]
    assert restored._pools[("f1", "people")] == ["Alice", "Bob", "Carol", "Dave", "Eve"]
    assert restored._pools[("f1", "places")] == ["Northmark", "Southport"]
    assert restored._pools[("f2", "people")] == ["Xavier", "Yara"]
    name = restored.get_name("f1", "people", current_tick=0, rng=random.Random(0))
    assert name in ["Alice", "Bob", "Carol", "Dave", "Eve"]


def test_naming_system_in_use_and_cooldowns_roundtrip():
    ns = _fresh_ns()
    ns.load_pool("f1", "people", ["Alice", "Bob", "Carol", "Dave", "Eve"])
    # Mark Alice in use
    ns._in_use["Alice"] = "f1"
    # Bob released at tick=50 with cooldown 100 → expiry 150
    ns._cooldowns["Bob"] = 150
    payload = _minimal_payload(naming_system=ns)
    r = deserialize_world(payload)["naming_system"]
    assert r._in_use == {"Alice": "f1"}
    assert r._cooldowns == {"Bob": 150}
    assert r.is_available("Alice", current_tick=200) is False
    assert r.is_available("Bob", current_tick=149) is False
    assert r.is_available("Bob", current_tick=151) is True


def test_naming_system_subsets_and_schism_parents_roundtrip():
    ns = _fresh_ns()
    parent_subset = {
        "linguistic_roots": ["Semitic triconsonantal", "Polynesian open syllables"],
        "phoneme_patterns": ["patronymic"],
        "cultural_flavor_tags": ["martial"],
    }
    ns.set_variable_subset("parent_f", parent_subset)
    ns._schism_parents["child_f"] = "parent_f"
    ns._schism_parents["grandchild_f"] = "child_f"
    ns.load_pool("parent_f", "people", ["Amara", "Beka", "Celo"])
    payload = _minimal_payload(naming_system=ns)
    r = deserialize_world(payload)["naming_system"]
    assert r.get_variable_subset("parent_f") == parent_subset
    assert r._schism_parents == {"child_f": "parent_f", "grandchild_f": "child_f"}
    r.derive_schism_subset("parent_f", "new_child", rng=random.Random(0))
    assert r.get_variable_subset("new_child") is not None


# ── CoherenceLedger isolation ─────────────────────────────────────────────────

def test_ledger_characters_roundtrip():
    ns = _fresh_ns()
    ledger = _fresh_ledger(ns)
    rng = random.Random(1)
    # Active character
    c1 = CharacterRecord("char_1", "Alice", "f1", "ra", "supreme_commander",
                         born_tick=0, lifespan_ticks=200)
    c1.event_history = ["evt_01", "evt_02"]
    c1.rival_of = ["char_99"]
    ledger._characters["char_1"] = c1
    ledger._next_char_id = 1
    # Historical character with parent
    c2 = CharacterRecord("char_2", "Bob", "f1", "ra", "regional_commander",
                         born_tick=10, lifespan_ticks=100, parent_id="char_1")
    c2.status = "historical"
    c2.death_tick = 110
    c2.lineage_id = "lineage_1"
    c1.children_ids = ["char_2"]
    ledger._characters["char_2"] = c2
    ledger._next_char_id = 2

    payload = _minimal_payload(ledger=ledger, naming_system=ns)
    r = deserialize_world(payload)["ledger"]

    rc1 = r.get_character_by_id("char_1")
    assert rc1 is not None
    assert rc1.name == "Alice"
    assert rc1.rank == "supreme_commander"
    assert rc1.status == "active"
    assert rc1.event_history == ["evt_01", "evt_02"]
    assert rc1.rival_of == ["char_99"]
    assert rc1.children_ids == ["char_2"]
    rc2 = r.get_character_by_id("char_2")
    assert rc2.status == "historical"
    assert rc2.death_tick == 110
    assert rc2.lineage_id == "lineage_1"
    assert rc2.parent_id == "char_1"

    in_region = r.get_characters_in_region("ra")
    assert any(c.id == "char_1" for c in in_region)


def test_ledger_lineages_and_main_character_ids_roundtrip():
    ns = _fresh_ns()
    ledger = _fresh_ledger(ns)
    c1 = CharacterRecord("char_1", "Alice", "f1", "ra", "supreme_commander",
                         born_tick=0, lifespan_ticks=200)
    c2 = CharacterRecord("char_2", "Bob", "f1", "rb", "lineage_member",
                         born_tick=5, lifespan_ticks=100)
    c3 = CharacterRecord("char_3", "Carol", "f1", "ra", "lineage_member",
                         born_tick=10, lifespan_ticks=80)
    c3.status = "historical"
    ledger._characters = {"char_1": c1, "char_2": c2, "char_3": c3}
    ledger._next_char_id = 3
    ledger._lineages["lineage_1"] = {
        "root_id": "char_1",
        "member_ids": ["char_1", "char_2", "char_3"],
    }
    ledger._next_lineage_id = 1
    ledger._main_character_ids = {"char_1"}

    payload = _minimal_payload(ledger=ledger, naming_system=ns)
    r = deserialize_world(payload)["ledger"]

    assert isinstance(r._main_character_ids, set)
    assert "char_1" in r._main_character_ids
    members = r.get_lineage_members("lineage_1")
    assert len(members) == 3
    statuses = {m.id: m.status for m in members}
    assert statuses["char_3"] == "historical"


def test_ledger_archetype_history_and_chapter_counts_roundtrip():
    ns = _fresh_ns()
    ledger = _fresh_ledger(ns)
    ledger.record_archetype("lineage_1", "conqueror")
    ledger.record_archetype("lineage_1", "conqueror")
    ledger.record_archetype("lineage_1", "fortifier")
    ledger.increment_chapter("lineage_1")
    ledger.increment_chapter("lineage_1")
    ledger.increment_chapter("lineage_2")

    payload = _minimal_payload(ledger=ledger, naming_system=ns)
    r = deserialize_world(payload)["ledger"]

    assert r.get_lineage_archetype_history("lineage_1") == {"conqueror": 2, "fortifier": 1}
    assert r.get_chapter_count("lineage_1") == 2
    assert r.get_chapter_count("lineage_2") == 1


def test_ledger_counter_continuity_post_restore():
    ns = _fresh_ns()
    ledger = _fresh_ledger(ns)
    # Create 5 chars + 2 lineages manually to set counters
    for i in range(1, 6):
        c = CharacterRecord(f"char_{i}", f"Name{i}", "f1", "ra",
                            "lineage_member", born_tick=0, lifespan_ticks=100)
        ledger._characters[f"char_{i}"] = c
    ledger._next_char_id = 5
    for i in range(1, 3):
        ledger._lineages[f"lineage_{i}"] = {"root_id": f"char_{i}", "member_ids": [f"char_{i}"]}
    ledger._next_lineage_id = 2

    payload = _minimal_payload(ledger=ledger, naming_system=ns)
    r = deserialize_world(payload)["ledger"]

    new_char = r.create_character("f1", "ra", "lineage_member", tick=0,
                                  rng=random.Random(0))
    assert new_char is not None
    assert new_char.id == "char_6"
    new_lin = r.create_lineage(new_char.id)
    assert new_lin == "lineage_3"


def test_ledger_naming_system_reference():
    ns = _fresh_ns()
    ledger = _fresh_ledger(ns)
    payload = _minimal_payload(ledger=ledger, naming_system=ns)
    result = deserialize_world(payload)
    assert result["ledger"]._naming is result["naming_system"]


# ── GenerationalState isolation ────────────────────────────────────────────────

def test_gen_state_roundtrip_and_default_chapter_replaced():
    gs = GenerationalState("player", start_tick=0)
    gs.current_chapter["character_id"] = "char_1"
    gs.current_chapter["end_tick"] = 50
    gs.current_chapter["end_reason"] = "test_end"
    gs._start_chapter("player", 50)
    gs.current_chapter["character_id"] = "char_2"
    gs.current_chapter["end_tick"] = 100
    gs.current_chapter["end_reason"] = "test_end_2"
    gs._start_chapter("player", 100)
    gs.current_chapter["character_id"] = "char_3"

    payload = _minimal_payload(gen_state=gs)
    r = deserialize_world(payload)["gen_state"]

    assert len(r.chapters) == 3
    assert r.current_chapter_index == 2
    assert r.player_faction_id == "player"
    assert r.chapters[0]["character_id"] == "char_1"
    assert r.chapters[1]["character_id"] == "char_2"
    assert r.chapters[2]["character_id"] == "char_3"


def test_gen_state_current_chapter_property_works_post_restore():
    gs = GenerationalState("player", start_tick=0)
    gs._start_chapter("player", 10)
    gs._start_chapter("player", 20)
    # current_chapter_index == 2
    assert gs.current_chapter_index == 2

    payload = _minimal_payload(gen_state=gs)
    r = deserialize_world(payload)["gen_state"]

    assert r.current_chapter["chapter_number"] == 3
    assert r.chapter_count == 3


# ── PendingQueue isolation ────────────────────────────────────────────────────

def _sample_entry(due_tick, template_id="evt_test"):
    return {
        "template_id": template_id,
        "region_id": "ra",
        "due_tick": due_tick,
        "probability": 0.5,
        "conditions": {},
        "chain_tag": "chain_0001",
        "source_faction_id": "f1",
        "chain_start_tick": 0,
    }


def test_pending_queue_data_roundtrip():
    pq = PendingQueue()
    pq.enqueue(_sample_entry(5))
    pq.enqueue(_sample_entry(10))
    pq.enqueue(_sample_entry(10, "evt_other"))
    pq.enqueue(_sample_entry(20))

    payload = _minimal_payload(pending_queue=pq)
    r = deserialize_world(payload)["pending_queue"]
    assert r.size() == 4


def test_pending_queue_due_this_tick_post_restore():
    pq = PendingQueue()
    pq.enqueue(_sample_entry(5))
    pq.enqueue(_sample_entry(10))
    pq.enqueue(_sample_entry(10, "evt_other"))
    pq.enqueue(_sample_entry(20))

    payload = _minimal_payload(pending_queue=pq)
    r = deserialize_world(payload)["pending_queue"]
    due = r.due_this_tick(10)
    assert len(due) == 2
    assert all(e["due_tick"] == 10 for e in due)


# ── Edge cases ────────────────────────────────────────────────────────────────

def test_empty_subsystems_roundtrip():
    ns = NamingSystem()
    ledger = CoherenceLedger(ns)
    pq = PendingQueue()
    gs = GenerationalState("player", start_tick=0)

    payload = _minimal_payload(naming_system=ns, ledger=ledger, gen_state=gs,
                               pending_queue=pq, player_lineage_id=None)
    r = deserialize_world(payload)

    assert r["naming_system"]._pools == {}
    assert r["ledger"]._characters == {}
    assert r["ledger"]._lineages == {}
    assert r["pending_queue"].size() == 0
    assert len(r["gen_state"].chapters) == 1
    assert r["player_lineage_id"] is None


def test_player_lineage_id_roundtrip():
    payload = _minimal_payload(player_lineage_id="lineage_42")
    assert deserialize_world(payload)["player_lineage_id"] == "lineage_42"

    payload_none = _minimal_payload(player_lineage_id=None)
    assert deserialize_world(payload_none)["player_lineage_id"] is None


# ── trigger_state + noise_offsets isolation (D1) ──────────────────────────────

def test_trigger_state_edge_active_roundtrips():
    # Edge-dedupe state: bool per (region, template_id). True = threshold currently breached.
    ts = {"ra": {"evt_garrison_collapse": True, "evt_famine": False}}
    payload = _minimal_payload(trigger_state=ts)
    r = deserialize_world(payload)
    assert r["trigger_state"] == {"ra": {"evt_garrison_collapse": True,
                                          "evt_famine": False}}
    # Exact bool types — not 1/0 ints.
    assert r["trigger_state"]["ra"]["evt_garrison_collapse"] is True
    assert r["trigger_state"]["ra"]["evt_famine"] is False


def test_trigger_state_revolt_cooldown_roundtrips():
    # Cooldown state: int last-fired-tick under "<tid>_cooldown" key.
    ts = {"ra": {"evt_regional_revolt_cooldown": 47}}
    payload = _minimal_payload(trigger_state=ts)
    r = deserialize_world(payload)
    assert r["trigger_state"] == {"ra": {"evt_regional_revolt_cooldown": 47}}
    # Exact int type preserved through JSON.
    assert isinstance(r["trigger_state"]["ra"]["evt_regional_revolt_cooldown"], int)
    assert r["trigger_state"]["ra"]["evt_regional_revolt_cooldown"] == 47


def test_noise_offsets_roundtrips_exact_floats():
    # Per-region per-template threshold jitter in [-EVENT_NOISE_RANGE, +EVENT_NOISE_RANGE].
    offsets = {
        "ra": {"evt_garrison_collapse": -1.5, "evt_trade_boom": 2.3},
        "rb": {"evt_garrison_collapse": 0.0},
    }
    payload = _minimal_payload(noise_offsets=offsets)
    r = deserialize_world(payload)
    assert r["noise_offsets"]["ra"]["evt_garrison_collapse"] == -1.5
    assert r["noise_offsets"]["ra"]["evt_trade_boom"] == 2.3
    assert r["noise_offsets"]["rb"]["evt_garrison_collapse"] == 0.0
    # Float type preserved (not int 0).
    assert isinstance(r["noise_offsets"]["rb"]["evt_garrison_collapse"], float)


def test_trigger_state_and_noise_offsets_default_empty_when_absent():
    # Back-compat: payload that doesn't carry the keys should restore as {} not KeyError.
    payload = _minimal_payload()
    # Simulate a payload that never had the new keys written.
    payload.pop("trigger_state", None)
    payload.pop("noise_offsets", None)
    r = deserialize_world(payload)
    assert r["trigger_state"] == {}
    assert r["noise_offsets"] == {}


# ── trigger_state + noise_offsets behavior / drift prevention (D1) ────────────

def test_resume_prevents_event_re_fire():
    """Drift test: after save+restore, an already-active threshold must NOT re-fire.

    Fixture variables: single region "ra", military=20 (< threshold 30), no jitter,
    tier="home", faction_id="player", tick=10 (past EVENT_GRACE_PERIOD=3).
    trigger_state pre-set with evt_garrison_collapse=True (edge already active pre-save).
    """
    import events as _events

    fields = {"military": 20.0, "economy": 60.0, "tension": 20.0, "population": 40.0}
    region = Region("ra", "Region A", "home", fields, faction_id="player")
    # No jitter: threshold stays 30; military 20 < 30 stays "active".
    offsets = {"ra": {"evt_garrison_collapse": 0.0}}
    ts_pre = {"ra": {"evt_garrison_collapse": True}}

    payload = _minimal_payload(trigger_state=ts_pre, noise_offsets=offsets)
    r = deserialize_world(payload)

    fired = _events.evaluate_triggers(
        region, r["noise_offsets"], r["trigger_state"], tick=11)
    assert "evt_garrison_collapse" not in fired, (
        "garrison_collapse re-fired despite was_active=True pre-restore — "
        "trigger_state dedupe lost across save/restore")

    # Fixture-proof sub-case: same fields + offsets, EMPTY trigger_state.
    # Confirms the field/threshold setup actually triggers when not deduped —
    # so the assertion above is detecting dedupe behavior, not a broken fixture.
    fired_no_dedupe = _events.evaluate_triggers(
        region, offsets, {}, tick=11)
    assert "evt_garrison_collapse" in fired_no_dedupe, (
        "fixture broken: garrison_collapse did NOT fire with empty trigger_state; "
        "field/threshold setup is wrong")


def test_resume_prevents_revolt_immediate_refire():
    """Drift test: revolt cooldown survives save+restore; revolt cannot fire inside window.

    Fixture variables: single region "ra", tension=99 (max revolt probability),
    tier="home", faction_id="player", save at tick=10 with cooldown_key=10,
    evaluate at tick=11 (diff 1 < REVOLT_COOLDOWN_TICKS=12 → must block).
    """
    import events as _events
    import config as _config

    fields = {"military": 50.0, "economy": 50.0, "tension": 99.0, "population": 50.0}
    region = Region("ra", "Region A", "home", fields, faction_id="player")
    # Threshold-mode revolt template has trigger_field=None, so noise_offsets entry not strictly needed.
    offsets = {"ra": {}}
    ts_pre = {"ra": {"evt_regional_revolt_cooldown": 10}}

    payload = _minimal_payload(trigger_state=ts_pre, noise_offsets=offsets)
    r = deserialize_world(payload)

    # Verify cooldown int survived.
    assert r["trigger_state"]["ra"]["evt_regional_revolt_cooldown"] == 10

    # Evaluate at tick=11: 11 - 10 = 1 < REVOLT_COOLDOWN_TICKS, so revolt MUST be blocked
    # regardless of rng. Use seed=0 for determinism.
    fired = _events.evaluate_triggers(
        region, r["noise_offsets"], r["trigger_state"],
        tick=11, rng=random.Random(0))
    assert "evt_regional_revolt" not in fired, (
        "revolt fired inside cooldown window — cooldown state lost across save/restore")
    assert _config.REVOLT_COOLDOWN_TICKS > 1, (
        "fixture invariant violated: REVOLT_COOLDOWN_TICKS must be >1 for this test")


# ── Integration ───────────────────────────────────────────────────────────────

def test_resume_continues_simulation():
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from pipe_transport import _setup_sim_env
    import tick as _tick
    import events as _events

    # Baseline: fresh env, run 20 ticks, assert at least 1 character
    sim_env = _setup_sim_env(seed=42)
    for i in range(20):
        t = sim_env["current_tick"] + 1
        _tick.run_tick(
            sim_env["world"], t,
            pending_queue=sim_env["pending_queue"],
            noise_offsets=sim_env["noise_offsets"],
            trigger_state=sim_env["trigger_state"],
            registry=sim_env["registry"],
            stances=sim_env.get("stances", {}),
            pending_telegraphs=sim_env.get("pending_telegraphs", []),
            coherence_ledger=sim_env.get("ledger"),
        )
        sim_env["current_tick"] = t

    baseline_char_count = sim_env["ledger"].active_character_count() + sim_env["ledger"].historical_character_count()
    assert baseline_char_count >= 1, "baseline: expected at least 1 character after 20 ticks"

    # Serialize
    payload = serialize_world(
        sim_env["world"],
        factions=sim_env["registry"],
        chronicle_entries=sim_env.get("chronicle_entries", []),
        tick=sim_env["current_tick"],
        era_id=sim_env.get("era_id", "settled_reach"),
        stances=sim_env.get("stances", {}),
        naming_system=sim_env.get("ns"),
        ledger=sim_env.get("ledger"),
        gen_state=sim_env.get("gen_state"),
        pending_queue=sim_env.get("pending_queue"),
        player_lineage_id=sim_env.get("player_lineage_id"),
    )

    # Build fresh env with different seed — proves restore, not fresh state
    restored_env = _setup_sim_env(seed=99)
    result = deserialize_world(payload)

    restored_env["world"] = result["world"]
    restored_env["registry"] = result["factions"]
    restored_env["ns"] = result["naming_system"]
    restored_env["ledger"] = result["ledger"]
    restored_env["gen_state"] = result["gen_state"]
    restored_env["pending_queue"] = result["pending_queue"]
    restored_env["current_tick"] = result["tick"]
    restored_env["chronicle_entries"] = result["chronicle_entries"]
    restored_env["stances"] = result["stances"]
    restored_env["player_lineage_id"] = result["player_lineage_id"]
    # D1: noise_offsets + trigger_state are persisted; use the restored values
    # (not a re-roll, not an empty dict). This prevents event re-fire on resume.
    restored_env["noise_offsets"] = result["noise_offsets"]
    restored_env["trigger_state"] = result["trigger_state"]

    # Run 20 more ticks on restored env — no exceptions
    for i in range(20):
        t = restored_env["current_tick"] + 1
        _tick.run_tick(
            restored_env["world"], t,
            pending_queue=restored_env["pending_queue"],
            noise_offsets=restored_env["noise_offsets"],
            trigger_state=restored_env["trigger_state"],
            registry=restored_env["registry"],
            stances=restored_env.get("stances", {}),
            pending_telegraphs=restored_env.get("pending_telegraphs", []),
            coherence_ledger=restored_env.get("ledger"),
        )
        restored_env["current_tick"] = t

    post_restore_count = (restored_env["ledger"].active_character_count()
                          + restored_env["ledger"].historical_character_count())
    assert post_restore_count >= baseline_char_count, (
        f"characters dropped: {baseline_char_count} → {post_restore_count}")


# ── Failure paths ─────────────────────────────────────────────────────────────

def test_save_version_mismatch_raises():
    payload = _minimal_payload()
    payload["save_version"] = 1
    with pytest.raises(SaveVersionError):
        deserialize_world(payload)
    payload["save_version"] = 99
    with pytest.raises(SaveVersionError):
        deserialize_world(payload)


# ── JSON-safety ───────────────────────────────────────────────────────────────

def test_full_payload_is_json_safe():
    ns = _fresh_ns()
    ns._in_use["Alice"] = "f1"
    ns._cooldowns["Bob"] = 150
    ns.set_variable_subset("f1", {"linguistic_roots": ["Semitic triconsonantal"],
                                   "phoneme_patterns": ["patronymic"],
                                   "cultural_flavor_tags": ["martial"]})
    ns._schism_parents["f2"] = "f1"

    ledger = CoherenceLedger(ns)
    c1 = CharacterRecord("char_1", "Alice", "f1", "ra", "supreme_commander",
                         born_tick=0, lifespan_ticks=200)
    ledger._characters["char_1"] = c1
    ledger._next_char_id = 1
    ledger._main_character_ids = {"char_1"}
    ledger.record_archetype("lineage_1", "conqueror")
    ledger.increment_chapter("lineage_1")

    gs = GenerationalState("player", start_tick=0)

    pq = PendingQueue()
    pq.enqueue(_sample_entry(10))

    w = _two_region_world()
    rng = random.Random(5)
    factions = _two_factions(rng)
    entries = [ScrollEntry(base_text="t", expanded_text="t", cluster_type="x",
                           category="region", tick_range=(0, 1))]

    trigger_state = {
        "ra": {"evt_garrison_collapse": True, "evt_famine": False,
                "evt_regional_revolt_cooldown": 7},
        "rb": {"evt_garrison_collapse": False},
    }
    noise_offsets = {
        "ra": {"evt_garrison_collapse": -1.25, "evt_trade_boom": 3.5},
        "rb": {"evt_garrison_collapse": 0.0},
    }

    payload = serialize_world(
        w, factions=factions, chronicle_entries=entries,
        tick=5, era_id="settled_reach",
        naming_system=ns, ledger=ledger, gen_state=gs,
        pending_queue=pq, player_lineage_id="lineage_1",
        trigger_state=trigger_state, noise_offsets=noise_offsets,
    )

    s = json.dumps(payload)
    assert isinstance(s, str)

    payload2 = json.loads(s)
    result = deserialize_world(payload2)
    assert result["naming_system"]._in_use == {"Alice": "f1"}
    assert result["ledger"].get_character_by_id("char_1").name == "Alice"
    assert result["gen_state"].chapter_count == 1
    assert result["pending_queue"].size() == 1
    assert result["player_lineage_id"] == "lineage_1"
    # D1: trigger_state + noise_offsets survive JSON roundtrip with type identity.
    assert result["trigger_state"]["ra"]["evt_garrison_collapse"] is True
    assert result["trigger_state"]["ra"]["evt_famine"] is False
    assert isinstance(result["trigger_state"]["ra"]["evt_regional_revolt_cooldown"], int)
    assert result["trigger_state"]["ra"]["evt_regional_revolt_cooldown"] == 7
    assert result["noise_offsets"]["ra"]["evt_garrison_collapse"] == -1.25
    assert isinstance(result["noise_offsets"]["rb"]["evt_garrison_collapse"], float)
