"""Story play S-142 "No pause, no rewind": R-142-01 in a live match. Pressing the pause key does not pause: the tick
keeps advancing and qa_state says so. The match is a one-player loopback match started from the lobby (Start with only
the host present; question Q-F-1 for the Architect: the spec has no solo-host start, this play fixes it as the way a
single QA instance reaches a match). qa_state of the tactical scene gains `net` {active: bool, state: str} (fixed here).
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


def test_s142_pause_key_does_not_pause_a_match(game):
    c = game.client
    P.start_solo_match(c)
    before = c.state()["result"]["qa"]
    assert before.get("net", {}).get("active") is True, before.get("net")
    c.call("input", "key", "Escape")
    c.call("input", "key", "P")
    time.sleep(1.5)
    after = P.record(c, "S-142", "after_pause_key")["qa"]
    assert int(after["tick"]) > int(before["tick"]), "the tick stopped after the pause key (R-142-01)"
    assert after.get("net", {}).get("state") == "running"
