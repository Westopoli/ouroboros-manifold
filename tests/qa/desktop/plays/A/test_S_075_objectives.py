"""Story play S-075 (E-10): "One primary objective I can see progressing, up to three secondary ones."
Moment: opening frame and after 200 ticks. The panel has one primary row and at most three more; beacons mark them in the
world. Red on main: no hud.objectives or objective_markers inventory."""
from play_support import count, has_key, moment


def test_s_075_objective_panel_and_beacons(tactical_game):
    client = tactical_game.client
    state = moment(client, "S-075", "objectives_open")
    assert has_key(state, "hud.objectives") and has_key(state, "objective_markers"), "S-075: inventory lacks hud.objectives / objective_markers"
    rows = count(state, "hud.objectives")
    assert 1 <= rows <= 4, "S-075: the panel shows %d objective rows, expected one primary and up to three secondary" % rows
    assert count(state, "objective_markers") >= 1, "S-075: the world shows no objective beacon"
    client.call("step", 200)
    moment(client, "S-075", "objectives_after_200_ticks")
