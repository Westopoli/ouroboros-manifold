"""Look-judge rig piece 5: compare an approved om-fight-2 trace with today's against DRAFT-feel-<measure> tolerances."""
import json
import math
import tomllib
from pathlib import Path

from scripts.qa import rts_detectors as det

TOLERANCES = Path(__file__).with_name("tolerances.toml")
MEASURES = ["path_length_ratio", "path_shape", "arrival_spread", "formation_spread", "nn_spacing",
            "stops", "reversals", "jitter", "time_overlapped", "shots_fired", "kill_order"]
ARRIVE_EPS = 0.5      # DRAFT: a unit has settled at its last tick that moved more than this, wu
OVERLAP_RADIUS = 10.0  # DRAFT: two alive units closer than this overlap, wu
SAMPLES = 20          # DRAFT: frames sampled for the O(n^2) spacing measures


def load_tolerances(path=None):
    return tomllib.loads(Path(path or TOLERANCES).read_text())


def _load(src):
    try:
        f = src if isinstance(src, dict) else json.loads(Path(src).read_text())
        if not f["frames"] or not f["frames"][0]["units"]:
            return None
        return f
    except Exception:
        return None


def _paths(f):
    """{uid: [(x, y) or None per frame]}"""
    n, out = len(f["frames"]), {}
    for i, fr in enumerate(f["frames"]):
        for u in fr["units"]:
            out.setdefault(u["id"], [None] * n)[i] = (u["x"], u["y"])
    return out


def _length(p):
    pts = [q for q in p if q]
    return sum(math.dist(a, b) for a, b in zip(pts, pts[1:]))


def _alive(fr):
    return [(u["x"], u["y"]) for u in fr["units"] if u["alive"]]


def _sample(n):
    return sorted({round(i * (n - 1) / (SAMPLES - 1)) for i in range(SAMPLES)}) if n > 1 else [0]


def _spread(pts):
    if not pts:
        return 0.0
    cx, cy = sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts)
    return math.sqrt(sum((x - cx) ** 2 + (y - cy) ** 2 for x, y in pts) / len(pts))


def _nn(pts):
    return [min(math.dist(p, q) for j, q in enumerate(pts) if j != i) for i, p in enumerate(pts)] if len(pts) > 1 else []


def _overlapped(pts):
    cells = {}
    for x, y in pts:
        cells.setdefault((math.floor(x / OVERLAP_RADIUS), math.floor(y / OVERLAP_RADIUS)), []).append((x, y))
    for (cx, cy), own in cells.items():
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for p in own:
                    for q in cells.get((cx + dx, cy + dy), ()):
                        if p is not q and math.dist(p, q) < OVERLAP_RADIUS:
                            return True
    return False


