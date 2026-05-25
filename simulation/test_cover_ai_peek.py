import math

import pytest

import config
from tactical_map import TacticalMap, CoverPolygon
from tactical_engine import TacticalEngine
from unit import FIELD_HP, FIELD_X, FIELD_Y


COVER_CENTER = (500.0, 500.0)
COVER_RADIUS = 80.0
COVER_VERTS = 12
ATTACKER_POS = (200.0, 500.0)


def _circle_polygon(cx, cy, r, n, polygon_id=1):
    verts = []
    for i in range(n):
        theta = 2.0 * math.pi * i / n
        verts.append((cx + r * math.cos(theta), cy + r * math.sin(theta)))
    return CoverPolygon(polygon_id, verts)


def _make_engine():
    poly = _circle_polygon(*COVER_CENTER, COVER_RADIUS, COVER_VERTS)
    tmap = TacticalMap(
        width=2000,
        height=2000,
        gradient_sources=[],
        spine_nodes=[],
        cover_polygons=[poly],
    )
    engine = TacticalEngine(tmap, seed=42)
    # No behavior_runners -> base AI targeting in tactical_engine.py is the system under test.
    return engine, tmap


def _spawn_defender(engine):
    return engine.store.spawn("Warden", faction_id=1, x=COVER_CENTER[0], y=COVER_CENTER[1])


def _spawn_attacker(engine):
    return engine.store.spawn("Raider", faction_id=0, x=ATTACKER_POS[0], y=ATTACKER_POS[1])


def _attacker_hp(store, uid):
    return float(store.data[uid, FIELD_HP])


def _defender_position(store, uid):
    return (float(store.data[uid, FIELD_X]), float(store.data[uid, FIELD_Y]))


def test_defender_in_cover_engages_visible_attacker_within_60_ticks():
    engine, _tmap = _make_engine()
    defender = _spawn_defender(engine)
    attacker = _spawn_attacker(engine)
    attacker_hp_start = _attacker_hp(engine.store, attacker)

    for _ in range(60):
        engine.step()

    attacker_hp_end = _attacker_hp(engine.store, attacker)
    # Defender fired at least once -> attacker HP dropped (L5 visibility gate lets shot through).
    assert attacker_hp_end < attacker_hp_start, (
        "AI defender in cover failed to engage visible attacker in 60 ticks "
        "(clumping pathology — Phase B fix would be required)"
    )


def test_defender_stays_inside_cover_polygon_over_120_ticks():
    engine, tmap = _make_engine()
    defender = _spawn_defender(engine)
    _spawn_attacker(engine)

    for _ in range(120):
        engine.step()

    dx, dy = _defender_position(engine.store, defender)
    assert tmap.is_in_cover(dx, dy), (
        f"Defender drifted out of cover polygon to ({dx:.1f}, {dy:.1f}); "
        "cover-peek behavior must not abandon cover entirely"
    )


def test_defender_eventually_damages_attacker_in_120_ticks():
    engine, _tmap = _make_engine()
    _spawn_defender(engine)
    attacker = _spawn_attacker(engine)
    attacker_hp_start = _attacker_hp(engine.store, attacker)

    for _ in range(120):
        engine.step()

    attacker_hp_end = _attacker_hp(engine.store, attacker)
    assert attacker_hp_end < attacker_hp_start, (
        "Defender fired OR moved to LOS within 120 ticks should yield damage on attacker"
    )


def test_defender_in_cover_with_no_enemies_holds_position():
    engine, _tmap = _make_engine()
    defender = _spawn_defender(engine)
    start_x, start_y = _defender_position(engine.store, defender)

    for _ in range(60):
        engine.step()

    end_x, end_y = _defender_position(engine.store, defender)
    # Regression guard: lone defender in cover with no enemies must idle (pre-Wave-2.5 behavior).
    assert (end_x, end_y) == (start_x, start_y), (
        f"Lone defender in cover moved from ({start_x:.1f}, {start_y:.1f}) "
        f"to ({end_x:.1f}, {end_y:.1f}) with no enemies visible — regression in idle behavior"
    )
    assert engine.store.auto_engage_target[defender] == -1
    assert not engine.store.has_move_target[defender]
