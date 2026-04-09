#!/usr/bin/env python3
"""Phase 5A — Commander death lineage decision tests."""
import os, sys, random, math
os.chdir(os.path.dirname(os.path.abspath(__file__)))

import config
import world as world_mod
from region import Region
from coherence_ledger import CoherenceLedger
from naming_system import NamingSystem
from generational import GenerationalState, handle_commander_death


def make_test_world():
    """5 regions in a cross: r_center connected to r_north, r_south, r_east, r_west."""
    rng = random.Random(42)
    def make(rid, fid):
        fields = {"military": 50.0, "economy": 50.0, "tension": 30.0, "population": 50.0}
        r = Region(rid, rid, "frontier", fields, faction_id=fid)
        r.econ_phase_offset = rng.uniform(0, 2 * math.pi)
        r.tension_phase_offset = rng.uniform(0, 2 * math.pi)
        return r

    regions = {
        "r_center": make("r_center", "faction_a"),
        "r_north":  make("r_north",  "faction_a"),
        "r_south":  make("r_south",  "faction_b"),
        "r_east":   make("r_east",   "faction_b"),
        "r_west":   make("r_west",   "faction_c"),
    }
    adjacency = {
        "r_center": ["r_north", "r_south", "r_east", "r_west"],
        "r_north":  ["r_center"],
        "r_south":  ["r_center"],
        "r_east":   ["r_center"],
        "r_west":   ["r_center"],
    }
    edge_types = {}
    for a, neighbors in adjacency.items():
        for b in neighbors:
            edge_types[(a, b)] = "both"
    return world_mod.World(regions, adjacency, edge_types, seed=42)


def make_ledger():
    ns = NamingSystem()
    for fid in ("faction_a", "faction_b", "faction_c"):
        ns.load_pool(fid, "people", [f"{fid}_person_{i}" for i in range(500)])
    return CoherenceLedger(ns)


def test_death_below_min_distant_heir():
    """Scenario 1: Commander dies on chapter 1. Living descendant in distant region.
    Below minimum → global search finds them. Lineage continues."""
    print("\n=== Test 1: Death below min, distant heir promoted (global search) ===")
    world = make_test_world()
    ledger = make_ledger()
    rng = random.Random(10)

    gen = GenerationalState("faction_a", start_tick=0)
    cmd = ledger.create_character("faction_a", "r_center", "supreme_commander", 0, rng)
    lin = ledger.create_lineage(cmd.id)
    gen.chapters[0]["character_id"] = cmd.id

    # Descendant in r_west — not adjacent to r_center's neighbors in test topology
    # Actually r_west IS adjacent to r_center in our cross. Use a 2-hop-away trick:
    # put the heir in r_south (adjacent) but test with region_id=r_north
    # so r_south is 2 hops from r_north (r_north→r_center→r_south).
    # For a true distant test, the mission region is r_north, heir is in r_south.
    heir = ledger.create_character("faction_a", "r_south", "lineage_member", 50, rng,
                                   lineage_id=lin, parent_id=cmd.id, generation=1)

    # Kill commander
    ledger.kill_character(cmd.id, 80)
    assert cmd.status == "historical"

    # Chapter 1, below LINEAGE_MIN_CHAPTERS (3). Mission region = r_north.
    # r_north neighbors = [r_center]. Heir in r_south is NOT adjacent to r_north.
    # Below minimum → global search should find them.
    result = handle_commander_death(gen, ledger, world, "r_north", rng, tick=80)

    assert result["type"] == "succession", f"Expected succession, got {result}"
    assert result["successor_id"] == heir.id
    assert result["search_scope"] == "global"
    assert heir.rank == "supreme_commander"
    print(f"  Commander died: {cmd.name}")
    print(f"  Heir promoted: {heir.name} (was in r_south, mission in r_north)")
    print(f"  Search scope: {result['search_scope']}")
    print("  PASSED")


