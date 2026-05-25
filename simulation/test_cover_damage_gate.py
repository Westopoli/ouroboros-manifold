import os
import re

from tactical_map import TacticalMap, CoverPolygon
from unit import (
    UnitStore,
    FIELD_X, FIELD_Y, FIELD_LAYER, FIELD_HP, FIELD_MAX_HP,
    FIELD_BASE_DAMAGE, FIELD_ATTACK_INTERVAL, FIELD_ATTACK_RANGE,
    FIELD_SENSOR_RADIUS, FIELD_AOE_RADIUS, FIELD_ATTACK_TIMER,
    CATEGORY_STRIKE,
)
from damage import resolve_damage
import config


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


def _spawn(store, faction_id, x, y, hp=1000.0, base_damage=50.0, attack_range=2000.0, sensor_radius=2000.0):
    uid = store.count
    store.count += 1
    store.data[uid, FIELD_X] = x
    store.data[uid, FIELD_Y] = y
    store.data[uid, FIELD_LAYER] = 0
    store.data[uid, FIELD_HP] = hp
    store.data[uid, FIELD_MAX_HP] = hp
    store.data[uid, FIELD_BASE_DAMAGE] = base_damage
    store.data[uid, FIELD_ATTACK_INTERVAL] = 1.0
    store.data[uid, FIELD_ATTACK_RANGE] = attack_range
    store.data[uid, FIELD_SENSOR_RADIUS] = sensor_radius
    store.data[uid, FIELD_AOE_RADIUS] = 0.0
    store.data[uid, FIELD_ATTACK_TIMER] = 0.0
    store.faction[uid] = faction_id
    store.category[uid] = CATEGORY_STRIKE
    store.alive[uid] = True
    return uid


def _expected_dmg(store, attacker_uid, target_uid):
    from unit import CATEGORY_NAMES
    attacker_cat = CATEGORY_NAMES[store.category[attacker_uid]]
    target_cat = CATEGORY_NAMES[store.category[target_uid]]
    base_dmg = store.data[attacker_uid, FIELD_BASE_DAMAGE]
    mult = config.CATEGORY_MULTIPLIER[attacker_cat][target_cat]
    return base_dmg * mult


def test_attacker_outside_cover_target_inside_blind_zero_damage():
    tm = _make_map()
    store = UnitStore()
    attacker = _spawn(store, faction_id=0, x=500.0, y=500.0)
    target = _spawn(store, faction_id=1, x=50.0, y=50.0)
    store.auto_engage_target[attacker] = target

    hp_before = store.data[target, FIELD_HP]
    resolve_damage(store, tm, dt=1.0)
    hp_after = store.data[target, FIELD_HP]

    assert hp_after == hp_before, (
        f"Hidden target took damage: before={hp_before} after={hp_after}"
    )


def test_attacker_and_target_same_polygon_full_damage_no_cover_mult():
    tm = _make_map()
    store = UnitStore()
    attacker = _spawn(store, faction_id=0, x=10.0, y=10.0)
    target = _spawn(store, faction_id=1, x=50.0, y=50.0)
    store.auto_engage_target[attacker] = target

    expected = _expected_dmg(store, attacker, target)
    hp_before = store.data[target, FIELD_HP]
    resolve_damage(store, tm, dt=1.0)
    hp_after = store.data[target, FIELD_HP]
    actual = hp_before - hp_after

    assert abs(actual - expected) < 1e-6, (
        f"Same-polygon damage mismatch: expected {expected}, got {actual}"
    )


def test_both_outside_cover_full_damage_no_cover_mult():
    tm = _make_map()
    store = UnitStore()
    attacker = _spawn(store, faction_id=0, x=500.0, y=500.0)
    target = _spawn(store, faction_id=1, x=510.0, y=510.0)
    store.auto_engage_target[attacker] = target

    expected = _expected_dmg(store, attacker, target)
    hp_before = store.data[target, FIELD_HP]
    resolve_damage(store, tm, dt=1.0)
    hp_after = store.data[target, FIELD_HP]
    actual = hp_before - hp_after

    assert abs(actual - expected) < 1e-6, (
        f"Open-field damage mismatch: expected {expected}, got {actual}"
    )


def test_damage_source_has_no_cover_multiplier_expression():
    here = os.path.dirname(__file__)
    damage_path = os.path.join(here, "damage.py")
    with open(damage_path, "r", encoding="utf-8") as f:
        src = f.read()
    pattern = re.compile(r"\(\s*1\.0\s*-\s*cover[^)]*\)")
    real_matches = []
    for line in src.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            continue
        if pattern.search(line):
            real_matches.append(line)
    assert not real_matches, (
        "damage.py still contains (1.0 - cover) expression:\n" + "\n".join(real_matches)
    )


def test_cover_density_method_still_callable():
    tm = TacticalMap(width=1000, height=1000, gradient_sources=[], spine_nodes=[])
    assert hasattr(tm, "cover_density"), "tactical_map.cover_density method removed"
    val = tm.cover_density(500.0, 500.0)
    assert isinstance(val, (int, float))
