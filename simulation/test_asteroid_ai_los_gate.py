"""
Tests for L11: AI targeting LOS gate via asteroid visibility filter.
Spec: docs/legacy/test_specs/cover_asteroid_movement_spec.md lines 46-52.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import damage
from tactical_map import TacticalMap, Asteroid, AsteroidField
from unit import (
    UnitStore, FIELD_X, FIELD_Y, FIELD_HP, FIELD_BASE_DAMAGE,
    FIELD_ATTACK_INTERVAL, FIELD_ATTACK_RANGE, FIELD_SENSOR_RADIUS,
    FIELD_ATTACK_TIMER, FIELD_LAYER, FIELD_AOE_RADIUS,
)


_COHORT_COUNT = 4  # mirrors config.TARGETING_COHORT_COUNT — used to flush all cohorts per tick


def _make_store_and_stats():
    store = UnitStore()
    stats = {
        "hp": 100.0,
        "base_damage": 20.0,
        "attack_interval": 1.0,
        "attack_range": 50.0,       # short — target at 200 is outside, forces sensor-pursuit
        "sensor_radius": 500.0,     # long — would normally detect target
        "speed": 50.0,
        "layer_transition_time": 0.0,
        "category": "Strike",
    }
    return store, stats


def _tick(store, tm):
    """Run update_targeting COHORT_COUNT times to guarantee every cohort fires."""
    for _ in range(_COHORT_COUNT):
        damage.update_targeting(store, tm, dt=0.1)


def _spawn_pair(store, stats):
    attacker = store.spawn("Strike", 0, 0.0, 0.0, layer=0, stats=dict(stats))
    target = store.spawn("Strike", 1, 200.0, 0.0, layer=0, stats=dict(stats))
    store.data[attacker, FIELD_AOE_RADIUS] = 0.0
    store.data[target, FIELD_AOE_RADIUS] = 0.0
    store.data[attacker, FIELD_ATTACK_TIMER] = 0.0
    store.attack_moving[attacker] = True
    return attacker, target


def _tm_with_asteroid():
    tm = TacticalMap(width=1000, height=1000, gradient_sources=[], spine_nodes=[])
    tm.asteroid_field = AsteroidField([
        Asteroid(
            asteroid_id=0, cluster_id=0,
            x=100.0, y=0.0,
            radius_xy=40.0, height=500.0, scale_class="huge",
        ),
    ])
    return tm


def _tm_empty():
    return TacticalMap(width=1000, height=1000, gradient_sources=[], spine_nodes=[])


# ---------------------------------------------------------------------------
# Test 1: Asteroid blocks LOS — sensor-pursuit must NOT acquire target.
# ---------------------------------------------------------------------------
def test_asteroid_blocks_acquisition():
    store, stats = _make_store_and_stats()
    tm = _tm_with_asteroid()
    attacker, target = _spawn_pair(store, stats)

    _tick(store, tm)  # flush all cohorts — attacker must not acquire

    assert store.auto_engage_target[attacker] == -1, (
        f"Gate failed: attacker acquired hidden target (uid={target})"
    )


# ---------------------------------------------------------------------------
# Test 2: No asteroid — sensor-pursuit acquires normally.
# ---------------------------------------------------------------------------
def test_no_asteroid_acquires_normally():
    store, stats = _make_store_and_stats()
    tm = _tm_empty()
    attacker, target = _spawn_pair(store, stats)

    _tick(store, tm)  # flush all cohorts — attacker's cohort fires, acquires visible target

    assert store.auto_engage_target[attacker] == target, (
        f"Expected acquisition of target uid={target}, got {store.auto_engage_target[attacker]}"
    )


# ---------------------------------------------------------------------------
# Test 3: Target moves into open between two ticks — second tick acquires.
# ---------------------------------------------------------------------------
def test_target_steps_into_open_second_tick_acquires():
    store, stats = _make_store_and_stats()
    tm = _tm_with_asteroid()
    attacker, target = _spawn_pair(store, stats)

    # Tick 1: target behind asteroid — no acquisition.
    _tick(store, tm)
    assert store.auto_engage_target[attacker] == -1, "Tick 1 should not acquire (asteroid blocks)"

    # Move target clear of asteroid (perpendicular — no asteroid between (0,0) and (0,200)).
    store.data[target, FIELD_X] = 0.0
    store.data[target, FIELD_Y] = 200.0

    # Tick 2: target now visible — acquisition expected.
    _tick(store, tm)
    assert store.auto_engage_target[attacker] == target, (
        f"Tick 2 should acquire now-visible target, got {store.auto_engage_target[attacker]}"
    )


# ---------------------------------------------------------------------------
# Test 4: Player-issued target on hidden unit — gate must NOT clear it.
# ---------------------------------------------------------------------------
def test_player_issued_target_preserved_when_hidden():
    store, stats = _make_store_and_stats()
    tm = _tm_with_asteroid()
    attacker, target = _spawn_pair(store, stats)

    # Simulate player command: pre-set target before update_targeting.
    store.auto_engage_target[attacker] = target

    _tick(store, tm)  # flush all cohorts

    assert store.auto_engage_target[attacker] == target, (
        f"Gate cleared player-issued target {target}; got {store.auto_engage_target[attacker]}"
    )


# ---------------------------------------------------------------------------
# Test 5: Signature check — callable as update_targeting(store, tmap, dt=0.1).
# ---------------------------------------------------------------------------
def test_update_targeting_signature_accepts_dt():
    store, stats = _make_store_and_stats()
    tm = _tm_empty()
    attacker, target = _spawn_pair(store, stats)

    # Must not raise TypeError.
    damage.update_targeting(store, tm, dt=0.1)
