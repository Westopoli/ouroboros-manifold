"""Story play S-241 "Teams, sub-commanders and sub-civilizations": the team-size choice in the lobby (no E2 part).
Rules R-141-01 ("it is played by teams of 2 or 4 (S-241)") and R-241-01 ("a team has 2 or 4 players"); R-241-04 keeps
the confirmed peer count at 4. The lobby offers a TeamSize choice whose options are exactly 2 and 4; qa_state lists
them under `team_sizes`. Names fixed by this play: control TeamSize, keys team_sizes and team_size.
Green on the built tree (VG-F-S241, spec Rev 13: docs/northstar/plans/2026-10-07-visible-game-spec.md, F-S241
paragraph and gaps g4 and g5, Architect rulings of 2026-10-14). The landing closes ledger row FU-F-s241-teamsize (the
play leaves scripts/specfactory/lane_plays_known_red.txt then, the clerk removes the line). The choice is a STUB until
R-241-03 scales the match with it (ledger row FU-F-teamsize-scaling stays open).
The `sorted(lobby.get("team_sizes", [])) == [2, 4]` assertion and the TeamSize lookup of the first test are NOT edited
(they are the play's original lines 28 and 29); everything else below adds to them.

Q-F-1 (Westley, 2026-10-11, closed): the plays emulate real players. The lobby of one game on the Steam-less local test
network (--net-local) is enough to see the choice; the real-input step is the host making the choice with a mouse click
on the control, as a player does (Host pressed first: only the host can change it, gap 5).
Inventory from the running scene (Visible-game guard 1): TeamSize on screen inside 1920x1080 showing "2" (the default),
a "Team size" label, team_sizes == [2, 4] in that order, team_size == 2, max_members == 4 (gap 4 (a): the choice does not
change the member cap), and HostButton, JoinButton, StartButton and MemberList still present (Start gating unchanged).
"""
import json
import time

import pytest

import _play as P

VIEWPORT = (1920, 1080)


def inside(control: dict, size: tuple[int, int]) -> bool:
    x, y, w, h = control["rect_px"]
    return x >= 0 and y >= 0 and x + w <= size[0] and y + h <= size[1]


@pytest.fixture(scope="module")
def game():
    # A drawn lobby port, so the Host step of the second test does not take the fixed default 47000 (DRAFT-lobby-port).
    port = P.draw_ports()[2]
    g = P.start_game(extra_args=["--net-local", "--net-local-lobby-port", str(port)])
    g.lobby_port = port
    try:
        yield g
    finally:
        g.stop()


def test_s241_lobby_offers_teams_of_2_and_4(game):
    c = game.client
    res = P.go_to_lobby(c)
    # CONTROL (green on any tree with a lobby): the lobby scene is reached under --net-local, its qa_state has a
    # members list and the Host button exists. A red after this line means the feature is missing, not the harness.
    assert P.lobby_qa(res).get("scene") == "lobby" and "members" in P.lobby_qa(res), "CONTROL: lobby qa %r" % res
    assert P.find_control(c.tree(), "HostButton") is not None, "CONTROL: no HostButton among %r" % P.control_names(c.tree())
    P.note("S-241 lobby qa before Host:", json.dumps(P.lobby_qa(res), sort_keys=True))
    P.note("S-241 lobby controls:", sorted(P.control_names(c.tree())))
    qa = P.record(c, "S-241", "team_size")
    lobby = qa.get("qa", qa)
    assert sorted(lobby.get("team_sizes", [])) == [2, 4], lobby.get("team_sizes")
    assert P.find_control(c.tree(), "TeamSize") is not None
    # Stricter, from the running scene (S-241, R-141-01, R-241-01, gaps 4 and 5).
    assert lobby["team_sizes"] == [2, 4], "S-241 gap 5: team_sizes must be [2, 4] in that order: %r" % lobby["team_sizes"]
    assert lobby.get("team_size") == 2, "S-241 gap 5: the default team_size is 2: %r" % lobby.get("team_size")
    assert lobby.get("max_members") == 4, "S-241 gap 4 (a): max_members stays 4: %r" % lobby.get("max_members")
    ctl = P.find_control(c.tree(), "TeamSize")
    assert inside(ctl, VIEWPORT), "S-241: TeamSize is not inside 1920x1080: %r" % ctl["rect_px"]
    assert str(ctl["text"]) == "2", "S-241 gap 5: TeamSize shows the selected numeral, got %r" % ctl["text"]
    assert P.control_with_text(c, "team size") is not None, "S-241 gap 5: no 'Team size' label among %r" % P.control_names(c.tree())
    for name in ("HostButton", "JoinButton", "StartButton", "MemberList"):
        assert P.find_control(c.tree(), name) is not None, "S-241: control %s vanished from the lobby" % name


