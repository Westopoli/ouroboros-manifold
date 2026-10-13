"""Story play S-108 "One unbroken shot" (docs/bible/stories.md S-108; E-16 R-108-01, R-108-02, R-108-05).

From the galaxy the player starts a mission and ends it (the verbs of tests/qa/desktop/test_flow_spine.py: NewGame,
step 10, Mission, Deploy, EndMission, Continue), then the camera pulls back into the galaxy and the chronicle scroll
panel slides in from the right with the galaxy at 62 percent width. Captures that moment (the scroll beside the galaxy)
as S-108 plus S-108-galaxy (the galaxy before the mission, for the half-width comparison). The reviewer judges the
pull-back and the 62 percent width from the shots; the play asserts only that the chronicle scene or panel was reached
and has at least one entry.
"""
import time

import pytest

import _play as P
from daemon_client import control_names, wait_for

DEBRIEF = "res://scenes/debrief/debrief.tscn"
BRIEFING = "res://scenes/mission_briefing/mission_briefing.tscn"
CHRONICLE = "res://scenes/world/chronicle_scroll_panel.tscn"
STEP_S = 10.0


@pytest.fixture(scope="module")
def game():
    g = P.start_game()
    try:
        yield g
    finally:
        g.stop()


def _on_chronicle(c, state: dict) -> bool:
    if state.get("scene") == CHRONICLE:
        return True
    return any("ChronicleScrollPanel" in n for n in control_names(c.tree()))


def test_s108_mission_ends_and_the_scroll_slides_in_beside_the_galaxy(game):
    c = game.client
    P.new_game(c)
    c.call("step", 10)
    wait_for(c, lambda s: int(s.get("qa", {}).get("tick", 0)) >= 10, STEP_S, label="galaxy tick 10")
    P.record(c, "S-108-galaxy")

    P.click_named(c, "Mission", "galaxy")
    wait_for(c, lambda s: s.get("scene") == BRIEFING, STEP_S, label="briefing")
    P.click_named(c, "Deploy", "briefing")
    wait_for(c, lambda s: s.get("scene") == P.TACTICAL, STEP_S, label="tactical")
    time.sleep(1.0)
    P.click_named(c, "EndMission", "tactical")
    wait_for(c, lambda s: s.get("scene") == DEBRIEF, STEP_S, label="debrief")
    P.click_named(c, "Continue", "debrief")
    wait_for(c, lambda s: _on_chronicle(c, s), STEP_S, label="chronicle")
    time.sleep(2.0)  # slide-in 0.40 s (R-108-02) plus the first entries printing
    res = P.record(c, "S-108")
    entries = res.get("qa", {}).get("entries", [])
    assert len(entries) >= 1, "no chronicle entry on screen; qa keys %r" % sorted(res.get("qa", {}).keys())
