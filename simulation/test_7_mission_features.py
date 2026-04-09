#!/usr/bin/env python3
"""Phase 7 — Mission-adjacent feature tests.

7A: Mission refusal (outcome band, consequence deltas)
7B: Inheritance detection (lineage connection to region)
7C: Per-archetype time limits (urgency scaling)
7D/7E: Documentation only — verified by reading the files.
"""
import os, sys, random, math
os.chdir(os.path.dirname(os.path.abspath(__file__)))

import config
from region import Region
from coherence_ledger import CoherenceLedger
from naming_system import NamingSystem
from objectives import build_refusal_result, compute_refusal_deltas, compute_time_limit


def make_ledger():
    ns = NamingSystem()
    for fid in ("faction_a", "faction_b"):
        ns.load_pool(fid, "people", [f"{fid}_person_{i}" for i in range(100)])
    return CoherenceLedger(ns)


def test_refusal_result():
    """7A: build_refusal_result produces correct MissionResult."""
    print("\n=== Test 1 (7A): Refusal MissionResult ===")
    result = build_refusal_result("mission_001")

    assert result.outcome_band == "refusal"
    assert result.objective_score == 0.0
    assert result.force_retention == 1.0
    assert result.commander_survived is True
    assert result.ticks_elapsed == 0
    assert result.per_objective == []
    print(f"  outcome_band:      {result.outcome_band}")
    print(f"  objective_score:   {result.objective_score}")
    print(f"  force_retention:   {result.force_retention}")
    print(f"  commander_survived:{result.commander_survived}")
    print(f"  ticks_elapsed:     {result.ticks_elapsed}")
    print("  PASSED")


def test_refusal_deltas():
    """7A: Refusal consequences — tension increase, no military/economy change."""
    print("\n=== Test 2 (7A): Refusal consequence deltas ===")
    fields = {"military": 60.0, "economy": 45.0, "tension": 40.0, "population": 50.0}
    region = Region("r1", "r1", "frontier", fields, faction_id="faction_a")

    deltas = compute_refusal_deltas(region)

    assert deltas["military"] == 0.0, "No military change on refusal"
    assert deltas["economy"] == 0.0, "No economy change on refusal"
    assert deltas["population"] == 0.0, "No population change on refusal"

    # tension=40, deficit=60, 8% of 60 = 4.8
    expected_tension = (100.0 - 40.0) * (config.REFUSAL_TENSION_PENALTY_PCT / 100.0)
    assert abs(deltas["tension"] - expected_tension) < 0.01, \
        f"Expected tension +{expected_tension}, got {deltas['tension']}"

    print(f"  Region tension: {region.fields['tension']}")
    print(f"  Tension deficit: {100.0 - region.fields['tension']}")
    print(f"  Penalty: {config.REFUSAL_TENSION_PENALTY_PCT}% of deficit = +{expected_tension}")
    print(f"  Deltas: {deltas}")

    # Compare: partial_failure would also change military and economy
    # Refusal explicitly does NOT (no battle happened)
    print(f"  Confirms: military=0, economy=0 (no battle)")
    print("  PASSED")


def test_refusal_high_tension():
    """7A: At high tension, refusal penalty is small (small deficit)."""
    print("\n=== Test 3 (7A): Refusal at high tension ===")
    fields = {"military": 50.0, "economy": 50.0, "tension": 90.0, "population": 50.0}
    region = Region("r1", "r1", "frontier", fields, faction_id="faction_a")

    deltas = compute_refusal_deltas(region)
    expected = (100.0 - 90.0) * (config.REFUSAL_TENSION_PENALTY_PCT / 100.0)
    assert abs(deltas["tension"] - expected) < 0.01
    print(f"  Tension=90, deficit=10, penalty={expected:.2f}")
    print("  PASSED")


def test_inheritance_connection():
    """7B: Inheritance detection finds lineage commander who operated in a region."""
    print("\n=== Test 4 (7B): Inheritance connection detected ===")
    ledger = make_ledger()
    rng = random.Random(10)

    cmd = ledger.create_character("faction_a", "r_target", "supreme_commander", 0, rng)
    lin = ledger.create_lineage(cmd.id)

    # Commander operated in r_target — should be detected
    result = ledger.check_inheritance_connection([lin], "r_target")
    assert result is not None
    assert result["ancestor_id"] == cmd.id
    assert result["ancestor_name"] == cmd.name
    assert result["lineage_id"] == lin
    print(f"  Found: {result['ancestor_name']} ({result['ancestor_rank']}) in r_target")
    print("  PASSED")


