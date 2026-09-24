import math
import re
from dataclasses import dataclass, field

RUBBERBAND_FACTOR = 1.5
STUCK_WINDOW = 40
STUCK_MIN_DISP = 0.05
STUCK_MIN_DIST = 25.0
BACKWARDS_MIN_TICKS = 5
BACKWARDS_MIN_SPEED = 0.1
DROPPED_GRACE = 3
DROPPED_TOL = 1e-9


@dataclass
class Finding:
    kind: str
    uid: int
    tick: int
    detail: dict = field(default_factory=dict)


def fingerprint(finding):
    keys = ",".join(sorted(finding.detail.keys()))
    return re.sub(r"\d", "", f"{finding.kind}:{keys}")


def rubberband(trace, speed, factor=RUBBERBAND_FACTOR):
    out = []
    for prev, cur in zip(trace, trace[1:]):
        limit = factor * speed * cur["dt"]
        for uid, u in cur["units"].items():
            p = prev["units"].get(uid)
            if p is None:
                continue
            dx, dy = u["x"] - p["x"], u["y"] - p["y"]
            disp = math.hypot(dx, dy)
            dot = dx * u["vx"] + dy * u["vy"]
            if disp > limit and dot < 0:
                out.append(Finding("rubberband", uid, cur["tick"],
                                   {"displacement": disp, "limit": limit, "dot": dot}))
    return out


def stuck(trace, window=STUCK_WINDOW, min_disp=STUCK_MIN_DISP, min_dist=STUCK_MIN_DIST):
    out = []
    reported = set()
    for end in range(window - 1, len(trace)):
        start = end - window + 1
        for uid, u in trace[end]["units"].items():
            if uid in reported:
                continue
            span = trace[start:end + 1]
            if not all(uid in t["units"] and t["units"][uid]["target_active"] for t in span):
                continue
            s = trace[start]["units"][uid]
            disp = math.hypot(u["x"] - s["x"], u["y"] - s["y"])
            dist = math.hypot(u["tx"] - u["x"], u["ty"] - u["y"])
            if disp < min_disp and dist > min_dist:
                reported.add(uid)
                out.append(Finding("stuck", uid, trace[end]["tick"],
                                   {"window": window, "displacement": disp, "dist_to_target": dist}))
    return out


def backwards(trace, min_ticks=BACKWARDS_MIN_TICKS, min_speed=BACKWARDS_MIN_SPEED):
    out = []
    streak = {}
    for t in trace:
        for uid, u in t["units"].items():
            vmag = math.hypot(u["vx"], u["vy"])
            dot = u["vx"] * math.cos(u["facing"]) + u["vy"] * math.sin(u["facing"])
            if vmag > min_speed and dot < 0:
                streak[uid] = streak.get(uid, 0) + 1
                if streak[uid] == min_ticks:
                    out.append(Finding("backwards", uid, t["tick"],
                                       {"consecutive_ticks": min_ticks, "dot": dot}))
            else:
                streak[uid] = 0
    return out


def dropped_order(trace, grace=DROPPED_GRACE, tol=DROPPED_TOL):
    out = []
    for i, t in enumerate(trace):
        for cmd in t["commands"]:
            if cmd["ack"] != 0:
                continue
            uid = cmd["uid"]
            taken = False
            for later in trace[i:i + grace + 1]:
                u = later["units"].get(uid)
                if u and abs(u["tx"] - cmd["tx"]) <= tol and abs(u["ty"] - cmd["ty"]) <= tol:
                    taken = True
                    break
            if not taken:
                out.append(Finding("dropped_order", uid, t["tick"],
                                   {"grace": grace, "commanded": (cmd["tx"], cmd["ty"])}))
    return out


def run_all(trace, speed):
    return {
        "rubberband": rubberband(trace, speed),
        "stuck": stuck(trace),
        "backwards": backwards(trace),
        "dropped_order": dropped_order(trace),
    }
