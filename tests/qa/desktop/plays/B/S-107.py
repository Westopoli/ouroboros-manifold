"""Story play S-107 "Reading the galaxy": the player clicks a system; the camera centres on it and zooms to Local
(R-107-01). Aims the click with qa_state systems_px, picking the owned system nearest the screen centre.
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


def test_s107_clicking_a_system_focuses_it(game):
    c = game.client
    P.new_game(c)
    before = c.state()["result"]["qa"]
    px = before["systems_px"]
    owned = [k for k, v in before["owners"].items() if int(v) >= 0 and k in px]
    assert owned, "no owned system on screen"
    k = min(owned, key=lambda k: (px[k][0] - 960) ** 2 + (px[k][1] - 540) ** 2)
    c.click(px[k][0], px[k][1])
    time.sleep(4.0)
    after = P.record(c, "S-107")["qa"]
    assert after["distance"] < before["distance"], (before["distance"], after["distance"])
