"""E-01 R-004-06: a walker on a slope is on the lower band below the midline and the upper band at or above it,
going up or down; it changes layer only on a slope, at the midline within one cell. Terrain stage 2 spec
2026-10-06, "move" lane.

Scene: seed 11 slope 0 (bottom edge (11950, 50) band 3, top edge (11950, 550) band 4, length 500, one cell wide;
read from om_terrain_slope_get, not hard-coded). Walking Raider at one edge ordered to the other; the unit's layer
(engine layer = band - 1) is read every tick. Red today because om_walk_route is a contract stub (-1) and
om_terrain_slope_at returns -1: the walker neither steers nor changes layer.
"""
import ctypes

from conftest import OMFeature, OMSlope

RAIDER = 0
FRIEND = 0
CANVAS = 16000.0
SEED = 11
SLOPE = 0
CELL_WU = 100.0              # "within one cell"
RUN = 400                    # ticks: far above the 500 wu crossing at 136 wu/s (about 74 ticks), a run limit


def _scene(lib, world_factory, from_top):
    w = world_factory(n_regions=1)
    lib.om_world_set_feature(w, OMFeature.TACTICAL, 1)
    assert lib.om_map_set_canvas(w, CANVAS, CANVAS) == 0
    assert lib.om_terrain_generate(w, SEED, CANVAS, CANVAS) == 0
    assert lib.om_roster_set_movement_kind(w, RAIDER, 1) == 0
    s = OMSlope()
    assert lib.om_terrain_slope_get(w, SLOPE, ctypes.byref(s)) == 0
    a, b = ((s.x1, s.y1), (s.x0, s.y0)) if from_top else ((s.x0, s.y0), (s.x1, s.y1))
    layer = (s.upper_band if from_top else s.lower_band) - 1
    u = lib.om_unit_spawn(w, RAIDER, FRIEND, a[0], a[1], layer)
    assert u != 0
    lib.om_command_move(w, u, b[0], b[1])
    return w, u, s, layer


def _walk(lib, w, u, s):
    trace = []
    for _ in range(RUN):
        lib.om_tactical_step(w)
        x, y = lib.om_unit_get_pos(w, u)
        trace.append((lib.om_unit_get_layer(w, u), x, y))
    return trace


def _check(lib, w, s, trace, first_layer, last_layer):
    moved = (trace[0][1], trace[0][2]) != (trace[-1][1], trace[-1][2])
    assert moved, "walker never moved (om_walk_route is a contract stub)"
    changes = [i for i in range(1, len(trace)) if trace[i][0] != trace[i - 1][0]]
    assert len(changes) == 1, f"expected exactly one layer change on the slope, got {len(changes)}"
    i = changes[0]
    lo, hi = s.lower_band - 1, s.upper_band - 1
    assert {trace[i - 1][0], trace[i][0]} == {lo, hi}
    assert trace[0][0] == first_layer and trace[-1][0] == last_layer
    cx, cy = trace[i][1], trace[i][2]
    out = OMSlope()
    assert lib.om_terrain_slope_at(w, cx, cy, ctypes.byref(out)) >= 0, \
        f"layer changed at ({cx:.1f}, {cy:.1f}), which is not on a slope"
    assert abs(cx - s.mx) <= CELL_WU and abs(cy - s.my) <= CELL_WU, \
        f"layer changed at ({cx:.1f}, {cy:.1f}), more than one cell from the midline ({s.mx:.1f}, {s.my:.1f})"


def test_R_004_06_a_walker_going_up_changes_layer_at_the_midline(lib, world_factory):
    w, u, s, layer = _scene(lib, world_factory, from_top=False)
    trace = _walk(lib, w, u, s)
    _check(lib, w, s, trace, s.lower_band - 1, s.upper_band - 1)


def test_R_004_06_a_walker_going_down_changes_layer_at_the_midline(lib, world_factory):
    w, u, s, layer = _scene(lib, world_factory, from_top=True)
    trace = _walk(lib, w, u, s)
    _check(lib, w, s, trace, s.upper_band - 1, s.lower_band - 1)
