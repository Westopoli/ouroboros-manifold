"""The arena runner: one layout, one seed, one fight, written down as a `fight.json` (spec: docs/stories/H-040.md "Part 2: arena runner";
file format: docs/stories/H-039.md, scripts/skilllab/arena/snapshot.py).

CLI: python3 -m scripts.skilllab.arena.run --layout <toml> --seed <int> --out <dir> [--seeds N] [--sight off|on] [--control-dir D] [--control ground|sight] [--cap-seconds 600]
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
stood still more than BLOCKED_SECONDS with a destination and no target; SNAPSHOT.md). `--control-dir D` also writes the control twin, the same layout with `features` emptied
and `movement` "walk" (`control_twin`: D/<id>-control.toml and .json), as D/<id>-control-s<n>.fight.json; its units walk on a canvas, so it differs from the main fight by the ground only.
Known gap: `Engine.spawn` takes no facing and engine.py does not bind `om_unit_set_facing`, so the layout's per-row `facing` is not applied; units
start at the engine default and attack-move turns them toward the enemy.
H-088 (stage 4, sight): `--sight on` is the stage 4 rule set (docs/stories/H-088.md): targeting by sight left on (R-093-02), ground era (`set_era_kind` 1), a canvas, every role
walks, reach 0 up 1 down for every role (DRAFT-stage4-reach-down), the holder of `hold:A` / `hold:B` on `order_guard` (R-096-08). The fight file then carries per-unit `seen`,
`sights`, `result.first_seen` (sampled every CHECK_EVERY ticks from tick 0) and `orders.guard`, and `results.md` two columns `first seen A` / `first seen B`. `--control sight`
(with `--control-dir`, `--sight on` only) writes D/<id>-control-s<n>.fight.json for every layout: the same fight with targeting by sight off (`fight` sight "control"),
the document `sight` "off". `--control ground` (default) is the twin above. See also: snapshot.validate, SNAPSHOT.md.
Stage 4 fixes (docs/reports/2026-11-06-stage4-fix-plan.md, H-088 follow-up): under `--sight on` the ground is the exact conversion (`features.apply(exact=True)`): planar rectangles
snapped to the 100 wu grid (snap.py; one `SNAPPED <id> <kind> authored ... built ...` line per feature, and `built_features` in the fight file) and each `vantage` as terrain
(hills.py), so a unit's starting layer is the ground's: `REJECT <id> G1 layer: side_a unit 0 ...` when the layout's `layer` column disagrees (a runner-local rule, not in rules.toml).
Layout `orders = "groups"` gives per-group orders with an optional release trigger (groups.py; `orders.groups` in the fight file); `REJECT <id> G2 groups: ...` for a malformed layout.
`--sight off` is unchanged (stages 1 to 3 reproduce byte for byte)."""
import argparse
import json
import sys
import tomllib
from pathlib import Path
from types import SimpleNamespace

from scripts.skilllab import invariants
from scripts.skilllab.arena import features, groups, hills, snap, snapshot
from scripts.skilllab.arena.rate import rate
from scripts.skilllab.catalogue.produce import _roster_ranges, check_layout, dump_toml, presets, rules
from scripts.skilllab.engine import Engine
from scripts.skilllab.fight import TICKS_PER_SECOND, _register_types

