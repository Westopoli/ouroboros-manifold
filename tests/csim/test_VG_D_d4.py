"""Visible-game programme lane D piece D4 (docs/northstar/plans/2026-10-07-visible-game-spec.md rev 4, lane D;
docs/northstar/plans/preflight_2026-10-07/5-space-kit.md). Fenced: builders never edit this file.

Proves S-246 (R-246-01 five open-or-blocked layers ported into the sim; R-246-03 masks plus polygons, Q-166-06 b),
E-01 R-001-04 (a binary mask per layer, written to the mapgen blocked bits), Q-STAGE3-03 b (the port; cross-layer
filling is the client's drawing, not tested here). D4 is the piece that runs D1 (noise), D2 (plates) and D3
(raster + carve) behind om_space_field_generate_nodes, writes the masks to blocked_bits per layer, makes cover from rubble
and keeps the polygons for the dump getters (K-d: om_space_field_poly_count / om_space_field_poly_get).

ASSUMED PROTOTYPES (the brief names the symbols; mismatches are contract questions for the Architect, not test defects):
  int om_space_field_generate_nodes(om_world*, uint32_t seed, double canvas_w, double canvas_h, double density)
      density 0..90 (the mockup's `generate(seed, canvas, density)`, default 35, clamped 0..90). QUESTION 1: main's
      K-d contract is the 4-argument form with no density; a density parameter changes a frozen signature (needs its
      own contract piece, and the call site om_pipe.c:1357). This file passes density as a fifth double argument; on
      main the extra argument is ignored. If the contract piece chooses a setter instead, only `gen` below changes.
  Plant (QUESTION 2): the positive control `space-no-carve` (skip the fill-and-carve join, as the mockup's
      QaPlants "space-no-carve" does) is assumed to be a debug-build bug id passed to om_debug_inject(w, bug) BEFORE
      om_space_field_generate_nodes. NO NUMBER IS GIVEN for it; NO_CARVE_BUG below is a named draft (above every id in
      csrc/ouroboros_sim.h on main, 1601). If the contract piece uses another id, change the one constant.
Everything else is main's K-d surface: om_space_field_present / _get_mask / _clear / _poly_count / _poly_get,
om_map_sample_layer_accessibility, om_map_cover_count / om_map_cover_at.

Reachability is the mockup's: mask opened with a 3 x 3 block (300 wu passage), six-neighbour flood fill (four in
plane, one up, one down), main region = the one holding layer 0 at the objective cell (120, 120); every other region
counts as unreachable (field_map_space.gd _open_block, _label_regions, regions_unreachable_after).

Threshold files: every Westley-threshold check (the blocked-share bands, polygon-coverage floor) is a test named
test_park_*; the landing clerk moves those to a *_park_* file per the spec's park rule (this brief allowed one file).
The band numbers are DRAFTS taken from docs/northstar/research/space_landscape/README.md (pass 3: 14 to 23 percent at
density 15; pass 6 widen mode, 6 seeds: 56 at density 55, 65 at density 70), widened by me to a +-5 point margin
around the measured value; Westley sets the real ones.
On main every generate-dependent test fails: the K-d placeholder paints four rectangles per layer (about 1 percent
blocked) at any density.
"""
import collections
import ctypes
import hashlib

import numpy as np
import pytest

