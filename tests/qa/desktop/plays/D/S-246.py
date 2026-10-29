"""Story play S-246 "In space each layer is a sheet of open and blocked space with real obstacles filling it, and the layers
sit visibly apart." Rules R-246-01 (generated field, five open-or-blocked sheets), R-246-02 (real obstacles fill the sheets, the
layers are visibly separated), R-246-03 (the client draws the layers as stacked 3D sheets from the masks and plate polygons the
sim sent once), R-246-04 (the vision tube and the layer indicators: "Given a unit below an upper layer that hides it from the
camera, When the player looks, Then a simple vision tube lets the player see through the covering layers around the cursor or
selection, with a small effect that says so (Q-S3-01); the layer-visibility system of the layers prototype ... is the one the
spec follows (Q-S3-02)", with a ring at the unit's layer and a second ring on the layer it is moving to). Westley 2026-10-13
(Q-S3-01 (a), Q-246-01 (a) gap 1,000 wu): the space kit approval is conditional on the vision tube and on layer indicators
showing which layer each unit is on, both in lane D's first shot. Spec: docs/northstar/plans/2026-10-13-d-view-spec.md (VG-D-VIEW,
Play bullet) with the Architect's gap rulings G1 (opt-in hosting), G2 (camera height 5,400, the play zooms out), G3 (2D bodies hidden)
and the null actions of G4 to G10 (rev 1); kit-mode spec sections 4 and P2.5.

The moment: the real game in the space era (no --era; the default era), seed 1, 1920x1080, Forward+ (this play must be run with
OM_QA_RENDERER=vulkan in the run line; the fixture also sets it when unset), hosting opted in with OM_SPACE_VIEW=1 (set by the
fixture for the game process only; G1: the default space era stays 2D until Westley approves the shot). After the first tactical
frame one part of the army is boxed and sent to engine layer 2 with the strip's "To layer 3" button (ToLayer2), another part to
engine layer 4 with "To layer 5" (ToLayer4); the play waits for arrival, zooms out through the wheel until the rig reports a
height of 5,400 (G2, 8 notches of 300 from 3,000), and puts the cursor on the focus-sheet screen position of the own-unit centroid (the pan target, Architect 2026-10-14) so the tube opens on the sheets above, centred on the army. The shot
S-246.png and S-246.json are written to docs/northstar/story_reviews/shots/<run id>/ by this play itself.

Control (green today): qa units_px is non-empty and the daemon "project" verb of one own unit lands within 1.5 px of its units_px
entry (both come from the view's one projection).
Not run: the ground variant (the ground era is untouched; the helper's OM_PLAY_ERA=ground boots a different mission, whose qa has
no space field, so there is no extra check here beyond the present:false control the 2D tests already hold). No "no 2D unit drawn
twice" check (G3): the qa inventory counts squad models, not visibility, so it cannot show a double draw.
Control groups: VG-A-startforce has not landed on this base (qa_state has no group key), so the play takes the box path and says
which path ran.
Rule pins: R-246-01@7374f6, R-246-02@a02180, R-246-03@0bdc9c, R-246-04@837f23
Red on main: qa["space3d"] is absent (the view is not hosted, the default space era is 2D), the control above and the whole
motion (boxes, orders, arrival, zoom skipped) run green first.
"""
import json
import os
import re
import shutil
import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "A"))  # lane A helpers, read-only
from play_support import RUN_ID, SHOT_DIR, qa, start_tactical_game, step_until  # noqa: E402
from daemon_client import control_center, find_control  # noqa: E402

W, H = 1920, 1080
# d-view spec rev 1 / lane D INTERFACE draft numbers (named drafts; Westley owns the thresholds and may veto on the shot)
LAYER_GAP_WU = 1000.0  # DRAFT-space-layer-gap, Q-246-01 (a)
UNIT_LIFT_WU = 150.0  # Units3D FLYER_CLEARANCE_WU (ground_units.gd:11); Architect FINAL 2026-10-14, d-view spec rev 3: unit y = sheet top + 150 (DRAFT-space-unit-lift 40 is struck)
SHEET_THICKNESS_WU = 60.0  # plate sheet (rubble would be 30): space3d.sheets[i] carries no kind, and the sheets in this play are plate sheets
TUBE_RADIUS_WU = 1500.0  # DRAFT-tube-radius
CAM_HEIGHT_WU = 5400.0  # DRAFT-space-cam-height, gap ruling G2 (the play zooms out to it)
FRAME_BUDGET_MS = 16.0  # DRAFT-space-frame-budget: REPORTED beside frame_ms, never asserted (Architect 2026-10-14: FINDING-space-view-frame-time; a later perf piece asserts on a real display)
PROJECT_TOL_PX = 1.5  # the control's tolerance (the brief)
TUBE_TOL_PX = 1.0  # the tube centre against the cursor
TUBE_CENTROID_TOL_WU = TUBE_RADIUS_WU  # the tube centre against the own-unit centroid: within one tube radius (Architect 2026-10-14)
CAM_CENTROID_TOL_WU = 25.0  # DRAFT-pan-centroid: at the first tactical frame the rig target is within this of the own-unit centroid (about 3 px at the start height; Architect 2026-10-14: pan target = centroid)
STRIP_X = 1800  # the To-layer strip sits at x 1840 and up: nothing the play looks at is to the right of it
MARGIN_PX = 80  # units must sit this far inside the screen (the rig's edge-scroll zone is 60 px)