ROOT = Path(__file__).resolve().parents[3]
BASE_EVERY = 5 * TICKS_PER_SECOND   # DRAFT-snapshot-seconds; snapshot.frame_ticks only ever lands on multiples of this, or on the last tick
SIDES = (("A", 0, "side_a"), ("B", 1, "side_b"))
SILENCE_TICKS = 10 * TICKS_PER_SECOND   # DRAFT-silence-seconds
CHECK_EVERY = TICKS_PER_SECOND          # silence is tested once a sim second; H-088: `first_seen` is sampled on the same cadence (DRAFT-seen-sample-seconds 1)
BLOCKED_SECONDS = 2                     # H-063: a unit still this long with a destination and no target is blocked
STILL_WU = 2.0                          # moved no more than this since its anchor counts as still
REACH_RULE = "R8"                       # catalogue/rules.toml
MOVED_WU = 5.0                          # a living unit displaced more than this over the window is not silent
RESULTS_HEAD = "| id | a:b | predict | winner | survivors | ticks | agree | blocked |\n|---|---|---|---|---|---|---|---|\n"
SIGHT_RESULTS_HEAD = "| id | a:b | predict | winner | survivors | ticks | agree | blocked | first seen A | first seen B |\n|---|---|---|---|---|---|---|---|---|---|\n"   # H-088, --sight on
REACH_UP, REACH_DOWN = 0, 1             # H-088 DRAFT-stage4-reach-down: levels a unit can fire up and down under --sight on


def _setup_for(layout):
    """A stand-in for the Setup that `fight._register_types` reads (`groups[*].unit`, `unit_types`): every role is a built-in type."""
    roles = sorted({u["role"] for _, _, key in SIDES for u in layout[key]["units"]})
    return SimpleNamespace(groups=[SimpleNamespace(unit=r) for r in roles], unit_types={})


def _centroid(engine, w, ids):
    pts = [engine.unit_pos(w, u) for u in ids]
    return sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts)


def _frame(engine, w, tick, rows, blocked=None, seen=False, fired=()):
    """One frame: every spawned unit (dead ones stay), sorted by id; rows is [(unit id, side letter, role)]; `blocked` (H-063) is written when not None;
    `seen` (H-088) adds to each unit the sorted ids of the living enemies it sees (`engine.can_see`), [] for a dead unit; `fired` is the set of unit ids that fired
    since the previous captured frame (replay-firing-lines): each row says whether its unit, alive here, is in it."""
    units = []
    living = {uid: side for uid, side, _ in rows if engine.unit_alive(w, uid)}
    for uid, side, role in rows:
        alive = engine.unit_alive(w, uid)
        x, y = engine.unit_pos(w, uid)
        target = engine.unit_target(w, uid)
        units.append({"id": uid, "side": side, "role": role, "x": round(x, 2), "y": round(y, 2), "layer": int(engine.unit_layer(w, uid)),
                      "facing": round(engine.unit_facing(w, uid), 3), "hp": round(engine.unit_hp(w, uid), 1) if alive else 0.0,
                      "alive": alive, "target": target if target else None, "fired": alive and uid in fired})
        if seen:
            units[-1]["seen"] = [e for e, s in sorted(living.items()) if s != side and engine.can_see(w, uid, e)] if alive else []
    frame = {"tick": tick, "alive": [sum(1 for u in units if u["alive"] and u["side"] == s) for s in "AB"], "units": units}
    if blocked is not None:
        frame["blocked"] = blocked
    return frame


def _orders_point(layout, centre):
    """(point, movers): where the orders send units and which sides ('side_a', 'side_b') move; the engine's own rule, read from tick-0 centroids."""
    orders = layout.get("orders", "both_same_point")
    if orders == "groups":
        return tuple(groups.marker_point(layout)), ("side_a", "side_b")
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


def _ground_world(layout, sight):
    """(engine, world, preset) with the layout's ground laid as the fight lays it (`sight` as in fight()); the caller frees the world."""
    preset = presets()[layout["landscape"]]
    engine = Engine()
    w = engine.new_world(layout.get("seed", 1))
    features.apply(engine, w, layout, preset, layout.get("seed", 1), exact=sight != "off")
    return engine, w, preset


