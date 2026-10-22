# Rule pins: R-096-02@e8ae96
# spec: docs/northstar/plans/2026-10-02-movement-layers-and-search-plan.md::Phase S (order timeline: later orders for bait, ambush, fall-back)
"""The order timeline through the production library.

EXPECTED RED until the timeline is implemented: Step, Setup.timeline and FightResult.steps_fired do not exist yet.
Only structure is asserted (what must hold once implemented), not combat numbers; the semantics are fixed in
tests/skilllab/test_timeline.py.
"""
import dataclasses
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.skilllab import engine, fight  # noqa: E402
from scripts.skilllab.contract import Group, Setup, Step  # noqa: E402


@pytest.fixture(scope="module")
def library():
    return engine.Engine()


def group(side, x, facing):
    return Group(side=side, unit="Vanguard", count=4, formation="line", x=x, y=0.0, facing_deg=facing, layer=0,
                 order="idle", goal=None, params={"spacing": 30.0})


def setup(timeline):
    return Setup(groups=(group(0, -600.0, 0.0), group(1, 300.0, 180.0)), unit_types={}, timeline=timeline)


def test_delayed_attack_move_fires_once_and_the_fight_ends(library):
    """Group 0 idles far from group 1; the tick-20 step sends it attack_move at the enemy. It fires at tick 20
    exactly once, the order takes effect (first contact after tick 20, damage dealt), and a second run is identical.

    LAB-REV2-L2 (Q-LAB-03): the old assertion "the fight is not a cap" is dropped. A timeline step issues a GROUP attack-move, and
    until LAB-REV2-E1 lands the engine ends a group's attack-move after its first engagement (R-096-02, rewritten 2026-10-13), so
    this scene can end `cap` on today's engine; E1's test pins elimination. The outcome must still be one of the four names."""
    s = setup((Step(0, ("tick", 20), "attack_move"),))
    first, second = fight.fight(s, 1, False, engine=library), fight.fight(s, 1, False, engine=library)
    assert first.steps_fired == ((0, 20),)
    assert first.outcome in ("side0", "side1", "draw", "cap")
    assert first.first_contact_tick > 20 and first.strength_left != (1.0, 1.0)
    assert first == second


def test_no_timeline_fires_nothing(library):
    """Control: the same two idle groups with timeline () report steps_fired == (), and swap fires the same steps."""
    quiet = fight.fight(setup(()), 1, False, engine=library)
    assert quiet.steps_fired == () and quiet.first_contact_tick == -1
    s = setup((Step(0, ("tick", 20), "attack_move"),))
    assert fight.fight(s, 1, True, engine=library).steps_fired == ((0, 20),)
