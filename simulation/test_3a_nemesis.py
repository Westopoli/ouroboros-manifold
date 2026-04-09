#!/usr/bin/env python3
"""Phase 3A — Nemesis detection tests. Exercises the real coherence ledger methods."""
import os, sys, random, math
os.chdir(os.path.dirname(os.path.abspath(__file__)))

import config
import world as world_mod
from region import Region
from coherence_ledger import CoherenceLedger
from naming_system import NamingSystem


def make_test_world():
    """3 regions in a line: r1 — r2 — r3, all owned by different factions."""
    rng = random.Random(42)
    def make(rid, fid):
        fields = {"military": 50.0, "economy": 50.0, "tension": 30.0, "population": 50.0}
        r = Region(rid, rid, "frontier", fields, faction_id=fid)
        r.econ_phase_offset = rng.uniform(0, 2 * math.pi)
        r.tension_phase_offset = rng.uniform(0, 2 * math.pi)
        return r

    r1 = make("r1", "player")
    r2 = make("r2", "enemy")
    r3 = make("r3", "enemy")
    r4 = make("r4", "neutral")

    regions = {r.id: r for r in [r1, r2, r3, r4]}
    adjacency = {"r1": ["r2"], "r2": ["r1", "r3"], "r3": ["r2", "r4"], "r4": ["r3"]}
    edge_types = {
        ("r1", "r2"): "border", ("r2", "r1"): "border",
        ("r2", "r3"): "both", ("r3", "r2"): "both",
        ("r3", "r4"): "border", ("r4", "r3"): "border",
    }
    return world_mod.World(regions, adjacency, edge_types, seed=42)


def make_ledger():
    ns = NamingSystem()
    for fid in ("player", "enemy", "neutral"):
        ns.load_pool(fid, "people", [f"{fid}_name_{i}" for i in range(50)])
    return CoherenceLedger(ns)


def test_tag_rivals():
    """tag_rivals marks enemy characters in a region with the commander's ID."""
    print("\n=== Test 1: tag_rivals() tags enemy characters ===")
    world = make_test_world()
    ledger = make_ledger()
    rng = random.Random(1)

    # Create characters: player commander in r1, enemy officers in r2
    commander = ledger.create_character("player", "r1", "supreme_commander", 0, rng)
    enemy1 = ledger.create_character("enemy", "r2", "regional_commander", 0, rng)
    enemy2 = ledger.create_character("enemy", "r2", "garrison_officer", 0, rng)
    friendly = ledger.create_character("player", "r2", "garrison_officer", 0, rng)

    tagged = ledger.tag_rivals("r2", commander.id, "player")

    assert len(tagged) == 2, f"Expected 2 tagged, got {len(tagged)}"
    assert enemy1 in tagged
    assert enemy2 in tagged
    assert friendly not in tagged
    assert commander.id in enemy1.rival_of
    assert commander.id in enemy2.rival_of
    assert len(friendly.rival_of) == 0
    print(f"  Tagged {len(tagged)} enemies: {[c.name for c in tagged]}")
    print(f"  Friendly not tagged: {friendly.name} rival_of={friendly.rival_of}")

    # Tagging again doesn't duplicate
    tagged2 = ledger.tag_rivals("r2", commander.id, "player")
    assert len(tagged2) == 0, f"Re-tagging should find 0 new, got {len(tagged2)}"
    assert len(enemy1.rival_of) == 1
    print(f"  Re-tag produces 0 duplicates")
    print("  PASSED")


def test_get_nemesis_candidates():
    """get_nemesis_candidates finds characters with rival_of tags matching given commanders."""
    print("\n=== Test 2: get_nemesis_candidates() returns tagged characters ===")
    world = make_test_world()
    ledger = make_ledger()
    rng = random.Random(2)

    cmd1 = ledger.create_character("player", "r1", "supreme_commander", 0, rng)
    cmd2 = ledger.create_character("player", "r1", "supreme_commander", 100, rng)
    enemy_a = ledger.create_character("enemy", "r2", "regional_commander", 0, rng)
    enemy_b = ledger.create_character("enemy", "r3", "regional_commander", 0, rng)
    enemy_c = ledger.create_character("enemy", "r3", "garrison_officer", 0, rng)

    # Tag enemy_a as rival of cmd1, enemy_b as rival of cmd2
    ledger.tag_rivals("r2", cmd1.id, "player")
    ledger.tag_rivals("r3", cmd2.id, "player")

    # Query with just cmd1
    results = ledger.get_nemesis_candidates([cmd1.id])
    assert len(results) == 1
    assert results[0].id == enemy_a.id
    print(f"  Candidates for cmd1: {[c.name for c in results]}")

    # Query with both commanders
    results_both = ledger.get_nemesis_candidates([cmd1.id, cmd2.id])
    ids = {c.id for c in results_both}
    assert enemy_a.id in ids
    assert enemy_b.id in ids
    assert enemy_c.id in ids
    print(f"  Candidates for cmd1+cmd2: {[c.name for c in results_both]}")

    # Empty query
    results_empty = ledger.get_nemesis_candidates([])
    assert len(results_empty) == 0
    print(f"  Empty query returns 0")
    print("  PASSED")


