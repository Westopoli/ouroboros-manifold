"""Story play S-141 "What a match is": the lobby moment. Rules R-141-01 (friends-only; teams of 2 or 4).
Spec: visible-game spec lane F part 1 (VG-F-SKEL-B); Steam spec W4. Two real game processes on the Steam-less local test
network (--net-local): the host makes a lobby, the guest types its id and joins, and the host's lobby lists both
players, at most 4, friends only (shot "lobby"). Q-F-1 closed by Westley, 2026-10-11 (two real players joining, no
shortcut beyond what the missing Steam requires). qa_state keys fixed by tests/test_vg_f_w4_lobby.gd (lobby.qa_state).
Red until VG-F-SKEL-B wires --net-local into lobby.gd: the Host button stays disabled.
"""
import pytest

import _play as P


@pytest.fixture(scope="module")
def pair():
    yield from P.pair_games()


def test_s141_lobby_after_multiplayer(pair):
    host, guest = pair
    P.reach_pair_lobby(host, guest)
    qa = P.record(host.client, "S-141", "lobby")
    lobby = P.lobby_qa(qa)
    assert lobby.get("scene") == "lobby"
    assert lobby.get("max_members") == 4 and lobby.get("friends_only") is True, lobby
    assert len(lobby.get("members", [])) == 2, "the host's lobby does not list both players: %r" % lobby
    assert P.find_control(host.client.tree(), "MemberList") is not None, "no MemberList control on the host's screen"
    glob = P.lobby_qa(guest.client.state()["result"])
    assert len(glob.get("members", [])) == 2, "the guest's lobby does not list both players: %r" % glob
    assert P.find_control(guest.client.tree(), "MemberList") is not None, "no MemberList control on the guest's screen"