W = ctypes.c_void_p
U8P = ctypes.POINTER(ctypes.c_uint8)
DBL = ctypes.POINTER(ctypes.c_double)
U32P = ctypes.POINTER(ctypes.c_uint32)
CANVAS = 24000.0
N = 240
CELLS = N * N
LAYERS = 5
SEEDS = (11, 12, 13, 14, 15, 16)
OBJ = (N // 2, N // 2)  # objective cell (cx, cy), canvas centre
MAX_PTS = 64  # poly_get buffer, points
NO_CARVE_BUG = 1700  # DRAFT id, see QUESTION 2
# DRAFT bands, fraction blocked, mean of the five layers, per seed (see the module note).
DRAFT_BANDS = {15: (0.12, 0.25), 55: (0.51, 0.61), 70: (0.60, 0.70)}
DRAFT_POLY_COVER_FLOOR = 0.90  # share of blocked cell centres inside some polygon of their layer
NONTRIVIAL_FLOOR = 0.10  # a map with less blocked than this is not a field (floor under DRAFT_BANDS[15])

_cache = {}


def bind(lib):
    needed = ["om_space_field_generate_nodes", "om_space_field_present", "om_space_field_get_mask", "om_space_field_clear",
              "om_space_field_poly_count", "om_space_field_poly_get", "om_map_cover_count", "om_map_cover_at"]
    missing = [n for n in needed if not hasattr(lib, n)]
    assert not missing, f"symbols missing from the library: {missing}"
    lib.om_space_field_generate_nodes.argtypes = [W, ctypes.c_uint32, ctypes.c_double, ctypes.c_double, ctypes.c_double, ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_uint32), ctypes.c_uint32]
    lib.om_space_field_generate_nodes.restype = ctypes.c_int
    lib.om_space_field_present.argtypes, lib.om_space_field_present.restype = [W], ctypes.c_int
    lib.om_space_field_get_mask.argtypes = [W, ctypes.c_uint32, U8P, ctypes.c_uint32]
    lib.om_space_field_get_mask.restype = ctypes.c_uint32
    lib.om_space_field_clear.argtypes, lib.om_space_field_clear.restype = [W], None
    lib.om_space_field_poly_count.argtypes, lib.om_space_field_poly_count.restype = [W], ctypes.c_uint32
    lib.om_space_field_poly_get.argtypes = [W, ctypes.c_uint32, U32P, U32P, DBL, ctypes.c_uint32]
    lib.om_space_field_poly_get.restype = ctypes.c_uint32
    lib.om_map_cover_count.argtypes, lib.om_map_cover_count.restype = [W], ctypes.c_uint32
    lib.om_map_cover_at.argtypes = [W, ctypes.c_uint32, DBL, DBL, DBL, DBL]
    lib.om_map_cover_at.restype = ctypes.c_int
    lib.om_map_set_canvas.argtypes = [W, ctypes.c_double, ctypes.c_double]
    lib.om_map_sample_layer_accessibility.argtypes = [W, ctypes.c_double, ctypes.c_double, ctypes.c_uint32]
    lib.om_map_sample_layer_accessibility.restype = ctypes.c_int


def make_world(lib, factory):
    bind(lib)
    w = factory(n_regions=1)
    assert lib.om_map_set_canvas(w, CANVAS, CANVAS) == 0
    return w


def gen(lib, w, seed, density):
    return lib.om_space_field_generate_nodes(w, seed, CANVAS, CANVAS, float(density), None, None, 0, None, None, 0)


def read_masks(lib, w):
    """(5, 240, 240) bool array, True = blocked (the blocked_bits sense)."""
    out = np.zeros((LAYERS, N, N), dtype=bool)
    for k in range(LAYERS):
        buf = (ctypes.c_uint8 * CELLS)()
        assert lib.om_space_field_get_mask(w, k, buf, CELLS) == CELLS, f"layer {k}: get_mask refused"
        out[k] = np.frombuffer(bytes(buf), dtype=np.uint8).reshape(N, N) != 0
    return out


def read_polys(lib, w):
    """[(layer, kind, np.array of shape (n, 2))]."""
    polys = []
    for i in range(lib.om_space_field_poly_count(w)):
        layer, kind = ctypes.c_uint32(), ctypes.c_uint32()
        xy = (ctypes.c_double * (2 * MAX_PTS))()
        n = lib.om_space_field_poly_get(w, i, ctypes.byref(layer), ctypes.byref(kind), xy, MAX_PTS)
        assert n >= 3, f"poly {i}: poly_get returned {n} points (a polygon needs 3, buffer holds {MAX_PTS})"
        polys.append((layer.value, kind.value, np.array(xy[:2 * n]).reshape(n, 2)))
    return polys


def field(lib, factory, seed, density):
    """Masks and polygons of (seed, density), cached; uses a fresh world that the factory frees."""
    key = (seed, density)
    if key not in _cache:
        w = make_world(lib, factory)
        assert gen(lib, w, seed, density) == 0
        _cache[key] = (read_masks(lib, w), read_polys(lib, w))
    return _cache[key]


