# spec: docs/northstar/plans/2026-10-14-skill-lab-rev2-decisions.md decision 43 item 4 as corrected by the Architect's 2026-10-20 ruling (L8M; the damage_up caps README calls it decision 49); docs/northstar/research/layer_dynamics/audits/damage_up_caps_2026-10-20/README.md
"""LAB-REV2-L8M against the real engine (OM_LAB_SLOW=1; about two seconds a fight): the damage_up fight that capped no longer caps.

The scene (the cap trace of 2026-10-20, docs/northstar/research/layer_dynamics/audits/damage_up_caps_2026-10-20/trace.py, trace3.py): the
damage_up sweep's knob point OM_TP_DAMAGE_UP_1 = 0.75 (sweep._damage_up(0.75), which also sets OM_TP_DAMAGE_UP_2 = 0.75 and no vision
setting: the family does not touch vision), play s3_layer_above, layout 192 of sweep.smoke_layouts(), 24 enemy heads, UNSWAPPED, replicate
seed 1 (the second fight of the cell), built exactly as the sweep builds it (sweep.default_builds then sweep.Applied), with
Setup.orders_per_unit set explicitly to False (group attack-move; this tree's default is True).
Measured on the unfixed lab tip (e54e69b7): outcome cap at 12000 ticks, survivors (2, 8), reengage (0, 0): unit 31 of side 1 holds an
unreachable destination blocked by idle bodies and shuttles in a ~70 wu loop of period ~40 ticks; the old silence counter counted its
every move, so the re-engage never fired.
Under the corrected L8 (destination-holders neither tested nor ordered; the idle units are re-engaged) the fight ends by elimination: a scratch
implementation of the rule (not committed) ended it `side1`, survivors (0, 7), at tick 6108 (the scratch end tick), reengage (0, 1). The
end tick and survivor counts are the engine's and the lab's to move; they are NOT asserted, only that the fight does not cap, that it is
not the capped survivor pair, and that a re-engage is what ended the stall.
Satisfiability: the scratch run above is the green; the red is the capped fight itself."""
import dataclasses
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.skilllab import engine as engine_mod, sweep  # noqa: E402
from scripts.skilllab.fight import fight  # noqa: E402

SLOW = pytest.mark.skipif(os.environ.get("OM_LAB_SLOW") != "1", reason="a real fight to the cap; set OM_LAB_SLOW=1")

PLAY, LAYOUT, HEADS, SEED, SWAP, KNOB = "s3_layer_above", "192", 24, 1, False, 0.75
CAPPED_SURVIVORS = (2, 8)


@pytest.fixture(scope="module")
def library():
    return engine_mod.Engine()


def _setup():
    build = sweep.Applied(sweep.default_builds(PLAY, "play", sweep.smoke_layouts()[LAYOUT]), sweep._damage_up(KNOB))
    return dataclasses.replace(build(HEADS, SWAP), orders_per_unit=False)


@SLOW
def test_the_scene_is_the_traced_one():
    """Precondition: group orders, the 0.75 knob on both layers, 24 enemy heads, the cap tick 12000 (the lab's; Westley's, not asserted
    beyond being the traced scene's)."""
    setup = _setup()
    assert setup.orders_per_unit is False and setup.max_ticks == 12000
    assert setup.settings["OM_TP_DAMAGE_UP_1"] == KNOB and setup.settings["OM_TP_DAMAGE_UP_2"] == KNOB


@SLOW
def test_the_damage_up_fight_with_a_looping_destination_holder_no_longer_caps(library):
    """Red on the unfixed tree: `cap (2, 8) at 12000, reengage (0, 0)`. Under the corrected L8 the idle units of side 1 are re-engaged and the
    fight ends by elimination."""
    r = fight(_setup(), SEED, SWAP, engine=library)
    where = f"outcome {r.outcome}, survivors {r.survivors}, ticks {r.ticks}, reengage {r.reengage}"
    assert r.outcome != "cap", where
    assert r.survivors != CAPPED_SURVIVORS, where
    # Fragile once the sight-engagement engine piece lands (the fight may then end with no re-engage): that needs a test-defect ledger row
    # (assumption changed), not a silent edit.
    assert sum(r.reengage) >= 1, "the stall was ended without a re-engage: " + where
