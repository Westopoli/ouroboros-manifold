"""Rung R1 terrain preset geometry (SPEC.md section 6), checked without running the sim.

These call `layerlab.terrain.build(terrain_dict)` (returns the filled ll_terrain) and
`layerlab.scenario.to_c(scn)` (validation that needs spawns). Masks: `open` bit L-1 set means
layer L is open at the cell; `land` likewise. Cell index = row * w_cells + col; the default grid
is 80 x 40 cells of 50 units, so the arena centre is column 40, row 20.

Readings chosen where SPEC 6 leaves a boundary open, so the tests pin geometry that any sane
reading satisfies and nothing finer:
- a strip `wt` cells thick has exactly `wt` blocked columns, and the columns next to the centre
  (39 and 40 for the default `cx`) are among them; which side takes the extra column is not tested;
- a `block` of bw x bh cells is that many cells, centred on the arena centre within one cell;
- the `wall`'s blocked rows run from row `end_gap` to row h_cells - end_gap - 1, and the `lane`
  channel is `ch` rows centred on the middle row, rows [20 - ch/2, 20 + ch/2); the lane's blocks
  run out to the arena's top and bottom rows.
"""
import numpy as np
import pytest

from conftest import grp, make_scenario
from layerlab import scenario, terrain

ALL = 0b11111
W, H, CELL = 80, 40, 50.0
BASE_TERRAIN = {"preset": "flat", "w_cells": W, "h_cells": H, "cell": CELL, "layer_spacing": 0.0}
INVALID = (ValueError, AssertionError)


def build(preset, **params):
    d = dict(BASE_TERRAIN)
    d["preset"] = preset
    d.update(params)
    return terrain.build(d)


def masks(t):
    n = t.w_cells * t.h_cells
    shape = (t.h_cells, t.w_cells)
    return (np.array(t.open[:n], dtype=np.uint8).reshape(shape),
            np.array(t.land[:n], dtype=np.uint8).reshape(shape))


def below(h):
    """Open mask where layers 1..h are blocked."""
    return ALL & ~((1 << h) - 1)


def blocked_cols(open_arr, row, full=ALL):
    return np.flatnonzero(open_arr[row] != full)


def test_flat_is_all_open_all_land_and_empty():
    """R-001-03 (every layer open: no restriction): `flat` is open and land on all five layers
    in every cell, with no slopes, cover, vantage or zones."""
    t = build("flat")
    o, l = masks(t)
    assert (o == ALL).all() and (l == ALL).all()
    assert (t.w_cells, t.h_cells, t.cell) == (W, H, CELL)
    assert t.n_slope == t.n_cover == t.n_vantage == t.n_zone == 0


@pytest.mark.parametrize("h", [1, 2, 3, 5])
def test_block_blocks_layers_1_to_h_inside_the_footprint(h):
    """R-001-01 / R-001-04 (binary mask per layer, layers 1..h blocked, h + 1..5 open): `block`
    of 10 x 10 cells at the arena centre: inside it open and land lose layers 1..h; outside
    every cell is untouched; open equals land everywhere."""
    o, l = masks(build("block", h=h))
    inside = o != ALL
    assert inside.sum() == 100
    assert (o[inside] == below(h)).all() and (l[inside] == below(h)).all()
    assert (o[~inside] == ALL).all() and (l[~inside] == ALL).all()
    rows, cols = np.nonzero(inside)
    assert rows.max() - rows.min() == 9 and cols.max() - cols.min() == 9
    assert abs((cols.min() + cols.max()) / 2 - 39.5) <= 1 and abs((rows.min() + rows.max()) / 2 - 19.5) <= 1
    assert inside[19, 39] and inside[20, 40]


def test_block_parameters_size_and_position():
    """SPEC 6 block keys bw bh cx cy: a 6 x 4 block centred on column 20, row 10 blocks 24 cells
    there and nothing else (negative: the arena centre is open)."""
    o, _ = masks(build("block", bw=6, bh=4, cx=20, cy=10, h=2))
    inside = o != ALL
    assert inside.sum() == 24
    rows, cols = np.nonzero(inside)
    assert abs((cols.min() + cols.max()) / 2 - 20) <= 1 and abs((rows.min() + rows.max()) / 2 - 10) <= 1
    assert inside[10, 20] and not inside[20, 40] and not inside[10, 40]


