# spec: docs/northstar/plans/2026-10-19-skill-lab-rev3-plan.md (requirement R4, test T8, defect D8); ledger FINDING-lab-d8; docs/northstar/plans/drift_audits/2026-10-19-positioning-in-code.md (measured table, section 3 of "Measured"); piece LAB-REV3-C
# Rule pins: R-164-01@511d57
"""LAB-REV3-C, T8 on the three audited setups of D8 (layout 192, 16 v 16, the real placed scenes of sweep.default_builds). No fight is run: the
paper prediction is a function of the Setup, so these tests build the scenes and read the score. About 3 s.

The three setups (the audit's names): the play s3_layer_above (Raiders on layer 1, reach (1, 1)), its reach_zero twin (Raiders reach (0, 0)),
and naive_defender_attacker_layer (Raiders moved to the enemy's layer 0). The opening window read all three as 10.5 : 3.0; they ended side0 (a
win), cap (a stall) and side1 (a loss); the whole-fight totals told them apart (709.0 : 565.2, 289.5 : 565.2, 297.8 : 776.8).

THE AUDIT'S PAPER SCORES (measured 2026-10-19 on lab c2d9bce8 by exp/setup_score.py; DRAFT numbers, they follow from the definition in
tests/skilllab/test_rev3_c_paper.py and are recomputed here by the reference oracle, a green control):
    play                                20.0 : 16.0    -> side0   (measured: side0 wins)
    reach_zero                          12.0 : 14.0    -> side1   (measured: cap)
    naive_defender_attacker_layer       20.0 : 20.0    -> tie     (measured: side1 wins)
RULED (Architect 2026-10-20, implementation; Westley may veto): no reading names the winner by itself, so T8's "names the winner on the three
audited setups" is NOT asserted for the second and third: the file pins what the definition gives (the three readings differ, which is what the
window could not do). The paper word folds in R7's structural oracle: "no_reach" only when nobody can reach anybody at tick 0. NONE of the three
audited setups is that: reach_zero is NOT mutual at tick 0 (its layer-0 Vanguards reach each other and score 12 : 14, side 1), so its paper
word is "side1" here, and the paper reading agrees with its no_reach_stall only at an END state (nothing asserted about that)."""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
for _p in (ROOT, ROOT / "tests" / "skilllab"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from scripts.skilllab import scenes, sweep  # noqa: E402
from test_rev3_c_paper import ref, ref_word  # noqa: E402

AUDIT = {"play": (20.0, 16.0), "reach_zero": (12.0, 14.0), "naive_defender_attacker_layer": (20.0, 20.0)}
WORDS = {"play": "side0", "reach_zero": "side1", "naive_defender_attacker_layer": "tie"}


def scene(role):
    return sweep.default_builds("s3_layer_above", role, sweep.smoke_layouts()["192"])(16, False)


@pytest.mark.parametrize("role", sorted(AUDIT))
def test_control_the_reference_oracle_reproduces_the_audit_scores(role):
    """Green today: the oracle (the audit's definition, in test_rev3_c_paper.py) gives the audit's measured numbers on the real placed scenes."""
    assert ref(scene(role)) == AUDIT[role]
    assert ref_word(scene(role)) == WORDS[role]     # the structural oracle is not mutual at tick 0 on any of the three (reach_zero included)


@pytest.mark.parametrize("role", sorted(AUDIT))
def test_the_paper_score_of_each_audited_setup(role):
    """T8, D8. Red today: scenes.paper_score does not exist."""
    s = scene(role)
    assert tuple(scenes.paper_score(s)) == AUDIT[role]
    assert scenes.paper_word(scenes.paper_score(s)) == WORDS[role]
    assert scenes.paper_prediction(s) == WORDS[role], "none of the audited setups is mutual no-reach at tick 0"


def test_the_three_setups_get_three_different_paper_readings():
    """The window read the three identically (10.5 : 3.0); the paper score separates them. Red today: AttributeError."""
    readings = {role: tuple(scenes.paper_score(scene(role))) for role in AUDIT}
    assert len(set(readings.values())) == 3, readings


def test_the_paper_call_on_the_winning_setup_is_the_measured_winner():
    """The one audited setup on which paper and outcome agree and a winner exists: the play, paper side0, measured side0 (709.0 : 565.2)."""
    assert scenes.paper_word(scenes.paper_score(scene("play"))) == "side0"
