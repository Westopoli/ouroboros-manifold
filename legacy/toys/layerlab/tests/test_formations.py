"""Rung R2 formation tests (SPEC.md sections 7 and 8; test list in the R2 brief).

Pure geometry through `layerlab.formations.place(kind, n, x, y, facing_deg, spacing, **params)`.
`line` exists in R0 and is a regression guard; `column box concave screen` raise
NotImplementedError until R2.

Conventions the SPEC leaves open and these tests fix (reported as gaps):
- column: centred on (x, y) along the facing, not starting at it.
- box: the grid lives in the group's facing frame: `cols` units across (perpendicular to the
  facing, like a line), rows along the facing; rows are filled in order (unit i is in row i // cols),
  the grid is centred on (x, y) in depth. A partial last row is only required to be `spacing` apart
  and inside the grid width (left- or centre-aligned both pass).
- column and box units face facing_deg, like line.
- concave and screen: units evenly spaced in angle, the end units at +/- arc_deg / 2 from the
  axis, n = 1 on the axis. Order of units along the arc is not asserted.
- Coordinates are rounded to 6 decimals, so length checks use 1e-5 and the circle and angle checks
  the 1e-6 / 1e-6 degree of the brief (rounding error is below 8e-7 for the radii used).

Each geometry check is a helper that returns a list of error strings; a self-test feeds every
helper a wrong shape so the detector is shown able to fail (the negative controls).
"""
import copy
import math

import pytest

from layerlab import scenario
from layerlab.formations import place

TOL = 1e-5            # lengths: coordinates are rounded to 1e-6
CIRCLE_TOL = 1e-6     # brief: distance to centre
ANGLE_TOL = 1e-6      # brief: degrees


# ---------------------------------------------------------------- geometry helpers

def _local(places, x, y, facing_deg):
    """(along-facing, lateral) of every placed unit; lateral is the facing rotated +90 degrees."""
    f = math.radians(facing_deg)
    out = []
    for px, py, _ in places:
        dx, dy = px - x, py - y
        out.append((dx * math.cos(f) + dy * math.sin(f), -dx * math.sin(f) + dy * math.cos(f)))
    return out


def _wrap(a):
    return (a + 180.0) % 360.0 - 180.0


def _row_errors(places, n, x, y, facing_deg, spacing, axis):
    """A straight row centred on (x, y): `lateral` (line) or `along` (column)."""
    err = []
    if len(places) != n:
        return ["got %d units, expected %d" % (len(places), n)]
    loc = _local(places, x, y, facing_deg)
    main = sorted((l[1] if axis == "lateral" else l[0]) for l in loc)
    other = [(l[0] if axis == "lateral" else l[1]) for l in loc]
    if any(abs(o) > TOL for o in other):
        err.append("not on the %s axis: off-axis components %s" % (axis, other))
    if any(abs((b - a) - spacing) > TOL for a, b in zip(main, main[1:])):
        err.append("neighbours not %g apart: %s" % (spacing, main))
    if abs(sum(main) / n) > TOL:
        err.append("not centred on (x, y): mean offset %g" % (sum(main) / n))
    if any(abs(_wrap(p[2] - facing_deg)) > ANGLE_TOL for p in places):
        err.append("not every unit faces facing_deg")
    return err


