#!/usr/bin/env python3
"""
Stage 5.5 Checkpoint G.5-Claims — per-spec-claim character selector scenarios.

Each function constructs minimal sim state, calls character_selector.run_selection()
directly, and asserts one claim. No shared generational loop; no warmup.

Claim IDs correspond to stage_5_5_spec.md line references.
"""
import os, random
os.chdir(os.path.dirname(os.path.abspath(__file__)))

import config
from region import Region
from world import World
from coherence_ledger import CoherenceLedger
from naming_system import NamingSystem
from generational import GenerationalState, reassign_player
import character_selector

# ── Shared helpers ─────────────────────────────────────────────────────────────

RESULTS = []

def _rec(name, passed, note=""):
    RESULTS.append((name, passed, note))
    print(f"  [{'PASS' if passed else 'FAIL'}] {name}" + (f"  — {note}" if note else ""))


def _make_world(player="faction_a", enemy="faction_b"):
    f = {"military": 50.0, "economy": 50.0, "tension": 30.0, "population": 50.0}
    regions = {
        "r0": Region("r0", "r0", "frontier", dict(f), faction_id=player),
        "r1": Region("r1", "r1", "frontier", dict(f), faction_id=player),
        "r2": Region("r2", "r2", "frontier", dict(f), faction_id=enemy),
    }
    adj = {"r0": ["r1", "r2"], "r1": ["r0"], "r2": ["r0"]}
    return World(regions, adj,
                 {(a, b): "both" for a, nb in adj.items() for b in nb},
                 seed=42)


def _make_ledger(*fids):
    ns = NamingSystem()
    for fid in fids:
        ns.load_pool(fid, "people", [f"{fid}_{i}" for i in range(500)])
    return CoherenceLedger(ns)


def _sel(gen, ledger, world, region="r0", rng=None, tick=0, lid=None, delta=0.0):
    return character_selector.run_selection(
        gen, ledger, world, region,
        rng or random.Random(42), tick,
        current_lineage_id=lid,
        region_field_delta=delta,
    )


def _setup_char(ledger, rng, faction="faction_a", region="r0",
                rank="supreme_commander"):
    """Create character + lineage; return (char, lineage_id)."""
    char = ledger.create_character(faction, region, rank, 0, rng)
    lid  = ledger.create_lineage(char.id)
    return char, lid


# ── Scenarios ──────────────────────────────────────────────────────────────────

def test_m17_first_mission_unrelated():
    """M17 (spec:620): no prior lineage survivors → pool draw falls to unrelated,
    new lineage created."""
    world  = _make_world()
    ledger = _make_ledger("faction_a")
    rng    = random.Random(42)
    gen    = GenerationalState("faction_a")

    # Create and immediately kill the only lineage member.
    # Previous pool finds no living members → falls through to unrelated.
    char, lid = _setup_char(ledger, rng)
    ledger.kill_character(char.id, 1)
    gen.current_chapter["character_id"] = char.id

    sel = _sel(gen, ledger, world, lid=lid)

    _rec("M17 first_mission_unrelated_pool",
         sel is not None
         and sel.pool_used == "unrelated"
         and sel.lineage_id is not None
         and sel.lineage_id != lid,
         f"pool={getattr(sel,'pool_used',None)} "
         f"new_lineage={getattr(sel,'lineage_id',None)}")


def test_m14_min_stay_blocks_rotation():
    """M14 (spec:162): chapter_counter < SELECTOR_MIN_CHAPTERS → decision=STAY."""
    world  = _make_world()
    ledger = _make_ledger("faction_a")
    rng    = random.Random(42)
    gen    = GenerationalState("faction_a")

    char, lid = _setup_char(ledger, rng)
    gen.current_chapter["character_id"] = char.id

    ledger.increment_chapter(lid)   # count=1 < SELECTOR_MIN_CHAPTERS(2)

    sel = _sel(gen, ledger, world, lid=lid, delta=0.0)

    _rec("M14 min_stay_blocks_rotation",
         sel is not None and sel.rotation_reason is None,
         f"chapter_count=1 min={config.SELECTOR_MIN_CHAPTERS} "
         f"rotation_reason={getattr(sel,'rotation_reason',None)}")


