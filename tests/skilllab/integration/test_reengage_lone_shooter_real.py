# spec: docs/northstar/plans/2026-10-14-skill-lab-rev2-decisions.md decision 49 condition (i) as AMENDED by the Architect's ruling of 2026-10-20 (a side's silence counter advances when no unit of THAT side fired); FINDING-lab-d11
"""LAB-REV2-L8M2 against the real engine (OM_LAB_SLOW=1; a few seconds a fight): the range_up fights that the L8M tip capped or stretched
through the lone-shooter silence now end by a re-engage.

The scene: the range_up sweep's knob point OM_TP_RANGE_UP_1 = 0.25 (sweep._range_up(0.25)), play s3_layer_above, layout 192 of
sweep.smoke_layouts(), 48 side-1 heads, built exactly as the sweep builds it (sweep.default_builds then sweep.Applied), Setup.orders_per_unit
at this tree's default (True), engine = the repository library. Two cells of the scan: (seed 1, swap True) and (seed 2, swap False).
Measured (scratch runs of 2026-10-20, same scene, same library):
  pre-L8M tip (e54e69b7, the own-side counter and the old 'moved'):   seed 1 swap True: side1 wins at tick 3630, survivors (0, 37), reengage (0, 1)
                                                                     seed 2 swap False: side1 wins at tick 6424, survivors (0, 32), reengage (0, 1)
  L8M tip (b35c4576, 'either side fired' delays the victim):          seed 1 swap True: cap at 12000, survivors (1, 29), reengage (0, 0)
                                                                     seed 2 swap False: side1 wins at tick 8860, survivors (0, 28), reengage (0, 0)
  a scratch of the amended rule (own-side counter + the L8M 'moved'; not committed): seed 1 swap True: side1, (0, 38), tick 2045, reengage (0, 1)
                                                                     seed 2 swap False: side1, (0, 36), tick 2395, reengage (0, 1)
The end ticks and survivor counts are NOT asserted: the pre-L8M ticks (3630, 6424) are not reproduced by the amended rule (the L8M 'moved'
changes the re-engage timing; the scratch ends at 2045 and 2395), and the engine and the lab are free to move them. What is asserted is what
the amended condition (i) forces: a lone shooter that fires every 16 ticks at idle enemies who never reply must not silence them (decision 49
as amended, FINDING-lab-d11), so side 1 (the side shot at) re-engages exactly once (reengage (0, 1)), the fight does not cap, and side 1 wins.
Red on b35c4576: the survivor of side 0 fires on, side 1's counter is zeroed by every shot, reengage stays (0, 0) (seed 1: the cap)."""
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.skilllab import engine as engine_mod, sweep  # noqa: E402
from scripts.skilllab.fight import fight  # noqa: E402

SLOW = pytest.mark.skipif(os.environ.get("OM_LAB_SLOW") != "1", reason="a real fight; set OM_LAB_SLOW=1")

PLAY, LAYOUT, HEADS, KNOB = "s3_layer_above", "192", 48, 0.25


@pytest.fixture(scope="module")
def library():
    return engine_mod.Engine()


def _setup(swap):
    build = sweep.Applied(sweep.default_builds(PLAY, "play", sweep.smoke_layouts()[LAYOUT]), sweep._range_up(KNOB))
    return build(HEADS, swap)


@SLOW
def test_the_scene_is_the_traced_one():
    """Precondition: the 0.25 range_up knob on layer 1, 48 enemy heads, the lab's cap tick 12000 (not asserted beyond being the scene's)."""
    setup = _setup(True)
    assert setup.settings["OM_TP_RANGE_UP_1"] == KNOB and setup.max_ticks == 12000


@SLOW
@pytest.mark.parametrize("seed,swap", [(1, True), (2, False)])
def test_the_range_up_fight_with_a_lone_shooter_ends_by_a_reengage_of_the_side_shot_at(library, seed, swap):
    """Decision 49 condition (i) as amended 2026-10-20, FINDING-lab-d11. Side 1 wins by elimination of side 0, and its single re-engage is
    what ended the stall: reengage (0, 1). Pre-L8M ticks 3630 and 6424 are in the module docstring, not asserted."""
    r = fight(_setup(swap), seed, swap, engine=library)
    where = f"seed {seed} swap {swap}: outcome {r.outcome}, survivors {r.survivors}, ticks {r.ticks}, reengage {r.reengage}"
    assert r.outcome == "side1", where
    assert tuple(r.reengage) == (0, 1), where
