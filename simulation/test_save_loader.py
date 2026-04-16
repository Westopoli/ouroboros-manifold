"""
Checkpoint D — Save Loader
===========================
Verifies round-trip fidelity, slot enumeration, tactical state consumption,
and clean deletion.

  TEST 1  Sim state round-trip — loaded payload matches written payload (byte-identical after re-serial)
  TEST 2  list_slots enumerates slots with correct metadata
  TEST 3  Tactical state: write → load → consume → verify file deleted
  TEST 4  Onboarding round-trip across load_onboarding()
  TEST 5  Delete slot leaves no files on disk

Output legend
  [PASS]  assertion met
  [FAIL]  assertion failed — detail on same line
  [INFO]  informational metric (no pass/fail judgment)
"""

import json
import os
import sys
import tempfile
import time

sys.path.insert(0, ".")

from save_writer import write_sim_state, write_tactical_state, write_onboarding
from save_loader import (
    list_slots, load_sim_state, load_tactical_state,
    load_onboarding, consume_tactical_state, delete_slot,
)


def _banner(label):
    print(f"\n{'─' * 62}")
    print(f"  {label}")
    print('─' * 62)


def _result(label, passed, detail=""):
    tag = "[PASS]" if passed else "[FAIL]"
    suffix = f"  ← {detail}" if detail else ""
    print(f"  {tag}  {label}{suffix}")
    return passed


def _info(label, value):
    print(f"  [INFO]  {label}: {value}")


def _make_sim_state(chapter=1, year=42, n_regions=12, n_entries=5):
    return {
        "chapter_number": chapter,
        "year": year,
        "rng_state": "0xdeadbeef",
        "sim_state": {
            "regions": [{"id": f"r{i}", "military": 0.5, "economy": 0.6} for i in range(n_regions)],
            "factions": [{"id": f"f{i}", "archetype": "conqueror", "tech": 25} for i in range(4)],
            "coherence_ledger": {"f0": 0.72},
            "diplomacy": {"f0_f1": "war"},
            "technology": {"f0": {"attack": 0.4}},
            "lifecycle": {"year": year, "chapter": chapter},
            "chronicle_entries": [{"tick": i * 100, "text": f"event_{i}"} for i in range(n_entries)],
        },
    }


def _make_tactical_state(mission_id="m_042", tick=500):
    return {
        "mission_id": mission_id,
        "tick": tick,
        "rng_state": "0xcafebabe",
        "engine_state": {"units": [{"uid": i, "hp": 100} for i in range(8)], "tick": tick},
        "mission_setup": {"archetype": "blitz", "map_seed": 99},
    }


# ── Test 1 — sim state round-trip ────────────────────────────────────────────

def test_sim_round_trip():
    _banner("TEST 1  Sim state round-trip — byte-identical after re-serialization")
    results = []

    with tempfile.TemporaryDirectory() as tmp:
        t0 = time.perf_counter()

        # Write 10 chapters (each overwriting the last)
        for ch in range(1, 11):
            sim = _make_sim_state(chapter=ch, year=ch * 30, n_regions=12, n_entries=ch * 2)
            write_sim_state("slot_a", sim, save_root=tmp)

        write_ms = (time.perf_counter() - t0) * 1000

        # Load the final state
        t1 = time.perf_counter()
        loaded = load_sim_state("slot_a", save_root=tmp)
        load_ms = (time.perf_counter() - t1) * 1000

        results.append(_result("load_sim_state returns dict", isinstance(loaded, dict)))
        results.append(_result("chapter_number=10", loaded.get("chapter_number") == 10,
                               f"got {loaded.get('chapter_number')}"))
        results.append(_result("year=300", loaded.get("year") == 300,
                               f"got {loaded.get('year')}"))
        results.append(_result("sim_state.regions present",
                               isinstance(loaded.get("sim_state", {}).get("regions"), list)))
        results.append(_result("chronicle_entries count=20",
                               len(loaded.get("sim_state", {}).get("chronicle_entries", [])) == 20,
                               f"got {len(loaded.get('sim_state', {}).get('chronicle_entries', []))}"))

        # Byte-identical check: re-serialize loaded payload and compare to file on disk
        path = os.path.join(tmp, "slot_a", "sim.json")
        with open(path) as f:
            raw_on_disk = f.read()
        re_serialized = json.dumps(loaded, indent=2)
        identical = raw_on_disk == re_serialized
        results.append(_result("round-trip is byte-identical after re-serialization", identical,
                               f"disk_len={len(raw_on_disk)} re_serial_len={len(re_serialized)}" if not identical else ""))

        _info("10-chapter write time", f"{write_ms:.2f} ms total")
        _info("load time", f"{load_ms:.2f} ms")
        _info("file size", f"{os.path.getsize(path)} bytes")

    return all(results)


# ── Test 2 — list_slots ───────────────────────────────────────────────────────

