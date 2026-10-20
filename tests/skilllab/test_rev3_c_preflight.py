# spec: docs/northstar/plans/2026-10-19-skill-lab-rev3-plan.md (requirement R7 "pre-flight refuses a scene that starts that way", test T9, defect D7); ledger FINDING-lab-d7; piece LAB-REV3-C
# Rule pins: R-164-01@511d57
"""LAB-REV3-C, R7's second half: scenes.preflight refuses a scene in which no living unit of either side can reach any enemy (reach table
plus layers, R-164-01), meeting or holder alike. Fast, fake engine.

BUILDER CONTRACT: scenes.preflight(setup, engine) returns the EXISTING word "no_reach" for such a scene (the word, its place in the order
no_fit, unroutable, no_reach, blind_post and sweep's handling of it are unchanged; what grows is the condition, which today looks only at
attackers against a holder). A scene where reach runs one way is NOT refused: it starts decided (decided_one_way_reach, see
test_rev3_c_stall.py), not stalled. Today's holder rule (attackers cannot reach the holder's layer) stays as it is.
HOLDER x ONE-WAY (audit gap F3, measured on the base 2026-10-20): the holder rule reads the ATTACKERS' reach only, so an Interceptor on guard on
layer 0 against attack-moving Vanguards on layer 2 (reach runs one way: the Interceptor reaches up 2, the Vanguards reach nothing) is refused
"no_reach" TODAY, by the holder rule's own condition. The brief for this follow-up asked for a test that this scene is not "no_reach"; that
contradicts the base and the sentence above ('the holder rule stays as it is'), so the test below pins the current word and the report flags
it. A holder scene whose attackers DO reach the holder's layer (a Vanguard on guard on layer 2 against Interceptors on layer 0) is "ok" and
must stay "ok": the new rule (nobody reaches anybody) must not refuse a one-way scene because of a holder.
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
from scripts.skilllab.contract import Group, Setup  # noqa: E402


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


def test_control_a_holder_the_attackers_cannot_reach_is_refused_by_the_holder_rule_even_when_the_holder_reaches_them():
    """Green today (characterisation, F3; see the module docstring): an Interceptor on guard on layer 0 against Vanguards on layer 2 is one-way
    reach (the Interceptor reaches up 2), yet today's holder rule, which reads the attackers' reach only, refuses it. It stays as it is: the
    word is the existing "no_reach". The same scene as a meeting (no guard) is "ok" (the decided case)."""
    assert word([G(0, "Interceptor", 4, 0, order="guard"), G(1, "Vanguard", 4, 2)]) == "no_reach"
    assert word([G(1, "Interceptor", 4, 0, order="guard"), G(0, "Vanguard", 4, 2)]) == "no_reach"
    assert word([G(0, "Interceptor", 4, 0), G(1, "Vanguard", 4, 2)]) == "ok"


def test_control_a_one_way_scene_whose_attackers_reach_the_holder_is_not_refused():
    """Green today and after (F3): a Vanguard on guard on layer 2, Interceptors attack-moving from layer 0 (up 2 reaches layer 2; the Vanguard
    reaches nothing above or below its own layer): reach runs one way, the holder rule passes, and the new rule must not refuse it."""
    assert word([G(0, "Vanguard", 4, 2, order="guard"), G(1, "Interceptor", 4, 0)]) == "ok"
    assert word([G(1, "Vanguard", 4, 2, order="guard"), G(0, "Interceptor", 4, 0)]) == "ok"


def test_control_no_fit_and_unroutable_are_reported_before_no_reach():
    """Green today and after (decisions 7 and 44, the order no_fit, unroutable, no_reach): a scene that is also mutual no-reach keeps the earlier
    word. no_fit: a Vanguard placed inside a block on its own layer; unroutable: a flyer whose goal lies behind a wall on its layer (the real library answers the movement-kind read)."""
    from scripts.skilllab.contract import Block, Terrain
    from scripts.skilllab.engine import Engine
    canvas = (4000.0, 1000.0)
    inside = Terrain(canvas=canvas, blocks=(Block(x0=200.0, y0=0.0, x1=400.0, y1=1000.0, layer_lo=0, layer_hi=0),))
    a = Group(side=0, unit="Vanguard", count=1, formation="points", x=300.0, y=500.0, facing_deg=0.0, layer=0, order="attack_move",
              goal=None, params={"points": [(300.0, 500.0)]})
    b = Group(side=1, unit="Vanguard", count=1, formation="points", x=3000.0, y=500.0, facing_deg=180.0, layer=2, order="attack_move",
              goal=None, params={"points": [(3000.0, 500.0)]})
    assert scenes.preflight(Setup(groups=(a, b), unit_types=dict(TYPES), terrain=inside, max_ticks=50), None) == "no_fit"
    wall = Terrain(canvas=canvas, blocks=(Block(x0=1800.0, y0=0.0, x1=2000.0, y1=1000.0, layer_lo=0, layer_hi=0),))
    a2 = Group(side=0, unit="Vanguard", count=1, formation="points", x=500.0, y=500.0, facing_deg=0.0, layer=0, order="move",
               goal=(3500.0, 500.0), params={"points": [(500.0, 500.0)]})
    assert scenes.preflight(Setup(groups=(a2, b), unit_types=dict(TYPES), terrain=wall, max_ticks=50), Engine()) == "unroutable"


@pytest.mark.parametrize("groups", [
    [G(0, "Vanguard", 4, 0), G(1, "Vanguard", 4, 0)],                         # same layer: reach (0, 0) is enough
    [G(0, "Raider", 4, 1), G(1, "Raider", 4, 0)],                             # reach both ways
    [G(0, "Interceptor", 4, 0), G(1, "Vanguard", 4, 2)],                      # one way: starts DECIDED, not refused
], ids=["same-layer", "both-ways", "one-way-starts-decided"])
def test_control_a_scene_with_any_reach_is_not_refused(groups):
    """Positive controls (green today and after): the refusal is for 'nobody can reach anybody' only. One-way reach is the decided case."""
    assert word(groups) == "ok"
