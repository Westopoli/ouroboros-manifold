"""The arena runner: one layout, one seed, one fight, written down as a `fight.json` (spec: docs/stories/H-040.md "Part 2: arena runner";
file format: docs/stories/H-039.md, scripts/skilllab/arena/snapshot.py).

CLI: python3 -m scripts.skilllab.arena.run --layout <toml> --seed <int> --out <dir> [--seeds N] [--sight off|on] [--cap-seconds 600]
H-053: `--seeds N` runs seeds S..S+N-1 from `--seed S`, one fight file each, then writes `<id>.rate.json` beside them (rate.py; the layout's `predict_rate`
is required). Layout key `orders_point` = [x, y] replaces the midpoint for both_same_point. Both sides wiped on the same tick is winner "none".
Stage 1 floor (DEC-lab-stage1-floor-2026-10-31): sight off (`OM_TP_TARGET_BY_SIGHT` 0, csrc/unit.c:1175), no defender, no guard, fight cap
DRAFT-fight-cap (snapshot.CAP_SECONDS). Orders (H-052, docs/stories/H-040.md "Orders and fight end"): layout key `orders` = "both_same_point" (default;
every unit of both sides attack-moves to the midpoint of the tick-0 centroids) or "hold:<A|B>" (that side gets no order, the other attack-moves to its centroid).
Fight end: wipe; silence (DRAFT-silence-seconds 10: over the last 10 s of sim time no shot by either side and no living unit moved more than
MOVED_WU, clock from tick 0); cap. Silence with both sides alive is a stall (winner "stall", `FIGHT <id> seed <n> STALL ticks <t>`).
Exit 0 with a FIGHT line, exit 2 with REJECT lines.
H-063 (stage 3, the ground pushes back): the layout's features go to the engine (features.py: planar blocks, the slope band); a layout whose moving units cannot
reach their destination is REJECTed `REJECT <id> R8 unreachable: side_b unit 2` (exit 2); a layout with features writes a per-frame `blocked` list (unit ids that
stood still more than BLOCKED_SECONDS with a destination and no target; SNAPSHOT.md). `--control-dir D` also writes the control twin, the same layout with `features` emptied, as D/<id>-control-s<n>.fight.json.
Known gap: `Engine.spawn` takes no facing and engine.py does not bind `om_unit_set_facing`, so the layout's per-row `facing` is not applied; units
start at the engine default and attack-move turns them toward the enemy."""
import argparse
import json
import sys
import tomllib
from pathlib import Path
from types import SimpleNamespace

from scripts.skilllab.arena import features, snapshot
from scripts.skilllab.arena.rate import rate
from scripts.skilllab.catalogue.produce import _roster_ranges, check_layout, presets, rules
from scripts.skilllab.engine import Engine
from scripts.skilllab.fight import TICKS_PER_SECOND, _register_types

ROOT = Path(__file__).resolve().parents[3]
BASE_EVERY = 5 * TICKS_PER_SECOND   # DRAFT-snapshot-seconds; snapshot.frame_ticks only ever lands on multiples of this, or on the last tick
SIDES = (("A", 0, "side_a"), ("B", 1, "side_b"))
SILENCE_TICKS = 10 * TICKS_PER_SECOND   # DRAFT-silence-seconds
CHECK_EVERY = TICKS_PER_SECOND          # silence is tested once a sim second
BLOCKED_SECONDS = 2                     # H-063: a unit still this long with a destination and no target is blocked
STILL_WU = 2.0                          # moved no more than this since its anchor counts as still
REACH_RULE = "R8"                       # catalogue/rules.toml
MOVED_WU = 5.0                          # a living unit displaced more than this over the window is not silent
RESULTS_HEAD = "| id | a:b | predict | winner | survivors | ticks | agree |\n|---|---|---|---|---|---|---|\n"


def _setup_for(layout):
    """A stand-in for the Setup that `fight._register_types` reads (`groups[*].unit`, `unit_types`): every role is a built-in type."""
    roles = sorted({u["role"] for _, _, key in SIDES for u in layout[key]["units"]})
    return SimpleNamespace(groups=[SimpleNamespace(unit=r) for r in roles], unit_types={})


def _centroid(engine, w, ids):
    pts = [engine.unit_pos(w, u) for u in ids]
    return sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts)


