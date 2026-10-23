# spec: docs/northstar/plans/2026-10-19-skill-lab-rev3-plan.md (requirement R8, test T10; defect D6); ledger FINDING-lab-d6; piece LAB-REV3-A
"""LAB-REV3-A, T10 (R8, D6) premise against the real engine (OM_LAB_SLOW=1; a second): the library ignores OM_TP_CATMULT_*. A Raider
(Strike) against a Bombard (Siege) is the 1.5 cell of ALG-60; the setting OM_TP_CATMULT_STRIKE_SIEGE at a quarter of that (0.375) leaves
the whole row byte-identical to the unset fight, which is why the family cannot be swept (FINDING-lab-d6).

POSITIVE CONTROL, green on the lab tip, and a TRIPWIRE: it must go red when the engine piece (csrc/unit.c reads the settings at run time,
unnamed in the plan) lands, and that piece retires this test together with the unavailable marker (test_rev3_a_category.py). Until then
it is what makes "unavailable" true rather than assumed. The control that the instrument sees a matrix change at all: the same fight
with the Raiders' own damage scaled does change the row."""
import dataclasses
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.skilllab import rows as rows_mod  # noqa: E402
from scripts.skilllab.contract import Group, Setup  # noqa: E402
from scripts.skilllab.fight import fight  # noqa: E402

SLOW = pytest.mark.skipif(os.environ.get("OM_LAB_SLOW") != "1", reason="real fights; set OM_LAB_SLOW=1")
KNOB = "OM_TP_CATMULT_STRIKE_SIEGE"


def setup(settings=None, unit_types=None):
    g = lambda side, unit, n, x: Group(side=side, unit=unit, count=n, formation="blob", x=x, y=0.0, facing_deg=0.0 if side == 0 else 180.0,
                                       layer=0, order="attack_move", params={"radius": 60.0})
    return Setup(groups=(g(0, "Raider", 4, -250.0), g(1, "Bombard", 4, 250.0)), unit_types=unit_types or {}, settings=settings or {})


def row(**kw):
    return rows_mod.fight_row(fight(setup(**kw), 0, False))


@SLOW
def test_positive_control_the_engine_ignores_the_category_multiplier_settings():
    """Green on the lab tip (the D6 premise): the setting is accepted, and the row does not move."""
    assert row(settings={KNOB: 0.375}) == row()


@SLOW
def test_positive_control_the_row_does_move_when_the_raiders_damage_does():
    """Green on the lab tip: the comparison above is not blind; a damage change on the same fight moves the row."""
    stronger = {"Raider": {"base": "Raider", "scale": {"base_damage": 0.5}}}
    assert row(unit_types=stronger) != row()
