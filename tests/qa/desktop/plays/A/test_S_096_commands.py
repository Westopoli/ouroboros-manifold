"""Story play S-096 (E-13): "Move is movement, attack-move fights along the way, attack-target commits, ability is a button."
Moment: a real right-click move order is acknowledged and the order feedback and ability slot are on screen.
Red on main: no hud.selection / abilities_fx inventory (the order itself already works)."""
import time

from play_support import count, has_key, moment, qa, select_own_by_drag


def test_s_096_move_order_and_ability_button(tactical_game):
    client = tactical_game.client
    select_own_by_drag(client)
    time.sleep(0.5)
    client.call("input", "click", 960, 540, 2)
    time.sleep(1.0)
    state = moment(client, "S-096", "move_ordered")
    last = state.get("last_command", {})
    assert last.get("ok") is True and last.get("kind") == "move", "S-096 CONTROL: the move order was not acknowledged: %r" % last
    assert has_key(state, "hud.selection") and has_key(state, "abilities_fx"), "S-096: inventory lacks hud.selection / abilities_fx"
    assert count(state, "hud.selection") > 0, "S-096: the selection panel (with the ability button) is empty while units are selected"
