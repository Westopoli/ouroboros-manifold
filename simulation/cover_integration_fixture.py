import math

from tactical_map import TacticalMap, CoverPolygon
from unit import (
    UnitStore,
    FIELD_X, FIELD_Y, FIELD_LAYER, FIELD_HP, FIELD_MAX_HP,
    FIELD_BASE_DAMAGE, FIELD_ATTACK_INTERVAL, FIELD_ATTACK_RANGE,
    FIELD_SENSOR_RADIUS, FIELD_AOE_RADIUS, FIELD_ATTACK_TIMER,
    CATEGORY_STRIKE,
)


def _circle_vertices(cx, cy, radius, n_verts):
    verts = []
    for i in range(n_verts):
        theta = 2.0 * math.pi * i / n_verts
        verts.append((cx + radius * math.cos(theta), cy + radius * math.sin(theta)))
    return verts


def _spawn(store, faction_id, x, y):
    uid = store.count
    store.count += 1
    store.data[uid, FIELD_X] = x
    store.data[uid, FIELD_Y] = y
    store.data[uid, FIELD_LAYER] = 0
    store.data[uid, FIELD_HP] = 1000.0
    store.data[uid, FIELD_MAX_HP] = 1000.0
    store.data[uid, FIELD_BASE_DAMAGE] = 50.0
    store.data[uid, FIELD_ATTACK_INTERVAL] = 1.0
    store.data[uid, FIELD_ATTACK_RANGE] = 2000.0
    store.data[uid, FIELD_SENSOR_RADIUS] = 2000.0
    store.data[uid, FIELD_AOE_RADIUS] = 0.0
    store.data[uid, FIELD_ATTACK_TIMER] = 0.0
    store.faction[uid] = faction_id
    store.category[uid] = CATEGORY_STRIKE
    store.alive[uid] = True
    return uid


def build_cover_apex_scenario():
    poly = CoverPolygon(1, _circle_vertices(500.0, 500.0, 80.0, 12))
    tm = TacticalMap(
        width=1000,
        height=1000,
        gradient_sources=[],
        spine_nodes=[],
        cover_polygons=[poly],
    )
    store = UnitStore()
    atk1 = _spawn(store, faction_id=0, x=200.0, y=500.0)
    atk2 = _spawn(store, faction_id=0, x=800.0, y=500.0)
    defender = _spawn(store, faction_id=1, x=500.0, y=500.0)
    return tm, store, [atk1, atk2], [defender]
