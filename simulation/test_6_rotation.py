#!/usr/bin/env python3
"""Phase 6 — Cross-faction lineage rotation tests.

Tests the implementable portions of Phase 6: should_rotate reason strings,
rotate_lineage faction reassignment, and cross_faction flag.

PHASE 6A DEFERRED (Stage 5.5): The mission generator does not exist yet.
When mission_generator.py is built, add a cross_faction=True parameter to its
candidate pool builder. At hard cap, the mission generator should scan ALL
factions' regions (not just the player's). The winning region_id is then passed
to rotate_lineage(), and the cross-faction switch happens automatically.
See: docs/random/bible_spec_reconciliation_plan.md, Phase 6A (line ~303).
Full Phase 6C integration test (scoring distribution across factions) is also
deferred to Stage 5.5.
"""
import os, sys, random, math
os.chdir(os.path.dirname(os.path.abspath(__file__)))

import config
import world as world_mod
from region import Region
from coherence_ledger import CoherenceLedger
from naming_system import NamingSystem
from generational import GenerationalState, should_rotate, rotate_lineage


def make_test_world():
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


def test_should_rotate_returns_reason():
    """should_rotate returns 'hard_cap', 'normal', or False."""
    print("\n=== Test 1: should_rotate returns reason strings ===")
    world = make_test_world()
    registry = {"faction_a": None}

    # Below minimum — should return False
    gen = GenerationalState("faction_a", start_tick=0)
    result = should_rotate(gen, world, registry, tick=100)
    assert result is False, f"Below min should be False, got {result}"
    print(f"  1 chapter, tick=100: {result} (below min)")

    # At hard cap — should return "hard_cap"
    gen2 = GenerationalState("faction_a", start_tick=0)
    for i in range(config.LINEAGE_HARD_CAP - 1):
        gen2.current_chapter["end_tick"] = (i + 1) * 100
        gen2.current_chapter["end_reason"] = "rotation"
        gen2._start_chapter("faction_a", (i + 1) * 100)

    assert gen2.chapter_count >= config.LINEAGE_HARD_CAP
    result2 = should_rotate(gen2, world, registry, tick=10000)
    assert result2 == "hard_cap", f"At hard cap should be 'hard_cap', got {result2}"
    print(f"  {gen2.chapter_count} chapters (hard cap={config.LINEAGE_HARD_CAP}): {result2}")

    # Normal rotation — force conditions: above min, low delta, long chapter
    gen3 = GenerationalState("faction_a", start_tick=0)
    for i in range(config.LINEAGE_MIN_CHAPTERS - 1):
        gen3.current_chapter["end_tick"] = (i + 1) * 100
        gen3.current_chapter["end_reason"] = "rotation"
        gen3._start_chapter("faction_a", (i + 1) * 100)

    # Set fields to exactly 50 (delta=0, below LINEAGE_DELTA_LOW → always rotate)
    for r in world.regions.values():
        r.fields["economy"] = 50.0
        r.fields["military"] = 50.0
        r.fields["tension"] = 10.0

    tick = gen3.current_chapter["start_tick"] + 100
    result3 = should_rotate(gen3, world, registry, tick)
    assert result3 == "normal", f"Low delta above min should be 'normal', got {result3}"
    print(f"  {gen3.chapter_count} chapters, low delta: {result3}")

    # Callers can still use truthiness: both "hard_cap" and "normal" are truthy
    assert result2  # "hard_cap" is truthy
    assert result3  # "normal" is truthy
    assert not False  # False is falsy
    print("  Truthiness preserved: 'hard_cap' and 'normal' are truthy, False is falsy")
    print("  PASSED")


def test_rotate_lineage_same_faction():
    """rotate_lineage within the same faction — cross_faction should be False."""
    print("\n=== Test 2: rotate_lineage same faction ===")
    world = make_test_world()
    ledger = make_ledger()
    rng = random.Random(10)

    gen = GenerationalState("faction_a", start_tick=0)
    cmd = ledger.create_character("faction_a", "r_center", "supreme_commander", 0, rng)
    gen.chapters[0]["character_id"] = cmd.id

    result = rotate_lineage(gen, ledger, world, "r_center", rng, tick=100, reason="normal")

    assert result["type"] == "rotation"
    assert result["cross_faction"] is False
    assert result["new_faction"] == "faction_a"
    assert result["old_faction"] == "faction_a"
    assert gen.player_faction_id == "faction_a"
    print(f"  Rotated: {result['old_faction']} → {result['new_faction']}")
    print(f"  cross_faction: {result['cross_faction']}")
    print("  PASSED")


