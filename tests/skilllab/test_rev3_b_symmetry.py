# Rule pins: R-164-01@511d57
# spec: docs/northstar/plans/2026-10-19-skill-lab-rev3-plan.md (requirement R2, test T6 the layer-symmetry control; defect D1); ledger FINDING-lab-d1; piece LAB-REV3-B
"""LAB-REV3-B, T6 (R2, D1): the layer-symmetry control. R2: "a layer-symmetry control shows a same-offset fight on (0,1) and on (3,4)
gives the same result in a space era." Fast half: the control's SHAPE, no fight. The fights are integration/test_rev3_b_symmetry_real.py.

BUILDER CONTRACT (scripts/skilllab/plays.py, the file of the lab's control plays blob_play, reach_play, damage_play; the plan lists plays.py
among B's files and gives it no other job; the NAME is the writer's, flagged to the Architect):
  plays.layer_symmetry_play(size, low_layer, unit="Raider") -> BuildFn, build(enemy_heads, swap) -> Setup
    - side 0: `size` units of `unit`, ONE blob group, on layer low_layer + 1, order attack_move;
      side 1: `enemy_heads` units of the same `unit`, ONE blob group, on layer low_layer, order attack_move (a mirror of one type, side 0
      one layer above: the offset is 1 whatever low_layer is);
    - the unit carries the bible reach of its type (R-164-01: Raider one up, one down) in `unit_types`, so both sides can fire across the
      layer; the real half checks that both sides fired;
    - NOTHING in the Setup depends on low_layer but the layers of the two groups: positions, radii, facing, point, max_ticks, settings,
      timeline, terrain are the same for every low_layer, so that two builds differ only by a shift of the layers;
    - low_layer must keep both layers inside the engine's five (0..4): low_layer outside 0..3 raises ValueError, as does size < 1 or
      enemy_heads < 1.
The control is a lab control play (like the mirror and numbers controls), not a swept play: nothing here asks for it in PLAYS_BY_FAMILY.
Where the batch runs it and how the artifact reports it is not in the plan (flagged); the real half is the test that it holds."""
import dataclasses
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.skilllab import plays  # noqa: E402
from scripts.skilllab.contract import Group, Setup  # noqa: E402


def shifted(setup, d):
    return dataclasses.replace(setup, groups=tuple(dataclasses.replace(g, layer=g.layer + d) for g in setup.groups))


def side(setup, n):
    return [g for g in setup.groups if g.side == n]


# ---- the comparison's own positive control (green on the lab tip) -----------------------------------------------------------------

def test_control_the_shift_comparison_sees_a_moved_group():
    g = lambda side_, layer, x: Group(side=side_, unit="Raider", count=4, formation="blob", x=x, y=0.0, facing_deg=0.0, layer=layer, order="attack_move")
    a = Setup(groups=(g(0, 1, -300.0), g(1, 0, 300.0)), unit_types={})
    assert shifted(a, 3) == Setup(groups=(g(0, 4, -300.0), g(1, 3, 300.0)), unit_types={})
    assert shifted(a, 3) != Setup(groups=(g(0, 4, -300.0), g(1, 3, 301.0)), unit_types={})      # a moved x is not a pure layer shift
    assert shifted(a, 3) != Setup(groups=(g(0, 4, -300.0), g(1, 4, 300.0)), unit_types={})      # a different offset is not either


# ---- the control's shape ----------------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("low", [0, 1, 2, 3])
def test_t6_the_control_puts_side_0_one_layer_above_side_1_whatever_the_low_layer(low):
    """T6 (R2). Red today: plays.layer_symmetry_play does not exist."""
    s = plays.layer_symmetry_play(16, low)(16, False)
    assert {g.layer for g in side(s, 0)} == {low + 1} and {g.layer for g in side(s, 1)} == {low}
    assert len(side(s, 0)) == len(side(s, 1)) == 1
    assert side(s, 0)[0].count == 16 and side(s, 1)[0].count == 16
    assert side(s, 0)[0].unit == side(s, 1)[0].unit == "Raider"
    assert {g.formation for g in s.groups} == {"blob"} and {g.order for g in s.groups} == {"attack_move"}


@pytest.mark.parametrize("low", [1, 2, 3])
def test_t6_two_builds_differ_only_by_a_shift_of_the_layers(low):
    """The (0,1) fight and the (3,4) fight are the same fight but for the layers: the Setup of low 3 is the Setup of low 0 with every
    group's layer plus 3, field for field (positions, radii, facing, point, max_ticks, settings, timeline, terrain)."""
    base = plays.layer_symmetry_play(16, 0)(16, False)
    assert shifted(base, low) == plays.layer_symmetry_play(16, low)(16, False)


def test_t6_the_heads_scale_side_1_and_side_0_stays_size():
    s = plays.layer_symmetry_play(16, 0)(24, False)
    assert side(s, 0)[0].count == 16 and side(s, 1)[0].count == 24


def test_t6_the_unit_carries_its_bible_reach_so_both_sides_can_fire_across_the_layer():
    """R-164-01: the Raider reaches one layer up and one down. The entry is read the way fight._check_reach reads it."""
    s = plays.layer_symmetry_play(16, 0)(16, False)
    entry = s.unit_types["Raider"]
    assert tuple(entry["reach"]) == (1, 1)


def test_t6_another_unit_type_builds_with_its_own_reach():
    s = plays.layer_symmetry_play(8, 0, unit="Interceptor")(8, False)
    assert {g.unit for g in s.groups} == {"Interceptor"} and tuple(s.unit_types["Interceptor"]["reach"]) == (2, 1)


@pytest.mark.parametrize("low", [-1, 4, 5])
def test_t6_a_low_layer_outside_0_to_3_is_refused(low):
    with pytest.raises(ValueError):
        plays.layer_symmetry_play(16, low)


def test_t6_a_size_or_headcount_below_one_is_refused():
    with pytest.raises(ValueError):
        plays.layer_symmetry_play(0, 0)(16, False)
    with pytest.raises(ValueError):
        plays.layer_symmetry_play(16, 0)(0, False)