def field_hash(masks, polys):
    h = hashlib.sha256()
    for k in range(LAYERS):
        h.update(np.packbits(masks[k]).tobytes())
    for layer, kind, pts in polys:
        h.update(bytes([layer, kind]))
        h.update(np.round(pts * 1000).astype(np.int64).tobytes())
    return h.hexdigest()


def open_block3(open_):
    """The mockup's _open_block(.., 3): erode with a 3 x 3 block (edge cells are never kept), dilate with 3 x 3."""
    e = np.zeros_like(open_)
    e[:, 1:-1, 1:-1] = np.ones((LAYERS, N - 2, N - 2), dtype=bool)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            e[:, 1:-1, 1:-1] &= open_[:, 1 + dy:N - 1 + dy, 1 + dx:N - 1 + dx]
    d = np.zeros_like(open_)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            ys, yd = (slice(max(dy, 0), N + min(dy, 0)), slice(max(-dy, 0), N + min(-dy, 0)))
            xs, xd = (slice(max(dx, 0), N + min(dx, 0)), slice(max(-dx, 0), N + min(-dx, 0)))
            d[:, ys, xs] |= e[:, yd, xd]
    return d


def unreachable_regions(blocked):
    """Regions of the ordinary-passage open mask other than the one holding layer 0 at the objective cell."""
    op = open_block3(~blocked)
    flat = op.reshape(-1)
    lab = np.full(flat.size, -1, dtype=np.int32)
    n_regions = 0
    main = -1
    anchor = 0 * CELLS + OBJ[1] * N + OBJ[0]
    for start in np.flatnonzero(flat):
        if lab[start] != -1:
            continue
        lab[start] = n_regions
        stack = collections.deque([start])
        while stack:
            c = stack.pop()
            k, p = divmod(c, CELLS)
            y, x = divmod(p, N)
            for ok, nb in ((x > 0, c - 1), (x < N - 1, c + 1), (y > 0, c - N), (y < N - 1, c + N),
                           (k > 0, c - CELLS), (k < LAYERS - 1, c + CELLS)):
                if ok and flat[nb] and lab[nb] == -1:
                    lab[nb] = n_regions
                    stack.append(nb)
        n_regions += 1
    if lab[anchor] != -1:
        main = lab[anchor]
    return n_regions - (1 if main >= 0 else 0)


def points_in_polygon(pts, poly):
    """Even-odd ray cast of an (m, 2) point array against a polygon (n, 2)."""
    px, py = pts[:, 0], pts[:, 1]
    inside = np.zeros(len(pts), dtype=bool)
    j = len(poly) - 1
    for i in range(len(poly)):
        xi, yi, xj, yj = poly[i, 0], poly[i, 1], poly[j, 0], poly[j, 1]
        if yi != yj:
            cross = ((yi > py) != (yj > py)) & (px < (xj - xi) * (py - yi) / (yj - yi) + xi)
            inside ^= cross
        j = i
    return inside


def mean_share(masks):
    return float(masks.mean())


# ---- positive controls for the detectors ---------------------------------------------------------------------

def test_control_unreachable_regions_counts_planted_pocket():
    """Positive control: an all-open field has 0 unreachable regions; a 7 x 7 pocket ringed by blocked cells on all
    five layers has 1; a pocket joined to the main region by a 1-cell corridor is still 1 (300 wu passage rule)."""
    blocked = np.zeros((LAYERS, N, N), dtype=bool)
    assert unreachable_regions(blocked) == 0
    blocked[:, 20:29, 20:29] = True
    blocked[:, 21:28, 21:28] = False
    assert unreachable_regions(blocked) == 1
    blocked[:, 24, 10:21] = False  # corridor 1 cell wide from the pocket's ring to open space
    assert unreachable_regions(blocked) == 1


