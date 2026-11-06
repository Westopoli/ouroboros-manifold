"""Layout features as ground for the arena sim (spec: docs/stories/H-063.md, "Rulings for the build" 7 and 8).

`apply` hands a layout's features to the engine through calls that already exist: the planar kinds (chokepoint walls, cover boxes, city buildings, the ridge inside a
flank_route feature) as `Engine.block_rect` over every layer of the landscape, and the slope band as a generated terrain whose heights are replaced by
`Engine.terrain_set_heights` (the walker then climbs at 1 / OM_TP_SLOPE_UP_DIV of the pace). Plateau, ring, band, pocket, disc and tier steps stay drawn only until
a layout uses them. `first_unreachable` is the preflight route check behind the runner's reachability REJECT (rule R8 in catalogue/rules.toml), after
scripts/skilllab/scenes.py `_unroutable`; it routes over the engine's own rules: blocks rounded out to NAV_CELL (100 wu, R-097-01) cells as `block_rect` rounds them and, for a slope or
a hill, the engine's walk mask on a world `apply` has run on.

Stage 4 fix (docs/reports/2026-11-06-stage4-fix-plan.md): `apply(..., exact=True)` is the `--sight on` conversion. Each planar rectangle is snapped to the 100 wu grid with no pad
(snap.py), so what the engine blocks is what is drawn (the old pad-and-round conversion over-blocked by up to 99 wu a side), and each `vantage` feature is built as terrain
(hills.py). `exact=False` is the stage 1 to 3 conversion, kept unchanged so that `--sight off` fights reproduce byte for byte.

Slope heights: only heading 0 (rising toward +x) and from_band 0 to_band 1 are built (every catalogue slope is that); anything else raises ValueError. The band
floors come from the highest cell (`om_terrain_set_heights` rule), so the cells of the ramp's two flanks beyond one buffer cell are a spike that is also the wall of the
cliff: the ribbon is the only way up. Planar blocks laid on a world with a slope are not seen by the walk planner (tests/csim/test_VG_W_w2_routes.py T0), so a layout
that carries both has its planar kinds honoured by the collision grid only.
See also: scripts/skilllab/arena/run.py (calls both), scenes/proto/layout_shot/layout_shot.gd (the drawing of the same features)."""
import collections
import math

WALKING_KIND = 1          # om_roster_set_movement_kind: 0 flying (the default), 1 walking (the same number as scripts/skilllab/fight.py)
PLANAR_KEYS = ("walls", "boxes", "buildings")
NAV_CELL = 100.0          # wu; OM_NAVMESH_CELL_SIZE (csrc/om_constants.h:585, R-097-01): the reachability grid is the engine's own block grid
LEGACY_NAV_CELL = 50.0    # the cell the stage 3 preflight (`exact=False`) assumed; kept so its REJECT decisions do not change. See also: NAV_CELL, snap.py
TERRAIN_CELL = 100.0      # OM_TERRAIN_CELL_WU
LOW_CM = 7000             # above the generator's dry level (6000 cm), so it is a band floor
STEP_CM = 16000           # one band: big enough that a one-cell step is steeper than OM_TP_TERRAIN_STEEP_DEG allows
EDGE_PAD_WU = 1.0         # (`exact=False` only) block_rect rounds out to whole navmesh cells, and a walker settles up to about 2 wu into the first blocked cell, so a cell-aligned edge needs one more cell
BAND_DIV = 5              # TG_BAND_DIV: the highest cell sets the floors, so the spike is LOW_CM + 5 steps


def _feature_rects(f):
    return [r for key in PLANAR_KEYS for r in f.get(key, [])] + ([f["ridge"]] if "ridge" in f else [])


def planar_rects(layout):
    """[(cx, cy, w, h)] of every wall, box, building and ridge rectangle of the layout's features."""
    return [(r["x"], r["y"], r["w"], r["h"]) for f in layout.get("features", []) for r in _feature_rects(f)]


def _engine_boxes(layout, exact=False):
    """[(x0, y0, x1, y1)] to block. `exact`: the snapped rectangles (snap.built_rects), no pad. Otherwise (stage 1 to 3): each rectangle padded by EDGE_PAD_WU on every edge, except that a chokepoint wall keeps an edge that faces the feature's own
    centre (x, y) from outside, which is the gap, and padding it would shut the gap by a cell."""
    if exact:
        from scripts.skilllab.arena import snap   # here, not at the top: snap imports this module
        return snap.built_rects(layout)
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