def _box_errors(places, n, cols, x, y, facing_deg, spacing):
    err = []
    if len(places) != n:
        return ["got %d units, expected %d" % (len(places), n)]
    rows = math.ceil(n / cols)
    loc = _local(places, x, y, facing_deg)
    row_along = []
    for r in range(rows):
        chunk = loc[r * cols:(r + 1) * cols]
        alongs = [c[0] for c in chunk]
        if max(alongs) - min(alongs) > TOL:
            err.append("row %d is not at one depth: %s" % (r, alongs))
        row_along.append(sum(alongs) / len(alongs))
        lat = sorted(c[1] for c in chunk)
        if any(abs((b - a) - spacing) > TOL for a, b in zip(lat, lat[1:])):
            err.append("row %d columns not %g apart: %s" % (r, spacing, lat))
        if any(abs(v) > (cols - 1) / 2.0 * spacing + TOL for v in lat):
            err.append("row %d wider than the grid: %s" % (r, lat))
        if len(chunk) == cols:
            want = [(c - (cols - 1) / 2.0) * spacing for c in range(cols)]
            if any(abs(a - b) > TOL for a, b in zip(lat, want)):
                err.append("full row %d columns %s, expected %s" % (r, lat, want))
    steps = [b - a for a, b in zip(row_along, row_along[1:])]
    if steps and (any(abs(abs(s) - spacing) > TOL for s in steps) or any(s * steps[0] <= 0 for s in steps)):
        err.append("rows not %g apart in a consistent direction: %s" % (spacing, steps))
    if abs(sum(row_along) / rows) > TOL:
        err.append("rows not centred on (x, y) in depth: mean %g" % (sum(row_along) / rows))
    if n % cols == 0:
        cx = sum(p[0] for p in places) / n
        cy = sum(p[1] for p in places) / n
        if math.hypot(cx - x, cy - y) > TOL:
            err.append("full grid centroid (%g, %g) is not (x, y)" % (cx, cy))
    if any(abs(_wrap(p[2] - facing_deg)) > ANGLE_TOL for p in places):
        err.append("not every unit faces facing_deg")
    return err


def _arc_errors(places, n, cx, cy, axis_deg, radius, arc_deg, outward):
    """Units on a circle (cx, cy, radius), spanning arc_deg centred on axis_deg, evenly spaced in
    angle, each facing the centre (concave) or directly away from it (screen)."""
    if len(places) != n:
        return ["got %d units, expected %d" % (len(places), n)]
    err = []
    offs = []
    for px, py, fdeg in places:
        d = math.hypot(px - cx, py - cy)
        if abs(d - radius) > CIRCLE_TOL:
            err.append("distance %.9f, expected %g" % (d, radius))
        ang = math.degrees(math.atan2(py - cy, px - cx))
        offs.append(_wrap(ang - axis_deg))
        want_face = ang if outward else math.degrees(math.atan2(cy - py, cx - px))
        if abs(_wrap(fdeg - want_face)) > ANGLE_TOL:
            err.append("facing %.9f, expected %.9f" % (fdeg, want_face))
    offs.sort()
    if n == 1:
        if abs(offs[0]) > ANGLE_TOL:
            err.append("a single unit must sit on the axis, offset %g" % offs[0])
    else:
        if abs(offs[0] + arc_deg / 2.0) > ANGLE_TOL or abs(offs[-1] - arc_deg / 2.0) > ANGLE_TOL:
            err.append("angular extent [%g, %g], expected +/- %g" % (offs[0], offs[-1], arc_deg / 2.0))
        gap = arc_deg / (n - 1)
        if any(abs((b - a) - gap) > 2 * ANGLE_TOL for a, b in zip(offs, offs[1:])):
            err.append("not evenly spaced by %g: %s" % (gap, offs))
    return err


def _concave_errors(places, n, center, x, y, radius, arc_deg):
    cx, cy = center
    axis = math.degrees(math.atan2(y - cy, x - cx))
    return _arc_errors(places, n, cx, cy, axis, radius, arc_deg, outward=False)


def _screen_errors(places, n, x, y, facing_deg, radius, arc_deg):
    return _arc_errors(places, n, x, y, facing_deg, radius, arc_deg, outward=True)


# ---------------------------------------------------------------- line (R0: regression guard)

