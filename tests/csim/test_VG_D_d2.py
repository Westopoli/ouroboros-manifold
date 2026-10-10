"""Visible-game programme lane D, piece D2: the plate lattice and the plate polygons
(docs/northstar/plans/2026-10-07-visible-game-spec.md rev 4, lane D; docs/northstar/plans/preflight_2026-10-07/5-space-kit.md;
the generator scenes/mockups/landscape/field_map_space.gd). Fenced: builders never edit this file.

Proves S-246 R-246-01 (each layer a sheet of plates, the generator ported into the simulation; Q-STAGE3-03 b), R-246-03
(the polygons the client draws, Q-166-06 b: masks plus polygons) and E-01 R-001-04 (a binary mask per layer), through the
frozen K-d getters only: om_space_field_generate_nodes, om_space_field_get_mask, om_space_field_poly_count and
om_space_field_poly_get (csrc/ouroboros_sim.h). The tunables are read off the output, because the contract has no setter:
  plate_cell_wu 1600   plate size scale                 -> polygon area and count per layer
  size_spread 0.6      some plates large, some small     -> the spread of plate areas
  density_swing 0.8    packed and open areas              -> blocked share varies across a layer
  shared_density true  one density field for all layers   -> the same areas are packed on every layer
  kinds plate / mass / rubble (0 / 1 / 2) on polygons     -> counts and shape
The mockup is a statistical reference, not a byte reference (pre-flight 5: float32 and a 241-point grid), so every band
below is a named draft (D2_* constants) measured on the mockup at seeds 11, 12 (see "Calibration"), widened to leave the C
port room; a threshold widening later needs Westley.

Not provable here, reported in the hand-off instead: layer_gap_wu 1000 (a drawing offset on the client's 3D axis; the sim
frame has only x, y per polygon); small_share 7.5 (small-craft sections are not exposed by any K-d getter and the small
craft is Q-166-05, outside D); sections, tunnels, walls, crossings (later D pieces); reachability (the carve piece).

Calibration (mockup, density 35, canvas 24000): see the constants' comments.
On main the generator body is the K-d placeholder (4 rectangles per layer), so the count, size, spread and density
tests fail; shape tests may pass on the stub and guard the port.
"""
import ctypes
import math

import pytest

W = ctypes.c_void_p
U8P = ctypes.POINTER(ctypes.c_uint8)
F64P = ctypes.POINTER(ctypes.c_double)
U32P = ctypes.POINTER(ctypes.c_uint32)
CANVAS = 24000.0
N = 240
CELLS = N * N
LAYERS = 5
SEEDS = (11, 12, 13)
PLATE_CELL_WU = 1600.0  # R-246-01 / mockup PLATE_CELL_WU
CHANNEL_WU = 160.0  # mockup CHANNEL_WU: the gap between two plates
KIND_PLATE, KIND_MASS, KIND_RUBBLE = 0, 1, 2
CAP_PTS = 64  # a buffer far above any plate's vertex count
EPS_WU = 1.0

