"""Story play S-193 (E-17): "The settlement grows." Moment: a few hundred ticks into the first mission the base has
lots at rising stages. Needs E1c (lot stages) and E1p (view wiring); qa_state `settlement_lots` (TD-VG-E-13) is a list of
{id,x,y,stage,building,owner} read from the running scene. Red on main: no `settlement_lots` key. Screenshot and qa_state go to
docs/northstar/story_reviews/shots/<run id>/."""
import pytest
from _k_common import moment, start_game, step_ticks, to_tactical

STORY = "S-193"


@pytest.fixture(scope="module")
def game():
    g = start_game()
    yield g
    g.stop()


def test_s_193_lots_rise_in_stages(game):
    c = game.client
    to_tactical(c)
    qa = step_ticks(c, 600)
    shot = moment(c, STORY, "lots_rising")
    assert "settlement_lots" in shot, "S-193: qa_state has no `settlement_lots` (keys: %s)" % sorted(shot)
    lots = shot["settlement_lots"]
    assert lots, "S-193: no lots in the running scene"
    assert all(0 <= int(l["stage"]) <= 5 for l in lots)
    assert max(int(l["stage"]) for l in lots) >= 2, "S-193: nothing rose past the empty stage"
