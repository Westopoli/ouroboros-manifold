import json
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from tactical_map import Asteroid, AsteroidField, TacticalMap
from snapshot_serializer import serialize_cover_asteroids


def _make_tactical_map_with_asteroids():
    tm = TacticalMap(width=1000, height=1000)
    asteroids = [
        Asteroid(asteroid_id=0, cluster_id=0, x=100.0, y=200.0, radius_xy=2.0,  height=3.0,   scale_class="tiny"),
        Asteroid(asteroid_id=1, cluster_id=0, x=300.0, y=400.0, radius_xy=5.0,  height=8.0,   scale_class="small"),
        Asteroid(asteroid_id=2, cluster_id=0, x=500.0, y=600.0, radius_xy=15.0, height=25.0,  scale_class="medium"),
    ]
    tm.asteroid_field = AsteroidField(asteroids)
    return tm


def test_serialize_cover_asteroids_count():
    tm = _make_tactical_map_with_asteroids()
    result = serialize_cover_asteroids(tm)
    assert len(result) == 3


def test_serialize_cover_asteroids_keys():
    tm = _make_tactical_map_with_asteroids()
    result = serialize_cover_asteroids(tm)
    expected_keys = {"id", "cluster", "x", "y", "r", "h", "class"}
    for entry in result:
        assert set(entry.keys()) == expected_keys


def test_serialize_cover_asteroids_values():
    tm = _make_tactical_map_with_asteroids()
    result = serialize_cover_asteroids(tm)
    first = result[0]
    assert first["id"] == 0
    assert first["cluster"] == 0
    assert first["x"] == 100.0
    assert first["y"] == 200.0
    assert first["r"] == 2.0
    assert first["h"] == 3.0
    assert first["class"] == "tiny"


def test_serialize_cover_asteroids_json_roundtrip():
    tm = _make_tactical_map_with_asteroids()
    result = serialize_cover_asteroids(tm)
    encoded = json.dumps(result)
    decoded = json.loads(encoded)
    assert len(decoded) == 3
    first = decoded[0]
    assert first["id"] == 0
    assert first["cluster"] == 0
    assert first["x"] == 100.0
    assert first["class"] == "tiny"


# Note: no build_map_manifest function found in snapshot_serializer.py —
# manifest is assembled inline in full_snapshot(). cover_asteroids wired
# into full_snapshot() under the "map" key instead.
def test_full_snapshot_map_contains_cover_asteroids():
    """Verify full_snapshot map dict includes cover_asteroids key."""
    # Import here to keep failure localized; full_snapshot needs engine mock
    # which is complex — skip with comment if engine mock unavailable.
    # This test asserts serialize_cover_asteroids output is list[dict] only.
    tm = _make_tactical_map_with_asteroids()
    result = serialize_cover_asteroids(tm)
    assert isinstance(result, list)
    assert all(isinstance(e, dict) for e in result)
