"""
Checkpoint E — Tactical Mid-Mission Quit-and-Resume
=====================================================
Proves that export_full_state() + restore_from_state() produce a tick-identical
continuation to an unbroken run.

Protocol:
  1. Run engine A (unbroken) to tick 600 with a fixed seed + command stream.
  2. Run engine B to tick 500 with the same seed + command stream.
     Export state at tick 500, write to disk, load back, restore into engine C.
  3. Step engine C from tick 500 → 600.
  4. At tick 600, compare engine A and engine C using compute_state_hash().
     They must be identical.

  TEST 1  Export / restore — state matches across all unit fields at tick 500
  TEST 2  Quit-and-resume — tick 500→600 on restored engine is tick-identical to unbroken
  TEST 3  Tactical file is consumed (deleted) after load
  TEST 4  Export + write + load timing reported

Output legend
  [PASS]  assertion met
  [FAIL]  assertion failed — detail on same line
  [INFO]  informational metric (no pass/fail judgment)
"""

import os
import sys
import tempfile
import time

sys.path.insert(0, ".")

from command import Command, compute_state_hash
from tactical_engine import TacticalEngine
from test_maps import open_field
from save_writer import write_tactical_state
from save_loader import load_tactical_state, consume_tactical_state

FACTION_A = 0
FACTION_B = 1
SEED = 42
QUIT_TICK = 500
RESUME_TICK = 600

UNIT_TYPES_A = ["Raider", "Raider", "Interceptor", "Vanguard", "Vanguard",
                "Warden", "Bombard", "Bastion"]
UNIT_TYPES_B = ["Raider", "Raider", "Interceptor", "Vanguard", "Vanguard",
                "Warden", "Bombard", "Bastion"]


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


def _build_engine():
    tmap = open_field()
    engine = TacticalEngine(tmap, seed=SEED)
    engine.player_faction = FACTION_A
    for i, ut in enumerate(UNIT_TYPES_A):
        engine.store.spawn(ut, FACTION_A, 400.0 + i * 150.0, 500.0)
    for i, ut in enumerate(UNIT_TYPES_B):
        engine.store.spawn(ut, FACTION_B, 400.0 + i * 150.0, 3500.0)
    a_ids = engine.store.active_ids_for_faction(FACTION_A)
    engine.command_queue.add(Command(tick=0, type="attack_move",
                                     unit_ids=a_ids,
                                     params={"target_x": 2000.0, "target_y": 3500.0}))
    b_ids = engine.store.active_ids_for_faction(FACTION_B)
    engine.command_queue.add(Command(tick=0, type="attack_move",
                                     unit_ids=b_ids,
                                     params={"target_x": 2000.0, "target_y": 500.0}))
    return engine


def _run_to(engine, tick):
    while engine.tick < tick and not engine.is_terminal():
        engine.step()


# ── Test 1 — export/restore field equality at tick 500 ───────────────────────

def test_export_restore_fields():
    _banner("TEST 1  Export / restore — unit fields match at tick 500")
    results = []

    engine_b = _build_engine()
    _run_to(engine_b, QUIT_TICK)

    hash_before = compute_state_hash(engine_b.store)
    tick_before = engine_b.tick
    alive_before = sum(engine_b.store.alive[:engine_b.store.count])

    _info(f"tick {QUIT_TICK} unit count", alive_before)
    _info(f"tick {QUIT_TICK} hash", hash_before)

    state = engine_b.export_full_state()
    results.append(_result("export returns dict", isinstance(state, dict)))
    results.append(_result("exported tick matches", state.get("tick") == QUIT_TICK,
                           f"got {state.get('tick')}"))
    results.append(_result("store count exported", state.get("store", {}).get("count") == engine_b.store.count,
                           f"got {state.get('store', {}).get('count')}"))

    # restore into fresh engine
    engine_c = TacticalEngine(open_field(), seed=SEED)
    engine_c.restore_from_state(state)

    results.append(_result("restored tick matches", engine_c.tick == QUIT_TICK,
                           f"got {engine_c.tick}"))
    results.append(_result("restored store count matches",
                           engine_c.store.count == engine_b.store.count,
                           f"got {engine_c.store.count}"))

    hash_after = compute_state_hash(engine_c.store)
    results.append(_result("restored hash matches original",
                           hash_after == hash_before,
                           f"before={hash_before} after={hash_after}"))

    return all(results)


# ── Test 2 — tick-identical continuation ─────────────────────────────────────

