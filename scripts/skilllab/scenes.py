"""Hand-built scenes in canvas coordinates."""
import collections
import dataclasses
import math

from scripts.skilllab import formations, maps, plays, plays_space, timeline
from scripts.skilllab.contract import Block, Group, Setup, Terrain
from scripts.skilllab.terrain import shift_terrain

_CANVAS = (3000.0, 1600.0)
_WALL = (1500, 1600)
_GAP = (700, 900)


def phase_b_choke(defenders=8):
    """The Phase B choke: a wall with a gap, defenders in a line behind it, attackers in a blob in front."""
    def build(enemy_heads, swap):
        if defenders < 1 or enemy_heads < 1:
            raise ValueError("defenders and enemy_heads must be >= 1")
        terrain = Terrain(canvas=_CANVAS, blocks=(Block(_WALL[0], 0, _WALL[1], _GAP[0], 0, 4),
                                                  Block(_WALL[0], _GAP[1], _WALL[1], _CANVAS[1], 0, 4)))
        return Setup(groups=(
            Group(side=0, unit="Vanguard", count=defenders, formation="line", x=1700.0, y=800.0, facing_deg=180.0,
                  layer=0, order="attack_move", params={"spacing": 30}),
            Group(side=1, unit="Vanguard", count=enemy_heads, formation="blob", x=800.0, y=800.0, facing_deg=0.0,
                  layer=0, order="attack_move", params={"radius": 80 + 12 * math.sqrt(enemy_heads)})),
            unit_types={}, terrain=terrain, point=((_WALL[0] + _WALL[1]) / 2, (_GAP[0] + _GAP[1]) / 2))
    build.labels = {"play_side0": "defenders line", "play_side1": "attackers blob",
                    "status_side0": "naive", "status_side1": "naive"}
    return build


def _placed_mean(groups):
    """The mean of the placed unit positions of `groups` (the centre of mass of a holder, ruling 6)."""
    pts = [p for g in groups for p in formations.place(g.formation, g.count, g.x, g.y, g.facing_deg, g.params)]
    return sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts)


def guard_defenders(build):
    """Side 1 of the built setup holds the guard order (R-096-08); the attacker's point is the guards' placed mean (ruling 6)."""
    def wrapped(enemy_heads, swap):
        setup = build(enemy_heads, swap)
        groups = tuple(dataclasses.replace(g, order="guard") if g.side == 1 else g for g in setup.groups)
        guards = [g for g in groups if g.order == "guard"]
        return dataclasses.replace(setup, groups=groups, point=_placed_mean(guards) if guards else setup.point)
    return wrapped


def objective_scene(start_distance, unit="Vanguard", size=16):
    """Both groups start start_distance apart and attack-move to a point midway between them (a meeting, ruling 6)."""
    def build(enemy_heads, swap):
        if size < 1 or enemy_heads < 1:
            raise ValueError("size and enemy_heads must be >= 1")
        objective = (0.0, 0.0)
        groups = tuple(
            Group(side=side, unit=unit, count=count, formation="blob", x=x, y=0.0, facing_deg=facing, layer=0,
                  order="attack_move", goal=objective, params={"radius": 80 + 12 * math.sqrt(count)})
            for side, count, x, facing in ((0, size, -start_distance / 2, 0.0), (1, enemy_heads, start_distance / 2, 180.0)))
        return Setup(groups=groups, unit_types={}, point=objective, max_ticks=plays.max_ticks_for(size, enemy_heads))
    return build


# Placed scenes (spec docs/northstar/plans/2026-10-06-layout-search-spec.md Rev 3 and Rev 4)
BEHIND_COVER = 150.0     # provisional (2026-10-07): short-reach types stand this far in front of the long-reach ones
AMBUSH_BEHIND = 200.0    # provisional (2026-10-07): the ambush group stands this far behind the bait group, as plays_space
NAIVE_PLAYS = ("naive", "naive_line")
_NAIVE_ANCHORS = plays_space.Anchors("attacker", "choke_mouth", "blob")


def _walls_and_lanes(layout):
    thick = maps.LAYOUT_WALL_THICK
    walls = sorted((b for b in layout.blocks if abs((b.x1 - b.x0) - thick) < 1e-6), key=lambda b: b.y0)
    lanes = [b for b in layout.blocks if abs((b.x1 - b.x0) - thick) >= 1e-6]
    return walls, lanes


def _resolve(layout, features):
    """The layout's choke centre, wall thickness, lane x range (or None) and covers, in layout coordinates."""
    walls, lanes = _walls_and_lanes(layout)
    if features.choke_width_bodies and len(walls) >= 2:
        a, b = walls[:2]
        centre, thick = ((a.x0 + a.x1) / 2, (a.y1 + b.y0) / 2), maps.LAYOUT_WALL_THICK
    else:
        centre, thick = (0.0, 0.0), 0.0
    lane_x = (min(b.x0 for b in lanes), max(b.x1 for b in lanes)) if features.lane_count and lanes else None
    return centre, thick, lane_x, layout.covers


