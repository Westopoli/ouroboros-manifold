"""Story play S-193 (E-17): "The settlement grows." Moment: a few hundred ticks into the first mission the base has
lots at rising stages. Needs E1c (lot stages) and E1p (view wiring); qa_state `settlement_lots` (TD-VG-E-13) is a list of
{id,x,y,stage,building,owner} read from the running scene. Red on main: no `settlement_lots` key. Screenshot and qa_state go to
docs/northstar/story_reviews/shots/<run id>/.
Ground era: lots exist only under Ground3D (spec line 192); the camera is edge-scrolled to lot 1 for the shot (TD-VG-E-14)."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "K"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "A"))
from _k_common import GodotGame, moment, pick_free_port, step_ticks, to_tactical  # noqa: E402
from play_support import _edge_scroll_to  # noqa: E402

STORY = "S-193"


@pytest.fixture(scope="module")
def game():
    g = GodotGame(qa_port=pick_free_port(), seed=1, resolution="1920x1080", extra_args=["--era", "greek_placeholder"], renderer="vulkan")
    g.start()
    g.wait_for_port(timeout=60.0)
    yield g
    g.stop()


def test_s_193_lots_rise_in_stages(game):
    c = game.client
    to_tactical(c)
    qa = step_ticks(c, 600)
    lots = qa.get("settlement_lots", [])
    assert lots, "S-193: no lots in the running scene"
    assert _edge_scroll_to(c, float(lots[0]["x"]), float(lots[0]["y"]), qa["camera"]), "S-193: the first lot never came on screen"
    shot = moment(c, STORY, "lots_rising")
    assert "settlement_lots" in shot, "S-193: qa_state has no `settlement_lots` (keys: %s)" % sorted(shot)
    lots = shot["settlement_lots"]
    assert lots, "S-193: no lots in the running scene"
    assert all(0 <= int(l["stage"]) <= 5 for l in lots)
    assert max(int(l["stage"]) for l in lots) >= 2, "S-193: nothing rose past the empty stage"
