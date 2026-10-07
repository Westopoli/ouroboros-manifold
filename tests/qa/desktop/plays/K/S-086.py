"""Story play S-086 / S-135 (E-11, E-18): "Each unit has exactly one ability" / "Every ability reads at a
glance as an ability in progress." Moment: the player presses the ability key for a selected Raider; the
next frame's qa_state `abilities_fx` has one entry (an ability in progress) and `hud.strip` is present. Needs
K-a (`acd`, ability events) then lane A. Red on main: no `abilities_fx` key. Screenshot and qa_state go to
docs/northstar/story_reviews/shots/<run id>/."""
import pytest
from _k_common import moment, start_game, step_ticks, to_tactical

STORY = "S-086"


@pytest.fixture(scope="module")
def game():
    g = start_game()
    yield g
    g.stop()


def test_s_086_ability_in_progress_is_visible(game):
    c = game.client
    qa = to_tactical(c)
    raiders = [uid for uid, u in qa.get("units", {}).items() if int(u.get("faction", -1)) == 0 and int(u.get("type", -1)) == 0]
    assert raiders, "control: no own Raider among qa units"
    c.call("qa_select", [int(raiders[0])])
    c.call("input", "key", "W")              # ability slot 1 (legacy inventory item 42: W/S/D/C/E)
    qa = step_ticks(c, 5)
    shot_qa = moment(c, STORY, "ability_in_progress")
    assert "abilities_fx" in shot_qa, "S-086/S-135: qa_state has no `abilities_fx` (keys: %s)" % sorted(shot_qa)
    assert len(shot_qa["abilities_fx"]) >= 1, "S-135: pressing the ability key left no ability effect in progress"