@pytest.fixture(scope="module")
def g():
    saved = {k: os.environ.get(k) for k in ("OM_SPACE_VIEW", "OM_QA_RENDERER")}
    os.environ["OM_SPACE_VIEW"] = "1"  # G1 opt-in, read by tactical_view.gd through OS.get_environment; GodotGame copies os.environ
    os.environ.setdefault("OM_QA_RENDERER", "vulkan")
    game = start_tactical_game()
    try:
        yield game
    finally:
        game.stop()
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


def _own_ids(q):
    me = q["local_faction"]
    return sorted(uid for uid, u in q["units"].items() if u["faction"] == me)


def _box(client, x0, y0, x1, y1):
    """A real drag over the rectangle, clamped 8 px inside the screen (the select_own_by_drag rule)."""
    x0, y0 = int(max(x0, 8)), int(max(y0, 8))
    x1, y1 = int(min(x1, W - 8)), int(min(y1, H - 8))
    client.call("input", "drag", x0, y0, x1, y1)
    time.sleep(0.5)  # harness wait: the selection lands a frame or two after the drag


def _split(pts):
    """pts: {id: [x, y]}. The army is cut at the widest horizontal gap between neighbouring units in the middle 40 percent of the
    x order, so the two boxes cannot share a unit. Returns (x of the cut, padded y0, padded y1, x0, x1)."""
    xs = sorted(p[0] for p in pts.values())
    n = len(xs)
    k = max(range(int(n * 0.3), int(n * 0.7)), key=lambda j: xs[j + 1] - xs[j])
    ys = [p[1] for p in pts.values()]
    return (xs[k] + xs[k + 1]) / 2.0, min(ys) - 8, max(ys) + 8, xs[0] - 8, xs[-1] + 8


def _press(client, name):
    c = find_control(client.tree(), name)
    assert c is not None, "S-246: no %s button in the tree (the strip's To-layer buttons, G8)" % name
    client.click(*control_center(c))
    time.sleep(0.3)  # harness wait


def _arrived(ids, layer):
    def pred(q):
        return all(i in q["units"] and q["units"][i]["layer"] == layer and not (q["units"][i].get("state", 0) & 4) for i in ids)
    return pred


def _centroid(q, own):
    """World centroid (x, y) of the own units in qa units (every own unit, in transit or not)."""
    return (sum(float(q["units"][i]["x"]) for i in own) / len(own), sum(float(q["units"][i]["y"]) for i in own) / len(own))


def _on_screen(p):
    return MARGIN_PX <= p[0] < STRIP_X and MARGIN_PX <= p[1] < H - MARGIN_PX


