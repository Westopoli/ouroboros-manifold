# spec: batch runner spec addendum 4 (batch4_spec.md) section 2 - scripts/skilllab/scenes.py, phase_b_choke
"""The Phase B choke scene: canvas coordinates, two Blocks, defenders on a line, attackers in a blob. No engine."""
import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.skilllab import scenes  # noqa: E402
from scripts.skilllab.contract import Block, Terrain  # noqa: E402


def test_groups_counts_and_orders():
    s = scenes.phase_b_choke()(10, False)
    assert len(s.groups) == 2
    d, a = s.groups
    assert (d.side, d.unit, d.count, d.formation, d.order) == (0, "Vanguard", 8, "line", "attack_move")
    assert (a.side, a.unit, a.count, a.formation, a.order) == (1, "Vanguard", 10, "blob", "attack_move")
    assert d.layer == 0 and a.layer == 0 and d.goal is None and a.goal is None


def test_positions_facing_spacing_and_blob_radius():
    s = scenes.phase_b_choke(defenders=6)(12, False)
    d, a = s.groups
    assert (d.x, d.y, d.facing_deg) == (1700.0, 800.0, 180.0)
    assert (a.x, a.y, a.facing_deg) == (800.0, 800.0, 0.0)
    assert d.params == {"spacing": 30}
    assert a.params == {"radius": pytest.approx(80 + 12 * math.sqrt(12))}


def test_blob_radius_follows_enemy_heads():
    for n in (7, 12):
        assert scenes.phase_b_choke()(n, False).groups[1].params["radius"] == pytest.approx(80 + 12 * math.sqrt(n))


def test_terrain_canvas_and_the_two_blocks_exactly():
    t = scenes.phase_b_choke()(8, False).terrain
    assert t == Terrain(canvas=(3000.0, 1600.0),
                        blocks=(Block(1500, 0, 1600, 700, 0, 4), Block(1500, 900, 1600, 1600, 0, 4)))
    assert t.covers == ()


def test_setup_is_otherwise_default():
    s = scenes.phase_b_choke()(8, False)
    assert s.timeline == () and s.settings == {} and s.abilities is False


def test_labels():
    b = scenes.phase_b_choke()
    assert b.labels["play_side0"] == "defenders line" and b.labels["play_side1"] == "attackers blob"
    assert b.labels["status_side0"] == "naive" and b.labels["status_side1"] == "naive"


def test_defenders_count_is_the_argument():
    for n in (1, 5, 12):
        assert scenes.phase_b_choke(defenders=n)(8, False).groups[0].count == n


def test_value_errors():
    with pytest.raises(ValueError):
        scenes.phase_b_choke(defenders=0)(8, False)
    with pytest.raises(ValueError):
        scenes.phase_b_choke(defenders=-3)(8, False)
    with pytest.raises(ValueError):
        scenes.phase_b_choke()(0, False)


def test_value_error_for_zero_defenders_is_raised_by_the_call_or_the_build():
    with pytest.raises(ValueError):
        scenes.phase_b_choke(defenders=0)(8, False)


def test_equal_inputs_give_identical_setups_and_swap_is_ignored():
    a, b = scenes.phase_b_choke(8)(9, False), scenes.phase_b_choke(8)(9, False)
    assert a == b
    assert scenes.phase_b_choke(8)(9, True) == a
    assert scenes.phase_b_choke(8)(10, False) != a


def test_all_spawn_points_sit_inside_the_canvas_and_on_their_own_side_of_the_wall():
    from scripts.skilllab.formations import place
    s = scenes.phase_b_choke()(12, False)
    for g, west in zip(s.groups, (False, True)):
        for x, y in place(g.formation, g.count, g.x, g.y, g.facing_deg, g.params):
            assert 0 <= x <= 3000 and 0 <= y <= 1600
            assert (x < 1500) if west else (x > 1600), (g.side, x)
