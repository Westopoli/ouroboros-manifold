"""Story play S-143 "Eras in sequence": the lobby says the match is limited to the common era set.
Rules R-143-01 ("the match may traverse only eras every peer owns, in chronological order") and R-143-03 ("Given a peer
lacks a pack, When the lobby forms, Then the match is limited to the common set and the lobby says so"); R-147-01 and
R-149-01 give the two first-build eras (the Settled Reach, space, order 0; the Greek placeholder pack, ground, order 1).
Green on the built tree (VG-F-S143, spec Rev 13: docs/northstar/plans/2026-10-07-visible-game-spec.md, F-S143
paragraph and gaps g1 to g3, Architect rulings of 2026-10-14). The landing closes ledger row FU-F-s143-common-eras (the
play leaves scripts/specfactory/lane_plays_known_red.txt then, the clerk removes the line) and rows FU-F-guest-faction
and FU-F-net-qa-key stay as they are (this play reads qa_state, not a `net` key, and both peers still play faction 0).

Q-F-1 (Westley, 2026-10-11, closed): "allowed, so long as the test does everything it can to emulate the reality of two
players joining and not taking shortcuts beyond what is strictly necessary given the limitation". So case 1 reaches the
lobby of one game on the Steam-less local test network (--net-local), and case 2 is two real game processes (P.pair_games)
where the guest types the host's lobby id and joins; no call into the lobby script, no pre-seeded table.

Case 1 (one game, no Host click): the lobby already shows its era line. Inventory from the running scene (Visible-game
guard 1): EraLine on screen inside 1920x1080 with exactly "Eras: you <list> . peers none . playable <list>" (gap 3; the
dot is U+00B7, ids comma-space separated in era_order, "peers" reads "none" with no other member); qa_state
owned_eras == eras[local member] == the installed, accessible packs, which on main is ["settled_reach"] (pins 1 and 2:
mock source entitlement stub; the installed packs are read here from res://assets/eras/*/manifest.json, test_only
skipped, era_order order, the source of gap 1); common_eras == playable_eras == owned_eras with no peer.
The existing assertions (owned and common non-empty, common inside owned, an on-screen text naming the eras) are kept.

Case 2 (two processes): the host is launched with --net-local-eras naming every installed era (it owns two, through the
seam, because the source yields one on main), the guest with --net-local-eras naming the first installed era (one era).
After the guest joins, on BOTH lobbies qa_state eras holds both rows, common_eras / playable_eras is that one era, and
each EraLine reads the words of gap 3 for a narrowed set (the host: peers = the guest's era; the guest: peers = the
host's eras). The host shot is taken with P.record. The guest reads the host's `playable_eras` and `era_table` lobby
data (gap 2 (a), rev 13a): the case would stay red if only the chat messages worked on one side.
"""
import json
from pathlib import Path

import pytest

import _play as P

VIEWPORT_HOST = (1920, 1080)
VIEWPORT_GUEST = (1280, 720)  # pair_games' guest resolution
HOST_ID, GUEST_ID = "1", "2"  # P.pair_games passes --net-local-id 1 and 2
DOT = "·"


def installed_era_ids() -> list[str]:
    """The ids of the installed packs as era_pack_source.gd manifests() yields them: res://assets/eras/*/manifest.json,
    test_only skipped, sorted by era_order (gap 1 source; scenes/era_library/era_pack_source.gd:14-29)."""
    packs = []
    for m in sorted(P.ROOT.glob("assets/eras/*/manifest.json")):
        d = json.loads(m.read_text())
        if not d.get("test_only", False):
            packs.append((int(d["era_order"]), str(d["era_id"])))
    return [era for _, era in sorted(packs)]


def inside(control: dict, size: tuple[int, int]) -> bool:
    x, y, w, h = control["rect_px"]
    return x >= 0 and y >= 0 and x + w <= size[0] and y + h <= size[1]


def era_line(owned: list, peers: list, playable: list) -> str:
    """The words of gap 3: 'Eras: you <list> . peers <list> . playable <list>', peers 'none' when empty."""
    def lst(ids):
        return ", ".join(ids) if ids else "none"
    return "Eras: you %s %s peers %s %s playable %s" % (lst(owned), DOT, lst(peers), DOT, lst(playable))


@pytest.fixture
def game():
    g = P.start_game(extra_args=["--net-local"])
    try:
        yield g
    finally:
        g.stop()


