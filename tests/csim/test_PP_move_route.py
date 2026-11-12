"""PP-move / PP-mapgen rule tests, routing, solid terrain and terrain slow (P3 route part, wave A4).

Kept apart from the other PP movement tests so that it can be split off and built later (plan, "How it is run":
A4 is routing, terrain and cover height). Proves E-13 R-097-01, R-097-06 (terrain slow, the first rule of that
number), R-097-09 (a unit found inside solid terrain is moved out; Westley, 2026-10-02: "A unit in solid terrain
is moved out, not stalled as in the Python"), R-099-04 (collision pushes slide along blocked cells), E-01
R-001-01, R-001-02, R-001-03, R-001-04 (S-001), E-13 R-098-02 and E-12 R-089-01 for sight and fire through a blocked
cell, and the OM_TP_ROUTE_AROUND_TERRAIN switch, both ways.

Terrain is hand-placed (P4, map content, is held for Westley's environment design): `om_map_block_rect`
(new contract, brief G2) and the existing `om_map_set_obstacle_density`. The canvas is set with `om_map_set_canvas`.

Cell arithmetic (100 wu cells, R-097-01): the wall below is column 5 (x 500..600), rows 0 to 7 (y 0..800). Rectangles are
given strictly inside the cell edges (510..590, 10..790) so that they cover exactly those cells whether the
rectangle's far edge is read as inclusive or not.

Layer indexing: the C numbers unit layers from 0; the scenes pick layers so that the verdict is the same whether the
"1 to 2" blocked range is read from 0 or from 1: blocked on layers 1 to 2, a unit on layer 1 is blocked and a unit
on layer 4 is not.

Loop bounds (400 or 600 ticks) are generous run limits so that a broken build ends; they are not rule thresholds.
"""
import ctypes
import math
import pathlib
import re

import pytest

from conftest import OMFeature

RAIDER = 0
FRIEND, ENEMY = 0, 1
POS_TOL = 0.05
ALL_LAYERS = (0, 4)
REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]

CANVAS = (2000.0, 2000.0)
WALL_X = (500.0, 600.0)      # blocked column 5
WALL_Y_TOP = 800.0           # blocked rows 0..7


@pytest.fixture
def tw_open(lib, world_factory):
    """A tactical world with no canvas set (today's state): for the scenes that need no grid size."""
    w = world_factory(n_regions=1)
    lib.om_world_set_feature(w, OMFeature.TACTICAL, 1)
    return w


@pytest.fixture
def tw(lib, tw_open):
    """A tactical world with the 2000 x 2000 canvas set (new contract call, red until PP-contract lands it)."""
    assert lib.om_map_set_canvas(tw_open, CANVAS[0], CANVAS[1]) == 0
    # Test-defect, A164: these scenes test same-layer routing; routing across layers (G4) is its own tests
    assert lib.om_tactical_set_param(tw_open, _tp("OM_TP_ROUTE_ACROSS_LAYERS"), 0.0) == 0
    return tw_open


def _wall(lib, w, layers=ALL_LAYERS):
    """Column 5, rows 0..7 blocked on the given inclusive layer range."""
    assert lib.om_map_block_rect(w, 510.0, 10.0, 590.0, 790.0, layers[0], layers[1]) == 0


def _in_wall(x, y):
    return WALL_X[0] <= x < WALL_X[1] and 0.0 <= y < WALL_Y_TOP


def _angle_diff(a, b):
    return (a - b + math.pi) % (2.0 * math.pi) - math.pi


def _walk(lib, w, u, ticks):
    """Positions after each of `ticks` tactical ticks (the start position is not included)."""
    out = []
    for _ in range(ticks):
        lib.om_tactical_step(w)
        out.append(lib.om_unit_get_pos(w, u))
    return out


def _tp(name):
    text = (REPO_ROOT / "csrc/ouroboros_sim.h").read_text()
    m = re.search(r"enum\s+(?:om_tac_param\s*)?\{([^{}]*?\bOM_TP_[A-Z0-9_]+[^{}]*?)\}\s*(?:om_tac_param)?\s*;", text, re.S)
    assert m, "csrc/ouroboros_sim.h has no enum om_tac_param (PP-contract has not landed)"
    body = re.sub(r"/\*.*?\*/", "", m.group(1), flags=re.S)
    nxt = 0
    for item in body.split(","):
        item = item.strip()
        if not item:
            continue
        if "=" in item:
            key, val = [t.strip() for t in item.split("=", 1)]
            nxt = int(val, 0)
        else:
            key = item
        if key == name:
            return nxt
        nxt += 1
    raise AssertionError(f"{name} is not a member of om_tac_param")


