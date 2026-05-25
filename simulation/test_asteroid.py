import math
import pytest
from tactical_map import Asteroid, AsteroidField, TacticalMap


def make_asteroid(aid=1, cid=1, x=0.0, y=0.0, r=5.0, h=50.0, sc="small"):
    return Asteroid(aid, cid, x, y, r, h, sc)


# --- Construction round-trip ---

def test_asteroid_construction_roundtrip():
    a = Asteroid(42, 7, 100.0, 200.0, 15.0, 80.0, "medium")
    assert a.asteroid_id == 42
    assert a.cluster_id == 7
    assert a.x == 100.0
    assert a.y == 200.0
    assert a.radius_xy == 15.0
    assert a.height == 80.0
    assert a.scale_class == "medium"


# --- AsteroidField spatial hash ---

def test_asteroid_field_spatial_hash_query():
    a = Asteroid(1, 1, 50.0, 50.0, 5.0, 40.0, "small")
    field = AsteroidField([a])
    # Asteroid at (50, 50) → cell (0,0) in a 100wu hash. Query bbox covering that cell.
    ids = field.spatial_hash.query_bbox(0.0, 0.0, 99.0, 99.0)
    assert 1 in ids


def test_asteroid_field_empty():
    field = AsteroidField([])
    ids = field.spatial_hash.query_bbox(0.0, 0.0, 200.0, 200.0)
    assert len(ids) == 0


# --- 3D ray-cylinder math ---

def _make_map_with_asteroid(ax, ay, radius, height, scale="small"):
    ast = Asteroid(1, 1, ax, ay, radius, height, scale)
    tmap = TacticalMap(1000, 1000)
    from tactical_map import AsteroidField
    tmap.asteroid_field = AsteroidField([ast])
    return tmap


def test_ray_hit_dead_center():
    # Axis-aligned ray from (0,0,10) to (100,0,10); asteroid at (50,0) r=5, h=50.
    tmap = _make_map_with_asteroid(50.0, 0.0, 5.0, 50.0)
    assert tmap.asteroid_blocks_los(0.0, 0.0, 10.0, 100.0, 0.0, 10.0) is True


def test_ray_miss_by_1wu():
    # Ray from (0, 6, 10) to (100, 6, 10); asteroid at (50, 0) r=5, h=50.
    # Closest approach = 6wu > r=5 → miss.
    tmap = _make_map_with_asteroid(50.0, 0.0, 5.0, 50.0)
    assert tmap.asteroid_blocks_los(0.0, 6.0, 10.0, 100.0, 6.0, 10.0) is False


def test_tall_asteroid_blocks_at_z50():
    # Asteroid height=200; ray at z=50 → blocked.
    tmap = _make_map_with_asteroid(50.0, 0.0, 5.0, 200.0)
    assert tmap.asteroid_blocks_los(0.0, 0.0, 50.0, 100.0, 0.0, 50.0) is True


def test_short_asteroid_does_not_block_at_z65():
    # Asteroid height=20; ray at z=65 → ray always above top of cylinder → NOT blocked.
    tmap = _make_map_with_asteroid(50.0, 0.0, 5.0, 20.0)
    assert tmap.asteroid_blocks_los(0.0, 0.0, 65.0, 100.0, 0.0, 65.0) is False


def test_ray_inside_cylinder_vertical_range():
    # Ray entirely within cylinder z-extent; asteroid at (50,0) r=5, h=100; ray z=50.
    tmap = _make_map_with_asteroid(50.0, 0.0, 5.0, 100.0)
    assert tmap.asteroid_blocks_los(0.0, 0.0, 50.0, 100.0, 0.0, 50.0) is True


# --- TacticalMap.asteroid_field exists on fresh map ---

def test_tactical_map_has_asteroid_field():
    tmap = TacticalMap(500, 500)
    assert hasattr(tmap, "asteroid_field")
    assert isinstance(tmap.asteroid_field, AsteroidField)
    assert len(tmap.asteroid_field.asteroids) == 0
