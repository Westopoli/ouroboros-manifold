"""The ping search scene (Stage A): one run on open ground, nobody fires; the measures.
Spec: docs/northstar/plans/2026-10-05-ping-search-spec.md.
Hold fire: both sides spawn a clone of the Vanguard with attack_range 0 (HOLD_FIRE_TYPE); checked by experiment that
idle units of the stock Vanguard do auto-acquire and lose hp, and the clone loses none. No attack order is issued."""
import math
import random
from dataclasses import dataclass, field

from scripts.skilllab import invariants
from scripts.skilllab.formations import place

VANGUARD = 2
TICKS_PER_SECOND = 20
HOLD_FIRE_TYPE = 100
CANVAS = (12000.0, 12000.0)             # provisional (lab draft, 2026-10-05)
SEEKER_START = (-3000.0, 0.0)           # provisional (lab draft, 2026-10-05)
ORIGIN = (6000.0, 6000.0)               # canvas centre; the engine clamps to 0..canvas, so spec coordinates are shifted by it
SEEKER_LAYER = 2                        # provisional (lab draft, 2026-10-05)
SEEKER_HEADING_DEG = 0.0                # provisional (lab draft, 2026-10-05)
HIDER_FORCE = 16                        # provisional (lab draft, 2026-10-05)
BLOB_RADIUS = 100.0                     # provisional (lab draft, 2026-10-05)
DECIDE_EVERY = 10                       # provisional (lab draft, 2026-10-05)
CAP_TICKS = 2400                        # provisional (lab draft, 2026-10-05)
AHEAD_HALF_ANGLE_DEG = 75.0             # provisional (lab draft, 2026-10-05)
PLACEMENT_EXTRA = 2000.0                # provisional (lab draft, 2026-10-05)
LAYERS = 5
GOAL_LEG = 12000.0                      # length of one move order


@dataclass(frozen=True)
class SearchSetting:
    radius: float          # ping radius, wu
    reach: float           # ping reach, wu
    reveal_ticks: int
    cooldown_ticks: int
    force: int             # seeker headcount; every unit casts


@dataclass(frozen=True)
class Placement:
    dx: float
    dy: float              # hider centre, relative to the seeker's start
    layer: int             # 0..4
    heading_deg: float
    script: str            # a key of search_policies.HIDER_SCRIPTS


@dataclass(frozen=True)
class SideResult:
    found_before_contact: bool
    first_reveal_tick: int | None
    warning_ticks: int | None
    share_revealed: float
    layer_learned: bool
    picture_age_ticks: int | None
    pings_cast: int
    pings_found: int


@dataclass(frozen=True)
class SearchResult:
    side: tuple
    contact_tick: int | None
    ended: str
    violations: list = field(default_factory=list)   # the rule checker (scripts/skilllab/invariants.py): first 20 by (tick, rule, unit); [] when clean
    invalid: bool = False
    suspended: dict = field(default_factory=dict)


def placements(seed, n, sight, reach_max):
    from scripts.skilllab.search_policies import HIDER_SCRIPTS
    keys = list(HIDER_SCRIPTS)
    rng = random.Random(seed)
    out = []
    for i in range(n):
        bearing = math.radians(rng.uniform(-AHEAD_HALF_ANGLE_DEG, AHEAD_HALF_ANGLE_DEG))
        dist = rng.uniform(sight * 1.001, reach_max + PLACEMENT_EXTRA)
        out.append(Placement(dx=dist * math.cos(bearing), dy=dist * math.sin(bearing), layer=rng.randrange(LAYERS),
                             heading_deg=rng.uniform(0.0, 360.0), script=keys[i % len(keys)]))
    return out


def coverage_rate(setting, layers=LAYERS):
    return (setting.force * math.pi * setting.radius ** 2) / (
        (setting.cooldown_ticks / TICKS_PER_SECOND) * math.pi * setting.reach ** 2 * layers)


def summarise_side(reveal_log, contact_tick, cap_ticks, enemy_headcount, pings):
    end = cap_ticks if contact_tick is None else contact_tick
    kept = [(t, ids) for t, ids in reveal_log if t < end and ids]
    pings_found = sum(1 for _, n in pings if n > 0)
    if not kept:
        return SideResult(False, None, None, 0.0, False, None, len(pings), pings_found)
    seen = set().union(*(ids for _, ids in kept))
    first = min(t for t, _ in kept)
    last = max(t for t, _ in kept)
    return SideResult(True, first, end - first, len(seen) / enemy_headcount, True, end - last, len(pings), pings_found)


def _centre(pos):
    return (sum(p[0] for p in pos) / len(pos), sum(p[1] for p in pos) / len(pos))