# ---- named drafts (Westley owns every threshold; see the module docstring) ----
D2_POLYS_PER_LAYER = (190, 530)  # pre-flight 5 "190 to 530 per layer at pass 3" (mockup: 417 to 496)
D2_MAX_PTS = 16  # a cell polygon is a square cut by bisectors; nothing near this many sides
D2_MEDIAN_PLATE_AREA_CELLS = (0.15, 1.2)  # mockup: 0.29 to 0.65  # median plate-kind area as a share of plate_cell_wu squared
D2_SPREAD_P90_OVER_P10_MIN = 3.0  # size_spread: p90 area over p10 area, plate kind (mockup: 7 to 54)
D2_P10_PLATE_MAX_CELLS = 0.3  # small floes: the 10th-percentile plate is under this many cells (mockup: 0.12)
D2_LARGEST_OVER_MEDIAN_MIN = 2.0  # large floes: the largest plate is at least this many times the median (mockup: 2.3 to 3)
D2_MIN_GAP_WU = 0.5 * CHANNEL_WU  # a neighbour pair closer than half a channel counts as touching (mockup gaps are 160)
D2_NEAR_WU = 400.0  # plate pairs this close are neighbours
D2_TOUCHING_MAX = 0.05  # share of neighbour pairs closer than D2_MIN_GAP_WU (mockup 0.012 to 0.017)
D2_SLIVER_CELLS = 0.01  # polygons under this many cells are slivers: the mockup emits a few of near-zero area; left out of the gap test
D2_CENTROID_BLOCKED_MIN = 0.80  # share of polygon centroids that sit in a blocked mask cell (carve opens some; mockup 0.86 to 0.90)
D2_UNCOVERED_BLOCKED_MAX = 0.20  # share of blocked cells no polygon covers (pockets, grid-edge cells; mockup 0.10 to 0.12)
D2_BLOCK_SIDE = 4  # density areas: a 4 x 4 grid of blocks, 6000 wu each
D2_SWING_MIN = 0.15  # density_swing: (max - min) blocked share over the blocks of a layer (mockup 0.26 to 0.42)
D2_SHARED_CORR_MIN = 0.45  # shared_density: mean pairwise correlation of block shares between layers (mockup 0.71 to 0.81)
D2_LAYER_SAME_MAX = 0.75  # two layers are separate sheets: at most this share of their blocked cells coincide (mockup max 0.46)
D2_MASS_PER_LAYER_MAX = 24  # a mass is a cluster of polygons (mockup: 4 to 16 on a layer that has one)
NEW = ["om_space_field_generate_nodes", "om_space_field_get_mask", "om_space_field_poly_count", "om_space_field_poly_get"]


def bind(lib):
    missing = [n for n in NEW if not hasattr(lib, n)]
    assert not missing, f"K-d symbols missing from libouroboros.so: {missing}"
    g = lib.om_space_field_generate_nodes
    g.argtypes, g.restype = [W, ctypes.c_uint32, ctypes.c_double, ctypes.c_double, ctypes.c_double, ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_uint32), ctypes.c_uint32], ctypes.c_int
    m = lib.om_space_field_get_mask
    m.argtypes, m.restype = [W, ctypes.c_uint32, U8P, ctypes.c_uint32], ctypes.c_uint32
    c = lib.om_space_field_poly_count
    c.argtypes, c.restype = [W], ctypes.c_uint32
    p = lib.om_space_field_poly_get
    p.argtypes, p.restype = [W, ctypes.c_uint32, U32P, U32P, F64P, ctypes.c_uint32], ctypes.c_uint32
    return g


def make_world(lib, world_factory):
    w = world_factory(n_regions=1)
    assert lib.om_map_set_canvas(w, CANVAS, CANVAS) == 0
    return w


def read_polys(lib, w):
    """[(layer, kind, [(x, y), ...])] for every polygon."""
    out = []
    for i in range(lib.om_space_field_poly_count(w)):
        layer, kind = ctypes.c_uint32(), ctypes.c_uint32()
        xy = (ctypes.c_double * (2 * CAP_PTS))()
        n = lib.om_space_field_poly_get(w, i, ctypes.byref(layer), ctypes.byref(kind), xy, CAP_PTS)
        assert n > 0, f"polygon {i}: poly_get returned 0 with a {CAP_PTS}-point buffer"
        out.append((layer.value, kind.value, [(xy[2 * j], xy[2 * j + 1]) for j in range(n)]))
    return out


def read_masks(lib, w):
    out = []
    for k in range(LAYERS):
        buf = (ctypes.c_uint8 * CELLS)()
        assert lib.om_space_field_get_mask(w, k, buf, CELLS) == CELLS
        out.append(bytes(buf))
    return out


_CACHE = {}


