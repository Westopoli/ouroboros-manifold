"""Layout features as ground for the arena sim (spec: docs/stories/H-063.md, "Rulings for the build" 7 and 8).

`apply` hands a layout's features to the engine through calls that already exist: the planar kinds (chokepoint walls, cover boxes, city buildings, the ridge inside a
flank_route feature) as `Engine.block_rect` over every layer of the landscape, and the slope band as a generated terrain whose heights are replaced by
`Engine.terrain_set_heights` (the walker then climbs at 1 / OM_TP_SLOPE_UP_DIV of the pace). Plateau, ring, band, pocket, disc and tier steps stay drawn only until
a layout uses them. `first_unreachable` is the preflight route check behind the runner's reachability REJECT (rule R8 in catalogue/rules.toml), after
scripts/skilllab/scenes.py `_unroutable`.

Slope heights: only heading 0 (rising toward +x) and from_band 0 to_band 1 are built (every catalogue slope is that); anything else raises ValueError. The band
floors come from the highest cell (`om_terrain_set_heights` rule), so the cells of the ramp's two flanks beyond one buffer cell are a spike that is also the wall of the
cliff: the ribbon is the only way up. Planar blocks laid on a world with a slope are not seen by the walk planner (tests/csim/test_VG_W_w2_routes.py T0), so a layout
that carries both has its planar kinds honoured by the collision grid only.
See also: scripts/skilllab/arena/run.py (calls both), scenes/proto/layout_shot/layout_shot.gd (the drawing of the same features)."""
import collections

WALKING_KIND = 1          # om_roster_set_movement_kind: 0 flying (the default), 1 walking (the same number as scripts/skilllab/fight.py)
PLANAR_KEYS = ("walls", "boxes", "buildings")
ROUTE_CELL = 20.0         # wu; the reachability grid. Finer than 50 so a 40 wu strip always holds a cell centre
TERRAIN_CELL = 100.0      # OM_TERRAIN_CELL_WU
LOW_CM = 7000             # above the generator's dry level (6000 cm), so it is a band floor
STEP_CM = 16000           # one band: big enough that a one-cell step is steeper than OM_TP_TERRAIN_STEEP_DEG allows
EDGE_PAD_WU = 1.0         # block_rect rounds out to 50 wu navmesh cells, and a walker settles up to about 2 wu into the first blocked cell, so a cell-aligned edge needs one more cell
BAND_DIV = 5              # TG_BAND_DIV: the highest cell sets the floors, so the spike is LOW_CM + 5 steps


def _feature_rects(f):
    return [r for key in PLANAR_KEYS for r in f.get(key, [])] + ([f["ridge"]] if "ridge" in f else [])


def planar_rects(layout):
    """[(cx, cy, w, h)] of every wall, box, building and ridge rectangle of the layout's features."""
    return [(r["x"], r["y"], r["w"], r["h"]) for f in layout.get("features", []) for r in _feature_rects(f)]


def _engine_boxes(layout):
    """[(x0, y0, x1, y1)] to block: each rectangle padded by EDGE_PAD_WU on every edge, except that a chokepoint wall keeps an edge that faces the feature's own
    centre (x, y) from outside, which is the gap, and padding it would shut the gap by a cell."""
    out = []
    for f in layout.get("features", []):
        for r in _feature_rects(f):
            x0, y0, x1, y1 = r["x"] - r["w"] / 2, r["y"] - r["h"] / 2, r["x"] + r["w"] / 2, r["y"] + r["h"] / 2
            fx, fy, pad = f.get("x", r["x"]), f.get("y", r["y"]), EDGE_PAD_WU
            gap = r in f.get("walls", [])
            out.append((x0 - (0 if gap and fx < x0 else pad), y0 - (0 if gap and fy < y0 else pad), x1 + (0 if gap and fx > x1 else pad), y1 + (0 if gap and fy > y1 else pad)))
    return out


def slopes(layout):
    return [f for f in layout.get("features", []) if f.get("kind") == "slope"]


def bound(layout):
    """True when `apply` gives the engine anything for this layout."""
    return bool(planar_rects(layout) or slopes(layout))


