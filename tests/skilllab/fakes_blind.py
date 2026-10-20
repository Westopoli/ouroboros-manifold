"""Helpers for the LAB-REV2-FIX round 3 tests (decision 44, blind naive-defender posts): an exact sight-line oracle written from the words of
R-098-02 (a blocked 100 wu cell on the lower layer of the pair crosses the segment; the cells holding the two ends are exempt), and the
cell search of the shift written as an exhaustive scan. No engine, nothing imported from the builder."""
import math
from fractions import Fraction

from scripts.skilllab import formations
from scripts.skilllab.contract import Block, Group, Setup, Terrain

SIGHT = 100                 # R-098-02: the cell of the blocked-cell sight test (OM_NAVMESH_CELL_SIZE)
ROUTE = 50                  # decision 7 / 20: the route grid a post moves on
GUARD_RADIUS = 200.0        # decision 43 item 6, DRAFT


def blocked_sight_cells(terrain, layer):
    """The 100 wu cells a Block turns blocked on `layer`: every cell the Block touches (lower bound floored, upper bound ceiled and
    one taken off), on each layer layer_lo..layer_hi (om_map_block_rect)."""
    out = set()
    for b in terrain.blocks:
        if not b.layer_lo <= layer <= b.layer_hi:
            continue
        lo_x, lo_y = max(b.x0, 0.0), max(b.y0, 0.0)
        hi_x, hi_y = min(b.x1, terrain.canvas[0]), min(b.y1, terrain.canvas[1])
        for cx in range(int(lo_x // SIGHT), math.ceil(hi_x / SIGHT)):
            for cy in range(int(lo_y // SIGHT), math.ceil(hi_y / SIGHT)):
                out.add((cx, cy))
    return out


def _overlap(a, b, cell, closed):
    """Does the segment a-b have positive length inside the cell [cx*100, (cx+1)*100) squared (closed: touching counts)?  Liang-Barsky on
    exact fractions; a segment parallel to an axis and lying ON a cell's boundary line belongs to the cell above or to the right
    (half-open), as the engine reads it."""
    ax, ay, bx, by = (Fraction(v) for v in (*a, *b))
    x0, y0 = Fraction(cell[0] * SIGHT), Fraction(cell[1] * SIGHT)
    box = ((x0, x0 + SIGHT), (y0, y0 + SIGHT))
    t0, t1 = Fraction(0), Fraction(1)
    for p, d, (lo, hi) in ((ax, bx - ax, box[0]), (ay, by - ay, box[1])):
        if d == 0:
            if not (lo <= p <= hi if closed else lo <= p < hi):
                return False
            continue
        s, e = sorted(((lo - p) / d, (hi - p) / d))
        t0, t1 = max(t0, s), min(t1, e)
    return t1 >= t0 if closed else t1 > t0


def clear(terrain, a, la, b, lb, closed=False):
    """True when no blocked cell of the lower layer of the pair crosses the segment, the cells holding its two ends exempt."""
    exempt = {(int(a[0] // SIGHT), int(a[1] // SIGHT)), (int(b[0] // SIGHT), int(b[1] // SIGHT))}
    cells = blocked_sight_cells(terrain, min(la, lb)) - exempt
    return not any(_overlap(a, b, c, closed) for c in cells)


def nearest(starts, p):
    return min(starts, key=lambda s: math.hypot(s[0] - p[0], s[1] - p[1]))


def blind(terrain, layer, post, starts, closed=False):
    """No clear sightline between the post and the nearest start point; range ignored."""
    if not starts:
        return False
    s = nearest(starts, post)
    return not clear(terrain, post, layer, (s[0], s[1]), s[2], closed)


def route_cells(terrain, layer):
    cols, rows = math.ceil(terrain.canvas[0] / ROUTE), math.ceil(terrain.canvas[1] / ROUTE)
    open_ = lambda i, j: not any(b.layer_lo <= layer <= b.layer_hi and b.x0 <= (i + .5) * ROUTE <= b.x1 and b.y0 <= (j + .5) * ROUTE <= b.y1
                                 for b in terrain.blocks)
    return cols, rows, open_


def region(terrain, layer, post):
    """The route cells connected over open cells to the cell of the post (the post's own cell is open in every fixture here)."""
    cols, rows, open_ = route_cells(terrain, layer)
    start = (int(post[0] // ROUTE), int(post[1] // ROUTE))
    assert open_(*start), "fixture: the post stands in a blocked route cell"
    seen, todo = {start}, [start]
    while todo:
        i, j = todo.pop()
        for n in ((i + 1, j), (i - 1, j), (i, j + 1), (i, j - 1)):
            if 0 <= n[0] < cols and 0 <= n[1] < rows and n not in seen and open_(*n):
                seen.add(n)
                todo.append(n)
    return seen


def candidates(terrain, layer, post, starts, radius=GUARD_RADIUS, closed=False):
    """The free, sighted route-cell centres of the post's region within `radius` of the post, nearest first, as (distance, centre)."""
    out = []
    for i, j in region(terrain, layer, post):
        c = ((i + .5) * ROUTE, (j + .5) * ROUTE)
        d = math.hypot(c[0] - post[0], c[1] - post[1])
        if d <= radius and not blind(terrain, layer, c, starts, closed):
            out.append((d, c))
    return sorted(out)


def expected_shift(terrain, layer, post, starts, radius=GUARD_RADIUS):
    """(centre, distance) of the nearest free sighted cell of the post's region within the radius; None when there is none. The answer must
    not depend on how a segment that only touches a cell corner is read: both readings of the oracle are computed and must agree."""
    got = [candidates(terrain, layer, post, starts, radius, closed) for closed in (False, True)]
    assert [g[:1] for g in got][0] == [g[:1] for g in got][1], "fixture reads differently when a corner touch blocks: pick another post"
    return None if not got[0] else (got[0][0][1], got[0][0][0])


def ties(terrain, layer, post, starts, radius=GUARD_RADIUS):
    """Every candidate centre at the least distance."""
    c = candidates(terrain, layer, post, starts, radius)
    return [p for d, p in c if c and d == c[0][0]]


# ---- fixtures -----------------------------------------------------------------------------------------------------------------------

CANVAS = (2000.0, 2000.0)
TYPES = {"Vanguard": {"base": "Vanguard", "movement": "flying"}, "Raider": {"base": "Raider", "movement": "flying"}}


def terrain(*blocks, canvas=CANVAS):
    return Terrain(canvas=canvas, blocks=tuple(blocks))


def blob(side, unit, count, x, y, layer=0, order="guard", facing=0.0):
    return Group(side=side, unit=unit, count=count, formation="blob", x=x, y=y, facing_deg=facing, layer=layer, order=order,
                 params={"radius": 80 + 12 * math.sqrt(count)})


def starts_of(setup, side=1):
    """The placed unit positions of `side` with their layers: the start points of the opposing side."""
    return [(x, y, g.layer) for g in setup.groups if g.side == side for x, y in formations.place(g.formation, g.count, g.x, g.y, g.facing_deg, g.params)]


def base_build(groups, blocks, canvas=CANVAS, enemy_at=None):
    """A stand-in for scenes.placed_scene's return: build(enemy_heads, swap) -> the Setup of `groups` on a hand-built terrain; the types
    are given so the pre-flight needs no engine (flyers, one layer). With `enemy_at` (x, y) the side-1 group is a blob of enemy_heads
    attack-moving units there (the sweep's headcount scan); else `groups` holds the whole scene."""
    def build(enemy_heads, swap):
        build.labels["prefight"] = "ok"
        scene = tuple(groups) + (() if enemy_at is None else (blob(1, "Vanguard", enemy_heads, *enemy_at, order="attack_move", facing=180.0),))
        return Setup(groups=scene, unit_types={k: dict(v) for k, v in TYPES.items()}, terrain=Terrain(canvas=canvas, blocks=tuple(blocks)),
                     point=(1000.0, 1000.0))
    build.labels = {"placement_shift": 0.0, "prefight": None}
    return build


# The wall of the main fixture: x 1000..1100 (one sight cell wide), y 600..1400, the enemy one unit at (1700, 1000) on the far side.
WALL = Block(1000.0, 600.0, 1100.0, 1400.0)
ENEMY_AT = (1700.0, 1000.0)
ENEMY = blob(1, "Vanguard", 1, *ENEMY_AT, order="attack_move", facing=180.0)