def field(lib, world_factory, seed):
    """(polys, masks) of one seed, generated once per session."""
    if seed not in _CACHE:
        g = bind(lib)
        w = make_world(lib, world_factory)
        assert g(w, seed, CANVAS, CANVAS, 35.0, None, None, 0) == 0
        _CACHE[seed] = (read_polys(lib, w), read_masks(lib, w))
    return _CACHE[seed]


# ---- geometry (every detector below has a positive control) ----
def area(pts):
    return 0.5 * sum(pts[i][0] * pts[(i + 1) % len(pts)][1] - pts[(i + 1) % len(pts)][0] * pts[i][1] for i in range(len(pts)))


def centroid(pts):
    return sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts)


def _cross(o, a, b):
    return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])


def is_simple_ccw(pts):
    """Counter-clockwise (positive area) with no two non-adjacent edges crossing. Not convex: the kit pulls each corner in
    by its own hashed share, so a few corners are slightly reflex (mockup: 206 of 2300 at seed 11)."""
    n = len(pts)
    if area(pts) <= 0:
        return False
    for i in range(n):
        for j in range(i + 2, n):
            if i == 0 and j == n - 1:
                continue
            a, b, c, d = pts[i], pts[(i + 1) % n], pts[j], pts[(j + 1) % n]
            if _cross(a, b, c) * _cross(a, b, d) < 0 and _cross(c, d, a) * _cross(c, d, b) < 0:
                return False
    return True


def penetration(a, b):
    """Smallest overlap depth of two (near-convex) polygons over their edge normals (<= 0 when they do not overlap)."""
    depth = math.inf
    for poly in (a, b):
        for i in range(len(poly)):
            ex, ey = poly[(i + 1) % len(poly)][0] - poly[i][0], poly[(i + 1) % len(poly)][1] - poly[i][1]
            ln = math.hypot(ex, ey) or 1.0
            nx, ny = ey / ln, -ex / ln
            pa = [p[0] * nx + p[1] * ny for p in a]
            pb = [p[0] * nx + p[1] * ny for p in b]
            depth = min(depth, min(max(pa), max(pb)) - max(min(pa), min(pb)))
    return depth


def seg_dist(p, a, b):
    ax, ay, bx, by = a[0], a[1], b[0], b[1]
    dx, dy = bx - ax, by - ay
    t = 0.0 if dx == dy == 0 else max(0.0, min(1.0, ((p[0] - ax) * dx + (p[1] - ay) * dy) / (dx * dx + dy * dy)))
    return math.hypot(p[0] - ax - t * dx, p[1] - ay - t * dy)


def poly_gap(a, b):
    """Distance between two disjoint convex polygons (vertex to edge both ways)."""
    best = math.inf
    for p, q in ((a, b), (b, a)):
        for v in p:
            for i in range(len(q)):
                best = min(best, seg_dist(v, q[i], q[(i + 1) % len(q)]))
    return best


def bbox(pts):
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    return min(xs), min(ys), max(xs), max(ys)


def point_in(pts, x, y):
    inside = False
    n = len(pts)
    for i in range(n):
        a, b = pts[i], pts[(i + 1) % n]
        if (a[1] <= y < b[1]) or (b[1] <= y < a[1]):
            if x < a[0] + (y - a[1]) / (b[1] - a[1]) * (b[0] - a[0]):
                inside = not inside
    return inside


