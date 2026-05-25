"""
Apex integration fixture — Wave 2.5R leaf-07.

Exports build_cover_asteroid_apex_scenario() for test_asteroid_integration.py.

Scenario geometry:
  TacticalMap 1000x1000. Dense asteroid cluster centered at (500, 500) radius 80.
  ~25 huge asteroids packed to guarantee opaque blocking on attacker→defender lines.
  Attackers: 2 Raiders (faction 0) at (50, 100) and (50, 900).
  Defender:  1 Warden  (faction 1) at (500, 500) — inside cluster.

Attacker y-positions are (50,100) and (50,900) — NOT (50,500)/(50,600) as in the brief.
Brief positions are geometrically impossible: rays from (50,500) and (50,600) to (900,500)
both pass through the cluster at (500,500) (closest approach ~47wu < cluster radius 80),
so assertion 3 (defender visible at (900,500)) can never pass. Symmetric positions
(50,100)/(50,900) give rays that clear the cluster (closest approach ~188wu > 80) for
open-ground check while both still intercept the cluster on the (500,500) line.
See leaf-07.ASSUMPTIONS.md §A3 for geometry derivation.

Cluster hand-built (not via gradient_placer.place_asteroid_fields) because:
  - place_asteroid_fields requires InstantiatedLayout + config density constants;
    no guarantee random placement covers attacker→defender line in every run.
  - Hand-built grid of huge asteroids gives deterministic, provably opaque blocking.
  - Spec allows either approach (see leaf-07.md task description).

See leaf-07.ASSUMPTIONS.md for full inference log.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "simulation"))

import math

from tactical_map import TacticalMap, Asteroid, AsteroidField
from unit import UnitStore, FIELD_X, FIELD_Y, FIELD_HP, FIELD_LAYER, FIELD_SENSOR_RADIUS


_CLUSTER_CX = 500.0
_CLUSTER_CY = 500.0
_CLUSTER_RADIUS = 80.0

# Huge asteroid dimensions: radius_xy=15 (gives ~25 asteroids in cluster), height=300 (blocks all layers).
# step_factor=1.8 × radius_xy = 27wu step → slight overlap → no ray gaps through cluster interior.
_AST_RADIUS_XY = 15.0
_AST_HEIGHT = 300.0
_AST_SCALE = "huge"
_STEP_FACTOR = 1.8


def _build_cluster() -> AsteroidField:
    """Pack ~25 huge asteroids in a grid inside the cluster disk. Guarantees opacity.

    Grid step = 1.8 × radius_xy (27wu) so adjacent asteroids slightly overlap → no gaps
    on any ray through cluster interior (defender's hide position).

    Geometry verification (see leaf-07.ASSUMPTIONS.md §A1):
      - Ray from (50,100)→(500,500): hits cluster center → BLOCKED.
      - Ray from (50,900)→(500,500): hits cluster center → BLOCKED.
      - Ray from (50,100)→(900,500): closest approach to (500,500) ≈ 188wu > 80 → CLEAR.
      - Ray from (50,900)→(900,500): closest approach to (500,500) ≈ 188wu > 80 → CLEAR.
    Produces exactly 25 asteroids per cluster_radius=80, radius_xy=15, step_factor=1.8.
    """
    asteroids = []
    asteroid_id = 0
    # Grid step: overlap factor so asteroids pack without gaps.
    step = _AST_RADIUS_XY * _STEP_FACTOR
    # Sample grid centered on cluster center.
    x0 = _CLUSTER_CX - _CLUSTER_RADIUS
    y0 = _CLUSTER_CY - _CLUSTER_RADIUS
    x_steps = int(math.ceil(2 * _CLUSTER_RADIUS / step)) + 1
    y_steps = int(math.ceil(2 * _CLUSTER_RADIUS / step)) + 1

    for i in range(x_steps):
        for j in range(y_steps):
            ax = x0 + i * step
            ay = y0 + j * step
            dx = ax - _CLUSTER_CX
            dy = ay - _CLUSTER_CY
            if dx * dx + dy * dy > _CLUSTER_RADIUS * _CLUSTER_RADIUS:
                continue
            asteroids.append(Asteroid(
                asteroid_id=asteroid_id,
                cluster_id=0,
                x=ax,
                y=ay,
                radius_xy=_AST_RADIUS_XY,
                height=_AST_HEIGHT,
                scale_class=_AST_SCALE,
            ))
            asteroid_id += 1

    return AsteroidField(asteroids)


# Sensor radius large enough to see across the full map; attack range reaches defender.
_SENSOR_RADIUS = 2000.0
_ATTACK_RANGE = 2000.0

_RAIDER_STATS = {
    "category": "Strike",
    "hp": 250.0,
    "base_damage": 9.0,
    "attack_interval": 0.8,
    "attack_range": _ATTACK_RANGE,
    "sensor_radius": _SENSOR_RADIUS,
    "speed": 150.0,
    "layer_transition_time": 1.0,
    "aoe_radius": 0,
}

_WARDEN_STATS = {
    "category": "Line",
    "hp": 375.0,
    "base_damage": 4.0,
    "attack_interval": 1.5,
    "attack_range": _ATTACK_RANGE,
    "sensor_radius": _SENSOR_RADIUS,
    "speed": 70.0,
    "layer_transition_time": 2.0,
    "aoe_radius": 0,
}


def build_cover_asteroid_apex_scenario():
    """Return (TacticalMap, UnitStore, attackers_list, defenders_list).

    attackers_list: [raider1_uid, raider2_uid]  — faction 0
    defenders_list: [warden_uid]               — faction 1
    """
    tm = TacticalMap(width=1000, height=1000, gradient_sources=[], spine_nodes=[])
    tm.asteroid_field = _build_cluster()

    store = UnitStore()
    # y-positions chosen so rays to (900,500) clear the cluster; see module docstring.
    raider1 = store.spawn("Raider", 0, 50.0, 100.0, layer=0, stats=_RAIDER_STATS)
    raider2 = store.spawn("Raider", 0, 50.0, 900.0, layer=0, stats=_RAIDER_STATS)
    warden  = store.spawn("Warden", 1, _CLUSTER_CX, _CLUSTER_CY, layer=0, stats=_WARDEN_STATS)

    return tm, store, [raider1, raider2], [warden]
