"""Story play S-136 (E-18, R-136-01/03): "A dying ship flares, burns, drifts, and darkens." Moment: the first frame with a
wreck after an attack-move. Red on main: no wrecks inventory."""
import time

import pytest

from play_support import count, follow_army_on, has_key, moment, nearest_enemy_px, qa, select_own_by_drag, start_tactical_game, step_until


@pytest.fixture(scope="module")
def tactical_game():
    """TD-VG-A-5: this play reads enemy positions (nearest_enemy_px), so it runs with the fog filter off."""
    g = start_tactical_game(fog_off=True)
    try:
        yield g
    finally:
        g.stop()


MAX_TICKS = 6730  # TD-VG-A-1: first wreck measured at tick 5382 after the order (seed 1, attack-move to the nearest enemy) + 25%
CHUNK = 25  # TD-VG-A-1: 6730 ticks at chunk 5 does not fit the 900 s play timeout (about 0.15 s per tick against 0.07 at chunk 25)
WRECK_CAP = 150


def test_s_136_a_wreck_is_on_the_field(tactical_game):
    client = tactical_game.client
    assert has_key(qa(client), "wrecks"), "S-136: no wrecks in the inventory"
    select_own_by_drag(client)
    client.call("input", "key", "A")
    ex, ey = nearest_enemy_px(client, qa(client))
    client.call("input", "click", ex, ey, 1)
    time.sleep(0.3)
    follow_army_on()  # TD-VG-A-9j
    seen = step_until(client, lambda q: count(q, "wrecks") > 0, MAX_TICKS, chunk=CHUNK)
    state = moment(client, "S-136", "first_wreck")
    assert seen, "S-136: no wreck appeared in %d ticks of attack-move" % MAX_TICKS
    assert count(state, "wrecks") <= WRECK_CAP, "S-136: R-136-03 more than %d wrecks" % WRECK_CAP