def test_get_descendants():
    """_get_descendants walks the parent→children tree."""
    print("\n=== Test 3: _get_descendants() traverses lineage tree ===")
    ledger = make_ledger()
    rng = random.Random(3)

    root = ledger.create_character("enemy", "r2", "regional_commander", 0, rng)
    lineage_id = ledger.create_lineage(root.id)

    child1 = ledger.create_character("enemy", "r2", "lineage_member", 50, rng,
                                     lineage_id=lineage_id, parent_id=root.id, generation=1)
    child2 = ledger.create_character("enemy", "r3", "lineage_member", 50, rng,
                                     lineage_id=lineage_id, parent_id=root.id, generation=1)
    grandchild = ledger.create_character("enemy", "r3", "lineage_member", 100, rng,
                                         lineage_id=lineage_id, parent_id=child2.id, generation=2)

    descendants = ledger._get_descendants(root.id)
    desc_ids = {d.id for d in descendants}
    assert child1.id in desc_ids
    assert child2.id in desc_ids
    assert grandchild.id in desc_ids
    assert root.id not in desc_ids
    print(f"  Root: {root.name}")
    print(f"  Descendants: {[d.name for d in descendants]} ({len(descendants)} total)")
    print("  PASSED")


def test_nemesis_descendants_in_region():
    """Full pipeline: tag → query nemesis → find descendants near a region."""
    print("\n=== Test 4: get_nemesis_descendants_in_region() full pipeline ===")
    world = make_test_world()
    ledger = make_ledger()
    rng = random.Random(4)

    # Player commander
    cmd = ledger.create_character("player", "r1", "supreme_commander", 0, rng)

    # Enemy nemesis in r2, with descendants spread across r2, r3, r4
    nemesis = ledger.create_character("enemy", "r2", "regional_commander", 0, rng)
    lineage_id = ledger.create_lineage(nemesis.id)

    desc_r2 = ledger.create_character("enemy", "r2", "lineage_member", 50, rng,
                                      lineage_id=lineage_id, parent_id=nemesis.id, generation=1)
    desc_r3 = ledger.create_character("enemy", "r3", "lineage_member", 50, rng,
                                      lineage_id=lineage_id, parent_id=nemesis.id, generation=1)
    desc_r4 = ledger.create_character("enemy", "r4", "lineage_member", 100, rng,
                                      lineage_id=lineage_id, parent_id=desc_r3.id, generation=2)

    # Tag nemesis as rival of commander
    ledger.tag_rivals("r2", cmd.id, "player")

    # Search near r1 with hop_range=1 (reaches r1, r2)
    results_1hop = ledger.get_nemesis_descendants_in_region(
        [cmd.id], "r1", world, hop_range=1)
    ids_1hop = {c.id for c in results_1hop}
    assert nemesis.id in ids_1hop, "Nemesis itself should be a candidate (in r2, 1 hop from r1)"
    assert desc_r2.id in ids_1hop, "Descendant in r2 should be found (1 hop)"
    assert desc_r3.id not in ids_1hop, "Descendant in r3 is 2 hops away"
    assert desc_r4.id not in ids_1hop, "Descendant in r4 is 3 hops away"
    print(f"  hop_range=1 from r1: {[c.name for c in results_1hop]}")

    # Search near r1 with hop_range=2 (reaches r1, r2, r3)
    results_2hop = ledger.get_nemesis_descendants_in_region(
        [cmd.id], "r1", world, hop_range=2)
    ids_2hop = {c.id for c in results_2hop}
    assert desc_r3.id in ids_2hop, "Descendant in r3 should be found (2 hops)"
    assert desc_r4.id not in ids_2hop, "Descendant in r4 is still 3 hops away"
    print(f"  hop_range=2 from r1: {[c.name for c in results_2hop]}")

    # Search near r2 with hop_range=2 (reaches r1, r2, r3, r4)
    results_from_r2 = ledger.get_nemesis_descendants_in_region(
        [cmd.id], "r2", world, hop_range=2)
    ids_from_r2 = {c.id for c in results_from_r2}
    assert desc_r4.id in ids_from_r2, "Descendant in r4 reachable from r2 in 2 hops"
    print(f"  hop_range=2 from r2: {[c.name for c in results_from_r2]}")
    print("  PASSED")


