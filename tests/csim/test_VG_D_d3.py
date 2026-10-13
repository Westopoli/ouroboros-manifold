"""Visible-game programme lane D, piece D3 (docs/northstar/plans/2026-10-07-visible-game-spec.md rev 4, lane D;
docs/northstar/plans/preflight_2026-10-07/5-space-kit.md): the plate polygons rasterised to the 100 wu cell masks, and
the carve step that guarantees a route to the objective. Fenced: builders never edit this file.

Proves S-246 R-246-01 (the generator ported into the simulation; Q-STAGE3-03 b), R-246-03 (masks and plate polygons
both reach the client, Q-166-06) and E-01 R-001-04 (a binary mask per layer), against the port of
scenes/mockups/landscape/field_map_space.gd. Only the symbols already in csrc/ouroboros_sim.h are used
(om_space_field_generate_nodes / _get_mask / _poly_count / _poly_get); D3 adds none.

What the tests encode, with its source in the mockup:
  RASTER   a mask cell whose centre ((cx + .5) * 100, (cy + .5) * 100 wu) lies at least 1 wu inside a plate polygon of
           that layer is blocked ("the fine mask opens, the plates lose the same area (see _cut_polygons), so mask and
           picture agree"). The converse is NOT asserted: pocket-filled cells are blocked with no polygon (_fill_pockets).
  SHAPE    polygons are straight-edged, counter-clockwise (positive signed area, "plate_polys ... counter-clockwise"),
           inside the 24000 wu canvas, kind in {0 plate, 1 mass, 2 rubble}; the plates are Voronoi-style cells, so
           every layer holds at least one edge that is neither horizontal nor vertical (the placeholder is boxes only).
  CARVE    the "ordinary" map: a cell is passable when it lies in a fully open 3 x 3 block of one layer
           (MIN_PASSAGE_WU 300 / 100 wu cells, _open_block); regions are six-neighbour (four in-plane, one above, one
           below) flood fills of passable cells (_label_regions). regions_unreachable_after = regions - 1 = 0: ONE
           region remains, and it holds a passable cell at the objective (canvas centre) and at both spawn points
           (15 % and 85 % of the canvas diagonal), each looked up in the 2 x 2 cells around the node point on any layer
           (unit spawn layer is an open flag in the pre-flight, so any layer).
           Every seed below must pass; the seeds are the test's own choice, not a threshold.

Positive controls (pure Python, no library): the checker flags a planted unblocked cell inside a polygon; the region
counter sees a sealed open room as a second region, sees a 1-cell-wide channel as NOT joining two halves (the 300 wu
passage rule) and a 3-cell-wide channel as joining them.

Not asserted (no number or rule given): blocked share per density, polygon count per layer, how many pocket-filled
cells exist, which of widen or drop joined a region, the small-craft map (Q-166-05, not in D), sections.
On main (the K-d placeholder: four axis-aligned boxes per layer) the SHAPE diagonal-edge test fails; every other test
holds there and keeps holding as the real generator lands.
"""
import ctypes

import pytest

W = ctypes.c_void_p
U8P = ctypes.POINTER(ctypes.c_uint8)
U32P = ctypes.POINTER(ctypes.c_uint32)
DP = ctypes.POINTER(ctypes.c_double)
CANVAS = 24000.0
N = 240
CELLS = N * N
CELL_WU = 100.0
LAYERS = 5
SEEDS = [1, 2, 3, 7, 11, 42]
PTS_CAP = 256  # points a read buffer holds; a polygon needing more is reported by poly_get returning 0
INSIDE_MARGIN_WU = 1.0
PASSAGE_CELLS = 3  # MIN_PASSAGE_WU 300 / 100
KINDS = (0, 1, 2)
ROW_MASK = (1 << N) - 1


# ---- library binding -------------------------------------------------------------------------------------------