@pytest.mark.parametrize("facing", [0.0, 90.0, 30.0, 180.0, -45.0, 270.5])
@pytest.mark.parametrize("n", [2, 3, 6])
def test_line_is_perpendicular_centred_and_faces_the_group(n, facing):
    """SPEC 7 (line): perpendicular to the facing, `spacing` apart, centred at (x, y), every unit
    facing facing_deg. Already built in R0, so this may pass today."""
    pl = place("line", n, 1200.0, 800.0, facing, 37.5)
    assert _row_errors(pl, n, 1200.0, 800.0, facing, 37.5, "lateral") == []


def test_line_facing_90_runs_along_x():
    """SPEC 7 (line): facing 90 points along +y, so the line is perpendicular to it and runs along
    x: every y equals the centre y, and the x values are the centre +/- 37.5 and +/- 75 (the unit
    order along the line is not fixed). Facing 0 is the transpose: a line along y."""
    ninety = place("line", 5, 1000.0, 500.0, 90.0, 37.5)
    assert all(abs(p[1] - 500.0) < TOL for p in ninety)
    assert sorted(p[0] for p in ninety) == pytest.approx([925.0, 962.5, 1000.0, 1037.5, 1075.0], abs=TOL)
    zero = place("line", 5, 1000.0, 500.0, 0.0, 37.5)
    assert all(abs(p[0] - 1000.0) < TOL for p in zero)
    assert sorted(p[1] for p in zero) == pytest.approx([425.0, 462.5, 500.0, 537.5, 575.0], abs=TOL)


@pytest.mark.parametrize("kind,params", [
    ("line", {}), ("column", {}), ("box", {"cols": 3}),
    ("concave", {"center": (3000.0, 1000.0), "R": 500.0, "arc_deg": 90.0}),
    ("screen", {"screen_r": 200.0, "arc_deg": 120.0}),
])
def test_single_unit_sits_at_the_anchor_or_on_the_axis(kind, params):
    """SPEC 7: n = 1. line, column and box return [(x, y, facing_deg)]; concave and screen put the
    one unit on the axis (checked by the arc tests below, here only that exactly one unit comes
    back with finite numbers)."""
    pl = place(kind, 1, 1000.0, 1000.0, 20.0, 37.5, **params)
    assert len(pl) == 1 and all(math.isfinite(v) for v in pl[0])
    if kind in ("line", "column", "box"):
        assert pl == [(1000.0, 1000.0, 20.0)]


# ---------------------------------------------------------------- column

@pytest.mark.parametrize("facing", [0.0, 90.0, 30.0, 180.0, 270.5])
@pytest.mark.parametrize("n", [2, 5])
def test_column_runs_along_the_facing_centred(n, facing):
    """SPEC 7 (column): 'along the facing', `spacing` apart. Chosen reading: centred on (x, y), so
    the offsets are symmetric about the anchor (SPEC gap, reported). Every unit faces facing_deg."""
    pl = place("column", n, 1200.0, 800.0, facing, 37.5)
    assert _row_errors(pl, n, 1200.0, 800.0, facing, 37.5, "along") == []


def test_column_facing_0_runs_along_x_and_is_not_a_line():
    """SPEC 7 (column vs line): facing 0 is +x, so a column has one y and spread x, the transpose
    of the line. Negative control: the line at the same facing fails the column check."""
    col = place("column", 4, 1000.0, 500.0, 0.0, 40.0)
    assert all(abs(p[1] - 500.0) < TOL for p in col)
    assert sorted(p[0] for p in col) == pytest.approx([940.0, 980.0, 1020.0, 1060.0], abs=TOL)
    line = place("line", 4, 1000.0, 500.0, 0.0, 40.0)
    assert _row_errors(line, 4, 1000.0, 500.0, 0.0, 40.0, "along") != []


# ---------------------------------------------------------------- box