def covered_cells(polys_of_layer):
    """Cell indices whose centre lies inside any polygon."""
    out = set()
    for pts in polys_of_layer:
        x0, y0, x1, y1 = bbox(pts)
        for cy in range(max(0, int(y0 // 100)), min(N - 1, int(y1 // 100)) + 1):
            for cx in range(max(0, int(x0 // 100)), min(N - 1, int(x1 // 100)) + 1):
                if point_in(pts, (cx + .5) * 100.0, (cy + .5) * 100.0):
                    out.add(cy * N + cx)
    return out


def block_shares(mask):
    """Blocked share of each block of the D2_BLOCK_SIDE x D2_BLOCK_SIDE grid."""
    s = N // D2_BLOCK_SIDE
    out = []
    for by in range(D2_BLOCK_SIDE):
        for bx in range(D2_BLOCK_SIDE):
            tot = sum(sum(mask[(by * s + y) * N + bx * s: (by * s + y) * N + bx * s + s]) for y in range(s))
            out.append(tot / (s * s))
    return out


def pearson(a, b):
    ma, mb = sum(a) / len(a), sum(b) / len(b)
    va, vb = sum((x - ma) ** 2 for x in a), sum((y - mb) ** 2 for y in b)
    if va == 0 or vb == 0:
        return 0.0
    return sum((x - ma) * (y - mb) for x, y in zip(a, b)) / math.sqrt(va * vb)


def by_layer(polys):
    return [[p for p in polys if p[0] == k] for k in range(LAYERS)]


def plate_areas(polys, k):
    return sorted(area(p[2]) for p in polys if p[0] == k and p[1] == KIND_PLATE)


def quantile(sorted_vals, q):
    return sorted_vals[min(len(sorted_vals) - 1, int(q * len(sorted_vals)))]


SQ = [(0.0, 0.0), (10.0, 0.0), (10.0, 10.0), (0.0, 10.0)]


def shifted(sq, dx, dy):
    return [(x + dx, y + dy) for x, y in sq]


# ---- positive controls ----
def test_control_geometry_detectors():
    assert area(SQ) == 100.0 and is_simple_ccw(SQ)
    assert is_simple_ccw([(0, 0), (10, 0), (5, 2), (10, 10), (0, 10)]), "a reflex corner was refused"
    assert not is_simple_ccw(SQ[::-1]), "clockwise accepted"
    assert not is_simple_ccw([(0, 0), (10, 10), (10, 0), (0, 10)]), "a bow-tie accepted"
    assert penetration(SQ, shifted(SQ, 5, 5)) > 0, "overlap not seen"
    assert penetration(SQ, shifted(SQ, 25, 0)) < 0, "separate squares seen as overlapping"
    assert abs(poly_gap(SQ, shifted(SQ, 25, 0)) - 15.0) < 1e-9
    assert point_in(SQ, 5, 5) and not point_in(SQ, 15, 5)


def test_control_coverage_and_correlation():
    sq = [(1000.0, 1000.0), (1500.0, 1000.0), (1500.0, 1500.0), (1000.0, 1500.0)]
    cells = covered_cells([sq])
    assert len(cells) == 25 and (10 * N + 10) in cells and (15 * N + 15) not in cells
    flat = bytes(CELLS)
    half = bytes([1] * (CELLS // 2)) + bytes(CELLS // 2)
    assert max(block_shares(half)) - min(block_shares(half)) == 1.0
    assert max(block_shares(flat)) - min(block_shares(flat)) == 0.0
    xs = [0.1, 0.5, 0.2, 0.9]
    assert pearson(xs, xs) > 0.999 and pearson(xs, [1 - x for x in xs]) < -0.999 and pearson(xs, [1] * 4) == 0.0


# ---- the contract surface ----
def test_symbols_present_and_bind(lib):
    bind(lib)


def test_no_polygons_before_generate_and_bounds(lib, world_factory):
    bind(lib)
    w = make_world(lib, world_factory)
    assert lib.om_space_field_poly_count(w) == 0
    layer, kind = ctypes.c_uint32(), ctypes.c_uint32()
    xy = (ctypes.c_double * (2 * CAP_PTS))()
    assert lib.om_space_field_poly_get(w, 0, ctypes.byref(layer), ctypes.byref(kind), xy, CAP_PTS) == 0
    assert lib.om_space_field_generate_nodes(w, SEEDS[0], CANVAS, CANVAS, 35.0, None, None, 0) == 0
    n = lib.om_space_field_poly_count(w)
    assert n > 0
    assert lib.om_space_field_poly_get(w, n, ctypes.byref(layer), ctypes.byref(kind), xy, CAP_PTS) == 0, "index == count answered"
    assert lib.om_space_field_poly_get(w, 0, ctypes.byref(layer), ctypes.byref(kind), xy, 2) == 0, "a 2-point buffer was accepted"


# ---- plate polygons per layer, kinds ----
@pytest.mark.parametrize("seed", SEEDS)
def test_every_layer_has_a_lattice_of_polygons(lib, world_factory, seed):
    """R-246-01 / plate_cell_wu 1600: a 24000 wu layer holds a lattice of hundreds of plate polygons (a coarse lattice
    would hold tens, as the K-d placeholder's four)."""
    polys, _ = field(lib, world_factory, seed)
    lo, hi = D2_POLYS_PER_LAYER
    counts = [len(p) for p in by_layer(polys)]
    assert all(lo <= c <= hi for c in counts), f"polygons per layer {counts}, expected {lo}..{hi} (D2_POLYS_PER_LAYER)"
    assert all(0 <= p[0] < LAYERS for p in polys)


@pytest.mark.parametrize("seed", SEEDS)
def test_kinds_are_plate_mass_rubble(lib, world_factory, seed):
    polys, _ = field(lib, world_factory, seed)
    assert {p[1] for p in polys} <= {KIND_PLATE, KIND_MASS, KIND_RUBBLE}
    for k, lp in enumerate(by_layer(polys)):
        kinds = [p[1] for p in lp]
        assert kinds.count(KIND_PLATE) >= 80, f"layer {k}: {kinds.count(KIND_PLATE)} plate polygons (mockup 112 to 176)"
        assert kinds.count(KIND_RUBBLE) >= 100, f"layer {k}: {kinds.count(KIND_RUBBLE)} rubble polygons (mockup 253 to 358: rubble gathers on dropped plates)"
        assert kinds.count(KIND_MASS) <= D2_MASS_PER_LAYER_MAX, f"layer {k}: {kinds.count(KIND_MASS)} mass polygons (D2_MASS_PER_LAYER_MAX)"
    assert any(p[1] == KIND_MASS for p in polys), "no mass polygon on any layer (MASS_CHANCE 0.5 per layer; the mockup has one on 1 to 4 of 5)"


@pytest.mark.parametrize("seed", SEEDS)
def test_polygons_are_simple_ccw_inside_the_canvas(lib, world_factory, seed):
    polys, _ = field(lib, world_factory, seed)
    bad = []
    for i, (k, kind, pts) in enumerate(polys):
        ok = 3 <= len(pts) <= D2_MAX_PTS and is_simple_ccw(pts)
        ok = ok and all(math.isfinite(x) and math.isfinite(y) and -EPS_WU <= x <= CANVAS + EPS_WU and -EPS_WU <= y <= CANVAS + EPS_WU for x, y in pts)
        if not ok:
            bad.append((i, k, kind, len(pts)))
    assert not bad, f"{len(bad)} polygons not simple counter-clockwise, 3..{D2_MAX_PTS} points, on the canvas; first {bad[:3]}"


# ---- plate size: plate_cell_wu and size_spread ----
@pytest.mark.parametrize("seed", SEEDS)
def test_plate_size_follows_the_lattice_cell(lib, world_factory, seed):
    """plate_cell_wu 1600: the median plate-kind polygon is a fraction of one 1600 wu cell (pulled in by half a channel)."""
    polys, _ = field(lib, world_factory, seed)
    lo, hi = D2_MEDIAN_PLATE_AREA_CELLS
    for k in range(LAYERS):
        a = plate_areas(polys, k)
        assert a, f"layer {k}: no plate-kind polygon"
        med = quantile(a, 0.5) / PLATE_CELL_WU ** 2
        assert lo <= med <= hi, f"layer {k}: median plate area {med:.3f} cells, expected {lo}..{hi} (D2_MEDIAN_PLATE_AREA_CELLS)"


@pytest.mark.parametrize("seed", SEEDS)
def test_size_spread_makes_large_and_small_floes(lib, world_factory, seed):
    """size_spread 0.6: the lowest size values are removed (a large floe takes the area), the highest split in four."""
    polys, _ = field(lib, world_factory, seed)
    for k in range(LAYERS):
        a = plate_areas(polys, k)
        cell2 = PLATE_CELL_WU ** 2
        assert quantile(a, 0.1) / cell2 <= D2_P10_PLATE_MAX_CELLS, f"layer {k}: p10 plate {quantile(a, 0.1) / cell2:.3f} cells, no small floes (D2_P10_PLATE_MAX_CELLS)"
        assert a[-1] >= D2_LARGEST_OVER_MEDIAN_MIN * quantile(a, 0.5), f"layer {k}: largest plate {a[-1] / quantile(a, 0.5):.2f} x the median, no large floe (D2_LARGEST_OVER_MEDIAN_MIN)"
        assert quantile(a, 0.9) / quantile(a, 0.1) >= D2_SPREAD_P90_OVER_P10_MIN, f"layer {k}: p90/p10 {quantile(a, 0.9) / quantile(a, 0.1):.2f}"


@pytest.mark.parametrize("seed", SEEDS)
def test_plates_do_not_overlap_and_keep_a_channel(lib, world_factory, seed):
    """The gap between two plates is one channel wide (mockup CHANNEL_WU 160): no two plate polygons of one layer overlap,
    and of the pairs within 400 wu of each other only a few touch (the mockup has 1 to 2 percent: its split floes)."""
    polys, _ = field(lib, world_factory, seed)
    worst_overlap, near, touching = -math.inf, 0, 0
    for lp in by_layer(polys):
        plates = [(bbox(p[2]), p[2]) for p in lp if p[1] == KIND_PLATE and area(p[2]) >= D2_SLIVER_CELLS * PLATE_CELL_WU ** 2]
        for i in range(len(plates)):
            for j in range(i + 1, len(plates)):
                (a0, a1, a2, a3), pa = plates[i]
                (b0, b1, b2, b3), pb = plates[j]
                if a2 + D2_NEAR_WU < b0 or b2 + D2_NEAR_WU < a0 or a3 + D2_NEAR_WU < b1 or b3 + D2_NEAR_WU < a1:
                    continue
                d = penetration(pa, pb)
                if d > 0:
                    worst_overlap = max(worst_overlap, d)
                    continue
                g = poly_gap(pa, pb)
                if g < D2_NEAR_WU:
                    near += 1
                    touching += g < D2_MIN_GAP_WU
    assert worst_overlap <= EPS_WU, f"two plates overlap by {worst_overlap:.1f} wu"
    assert near > 100, f"only {near} plate pairs within {D2_NEAR_WU} wu: no lattice"
    assert touching / near <= D2_TOUCHING_MAX, f"{touching}/{near} near plate pairs closer than {D2_MIN_GAP_WU} wu (D2_TOUCHING_MAX {D2_TOUCHING_MAX})"


# ---- polygons and masks agree (R-246-03: the picture and the play data are one thing) ----
@pytest.mark.parametrize("seed", SEEDS[:2])
def test_polygons_and_masks_agree(lib, world_factory, seed):
    polys, masks = field(lib, world_factory, seed)
    for k, lp in enumerate(by_layer(polys)):
        pts = [p[2] for p in lp]
        inside = sum(1 for p in pts if masks[k][min(N - 1, int(centroid(p)[1] // 100)) * N + min(N - 1, int(centroid(p)[0] // 100))])
        assert inside / len(pts) >= D2_CENTROID_BLOCKED_MIN, f"layer {k}: {inside}/{len(pts)} polygon centroids in blocked cells (D2_CENTROID_BLOCKED_MIN)"
        cov = covered_cells(pts)
        blocked = [i for i in range(CELLS) if masks[k][i]]
        assert blocked, f"layer {k}: nothing blocked"
        unc = sum(1 for i in blocked if i not in cov) / len(blocked)
        assert unc <= D2_UNCOVERED_BLOCKED_MAX, f"layer {k}: {unc:.3f} of blocked cells under no polygon (D2_UNCOVERED_BLOCKED_MAX)"


# ---- density_swing and shared_density ----
@pytest.mark.parametrize("seed", SEEDS)
def test_density_swings_across_a_layer(lib, world_factory, seed):
    """density_swing 0.8: some areas are packed and some open, so the blocked share differs strongly between blocks."""
    _, masks = field(lib, world_factory, seed)
    for k in range(LAYERS):
        s = block_shares(masks[k])
        assert max(s) - min(s) >= D2_SWING_MIN, f"layer {k}: block shares {min(s):.2f}..{max(s):.2f} (D2_SWING_MIN {D2_SWING_MIN})"


@pytest.mark.parametrize("seed", SEEDS)
def test_shared_density_packs_the_same_areas_on_every_layer(lib, world_factory, seed):
    """shared_density true: one density field serves all layers, so a packed area is packed on every layer."""
    _, masks = field(lib, world_factory, seed)
    shares = [block_shares(m) for m in masks]
    corr = [pearson(shares[a], shares[b]) for a in range(LAYERS) for b in range(a + 1, LAYERS)]
    mean = sum(corr) / len(corr)
    assert mean >= D2_SHARED_CORR_MIN, f"mean block-share correlation between layers {mean:.2f} (D2_SHARED_CORR_MIN {D2_SHARED_CORR_MIN})"


@pytest.mark.parametrize("seed", SEEDS)
def test_layers_are_separate_sheets(lib, world_factory, seed):
    """Each layer has its own seed: the same density areas, but not the same plates (the mockup's coherent-layers plant is the failure)."""
    polys, masks = field(lib, world_factory, seed)
    for a in range(LAYERS):
        for b in range(a + 1, LAYERS):
            both = sum(1 for i in range(CELLS) if masks[a][i] and masks[b][i])
            either = sum(1 for i in range(CELLS) if masks[a][i] or masks[b][i])
            assert both / either <= D2_LAYER_SAME_MAX, f"layers {a} and {b}: {both / either:.2f} of blocked cells shared (D2_LAYER_SAME_MAX)"
    lp = by_layer(polys)
    sigs = [tuple(sorted((round(centroid(p[2])[0]), round(centroid(p[2])[1])) for p in layer)) for layer in lp]
    assert len(set(sigs)) == LAYERS, "two layers hold the same polygon set"


# ---- determinism and replacement ----
def test_same_seed_identical_polygons_and_seed_changes_them(lib, world_factory):
    g = bind(lib)
    a, b, c = (make_world(lib, world_factory) for _ in range(3))
    assert g(a, SEEDS[0], CANVAS, CANVAS, 35.0, None, None, 0) == 0 and g(b, SEEDS[0], CANVAS, CANVAS, 35.0, None, None, 0) == 0 and g(c, SEEDS[1], CANVAS, CANVAS, 35.0, None, None, 0) == 0
    pa, pb, pc = read_polys(lib, a), read_polys(lib, b), read_polys(lib, c)
    assert pa == pb, "same seed, different polygons"
    assert pa != pc, "seeds 11 and 12 gave identical polygons"


def test_regenerate_replaces_polygons(lib, world_factory):
    g = bind(lib)
    a, b = make_world(lib, world_factory), make_world(lib, world_factory)
    assert g(a, SEEDS[0], CANVAS, CANVAS, 35.0, None, None, 0) == 0 and g(a, SEEDS[1], CANVAS, CANVAS, 35.0, None, None, 0) == 0
    assert g(b, SEEDS[1], CANVAS, CANVAS, 35.0, None, None, 0) == 0
    assert read_polys(lib, a) == read_polys(lib, b), "a second generate left polygons of the first"
