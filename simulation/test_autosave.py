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
    w, factions, entries, tick, era, stances = deserialize_world(inner)
    assert "ra" in w.regions
    assert "player" in factions
    assert entries[0].base_text == "A reach holds."
    assert tick == 12
    assert era == "settled_reach"
    assert stances == sim_env["stances"]
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
    _, _, entries, _, _, stances = deserialize_world(raw["sim_state"])
    assert entries == []
    assert stances == {}
