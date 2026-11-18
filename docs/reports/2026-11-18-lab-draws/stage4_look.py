#!/usr/bin/env python3
"""Independent per-tick reading of a stage 4 fight file (every tick). Not the lab checker: written from the rule text."""
import json, math, sys
from collections import Counter, defaultdict

path = sys.argv[1]
d = json.load(open(path))
frames = d["frames"]
R = d["ranges"]
MARGIN = 0.1

rects = []
for f in d.get("built_features", []):
    for b in f.get("boxes", []) or []:
        rects.append((b["x"] - b["w"] / 2, b["y"] - b["h"] / 2, b["x"] + b["w"] / 2, b["y"] + b["h"] / 2))
    for k in ("walls", "rects", "blocks"):
        for b in f.get(k, []) or []:
            if isinstance(b, dict):
                if "x0" in b:
                    rects.append((b["x0"], b["y0"], b["x1"], b["y1"]))
                else:
                    rects.append((b["x"] - b["w"] / 2, b["y"] - b["h"] / 2, b["x"] + b["w"] / 2, b["y"] + b["h"] / 2))
            else:
                rects.append(tuple(b))
print("layout", d["layout_id"], "ticks", len(frames) - 1, "result", d["result"]["winner"], d["result"]["survivors"])
print("feature keys", [(f.get("kind"), sorted(f.keys())) for f in d.get("built_features", [])])
print("obstacle rects", rects)


def inside(x, y, r, pad=0.0):
    return r[0] + pad < x < r[2] - pad and r[1] + pad < y < r[3] - pad


def seg_hits(p, q, r, pad=1.0):
    """Liang-Barsky: does segment p-q cross the interior of rect r shrunk by pad."""
    x0, y0, x1, y1 = r[0] + pad, r[1] + pad, r[2] - pad, r[3] - pad
    dx, dy = q[0] - p[0], q[1] - p[1]
    t0, t1 = 0.0, 1.0
    for pp, qq in ((-dx, p[0] - x0), (dx, x1 - p[0]), (-dy, p[1] - y0), (dy, y1 - p[1])):
        if pp == 0:
            if qq < 0:
                return False
        else:
            t = qq / pp
            if pp < 0:
                if t > t1:
                    return False
                t0 = max(t0, t)
            else:
                if t < t0:
                    return False
                t1 = min(t1, t)
    return t0 < t1


def dist(a, b):
    return math.hypot(a["x"] - b["x"], a["y"] - b["y"])


C = Counter()
ex = defaultdict(list)


def note(key, item, cap=6):
    C[key] += 1
    if len(ex[key]) < cap:
        ex[key].append(item)


start = {u["id"]: (u["x"], u["y"]) for u in frames[0]["units"]}
last_hp_drop = {}
last_shot = {}
close_run = Counter()
max_ratio = 0.0
shots = 0
picks = 0
guard_max = Counter()

