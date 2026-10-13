"""Story play S-241 "Teams, sub-commanders and sub-civilizations": the team-size choice in the lobby (no E2 part).
Rule R-241-01..03 (teams of 2 or 4 at launch). The lobby offers a TeamSize choice whose options are exactly 2 and 4;
qa_state lists them under `team_sizes`. Names fixed here (flagged to the Architect): control TeamSize, key team_sizes.
Reaches the lobby of one game on the Steam-less local test network (--net-local; Q-F-1 closed by Westley,
2026-10-11); no second player is needed to see the team-size choice.
Stays red by design until the later lane F piece that adds the team_sizes key and the TeamSize control (ledger row
FU-F-s241-teamsize); it is on scripts/specfactory/lane_plays_known_red.txt.
"""
import pytest

import _play as P


@pytest.fixture(scope="module")
def game():
    g = P.start_game(extra_args=["--net-local"])
    try:
        yield g
    finally:
        g.stop()


def test_s241_lobby_offers_teams_of_2_and_4(game):
    c = game.client
    P.go_to_lobby(c)
    qa = P.record(c, "S-241", "team_size")
    lobby = qa.get("qa", qa)
    assert sorted(lobby.get("team_sizes", [])) == [2, 4], lobby.get("team_sizes")
    assert P.find_control(c.tree(), "TeamSize") is not None