def unreachable(layout, sight="off"):
    """'side_b unit 2' for the first unit that cannot route to its orders point over the ground the engine is given (planar blocks, the slope, the hills), else None (H-063 rule R8).
    Builds a throwaway world to read the engine's own walk mask. A groups layout (F3) checks each group that walks to a fixed point (an `enemy_centroid` target is unknown
    before the fight); a release point is not a destination. See also: features.first_unreachable."""
    point, movers = _orders_point(layout, _layout_centres(layout))
    engine, w, preset = _ground_world(layout, sight)
    try:
        if layout.get("orders") != "groups":
            return features.first_unreachable(engine, w, layout, preset, point, movers, **({"exact": True} if sight != "off" else {}))   # --sight off: the stage 3 call, unchanged
        for r in layout["order_groups"]:
            if isinstance(r["to"], list):
                side = groups.SIDES[r["side"]][1]
                members = {(side, i) for i, u in enumerate(layout[side]["units"]) if u["group"] == r["group"]}
                miss = features.first_unreachable(engine, w, layout, preset, tuple(r["to"]), (side,), sight != "off", members)
                if miss:
                    return miss
        return None
    finally:
        engine.free_world(w)


def layer_mismatch(layout):
    """'side_a unit 0 is on layer 0 ...' for the first unit whose `layer` column disagrees with the ground the hills give it (stage 4, G1), else None. Only a layout with a vantage."""
    if not hills.vantages(layout):
        return None
    engine, w, _ = _ground_world(layout, "on")
    try:
        for _, _, key in SIDES:
            for i, u in enumerate(layout[key]["units"]):
                ground = hills.ground_layer(engine, w, u["x"], u["y"])
                if ground != u["layer"]:
                    return "%s unit %d is on layer %d in the layout but the ground there is layer %d" % (key, i, u["layer"], ground)
        return None
    finally:
        engine.free_world(w)


def control_twin(layout, layout_path, control_dir):
    """(twin layout, path of its TOML) for a layout `features.bound` says the engine is given something for, else (None, None). The twin is the same layout with
    `features` emptied and `movement` "walk" (its units still walk, `fight`); `<control_dir>/<id>-control.toml` and `.json` are written as `produce.write_layout` writes a
    layout. `layout_path` is the main layout's file, kept for the signature the runner passes. See also: fight, _document."""
    if not features.bound(layout):
        return None, None
    twin = {**layout, "features": [], "movement": "walk"}
    control_dir = Path(control_dir)
    control_dir.mkdir(parents=True, exist_ok=True)
    toml_path = control_dir / ("%s-control.toml" % layout["id"])
    toml_path.write_text(dump_toml(twin))
    toml_path.with_suffix(".json").write_text(json.dumps(twin, indent=2) + "\n")
    return twin, toml_path


