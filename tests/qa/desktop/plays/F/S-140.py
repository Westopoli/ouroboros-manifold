"""Story play S-140 "Commands over the wire": an order given in a match goes through the session and the unit moves.
In the solo loopback match (see S-142.py, Q-F-1) the player box-selects own units, right-clicks a point, and the
selected units' positions change while qa_state net.state stays running. Rules R-140-02 (orders are applied at tick+3,
so allow a short wait), R-140-03. Uses units_px (own units) from the tactical qa_state to aim the drag, as the galaxy
and tactical plays do.
Red on main: no lobby.
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


def test_s140_move_order_in_a_match_moves_the_units(game):
    c = game.client
    P.start_solo_match(c)
    qa = c.state()["result"]["qa"]
    own = [uid for uid, u in qa["units"].items() if u["faction"] == qa["local_faction"]]
    assert own, "no own units in the match frame"
    px = qa["units_px"]
    xs = [px[u][0] for u in own if u in px]
    ys = [px[u][1] for u in own if u in px]
    assert xs, "no own unit is on screen"
    c.call("input", "drag", min(xs) - 20, min(ys) - 20, max(xs) + 20, max(ys) + 20, 8)
    start = {u: (qa["units"][u]["x"], qa["units"][u]["y"]) for u in own}
    c.call("input", "click", 960, 540, 2)
    time.sleep(3.0)
    after = P.record(c, "S-140", "after_move_order")["qa"]
    moved = [u for u in own if u in after["units"] and (after["units"][u]["x"], after["units"][u]["y"]) != start[u]]
    assert moved, "no selected unit moved after a move order in a match"
    assert after.get("net", {}).get("state") == "running"
