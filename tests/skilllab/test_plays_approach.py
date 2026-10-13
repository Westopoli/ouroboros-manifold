# spec: Architect rulings A198 and A199 - the hold-to-contact approach is a lab setting, default off (Setup.approach 0.0);
# a play builder takes approach=0.95 to switch it on
"""Which builders set approach, which keep 0.0, and which wrappers carry the field. No engine."""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
for _p in (ROOT, Path(__file__).resolve().parent):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import scripts.skilllab.plays as plays  # noqa: E402
from fakes_batches import fake_sensors  # noqa: E402
from scripts.skilllab import asym, positions, scenes  # noqa: E402
from scripts.skilllab.ground import scenes_ground  # noqa: E402
from scripts.skilllab.asym import Side, asym_play  # noqa: E402
from scripts.skilllab.terrain import with_terrain  # noqa: E402


@pytest.fixture(autouse=True)
def _sensors(monkeypatch):
    fake_sensors(monkeypatch)
    monkeypatch.setattr(plays, "unit_stats", lambda name: {"category": 1, "max_hp": 100.0, "base_damage": 10.0,
                                                           "attack_interval": 20.0, "attack_range": 100.0,
                                                           "speed": 5.0, "sensor_radius": 700.0,
                                                           "layer_transition_time": 0.0, "aoe_radius": 0.0})


def test_the_default_is_off_the_lab_value_is_point_nine_five_and_asym_shares_both():
    assert plays.APPROACH == 0.0 and plays.APPROACH_STOP == 0.95
    assert asym.APPROACH == 0.0 and asym.APPROACH_STOP == 0.95


@pytest.mark.parametrize("play", [plays.blob_play, plays.line_play, plays.reach_play, plays.damage_play])
@pytest.mark.parametrize("swap", [False, True])
def test_basic_plays_default_to_no_approach_and_take_the_keyword(play, swap):
    assert play(16)(12, swap).approach == 0.0
    assert play(16, approach=0.95)(12, swap).approach == 0.95


@pytest.mark.parametrize("role", ["blob", "line", "skilled", "counter"])
def test_asym_play_takes_the_keyword_for_every_role_on_either_side(role):
    other = "blob"
    assert asym_play(16, Side(role), Side(other))(12, False).approach == 0.0
    assert asym_play(16, Side(role), Side(other), approach=0.95)(12, False).approach == 0.95
    assert asym_play(16, Side(other), Side(role), approach=0.95)(12, False).approach == 0.95


def test_asym_play_takes_the_keyword_for_a_mixed_side():
    mixed = Side("blob", mix=(("Vanguard", 1), ("Raider", 1)))
    s = asym_play(16, mixed, Side("line"), approach=0.95)(12, False)
    assert s.approach == 0.95
    assert any(g.formation == "points" for g in s.groups)


def test_asym_play_defaults_still_order_attack_move_before_the_rewrite():
    """The play builds attack_move groups; approach_setup turns them into group_move groups at fight time, not at build time."""
    s = asym_play(16, Side("blob"), Side("blob"))(12, False)
    assert [g.order for g in s.groups] == ["attack_move", "attack_move"]
    assert s.timeline == ()


@pytest.mark.parametrize("play", [positions.bait_play, positions.ambush_play, positions.fall_back_play])
def test_position_plays_keep_approach_off(play):
    s = play(16)(12, False)
    assert s.approach == 0.0
    assert s.timeline != ()


def test_choke_scene_keeps_approach_off():
    assert scenes.phase_b_choke()(12, False).approach == 0.0


def test_with_terrain_keeps_the_field():
    naive = asym_play(16, Side("blob"), Side("blob"), approach=0.95)
    s = with_terrain(naive, scenes_ground.tall_cover_terrain())(12, False)
    assert s.approach == 0.95


def test_guard_defenders_keeps_the_field():
    naive = asym_play(16, Side("blob"), Side("blob"), approach=0.95)
    assert scenes.guard_defenders(naive)(12, False).approach == 0.95


@pytest.mark.parametrize("counter", [False, True])
def test_tall_cover_follows_the_default_off(counter):
    assert scenes_ground.tall_cover(3, counter=counter)(16)(12, False).approach == 0.0   # off by default (A199), like every play
