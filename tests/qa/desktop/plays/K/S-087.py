# Rule pins: R-104-01@1aaaa3
"""Story play S-087 (E-11): "Every unit on both sides flinches, obeys, then shoots the nearest thing in
range." Moment: a few hundred ticks into the first mission, shots are in the air. Needs K-a's fire events
and lane A's shot effects: qa_state `shots_in_flight` (spec section 2 inventory) counts shots in flight and
`hud.events` exists. Red on main: the tactical view publishes neither key. Writes the screenshot and
qa_state to docs/northstar/story_reviews/shots/<run id>/."""
import pytest
from _k_common import moment, start_game, step_ticks, to_tactical

STORY = "S-087"


@pytest.fixture(scope="module")
def game():
    g = start_game()
    yield g
    g.stop()


def test_s_087_shots_fly_once_the_forces_meet(game):
    c = game.client
    to_tactical(c)
    qa = {}
    for _ in range(30):                      # up to 30 x 100 ticks; seed 1 meets well before this
        qa = step_ticks(c, 100)
        if int(qa.get("shots_in_flight", 0)) > 0:
            break
    shot_qa = moment(c, STORY, "shots_in_flight")
    assert "shots_in_flight" in shot_qa, "S-087: qa_state has no `shots_in_flight` (keys: %s)" % sorted(shot_qa)
    assert int(shot_qa["shots_in_flight"]) > 0, "S-087: no shot in flight in 3000 ticks"
    assert "hud" in shot_qa and "events" in shot_qa["hud"], "S-087 (R-104-01): no hud.events in qa_state"