def test_m15_hard_cap_forces_rotation():
    """M15 (spec:174): chapter_counter == SELECTOR_HARD_CAP → ROTATE reason='hard_cap'."""
    world  = _make_world()
    ledger = _make_ledger("faction_a")
    gen    = GenerationalState("faction_a")

    char, lid = _setup_char(ledger, random.Random(7))
    gen.current_chapter["character_id"] = char.id

    for _ in range(config.SELECTOR_HARD_CAP):
        ledger.increment_chapter(lid)   # count == HARD_CAP

    sel = _sel(gen, ledger, world, rng=random.Random(99), lid=lid)

    _rec("M15 hard_cap_forces_rotation",
         sel is not None and sel.rotation_reason == "hard_cap",
         f"chapter_count={config.SELECTOR_HARD_CAP} "
         f"rotation_reason={getattr(sel,'rotation_reason',None)}")


def test_delta_based_rotate_high_delta():
    """delta≈0 → rotation_prob=MAX(0.8) → ROTATE reason='normal'.
    Seed 1: first rng.random() ≈ 0.13, well below 0.8.
    """
    world  = _make_world()
    ledger = _make_ledger("faction_a")
    gen    = GenerationalState("faction_a")

    char, lid = _setup_char(ledger, random.Random(7))
    gen.current_chapter["character_id"] = char.id

    for _ in range(3):              # 2 ≤ chapter_count(3) < HARD_CAP(6)
        ledger.increment_chapter(lid)

    # Fresh RNG; first call hits the step-4 rotation-prob check.
    sel = _sel(gen, ledger, world, rng=random.Random(1), lid=lid, delta=0.0)

    _rec("delta_based_rotate_high_delta",
         sel is not None and sel.rotation_reason == "normal",
         f"delta=0 rotation_prob={config.SELECTOR_MAX_ROTATION_PROB} "
         f"rotation_reason={getattr(sel,'rotation_reason',None)}")


def test_delta_based_stay_low_delta():
    """delta≥SELECTOR_DELTA_SAFE → rotation_prob=MIN(0.1) → STAY for most seeds.
    Seed 42: first rng.random() well above 0.1.
    """
    world  = _make_world()
    ledger = _make_ledger("faction_a")
    gen    = GenerationalState("faction_a")

    char, lid = _setup_char(ledger, random.Random(7))
    gen.current_chapter["character_id"] = char.id

    for _ in range(3):
        ledger.increment_chapter(lid)

    sel = _sel(gen, ledger, world, rng=random.Random(42), lid=lid,
               delta=config.SELECTOR_DELTA_SAFE)

    _rec("delta_based_stay_low_delta",
         sel is not None and sel.rotation_reason is None,
         f"delta={config.SELECTOR_DELTA_SAFE} rotation_prob={config.SELECTOR_MIN_ROTATION_PROB} "
         f"rotation_reason={getattr(sel,'rotation_reason',None)}")


def test_crisis_veto_blocks_rotation():
    """delta≈0 → would rotate, but home-region stability < SELECTOR_CRISIS_THRESHOLD → STAY.
    stability = mil*0.40 + (100-tension)*0.35 + pop*0.25, with low-mil/low-pop penalties.
    Seed 1: first rng.random() ≈ 0.13 < 0.8 → enters veto check.
    """
    crisis = {"military": 5.0, "economy": 50.0, "tension": 99.0, "population": 5.0}
    normal = {"military": 50.0, "economy": 50.0, "tension": 30.0, "population": 50.0}
    regions = {
        "r0": Region("r0", "r0", "frontier", dict(crisis), faction_id="faction_a"),
        "r1": Region("r1", "r1", "frontier", dict(crisis), faction_id="faction_a"),
        "r2": Region("r2", "r2", "frontier", dict(normal), faction_id="faction_b"),
    }
    adj   = {"r0": ["r1", "r2"], "r1": ["r0"], "r2": ["r0"]}
    world = World(regions, adj,
                  {(a, b): "both" for a, nb in adj.items() for b in nb},
                  seed=42)

    ledger = _make_ledger("faction_a")
    gen    = GenerationalState("faction_a")

    char, lid = _setup_char(ledger, random.Random(7))
    gen.current_chapter["character_id"] = char.id

    for _ in range(3):
        ledger.increment_chapter(lid)

    stab = world.regions["r0"].composites.get("stability", 0)
    sel  = _sel(gen, ledger, world, rng=random.Random(1), lid=lid, delta=0.0)

    _rec("crisis_veto_blocks_rotation",
         sel is not None
         and sel.rotation_reason is None
         and stab < config.SELECTOR_CRISIS_THRESHOLD,
         f"stability={stab:.2f} threshold={config.SELECTOR_CRISIS_THRESHOLD} "
         f"rotation_reason={getattr(sel,'rotation_reason',None)}")


