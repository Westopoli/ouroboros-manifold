"""
Tests for Wave 2.5R damage gate + Wave 2.6M AI targeting LOS gate.

All fixtures minimal: TacticalMap(1000, 1000) + UnitStore() + hand-built AsteroidField.
Loads staged damage.py explicitly via importlib to bypass pytest sys.path ordering.
"""

import sys
import os
import re
import importlib
import importlib.util
import math
import pytest

_STAGED_DIR = os.path.dirname(os.path.abspath(__file__))
_REAL_SIM = os.path.abspath(os.path.join(_STAGED_DIR, "../../../..", "simulation"))

# Ensure real simulation modules (unit, config, etc.) are importable.
if _REAL_SIM not in sys.path:
    sys.path.insert(0, _REAL_SIM)

# Explicitly load staged damage.py from its on-disk path, bypassing sys.path priority.
_STAGED_DAMAGE_PATH = os.path.join(_STAGED_DIR, "damage.py")
_spec = importlib.util.spec_from_file_location("damage", _STAGED_DAMAGE_PATH)
damage = importlib.util.module_from_spec(_spec)
sys.modules["damage"] = damage
_spec.loader.exec_module(damage)
from unit import (
    UnitStore,
    FIELD_X, FIELD_Y, FIELD_HP, FIELD_BASE_DAMAGE, FIELD_ATTACK_INTERVAL,
    FIELD_ATTACK_RANGE, FIELD_SENSOR_RADIUS, FIELD_LAYER, FIELD_AOE_RADIUS,
    FIELD_ATTACK_TIMER,
)
from tactical_map import TacticalMap, Asteroid, AsteroidField
import config


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_UNIT_STATS = {
    "hp": 100.0,
    "base_damage": 10.0,
    "attack_interval": 1.0,
    "attack_range": 100.0,
    "sensor_radius": 500.0,
    "speed": 50.0,
    "layer_transition_time": 0.0,
    "aoe_radius": 0.0,
    "category": "Strike",
}

_AOE_STATS = {**_UNIT_STATS, "aoe_radius": 60.0}

_SENSOR_STATS = {
    **_UNIT_STATS,
    "attack_range": 50.0,
    "sensor_radius": 500.0,
}


def _spawn(store, faction, x, y, stats=None):
    stats = stats or _UNIT_STATS
    uid = store.spawn("Strike", faction, x, y, stats=stats)
    # Ensure attack timer is 0 so damage fires immediately.
    store.data[uid, FIELD_ATTACK_TIMER] = 0.0
    return uid


def _make_map_with_huge_asteroid(ax=500.0, ay=500.0):
    """Return TacticalMap with one huge asteroid (radius 80) at (ax, ay)."""
    tm = TacticalMap(width=1000, height=1000, gradient_sources=[], spine_nodes=[])
    ast = Asteroid(
        asteroid_id=0,
        cluster_id=0,
        x=ax,
        y=ay,
        radius_xy=80.0,
        height=300.0,   # tall enough to block all layers
        scale_class="huge",
    )
    tm.asteroid_field = AsteroidField([ast])
    return tm


def _run_targeting_full_cohort(store, tm, n=1):
    """Drive update_targeting TARGETING_COHORT_COUNT * n times to advance all cohorts."""
    for _ in range(config.TARGETING_COHORT_COUNT * n):
        damage.update_targeting(store, tm)


# ---------------------------------------------------------------------------
# resolve_damage: visibility gate
# ---------------------------------------------------------------------------

class TestResolveDamageAsteroidGate:
    def test_huge_asteroid_blocks_damage(self):
        """Attacker→target blocked by asteroid: HP unchanged after resolve_damage."""
        store = UnitStore()
        # Attacker at x=200, target at x=800; asteroid at x=500 in between.
        attacker = _spawn(store, 0, 200.0, 500.0)
        target = _spawn(store, 1, 800.0, 500.0)
        store.auto_engage_target[attacker] = target
        # Put attacker close enough to attack range (use huge range for simplicity).
        store.data[attacker, FIELD_ATTACK_RANGE] = 700.0

        tm = _make_map_with_huge_asteroid(ax=500.0, ay=500.0)
        hp_before = store.data[target, FIELD_HP]

        damage.resolve_damage(store, tm, dt=1.0)

        assert store.data[target, FIELD_HP] == hp_before, (
            "HP should be unchanged; asteroid should block damage"
        )

    def test_no_asteroid_damage_applies(self):
        """No asteroid: attacker in range → target HP decreases."""
        store = UnitStore()
        attacker = _spawn(store, 0, 100.0, 500.0)
        target = _spawn(store, 1, 150.0, 500.0)
        store.auto_engage_target[attacker] = target
        store.data[attacker, FIELD_ATTACK_RANGE] = 200.0

        tm = TacticalMap(width=1000, height=1000, gradient_sources=[], spine_nodes=[])
        hp_before = store.data[target, FIELD_HP]

        damage.resolve_damage(store, tm, dt=1.0)

        assert store.data[target, FIELD_HP] < hp_before, "HP should decrease with no blocking asteroid"


