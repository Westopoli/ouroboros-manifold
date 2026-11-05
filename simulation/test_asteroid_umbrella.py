"""Wave 2.5R + 2.6 Cover-Asteroid LOS umbrella test.

Encodes top-level acceptance criteria from `docs/legacy/test_specs/cover_asteroid_los_spec.md`.
Initially RED. Goes GREEN only after all 9 leaves (L1-L9) merge.

DO NOT EDIT leaf-by-leaf. Parent-owned end-to-end gate.
"""

import os
import re

import pytest

import tactical_map
from tactical_map import TacticalMap


# ---------------------------------------------------------------------------
# A. Asteroid data structure + raycast API (L2)
# ---------------------------------------------------------------------------


def test_umbrella_a_asteroid_class_exists():
    assert hasattr(tactical_map, "Asteroid"), (
        "L2 not landed: tactical_map.Asteroid class must exist"
    )


def test_umbrella_a_asteroid_field_class_exists():
    assert hasattr(tactical_map, "AsteroidField"), (
        "L2 not landed: tactical_map.AsteroidField class must exist"
    )


def test_umbrella_a_tactical_map_exposes_asteroid_field():
    tm = TacticalMap(width=1000, height=1000, gradient_sources=[], spine_nodes=[])
    assert hasattr(tm, "asteroid_field"), (
        "L2 not landed: TacticalMap.asteroid_field attribute"
    )


def test_umbrella_a_asteroid_blocks_los_api():
    tm = TacticalMap(width=1000, height=1000, gradient_sources=[], spine_nodes=[])
    assert hasattr(tm, "asteroid_blocks_los"), (
        "L2 not landed: TacticalMap.asteroid_blocks_los method"
    )
    # Empty field: nothing blocks.
    assert tm.asteroid_blocks_los(0.0, 0.0, 15.0, 500.0, 500.0, 15.0) is False


# ---------------------------------------------------------------------------
# B. Placement (L3)
# ---------------------------------------------------------------------------


def test_umbrella_b_place_asteroid_fields_exists():
    import gradient_placer
    assert hasattr(gradient_placer, "place_asteroid_fields"), (
        "L3 not landed: gradient_placer.place_asteroid_fields"
    )


def test_umbrella_b_chokepoint_emits_cluster():
    import gradient_placer
    from tactical_map import TacticalMap, SpineNode

    tm = TacticalMap(
        width=1000,
        height=1000,
        gradient_sources=[],
        spine_nodes=[SpineNode(position=(500.0, 500.0), node_type="chokepoint")],
    )
    field = gradient_placer.place_asteroid_fields(tm)
    assert field is not None
    assert len(field.asteroids) > 0, "L3: chokepoint must emit at least one asteroid"


# ---------------------------------------------------------------------------
# C. Visibility (L4)
# ---------------------------------------------------------------------------


def test_umbrella_c_fog_uses_asteroid_raycast():
    """fog_of_war.compute_visibility must respect per-asteroid LOS."""
    import fog_of_war
    src = open(fog_of_war.__file__).read()
    assert "asteroid_blocks_los" in src, (
        "L4 not landed: fog_of_war must call asteroid_blocks_los"
    )


# ---------------------------------------------------------------------------
# D. Damage gate (L5)
# ---------------------------------------------------------------------------


def test_umbrella_d_no_cover_mult_in_damage():
    import damage
    src = open(damage.__file__).read()
    assert not re.search(r"\(1\.0\s*-\s*cover", src), (
        "L5 not landed: damage.py still contains (1.0 - cover) multiplier"
    )


# ---------------------------------------------------------------------------
# E. Bible language (L1)
# ---------------------------------------------------------------------------


def test_umbrella_e_bible_world_says_asteroid_los_blocker():
    path = os.path.join(
        os.path.dirname(__file__), "..", "docs", "bible", "docs/bible_history/bible_2_00_world.md"
    )
    with open(path) as f:
        body = f.read().lower()
    assert "asteroid" in body, "L1: docs/bible_history/bible_2_00_world.md must mention asteroid cover"
    assert "los" in body or "line of sight" in body or "line-of-sight" in body, (
        "L1: docs/bible_history/bible_2_00_world.md must describe LOS-blocker semantics"
    )


def test_umbrella_e_bible_combat_no_cover_density_mult():
    path = os.path.join(
        os.path.dirname(__file__), "..", "docs", "bible", "docs/bible_history/bible_2_00_combat.md"
    )
    with open(path) as f:
        body = f.read()
    assert not re.search(r"\(1\.0?\s*[-−]\s*cover_density\)", body), (
        "L1: docs/bible_history/bible_2_00_combat.md still describes cover_density damage multiplier"
    )


# ---------------------------------------------------------------------------
# F. Integration (L7)
# ---------------------------------------------------------------------------


def test_umbrella_f_apex_scenario_builder_exists():
    try:
        from asteroid_integration_fixture import build_cover_asteroid_apex_scenario
    except ImportError:
        pytest.fail("L7 not landed: build_cover_asteroid_apex_scenario fixture missing")


def test_umbrella_f_integration_cover_blocks_fire():
    from asteroid_integration_fixture import build_cover_asteroid_apex_scenario
    from fog_of_war import compute_visibility
    from damage import resolve_damage
    from unit import FIELD_HP, FIELD_X, FIELD_Y

    tm, store, attackers, defenders = build_cover_asteroid_apex_scenario()
    defender = defenders[0]
    vis = compute_visibility(store, tm)
    for atk in attackers:
        assert defender not in vis[atk], (
            "L7: defender behind asteroid cluster must be hidden"
        )
        store.auto_engage_target[atk] = defender
    hp_before = store.data[defender, FIELD_HP]
    resolve_damage(store, tm, dt=1.0)
    assert store.data[defender, FIELD_HP] == hp_before, (
        "L7: hidden defender must take no damage"
    )
    # Defender steps into open ground.
    store.data[defender, FIELD_X] = 900.0
    store.data[defender, FIELD_Y] = 500.0
    vis2 = compute_visibility(store, tm)
    assert any(defender in vis2[atk] for atk in attackers), (
        "L7: defender in open must be visible"
    )
    hp_mid = store.data[defender, FIELD_HP]
    resolve_damage(store, tm, dt=1.0)
    assert store.data[defender, FIELD_HP] < hp_mid, (
        "L7: visible defender must take damage"
    )