def _frame(engine, w, tick, rows, blocked=None):
    """One frame: every spawned unit (dead ones stay), sorted by id; rows is [(unit id, side letter, role)]; `blocked` (H-063) is written when not None."""
    units = []
    for uid, side, role in rows:
        alive = engine.unit_alive(w, uid)
        x, y = engine.unit_pos(w, uid)
        target = engine.unit_target(w, uid)
        units.append({"id": uid, "side": side, "role": role, "x": round(x, 2), "y": round(y, 2), "layer": int(engine.unit_layer(w, uid)),
                      "facing": round(engine.unit_facing(w, uid), 3), "hp": round(engine.unit_hp(w, uid), 1) if alive else 0.0,
                      "alive": alive, "target": target if target else None})
    frame = {"tick": tick, "alive": [sum(1 for u in units if u["alive"] and u["side"] == s) for s in "AB"], "units": units}
    if blocked is not None:
        frame["blocked"] = blocked
    return frame


def _orders_point(layout, centre):
    """(point, movers): where the orders send units and which sides ('side_a', 'side_b') move; the engine's own rule, read from tick-0 centroids."""
    orders = layout.get("orders", "both_same_point")
    if orders == "both_same_point":
        point = tuple(layout["orders_point"]) if "orders_point" in layout else ((centre[0][0] + centre[1][0]) / 2, (centre[0][1] + centre[1][1]) / 2)
        return point, ("side_a", "side_b")
    if orders in ("hold:A", "hold:B"):
        holder = 0 if orders == "hold:A" else 1
        return centre[holder], ("side_b",) if holder == 0 else ("side_a",)
    raise ValueError("orders %r is not both_same_point, hold:A or hold:B" % (orders,))


def _layout_centres(layout):
    return [(sum(u["x"] for u in layout[key]["units"]) / len(layout[key]["units"]), sum(u["y"] for u in layout[key]["units"]) / len(layout[key]["units"]))
            for _, _, key in SIDES]


def unreachable(layout):
    """'side_b unit 2' for the first unit that cannot route to its orders point over the layout's planar features, else None (H-063 rule R8)."""
    point, movers = _orders_point(layout, _layout_centres(layout))
    return features.first_unreachable(layout, presets()[layout["landscape"]], point, movers)