def _anchor_points(kind, s, centre, thick, lane_x, covers, reach):
    """(mouth, anchor): the choke mouth on the defender's side and the defender's anchor for this kind, layout coordinates."""
    mouth = (centre[0] + s * thick / 2, centre[1])
    if kind == "reach_beyond_exit":
        return mouth, (mouth[0] + s * reach * plays_space.OUTRANGE_FACTOR, mouth[1])
    if kind == "exit_line":
        return mouth, (mouth[0] + s * reach, mouth[1])
    if kind == "lane_mouth":
        return mouth, mouth if lane_x is None else ((lane_x[0] if s < 0 else lane_x[1]), centre[1])
    if kind == "far_side":
        return mouth, (centre[0] + s * plays_space.FRAIL_BACK, centre[1])
    if kind == "behind_cover":
        if not covers:
            return mouth, (mouth[0] + s * BEHIND_COVER / 2, mouth[1])
        c = min(covers, key=lambda c: math.dist((c.x, c.y), mouth))
        return mouth, (c.x + s * c.radius, c.y)
    return mouth, mouth


def _defender_positions(kind, n_groups, mouth, anchor, s):
    """One (x, y) per defender group, in group order."""
    if kind == "exit_screen":
        return [(mouth[0] - s * plays_space.SCREEN_AHEAD, mouth[1]), (mouth[0] + s * plays_space.SCREEN_BEHIND, mouth[1])]
    if kind == "behind_cover":
        return [anchor, (anchor[0] - s * BEHIND_COVER, anchor[1])]
    if kind == "lane_mouth":
        return [anchor, (anchor[0] + s * AMBUSH_BEHIND, anchor[1])][:n_groups]
    if kind == "far_side":
        return [mouth, anchor]
    return [anchor] * n_groups


def _blob_group(side, unit, count, x, y, facing, order):
    return Group(side=side, unit=unit, count=count, formation="blob", x=x, y=y, facing_deg=facing, layer=0, order=order,
                 params={"radius": 80 + 12 * math.sqrt(count)})


def _naive_defender(play, heads):
    if play == "naive":
        return _blob_group(1, "Vanguard", heads, 0.0, 0.0, 180.0, "guard")
    return Group(side=1, unit="Vanguard", count=heads, formation="line", x=0.0, y=0.0, facing_deg=180.0, layer=0, order="guard",
                 params={"spacing": plays_space.SPREAD_SPACING})


def _groups_and_timeline(play, anchors, heads, swap):
    """The play's groups and timeline before placement, defender groups first for a defender play."""
    if play in NAIVE_PLAYS:
        return (_blob_group(0, "Vanguard", plays_space.UNITS, 0.0, 0.0, 0.0, "attack_move"), _naive_defender(play, heads)), (), {}, {}
    setup = plays_space.scan_build(play)(None, heads, False)
    return setup.groups, setup.timeline, setup.unit_types, setup.settings


ROUTE_CELL = 50.0        # decision 7 (2026-10-14): wu of the lab-side breadth-first search grid; a cell is open when its centre is
TERRAIN_CELL = 100.0     # OM_TERRAIN_CELL_WU (csrc/om_internal.h): the cell of the generated field's walk mask
_MOVING = ("attack_move", "move", "group_move")


def _lazy_engine(engine):
    if engine is None:
        from scripts.skilllab.engine import Engine
        engine = Engine()
    return engine


def _in_block(b, layer, x, y):
    return b.layer_lo <= layer <= b.layer_hi and b.x0 <= x <= b.x1 and b.y0 <= y <= b.y1


def _placed(g):
    return formations.place(g.formation, g.count, g.x, g.y, g.facing_deg, g.params)


def _no_fit(setup, engine):
    """A placed unit stands inside a block on its layer, or on ground a generated field says is not walkable (no shifting, ruling 6)."""
    t = setup.terrain
    if t is None:
        return False
    if any(_in_block(b, g.layer, x, y) for g in setup.groups for x, y in _placed(g) for b in t.blocks):
        return True
    if t.field_seed is None:
        return False
    engine = _lazy_engine(engine)
    w = engine.new_world(0)
    try:
        engine.set_canvas(w, t.canvas[0], t.canvas[1])
        engine.terrain_generate(w, t.field_seed, t.canvas[0])
        return any(not engine.terrain_walkable_at(w, x, y) for g in setup.groups for x, y in _placed(g))
    finally:
        engine.free_world(w)