def test_control_points_in_polygon():
    """Positive control for points_in_polygon: a unit square contains its centre, not an outside point."""
    sq = np.array([[0.0, 0.0], [10.0, 0.0], [10.0, 10.0], [0.0, 10.0]])
    got = points_in_polygon(np.array([[5.0, 5.0], [15.0, 5.0], [5.0, -1.0]]), sq)
    assert got.tolist() == [True, False, False]


def test_control_share_and_hash_detect_a_change():
    """Positive control for mean_share and field_hash: planted blocked cells move both."""
    a = np.zeros((LAYERS, N, N), dtype=bool)
    b = a.copy()
    b[2, 10:30, 10:30] = True
    assert mean_share(a) == 0.0 and mean_share(b) > 0.0
    assert field_hash(a, []) != field_hash(b, [])
    assert field_hash(a, []) == field_hash(a.copy(), [])


# ---- generate: R-246-01, R-001-04 -----------------------------------------------------------------------------

def test_generate_returns_ok_and_field_is_present(lib, world_factory):
    w = make_world(lib, world_factory)
    assert not lib.om_space_field_present(w)
    assert gen(lib, w, 11, 35) == 0
    assert lib.om_space_field_present(w) == 1


def test_density_changes_the_field_and_is_monotone(lib, world_factory):
    """R-246-01 'one dial': a heavier density blocks more, on every seed 11 to 16 (mean of five layers)."""
    for seed in SEEDS:
        shares = [mean_share(field(lib, world_factory, seed, d)[0]) for d in (15, 35, 55, 70)]
        assert shares == sorted(shares) and len(set(shares)) == 4, f"seed {seed}: shares by density 15/35/55/70 = {shares}"


def test_every_layer_has_open_and_blocked_cells(lib, world_factory):
    masks, _ = field(lib, world_factory, 11, 35)
    for k in range(LAYERS):
        assert masks[k].any() and not masks[k].all(), f"layer {k}: blocked share {masks[k].mean():.3f}"


def test_layers_differ_but_are_not_independent(lib, world_factory):
    """Five sheets, not one plane copied (layers differ), and the shared density keeps stacked blocked cells common:
    the share of cells blocked on layer k and k + 1 is above what independent layers would give."""
    masks, _ = field(lib, world_factory, 11, 55)
    assert any((masks[k] != masks[k + 1]).any() for k in range(LAYERS - 1)), "all layers identical"
    for k in range(LAYERS - 1):
        both = float((masks[k] & masks[k + 1]).mean())
        indep = float(masks[k].mean() * masks[k + 1].mean())
        assert both > indep, f"layers {k},{k + 1}: stacked blocked {both:.3f} not above independent {indep:.3f}"


def test_objective_cell_is_open_on_layer_zero_every_density(lib, world_factory):
    """The reachability anchor and the layout clear radius: the canvas centre cell is open on layer 0."""
    for seed in SEEDS:
        for d in (15, 35, 55, 70):
            masks, _ = field(lib, world_factory, seed, d)
            assert not masks[0][OBJ[1], OBJ[0]], f"seed {seed} density {d}: objective cell blocked on layer 0"


# ---- blocked_bits written per layer ----------------------------------------------------------------------------

