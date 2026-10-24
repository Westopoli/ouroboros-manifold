# Rule pins: R-104-01@1aaaa3, R-104-03@9dae08
"""Story play S-104 (E-16, R-104-01/03/09): "A lean HUD that shows what I need and stays out of the way."
Moment: the first tactical frame after Deploy. The HUD inventory exists: clock, objectives, selection, events, strip,
comb, reinforcements; the clock reads mm:ss; the objectives list is not empty. Red on main: none of the inventory keys exist."""
import re

from play_support import count, has_key, inv, moment, qa

KEYS = ["hud.clock", "hud.objectives", "hud.selection", "hud.events", "hud.strip", "hud.comb", "hud.reinforcements"]


def test_s_104_hud_elements_exist(tactical_game):
    client = tactical_game.client
    state = moment(client, "S-104", "first_frame")
    missing = [k for k in KEYS if not has_key(state, k)]
    assert not missing, "S-104: qa_state inventory lacks %r (section 2 inventory keys)" % missing
    assert count(state, "hud.objectives") >= 1, "S-104: R-104-01 the objective list is empty"
    texts = [c.get("text", "") for c in client.tree().get("result", {}).get("controls", [])]
    assert any(re.fullmatch(r"\d\d:\d\d", t.strip()) for t in texts), "S-104: R-104-03 no mm:ss clock text among %r" % texts[:12]
