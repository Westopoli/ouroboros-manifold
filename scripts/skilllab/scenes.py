"""Hand-built scenes in canvas coordinates."""
import collections
import dataclasses
import functools
import math
from fractions import Fraction

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
BEHIND_COVER = 150.0     # DRAFT-behind-cover, provisional (2026-10-07): short-reach types stand this far in front of the long-reach ones
AMBUSH_BEHIND = 200.0    # DRAFT-ambush-behind, provisional (2026-10-07): the ambush group stands this far behind the bait group, as plays_space
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


def naive_mix(naive_build, play):
    """The play-less naive scene (one Vanguard blob each side) with both sides fielding the play's own roster (rev 3 plan T4, D4,
    FINDING-lab-d4) on the play's own layer pair (rev 3 plan R2): per side, one blob per (unit name, layer) of the play's groups at the
    position the naive scene gave that side, side 0 the play's side 0 counts, side 1 the play's side 1 counts at that headcount. Orders
    and the empty timeline stay the naive scene's; the play's unit types come with the units."""
    def wrapped(enemy_heads, swap):
        setup = naive_build(enemy_heads, swap)
        mix = plays_space.scan_build(play)(None, enemy_heads, False)
        groups = []
        for side in (0, 1):
            anchor = next(g for g in setup.groups if g.side == side)
            counts = {}
            for g in mix.groups:
                if g.side == side:
                    counts[(g.unit, g.layer)] = counts.get((g.unit, g.layer), 0) + g.count
            groups += [dataclasses.replace(anchor, unit=u, count=n, layer=layer, formation="blob", params={"radius": 80 + 12 * math.sqrt(n)})
                       for (u, layer), n in counts.items()]
        skipped = tuple(skip_blocked(g, setup.terrain) for g in groups)
        point = setup.point if skipped == tuple(groups) else _placed_mean([g for g in skipped if g.side == 1])
        out = dataclasses.replace(setup, groups=skipped, unit_types=dict(mix.unit_types), settings=dict(mix.settings), point=point)
        wrapped.labels["prefight"] = preflight(out, None)
        return out
    wrapped.labels = {"placement_shift": 0.0, "prefight": None}
    return wrapped


ROUTE_CELL = 50.0        # decision 7 (2026-10-14): wu of the lab-side breadth-first search grid; a cell is open when its centre is
TERRAIN_CELL = 100.0     # OM_TERRAIN_CELL_WU (csrc/om_internal.h): the cell of the generated field's walk mask
SIGHT_CELL = 100.0       # R-098-02's blocked-cell size (OM_NAVMESH_CELL_SIZE)
GUARD_RADIUS = 200.0     # DRAFT (decision 44): how far a blind naive-defender post may move to a cell that sees the attackers' start
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


def _fill_cells(n, x, y, radius):
    """formations._blob's fill order (anchor first when n is odd, then each pair) continued without end: i = pairs, pairs + 1, ...
    Decision 36. See also: formations._blob. n >= 2."""
    pairs = n // 2
    if n % 2:
        yield float(x), float(y)
    i = 0
    while True:
        d = radius * math.sqrt((i + 0.5) / pairs)
        a = i * formations._GOLDEN_ANGLE
        dx, dy = round(d * math.cos(a), 6), round(d * math.sin(a), 6)
        yield float(x + dx), float(y + dy)
        yield float(x - dx), float(y - dy)
        i += 1