# ---------------------------------------------------------------- contract

def test_P3_block_rect_contract_returns_0_and_fills_the_accessibility_grid(lib, tw):
    """Plan appendix / brief G2: `om_map_block_rect(w, x0, y0, x1, y1, layer_lo, layer_hi)` blocks the route-grid cells
    the rectangle covers on a range of layers; `om_map_sample_layer_accessibility` reads the grid (R-001-04: binary,
    open = 1, blocked = 0). With the wall blocked on layers 1 to 2: inside it layers 1 and 2 are blocked and layer 4 is
    open; outside it every layer is open. The accessibility call is a stub that returns 0 today."""
    _wall(lib, tw, (1, 2))
    for layer, want in ((1, 0), (2, 0), (4, 1)):
        assert lib.om_map_sample_layer_accessibility(tw, 550.0, 400.0, layer) == want, f"inside the wall, layer {layer}"
    for layer in (1, 2, 4):
        assert lib.om_map_sample_layer_accessibility(tw, 300.0, 400.0, layer) == 1, f"outside the wall, layer {layer}"
    assert lib.om_map_sample_layer_accessibility(tw, 550.0, 900.0, 1) == 1, "above the wall (row 9), layer 1"


# ---------------------------------------------------------------- routing around solid terrain

def test_R_097_01_with_nothing_in_the_way_the_route_is_the_straight_line(lib, tw_open):
    """R-097-01 / brief G2: with no blocked cell on the straight line the path is the straight line. A Raider (300,400)
    ordered to (900,400) walks +x along y = 400 and arrives. Positive control for the routing tests; green today."""
    tw = tw_open
    u = lib.om_unit_spawn(tw, RAIDER, FRIEND, 300.0, 400.0, 0)
    lib.om_command_move(tw, u, 900.0, 400.0)
    trace = _walk(lib, tw, u, 100)
    assert all(abs(y - 400.0) < POS_TOL for _, y in trace)
    assert trace[-1][0] == pytest.approx(900.0, abs=30.0)


def test_R_097_01_route_goes_around_a_wall_and_never_enters_a_blocked_cell(lib, tw):
    """R-097-01 / R-001-03 inverse / E-13 invariant "a unit never enters a blocked cell": a Raider at (300,400) ordered to
    (900,400) behind a wall (column 5, rows 0..7) takes the shortest route round its open end (above y = 800), straightened
    by line of sight: no tick has it inside a blocked cell, it crosses the wall's column only above y = 800, the trip is
    longer than the straight 600 wu, and it arrives within 30 wu of the point."""
    _wall(lib, tw)
    u = lib.om_unit_spawn(tw, RAIDER, FRIEND, 300.0, 400.0, 0)
    lib.om_command_move(tw, u, 900.0, 400.0)
    x0, y0 = lib.om_unit_get_pos(tw, u)
    length = 0.0
    arrived = False
    for k in range(600):
        lib.om_tactical_step(tw)
        x, y = lib.om_unit_get_pos(tw, u)
        length += math.hypot(x - x0, y - y0)
        x0, y0 = x, y
        assert not _in_wall(x, y), f"tick {k + 1}: unit inside the blocked wall at ({x:.1f}, {y:.1f})"
        if WALL_X[0] <= x < WALL_X[1]:
            assert y >= WALL_Y_TOP, f"tick {k + 1}: crossed the wall's column below its open end"
        if math.hypot(x - 900.0, y - 400.0) <= 30.0:
            arrived = True
            break
    assert arrived, "the routed unit never arrived"
    assert length > 600.0 + 100.0, "the trip is not longer than the straight line by a detour"


def test_R_097_01_two_masses_with_a_200_wu_gap_the_unit_goes_through_the_gap(lib, tw):
    """Brief G2 test: two masses (column 5, rows 0..7 and rows 10..19) leave a 200 wu gap (y 800..1000). A unit ordered
    to the far side goes through the gap and never occupies a blocked cell; the trip is longer than the straight line."""
    assert lib.om_map_block_rect(tw, 510.0, 10.0, 590.0, 790.0, 0, 4) == 0
    assert lib.om_map_block_rect(tw, 510.0, 1010.0, 590.0, 1990.0, 0, 4) == 0
    u = lib.om_unit_spawn(tw, RAIDER, FRIEND, 300.0, 400.0, 0)
    lib.om_command_move(tw, u, 900.0, 400.0)
    crossed = False
    for k in range(600):
        lib.om_tactical_step(tw)
        x, y = lib.om_unit_get_pos(tw, u)
        if WALL_X[0] <= x < WALL_X[1]:
            crossed = True
            assert 800.0 <= y < 1000.0, f"tick {k + 1}: in the wall's column outside the gap at ({x:.1f}, {y:.1f})"
        if math.hypot(x - 900.0, y - 400.0) <= 30.0:
            break
    assert crossed, "the unit never crossed the wall's column"
    assert math.hypot(*(a - b for a, b in zip(lib.om_unit_get_pos(tw, u), (900.0, 400.0)))) <= 30.0


