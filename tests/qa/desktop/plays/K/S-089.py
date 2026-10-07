"""Story play S-089 (E-12): "The map is revealed only around my units." Moment: first frame of the first
mission. R-089-03 (K-h, fog filter on in the live path once lane A's A4 has landed): qa_state publishes
`fog_layer` and `units_px` lists only own-faction units (an unseen enemy's position is not in the client's
data). Red on main: no `fog_layer` key, and the first frame holds both factions. The screenshot and qa_state go
to docs/northstar/story_reviews/shots/<run id>/."""
import pytest
from _k_common import moment, start_game, to_tactical

STORY = "S-089"


@pytest.fixture(scope="module")
def game():
    g = start_game()
    yield g
    g.stop()


def test_s_089_only_own_units_and_a_fog_layer_at_first_frame(game):
    c = game.client
    to_tactical(c)
    qa = moment(c, STORY, "first_frame_fog")
    assert "fog_layer" in qa, "S-089: qa_state has no `fog_layer` (keys: %s)" % sorted(qa)
    factions = {int(u.get("faction", -1)) for u in qa.get("units", {}).values()}
    assert len(factions) == 1, "R-089-03: first-frame qa units hold factions %s; unseen enemies must be absent" % sorted(factions)
    assert qa["fog_layer"], "S-089: `fog_layer` is empty/false at the first frame"
