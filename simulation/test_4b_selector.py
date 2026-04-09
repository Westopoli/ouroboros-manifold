#!/usr/bin/env python3
"""Phase 4B — Character selector three-pool selection tests."""
import os, sys, random, math
os.chdir(os.path.dirname(os.path.abspath(__file__)))

import config
import world as world_mod
from region import Region
from coherence_ledger import CoherenceLedger
from naming_system import NamingSystem
from generational import GenerationalState
import character_selector


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


def setup_full_scenario():
    """
    Create a scenario with:
    - 3 previous lineages (played in chapters 1, 2, 3)
    - 1 nemesis relationship (enemy tagged as rival of chapter 2 commander)
    - Descendants spread across regions
    """
    world = make_test_world()
    ledger = make_ledger()
    rng = random.Random(100)

    # Build a GenerationalState with 3 previous chapters
    gen = GenerationalState("faction_a", start_tick=0)

    # Chapter 1: commander in r_north (faction_a), lineage_1
    cmd1 = ledger.create_character("faction_a", "r_north", "supreme_commander", 0, rng)
    lin1 = ledger.create_lineage(cmd1.id)
    gen.chapters[0]["character_id"] = cmd1.id

    # Spawn descendants of lineage_1 in r_north and r_center
    for _ in range(3):
        ledger.create_character("faction_a", "r_north", "lineage_member", 50, rng,
                                lineage_id=lin1, parent_id=cmd1.id, generation=1)
    ledger.create_character("faction_a", "r_center", "lineage_member", 50, rng,
                            lineage_id=lin1, parent_id=cmd1.id, generation=1)

    # Chapter 2: commander in r_south (faction_b), lineage_2
    gen.current_chapter["end_tick"] = 100
    gen.current_chapter["end_reason"] = "rotation"
    gen._start_chapter("faction_b", 100)
    cmd2 = ledger.create_character("faction_b", "r_south", "supreme_commander", 100, rng)
    lin2 = ledger.create_lineage(cmd2.id)
    gen.chapters[1]["character_id"] = cmd2.id

    # Spawn descendants of lineage_2 in r_south
    for _ in range(2):
        ledger.create_character("faction_b", "r_south", "lineage_member", 150, rng,
                                lineage_id=lin2, parent_id=cmd2.id, generation=1)

    # Create a nemesis: faction_a officer in r_east tagged as rival of cmd2 (faction_b)
    nemesis = ledger.create_character("faction_a", "r_east", "regional_commander", 100, rng)
    nem_lin = ledger.create_lineage(nemesis.id)
    ledger.tag_rivals("r_east", cmd2.id, "faction_b")
    # Nemesis descendants in r_east and r_center
    ledger.create_character("faction_a", "r_east", "lineage_member", 200, rng,
                            lineage_id=nem_lin, parent_id=nemesis.id, generation=1)
    ledger.create_character("faction_a", "r_center", "lineage_member", 200, rng,
                            lineage_id=nem_lin, parent_id=nemesis.id, generation=1)

    # Chapter 3 (current): commander in r_west (faction_c), lineage_3
    gen.current_chapter["end_tick"] = 200
    gen.current_chapter["end_reason"] = "rotation"
    gen._start_chapter("faction_c", 200)
    cmd3 = ledger.create_character("faction_c", "r_west", "supreme_commander", 200, rng)
    lin3 = ledger.create_lineage(cmd3.id)
    gen.chapters[2]["character_id"] = cmd3.id

    # Spawn descendants of lineage_3 in r_west
    ledger.create_character("faction_c", "r_west", "lineage_member", 250, rng,
                            lineage_id=lin3, parent_id=cmd3.id, generation=1)

    return world, ledger, gen


