"""Story play S-140 "Commands over the wire": an order given in a match goes through the session and the unit moves.
Two real game processes on the Steam-less local test network (VG-F-SKEL-B; Q-F-1 closed by Westley, 2026-10-11): the
host box-selects its own units and right-clicks a point; at a common tick after the settle ticks the guest's qa_state shows
every ordered unit at the host's x and y (the order crossed to the guest). Both peers are faction 0 for the skeleton
(ledger row FU-F-guest-faction), so the guest's faction-0 units are the units the host ordered. Rules R-140-02 (orders
are applied at tick+3), R-140-03. The qa `net` key waits for a later piece (row FU-F-net-qa-key): the check here is the
tick advancing on both processes plus the position match.
The settle wait counts game ticks, not seconds (A17's rule): _play.SETTLE_TICKS is DRAFT-s140-settle-ticks (ledger row,
docs/northstar/plans/push_ledger_2026-09-22.md, measured 781 ticks x 1.5 = 1200). The condition is equality at a common
tick, not rest (Architect 2026-10-12): at a tick T both peers have sampled, at least SETTLE_TICKS after the order, every
ordered unit's (x, y, layer) is byte-equal on host and guest, and the units have made progress toward the click.
"""
import time

import pytest

import _play as P


@pytest.fixture(scope="module")
def pair():
    yield from P.pair_games()


# The receiving peer rejects a command naming more units than this as a bad packet and the match stalls
# (autoload/net/lockstep_session.gd UNITS_MAX 70, _valid), so the play orders a box of at most this many own units.
# liberty 2026-10-11: the over-70 order is reported to the Architect as a finding, not tested here.
UNITS_MAX = 70


def box_select(hc, own: dict) -> list:
    """A real drag over a box around the own unit nearest the screen centre (away from the edge-scroll margin), shrunk
    until 1..UNITS_MAX units are selected; clamped at least 8 px inside the 1920x1080 screen (plays/A/play_support.py
    TD-VG-A-9). Returns (the selected ids, the anchor pixel)."""
    anchor = min(own, key=lambda u: (own[u][0] - 960) ** 2 + (own[u][1] - 540) ** 2)
    cx, cy = own[anchor]
    half = 240.0
    while half >= 15.0:
        x0, y0 = max(cx - half, 8), max(cy - half, 8)
        x1, y1 = min(cx + half, 1912), min(cy + half, 1072)
        hc.call("input", "drag", x0, y0, x1, y1, 8)
        time.sleep(0.3)
        sel = [str(u) for u in P.tactical_qa(hc)["selected"]]
        if 1 <= len(sel) <= UNITS_MAX:
            return sel, (cx, cy)
        half *= 0.6  # liberty 2026-10-11: harness search step
    raise AssertionError("spec-gap: no box of 1..%d own units found around unit %s" % (UNITS_MAX, anchor))


def test_s140_move_order_in_a_match_moves_the_units_on_both_peers(pair):
    host, guest = pair
    hc, gc = host.client, guest.client
    P.start_pair_match(host, guest)
    qa = P.tactical_qa(hc)
    own = {uid: qa["units_px"][uid] for uid, u in qa["units"].items()
           if u["faction"] == qa["local_faction"] and uid in qa["units_px"]}
    assert own, "no own unit is on screen in the match frame"
    ordered, (cx, cy) = box_select(hc, own)
    P.note("own units on screen:", len(own), "box-selected and ordered:", len(ordered))
    tick0 = (int(qa["tick"]), int(P.tactical_qa(gc)["tick"]))
    start_h = P.positions(hc, ordered)
    start_g = P.positions(gc, ordered)
    # Right-click well away from the group (about 360 px, inside the screen, outside the edge-scroll margin) so the
    # units have somewhere to walk to.
    hc.call("input", "click", cx, 900 if cy < 600 else 180, 2)
    settled_h, settled_g = P.wait_settled(host, guest, ordered, start_h)
    after = P.record(hc, "S-140", "after_move_order")["qa"]
    P.note("ordered units:", len(ordered), "start host/guest:", start_h, start_g, "settled host/guest:", settled_h, settled_g)
    tick1 = (int(after["tick"]), int(P.tactical_qa(gc)["tick"]))
    assert tick1[0] > tick0[0] and tick1[1] > tick0[1], "the tick did not advance on both peers: %r -> %r" % (tick0, tick1)
    assert settled_h != start_h, "no ordered unit moved on the host after a move order"
    assert settled_g != start_g, "no ordered unit moved on the guest after the host's move order (the order did not cross)"
    for u in ordered:
        assert settled_g.get(u) == settled_h.get(u), "unit %s: host %r, guest %r" % (u, settled_h.get(u), settled_g.get(u))
