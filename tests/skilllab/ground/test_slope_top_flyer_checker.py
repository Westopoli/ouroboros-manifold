# Rule pins: R-087-10
"""Engine rules round 2, T8: the whole-run checker agrees with the engine about flyers (DRAFT-slant-ground-only, tests/csim/test_E11_R087_10_spherical_distance.py).

R-087-10 (docs/bible/epics/E-11-units-and-combat.md): "... the distance is spherical: the horizontal distance and the height difference between the two units' layers ...". Read
DRAFT-slant-ground-only (provisional, pending the owner's ruling): the slant is used only when both units are walkers on ground bands; a flyer is measured flat.

The fight is the one of test_slope_top_variants.py::test_the_flyer_fight_still_ends_by_elimination (scene s1_slope_top_flyer, 16 a side, seed 1, walkers and flyers on both sides): the
engine ending that fight by elimination needs flyers to shoot across air layers, and the shots the lab's checker then sees are shots by flyers at horizontal range and 900 wu and more by slant.
Premise dumped 2026-11-11 on this tree (before the engine change): the fight runs to the 12,000 tick cap (outcome 'cap'), because no flyer can reach another layer by slant. This test is GREEN
today (no flyer shoots across layers yet, the checker has nothing to report) and is the integration guard: it goes red if the engine is changed and the checker is not, and stays green when both are.
"""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.skilllab import fight, invariants  # noqa: E402
from scripts.skilllab.ground import scenes_ground as sg  # noqa: E402

pytestmark = pytest.mark.variant


def test_R_087_10_the_monitor_reports_no_slant_violation_in_the_flyer_fight():
    """R-087-10 wired (DRAFT-slant-ground-only): every violation the shipped Monitor collects over the whole flyer fight (kept whole, not the 20 a result carries) is judged: none is an
    R-087-10 report. Green today (vacuous: no flyer shoots across layers); red when the engine lets flyers shoot across air layers and the checker still measures them by slant."""
    made, orig = [], invariants.Monitor

    class Cap(orig):
        def __init__(self, *a, **k):
            super().__init__(*a, **k)
            made.append(self)
    invariants.Monitor = Cap
    try:
        fight.fight(sg.slope_top_flyer()(16, False), 1, False)
    finally:
        invariants.Monitor = orig
    bad = [v for v in made[0].violations if v["rule"] == "R-087-10"]
    assert bad == [], "%d R-087-10 reports, first %s" % (len(bad), bad[:3])
