"""PP fog wave A5 (Addendum 59, A159): sight through a blocked cell is decided by exact grid traversal.

Proves E-12 R-098-02 (sight line through blocked route-grid cells; see the epic's R-098-02 wording): a straight
line from observer to target that passes through the OPEN INTERIOR of a blocked 100 wu cell, by any amount, is
blocked. `om_fog_grid_blocks` (csrc/fog.c) samples the line every half cell (50 wu), so a segment that only
clips a corner of the blocked cell, a chord of a few wu, falls between two samples and is missed.

Pinning "interior" exactly: the blocked cell is [500,600) x [500,600) (hand-placed with om_map_block_rect).
A segment that meets the cell only at its corner POINT (here (500,600) or (600,500)) has no interior in
common with it and is NOT blocked; a segment entering by 2 wu (a 2.83 wu chord) is blocked. Both lines are
built from exactly representable doubles (multiples of 1 or 2), so the touch is exact, not a rounding result.
Whether the exact corner point blocks is a choice made here (open-interior reading of "touching a cell's
interior counts"); flagged in the wave report.

Scene: both units on layer 0, both outside the blocked cell, 141 wu apart (inside any sensor radius used),
no cover. The first 45-degree line y - x = 98 clips corner (500,600); its samples at 1/3 and 2/3 of the way,
(483,581) and (517,615), are both outside the cell, so the old code sees the line as clear.
"""
import pytest

from conftest import OMFeature

RAIDER = 0
FRIEND, ENEMY = 0, 1


@pytest.fixture
def fw(lib, world_factory):
    """A tactical world with terrain routing on (the fog check only runs with ROUTE_AROUND_TERRAIN) and the
    cell (5,5) = [500,600) x [500,600) blocked on layer 0."""
    w = world_factory(n_regions=1)
    lib.om_world_set_feature(w, OMFeature.TACTICAL, 1)
    lib.om_tactical_set_param(w, 1, 1.0)  # ROUTE_AROUND_TERRAIN
    assert lib.om_map_set_canvas(w, 2000.0, 2000.0) == 0
    assert lib.om_map_block_rect(w, 500.0, 500.0, 600.0, 600.0, 0, 0) == 0
    return w


def _sees(lib, w, a, b):
    ua = lib.om_unit_spawn(w, RAIDER, FRIEND, a[0], a[1], 0)
    ub = lib.om_unit_spawn(w, RAIDER, ENEMY, b[0], b[1], 0)
    return bool(lib.om_unit_can_see(w, ua, ub)), bool(lib.om_unit_can_see(w, ub, ua))


def test_R_098_02_line_through_the_cell_centre_is_blocked_control(lib, fw):
    """Positive control, green today: the line from (450,550) to (650,550) crosses the whole blocked cell
    and is blocked both ways. Proves the cell is blocked and the units are in sight range."""
    assert _sees(lib, fw, (450.0, 550.0), (650.0, 550.0)) == (False, False)


def test_R_098_02_line_clear_of_the_cell_is_not_blocked_control(lib, fw):
    """Positive control, green today and after: the line (450,552) to (550,652), y - x = 102, passes beside
    corner (500,600) without touching the cell. Not blocked."""
    assert _sees(lib, fw, (450.0, 552.0), (550.0, 652.0)) == (True, True)


def test_R_098_02_line_touching_only_the_corner_point_is_not_blocked(lib, fw):
    """R-098-02, exact touch: y - x = 100 passes through the corner point (500,600) and nowhere else meets
    the cell, so it is not blocked (no interior contact). Green today (the sampler sees nothing) and must
    stay green with exact traversal."""
    assert _sees(lib, fw, (450.0, 550.0), (550.0, 650.0)) == (True, True)


def test_R_098_02_line_clipping_the_top_left_corner_is_blocked(lib, fw):
    """R-098-02: y - x = 98 enters the cell's interior at (500,598) and leaves at (502,600), a 2.83 wu chord,
    and must be blocked both ways. Red today: samples fall at (483,581) and (517,615), both outside."""
    assert _sees(lib, fw, (450.0, 548.0), (550.0, 648.0)) == (False, False)


def test_R_098_02_line_clipping_the_bottom_right_corner_is_blocked(lib, fw):
    """R-098-02, the opposite corner: y - x = -98 clips corner (600,500), entering at (598,500) and leaving
    at (600,502). Must be blocked both ways. Red today for the same sampling reason."""
    assert _sees(lib, fw, (550.0, 452.0), (650.0, 552.0)) == (False, False)
