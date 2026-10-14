# spec: LAB-REV2-L6 (docs/northstar/plans/2026-10-14-skill-lab-rev2-spec.md, rulings 10 and 11, the L6 row); R-005-09 (ground vision), S-164 (reach by type), R-004-06 (slope midline)
"""The ground scene s1_slope_top (M1): its structure, its knob grid, and the retirement of ground/highground.py.

The library is used only to read seed 11's generated field (bands, slopes, walkable ground); no fight runs here (the fights
are in tests/skilllab/integration/test_ground_slope_real.py).

Contract these tests fix for scripts/skilllab/ground/scenes_ground.py (the implementation comes later):
  SCENE = "s1_slope_top", SEED = 11, CANVAS (a canvas on which seed 11 has slopes: 4000 has none, 12000 has six)
  slope_top(size=16) -> build(enemy_heads, swap) -> Setup; build.labels["scene"] == SCENE, build.labels["prefight"] == "ok"
    side 0 is the attacker (size units, M1: Vanguard and Raider in equal halves), side 1 the holder (enemy_heads units, same mix)
  SLOPE_TOP_KNOBS = {parameter name: grid tuple}, INERT_KNOBS = {parameter name: reason string} for a knob that changes nothing here
Test numbers are test drafts (2026-10-14), Westley may tighten: FOOT_NEAR."""
import ctypes
import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.skilllab import engine, formations  # noqa: E402
from scripts.skilllab.ground import scenes_ground as sg  # noqa: E402

SEED = 11
FOOT_NEAR = 300.0                        # test draft (2026-10-14): the attackers start within this of the slope's foot
GRID = {"OM_TP_SIGHT_EYE_HEIGHT": (25, 50, 100, 200),
        "OM_TP_GROUND_FLYER_SEEN_MULT": (1.25, 1.5, 2, 3),
        "OM_TP_SLOPE_UP_DIV": (1.0, 1.1, 1.3, 2.0)}        # the L6 row; the slope divisor is a DRAFT (the 0.25x band means nothing near 1)
DEFAULTS = {"OM_TP_SIGHT_EYE_HEIGHT": 50.0, "OM_TP_GROUND_FLYER_SEEN_MULT": 1.5, "OM_TP_SLOPE_UP_DIV": 1.1}   # pp_contract.md rows 62, 64, 65
RANGES = {"OM_TP_SIGHT_EYE_HEIGHT": (0.0, 1000.0), "OM_TP_GROUND_FLYER_SEEN_MULT": (1.0, 10.0), "OM_TP_SLOPE_UP_DIV": (1.0, 10.0)}


class _Slope(ctypes.Structure):
    _fields_ = [(n, ctypes.c_double) for n in ("x0", "y0", "x1", "y1", "mx", "my", "length")] + \
               [("lower_band", ctypes.c_int32), ("upper_band", ctypes.c_int32)]


@pytest.fixture(scope="module")
def lib():
    return engine.Engine()


def _field(lib, canvas):
    w = lib.new_world(0)
    lib.set_canvas(w, canvas, canvas)
    assert lib.terrain_generate(w, SEED, canvas) == 0
    return w


def _slopes(lib, w):
    out = []
    for i in range(int(lib._lib.om_terrain_slope_count(w))):
        s = _Slope()
        assert lib._lib.om_terrain_slope_get(w, i, ctypes.byref(s)) == 0
        out.append(s)
    return out


def _height(lib, w, x, y):
    fn = lib._lib.om_terrain_height_at
    fn.restype = ctypes.c_double
    return float(fn(w, ctypes.c_double(x), ctypes.c_double(y)))


@pytest.fixture(scope="module")
def field(lib):
    w = _field(lib, sg.CANVAS)
    yield w
    lib.free_world(w)


@pytest.fixture(scope="module")
def setup(lib):
    return sg.slope_top()(16, False)


def _side(setup, side):
    return [g for g in setup.groups if g.side == side]


def _placed(groups):
    return [p for g in groups for p in formations.place(g.formation, g.count, g.x, g.y, g.facing_deg, g.params)]


def _centroid(points):
    return sum(p[0] for p in points) / len(points), sum(p[1] for p in points) / len(points)


# ---------------------------------------------------------------- control: the field itself (green before the build)

def test_control_seed_11_has_no_slope_at_canvas_4000_and_six_at_12000(lib):
    """Why the scene cannot live on the 4000 canvas: seed 11 generates no slope there, so a layer-0 attacker aimed at a higher
    band is `unroutable` by construction. At 12000 the field has six slopes, two of them (index 0 and 1) joining bands 2 and 3."""
    w4, w12 = _field(lib, 4000.0), _field(lib, 12000.0)
    try:
        assert int(lib._lib.om_terrain_slope_count(w4)) == 0
        slopes = _slopes(lib, w12)
        assert len(slopes) == 6 and sum(1 for s in slopes if (s.lower_band, s.upper_band) == (2, 3)) == 3
    finally:
        lib.free_world(w4)
        lib.free_world(w12)


