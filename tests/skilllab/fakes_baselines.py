"""Helpers for the LAB-REV2-BASE tests (decisions 25 and 26): the fill order of a naive blob, blocked-cell reading, and a fake base
build for sweep.default_builds. No engine here."""
import math

from scripts.skilllab import formations
from scripts.skilllab.contract import Block, Group, Setup, Terrain

GOLDEN_ANGLE = 2.399963229728653     # formations._GOLDEN_ANGLE: the fill order of a blob is its Fermat spiral


def radius_of(count):
    """The blob radius every naive scene gives a blob of `count` units (scenes._blob_group, sweep._naive_side)."""
    return 80 + 12 * math.sqrt(count)


def positions(g):
    """Where fight() puts the units of a group: formations.place on the group's own fields (the seam every consumer uses)."""
    return formations.place(g.formation, g.count, g.x, g.y, g.facing_deg, g.params)


def in_block(blocks, layer, p):
    """A point stands in a blocked cell of its layer (the pre-flight no_fit reading: bounds inclusive)."""
    return any(b.layer_lo <= layer <= b.layer_hi and b.x0 <= p[0] <= b.x1 and b.y0 <= p[1] <= b.y1 for b in blocks)


def fill_order(n, x, y, radius):
    """The existing fill order of a blob of n units, CONTINUED past its last cell (decision 36 item 2: "the existing Fermat spiral
    continued without end, same pair count and radius formula, i = pairs, pairs + 1, ..."): the anchor first when n is odd, then the
    pairs (p_i, reflection of p_i) of formations._blob, with d_i = radius * sqrt((i + 0.5) / (n // 2)) and angle i * golden angle, for i
    = 0, 1, 2, ... without end. Positions rounded to 6 places as formations._blob rounds. A blob of ONE unit has no pairs to count
    (n // 2 = 0): the helper reads its continuation as the anchor, then a one-pair spiral (pairs 1); the tests use that only for "the
    anchor comes first" and check the cell after the anchor by properties, not by this sequence."""
    pairs = max(n // 2, 1)
    if n % 2:
        yield (float(x), float(y))
    i = 0
    while True:
        d = radius * math.sqrt((i + 0.5) / pairs)
        a = i * GOLDEN_ANGLE
        dx, dy = round(d * math.cos(a), 6), round(d * math.sin(a), 6)
        yield (float(x + dx), float(y + dy))
        yield (float(x - dx), float(y - dy))
        i += 1


ROUTE_CELL = 50.0      # decision 20 / scenes.ROUTE_CELL: wu of the breadth-first search grid; a cell is open when its CENTRE is in no block


def aligned(x0, y0, x1, y1, layer_lo=0, layer_hi=4):
    """A Block whose bounds are multiples of the 50 wu route cell (x0, y0 rounded down, x1, y1 up): every route cell is then wholly
    inside or wholly outside it, so "this point is in the anchor's region" reads the same at cell and at point resolution."""
    r = ROUTE_CELL
    return Block(math.floor(x0 / r) * r, math.floor(y0 / r) * r, math.ceil(x1 / r) * r, math.ceil(y1 / r) * r, layer_lo, layer_hi)


def _grid(terrain):
    return math.ceil(terrain.canvas[0] / ROUTE_CELL), math.ceil(terrain.canvas[1] / ROUTE_CELL)


def cell_of(terrain, p):
    """The route cell (column, row) of a point, clamped to the canvas grid."""
    cols, rows = _grid(terrain)
    return min(max(int(p[0] // ROUTE_CELL), 0), cols - 1), min(max(int(p[1] // ROUTE_CELL), 0), rows - 1)


def cell_centre(c):
    return (c[0] + 0.5) * ROUTE_CELL, (c[1] + 0.5) * ROUTE_CELL


def cell_open(terrain, layer, c):
    """Decision 20: a route cell is open when its CENTRE is in no block that reaches `layer`."""
    return not in_block(terrain.blocks, layer, cell_centre(c))


def nearest_free_cell(terrain, layer, anchor):
    """The open route cell whose centre is nearest the anchor (decision 38 items 2 and 3); None when no cell is open. Written here
    from the words of the ruling, not from any builder: an exhaustive scan of the grid. Exact ties are broken by (column, row) and
    are NOT part of what the tests pin: every test that uses this has a unique nearest cell, or only needs the region it starts."""
    cols, rows = _grid(terrain)
    cands = [(math.hypot(cell_centre((i, j))[0] - anchor[0], cell_centre((i, j))[1] - anchor[1]), i, j)
             for i in range(cols) for j in range(rows) if cell_open(terrain, layer, (i, j))]
    return None if not cands else min(cands)[1:]


def route_region(terrain, layer, anchor):
    """(cells, cell_of): the route cells connected (four neighbours) over open cells to the anchor's cell; when the anchor's own cell
    is not open, to the nearest open cell (decision 38 item 2). On a hand-built terrain the mask of a flyer and a walker agree. The
    second item is a function point -> cell. Empty when no cell is open."""
    cols, rows = _grid(terrain)
    start = cell_of(terrain, anchor)
    if not cell_open(terrain, layer, start):
        start = nearest_free_cell(terrain, layer, anchor)
        if start is None:
            return set(), (lambda p: cell_of(terrain, p))
    seen, queue = {start}, [start]
    while queue:
        cx, cy = queue.pop()
        for n in ((cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1)):
            if 0 <= n[0] < cols and 0 <= n[1] < rows and n not in seen and cell_open(terrain, layer, n):
                seen.add(n)
                queue.append(n)
    return seen, (lambda p: cell_of(terrain, p))


def single_unit_cell(terrain, layer, anchor):
    """Where a blob of ONE unit stands (decision 38 item 3), as a route cell: its own anchor's cell when the anchor point is free and
    its cell open and in the region, else the nearest open in-region cell. (The nearest open cell is the start of the region, so it is
    in the region.) The tests pin the CELL the unit stands in, not a coordinate inside it."""
    seen, cell_fn = route_region(terrain, layer, anchor)
    if inside_canvas(terrain, anchor) and not in_block(terrain.blocks, layer, anchor) and cell_fn(anchor) in seen:
        return cell_fn(anchor)
    return nearest_free_cell(terrain, layer, anchor)


def inside_canvas(terrain, p):
    """Decision 36 item 1: a cell outside the layout's canvas counts as blocked (bounds inclusive)."""
    return 0.0 <= p[0] <= terrain.canvas[0] and 0.0 <= p[1] <= terrain.canvas[1]


def expected_skipping(g, terrain, canvas=True, connected=True):
    """The positions, IN FILL ORDER, a naive blob group g holds when its next cell is skipped while it is blocked, outside the canvas
    or outside the anchor's connected region (decisions 26 and 36): the first g.count such free cells of fill_order. None when the
    region has no free cell left for the count ("cannot hold the count"; the sequence is walked out to the canvas diagonal, past
    which nothing is inside the canvas). `canvas=False` / `connected=False` give the readings of a builder that ignores that rule (the
    tests' fixture guards use them to show a case really separates the rules)."""
    anchor = (g.x, g.y)
    seen, cell_of = route_region(terrain, g.layer, anchor)
    reach = math.hypot(*terrain.canvas) + 1.0
    out = []
    for p in fill_order(g.count, g.x, g.y, radius_of(g.count)):
        if math.hypot(p[0] - g.x, p[1] - g.y) > reach:
            return None
        if (canvas and not inside_canvas(terrain, p)) or in_block(terrain.blocks, g.layer, p) or (connected and cell_of(p) not in seen):
            continue
        out.append(p)
        if len(out) == g.count:
            return out
    return None


def keyed(pts, nd=4):
    """Sorted, rounded: for SET comparisons only. Skipped cells are compared in fill order with rounded()."""
    return sorted(rounded(pts, nd))


def rounded(pts, nd=4):
    """The points to `nd` decimals in the order given (decision 36 item 3: the skipped cells are compared unsorted, in fill order)."""
    return [(round(p[0], nd), round(p[1], nd)) for p in pts]


def slab_through(g, dx0, dx1, dy0, dy1, layer_lo=0, layer_hi=4):
    """A wall in FINAL coordinates through group g's blob: x from g.x + dx0 to g.x + dx1, y from g.y + dy0 to g.y + dy1."""
    return Block(g.x + dx0, g.y + dy0, g.x + dx1, g.y + dy1, layer_lo, layer_hi)


def fake_base(groups, blocks=(), label="ok", canvas=(4000.0, 4000.0), point=(2000.0, 1000.0)):
    """A stand-in for scenes.placed_scene's return: build(enemy_heads, swap) -> Setup of `groups` on a hand-built terrain, whose
    labels['prefight'] is `label` whatever the Setup is (a base that is wrong about itself on purpose)."""
    def build(enemy_heads, swap):
        build.labels["prefight"] = label
        return Setup(groups=tuple(groups), unit_types={}, terrain=Terrain(canvas=canvas, blocks=tuple(blocks)), point=point)
    build.labels = {"placement_shift": 0.0, "prefight": None}
    return build


def vg(side, unit, count, x, y, layer=0, order="attack_move", facing=0.0):
    return Group(side=side, unit=unit, count=count, formation="blob", x=x, y=y, facing_deg=facing, layer=layer, order=order,
                 params={"radius": radius_of(count)})