def bound(layout, exact=False):
    """True when `apply` gives the engine anything for this layout (`exact`: a vantage is terrain too)."""
    return bool(planar_rects(layout) or slopes(layout) or (exact and _hills(layout)))


def _hills(layout):
    from scripts.skilllab.arena import hills   # here, not at the top: keeps the import order of the older modules
    return hills.vantages(layout)


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


def apply(engine, w, layout, preset, seed, exact=False):
    """Lay the layout's features on world `w`; True when anything was laid. Call before spawning. Sets the canvas to the preset's size (block_rect needs one).
    `exact` is the `--sight on` conversion (module docstring): snapped blocks and the vantage hills as terrain."""
    boxes, ramps, hill_features = _engine_boxes(layout, exact), slopes(layout), _hills(layout) if exact else []
    if not (boxes or ramps or hill_features):
        return False
    engine.set_canvas(w, preset["width"], preset["height"])
    if hill_features:
        from scripts.skilllab.arena import hills
        if ramps:
            raise ValueError("a layout with a vantage and a slope feature is not built (one terrain a layout)")
        hills.check_preset(preset)
        engine.terrain_generate(w, seed, preset["width"])
        engine.set_era_kind(w, 1)
        cw, ch, _ = engine.terrain_dump_bands(w)
        engine.terrain_set_heights(w, hills.heights(hill_features, cw, ch), cw, ch)
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


def _open_grid(engine, w, layout, preset, exact=False):
    """(grid, cols, rows) on cells, 1 = open: every `_engine_boxes` rectangle rounded out to whole cells as `apply` sets them, and for a slope or a hill the cells whose
    centre is walkable on no layer of the preset (`Engine.terrain_walk_mask`, one byte per TERRAIN_CELL; DRAFT-reach-mask-union). `w` has had `apply` run on it. The cell is
    NAV_CELL (100 wu, the engine's); `exact=False` keeps the stage 3 figure LEGACY_NAV_CELL (cell_wu below)."""
    cell_wu = NAV_CELL if exact else LEGACY_NAV_CELL
    cols, rows = int(preset["width"] // cell_wu), int(preset["height"] // cell_wu)
    grid = bytearray(b"\x01" * (cols * rows))
    for x0, y0, x1, y1 in _engine_boxes(layout, exact):
        gx0, gx1 = max(0, math.floor(x0 / cell_wu)), min(cols - 1, math.ceil(x1 / cell_wu) - 1)
        for gy in range(max(0, math.floor(y0 / cell_wu)), min(rows - 1, math.ceil(y1 / cell_wu) - 1) + 1):
            for gx in range(gx0, gx1 + 1):
                grid[gy * cols + gx] = 0
    if slopes(layout) or (exact and _hills(layout)):
        tw, _, _ = engine.terrain_dump_bands(w)
        walk = None
        for layer in range(preset["layers"]):
            mask = engine.terrain_walk_mask(w, layer)
            walk = mask if walk is None else bytes(a | b for a, b in zip(walk, mask))
        for gy in range(rows):
            for gx in range(cols):
                if not walk[int((gy + 0.5) * cell_wu // TERRAIN_CELL) * tw + int((gx + 0.5) * cell_wu // TERRAIN_CELL)]:
                    grid[gy * cols + gx] = 0
    return grid, cols, rows


def first_unreachable(engine, w, layout, preset, point, sides, exact=False, members=None):
    """'side_b unit 2' for the first unit (side_a rows first) of `sides` ('side_a', 'side_b') with no 4-connected path of open cells to `point`, else None.
    The open cells are the engine's (`_open_grid`; `apply` has already run on world `w`). A unit passes when its own cell or a neighbour is reached; a point inside a
    blocked area is moved to the nearest open cells. None when the layout has neither planar rectangles nor a slope."""
    if not bound(layout, exact):
        return None
    grid, cols, rows = _open_grid(engine, w, layout, preset, exact)
    cell_wu = NAV_CELL if exact else LEGACY_NAV_CELL
    cell = lambda x, y: (min(max(int(x // cell_wu), 0), cols - 1), min(max(int(y // cell_wu), 0), rows - 1))
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
            if members is not None and (side, i) not in members:
                continue   # group orders: only the units that walk to this point
            x, y = cell(u["x"], u["y"])
            if not any(c in seen for c in ((x, y), (x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1))):
                return "%s unit %d" % (side, i)
    return None
