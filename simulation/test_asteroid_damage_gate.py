"""
Regression: damage visibility gate + asteroid LOS block (Wave 2.5R leaf-05).

Spec lines 162-166 (cover_asteroid_los_spec.md):
  damage.py gates on compute_visibility(); zero damage when target hidden.

Four assertions:
  1. Tall asteroid between attacker and target → 0 damage applied (HP unchanged).
  2. No asteroid → damage applied (HP reduced).
  3. Regex: no (1.0 - cover) term in damage.py source.
  4. resolve_damage callable with (store, tactical_map, dt) signature.
"""

import re
import damage
from unit import (
    UnitStore,
    FIELD_X, FIELD_Y, FIELD_HP, FIELD_BASE_DAMAGE,
    FIELD_ATTACK_INTERVAL, FIELD_ATTACK_RANGE, FIELD_SENSOR_RADIUS,
    FIELD_ATTACK_TIMER, FIELD_LAYER, FIELD_AOE_RADIUS,
)
from tactical_map import TacticalMap, Asteroid, AsteroidField
from fog_of_war import compute_visibility


# ── layer-z constants matching fog_of_war.py fallback ──────────────────────
_LAYER_Z_FLOORS = [0.0, 30.0, 100.0]
_LAYER_Z_CEILINGS = [30.0, 100.0, 300.0]
_LAYER_0_Z_MID = (_LAYER_Z_FLOORS[0] + _LAYER_Z_CEILINGS[0]) / 2.0  # 15.0


def _make_store_pair(ax, ay, tx, ty, sensor_radius=500.0, attack_range=300.0):
    """Two-unit store: uid=0 (faction 0) vs uid=1 (faction 1), same layer 0."""
    store = UnitStore()
    stats_a = {
        "hp": 100.0, "base_damage": 20.0, "attack_interval": 1.0,
        "attack_range": attack_range, "sensor_radius": sensor_radius,
        "speed": 0.0, "layer_transition_time": 0.0, "category": "Strike",
    }
    stats_b = dict(stats_a)

    attacker = store.spawn("Strike", 0, ax, ay, layer=0, stats=stats_a)
    target   = store.spawn("Strike", 1, tx, ty, layer=0, stats=stats_b)

    store.data[attacker, FIELD_AOE_RADIUS] = 0.0
    store.data[attacker, FIELD_ATTACK_TIMER] = 0.0
    store.auto_engage_target[attacker] = target
    return store, attacker, target


def _make_blocking_tmap(asteroid_x, asteroid_y, radius_xy=40.0, height=500.0):
    """TacticalMap with one huge asteroid on the ray from (0,0) to (200,0)."""
    tmap = TacticalMap(1000, 1000)
    ast = Asteroid(
        asteroid_id=0,
        cluster_id=0,
        x=asteroid_x,
        y=asteroid_y,
        radius_xy=radius_xy,
        height=height,
        scale_class="huge",
    )
    tmap.asteroid_field = AsteroidField([ast])
    return tmap


def _make_clear_tmap():
    tmap = TacticalMap(1000, 1000)
    tmap.asteroid_field = AsteroidField([])
    return tmap


# ── tests ────────────────────────────────────────────────────────────────────

def test_blocked_asteroid_zero_damage():
    """Tall asteroid on the ray → target HP unchanged after resolve_damage."""
    store, attacker, target = _make_store_pair(ax=0.0, ay=0.0, tx=200.0, ty=0.0)
    hp_before = store.data[target, FIELD_HP]

    # Asteroid sits at midpoint of the ray, large enough to block.
    tmap = _make_blocking_tmap(asteroid_x=100.0, asteroid_y=0.0, radius_xy=40.0, height=500.0)

    damage.resolve_damage(store, tmap, dt=2.0)

    assert store.data[target, FIELD_HP] == hp_before, (
        f"Expected HP {hp_before}, got {store.data[target, FIELD_HP]}: "
        "asteroid should block LOS and suppress damage"
    )


def test_no_asteroid_damage_applied():
    """Clear map → damage applied and target HP reduced."""
    store, attacker, target = _make_store_pair(ax=0.0, ay=0.0, tx=200.0, ty=0.0)
    hp_before = store.data[target, FIELD_HP]

    tmap = _make_clear_tmap()

    damage.resolve_damage(store, tmap, dt=2.0)

    assert store.data[target, FIELD_HP] < hp_before, (
        f"Expected HP < {hp_before}, got {store.data[target, FIELD_HP]}: "
        "no asteroid, damage should land"
    )


def test_no_cover_factor_in_damage_source():
    """Regex: (1.0 - cover) term must not appear in damage.py."""
    src = open(damage.__file__).read()
    match = re.search(r"\(1\.0?\s*[-\u2212]\s*cover", src)
    assert match is None, f"Legacy cover factor found at: {match}"


def test_resolve_damage_signature():
    """resolve_damage must accept (store, tactical_map, dt) without TypeError."""
    store, _a, _t = _make_store_pair(ax=0.0, ay=0.0, tx=600.0, ty=0.0,
                                     attack_range=50.0)  # out of range → no-op
    tmap = _make_clear_tmap()
    result = damage.resolve_damage(store, tmap, dt=1.0)
    assert isinstance(result, tuple) and len(result) == 2
