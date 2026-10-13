"""Story plays S-095, S-097, S-098, S-099 (E-13, movement and formation, via E-13/E-13.png): after a group move the selected
units advance together and settle. Moment: before and 60 ticks after a real right-click move order; selected units' mean
position moved toward the target. Red on main: the control passes; the inventory squads key does not exist."""
import time

from play_support import has_key, moment, qa, select_own_by_drag


def _mean(units, ids):
    xs = [(units[i]["x"], units[i]["y"]) for i in ids if i in units]
    return (sum(x for x, _ in xs) / len(xs), sum(y for _, y in xs) / len(xs))


def test_s_095_group_moves_together(tactical_game):
    client = tactical_game.client
    select_own_by_drag(client)
    time.sleep(0.5)
    before = moment(client, "S-095", "before_move")
    ids = [str(i) for i in before["selected"]]
    assert ids, "S-095 CONTROL: nothing selected"
    m0 = _mean(before["units"], ids)
    client.call("input", "click", 960, 540, 2)
    client.call("step", 60)
    after = moment(client, "S-095", "after_move")
    m1 = _mean(after["units"], ids)
    assert (m1[0] - m0[0]) ** 2 + (m1[1] - m0[1]) ** 2 > 1.0, "S-095 CONTROL: the group did not move after 60 ticks"
    assert has_key(after, "squads"), "S-097: the inventory lacks squads (models drawn per unit, moving as one)"
