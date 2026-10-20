# spec: docs/northstar/plans/2026-10-19-skill-lab-rev3-plan.md (requirement R7 "pre-flight refuses a scene that starts that way", test T9, defect D7); ledger FINDING-lab-d7; piece LAB-REV3-C
# Rule pins: R-164-01@511d57
"""LAB-REV3-C, R7's second half: scenes.preflight refuses a scene in which no living unit of either side can reach any enemy (reach table
plus layers, R-164-01), meeting or holder alike. Fast, fake engine.

BUILDER CONTRACT: scenes.preflight(setup, engine) returns the EXISTING word "no_reach" for such a scene (the word, its place in the order
no_fit, unroutable, no_reach, blind_post and sweep's handling of it are unchanged; what grows is the condition, which today looks only at
attackers against a holder). A scene where reach runs one way is NOT refused: it starts decided (decided_one_way_reach, see
test_rev3_c_stall.py), not stalled. Today's holder rule (attackers cannot reach the holder's layer) stays as it is.
Red today: a meeting (no group on guard) is never refused; the controls are green."""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
for _p in (ROOT, Path(__file__).resolve().parent):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from test_rev3_c_support import G, TYPES, ReachLayerFake  # noqa: E402
from scripts.skilllab import scenes  # noqa: E402
from scripts.skilllab.contract import Setup  # noqa: E402


def word(groups):
    return scenes.preflight(Setup(groups=tuple(groups), unit_types=dict(TYPES), max_ticks=50), ReachLayerFake())


def test_a_meeting_where_nobody_can_reach_anybody_is_refused_no_reach():
    """R7: Vanguards on layer 0 against Vanguards on layer 2, both attack-moving (no holder). Red today: 'ok'."""
    assert word([G(0, "Vanguard", 4, 0), G(1, "Vanguard", 4, 2)]) == "no_reach"


def test_a_meeting_with_reach_capable_types_but_no_target_layer_is_refused_no_reach():
    """Interceptors (up 2) on layer 0 and Raiders (1, 1) on layer 3: the offset of 3 is outside both reaches. Red today: 'ok'."""
    assert word([G(0, "Interceptor", 2, 0), G(1, "Raider", 2, 3)]) == "no_reach"


def test_control_a_holder_that_the_attackers_cannot_reach_is_still_refused():
    """Green today: the existing holder rule (a group on guard on layer 0, attackers with reach (0, 0) on layer 2)."""
    assert word([G(0, "Vanguard", 4, 0, order="guard"), G(1, "Vanguard", 4, 2)]) == "no_reach"


@pytest.mark.parametrize("groups", [
    [G(0, "Vanguard", 4, 0), G(1, "Vanguard", 4, 0)],                         # same layer: reach (0, 0) is enough
    [G(0, "Raider", 4, 1), G(1, "Raider", 4, 0)],                             # reach both ways
    [G(0, "Interceptor", 4, 0), G(1, "Vanguard", 4, 2)],                      # one way: starts DECIDED, not refused
], ids=["same-layer", "both-ways", "one-way-starts-decided"])
def test_control_a_scene_with_any_reach_is_not_refused(groups):
    """Positive controls (green today and after): the refusal is for 'nobody can reach anybody' only. One-way reach is the decided case."""
    assert word(groups) == "ok"
