# spec: docs/northstar/plans/2026-10-19-skill-lab-rev3-plan.md (requirement R2, test T6 the layer-symmetry control; defect D1); ledger FINDING-lab-d1; piece LAB-REV3-B
"""LAB-REV3-B, T6 (R2, D1) against the real engine (OM_LAB_SLOW=1; about two minutes): the layer-symmetry control. A same-offset fight gives
the same result on layers (0,1), (1,2), (2,3) and (3,4) in a space era (open ground, no terrain). The control is
`plays.layer_symmetry_play(16, low_layer)` of tests/skilllab/test_rev3_b_symmetry.py (builder contract there).

Two settings, because the layer offset changes nothing at the defaults: measured on the lab tip (2026-10-20, this file's author, a scratch
Setup of the same shape), Raider against Raider with side 0 one layer up gives, at the base settings, the SAME result as with the offset
removed (side1 wins at tick 1040, survivors (0, 3), seed 0), so a symmetry check at the base settings cannot tell a symmetric engine from
one that ignores the layer. Under OM_TP_DAMAGE_UP_1 = 0.5 (the damage the units that fire UP deal, ALG-60's layer penalty knob) the offset
bites: side 0 wins at tick 889 with (10, 0) left where the flat fight is the loss above. So:
  - SYMMETRY, base settings and damage_up 0.5: layers (0,1) to (3,4) give one result per (seed, swap), four seeds-and-swaps each;
  - POSITIVE CONTROL: at damage_up 0.5 the offset-1 fight is NOT the flat fight (the comparison can fail);
  - both sides fired across the layer and no fight capped (a fight that does not fire is not a symmetry result)."""
import dataclasses
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.skilllab import plays  # noqa: E402
from scripts.skilllab.fight import fight  # noqa: E402

SLOW = pytest.mark.skipif(os.environ.get("OM_LAB_SLOW") != "1", reason="real fights; set OM_LAB_SLOW=1")
RUNS = [(0, False), (0, True), (1, False), (1, True)]            # (seed, swap)
SETTINGS = {"base": {}, "damage_up_half": {"OM_TP_DAMAGE_UP_1": 0.5}}


def key(r):
    return (r.outcome, r.ticks, r.survivors, round(r.margin, 6), tuple(r.firing_unit_seconds), tuple(r.firing_window))


def run(setup, seed, swap):
    return fight(setup, seed, swap)


def control(low, settings):
    return dataclasses.replace(plays.layer_symmetry_play(16, low)(16, False), settings=dict(settings))


def flat(setup):
    low = min(g.layer for g in setup.groups)
    return dataclasses.replace(setup, groups=tuple(dataclasses.replace(g, layer=low) for g in setup.groups))


@SLOW
@pytest.mark.parametrize("name", sorted(SETTINGS))
def test_t6_the_same_offset_fight_gives_the_same_result_on_every_layer_pair(name):
    """T6 (R2): layers (0,1), (1,2), (2,3), (3,4), equal outcome, ticks, survivors, margin and firing for every seed and swap; every
    fight fired on both sides and ended (not "cap"). Red today: plays.layer_symmetry_play does not exist."""
    for seed, swap in RUNS:
        got = {low: run(control(low, SETTINGS[name]), seed, swap) for low in (0, 1, 2, 3)}
        for low, r in got.items():
            assert r.outcome in ("side0", "side1"), (name, low, seed, swap, r.outcome)
            assert min(r.firing_unit_seconds) > 0, (name, low, seed, swap, r.firing_unit_seconds)
        assert {low: key(r) for low, r in got.items() if key(r) != key(got[0])} == {}, (name, seed, swap, key(got[0]))


@SLOW
def test_t6_positive_control_the_offset_matters_under_damage_up_half():
    """The comparison above can fail: at damage_up 0.5 the fight one layer apart is not the fight on one layer (seed 0 unswapped: a win
    for side 0 at tick 889 against a loss at tick 1040 on the lab tip). Red today for the missing control play."""
    setup = control(0, SETTINGS["damage_up_half"])
    assert key(run(setup, 0, False)) != key(run(flat(setup), 0, False))


@SLOW
def test_t6_positive_control_the_base_settings_do_not_see_the_offset():
    """Why the second setting exists (see the module docstring): at the base settings the offset-1 fight IS the flat fight, so equality
    across layer pairs there is a weaker claim than under damage_up 0.5. Green once the control exists; records the measurement."""
    setup = control(0, SETTINGS["base"])
    assert key(run(setup, 0, False)) == key(run(flat(setup), 0, False))
