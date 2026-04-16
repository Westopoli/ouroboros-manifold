# Replaces socket_server.py's TCP transport with stdio pipe I/O.
# Godot spawns this process and communicates over stdin/stdout.
# See socket_server.py — that file's TCP transport is superseded by this module.
#
# Protocol: 4-byte big-endian length header + UTF-8 JSON body, both directions.
# Stdout is owned entirely by this protocol. Stray print() calls are intercepted
# by _StdoutTrap and routed to stderr (logs/sim_stderr.log) to prevent corruption.

import sys
import os
import json
import struct
import threading
import queue
import platform
import traceback
import logging
import time

SIM_VERSION = "0.10.0"

_real_stdout_buffer = None


class _StdoutTrap:
    """Routes stray print() calls to stderr so they don't corrupt the pipe protocol."""

    def write(self, s):
        if s.strip():
            try:
                sys.stderr.write(f"[pipe:stdout-intercepted] {s}\n")
                sys.stderr.flush()
            except Exception:
                pass
        return len(s)

    def flush(self):
        pass


def _setup_io():
    global _real_stdout_buffer
    _real_stdout_buffer = sys.stdout.buffer

    import config as _cfg
    os.makedirs("logs", exist_ok=True)
    stderr_log = open(_cfg.STDERR_LOG_PATH, "w", encoding="utf-8", buffering=1)
    sys.stderr = stderr_log
    sys.stdout = _StdoutTrap()
    logging.basicConfig(stream=stderr_log, level=logging.INFO, format="%(levelname)s %(message)s")


def _install_crash_handler():
    import config as _cfg

    def _handler(exc_type, exc_val, exc_tb):
        try:
            os.makedirs("logs", exist_ok=True)
            tb_text = _strip_abs_paths(
                "".join(traceback.format_exception(exc_type, exc_val, exc_tb))
            )
            with open(_cfg.CRASH_LOG_PATH, "w", encoding="utf-8") as f:
                f.write(f"sim_version: {SIM_VERSION}\n")
                f.write(f"os: {platform.system()} {platform.release()}\n")
                f.write(f"python: {sys.version}\n")
                f.write("\n--- traceback ---\n")
                f.write(tb_text)
        except Exception:
            pass  # crash handler must never itself crash

    sys.excepthook = _handler


def _strip_abs_paths(text: str) -> str:
    """Strip cwd prefix from absolute paths in a traceback string."""
    for cwd in (os.path.realpath(os.getcwd()), os.getcwd()):
        for sep in ("/", os.sep):
            key = cwd.rstrip(sep) + sep
            if key in text:
                text = text.replace(key, "")
    return text


def _build_mission_briefing(snapshot: dict, player_faction: int) -> dict:
    player_by_type: dict = {}
    enemy_count: int = 0
    for u in snapshot.get("units", []):
        if u.get("faction") == player_faction:
            t = str(u.get("type", "unit")).lower()
            player_by_type[t] = player_by_type.get(t, 0) + 1
        else:
            enemy_count += 1
    player_units = [
        {"type_abstract": t, "type_display_name": t.capitalize(), "category": "line", "count": c}
        for t, c in player_by_type.items()
    ]
    total_player = sum(player_by_type.values())
    parity = int(100 * total_player / max(enemy_count, 1))
    return {
        "mission_id_label": "OP-%04d" % snapshot.get("tick", 0),
        "chapter": 1,
        "generation": 1,
        "era_id": "roman",
        "mission_title": "Field Engagement",
        "mission_subtitle": "Forces in contact across the operational area",
        "tick_counter": snapshot.get("tick", 0),
        "situation_text": "Forces are in contact. Engage and destroy the enemy.",
        "objective_primary": {
            "text": "Destroy the enemy force.",
            "archetype": "Assault",
            "success_spectrum_label": "TOTAL VICTORY",
        },
        "objectives_secondary": [],
        "enemy_assessment": {
            "faction_name": "Enemy Force",
            "archetype_label": "UNKNOWN",
            "military_stat": min(100, enemy_count * 10),
            "military_stat_max": 100,
            "tech_tier": 1,
            "behavior_tag": "ACTIVE",
        },
        "player_force": {
            "parity_percentage": parity,
            "units": player_units,
        },
        "region_state": {
            "name": "Operational Area",
            "tier": "Frontier",
            "economy": {"value": 50, "max": 100},
            "military": {"value": 60, "max": 100},
            "tension": {"value": 80, "max": 100},
        },
        "commander_lineage": {
            "name": "Commander",
            "generation_number": 1,
            "predecessor_name": "",
            "predecessor_status": "",
        },
        "reinforcement_note": "",
    }


