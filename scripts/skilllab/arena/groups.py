"""Per-group orders with an optional release trigger (stage 4 fix F3; docs/reports/2026-11-06-stage4-fix-plan.md, DEC-stage4-group-orders-2026-11-06).

Layout `orders = "groups"`: every unit row carries `group = "<name>"`, and each `[[order_groups]]` row gives one side's group an order: `side` "A" or "B", `group`, `order`
"attack_move" (to `to` at tick 0) or "hold" (a guard under the stage 4 rule set, R-096-08, nothing under `--sight off`), `to` an [x, y] or "enemy_centroid" (the centroid of the
living enemy units when the order is given), and for a hold an optional `release = {point = [x, y], radius = R}`: on the first tick on which any living enemy unit is within R wu
of the point (evaluated from engine state after each step, tick 0 included) the group's orders are cleared and it attack-moves to `to`. The fight file's `orders.groups`
records per group the unit ids, `order`, `to`, `release` and `released_at` (the tick, or null). A layout without `orders = "groups"` never reaches this module.
See also: scripts/skilllab/arena/run.py (the only caller), scripts/skilllab/catalogue/round3.py `trap` (the producer of the trap layouts)."""
import math

SIDES = {"A": (0, "side_a"), "B": (1, "side_b")}
ORDERS = ("attack_move", "hold")


def check(layout):
    """None when the groups are well formed, else the first problem as 'side_a unit 3' (a unit with no group row) or a short reason."""
    rows = layout.get("order_groups", [])
    known = set()
    for r in rows:
        if r.get("side") not in SIDES or r.get("order") not in ORDERS or "group" not in r:
            return "order_groups row %r" % (r,)
        if (r["side"], r["group"]) in known:
            return "order_groups group %s of side %s twice" % (r["group"], r["side"])
        known.add((r["side"], r["group"]))
        to = r.get("to")
        if not (to == "enemy_centroid" or (isinstance(to, list) and len(to) == 2)):
            return "order_groups row %s has no to" % r["group"]
    for letter, (_, key) in SIDES.items():
        for i, u in enumerate(layout[key]["units"]):
            if (letter, u.get("group")) not in known:
                return "%s unit %d" % (key, i)
    return None


def _centroid(engine, w, ids):
    live = [engine.unit_pos(w, u) for u in ids if engine.unit_alive(w, u)]
    return (sum(p[0] for p in live) / len(live), sum(p[1] for p in live) / len(live)) if live else None


def _attack(engine, w, g, ids):
    to = g["to"]
    point = _centroid(engine, w, ids[1 - SIDES[g["side"]][0]]) if to == "enemy_centroid" else to
    if point is not None:
        engine.order_attack_move(w, g["units"], point[0], point[1])


def start(engine, w, layout, ids, stage4):
    """The groups state, orders given at tick 0. `ids[faction]` are the spawned unit ids in layout order. Evaluates the triggers once, so one that already holds fires at 0."""
    state = []
    for r in layout["order_groups"]:
        faction, key = SIDES[r["side"]]
        units = [uid for uid, u in zip(ids[faction], layout[key]["units"]) if u["group"] == r["group"]]
        g = {"side": r["side"], "group": r["group"], "units": units, "order": r["order"], "to": r["to"], "release": r.get("release"), "released_at": None}
        if r["order"] == "attack_move":
            _attack(engine, w, g, ids)
        elif stage4:
            engine.order_guard(w, units)
        state.append(g)
    tick(engine, w, state, ids, 0)
    return state


def tick(engine, w, state, ids, at):
    """Release every hold whose trigger holds now (call after each engine step with the tick count)."""
    for g in state:
        rel = g["release"]
        if g["released_at"] is not None or not rel:
            continue
        enemies = ids[1 - SIDES[g["side"]][0]]
        if any(engine.unit_alive(w, u) and math.dist(engine.unit_pos(w, u), rel["point"]) <= rel["radius"] for u in enemies):
            engine.clear_orders(w, g["units"])
            _attack(engine, w, g, ids)
            g["released_at"] = at


def record(state):
    """The fight file's `orders.groups`."""
    return [dict(g, release=dict(g["release"]) if g["release"] else None) for g in state]


def marker_point(layout):
    """[x, y] for readers that draw one orders marker: the first release point, else the first fixed `to`, else [0.0, 0.0]."""
    for r in layout["order_groups"]:
        if r.get("release"):
            return [float(c) for c in r["release"]["point"]]
    for r in layout["order_groups"]:
        if isinstance(r["to"], list):
            return [float(c) for c in r["to"]]
    return [0.0, 0.0]


def guarded(layout, stage4):
    return bool(stage4 and any(r["order"] == "hold" for r in layout["order_groups"]))
