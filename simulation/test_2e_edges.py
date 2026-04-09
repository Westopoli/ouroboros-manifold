#!/usr/bin/env python3
import os, sys
os.chdir(os.path.dirname(os.path.abspath(__file__)))

import random, math, config
import world as world_mod
import faction as faction_mod
import diplomacy as _diplomacy
import tick as _tick
from region import Region


def _make_region(rid, tier, fid, rng):
    fields = {"military": 60.0, "economy": 60.0, "tension": 30.0, "population": 60.0}
    r = Region(rid, rid, tier, fields, faction_id=fid)
    r.econ_phase_offset = rng.uniform(0, 2 * math.pi)
    r.tension_phase_offset = rng.uniform(0, 2 * math.pi)
    return r


def _link(adjacency, edge_types, a, b, etype="border"):
    adjacency[a].append(b)
    adjacency[b].append(a)
    edge_types[(a, b)] = etype
    edge_types[(b, a)] = etype


def make_two_faction_world():
    rng = random.Random(42)
    p_home = _make_region("p_home", "home", "player", rng)
    p_front = _make_region("p_front", "frontier", "player", rng)
    c_home = _make_region("c_home", "home", "conqueror", rng)
    c_front = _make_region("c_front", "frontier", "conqueror", rng)
    empty = Region("empty_1", "empty_1", "empty")

    regions = {r.id: r for r in [p_home, p_front, c_home, c_front, empty]}
    adjacency = {rid: [] for rid in regions}
    edge_types = {}

    _link(adjacency, edge_types, "p_home", "p_front", "both")
    _link(adjacency, edge_types, "c_home", "c_front", "both")
    _link(adjacency, edge_types, "p_front", "c_front", "border")
    _link(adjacency, edge_types, "p_front", "empty_1", "border")

    world = world_mod.World(regions, adjacency, edge_types, seed=42)
    registry = {
        "player": faction_mod.Faction("player", "Player", "player_civilization",
                                      budget=50.0,
                                      diplomatic_stance={"conqueror": "neutral"},
                                      rng=rng),
        "conqueror": faction_mod.Faction("conqueror", "Conqueror", "conqueror",
                                         budget=50.0,
                                         diplomatic_stance={"player": "neutral"},
                                         rng=rng),
    }
    return world, registry


def make_three_faction_world():
    rng = random.Random(99)
    p_home = _make_region("p_home", "home", "player", rng)
    c_home = _make_region("c_home", "home", "conqueror", rng)
    f_region = _make_region("f_region", "frontier", "fortifier", rng)
    empty = Region("empty_1", "empty_1", "empty")

    regions = {r.id: r for r in [p_home, c_home, f_region, empty]}
    adjacency = {rid: [] for rid in regions}
    edge_types = {}

    _link(adjacency, edge_types, "p_home", "f_region", "border")
    _link(adjacency, edge_types, "c_home", "f_region", "border")
    _link(adjacency, edge_types, "p_home", "c_home", "both")
    _link(adjacency, edge_types, "c_home", "empty_1", "border")

    world = world_mod.World(regions, adjacency, edge_types, seed=99)
    registry = {
        "player": faction_mod.Faction("player", "Player", "player_civilization",
                                      budget=50.0,
                                      diplomatic_stance={"conqueror": "cooperative", "fortifier": "hostile"},
                                      rng=rng),
        "conqueror": faction_mod.Faction("conqueror", "Conqueror", "conqueror",
                                         budget=50.0,
                                         diplomatic_stance={"player": "cooperative", "fortifier": "hostile"},
                                         rng=rng),
        "fortifier": faction_mod.Faction("fortifier", "Fortifier", "fortifier",
                                         budget=50.0,
                                         diplomatic_stance={"player": "hostile", "conqueror": "hostile"},
                                         rng=rng),
    }
    return world, registry


def test_peace_formation_upgrades_edges():
    """Call check_peace_formation and verify it upgrades shared edges."""
    print("\n=== Test 1: check_peace_formation() upgrades shared edges ===")
    world, registry = make_two_faction_world()
    stances = _diplomacy.init_stances(registry)

    _diplomacy.set_stance(stances, "player", "conqueror", "neutral", tick=0)
    _diplomacy.sync_to_factions(stances, registry)
    key = _diplomacy._pair_key("player", "conqueror")
    stances[key]["non_aggression_ticks"] = config.PEACE_FORMATION_THRESHOLD + 10

    for r in world.regions.values():
        if r.fields:
            r.fields["tension"] = 10.0
            r.fields["economy"] = 80.0
            r.recompute_composites()

    assert world.edge_types[("p_front", "c_front")] == "border"
    print(f"  Before: p_front↔c_front = border")

    # Try seeds until peace forms (probabilistic)
    for seed in range(200):
        # Reset state each attempt
        w, reg = make_two_faction_world()
        st = _diplomacy.init_stances(reg)
        _diplomacy.set_stance(st, "player", "conqueror", "neutral", tick=0)
        _diplomacy.sync_to_factions(st, reg)
        k = _diplomacy._pair_key("player", "conqueror")
        st[k]["non_aggression_ticks"] = config.PEACE_FORMATION_THRESHOLD + 10
        for r in w.regions.values():
            if r.fields:
                r.fields["tension"] = 10.0
                r.fields["economy"] = 80.0
                r.recompute_composites()

        rng = random.Random(seed)
        _diplomacy.check_peace_formation(st, reg, w, rng, tick=100, tick_log={})

        if _diplomacy.get_stance(st, "player", "conqueror") == "cooperative":
            edge = w.edge_types[("p_front", "c_front")]
            assert edge == "both", f"Peace formed but edge is '{edge}', expected 'both'"
            print(f"  After (seed {seed}): p_front↔c_front = {edge}")
            trade_n = w.get_neighbors("p_front", edge_type="trade")
            assert "c_front" in trade_n
            print(f"  Trade neighbors of p_front: {trade_n}")
            print("  PASSED")
            return
    assert False, "Peace never formed in 200 seeds"


