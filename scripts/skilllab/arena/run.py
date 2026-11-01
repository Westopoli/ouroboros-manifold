"""The arena runner: one layout, one seed, one fight, written down as a `fight.json` (spec: docs/stories/H-040.md "Part 2: arena runner";
file format: docs/stories/H-039.md, scripts/skilllab/arena/snapshot.py).

CLI: python3 -m scripts.skilllab.arena.run --layout <toml> --seed <int> --out <dir> [--sight off|on] [--cap-seconds 600]
Stage 1 floor (DEC-lab-stage1-floor-2026-10-31): sight off (`OM_TP_TARGET_BY_SIGHT` 0, csrc/unit.c:1175), every unit attack-moves to the enemy
centroid at tick 0, no defender, no guard, fight cap DRAFT-fight-cap (snapshot.CAP_SECONDS). Exit 0 with a FIGHT line, exit 2 with REJECT lines.
Known gap: `Engine.spawn` takes no facing and engine.py does not bind `om_unit_set_facing`, so the layout's per-row `facing` is not applied; units
start at the engine default and attack-move turns them toward the enemy."""
import argparse
import sys
import tomllib
from pathlib import Path
from types import SimpleNamespace

from scripts.skilllab.arena import snapshot
from scripts.skilllab.catalogue.produce import check_layout, presets, rules
from scripts.skilllab.engine import Engine
from scripts.skilllab.fight import TICKS_PER_SECOND, _register_types

ROOT = Path(__file__).resolve().parents[3]
BASE_EVERY = 5 * TICKS_PER_SECOND   # DRAFT-snapshot-seconds; snapshot.frame_ticks only ever lands on multiples of this, or on the last tick
SIDES = (("A", 0, "side_a"), ("B", 1, "side_b"))
RESULTS_HEAD = "| id | a:b | predict | winner | survivors | ticks | agree |\n|---|---|---|---|---|---|---|\n"


def _setup_for(layout):
    """A stand-in for the Setup that `fight._register_types` reads (`groups[*].unit`, `unit_types`): every role is a built-in type."""
    roles = sorted({u["role"] for _, _, key in SIDES for u in layout[key]["units"]})
    return SimpleNamespace(groups=[SimpleNamespace(unit=r) for r in roles], unit_types={})


def _centroid(engine, w, ids):
    pts = [engine.unit_pos(w, u) for u in ids]
    return sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts)


def _frame(engine, w, tick, rows):
    """One frame: every spawned unit (dead ones stay), sorted by id; rows is [(unit id, side letter, role)]."""
    units = []
    for uid, side, role in rows:
        alive = engine.unit_alive(w, uid)
        x, y = engine.unit_pos(w, uid)
        target = engine.unit_target(w, uid)
        units.append({"id": uid, "side": side, "role": role, "x": round(x, 2), "y": round(y, 2), "layer": int(engine.unit_layer(w, uid)),
                      "facing": round(engine.unit_facing(w, uid), 3), "hp": round(engine.unit_hp(w, uid), 1) if alive else 0.0,
                      "alive": alive, "target": target if target else None})
    return {"tick": tick, "alive": [sum(1 for u in units if u["alive"] and u["side"] == s) for s in "AB"], "units": units}


def fight(layout, seed, sight, cap_seconds):
    """Run one fight; returns (frames by tick, last tick, capped). Frames are kept every BASE_EVERY ticks and at the last tick, then chosen by
    `snapshot.frame_ticks` once the last tick is known."""
    engine = Engine()
    w = engine.new_world(seed)
    try:
        engine.disable_abilities(w)
        if sight == "off":
            engine.set_param(w, engine.param_id("OM_TP_TARGET_BY_SIGHT"), 0)
        types = _register_types(engine, w, _setup_for(layout))
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
        engine.order_attack_move(w, ids[0], *centre[1])
        engine.order_attack_move(w, ids[1], *centre[0])
        frames = {0: _frame(engine, w, 0, rows)}
        cap = cap_seconds * TICKS_PER_SECOND
        tick, capped = 0, True
        while tick < cap:
            engine.step(w)
            tick += 1
            if tick % BASE_EVERY == 0 or tick == cap:
                frames[tick] = _frame(engine, w, tick, rows)
            if min(sum(1 for u in ids[f] if engine.unit_alive(w, u)) for f in ids) == 0:
                capped = False
                break
        if tick not in frames:
            frames[tick] = _frame(engine, w, tick, rows)
        return frames, tick, capped
    finally:
        engine.free_world(w)


def _document(layout, layout_path, seed, sight, frames, last, capped):
    ticks = snapshot.frame_ticks(last, TICKS_PER_SECOND)
    every = ticks[1] - ticks[0] if len(ticks) > 2 else BASE_EVERY
    survivors = frames[last]["alive"]
    a, b = survivors
    winner = "A" if a > 0 and b == 0 else "B" if b > 0 and a == 0 else "draw"
    try:
        shown = Path(layout_path).resolve().relative_to(ROOT).as_posix()
    except ValueError:
        shown = Path(layout_path).as_posix()
    return {"schema": snapshot.SCHEMA, "layout_id": layout["id"], "layout_path": shown, "seed": seed, "tick_rate": TICKS_PER_SECOND,
            "snapshot_every": every, "sight": sight, "frames": [frames[t] for t in ticks],
            "result": {"winner": winner, "survivors": survivors, "ticks": last, "capped": capped, "predict": layout["predict"],
                       "agree": winner == layout["predict"]}}


def main(argv=None):
    ap = argparse.ArgumentParser(prog="python3 -m scripts.skilllab.arena.run")
    ap.add_argument("--layout", required=True, type=Path)
    ap.add_argument("--seed", required=True, type=int)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--sight", choices=("off", "on"), default="off")
    ap.add_argument("--cap-seconds", type=int, default=snapshot.CAP_SECONDS)
    args = ap.parse_args(argv)
    with open(args.layout, "rb") as f:
        layout = tomllib.load(f)
    broken = check_layout(layout, presets(), rules())
    if broken:
        for rule in broken:
            print("REJECT %s %s" % (layout.get("id", args.layout.stem), rule))
        return 2
    frames, last, capped = fight(layout, args.seed, args.sight, args.cap_seconds)
    doc = _document(layout, args.layout, args.seed, args.sight, frames, last, capped)
    args.out.mkdir(parents=True, exist_ok=True)
    snapshot.write(doc, args.out / ("%s-s%d.fight.json" % (layout["id"], args.seed)))
    res = doc["result"]
    results = args.out / "results.md"
    row = "| %s | %d:%d | %s | %s | %d:%d | %d | %s |\n" % (
        layout["id"], len(layout["side_a"]["units"]), len(layout["side_b"]["units"]), res["predict"], res["winner"],
        res["survivors"][0], res["survivors"][1], res["ticks"], "yes" if res["agree"] else "no")
    head = "" if results.exists() and results.stat().st_size else RESULTS_HEAD
    with open(results, "a", encoding="utf-8") as f:
        f.write(head + row)
    print("FIGHT %s seed %d winner %s ticks %d agree %s" % (layout["id"], args.seed, res["winner"], res["ticks"], "yes" if res["agree"] else "no"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