# ---------------------------------------------------------------------------
# G. Map manifest (L8)
# ---------------------------------------------------------------------------


def test_umbrella_g_serialize_cover_asteroids_exists():
    import snapshot_serializer
    assert hasattr(snapshot_serializer, "serialize_cover_asteroids"), (
        "L8 not landed: snapshot_serializer.serialize_cover_asteroids"
    )


def test_umbrella_g_manifest_shape():
    import snapshot_serializer
    import gradient_placer
    from tactical_map import TacticalMap, SpineNode

    tm = TacticalMap(
        width=1000,
        height=1000,
        gradient_sources=[],
        spine_nodes=[SpineNode(position=(500.0, 500.0), node_type="chokepoint")],
    )
    tm.asteroid_field = gradient_placer.place_asteroid_fields(tm)
    payload = snapshot_serializer.serialize_cover_asteroids(tm)
    assert isinstance(payload, list)
    assert len(payload) > 0
    sample = payload[0]
    for key in ("id", "cluster", "x", "y", "r", "h", "class"):
        assert key in sample, f"L8: manifest entry missing key {key!r}"


# ---------------------------------------------------------------------------
# H. Movement-block (L10 — Wave 2.6M)
# ---------------------------------------------------------------------------


def test_umbrella_h_navmesh_blocks_huge_asteroid():
    """Cell under huge asteroid is unwalkable after navmesh build."""
    from movement import Navmesh
    from tactical_map import TacticalMap, Asteroid, AsteroidField

    tm = TacticalMap(width=1000, height=1000, gradient_sources=[], spine_nodes=[])
    tm.asteroid_field = AsteroidField([
        Asteroid(
            asteroid_id=0, cluster_id=0,
            x=500.0, y=500.0,
            radius_xy=50.0, height=200.0, scale_class="huge",
        ),
    ])
    nm = Navmesh.from_tactical_map(tm)
    r, c = nm.cell(500.0, 500.0)
    assert nm.is_walkable(r, c) is False, (
        "L10 not landed: huge asteroid cell must be unwalkable"
    )


def test_umbrella_h_navmesh_passes_tiny_asteroid():
    """Cell under tiny asteroid stays walkable (debris, not blocker)."""
    from movement import Navmesh
    from tactical_map import TacticalMap, Asteroid, AsteroidField

    tm = TacticalMap(width=1000, height=1000, gradient_sources=[], spine_nodes=[])
    tm.asteroid_field = AsteroidField([
        Asteroid(
            asteroid_id=0, cluster_id=0,
            x=500.0, y=500.0,
            radius_xy=2.0, height=4.0, scale_class="tiny",
        ),
    ])
    nm = Navmesh.from_tactical_map(tm)
    r, c = nm.cell(500.0, 500.0)
    assert nm.is_walkable(r, c) is True, (
        "L10: tiny asteroid must NOT block movement"
    )


# ---------------------------------------------------------------------------
# I. AI targeting LOS gate (L11 — Wave 2.6M)
# ---------------------------------------------------------------------------


def test_umbrella_i_targeting_skips_hidden_via_sensor_pursuit():
    """AI sensor-pursuit (update_targeting) must NOT acquire target hidden by asteroid."""
    import damage
    from tactical_map import TacticalMap, Asteroid, AsteroidField
    from unit import (
        UnitStore, FIELD_X, FIELD_Y, FIELD_HP, FIELD_BASE_DAMAGE,
        FIELD_ATTACK_INTERVAL, FIELD_ATTACK_RANGE, FIELD_SENSOR_RADIUS,
        FIELD_ATTACK_TIMER, FIELD_LAYER, FIELD_AOE_RADIUS,
    )

    tm = TacticalMap(width=1000, height=1000, gradient_sources=[], spine_nodes=[])
    tm.asteroid_field = AsteroidField([
        Asteroid(
            asteroid_id=0, cluster_id=0,
            x=100.0, y=0.0,
            radius_xy=40.0, height=500.0, scale_class="huge",
        ),
    ])

    store = UnitStore()
    stats = {
        "hp": 100.0, "base_damage": 20.0, "attack_interval": 1.0,
        "attack_range": 50.0,           # short — must rely on sensor-pursuit
        "sensor_radius": 500.0,         # long — would normally see target
        "speed": 50.0, "layer_transition_time": 0.0, "category": "Strike",
    }
    attacker = store.spawn("Strike", 0, 0.0, 0.0, layer=0, stats=dict(stats))
    target = store.spawn("Strike", 1, 200.0, 0.0, layer=0, stats=dict(stats))
    store.data[attacker, FIELD_AOE_RADIUS] = 0.0
    store.data[target, FIELD_AOE_RADIUS] = 0.0
    store.data[attacker, FIELD_ATTACK_TIMER] = 0.0
    store.attack_moving[attacker] = True

    damage.update_targeting(store, tm, dt=0.1)
    # Without L11 gate, sensor-pursuit acquires target despite asteroid block.
    assert store.auto_engage_target[attacker] == -1, (
        "L11 not landed: sensor-pursuit acquired target hidden behind asteroid"
    )
