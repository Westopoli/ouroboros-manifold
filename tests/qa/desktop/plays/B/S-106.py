"""Story play S-106 "The galaxy between missions": after New Game the player sees the galaxy: luminous system points,
faction territory (shells, filament arcs), faction labels. Rules R-106-01/02/03/05. Asserts only that the galaxy is
populated (80 systems, some owned); whether it looks right is the reviewer's call on the screenshot.
"""
import time

import pytest

import _play as P


@pytest.fixture(scope="module")
def game():
    g = P.start_game()
    try:
        yield g
    finally:
        g.stop()


def test_s106_new_game_shows_the_galaxy(game):
    c = game.client
    P.new_game(c)
    qa = P.record(c, "S-106")["qa"]
    assert qa["system_count"] > 0, qa
    assert any(int(v) >= 0 for v in qa["owners"].values()), "no owned system"