def bind(lib):
    names = ["om_space_field_generate_nodes", "om_space_field_get_mask", "om_space_field_poly_count",
             "om_space_field_poly_get"]
    missing = [n for n in names if not hasattr(lib, n)]
    assert not missing, f"space field symbols missing from libouroboros.so: {missing}"
    lib.om_space_field_generate_nodes.argtypes = [W, ctypes.c_uint32, ctypes.c_double, ctypes.c_double, ctypes.c_double, ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_uint32), ctypes.c_uint32]
    lib.om_space_field_generate_nodes.restype = ctypes.c_int
    lib.om_space_field_get_mask.argtypes = [W, ctypes.c_uint32, U8P, ctypes.c_uint32]
    lib.om_space_field_get_mask.restype = ctypes.c_uint32
    lib.om_space_field_poly_count.argtypes = [W]
    lib.om_space_field_poly_count.restype = ctypes.c_uint32
    lib.om_space_field_poly_get.argtypes = [W, ctypes.c_uint32, U32P, U32P, DP, ctypes.c_uint32]
    lib.om_space_field_poly_get.restype = ctypes.c_uint32


def generated(lib, world_factory, seed):
    bind(lib)
    w = world_factory(n_regions=1)
    assert lib.om_map_set_canvas(w, CANVAS, CANVAS) == 0
    assert lib.om_space_field_generate_nodes(w, seed, CANVAS, CANVAS, 35.0, None, None, 0) == 0
    return w


def read_masks(lib, w):
    out = []
    for k in range(LAYERS):
        buf = (ctypes.c_uint8 * CELLS)()
        assert lib.om_space_field_get_mask(w, k, buf, CELLS) == CELLS
        out.append(bytes(buf))
    return out


def read_polys(lib, w):
    """[(layer, kind, [(x, y), ...])]"""
    polys = []
    for i in range(lib.om_space_field_poly_count(w)):
        layer, kind = ctypes.c_uint32(), ctypes.c_uint32()
        xy = (ctypes.c_double * (2 * PTS_CAP))()
        n = lib.om_space_field_poly_get(w, i, ctypes.byref(layer), ctypes.byref(kind), xy, PTS_CAP)
        assert n >= 3, f"polygon {i}: poly_get returned {n} points (cap {PTS_CAP})"
        polys.append((layer.value, kind.value, [(xy[2 * j], xy[2 * j + 1]) for j in range(n)]))
    return polys


# ---- geometry and mask checkers (pure Python) --------------------------------------------------------------------

def signed_area(pts):
    return 0.5 * sum(pts[i][0] * pts[(i + 1) % len(pts)][1] - pts[(i + 1) % len(pts)][0] * pts[i][1]
                     for i in range(len(pts)))


def inside_with_margin(pts, px, py, margin):
    """Even-odd inside and at least `margin` wu from every edge."""
    inside = False
    n = len(pts)
    for i in range(n):
        ax, ay = pts[i]
        bx, by = pts[(i + 1) % n]
        if (ay <= py < by) or (by <= py < ay):
            if ax + (py - ay) / (by - ay) * (bx - ax) > px:
                inside = not inside
        dx, dy = bx - ax, by - ay
        ln2 = dx * dx + dy * dy
        t = 0.0 if ln2 == 0.0 else max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / ln2))
        cx, cy = ax + t * dx, ay + t * dy
        if (px - cx) ** 2 + (py - cy) ** 2 < margin * margin:
            return False
    return inside


