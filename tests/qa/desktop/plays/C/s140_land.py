# Rule pins: R-009-01@4af687, R-010-01@b3e461
"""S-140 land play (VG-C-land-one-projection, spec paragraph "VG-C-land-one-projection" in
docs/northstar/plans/2026-10-07-visible-game-spec.md; lane C's copy of the S-140 moment on land, DEC-S140-live-look).
Proves R-010-01 (a unit's marks sit on its ground position) and R-009-01 (a structure's marks sit on its ground position)
as the paragraph tags them: after a move order on the ground view every visible mark of the ordered units is where
`units_px` puts them, with no sim step between the pan and the read.

Moment 'tick60': box-select the 20 own units nearest the screen centre (the px bounding box of those 20, padded BOX_PAD
12 px, the S-140 play's BOX_PAD, tests/qa/desktop/plays/F/S-140.py:49), right-click at the selected centroid plus 400 wu
along +x projected through the `project` verb (the same projector as `units_px`), step 60 ticks, and assert
  (a) moved toward the click: the selected centroid's world x rose by at least MIN_RISE_WU 50 wu,
  (b) every visible mark of the selected units (qa_state marks_px: the icon, and the squads when UnitSquads is visible)
      lies within TOL_PX 1 px of units_px, at the default camera and again at height 300.
The frame at tick 60 at height 300 is the shot (`s140_land_tick60`), queued for Westley with the live-look command of
DEC-S140-live-look. Height 300 is set with the qa verb camera_set {height} (VG-C-land-one-projection adds it, no sim step).
CONTROLS: c0 the box took at least the 20 units (the drag selected something, so a pass is not on an empty set);
c1 the click was accepted (last_command ok) so a red result is not a mis-click; c2 the selection survived the 60 ticks;
c3 marks_px lists every selected id (an absent mark cannot pass as 'within 1 px')."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _play  # noqa: E402

SCREEN_W, SCREEN_H = 1920, 1080  # _play.start_ground_game resolution
BOX_PAD = 12.0  # px: the S-140 play's BOX_PAD (plays/F/S-140.py:49)
NEAREST = 20  # own units nearest the screen centre
CLICK_WU = 400.0  # along +x of the selected centroid
STEP_TICKS = 60
MIN_RISE_WU = 50.0  # the selected centroid's world x rises by at least this within STEP_TICKS
TOL_PX = 1.0
HEIGHT_SHOT = 300.0  # the shot's camera height


@pytest.fixture(scope="module")
def game():
    g = _play.start_ground_game()
    try:
        yield g
    finally:
        g.stop()


def _centroid_world(q, ids):
    pts = [(float(q["units"][i]["x"]), float(q["units"][i]["y"])) for i in ids if i in q["units"]]
    assert pts, "c2: none of the selected units is in the frame"
    return sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts)


def _marks_within(q, ids, label):
    """Every visible mark of `ids` (icon, squads) within TOL_PX of units_px; returns the worst distance in px."""
    marks, px = q.get("marks_px"), q.get("units_px", {})
    assert isinstance(marks, dict), "%s: qa_state has no marks_px (interface not built)" % label
    worst = 0.0
    for i in ids:
        m = marks.get(str(i))
        assert m is not None and "icon" in m, "c3 %s: marks_px has no icon for unit %s" % (label, i)
        want = px.get(str(i))
        assert want is not None, "%s: units_px has no unit %s" % (label, i)
        for kind, pt in [("icon", m["icon"])] + [("squads", s) for s in m.get("squads", [])]:
            d = ((pt[0] - want[0]) ** 2 + (pt[1] - want[1]) ** 2) ** 0.5
            worst = max(worst, d)
            assert d <= TOL_PX, "R-010-01 %s: unit %s %s mark at %r is %.1f px from units_px %r" % (label, i, kind, pt, d, want)
    return worst


def test_s140_land_marks_follow_the_ground_after_a_move_order(game):
    c = game.client
    q0 = _play.qa(game)
    _play.ground3d(game)
    own = {i: p for i, p in q0["units_px"].items() if q0["units"][i]["faction"] == q0["local_faction"]}
    assert len(own) >= NEAREST, "gap: only %d own units on screen" % len(own)
    near = sorted(own, key=lambda i: ((own[i][0] - SCREEN_W / 2) ** 2 + (own[i][1] - SCREEN_H / 2) ** 2, int(i)))[:NEAREST]
    x0, y0 = min(own[i][0] for i in near) - BOX_PAD, min(own[i][1] for i in near) - BOX_PAD
    x1, y1 = max(own[i][0] for i in near) + BOX_PAD, max(own[i][1] for i in near) + BOX_PAD
    c.call("input", "drag", x0, y0, x1, y1, 8)
    q1 = _play.qa(game)
    sel = [str(i) for i in q1["selected"]]
    print("PREMISE own on screen", len(own), "nearest", len(near), "box", (x0, y0, x1, y1), "selected", len(sel))
    assert len(sel) >= NEAREST, "c0: the drag selected %d units, the box holds at least %d" % (len(sel), NEAREST)
    cx0, cy0 = _centroid_world(q1, sel)
    r = c.call("project", cx0 + CLICK_WU, cy0)
    assert r.get("ok") is True, "project verb refused: %r" % (r,)
    click = (r["result"]["x"], r["result"]["y"])
    print("PREMISE centroid", (cx0, cy0), "click world", (cx0 + CLICK_WU, cy0), "click px", click)
    c.call("input", "click", float(click[0]), float(click[1]), 2)
    lc = _play.qa(game).get("last_command", {})
    assert lc.get("ok") is True, "c1: the move order was refused: %r" % (lc,)
    _play.step(game, STEP_TICKS)
    q2 = _play.qa(game)
    assert int(q2["tick"]) >= int(q1["tick"]) + STEP_TICKS, "tick %s after %s + %d" % (q2["tick"], q1["tick"], STEP_TICKS)
    assert set(sel) <= {str(i) for i in q2["selected"]}, "c2: the selection changed during the 60 ticks"
    cx1, cy1 = _centroid_world(q2, sel)
    print("SAMPLE tick", q2["tick"], "centroid", (cx1, cy1), "rise", cx1 - cx0)
    assert cx1 - cx0 >= MIN_RISE_WU, "the selected centroid's x rose %.1f wu in %d ticks, at least %.0f expected" % (cx1 - cx0, STEP_TICKS, MIN_RISE_WU)
    w_default = _marks_within(q2, sel, "tick 60 default camera")
    r = c.call("camera_set", {"height": HEIGHT_SHOT})
    assert r.get("ok") is True, "camera_set refused: %r" % (r,)
    q3 = _play.qa(game)
    assert int(q3["tick"]) == int(q2["tick"]), "camera_set stepped the sim: %s -> %s" % (q2["tick"], q3["tick"])
    w_low = _marks_within(q3, sel, "tick 60 height %d" % int(HEIGHT_SHOT))
    print("SAMPLE worst mark offset px: default %.3f, height %d %.3f" % (w_default, int(HEIGHT_SHOT), w_low))
    _play.evidence(game, "s140_land", "tick60")