def fight(layout, seed, sight, cap_seconds, every=BASE_EVERY):
    """Run one fight; returns (frames by tick, last tick, end, orders block). Frames are kept every `every` ticks (BASE_EVERY; closeup.py passes its K) and at the last tick,
    then chosen by `snapshot.frame_ticks` once the last tick is known (closeup.py keeps them all). `sight` "off" is stage 3's rule set; "on" is stage 4's (module docstring); "control" is stage 4's with
    targeting by sight off (`--control sight`). Under "on" the orders block gains `guard` and a `stage4` entry ({first_seen, sights}) that `_document` removes and writes."""
    engine = Engine()
    w = engine.new_world(seed)
    stage4 = sight != "off"
    try:
        engine.disable_abilities(w)
        if sight != "on":
            engine.set_param(w, engine.param_id("OM_TP_TARGET_BY_SIGHT"), 0)
        preset = presets()[layout["landscape"]]
        ground = features.apply(engine, w, layout, preset, seed, exact=stage4)
        types = _register_types(engine, w, _setup_for(layout))
        if ground or stage4 or layout.get("movement") == "walk":   # the control twin has no features and still walks; so does every stage 4 fight
            if not ground:
                engine.set_canvas(w, preset["width"], preset["height"])   # apply returns before it sets one, and a walker with no canvas never moves
            features.walk_on_ground(engine, w, types)
        if stage4:
            engine.set_era_kind(w, 1)
            for type_id, _ in types.values():
                engine.set_reach(w, type_id, REACH_UP, REACH_DOWN)
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
        group_state = None
        if orders == "groups":
            group_state = groups.start(engine, w, layout, ids, stage4)
            point = groups.marker_point(layout)
            doc_orders = {"mode": "groups", "point": [round(point[0], 2), round(point[1], 2)], "attacker": None}
        elif orders == "both_same_point":
            point = tuple(layout["orders_point"]) if "orders_point" in layout else ((centre[0][0] + centre[1][0]) / 2, (centre[0][1] + centre[1][1]) / 2)
            engine.order_attack_move(w, ids[0], *point)
            engine.order_attack_move(w, ids[1], *point)
            doc_orders = {"mode": "both_same_point", "point": [round(point[0], 2), round(point[1], 2)], "attacker": None}
        elif orders in ("hold:A", "hold:B"):
            holder = 0 if orders == "hold:A" else 1
            point = centre[holder]
            engine.order_attack_move(w, ids[1 - holder], *point)
            doc_orders = {"mode": "hold_and_attack", "point": [round(point[0], 2), round(point[1], 2)], "attacker": "AB"[1 - holder]}
            if stage4:
                engine.order_guard(w, ids[holder])
        else:
            raise ValueError("orders %r is not both_same_point, hold:A or hold:B" % (orders,))
        if stage4:
            doc_orders["guard"] = groups.guarded(layout, True) if orders == "groups" else orders != "both_same_point"
        first_seen = {"A": None, "B": None}   # H-088, --sight on: the first sampled tick at which that side's living units see a living enemy

        def sample_seen(at):
            for letter, faction, _ in SIDES:
                if first_seen[letter] is None and engine.seen_by_sight(w, faction, [u for u in ids[1 - faction] if engine.unit_alive(w, u)]):
                    first_seen[letter] = at

        still = {}   # unit id -> (x, y, tick) it was last seen moving at; read only when `ground`

        def blocked_now(at):
            return [uid for uid, _, _ in rows if uid in still and engine.unit_alive(w, uid) and at - still[uid][2] > BLOCKED_SECONDS * TICKS_PER_SECOND
                    and not engine.unit_target(w, uid) and engine.unit_destination(w, uid) is not None]

        monitor = invariants.Monitor(engine, w, preset["width"], preset["height"], sight)   # F0: every rule the checker knows, judged after each step; see doc["violations"]
        seen = sight == "on"
        frames = {0: _frame(engine, w, 0, rows, [] if ground else None, seen)}
        if seen:
            sample_seen(0)
        cap = cap_seconds * TICKS_PER_SECOND
        everyone = [u for f in ids for u in ids[f]]
        hp = {u: engine.unit_hp(w, u) for u in everyone}
        fired = set()   # attackers of fire events since the last captured frame; a thinned file keeps what the frame had when captured
        last_shot, history = 0, {0: {u: engine.unit_pos(w, u) for u in everyone}}
        tick, end = 0, "cap"
        while tick < cap:
            engine.step(w)
            monitor.after_step()
            fired |= engine.fire_attackers(w)
            tick += 1
            if group_state:
                groups.tick(engine, w, group_state, ids, tick)
                for g in group_state:
                    if g["released_at"] == tick:
                        monitor.new_order(g["units"])
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
            if tick % every == 0 or tick == cap:
                frames[tick] = _frame(engine, w, tick, rows, blocked_now(tick) if ground else None, seen, fired)
                fired = set()
            if seen and tick % CHECK_EVERY == 0:
                sample_seen(tick)
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
            frames[tick] = _frame(engine, w, tick, rows, blocked_now(tick) if ground else None, seen, fired)
        if seen:
            sights = {r: engine.type_stats(w, types[r][0])["sensor_radius"] for r in sorted(types)}
            doc_orders["stage4"] = {"first_seen": first_seen, "sights": sights}
        if group_state:
            doc_orders["groups"] = groups.record(group_state)
        doc_orders["invariants"] = monitor.document_keys()   # _document removes it
        return frames, tick, end, doc_orders
    finally:
        engine.free_world(w)


