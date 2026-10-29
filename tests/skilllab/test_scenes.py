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


# ---------------------------------------------------------------- LAB-REV2-L2 (D10): the shared point on the guard and choke scenes

def _placed_mean(setup, groups):
    from scripts.skilllab.formations import place
    pts = [p for g in groups for p in place(g.formation, g.count, g.x, g.y, g.facing_deg, g.params)]
    return sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts)


def test_phase_b_choke_sets_a_point_on_the_canvas():
    """Decision 2026-10-14: phase_b_choke sets Setup.point (the fight reads it; no fallback is needed). The bare scene has no group on
    guard, so only 'set and inside the canvas' is pinned here; the guarded variant is the test below."""
    s = scenes.phase_b_choke()(10, False)
    assert s.point is not None and 0 <= s.point[0] <= 3000 and 0 <= s.point[1] <= 1600


def test_guard_defenders_around_phase_b_choke_has_the_placed_mean_of_the_guarding_groups_as_its_point():
    """Decision (D10): after guard_defenders the point is the mean of the placed unit positions of the groups on guard (side 1 of
    the built setup, the blob here), not the setup's earlier point."""
    inner = scenes.phase_b_choke()(10, False)
    s = scenes.guard_defenders(scenes.phase_b_choke())(10, False)
    guards = [g for g in s.groups if g.order == "guard"]
    assert guards and all(g.side == 1 for g in guards)
    assert s.point == pytest.approx(_placed_mean(s, guards), abs=1e-6)
    assert s.point == pytest.approx(_placed_mean(inner, [g for g in inner.groups if g.side == 1]), abs=1e-6)
    assert s.point != pytest.approx(_placed_mean(s, [g for g in s.groups if g.side == 0]), abs=1.0)    # control: not the other side's


def test_guard_defenders_point_is_the_mean_of_the_units_not_of_the_group_centres():
    """Two guarding groups of unequal size and shape: the point is the mean over all their placed unit positions. The control
    asserts the two readings differ here, so the test can fail."""
    from scripts.skilllab.contract import Group, Setup

    def build(enemy_heads, swap):
        groups = (Group(side=0, unit="Vanguard", count=4, formation="line", x=-500.0, y=0.0, facing_deg=0.0, layer=0,
                        order="attack_move", params={"spacing": 30.0}),
                  Group(side=1, unit="Vanguard", count=2, formation="line", x=400.0, y=-200.0, facing_deg=180.0, layer=0,
                        order="attack_move", params={"spacing": 30.0}),
                  Group(side=1, unit="Vanguard", count=6, formation="line", x=600.0, y=300.0, facing_deg=180.0, layer=0,
                        order="attack_move", params={"spacing": 30.0}))
        return Setup(groups=groups, unit_types={}, point=(0.0, 0.0))

    s = scenes.guard_defenders(build)(8, False)
    guards = [g for g in s.groups if g.order == "guard"]
    assert [g.count for g in guards] == [2, 6]
    mean = _placed_mean(s, guards)
    assert s.point == pytest.approx(mean, abs=1e-6)
    centres = ((guards[0].x + guards[1].x) / 2, (guards[0].y + guards[1].y) / 2)
    assert abs(mean[1] - centres[1]) > 10.0        # control: the mean of the two group centres is a different point


def test_guard_defenders_around_the_asym_play_moves_the_point_to_the_defenders():
    """The landscape batch's use: guard_defenders(asym_play(...)). The meeting point (the midpoint of the two groups) becomes the
    guarding side's placed mean."""
    from scripts.skilllab.asym import Side, asym_play
    base = asym_play(16, Side("blob"), Side("blob"))(12, False)
    s = scenes.guard_defenders(asym_play(16, Side("blob"), Side("blob")))(12, False)
    guards = [g for g in s.groups if g.order == "guard"]
    assert guards and s.point == pytest.approx(_placed_mean(s, guards), abs=1e-6)
    assert base.point is not None and s.point != pytest.approx(base.point, abs=1.0)


def test_with_terrain_shifts_the_setup_point_by_the_same_half_canvas():
    """Decision (D11): Setup.point is a play-coordinate position like a goal and moves with the groups by (w/2, h/2) in with_terrain; a
    None point stays None (the fight's fallback is the first anchor of the other side, which has moved with the groups)."""
    import dataclasses
    from scripts.skilllab.contract import Group, Setup
    from scripts.skilllab.terrain import with_terrain
    t = Terrain(canvas=(4000.0, 3000.0), blocks=(Block(-10.0, -10.0, 10.0, 10.0, 0, 4),))
    groups = tuple(Group(side=s, unit="Vanguard", count=2, formation="line", x=x, y=0.0, facing_deg=0.0, layer=0, order="attack_move",
                         params={}) for s, x in ((0, -300.0), (1, 300.0)))
    base = Setup(groups=groups, unit_types={}, point=(100.0, -50.0))
    out = with_terrain(lambda e, sw: base, t)(2, False)
    assert out.point == pytest.approx((2100.0, 1450.0), abs=1e-6)
    assert base.point == (100.0, -50.0)                      # the build's own Setup is untouched
    assert with_terrain(lambda e, sw: dataclasses.replace(base, point=None), t)(2, False).point is None