def _slope_heights(f, cells_w, cells_h):
    if f.get("heading", 0.0) != 0.0 or f.get("from_band", 0) != 0 or f.get("to_band", 1) != 1:
        raise ValueError("slope feature %r: only heading 0 and from_band 0 to_band 1 are built" % (f,))
    c0 = int((f["x"] - f["length"] / 2) // TERRAIN_CELL)
    c1 = int((f["x"] + f["length"] / 2) // TERRAIN_CELL) - 1
    r0 = int((f["y"] - f["width"] / 2) // TERRAIN_CELL)
    r1 = int((f["y"] + f["width"] / 2) // TERRAIN_CELL) - 1
    if c1 <= c0 or r1 < r0:
        raise ValueError("slope feature %r is under two cells long or a cell wide" % (f,))
    high, spike = LOW_CM + STEP_CM, LOW_CM + BAND_DIV * STEP_CM
    cm = []
    for cy in range(cells_h):
        for cx in range(cells_w):
            ramp = LOW_CM + (STEP_CM * (cx - c0)) // (c1 - c0)
            if cx < c0:
                cm.append(LOW_CM)
            elif cx > c1:
                cm.append(high)
            elif r0 - 1 <= cy <= r1 + 1:   # the ribbon and one buffer cell either side, so the spike does not tip the ribbon's own cells steep
                cm.append(ramp)
            else:
                cm.append(spike)
    return cm


def apply(engine, w, layout, preset, seed):
    """Lay the layout's features on world `w`; True when anything was laid. Call before spawning. Sets the canvas to the preset's size (block_rect needs one)."""
    boxes, ramps = _engine_boxes(layout), slopes(layout)
    if not (boxes or ramps):
        return False
    engine.set_canvas(w, preset["width"], preset["height"])
    if ramps:
        if len(ramps) > 1:
            raise ValueError("one slope feature a layout is built, got %d" % len(ramps))
        engine.terrain_generate(w, seed, preset["width"])
        engine.set_era_kind(w, 1)   # the walker's movement kind, as fight.py does after a generated field
        cw, ch, _ = engine.terrain_dump_bands(w)
        engine.terrain_set_heights(w, _slope_heights(ramps[0], cw, ch), cw, ch)
    for x0, y0, x1, y1 in boxes:   # after set_heights: it rewrites the mapgen blocked bits
        engine.block_rect(w, x0, y0, x1, y1, 0, preset["layers"] - 1)
    return True


def walk_on_ground(engine, w, types):
    """Make every role in `types` ({role: (type id, range)}) a walker. A built-in type flies, and a flyer neither follows a walk route nor feels the slope;
    ground that pushes back needs walking (scripts/skilllab/fight.py WALKING_KIND)."""
    for type_id, _ in types.values():
        engine.set_movement_kind(w, type_id, WALKING_KIND)


def _open_grid(layout, preset):
    cols, rows = int(preset["width"] // ROUTE_CELL), int(preset["height"] // ROUTE_CELL)
    grid = bytearray(b"\x01" * (cols * rows))   # 1 = open
    for cx, cy, rw, rh in planar_rects(layout):
        # cells whose centre lies strictly inside the rectangle
        x0 = max(0, int((cx - rw / 2) // ROUTE_CELL))
        x1 = min(cols - 1, int((cx + rw / 2) // ROUTE_CELL))
        y0 = max(0, int((cy - rh / 2) // ROUTE_CELL))
        y1 = min(rows - 1, int((cy + rh / 2) // ROUTE_CELL))
        for gy in range(y0, y1 + 1):
            for gx in range(x0, x1 + 1):
                if abs((gx + 0.5) * ROUTE_CELL - cx) < rw / 2 and abs((gy + 0.5) * ROUTE_CELL - cy) < rh / 2:
                    grid[gy * cols + gx] = 0
    return grid, cols, rows


def first_unreachable(layout, preset, point, sides):
    """'side_b unit 2' for the first unit (side_a rows first) of `sides` ('side_a', 'side_b') with no 4-connected path of open cells to `point`, else None.
    A unit passes when its own cell or a neighbour is reached; a point inside a blocked area is moved to the nearest open cells."""
    if not planar_rects(layout):
        return None
    grid, cols, rows = _open_grid(layout, preset)
    cell = lambda x, y: (min(max(int(x // ROUTE_CELL), 0), cols - 1), min(max(int(y // ROUTE_CELL), 0), rows - 1))
    start = cell(*point)
    ring, seen_all = [start], {start}
    while ring and not any(grid[y * cols + x] for x, y in ring):   # the nearest open cells, ignoring blocks
        nxt = []
        for x, y in ring:
            for n in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                if 0 <= n[0] < cols and 0 <= n[1] < rows and n not in seen_all:
                    seen_all.add(n)
                    nxt.append(n)
        ring = nxt
    seeds = [c for c in ring if grid[c[1] * cols + c[0]]]
    seen, queue = set(seeds), collections.deque(seeds)
    while queue:
        x, y = queue.popleft()
        for n in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if 0 <= n[0] < cols and 0 <= n[1] < rows and n not in seen and grid[n[1] * cols + n[0]]:
                seen.add(n)
                queue.append(n)
    for side in sides:
        for i, u in enumerate(layout[side]["units"]):
            x, y = cell(u["x"], u["y"])
            if not any(c in seen for c in ((x, y), (x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1))):
                return "%s unit %d" % (side, i)
    return None