def test_wall_has_open_ends():
    """R-001-01 / R-001-02 (wall of height 2, SPEC 6 wall wt 4, end_gap 6): the strip is 4
    columns thick and blocks layers 1..2 for rows 6..33 only (28 rows); rows 0..5 and 34..39 are
    open on every layer in the strip's columns (the open ends: negative), and layers 3..5 are
    open throughout (positive)."""
    o, l = masks(build("wall", h=2))
    cols = blocked_cols(o, 20)
    assert len(cols) == 4 and 39 in cols and 40 in cols
    for row in range(H):
        wall_row = 6 <= row <= 33
        if wall_row:
            assert (o[row, cols] == below(2)).all() and (l[row, cols] == below(2)).all()
            assert len(blocked_cols(o, row)) == 4
        else:
            assert (o[row] == ALL).all() and (l[row] == ALL).all(), "row %d should be open" % row
    assert (o & 0b11100 == 0b11100).all(), "layers 3..5 must be open everywhere"
    assert build("wall", h=2).n_slope == 0


def test_wall_end_gap_parameter():
    """SPEC 6 wall end_gap: end_gap 10 blocks rows 10..29 and leaves rows 0..9 and 30..39 open."""
    o, _ = masks(build("wall", h=2, end_gap=10))
    blocked_rows = np.flatnonzero((o != ALL).any(axis=1))
    assert blocked_rows.min() == 10 and blocked_rows.max() == 29 and len(blocked_rows) == 20


@pytest.mark.parametrize("h", [1, 2, 3])
def test_barrier_spans_the_full_width_of_the_map(h):
    """R-001-01 / Q-001-04 (barrier: the case with no way round): a strip 4 columns thick, in
    every row, blocking layers 1..h in open and land; every other cell open on all layers."""
    o, l = masks(build("barrier", h=h))
    cols = blocked_cols(o, 0)
    assert len(cols) == 4 and 39 in cols and 40 in cols
    for row in range(H):
        assert np.array_equal(blocked_cols(o, row), cols), "row %d differs" % row
        assert (o[row, cols] == below(h)).all() and (l[row, cols] == below(h)).all()
    others = np.ones(W, dtype=bool)
    others[cols] = False
    assert (o[:, others] == ALL).all() and (l[:, others] == ALL).all()


def test_barrier_centre_column_parameter():
    """SPEC 6 barrier key cx: cx = 20 moves the strip to columns around 20 (negative: the arena
    centre columns are then open on every layer)."""
    o, _ = masks(build("barrier", h=2, cx=20))
    cols = blocked_cols(o, 5)
    assert len(cols) == 4 and 19 in cols and 20 in cols
    assert (o[:, 39:42] == ALL).all()


def test_lane_has_a_channel_open_on_every_layer():
    """R-001-01 / R-001-03 (lane: blocks above and below a channel, SPEC 6 lane wt 4, ch 8): in
    the strip's 4 columns, rows 16..23 (the channel) are open on all layers (positive); every
    other row of the strip blocks layers 1..h (negative), 32 blocked cells per strip column;
    nothing outside the strip is blocked."""
    h = 2
    o, l = masks(build("lane", h=h))
    cols = blocked_cols(o, 0)
    assert len(cols) == 4 and 39 in cols and 40 in cols
    for row in range(H):
        channel = 16 <= row <= 23
        want = ALL if channel else below(h)
        assert (o[row, cols] == want).all() and (l[row, cols] == want).all(), "row %d" % row
    for c in cols:
        assert (o[:, c] != ALL).sum() == 32
    others = np.ones(W, dtype=bool)
    others[cols] = False
    assert (o[:, others] == ALL).all()