def test_betrayal_downgrades_edges():
    """Call check_betrayals and verify it downgrades shared edges."""
    print("\n=== Test 2: check_betrayals() downgrades shared edges ===")

    for seed in range(200):
        world, registry = make_two_faction_world()
        stances = _diplomacy.init_stances(registry)

        # Start cooperative with "both" edges
        _diplomacy.set_stance(stances, "player", "conqueror", "cooperative", tick=0)
        _diplomacy.sync_to_factions(stances, registry)
        world.update_faction_pair_edges("player", "conqueror", "both")
        assert world.edge_types[("p_front", "c_front")] == "both"

        # Make betrayal likely: conqueror is strong, player is weak at border
        world.regions["c_front"].fields["military"] = 95.0
        world.regions["p_front"].fields["military"] = 10.0
        world.regions["c_front"].fields["tension"] = 80.0

        rng = random.Random(seed)
        betrayals = _diplomacy.check_betrayals(stances, registry, world, rng, tick=50)

        if betrayals:
            edge = world.edge_types[("p_front", "c_front")]
            assert edge == "border", f"Betrayal fired but edge is '{edge}', expected 'border'"
            trade_n = world.get_neighbors("p_front", edge_type="trade")
            assert "c_front" not in trade_n
            print(f"  Betrayal at seed {seed}: p_front↔c_front = {edge}")
            print(f"  Trade neighbors of p_front: {trade_n}")
            print("  PASSED")
            return
    assert False, "Betrayal never fired in 200 seeds"


def test_colonization_via_apply_resolved_action():
    """Call _apply_resolved_action with a colonization action and verify edges."""
    print("\n=== Test 3: _apply_resolved_action() colonization sets 'both' edges ===")
    world, registry = make_two_faction_world()

    assert world.edge_types[("p_front", "empty_1")] == "border"
    print(f"  Before: p_front↔empty_1 = border")

    action = {
        "faction_id": "player",
        "action": "colonize",
        "target_region": "empty_1",
        "budget_committed": 10.0,
        "budget_spent": 10.0,
        "outcome_band": "colonize",
        "colonization": {"region_id": "empty_1", "faction_id": "player"},
        "conquest": None,
        "deltas": {},
        "log": {},
        "chain_spawns": [],
    }
    _tick._apply_resolved_action(world, registry, action, None, None, tick_num=10)

    assert world.regions["empty_1"].faction_id == "player"
    assert world.regions["empty_1"].tier == "frontier"
    edge = world.edge_types[("p_front", "empty_1")]
    assert edge == "both", f"Expected 'both', got '{edge}'"
    print(f"  After:  p_front↔empty_1 = {edge}")

    trade_n = world.get_neighbors("empty_1", edge_type="trade")
    assert "p_front" in trade_n
    print(f"  Trade neighbors of empty_1: {trade_n}")
    print("  PASSED")


def test_conquest_via_apply_resolved_action():
    """Call _apply_resolved_action with a conquest action and verify edges."""
    print("\n=== Test 4: _apply_resolved_action() conquest updates edges ===")
    world, registry = make_two_faction_world()

    print(f"  Before: c_front owner=conqueror")
    print(f"    c_front↔c_home  = {world.edge_types[('c_front', 'c_home')]}")
    print(f"    c_front↔p_front = {world.edge_types[('c_front', 'p_front')]}")

    action = {
        "faction_id": "player",
        "action": "attack",
        "target_region": "c_front",
        "budget_committed": 20.0,
        "budget_spent": 20.0,
        "outcome_band": "decisive_victory",
        "conquest": {
            "region_id": "c_front",
            "old_faction_id": "conqueror",
            "new_faction_id": "player",
            "garrison": 15.0,
        },
        "colonization": None,
        "deltas": {"c_front": {"military": -30.0}},
        "log": {},
        "chain_spawns": [],
    }
    _tick._apply_resolved_action(world, registry, action, None, None, tick_num=10)

    assert world.regions["c_front"].faction_id == "player"
    edge_to_player = world.edge_types[("c_front", "p_front")]
    edge_to_conq = world.edge_types[("c_front", "c_home")]
    assert edge_to_player == "both", f"Expected 'both' to conqueror territory, got '{edge_to_player}'"
    assert edge_to_conq == "border", f"Expected 'border' to former owner, got '{edge_to_conq}'"
    print(f"  After: c_front owner=player")
    print(f"    c_front↔p_front = {edge_to_player} (own territory → trade)")
    print(f"    c_front↔c_home  = {edge_to_conq} (former owner → border)")
    print("  PASSED")


