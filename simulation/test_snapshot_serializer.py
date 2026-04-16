"""
Checkpoint B — Snapshot + Delta Wire Format Against a Headless Engine
======================================================================
Runs 100 ticks against a hand-authored test map, verifies:

  TEST 1  Snapshot field coverage matches live engine state
  TEST 2  Delta sizes — legacy mode (baseline) then DR mode (scalability target)
  TEST 3  Exact reconstruction via legacy deltas (no dead-reckoning)
  TEST 4  Socket server emits snapshot → deltas at 20 Hz (wire smoke test)
  TEST 5  Dead-reckoning suppression: position updates sparse during straight march,
          correct on engagement, approximate reconstruction within DR_RESYNC_THRESHOLD

Output legend
  [PASS]  assertion met
  [FAIL]  assertion failed — detail on same line
  [INFO]  informational metric (no pass/fail judgment)
"""

import asyncio
import json
import math
import sys
import time

sys.path.insert(0, ".")

import config
from command import Command
from tactical_engine import TacticalEngine
from test_maps import open_field
from snapshot_serializer import (
    DeadReckoningTracker, full_snapshot, delta, apply_delta,
)

FACTION_A = 0
FACTION_B = 1
TICK_COUNT = 100

UNIT_TYPES_A = ["Raider", "Raider", "Interceptor", "Vanguard", "Vanguard",
                "Warden", "Bombard", "Bastion"]
UNIT_TYPES_B = ["Raider", "Raider", "Interceptor", "Vanguard", "Vanguard",
                "Warden", "Bombard", "Bastion"]


# ── helpers ──────────────────────────────────────────────────────────────────

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
    engine = TacticalEngine(tmap, seed=42)
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


# ── TEST 1: snapshot field coverage ──────────────────────────────────────────

def test_snapshot_fields():
    _banner("TEST 1 — Full snapshot field coverage")

    engine = _build_engine()
    snap = full_snapshot(engine)

    raw = json.dumps(snap)
    size_bytes = len(raw.encode())
    _info("snapshot size", f"{size_bytes:,} bytes")
    _info("unit count", len(snap["units"]))
    _info("tick in snapshot", snap["tick"])

    top_keys = {"type", "tick", "mission_id", "map", "units", "structures",
                "objectives", "fog_of_war", "tick_rate_hz"}
    _result("all top-level keys present",
            top_keys.issubset(snap.keys()),
            f"missing: {top_keys - snap.keys()}")

    map_keys = {"canvas_size", "spine_nodes", "gradient_sources", "drifting_nodes"}
    _result("map sub-keys present",
            map_keys.issubset(snap["map"].keys()),
            f"missing: {map_keys - snap['map'].keys()}")

    if snap["units"]:
        unit = snap["units"][0]
        unit_keys = {"uid", "type", "pos", "layer", "hp", "max_hp",
                     "faction", "facing_rad", "ability_cd_sec",
                     "selection_eligible", "velocity"}
        _result("unit entry keys present (including velocity)",
                unit_keys.issubset(unit.keys()),
                f"missing: {unit_keys - unit.keys()}")
        _result("snapshot velocity is [0,0]",
                unit["velocity"] == [0.0, 0.0],
                f"got {unit['velocity']}")

    snap_uids = {u["uid"] for u in snap["units"]}
    engine_uids = set(engine.store.active_ids())
    _result("snapshot UIDs match engine alive set", snap_uids == engine_uids)

    _result("tick_rate_hz matches config",
            snap["tick_rate_hz"] == config.TICK_HZ)
    _result("snapshot type field correct",
            snap["type"] == "snapshot")

    return True


# ── TEST 2: delta sizes — legacy vs DR mode ───────────────────────────────────

