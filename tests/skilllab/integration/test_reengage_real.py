# Rule pins: R-087-06@2b0850, R-099-05@ea8d02
# spec: docs/northstar/plans/2026-10-14-skill-lab-rev2-decisions.md decision 28 point 3 (re-engage) and decision 23 (FINDING-group-orders-cap)
"""LAB-REV2-L8 against the real engine (OM_LAB_SLOW=1: two capped fights today, about a second each).

The cap trace of 2026-10-19 (docs/northstar/research/layer_dynamics/audits/attackmove_idle_cap_2026-10-19/, cf3.py): under GROUP
attack-move orders (Setup.orders_per_unit=False) two fights end at the 12000-tick cap: the objective scene at start distance 2800,
16 v 16 Vanguards, seed 0, unswapped, with 1 v 2 alive (contact at tick 290); and the mirror control, plays.blob_play(16)(16, True)
(16 v 16, seed 0, SWAPPED), with 1 v 1 alive. (The objective scene swapped does not cap today; it is not the mirror control.) The survivors' routes ended short of
their point, they went idle holding the attack-move with the enemy just outside range, and nobody closed. With the lab's re-engage
(a silent side with a visible enemy is attack-moved onto the enemy centroid) both fights must end by elimination.

Red today: both fights are outcome "cap" at 12000 ticks. The mechanism assertion (the counts) ties the elimination to the re-engage
and not to luck; no tick count, survivor count or count of re-engage events is pinned beyond "at least one".

WHY "at least one" SURVIVES THE ENGINE FOLLOW-ON E1b (measured 2026-10-19 with a throwaway ~35-line reference of the trigger, in scratch
worktrees only, nothing committed; E1b = origin/push/labrev2-e1b 59416a00, R-087-06 return-fire resume): on the E1b engine, with the
trigger switched off, both group-order fights still end at the cap, identically to the lab tip without E1b (objective: cap, 12000
ticks, survivors (1, 2); mirror swapped: cap, survivors (1, 1)); with the trigger on, both end by elimination (objective: side1 at
tick 5328, reengage (0, 1); mirror: side1 at tick 4370, reengage (0, 1)), on the lab tip and on E1b alike. The cap is the group
give-up pass (R-099-05), which E1b does not touch (E1b changes the return-fire redirect, R-087-06, which a group order never
reaches here), so these two fights are still re-engage-only eliminations and the count assertion stays. A fight that E1b makes end
without any re-engage would be a different scene, not these two. A fight takes about one second.
"""
import dataclasses
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.skilllab import engine as engine_mod, plays, scenes  # noqa: E402
from scripts.skilllab.fight import fight  # noqa: E402

SLOW = pytest.mark.skipif(os.environ.get("OM_LAB_SLOW") != "1", reason="real fights to the cap; set OM_LAB_SLOW=1")


@pytest.fixture(scope="module")
def library():
    return engine_mod.Engine()


def _group_orders_objective():
    setup = scenes.objective_scene(2800.0)(16, False)
    return dataclasses.replace(setup, orders_per_unit=False)


def _group_orders_mirror():
    return dataclasses.replace(plays.blob_play(16)(16, True), orders_per_unit=False)


@SLOW
@pytest.mark.parametrize("name,make,swap", [
    ("objective scene, unswapped (caps with 1 v 2 alive today)", _group_orders_objective, False),
    ("mirror control, swapped (caps with 1 v 1 alive today)", _group_orders_mirror, True),
])
def test_the_capped_group_order_fights_end_by_elimination(library, name, make, swap):
    setup = make()
    res = fight(setup, 0, swap, engine=library)
    assert res.outcome in ("side0", "side1", "draw"), "%s: %s at tick %d, survivors %r" % (name, res.outcome, res.ticks, res.survivors)
    assert res.ticks < setup.max_ticks and 0 in res.survivors
    assert res.first_contact_tick >= 0


@SLOW
@pytest.mark.parametrize("make,swap", [(_group_orders_objective, False), (_group_orders_mirror, True)])
def test_the_elimination_came_through_a_reengage(library, make, swap):
    """Mechanism tie: each fight was a cap because nobody closed; it ends because a side was re-engaged."""
    res = fight(make(), 0, swap, engine=library)
    assert sum(res.reengage) >= 1, res.reengage


@SLOW
def test_per_unit_orders_on_the_same_scene_are_untouched_by_the_counts_field(library):
    """Control: per-unit orders (today's default) end by elimination on this scene, and the count is readable as a pair of ints."""
    res = fight(scenes.objective_scene(2800.0)(16, False), 0, False, engine=library)
    assert res.outcome in ("side0", "side1", "draw")
    assert len(res.reengage) == 2 and all(isinstance(c, int) and c >= 0 for c in res.reengage)
