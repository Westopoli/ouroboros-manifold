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
    w2, f2, c2, tick2, era2, s2 = deserialize_world(payload)
    assert w2.regions == {}
    assert w2.adjacency == {}
    assert w2.edge_types == {}
    assert f2 == {}
    assert c2 == []
    assert tick2 == 0
    assert era2 == "settled_reach"
    assert s2 == {}


# ── 3. Region fields ──────────────────────────────────────────────────────────

def test_single_region_full_fields():
    fields = {"military": 51.7, "economy": 62.3, "tension": 18.9, "population": 44.1}
    r = Region("ra", "Region A", "home", fields, faction_id="player")
    w = World(regions={"ra": r}, adjacency={"ra": []}, edge_types={}, seed=0)
    payload = serialize_world(w, factions={}, chronicle_entries=[],
                              tick=0, era_id="settled_reach")
    w2, _, _, _, _, _ = deserialize_world(payload)
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
    w2, _, _, _, _, _ = deserialize_world(payload)
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
    w2, _, _, _, _, _ = deserialize_world(payload)
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
    w2, _, _, _, _, _ = deserialize_world(payload)
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
    _, f2, _, _, _, _ = deserialize_world(payload)
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
    _, _, c2, _, _, _ = deserialize_world(payload)
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
    _, _, _, _, _, s2 = deserialize_world(payload)
    assert s2 == stances


def test_stances_omitted_in_payload_loads_as_empty():
    payload = serialize_world(_empty_world(), factions={}, chronicle_entries=[],
                              tick=0, era_id="settled_reach")
    _, _, _, _, _, s2 = deserialize_world(payload)
    assert s2 == {}


def test_stances_payload_is_json_safe():
    stances = {
        ("a", "b"): {"stance": "neutral", "non_aggression_ticks": 5,
                     "cooperative_since_tick": None},
    }
    payload = serialize_world(_empty_world(), factions={}, chronicle_entries=[],
                              tick=0, era_id="settled_reach", stances=stances)
    payload2 = json.loads(json.dumps(payload))
    _, _, _, _, _, s2 = deserialize_world(payload2)
    assert s2 == stances


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
    w2, _, _, _, _, _ = deserialize_world(payload)
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
    w2, f2, c2, tick2, era2, _ = deserialize_world(payload2)
    assert w2.regions["ra"].id == "ra"
    assert set(f2.keys()) == {"player", "faction_1"}
    assert tick2 == 4
    assert era2 == "settled_reach"
    assert c2[0].tick_range == (0, 1)


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
    w2, f2, _, tick2, _, _ = deserialize_world(payload2)

    assert tick2 == 7
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
