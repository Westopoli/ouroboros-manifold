# Checkpoint F — Game Loop Integration Test
# ============================================
# Tests the pipe transport game loop phases:
#   1. Sim starts, enters tactical phase, detects terminal state
#   2. Sim sends debrief message with correct shape
#   3. Sim waits for continue_from_debrief, then ready_for_time_jump
#   4. Sim sends time_jump_start, keyframe/chronicle messages, time_jump_end
#   5. Sim waits for proceed_to_next_mission
#   6. Sim creates new engine, sends next_mission, waits for ready_for_tactical
#   7. New tactical phase starts with fresh snapshot
#
# Run from project root:
#   python3 simulation/test_game_loop.py

import subprocess
import sys
import os
import json
import struct
import time
import threading
import queue as _queue

SIMULATION_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SIMULATION_DIR)
TEST_SCRIPT = os.path.join(SIMULATION_DIR, "test_game_loop_harness.py")


def _banner(label):
    print(f"\n{'─' * 60}")
    print(f"  {label}")
    print("─" * 60)


def _result(label, passed, detail=""):
    tag = "[PASS]" if passed else "[FAIL]"
    suffix = f"  ← {detail}" if detail else ""
    print(f"  {tag}  {label}{suffix}")
    return passed


def _read_framed(pipe) -> dict | None:
    try:
        header = pipe.read(4)
        if len(header) < 4:
            return None
        length = struct.unpack(">I", header)[0]
        if length > 10 * 1024 * 1024:
            return None
        body = pipe.read(length)
        if len(body) < length:
            return None
        return json.loads(body.decode("utf-8"))
    except Exception:
        return None


def _send_framed(pipe, msg: dict):
    encoded = json.dumps(msg).encode("utf-8")
    pipe.write(struct.pack(">I", len(encoded)) + encoded)
    pipe.flush()


def _read_messages(proc, msg_queue, stop_event):
    while not stop_event.is_set():
        msg = _read_framed(proc.stdout)
        if msg is None:
            msg_queue.put(None)
            break
        msg_queue.put(msg)


def _collect_until(msg_queue, type_name, timeout=30.0):
    """Collect messages until we see one with the given type. Returns (all_messages, target_msg)."""
    collected = []
    deadline = time.monotonic() + timeout
    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return collected, None
        try:
            msg = msg_queue.get(timeout=min(remaining, 0.5))
            if msg is None:
                return collected, None
            collected.append(msg)
            if msg.get("type") == type_name:
                return collected, msg
        except _queue.Empty:
            continue


def _collect_n(msg_queue, n, timeout=10.0):
    """Collect exactly n messages."""
    collected = []
    deadline = time.monotonic() + timeout
    while len(collected) < n:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            break
        try:
            msg = msg_queue.get(timeout=min(remaining, 0.5))
            if msg is None:
                break
            collected.append(msg)
        except _queue.Empty:
            continue
    return collected


def main():
    print("\n══════════════════════════════════════════════════════════")
    print("  Checkpoint F — Game Loop Integration Test")
    print("══════════════════════════════════════════════════════════")

    proc = subprocess.Popen(
        [sys.executable, TEST_SCRIPT],
        stdout=subprocess.PIPE,
        stdin=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=SIMULATION_DIR,
    )

    msg_queue = _queue.Queue()
    stop = threading.Event()
    reader = threading.Thread(target=_read_messages, args=(proc, msg_queue, stop), daemon=True)
    reader.start()

    try:
        _run_tests(proc, msg_queue)
    finally:
        stop.set()
        proc.kill()
        proc.wait()
        stderr_out = proc.stderr.read().decode("utf-8", errors="replace")
        if stderr_out.strip():
            print(f"\n  [stderr tail]: {stderr_out[-500:]}")

    print("\n══════════════════════════════════════════════════════════")
    print("  Checkpoint F — Game Loop Test Complete")
    print("══════════════════════════════════════════════════════════\n")


def _run_tests(proc, msg_queue):
    # Phase 1: Wait for ready
    _banner("PHASE 1 — Startup → Ready")
    msgs, ready = _collect_until(msg_queue, "ready", timeout=20.0)
    _result("ready message received", ready is not None, f"got {len(msgs)} msgs total")

    # Phase 2: Tactical → should auto-terminate (1v1, both factions attack)
    _banner("PHASE 2 — Tactical phase → auto-terminal")
    msgs, debrief = _collect_until(msg_queue, "debrief", timeout=120.0)
    snap_count = sum(1 for m in msgs if m.get("type") in ("snapshot", "delta"))
    _result("debrief message received after tactical phase", debrief is not None, f"snapshots/deltas: {snap_count}")
    if debrief:
        _result("debrief has outcome_band", "outcome_band" in debrief, str(debrief.get("outcome_band")))
        _result("debrief has force_retention", "force_retention" in debrief)
        _result("debrief has field_deltas", "field_deltas" in debrief)
        _result("debrief has objectives", "objectives" in debrief)
        _result("debrief has impact_preview", "impact_preview" in debrief)

    # Phase 3: Send continue_from_debrief, then ready_for_time_jump
    _banner("PHASE 3 — Debrief → Time Jump")
    _send_framed(proc.stdin, {"type": "command", "cmd": "continue_from_debrief"})
    time.sleep(0.1)
    _send_framed(proc.stdin, {"type": "command", "cmd": "ready_for_time_jump"})

    msgs, tj_end = _collect_until(msg_queue, "time_jump_end", timeout=30.0)
    tj_start_msgs = [m for m in msgs if m.get("type") == "time_jump_start"]
    kf_msgs = [m for m in msgs if m.get("type") == "keyframe"]
    ce_msgs = [m for m in msgs if m.get("type") == "chronicle_entry"]

    _result("time_jump_start received", len(tj_start_msgs) == 1)
    _result("time_jump_end received", tj_end is not None)
    _result("at least 1 keyframe", len(kf_msgs) >= 1, f"got {len(kf_msgs)}")
    print(f"  chronicle entries: {len(ce_msgs)}")

    if tj_start_msgs:
        tj_start = tj_start_msgs[0]
        _result("time_jump_start has span_years", "span_years" in tj_start)
        _result("time_jump_start has total_entries", "total_entries" in tj_start)

    # Phase 4: Send proceed_to_next_mission
    _banner("PHASE 4 — Proceed → Next Mission")
    _send_framed(proc.stdin, {"type": "command", "cmd": "proceed_to_next_mission"})

    msgs, next_mission = _collect_until(msg_queue, "next_mission", timeout=10.0)
    _result("next_mission message received", next_mission is not None)
    if next_mission:
        _result("next_mission has chapter", "chapter" in next_mission, f"chapter={next_mission.get('chapter')}")

    # Phase 5: Send ready_for_tactical, expect new snapshot
    _banner("PHASE 5 — New Tactical Phase")
    _send_framed(proc.stdin, {"type": "command", "cmd": "ready_for_tactical"})

    msgs = _collect_n(msg_queue, 3, timeout=10.0)
    snap_msgs = [m for m in msgs if m.get("type") == "snapshot"]
    state_msgs = [m for m in msgs if m.get("type") == "sim_state"]
    _result("new snapshot received", len(snap_msgs) >= 1, f"got {len(snap_msgs)}")
    _result("new sim_state (briefing) received", len(state_msgs) >= 1)


if __name__ == "__main__":
    main()
