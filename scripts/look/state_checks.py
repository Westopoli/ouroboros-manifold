"""State checks over a fight file (schema om-fight-2). Each returns {verdict, numbers, tick}; nothing here returns PASS on missing data.
R-097-05 check reuses the rule's shape from scripts/skilllab/invariants_r6.py (same layer, living units, more than 3 consecutive frames).
# See also: scripts/skilllab/invariants_r6.py
"""
import math

DRAFT_LOOK_RADIUS = 15.0        # DRAFT-look-radius: one unit radius, wu (spec piece 1); Westley's
DRAFT_LOOK_MAX_TICKS = 3        # DRAFT-look-overlap-ticks: overlap allowed this many consecutive frames
DRAFT_LOOK_FROZEN_WINDOW = 5    # DRAFT-look-frozen-window: identical consecutive frames allowed; Westley's


def _res(verdict, numbers, tick=0):
    return {"verdict": verdict, "numbers": numbers, "tick": tick}


def check_overlap(fight, radius=DRAFT_LOOK_RADIUS, max_ticks=DRAFT_LOOK_MAX_TICKS):
    frames = fight.get("frames") or []
    if not frames:
        return _res("FAIL", {"reason": "no frames", "pairs": []})
    run, best = {}, {}
    for fr in frames:
        us = [u for u in fr["units"] if u["alive"]]
        now = {}
        for i, a in enumerate(us):
            for b in us[i + 1:]:
                if a["layer"] != b["layer"]:
                    continue
                d = math.hypot(a["x"] - b["x"], a["y"] - b["y"])
                if d < radius:
                    k = (min(a["id"], b["id"]), max(a["id"], b["id"]))
                    r = run.get(k, {"ticks": 0, "min_dist": d})
                    now[k] = {"ticks": r["ticks"] + 1, "min_dist": min(r["min_dist"], d), "last_tick": fr["tick"]}
        run = now
        for k, r in now.items():
            if r["ticks"] > max_ticks and (k not in best or r["ticks"] > best[k]["ticks"]):
                best[k] = dict(r)
    pairs = [{"a": k[0], "b": k[1], "ticks": r["ticks"], "last_tick": r["last_tick"], "min_dist": round(r["min_dist"], 3)}
             for k, r in sorted(best.items())]
    if pairs:
        return _res("FAIL", {"pairs": pairs, "radius": radius, "max_ticks": max_ticks}, pairs[0]["last_tick"])
    return _res("PASS", {"pairs": [], "radius": radius, "max_ticks": max_ticks}, frames[-1]["tick"])


def check_unit_in_wall(fight):
    frames = fight.get("frames") or []
    walls = fight.get("walls")
    if not frames:
        return _res("FAIL", {"reason": "no frames", "hits": []})
    if walls is None:
        return _res("UNSURE", {"reason": "fight has no walls", "hits": []})
    hits = []
    for fr in frames:
        for u in fr["units"]:
            if u["alive"] and any(w[0] <= u["x"] <= w[2] and w[1] <= u["y"] <= w[3] for w in walls):
                hits.append({"unit": u["id"], "tick": fr["tick"]})
    if hits:
        return _res("FAIL", {"hits": hits[:20], "count": len(hits)}, hits[0]["tick"])
    return _res("PASS", {"hits": []}, frames[-1]["tick"])


def check_frozen(fight, max_identical=DRAFT_LOOK_FROZEN_WINDOW):
    frames = fight.get("frames") or []
    if not frames:
        return _res("FAIL", {"reason": "no frames"})
    sig = lambda fr: [(u["id"], u["x"], u["y"], u["hp"], u["alive"]) for u in fr["units"]]
    n, worst, at = 1, 1, frames[0]["tick"]
    for p, fr in zip(frames, frames[1:]):
        n = n + 1 if sig(p) == sig(fr) else 1
        if n > worst:
            worst, at = n, fr["tick"]
    return _res("FAIL" if worst > max_identical else "PASS", {"longest_identical": worst, "max_identical": max_identical}, at)


def check_winner(fight, expected):
    w = (fight.get("result") or {}).get("winner")
    if not fight.get("frames") or w is None:
        return _res("FAIL", {"reason": "no frames or no winner", "winner": w})
    return _res("PASS" if w == expected else "FAIL", {"winner": w, "expected": expected}, (fight["result"].get("ticks") or 0))