def _pan_into_view(client, ids):
    """G2 r4: a player edge-scrolls with the pointer (the rig has no camera verb) until every unit of ids is inside the margins.
    liberty 2026-10-12: best-effort pan, bounded at 60 polls; the assertion on units_px afterwards is what decides."""
    for _ in range(60):
        px = qa(client)["units_px"]
        off = [px[i] for i in ids if i in px and not _on_screen(px[i])]
        if not off:
            break
        p = off[0]
        mx = 2 if p[0] < MARGIN_PX else (W - 3 if p[0] >= STRIP_X else W // 2)
        my = 2 if p[1] < MARGIN_PX else (H - 3 if p[1] >= H - MARGIN_PX else H // 2)
        client.call("input", "move", mx, my)
        time.sleep(0.3)  # harness wait: the pan is a screen rate in wall time
    client.call("input", "move", W // 2, H // 2)


def _gpu_line(game):
    for name in ("stdout.log", "stderr.log"):
        path = game.out_dir / name
        if path.exists():
            for line in path.read_text(errors="replace").splitlines():
                if re.search(r"Vulkan|Using Device|OpenGL API|Forward\+", line):
                    return line.strip()
    return "(no renderer line in the daemon log)"


def test_s246_space_sheets_rings_tube(g):
    client = g.client
    q = qa(client)

    # CONTROL, green today: the view's two projections agree for one own unit
    assert q["units_px"], "S-246 CONTROL: qa units_px is empty after the first tactical frame"
    own = _own_ids(q)
    assert own, "S-246 CONTROL: no own unit in qa units (local_faction %r)" % q["local_faction"]
    probe = next(i for i in own if i in q["units_px"])
    r = client.call("project", float(q["units"][probe]["x"]), float(q["units"][probe]["y"]))
    assert r.get("ok") is True, "S-246 CONTROL: the project verb refused: %r" % r
    d = max(abs(r["result"]["x"] - q["units_px"][probe][0]), abs(r["result"]["y"] - q["units_px"][probe][1]))
    print("CONTROL: unit %s project (%.2f, %.2f) vs units_px (%.2f, %.2f), max delta %.3f px" % (
        probe, r["result"]["x"], r["result"]["y"], q["units_px"][probe][0], q["units_px"][probe][1], d))
    assert d <= PROJECT_TOL_PX, "S-246 CONTROL: project and units_px disagree by %.2f px for unit %s" % (d, probe)
    # the rig target at the first tactical frame, kept for the pan assertion after the shot (the player's own panning and the zoom move it later)
    cam0 = (q.get("space3d") or {}).get("camera")
    cen0 = _centroid(q, own)

    # PREMISES, dumped
    groups = {k: v for k, v in q.items() if "group" in k.lower() and k != "ground3d"}
    print("PREMISES: local_faction %r, own units %d of %d, canvas %r, tick %r, camera %r, scale %r, focus_layer %r, space3d %r, control group state %r, units_px %d" % (
        q["local_faction"], len(own), len(q["units"]), q["canvas"], q["tick"], q["camera"], q["scale"], q["focus_layer"],
        q.get("space3d"), groups or "(qa_state has no group key: the box path runs)", len(q["units_px"])))
    assert len(own) >= 2, "S-246 premise: fewer than two own units (%d): two groups cannot be ordered" % len(own)

    # THE ORDERS. Control groups would be keyed 2 and 3 after VG-A-startforce; with no group key in qa the box path runs.
    cut, y0, y1, xa, xb = _split({i: q["units_px"][i] for i in own if i in q["units_px"]})
    _box(client, xa, y0, cut - 1, y1)
    sel2 = sorted(str(i) for i in qa(client)["selected"])
    assert sel2, "S-246 premise: the first box selected nothing"
    _press(client, "ToLayer2")  # text "To layer 3": engine layer 2 (G8)
    _box(client, cut + 1, y0, xb, y1)
    sel4 = sorted(str(i) for i in qa(client)["selected"])
    assert sel4 and not set(sel2) & set(sel4), "S-246 premise: the two boxes overlap or the second selected nothing: %d vs %d units, %r shared" % (
        len(sel2), len(sel4), sorted(set(sel2) & set(sel4)))
    _press(client, "ToLayer4")  # text "To layer 5": engine layer 4 (G8)
    print("ORDERS: path box (no group key in qa), cut at px x %.1f; engine layer 2 <- %d units, engine layer 4 <- %d units" % (cut, len(sel2), len(sel4)))
    ok2 = step_until(client, _arrived(sel2, 2), 1200)
    ok4 = step_until(client, _arrived(sel4, 4), 1200)
    q = qa(client)
    assert ok2, "S-246: group 2 never arrived on layer 2: layers %r" % {i: (q["units"][i]["layer"], q["units"][i].get("state")) for i in sel2}
    assert ok4, "S-246: group 3 never arrived on layer 4: layers %r" % {i: (q["units"][i]["layer"], q["units"][i].get("state")) for i in sel4}

    # THE CAMERA (G2): zoom out through the wheel until the rig reports 5,400, then pan so both groups are in view
    client.call("input", "move", W // 2, H // 2)
    if q.get("space3d", {}).get("present"):
        for _ in range(14):
            if qa(client)["space3d"]["camera"]["height"] >= CAM_HEIGHT_WU:
                break
            client.call("input", "wheel", -1)  # one notch OUT (qa_daemon wheel: n < 0 zooms out)
            time.sleep(0.2)  # harness wait
        _pan_into_view(client, sel2 + sel4)

    # THE CURSOR over the army (Architect 2026-10-14): the SpaceView pan target is the own-unit centroid at ground height, so the army sits at
    # screen centre and the focus sheet under it is sheet 0. The cursor goes to the screen position of the centroid on the FOCUS sheet (the daemon
    # project verb, which uses the focus plane), so the tube is centred on the army. 3 s of wall time for the frame-time average (G9).
    q = qa(client)
    cen = _centroid(q, own)
    r = client.call("project", cen[0], cen[1])
    assert r.get("ok") is True, "S-246: the project verb refused the own-unit centroid %r: %r" % (cen, r)
    cx, cy = int(round(r["result"]["x"])), int(round(r["result"]["y"]))
    print("CENTROID world (%.1f, %.1f) projects on the focus sheet (focus_layer %r) to px (%d, %d); screen centre (%d, %d)" % (
        cen[0], cen[1], q["focus_layer"], cx, cy, W // 2, H // 2))
    client.call("input", "move", cx, cy)
    time.sleep(3.0)  # harness wait: wall time, the frame-time average is over the last 120 frames

    # THE SHOT, written by this play (play_support.moment would name it S-246_<label>)
    src = client.user_dir / "qa" / "S-246.png"
    if src.exists():
        src.unlink()  # a stale file from an earlier run must not be copied
    client.screenshot("S-246")
    SHOT_DIR.mkdir(parents=True, exist_ok=True)
    deadline = time.monotonic() + 5.0
    while not src.exists() and time.monotonic() < deadline:
        time.sleep(0.1)
    assert src.exists(), "S-246: the daemon wrote no screenshot at %s" % src
    shutil.copy(src, SHOT_DIR / "S-246.png")
    state = client.state()["result"]
    (SHOT_DIR / "S-246.json").write_text(json.dumps(state, indent=1, sort_keys=True))
    q = state["qa"]
    print("SHOT: %s (run id %s)" % (SHOT_DIR / "S-246.png", RUN_ID))

    # ASSERTIONS, in the order the spec lists them (qa_state space3d inventory, R-246-04, Q-S3-01, G2)
    s3 = q.get("space3d")
    assert s3 is not None and s3.get("present") is True, "S-246 R-246-03 Q-S3-01: qa_state space3d is %r, not present true (the SpaceView is not hosted: OM_SPACE_VIEW=1, G1)" % (s3,)
    # the frame budget (DRAFT-space-frame-budget): REPORTED, never asserted (Architect 2026-10-14; FINDING-space-view-frame-time)
    gpu = _gpu_line(g)
    ms = s3.get("frame_ms")
    print("FRAME_MS mean %r (draft budget %.1f ms, not asserted); renderer line: %s" % (ms, FRAME_BUDGET_MS, gpu))
    sheets = s3["sheets"]
    assert len(sheets) == 5, "S-246 R-246-01: %d sheets, not 5" % len(sheets)
    assert [s["y"] for s in sheets] == [0.0, 1000.0, 2000.0, 3000.0, 4000.0], "S-246 R-246-02 Q-246-01 (a): sheet y %r, not layer * 1,000 wu (engine layers 0 to 4)" % [s["y"] for s in sheets]
    assert s3["gap_wu"] == LAYER_GAP_WU, "S-246 Q-246-01: gap_wu %r" % s3["gap_wu"]
    for s in sheets:
        print("SHEET layer %d y %.1f blocked_cells %d slabs %d" % (s["layer"], s["y"], s["blocked_cells"], s["slabs"]))
        assert s["blocked_cells"] > 0, "S-246 R-246-01: sheet %d draws no blocked cell" % s["layer"]
        assert s["slabs"] >= 0, "S-246 R-246-02: sheet %d slab count %r" % (s["layer"], s["slabs"])
    # every drawn own unit: a ring on its own layer and y on its sheet (outside transit)
    units3 = s3["units"]
    assert units3, "S-246 R-246-04: space3d.units is empty"
    for uid in own:
        u = q["units"][uid]
        assert uid in units3, "S-246 R-246-04: own unit %s has no entry in space3d.units" % uid
        e = units3[uid]
        assert e["ring_layer"] == u["layer"], "S-246 R-246-04: unit %s ring_layer %r != its layer %r" % (uid, e["ring_layer"], u["layer"])
        if not (u.get("state", 0) & 4):
            sheet_y = u["layer"] * LAYER_GAP_WU
            want_y = sheet_y + SHEET_THICKNESS_WU + UNIT_LIFT_WU
            assert abs(e["y"] - want_y) < 0.01, "S-246 R-246-02: unit %s on layer %d is drawn at y %r, not %r (sheet top + 150 = layer * 1,000 + 60 + 150; layer 2 is 2,210)" % (
                uid, u["layer"], e["y"], want_y)
            assert e["dest_ring_layer"] == -1, "S-246 R-246-04: unit %s is not in transit but shows a destination ring %r" % (uid, e["dest_ring_layer"])
    layers_present = {q["units"][i]["layer"] for i in own}
    assert {2, 4} <= layers_present, "S-246 premise: layers present among own units %r, not both 2 and 4" % sorted(layers_present)
    # the units on layers 4 and 2 are on screen (G2)
    for uid in sel2 + sel4:
        p = q["units_px"].get(uid)
        assert p is not None and 0 <= p[0] < W and 0 <= p[1] < H, "S-246 G2: unit %s (layer %d) is off screen at %r" % (uid, q["units"][uid]["layer"], p)
    cam = s3["camera"]
    print("CAMERA %r" % cam)
    # the pan target is the own-unit centroid at ground height (Architect 2026-10-14), not the kind-7 spawn anchor: read at the first frame
    assert cam0 is not None, "S-246 G2: qa_state space3d.camera is absent at the first tactical frame"
    dpan = ((cam0["x"] - cen0[0]) ** 2 + (cam0["y"] - cen0[1]) ** 2) ** 0.5
    print("PAN at the first frame: rig target (%.1f, %.1f) vs own-unit centroid (%.1f, %.1f): %.1f wu (tolerance %.0f wu)" % (cam0["x"], cam0["y"], cen0[0], cen0[1], dpan, CAM_CENTROID_TOL_WU))
    assert dpan <= CAM_CENTROID_TOL_WU, "S-246 G2 (Architect 2026-10-14): the rig target at the first frame is %.1f wu from the own-unit centroid (tolerance %.0f wu): the pan target is not the centroid" % (dpan, CAM_CENTROID_TOL_WU)
    assert cam["height"] >= CAM_HEIGHT_WU, "S-246 G2: the rig reports height %r, below the 5,400 the play zooms to" % cam["height"]
    # the tube
    tube = s3["tube"]
    focus = q["focus_layer"]
    print("TUBE %r focus_layer %r cursor (%d, %d)" % (tube, focus, cx, cy))
    assert tube["active"] is True, "S-246 R-246-04 Q-S3-01 (a): the tube is not active with the cursor over the army (%r)" % (tube,)
    assert tube["faded_layers"], "S-246 R-246-04 Q-S3-01 (a): tube.faded_layers is empty"
    assert all(l > focus for l in tube["faded_layers"]), "S-246 R-246-04: faded_layers %r holds a layer at or below the focus layer %r" % (tube["faded_layers"], focus)
    assert sorted(tube["faded_layers"]) == list(range(focus + 1, 5)), "S-246 R-246-04: faded_layers %r is not the sheets above the focus layer %r" % (tube["faded_layers"], focus)
    assert tube["radius_wu"] == TUBE_RADIUS_WU, "S-246 DRAFT-tube-radius: radius_wu %r" % tube["radius_wu"]
    # the tube is centred on the army: its centre projects (focus sheet, the daemon project verb) onto the cursor, which was aimed at the
    # own-unit centroid, and lies within one tube radius of that centroid in world units; the centroid sits near the screen centre (pan target)
    r = client.call("project", float(tube["cx"]), float(tube["cy"]))
    assert r.get("ok") is True, "S-246: the project verb refused: %r" % r
    dx, dy = r["result"]["x"] - cx, r["result"]["y"] - cy
    print("TUBE centre projects to (%.2f, %.2f), cursor (%d, %d)" % (r["result"]["x"], r["result"]["y"], cx, cy))
    assert max(abs(dx), abs(dy)) <= TUBE_TOL_PX, "S-246 R-246-04: the tube centre projects %.2f px from the cursor (tolerance %.1f px)" % (max(abs(dx), abs(dy)), TUBE_TOL_PX)
    cen = _centroid(q, own)
    dw = ((tube["cx"] - cen[0]) ** 2 + (tube["cy"] - cen[1]) ** 2) ** 0.5
    print("TUBE centre (%.1f, %.1f) vs own-unit centroid (%.1f, %.1f): %.1f wu (tolerance %.0f wu)" % (tube["cx"], tube["cy"], cen[0], cen[1], dw, TUBE_CENTROID_TOL_WU))
    assert dw <= TUBE_CENTROID_TOL_WU, "S-246 R-246-04: the tube centre is %.1f wu from the own-unit centroid, more than one tube radius (%.0f wu): the tube is not centred on the army" % (dw, TUBE_CENTROID_TOL_WU)
    assert isinstance(ms, (int, float)) and ms > 0.0, "S-246: space3d.frame_ms is %r, no frame sample" % (ms,)
