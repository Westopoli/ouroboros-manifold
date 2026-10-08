"""Story play S-134 (E-18, R-134-05): "Shots travel, hits bloom, nothing twitches." Moment: the first frame in which a shot is
in flight after an attack-move toward the enemy. Red on main: no shots_in_flight inventory."""
import time

from play_support import count, has_key, moment, qa, step_until

MAX_TICKS = 3000


def test_s_134_a_shot_is_in_flight_during_combat(tactical_game):
    client = tactical_game.client
    assert has_key(qa(client), "shots_in_flight"), "S-134: no shots_in_flight in the inventory"
    client.call("input", "drag", 0, 0, 1900, 140)
    client.call("input", "key", "A")
    client.call("input", "click", 960, 900, 1)
    time.sleep(0.3)
    seen = step_until(client, lambda q: count(q, "shots_in_flight") > 0, MAX_TICKS)
    moment(client, "S-134", "shots_in_flight")
    assert seen, "S-134: no shot was drawn in %d ticks of attack-move" % MAX_TICKS