def test_R_097_01_no_route_leaves_the_unit_stopped_beside_the_wall_not_inside_a_cell(lib, tw):
    """Brief G2 test: a destination with no route leaves the unit stopped at the nearest reachable point, not frozen
    inside a cell. A wall the whole height of the canvas (column 5) cuts the map; the unit at (300,400) is ordered to
    (900,400). It ends outside the wall, in the open column next to it (x in 400..500), not moving."""
    assert lib.om_map_block_rect(tw, 510.0, 10.0, 590.0, 1990.0, 0, 4) == 0
    u = lib.om_unit_spawn(tw, RAIDER, FRIEND, 300.0, 400.0, 0)
    lib.om_command_move(tw, u, 900.0, 400.0)
    trace = _walk(lib, tw, u, 150)
    assert not any(WALL_X[0] <= x < WALL_X[1] for x, _ in trace), "the unit entered the blocked column"
    x, y = trace[-1]
    assert 400.0 <= x < 500.0, f"stopped at x = {x:.1f}, not in the open column beside the wall"
    assert trace[-1] == pytest.approx(trace[-2], abs=POS_TOL), "the unit is still moving"


def test_R_001_01_02_blocked_layers_detour_other_layers_pass_straight_over(lib, tw):
    """E-01 R-001-01 / R-001-02: where layers 1 and 2 are blocked, a unit on layer 1 detours round the area on its layer;
    a unit on layer 4 passes straight through with no detour (along y = 400, inside the wall's column, arriving
    in a straight run)."""
    _wall(lib, tw, (1, 2))
    low = lib.om_unit_spawn(tw, RAIDER, FRIEND, 300.0, 400.0, 1)
    high = lib.om_unit_spawn(tw, RAIDER, FRIEND, 300.0, 300.0, 4)
    lib.om_command_move(tw, low, 900.0, 400.0)
    lib.om_command_move(tw, high, 900.0, 300.0)
    crossed_straight = False
    for k in range(600):
        lib.om_tactical_step(tw)
        lx, ly = lib.om_unit_get_pos(tw, low)
        hx, hy = lib.om_unit_get_pos(tw, high)
        assert not _in_wall(lx, ly), f"tick {k + 1}: the layer 1 unit entered the blocked wall"
        assert abs(hy - 300.0) < POS_TOL, f"tick {k + 1}: the layer 4 unit detoured"
        if WALL_X[0] <= hx < WALL_X[1]:
            crossed_straight = True
    assert crossed_straight, "the layer 4 unit never crossed the wall's column"


# ---------------------------------------------------------------- a unit inside solid terrain is moved out

def test_R_097_09_unit_found_inside_a_blocked_cell_is_moved_to_the_nearest_open_cell(lib, tw):
    """R-097-09 as ruled (Westley, 2026-10-02: moved out, not stalled): a unit found inside a blocked cell on its layer
    is moved to the nearest open cell. The unit idles at (520,420), inside the wall (column 5, row 4); the nearest open
    cell is column 4, row 4 (x 400..500, y 400..500). After one tick it is there. Control: the same position on layer 3,
    where the wall (layers 1 to 2) does not exist, is left alone."""
    _wall(lib, tw, (1, 2))
    stuck = lib.om_unit_spawn(tw, RAIDER, FRIEND, 520.0, 420.0, 1)
    free = lib.om_unit_spawn(tw, RAIDER, FRIEND, 520.0, 420.0, 3)
    lib.om_tactical_step(tw)
    x, y = lib.om_unit_get_pos(tw, stuck)
    assert 400.0 <= x < 500.0 and 400.0 <= y < 500.0, f"not moved to the nearest open cell: ({x:.1f}, {y:.1f})"
    assert lib.om_unit_get_pos(tw, free) == (520.0, 420.0)


# ---------------------------------------------------------------- threshold 0.7 and terrain slow

def _density_band(lib, w, d, cols=range(3, 10), row=4):
    for c in cols:
        lib.om_map_set_obstacle_density(w, c, row, 0, d)


@pytest.mark.parametrize("d,mult", [(0.2, 1.0), (0.3, 1.0 - 0.5 * 0.3), (0.4, 1.0 - 0.5 * 0.4), (0.7, 1.0 - 0.5 * 0.7)],
                         ids=["below_0_3_unchanged", "at_0_3", "at_0_4", "at_0_7_not_blocked"])