def test_list_slots():
    _banner("TEST 2  list_slots enumerates slots with correct metadata")
    results = []

    with tempfile.TemporaryDirectory() as tmp:
        write_sim_state("slot_a", _make_sim_state(chapter=3, year=90), save_root=tmp)
        write_sim_state("slot_b", _make_sim_state(chapter=7, year=210), save_root=tmp)
        write_onboarding("slot_a", {"difficulty": "hard", "rare_marks": ["blitz", "siege"]},
                         save_root=tmp)
        write_tactical_state("slot_b", _make_tactical_state(), save_root=tmp)

        slots = list_slots(save_root=tmp)
        slot_ids = [s["slot_id"] for s in slots]

        _info("slots found", slot_ids)

        results.append(_result("list_slots finds 2 slots", len(slots) == 2,
                               f"found {len(slots)}"))
        results.append(_result("slot_a in list", "slot_a" in slot_ids))
        results.append(_result("slot_b in list", "slot_b" in slot_ids))

        slot_a = next(s for s in slots if s["slot_id"] == "slot_a")
        slot_b = next(s for s in slots if s["slot_id"] == "slot_b")

        results.append(_result("slot_a chapter=3", slot_a["chapter_number"] == 3,
                               f"got {slot_a['chapter_number']}"))
        results.append(_result("slot_b chapter=7", slot_b["chapter_number"] == 7,
                               f"got {slot_b['chapter_number']}"))
        results.append(_result("slot_a has_tactical_state=False", not slot_a["has_tactical_state"]))
        results.append(_result("slot_b has_tactical_state=True", slot_b["has_tactical_state"]))
        results.append(_result("slot_a onboarding difficulty=hard",
                               slot_a["onboarding_summary"]["difficulty"] == "hard",
                               f"got {slot_a['onboarding_summary']['difficulty']!r}"))
        results.append(_result("slot_a onboarding rare_mark_count=2",
                               slot_a["onboarding_summary"]["rare_mark_count"] == 2,
                               f"got {slot_a['onboarding_summary']['rare_mark_count']}"))

    return all(results)


# ── Test 3 — tactical state consume ──────────────────────────────────────────

def test_tactical_consume():
    _banner("TEST 3  Tactical state: write → load → consume → file deleted")
    results = []

    with tempfile.TemporaryDirectory() as tmp:
        tac = _make_tactical_state(mission_id="m_99", tick=1847)
        write_tactical_state("slot_a", tac, save_root=tmp)

        loaded = load_tactical_state("slot_a", save_root=tmp)
        results.append(_result("load_tactical_state returns dict", isinstance(loaded, dict)))
        results.append(_result("mission_id='m_99'", loaded.get("mission_id") == "m_99",
                               f"got {loaded.get('mission_id')!r}"))
        results.append(_result("tick=1847", loaded.get("tick") == 1847,
                               f"got {loaded.get('tick')}"))

        path = os.path.join(tmp, "slot_a", "tactical.json")
        results.append(_result("tactical.json exists before consume", os.path.exists(path)))

        consume_tactical_state("slot_a", save_root=tmp)
        results.append(_result("tactical.json deleted after consume", not os.path.exists(path)))

        reloaded = load_tactical_state("slot_a", save_root=tmp)
        results.append(_result("load_tactical_state returns None after consume", reloaded is None))

    return all(results)


# ── Test 4 — onboarding round-trip ───────────────────────────────────────────

def test_onboarding_round_trip():
    _banner("TEST 4  Onboarding round-trip via load_onboarding()")
    results = []

    with tempfile.TemporaryDirectory() as tmp:
        prefs = {
            "difficulty": "easy",
            "rare_marks": ["evacuation", "sabotage", "escort"],
            "generational_cycle_id": 3,
        }
        write_onboarding("slot_a", prefs, save_root=tmp)
        loaded = load_onboarding("slot_a", save_root=tmp)

        results.append(_result("load_onboarding returns dict", isinstance(loaded, dict)))
        results.append(_result("difficulty='easy'",
                               loaded.get("difficulty") == "easy"))
        results.append(_result("rare_marks count=3",
                               len(loaded.get("rare_marks", [])) == 3,
                               f"got {loaded.get('rare_marks')}"))
        results.append(_result("generational_cycle_id=3",
                               loaded.get("generational_cycle_id") == 3,
                               f"got {loaded.get('generational_cycle_id')}"))

        # missing slot returns None
        result = load_onboarding("no_such_slot", save_root=tmp)
        results.append(_result("missing slot returns None", result is None))

    return all(results)


# ── Test 5 — delete slot cleans disk ─────────────────────────────────────────

def test_delete_slot():
    _banner("TEST 5  Delete slot leaves no files on disk")
    results = []

    with tempfile.TemporaryDirectory() as tmp:
        # Write all three file types for slot_a
        write_sim_state("slot_a", _make_sim_state(), save_root=tmp)
        write_tactical_state("slot_a", _make_tactical_state(), save_root=tmp)
        write_onboarding("slot_a", {"difficulty": "medium", "rare_marks": []}, save_root=tmp)

        # Write slot_b so we can verify it's untouched
        write_sim_state("slot_b", _make_sim_state(chapter=5), save_root=tmp)

        slot_dir = os.path.join(tmp, "slot_a")
        results.append(_result("slot_a dir exists before delete", os.path.isdir(slot_dir)))

        delete_slot("slot_a", save_root=tmp)

        results.append(_result("slot_a dir removed", not os.path.isdir(slot_dir)))

        # Verify no leftover files in the save root with slot_a name
        leftover = [f for f in os.listdir(tmp) if "slot_a" in f]
        results.append(_result("no slot_a leftovers in save root", len(leftover) == 0,
                               f"found: {leftover}"))

        # slot_b untouched
        slot_b_path = os.path.join(tmp, "slot_b", "sim.json")
        results.append(_result("slot_b untouched", os.path.exists(slot_b_path)))

        # list_slots after delete shows only slot_b
        slots = list_slots(save_root=tmp)
        results.append(_result("list_slots returns 1 slot after delete", len(slots) == 1,
                               f"found {len(slots)}: {[s['slot_id'] for s in slots]}"))

    return all(results)


# ── main ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    passed = [
        test_sim_round_trip(),
        test_list_slots(),
        test_tactical_consume(),
        test_onboarding_round_trip(),
        test_delete_slot(),
    ]

    total = len(passed)
    n_pass = sum(passed)
    print(f"\n{'═' * 62}")
    print(f"  Save Loader result: {n_pass}/{total} tests passed")
    print(f"{'═' * 62}\n")
    sys.exit(0 if n_pass == total else 1)