def test_rotate_lineage_cross_faction():
    """rotate_lineage into a different faction's region — cross_faction should be True."""
    print("\n=== Test 3: rotate_lineage cross-faction ===")
    world = make_test_world()
    ledger = make_ledger()
    rng = random.Random(20)

    gen = GenerationalState("faction_a", start_tick=0)
    cmd = ledger.create_character("faction_a", "r_center", "supreme_commander", 0, rng)
    gen.chapters[0]["character_id"] = cmd.id

    # Rotate into faction_b's region (r_south)
    result = rotate_lineage(gen, ledger, world, "r_south", rng, tick=100, reason="hard_cap")

    assert result["type"] == "rotation"
    assert result["cross_faction"] is True
    assert result["old_faction"] == "faction_a"
    assert result["new_faction"] == "faction_b"
    assert result["reason"] == "hard_cap"
    assert gen.player_faction_id == "faction_b"
    print(f"  Rotated: {result['old_faction']} → {result['new_faction']}")
    print(f"  cross_faction: {result['cross_faction']}")
    print(f"  reason: {result['reason']}")
    print(f"  player_faction_id updated: {gen.player_faction_id}")
    print("  PASSED")


def test_rotate_lineage_chapter_tracking():
    """After rotation, new chapter is created with correct fields."""
    print("\n=== Test 4: rotate_lineage creates proper chapter ===")
    world = make_test_world()
    ledger = make_ledger()
    rng = random.Random(30)

    gen = GenerationalState("faction_a", start_tick=0)
    cmd = ledger.create_character("faction_a", "r_center", "supreme_commander", 0, rng)
    gen.chapters[0]["character_id"] = cmd.id

    assert gen.chapter_count == 1

    result = rotate_lineage(gen, ledger, world, "r_south", rng, tick=200, reason="hard_cap")

    assert gen.chapter_count == 2
    old_ch = gen.chapters[0]
    new_ch = gen.chapters[1]
    assert old_ch["end_tick"] == 200
    assert old_ch["end_reason"] == "hard_cap"
    assert new_ch["start_tick"] == 200
    assert new_ch["character_id"] == result["new_character_id"]
    assert new_ch["faction_id"] == result["new_faction"]
    assert result["chapter_number"] == 2
    print(f"  Old chapter closed: end_tick={old_ch['end_tick']}, reason={old_ch['end_reason']}")
    print(f"  New chapter opened: start_tick={new_ch['start_tick']}, faction={new_ch['faction_id']}")
    print(f"  Chapter count: {gen.chapter_count}")
    print("  PASSED")


def test_death_still_works_after_refactor():
    """handle_commander_death still works after it was rewired to use rotate_lineage."""
    print("\n=== Test 5: handle_commander_death uses rotate_lineage correctly ===")
    from generational import handle_commander_death

    world = make_test_world()
    ledger = make_ledger()
    rng = random.Random(40)

    gen = GenerationalState("faction_a", start_tick=0)
    cmd = ledger.create_character("faction_a", "r_center", "supreme_commander", 0, rng)
    lin = ledger.create_lineage(cmd.id)
    gen.chapters[0]["character_id"] = cmd.id

    # Kill with no heirs — bloodline extinct, rotation fires
    ledger.kill_character(cmd.id, 80)
    result = handle_commander_death(gen, ledger, world, "r_center", rng, tick=80)

    assert result["type"] == "rotation"
    assert result["death_reason"] == "bloodline_extinct"
    assert result.get("cross_faction") is not None  # Has the cross_faction field from rotate_lineage
    print(f"  Death rotation: reason={result['death_reason']}, cross_faction={result['cross_faction']}")
    print(f"  New faction: {result['new_faction']}")
    print("  PASSED")


if __name__ == "__main__":
    test_should_rotate_returns_reason()
    test_rotate_lineage_same_faction()
    test_rotate_lineage_cross_faction()
    test_rotate_lineage_chapter_tracking()
    test_death_still_works_after_refactor()
    print(f"\n{'='*60}")
    print("All Phase 6 cross-faction rotation tests passed.")
    print(f"{'='*60}")
