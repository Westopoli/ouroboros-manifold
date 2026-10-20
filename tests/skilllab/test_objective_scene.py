# spec: docs/northstar/plans/2026-10-14-skill-lab-rev2-spec.md ruling 6 (a meeting is both sides attack-moved to one point) and Q-LAB-03; was P2 of the 2026-10-06 layout-search spec
"""scenes.objective_scene(start_distance, unit, size): the meeting scene. Rev 2 (LAB-REV2-L2): Setup.start_distance, Setup.objective
and Setup.quiet_from_first_damage are retired with the stalemate window (Q-LAB-03); the scene carries Setup.point, the middle of the
corridor, and both groups attack-move to it (one order per unit, Setup.orders_per_unit).

Name left open by the spec and kept: the function is still called objective_scene (only the Setup field `objective` is retired);
a group's own goal may be None (the fight uses Setup.point) or equal to the point.

Retired with this rewrite (Q-LAB-03): the quiet-window tests (cap-only before contact, quiet window from first damage, a later
damage restarts it, flag false keeps the window from tick zero) and the byte-identity hash of blob_play / line_play rows
(`DEFAULT_PLAYS_HASH`): the rows gain columns in rev 2, so the guard is the re-recorded golden hashes of
integration/test_cross_machine.py (ledger row TD-LAB-REV2-golden)."""
import dataclasses
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
for _p in (ROOT, Path(__file__).resolve().parent):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from scripts.skilllab import engine, scenes  # noqa: E402
from scripts.skilllab.contract import Setup  # noqa: E402
from scripts.skilllab.fight import fight  # noqa: E402

RETIRED = ("start_distance", "objective", "quiet_from_first_damage", "mopup", "mopup_interval_ticks", "stalemate_ticks")


def _sides(setup):
    return (next(g for g in setup.groups if g.side == 0), next(g for g in setup.groups if g.side == 1))


def test_setup_has_none_of_the_objective_scene_fields_any_more():
    """Q-LAB-03: start_distance, objective and quiet_from_first_damage are gone from Setup; point is the replacement."""
    fields = Setup.__dataclass_fields__
    assert not set(RETIRED) & set(fields) and "point" in fields
    setup = scenes.objective_scene(2800.0)(16, False)
    assert not any(hasattr(setup, name) for name in RETIRED)


def test_objective_scene_sets_sides_d_apart():
    """Sides start `d` apart (anchor distance in x, same y)."""
    for d in (1400.0, 2800.0):
        g0, g1 = _sides(scenes.objective_scene(d)(16, False))
        assert (g1.x - g0.x, g1.y - g0.y) == (d, 0.0)


def test_objective_scene_sends_both_groups_to_the_point_between_them():
    """Ruling 6: both groups attack-move to one point, at the corridor's middle, one order per group (the default since the
    L4 flip, TD-LAB-REV2-flip)."""
    setup = scenes.objective_scene(2800.0)(16, False)
    g0, g1 = _sides(setup)
    assert setup.point is not None and setup.orders_per_unit is False
    for g in (g0, g1):
        assert g.order == "attack_move" and g.goal in (None, tuple(setup.point))
    assert g0.x < setup.point[0] < g1.x
    assert setup.point == pytest.approx(((g0.x + g1.x) / 2, (g0.y + g1.y) / 2))


def test_objective_scene_has_16_v_16_by_default_and_takes_the_enemy_heads():
    setup = scenes.objective_scene(1400.0)(24, False)
    assert sorted((g.side, g.count) for g in setup.groups) == [(0, 16), (1, 24)]


def test_objective_scene_size_and_unit_arguments_are_kept():
    setup = scenes.objective_scene(1400.0, unit="Warden", size=8)(12, False)
    assert sorted((g.side, g.count, g.unit) for g in setup.groups) == [(0, 8, "Warden"), (1, 12, "Warden")]


def test_objective_scene_rejects_empty_sides():
    with pytest.raises(ValueError):
        scenes.objective_scene(1400.0)(0, False)
    with pytest.raises(ValueError):
        scenes.objective_scene(1400.0, size=0)(8, False)


def test_objective_scene_is_deterministic_and_ignores_swap():
    a = scenes.objective_scene(1400.0)(12, False)
    assert a == scenes.objective_scene(1400.0)(12, False) == scenes.objective_scene(1400.0)(12, True)


def test_far_open_ground_fight_is_ended_by_elimination_not_by_quiet():
    """Q-LAB-03 / ruling 6 (real engine): a fight at d = 2800 on open ground has contact after tick 0 and ends side0, side1 or
    draw: never a stalemate, never the cap (red on the old code: it ended by its mop-up and quiet rules)."""
    # LAB-REV2 flip ruler (TD-LAB-REV2-flip, decision 40): the test is about the ending rule, measured with per-unit orders as before the flip
    # (with the group order this scene caps at 12000 ticks with 1 v 2 left on seed 0: reported as a finding, not tested here).
    setup = dataclasses.replace(scenes.objective_scene(2800.0)(16, False), orders_per_unit=True)
    r = fight(setup, 0, False, engine=engine.Engine())
    assert r.first_contact_tick > 0
    assert r.outcome in ("side0", "side1", "draw"), (r.outcome, r.ticks)


def test_positive_control_the_same_scene_with_a_two_tick_cap_is_a_cap():
    """Control: the cap is still a label for a fight that is not over, so the test above is not vacuous."""
    setup = dataclasses.replace(scenes.objective_scene(2800.0)(16, False), max_ticks=2)
    r = fight(setup, 0, False, engine=engine.Engine())
    assert (r.outcome, r.ticks) == ("cap", 2)