def test_lane_channel_width_parameter():
    """SPEC 6 lane key ch: ch = 4 leaves rows 18..21 open in the strip and blocks the rest."""
    o, _ = masks(build("lane", h=2, ch=4))
    cols = blocked_cols(o, 0)
    open_rows = [r for r in range(H) if (o[r, cols] == ALL).all()]
    assert open_rows == [18, 19, 20, 21]


def _slope_fields(s):
    return (s.x0, s.y0, s.dx, s.dy, s.length, s.width, s.bottom_layer, s.top_layer)


@pytest.mark.parametrize("h,g,ground_land,plateau", [
    (1, 1, 0b00001, 0b11110),
    (2, 1, 0b00001, 0b11100),
    (2, 2, 0b00010, 0b11100),
])
def test_ramp_land_rules_and_slope(h, g, ground_land, plateau):
    """R-001-06 / R-001-07 (SPEC 6 ramp, x1 40, sl 600, sw 200): a barrier from column 40 to the
    far edge (the plateau) blocks layers 1..h in open. Land outside the plateau is only the ground
    layer g; land inside is only layers h + 1..5; open outside is all five layers. One slope on the
    face at mid-y: bottom edge centre (1975, 1000) (the centre of the last ground column, SPEC 6) on
    layer g, direction +x, length 600, width 200, top layer h + 1; its top edge centre (2575, 1000)
    is a plateau cell that is land on the top
    layer, and the cell just outside the face is land on layer g."""
    t = build("ramp", h=h, g=g)
    o, l = masks(t)
    assert (o[:, :40] == ALL).all() and (l[:, :40] == ground_land).all()
    assert (o[:, 40:] == plateau).all() and (l[:, 40:] == plateau).all()
    assert t.n_slope == 1
    assert _slope_fields(t.slope[0]) == (1975.0, 1000.0, 1.0, 0.0, 600.0, 200.0, g, h + 1)
    assert l[20, 39] & (1 << (g - 1))
    assert l[20, 52] & (1 << h)          # top edge cell (2575, 1000) on layer h + 1


def test_ramp_parameters_move_the_plateau_and_the_slope():
    """SPEC 6 ramp keys x1 and sl: x1 = 30, sl = 300 puts the plateau at column 30, the slope's
    bottom edge at (1475, 1000) and its top edge at (1775, 1000), a plateau cell."""
    t = build("ramp", h=1, x1=30, sl=300.0)
    o, l = masks(t)
    assert (o[:, :30] == ALL).all() and (o[:, 30:] == 0b11110).all()
    assert _slope_fields(t.slope[0])[:5] == (1475.0, 1000.0, 1.0, 0.0, 300.0)
    assert l[20, 36] & 0b10


def test_ramp_with_top_edge_outside_the_plateau_is_rejected():
    """SPEC 6 ramp ('the slope's top edge centre must fall inside the plateau; the preset asserts
    it'): sl = 2200 puts the top edge at x = 4200, beyond the 4000-wide map, and is an error
    (negative). sl = 1900 (top edge at x = 3900, still on the plateau) builds (positive)."""
    with pytest.raises(INVALID):
        build("ramp", h=1, sl=2200.0)
    assert build("ramp", h=1, sl=1900.0).n_slope == 1


def _one_flyer(layer, x, y, terrain_dict, kind="fly"):
    scn = make_scenario([grp("A", "mover", x, y, layer), grp("B", "raider", 3900.0, 150.0, 5)],
                        terrain=terrain_dict)
    scn["types"]["mover"] = {**scn["types"]["raider"], "movement_kind": kind}
    return scn


def test_spawn_on_a_blocked_cell_is_an_error_before_the_c_call():
    """SPEC 6 ('every preset validates: spawns land on open cells; violations raise before the C
    call'; R-001-01): a flyer on layer 1 at the centre of an h = 2 block is rejected (negative).
    Controls: the same position on layer 3 (open) and a layer-1 spawn off the block are accepted."""
    block = {"preset": "block", "h": 2}
    with pytest.raises(INVALID):
        scenario.to_c(_one_flyer(1, 2000.0, 1000.0, block))
    scenario.to_c(_one_flyer(3, 2000.0, 1000.0, block))
    scenario.to_c(_one_flyer(1, 1000.0, 1000.0, block))


