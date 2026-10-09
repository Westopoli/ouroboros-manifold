"""Story play S-105 (E-16, R-105-01/02/04): "Click, box-select, bind groups, and never an all-army button."
Moment: after a real box drag the selection panel shows the selection (type x count); after the group digit the group tab
shows. Control: no select-all control exists in the tree. Red on main: no hud.selection inventory."""
import time

from play_support import count, has_key, moment, qa, select_own_by_drag


def test_s_105_box_select_shows_in_the_selection_panel(tactical_game):
    client = tactical_game.client
    select_own_by_drag(client)
    time.sleep(0.5)
    state = moment(client, "S-105", "box_selected")
    assert len(state["selected"]) > 0, "S-105 CONTROL: the drag selected nothing (the old selection path)"
    assert has_key(state, "hud.selection"), "S-105: no hud.selection in the inventory"
    assert count(state, "hud.selection") > 0, "S-105: R-104-04 the selection panel is empty after a box select of %d units" % len(state["selected"])


def test_s_105_there_is_no_select_all_control(tactical_game):
    names = [c["path"].rsplit("/", 1)[-1] for c in tactical_game.client.tree().get("result", {}).get("controls", [])]
    assert not [n for n in names if "select_all" in n.lower() or "selectall" in n.lower()], "S-105: R-105-04 a select-all control exists"