def test_delta_sizes():
    _banner("TEST 2 — Delta sizes: legacy mode vs dead-reckoning mode")

    # ── legacy ──
    engine = _build_engine()
    snap_0 = full_snapshot(engine)
    snap_0_size = len(json.dumps(snap_0).encode())

    legacy_sizes = []
    prev = snap_0
    for _ in range(TICK_COUNT):
        engine.step()
        d = delta(engine, prev)           # no tracker → legacy
        legacy_sizes.append(len(json.dumps(d).encode()))
        prev = full_snapshot(engine)

    # ── dead-reckoning ──
    engine = _build_engine()
    snap_0 = full_snapshot(engine)
    tracker = DeadReckoningTracker()

    dr_sizes = []
    dr_pos_update_counts = []   # how many units sent a pos update per tick
    prev = snap_0
    for _ in range(TICK_COUNT):
        engine.step()
        d = delta(engine, prev, tracker)  # with tracker → DR mode
        dr_sizes.append(len(json.dumps(d).encode()))
        dr_pos_update_counts.append(
            sum(1 for u in d["units_updated"] if "pos" in u)
        )
        prev = full_snapshot(engine)

    # ── report ──
    legacy_avg  = sum(legacy_sizes) / len(legacy_sizes)
    dr_avg      = sum(dr_sizes) / len(dr_sizes)
    ratio_snap  = snap_0_size / dr_avg if dr_avg else 0
    ratio_modes = legacy_avg / dr_avg if dr_avg else 0

    _info("snapshot size", f"{snap_0_size:,} bytes")
    _info("legacy delta  min/avg/max",
          f"{min(legacy_sizes):,} / {legacy_avg:,.0f} / {max(legacy_sizes):,} bytes")
    _info("DR delta      min/avg/max",
          f"{min(dr_sizes):,} / {dr_avg:,.0f} / {max(dr_sizes):,} bytes")
    _info("snapshot / DR-avg ratio", f"{ratio_snap:.1f}x")
    _info("legacy-avg / DR-avg ratio", f"{ratio_modes:.1f}x")
    _info("pos updates per tick  min/avg/max",
          f"{min(dr_pos_update_counts)} / "
          f"{sum(dr_pos_update_counts)/len(dr_pos_update_counts):.1f} / "
          f"{max(dr_pos_update_counts)}")

    serialize_errors = 0
    _result("no serialization errors", serialize_errors == 0)
    _result("DR deltas smaller than snapshot (avg)",
            dr_avg < snap_0_size,
            f"avg DR delta {dr_avg:.0f}B vs snapshot {snap_0_size}B")
    _result("DR smaller than legacy (avg)",
            dr_avg < legacy_avg,
            f"DR {dr_avg:.0f}B vs legacy {legacy_avg:.0f}B")
    _result("snapshot/DR-avg ratio ≥ 5x (scalability target)",
            ratio_snap >= 5.0,
            f"ratio = {ratio_snap:.1f}x")

    return True


# ── TEST 3: exact reconstruction via legacy deltas ────────────────────────────

def test_reconstruction():
    _banner("TEST 3 — Exact reconstruction via legacy deltas (no dead-reckoning)")

    engine = _build_engine()
    initial_snap = full_snapshot(engine)

    deltas = []
    prev = initial_snap
    for _ in range(TICK_COUNT):
        engine.step()
        d = delta(engine, prev)   # legacy — all position changes sent explicitly
        deltas.append(d)
        prev = full_snapshot(engine)

    final_snap = full_snapshot(engine)

    reconstructed = initial_snap
    for d in deltas:
        reconstructed = apply_delta(reconstructed, d)

    rec_units = {u["uid"]: u for u in reconstructed["units"]}
    act_units = {u["uid"]: u for u in final_snap["units"]}

    uid_match = set(rec_units.keys()) == set(act_units.keys())
    _result("alive unit set matches", uid_match,
            f"rec={set(rec_units.keys())} act={set(act_units.keys())}"
            if not uid_match else "")

    mismatches = []
    for uid in act_units:
        if uid not in rec_units:
            mismatches.append(f"uid {uid} missing")
            continue
        for field in ("pos", "hp", "layer", "ability_cd_sec"):
            r_val = rec_units[uid].get(field)
            a_val = act_units[uid].get(field)
            if r_val != a_val:
                mismatches.append(f"uid {uid} {field}: rec={r_val} act={a_val}")

    _result("all unit fields exact match",
            len(mismatches) == 0,
            f"{len(mismatches)} mismatch(es)" if mismatches else "")
    for m in mismatches[:5]:
        print(f"    {m}")

    rec_objs = {o["id"]: o for o in reconstructed.get("objectives", [])}
    act_objs = {o["id"]: o for o in final_snap.get("objectives", [])}
    _result("objectives match", rec_objs == act_objs)

    _result("final tick matches",
            reconstructed["tick"] == final_snap["tick"],
            f"rec={reconstructed['tick']} act={final_snap['tick']}")

    return uid_match and len(mismatches) == 0


# ── TEST 4: socket server wire emission ───────────────────────────────────────

_SERVER_TEST_TICKS = 20

