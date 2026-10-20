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

Rewrite VG-F-S140-CLICK (TD-VG-F-s140-click, Architect 2026-10-20, spec "Lane F part 1b" as ruled on the finding
that 185 own units are on screen at seed 1 and the receiver rejects an order naming more than UNITS_MAX = 70). VG-A18's
framing changed which units the old fixed box took (42 of the 185 own units on screen; 56 was the old box's selection
at 6fdc9d64) and where the old fixed click landed, so the unselected own units stood between the group and the click.
The play now picks the click side first (of down, up, right, left, the side with the most room between the own-unit
pixel extent and the edge-scroll margin), selects the UNITS_MAX own units nearest that side by a real drag (their
bounding box padded DRAFT-s140-box-pad, kept out of the edge-scroll zone), and right-clicks the point
DRAFT-s140-click-offset beyond the group's leading edge, in a corridor with no unselected own unit; a side whose
corridor is not clear gives way to the next side.
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
MIN_SELECTED = 8
SIDES = ["down", "up", "right", "left"]  # tie order; screen y grows downward
_DIR = {"down": (0, 1), "up": (0, -1), "right": (1, 0), "left": (-1, 0)}


def _clamp(x: float, y: float) -> tuple:
    return min(max(x, MARGIN), SCREEN_W - MARGIN), min(max(y, MARGIN), SCREEN_H - MARGIN)


def _lead(side: str, p) -> float:
    """How far a pixel is toward `side` (bigger = nearer that side)."""
    dx, dy = _DIR[side]
    return p[0] * dx + p[1] * dy


def ranked_sides(own: dict) -> list:
    """The four sides by room to walk: the distance from the own-unit pixel extent's edge on that side to the screen's
    edge-scroll margin, the most room first, ties in the order of SIDES. Returns [(side, room)]. The play tries them in
    this order (liberty 2026-10-20: the spec's "the next side in the order above" read as the next by room)."""
    xs = [p[0] for p in own.values()]
    ys = [p[1] for p in own.values()]
    room = {"down": (SCREEN_H - MARGIN) - max(ys), "up": min(ys) - MARGIN,
            "right": (SCREEN_W - MARGIN) - max(xs), "left": min(xs) - MARGIN}
    return [(s, room[s]) for s in sorted(SIDES, key=lambda s: (-room[s], SIDES.index(s)))]


def nearest_to(own: dict, side: str, n: int) -> list:
    """The n own unit ids nearest `side` (largest y for down, smallest y for up, largest x for right, smallest x for
    left); equal pixels by id, so the set is repeatable."""
    return sorted(own, key=lambda u: (-_lead(side, own[u]), str(u)))[:n]


def drag_box(pts: list, pad: float) -> tuple:
    """The bounding box of the pixels padded `pad`, both corners at least MARGIN px inside the screen."""
    x0, y0 = _clamp(min(p[0] for p in pts) - pad, min(p[1] for p in pts) - pad)
    x1, y1 = _clamp(max(p[0] for p in pts) + pad, max(p[1] for p in pts) + pad)
    return x0, y0, x1, y1


def select_side(hc, own: dict, side: str) -> tuple:
    """A real drag over the UNITS_MAX own units nearest `side`. If the box takes more than UNITS_MAX units (neighbours
    inside it), the pad shrinks to 0, and then the set shrinks from the far side until the count is at most UNITS_MAX
    and at least MIN_SELECTED. Returns (selected ids, the drag box)."""
    n, pad = min(UNITS_MAX, len(own)), BOX_PAD
    while n >= MIN_SELECTED:
        box = drag_box([own[u] for u in nearest_to(own, side, n)], pad)
        hc.call("input", "drag", *box, 8)
        time.sleep(0.3)
        sel = [str(u) for u in P.tactical_qa(hc)["selected"]]
        if len(sel) <= UNITS_MAX:
            return sel, box
        if pad > 0:
            pad = 0.0
        else:
            n -= max(1, len(sel) - UNITS_MAX)  # liberty 2026-10-20: step the set down by the excess
    raise AssertionError("spec-gap: no drag of %d..%d own units found on the %s side" % (MIN_SELECTED, UNITS_MAX, side))