# ---------------------------------------------------------------------------
# _accumulate_single: cover mult retired
# ---------------------------------------------------------------------------

class TestAccumulateSingleCoverRetired:
    def test_no_cover_formula_in_source(self):
        """Regex confirms (1.0 - cover) pattern absent from damage source."""
        src = open(damage.__file__).read()
        match = re.search(r"\(1\.0?\s*[-\u2212]\s*cover", src)
        assert match is None, f"Found retired cover formula at position {match.start() if match else '?'}"

    def test_cover_density_no_effect_single(self):
        """High cover_density map vs no-cover map: same damage applied to target."""
        # Map with high cover density gradient source.
        from tactical_map import GradientSource
        cover_src = GradientSource(
            position=(500.0, 500.0),
            property_type="cover_density",
            radius=1000.0,
            intensity=1.0,
            falloff="constant",
        )
        tm_with_cover = TacticalMap(1000, 1000, gradient_sources=[cover_src], spine_nodes=[])
        tm_no_cover = TacticalMap(1000, 1000, gradient_sources=[], spine_nodes=[])

        def _run(tm):
            store = UnitStore()
            attacker = _spawn(store, 0, 100.0, 100.0)
            target = _spawn(store, 1, 150.0, 100.0)
            pending = {}
            damage._accumulate_single(
                store, attacker, target,
                store.data[attacker, FIELD_BASE_DAMAGE],
                "Strike", tm, pending,
            )
            return pending[target][0][1]  # dmg value

        dmg_with = _run(tm_with_cover)
        dmg_without = _run(tm_no_cover)
        assert dmg_with == dmg_without, (
            f"cover_density should not affect damage; got {dmg_with} vs {dmg_without}"
        )


# ---------------------------------------------------------------------------
# _accumulate_aoe: cover mult retired
# ---------------------------------------------------------------------------

class TestAccumulateAoeCoverRetired:
    def test_no_cover_formula_in_source_aoe(self):
        """Same regex check — no (1.0 - cover) pattern anywhere in source (shared)."""
        src = open(damage.__file__).read()
        count = len(re.findall(r"\(1\.0?\s*[-\u2212]\s*cover", src))
        assert count == 0, f"Found {count} retired cover formula occurrence(s)"

    def test_cover_density_no_effect_aoe(self):
        """High cover_density map vs no-cover map: same AOE damage applied."""
        from tactical_map import GradientSource
        cover_src = GradientSource(
            position=(500.0, 500.0),
            property_type="cover_density",
            radius=1000.0,
            intensity=1.0,
            falloff="constant",
        )
        tm_with = TacticalMap(1000, 1000, gradient_sources=[cover_src], spine_nodes=[])
        tm_no = TacticalMap(1000, 1000, gradient_sources=[], spine_nodes=[])

        def _run(tm):
            store = UnitStore()
            attacker = _spawn(store, 0, 100.0, 100.0, stats=_AOE_STATS)
            target = _spawn(store, 1, 110.0, 100.0)
            pending = {}
            damage._accumulate_aoe(
                store, attacker, target,
                store.data[attacker, FIELD_BASE_DAMAGE],
                "Strike", store.data[attacker, FIELD_AOE_RADIUS],
                tm, pending,
            )
            return pending[target][0][1]

        dmg_with = _run(tm_with)
        dmg_no = _run(tm_no)
        assert dmg_with == dmg_no, (
            f"cover_density should not affect AOE damage; got {dmg_with} vs {dmg_no}"
        )


# ---------------------------------------------------------------------------
# update_targeting: LOS gate
# ---------------------------------------------------------------------------

