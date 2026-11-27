"""Lab stage 5 (facing, arcs and height bands; story docs/stories/H-091.md, rules R-091-08 to R-091-11): what `run.fight` computes when `--facing on` is given.

- `spawn_facing` (R-091-08): the facing each unit is set to before the first tick.
- `block` (R-091-09): the document's top-level `stage5` table.
- `climbing` (R-091-10): a unit's position along its slope, from the slope's record, the layout's slope feature (E-01 R-004-06); the engine's `transition_progress` reads 0 for a walker.
- `hit` and `regroup` (R-091-11): one `hits` entry per shot, and the entries moved into the frames a thinned file keeps.
DRAFT-stage5-front-deg 45 and DRAFT-stage5-rear-deg 135 are Westley's to rule. See also: scripts/skilllab/arena/stage5_measures.py (reads these entries back)."""
import math

FRONT_DEG, REAR_DEG = 45, 135   # DRAFT-stage5-front-deg, DRAFT-stage5-rear-deg: front up to 45, rear from 135, side between
ARC_PARAM = "OM_TP_FIRING_ARC_DEG"
SLOPE_PARAM = "OM_TP_SLOPE_UP_DIV"


def block(engine, w, arc_deg):
    """The document's `stage5` table; `arc_deg` is what `OM_TP_FIRING_ARC_DEG` was set to, the slope divisor is read from the world."""
    return {"arc_deg": arc_deg, "slope_up_div": engine.get_param(w, engine.param_id(SLOPE_PARAM)), "front_deg": FRONT_DEG, "rear_deg": REAR_DEG}


def spawn_facing(layout, centre, point, orders):
    """[[radians for each unit of side_a], [... side_b]]: the layout's own `facing` where a unit row has one; otherwise a holder (the side `orders` "hold:A" / "hold:B" gives no order)
    faces the other side's centre of mass and every other unit faces the orders point `point`. `centre` is [(x, y) of side A's spawn centroid, side B's]; each bearing is from the unit."""
    holder = {"hold:A": 0, "hold:B": 1}.get(orders)
    out = []
    for n, key in enumerate(("side_a", "side_b")):
        want = centre[1 - n] if holder == n else point
        out.append([u["facing"] if "facing" in u else math.atan2(want[1] - u["y"], want[0] - u["x"]) for u in layout[key]["units"]])
    return out


def climbing(slopes, x, y):
    """0.0 off a slope; on one, the fraction of the way from its foot (0) to its top (1) along its heading. `slopes` is the layout's slope features (`features.slopes(layout)`; only heading 0,
    rising toward +x, is built): the ramp is the feature's rectangle, x from `x - length / 2` (the foot) to `x + length / 2` (the top), y within half the `width` of its `y`.
    The engine's own slope record (om_terrain_slope_get) is not used: on a built ribbon it spans the whole row of cells, the flat ground either side of the ramp too (foot x 50, top x 3950 on a 4000 wu
    canvas), so a position along it is not a position along the ramp."""
    for f in slopes:
        foot = f["x"] - f["length"] / 2
        if foot <= x <= f["x"] + f["length"] / 2 and abs(y - f["y"]) <= f["width"] / 2:
            return round((x - foot) / f["length"], 4)
    return 0.0


def hit(engine, w, tick, attacker, victim):
    """One `hits` entry for a shot of `tick`: off_deg is the angle between the victim's facing and the direction from the victim to the attacker, on the positions and the facing the
    tick ended with (the rows of that tick's frame); cls from FRONT_DEG and REAR_DEG on the rounded angle."""
    vx, vy = engine.unit_pos(w, victim)
    ax, ay = engine.unit_pos(w, attacker)
    turn = (math.atan2(ay - vy, ax - vx) - engine.unit_facing(w, victim) + math.pi) % (2.0 * math.pi) - math.pi
    off = round(abs(math.degrees(turn)), 2)
    return {"a": attacker, "v": victim, "tick": tick, "off_deg": off, "cls": "front" if off <= FRONT_DEG else "rear" if off >= REAR_DEG else "side"}


def regroup(frames, ticks):
    """The frames of `ticks` (sorted) from `frames` ({tick: frame}), each a copy whose `hits` are every shot of `frames` with a tick after the previous kept frame's and not after its own,
    so a thinned file loses no shot (R-091-11)."""
    shots = [h for t in sorted(frames) for h in frames[t]["hits"]]
    out, n = [], 0
    for t in ticks:
        start = n
        while n < len(shots) and shots[n]["tick"] <= t:
            n += 1
        out.append(dict(frames[t], hits=shots[start:n]))
    return out
