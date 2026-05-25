import sys
import os
import math

sys.path.insert(0, os.path.dirname(__file__))

import config
from tactical_map import TacticalMap, Asteroid, AsteroidField
from movement import Navmesh


def _make_tmap(asteroids=None):
    tmap = TacticalMap(width=1000, height=1000, gradient_sources=[], spine_nodes=[])
    if asteroids is not None:
        tmap.asteroid_field = AsteroidField(asteroids)
    return tmap


def _asteroid(aid, x, y, radius_xy, scale_class):
    return Asteroid(
        asteroid_id=aid,
        cluster_id=0,
        x=x,
        y=y,
        radius_xy=radius_xy,
        height=radius_xy,
        scale_class=scale_class,
    )


# ── Tests ─────────────────────────────────────────────────────────────────────

def test_huge_asteroid_center_unwalkable():
    ast = _asteroid(1, 500.0, 500.0, 50.0, "huge")
    tmap = _make_tmap([ast])
    nm = Navmesh.from_tactical_map(tmap)
    r, c = nm.cell(500.0, 500.0)
    assert not nm.is_walkable(r, c), "huge asteroid center must be unwalkable"


def test_medium_asteroid_center_unwalkable():
    # Place asteroid at a cell center so the center cell is within block_dist.
    # With cell_size=100, cell (5,5) center = (550, 550).
    ast = _asteroid(2, 550.0, 550.0, 10.0, "medium")
    tmap = _make_tmap([ast])
    nm = Navmesh.from_tactical_map(tmap)
    r, c = nm.cell(550.0, 550.0)
    assert not nm.is_walkable(r, c), "medium asteroid (radius>=8) center must be unwalkable"


def test_small_asteroid_center_walkable():
    ast = _asteroid(3, 500.0, 500.0, 5.0, "small")
    tmap = _make_tmap([ast])
    nm = Navmesh.from_tactical_map(tmap)
    r, c = nm.cell(500.0, 500.0)
    assert nm.is_walkable(r, c), "small asteroid (radius<8) must not block navmesh"


def test_tiny_asteroid_center_walkable():
    ast = _asteroid(4, 500.0, 500.0, 2.0, "tiny")
    tmap = _make_tmap([ast])
    nm = Navmesh.from_tactical_map(tmap)
    r, c = nm.cell(500.0, 500.0)
    assert nm.is_walkable(r, c), "tiny asteroid (radius<8) must not block navmesh"


def test_none_asteroid_field_no_error():
    tmap = TacticalMap(width=1000, height=1000, gradient_sources=[], spine_nodes=[])
    tmap.asteroid_field = None
    nm = Navmesh.from_tactical_map(tmap)
    assert nm is not None
    r, c = nm.cell(500.0, 500.0)
    assert nm.is_walkable(r, c), "no asteroid field — map should be fully walkable"


def test_determinism():
    ast = _asteroid(5, 300.0, 300.0, 20.0, "huge")
    tmap1 = _make_tmap([ast])
    tmap2 = _make_tmap([ast])
    nm1 = Navmesh.from_tactical_map(tmap1)
    nm2 = Navmesh.from_tactical_map(tmap2)
    assert nm1.grid == nm2.grid, "identical tmaps must produce identical navmesh grids"


def test_conservative_ring_outside_stays_walkable():
    # Cell whose center is just outside (radius_xy + cell_size/2) must remain walkable.
    ast_x, ast_y = 500.0, 500.0
    radius = 50.0  # huge
    ast = _asteroid(6, ast_x, ast_y, radius, "huge")
    tmap = _make_tmap([ast])
    nm = Navmesh.from_tactical_map(tmap)
    cell_size = nm.cell_size
    block_dist = radius + cell_size / 2.0
    epsilon = cell_size * 1.5  # well outside the conservative ring
    probe_x = ast_x + block_dist + epsilon
    probe_y = ast_y
    r, c = nm.cell(probe_x, probe_y)
    cx, cy = nm.cell_center(r, c)
    dist = math.sqrt((cx - ast_x) ** 2 + (cy - ast_y) ** 2)
    assert dist > block_dist, "test fixture: cell center must be outside block threshold"
    assert nm.is_walkable(r, c), "cell outside conservative ring must stay walkable"