def _choose(client, want: int) -> int:
    """A player opens the TeamSize drop-down with a click and clicks the item. The open popup is a separate window the
    tree does not list and a frame does not draw (S-110.py:16), so the item is found as a player would: the popup opens
    under the button, one row per item, a row about as tall as the button; try the row centre and a few pixels either
    side (never past the two-row popup, so no control below it is hit) until the lobby shows the wanted size (every attempt reopens the drop-down; a click that misses closes it)."""
    ctl = P.find_control(client.tree(), "TeamSize")
    assert ctl is not None, "S-241: no TeamSize control among %r" % P.control_names(client.tree())
    x, y, w, h = ctl["rect_px"]
    row = [2, 4].index(want)
    tried = []
    for d in (0, -6, 6, -12):  # measured on the Settings drop-down: rows are about 25 px, the popup starts ~8 px below
        dy = 3 + (row + 0.5) * h + d
        client.click(x + w / 2.0, y + h / 2.0)
        time.sleep(0.4)
        client.click(x + w / 2.0, y + h + dy)
        time.sleep(0.4)
        size = P.lobby_qa(client.state()["result"]).get("team_size")
        tried.append((round(dy, 1), size))
        if size == want:
            return size
    raise AssertionError("S-241 gap 5: clicking the TeamSize item for %d never changed team_size (offsets below the "
                         "button -> team_size: %r)" % (want, tried))


def test_s241_host_changes_team_size_with_a_click(game):
    c = game.client
    q0 = P.lobby_qa(c.state()["result"])
    assert q0.get("scene") == "lobby", "CONTROL: expected the lobby from the first test: %r" % q0
    # Only the host changes the choice (gap 5): press Host like a player, on the drawn lobby port.
    P.click_named(c, "HostButton", "lobby")
    P.wait_until(lambda: P.field_text(c, "LobbyIdField") == str(game.lobby_port), P.STEP_S,
                 "S-241: host LobbyIdField shows the lobby id",
                 why=lambda: "LobbyIdField=%r, StatusLine=%r" % (P.field_text(c, "LobbyIdField"), P.field_text(c, "StatusLine")))
    P.note("S-241 lobby qa after Host:", json.dumps(P.lobby_qa(c.state()["result"]), sort_keys=True))
    assert P.lobby_qa(c.state()["result"]).get("team_size") == 2, "S-241 gap 5: default team_size is 2"
    _choose(c, 4)
    q = P.lobby_qa(c.state()["result"])
    assert q["team_size"] == 4 and q["max_members"] == 4, \
        "S-241 gap 4 (a) / gap 5: after the click team_size must be 4 and max_members stay 4: %r" % q
    assert q["team_sizes"] == [2, 4], "S-241 gap 5: the offered sizes do not change: %r" % q["team_sizes"]
    assert str(P.find_control(c.tree(), "TeamSize")["text"]) == "4", "S-241: TeamSize does not show the chosen 4"
    assert P.find_control(c.tree(), "StartButton") is not None, "S-241: Start vanished (gating is unchanged)"
    _choose(c, 2)
    q = P.lobby_qa(c.state()["result"])
    assert q["team_size"] == 2 and q["max_members"] == 4, "S-241 gap 5: clicking back must restore 2: %r" % q
