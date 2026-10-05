"""Ping policies and hider scripts for the search scene. Pure functions of the view; no engine, no random."""
import math
from dataclasses import dataclass, field

from scripts.skilllab.search import SearchSetting

DECIDE_EVERY = 10
REVEAL_MEMORY = 200                 # provisional (lab draft, 2026-10-05)
SWEEP_BEARINGS = (-60, -30, 0, 30, 60)   # provisional (lab draft, 2026-10-05)
SWEEP_RINGS = (0.5, 1.0)            # provisional (lab draft, 2026-10-05)
SWEEP_LAYERS = 5                    # provisional (lab draft, 2026-10-05)
CHASE_UNITS = 4                     # provisional (lab draft, 2026-10-05): ready units that chase the last picture
SHIFT_EVERY = 400                   # provisional (lab draft, 2026-10-05)
DRIFT_LEG = 12000.0                 # provisional (lab draft, 2026-10-05): length of one drift move order


@dataclass
class PolicyView:
    tick: int
    setting: SearchSetting
    centre: tuple
    heading_deg: float
    layer: int
    ready: list
    unit_pos: dict
    revealed: dict
    memory: dict = field(default_factory=dict)


def _none(view):
    return []


def _ahead(view):
    h = math.radians(view.heading_deg)
    dx, dy = view.setting.reach * math.cos(h), view.setting.reach * math.sin(h)
    out = []
    for u in sorted(view.ready):
        x, y = view.unit_pos[u]
        out.append((u, view.layer, x + dx, y + dy))
    return out


def _sweep_targets(view):
    reach = view.setting.reach
    layers = [(view.layer + k) % SWEEP_LAYERS for k in range(SWEEP_LAYERS)]
    out = []
    for b in SWEEP_BEARINGS:
        a = math.radians(view.heading_deg + b)
        for r in SWEEP_RINGS:
            x = view.centre[0] + r * reach * math.cos(a)
            y = view.centre[1] + r * reach * math.sin(a)
            for layer in layers:
                out.append((layer, x, y))
    return out


def _sweep_units(view, units):
    targets = _sweep_targets(view)
    n = len(targets)
    i = view.memory.get("sweep_i", 0) % n
    out = []
    for u in units:
        pos = view.unit_pos.get(u, view.centre)
        for _ in range(n):
            layer, x, y = targets[i]
            i = (i + 1) % n
            if math.hypot(x - pos[0], y - pos[1]) <= view.setting.reach:
                out.append((u, layer, x, y))
                break
    view.memory["sweep_i"] = i
    return out


def _sweep(view):
    return _sweep_units(view, sorted(view.ready))


def _reactive(view):
    mem = view.memory
    last = mem.get("seen")
    if view.revealed:
        ids = sorted(view.revealed)
        cx = sum(view.revealed[i][0] for i in ids) / len(ids)
        cy = sum(view.revealed[i][1] for i in ids) / len(ids)
        layer = view.revealed[ids[0]][2]
        vx = vy = 0.0
        if last and 0 < view.tick - last["tick"] <= REVEAL_MEMORY:
            dt = view.tick - last["tick"]
            vx, vy = (cx - last["x"]) / dt, (cy - last["y"]) / dt
        last = mem["seen"] = {"tick": view.tick, "x": cx, "y": cy, "layer": layer, "vx": vx, "vy": vy}
    units = sorted(view.ready)
    if not last or view.tick - last["tick"] > REVEAL_MEMORY:
        return _sweep_units(view, units)
    ahead = view.tick - last["tick"] + DECIDE_EVERY
    tx, ty = last["x"] + last["vx"] * ahead, last["y"] + last["vy"] * ahead
    chasers = units[:CHASE_UNITS]
    out = [(u, last["layer"], tx, ty) for u in chasers]
    out += _sweep_units(view, [u for u in units if u not in chasers])
    return sorted(out, key=lambda o: o[0])


POLICIES = {"none": _none, "ahead": _ahead, "sweep": _sweep, "reactive": _reactive}


def _still(tick, centre, heading_deg, layer, speed):
    return []


def _drift(tick, centre, heading_deg, layer, speed):
    h = math.radians(heading_deg)
    return [("move", centre[0] + DRIFT_LEG * math.cos(h), centre[1] + DRIFT_LEG * math.sin(h))]


def _shift(tick, centre, heading_deg, layer, speed):
    orders = _drift(tick, centre, heading_deg, layer, speed)
    if tick > 0 and tick % SHIFT_EVERY == 0:
        step = 1 if (tick // SHIFT_EVERY) % 2 == 1 else -1
        if not 0 <= layer + step <= SWEEP_LAYERS - 1:
            step = -step
        orders.append(("layer", layer + step))
    return orders


HIDER_SCRIPTS = {"still": _still, "drift": _drift, "shift": _shift}
