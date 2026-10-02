# spec: docs/northstar/plans/skilllab-harness-spec.md::Acceptance criteria::AC-4
"""formations.place: five kinds, exact counts, determinism, error cases."""
import math
import random
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
for _p in (ROOT, Path(__file__).resolve().parent):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from scripts.skilllab.formations import place  # noqa: E402

PARAMS = {
    "line": {"spacing": 30.0},
    "column": {"spacing": 30.0, "cols": 3},
    "concave": {"spacing": 30.0, "arc_deg": 120.0, "radius": 100.0},
    "blob": {"radius": 50.0},
}


def _center_and_radius(p, q, r):
    """Circumcentre of three non-collinear points."""
    ax, ay = p
    bx, by = q
    cx, cy = r
    d = 2 * (ax * (by - cy) + bx * (cy - ay) + cx * (ay - by))
    ux = ((ax * ax + ay * ay) * (by - cy) + (bx * bx + by * by) * (cy - ay) + (cx * cx + cy * cy) * (ay - by)) / d
    uy = ((ax * ax + ay * ay) * (cx - bx) + (bx * bx + by * by) * (ax - cx) + (cx * cx + cy * cy) * (bx - ax)) / d
    return (ux, uy), math.hypot(ax - ux, ay - uy)


@pytest.mark.parametrize("kind", ["line", "blob", "concave", "column"])
@pytest.mark.parametrize("n", [1, 2, 7, 16])
def test_ac4_returns_exactly_n_float_points(kind, n):
    """AC-4: exactly n (x, y) points, plain Python floats, for every generated kind."""
    pts = place(kind, n, 10.0, -20.0, 30.0, dict(PARAMS[kind]))
    assert len(pts) == n and all(len(p) == 2 and type(p[0]) is float and type(p[1]) is float for p in pts)


def test_ac4_points_kind_is_verbatim_and_ignores_anchor():
    """AC-4: points returns params["points"] verbatim; anchor and facing do not move it."""
    pts = [(1.0, 2.0), (3.5, -4.0), (0.0, 9.0)]
    out = place("points", 3, 999.0, 999.0, 77.0, {"points": list(pts)})
    assert [tuple(p) for p in out] == pts


@pytest.mark.parametrize("given", [2, 4, 0])
def test_ac4_points_wrong_length_is_an_error(given):
    """AC-4: a points list whose length is not n raises (both shorter and longer)."""
    pts = [(float(i), 0.0) for i in range(given)]
    with pytest.raises(ValueError):
        place("points", 3, 0.0, 0.0, 0.0, {"points": pts})


@pytest.mark.parametrize("kind", ["hexagon", "", "box"])
def test_ac4_unknown_kind_is_an_error(kind):
    """AC-4: any kind outside line/blob/concave/column/points raises ValueError."""
    with pytest.raises(ValueError):
        place(kind, 3, 0.0, 0.0, 0.0, {"spacing": 30.0})


@pytest.mark.parametrize("facing", [0.0, 90.0, 37.0, 180.0, -90.0])
def test_ac4_line_is_abreast_perpendicular_centred_and_spaced(facing):
    """AC-4 line: n points abreast, perpendicular to facing, centred on the anchor, spacing apart."""
    ax, ay, n, sp = 10.0, -20.0, 5, 12.5
    pts = sorted(place("line", n, ax, ay, facing, {"spacing": sp}))
    fx, fy = math.cos(math.radians(facing)), math.sin(math.radians(facing))
    cx = sum(p[0] for p in pts) / n
    cy = sum(p[1] for p in pts) / n
    gaps = [math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(pts, pts[1:])]
    along = [(p[0] - ax) * fx + (p[1] - ay) * fy for p in pts]
    assert (cx, cy) == pytest.approx((ax, ay), abs=1e-5)
    assert gaps == pytest.approx([sp] * (n - 1), abs=1e-5)
    assert along == pytest.approx([0.0] * n, abs=1e-5)