def test_forced_rotation_bloodline_extinct():
    """All lineage members dead → forced_rotate=True → ROTATE reason='forced'."""
    world  = _make_world()
    ledger = _make_ledger("faction_a")
    gen    = GenerationalState("faction_a")
    rng    = random.Random(42)

    char, lid = _setup_char(ledger, rng)
    ledger.kill_character(char.id, 1)
    gen.current_chapter["character_id"] = char.id

    sel = _sel(gen, ledger, world, rng=random.Random(99), lid=lid)

    _rec("forced_rotation_bloodline_extinct",
         sel is not None and sel.rotation_reason == "forced",
         f"rotation_reason={getattr(sel,'rotation_reason',None)}")


def test_forced_rotation_kia_no_successor():
    """Commander KIA; all other living lineage members are supreme_commanders
    (rank excluded from succession) → _find_lineage_successor_near returns None
    → forced_rotate=True → ROTATE reason='forced'."""
    world  = _make_world()
    ledger = _make_ledger("faction_a")
    gen    = GenerationalState("faction_a")
    rng    = random.Random(42)

    # Living supreme_commander: keeps forced_rotate=False on the living-members check,
    # but is ineligible for succession (rank == "supreme_commander").
    living_sc, lid = _setup_char(ledger, rng, rank="supreme_commander")

    # Dead commander enrolled in the same lineage.
    dead_cmdr = ledger.create_character(
        "faction_a", "r0", "supreme_commander", 0, rng, lineage_id=lid)
    ledger.kill_character(dead_cmdr.id, 50)
    gen.current_chapter["character_id"] = dead_cmdr.id

    sel = _sel(gen, ledger, world, rng=random.Random(99), lid=lid)

    _rec("forced_rotation_kia_no_successor",
         sel is not None and sel.rotation_reason == "forced",
         f"rotation_reason={getattr(sel,'rotation_reason',None)}")


def test_m18_faction_collapse_reassignment():
    """M18: player faction has 0 regions → reassign_player picks faction with ≥1 region."""
    world = _make_world("faction_a", "faction_b")
    for r in world.regions.values():   # strip faction_a of all territory
        r.faction_id = "faction_b"

    gen      = GenerationalState("faction_a")
    registry = {"faction_a": None, "faction_b": None}

    result  = reassign_player(gen, world, registry, random.Random(42), tick=100)
    new_fid = result.get("new_faction")
    n_owned = len(world.regions_by_faction(new_fid)) if new_fid else 0

    _rec("M18 faction_collapse_reassignment",
         result.get("type") == "reassignment" and n_owned >= 1,
         f"new_faction={new_fid} regions_owned={n_owned}")


def test_pool_previous_descendant():
    """Prior lineage has living member near mission region; forced rotation;
    seed → previous_descendant pool.
    random.Random(1).random() ≈ 0.13 < SELECTOR_POOL_PREVIOUS_WEIGHT(0.70).
    chapters_ago=1 ≥ RECENCY_PENALTY_WINDOW(1) so lineage is eligible.
    """
    world  = _make_world()
    ledger = _make_ledger("faction_a")
    gen    = GenerationalState("faction_a")
    rng    = random.Random(42)

    # Chapter 1: living char_a in r0, lineage_a — will appear in previous pool.
    char_a = ledger.create_character("faction_a", "r0", "lineage_member", 0, rng)
    lid_a  = ledger.create_lineage(char_a.id)
    gen.current_chapter["character_id"] = char_a.id

    # Chapter 2 (current): dead char_b, lineage_b → forces rotation.
    # chapters_ago for lineage_a = chapter_count(2) − last_played(1) = 1 ≥ window(1).
    gen._start_chapter("faction_a", 50)
    char_b, lid_b = _setup_char(ledger, rng, rank="lineage_member")
    gen.current_chapter["character_id"] = char_b.id
    ledger.kill_character(char_b.id, 60)

    sel = _sel(gen, ledger, world, rng=random.Random(1), lid=lid_b)

    _rec("pool_previous_descendant",
         sel is not None and sel.pool_used == "previous_descendant",
         f"pool_used={getattr(sel,'pool_used',None)} "
         f"char={getattr(sel,'character_id',None)}")


