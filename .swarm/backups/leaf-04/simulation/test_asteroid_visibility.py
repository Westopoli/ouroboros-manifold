"""
fog_of_war per-asteroid LOS tests (L4 spec lines 228-233).
Minimal fixtures — no L7 scene import.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

# LAYER_Z fallback if config lacks constants (leaf-04 assumption: config lacks them until leaf-03 lands)
try:
    from config import LAYER_Z_FLOORS, LAYER_Z_CEILINGS
except ImportError:
    LAYER_Z_FLOORS = [0.0, 30.0, 100.0]
    LAYER_Z_CEILINGS = [30.0, 100.0, 300.0]
    print("[leaf-04 assumption] LAYER_Z_FLOORS/CEILINGS not in config — using inline literals")

import pytest
from unit import UnitStore
from tactical_map import Asteroid, AsteroidField, TacticalMap
from fog_of_war import compute_visibility


# --- Minimal stats dict for spawning units without touching config.UNIT_STATS ---
_STATS = {
    "hp": 100,
    "base_damage": 10,
    "attack_interval": 1.0,
    "attack_range": 800,
    "speed": 100,
    "sensor_radius": 99999,  # huge so distance never gates visibility
    "layer_transition_time": 1.0,
    "category": "Strike",
    "aoe_radius": 0,
}


def _make_map(asteroids=None):
    """Minimal TacticalMap with an AsteroidField and no spine nodes."""
    tm = TacticalMap.__new__(TacticalMap)
    tm.spine_nodes = []
    field = AsteroidField(asteroids or [])
    tm.asteroid_field = field
    # Stub out methods fog_of_war calls
    tm.sensor_interference = lambda x, y: 0.0
    tm.get_spine_nodes_by_type = lambda t: []
    return tm


def _layer_z_mid(layer):
    return (LAYER_Z_FLOORS[layer] + LAYER_Z_CEILINGS[layer]) / 2.0


def _midpoint(x1, y1, x2, y2):
    return (x1 + x2) / 2.0, (y1 + y2) / 2.0


# Observer at (500,500) — target at (50,50). Two different factions.
OBS_X, OBS_Y = 500.0, 500.0
TGT_X, TGT_Y = 50.0, 50.0
MID_X, MID_Y = _midpoint(OBS_X, OBS_Y, TGT_X, TGT_Y)  # (275, 275)


def _spawn_pair(layer_obs=0, layer_tgt=0):
    store = UnitStore()
    obs_uid = store.spawn("Raider", 0, OBS_X, OBS_Y, layer=layer_obs, stats=_STATS)
    tgt_uid = store.spawn("Raider", 1, TGT_X, TGT_Y, layer=layer_tgt, stats=_STATS)
    return store, obs_uid, tgt_uid


# Test 1: no asteroids → target visible
def test_no_asteroids_target_visible():
    store, obs, tgt = _spawn_pair(layer_obs=0, layer_tgt=0)
    tm = _make_map(asteroids=[])
    vis = compute_visibility(store, tm)
    assert tgt in vis[obs], "target must be visible with no asteroids"


# Test 2: huge asteroid (height 200) at midpoint, layer 0 → target blocked
def test_huge_asteroid_blocks_layer0():
    store, obs, tgt = _spawn_pair(layer_obs=0, layer_tgt=0)
    ast = Asteroid(
        asteroid_id=0, cluster_id=0,
        x=MID_X, y=MID_Y,
        radius_xy=20.0, height=200.0,
        scale_class="huge",
    )
    tm = _make_map(asteroids=[ast])
    vis = compute_visibility(store, tm)
    assert tgt not in vis[obs], "huge asteroid must block layer-0 LOS"


# Test 3: tiny asteroid (height 20) at midpoint, observer+target layer 1 (z ~65) → ray passes over → visible
def test_tiny_asteroid_does_not_block_layer1():
    store, obs, tgt = _spawn_pair(layer_obs=1, layer_tgt=1)
    ast = Asteroid(
        asteroid_id=0, cluster_id=0,
        x=MID_X, y=MID_Y,
        radius_xy=20.0, height=20.0,
        scale_class="tiny",
    )
    tm = _make_map(asteroids=[ast])
    vis = compute_visibility(store, tm)
    assert tgt in vis[obs], "tiny asteroid must NOT block layer-1 ray (ray z ~65 > height 20)"


# Test 4: tall asteroid (height 200) at midpoint, layer 2 (z ~200) → height >= LAYER_Z_FLOORS[2]=100 → blocked
def test_tall_asteroid_blocks_layer2():
    store, obs, tgt = _spawn_pair(layer_obs=2, layer_tgt=2)
    ast = Asteroid(
        asteroid_id=0, cluster_id=0,
        x=MID_X, y=MID_Y,
        radius_xy=20.0, height=200.0,
        scale_class="huge",
    )
    tm = _make_map(asteroids=[ast])
    vis = compute_visibility(store, tm)
    assert tgt not in vis[obs], "tall asteroid (h=200 >= LAYER_Z_FLOORS[2]=100) must block layer-2 LOS"


# Test 5: ray skirting just outside asteroid radius_xy → target visible
def test_ray_skirting_asteroid_edge_visible():
    store, obs, tgt = _spawn_pair(layer_obs=0, layer_tgt=0)
    # Place asteroid offset from the ray line by slightly more than radius_xy
    # Ray goes (500,500)→(50,50), direction ~(-1,-1). A point perpendicular to that
    # at midpoint (275,275) offset by radius_xy + 1wu → asteroid misses ray.
    r = 20.0
    offset = r + 1.0  # just outside
    ast = Asteroid(
        asteroid_id=0, cluster_id=0,
        x=MID_X + offset,  # displaced perpendicular to the ray (enough to skirt)
        y=MID_Y - offset,
        radius_xy=r, height=200.0,
        scale_class="huge",
    )
    tm = _make_map(asteroids=[ast])
    vis = compute_visibility(store, tm)
    assert tgt in vis[obs], "asteroid just outside ray radius must NOT block LOS"
