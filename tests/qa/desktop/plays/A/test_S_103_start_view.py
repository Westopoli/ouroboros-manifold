"""Story play S-103 (E-16, R-103-01, R-103-02, R-246-07; visible-game spec Rev 12d, A18, the camera at mission start):
"A free camera I manage myself, with the Angle Rack, the Layer Peel, and a flip key." (docs/bible/stories.md:109)
Westley 2026-10-12, camera at mission start: "yes, of your base".

Rules quoted:
  R-103-01: "the classic view has one auto-anchor home the player returns to by key"
  R-246-07: "the army spawns at its home base"
  R-103-02: the camera centre never leaves 0..canvas at any zoom (not asserted here; the GD test owns it).

Gap rulings used (Architect 2026-10-12, A18): G2 the margin is 10% of the viewport per side (DRAFT-a18-margin, spec Rev 12d A18,
untagged in the spec); G3 the player's spawn point is the kind-7 node nearest the own-unit centroid; G4 the home key is Home
(KEY_HOME, DRAFT-a18-home-key) and restores the stored opening camera and zoom; G5 the 2D path in this piece (the 3D rig fit is
FU-A18-3d); G7 own units only, no visible enemy, no sight term; G9 the opening frame is the first frame held after Deploy (tick 1 on
the live path, not 0; the qa tick read here is whatever the harness reached, the camera does not follow so it is the opening framing).

Moment: the first tactical frame after Deploy, S-103 "start_view" (the queued shot). Order of the tests in this file matters: the pan
test moves the camera, so it runs last.

ERAS (G5): the body is era-agnostic. Default run is the space era the fixture boots. Ground variant:
  OM_PLAY_ERA=ground xvfb-run -a timeout 900 env OM_QA_RENDERER=vulkan ~/Projects/ouroboros-manifold/.venv/bin/python -m pytest tests/qa/desktop/plays/A/test_S_103_start_view.py -q
(play_support.py:27-31 reads OM_PLAY_ERA; the shot name gets the suffix _ground). Measured on main in the ground era: tests 1 to 3 are green
(the existing fit already leaves the margin on that wide box; the 4 settlement_lots rows are all owner -1, so the lot clause is vacuous there too) and
test 4 (Home) is red; so the ground variant guards against a regression, and is red only for the home key.

Test 1 (CONTROL, green today): units_px is non-empty and the project verb agrees with units_px for one own unit within 1.5 px.
Test 2 (green on main for this live mission, a measured finding): every own unit is fully inside 1920x1080 (px +- 12, UNIT_SIZE / 2,
R-103-01). Measured on main: all 330 own units pass, the topmost at y = 12.00002, i.e. flush with the top edge by 0.00002 px. The
"23 of 236 outside" of tests/test_tactical_camera.gd is that test's own frame; the units clause stays here as the regression guard.
Test 3 (red on main): the own lots and the spawn point project on screen (both green today) and the own units' px box keeps the
10% viewport margin (G2). Red on main: the box is (636, 12)..(1216, 322), flush with the top edge, no margin.
  The lot clause: none is expected at open on the live mission (settlement_lots is [] in the space era and before any lot is owned),
  so the lot clause is vacuous on the live mission and is proven by the GD fixture (tests/test_tactical_camera.gd, the A18 groups).
  The spawn clause: qa_state exposes no map.nodes (only objects_px for the objective nodes), so the kind-7 node of G3 cannot be read
  from here; the own-unit centroid stands in for it (liberty 2026-10-12). It lies inside the own units' box, so the clause cannot
  catch a builder that frames the exact node but not the units; the units clause above does that. The exact node is proven by the GD
  fixture (frame["map"]["nodes"]).
Test 4 (red on main): pan away with the arrow keys and zoom out one wheel notch (control: both really moved), press Home, and camera
and scale return to the opening values. Red on main: Home is bound to nothing.
"""
import time

import pytest

from play_support import RESOLUTION, moment, qa