# ---------------------------------------------------------------- the scene's identity

def test_names_seed_and_a_canvas_on_which_the_field_has_slopes(lib, setup):
    assert sg.SCENE == "s1_slope_top" and sg.SEED == SEED
    w = _field(lib, sg.CANVAS)
    try:
        assert len(_slopes(lib, w)) >= 1, "canvas %r has no slope on seed 11" % (sg.CANVAS,)
    finally:
        lib.free_world(w)
    t = setup.terrain
    assert t is not None and t.field_seed == SEED and t.canvas == (sg.CANVAS, sg.CANVAS)
    assert t.blocks == () and t.covers == ()


def test_labels_name_the_scene_and_the_preflight_is_ok(lib):
    build = sg.slope_top()
    s = build(16, False)
    assert build.labels["scene"] == "s1_slope_top"
    assert build.labels["prefight"] == "ok"
    from scripts.skilllab import scenes
    assert scenes.preflight(s, lib) == "ok"


def test_the_build_is_deterministic_and_swap_does_not_change_the_setup():
    build = sg.slope_top()
    assert build(16, False) == build(16, False) == build(16, True)


# ---------------------------------------------------------------- M1 and the orders

@pytest.mark.parametrize("size,heads", [(16, 16), (24, 12), (8, 24), (16, 48)])
def test_both_sides_field_the_m1_mix_in_equal_halves(size, heads):
    s = sg.slope_top(size)(heads, False)
    for side, n in ((0, size), (1, heads)):
        counts = {}
        for g in _side(s, side):
            counts[g.unit] = counts.get(g.unit, 0) + g.count
        assert set(counts) == {"Vanguard", "Raider"}, counts
        assert sum(counts.values()) == n and abs(counts["Vanguard"] - counts["Raider"]) <= 1, counts


def test_the_holder_guards_and_the_attacker_attack_moves_to_the_shared_point(setup):
    assert {g.order for g in _side(setup, 1)} == {"guard"}
    assert {g.order for g in _side(setup, 0)} == {"attack_move"}
    assert setup.point is not None
    assert all(g.goal in (None, setup.point) for g in setup.groups)


def test_the_shared_point_is_the_holders_placed_mean(setup):
    hx, hy = _centroid(_placed(_side(setup, 1)))
    assert setup.point == pytest.approx((hx, hy), abs=1e-6)


# ---------------------------------------------------------------- the slope: the holder is past its midline on the top band

def test_holder_is_one_layer_above_the_attacker_and_each_side_shares_a_layer(setup):
    la, lh = {g.layer for g in _side(setup, 0)}, {g.layer for g in _side(setup, 1)}
    assert len(la) == 1 and len(lh) == 1 and lh.pop() == la.pop() + 1


def test_the_attacker_starts_at_the_foot_of_a_slope_that_joins_its_layer_to_the_holders(lib, field, setup):
    la, lh = _side(setup, 0)[0].layer, _side(setup, 1)[0].layer
    ax, ay = _centroid(_placed(_side(setup, 0)))
    joining = [s for s in _slopes(lib, field) if (s.lower_band, s.upper_band) == (la + 1, lh + 1)]
    assert joining, "no slope of seed 11 joins band %d to band %d" % (la + 1, lh + 1)
    foot = min(math.hypot(s.x0 - ax, s.y0 - ay) for s in joining)
    assert foot <= FOOT_NEAR, "the attackers' centroid is %.0f wu from the nearest foot" % foot


def test_the_shared_point_is_past_the_slopes_midline_on_the_top_band_and_higher_than_the_attackers(lib, field, setup):
    la, lh = _side(setup, 0)[0].layer, _side(setup, 1)[0].layer
    ax, ay = _centroid(_placed(_side(setup, 0)))
    px, py = setup.point
    joining = [s for s in _slopes(lib, field) if (s.lower_band, s.upper_band) == (la + 1, lh + 1)]
    s = min(joining, key=lambda s: math.hypot(s.x0 - ax, s.y0 - ay))
    ux, uy = s.x1 - s.x0, s.y1 - s.y0
    along = lambda x, y: ((x - s.x0) * ux + (y - s.y0) * uy) / (ux * ux + uy * uy)
    assert along(px, py) >= along(s.mx, s.my), "the holder's point is below the slope's midline"
    assert lib.terrain_band_at(field, px, py) == lh + 1
    assert _height(lib, field, px, py) > _height(lib, field, ax, ay)