@pytest.mark.parametrize("facing", [0.0, 90.0, 30.0, 215.0])
@pytest.mark.parametrize("n,cols", [(12, 4), (6, 3), (6, 2), (3, 1), (8, 8)])
def test_box_full_grid_is_cols_wide_spaced_and_centred(n, cols, facing):
    """SPEC 7 (box): a `cols` wide grid, `spacing` apart, rows filled in order, centred on
    (x, y). Full grids (n a multiple of cols): every lattice point once, centroid on the anchor.
    Chosen reading: width across the facing, depth along it (SPEC gap, reported)."""
    pl = place("box", n, 1500.0, 900.0, facing, 37.5, cols=cols)
    assert _box_errors(pl, n, cols, 1500.0, 900.0, facing, 37.5) == []
    assert len({(round(p[0], 4), round(p[1], 4)) for p in pl}) == n, "two units on one lattice point"


@pytest.mark.parametrize("n,cols", [(10, 4), (7, 3), (5, 4)])
def test_box_partial_last_row_stays_in_the_grid(n, cols):
    """SPEC 7 (box): n not a multiple of cols leaves a short last row; rows are still filled in
    order, rows `spacing` apart and centred in depth, the short row inside the grid width."""
    pl = place("box", n, 1500.0, 900.0, 0.0, 37.5, cols=cols)
    assert _box_errors(pl, n, cols, 1500.0, 900.0, 0.0, 37.5) == []


def test_box_cols_changes_the_shape():
    """SPEC 7 (box): `cols` is the knob. Twelve units with cols 4 and cols 6 give different grids
    (positive control for cols being read), each valid for its own cols and invalid for the other."""
    a = place("box", 12, 1500.0, 900.0, 0.0, 37.5, cols=4)
    b = place("box", 12, 1500.0, 900.0, 0.0, 37.5, cols=6)
    assert a != b
    assert _box_errors(a, 12, 4, 1500.0, 900.0, 0.0, 37.5) == []
    assert _box_errors(b, 12, 6, 1500.0, 900.0, 0.0, 37.5) == []
    assert _box_errors(a, 12, 6, 1500.0, 900.0, 0.0, 37.5) != []


# ---------------------------------------------------------------- concave

CONCAVE_CASES = [
    # n, center, (x, y), R, arc_deg
    (5, (3000.0, 1000.0), (1000.0, 1000.0), 500.0, 90.0),     # axis 180 degrees
    (7, (2000.0, 1500.0), (1200.0, 700.0), 400.0, 120.0),     # axis 225 degrees
    (2, (3000.0, 1000.0), (1000.0, 1500.0), 300.0, 60.0),     # two units: just the ends
    (4, (2500.0, 800.0), (2500.0, 1800.0), 150.0, 180.0),     # axis +90, a half circle
    (9, (1000.0, 1000.0), (3000.0, 1000.0), 600.0, 270.0),    # axis 0, a wide arc
]


@pytest.mark.parametrize("n,center,anchor,radius,arc", CONCAVE_CASES)
def test_concave_arcs_around_the_centre_facing_it(n, center, anchor, radius, arc):
    """SPEC 7 (concave): units on a circle of radius R around center, spanning arc_deg centred on
    the bearing from center to (x, y), each facing the centre: distance to centre == R (1e-6),
    end units at +/- arc/2 from the axis, evenly spaced, each facing within 1e-6 degrees of the
    bearing to the centre."""
    pl = place("concave", n, anchor[0], anchor[1], 0.0, 37.5, center=center, R=radius, arc_deg=arc)
    assert _concave_errors(pl, n, center, anchor[0], anchor[1], radius, arc) == []


def test_concave_single_unit_is_on_the_axis():
    """SPEC 7 (concave): n = 1 sits on the axis, at center + R toward (x, y), facing the centre."""
    pl = place("concave", 1, 1000.0, 1000.0, 0.0, 37.5, center=(3000.0, 1000.0), R=500.0, arc_deg=90.0)
    assert pl[0][0] == pytest.approx(2500.0, abs=2e-6)
    assert pl[0][1] == pytest.approx(1000.0, abs=2e-6)
    assert abs(_wrap(pl[0][2] - 0.0)) < ANGLE_TOL