def test_s143_lobby_shows_common_era_set(game):
    c = game.client
    res = P.go_to_lobby(c)
    # CONTROL (green on any tree with a lobby): the lobby scene is reached under --net-local, its qa_state has a
    # members list and the Host button exists. A red after this line means the feature is missing, not the harness.
    assert P.lobby_qa(res).get("scene") == "lobby" and "members" in P.lobby_qa(res), "CONTROL: lobby qa %r" % res
    assert P.find_control(c.tree(), "HostButton") is not None, "CONTROL: no HostButton among %r" % P.control_names(c.tree())
    P.note("S-143 lobby qa before Host:", json.dumps(P.lobby_qa(res), sort_keys=True))
    P.note("S-143 lobby controls:", sorted(P.control_names(c.tree())))
    P.note("installed eras from the manifests:", installed_era_ids())
    qa = P.record(c, "S-143", "common_eras")
    lobby = qa.get("qa", qa)
    owned, common = lobby.get("owned_eras", []), lobby.get("common_eras", [])
    assert owned and common, lobby
    assert set(common) <= set(owned), "the common set must be inside the host's own packs (R-143-03)"
    era_ctl = P.control_with_text(c, "era")
    assert era_ctl is not None, "no on-screen text naming the eras"
    # Stricter, from the running scene (S-143, R-143-03, gaps 1 and 3, pins 1 and 2 of the rulings).
    installed = installed_era_ids()
    assert owned == ["settled_reach"], "S-143 gap 1 / pin 2: owned_eras on main is the accessible installed packs, %r" % owned
    assert set(owned) <= set(installed) and owned == [e for e in installed if e in owned], \
        "S-143 gap 1: owned_eras %r must be installed ids in era_order order (installed %r)" % (owned, installed)
    assert common == owned, "S-143 gap 3: with no peer common_eras (= playable_eras) equals owned_eras: %r" % lobby
    assert lobby.get("playable_eras") == common, "S-143 gap 3: playable_eras must equal common_eras: %r" % lobby
    eras = lobby.get("eras")
    assert isinstance(eras, dict) and list(eras.values()) == [owned], \
        "S-143 gap 3 / pin 1: eras must hold exactly the local row, equal to owned_eras: %r" % (eras,)
    line = P.find_control(c.tree(), "EraLine")
    assert line is not None, "S-143: no EraLine among %r" % P.control_names(c.tree())
    assert inside(line, VIEWPORT_HOST), "S-143: EraLine is not inside 1920x1080: %r" % line["rect_px"]
    assert line["text"] == era_line(owned, [], common), "S-143 gap 3: EraLine reads %r" % line["text"]


@pytest.fixture(scope="module")
def pair():
    installed = installed_era_ids()
    assert len(installed) >= 2, "S-143: two installed non-test packs needed for the narrowed case (R-147-01): %r" % installed
    yield from P.pair_games(host_args=["--net-local-eras", ",".join(installed)],
                            guest_args=["--net-local-eras", installed[0]])


def test_s143_two_players_lobby_narrows_to_common_era(pair):
    host, guest = pair
    installed = installed_era_ids()
    host_eras, guest_eras = installed, installed[:1]
    # CONTROL is inside reach_pair_lobby: both lobbies reached under --net-local with a members list and a HostButton.
    P.reach_pair_lobby(host, guest)
    hc, gc = host.client, guest.client

    def both_rows(client):
        q = P.lobby_qa(client.state()["result"])
        return q if len(q.get("eras") or {}) == 2 else None

    def dump(client):
        return json.dumps(P.lobby_qa(client.state()["result"]), sort_keys=True)

    hq0 = P.lobby_qa(hc.state()["result"])
    assert "owned_eras" in hq0 and "common_eras" in hq0 and "eras" in hq0, \
        "S-143 gap 3: the host lobby qa_state has no owned_eras / common_eras / eras keys: %s" % dump(hc)
    P.wait_until(lambda: both_rows(hc), P.PAIR_S, "S-143: host lobby holds both players' era rows",
                 why=lambda: "host qa %s" % dump(hc))
    P.wait_until(lambda: both_rows(gc), P.PAIR_S, "S-143: guest lobby holds both players' era rows (the host's keys "
                 "playable_eras / era_table reached it, gap 2 (a))", why=lambda: "guest qa %s" % dump(gc))
    shot = P.record(hc, "S-143", "common_eras_pair")
    hq, gq = P.lobby_qa(shot), P.lobby_qa(gc.state()["result"])
    P.note("host lobby qa:", json.dumps(hq, sort_keys=True))
    P.note("guest lobby qa:", json.dumps(gq, sort_keys=True))
    P.note("host seam eras:", host_eras, "guest seam eras:", guest_eras)
    assert sorted(str(m) for m in hq["members"]) == [HOST_ID, GUEST_ID], hq
    for who, q, own in (("host", hq, host_eras), ("guest", gq, guest_eras)):
        assert q["eras"] == {HOST_ID: host_eras, GUEST_ID: guest_eras}, \
            "S-143 gap 3: %s eras table %r, wanted the seam sets %r" % (who, q["eras"], {HOST_ID: host_eras, GUEST_ID: guest_eras})
        assert q["owned_eras"] == own, "S-143 gap 1/2: %s owned_eras %r, wanted %r (the seam)" % (who, q["owned_eras"], own)
        assert q["playable_eras"] == guest_eras and q["common_eras"] == guest_eras, \
            "S-143 R-143-03: %s common set %r / %r, wanted the guest's one era %r" % (who, q["common_eras"], q["playable_eras"], guest_eras)
        assert set(q["common_eras"]) < set(host_eras), "S-143: the common set must be narrower than the host's own eras"
    for who, client, size, own, peers in (("host", hc, VIEWPORT_HOST, host_eras, guest_eras),
                                          ("guest", gc, VIEWPORT_GUEST, guest_eras, host_eras)):
        line = P.find_control(client.tree(), "EraLine")
        assert line is not None, "S-143: %s has no EraLine among %r" % (who, P.control_names(client.tree()))
        assert inside(line, size), "S-143: %s EraLine is not inside %dx%d: %r" % (who, size[0], size[1], line["rect_px"])
        assert line["text"] == era_line(own, peers, guest_eras), "S-143 gap 3: %s EraLine reads %r" % (who, line["text"])
