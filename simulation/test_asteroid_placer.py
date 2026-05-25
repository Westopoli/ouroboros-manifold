import math
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pytest
from tactical_map import SpineNode, AsteroidField
import config
from gradient_placer import place_asteroid_fields


def _make_inst(node_defs, seed=42):
    class _FakeInst:
        def __init__(self, nodes, s):
            self.spine_nodes = nodes
            self.map_seed = s
    nodes = [SpineNode(position=pos, node_type=nt) for pos, nt in node_defs]
    return _FakeInst(nodes, seed)


def _expected_count(radius):
    return math.pi * radius ** 2 * config.ASTEROID_BASE_DENSITY


# ── Single chokepoint cluster ─────────────────────────────────────────────────

def test_chokepoint_count_within_tolerance():
    inst = _make_inst([((500.0, 500.0), "chokepoint")])
    field = place_asteroid_fields(inst)
    assert isinstance(field, AsteroidField)
    radius = config.GRADIENT_CHOKEPOINT_COVER_RADIUS
    expected = _expected_count(radius)
    n = len(field.asteroids)
    assert abs(n - expected) / expected < 0.10, f"count {n} not within 10% of {expected:.1f}"


def test_chokepoint_scale_distribution():
    inst = _make_inst([((500.0, 500.0), "chokepoint")])
    field = place_asteroid_fields(inst)
    n = len(field.asteroids)
    counts = {k: 0 for k in config.ASTEROID_SCALE_DISTRIBUTION}
    for a in field.asteroids:
        counts[a.scale_class] += 1
    for cls, target_frac in config.ASTEROID_SCALE_DISTRIBUTION.items():
        actual_frac = counts[cls] / n
        assert abs(actual_frac - target_frac) < 0.10, (
            f"{cls}: got {actual_frac:.3f}, expected {target_frac:.3f}")


def test_chokepoint_positions_within_radius():
    inst = _make_inst([((500.0, 500.0), "chokepoint")])
    field = place_asteroid_fields(inst)
    cx, cy = 500.0, 500.0
    radius = config.GRADIENT_CHOKEPOINT_COVER_RADIUS
    for a in field.asteroids:
        dist = math.hypot(a.x - cx, a.y - cy)
        assert dist <= radius, f"asteroid at ({a.x:.1f},{a.y:.1f}) outside radius {radius}"


# ── Five node types → five clusters ──────────────────────────────────────────

def test_five_node_types_each_produce_cluster():
    node_defs = [
        ((100.0, 100.0), "chokepoint"),
        ((300.0, 100.0), "staging"),
        ((500.0, 100.0), "objective"),
        ((700.0, 100.0), "hazard_zone_anchor"),
        ((900.0, 100.0), "flank_route"),
    ]
    inst = _make_inst(node_defs)
    field = place_asteroid_fields(inst)
    cluster_ids = {a.cluster_id for a in field.asteroids}
    assert len(cluster_ids) == 5, f"expected 5 clusters, got {len(cluster_ids)}"
    assert len(field.asteroids) > 0


# ── Vantage-only spine → empty field ─────────────────────────────────────────

def test_vantage_only_empty_field():
    inst = _make_inst([((500.0, 500.0), "vantage")])
    field = place_asteroid_fields(inst)
    assert isinstance(field, AsteroidField)
    assert len(field.asteroids) == 0


# ── Determinism ───────────────────────────────────────────────────────────────

def test_deterministic_same_seed():
    node_defs = [((500.0, 500.0), "chokepoint"), ((200.0, 200.0), "staging")]
    inst_a = _make_inst(node_defs, seed=77)
    inst_b = _make_inst(node_defs, seed=77)
    field_a = place_asteroid_fields(inst_a)
    field_b = place_asteroid_fields(inst_b)
    assert len(field_a.asteroids) == len(field_b.asteroids)
    for a, b in zip(field_a.asteroids, field_b.asteroids):
        assert a.asteroid_id == b.asteroid_id
        assert a.x == b.x
        assert a.y == b.y
        assert a.radius_xy == b.radius_xy
        assert a.height == b.height
        assert a.scale_class == b.scale_class
