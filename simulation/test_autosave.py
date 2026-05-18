import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import config
from save.autosave import autosave_world_view
from save.world_serializer import deserialize_world
from world import World
from region import Region
from faction import Faction
from chronicle_assembler import ScrollEntry
from naming_system import NamingSystem
from coherence_ledger import CoherenceLedger, CharacterRecord
from generational import GenerationalState
from events import PendingQueue


def _sim_env(tmp_path):
    fields = {"military": 50.0, "economy": 60.0, "tension": 20.0, "population": 40.0}
    region = Region("ra", "Region A", "home", fields, faction_id="player")
    world = World(regions={"ra": region}, adjacency={"ra": []}, edge_types={}, seed=0)
    rng = random.Random(0)
    faction = Faction("player", "Player", "player_civilization",
                      budget=12.5, diplomatic_stance={}, rng=rng)
    entry = ScrollEntry(base_text="A reach holds.", expanded_text="A reach holds.",
                       cluster_type="hold", category="region",
                       region_id="ra", tick_range=(0, 1))
    return {
        "world": world,
        "registry": {"player": faction},
        "chronicle_entries": [entry],
        "stances": {("player", "faction_1"): {"stance": "hostile",
                                              "non_aggression_ticks": 7,
                                              "cooperative_since_tick": None}},
        "current_tick": 12,
        "chapter_num": 2,
        "era_id": "settled_reach",
    }


def _autosave_path(save_root):
    return Path(save_root) / config.AUTOSAVE_SLOT_ID / "sim.json"


def test_autosave_writes_file(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "SAVE_ROOT", str(tmp_path))
    sim_env = _sim_env(tmp_path)
    autosave_world_view(sim_env)
    path = _autosave_path(tmp_path)
    assert path.exists(), f"autosave file missing at {path}"


def test_autosave_payload_roundtrips(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "SAVE_ROOT", str(tmp_path))
    sim_env = _sim_env(tmp_path)
    autosave_world_view(sim_env)
    raw = json.loads(_autosave_path(tmp_path).read_text())
    inner = raw["sim_state"]
    r = deserialize_world(inner)
    assert "ra" in r["world"].regions
    assert "player" in r["factions"]
    assert r["chronicle_entries"][0].base_text == "A reach holds."
    assert r["tick"] == 12
    assert r["era_id"] == "settled_reach"
    assert r["stances"] == sim_env["stances"]
    assert raw["chapter_number"] == 2


def test_autosave_disabled_by_flag(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "SAVE_ROOT", str(tmp_path))
    monkeypatch.setattr(config, "ENABLE_STAGE12_AUTOSAVE", False)
    sim_env = _sim_env(tmp_path)
    autosave_world_view(sim_env)
    assert not _autosave_path(tmp_path).exists()


def test_autosave_with_empty_chronicle_and_stances(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "SAVE_ROOT", str(tmp_path))
    sim_env = _sim_env(tmp_path)
    sim_env["chronicle_entries"] = []
    sim_env["stances"] = {}
    autosave_world_view(sim_env)
    raw = json.loads(_autosave_path(tmp_path).read_text())
    r = deserialize_world(raw["sim_state"])
    assert r["chronicle_entries"] == []
    assert r["stances"] == {}


# ── test 18: autosave full-fidelity roundtrip ─────────────────────────────────

def test_autosave_full_fidelity_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "SAVE_ROOT", str(tmp_path))

    ns = NamingSystem()
    ns.load_pool("player", "people", ["Alpha", "Beta", "Gamma"])
    ns._in_use["Alpha"] = "player"

    ledger = CoherenceLedger(ns)
    c1 = CharacterRecord("char_1", "Alpha", "player", "ra", "supreme_commander",
                         born_tick=0, lifespan_ticks=200)
    ledger._characters["char_1"] = c1
    ledger._next_char_id = 1
    ledger._main_character_ids = {"char_1"}

    gs = GenerationalState("player", start_tick=0)
    gs.current_chapter["character_id"] = "char_1"

    pq = PendingQueue()
    pq.enqueue({
        "template_id": "evt_garrison_collapse",
        "region_id": "ra",
        "due_tick": 15,
        "probability": 0.55,
        "conditions": {},
        "chain_tag": "chain_0001",
        "source_faction_id": "player",
        "chain_start_tick": 5,
    })

    fields = {"military": 50.0, "economy": 60.0, "tension": 20.0, "population": 40.0}
    region = Region("ra", "Region A", "home", fields, faction_id="player")
    world = World(regions={"ra": region}, adjacency={"ra": []}, edge_types={}, seed=0)
    rng = random.Random(0)
    faction = Faction("player", "Player", "player_civilization",
                      budget=12.5, diplomatic_stance={}, rng=rng)

    sim_env = {
        "world": world,
        "registry": {"player": faction},
        "chronicle_entries": [],
        "stances": {},
        "current_tick": 5,
        "chapter_num": 1,
        "era_id": "settled_reach",
        "ns": ns,
        "ledger": ledger,
        "gen_state": gs,
        "pending_queue": pq,
        "player_lineage_id": "lineage_1",
    }

    autosave_world_view(sim_env)
    raw = json.loads(_autosave_path(tmp_path).read_text())
    r = deserialize_world(raw["sim_state"])

    assert r["naming_system"] is not None
    assert r["naming_system"]._in_use == {"Alpha": "player"}
    assert r["ledger"] is not None
    assert r["ledger"].get_character_by_id("char_1").name == "Alpha"
    assert "char_1" in r["ledger"]._main_character_ids
    assert r["gen_state"] is not None
    assert r["gen_state"].current_chapter["character_id"] == "char_1"
    assert r["pending_queue"].size() == 1
    assert r["pending_queue"].due_this_tick(15)[0]["template_id"] == "evt_garrison_collapse"
    assert r["player_lineage_id"] == "lineage_1"