def _median(v):
    v = sorted(v)
    return v[len(v) // 2] if v else 0.0


def _detector_trace(f):
    """om-fight-2 frames as rts_detectors frames: dt 1, velocity is the previous tick's step, target is the order's x on the unit's own row."""
    pt = (f.get("orders") or {}).get("point")
    out, prev, vel = [], {}, {}
    for fr in f["frames"]:
        units, cur = {}, {}
        for u in fr["units"]:
            if not u["alive"]:
                continue
            uid, p = u["id"], (u["x"], u["y"])
            v = vel.get(uid, (0.0, 0.0))
            units[uid] = {"x": p[0], "y": p[1], "vx": v[0], "vy": v[1], "facing": u["facing"],
                          "tx": pt[0] if pt else p[0], "ty": p[1], "target_active": True}
            cur[uid] = p
        vel = {uid: (p[0] - prev[uid][0], p[1] - prev[uid][1]) if uid in prev else (0.0, 0.0) for uid, p in cur.items()}
        prev = cur
        out.append({"tick": fr["tick"], "dt": 1.0, "commands": [], "units": units})
    return out


def _kill_order(f):
    dead = {}
    for fr in f["frames"]:
        for u in fr["units"]:
            if not u["alive"]:
                dead.setdefault(u["id"], fr["tick"])
    return [uid for uid, _ in sorted(dead.items(), key=lambda kv: (kv[1], kv[0]))]


def _settle(f):
    ticks = [fr["tick"] for fr in f["frames"]]
    last = 0
    for p in _paths(f).values():
        for i in range(1, len(p)):
            if p[i] and p[i - 1] and math.dist(p[i], p[i - 1]) > ARRIVE_EPS:
                last = max(last, i)
    return ticks[last] - ticks[0]


def _scalars(f, speed):
    n = len(f["frames"])
    idx = _sample(n)
    nn = [d for i in idx for d in _nn(_alive(f["frames"][i]))]
    trace = _detector_trace(f)
    return {
        "arrival_spread": _settle(f),
        "formation_spread": sum(_spread(_alive(f["frames"][i])) for i in idx) / len(idx),
        "nn_spacing": _median(nn),
        "stops": len(det.stuck(trace)),
        "reversals": len(det.backwards(trace)),
        "jitter": len(det.rubberband(trace, speed)),
        "time_overlapped": sum(_overlapped(_alive(fr)) for fr in f["frames"]) * f.get("snapshot_every", 1),
        "shots_fired": sum(u["fired"] for fr in f["frames"] for u in fr["units"]),
    }


def _series(f, measure):
    frames = f["frames"]
    if measure == "formation_spread":
        return [_spread(_alive(fr)) for fr in frames]
    if measure == "nn_spacing":
        return [_median(_nn(_alive(fr))) for fr in frames]
    if measure == "time_overlapped":
        return [float(_overlapped(_alive(fr))) for fr in frames]
    if measure == "shots_fired":
        total, out = 0, []
        for fr in frames:
            total += sum(u["fired"] for u in fr["units"])
            out.append(total)
        return out
    if measure == "kill_order":
        return [sum(not u["alive"] for u in fr["units"]) for fr in frames]
    paths = _paths(f)  # movement measures: mean distance walked so far
    return [sum(_length(p[:i + 1]) for p in paths.values()) / len(paths) for i in range(len(frames))]


def _camera(a, b):
    xs, ys = [], []
    for f in (a, b):
        for fr in f["frames"]:
            for u in fr["units"]:
                xs.append(u["x"])
                ys.append(u["y"])
    return {"min_x": min(xs), "max_x": max(xs), "min_y": min(ys), "max_y": max(ys)}


def _fail(error):
    return {"verdict": "FAIL", "error": error, "rows": [], "page": {"camera": {}, "panels": []}}


def compare(approved, today, tolerances=None):
    a, t = _load(approved), _load(today)
    if a is None or t is None:
        return _fail("approved trace unusable" if a is None else "today trace unusable")
    tol = {**load_tolerances(), **(tolerances or {})}
    pa, pt = _paths(a), _paths(t)
    ratios, shapes = [], []
    for uid, p in pa.items():
        q = pt.get(uid)
        la = _length(p)
        ratios.append((_length(q) / la if la else 1.0) if q else 0.0)
        shapes.append(sum(math.dist(x, y) for x, y in zip(p, q) if x and y) / max(1, len(p)) if q else math.inf)
    speed = _median([d for p in pa.values() for d in (math.dist(x, y) for x, y in zip(p, p[1:]) if x and y) if d > 0]) or 1.0
    sa, st = _scalars(a, speed), _scalars(t, speed)
    sa["path_length_ratio"], st["path_length_ratio"] = 1.0, max(ratios, key=lambda r: abs(r - 1.0))
    sa["path_shape"], st["path_shape"] = 0.0, max(shapes)
    ka, kt = _kill_order(a), _kill_order(t)
    sa["kill_order"], st["kill_order"] = 0, sum(x != y for x, y in zip(ka, kt)) + abs(len(ka) - len(kt))
    rows = []
    for m in MEASURES:
        d, limit = abs(st[m] - sa[m]), tol[f"DRAFT-feel-{m}"]
        rows.append({"measure": m, "verdict": "PASS" if d <= limit else "FAIL", "approved": sa[m], "today": st[m],
                     "difference": d, "tolerance": limit})
    n = min(len(a["frames"]), len(t["frames"]))
    panels = [{"measure": r["measure"], "ticks": [fr["tick"] for fr in a["frames"][:n]],
               "approved": _series(a, r["measure"])[:n], "today": _series(t, r["measure"])[:n],
               "approved_value": r["approved"], "today_value": r["today"], "tolerance": r["tolerance"]}
              for r in rows if r["verdict"] == "FAIL"]
    return {"verdict": "FAIL" if panels else "PASS", "rows": rows, "page": {"camera": _camera(a, t), "panels": panels}}