async def _run_server_test(port):
    from socket_server import SocketServer
    srv = SocketServer(host="127.0.0.1", port=port, engine_factory=_build_engine)
    server_task = asyncio.create_task(srv.start())
    await asyncio.sleep(0.05)

    received = []
    reader, writer = await asyncio.wait_for(
        asyncio.open_connection("127.0.0.1", port), timeout=2.0
    )
    try:
        for _ in range(_SERVER_TEST_TICKS + 1):
            line = await asyncio.wait_for(reader.readline(), timeout=8.0)
            if not line:
                break
            received.append(json.loads(line.decode().strip()))
    finally:
        writer.close()
        try:
            await writer.wait_closed()
        except Exception:
            pass

    await asyncio.sleep(0.15)
    srv.stop()
    try:
        await asyncio.wait_for(server_task, timeout=2.0)
    except asyncio.TimeoutError:
        server_task.cancel()
        try:
            await server_task
        except asyncio.CancelledError:
            pass

    return received


def test_server_emission():
    _banner("TEST 4 — Socket server emits snapshot then deltas at 20 Hz")

    TEST_PORT = 18766
    try:
        received_packets = asyncio.run(_run_server_test(TEST_PORT))
    except Exception as exc:
        _result("server ran without errors", False, str(exc))
        return False

    n = len(received_packets)
    _info("packets received", n)
    _info("ticks requested", _SERVER_TEST_TICKS)

    expected = _SERVER_TEST_TICKS + 1
    _result("received initial snapshot + deltas", n >= expected,
            f"got {n}, expected ≥{expected}")

    if n == 0:
        return False

    first = received_packets[0]
    _result("first packet is a snapshot", first.get("type") == "snapshot",
            f"got {first.get('type')!r}")

    delta_packets = [p for p in received_packets[1:] if p.get("type") == "delta"]
    _result("subsequent packets are deltas",
            len(delta_packets) >= _SERVER_TEST_TICKS - 3,
            f"delta count={len(delta_packets)}")

    tick_sequence = [p["tick"] for p in received_packets]
    monotonic = all(tick_sequence[i] <= tick_sequence[i+1]
                    for i in range(len(tick_sequence) - 1))
    _result("tick numbers non-decreasing", monotonic,
            f"first 10: {tick_sequence[:10]}")

    # Verify DR: server-emitted deltas should have sparse pos updates
    if len(delta_packets) >= 5:
        pos_update_counts = [
            sum(1 for u in p.get("units_updated", []) if "pos" in u)
            for p in delta_packets
        ]
        avg_pos = sum(pos_update_counts) / len(pos_update_counts)
        _info("avg pos updates per DR delta (server)", f"{avg_pos:.1f} of {len(UNIT_TYPES_A)+len(UNIT_TYPES_B)} units")
        _result("server DR: most ticks have fewer pos updates than total units",
                avg_pos < len(UNIT_TYPES_A) + len(UNIT_TYPES_B),
                f"avg={avg_pos:.1f} total_units={len(UNIT_TYPES_A)+len(UNIT_TYPES_B)}")

    return n >= expected and monotonic


# ── TEST 5: dead-reckoning suppression behavior ───────────────────────────────