def test_blocked_bits_match_mask_per_layer(lib, world_factory):
    """R-246-01 'masks written to blocked_bits per layer': routing's accessibility sample agrees with get_mask, and
    is read per layer (cells that differ between layers are sampled on both)."""
    w = make_world(lib, world_factory)
    assert gen(lib, w, 11, 35) == 0
    masks = read_masks(lib, w)
    diff = np.argwhere(masks[0] != masks[3])
    assert len(diff) > 100, "layers 0 and 3 barely differ, nothing to prove per-layer writing"
    bad = []
    for cy, cx in diff[::max(1, len(diff) // 400)]:
        for k in (0, 3):
            got = lib.om_map_sample_layer_accessibility(w, (cx + .5) * 100.0, (cy + .5) * 100.0, k)
            if got != (0 if masks[k][cy, cx] else 1):
                bad.append((k, int(cx), int(cy)))
    assert not bad, f"{len(bad)} per-layer disagreements, first {bad[:3]}"


def test_regenerate_leaves_no_stale_blocked_bits(lib, world_factory):
    """A second generate replaces the first in the field and in routing: world A (seed 11 then 12) equals world B (12)."""
    a, b = make_world(lib, world_factory), make_world(lib, world_factory)
    assert gen(lib, a, 11, 70) == 0 and gen(lib, a, 12, 15) == 0 and gen(lib, b, 12, 15) == 0
    assert (read_masks(lib, a) == read_masks(lib, b)).all()
    bad = 0
    for k in range(LAYERS):
        for cy in range(0, N, 5):
            for cx in range(0, N, 5):
                x, y = (cx + .5) * 100.0, (cy + .5) * 100.0
                bad += lib.om_map_sample_layer_accessibility(a, x, y, k) != lib.om_map_sample_layer_accessibility(b, x, y, k)
    assert bad == 0, f"{bad} sampled cells where the replaced world routes differently from a fresh one"


def test_clear_removes_field(lib, world_factory):
    w = make_world(lib, world_factory)
    assert gen(lib, w, 11, 35) == 0
    lib.om_space_field_clear(w)
    assert lib.om_space_field_present(w) == 0 and lib.om_space_field_poly_count(w) == 0


# ---- cover from rubble -----------------------------------------------------------------------------------------

# ---- dump getters (K-d): R-246-03 -------------------------------------------------------------------------------

def test_poly_dump_shape(lib, world_factory):
    """Masks plus polygons (Q-166-06 b): every layer has polygons of kinds 0 to 2 (plate, mass, rubble), three or
    more points each, inside the canvas (a small margin for the skirt), counter-clockwise (area > 0)."""
    _, polys = field(lib, world_factory, 11, 35)
    assert polys, "no polygons kept for the dump"
    per_layer = collections.Counter(p[0] for p in polys)
    assert set(per_layer) == set(range(LAYERS)), f"polygons by layer: {dict(per_layer)}"
    assert {p[1] for p in polys} <= {0, 1, 2} and {0, 2} <= {p[1] for p in polys}
    for layer, kind, pts in polys:
        assert pts.min() >= -600.0 and pts.max() <= CANVAS + 600.0, (layer, kind, pts.min(), pts.max())
        x, y = pts[:, 0], pts[:, 1]
        area2 = float(np.dot(x, np.roll(y, -1)) - np.dot(np.roll(x, -1), y))
        assert area2 > 0.0, f"layer {layer} kind {kind}: not counter-clockwise (twice area {area2})"


def test_poly_get_bounds(lib, world_factory):
    w = make_world(lib, world_factory)
    bind(lib)
    assert lib.om_space_field_poly_count(w) == 0
    assert gen(lib, w, 11, 35) == 0
    n = lib.om_space_field_poly_count(w)
    xy = (ctypes.c_double * (2 * MAX_PTS))()
    assert lib.om_space_field_poly_get(w, n, None, None, xy, MAX_PTS) == 0, "index past the end"
    assert lib.om_space_field_poly_get(w, 0, None, None, xy, 2) == 0, "buffer smaller than the polygon"
    assert lib.om_space_field_poly_get(w, 0, None, None, xy, MAX_PTS) >= 3


def test_polygon_count_is_a_real_field_not_the_placeholder(lib, world_factory):
    """The K-d placeholder keeps 20 rectangles; the port keeps hundreds per layer (pass 3: 190 to 530 at density 35 to
    70). Floor only: more than 20 per layer on average and a total above the placeholder cap of 64."""
    _, polys = field(lib, world_factory, 11, 35)
    assert len(polys) > 64 and len(polys) / LAYERS > 20, f"{len(polys)} polygons"


# ---- determinism ------------------------------------------------------------------------------------------------

def test_hash_stable_per_seed_two_worlds(lib, world_factory):
    """Same seed and density: byte-identical masks and polygons in two worlds; another seed or density differs."""
    a, b = make_world(lib, world_factory), make_world(lib, world_factory)
    assert gen(lib, a, 11, 55) == 0 and gen(lib, b, 11, 55) == 0
    ha = field_hash(read_masks(lib, a), read_polys(lib, a))
    assert ha == field_hash(read_masks(lib, b), read_polys(lib, b))
    assert ha != field_hash(*field(lib, world_factory, 12, 55))
    assert ha != field_hash(*field(lib, world_factory, 11, 70))


def test_hash_stable_across_interleaved_generates(lib, world_factory):
    """No hidden state: generating other fields between two runs of one seed does not change it."""
    w = make_world(lib, world_factory)
    assert gen(lib, w, 14, 35) == 0
    h1 = field_hash(read_masks(lib, w), read_polys(lib, w))
    assert gen(lib, w, 15, 70) == 0 and gen(lib, w, 14, 35) == 0
    assert field_hash(read_masks(lib, w), read_polys(lib, w)) == h1


# ---- reachability: 0 unreachable regions -------------------------------------------------------------------------

def test_zero_unreachable_regions_every_seed_and_density(lib, world_factory):
    """R-246-01 / mockup checklist: with the carve, 0 unreachable regions on seeds 11 to 16 at densities 15, 35, 55,
    70; and the field is a real one (mean blocked above NONTRIVIAL_FLOOR), so 0 is not the empty map's 0."""
    bad = []
    for seed in SEEDS:
        for d in (15, 35, 55, 70):
            masks, _ = field(lib, world_factory, seed, d)
            assert mean_share(masks) >= NONTRIVIAL_FLOOR, f"seed {seed} density {d}: share {mean_share(masks):.3f}"
            n = unreachable_regions(masks)
            if n:
                bad.append((seed, d, n))
    assert not bad, f"(seed, density, unreachable regions): {bad}"


def test_control_space_no_carve_leaves_unreachable_regions(dbg, dbg_world_factory):
    """Positive control `space-no-carve` (see QUESTION 2): with the carve skipped, density 70 gives more than 0
    unreachable regions on at least one of seeds 11 to 16. Proves the detector above can fail."""
    bind(dbg)
    dbg.om_debug_inject.argtypes, dbg.om_debug_inject.restype = [W, ctypes.c_int], None
    counts = {}
    for seed in SEEDS:
        w = make_world(dbg, dbg_world_factory)
        dbg.om_debug_inject(w, NO_CARVE_BUG)
        assert gen(dbg, w, seed, 70) == 0
        counts[seed] = unreachable_regions(read_masks(dbg, w))
    assert max(counts.values()) > 0, f"no-carve still reachable everywhere: {counts}"


# ---- statistics against the mockup: Westley's numbers, parked ---------------------------------------------------

@pytest.mark.parametrize("density", sorted(DRAFT_BANDS))
def test_park_blocked_share_band_per_density(lib, world_factory, density):
    """Westley's threshold (DRAFT numbers, module note): mean blocked share of the five layers, each of seeds 11 to
    16, inside the band for the density. Parked when red."""
    lo, hi = DRAFT_BANDS[density]
    shares = {s: round(mean_share(field(lib, world_factory, s, density)[0]), 3) for s in SEEDS}
    out = {s: v for s, v in shares.items() if not lo <= v <= hi}
    assert not out, f"density {density}: band {lo}..{hi}, outside: {out}"


def test_park_polygons_cover_blocked_cells(lib, world_factory):
    """Westley's threshold (DRAFT 0.90): the polygons reproduce the masks. At least DRAFT_POLY_COVER_FLOOR of blocked
    cell centres lie inside a polygon of their layer (the rest are filled pockets, which carry no polygon)."""
    masks, polys = field(lib, world_factory, 11, 55)
    ys, xs = np.mgrid[0:N, 0:N]
    centres = np.column_stack([(xs.ravel() + .5) * 100.0, (ys.ravel() + .5) * 100.0])
    inside = np.zeros((LAYERS, CELLS), dtype=bool)
    for layer, _, pts in polys:
        inside[layer] |= points_in_polygon(centres, pts)
    for k in range(LAYERS):
        blocked = masks[k].ravel()
        frac = float(inside[k][blocked].mean())
        assert frac >= DRAFT_POLY_COVER_FLOOR, f"layer {k}: {frac:.3f} of blocked cells inside a polygon"
