"""Story play S-134 (E-18, R-134-05): "Shots travel, hits bloom, nothing twitches." Moment: the first frame in which a shot is
in flight after an attack-move toward the enemy. Red on main: no shots_in_flight inventory."""
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


MAX_TICKS = 3000  # TD-VG-A-11: the TD-VG-A-1 raise to 6730 was reverted (Westley 2026-10-11); old budget restored. A17 (TD-VG-A-12) fixed the scroll, so a miss here is the army march, not the helper: FINDING-contact-distance (first contact past this budget stays red, budget and march are Westley's), Q-A17-01 (spawn near the home base stays)
CHUNK = 25  # TD-VG-A-1 step chunk (kept, not part of the reverted budget raise); see TD-VG-A-11


def test_s_134_a_shot_is_in_flight_during_combat(tactical_game):
    client = tactical_game.client
    assert has_key(qa(client), "shots_in_flight"), "S-134: no shots_in_flight in the inventory"
    select_own_by_drag(client)
    client.call("input", "key", "A")
    ex, ey = nearest_enemy_px(client, qa(client))
    client.call("input", "click", ex, ey, 1)
    time.sleep(0.3)
    follow_army_on()  # TD-VG-A-9j
    seen = step_until(client, lambda q: count(q, "shots_in_flight") > 0, MAX_TICKS, chunk=CHUNK)
    moment(client, "S-134", "shots_in_flight")
    assert seen, "S-134: no shot was drawn in %d ticks of attack-move" % MAX_TICKS