def _route_region(terrain, layer, x, y):
    """(cells, cell_of, start): the 50 wu route cells connected over open cells (centre in no block reaching `layer`) to the cell of
    (x, y), or to the nearest open cell when that one is blocked (decision 38); start is None when no cell is open."""
    cols, rows = math.ceil(terrain.canvas[0] / ROUTE_CELL), math.ceil(terrain.canvas[1] / ROUTE_CELL)

    def cell_of(px, py):
        return min(max(int(px // ROUTE_CELL), 0), cols - 1), min(max(int(py // ROUTE_CELL), 0), rows - 1)

    def centre(c):
        return (c[0] + 0.5) * ROUTE_CELL, (c[1] + 0.5) * ROUTE_CELL

    def open_cell(c):
        cx, cy = centre(c)
        return not any(_in_block(b, layer, cx, cy) for b in terrain.blocks)

    start = cell_of(x, y)
    if not open_cell(start):
        near = [(math.hypot(centre((i, j))[0] - x, centre((i, j))[1] - y), i, j)
                for i in range(cols) for j in range(rows) if open_cell((i, j))]
        if not near:
            return set(), cell_of, None
        start = min(near)[1:]
    seen, queue = {start}, collections.deque([start])
    while queue:
        cx, cy = queue.popleft()
        for n in ((cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1)):
            if 0 <= n[0] < cols and 0 <= n[1] < rows and n not in seen and open_cell(n):
                seen.add(n)
                queue.append(n)
    return seen, cell_of, start


def skip_blocked(g, terrain):
    """A naive blob whose next cell is blocked takes the next free cell of its fill order (decisions 26, 36, 38): a point inside the
    canvas, in no block reaching the group's layer, whose route cell is open and in the anchor's connected region. A blob of one unit
    that cannot stand on its anchor takes the centre of the nearest open cell. A region that cannot hold the count leaves the
    open-ground placement, which the pre-flight then reads as no_fit."""
    if g.formation != "blob" or terrain is None or g.count < 1:
        return g
    width, height = terrain.canvas
    inside = lambda p: 0.0 <= p[0] <= width and 0.0 <= p[1] <= height
    if not terrain.blocks and all(inside(p) for p in _placed(g)):
        return g
    seen, cell_of, start = _route_region(terrain, g.layer, g.x, g.y)
    free = lambda p: (inside(p) and cell_of(*p) in seen and not any(_in_block(b, g.layer, p[0], p[1]) for b in terrain.blocks))
    if g.count == 1:
        if free((g.x, g.y)) or start is None:
            return g
        return dataclasses.replace(g, formation="points", params={"points": [((start[0] + 0.5) * ROUTE_CELL, (start[1] + 0.5) * ROUTE_CELL)]})
    reach = math.hypot(width, height) + 1.0
    points = []
    for p in _fill_cells(g.count, g.x, g.y, g.params["radius"]):
        if math.hypot(p[0] - g.x, p[1] - g.y) > reach:
            return g
        if free(p):
            points.append(p)
            if len(points) == g.count:
                break
    if points == _placed(g):
        return g
    return dataclasses.replace(g, formation="points", params={"points": points})


@functools.lru_cache(maxsize=256)
def _blocked_sight_cells(blocks, canvas, layer):
    """The 100 wu cells the blocks turn blocked on `layer`: every cell a block touches (low bound floored, high bound ceiled and one
    taken off, as om_map_block_rect), clipped to the canvas, on the block's layers layer_lo..layer_hi."""
    out = set()
    for b in blocks:
        if not b.layer_lo <= layer <= b.layer_hi:
            continue
        lo_x, lo_y = max(b.x0, 0.0), max(b.y0, 0.0)
        hi_x, hi_y = min(b.x1, canvas[0]), min(b.y1, canvas[1])
        for cx in range(int(lo_x // SIGHT_CELL), math.ceil(hi_x / SIGHT_CELL)):
            for cy in range(int(lo_y // SIGHT_CELL), math.ceil(hi_y / SIGHT_CELL)):
                out.add((cx, cy))
    return out


def _crosses(a, b, cell):
    """Does the segment a-b have positive length inside the half-open cell [cx*100, (cx+1)*100) squared? Exact on fractions, so a
    segment that only touches a corner does not cross and one lying on a boundary line belongs to the cell above or to the right."""
    ax, ay, bx, by = (Fraction(v) for v in (*a, *b))
    x0, y0 = Fraction(cell[0] * SIGHT_CELL), Fraction(cell[1] * SIGHT_CELL)
    t0, t1 = Fraction(0), Fraction(1)
    for p, d, lo in ((ax, bx - ax, x0), (ay, by - ay, y0)):
        hi = lo + Fraction(SIGHT_CELL)
        if d == 0:
            if not lo <= p < hi:
                return False
            continue
        s, e = sorted(((lo - p) / d, (hi - p) / d))
        t0, t1 = max(t0, s), min(t1, e)
    return t1 > t0


def sight_clear(terrain, a, la, b, lb):
    """True when no blocked 100 wu cell crosses the segment a-b (R-098-02, range ignored; decision 44). The cell tested for a pair is the
    one on the lower layer of the pair (csrc/fog.c om_fog_grid_blocks); the cells holding the two ends are exempt. Terrain None: clear."""
    if terrain is None or not terrain.blocks:
        return True
    cells = _blocked_sight_cells(terrain.blocks, terrain.canvas, min(la, lb))
    if not cells:
        return True
    ends = {(int(p[0] // SIGHT_CELL), int(p[1] // SIGHT_CELL)) for p in (a, b)}
    lo_c = (int(min(a[0], b[0]) // SIGHT_CELL), int(min(a[1], b[1]) // SIGHT_CELL))
    hi_c = (int(max(a[0], b[0]) // SIGHT_CELL), int(max(a[1], b[1]) // SIGHT_CELL))
    box = [(i, j) for i in range(lo_c[0], hi_c[0] + 1) for j in range(lo_c[1], hi_c[1] + 1)] if (
        (hi_c[0] - lo_c[0] + 1) * (hi_c[1] - lo_c[1] + 1) < len(cells)) else [c for c in cells if lo_c[0] <= c[0] <= hi_c[0] and lo_c[1] <= c[1] <= hi_c[1]]
    return not any(c in cells and c not in ends and _crosses(a, b, c) for c in box)


def blind_post(terrain, layer, post, starts):
    """True iff there is a start and no clear sightline runs from `post` to the start nearest it (Euclid; decision 44). `starts`:
    (x, y, layer) of the placed units of the opposing side."""
    starts = list(starts)
    if not starts:
        return False
    s = min(starts, key=lambda p: math.hypot(p[0] - post[0], p[1] - post[1]))
    return not sight_clear(terrain, post, layer, (s[0], s[1]), s[2])


def shifted_post(terrain, layer, post, starts, radius=GUARD_RADIUS):
    """`post` itself when it is not blind, else the centre of the nearest free route cell of the post's region, within `radius`
    (inclusive), from which the nearest start is seen: ties by angle from the post. None when there is none (decision 44)."""
    if not blind_post(terrain, layer, post, starts):
        return tuple(post)
    seen, _cell_of, _start = _route_region(terrain, layer, post[0], post[1])
    reach = int(radius // ROUTE_CELL) + 2
    ci, cj = int(post[0] // ROUTE_CELL), int(post[1] // ROUTE_CELL)
    found = []
    for i in range(ci - reach, ci + reach + 1):
        for j in range(cj - reach, cj + reach + 1):
            if (i, j) not in seen:
                continue
            c = ((i + 0.5) * ROUTE_CELL, (j + 0.5) * ROUTE_CELL)
            d = math.hypot(c[0] - post[0], c[1] - post[1])
            if d <= radius:
                found.append((d, math.atan2(c[1] - post[1], c[0] - post[0]) % (2 * math.pi), c))
    for _d, _angle, c in sorted(found):
        if not blind_post(terrain, layer, c, starts):
            return c
    return None


def _no_fit(setup, engine):
    """A placed unit stands inside a block on its layer, or a walking mover stands on ground a generated field says is not walkable
    (decision 20; a flyer and a guard are checked against blocks only; no shifting, ruling 6)."""
    t = setup.terrain
    if t is None:
        return False
    if any(_in_block(b, g.layer, x, y) for g in setup.groups for x, y in _placed(g) for b in t.blocks):
        return True
    if t.field_seed is None:
        return False
    movers = [g for g in setup.groups if g.order in _MOVING]
    walking = _walking_names(setup, engine, movers) if movers else set()
    walkers = [g for g in movers if g.unit in walking]
    if not walkers:
        return False
    engine = _lazy_engine(engine)
    w = engine.new_world(0)
    try:
        engine.set_canvas(w, t.canvas[0], t.canvas[1])
        engine.terrain_generate(w, t.field_seed, t.canvas[0])
        return any(not engine.terrain_walkable_at(w, x, y) for g in walkers for x, y in _placed(g))
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


def _walking_names(setup, engine, groups):
    """Unit names among `groups` that walk: the play's own "movement" key, else the engine's reading (an unset type reads flying)."""
    names = {g.unit for g in groups}
    walking = {n for n in names if setup.unit_types.get(n, {}).get("movement") == "walking"}
    builtin = sorted(n for n in names if n not in setup.unit_types)
    if builtin:
        engine = _lazy_engine(engine)
        w = engine.new_world(0)
        try:
            walking |= {n for n in builtin if engine.movement_kind(w, engine.type_id(n)) == 1}
        finally:
            engine.free_world(w)
    return walking


def _unroutable(setup, engine):
    """Some moving group has no path of open 50 wu cells from its placed positions to its target on its own layer. Every mover is routed
    the same way; only the mask differs: a flyer's open cells are those no block reaching its layer covers, a walker's also need walkable ground."""
    t = setup.terrain
    if t is None:
        return False
    cols, rows = math.ceil(t.canvas[0] / ROUTE_CELL), math.ceil(t.canvas[1] / ROUTE_CELL)
    anchors = timeline.first_anchors(setup)
    movers = [g for g in setup.groups if g.order in _MOVING]
    # See also: tests/skilllab/test_scenes_preflight_flyer.py, ground/test_slope_top_variants.py (s1_slope_top_flyer).
    walking = _walking_names(setup, engine, movers) if movers else set()
    walk_layers = sorted({g.layer for g in movers if g.unit in walking})
    masks = _field_masks(_lazy_engine(engine), setup, walk_layers) if walk_layers and t.field_seed is not None else {}

    def cell(x, y):
        return min(max(int(x // ROUTE_CELL), 0), cols - 1), min(max(int(y // ROUTE_CELL), 0), rows - 1)

    def open_cell(layer, walks, c):
        x, y = (c[0] + 0.5) * ROUTE_CELL, (c[1] + 0.5) * ROUTE_CELL
        if any(_in_block(b, layer, x, y) for b in t.blocks):
            return False
        if walks and layer in masks:
            width, mask = masks[layer]
            return bool(mask[int(y // TERRAIN_CELL) * width + int(x // TERRAIN_CELL)])
        return True

    reached = {}
    for g in movers:
        walks = g.unit in walking
        target = g.goal if g.goal is not None else setup.point if setup.point is not None else anchors[1 - g.side]
        key = (g.layer, walks, cell(*target))
        if key not in reached:
            seen, queue = {key[2]}, collections.deque([key[2]])
            while queue:
                cx, cy = queue.popleft()
                for n in ((cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1)):
                    if 0 <= n[0] < cols and 0 <= n[1] < rows and n not in seen and open_cell(g.layer, walks, n):
                        seen.add(n)
                        queue.append(n)
            reached[key] = seen
        seen = reached[key]
        for x, y in formations.place(g.formation, g.count, g.x, g.y, g.facing_deg, g.params):
            c = cell(x, y)
            if c not in seen and not any(n in seen for n in ((c[0] + 1, c[1]), (c[0] - 1, c[1]), (c[0], c[1] + 1), (c[0], c[1] - 1))):
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


def _blind_holder(setup):
    """Some side-0 group on guard has an anchor from which the nearest placed unit of side 1 is not seen (decision 44)."""
    starts = [(x, y, g.layer) for g in setup.groups if g.side == 1 for x, y in _placed(g)]
    return any(blind_post(setup.terrain, g.layer, (g.x, g.y), starts) for g in setup.groups if g.side == 0 and g.order == "guard")


def preflight(setup, engine, naive_defender=False):
    """"ok", or the first refusal in the order no_fit, unroutable, no_reach, blind_post (decisions 7 and 44). Runs no tick, moves nothing.
    no_fit: a placed point inside a blocked cell, or a walking mover on ground a generated field says is not walkable. unroutable:
    a moving group cannot reach its target over the open cells of its layer, a flyer's open cells being those no block reaching its
    layer covers and a walker's also the walkable ground. no_reach: no type facing a holder (a group on guard) reaches the holder's
    layer; a meeting has no holder. blind_post, asked for with naive_defender=True only: a side-0 guard group's anchor sees no
    clear line to the nearest unit of side 1. The engine is needed only for a reach read, a generated field or a unit type's
    movement and is built when None."""
    if _no_fit(setup, engine):
        return "no_fit"
    if _unroutable(setup, engine):
        return "unroutable"
    if _no_reach(setup, engine):
        return "no_reach"
    if naive_defender and setup.terrain is not None and _blind_holder(setup):
        return "blind_post"
    return "ok"


def placed_scene(layout, play, start_distance, features, counter=False):
    """build(enemy_heads, swap) for `play` placed on `layout` (Rev 4): the defender stands already in shape at its anchor on guard,
    the attacker `start_distance` from the choke on the other side attack-moves at it. Side 0 is the skilled, counter or naive side;
    the defender is side 0 for a defender play and side 1 for an attacker play. `counter` uses a play as the counter it is
    (plays_space.COUNTER_USE). Setup.point is the defender's centre of mass (ruling 6). Nothing is shifted to fit (Q-LAB-03):
    build.labels['prefight'] is scenes.preflight of the built Setup, and build.labels['placement_shift'] stays 0.0 (the naive defender's
    blind-post shift is sweep._naive_side's, on its own build)."""
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
        point = (hold[0] + tx, hold[1] + ty)
        if play == "naive":
            skipped = tuple(skip_blocked(g, terrain) for g in final)
            if skipped != final:
                final, point = skipped, _placed_mean([g for g in skipped if g.side == ds])
        enemy_anchor = next((g.x, g.y) for g in final if g.side == 1)

        def step_goal(t):
            if t.goal is None:
                return None
            if t.order == "ping":
                return enemy_anchor
            return (placed[t.group].x + s * abs(t.goal[0] - groups[t.group].x) + tx, placed[t.group].y + t.goal[1] - groups[t.group].y + ty)
        steps = tuple(dataclasses.replace(t, when=("seen",) if play == "s4_bait" else t.when, goal=step_goal(t)) for t in steps_in)
        setup = Setup(groups=final, unit_types=dict(unit_types), settings=dict(settings), timeline=steps, terrain=terrain,
                      point=point)
        build.labels["prefight"] = preflight(setup, None)
        return setup
    build.labels = {"placement_shift": 0.0, "prefight": None}
    return build