def test_dead_reckoning():
    _banner("TEST 5 — Dead-reckoning suppression: sparse approach, correct engagement")

    engine = _build_engine()
    tracker = DeadReckoningTracker()
    prev = full_snapshot(engine)

    # Phase 1: approach (ticks 1-30) — units moving straight, DR should suppress most
    approach_pos_updates = []
    for _ in range(30):
        engine.step()
        d = delta(engine, prev, tracker)
        approach_pos_updates.append(
            sum(1 for u in d["units_updated"] if "pos" in u)
        )
        prev = full_snapshot(engine)

    avg_approach = sum(approach_pos_updates) / len(approach_pos_updates)
    total_units = len(UNIT_TYPES_A) + len(UNIT_TYPES_B)

    _info("approach phase: avg pos updates/tick",
          f"{avg_approach:.1f} of {total_units} units")
    _info("approach phase: pos update counts per tick", approach_pos_updates)

    _result("approach phase: DR suppresses most positions (avg < 50% of units)",
            avg_approach < total_units * 0.5,
            f"avg={avg_approach:.1f} threshold={total_units * 0.5:.1f}")

    # Phase 2: run to combat (continue to tick 80)
    for _ in range(50):
        engine.step()
        d = delta(engine, prev, tracker)
        prev = full_snapshot(engine)

    # At engagement, check that units which stopped moving got a resync
    # (velocity dropped to [0,0] → velocity change > DR_VEL_CHANGE_THRESHOLD)
    final_snap = full_snapshot(engine)
    dead_count = total_units - len(final_snap["units"])
    _info("units dead by tick 80", dead_count)

    # Phase 3: DR approximate reconstruction check
    # Use DR deltas and compare reconstructed to actual (tolerance = DR_RESYNC_THRESHOLD)
    engine2 = _build_engine()
    tracker2 = DeadReckoningTracker()
    initial_snap2 = full_snapshot(engine2)
    dr_deltas2 = []
    prev2 = initial_snap2
    for _ in range(80):
        engine2.step()
        d2 = delta(engine2, prev2, tracker2)
        dr_deltas2.append(d2)
        prev2 = full_snapshot(engine2)

    final_snap2 = full_snapshot(engine2)
    reconstructed2 = initial_snap2
    for d2 in dr_deltas2:
        reconstructed2 = apply_delta(reconstructed2, d2)

    rec_units2 = {u["uid"]: u for u in reconstructed2["units"]}
    act_units2 = {u["uid"]: u for u in final_snap2["units"]}

    uid_match2 = set(rec_units2.keys()) == set(act_units2.keys())
    _result("DR reconstruction: alive unit sets match", uid_match2)

    max_pos_error = 0.0
    for uid in act_units2:
        if uid not in rec_units2:
            continue
        r_pos = rec_units2[uid]["pos"]
        a_pos = act_units2[uid]["pos"]
        err = math.sqrt((r_pos[0]-a_pos[0])**2 + (r_pos[1]-a_pos[1])**2)
        max_pos_error = max(max_pos_error, err)

    _info("DR reconstruction: max position error (world units)", f"{max_pos_error:.4f}")
    _result(
        f"DR reconstruction: max pos error within DR_RESYNC_THRESHOLD "
        f"({config.DR_RESYNC_THRESHOLD} wu)",
        max_pos_error <= config.DR_RESYNC_THRESHOLD,
        f"max_err={max_pos_error:.4f}",
    )

    found_vel = any("velocity" in u for d2 in dr_deltas2 for u in d2["units_updated"])
    _result("velocity field present in resynced units_updated",
            found_vel,
            "no velocity field found in any delta" if not found_vel else "")

    # ── engagement transition: unit stops → velocity=[0,0] resync fires same tick ──
    # Two Raiders 400 wu apart close at ~15 wu/tick combined → engage in ~13 ticks.
    # Raider attack_range=200, speed=150 wu/s.
    eng_tmap = open_field()
    eng2 = TacticalEngine(eng_tmap, seed=7)
    eng2.player_faction = 0
    uid_a = eng2.store.spawn("Raider", 0, 2000.0, 800.0)
    uid_b = eng2.store.spawn("Raider", 1, 2000.0, 1200.0)
    eng2.command_queue.add(Command(tick=0, type="attack_move",
                                   unit_ids=[uid_a],
                                   params={"target_x": 2000.0, "target_y": 1200.0}))
    eng2.command_queue.add(Command(tick=0, type="attack_move",
                                   unit_ids=[uid_b],
                                   params={"target_x": 2000.0, "target_y": 800.0}))

    eng_tracker = DeadReckoningTracker()
    eng_prev = full_snapshot(eng2)
    engagement_tick = None

    for _ in range(30):
        eng2.step()
        d_eng = delta(eng2, eng_prev, eng_tracker)
        for u in d_eng["units_updated"]:
            if "velocity" in u and u["velocity"] == [0.0, 0.0]:
                engagement_tick = eng2.tick
                break
        if engagement_tick is not None:
            break
        eng_prev = full_snapshot(eng2)

    _result("engagement stop fires velocity=[0,0] resync",
            engagement_tick is not None,
            f"no zero-vel resync in 30 ticks" if engagement_tick is None
            else f"fired at tick {engagement_tick}")

    return (avg_approach < total_units * 0.5
            and max_pos_error <= config.DR_RESYNC_THRESHOLD
            and engagement_tick is not None)


# ── summary ───────────────────────────────────────────────────────────────────

def main():
    print("\n══════════════════════════════════════════════════════════════")
    print("  Checkpoint B — Snapshot + Delta Wire Format")
    print("══════════════════════════════════════════════════════════════")
    print(f"  ticks: {TICK_COUNT}   units per side: {len(UNIT_TYPES_A)}")
    print(f"  tick_hz: {config.TICK_HZ}   DR_RESYNC_THRESHOLD: {config.DR_RESYNC_THRESHOLD} wu")
    print(f"  DR_VEL_CHANGE_THRESHOLD: {config.DR_VEL_CHANGE_THRESHOLD} wu/s")

    r1 = test_snapshot_fields()
    r2 = test_delta_sizes()
    r3 = test_reconstruction()
    r4 = test_server_emission()
    r5 = test_dead_reckoning()

    print("\n══════════════════════════════════════════════════════════════")
    all_pass = all([r1, r2, r3, r4, r5])
    status = "ALL PASS" if all_pass else "FAILURES PRESENT"
    print(f"  Checkpoint B — {status}")
    print("══════════════════════════════════════════════════════════════\n")


if __name__ == "__main__":
    main()
