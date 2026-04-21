# Headless TCP client that speaks the same protocol as Godot's WsClient.
# Consumes snapshots + deltas, maintains a local dead-reckoned unit dict,
# and logs any position "snap" — the distance between where DR predicted
# a unit would be and where the authoritative update puts it. Snaps above
# the noise floor likely correspond to the visible hitches in-game.
#
# Usage:
#   terminal 1: python3 simulation/run_debug_server.py
#   terminal 2: python3 simulation/perf_probe_client.py [duration_sec]
#
# Output: logs/client_perf.jsonl

import json
import math
import os
import socket
import sys
import time

sys.path.insert(0, os.path.dirname(__file__))
import config


PERF_PATH = "logs/client_perf.jsonl"
HOST = "127.0.0.1"
PORT = 8765
# 2x the server's resync threshold: below this, "snap" is just float noise,
# not a user-perceivable teleport.
SNAP_NOISE_FLOOR_WU = config.DR_RESYNC_THRESHOLD * 2.0


class ClientState:
    def __init__(self):
        # uid → {"pos": [x,y], "vel": [vx,vy], "last_update_tick": int, "fresh": bool}
        self.units: dict = {}
        self.tick: int = 0
        self.pending_snaps: list = []  # accumulated per-message, cleared by caller

    def apply_snapshot(self, snap: dict):
        self.tick = snap.get("tick", 0)
        # Note: a full snapshot is expected to STOMP dead-reckoned state.
        # That's precisely hypothesis A — we log the implied stomp distance
        # for each previously-known unit before overwriting.
        new_units = {u["uid"]: u for u in snap.get("units", [])}
        dt = config.TACTICAL_TICK_DURATION
        for uid, old in self.units.items():
            if uid not in new_units:
                continue
            elapsed = (self.tick - old["last_update_tick"]) * dt
            dr_x = old["pos"][0] + old["vel"][0] * elapsed
            dr_y = old["pos"][1] + old["vel"][1] * elapsed
            new_pos = new_units[uid]["pos"]
            d = math.hypot(new_pos[0] - dr_x, new_pos[1] - dr_y)
            if d > SNAP_NOISE_FLOOR_WU:
                self.pending_snaps.append({
                    "uid": uid,
                    "snap_wu": round(d, 3),
                    "elapsed_ticks": self.tick - old["last_update_tick"],
                    "vel_mag": round(math.hypot(old["vel"][0], old["vel"][1]), 3),
                    "cause": "snapshot_stomp",
                })
        self.units = {}
        for u in snap.get("units", []):
            self.units[u["uid"]] = {
                "pos": list(u["pos"]),
                "vel": list(u.get("velocity", [0.0, 0.0])),
                "last_update_tick": self.tick,
                "fresh": True,  # first update after snapshot has vel=[0,0] → suppress false positive
            }

    def apply_delta(self, d: dict):
        dt = config.TACTICAL_TICK_DURATION
        self.tick = d.get("tick", self.tick + 1)

        for uid in d.get("units_removed", []):
            self.units.pop(uid, None)

        for u in d.get("units_added", []):
            self.units[u["uid"]] = {
                "pos": list(u["pos"]),
                "vel": list(u.get("velocity", [0.0, 0.0])),
                "last_update_tick": self.tick,
                "fresh": True,
            }

        updated_uids = set()
        for upd in d.get("units_updated", []):
            uid = upd["uid"]
            updated_uids.add(uid)
            if uid not in self.units:
                continue
            u = self.units[uid]
            if "pos" in upd:
                elapsed = (self.tick - u["last_update_tick"]) * dt
                dr_x = u["pos"][0] + u["vel"][0] * elapsed
                dr_y = u["pos"][1] + u["vel"][1] * elapsed
                new_pos = upd["pos"]
                d_snap = math.hypot(new_pos[0] - dr_x, new_pos[1] - dr_y)
                # Skip first update after add — fresh units have vel=[0,0]
                # so any real motion registers as a false "snap".
                if d_snap > SNAP_NOISE_FLOOR_WU and not u.get("fresh", False):
                    vel_mag = math.hypot(u["vel"][0], u["vel"][1])
                    # Backward: new pos is closer to old pos than DR pos was.
                    dist_old_to_dr = math.hypot(dr_x - u["pos"][0], dr_y - u["pos"][1])
                    dist_old_to_new = math.hypot(new_pos[0] - u["pos"][0], new_pos[1] - u["pos"][1])
                    backward = dist_old_to_new < dist_old_to_dr - 0.1
                    self.pending_snaps.append({
                        "uid": uid,
                        "snap_wu": round(d_snap, 3),
                        "elapsed_ticks": self.tick - u["last_update_tick"],
                        "vel_mag": round(vel_mag, 3),
                        "backward": backward,
                        "cause": "delta_update",
                    })
                u["pos"] = list(new_pos)
                u["last_update_tick"] = self.tick
                u["fresh"] = False
            if "velocity" in upd:
                u["vel"] = list(upd["velocity"])

        # Dead-reckon all unupdated units forward by one tick.
        for uid, u in self.units.items():
            if uid in updated_uids:
                continue
            if u["vel"][0] == 0.0 and u["vel"][1] == 0.0:
                continue
            u["pos"][0] += u["vel"][0] * dt
            u["pos"][1] += u["vel"][1] * dt

    def drain_snaps(self) -> list:
        s = self.pending_snaps
        self.pending_snaps = []
        return s