def test_walker_spawn_needs_land_not_just_open():
    """SPEC 6 ('spawns land on open (and land for walkers) cells'; R-001-07): on a `ramp` (h = 1)
    a walker on layer 2 over the ground side is rejected (open but not land) and so is a walker on
    layer 1 on the plateau (blocked). Controls: a flyer on layer 2 over the ground, a walker on
    layer 1 on the ground, and a walker on layer 2 on the plateau are all accepted."""
    ramp = {"preset": "ramp", "h": 1}
    with pytest.raises(INVALID):
        scenario.to_c(_one_flyer(2, 1000.0, 1000.0, ramp, kind="walk"))
    with pytest.raises(INVALID):
        scenario.to_c(_one_flyer(1, 3000.0, 1000.0, ramp, kind="walk"))
    scenario.to_c(_one_flyer(2, 1000.0, 1000.0, ramp, kind="fly"))
    scenario.to_c(_one_flyer(1, 1000.0, 1000.0, ramp, kind="walk"))
    scenario.to_c(_one_flyer(2, 3000.0, 1000.0, ramp, kind="walk"))


def test_explicit_terrain_extras_reach_the_c_struct():
    """SPEC 6 explicit extras ([[terrain.cover]], [[terrain.vantage]], [[terrain.zone]],
    [[terrain.slope]]): on a flat map they arrive in the struct field for field, with the slope
    direction normalised by the loader ((3, 4) becomes (0.6, 0.8))."""
    extras = {
        "cover": [{"x": 100.0, "y": 200.0, "r": 30.0, "height_layer": 2}],
        "vantage": [{"x": 300.0, "y": 400.0, "r": 50.0}],
        "zone": [{"x": 500.0, "y": 600.0, "r": 70.0, "intensity": 0.5, "layer": 3}],
        "slope": [{"x0": 1000.0, "y0": 1000.0, "dx": 3.0, "dy": 4.0, "length": 600.0, "width": 100.0,
                   "bottom_layer": 1, "top_layer": 2}],
    }
    sc = scenario.to_c(make_scenario([grp("A", "raider", 500.0, 500.0, 1)], terrain=extras))
    t = sc.terrain
    assert (t.n_cover, t.n_vantage, t.n_zone, t.n_slope) == (1, 1, 1, 1)
    assert (t.cover[0].x, t.cover[0].y, t.cover[0].r, t.cover[0].height_layer) == (100.0, 200.0, 30.0, 2)
    assert (t.vantage[0].x, t.vantage[0].y, t.vantage[0].r) == (300.0, 400.0, 50.0)
    z = t.zone[0]
    assert (z.x, z.y, z.r, z.intensity, z.layer) == (500.0, 600.0, 70.0, 0.5, 3)
    s = t.slope[0]
    assert (s.dx, s.dy) == pytest.approx((0.6, 0.8))
    assert (s.x0, s.y0, s.length, s.width, s.bottom_layer, s.top_layer) == (1000.0, 1000.0, 600.0, 100.0, 1, 2)


def test_overlapping_slope_footprints_are_rejected():
    """SPEC 6 ('slope footprints do not overlap'): two slopes on a flat map whose corridors
    overlap raise (negative); the same two moved 500 apart in y build (positive)."""
    def slopes(y2):
        return {"slope": [
            {"x0": 1000.0, "y0": 1000.0, "dx": 1.0, "dy": 0.0, "length": 600.0, "width": 200.0,
             "bottom_layer": 1, "top_layer": 2},
            {"x0": 1300.0, "y0": y2, "dx": 1.0, "dy": 0.0, "length": 600.0, "width": 200.0,
             "bottom_layer": 1, "top_layer": 2}]}
    with pytest.raises(INVALID):
        scenario.to_c(make_scenario([grp("A", "raider", 500.0, 500.0, 1)], terrain=slopes(1050.0)))
    sc = scenario.to_c(make_scenario([grp("A", "raider", 500.0, 500.0, 1)], terrain=slopes(1500.0)))
    assert sc.terrain.n_slope == 2