def unblocked_cells_inside_polys(masks, polys):
    """(layer, cx, cy) of every open cell whose centre lies >= INSIDE_MARGIN_WU inside a polygon of that layer."""
    bad = []
    for layer, _kind, pts in polys:
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        for cy in range(max(0, int(min(ys) // CELL_WU) - 1), min(N, int(max(ys) // CELL_WU) + 2)):
            for cx in range(max(0, int(min(xs) // CELL_WU) - 1), min(N, int(max(xs) // CELL_WU) + 2)):
                if masks[layer][cy * N + cx] == 0 and inside_with_margin(
                        pts, (cx + 0.5) * CELL_WU, (cy + 0.5) * CELL_WU, INSIDE_MARGIN_WU):
                    bad.append((layer, cx, cy))
    return bad


def _rows(mask):
    """Open cells (mask byte 0) of one layer as one int bitmask per row (bit cx)."""
    rows = []
    for cy in range(N):
        r = 0
        for cx in range(N):
            if mask[cy * N + cx] == 0:
                r |= 1 << cx
        rows.append(r)
    return rows


def passable_rows(mask):
    """_open_block with size 3: every cell inside a fully open 3 x 3 block of the layer."""
    rows = _rows(mask)
    h = [r & (r << 1) & (r >> 1) & ROW_MASK for r in rows]
    eroded = [0] * N
    for y in range(1, N - 1):
        eroded[y] = h[y - 1] & h[y] & h[y + 1]
    d = [(r | (r << 1) | (r >> 1)) & ROW_MASK for r in eroded]
    return [(d[y] | (d[y - 1] if y else 0) | (d[y + 1] if y < N - 1 else 0)) for y in range(N)]


def regions(masks):
    """Six-neighbour flood fill over passable cells of all layers. Returns (labels dict cell -> id, sizes)."""
    layers = [passable_rows(m) for m in masks]
    labels, sizes = {}, []
    for k in range(LAYERS):
        for y in range(N):
            r = layers[k][y]
            while r:
                low = r & -r
                x = low.bit_length() - 1
                r ^= low
                if (k, x, y) in labels:
                    continue
                rid = len(sizes)
                labels[(k, x, y)] = rid
                stack, size = [(k, x, y)], 0
                while stack:
                    kk, cx, cy = stack.pop()
                    size += 1
                    for nk, nx, ny in ((kk, cx - 1, cy), (kk, cx + 1, cy), (kk, cx, cy - 1), (kk, cx, cy + 1),
                                       (kk - 1, cx, cy), (kk + 1, cx, cy)):
                        if 0 <= nk < LAYERS and 0 <= nx < N and 0 <= ny < N and (nk, nx, ny) not in labels \
                                and (layers[nk][ny] >> nx) & 1:
                            labels[(nk, nx, ny)] = rid
                            stack.append((nk, nx, ny))
                sizes.append(size)
    return labels, sizes


def node_regions(labels, wx, wy):
    """Region ids of passable cells in the 2 x 2 cells around the world point, any layer."""
    cx0, cy0 = int(wx // CELL_WU), int(wy // CELL_WU)
    found = set()
    for k in range(LAYERS):
        for cy in (cy0 - 1, cy0):
            for cx in (cx0 - 1, cx0):
                if (k, cx, cy) in labels:
                    found.add(labels[(k, cx, cy)])
    return found


# ---- positive controls ---------------------------------------------------------------------------------------------

def synth_open():
    return [bytearray(CELLS) for _ in range(LAYERS)]  # all open


def block_rect(mask, x0, y0, x1, y1):
    for y in range(y0, y1):
        for x in range(x0, x1):
            mask[y * N + x] = 1


def test_control_raster_checker_flags_a_planted_open_cell():
    box = [(1000.0, 1000.0), (3000.0, 1000.0), (3000.0, 3000.0), (1000.0, 3000.0)]
    masks = [bytearray(CELLS) for _ in range(LAYERS)]
    block_rect(masks[2], 10, 10, 30, 30)
    assert unblocked_cells_inside_polys(masks, [(2, 0, box)]) == []
    masks[2][20 * N + 20] = 0
    assert unblocked_cells_inside_polys(masks, [(2, 0, box)]) == [(2, 20, 20)]
    assert unblocked_cells_inside_polys(masks, [(3, 0, box)]) != [], "wrong layer must not hide the open cells"


def test_control_region_counter_sees_a_sealed_room_and_the_passage_width():
    # one open field: a single region
    assert len(regions(synth_open())[1]) == 1
    # a sealed 8 x 8 open room (walls 4 thick) on every layer is a second region
    masks = [bytearray(b"\x01" * CELLS) for _ in range(LAYERS)]
    for m in masks:
        for y in range(0, 100):
            for x in range(0, 100):
                m[y * N + x] = 0  # big room
        for y in range(150, 158):
            for x in range(150, 158):
                m[y * N + x] = 0  # sealed room
    assert len(regions(masks)[1]) == 2
    # two halves joined by a channel of width 1 (too narrow) or 3 (enough)
    for width, count in ((1, 2), (3, 1)):
        masks = [bytearray(CELLS) for _ in range(LAYERS)]
        for m in masks:
            block_rect(m, 118, 0, 122, N)  # a wall 4 cells thick
            for y in range(100, 100 + width):
                for x in range(118, 122):
                    m[y * N + x] = 0
        assert len(regions(masks)[1]) == count, f"channel width {width} should give {count} region(s)"


# ---- rasterisation and shape -----------------------------------------------------------------------------------------

@pytest.mark.parametrize("seed", SEEDS)
def test_cells_inside_a_plate_polygon_are_blocked(lib, world_factory, seed):
    """R-246-01 / R-246-03: the mask is the polygons rasterised (cell centre inside a plate means blocked)."""
    w = generated(lib, world_factory, seed)
    polys = read_polys(lib, w)
    assert polys, "no plate polygons reported"
    bad = unblocked_cells_inside_polys(read_masks(lib, w), polys)
    assert not bad, f"{len(bad)} open cells lie inside a plate polygon, first {bad[:3]}"


def test_polygons_are_straight_ccw_in_canvas_with_known_kinds(lib, world_factory):
    w = generated(lib, world_factory, SEEDS[0])
    polys = read_polys(lib, w)
    assert polys
    for i, (layer, kind, pts) in enumerate(polys):
        assert layer < LAYERS, f"polygon {i}: layer {layer}"
        assert kind in KINDS, f"polygon {i}: kind {kind}"
        assert signed_area(pts) > 0.0, f"polygon {i}: not counter-clockwise with positive area"
        assert all(0.0 <= x <= CANVAS and 0.0 <= y <= CANVAS for x, y in pts), f"polygon {i}: outside the canvas"


def test_every_layer_has_a_diagonal_plate_edge(lib, world_factory):
    """Plates are straight-edged cells of a lattice, not boxes: each layer has an edge that is neither horizontal nor
    vertical (red on the K-d placeholder, whose plates are all axis-aligned boxes)."""
    w = generated(lib, world_factory, SEEDS[0])
    has = [False] * LAYERS
    for layer, _kind, pts in read_polys(lib, w):
        for i in range(len(pts)):
            (ax, ay), (bx, by) = pts[i], pts[(i + 1) % len(pts)]
            if abs(ax - bx) > 1e-6 and abs(ay - by) > 1e-6:
                has[layer] = True
    assert all(has), f"layers without a diagonal edge: {[k for k in range(LAYERS) if not has[k]]}"


def test_same_seed_same_polygons_and_masks(lib, world_factory):
    """Determinism contract: same seed, identical polygons (bit for bit) and masks."""
    a, b = generated(lib, world_factory, SEEDS[0]), generated(lib, world_factory, SEEDS[0])
    assert read_polys(lib, a) == read_polys(lib, b)
    assert read_masks(lib, a) == read_masks(lib, b)


# ---- the carve step -----------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("seed", SEEDS)
def test_carve_leaves_zero_unreachable_regions(lib, world_factory, seed):
    """The mockup's regions_unreachable_after: after the carve exactly one passable region remains."""
    w = generated(lib, world_factory, seed)
    _labels, sizes = regions(read_masks(lib, w))
    assert len(sizes) >= 1, "no passable cell at all"
    assert len(sizes) == 1, f"{len(sizes) - 1} unreachable regions remain (region sizes {sorted(sizes)[:6]}...)"


@pytest.mark.parametrize("seed", SEEDS)
def test_route_exists_to_objective_from_both_spawns(lib, world_factory, seed):
    """The carve guarantees a route to the objective: the canvas centre and both spawn points (15 % and 85 % of the
    canvas) each hold a passable cell and share the one region."""
    w = generated(lib, world_factory, seed)
    labels, sizes = regions(read_masks(lib, w))
    points = {"objective": (CANVAS * 0.5, CANVAS * 0.5), "spawn A": (CANVAS * 0.15, CANVAS * 0.15),
              "spawn B": (CANVAS * 0.85, CANVAS * 0.85)}
    found = {name: node_regions(labels, *p) for name, p in points.items()}
    empty = [n for n, f in found.items() if not f]
    assert not empty, f"no passable cell at {empty}"
    assert len(set().union(*found.values())) == 1, f"nodes sit in different regions: {found}"
    assert len(sizes) == 1