W, H = (int(v) for v in RESOLUTION.split("x"))
UNIT_HALF = 12.0  # UNIT_SIZE / 2 (the sprite half-size of the existing predicate, tests/test_tactical_camera.gd _not_inside)
PROJECT_TOL_PX = 1.5  # the brief's tolerance for the project verb against units_px
# G2 (Architect 2026-10-12): 10% of the viewport per side. spec Rev 12d A18, DRAFT-a18-margin (untagged in the spec)
MARGIN_FRAC = 0.1
MARGIN_TOL_PX = 1.5  # float slack on the fitted edge, the same 1.5 px as the project agreement
HOME_KEY = "Home"  # G4: KEY_HOME, DRAFT-a18-home-key
HOME_TOL = 1e-3  # JSON float round trip of the stored camera and scale


def _own(q):
    me = q["local_faction"]
    return {uid: u for uid, u in q["units"].items() if u["faction"] == me}


def _premises(q):
    own = _own(q)
    xs = [u["x"] for u in own.values()]
    ys = [u["y"] for u in own.values()]
    return ("premises: local_faction %r, own units %d of %d, units_px %d, canvas %r, tick %r, camera %r, scale %r, own world box "
            "x %.0f..%.0f y %.0f..%.0f, settlement_lots %r, map.nodes not in qa_state (objects_px %r)" % (
                q["local_faction"], len(own), len(q["units"]), len(q["units_px"]), q["canvas"], q["tick"], q["camera"], q["scale"],
                min(xs) if xs else 0, max(xs) if xs else 0, min(ys) if ys else 0, max(ys) if ys else 0,
                q["settlement_lots"], q.get("objects_px")))


@pytest.fixture(scope="module")
def opening(tactical_game):
    """The opening frame, read before anything touches the camera."""
    q = qa(tactical_game.client)
    print("S-103 " + _premises(q))
    return q


def test_s_103_control_project_agrees_with_units_px(tactical_game, opening):
    client = tactical_game.client
    assert opening["units_px"], "S-103 CONTROL: units_px is empty; %s" % _premises(opening)
    own = _own(opening)
    assert own, "S-103 CONTROL: no own unit (faction == local_faction); %s" % _premises(opening)
    uid = sorted(own, key=lambda k: int(k))[0]
    assert uid in opening["units_px"], "S-103 CONTROL: own unit %s is not in units_px; %s" % (uid, _premises(opening))
    r = client.call("project", float(own[uid]["x"]), float(own[uid]["y"]))
    assert r.get("ok") is True, "S-103 CONTROL: the project verb refused: %r" % r
    px, py = opening["units_px"][uid]
    d = max(abs(r["result"]["x"] - px), abs(r["result"]["y"] - py))
    assert d <= PROJECT_TOL_PX, "S-103 CONTROL: project(%s) = (%.1f, %.1f) but units_px = (%.1f, %.1f)" % (uid, r["result"]["x"], r["result"]["y"], px, py)


def test_s_103_opening_frame_own_units_inside(tactical_game, opening):
    client = tactical_game.client
    moment(client, "S-103", "start_view")  # the queued shot, taken at the opening frame before any input
    q = opening
    own = _own(q)
    prem = _premises(q)
    assert own, "S-103: no own unit to frame; %s" % prem
    px = q["units_px"]
    missing = sorted(uid for uid in own if uid not in px)
    outside = sorted(uid for uid in own if uid in px
                     and not (UNIT_HALF <= px[uid][0] <= W - UNIT_HALF and UNIT_HALF <= px[uid][1] <= H - UNIT_HALF))
    assert not missing and not outside, (
        "S-103 R-103-01 (A18, Architect 2026-10-12 G7 own units only): %d of %d own units are not fully inside the %dx%d viewport at the opening "
        "frame (px +- %d): %d absent from units_px, %d outside; first outside %s; %s" % (
            len(missing) + len(outside), len(own), W, H, int(UNIT_HALF), len(missing), len(outside),
            [(u, [round(v, 1) for v in px[u]]) for u in outside[:3]], prem))