def test_inheritance_no_connection():
    """7B: No inheritance if lineage never operated in the region."""
    print("\n=== Test 5 (7B): No inheritance connection ===")
    ledger = make_ledger()
    rng = random.Random(20)

    cmd = ledger.create_character("faction_a", "r_other", "supreme_commander", 0, rng)
    lin = ledger.create_lineage(cmd.id)

    # Lineage member in r_other, not r_target
    result = ledger.check_inheritance_connection([lin], "r_target")
    assert result is None
    print(f"  Commander in r_other, checking r_target: {result}")
    print("  PASSED")


def test_inheritance_lineage_member_not_commander():
    """7B: Regular lineage members don't trigger inheritance — only commanders."""
    print("\n=== Test 6 (7B): Lineage member (non-commander) doesn't trigger ===")
    ledger = make_ledger()
    rng = random.Random(30)

    cmd = ledger.create_character("faction_a", "r_other", "supreme_commander", 0, rng)
    lin = ledger.create_lineage(cmd.id)
    member = ledger.create_character("faction_a", "r_target", "lineage_member", 50, rng,
                                     lineage_id=lin, parent_id=cmd.id, generation=1)

    result = ledger.check_inheritance_connection([lin], "r_target")
    assert result is None, "Regular lineage_member should not trigger inheritance"
    print(f"  Member '{member.name}' (rank={member.rank}) in r_target: not a commander, no match")
    print("  PASSED")


def test_time_limit_scaling():
    """7C: Time limits scale with urgency, respect floor."""
    print("\n=== Test 7 (7C): Time limit urgency scaling ===")
    archetype = "defensive_stand"
    base = config.ARCHETYPE_TIME_LIMITS[archetype]

    # urgency=0 → full base time
    t0 = compute_time_limit(archetype, 0.0)
    assert t0 == base, f"urgency=0 should give base time {base}, got {t0}"

    # urgency=0.5 → reduced by 10%
    t05 = compute_time_limit(archetype, 0.5)
    expected_05 = base * (1.0 - 0.5 * config.TIME_PRESSURE_SCALING)
    assert abs(t05 - expected_05) < 0.01

    # urgency=1.0 → reduced by 20%
    t1 = compute_time_limit(archetype, 1.0)
    expected_1 = base * (1.0 - 1.0 * config.TIME_PRESSURE_SCALING)
    assert abs(t1 - expected_1) < 0.01

    # urgency very high (beyond 1.0 edge case) → clamped at floor
    t_extreme = compute_time_limit(archetype, 5.0)
    floor = base * config.TIME_LIMIT_FLOOR_PCT
    assert t_extreme == floor, f"Extreme urgency should hit floor {floor}, got {t_extreme}"

    print(f"  Archetype: {archetype} (base={base} ticks)")
    print(f"  urgency=0.0: {t0} ticks")
    print(f"  urgency=0.5: {t05} ticks ({t05/base*100:.0f}% of base)")
    print(f"  urgency=1.0: {t1} ticks ({t1/base*100:.0f}% of base)")
    print(f"  urgency=5.0: {t_extreme} ticks (floor={config.TIME_LIMIT_FLOOR_PCT*100:.0f}%)")
    print("  PASSED")


def test_time_limit_all_archetypes():
    """7C: Every archetype has a valid time limit."""
    print("\n=== Test 8 (7C): All archetypes have time limits ===")
    for archetype, base in config.ARCHETYPE_TIME_LIMITS.items():
        t = compute_time_limit(archetype, 0.5)
        assert t > 0
        assert t <= base
        print(f"  {archetype:<25} base={base:>5}  urgency=0.5 → {t:>5.0f}")
    print("  PASSED")


if __name__ == "__main__":
    test_refusal_result()
    test_refusal_deltas()
    test_refusal_high_tension()
    test_inheritance_connection()
    test_inheritance_no_connection()
    test_inheritance_lineage_member_not_commander()
    test_time_limit_scaling()
    test_time_limit_all_archetypes()
    print(f"\n{'='*60}")
    print("All Phase 7 mission-adjacent feature tests passed.")
    print(f"{'='*60}")