def run_probe(duration_sec: float, out_path: str):
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    fh = open(out_path, "w", encoding="utf-8")
    fh.write(json.dumps({
        "type": "header",
        "wall_time": time.time(),
        "duration_sec": duration_sec,
        "snap_noise_floor_wu": SNAP_NOISE_FLOOR_WU,
    }) + "\n")

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((HOST, PORT))
    sock.settimeout(1.0)

    state = ClientState()
    buf = b""
    start = time.monotonic()
    deadline = start + duration_sec
    msg_count = 0
    total_snaps = 0

    while time.monotonic() < deadline:
        try:
            chunk = sock.recv(65536)
        except socket.timeout:
            continue
        if not chunk:
            break
        buf += chunk
        while b"\n" in buf:
            line, buf = buf.split(b"\n", 1)
            if not line:
                continue
            try:
                msg = json.loads(line.decode("utf-8"))
            except json.JSONDecodeError:
                continue
            t_recv = time.monotonic() - start
            mtype = msg.get("type", "?")
            if mtype == "snapshot":
                state.apply_snapshot(msg)
            elif mtype == "delta":
                state.apply_delta(msg)
            else:
                continue
            snaps = state.drain_snaps()
            total_snaps += len(snaps)
            rec = {
                "tick": state.tick,
                "msg": mtype,
                "t_recv": round(t_recv, 6),
                "bytes": len(line),
                "units_in_state": len(state.units),
                "snap_events": len(snaps),
                "snap_max_wu": round(max((s["snap_wu"] for s in snaps), default=0.0), 3),
            }
            fh.write(json.dumps(rec) + "\n")
            for s in snaps:
                fh.write(json.dumps({"tick": state.tick, "event": "snap", **s}) + "\n")
            msg_count += 1
        fh.flush()

    sock.close()
    fh.close()
    return msg_count, total_snaps, state


if __name__ == "__main__":
    duration = float(sys.argv[1]) if len(sys.argv) > 1 else 30.0
    print(f"Connecting to {HOST}:{PORT}, probing for {duration}s ...")
    try:
        msg_count, total_snaps, state = run_probe(duration, PERF_PATH)
    except ConnectionRefusedError:
        print("Connection refused — is run_debug_server.py running?")
        sys.exit(1)
    print(f"Done. {msg_count} messages received. {total_snaps} snap events. "
          f"Final state: {len(state.units)} units, tick {state.tick}.")
    print(f"Log: {PERF_PATH}")