def test_conquest_cooperative_partner_via_apply():
    """Conquest near a cooperative partner should upgrade that edge too."""
    print("\n=== Test 5: _apply_resolved_action() conquest upgrades cooperative partner edge ===")
    world, registry = make_three_faction_world()

    print(f"  Before: f_region owner=fortifier")
    print(f"    f_region↔p_home = {world.edge_types[('f_region', 'p_home')]}")
    print(f"    f_region↔c_home = {world.edge_types[('f_region', 'c_home')]}")

    action = {
        "faction_id": "conqueror",
        "action": "attack",
        "target_region": "f_region",
        "budget_committed": 20.0,
        "budget_spent": 20.0,
        "outcome_band": "decisive_victory",
        "conquest": {
            "region_id": "f_region",
            "old_faction_id": "fortifier",
            "new_faction_id": "conqueror",
            "garrison": 15.0,
        },
        "colonization": None,
        "deltas": {"f_region": {"military": -30.0}},
        "log": {},
        "chain_spawns": [],
    }
    _tick._apply_resolved_action(world, registry, action, None, None, tick_num=10)

    assert world.regions["f_region"].faction_id == "conqueror"
    edge_to_conq = world.edge_types[("f_region", "c_home")]
    edge_to_player = world.edge_types[("f_region", "p_home")]
    assert edge_to_conq == "both", f"Expected 'both' to own territory, got '{edge_to_conq}'"
    assert edge_to_player == "both", f"Expected 'both' to cooperative partner, got '{edge_to_player}'"
    print(f"  After: f_region owner=conqueror")
    print(f"    f_region↔c_home = {edge_to_conq} (own territory → trade)")
    print(f"    f_region↔p_home = {edge_to_player} (cooperative partner → trade)")

    trade_n = world.get_neighbors("f_region", edge_type="trade")
    assert "p_home" in trade_n
    assert "c_home" in trade_n
    print(f"    Trade neighbors: {trade_n}")
    print("  PASSED")


def test_colonization_cooperative_partner_via_apply():
    """Colonization near a cooperative partner should upgrade that edge too."""
    print("\n=== Test 6: _apply_resolved_action() colonization upgrades cooperative partner edge ===")
    world, registry = make_three_faction_world()

    # Conqueror colonizes empty_1 (which borders c_home only in this topology)
    # Add an edge from empty_1 to p_home to test the cooperative partner case
    world.adjacency["empty_1"].append("p_home")
    world.adjacency["p_home"].append("empty_1")
    world.edge_types[("empty_1", "p_home")] = "border"
    world.edge_types[("p_home", "empty_1")] = "border"

    print(f"  Before: empty_1↔c_home = {world.edge_types[('empty_1', 'c_home')]}")
    print(f"  Before: empty_1↔p_home = {world.edge_types[('empty_1', 'p_home')]}")

    action = {
        "faction_id": "conqueror",
        "action": "colonize",
        "target_region": "empty_1",
        "budget_committed": 10.0,
        "budget_spent": 10.0,
        "outcome_band": "colonize",
        "colonization": {"region_id": "empty_1", "faction_id": "conqueror"},
        "conquest": None,
        "deltas": {},
        "log": {},
        "chain_spawns": [],
    }
    _tick._apply_resolved_action(world, registry, action, None, None, tick_num=10)

    assert world.regions["empty_1"].faction_id == "conqueror"
    edge_to_conq = world.edge_types[("empty_1", "c_home")]
    edge_to_player = world.edge_types[("empty_1", "p_home")]
    assert edge_to_conq == "both", f"Expected 'both' to own territory, got '{edge_to_conq}'"
    assert edge_to_player == "both", f"Expected 'both' to cooperative partner, got '{edge_to_player}'"
    print(f"  After: empty_1 owner=conqueror")
    print(f"    empty_1↔c_home = {edge_to_conq} (own territory → trade)")
    print(f"    empty_1↔p_home = {edge_to_player} (cooperative partner → trade)")
    print("  PASSED")


if __name__ == "__main__":
    test_peace_formation_upgrades_edges()
    test_betrayal_downgrades_edges()
    test_colonization_via_apply_resolved_action()
    test_conquest_via_apply_resolved_action()
    test_conquest_cooperative_partner_via_apply()
    test_colonization_cooperative_partner_via_apply()
    print(f"\n{'='*60}")
    print("All Phase 2E edge type tests passed.")
    print(f"{'='*60}")