def test_concave_takes_center_as_list_or_tuple_and_does_not_mutate_it():
    """SPEC 8 (scenario `center = [cx, cy]` arrives as a list): list and tuple give the same
    placement and the caller's list is left alone."""
    lst = [3000.0, 1000.0]
    a = place("concave", 5, 1000.0, 1000.0, 0.0, 37.5, center=lst, R=500.0, arc_deg=90.0)
    b = place("concave", 5, 1000.0, 1000.0, 0.0, 37.5, center=(3000.0, 1000.0), R=500.0, arc_deg=90.0)
    assert a == b and lst == [3000.0, 1000.0]


def test_concave_radius_and_arc_are_live_knobs():
    """SPEC 7 (concave) positive and negative control: a placement valid for (R 500, arc 90) is
    rejected by the checker for (R 400, arc 90) and (R 500, arc 120); the same call with R 400 is
    valid for R 400, so the checker follows R and arc."""
    c = (3000.0, 1000.0)
    pl = place("concave", 5, 1000.0, 1000.0, 0.0, 37.5, center=c, R=500.0, arc_deg=90.0)
    assert _concave_errors(pl, 5, c, 1000.0, 1000.0, 500.0, 90.0) == []
    assert _concave_errors(pl, 5, c, 1000.0, 1000.0, 400.0, 90.0) != []
    assert _concave_errors(pl, 5, c, 1000.0, 1000.0, 500.0, 120.0) != []
    other = place("concave", 5, 1000.0, 1000.0, 0.0, 37.5, center=c, R=400.0, arc_deg=90.0)
    assert _concave_errors(other, 5, c, 1000.0, 1000.0, 400.0, 90.0) == []


# ---------------------------------------------------------------- screen

SCREEN_CASES = [
    # n, (x, y), facing_deg, screen_r, arc_deg
    (4, (3000.0, 1000.0), 180.0, 200.0, 120.0),
    (6, (1500.0, 900.0), 45.0, 300.0, 270.0),
    (2, (2000.0, 1000.0), 0.0, 250.0, 90.0),
    (5, (2000.0, 1000.0), 90.0, 150.0, 180.0),
]


@pytest.mark.parametrize("n,anchor,facing,radius,arc", SCREEN_CASES)
def test_screen_ring_faces_outward_around_the_protected_point(n, anchor, facing, radius, arc):
    """SPEC 7 (screen): `count` units on a circle of radius screen_r around (x, y), spanning
    arc_deg centred on the group's facing (the direction of the enemy), each facing outward, i.e.
    along the bearing from (x, y) to that unit (within 1e-6 degrees)."""
    pl = place("screen", n, anchor[0], anchor[1], facing, 37.5, screen_r=radius, arc_deg=arc)
    assert _screen_errors(pl, n, anchor[0], anchor[1], facing, radius, arc) == []


def test_screen_single_unit_is_on_the_facing_axis():
    """SPEC 7 (screen): n = 1 stands screen_r from (x, y) in the facing direction, facing outward."""
    pl = place("screen", 1, 2000.0, 1000.0, 90.0, 37.5, screen_r=150.0, arc_deg=120.0)
    assert pl[0][0] == pytest.approx(2000.0, abs=2e-6)
    assert pl[0][1] == pytest.approx(1150.0, abs=2e-6)
    assert abs(_wrap(pl[0][2] - 90.0)) < ANGLE_TOL


def test_screen_is_not_a_concave_and_not_a_wrong_axis():
    """SPEC 7 (screen) negative controls: the same placement fails the check for the wrong axis
    (facing + 30) and fails the concave check (facing inward), so the checker can tell outward
    from inward and centred from off-centre."""
    pl = place("screen", 5, 2000.0, 1000.0, 0.0, 37.5, screen_r=200.0, arc_deg=120.0)
    assert _screen_errors(pl, 5, 2000.0, 1000.0, 0.0, 200.0, 120.0) == []
    assert _screen_errors(pl, 5, 2000.0, 1000.0, 30.0, 200.0, 120.0) != []
    assert _arc_errors(pl, 5, 2000.0, 1000.0, 0.0, 200.0, 120.0, outward=False) != []