def test_R_097_06_terrain_slow_in_density_0_3_to_0_7(lib, tw_open, d, mult):
    """R-097-06 (terrain, ruled in Q-099-01): in [0.3, 0.7] speed is multiplied by (1 - 0.5 d); below 0.3 it is unchanged;
    at 0.7 the cell is still open (blocked only above 0.7, Westley: "The current C engine is fine"). A Raider crossing a band
    of cells of density d (columns 3 to 9, row 4) steps 7.5 x mult per tick. The band is read from the same grid as
    om_map_block_rect, so hand-placed terrain slows units. Green today (regression: the dense grid must keep it)."""
    tw = tw_open
    _density_band(lib, tw, d)
    u = lib.om_unit_spawn(tw, RAIDER, FRIEND, 350.0, 450.0, 0)
    lib.om_command_move(tw, u, 950.0, 450.0)
    for _ in range(4):
        x0 = lib.om_unit_get_pos(tw, u)[0]
        lib.om_tactical_step(tw)
        x1 = lib.om_unit_get_pos(tw, u)[0]
        assert x1 - x0 == pytest.approx(7.5 * mult, abs=0.01)


def test_R_097_01_density_above_0_7_is_blocked_and_routed_around_0_7_is_not(lib, tw):
    """R-097-01: a cell is blocked where obstacle density > 0.7. Column 5, rows 0..7 at density 0.75: the unit routes
    round the wall's open end and never enters it. The same wall at 0.70 is open (slowed to 0.65): the unit walks
    straight across it along y = 400."""
    passable = None
    for r in range(8):
        lib.om_map_set_obstacle_density(tw, 5, r, 0, 0.75)
    u = lib.om_unit_spawn(tw, RAIDER, FRIEND, 300.0, 400.0, 0)
    lib.om_command_move(tw, u, 900.0, 400.0)
    for k in range(400):
        lib.om_tactical_step(tw)
        x, y = lib.om_unit_get_pos(tw, u)
        assert not _in_wall(x, y), f"tick {k + 1}: entered a cell of density 0.75"
        if math.hypot(x - 900.0, y - 400.0) <= 30.0:
            break
    assert math.hypot(x - 900.0, y - 400.0) <= 30.0, "the unit never got round the 0.75 wall"

    try:
        passable = lib.om_world_new(1, 1)
        lib.om_world_set_feature(passable, OMFeature.TACTICAL, 1)
        assert lib.om_map_set_canvas(passable, CANVAS[0], CANVAS[1]) == 0
        for r in range(8):
            lib.om_map_set_obstacle_density(passable, 5, r, 0, 0.70)
        v = lib.om_unit_spawn(passable, RAIDER, FRIEND, 300.0, 400.0, 0)
        lib.om_command_move(passable, v, 900.0, 400.0)
        went_through = False
        for _ in range(400):
            lib.om_tactical_step(passable)
            x, y = lib.om_unit_get_pos(passable, v)
            assert abs(y - 400.0) < POS_TOL, "a density 0.70 wall was routed around"
            went_through = went_through or _in_wall(x, y)
            if math.hypot(x - 900.0, y - 400.0) <= 30.0:
                break
        assert went_through, "the unit never crossed the 0.70 wall"
    finally:
        if passable is not None:
            lib.om_world_free(passable)


# ---------------------------------------------------------------- sight and fire through a blocked cell

def test_R_098_02_blocked_cell_blocks_sight_and_fire_on_its_layers(lib, tw):
    """E-13 R-098-02 / brief G2: a sight line and a line of fire are blocked by a blocked cell on the layers involved.
    Two Raiders either side of the wall (400,400) and (700,400), both on layer 1, wall blocked on layers 1 to 2: neither
    sees nor can shoot the other. Both on layer 4: they can. Moved to face the gap, (400,900) and (700,900), on layer 1:
    they can."""
    _wall(lib, tw, (1, 2))
    a = lib.om_unit_spawn(tw, RAIDER, FRIEND, 400.0, 400.0, 1)
    b = lib.om_unit_spawn(tw, RAIDER, ENEMY, 700.0, 400.0, 1)
    c = lib.om_unit_spawn(tw, RAIDER, FRIEND, 400.0, 400.0, 4)
    d = lib.om_unit_spawn(tw, RAIDER, ENEMY, 700.0, 400.0, 4)
    assert lib.om_unit_can_see(tw, a, b) == 0
    assert lib.om_combat_can_shoot(tw, a, b) == 0
    assert lib.om_unit_can_see(tw, c, d) == 1, "a layer the wall does not block was blocked"
    assert lib.om_combat_can_shoot(tw, c, d) == 1
    lib.om_unit_set_pos(tw, a, 400.0, 900.0)
    lib.om_unit_set_pos(tw, b, 700.0, 900.0)
    assert lib.om_unit_can_see(tw, a, b) == 1
    assert lib.om_combat_can_shoot(tw, a, b) == 1