def test_pool_distribution():
    """Run selector 300 times, verify pool distribution approximates 70/20/10."""
    print("\n=== Test 1: Pool distribution over 300 runs ===")
    world, ledger, gen = setup_full_scenario()

    pool_counts = {"previous_descendant": 0, "nemesis_descendant": 0, "unrelated": 0}
    pool_rolled_counts = {"previous_descendant": 0, "nemesis_descendant": 0, "unrelated": 0}

    for seed in range(300):
        rng = random.Random(seed)
        result = character_selector.select_commander(gen, ledger, world, "r_center", rng)
        assert result is not None, f"Selector returned None at seed {seed}"
        pool_counts[result["pool_used"]] += 1
        pool_rolled_counts[result["pool_rolled"]] += 1

    total = sum(pool_counts.values())
    print(f"  Pool USED distribution (n={total}):")
    for pool, count in pool_counts.items():
        pct = count / total * 100
        print(f"    {pool:<25} {count:>4} ({pct:>5.1f}%)")

    print(f"\n  Pool ROLLED distribution (before fallthrough):")
    for pool, count in pool_rolled_counts.items():
        pct = count / total * 100
        print(f"    {pool:<25} {count:>4} ({pct:>5.1f}%)")

    # Verify approximate distribution — generous bounds for 300 samples
    prev_pct = pool_counts["previous_descendant"] / total
    nem_pct = pool_counts["nemesis_descendant"] / total
    unrel_pct = pool_counts["unrelated"] / total

    # Rolled distribution should be close to 70/20/10
    prev_rolled_pct = pool_rolled_counts["previous_descendant"] / total
    nem_rolled_pct = pool_rolled_counts["nemesis_descendant"] / total
    unrel_rolled_pct = pool_rolled_counts["unrelated"] / total
    assert 0.55 < prev_rolled_pct < 0.85, f"Rolled previous_descendant {prev_rolled_pct:.2f} out of range"
    assert 0.10 < nem_rolled_pct < 0.35, f"Rolled nemesis_descendant {nem_rolled_pct:.2f} out of range"
    assert 0.02 < unrel_rolled_pct < 0.22, f"Rolled unrelated {unrel_rolled_pct:.2f} out of range"

    print("  PASSED")


def test_fallthrough_no_nemesis():
    """When no nemesis exists, nemesis rolls fall through to previous_descendant."""
    print("\n=== Test 2: Nemesis pool empty → fallthrough ===")
    world = make_test_world()
    ledger = make_ledger()
    rng_setup = random.Random(50)

    gen = GenerationalState("faction_a", start_tick=0)
    cmd1 = ledger.create_character("faction_a", "r_north", "supreme_commander", 0, rng_setup)
    lin1 = ledger.create_lineage(cmd1.id)
    gen.chapters[0]["character_id"] = cmd1.id

    # Only lineage_1 descendants, no nemesis tags at all
    for _ in range(5):
        ledger.create_character("faction_a", "r_center", "lineage_member", 50, rng_setup,
                                lineage_id=lin1, parent_id=cmd1.id, generation=1)

    # Start chapter 2+ to avoid recency penalty on lineage_1
    gen.current_chapter["end_tick"] = 100
    gen.current_chapter["end_reason"] = "rotation"
    gen._start_chapter("faction_b", 100)
    cmd2 = ledger.create_character("faction_b", "r_south", "supreme_commander", 100, rng_setup)
    gen.chapters[1]["character_id"] = cmd2.id

    gen.current_chapter["end_tick"] = 200
    gen.current_chapter["end_reason"] = "rotation"
    gen._start_chapter("faction_a", 200)
    cmd3 = ledger.create_character("faction_a", "r_north", "supreme_commander", 200, rng_setup)
    gen.chapters[2]["character_id"] = cmd3.id

    pool_counts = {"previous_descendant": 0, "nemesis_descendant": 0, "unrelated": 0}
    for seed in range(100):
        rng = random.Random(seed)
        result = character_selector.select_commander(gen, ledger, world, "r_center", rng)
        assert result is not None
        pool_counts[result["pool_used"]] += 1

    total = sum(pool_counts.values())
    print(f"  Distribution (no nemesis available):")
    for pool, count in pool_counts.items():
        print(f"    {pool:<25} {count:>4} ({count/total*100:>5.1f}%)")

    # Nemesis pool should be 0 — all nemesis rolls fall through
    assert pool_counts["nemesis_descendant"] == 0, "Nemesis should be 0 with no tags"
    # previous_descendant should absorb the nemesis fallthrough (~90%)
    prev_pct = pool_counts["previous_descendant"] / total
    assert prev_pct > 0.80, f"Expected ~90% previous, got {prev_pct:.2f}"
    print("  PASSED")


