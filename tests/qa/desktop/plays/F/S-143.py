"""Story play S-143 "Eras in sequence": the lobby says the match is limited to the common era set (R-143-01, R-143-03).
A host sees an EraLine naming the era(s) they own; qa_state carries owned_eras and common_eras (lists of era ids,
never empty for a host) and common_eras is a subset of owned_eras. Names fixed here (flagged to the Architect).
Reaches the lobby of one game on the Steam-less local test network (--net-local; Q-F-1 closed by Westley,
2026-10-11); no second player is needed to see the era line.
Stays red by design until the later lane F piece that adds owned_eras and common_eras to the lobby qa_state (ledger
row FU-F-s143-common-eras); it is on scripts/specfactory/lane_plays_known_red.txt.
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


def test_s143_lobby_shows_common_era_set(game):
    c = game.client
    P.go_to_lobby(c)
    qa = P.record(c, "S-143", "common_eras")
    lobby = qa.get("qa", qa)
    owned, common = lobby.get("owned_eras", []), lobby.get("common_eras", [])
    assert owned and common, lobby
    assert set(common) <= set(owned), "the common set must be inside the host's own packs (R-143-03)"
    era_line = P.control_with_text(c, "era")
    assert era_line is not None, "no on-screen text naming the eras"