def fight(layout, seed, sight, cap_seconds):
    """Run one fight; returns (frames by tick, last tick, end, orders block). Frames are kept every BASE_EVERY ticks and at the last tick, then chosen by
    `snapshot.frame_ticks` once the last tick is known."""
    engine = Engine()
    w = engine.new_world(seed)
    try:
        engine.disable_abilities(w)
        if sight == "off":
            engine.set_param(w, engine.param_id("OM_TP_TARGET_BY_SIGHT"), 0)
        ground = features.apply(engine, w, layout, presets()[layout["landscape"]], seed)
        types = _register_types(engine, w, _setup_for(layout))
        if ground:
            features.walk_on_ground(engine, w, types)
        rows, ids = [], {}
        for letter, faction, key in SIDES:
            ids[faction] = []
            for u in layout[key]["units"]:
                uid = engine.spawn(w, types[u["role"]][0], faction, u["x"], u["y"], u["layer"])
                if uid == 0:
                    raise RuntimeError("spawn of %s at (%s, %s) layer %s returned unit id 0" % (u["role"], u["x"], u["y"], u["layer"]))
                ids[faction].append(uid)
                rows.append((uid, letter, u["role"]))
        rows.sort()
        centre = {f: _centroid(engine, w, ids[f]) for f in ids}
        orders = layout.get("orders", "both_same_point")
        if orders == "both_same_point":
            point = tuple(layout["orders_point"]) if "orders_point" in layout else ((centre[0][0] + centre[1][0]) / 2, (centre[0][1] + centre[1][1]) / 2)
            engine.order_attack_move(w, ids[0], *point)
            engine.order_attack_move(w, ids[1], *point)
            doc_orders = {"mode": "both_same_point", "point": [round(point[0], 2), round(point[1], 2)], "attacker": None}
        elif orders in ("hold:A", "hold:B"):
            holder = 0 if orders == "hold:A" else 1
            point = centre[holder]
            engine.order_attack_move(w, ids[1 - holder], *point)
            doc_orders = {"mode": "hold_and_attack", "point": [round(point[0], 2), round(point[1], 2)], "attacker": "AB"[1 - holder]}
        else:
            raise ValueError("orders %r is not both_same_point, hold:A or hold:B" % (orders,))
        still = {}   # unit id -> (x, y, tick) it was last seen moving at; read only when `ground`

        def blocked_now(at):
            return [uid for uid, _, _ in rows if uid in still and engine.unit_alive(w, uid) and at - still[uid][2] > BLOCKED_SECONDS * TICKS_PER_SECOND
                    and not engine.unit_target(w, uid) and engine.unit_destination(w, uid) is not None]

        frames = {0: _frame(engine, w, 0, rows, [] if ground else None)}
        cap = cap_seconds * TICKS_PER_SECOND
        everyone = [u for f in ids for u in ids[f]]
        hp = {u: engine.unit_hp(w, u) for u in everyone}
        last_shot, history = 0, {0: {u: engine.unit_pos(w, u) for u in everyone}}
        tick, end = 0, "cap"
        while tick < cap:
            engine.step(w)
            tick += 1
            for u in everyone:
                if hp[u] > 0:
                    h = engine.unit_hp(w, u)
                    if h < hp[u]:
                        last_shot = tick
                    hp[u] = h
            if ground and tick % CHECK_EVERY == 0:
                for uid in everyone:
                    x, y = engine.unit_pos(w, uid)
                    if uid not in still or (x - still[uid][0]) ** 2 + (y - still[uid][1]) ** 2 > STILL_WU * STILL_WU:
                        still[uid] = (x, y, tick)
            if tick % BASE_EVERY == 0 or tick == cap:
                frames[tick] = _frame(engine, w, tick, rows, blocked_now(tick) if ground else None)
            if min(sum(1 for u in ids[f] if engine.unit_alive(w, u)) for f in ids) == 0:
                end = "wipe"
                break
            if tick % CHECK_EVERY == 0:
                now = history[tick] = {u: engine.unit_pos(w, u) for u in everyone if engine.unit_alive(w, u)}
                before = history.pop(tick - SILENCE_TICKS, None)
                if before is not None and last_shot <= tick - SILENCE_TICKS and not any(
                        u in before and (p[0] - before[u][0]) ** 2 + (p[1] - before[u][1]) ** 2 > MOVED_WU * MOVED_WU for u, p in now.items()):
                    end = "silence"
                    break
        if tick not in frames:
            frames[tick] = _frame(engine, w, tick, rows, blocked_now(tick) if ground else None)
        return frames, tick, end, doc_orders
    finally:
        engine.free_world(w)


def _document(layout, layout_path, seed, sight, frames, last, end, orders):
    ticks = snapshot.frame_ticks(last, TICKS_PER_SECOND)
    every = ticks[1] - ticks[0] if len(ticks) > 2 else BASE_EVERY
    survivors = frames[last]["alive"]
    a, b = survivors
    stall = end == "silence" and a > 0 and b > 0
    winner = "A" if a > 0 and b == 0 else "B" if b > 0 and a == 0 else "stall" if stall else "none" if end == "wipe" else "draw"
    try:
        shown = Path(layout_path).resolve().relative_to(ROOT).as_posix()
    except ValueError:
        shown = Path(layout_path).as_posix()
    roster = _roster_ranges()
    roles = {u["role"] for u in frames[0]["units"]}
    return {"schema": snapshot.SCHEMA_V2, "ranges": {r: roster[r] for r in sorted(roles)}, "layout_id": layout["id"], "layout_path": shown, "seed": seed, "tick_rate": TICKS_PER_SECOND,
            "snapshot_every": every, "sight": sight, "orders": orders, "frames": [frames[t] for t in ticks],
            "result": {"winner": winner, "survivors": survivors, "ticks": last, "capped": end == "cap", "end": end, "stall": stall,
                       "predict": layout["predict"],
                       "agree": winner == layout["predict"]}}