# ---------------------------------------------------------------- checker self-tests (negative controls)

def test_checkers_reject_the_wrong_shape():
    """Negative controls for the helpers above: each rejects a plausible wrong placement, so a
    green result in the tests above means something. (These pass today by construction: they
    exercise the helpers and the R0 `line`, not the R2 code.)"""
    line = place("line", 5, 1000.0, 1000.0, 0.0, 37.5)
    assert _row_errors(line, 5, 1000.0, 1000.0, 0.0, 37.5, "lateral") == []
    assert _row_errors(line, 5, 1000.0, 1000.0, 0.0, 37.5, "along") != []             # wrong axis
    assert _row_errors(line, 5, 1000.0, 1000.0, 0.0, 40.0, "lateral") != []           # wrong spacing
    assert _row_errors(line, 5, 1010.0, 1000.0, 0.0, 37.5, "lateral") != []           # off-centre
    assert _row_errors([(x, y, 5.0) for x, y, _ in line], 5, 1000.0, 1000.0, 0.0, 37.5, "lateral") != []
    ring = [(3000.0 + 500.0 * math.cos(math.radians(a)), 1000.0 + 500.0 * math.sin(math.radians(a)),
             _wrap(a + 180.0)) for a in (135.0, 157.5, 180.0, 202.5, 225.0)]
    assert _concave_errors(ring, 5, (3000.0, 1000.0), 1000.0, 1000.0, 500.0, 90.0) == []
    bad = list(ring)
    bad[1] = (bad[1][0] + 0.01, bad[1][1], bad[1][2])                                  # off the circle
    assert _concave_errors(bad, 5, (3000.0, 1000.0), 1000.0, 1000.0, 500.0, 90.0) != []
    assert _concave_errors(ring, 5, (3000.0, 1000.0), 1000.0, 1000.0, 500.0, 100.0) != []  # wrong arc
    cols = [(1000.0 + 37.5 * r, 1000.0 + 37.5 * c, 0.0) for r in range(2) for c in range(3)]   # facing 0: rows along x
    assert _box_errors(cols, 6, 3, 1018.75, 1037.5, 0.0, 37.5) == []                   # anchor = lattice centre
    assert _box_errors(cols, 6, 3, 1000.0, 1000.0, 0.0, 37.5) != []                    # not centred on (x, y)


# ---------------------------------------------------------------- determinism and rounding

PARAMS = {
    "line": {}, "column": {}, "box": {"cols": 4},
    "concave": {"center": (3000.0, 1000.0), "R": 500.0, "arc_deg": 90.0},
    "screen": {"screen_r": 200.0, "arc_deg": 120.0},
}


def _unrounded(places):
    return [p for p in places for v in p[:2] if round(v, 6) != v]


@pytest.mark.parametrize("kind", sorted(PARAMS))
def test_place_is_deterministic_and_rounded_to_6_decimals(kind):
    """SPEC 7 ('pure geometry: no draws') and the driver contract (coordinates rounded to 6
    decimals): two identical calls return identical lists, and every x and y is already rounded
    to 6 decimals, with awkward inputs that would not round themselves."""
    args = (kind, 7, 1234.5678912, 987.6543219, 33.3333333, 37.5)
    a = place(*args, **copy.deepcopy(PARAMS[kind]))
    b = place(*args, **copy.deepcopy(PARAMS[kind]))
    assert a == b and len(a) == 7
    assert _unrounded(a) == []


