"""E-01 R-005-11 (ground era, terrain stage 2 spec 2026-10-06, lane "fog"): a flyer over land. The flyer rule is evaluated
first: a target whose type is flying and whose layer is above the band under it is visible when within
max(observer radius, target radius) x OM_TP_GROUND_FLYER_SEEN_MULT (1.5) and the sight sampler does not block, so a flyer
is always seen from farther than it sees. A flyer looking down sees a walker within its own radius, from the eye at the
floor of its layer (so it looks over a ridge that blocks a walker's eye).

Types: INTERCEPTOR (sensor 1,000) and BOMBARD (300) stay flyers (movement kind default 0); VANGUARD (700) and RAIDER (800)
are set to walking. A flyer is spawned on engine layer 4 over a band-1 cell (layer above the band under it).

Expected today (cross-layer VISION_UP/DOWN 3 and 4 offsets are 0: nothing is seen across 3 or 4 layers):
 red:   test_flyer_is_seen_beyond_its_own_radius, test_flyer_seen_distance_follows_the_larger_radius,
        test_flyer_sees_a_walker_below_within_its_radius, test_flyer_looks_over_a_ridge, and the control
        test_walker_at_the_ridge_cannot_see_across_it (red because om_terrain_sight_blocks is a stub returning 0: the
        ridge cells are band 1, so the cell grid does not block them).
 green today (guards): the "not seen" legs, test_flyer_does_not_see_beyond_its_own_radius_so_it_is_seen_from_farther
        (the flyer's own sight is 0 across four layers today), test_era_kind_0_flyer_is_not_seen_from_afar.
"""
import math

import pytest

from test_E01_T2_fog_support import (BOMBARD, INTERCEPTOR, RADIUS, RAIDER, VANGUARD, Scan, make_ground_world, open_line,
                                     sees, spawn, valley_ridge_pair, FLYER_SEEN_MULT)

FLYER_LAYER = 4
LINE_CELLS = 17   # a 1,700 wu band-1 line, longest distance used 1,600
SEEN_MARGIN = 100.0   # provisional (2026-10-06): distance steps either side of a limit


def _line(lib, w):
    return open_line(Scan(lib, w), LINE_CELLS)


def _flyer_and_walker(lib, w, flyer_type, walker_type, d):
    x0, y, _, _ = _line(lib, w)
    f = spawn(lib, w, flyer_type, 1, x0, y, FLYER_LAYER)
    k = spawn(lib, w, walker_type, 0, x0 + d, y, 0)
    return k, f


@pytest.mark.parametrize("d", [1200.0, 1400.0])
def test_flyer_is_seen_beyond_its_own_radius(lib, world_factory, d):
    """R-005-11: a walker (700) sees an INTERCEPTOR flyer (1,000) at 1,200 and 1,400, inside max(700, 1000) x 1.5 = 1,500,
    which is past the flyer's own radius. Red today."""
    w = make_ground_world(lib, world_factory)
    walker, flyer = _flyer_and_walker(lib, w, INTERCEPTOR, VANGUARD, d)
    assert d > RADIUS[INTERCEPTOR] and d < max(RADIUS[VANGUARD], RADIUS[INTERCEPTOR]) * FLYER_SEEN_MULT
    assert sees(lib, w, walker, flyer) == 1


def test_flyer_not_seen_beyond_the_seen_from_distance(lib, world_factory):
    """R-005-11: past 1,500 the walker does not see the flyer. Guard (green today)."""
    w = make_ground_world(lib, world_factory)
    walker, flyer = _flyer_and_walker(lib, w, INTERCEPTOR, VANGUARD, 1500.0 + SEEN_MARGIN)
    assert sees(lib, w, walker, flyer) == 0


def test_flyer_does_not_see_beyond_its_own_radius_so_it_is_seen_from_farther(lib, world_factory):
    """R-005-11 "always seen from farther than it sees": at 1,200 the walker sees the flyer (red test above) and the flyer
    does not see the walker (its radius is 1,000). Guard for the second half (green today)."""
    w = make_ground_world(lib, world_factory)
    walker, flyer = _flyer_and_walker(lib, w, INTERCEPTOR, VANGUARD, 1200.0)
    assert sees(lib, w, flyer, walker) == 0


@pytest.mark.parametrize("d,expected", [(1100.0, 1), (1300.0, 0)])
def test_flyer_seen_distance_follows_the_larger_radius(lib, world_factory, d, expected):
    """R-005-11: the observer's radius is the larger (RAIDER walker 800 against a BOMBARD flyer 300): seen out to
    800 x 1.5 = 1,200, not at 1,300. The 1,100 leg is red today, the 1,300 leg a guard."""
    w = make_ground_world(lib, world_factory)
    walker, flyer = _flyer_and_walker(lib, w, BOMBARD, RAIDER, d)
    assert sees(lib, w, walker, flyer) == expected


def test_flyer_sees_a_walker_below_within_its_radius(lib, world_factory):
    """R-005-11: looking down the cross-layer factor is 1.0, so the INTERCEPTOR flyer sees a walker 900 wu away across
    four layers. Red today (offset 4 is 0)."""
    w = make_ground_world(lib, world_factory)
    walker, flyer = _flyer_and_walker(lib, w, INTERCEPTOR, VANGUARD, 900.0)
    assert sees(lib, w, flyer, walker) == 1


def test_walker_at_the_ridge_cannot_see_across_it(lib, world_factory):
    """Control for the next test: the same two cells with a walker at each end are blocked by the ridge."""
    w = make_ground_world(lib, world_factory)
    fx, fy, qx, qy = valley_ridge_pair(Scan(lib, w), 600, 900)
    a = spawn(lib, w, VANGUARD, 1, fx, fy, 0)
    q = spawn(lib, w, VANGUARD, 0, qx, qy, 0)
    assert sees(lib, w, a, q) == 0


def test_flyer_looks_over_a_ridge(lib, world_factory):
    """Spec: a flyer hovering above a valley sees a walker across a ridge lower than the flyer (its eye is at the floor
    of its layer, 2,819 + 50, not the ground's). The same cells blocked a walker's eye (control above). Red today."""
    w = make_ground_world(lib, world_factory)
    fx, fy, qx, qy = valley_ridge_pair(Scan(lib, w), 600, 900)
    assert math.hypot(qx - fx, qy - fy) <= RADIUS[INTERCEPTOR]
    flyer = spawn(lib, w, INTERCEPTOR, 1, fx, fy, 3)
    walker = spawn(lib, w, VANGUARD, 0, qx, qy, 0)
    assert sees(lib, w, flyer, walker) == 1


def test_era_kind_0_flyer_is_not_seen_from_afar(lib, world_factory):
    """Space model unchanged: with era kind 0 the same flyer at 1,200 is not seen by the walker. Guard (green today)."""
    w = make_ground_world(lib, world_factory, era_kind=0)
    walker, flyer = _flyer_and_walker(lib, w, INTERCEPTOR, VANGUARD, 1200.0)
    assert sees(lib, w, walker, flyer) == 0
