import pytest

from tactical_map import TacticalMap, CoverPolygon
from unit import UnitStore, FIELD_X, FIELD_Y, FIELD_LAYER, FIELD_SENSOR_RADIUS
from fog_of_war import compute_visibility


def _make_map():
    poly1 = CoverPolygon(1, [(0.0, 0.0), (100.0, 0.0), (100.0, 100.0), (0.0, 100.0)])
    poly2 = CoverPolygon(2, [(200.0, 200.0), (300.0, 200.0), (300.0, 300.0), (200.0, 300.0)])
    return TacticalMap(
        width=1000,
        height=1000,
        gradient_sources=[],
        spine_nodes=[],
        cover_polygons=[poly1, poly2],
    )


def _spawn(store, faction_id, x, y, sensor_radius=2000.0):
    uid = store.count
    store.count += 1
    store.data[uid, FIELD_X] = x
    store.data[uid, FIELD_Y] = y
    store.data[uid, FIELD_LAYER] = 0
    store.data[uid, FIELD_SENSOR_RADIUS] = sensor_radius
    store.faction[uid] = faction_id
    store.alive[uid] = True
    return uid


def test_target_in_cover_observer_outside_blind():
    tm = _make_map()
    store = UnitStore()
    a = _spawn(store, faction_id=0, x=500.0, y=500.0)
    b = _spawn(store, faction_id=1, x=50.0, y=50.0)
    vis = compute_visibility(store, tm)
    assert b not in vis[a]


def test_target_and_observer_same_polygon_visible():
    tm = _make_map()
    store = UnitStore()
    a = _spawn(store, faction_id=0, x=10.0, y=10.0)
    b = _spawn(store, faction_id=1, x=50.0, y=50.0)
    vis = compute_visibility(store, tm)
    assert b in vis[a]
    assert a in vis[b]


def test_target_and_observer_different_polygons_blind():
    tm = _make_map()
    store = UnitStore()
    a = _spawn(store, faction_id=0, x=10.0, y=10.0)
    b = _spawn(store, faction_id=1, x=250.0, y=250.0)
    vis = compute_visibility(store, tm)
    assert b not in vis[a]
    assert a not in vis[b]


def test_both_outside_cover_visible():
    tm = _make_map()
    store = UnitStore()
    a = _spawn(store, faction_id=0, x=500.0, y=500.0)
    b = _spawn(store, faction_id=1, x=510.0, y=510.0)
    vis = compute_visibility(store, tm)
    assert b in vis[a]
    assert a in vis[b]


def test_same_faction_both_outside_not_in_visible():
    # Same-faction units are skipped in visibility (existing behavior — they
    # never appear in each other's visible set; engine treats own side as
    # always known by other code paths).
    tm = _make_map()
    store = UnitStore()
    a = _spawn(store, faction_id=0, x=500.0, y=500.0)
    b = _spawn(store, faction_id=0, x=510.0, y=510.0)
    vis = compute_visibility(store, tm)
    assert b not in vis[a]
    assert a not in vis[b]


def test_same_faction_one_in_cover_one_outside_not_in_visible():
    tm = _make_map()
    store = UnitStore()
    a = _spawn(store, faction_id=0, x=50.0, y=50.0)
    b = _spawn(store, faction_id=0, x=500.0, y=500.0)
    vis = compute_visibility(store, tm)
    assert b not in vis[a]
    assert a not in vis[b]


def test_same_faction_different_polygons_not_in_visible():
    tm = _make_map()
    store = UnitStore()
    a = _spawn(store, faction_id=0, x=50.0, y=50.0)
    b = _spawn(store, faction_id=0, x=250.0, y=250.0)
    vis = compute_visibility(store, tm)
    assert b not in vis[a]
    assert a not in vis[b]
