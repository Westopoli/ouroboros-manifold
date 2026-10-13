"""E-01 R-005-09 (ground era, terrain stage 2 spec 2026-10-06, lane "fog"): in a ground era (om_era_kind 1) a lower unit
never sees a higher one; a higher unit sees down within its sensor radius unless ground stands in the line; vantage nodes
and the elevation bonus do nothing; a mapgen block rectangle on the same band still blocks; era kind 0 is today's model.

Scenes are picked on terrain seed 11 by test_E01_T2_fog_support.py (a python copy of the spec's sampler picks them; the
assertions go through om_unit_can_see only). Walkers: VANGUARD (sensor 700) and RAIDER (800) are set to movement kind
walking; units are spawned on the layer of the band under them.

Expected today (fog.c is unchanged; om_terrain_sight_blocks is a stub returning 0; cross-layer factor is the space model,
VISION 0.5, and the cell grid blocks on terrain-derived bits):
 red:   test_higher_sees_lower_within_radius[1-3], test_plateau_case_sees, test_lower_never_sees_higher (near distances),
        test_elevation_bonus_does_nothing, test_ridge_inside_the_band_blocks (the sampler stub is the reason).
 green today (guards): test_higher_does_not_see_lower_beyond_radius, test_era_kind_0_keeps_the_space_model,
        test_ridge_between_bands_blocks (the cell grid already blocks it, so it proves nothing about the sampler until it
        is read with the red test beside it), test_same_band_sees_inside_radius (control), test_block_rect_still_blocks.
"""
import math

import pytest

from test_E01_T2_fog_support import (RAIDER, VANGUARD, Scan, clear_pair_same_band, down_pair, make_ground_world,
                                     open_line, ridge_pair_across_bands, ridge_pair_same_band, sees, spawn)

NEAR = (300, 600)       # provisional (2026-10-06): inside the walker radius 700
FAR = (800, 1000)       # provisional (2026-10-06): beyond 700
CLOSE = (100, 200)      # provisional (2026-10-06)
VANGUARD_RADIUS = 700.0


@pytest.fixture
def scene(lib, world_factory):
    w = make_ground_world(lib, world_factory)
    return w, Scan(lib, w)


def _pair(lib, w, a, b, x0, y0, l0, x1, y1, l1, t0=VANGUARD, t1=VANGUARD):
    return spawn(lib, w, t0, 0, x0, y0, l0), spawn(lib, w, t1, 1, x1, y1, l1)


@pytest.mark.parametrize("lower_band", [1, 2, 3])
def test_higher_sees_lower_within_radius(lib, scene, lower_band):
    """R-005-09 positive control for the file: P one band up sees Q inside its radius, where the space model (0.5 x 700)
    says it cannot. Red today: the cross-layer factor is 0.5 and the cell grid blocks on the plateau."""
    w, sc = scene
    px, py, qx, qy, lp, lq = down_pair(sc, *NEAR, lower_band)
    d = math.hypot(qx - px, qy - py)
    assert 0 < d <= VANGUARD_RADIUS
    p, q = _pair(lib, w, 0, 1, px, py, lp, qx, qy, lq)
    assert sees(lib, w, p, q) == 1, f"band {lower_band + 1} unit at {d} wu does not see the band {lower_band} unit below"


def test_plateau_case_sees(lib, scene):
    """R-005-09 / spec "plateau case": the line leaves across the higher unit's own plateau cells (blocked bits on the
    lower layer today over-block it); the higher unit still sees down. Red today."""
    w, sc = scene
    px, py, qx, qy, lp, lq = down_pair(sc, *NEAR, 2, plateau=True)
    p, q = _pair(lib, w, 0, 1, px, py, lp, qx, qy, lq)
    assert sees(lib, w, p, q) == 1


@pytest.mark.parametrize("dist", [CLOSE, NEAR, FAR])
@pytest.mark.parametrize("lower_band", [1, 3])
def test_lower_never_sees_higher(lib, scene, lower_band, dist):
    """R-005-09: whatever VISION_UP says, the lower unit sees nothing higher, at any distance (close, inside radius,
    beyond). The same scene's higher unit is the control in test_higher_sees_lower_within_radius."""
    w, sc = scene
    px, py, qx, qy, lp, lq = down_pair(sc, *dist, lower_band)
    p, q = _pair(lib, w, 0, 1, px, py, lp, qx, qy, lq)
    assert sees(lib, w, q, p) == 0, f"the lower unit sees the higher at {math.hypot(qx - px, qy - py)} wu"