def _send_message(msg: dict):
    """Write one length-prefixed JSON message to real stdout."""
    encoded = json.dumps(msg).encode("utf-8")
    _real_stdout_buffer.write(struct.pack(">I", len(encoded)) + encoded)
    _real_stdout_buffer.flush()


def _read_message(buf) -> dict | None:
    """Read one length-prefixed JSON message from a binary buffer. Returns None on EOF."""
    header = buf.read(4)
    if len(header) < 4:
        return None
    length = struct.unpack(">I", header)[0]
    body = buf.read(length)
    if len(body) < length:
        return None
    return json.loads(body.decode("utf-8"))


def _stdin_reader(cmd_queue: queue.Queue):
    """Background thread: reads commands from stdin and puts them on the queue."""
    buf = sys.stdin.buffer
    while True:
        msg = _read_message(buf)
        if msg is None:
            cmd_queue.put(None)  # EOF / pipe closed → signal exit
            break
        cmd_queue.put(msg)


def run(engine_factory, *, crash_after_ready: bool = False, test_print: bool = False):
    """
    Main entry point for the pipe transport.
    engine_factory: callable() → TacticalEngine
    """
    _setup_io()
    _install_crash_handler()

    logger = logging.getLogger(__name__)
    logger.info("pipe transport starting, version=%s", SIM_VERSION)

    _send_message({"type": "progress", "step": "loading_config", "pct": 0.2})

    _send_message({"type": "progress", "step": "initializing_simulation", "pct": 0.4})
    engine = engine_factory()

    _send_message({"type": "progress", "step": "building_world", "pct": 0.8})

    if test_print:
        print("debug_intercept_test")  # intentional — tests that _StdoutTrap intercepts this

    _send_message({"type": "ready", "version": SIM_VERSION})
    logger.info("sent ready message")

    if crash_after_ready:
        raise RuntimeError("deliberate crash for pipe transport crash-handler test")

    cmd_queue = queue.Queue()
    reader = threading.Thread(target=_stdin_reader, args=(cmd_queue,), daemon=True)
    reader.start()

    from snapshot_serializer import full_snapshot, delta, DeadReckoningTracker
    import command_ingest
    import config as _config

    dr_tracker = DeadReckoningTracker()
    prev_state = full_snapshot(engine)
    _send_message(prev_state)
    _send_message({
        "type": "sim_state",
        "mission_briefing": _build_mission_briefing(prev_state, getattr(engine, "player_faction", 0)),
    })

    tick_interval = 1.0 / _config.TICK_HZ
    next_snap_at = time.monotonic() + _config.SNAPSHOT_INTERVAL_SEC
    tick_num = 0
    start_time = time.monotonic()

    while True:
        while True:
            try:
                pkt = cmd_queue.get_nowait()
                if pkt is None:
                    logger.info("stdin closed, exiting")
                    return
                logger.info("command received: type=%s kind=%s", pkt.get("type"), pkt.get("command", {}).get("kind") if isinstance(pkt.get("command"), dict) else pkt.get("cmd"))
                command_ingest.ingest(pkt, engine)
            except queue.Empty:
                break

        engine.step()

        now = time.monotonic()
        if now >= next_snap_at:
            pkt = full_snapshot(engine)
            dr_tracker.reset()
            next_snap_at += _config.SNAPSHOT_INTERVAL_SEC
        else:
            pkt = delta(engine, prev_state, dr_tracker)

        prev_state = full_snapshot(engine)
        _send_message(pkt)

        tick_num += 1
        sleep_for = (start_time + tick_num * tick_interval) - time.monotonic()
        if sleep_for > 0:
            time.sleep(sleep_for)


if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

    from tactical_engine import TacticalEngine
    from test_maps import open_field

    _crash = "--crash" in sys.argv
    _test_print = "--test-print" in sys.argv

    def _make_engine():
        tmap = open_field()
        eng = TacticalEngine(tmap, seed=42)
        eng.player_faction = 0
        eng.store.spawn("Vanguard", 0, 1000.0, 500.0)
        eng.store.spawn("Vanguard", 1, 1000.0, 3500.0)
        return eng

    run(_make_engine, crash_after_ready=_crash, test_print=_test_print)