class TestUpdateTargetingLosGate:
    def test_asteroid_hidden_target_not_acquired(self):
        """Huge asteroid between attacker and target: auto_engage_target stays -1."""
        store = UnitStore()
        # Attacker at x=200, target at x=800; asteroid at x=500 blocks LOS.
        # attack_range=50 (so target not in attack range), sensor_radius=500 (sees far).
        attacker = _spawn(store, 0, 200.0, 500.0, stats=_SENSOR_STATS)
        store.attack_moving[attacker] = True

        target = _spawn(store, 1, 800.0, 500.0, stats=_SENSOR_STATS)

        tm = _make_map_with_huge_asteroid(ax=500.0, ay=500.0)

        _run_targeting_full_cohort(store, tm, n=2)

        assert store.auto_engage_target[attacker] == -1, (
            f"Target hidden behind asteroid; expected no acquisition, got {store.auto_engage_target[attacker]}"
        )

    def test_no_asteroid_target_acquired(self):
        """No asteroid: an enemy seen but outside attack range is not acquired (A199, R-087-04: no pursuit on
        sight); the same enemy inside attack range 50 is → auto_engage_target == target uid.
        TD-PP-A199-repin: the old expectation was acquisition on first sight at 200 wu."""
        store = UnitStore()
        attacker = _spawn(store, 0, 200.0, 500.0, stats=_SENSOR_STATS)
        store.attack_moving[attacker] = True

        target = _spawn(store, 1, 400.0, 500.0, stats=_SENSOR_STATS)

        tm = TacticalMap(width=1000, height=1000, gradient_sources=[], spine_nodes=[])

        _run_targeting_full_cohort(store, tm, n=2)

        assert store.auto_engage_target[attacker] == -1, (
            f"Enemy 200 wu away is outside attack range 50; expected no acquisition, got {store.auto_engage_target[attacker]}"
        )

        store.data[target, FIELD_X] = 240.0     # 40 wu from the attacker: inside attack range 50
        _run_targeting_full_cohort(store, tm, n=2)

        assert store.auto_engage_target[attacker] == target, (
            f"Expected target {target} acquired; got {store.auto_engage_target[attacker]}"
        )

    def test_target_steps_into_open_acquired_on_second_call(self):
        """Target starts hidden (behind asteroid), moves to open; second cohort cycle acquires."""
        store = UnitStore()
        # Attacker at 200,500; asteroid at 500,500 blocks to 800,500
        attacker = _spawn(store, 0, 200.0, 500.0, stats=_SENSOR_STATS)
        store.attack_moving[attacker] = True

        target = _spawn(store, 1, 800.0, 500.0, stats=_SENSOR_STATS)

        tm = _make_map_with_huge_asteroid(ax=500.0, ay=500.0)

        # First pass: blocked.
        _run_targeting_full_cohort(store, tm, n=2)
        assert store.auto_engage_target[attacker] == -1

        # Move target to open, inside attack range 50 (A199: acquisition needs range, not sight; TD-PP-A199-repin).
        store.data[target, FIELD_X] = 240.0
        store.data[target, FIELD_Y] = 500.0
        # Remove asteroid (empty field).
        tm.asteroid_field = AsteroidField([])

        # Second pass: now visible.
        _run_targeting_full_cohort(store, tm, n=2)
        assert store.auto_engage_target[attacker] == target, (
            f"Expected acquisition after target steps into open; got {store.auto_engage_target[attacker]}"
        )

    def test_player_issued_target_preserved_when_hidden(self):
        """auto_engage_target set manually (player command) persists even when target is hidden."""
        store = UnitStore()
        attacker = _spawn(store, 0, 200.0, 500.0, stats=_SENSOR_STATS)
        # Not attack_moving: player issued a direct target.
        store.attack_moving[attacker] = False

        target = _spawn(store, 1, 800.0, 500.0, stats=_SENSOR_STATS)
        # Simulate player-issued target lock.
        store.auto_engage_target[attacker] = target

        tm = _make_map_with_huge_asteroid(ax=500.0, ay=500.0)

        _run_targeting_full_cohort(store, tm, n=2)

        # Target is out of attack_range=50; cohort would normally clear.
        # Brief Edit 5(c): pre_acquisition >= 0 → preserve rather than clear.
        assert store.auto_engage_target[attacker] == target, (
            f"Player-issued target should be preserved; got {store.auto_engage_target[attacker]}"
        )

    def test_signature_no_dt(self):
        """update_targeting callable without dt param (backwards compat)."""
        store = UnitStore()
        tm = TacticalMap(width=1000, height=1000, gradient_sources=[], spine_nodes=[])
        # Must not raise.
        damage.update_targeting(store, tm)

    def test_signature_with_dt(self):
        """update_targeting callable with dt=0.1 kwarg."""
        store = UnitStore()
        tm = TacticalMap(width=1000, height=1000, gradient_sources=[], spine_nodes=[])
        damage.update_targeting(store, tm, dt=0.1)
