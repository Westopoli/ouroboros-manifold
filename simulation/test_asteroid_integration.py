"""
Apex integration tests — Wave 2.5R leaf-07.

Spec lines 249-251 (cover_asteroid_los_spec.md §L7):
  2 Raider attackers + 1 Warden defender behind dense asteroid cluster.
  Cluster center (500,500), radius 80, ~25 asteroids skewed huge.

Four assertions:
  1. Defender NOT in attacker visibility set (cluster blocks LOS).
  2. Attackers fire at defender → 0 damage (resolve_damage gate intact).
  3. Defender moves to (900,500) open ground → visible to ≥1 attacker;
     subsequent resolve_damage tick reduces defender HP.
  4. Defender fires from cover at one attacker (auto_engage_target set) →
     attacker NOT in defender's own visibility set (defender hidden from
     attacker; asymmetric one-sided engagement per spec line 49).
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "simulation"))

import pytest
from asteroid_integration_fixture import build_cover_asteroid_apex_scenario
from fog_of_war import compute_visibility
from damage import resolve_damage
from unit import FIELD_X, FIELD_Y, FIELD_HP


def test_defender_hidden_behind_cluster():
    """Defender behind dense cluster: not in any attacker's visibility set."""
    tm, store, attackers, defenders = build_cover_asteroid_apex_scenario()
    defender = defenders[0]
    vis = compute_visibility(store, tm)
    for atk in attackers:
        assert defender not in vis.get(atk, set()), (
            f"Attacker {atk} should NOT see defender behind asteroid cluster"
        )


def test_blocked_attacker_deals_zero_damage():
    """Attackers targeting hidden defender → 0 damage applied."""
    tm, store, attackers, defenders = build_cover_asteroid_apex_scenario()
    defender = defenders[0]
    for atk in attackers:
        store.auto_engage_target[atk] = defender
    hp_before = store.data[defender, FIELD_HP]

    resolve_damage(store, tm, dt=2.0)

    assert store.data[defender, FIELD_HP] == hp_before, (
        f"Defender HP must not change: was {hp_before}, "
        f"got {store.data[defender, FIELD_HP]}; asteroid cluster must gate damage"
    )


def test_open_ground_defender_takes_damage():
    """Defender moves to (900,500) clear ground → visible + takes damage."""
    tm, store, attackers, defenders = build_cover_asteroid_apex_scenario()
    defender = defenders[0]
    for atk in attackers:
        store.auto_engage_target[atk] = defender

    store.data[defender, FIELD_X] = 900.0
    store.data[defender, FIELD_Y] = 500.0

    vis2 = compute_visibility(store, tm)
    assert any(defender in vis2.get(atk, set()) for atk in attackers), (
        "Defender at (900,500) should be visible to at least one attacker"
    )

    hp_mid = store.data[defender, FIELD_HP]
    resolve_damage(store, tm, dt=2.0)
    assert store.data[defender, FIELD_HP] < hp_mid, (
        f"Visible defender must take damage: HP was {hp_mid}, "
        f"got {store.data[defender, FIELD_HP]}"
    )


def test_defender_fires_from_cover_asymmetric():
    """Defender fires from cover: attackers do NOT appear in defender's visibility set.

    Spec line 49: no fire-reveal. Defender's own compute_visibility call returns
    attackers as NOT visible (cluster blocks outgoing LOS too at layer 0).
    Asymmetry: defender can fire at attacker (auto_engage_target set manually)
    but attacker cannot see defender.
    """
    tm, store, attackers, defenders = build_cover_asteroid_apex_scenario()
    defender = defenders[0]
    # Arm defender to fire at first attacker (manual target assignment).
    store.auto_engage_target[defender] = attackers[0]

    vis = compute_visibility(store, tm)
    for atk in attackers:
        assert atk not in vis.get(defender, set()), (
            f"Defender at cluster center must NOT see attacker {atk} "
            "through its own cluster (no fire-reveal per spec line 49)"
        )
