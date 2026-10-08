"""Story play S-136 (E-18, R-136-01/03): "A dying ship flares, burns, drifts, and darkens." Moment: the first frame with a
wreck after an attack-move. Red on main: no wrecks inventory."""
import time

from play_support import count, has_key, moment, qa, step_until

MAX_TICKS = 4000
WRECK_CAP = 150


def test_s_136_a_wreck_is_on_the_field(tactical_game):
    client = tactical_game.client
    assert has_key(qa(client), "wrecks"), "S-136: no wrecks in the inventory"
    client.call("input", "drag", 0, 0, 1900, 140)
    client.call("input", "key", "A")
    client.call("input", "click", 960, 900, 1)
    time.sleep(0.3)
    seen = step_until(client, lambda q: count(q, "wrecks") > 0, MAX_TICKS)
    state = moment(client, "S-136", "first_wreck")
    assert seen, "S-136: no wreck appeared in %d ticks of attack-move" % MAX_TICKS
    assert count(state, "wrecks") <= WRECK_CAP, "S-136: R-136-03 more than %d wrecks" % WRECK_CAP