def _move_all(engine, w, ids, centre, tx, ty):
    for u in ids:
        px, py = engine.unit_pos(w, u)
        engine.order_move(w, [u], px + tx - centre[0], py + ty - centre[1])


def run_search(setting, policy0, policy1, placement, seed, cap_ticks=CAP_TICKS, engine=None):
    from scripts.skilllab.search_policies import HIDER_SCRIPTS, POLICIES, PolicyView
    if engine is None:
        from scripts.skilllab.engine import Engine
        engine = Engine()
    w = engine.new_world(seed)
    try:
        engine.disable_abilities(w)
        engine.set_canvas(w, *CANVAS)
        engine.set_ping_params(w, radius=setting.radius, reach=setting.reach, reveal_ticks=setting.reveal_ticks,
                               cooldown_ticks=setting.cooldown_ticks)
        stats = dict(engine.type_stats(w, VANGUARD), attack_range=0.0, role="Vanguard", ability_id=0)
        engine.register_unit_type(w, HOLD_FIRE_TYPE, stats)
        speed = stats["speed"]
        sx, sy = ORIGIN[0] + SEEKER_START[0], ORIGIN[1] + SEEKER_START[1]
        hx, hy = sx + placement.dx, sy + placement.dy
        sides = (
            [engine.spawn(w, HOLD_FIRE_TYPE, 0, px, py, SEEKER_LAYER)
             for px, py in place("blob", setting.force, sx, sy, 0.0, {"radius": BLOB_RADIUS})],
            [engine.spawn(w, HOLD_FIRE_TYPE, 1, px, py, placement.layer)
             for px, py in place("blob", HIDER_FORCE, hx, hy, 0.0, {"radius": BLOB_RADIUS})])
        monitor = invariants.watch(engine, w, *CANVAS)
        policies = (POLICIES[policy0], POLICIES[policy1])
        script = HIDER_SCRIPTS[placement.script]
        headings = (SEEKER_HEADING_DEG, placement.heading_deg)
        memory, last_cast, pings = ({}, {}), ({}, {}), ([], [])
        logs, revealed_now = ([], []), ({}, {})
        contact = None
        for tick in range(cap_ticks):
            if tick % DECIDE_EVERY == 0:
                pos = tuple({u: engine.unit_pos(w, u) for u in ids if engine.unit_alive(w, u)} for ids in sides)
                centres = tuple(_centre(list(p.values())) for p in pos)
                layers = tuple(engine.unit_layer(w, next(iter(p))) for p in pos)
                for s in (0, 1):
                    if s == 1:
                        for order in script(tick, centres[1], headings[1], layers[1], speed):
                            if order[0] == "move":
                                _move_all(engine, w, sides[1], centres[1], order[1], order[2])
                            elif order[0] == "layer":
                                engine.set_layer(w, sides[1], order[1])
                    else:
                        _move_all(engine, w, sides[0], centres[0], centres[0][0] + GOAL_LEG, centres[0][1]) \
                            if tick == 0 else None
                    ready = sorted(u for u in pos[s] if u not in last_cast[s]
                                   or tick - last_cast[s][u] >= setting.cooldown_ticks)
                    view = PolicyView(tick, setting, centres[s], headings[s], layers[s], ready, pos[s],
                                      dict(revealed_now[s]), memory[s])
                    for caster, layer, x, y in policies[s](view):
                        if engine.ping(w, caster, layer, x, y) != 0:
                            continue
                        last_cast[s][caster] = tick
                        caught = sum(1 for e, (ex, ey) in pos[1 - s].items()
                                     if engine.unit_layer(w, e) == layer and math.hypot(ex - x, ey - y) <= setting.radius)
                        pings[s].append((tick, caught))
            engine.step(w)
            monitor.after_step()
            now = tick + 1
            sight = tuple(engine.seen_by_sight(w, s, sides[1 - s]) for s in (0, 1))
            for s in (0, 1):
                vis = engine.visible_enemies(w, s, sides[1 - s])
                by_ping = vis - sight[s]
                if by_ping:
                    logs[s].append((now, by_ping))
                revealed_now[s].clear()
                for e in vis:
                    ex, ey = engine.unit_pos(w, e)
                    revealed_now[s][e] = (ex, ey, engine.unit_layer(w, e))
            if sight[0] or sight[1]:
                contact = now
                break
        heads = (HIDER_FORCE, setting.force)
        return SearchResult(tuple(summarise_side(logs[s], contact, cap_ticks, heads[s], pings[s]) for s in (0, 1)),
                            contact, "contact" if contact is not None else "cap", **monitor.verdict())
    finally:
        engine.free_world(w)