@pytest.mark.parametrize("size,heads", [(16, 16), (16, 8), (16, 48), (24, 12)])
def test_every_placed_unit_stands_on_walkable_ground(lib, field, size, heads):
    """A walker spawned on ground it cannot walk gets id 0 and is silently counted dead (measured 2026-10-14: 4 of 16
    attackers lost that way in a first sketch of this scene). The scan runs the holder at 8 to 48 units (ruling 4)."""
    setup = sg.slope_top(size)(heads, False)
    for g in setup.groups:
        for x, y in formations.place(g.formation, g.count, g.x, g.y, g.facing_deg, g.params):
            assert lib.terrain_walkable_at(field, x, y), "unit at (%.0f, %.0f) is not walkable ground" % (x, y)


# ---------------------------------------------------------------- the knob grid (rulings 10 and 11)

def test_the_grid_equals_the_lists():
    assert dict(sg.SLOPE_TOP_KNOBS) == GRID
    assert [tuple(sg.SLOPE_TOP_KNOBS[k]) for k in GRID] == [tuple(v) for v in GRID.values()]


@pytest.mark.parametrize("name", list(GRID))
def test_each_grid_is_ascending_inside_the_parameter_range_and_holds_the_default(name):
    values = tuple(sg.SLOPE_TOP_KNOBS[name])
    lo, hi = RANGES[name]
    assert list(values) == sorted(set(values)) and 3 <= len(values) <= 5          # ruling 11: three to five points
    assert all(lo <= v <= hi for v in values) and DEFAULTS[name] in values        # the sweep starts at the bible's value


def test_the_defaults_in_the_test_are_the_engines(lib):
    w = lib.new_world(0)
    try:
        for name, default in DEFAULTS.items():
            assert lib.get_param(w, lib.param_id(name)) == pytest.approx(default)
    finally:
        lib.free_world(w)


@pytest.mark.parametrize("name", ["OM_TP_SIGHT_EYE_HEIGHT", "OM_TP_GROUND_FLYER_SEEN_MULT"])
def test_the_factor_steps_stay_inside_a_quarter_to_four_times_the_default(name):
    """Ruling 11. The slope divisor is exempt (DRAFT, L6 row): a divisor near 1 makes the 0.25x band meaningless."""
    for v in sg.SLOPE_TOP_KNOBS[name]:
        assert 0.25 <= v / DEFAULTS[name] <= 4.0, (name, v)


def test_inert_knobs_name_a_known_knob_with_a_reason_and_the_climb_is_not_inert():
    assert set(sg.INERT_KNOBS) <= set(GRID)
    assert all(isinstance(r, str) and len(r) > 10 for r in sg.INERT_KNOBS.values())
    assert "OM_TP_SLOPE_UP_DIV" not in sg.INERT_KNOBS, "the climb speed is the one knob this scene must move (walkers)"


# ---------------------------------------------------------------- ground/highground.py retired (R-005-09, S-164)

def test_highground_py_and_its_tests_are_gone():
    """R-005-09 (high ground sees down, by terrain) and S-164 (reach by type) replace the layer-change stand-in. What the
    stand-in showed, and where the replacement shows it: a climb that takes time (OM_TP_SLOPE_UP_DIV, tested here and in
    test_ground_slope_real.py), defenders holding the top on guard (test_the_holder_guards_...), cross-layer reach rules
    (the reach table, test_ground_slope_real.py), no ground (now a generated field, test_names_seed_...)."""
    ground = ROOT / "scripts/skilllab/ground"
    assert not (ground / "highground.py").exists(), "ground/highground.py is retired with R-005-09 / S-164"
    here = Path(__file__).resolve().parent
    assert not (here / "test_highground.py").exists() and not (here / "test_highground_real.py").exists()


def test_the_climb_row_of_the_retired_stand_in_lives_on_in_the_replacement():
    """Parity row: the stand-in swept climb time; the replacement sweeps the slope divisor and the holders stay on guard."""
    assert "OM_TP_SLOPE_UP_DIV" in sg.SLOPE_TOP_KNOBS and "OM_TP_SLOPE_UP_DIV" not in sg.INERT_KNOBS


def test_the_ground_readme_describes_the_scene_and_not_the_retired_module():
    text = (ROOT / "scripts/skilllab/ground/README.md").read_text()
    assert "s1_slope_top" in text and "highground" not in text
    for name in GRID:
        assert name in text, "ground/README.md does not mention %s" % name
    for name in sg.INERT_KNOBS:
        assert "inert" in text.lower(), "ground/README.md must say which knob is inert (%s)" % name