def _field_masks(engine, setup, layers):
    """{layer: walk mask bytes} of the generated field, or {} for a hand-built terrain."""
    t = setup.terrain
    if t.field_seed is None:
        return {}
    w = engine.new_world(0)
    try:
        engine.set_canvas(w, t.canvas[0], t.canvas[1])
        engine.terrain_generate(w, t.field_seed, t.canvas[0])
        cols, _rows, _bands = engine.terrain_dump_bands(w)
        return {layer: (cols, engine.terrain_walk_mask(w, layer)) for layer in layers}
    finally:
        engine.free_world(w)


def _walks(setup, g):
    return setup.unit_types.get(g.unit, {}).get("movement") == "walking"


def _blocked_on_line(t, layer, a, b):
    """The straight line from a to b crosses a 50 wu cell whose centre is in a block reaching `layer` (a flyer's own-layer route)."""
    n = max(1, int(math.dist(a, b) // (ROUTE_CELL / 2)))
    cells = {(int((a[0] + (b[0] - a[0]) * i / n) // ROUTE_CELL), int((a[1] + (b[1] - a[1]) * i / n) // ROUTE_CELL)) for i in range(n + 1)}
    return any(_in_block(blk, layer, (cx + 0.5) * ROUTE_CELL, (cy + 0.5) * ROUTE_CELL) for cx, cy in cells for blk in t.blocks)


def _unroutable(setup, engine):
    """Some moving group has no path of open 50 wu cells from its placed positions to its target on its own layer."""
    t = setup.terrain
    if t is None:
        return False
    cols, rows = math.ceil(t.canvas[0] / ROUTE_CELL), math.ceil(t.canvas[1] / ROUTE_CELL)
    anchors = timeline.first_anchors(setup)
    movers = [g for g in setup.groups if g.order in _MOVING]
    # See also: tests/skilllab/test_scenes_preflight_flyer.py, ground/test_slope_top_variants.py (s1_slope_top_flyer). Only a walker is
    # routed (breadth-first, over the ground's walk mask on a generated field); a flyer (unit type not "walking") needs no path on the
    # ground, so its placed mean is checked by a straight line over blocks on its own layer (Architect, 2026-10-19).
    flyers = [g for g in movers if not _walks(setup, g)]
    movers = [g for g in movers if g not in flyers]
    masks = _field_masks(_lazy_engine(engine), setup, sorted({g.layer for g in movers})) if movers and t.field_seed is not None else {}

    def cell(x, y):
        return min(max(int(x // ROUTE_CELL), 0), cols - 1), min(max(int(y // ROUTE_CELL), 0), rows - 1)

    def open_cell(layer, c):
        x, y = (c[0] + 0.5) * ROUTE_CELL, (c[1] + 0.5) * ROUTE_CELL
        if any(_in_block(b, layer, x, y) for b in t.blocks):
            return False
        if layer in masks:
            width, mask = masks[layer]
            return bool(mask[int(y // TERRAIN_CELL) * width + int(x // TERRAIN_CELL)])
        return True

    reached = {}
    for g in movers:
        target = g.goal if g.goal is not None else setup.point if setup.point is not None else anchors[1 - g.side]
        key = (g.layer, cell(*target))
        if key not in reached:
            seen, queue = {key[1]}, collections.deque([key[1]])
            while queue:
                cx, cy = queue.popleft()
                for n in ((cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1)):
                    if 0 <= n[0] < cols and 0 <= n[1] < rows and n not in seen and open_cell(g.layer, n):
                        seen.add(n)
                        queue.append(n)
            reached[key] = seen
        seen = reached[key]
        for x, y in formations.place(g.formation, g.count, g.x, g.y, g.facing_deg, g.params):
            c = cell(x, y)
            if c not in seen and not any(n in seen for n in ((c[0] + 1, c[1]), (c[0] - 1, c[1]), (c[0], c[1] + 1), (c[0], c[1] - 1))):
                return True
    for g in flyers:
        target = g.goal if g.goal is not None else setup.point if setup.point is not None else anchors[1 - g.side]
        if _blocked_on_line(t, g.layer, _placed_mean([g]), target):
            return True
    return False


def _no_reach(setup, engine):
    """Holders are the groups on guard. No type of the groups facing a holder reaches the holder's layer from its own layer."""
    holders = [g for g in setup.groups if g.order == "guard"]
    pairs = [(a, h) for h in holders for a in setup.groups if a.side != h.side and a.order != "guard"]
    if not pairs or any(a.layer == h.layer for a, h in pairs):
        return False
    engine = _lazy_engine(engine)
    from scripts.skilllab.fight import _register_types
    w = engine.new_world(0)
    try:
        types = _register_types(engine, w, setup)
        reach = {name: engine.profile_reach(w, tid) for name, (tid, _range) in types.items()}
    finally:
        engine.free_world(w)
    return not any(-reach[a.unit][1] <= h.layer - a.layer <= reach[a.unit][0] for a, h in pairs)


def preflight(setup, engine):
    """"ok", or the first refusal in the order no_fit, unroutable, no_reach (decision 7, 2026-10-14). Runs no tick, moves nothing.
    no_fit: a placed point inside a blocked cell. unroutable: a moving group cannot reach its target over the open cells of its
    layer (a flyer, a type not "walking", is checked by a straight line over the blocks of its layer instead). no_reach: no type facing a holder (a group
    on guard) reaches the holder's layer; a meeting has no holder. no_fit also covers a placed point on ground a generated field
    says is not walkable. The engine is needed only for a reach read or a generated field and is built when None."""
    if _no_fit(setup, engine):
        return "no_fit"
    if _unroutable(setup, engine):
        return "unroutable"
    if _no_reach(setup, engine):
        return "no_reach"
    return "ok"


def placed_scene(layout, play, start_distance, features, counter=False):
    """build(enemy_heads, swap) for `play` placed on `layout` (Rev 4): the defender stands already in shape at its anchor on guard,
    the attacker `start_distance` from the choke on the other side attack-moves at it. Side 0 is the skilled, counter or naive side;
    the defender is side 0 for a defender play and side 1 for an attacker play. `counter` uses a play as the counter it is
    (plays_space.COUNTER_USE). Setup.point is the defender's centre of mass (ruling 6). Nothing is shifted to fit (Q-LAB-03):
    build.labels['prefight'] is scenes.preflight of the built Setup, and build.labels['placement_shift'] stays 0.0."""
    if play in NAIVE_PLAYS:
        anchors = _NAIVE_ANCHORS
    else:
        anchors = plays_space.COUNTER_USE.get(play) if counter else None
        anchors = anchors or plays_space.PLAYS[play].anchors
    ds = 0 if anchors.role == "defender" else 1
    s = -1 if ds == 0 else 1
    centre, thick, lane_x, covers = _resolve(layout, features)
    reach = plays.unit_stats("Vanguard")["attack_range"]
    mouth, anchor = _anchor_points(anchors.defender, s, centre, thick, lane_x, covers, reach)
    face_d, face_a = (0.0, 180.0) if s < 0 else (180.0, 0.0)
    attack_x = centre[0] - s * start_distance
    tx = layout.canvas[0] / 2 + s * (start_distance - 500.0) / 2 - centre[0]
    ty = layout.canvas[1] / 2 - centre[1]
    terrain = shift_terrain(layout, tx, ty)

    def build(enemy_heads, swap):
        if enemy_heads < 1:
            raise ValueError("enemy_heads must be at least 1")
        groups, steps_in, unit_types, settings = _groups_and_timeline(play, anchors, enemy_heads, swap)
        is_def = [g.side == ds for g in groups]
        d_idx = [i for i, g in enumerate(groups) if g.side == ds]
        positions = _defender_positions(anchors.defender, len(d_idx), mouth, anchor, s)
        placed = list(groups)
        for i, (x, y) in zip(d_idx, positions):
            placed[i] = dataclasses.replace(groups[i], x=x, y=y, facing_deg=face_d, order="guard")
        end_y = 0.0
        if anchors.attacker == "mass_one_end":
            line = next(g for g in placed if g.side == ds)
            end_y = (line.count - 1) * plays_space.SPREAD_SPACING / 2
        for i, g in enumerate(groups):
            if is_def[i]:
                continue
            goal = None
            if anchors.attacker == "mass_one_end":
                goal = (placed[d_idx[0]].x, placed[d_idx[0]].y + end_y)
            placed[i] = dataclasses.replace(g, x=attack_x, y=centre[1] + end_y, facing_deg=face_a, goal=goal,
                                            order=g.order if anchors.attacker == "hold" else "attack_move")
        hold = _placed_mean([placed[i] for i in d_idx])
        final = tuple(dataclasses.replace(g, x=g.x + tx, y=g.y + ty, goal=None if g.goal is None else (g.goal[0] + tx, g.goal[1] + ty))
                      for g in placed)
        enemy_anchor = next((g.x, g.y) for g in final if g.side == 1)

        def step_goal(t):
            if t.goal is None:
                return None
            if t.order == "ping":
                return enemy_anchor
            return (placed[t.group].x + s * abs(t.goal[0] - groups[t.group].x) + tx, placed[t.group].y + t.goal[1] - groups[t.group].y + ty)
        steps = tuple(dataclasses.replace(t, when=("seen",) if play == "s4_bait" else t.when, goal=step_goal(t)) for t in steps_in)
        setup = Setup(groups=final, unit_types=dict(unit_types), settings=dict(settings), timeline=steps, terrain=terrain,
                      point=(hold[0] + tx, hold[1] + ty))
        build.labels["prefight"] = preflight(setup, None)
        return setup
    build.labels = {"placement_shift": 0.0, "prefight": None}
    return build