prev = None
for fr in frames:
    t = fr["tick"]
    U = {u["id"]: u for u in fr["units"]}
    alive = [u for u in fr["units"] if u["alive"]]
    seen_side = defaultdict(set)
    for u in alive:
        seen_side[u["side"]].update(u.get("seen") or [])
    if prev:
        PU, pseen = prev
        for u in alive:
            p = PU.get(u["id"])
            if p and u["hp"] < p["hp"] - 1e-9:
                last_hp_drop[u["id"]] = t
    for u in alive:
        # A. inside an obstacle
        for r in rects:
            if inside(u["x"], u["y"], r):
                note("A inside obstacle", (t, u["id"], round(u["x"], 1), round(u["y"], 1)))
        p = prev[0].get(u["id"]) if prev else None
        moved = math.hypot(u["x"] - p["x"], u["y"] - p["y"]) if p else 0.0
        if u["side"] == "A":
            sx, sy = start[u["id"]]
            guard_max[u["id"]] = max(guard_max[u["id"]], math.hypot(u["x"] - sx, u["y"] - sy))
        tgt = U.get(u["target"]) if u["target"] is not None else None
        rng = R[u["role"]]
        notice = rng * (1 + MARGIN)
        if u.get("fired") and tgt is not None:
            shots += 1
            ptgt = prev[0].get(tgt["id"]) if prev else None
            cands = [tgt] + ([ptgt] if ptgt else [])
            me = [u] + ([p] if p else [])
            dmin = min(dist(a, b) for a in me for b in cands)
            max_ratio = max(max_ratio, dmin / rng)
            # B. line through an obstacle (every reading must cross to count)
            for r in rects:
                if all(seg_hits((a["x"], a["y"]), (b["x"], b["y"]), r) for a in me for b in cands):
                    note("B shot line crosses an obstacle (" + u["role"] + ")", (t, u["id"], tgt["id"]))
            # C. shot at a target the side sees in neither frame
            if tgt["id"] not in seen_side[u["side"]] and not (prev and tgt["id"] in prev[1][u["side"]]):
                note("C shot at a target its side does not see", (t, u["id"], tgt["id"]))
            # D. beyond range
            if dmin > rng + 8.0:
                note("D shot beyond attack range", (t, u["id"], tgt["id"], round(dmin, 1), rng, u["layer"], tgt["layer"]))
            # E. fired on a tick it moved
            if moved > 0.5:
                note("E fired on a tick it moved", (t, u["id"], round(moved, 2)))
            # I. reach: 0 up, 1 down
            if tgt["layer"] > u["layer"]:
                note("I fired up at a higher layer", (t, u["id"], tgt["id"], u["layer"], tgt["layer"]))
            if u["layer"] - tgt["layer"] > 1:
                note("I fired down more than one layer", (t, u["id"], tgt["id"], u["layer"], tgt["layer"]))
            last_shot[u["id"]] = (t, u["x"], u["y"])
        # F. own-power move in the nine ticks after a shot (pushes cannot be told apart: reported as a count with the largest step)
        ls = last_shot.get(u["id"])
        if ls and 0 < t - ls[0] <= 9 and moved > 1.0:
            note("F moved within 9 ticks of its shot (step > 1 wu; includes pushes)", (t, u["id"], round(moved, 2)))
        if p:
            # G. a pick beyond the notice distance in every reading, with no hit taken lately
            if u["target"] is not None and u["target"] != p["target"] and tgt is not None:
                picks += 1
                ptgt = prev[0].get(tgt["id"])
                dmin = min(dist(a, b) for a in (u, p) for b in ([tgt] + ([ptgt] if ptgt else [])))
                hit_lately = t - last_hp_drop.get(u["id"], -999) <= 6
                if dmin > notice + 1.0 and not hit_lately:
                    note("G pick beyond the notice distance, no hit taken in the last 6 ticks", (t, u["id"], tgt["id"], round(dmin, 1), round(notice, 1)))
                # nearest: another enemy seen in both frames nearer in every reading
                for e in alive:
                    if e["side"] == u["side"] or e["id"] == tgt["id"]:
                        continue
                    pe = prev[0].get(e["id"])
                    if not pe or e["id"] not in seen_side[u["side"]] or e["id"] not in prev[1][u["side"]]:
                        continue
                    if e["layer"] > u["layer"] or u["layer"] - e["layer"] > 1:
                        continue
                    far_e = max(dist(a, b) for a in (u, p) for b in (e, pe))
                    near_t = min(dist(a, b) for a in (u, p) for b in ([tgt] + ([ptgt] if ptgt else [])))
                    if far_e < near_t - 1.0 and far_e <= notice and not hit_lately:
                        note("G2 pick was not the nearest seen enemy in reach (every reading)", (t, u["id"], tgt["id"], round(near_t, 1), e["id"], round(far_e, 1)))
                        break
            # H. a swap straight from one live, seen, in-notice target to another
            if p["target"] is not None and u["target"] is not None and u["target"] != p["target"]:
                old = U.get(p["target"]); pold = prev[0].get(p["target"])
                if old and old["alive"] and pold and old["id"] in seen_side[u["side"]] and old["id"] in prev[1][u["side"]]:
                    dmax = max(dist(a, b) for a in (u, p) for b in (old, pold))
                    if dmax <= notice - 1.0 and not (t - last_hp_drop.get(u["id"], -999) <= 6):
                        note("H target swapped while the old one was alive, seen and inside the notice distance", (t, u["id"], p["target"], u["target"], round(dmax, 1)))
    # J. pairs on one layer closer than 28 wu for more than 3 ticks
    now = set()
    n = len(alive)
    for i in range(n):
        a = alive[i]
        for j in range(i + 1, n):
            b = alive[j]
            if a["layer"] == b["layer"] and abs(a["x"] - b["x"]) < 28 and abs(a["y"] - b["y"]) < 28 and dist(a, b) < 28:
                now.add((a["id"], b["id"]))
    for k in list(close_run):
        if k not in now:
            del close_run[k]
    for k in now:
        close_run[k] += 1
        if close_run[k] == 4:
            a, b = U[k[0]], U[k[1]]
            note("J same-layer pair under 28 wu for more than 3 ticks", (t, k[0], k[1], round(dist(a, b), 1)))
    prev = (U, seen_side)

print("shots judged", shots, "| picks judged", picks, "| largest shot distance / range", round(max_ratio, 3))
if d["orders"].get("guard") or "hold" in str(d["orders"].get("mode")):
    print("side A farthest from its start (wu):", round(max(guard_max.values()), 1))
print("orders", d["orders"])
if not C:
    print("NO FINDING")
for k in sorted(C):
    print(f"{C[k]:>7}  {k}")
    for e in ex[k]:
        print("          ", e)