def test_death_below_min_bloodline_extinct():
    """Scenario 2: Commander dies on chapter 1. Zero living lineage members.
    Forced rotation via Phase 4 selector."""
    print("\n=== Test 2: Death below min, bloodline extinct → forced rotation ===")
    world = make_test_world()
    ledger = make_ledger()
    rng = random.Random(20)

    gen = GenerationalState("faction_a", start_tick=0)
    cmd = ledger.create_character("faction_a", "r_center", "supreme_commander", 0, rng)
    lin = ledger.create_lineage(cmd.id)
    gen.chapters[0]["character_id"] = cmd.id
    # No descendants created — bloodline is just the commander

    ledger.kill_character(cmd.id, 80)

    result = handle_commander_death(gen, ledger, world, "r_center", rng, tick=80)

    assert result["type"] == "rotation", f"Expected rotation, got {result}"
    assert result["death_reason"] == "bloodline_extinct"
    assert result["new_character_id"] is not None
    assert result["pool_used"] == "unrelated"  # no previous lineages with descendants
    print(f"  Commander died: {cmd.name}, no living descendants")
    print(f"  Rotation fired: pool={result['pool_used']}, new char={result['new_character_id']}")
    print("  PASSED")


def test_death_above_min_no_nearby_heir():
    """Scenario 3: Commander dies on chapter 4 (above min). Heir exists far away.
    Above minimum → only nearby search → no heir found → rotation."""
    print("\n=== Test 3: Death above min, no nearby heir → rotation ===")
    world = make_test_world()
    ledger = make_ledger()
    rng = random.Random(30)

    gen = GenerationalState("faction_a", start_tick=0)

    # Build up 4 chapters so we're above LINEAGE_MIN_CHAPTERS (3)
    cmd1 = ledger.create_character("faction_a", "r_center", "supreme_commander", 0, rng)
    lin1 = ledger.create_lineage(cmd1.id)
    gen.chapters[0]["character_id"] = cmd1.id

    # Chapter 2
    gen.current_chapter["end_tick"] = 100
    gen.current_chapter["end_reason"] = "rotation"
    gen._start_chapter("faction_a", 100)
    cmd2 = ledger.create_character("faction_a", "r_center", "supreme_commander", 100, rng)
    lin2 = ledger.create_lineage(cmd2.id)
    gen.chapters[1]["character_id"] = cmd2.id

    # Chapter 3
    gen.current_chapter["end_tick"] = 200
    gen.current_chapter["end_reason"] = "rotation"
    gen._start_chapter("faction_a", 200)
    cmd3 = ledger.create_character("faction_a", "r_center", "supreme_commander", 200, rng)
    lin3 = ledger.create_lineage(cmd3.id)
    gen.chapters[2]["character_id"] = cmd3.id

    # Chapter 4 — current, same lineage as chapter 3
    gen.current_chapter["end_tick"] = 300
    gen.current_chapter["end_reason"] = "rotation"
    gen._start_chapter("faction_a", 300)
    cmd4 = ledger.create_character("faction_a", "r_north", "supreme_commander", 300, rng,
                                   lineage_id=lin3, parent_id=cmd3.id, generation=1)
    gen.chapters[3]["character_id"] = cmd4.id

    # Distant heir — in r_south, 2 hops from r_north (mission region)
    heir = ledger.create_character("faction_a", "r_south", "lineage_member", 310, rng,
                                   lineage_id=lin3, parent_id=cmd3.id, generation=1)

    ledger.kill_character(cmd4.id, 350)

    # lineage_3 has 2 chapters (ch3 + ch4), above min=3? No — _count_lineage_chapters
    # counts chapters where the character's lineage_id matches. cmd3 has lin3, cmd4 has lin3.
    # So chapters_in_lineage = 2. That's below min (3). Global search would fire.
    # We need 3+ chapters with the same lineage to test the above-min path.
    # Let's also assign lin3 to chapter 2's commander.
    cmd2.lineage_id = lin3  # Pretend ch2 was also lin3

    # Now lineage_3 has 3 chapters (ch2, ch3, ch4) — at minimum, not below.
    # _count_lineage_chapters should return 3, and 3 < 3 is False → above/at minimum.
    result = handle_commander_death(gen, ledger, world, "r_north", rng, tick=350)

    assert result["type"] == "rotation", f"Expected rotation, got {result}"
    assert result["death_reason"] == "no_nearby_heir"
    print(f"  Commander died: {cmd4.name} (chapter 4, lineage has 3 chapters)")
    print(f"  Distant heir exists in r_south but NOT promoted (above min, nearby-only search)")
    print(f"  Rotation fired: pool={result['pool_used']}")
    print("  PASSED")