def _document(layout, layout_path, seed, sight, frames, last, end, orders, dense_every=None):
    """The fight file; `sight` "control" (fight()) is written as "off". `orders` may carry fight()'s `stage4` entry, which becomes `sights` and `result.first_seen`.
    `dense_every` (closeup.py): keep every frame given, in tick order, and write it as `snapshot_every`, instead of thinning to snapshot.MAX_FRAMES."""
    orders = dict(orders)
    stage4 = orders.pop("stage4", None)
    checked = orders.pop("invariants", None)   # F0: fight()'s verdict of the checker
    ticks = snapshot.frame_ticks(last, TICKS_PER_SECOND) if dense_every is None else sorted(frames)
    every = dense_every or (ticks[1] - ticks[0] if len(ticks) > 2 else BASE_EVERY)
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
    walks = features.bound(layout) or layout.get("movement") == "walk" or sight != "off"   # as fight(): the units walk (`ground`, the control twin, any stage 4 fight)
    doc = {"schema": snapshot.SCHEMA_V2, "ranges": {r: roster[r] for r in sorted(roles)}, "layout_id": layout["id"], "layout_path": shown, "landscape": layout["landscape"], "seed": seed, "tick_rate": TICKS_PER_SECOND,
            "snapshot_every": every, "sight": "off" if sight == "control" else sight, "orders": orders, "frames": [frames[t] for t in ticks],
            "result": {"winner": winner, "survivors": survivors, "ticks": last, "capped": end == "cap", "end": end, "stall": stall,
                       "predict": layout["predict"],
                       "agree": winner == layout["predict"]}}
    if walks:
        doc["movement_kind"] = features.WALKING_KIND
    if sight != "off" and features.planar_rects(layout):
        doc["built_features"] = snap.built_features(layout)   # F2: the snapped rectangles the engine blocks; the replay draws these, so drawn equals blocked
    if stage4:
        doc["sights"] = stage4["sights"]
        doc["result"]["first_seen"] = stage4["first_seen"]
    if checked:
        doc.update(checked)   # `violations` (the first 20) and `invalid`, only when a rule was broken
    return doc


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


def report_invalid(label, doc):
    """F0: one `INVALID <label> <rule> tick <N> unit <U>` line per distinct rule of the fight's `violations` (the earliest of that rule); True when the fight is invalid."""
    first = {}
    for v in doc.get("violations", []):
        first.setdefault(v["rule"], v)
    for rule in sorted(first, key=lambda r: (first[r]["tick"], r)):
        print("INVALID %s %s tick %d unit %d" % (label, rule, first[rule]["tick"], first[rule]["unit"]))
    return bool(doc.get("invalid"))


