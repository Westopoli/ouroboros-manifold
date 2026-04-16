"""
Checkpoint D — Save Writer
===========================
Verifies that save_writer correctly serializes all three state classes to disk.

  TEST 1  Sim state writes produce the correct file with correct schema fields
  TEST 2  Tactical state writes produce the correct file
  TEST 3  Onboarding write delegates validation (10-mark case rejected)
  TEST 4  Multiple slots coexist independently on disk
  TEST 5  File sizes and write times reported for a 10-chapter simulated slot

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


def _make_sim_state(chapter=1, year=42):
    return {
        "chapter_number": chapter,
        "year": year,
        "rng_state": "0xdeadbeef",
        "sim_state": {
            "regions": [{"id": f"r{i}", "military": 0.5, "economy": 0.6} for i in range(12)],
            "factions": [{"id": f"f{i}", "archetype": "conqueror", "tech": 25} for i in range(4)],
            "coherence_ledger": {"f0": 0.72, "f1": 0.68},
            "diplomacy": {"f0_f1": "war", "f2_f3": "peace"},
            "technology": {"f0": {"attack": 0.4, "defense": 0.2, "economy": 0.3}},
            "lifecycle": {"year": year, "chapter": chapter},
            "chronicle_entries": [{"tick": i * 100, "text": f"event_{i}"} for i in range(5)],
        },
    }


def _make_tactical_state(mission_id="m_042", tick=500):
    return {
        "mission_id": mission_id,
        "tick": tick,
        "rng_state": "0xcafebabe",
        "engine_state": {
            "units": [{"uid": i, "hp": 100, "x": float(i * 50)} for i in range(16)],
            "tick": tick,
        },
        "mission_setup": {
            "archetype": "blitz",
            "map_seed": 12345,
            "faction_a": 0,
            "faction_b": 1,
        },
    }


# ── Test 1 — sim state file ───────────────────────────────────────────────────

def test_sim_state_write():
    _banner("TEST 1  Sim state write — file exists with correct schema fields")
    results = []

    with tempfile.TemporaryDirectory() as tmp:
        sim = _make_sim_state(chapter=7, year=214)
        write_sim_state("slot_a", sim, save_root=tmp)

        path = os.path.join(tmp, "slot_a", "sim.json")
        results.append(_result("sim.json created", os.path.exists(path), path))

        with open(path) as f:
            payload = json.load(f)

        results.append(_result("schema_version=1", payload.get("schema_version") == 1))
        results.append(_result("slot_id='slot_a'", payload.get("slot_id") == "slot_a"))
        results.append(_result("chapter_number=7", payload.get("chapter_number") == 7,
                               f"got {payload.get('chapter_number')}"))
        results.append(_result("year=214", payload.get("year") == 214,
                               f"got {payload.get('year')}"))
        results.append(_result("rng_state present", bool(payload.get("rng_state"))))
        results.append(_result("last_written_at present", bool(payload.get("last_written_at"))))
        results.append(_result("sim_state.regions present",
                               isinstance(payload.get("sim_state", {}).get("regions"), list)))
        results.append(_result("sim_state.chronicle_entries present",
                               isinstance(payload.get("sim_state", {}).get("chronicle_entries"), list)))

        _info("sim.json size", f"{os.path.getsize(path)} bytes")

    return all(results)


# ── Test 2 — tactical state file ─────────────────────────────────────────────

def test_tactical_state_write():
    _banner("TEST 2  Tactical state write — file exists with correct fields")
    results = []

    with tempfile.TemporaryDirectory() as tmp:
        tac = _make_tactical_state(mission_id="m_007", tick=1847)
        write_tactical_state("slot_a", tac, save_root=tmp)

        path = os.path.join(tmp, "slot_a", "tactical.json")
        results.append(_result("tactical.json created", os.path.exists(path)))

        with open(path) as f:
            payload = json.load(f)

        results.append(_result("schema_version=1", payload.get("schema_version") == 1))
        results.append(_result("slot_id='slot_a'", payload.get("slot_id") == "slot_a"))
        results.append(_result("mission_id='m_007'", payload.get("mission_id") == "m_007",
                               f"got {payload.get('mission_id')!r}"))
        results.append(_result("tick=1847", payload.get("tick") == 1847,
                               f"got {payload.get('tick')}"))
        results.append(_result("engine_state present", "engine_state" in payload))
        results.append(_result("mission_setup present", "mission_setup" in payload))

        _info("tactical.json size", f"{os.path.getsize(path)} bytes")

    return all(results)


# ── Test 3 — onboarding delegates validation ──────────────────────────────────

def test_onboarding_write_validation():
    _banner("TEST 3  Onboarding write — valid accepted, 10-mark rejected")
    results = []

    with tempfile.TemporaryDirectory() as tmp:
        # valid write
        try:
            write_onboarding("slot_a", {
                "difficulty": "medium",
                "rare_marks": ["blitz", "siege"],
            }, save_root=tmp)
            path = os.path.join(tmp, "slot_a", "onboarding.json")
            results.append(_result("valid onboarding written", os.path.exists(path)))
        except Exception as e:
            results.append(_result("valid onboarding written", False, str(e)))

        # 10-mark rejected
        all_ten = [f"arch_{i}" for i in range(10)]
        rejected = False
        try:
            write_onboarding("slot_a", {
                "difficulty": "easy",
                "rare_marks": all_ten,
            }, save_root=tmp)
        except ValueError:
            rejected = True
        results.append(_result("10-mark payload rejected by writer", rejected))

    return all(results)


# ── Test 4 — multiple slots coexist ──────────────────────────────────────────

def test_multi_slot():
    _banner("TEST 4  Multiple slots coexist independently")
    results = []

    with tempfile.TemporaryDirectory() as tmp:
        write_sim_state("slot_a", _make_sim_state(chapter=3, year=80), save_root=tmp)
        write_sim_state("slot_b", _make_sim_state(chapter=11, year=330), save_root=tmp)

        path_a = os.path.join(tmp, "slot_a", "sim.json")
        path_b = os.path.join(tmp, "slot_b", "sim.json")
        results.append(_result("slot_a/sim.json exists", os.path.exists(path_a)))
        results.append(_result("slot_b/sim.json exists", os.path.exists(path_b)))

        with open(path_a) as f:
            a = json.load(f)
        with open(path_b) as f:
            b = json.load(f)

        results.append(_result("slot_a chapter=3", a.get("chapter_number") == 3,
                               f"got {a.get('chapter_number')}"))
        results.append(_result("slot_b chapter=11", b.get("chapter_number") == 11,
                               f"got {b.get('chapter_number')}"))

    return all(results)


# ── Test 5 — 10-chapter write times ──────────────────────────────────────────

def test_write_performance():
    _banner("TEST 5  Write performance — 10-chapter simulated slot")
    results = []

    with tempfile.TemporaryDirectory() as tmp:
        write_times = []
        for ch in range(1, 11):
            sim = _make_sim_state(chapter=ch, year=ch * 30)
            t0 = time.perf_counter()
            write_sim_state("slot_perf", sim, save_root=tmp)
            write_times.append((time.perf_counter() - t0) * 1000)

        avg_ms = sum(write_times) / len(write_times)
        max_ms = max(write_times)
        path = os.path.join(tmp, "slot_perf", "sim.json")
        file_size = os.path.getsize(path)

        _info("sim.json final size", f"{file_size} bytes")
        _info("write time avg", f"{avg_ms:.2f} ms")
        _info("write time max", f"{max_ms:.2f} ms")

        results.append(_result("10 chapters written successfully",
                               os.path.exists(path)))
        results.append(_result("write time avg < 100ms",
                               avg_ms < 100,
                               f"avg={avg_ms:.2f}ms"))

    return all(results)


# ── main ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    passed = [
        test_sim_state_write(),
        test_tactical_state_write(),
        test_onboarding_write_validation(),
        test_multi_slot(),
        test_write_performance(),
    ]

    total = len(passed)
    n_pass = sum(passed)
    print(f"\n{'═' * 62}")
    print(f"  Save Writer result: {n_pass}/{total} tests passed")
    print(f"{'═' * 62}\n")
    sys.exit(0 if n_pass == total else 1)
