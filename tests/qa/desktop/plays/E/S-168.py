"""Story play S-168 (E-22) / S-193 (E-17): "Place a building anywhere on walkable ground; it claims its footprint and the
pieces around it refill." Moment: the player is in a mission; qa_state carries `settlement_lots` (the E1k layer's lots, a
list). The placement UI (E1o) is not click-reachable yet, so the play pins only the observable key. Red on main: no
`settlement_lots` key. Screenshot and qa_state go to docs/northstar/story_reviews/shots/<run id>/."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "K"))
from _k_common import moment, start_game, to_tactical  # noqa: E402

STORY = "S-168"


@pytest.fixture(scope="module")
def game():
    g = start_game()
    yield g
    g.stop()


def test_s_168_settlement_lots_are_published(game):
    qa = to_tactical(game.client)
    assert qa.get("units"), "control: tactical qa_state has no units"
    shot_qa = moment(game.client, STORY, "settlement")
    assert "settlement_lots" in shot_qa, "S-168/S-193: qa_state has no `settlement_lots` (keys: %s)" % sorted(shot_qa)
    assert isinstance(shot_qa["settlement_lots"], list)
