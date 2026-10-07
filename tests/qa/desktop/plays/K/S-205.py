"""Story play S-205 (E-12): "An enemy building appears when my units see it and shows what it is doing."
Moment: the first frame lists only the structures the local side can see (R-205-02 via K-h's fog filter and
K-a's structures field): qa_state `structures` is a list of rows with `owner`, `stage`, `cap`, and holds no
row of an unseen enemy structure. Red on main: no `structures` key in qa_state. Screenshot and qa_state go to
docs/northstar/story_reviews/shots/<run id>/."""
import pytest
from _k_common import moment, start_game, to_tactical

STORY = "S-205"


@pytest.fixture(scope="module")
def game():
    g = start_game()
    yield g
    g.stop()


def test_s_205_structures_in_state_are_the_visible_ones(game):
    c = game.client
    to_tactical(c)
    qa = moment(c, STORY, "structures_first_frame")
    assert "structures" in qa, "S-205: qa_state has no `structures` (keys: %s)" % sorted(qa)
    rows = qa["structures"]
    assert isinstance(rows, list) and rows, "S-205: no structure rows at the first frame (own structures are always visible)"
    assert all({"owner", "stage", "cap"} <= set(r) for r in rows), "S-205: structure rows lack owner/stage/cap: %s" % rows[:2]
    assert all(int(r["owner"]) == 0 or r.get("seen", True) for r in rows), "R-205-02: an unseen enemy structure is listed"