def corridor(side: str, sel_px: list, box: tuple, blockers: dict) -> tuple:
    """The click and its corridor for `side`: the leading edge is the selected set's extreme pixel toward `side`; the
    click is CLICK_OFFSET beyond it, clamped inside MARGIN; the corridor is the band from the leading edge to the click,
    as wide as the drag box's side across the walk direction (centred on the selection). Returns (leading edge
    coordinate, click, sorted ids of the unselected own units inside the band)."""
    dx, dy = _DIR[side]
    if dx == 0:  # walking along y: the band is the box's width wide
        edge = max(p[1] for p in sel_px) if dy > 0 else min(p[1] for p in sel_px)
        mid = (min(p[0] for p in sel_px) + max(p[0] for p in sel_px)) / 2.0
        half = (box[2] - box[0]) / 2.0
        click = _clamp(mid, edge + dy * CLICK_OFFSET)
        lo, hi = sorted((edge, click[1]))
        hit = [u for u, p in blockers.items() if mid - half <= p[0] <= mid + half and lo <= p[1] <= hi]
    else:  # walking along x: the band is the box's height wide
        edge = max(p[0] for p in sel_px) if dx > 0 else min(p[0] for p in sel_px)
        mid = (min(p[1] for p in sel_px) + max(p[1] for p in sel_px)) / 2.0
        half = (box[3] - box[1]) / 2.0
        click = _clamp(edge + dx * CLICK_OFFSET, mid)
        lo, hi = sorted((edge, click[0]))
        hit = [u for u, p in blockers.items() if mid - half <= p[1] <= mid + half and lo <= p[0] <= hi]
    return edge, click, sorted(hit)


def test_s140_move_order_in_a_match_moves_the_units_on_both_peers(pair):
    host, guest = pair
    hc, gc = host.client, guest.client
    P.start_pair_match(host, guest)
    qa = P.tactical_qa(hc)
    own = {uid: qa["units_px"][uid] for uid, u in qa["units"].items()
           if u["faction"] == qa["local_faction"] and uid in qa["units_px"]}
    assert own, "no own unit is on screen in the match frame"
    ranked = ranked_sides(own)
    P.note("own units on screen:", len(own), "units total:", len(qa["units"]), "selected before:", len(qa["selected"]),
           "own pixel extent x:", min(p[0] for p in own.values()), max(p[0] for p in own.values()),
           "y:", min(p[1] for p in own.values()), max(p[1] for p in own.values()), "sides by room:", ranked)
    assert len(own) >= MIN_SELECTED, "spec-gap: only %d own units on screen" % len(own)
    own_ids = {str(o) for o in own}
    seen = {}
    for side, _room in ranked:
        ordered, box = select_side(hc, own, side)
        # New assertions (VG-F-S140-CLICK): the selection is real, and within what the receiver accepts.
        assert set(ordered) <= own_ids, "selected units outside own: %r" % (sorted(set(ordered) - own_ids),)
        assert MIN_SELECTED <= len(ordered) <= UNITS_MAX, "selected %d units (needs %d..%d)" % (len(ordered), MIN_SELECTED, UNITS_MAX)
        qa = P.tactical_qa(hc)  # the pixels of the moment after the drag
        px = qa["units_px"]
        sel_px = [px[u] for u in ordered if u in px]
        assert sel_px, "no selected unit has a pixel position after the drag"
        blockers = {str(u): px[u] for u, un in qa["units"].items()
                    if un["faction"] == qa["local_faction"] and str(u) not in set(ordered) and u in px}
        edge, click, hit = corridor(side, sel_px, box, blockers)
        P.note("side:", side, "selected:", len(ordered), "drag box:", box, "leading edge:", edge, "click:", click,
               "unselected own:", len(blockers), "blockers in the corridor:", hit)
        if not hit:
            break
        seen[side] = hit
    else:
        raise AssertionError("spec-gap: no clear corridor; blockers per side: %r" % (seen,))
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
