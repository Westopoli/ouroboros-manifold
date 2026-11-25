# spec: docs/northstar/plans/lab-isolation-2026-11-24/spec.md, piece LI2 (the isolation measures); interface: docs/reports/2026-11-24-li2-interface.md
"""Helpers shared by test_isolation_measures_*.py: synthetic fight documents (om-fight-2) with a known answer for each measure.
The module under test is imported lazily so a missing module fails each test (red), not the collection.

Premises, dumped from real lab files on 2026-11-24 (`r6-ladder/out/L-9106-s1.45245ff88.every2ticks.fight.json`, `L-0054-s1.4fa618ce7...`, `r6-compare/runs/A-sit/...`):
a frame is {tick, alive [a, b], units: [{id, side "A"|"B", role, x, y, layer, facing, hp, alive, target (id | null), fired (bool)}]}; dead units stay in every frame with hp 0.0;
the file carries no per-unit destination, only `orders` {mode both_same_point | hold_and_attack, attacker "A"|"B"|null, point [x, y]}; `ranges` {role: weapon range wu};
a stage 3 (sight off) file has no `sights`, no `seen`; `result` {winner, survivors [a, b], ticks, end, capped, stall, agree, predict}; the last frame can be one tick before result.ticks."""
import importlib
import math

NOT_MEASURED = "not measured"


def m():
    return importlib.import_module("scripts.skilllab.arena.isolation_measures")


def grid(span, max_frames=19):
    """Frame ticks 0 .. span (multiples of one step, step a multiple of 10 chosen so that no more than max_frames frames exist)."""
    step = 10 * math.ceil(span / (10.0 * (max_frames - 1)))
    ticks = list(range(0, span + 1, step))
    return ticks, step


def result(winner, survivors, ticks, end="wipe"):
    r = {"agree": winner == "A", "capped": end == "cap", "end": end, "predict": "A", "stall": False,
         "survivors": list(survivors), "ticks": ticks, "winner": winner}
    if end == "apart":
        r["nearest_enemy_wu"] = 371.47
    return r


def make_doc(roster, ticks, *, pos, hp=None, alive=None, target=None, fired=None, layer=None, orders=None, res=None, ranges=None,
             sights=None, with_fired=True, tick_rate=20):
    """roster [(id, side, role)]; pos(id, tick) -> (x, y); hp(id, tick) -> float (default 500, 0 once not alive); alive(id, tick) -> bool (default hp > 0);
    target(id, tick) -> id | None; fired(id, tick) -> bool; layer(id, tick) -> int. with_fired False leaves the key off every unit row (a lab that writes none)."""
    frames = []
    for t in ticks:
        rows = []
        for uid, side, role in sorted(roster):
            h = hp(uid, t) if hp else 500.0
            a = alive(uid, t) if alive else h > 0
            h = h if a else 0.0
            x, y = pos(uid, t)
            row = {"id": uid, "side": side, "role": role, "x": round(x, 2), "y": round(y, 2), "layer": layer(uid, t) if layer else 0, "facing": 0.0,
                   "hp": round(h, 1), "alive": bool(a), "target": target(uid, t) if (target and a) else None}
            if with_fired:
                row["fired"] = bool(fired(uid, t)) if (fired and a) else False
            rows.append(row)
        frames.append({"tick": t, "alive": [sum(1 for r in rows if r["alive"] and r["side"] == s) for s in "AB"], "units": rows})
    doc = {"schema": "om-fight-2", "layout_id": "L-9999", "layout_path": "synthetic.toml", "seed": 1, "tick_rate": tick_rate, "snapshot_every": 10,
           "sight": "off", "landscape": "small_flat", "frames": frames,
           "result": res if res is not None else result("A", frames[-1]["alive"], ticks[-1])}
    doc["orders"] = orders if orders is not None else {"attacker": None, "mode": "both_same_point", "point": [2000.0, 2000.0]}   # a lab file always has them
    if ranges is not None:
        doc["ranges"] = ranges
    if sights is not None:
        doc["sights"] = sights
    return doc


def static(points):
    """pos function: {id: (x, y)} constant."""
    return lambda uid, t: points[uid]


def dist(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])