def test_pool_nemesis_descendant():
    """Rival's child is in mission region with lineage_id set; previous pool empty;
    pool draw routes to nemesis_descendant (via fallthrough from previous if needed).
    """
    world  = _make_world()
    ledger = _make_ledger("faction_a", "faction_b")
    gen    = GenerationalState("faction_a")
    rng    = random.Random(42)

    # Commander (dead) — provides the commander_id used to identify nemeses.
    cmdr, lid_cmdr = _setup_char(ledger, rng, faction="faction_a")
    gen.current_chapter["character_id"] = cmdr.id
    ledger.kill_character(cmdr.id, 1)   # lineage_cmdr extinct → forced rotation

    # Rival: enemy character tagged with cmdr's id in rival_of.
    rival    = ledger.create_character("faction_b", "r2", "lineage_member", 0, rng)
    lid_rival = ledger.create_lineage(rival.id)
    rival.rival_of.append(cmdr.id)

    # Child of rival in r0 (mission region) with lineage enrolled — satisfies
    # the lineage_id is not None invariant asserted in select_commander.
    child = ledger.create_character(
        "faction_b", "r0", "lineage_member", 0, rng,
        lineage_id=lid_rival, parent_id=rival.id)

    # Seed 1: roll ≈ 0.13 → tries previous (no survivors) → falls to nemesis → child.
    sel = _sel(gen, ledger, world, rng=random.Random(1), lid=lid_cmdr)

    _rec("pool_nemesis_descendant",
         sel is not None
         and sel.pool_used == "nemesis_descendant"
         and sel.character_id == child.id,
         f"pool_used={getattr(sel,'pool_used',None)} "
         f"char={getattr(sel,'character_id',None)} expected={child.id}")


def test_pool_unrelated_fallback():
    """No previous survivors, no nemesis candidates → unrelated pool; new lineage created."""
    world  = _make_world()
    ledger = _make_ledger("faction_a")
    gen    = GenerationalState("faction_a")
    rng    = random.Random(42)

    char, lid = _setup_char(ledger, rng)
    ledger.kill_character(char.id, 1)   # all dead → forced rotation
    gen.current_chapter["character_id"] = char.id

    sel = _sel(gen, ledger, world, rng=random.Random(99), lid=lid)

    _rec("pool_unrelated_fallback",
         sel is not None
         and sel.pool_used == "unrelated"
         and sel.lineage_id is not None
         and sel.lineage_id != lid,
         f"pool_used={getattr(sel,'pool_used',None)} "
         f"new_lineage={getattr(sel,'lineage_id',None)}")


def test_m16_commander_proximity():
    """M16 (spec:668): selected commander's region is within SELECTOR_PROXIMITY_HOPS
    of the mission region. Verified for a previous-pool draw where the candidate
    lives in an adjacent region (r1, 1 hop from mission region r0).
    """
    world  = _make_world()
    ledger = _make_ledger("faction_a")
    gen    = GenerationalState("faction_a")
    rng    = random.Random(42)

    # Chapter 1: char_a in r1 (1 hop from r0), lineage_a.
    char_a = ledger.create_character("faction_a", "r1", "lineage_member", 0, rng)
    lid_a  = ledger.create_lineage(char_a.id)
    gen.current_chapter["character_id"] = char_a.id

    # Chapter 2: dead char_b → forces rotation; char_a eligible via previous pool.
    gen._start_chapter("faction_a", 50)
    char_b, lid_b = _setup_char(ledger, rng, rank="lineage_member")
    gen.current_chapter["character_id"] = char_b.id
    ledger.kill_character(char_b.id, 60)

    sel = _sel(gen, ledger, world, rng=random.Random(1), lid=lid_b)

    if sel:
        nearby   = character_selector._nearby_region_ids(
            world, "r0", config.SELECTOR_PROXIMITY_HOPS)
        in_range = sel.region_id in nearby
    else:
        in_range = False

    _rec("M16 commander_proximity",
         in_range,
         f"commander_region={getattr(sel,'region_id',None)} "
         f"within {config.SELECTOR_PROXIMITY_HOPS} hops of r0 "
         f"nearby={sorted(character_selector._nearby_region_ids(world,'r0',config.SELECTOR_PROXIMITY_HOPS)) if sel else '?'}")