def test_s_103_opening_frame_lots_spawn_and_margin(tactical_game, opening):
    client = tactical_game.client
    q = opening
    own = _own(q)
    prem = _premises(q)
    px = q["units_px"]
    assert own, "S-103: no own unit to frame; %s" % prem
    # the own lots (lot clause; vacuous on the live mission, see the docstring)
    lots = [l for l in q["settlement_lots"] if l.get("owner") == q["local_faction"]]
    for lot in lots:
        r = client.call("project", float(lot["x"]), float(lot["y"]))
        assert r.get("ok") is True and r["result"]["on_screen"], (
            "S-103 R-103-01 (A18): own lot %r does not project on screen (%r); %s" % (lot, r, prem))
    if not lots:
        print("S-103: the lot clause is vacuous on the live mission (0 own lots in settlement_lots); proven by the GD fixture")
    # G3: the spawn point on screen; the own-unit centroid stands in for the kind-7 node (liberty 2026-10-12, see the docstring)
    cx = sum(u["x"] for u in own.values()) / len(own)
    cy = sum(u["y"] for u in own.values()) / len(own)
    r = client.call("project", float(cx), float(cy))
    assert r.get("ok") is True and r["result"]["on_screen"], (
        "S-103 R-246-07 (A18, G3 spawn point; own-unit centroid as the stand-in): (%.0f, %.0f) projects to %r; %s" % (cx, cy, r, prem))
    # G2: the margin of 10% of the viewport per side holds for the own units' px box
    xs = [px[u][0] for u in own if u in px]
    ys = [px[u][1] for u in own if u in px]
    mx, my = MARGIN_FRAC * W, MARGIN_FRAC * H
    box = (min(xs), min(ys), max(xs), max(ys))
    assert (box[0] >= mx - MARGIN_TOL_PX and box[1] >= my - MARGIN_TOL_PX and box[2] <= W - mx + MARGIN_TOL_PX and box[3] <= H - my + MARGIN_TOL_PX), (
        "S-103 R-103-01 (A18, G2 a margin of 10%% of the viewport per side, DRAFT-a18-margin): the own units' px box %s is not inside "
        "(%.0f, %.0f)..(%.0f, %.0f); %s" % ([round(v, 1) for v in box], mx, my, W - mx, H - my, prem))


def _hold(client, key, until, cap_s):
    """Holds a key down until pred(qa) is true or cap_s wall seconds pass; always releases."""
    client.call("input", "key_down", key)
    try:
        t0 = time.monotonic()
        while time.monotonic() - t0 < cap_s:
            time.sleep(0.2)  # harness wait: 2 to 4 software fps
            if until(qa(client)):
                break
    finally:
        client.call("input", "key_up", key)


def test_s_103_home_key_returns_to_the_opening_view(tactical_game, opening):
    client = tactical_game.client
    cam0, scale0 = dict(opening["camera"]), opening["scale"]
    client.call("input", "move", W // 2, H // 2)  # off the edge-scroll margin; the wheel acts at the pointer
    _hold(client, "Left", lambda q: abs(q["camera"]["x"] - cam0["x"]) >= 200.0, 20.0)
    client.call("input", "wheel", -1)  # one notch out
    time.sleep(0.5)
    away = qa(client)
    assert abs(away["camera"]["x"] - cam0["x"]) >= 100.0, "S-103 CONTROL: the Left key did not pan the camera (%r from %r)" % (away["camera"], cam0)
    assert abs(away["scale"] - scale0) > HOME_TOL, "S-103 CONTROL: the wheel did not change the scale (%r from %r)" % (away["scale"], scale0)
    client.call("input", "key", HOME_KEY)  # G4: KEY_HOME
    back = away
    for _ in range(15):
        time.sleep(0.2)
        back = qa(client)
        if abs(back["camera"]["x"] - cam0["x"]) <= HOME_TOL and abs(back["camera"]["y"] - cam0["y"]) <= HOME_TOL:
            break
    assert (abs(back["camera"]["x"] - cam0["x"]) <= HOME_TOL and abs(back["camera"]["y"] - cam0["y"]) <= HOME_TOL
            and abs(back["scale"] - scale0) <= HOME_TOL), (
        "S-103 R-103-01 (A18, G4 home key %s, DRAFT-a18-home-key): after panning away to %r at scale %r the home key left camera %r scale %r; "
        "the opening values were camera %r scale %r" % (HOME_KEY, away["camera"], away["scale"], back["camera"], back["scale"], cam0, scale0))