def test_ac4_line_facing_zero_runs_along_y_with_exact_offsets():
    """AC-4 line: facing 0 puts the points on x = anchor with y offsets (i - (n-1)/2) * spacing (toy geometry)."""
    pts = sorted(place("line", 4, 100.0, 50.0, 0.0, {"spacing": 30.0}))
    flat = [v for p in pts for v in p]
    assert flat == pytest.approx([100.0, 5.0, 100.0, 35.0, 100.0, 65.0, 100.0, 95.0], abs=1e-5)


def test_ac4_line_single_unit_sits_on_the_anchor():
    """AC-4 (cardinality one): one point, on the anchor."""
    assert place("line", 1, 7.0, 8.0, 33.0, {"spacing": 30.0})[0] == pytest.approx((7.0, 8.0), abs=1e-5)


def test_ac4_column_cols_changes_the_layout_and_points_are_distinct():
    """AC-4 column: params["cols"] shapes the layout (2 columns differ from 3) and no two units share a point."""
    two = place("column", 6, 0.0, 0.0, 0.0, {"spacing": 30.0, "cols": 2})
    three = place("column", 6, 0.0, 0.0, 0.0, {"spacing": 30.0, "cols": 3})
    assert sorted(two) != sorted(three)
    assert len(set(two)) == 6 and len(set(three)) == 6