def test_bloodline_succession_on_commander_death():
    """Spec: commander KIA with a living lineage member nearby → STAY (same lineage,
    new character). Step 1 dead-commander check pre-empts delta scoring even when
    chapter_counter=3 (above min_stay=2, below hard_cap=6).

    Assertions:
      decision == STAY  (rotation_reason is None)
      lineage unchanged (lineage_id == lid)
      character changed  (character_id == C2, != C1)
      rotation_mechanism is None
      pool_used is None
    """
    world  = _make_world()
    ledger = _make_ledger("faction_a")
    gen    = GenerationalState("faction_a")
    rng    = random.Random(42)

    # C1: current commander, KIA — enrolled as supreme_commander so it is NOT
    # itself eligible for succession, but its presence keeps lineage non-empty
    # until killed; after kill, C2 is the sole living member.
    char_c1, lid = _setup_char(ledger, rng, rank="supreme_commander")
    ledger.kill_character(char_c1.id, 50)
    gen.current_chapter["character_id"] = char_c1.id

    # C2: living lineage member in mission region — eligible for succession
    # (_find_lineage_successor_near excludes rank=="supreme_commander").
    char_c2 = ledger.create_character(
        "faction_a", "r0", "lineage_member", 0, rng, lineage_id=lid)

    # chapter_count=3: above min_stay(2), below hard_cap(6).
    # Proves the dead-commander path fires before step 4 (delta scoring).
    for _ in range(3):
        ledger.increment_chapter(lid)

    sel = _sel(gen, ledger, world, rng=random.Random(42), lid=lid, delta=0.0)

    ok_stay      = sel is not None and sel.rotation_reason is None
    ok_lineage   = sel is not None and sel.lineage_id == lid
    ok_is_c2     = sel is not None and sel.character_id == char_c2.id
    ok_not_c1    = sel is not None and sel.character_id != char_c1.id
    ok_mechanism = sel is not None and sel.rotation_mechanism is None
    ok_pool      = sel is not None and sel.pool_used is None

    _rec("bloodline_succession_on_commander_death",
         ok_stay and ok_lineage and ok_is_c2 and ok_not_c1 and ok_mechanism and ok_pool,
         f"rotation_reason={getattr(sel,'rotation_reason',None)} "
         f"lineage={getattr(sel,'lineage_id',None)} (want {lid}) "
         f"char={getattr(sel,'character_id',None)} (want {char_c2.id}) "
         f"mechanism={getattr(sel,'rotation_mechanism',None)} "
         f"pool={getattr(sel,'pool_used',None)}")


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    print(f"\n{'═'*60}")
    print(f"  Stage 5.5 Checkpoint G.5-Claims")
    print(f"{'═'*60}\n")

    test_m17_first_mission_unrelated()
    test_m14_min_stay_blocks_rotation()
    test_m15_hard_cap_forces_rotation()
    test_delta_based_rotate_high_delta()
    test_delta_based_stay_low_delta()
    test_crisis_veto_blocks_rotation()
    test_forced_rotation_bloodline_extinct()
    test_forced_rotation_kia_no_successor()
    test_m18_faction_collapse_reassignment()
    test_pool_previous_descendant()
    test_pool_nemesis_descendant()
    test_pool_unrelated_fallback()
    test_m16_commander_proximity()
    test_bloodline_succession_on_commander_death()

    passed = sum(1 for _, p, _ in RESULTS if p)
    total  = len(RESULTS)

    print(f"\n{'─'*60}")
    print(f"  {passed}/{total} passed")
    if passed < total:
        print(f"\n  Failed:")
        for name, p, note in RESULTS:
            if not p:
                print(f"    FAIL  {name}  — {note}")
    print(f"{'═'*60}\n")
    return passed == total


if __name__ == "__main__":
    import sys
    sys.exit(0 if main() else 1)