def test_dead_nemesis_living_descendants():
    """Nemesis is dead but their descendants are alive — should still find them."""
    print("\n=== Test 5: Dead nemesis, living descendants ===")
    world = make_test_world()
    ledger = make_ledger()
    rng = random.Random(5)

    cmd = ledger.create_character("player", "r1", "supreme_commander", 0, rng)
    nemesis = ledger.create_character("enemy", "r2", "regional_commander", 0, rng)
    lineage_id = ledger.create_lineage(nemesis.id)

    desc = ledger.create_character("enemy", "r2", "lineage_member", 50, rng,
                                   lineage_id=lineage_id, parent_id=nemesis.id, generation=1)

    # Tag, then kill the nemesis
    ledger.tag_rivals("r2", cmd.id, "player")
    ledger.kill_character(nemesis.id, 80)
    assert nemesis.status == "historical"

    # Descendant should still be found
    results = ledger.get_nemesis_descendants_in_region([cmd.id], "r1", world, hop_range=1)
    ids = {c.id for c in results}
    assert desc.id in ids, "Living descendant of dead nemesis should be found"
    assert nemesis.id not in ids, "Dead nemesis should not be returned"
    print(f"  Dead nemesis: {nemesis.name} (status={nemesis.status})")
    print(f"  Living descendant found: {[c.name for c in results]}")
    print("  PASSED")


def test_no_nemesis_returns_empty():
    """No rival tags exist — queries return empty lists."""
    print("\n=== Test 6: No nemesis tags → empty results ===")
    world = make_test_world()
    ledger = make_ledger()
    rng = random.Random(6)

    cmd = ledger.create_character("player", "r1", "supreme_commander", 0, rng)
    enemy = ledger.create_character("enemy", "r2", "regional_commander", 0, rng)

    # No tagging
    candidates = ledger.get_nemesis_candidates([cmd.id])
    assert len(candidates) == 0
    print(f"  No tags: candidates = {candidates}")

    descendants = ledger.get_nemesis_descendants_in_region([cmd.id], "r1", world, hop_range=2)
    assert len(descendants) == 0
    print(f"  No tags: descendants = {descendants}")
    print("  PASSED")


def test_multiple_commanders_tag_same_enemy():
    """An enemy can be rival_of multiple commanders."""
    print("\n=== Test 7: Multiple commanders tag the same enemy ===")
    world = make_test_world()
    ledger = make_ledger()
    rng = random.Random(7)

    cmd1 = ledger.create_character("player", "r1", "supreme_commander", 0, rng)
    cmd2 = ledger.create_character("player", "r1", "supreme_commander", 100, rng)
    enemy = ledger.create_character("enemy", "r2", "regional_commander", 0, rng)

    ledger.tag_rivals("r2", cmd1.id, "player")
    ledger.tag_rivals("r2", cmd2.id, "player")

    assert len(enemy.rival_of) == 2
    assert cmd1.id in enemy.rival_of
    assert cmd2.id in enemy.rival_of
    print(f"  {enemy.name} rival_of: {enemy.rival_of}")

    # Either commander finds this enemy
    for cmd_id in [cmd1.id, cmd2.id]:
        results = ledger.get_nemesis_candidates([cmd_id])
        assert enemy in results
    print(f"  Both commanders find the enemy as nemesis")
    print("  PASSED")


if __name__ == "__main__":
    test_tag_rivals()
    test_get_nemesis_candidates()
    test_get_descendants()
    test_nemesis_descendants_in_region()
    test_dead_nemesis_living_descendants()
    test_no_nemesis_returns_empty()
    test_multiple_commanders_tag_same_enemy()
    print(f"\n{'='*60}")
    print("All Phase 3A nemesis detection tests passed.")
    print(f"{'='*60}")