@pytest.mark.parametrize("facing", [0.0, 90.0])
@pytest.mark.parametrize("arc", [60.0, 120.0])
def test_ac4_concave_points_lie_on_an_arc_of_arc_deg_opening_toward_facing(facing, arc):
    """AC-4 concave: points are concyclic, span arc_deg of that circle, and the circle's centre lies ahead of the arc."""
    n = 7
    pts = place("concave", n, 0.0, 0.0, facing, {"spacing": 30.0, "arc_deg": arc, "radius": 100.0})
    centre, rad = _center_and_radius(pts[0], pts[n // 2], pts[-1])
    dists = [math.hypot(p[0] - centre[0], p[1] - centre[1]) for p in pts]
    angs = [math.atan2(p[1] - centre[1], p[0] - centre[0]) for p in pts]
    mean_dir = math.atan2(sum(math.sin(a) for a in angs), sum(math.cos(a) for a in angs))
    dev = [math.degrees((a - mean_dir + math.pi) % (2 * math.pi) - math.pi) for a in angs]
    mx = sum(p[0] for p in pts) / n
    my = sum(p[1] for p in pts) / n
    ahead = (centre[0] - mx) * math.cos(math.radians(facing)) + (centre[1] - my) * math.sin(math.radians(facing))
    assert dists == pytest.approx([rad] * n, abs=1e-3)
    assert max(dev) - min(dev) == pytest.approx(arc, abs=0.01)
    assert ahead > 0.0


def test_ac4_blob_points_fit_in_a_disc_of_radius_and_are_distinct():
    """AC-4 blob: every point within `radius` of the ANCHOR; no two further apart than a diameter; distinct; radius governs the size."""
    ax, ay = 100.0, -50.0

    def widest(r, n):
        pts = place("blob", n, ax, ay, 0.0, {"radius": r})
        assert len(set(pts)) == n
        assert max(math.hypot(p[0] - ax, p[1] - ay) for p in pts) <= r + 1e-5     # the disc is centred on the anchor
        return max(math.hypot(a[0] - b[0], a[1] - b[1]) for a in pts for b in pts)
    assert widest(50.0, 40) <= 100.0 + 1e-5
    assert widest(10.0, 40) <= 20.0 + 1e-5
    assert widest(50.0, 40) > 20.0          # positive control: the big blob really is bigger than the small disc
    for n in (1, 2, 7):
        widest(50.0, n)


def test_ac4_blob_follows_the_anchor():
    """AC-4 blob: moving the anchor moves the blob; the points sit within radius of the anchor and their mean near it."""
    for ax, ay in ((0.0, 0.0), (500.0, 500.0), (-600.0, 0.0)):
        for n in (20, 40):
            pts = place("blob", n, ax, ay, 0.0, {"radius": 50.0})
            cx = sum(p[0] for p in pts) / n
            cy = sum(p[1] for p in pts) / n
            assert max(math.hypot(p[0] - ax, p[1] - ay) for p in pts) <= 50.0 + 1e-5
            assert math.hypot(cx - ax, cy - ay) <= 25.0       # mean within half a radius of the anchor, not off to one side


def _centrally_symmetric(pts, ax, ay, tol=1e-6):
    """True when every point's reflection through (ax, ay) is also a point (each coordinate within tol), one match per point."""
    left = list(pts)
    for p in pts:
        q = (2 * ax - p[0], 2 * ay - p[1])
        hit = next((i for i, r in enumerate(left) if abs(r[0] - q[0]) <= tol + 1e-9 and abs(r[1] - q[1]) <= tol + 1e-9), None)
        if hit is None:
            return False
        left.pop(hit)
    return True


@pytest.mark.parametrize("anchor,facing", [((0.0, 0.0), 0.0), ((-600.0, 25.0), 0.0), ((600.0, -40.0), 180.0), ((123.5, -77.25), 37.0)])
@pytest.mark.parametrize("n", [1, 2, 3, 4, 7, 8, 16, 17, 40])
def test_ac4_blob_is_centrally_symmetric_about_the_anchor(n, anchor, facing):
    """AC-4 blob: every point's reflection through the anchor is a point (1e-6); an odd n puts one point on the anchor."""
    ax, ay = anchor
    pts = place("blob", n, ax, ay, facing, {"radius": 80.0 + 12.0 * math.sqrt(n)})
    assert _centrally_symmetric(pts, ax, ay)
    if n % 2 == 1:
        assert sum(1 for p in pts if abs(p[0] - ax) <= 1e-6 and abs(p[1] - ay) <= 1e-6) == 1


def test_ac4_blob_symmetry_check_has_teeth_positive_control():
    """AC-4 positive control: the check rejects a Fermat spiral and a disc nudged off the anchor, accepts a hand-built symmetric set."""
    n, r = 16, 50.0
    fermat = [(r * math.sqrt((i + 0.5) / n) * math.cos(i * 2.399963229728653),
               r * math.sqrt((i + 0.5) / n) * math.sin(i * 2.399963229728653)) for i in range(n)]
    real = place("blob", n, 0.0, 0.0, 0.0, {"radius": r})
    assert not _centrally_symmetric(fermat, 0.0, 0.0)
    assert not _centrally_symmetric([(x + 3.0, y) for x, y in real], 0.0, 0.0)
    assert _centrally_symmetric([(0.0, 0.0), (5.0, 2.0), (-5.0, -2.0)], 0.0, 0.0)


@pytest.mark.parametrize("kind", ["line", "blob", "concave", "column"])
def test_ac4_same_input_same_output_and_no_randomness(kind):
    """AC-4: same input gives same output, and place neither reads nor disturbs the global RNG."""
    args = (kind, 9, 5.0, 6.0, 45.0, dict(PARAMS[kind]))
    random.seed(1)
    first = place(*args)
    random.seed(999)
    second = place(*args)
    random.seed(5)
    before = random.random()
    random.seed(5)
    place(*args)
    after = random.random()
    assert first == second and before == after


# ---------------------------------------------------------------- AC 4 Readings: the toy's behaviour, pinned by literals
# Literals below come from ONE run of toys/layerlab/layerlab/formations.py (x, y of each returned point, in the
# order the toy returned them). Mapping used for that run: harness `line` = toy `line`; harness `column` = toy `box`
# (cols, spacing); harness `concave` = toy `concave` with R = params["radius"] and the centre one radius ahead of
# the anchor along facing, so the anchor is the midpoint of the arc.

def _flat(pts):
    return [v for p in pts for v in p]


def test_ac4_toy_line_point_order_and_offsets_literals():
    """AC-4 (Readings): line point order is the toy's: increasing offset along facing + 90 degrees (literals from the toy)."""
    got = place("line", 4, 10.0, 20.0, 30.0, {"spacing": 15.0})
    assert _flat(got) == pytest.approx([21.25, 0.514428, 13.75, 13.504809, 6.25, 26.495191, -1.25, 39.485572], abs=1e-5)
    assert _flat(place("line", 3, 0.0, 0.0, 0.0, {"spacing": 30.0})) == pytest.approx([0, -30, 0, 0, 0, 30], abs=1e-5)
    assert _flat(place("line", 3, 0.0, 0.0, 90.0, {"spacing": 30.0})) == pytest.approx([30, 0, 0, 0, -30, 0], abs=1e-5)


def test_ac4_toy_column_cols_and_spacing_literals():
    """AC-4 (Readings): column = toy box: `cols` per row across the front, rows along facing, short last row centred (toy literals)."""
    got0 = place("column", 7, 0.0, 0.0, 0.0, {"spacing": 20.0, "cols": 3})
    got90 = place("column", 7, 5.0, -5.0, 90.0, {"spacing": 20.0, "cols": 3})
    assert _flat(got0) == pytest.approx([-20, -20, -20, 0, -20, 20, 0, -20, 0, 0, 0, 20, 20, 0], abs=1e-5)
    assert _flat(got90) == pytest.approx([25, -25, 5, -25, -15, -25, 25, -5, 5, -5, -15, -5, 5, 15], abs=1e-5)


def test_ac4_toy_concave_anchor_is_the_arc_midpoint_literals():
    """AC-4 (Readings): the anchor is the midpoint of a concave arc (toy literals: n = 5, arc 90, R 120, facing 20)."""
    params = {"spacing": 30.0, "arc_deg": 90.0, "radius": 120.0}
    got = place("concave", 5, 100.0, 50.0, 20.0, params)
    assert _flat(got) == pytest.approx([104.00618, 141.756609, 92.877328, 96.276744, 100.0, 50.0,
                                        124.289834, 9.971592, 162.048923, -17.714517], abs=1e-4)
    assert _flat(place("concave", 1, 100.0, 50.0, 20.0, params)) == pytest.approx([100.0, 50.0], abs=1e-5)


@pytest.mark.parametrize("kind", ["line", "blob", "concave", "column", "points"])
def test_ac4_n_zero_returns_empty_list(kind):
    """AC-4 (Readings): n == 0 returns [] for every kind."""
    params = dict(PARAMS.get(kind, {"points": []}))
    assert list(place(kind, 0, 0.0, 0.0, 0.0, params)) == []


@pytest.mark.parametrize("kind", ["line", "blob", "concave", "column", "points"])
def test_ac4_negative_n_raises_valueerror(kind):
    """AC-4 (Readings): n < 0 raises ValueError for every kind."""
    params = dict(PARAMS.get(kind, {"points": []}))
    with pytest.raises(ValueError):
        place(kind, -1, 0.0, 0.0, 0.0, params)


@pytest.mark.parametrize("kind", ["Line", "LINE", "Blob", "Points", "CONCAVE"])
def test_ac4_kind_is_case_sensitive(kind):
    """AC-4 (Readings): a kind spelled in another case is an unknown kind (ValueError)."""
    with pytest.raises(ValueError):
        place(kind, 3, 0.0, 0.0, 0.0, {"spacing": 30.0, "radius": 50.0, "arc_deg": 90.0, "cols": 2, "points": [(0, 0)] * 3})


@pytest.mark.parametrize("kind,params", [
    ("line", {}), ("column", {"cols": 3}), ("concave", {"spacing": 30.0, "radius": 100.0}), ("blob", {"spacing": 30.0}),
])
def test_ac4_missing_required_parameter_raises_valueerror(kind, params):
    """AC-4 (Readings): spacing (line, column), arc_deg (concave) and radius (blob) are required; missing -> ValueError."""
    with pytest.raises(ValueError):
        place(kind, 4, 0.0, 0.0, 0.0, params)


@pytest.mark.parametrize("kind", ["line", "blob", "concave", "column"])
def test_ac4_extra_parameters_are_ignored(kind):
    """AC-4 (Readings): parameters a kind does not use change nothing and raise nothing."""
    plain = place(kind, 6, 3.0, 4.0, 25.0, dict(PARAMS[kind]))
    noisy = place(kind, 6, 3.0, 4.0, 25.0, dict(PARAMS[kind], junk=1, points=[(9, 9)], unused_radius=7.0))
    assert plain == noisy
