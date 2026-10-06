# spec: R-096-08 (guard), R-096-04 (layer reach) - scripts/skilllab/ground/scenes_ground.py tall_cover (unconfirmed draft)
"""The tall-cover scene: a wall of nine Cover discs between a blob and guarding defenders. Fake sensors, no engine."""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
for _p in (ROOT, Path(__file__).resolve().parents[1]):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from fakes_batches import fake_sensors  # noqa: E402
from scripts.skilllab.ground import scenes_ground as scenes  # noqa: E402
from scripts.skilllab.contract import Cover, Terrain  # noqa: E402


@pytest.fixture(autouse=True)
def sensors(monkeypatch):
    fake_sensors(monkeypatch)


def build(height=3, counter=False, size=16, heads=12, swap=False):
    return scenes.tall_cover(height=height, counter=counter)(size)(heads, swap)


def test_terrain_is_nine_discs_in_a_wall_at_canvas_centre():
    t = build().terrain
    assert t.canvas == (4000.0, 4000.0) and t.blocks == ()
    assert t.covers == tuple(Cover(x=2000.0, y=2000.0 + k * 150, radius=100.0, height=3) for k in range(-4, 5))
    assert len(t.covers) == 9


@pytest.mark.parametrize("h", [1, 2, 4])
def test_height_is_the_argument(h):
    assert {c.height for c in build(height=h).terrain.covers} == {h}


def test_default_is_height_three_without_counter():
    s = scenes.tall_cover()(16)(12, False)
    assert {c.height for c in s.terrain.covers} == {3} and s.unit_types == {}


def test_counter_false_keeps_attackers_on_layer_zero_and_has_no_unit_types():
    s = build(counter=False)
    assert s.unit_types == {}
    assert {g.layer for g in s.groups if g.side == 0} == {0}
    assert {g.unit for g in s.groups} == {"Vanguard"}


def test_counter_true_lifts_attackers_to_the_cover_height_with_the_reach_type():
    for h in (2, 3):
        s = build(height=h, counter=True)
        assert s.unit_types == {"VanguardHigh": {"base": "Vanguard", "scale": {}, "set": {}, "reach": (0, h)}}
        side0 = [g for g in s.groups if g.side == 0]
        assert side0 and {g.unit for g in side0} == {"VanguardHigh"} and {g.layer for g in side0} == {h}
        assert {g.layer for g in s.groups if g.side == 1} == {0} and {g.unit for g in s.groups if g.side == 1} == {"Vanguard"}


def test_defenders_guard_and_attackers_attack_move():
    for counter in (False, True):
        s = build(counter=counter)
        assert {g.order for g in s.groups if g.side == 1} == {"guard"}
        assert {g.order for g in s.groups if g.side == 0} == {"attack_move"}


def test_headcounts_are_size_against_enemy_heads_blob_against_blob():
    s = build(size=16, heads=9)
    assert sum(g.count for g in s.groups if g.side == 0) == 16
    assert sum(g.count for g in s.groups if g.side == 1) == 9
    assert {g.formation for g in s.groups} == {"blob"}


def test_groups_sit_either_side_of_the_wall_inside_the_canvas():
    s = build()
    x0 = [g.x for g in s.groups if g.side == 0]
    x1 = [g.x for g in s.groups if g.side == 1]
    assert max(x0) < 2000.0 < min(x1)
    assert all(0 <= g.y <= 4000 for g in s.groups)


def test_labels_carry_the_draft_status_and_both_play_names():
    for counter in (False, True):
        b = scenes.tall_cover(counter=counter)(16)
        assert b.labels["status"] == "unconfirmed draft"
        assert "play_side0" in b.labels and "play_side1" in b.labels


def test_swap_still_builds_the_same_scene():
    assert build(swap=True).terrain == build(swap=False).terrain


@pytest.mark.parametrize("bad", [-1, 6, 2.5])
@pytest.mark.parametrize("counter", [False, True])
def test_bad_height_raises_value_error(bad, counter):
    with pytest.raises(ValueError):
        scenes.tall_cover(height=bad, counter=counter)(16)(12, False)


def test_covers_are_validated_whole_discs_of_radius_100():
    for c in build().terrain.covers:
        assert c.radius == 100.0 and isinstance(c.height, int)


def test_the_returned_terrain_type_is_a_terrain():
    assert isinstance(build().terrain, Terrain)