def main(argv=None):
    ap = argparse.ArgumentParser(prog="python3 -m scripts.skilllab.arena.run")
    ap.add_argument("--layout", required=True, type=Path)
    ap.add_argument("--seed", required=True, type=int)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--seeds", type=int, default=0, help="run N seeds from --seed and write <id>.rate.json (H-053)")
    ap.add_argument("--sight", choices=("off", "on"), default="off")
    ap.add_argument("--control-dir", type=Path, help="also run each seed as the control and write <id>-control-s<n>.fight.json here (H-063; --control picks which)")
    ap.add_argument("--control", choices=("ground", "sight"), default="ground",
                    help="ground: the twin with `features` emptied (H-063); sight: the same fight with targeting by sight off, every layout (H-088, needs --sight on)")
    ap.add_argument("--cap-seconds", type=int, default=snapshot.CAP_SECONDS)
    ap.add_argument("--allow-invalid", action="store_true", help="exit 0 although a fight broke a rule of scripts/skilllab/invariants.py (the INVALID lines and the flag in the file stay)")
    args = ap.parse_args(argv)
    if args.control == "sight" and args.sight == "off":
        ap.error("--control sight needs --sight on")
    with open(args.layout, "rb") as f:
        layout = tomllib.load(f)
    broken = check_layout(layout, presets(), rules())
    if broken:
        for rule in broken:
            print("REJECT %s %s" % (layout.get("id", args.layout.stem), rule))
        return 2
    if layout.get("orders") == "groups":
        bad = groups.check(layout)
        if bad:
            print("REJECT %s G2 groups: %s" % (layout["id"], bad))
            return 2
    wrong = layer_mismatch(layout) if args.sight == "on" else None
    if wrong:
        print("REJECT %s G1 layer: %s" % (layout["id"], wrong))
        return 2
    miss = unreachable(layout, args.sight)
    if miss:
        print("REJECT %s %s unreachable: %s" % (layout["id"], REACH_RULE, miss))
        return 2
    if args.sight == "on":
        for line in snap.report(layout):
            print(line)
    count = args.seeds or 1
    if args.seeds and "predict_rate" not in layout:
        print("REJECT %s missing predict_rate (--seeds writes a rate file)" % layout["id"])
        return 2
    args.out.mkdir(parents=True, exist_ok=True)
    fights = []
    invalid = False
    runs = [(layout["id"], args.sight)] + ([(layout["id"] + "-control", "control")] if args.control_dir and args.control == "sight" else [])   # the sight-off control is a run too
    for name, sight in runs:
        for rule, switch in sorted(invariants.suspended_for(sight).items()):
            print("SUSPENDED %s %s %s" % (name, rule, switch), file=sys.stderr)   # F0: a check this run cannot judge is said, never passed in silence (stderr: stdout is pinned by the stage tests)
    for seed in range(args.seed, args.seed + count):
        frames, last, end, orders = fight(layout, seed, args.sight, args.cap_seconds)
        doc = _document(layout, args.layout, seed, args.sight, frames, last, end, orders)
        snapshot.write(doc, args.out / ("%s-s%d.fight.json" % (layout["id"], seed)))
        invalid = report_invalid(layout["id"], doc) or invalid
        if args.control_dir and args.control == "sight":
            args.control_dir.mkdir(parents=True, exist_ok=True)
            control = _document(layout, args.layout, seed, "control", *fight(layout, seed, "control", args.cap_seconds))
            snapshot.write(control, args.control_dir / ("%s-control-s%d.fight.json" % (layout["id"], seed)))
            invalid = report_invalid(layout["id"] + "-control", control) or invalid
        elif args.control_dir and features.bound(layout):
            twin, twin_path = control_twin(layout, args.layout, args.control_dir)
            control = _document(twin, twin_path, seed, args.sight, *fight(twin, seed, args.sight, args.cap_seconds))
            snapshot.write(control, args.control_dir / ("%s-control-s%d.fight.json" % (layout["id"], seed)))
            invalid = report_invalid(layout["id"] + "-control", control) or invalid
        fights.append(snapshot.read(args.out / ("%s-s%d.fight.json" % (layout["id"], seed))))
        res = doc["result"]
        results = args.out / "results.md"
        row = "| %s | %d:%d | %s | %s | %d:%d | %d | %s | %d |\n" % (
            layout["id"], len(layout["side_a"]["units"]), len(layout["side_b"]["units"]), res["predict"], res["winner"],
            res["survivors"][0], res["survivors"][1], res["ticks"], "yes" if res["agree"] else "no",
            sum(len(fr.get("blocked", [])) for fr in doc["frames"]))
        if args.sight == "on":
            row = row[:-1] + " %s | %s |\n" % tuple("-" if res["first_seen"][s] is None else res["first_seen"][s] for s in "AB")
        head = "" if results.exists() and results.stat().st_size else SIGHT_RESULTS_HEAD if args.sight == "on" else RESULTS_HEAD
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
    return 2 if invalid and not args.allow_invalid else 0


if __name__ == "__main__":
    sys.exit(main())