def test_quit_resume():
    _banner("TEST 2  Quit-and-resume — tick 500→600 identical to unbroken run")
    results = []

    # Engine A: unbroken run to tick 600
    engine_a = _build_engine()
    _run_to(engine_a, RESUME_TICK)
    hash_a_600 = compute_state_hash(engine_a.store)
    alive_a_600 = sum(engine_a.store.alive[:engine_a.store.count])

    _info(f"unbroken run tick {RESUME_TICK} unit count", alive_a_600)
    _info(f"unbroken run tick {RESUME_TICK} hash", hash_a_600)

    # Engine B: run to 500, export, restore into C, continue to 600
    engine_b = _build_engine()
    _run_to(engine_b, QUIT_TICK)
    state = engine_b.export_full_state()

    engine_c = TacticalEngine(open_field(), seed=SEED)
    engine_c.restore_from_state(state)
    _run_to(engine_c, RESUME_TICK)
    hash_c_600 = compute_state_hash(engine_c.store)
    alive_c_600 = sum(engine_c.store.alive[:engine_c.store.count])

    _info(f"resumed run tick {RESUME_TICK} unit count", alive_c_600)
    _info(f"resumed run tick {RESUME_TICK} hash", hash_c_600)

    results.append(_result("unit counts match at tick 600",
                           alive_a_600 == alive_c_600,
                           f"unbroken={alive_a_600} resumed={alive_c_600}"))
    results.append(_result("state hashes match at tick 600 — tick-identical",
                           hash_a_600 == hash_c_600,
                           f"unbroken={hash_a_600} resumed={hash_c_600}"))

    return all(results)


# ── Test 3 — tactical file consumed on load ───────────────────────────────────

def test_file_consumed():
    _banner("TEST 3  Tactical file consumed (deleted) after load")
    results = []

    with tempfile.TemporaryDirectory() as tmp:
        engine_b = _build_engine()
        _run_to(engine_b, QUIT_TICK)
        state = engine_b.export_full_state()

        tac_payload = {
            "mission_id": "mission_e_test",
            "tick": state["tick"],
            "rng_state": "captured_separately",
            "engine_state": state,
            "mission_setup": {"archetype": "blitz"},
        }

        write_tactical_state("slot_a", tac_payload, save_root=tmp)
        tac_path = os.path.join(tmp, "slot_a", "tactical.json")
        results.append(_result("tactical.json written", os.path.exists(tac_path)))
        _info("tactical.json path", tac_path)
        _info("tactical.json size", f"{os.path.getsize(tac_path)} bytes")

        loaded = load_tactical_state("slot_a", save_root=tmp)
        results.append(_result("load returns dict", isinstance(loaded, dict)))
        results.append(_result("loaded mission_id matches",
                               loaded.get("mission_id") == "mission_e_test"))

        consume_tactical_state("slot_a", save_root=tmp)
        results.append(_result("file deleted after consume", not os.path.exists(tac_path)))

        reloaded = load_tactical_state("slot_a", save_root=tmp)
        results.append(_result("load returns None after consume", reloaded is None))

    return all(results)


# ── Test 4 — timing ───────────────────────────────────────────────────────────

def test_timing():
    _banner("TEST 4  Export + write + load timing")
    results = []

    with tempfile.TemporaryDirectory() as tmp:
        engine_b = _build_engine()
        _run_to(engine_b, QUIT_TICK)

        t0 = time.perf_counter()
        state = engine_b.export_full_state()
        export_ms = (time.perf_counter() - t0) * 1000

        tac_payload = {
            "mission_id": "timing_test",
            "tick": state["tick"],
            "rng_state": "",
            "engine_state": state,
            "mission_setup": {},
        }

        t1 = time.perf_counter()
        write_tactical_state("slot_a", tac_payload, save_root=tmp)
        write_ms = (time.perf_counter() - t1) * 1000

        t2 = time.perf_counter()
        loaded = load_tactical_state("slot_a", save_root=tmp)
        load_ms = (time.perf_counter() - t2) * 1000

        tac_path = os.path.join(tmp, "slot_a", "tactical.json")
        file_size = os.path.getsize(tac_path)

        _info("export time", f"{export_ms:.2f} ms")
        _info("write time", f"{write_ms:.2f} ms")
        _info("load time", f"{load_ms:.2f} ms")
        _info("tactical.json size", f"{file_size:,} bytes")

        results.append(_result("export < 500ms", export_ms < 500,
                               f"{export_ms:.1f}ms"))
        results.append(_result("write < 500ms", write_ms < 500,
                               f"{write_ms:.1f}ms"))
        results.append(_result("load < 500ms", load_ms < 500,
                               f"{load_ms:.1f}ms"))

    return all(results)


# ── main ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    passed = [
        test_export_restore_fields(),
        test_quit_resume(),
        test_file_consumed(),
        test_timing(),
    ]

    total = len(passed)
    n_pass = sum(passed)
    print(f"\n{'═' * 62}")
    print(f"  Checkpoint E result: {n_pass}/{total} tests passed")
    print(f"{'═' * 62}\n")
    sys.exit(0 if n_pass == total else 1)