def test_rounding_detector_rejects_unrounded_values():
    """Negative control for the rounding check: a list with a 9 decimal coordinate is flagged."""
    assert _unrounded([(1.123456789, 2.0, 0.0)]) != []
    assert _unrounded([(1.123457, 2.0, 0.0)]) == []


# ---------------------------------------------------------------- scenario integration (SPEC 8)

def _scn(scenarios_dir, group):
    scn = scenario.load(str(scenarios_dir / "base.toml"))
    scn["groups"] = [group]
    return scn


def _group(**kw):
    g = {"side": "A", "type": "raider", "count": 6, "x": 1500.0, "y": 1000.0, "facing": 0.0,
         "layer": 3, "order": "hold"}
    g.update(kw)
    return g


# kind, extra group keys (SPEC 8), spacing the spawn must use (default 2.5 * body_radius 15 = 37.5)
SCENARIO_CASES = [
    ("line", {}, 37.5),
    ("column", {"spacing": 60.0}, 60.0),
    ("box", {"cols": 3}, 37.5),
    ("concave", {"center": [3000.0, 1000.0], "R": 500.0, "arc_deg": 90.0}, 37.5),
    ("screen", {"screen_r": 200.0, "arc_deg": 120.0}, 37.5),
]


def _expected(kind, count, g, spacing):
    extra = {k: v for k, v in g.items() if k in ("cols", "center", "R", "arc_deg", "screen_r")}
    return place(kind, count, g["x"], g["y"], g["facing"], spacing, **extra)


@pytest.mark.parametrize("kind,extra,spacing", SCENARIO_CASES)
def test_scenario_group_spawns_equal_place(scenarios_dir, kind, extra, spacing):
    """SPEC 8 (group keys: spacing; box cols; concave center, R, arc_deg; screen screen_r, arc_deg)
    and 7: a TOML-shaped scenario converts with `scenario.to_c` and the spawn positions and
    facings equal `formations.place` for the same arguments (jitter is applied later, in C)."""
    g = _group(formation=kind, **extra)
    sc = scenario.to_c(_scn(scenarios_dir, g))
    want = _expected(kind, g["count"], g, spacing)
    assert sc.n_spawns == len(want) == g["count"]
    for i, (x, y, f) in enumerate(want):
        s = sc.spawns[i]
        assert (s.x, s.y) == pytest.approx((x, y), abs=1e-9), (kind, i)
        assert s.facing_deg == pytest.approx(f, abs=1e-9), (kind, i)


@pytest.mark.parametrize("kind,key,old,new", [
    ("box", "cols", 3, 2),
    ("concave", "R", 500.0, 650.0),
    ("concave", "arc_deg", 90.0, 150.0),
    ("screen", "screen_r", 200.0, 320.0),
    ("screen", "arc_deg", 120.0, 60.0),
])
def test_scenario_formation_params_are_read_not_defaulted(scenarios_dir, kind, key, old, new):
    """SPEC 8 negative control: changing one formation key moves the spawns (to exactly what
    `place` gives for the new value, and away from the old placement), so the loader forwards
    the keys instead of ignoring them."""
    base_extra = dict(next(e for k, e, _ in SCENARIO_CASES if k == kind))
    first = _group(formation=kind, **base_extra)
    changed = _group(formation=kind, **{**base_extra, key: new})
    assert first[key] == old
    sc_old = scenario.to_c(_scn(scenarios_dir, first))
    sc_new = scenario.to_c(_scn(scenarios_dir, changed))
    old_pos = [(sc_old.spawns[i].x, sc_old.spawns[i].y) for i in range(sc_old.n_spawns)]
    new_pos = [(sc_new.spawns[i].x, sc_new.spawns[i].y) for i in range(sc_new.n_spawns)]
    assert old_pos != new_pos
    want = _expected(kind, changed["count"], changed, 37.5)
    assert new_pos == pytest.approx([(x, y) for x, y, _ in want], abs=1e-9)