# ── test 19: autosave persists trigger_state + noise_offsets (D1) ─────────────

def test_autosave_includes_trigger_state_and_noise_offsets(tmp_path, monkeypatch):
    """D1 drift fix: autosave file must roundtrip trigger_state + noise_offsets exactly."""
    monkeypatch.setattr(config, "SAVE_ROOT", str(tmp_path))
    sim_env = _sim_env(tmp_path)
    sim_env["trigger_state"] = {
        "ra": {
            "evt_garrison_collapse": True,
            "evt_famine": False,
            "evt_regional_revolt_cooldown": 7,
        }
    }
    sim_env["noise_offsets"] = {
        "ra": {"evt_garrison_collapse": -1.25, "evt_trade_boom": 3.5}
    }
    autosave_world_view(sim_env)
    raw = json.loads(_autosave_path(tmp_path).read_text())
    r = deserialize_world(raw["sim_state"])

    assert r["trigger_state"] == {
        "ra": {
            "evt_garrison_collapse": True,
            "evt_famine": False,
            "evt_regional_revolt_cooldown": 7,
        }
    }
    assert r["trigger_state"]["ra"]["evt_garrison_collapse"] is True
    assert r["trigger_state"]["ra"]["evt_famine"] is False
    assert isinstance(r["trigger_state"]["ra"]["evt_regional_revolt_cooldown"], int)
    assert r["noise_offsets"]["ra"]["evt_garrison_collapse"] == -1.25
    assert r["noise_offsets"]["ra"]["evt_trade_boom"] == 3.5


# ── test 20: autosave persists last_time_jump_messages (BLOCKER 1 Step C) ─────

def test_autosave_persists_last_time_jump_messages(tmp_path, monkeypatch):
    """Resume replay path: sim_env['last_time_jump_messages'] -> top-level JSON key."""
    monkeypatch.setattr(config, "SAVE_ROOT", str(tmp_path))
    sim_env = _sim_env(tmp_path)
    sample = [
        {"type": "time_jump_start", "time_jump_id": "tj_opening", "span_years": 5,
         "total_keyframes": 1, "total_entries": 1,
         "faction_names": {"player": "Player"},
         "ownership_timeline": [{"tick": 5, "ra": "player"}]},
        {"type": "chronicle_entry", "time_jump_id": "tj_opening", "entry_id": "ce_0",
         "tick_range_start": 0, "tick_range_end": 5,
         "base_form": "A reach holds.", "expanded_form": "A reach holds firm."},
        {"type": "keyframe", "time_jump_id": "tj_opening", "keyframe_index": 0,
         "tick": 5, "chronicle_entry_id": "ce_0",
         "regions_snapshot": [{"region_id": "ra", "owner_faction_id": "player",
                               "significance": 0.5, "x": 1.0, "y": 2.0, "z": 0.0}],
         "connections_snapshot": []},
        {"type": "time_jump_end", "time_jump_id": "tj_opening"},
    ]
    sim_env["last_time_jump_messages"] = sample
    autosave_world_view(sim_env)
    raw = json.loads(_autosave_path(tmp_path).read_text())
    assert raw["last_time_jump_messages"] == sample


def test_autosave_last_time_jump_messages_absent_writes_empty(tmp_path, monkeypatch):
    """Backcompat: sim_env without the key -> autosave writes empty list."""
    monkeypatch.setattr(config, "SAVE_ROOT", str(tmp_path))
    sim_env = _sim_env(tmp_path)
    # key intentionally not set
    autosave_world_view(sim_env)
    raw = json.loads(_autosave_path(tmp_path).read_text())
    assert raw.get("last_time_jump_messages", []) == []


def test_autosave_overwrites_prior_last_time_jump_messages(tmp_path, monkeypatch):
    """Last-only semantics: subsequent autosave REPLACES the persisted list,
    not appends. Multi-time-jump campaigns must keep only the most recent
    jump's stream so save size stays bounded."""
    monkeypatch.setattr(config, "SAVE_ROOT", str(tmp_path))
    sim_env = _sim_env(tmp_path)
    first = [{"type": "time_jump_start", "time_jump_id": "tj_opening",
              "span_years": 5, "total_keyframes": 0, "total_entries": 0,
              "faction_names": {}, "ownership_timeline": []},
             {"type": "time_jump_end", "time_jump_id": "tj_opening"}]
    second = [{"type": "time_jump_start", "time_jump_id": "tj_002",
               "span_years": 8, "total_keyframes": 0, "total_entries": 0,
               "faction_names": {}, "ownership_timeline": []},
              {"type": "time_jump_end", "time_jump_id": "tj_002"}]
    sim_env["last_time_jump_messages"] = first
    autosave_world_view(sim_env)
    sim_env["last_time_jump_messages"] = second
    autosave_world_view(sim_env)
    raw = json.loads(_autosave_path(tmp_path).read_text())
    assert raw["last_time_jump_messages"] == second