def is_mirror(layout):
    """True when side B is side A reflected across the line or point midway between their centroids (same roles, same positions); H-053 Scoring: such a layout with
    Predict draw is not scored. DRAFT-mirror-test, the Architect's reading of "exact mirror"."""
    ua, ub = layout["side_a"]["units"], layout["side_b"]["units"]
    if len(ua) != len(ub):
        return False
    cx = (sum(u["x"] for u in ua) + sum(u["x"] for u in ub)) / (2 * len(ua))
    cy = (sum(u["y"] for u in ua) + sum(u["y"] for u in ub)) / (2 * len(ua))
    key = lambda pts: sorted((role, round(x, 3), round(y, 3)) for role, x, y in pts)
    a = [(u["role"], u["x"], u["y"]) for u in ua]
    return any(key(a2) == key((u["role"], u["x"], u["y"]) for u in ub)
               for a2 in ([(r, 2 * cx - x, y) for r, x, y in a], [(r, x, 2 * cy - y) for r, x, y in a], [(r, 2 * cx - x, 2 * cy - y) for r, x, y in a]))


def main(argv=None):
    ap = argparse.ArgumentParser(prog="python3 -m scripts.skilllab.arena.run")
    ap.add_argument("--layout", required=True, type=Path)
    ap.add_argument("--seed", required=True, type=int)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--seeds", type=int, default=0, help="run N seeds from --seed and write <id>.rate.json (H-053)")
    ap.add_argument("--sight", choices=("off", "on"), default="off")
    ap.add_argument("--control-dir", type=Path, help="also run each seed with `features` emptied and write <id>-control-s<n>.fight.json here (H-063)")
    ap.add_argument("--cap-seconds", type=int, default=snapshot.CAP_SECONDS)
    args = ap.parse_args(argv)
    with open(args.layout, "rb") as f:
        layout = tomllib.load(f)
    broken = check_layout(layout, presets(), rules())
    if broken:
        for rule in broken:
            print("REJECT %s %s" % (layout.get("id", args.layout.stem), rule))
        return 2
    miss = unreachable(layout)
    if miss:
        print("REJECT %s %s unreachable: %s" % (layout["id"], REACH_RULE, miss))
        return 2
    count = args.seeds or 1
    if args.seeds and "predict_rate" not in layout:
        print("REJECT %s missing predict_rate (--seeds writes a rate file)" % layout["id"])
        return 2
    args.out.mkdir(parents=True, exist_ok=True)
    fights = []
    for seed in range(args.seed, args.seed + count):
        frames, last, end, orders = fight(layout, seed, args.sight, args.cap_seconds)
        doc = _document(layout, args.layout, seed, args.sight, frames, last, end, orders)
        snapshot.write(doc, args.out / ("%s-s%d.fight.json" % (layout["id"], seed)))
        if args.control_dir and features.bound(layout):
            twin = {**layout, "features": []}
            args.control_dir.mkdir(parents=True, exist_ok=True)
            snapshot.write(_document(twin, args.layout, seed, args.sight, *fight(twin, seed, args.sight, args.cap_seconds)),
                           args.control_dir / ("%s-control-s%d.fight.json" % (layout["id"], seed)))
        fights.append(snapshot.read(args.out / ("%s-s%d.fight.json" % (layout["id"], seed))))
        res = doc["result"]
        results = args.out / "results.md"
        row = "| %s | %d:%d | %s | %s | %d:%d | %d | %s |\n" % (
            layout["id"], len(layout["side_a"]["units"]), len(layout["side_b"]["units"]), res["predict"], res["winner"],
            res["survivors"][0], res["survivors"][1], res["ticks"], "yes" if res["agree"] else "no")
        head = "" if results.exists() and results.stat().st_size else RESULTS_HEAD
        with open(results, "a", encoding="utf-8") as f:
            f.write(head + row)
        if res["stall"]:
            print("FIGHT %s seed %d STALL ticks %d" % (layout["id"], seed, res["ticks"]))
        else:
            print("FIGHT %s seed %d winner %s ticks %d agree %s" % (layout["id"], seed, res["winner"], res["ticks"], "yes" if res["agree"] else "no"))
    if args.seeds:
        summary = rate(fights, layout["predict_rate"], mirror=is_mirror(layout))
        (args.out / ("%s.rate.json" % layout["id"])).write_text(json.dumps(summary, indent=2) + "\n")
        print("RATE %s seeds %d rate_a %s predict_rate %s agree %s" % (layout["id"], len(fights), summary["rate_a"], summary["predict_rate"],
                                                                      {True: "yes", False: "no", None: "not scored (mirror)"}[summary["agree"]]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
