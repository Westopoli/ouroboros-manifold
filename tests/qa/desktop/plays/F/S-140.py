# Rule pins: R-140-02@56c964, R-140-03@14a1c8
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

Rewrite VG-F-S140-CLICK (TD-VG-F-s140-click, Architect 2026-10-20, spec "Lane F part 1b"). VG-A18's framing changed which
units the old fixed box took (42 of 56) and where the old fixed click landed, so the unselected own units stood between
the group and the click. The play now selects EVERY own unit on screen (the bounding box of their pixels, padded
DRAFT-s140-box-pad, kept out of the edge-scroll zone) and right-clicks the first clear compass point at
DRAFT-s140-click-offset from the selection's centroid, where clear means no unselected own unit stands in the corridor.
This rewrite does NOT test the sim stall of FINDING-sim-move-blocked-by-idle-own (a group stopping short of idle own
units, Q-087-02 closed (b)); that stall's test is the csim test of the Q-087-02 fix piece, and this play must not
pretend to cover it. No threshold moves: arrival and progress are _play.wait_settled and SETTLE_TICKS, unchanged.
"""
import math
import time

import pytest

import _play as P


@pytest.fixture(scope="module")
def pair():
    yield from P.pair_games()


# The receiving peer rejects a command naming more units than this as a bad packet and the match stalls
# (autoload/net/lockstep_session.gd UNITS_MAX 70, _valid), so the play orders at most this many own units.
# liberty 2026-10-11: the over-70 order is reported to the Architect as a finding, not tested here.
UNITS_MAX = 70
SCREEN_W, SCREEN_H = 1920, 1080
# The edge-scroll zone is 60 px (scenes/ground3d/camera_rig_3d.gd:14 EDGE_SCROLL_ZONE); the pointer stays 4 px beyond it.
EDGE_SCROLL_ZONE = 60.0
MARGIN = EDGE_SCROLL_ZONE + 4.0
# DRAFT-s140-box-pad and DRAFT-s140-click-offset (ledger docs/northstar/plans/push_ledger_2026-09-22.md, day37 rows).
BOX_PAD = 12.0
CLICK_OFFSET = 360.0
# The eight compass points in the order the play tries them: down, up, right, left, then the four diagonals
# (liberty 2026-10-20: the spec fixes the first four; the diagonal order is the writer's).
COMPASS = [(0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (-1, 1), (1, -1), (-1, -1)]


def _clamp(x: float, y: float) -> tuple:
    return min(max(x, MARGIN), SCREEN_W - MARGIN), min(max(y, MARGIN), SCREEN_H - MARGIN)


def _dist_to_segment(p, a, b) -> float:
    ax, ay = a
    dx, dy = b[0] - ax, b[1] - ay
    n = dx * dx + dy * dy
    t = 0.0 if n == 0 else max(0.0, min(1.0, ((p[0] - ax) * dx + (p[1] - ay) * dy) / n))
    return math.hypot(p[0] - (ax + t * dx), p[1] - (ay + t * dy))


def drag_box(own: dict) -> tuple:
    """The drag that takes every own unit: the bounding box of their pixels padded BOX_PAD, both corners at least
    MARGIN px inside the screen. Returns (x0, y0, x1, y1)."""
    xs = [p[0] for p in own.values()]
    ys = [p[1] for p in own.values()]
    x0, y0 = _clamp(min(xs) - BOX_PAD, min(ys) - BOX_PAD)
    x1, y1 = _clamp(max(xs) + BOX_PAD, max(ys) + BOX_PAD)
    return x0, y0, x1, y1


def shrunk_box(own: dict) -> tuple:
    """Over UNITS_MAX own units on screen (the all-units box would be refused by the receiving peer): the old search,
    a box around the own unit nearest the screen centre, shrunk until it takes 1..UNITS_MAX units. Yields boxes."""
    anchor = min(own, key=lambda u: (own[u][0] - 960) ** 2 + (own[u][1] - 540) ** 2)
    cx, cy = own[anchor]
    half = 240.0
    while half >= 15.0:
        x0, y0 = _clamp(cx - half, cy - half)
        x1, y1 = _clamp(cx + half, cy + half)
        yield (x0, y0, x1, y1)
        half *= 0.6  # liberty 2026-10-11: harness search step
    raise AssertionError("spec-gap: no box of 1..%d own units found around unit %s" % (UNITS_MAX, anchor))


def box_select(hc, own: dict) -> tuple:
    """A real drag. At most UNITS_MAX own units: one drag over all of them, then set(selected) == set(own).
    More: shrink around the anchor until 1..UNITS_MAX are selected. Returns (selected ids, the drag box)."""
    if len(own) <= UNITS_MAX:
        boxes = iter([drag_box(own)])
    else:
        boxes = shrunk_box(own)
    for box in boxes:
        hc.call("input", "drag", *box, 8)
        time.sleep(0.3)
        sel = [str(u) for u in P.tactical_qa(hc)["selected"]]
        if 1 <= len(sel) <= UNITS_MAX:
            return sel, box
    raise AssertionError("spec-gap: the drag %r selected no unit" % (box,))


def clear_click(centroid: tuple, box: tuple, blockers: dict) -> tuple:
    """The first clear compass candidate (CLICK_OFFSET from the centroid, clamped inside MARGIN) whose corridor holds no
    blocker pixel; the corridor is the segment centroid-candidate widened each side by half the box's larger side.
    Returns (candidate, name, per-candidate blocker ids)."""
    half = max(box[2] - box[0], box[3] - box[1]) / 2.0
    names = ["down", "up", "right", "left", "down-right", "down-left", "up-right", "up-left"]
    seen = {}
    for name, (dx, dy) in zip(names, COMPASS):
        norm = math.hypot(dx, dy)
        cand = _clamp(centroid[0] + CLICK_OFFSET * dx / norm, centroid[1] + CLICK_OFFSET * dy / norm)
        hit = sorted(u for u, p in blockers.items() if _dist_to_segment(p, centroid, cand) <= half)
        seen[name] = hit
        if not hit:
            return cand, name, seen
    raise AssertionError("spec-gap: no clear corridor; blockers per candidate: %r" % (seen,))


def test_s140_move_order_in_a_match_moves_the_units_on_both_peers(pair):
    host, guest = pair
    hc, gc = host.client, guest.client
    P.start_pair_match(host, guest)
    qa = P.tactical_qa(hc)
    own = {uid: qa["units_px"][uid] for uid, u in qa["units"].items()
           if u["faction"] == qa["local_faction"] and uid in qa["units_px"]}
    assert own, "no own unit is on screen in the match frame"
    P.note("own pixel extent x:", min(p[0] for p in own.values()), max(p[0] for p in own.values()),
           "y:", min(p[1] for p in own.values()), max(p[1] for p in own.values()),
           "own in the screen minus MARGIN:", sum(1 for p in own.values() if _clamp(*p) == tuple(p)),
           "units total:", len(qa["units"]), "units_px:", len(qa["units_px"]), "selected before:", len(qa["selected"]))
    ordered, box = box_select(hc, own)
    if len(own) <= UNITS_MAX:
        # New assertion (VG-F-S140-CLICK): the drag takes every own unit (red on the old play: 42 of 56).
        assert set(ordered) == {str(u) for u in own}, (
            "the drag took %d of %d own units; missing %s" % (len(ordered), len(own), sorted({str(u) for u in own} - set(ordered))))
    qa = P.tactical_qa(hc)  # the pixels of the moment after the drag
    px = qa["units_px"]
    sel_px = [px[u] for u in ordered if u in px]
    assert sel_px, "no selected unit has a pixel position after the drag"
    centroid = (sum(p[0] for p in sel_px) / len(sel_px), sum(p[1] for p in sel_px) / len(sel_px))
    blockers = {str(u): px[u] for u, un in qa["units"].items()
                if un["faction"] == qa["local_faction"] and str(u) not in set(ordered) and u in px}
    P.note("own units on screen:", len(own), "box-selected and ordered:", len(ordered), "drag box:", box,
           "centroid:", centroid, "unselected own:", len(blockers))
    click, name, seen = clear_click(centroid, box, blockers)
    P.note("candidate:", name, "click:", click, "blockers per candidate tried:", seen)
    tick0 = (int(qa["tick"]), int(P.tactical_qa(gc)["tick"]))
    start_h = P.positions(hc, ordered)
    start_g = P.positions(gc, ordered)
    hc.call("input", "click", click[0], click[1], 2)
    settled_h, settled_g = P.wait_settled(host, guest, ordered, start_h)
    after = P.record(hc, "S-140", "after_move_order")["qa"]
    P.note("ordered units:", len(ordered), "start host/guest:", start_h, start_g, "settled host/guest:", settled_h, settled_g)
    tick1 = (int(after["tick"]), int(P.tactical_qa(gc)["tick"]))
    assert tick1[0] > tick0[0] and tick1[1] > tick0[1], "the tick did not advance on both peers: %r -> %r" % (tick0, tick1)
    assert settled_h != start_h, "no ordered unit moved on the host after a move order"
    assert settled_g != start_g, "no ordered unit moved on the guest after the host's move order (the order did not cross)"
    for u in ordered:
        assert settled_g.get(u) == settled_h.get(u), "unit %s: host %r, guest %r" % (u, settled_h.get(u), settled_g.get(u))
