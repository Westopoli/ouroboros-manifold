"""E-01 R-004-07: on a slope a walker's speed is divided by 1.1 going up and multiplied by 1.1 going down; the
unit's transition time plays no part. Terrain stage 2 spec 2026-10-06, "move" lane.

Scene: seed 11 slope 0 (500 wu, vertical, bottom (11950, 50), top (11950, 550)). The spec's 600 wu example is the
same arithmetic on a different length: seconds = length / (speed / 1.1) up, length / (speed * 1.1) down. Expected
ticks are computed from the slope read out of the world. Raider (150) and Bastion (40) walk the whole slope from
one edge centre to the other; arrival is within ARRIVE_WU of the goal; the answer is within 2 ticks (spec).
Red today because om_walk_route is a contract stub: the walker does not move.
"""
import ctypes

from conftest import OMFeature, OMSlope

RAIDER, BASTION = 0, 5
SPEED = {RAIDER: 150.0, BASTION: 40.0}
FRIEND = 0
CANVAS = 16000.0
SEED = 11
SLOPE = 0
FACTOR = 1.1                 # R-004-07, provisional setting (Westley 2026-10-06)
TICK_RATE = 20
TOLERANCE_TICKS = 2          # spec
ARRIVE_WU = 1.0              # provisional (2026-10-06): arrival radius at the goal cell centre
RUN = 600                    # ticks: Bastion up takes 275, a run limit


def _time_ticks(lib, world_factory, utype, up):
    w = world_factory(n_regions=1)
    lib.om_world_set_feature(w, OMFeature.TACTICAL, 1)
    assert lib.om_map_set_canvas(w, CANVAS, CANVAS) == 0
    assert lib.om_terrain_generate(w, SEED, CANVAS, CANVAS) == 0
    assert lib.om_roster_set_movement_kind(w, utype, 1) == 0
    s = OMSlope()
    assert lib.om_terrain_slope_get(w, SLOPE, ctypes.byref(s)) == 0
    a, b = ((s.x0, s.y0), (s.x1, s.y1)) if up else ((s.x1, s.y1), (s.x0, s.y0))
    layer = (s.lower_band if up else s.upper_band) - 1
    u = lib.om_unit_spawn(w, utype, FRIEND, a[0], a[1], layer)
    assert u != 0
    lib.om_command_move(w, u, b[0], b[1])
    for k in range(1, RUN + 1):
        lib.om_tactical_step(w)
        x, y = lib.om_unit_get_pos(w, u)
        if abs(x - b[0]) <= ARRIVE_WU and abs(y - b[1]) <= ARRIVE_WU:
            return k, s.length
    return None, s.length


def _expect(length, speed, up):
    v = speed / FACTOR if up else speed * FACTOR
    return length / v * TICK_RATE


def _case(lib, world_factory, utype, up):
    got, length = _time_ticks(lib, world_factory, utype, up)
    want = _expect(length, SPEED[utype], up)
    assert got is not None, f"walker never reached the goal cell (no walking route or slope speed yet: om_walk_route is a stub); wanted about {want:.1f} ticks"
    assert abs(got - want) <= TOLERANCE_TICKS, f"{got} ticks, wanted {want:.1f} +- {TOLERANCE_TICKS}"


def test_R_004_07_raider_up_the_slope(lib, world_factory):
    _case(lib, world_factory, RAIDER, True)


def test_R_004_07_raider_down_the_slope(lib, world_factory):
    _case(lib, world_factory, RAIDER, False)


def test_R_004_07_bastion_up_the_slope(lib, world_factory):
    _case(lib, world_factory, BASTION, True)


def test_R_004_07_bastion_down_the_slope(lib, world_factory):
    _case(lib, world_factory, BASTION, False)
