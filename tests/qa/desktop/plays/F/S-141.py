"""Story play S-141 "What a match is": the lobby moment. Rules R-141-01 (friends-only; teams of 2 or 4).
Spec: visible-game spec lane F; Steam spec W4. A player picks MULTIPLAYER on the main menu and sees a lobby of at
most 4, friends only, with themselves listed. qa_state keys fixed by tests/test_vg_f_w4_lobby.gd (lobby.qa_state).
Red on main: the main menu has no MULTIPLAYER row.
"""
import pytest

import _play as P


@pytest.fixture(scope="module")
def game():
    g = P.start_game()
    try:
        yield g
    finally:
        g.stop()


def test_s141_lobby_after_multiplayer(game):
    c = game.client
    P.go_to_lobby(c)
    qa = P.record(c, "S-141", "lobby")
    lobby = qa.get("qa", qa)
    assert lobby.get("scene") == "lobby"
    assert lobby.get("max_members") == 4 and lobby.get("friends_only") is True, lobby
    assert len(lobby.get("members", [])) >= 1, "the lobby does not list the local player"
    assert P.find_control(c.tree(), "MemberList") is not None, "no MemberList control on screen"