# ---------------------------------------------------------------- collision pushes slide along blocked cells

def _slide_scene(lib, w, wall):
    """M (195,500) goes +y; idle ENEMY S (a Supply, which never fires) at (180,520). After the step M is 19.5 from S and is pushed along S->M, toward +x
    (203.1, 500.8): into column 2 (x 200..300) when that is blocked.
    Test-defect (engine rules round 4, T10): S was a unit of M's own side; R-097-10 gives the push of an idle own unit to the idle unit, so M would not have been pushed and the slide test proved nothing
    (its control above, the unblocked push, went red). An idle enemy takes none, as the scene needs."""
    if wall:
        assert lib.om_map_block_rect(w, 210.0, 10.0, 290.0, 1990.0, 0, 4) == 0
    m = lib.om_unit_spawn(w, RAIDER, FRIEND, 195.0, 500.0, 0)
    lib.om_unit_spawn(w, 6, ENEMY, 180.0, 520.0, 0)   # 6 = Supply
    lib.om_command_move(w, m, 195.0, 1500.0)
    lib.om_tactical_step(w)
    return lib.om_unit_get_pos(w, m)


def test_R_099_04_collision_push_into_a_blocked_cell_slides_along_it(lib, tw):
    """Collision row of the plan (Python _resolve_collisions, slide along each axis before a full revert): a push that
    would carry a unit into a blocked cell is turned into a slide along it. The unit is not left inside column 2 (x < 200),
    and it did slide (its y has come down from 507.5 under the push)."""
    x, y = _slide_scene(lib, tw, wall=True)
    assert x < 200.0, f"pushed into the blocked column: x = {x:.2f}"
    assert y < 506.5, f"no slide: y = {y:.2f} (a full revert would leave 507.5)"


def test_R_099_04_unblocked_push_goes_where_it_goes_control(lib, tw):
    """Positive control for the slide test: with no wall the same push does carry the unit past x = 200."""
    x, y = _slide_scene(lib, tw, wall=False)
    assert x > 200.0, f"the scene does not push toward the wall: x = {x:.2f}"


# ---------------------------------------------------------------- OM_TP_ROUTE_AROUND_TERRAIN, both ways

def _first_steps(lib, w, ticks=5):
    _wall(lib, w)
    u = lib.om_unit_spawn(w, RAIDER, FRIEND, 300.0, 400.0, 0)
    lib.om_command_move(w, u, 900.0, 400.0)
    out, p0 = [], lib.om_unit_get_pos(w, u)
    for _ in range(ticks):
        lib.om_tactical_step(w)
        p1 = lib.om_unit_get_pos(w, u)
        out.append((math.atan2(p1[1] - p0[1], p1[0] - p0[0]), math.hypot(p1[0] - p0[0], p1[1] - p0[1])))
        p0 = p1
    return out


def test_P3_route_around_terrain_on_heads_for_the_open_end(lib, tw):
    """OM_TP_ROUTE_AROUND_TERRAIN = 1 (the default, the new behaviour): the first steps already bend toward the wall's
    open end (north, +y), at least 0.1 rad off the straight line to (900,400)."""
    lib.om_tactical_get_param.restype = ctypes.c_double
    assert lib.om_tactical_get_param(tw, _tp("OM_TP_ROUTE_AROUND_TERRAIN")) == 1.0
    steps = _first_steps(lib, tw)
    assert all(d > 0.5 for _, d in steps)
    assert all(a > 0.1 for a, _ in steps), "the route does not bend toward the open end"


def test_P3_route_around_terrain_off_is_the_old_straight_line_control(lib, tw):
    """OM_TP_ROUTE_AROUND_TERRAIN = 0 gives the old behaviour (the hash baseline): the unit heads straight for the point
    whatever the wall: every step along +x, no bend. Positive control for the 'on' test: the same scene, the opposite
    verdict."""
    assert lib.om_tactical_set_param(tw, _tp("OM_TP_ROUTE_AROUND_TERRAIN"), 0.0) == 0
    steps = _first_steps(lib, tw)
    assert all(abs(_angle_diff(a, 0.0)) < 0.01 for a, _ in steps), "the old straight line bends"
