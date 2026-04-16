#!/usr/bin/env python3
"""Stage 7.5 Checkpoint A — TriggerBus tests.

Verifies: set/get/clear flags, set/get values, default-false on unknown flags,
multi-force flag visibility, serialization round-trip.
"""
import os
import sys
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from trigger_bus import TriggerBus

PASS = "✓"
FAIL = "✗ FAIL"
_failures = 0


def _check(label: str, expected, actual, width: int = 52) -> None:
    global _failures
    ok = expected == actual
    if not ok:
        _failures += 1
    status = PASS if ok else FAIL
    exp_s = str(expected)
    act_s = str(actual)
    print(f"  {label:<{width}}  expected={exp_s:<8}  got={act_s:<8}  {status}")


def _section(title: str) -> None:
    print()
    print(f"  {'─'*70}")
    print(f"  {title}")
    print(f"  {'─'*70}")


def test_flags() -> None:
    _section("FLAGS — set / get / clear")

    bus = TriggerBus()

    _check("unknown flag defaults to False",          False, bus.get_flag("alpha"))

    bus.set_flag("alpha")
    _check("set_flag('alpha') → True",                True,  bus.get_flag("alpha"))

    bus.clear_flag("alpha")
    _check("clear_flag('alpha') → False",             False, bus.get_flag("alpha"))

    bus.set_flag("force_b_broken")
    bus.set_flag("objective_reached")
    _check("force_b_broken set",                      True,  bus.get_flag("force_b_broken"))
    _check("objective_reached set",                   True,  bus.get_flag("objective_reached"))
    _check("unset flag not contaminated",             False, bus.get_flag("primary_chokepoint_contested"))

    bus.clear_flag("force_b_broken")
    _check("clear force_b_broken, other flags intact", True, bus.get_flag("objective_reached"))
    _check("force_b_broken now False",                False, bus.get_flag("force_b_broken"))


def test_values() -> None:
    _section("VALUES — set / get")

    bus = TriggerBus()

    _check("unknown value defaults to None",           None,        bus.get_value("missing"))

    bus.set_value("counterinsurgency_fragmentation", "dispersed")
    _check("string value round-trips",                "dispersed", bus.get_value("counterinsurgency_fragmentation"))

    bus.set_value("cell_power_share", 0.25)
    _check("float value round-trips",                 0.25,        bus.get_value("cell_power_share"))

    bus.set_value("cell_power_share", 0.33)
    _check("overwrite float value",                   0.33,        bus.get_value("cell_power_share"))


def test_multi_force_visibility() -> None:
    _section("MULTI-FORCE — writes on one bus visible to all readers")

    bus = TriggerBus()

    # Simulate Force A writing a flag that Force B's runner reads
    # (same bus instance passed to both runners — single-threaded, no contention)
    force_a_sees_before = bus.get_flag("force_a_broken")
    bus.set_flag("force_a_broken")    # Force A's runner sets this on retreat
    force_b_sees_after  = bus.get_flag("force_a_broken")  # Force B reads it

    _check("Force B sees False before Force A sets flag", False, force_a_sees_before)
    _check("Force B sees True after Force A sets flag",   True,  force_b_sees_after)


def test_serialization() -> None:
    _section("SERIALIZATION — to_dict / from_dict round-trip")

    bus = TriggerBus()
    bus.set_flag("force_b_broken")
    bus.set_flag("primary_chokepoint_contested")
    bus.clear_flag("primary_chokepoint_contested")   # explicitly cleared
    bus.set_value("counterinsurgency_fragmentation", "fragmented")
    bus.set_value("mission_tick", 840.0)

    snapshot = bus.to_dict()
    restored = TriggerBus.from_dict(snapshot)

    _check("flag force_b_broken survives round-trip",              True,        restored.get_flag("force_b_broken"))
    _check("cleared flag stays False after round-trip",            False,       restored.get_flag("primary_chokepoint_contested"))
    _check("string value survives round-trip",                     "fragmented",restored.get_value("counterinsurgency_fragmentation"))
    _check("float value survives round-trip",                      840.0,       restored.get_value("mission_tick"))
    _check("unknown flag on restored bus defaults to False",       False,       restored.get_flag("nonexistent"))

    # Mutating the restored bus must not affect the original
    restored.set_flag("new_flag_on_restored")
    _check("original unaffected by mutation of restored copy",     False,       bus.get_flag("new_flag_on_restored"))


if __name__ == "__main__":
    print("=" * 72)
    print("  STAGE 7.5 CHECKPOINT A — TriggerBus")
    print("=" * 72)

    test_flags()
    test_values()
    test_multi_force_visibility()
    test_serialization()

    print()
    print("=" * 72)
    if _failures == 0:
        print(f"  {PASS}  All trigger bus tests passed.")
    else:
        print(f"  {FAIL}  {_failures} test(s) failed.")
    print("=" * 72)
    sys.exit(0 if _failures == 0 else 1)
