# spec: docs/northstar/plans/2026-10-19-skill-lab-rev3-plan.md (requirement R3, test T7, defect D1); Westley 2026-10-19 on varying reach per type; ledger FINDING-lab-d1; piece LAB-REV3-C
# Rule pins: R-164-01@511d57
"""LAB-REV3-C, T7 on the real engine (OM_LAB_SLOW=1; about 15 s): the reach table is a swept input and a changed reach changes a real fight.

The scene: s3_layer_above on layout 192 (sweep.default_builds, the sweep's own build), 24 side-1 heads, seed 0, swap False. Raiders stand on
layer 1 and the enemy on layer 0, so a Raider of side 0 fires DOWN one layer. Reach is a per-TYPE table and with_reach rewrites it for BOTH sides: the enemy is 12 Vanguards and
12 Raiders on layer 0, and it is those Raiders' UPWARD fire that decides this play. What flips the fight is up 0: it strips the enemy Raiders on
layer 0 of their fire at layer 1 (the side-0 Raiders keep their down 1); down 0 moves the fight a little (tick 1796 against 1759, same winner) and up 2 or
down 2 change nothing here. (The first draft of this docstring said the DOWN value decides; the measurements below say otherwise.)
Measured 2026-10-20 on this tree (Raider reach written into Setup.unit_types, one fight each):
    (1, 1) the bible's base     side1 wins at tick 1759, survivors (0, 16)
    (2, 1) up 2                 byte-identical to (1, 1)      <- T7 as worded in the plan ("Raider reach up 2 against up 1")
    (1, 2) down 2               byte-identical to (1, 1)
    (1, 0) down 0               side1 wins at tick 1796, survivors (0, 18)
    (0, 1) up 0                 side0 wins at tick 3041, survivors (8, 0)
PLAN-VS-RECORD DIFFERENCE: the plan's T7 sentence ("reach up 2 produces a different break-even than reach up 1 on s3_layer_above") cannot hold
on this play: up 2 is inert here (the very D1 failure, a knob that cannot bite on the play it is swept on). These tests therefore compare the
base with a reach change that does bite, (0, 1), and pin up 2 as the documented inert control. Which reach values the batch sweeps, and on which
play each can bite, is for the Architect and Westley (R3 numbers beyond 0, 1, 2 are his).
BUILDER CONTRACT: sweep.with_reach(build, table) as in tests/skilllab/test_rev3_c_reach_knob.py. Red today: AttributeError, no sweep.with_reach."""
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
for _p in (ROOT, ROOT / "tests" / "skilllab"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from scripts.skilllab import sweep  # noqa: E402
from scripts.skilllab.engine import Engine  # noqa: E402
from scripts.skilllab.fight import fight  # noqa: E402

SLOW = pytest.mark.skipif(os.environ.get("OM_LAB_SLOW") != "1", reason="real fights over the real plays; set OM_LAB_SLOW=1")
HEADS = 24


def build():
    return sweep.default_builds("s3_layer_above", "play", sweep.smoke_layouts()["192"])


def key(r):
    return (r.outcome, r.ticks, r.survivors, tuple(r.firing_unit_seconds))


@SLOW
def test_a_changed_raider_reach_changes_the_real_fight():
    """T7: base (1, 1) against (0, 1) on s3_layer_above: different outcome and tick. Red today: sweep.with_reach does not exist."""
    eng = Engine()
    base = fight(build()(HEADS, False), 0, False, engine=eng)
    cfg = fight(sweep.with_reach(build(), {"Raider": (0, 1)})(HEADS, False), 0, False, engine=eng)
    assert key(cfg) != key(base), (key(cfg), key(base))
    assert cfg.outcome != base.outcome, (cfg.outcome, base.outcome)


@SLOW
def test_the_base_table_through_with_reach_is_the_play_itself():
    """Positive control for the wrapper: writing the bible's own reach (1, 1) for the Raider changes nothing (byte-identical fight)."""
    eng = Engine()
    base = fight(build()(HEADS, False), 0, False, engine=eng)
    same = fight(sweep.with_reach(build(), {"Raider": (1, 1)})(HEADS, False), 0, False, engine=eng)
    assert key(same) == key(base)


@SLOW
def test_documented_up_2_is_inert_on_this_play():
    """Documentation of the plan-vs-record difference above: Raider up 2 is byte-identical to the base on s3_layer_above (the Raiders fire down)."""
    eng = Engine()
    base = fight(build()(HEADS, False), 0, False, engine=eng)
    up2 = fight(sweep.with_reach(build(), {"Raider": (2, 1)})(HEADS, False), 0, False, engine=eng)
    assert key(up2) == key(base)
