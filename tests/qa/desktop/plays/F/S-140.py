"""Story play S-140 "Commands over the wire": an order given in a match goes through the session and the unit moves.
Two real game processes on the Steam-less local test network (VG-F-SKEL-B; Q-F-1 closed by Westley, 2026-10-11): the
host box-selects its own units and right-clicks a point; once the ordered units have stopped, the guest's qa_state shows
every ordered unit at the host's x and y (the order crossed to the guest). Both peers are faction 0 for the skeleton
(ledger row FU-F-guest-faction), so the guest's faction-0 units are the units the host ordered. Rules R-140-02 (orders
are applied at tick+3), R-140-03. The qa `net` key waits for a later piece (row FU-F-net-qa-key): the check here is the
tick advancing on both processes plus the position match.
Red until VG-F-SKEL-B wires --net-local into lobby.gd: the Host button stays disabled.
"""
import time

import pytest

import _play as P


@pytest.fixture(scope="module")
def pair():
    yield from P.pair_games()


def test_s140_move_order_in_a_match_moves_the_units_on_both_peers(pair):
    host, guest = pair
    hc, gc = host.client, guest.client
    P.start_pair_match(host, guest)
    qa = P.tactical_qa(hc)
    own = [uid for uid, u in qa["units"].items() if u["faction"] == qa["local_faction"]]
    assert own, "no own units in the match frame"
    px = qa["units_px"]
    ordered = [u for u in own if u in px]
    assert ordered, "no own unit is on screen"
    xs = [px[u][0] for u in ordered]
    ys = [px[u][1] for u in ordered]
    tick0 = (int(qa["tick"]), int(P.tactical_qa(gc)["tick"]))
    hc.call("input", "drag", min(xs) - 20, min(ys) - 20, max(xs) + 20, max(ys) + 20, 8)
    start_h = P.positions(hc, ordered)
    start_g = P.positions(gc, ordered)
    hc.call("input", "click", 960, 540, 2)
    settled_h, settled_g = P.wait_settled(host, guest, ordered, start_h)
    after = P.record(hc, "S-140", "after_move_order")["qa"]
    P.note("ordered units:", len(ordered), "start host/guest:", start_h, start_g, "settled host/guest:", settled_h, settled_g)
    tick1 = (int(after["tick"]), int(P.tactical_qa(gc)["tick"]))
    assert tick1[0] > tick0[0] and tick1[1] > tick0[1], "the tick did not advance on both peers: %r -> %r" % (tick0, tick1)
    assert settled_h != start_h, "no ordered unit moved on the host after a move order"
    assert settled_g != start_g, "no ordered unit moved on the guest after the host's move order (the order did not cross)"
    for u in ordered:
        assert settled_g.get(u) == settled_h.get(u), "unit %s: host %r, guest %r" % (u, settled_h.get(u), settled_g.get(u))