def test_death_above_min_adjacent_heir():
    """Scenario 4: Commander dies on chapter 4. Lineage member in adjacent region.
    Above minimum, but nearby heir → succession continues."""
    print("\n=== Test 4: Death above min, adjacent heir → succession ===")
    world = make_test_world()
    ledger = make_ledger()
    rng = random.Random(40)

    gen = GenerationalState("faction_a", start_tick=0)

    cmd1 = ledger.create_character("faction_a", "r_center", "supreme_commander", 0, rng)
    lin = ledger.create_lineage(cmd1.id)
    gen.chapters[0]["character_id"] = cmd1.id

    # Chapters 2 and 3 — same lineage
    gen.current_chapter["end_tick"] = 100
    gen.current_chapter["end_reason"] = "rotation"
    gen._start_chapter("faction_a", 100)
    cmd2 = ledger.create_character("faction_a", "r_center", "supreme_commander", 100, rng,
                                   lineage_id=lin, parent_id=cmd1.id, generation=1)
    gen.chapters[1]["character_id"] = cmd2.id

    gen.current_chapter["end_tick"] = 200
    gen.current_chapter["end_reason"] = "rotation"
    gen._start_chapter("faction_a", 200)
    cmd3 = ledger.create_character("faction_a", "r_center", "supreme_commander", 200, rng,
                                   lineage_id=lin, parent_id=cmd2.id, generation=2)
    gen.chapters[2]["character_id"] = cmd3.id

    # Chapter 4 — commander in r_north
    gen.current_chapter["end_tick"] = 300
    gen.current_chapter["end_reason"] = "rotation"
    gen._start_chapter("faction_a", 300)
    cmd4 = ledger.create_character("faction_a", "r_north", "supreme_commander", 300, rng,
                                   lineage_id=lin, parent_id=cmd3.id, generation=3)
    gen.chapters[3]["character_id"] = cmd4.id

    # Heir in r_center — adjacent to r_north
    heir = ledger.create_character("faction_a", "r_center", "lineage_member", 310, rng,
                                   lineage_id=lin, parent_id=cmd3.id, generation=3)

    ledger.kill_character(cmd4.id, 350)

    # Lineage has 4 chapters (all same lineage) — above min (3).
    # Heir in r_center is adjacent to r_north → nearby search finds them.
    result = handle_commander_death(gen, ledger, world, "r_north", rng, tick=350)

    assert result["type"] == "succession", f"Expected succession, got {result}"
    assert result["successor_id"] == heir.id
    assert result["search_scope"] == "nearby"
    assert heir.rank == "supreme_commander"
    print(f"  Commander died: {cmd4.name} (chapter 4, lineage has 4 chapters)")
    print(f"  Adjacent heir promoted: {heir.name} (in r_center, adjacent to r_north)")
    print(f"  Search scope: {result['search_scope']}")
    print("  PASSED")


def test_commander_survives():
    """Scenario 5: Commander survives. No change to behavior."""
    print("\n=== Test 5: Commander survives → no-op ===")
    world = make_test_world()
    ledger = make_ledger()
    rng = random.Random(50)

    gen = GenerationalState("faction_a", start_tick=0)
    cmd = ledger.create_character("faction_a", "r_center", "supreme_commander", 0, rng)
    gen.chapters[0]["character_id"] = cmd.id

    assert cmd.status == "active"

    result = handle_commander_death(gen, ledger, world, "r_center", rng, tick=100)

    assert result["type"] == "no_op"
    assert result["reason"] == "commander_alive"
    assert cmd.rank == "supreme_commander"
    print(f"  Commander alive: {cmd.name} (status={cmd.status})")
    print(f"  Result: {result}")
    print("  PASSED")


if __name__ == "__main__":
    test_death_below_min_distant_heir()
    test_death_below_min_bloodline_extinct()
    test_death_above_min_no_nearby_heir()
    test_death_above_min_adjacent_heir()
    test_commander_survives()
    print(f"\n{'='*60}")
    print("All Phase 5A commander death tests passed.")
    print(f"{'='*60}")