def test_recency_penalty():
    """Lineages played in the last 2 chapters are skipped by previous_descendant pool."""
    print("\n=== Test 3: Recency penalty skips recently played lineages ===")
    world = make_test_world()
    ledger = make_ledger()
    rng_setup = random.Random(60)

    gen = GenerationalState("faction_a", start_tick=0)

    # Chapter 1: lineage_1 (old, should be eligible)
    cmd1 = ledger.create_character("faction_a", "r_north", "supreme_commander", 0, rng_setup)
    lin1 = ledger.create_lineage(cmd1.id)
    gen.chapters[0]["character_id"] = cmd1.id
    for _ in range(3):
        ledger.create_character("faction_a", "r_center", "lineage_member", 50, rng_setup,
                                lineage_id=lin1, parent_id=cmd1.id, generation=1)

    # Chapter 2: lineage_2 (recent, should be penalized)
    gen.current_chapter["end_tick"] = 100
    gen._start_chapter("faction_b", 100)
    cmd2 = ledger.create_character("faction_b", "r_south", "supreme_commander", 100, rng_setup)
    lin2 = ledger.create_lineage(cmd2.id)
    gen.chapters[1]["character_id"] = cmd2.id
    for _ in range(3):
        ledger.create_character("faction_b", "r_center", "lineage_member", 150, rng_setup,
                                lineage_id=lin2, parent_id=cmd2.id, generation=1)

    # Chapter 3 (current): lineage_3 (most recent, also penalized)
    gen.current_chapter["end_tick"] = 200
    gen._start_chapter("faction_c", 200)
    cmd3 = ledger.create_character("faction_c", "r_west", "supreme_commander", 200, rng_setup)
    lin3 = ledger.create_lineage(cmd3.id)
    gen.chapters[2]["character_id"] = cmd3.id
    for _ in range(3):
        ledger.create_character("faction_c", "r_center", "lineage_member", 250, rng_setup,
                                lineage_id=lin3, parent_id=cmd3.id, generation=1)

    # With recency penalty = 2, only lineage_1 (chapter 1, 2 chapters ago) should be eligible
    # lineage_2 (chapter 2, 1 chapter ago) and lineage_3 (chapter 3, current) are blocked
    lineage_selections = {lin1: 0, lin2: 0, lin3: 0}
    previous_pool_count = 0
    for seed in range(100):
        rng = random.Random(seed)
        result = character_selector.select_commander(gen, ledger, world, "r_center", rng)
        if result["pool_used"] == "previous_descendant":
            previous_pool_count += 1
            rec = ledger.get_character_by_id(result["character_id"])
            if rec and rec.lineage_id in lineage_selections:
                lineage_selections[rec.lineage_id] += 1

    print(f"  Previous descendant selections: {previous_pool_count}/100")
    print(f"  Lineage breakdown:")
    print(f"    lineage_1 (ch1, 2 ago):  {lineage_selections[lin1]}")
    print(f"    lineage_2 (ch2, 1 ago):  {lineage_selections[lin2]}")
    print(f"    lineage_3 (ch3, current): {lineage_selections[lin3]}")

    assert lineage_selections[lin2] == 0, "Recent lineage_2 should be penalized"
    assert lineage_selections[lin3] == 0, "Current lineage_3 should be penalized"
    if previous_pool_count > 0:
        assert lineage_selections[lin1] > 0, "Eligible lineage_1 should be selected"
    print("  PASSED")


def test_unrelated_creates_new():
    """When no previous or nemesis candidates exist, unrelated pool creates a new character."""
    print("\n=== Test 4: Unrelated pool creates new character + lineage ===")
    world = make_test_world()
    ledger = make_ledger()
    rng_setup = random.Random(70)

    # Only 1 chapter, no descendants anywhere, no nemesis
    gen = GenerationalState("faction_a", start_tick=0)
    cmd1 = ledger.create_character("faction_a", "r_north", "supreme_commander", 0, rng_setup)
    gen.chapters[0]["character_id"] = cmd1.id
    # No lineage created, no descendants

    unrelated_count = 0
    for seed in range(50):
        rng = random.Random(seed)
        result = character_selector.select_commander(gen, ledger, world, "r_center", rng)
        assert result is not None
        if result["pool_used"] == "unrelated":
            unrelated_count += 1
            assert result["lineage_id"] is not None, "Unrelated should create a new lineage"
            assert result["faction_id"] == "faction_a", "Should match region owner"

    print(f"  Unrelated pool used: {unrelated_count}/50")
    assert unrelated_count > 0, "With no candidates, unrelated should fire"
    print("  PASSED")


def test_selector_returns_correct_fields():
    """Verify the return dict has all expected fields."""
    print("\n=== Test 5: Return dict structure ===")
    world, ledger, gen = setup_full_scenario()
    rng = random.Random(42)

    result = character_selector.select_commander(gen, ledger, world, "r_center", rng)
    assert result is not None
    expected_keys = {"character_id", "lineage_id", "faction_id", "region_id",
                     "pool_used", "pool_rolled"}
    assert set(result.keys()) == expected_keys, f"Keys mismatch: {set(result.keys())} vs {expected_keys}"
    assert result["pool_used"] in ("previous_descendant", "nemesis_descendant", "unrelated")
    assert result["pool_rolled"] in ("previous_descendant", "nemesis_descendant", "unrelated")
    print(f"  Result: {result}")
    print("  PASSED")


if __name__ == "__main__":
    test_pool_distribution()
    test_fallthrough_no_nemesis()
    test_recency_penalty()
    test_unrelated_creates_new()
    test_selector_returns_correct_fields()
    print(f"\n{'='*60}")
    print("All Phase 4B character selector tests passed.")
    print(f"{'='*60}")