def test_higher_does_not_see_lower_beyond_radius(lib, scene):
    """R-005-09: down is 1.0 of the radius, not more. Guard (green today)."""
    w, sc = scene
    px, py, qx, qy, lp, lq = down_pair(sc, *FAR, 1)
    assert math.hypot(qx - px, qy - py) > VANGUARD_RADIUS
    p, q = _pair(lib, w, 0, 1, px, py, lp, qx, qy, lq)
    assert sees(lib, w, p, q) == 0


def test_same_band_sees_inside_radius(lib, scene):
    """Control: two units on one band, nothing between, see each other (green today)."""
    w, sc = scene
    x0, y0, x1, y1, layer = clear_pair_same_band(sc, *NEAR)
    p, q = _pair(lib, w, 0, 1, x0, y0, layer, x1, y1, layer)
    assert sees(lib, w, p, q) == 1 and sees(lib, w, q, p) == 1


def test_ridge_inside_the_band_blocks(lib, scene):
    """R-005-09 "unless ground stands in the line": two units on one band inside radius, a ridge of that band's own
    cells higher than both eye lines between them (the cell grid does not block it; only the height sampler can). Red
    today for that reason: om_terrain_sight_blocks is a stub returning 0. Control: test_same_band_sees_inside_radius."""
    w, sc = scene
    x0, y0, x1, y1, layer = ridge_pair_same_band(sc, *NEAR)
    assert math.hypot(x1 - x0, y1 - y0) <= VANGUARD_RADIUS
    p, q = _pair(lib, w, 0, 1, x0, y0, layer, x1, y1, layer)
    assert sees(lib, w, p, q) == 0 and sees(lib, w, q, p) == 0


def test_ridge_between_bands_blocks(lib, scene):
    """R-005-09: a higher unit inside radius does not see the lower across a ridge above both eye lines. Likely green
    today because the cell grid blocks the ridge cells on the lower layer; kept because it must stay blocked after the
    grid skips terrain-only cells (the sampler then carries it)."""
    w, sc = scene
    px, py, qx, qy, lp, lq = ridge_pair_across_bands(sc, *NEAR)
    assert math.hypot(qx - px, qy - py) <= VANGUARD_RADIUS
    p, q = _pair(lib, w, 0, 1, px, py, lp, qx, qy, lq)
    assert sees(lib, w, p, q) == 0


def test_block_rect_still_blocks(lib, scene):
    """Spec: a mapgen rectangle on the same band still blocks in a ground era. Control: same pair sees without it."""
    w, sc = scene
    x0, y0, x1, y1, layer = clear_pair_same_band(sc, *NEAR)
    p, q = _pair(lib, w, 0, 1, x0, y0, layer, x1, y1, layer)
    assert sees(lib, w, p, q) == 1, "control: clear before the rectangle"
    mx, my = (x0 + x1) / 2, (y0 + y1) / 2
    assert lib.om_map_block_rect(w, mx - 20.0, my - 20.0, mx + 20.0, my + 20.0, layer, layer) == 0
    assert sees(lib, w, p, q) == 0, "a mapgen rectangle on the same band does not block in a ground era"


def test_elevation_bonus_does_nothing(lib, world_factory):
    """Spec: the elevation bonus is skipped in a ground era. Observer elevation tier 3, target 0: the space model's
    radius is 700 x (1 + 0.15 x 3) = 1,015, so a target at 900 wu on the same band is seen in era 0 (control) and, with
    the bonus skipped, not in era 1. Red today (era 1 still applies the bonus)."""
    seen = {}
    for era in (0, 1):
        w = make_ground_world(lib, world_factory, era_kind=era)
        sc = Scan(lib, w)
        x0, y0, x1, y1, layer = clear_pair_same_band(sc, 900, 900)
        assert math.hypot(x1 - x0, y1 - y0) == 900.0
        p = lib.om_unit_spawn_with_elevation(w, VANGUARD, 0, x0, y0, layer, 3)
        q = spawn(lib, w, VANGUARD, 1, x1, y1, layer)
        assert p != 0
        seen[era] = sees(lib, w, p, q)
    assert seen[0] == 1, "control: the bonus works in the space model"
    assert seen[1] == 0, "the elevation bonus still applies in a ground era"


def test_era_kind_0_keeps_the_space_model(lib, world_factory):
    """Spec: the same world with era kind 0 behaves as today. Guard (green today): P one band up at 400 wu does not see
    Q below (0.5 x 700 = 350), and the lower unit sees nothing it should not; era 1 sees (red test above)."""
    w = make_ground_world(lib, world_factory, era_kind=0)
    sc = Scan(lib, w)
    px, py, qx, qy, lp, lq = down_pair(sc, 400, 400, 1)
    p, q = _pair(lib, w, 0, 1, px, py, lp, qx, qy, lq)
    assert lib.om_era_kind(w) == 0
    assert sees(lib, w, p, q) == 0
