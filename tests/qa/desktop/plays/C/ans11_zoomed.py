"""Probe for Westley's decision-batch point 11 (2026-10-18): the ground opening frame judged too far out.
Not a story play and not a test of a rule: it frames each own group of the opening force close up, at three camera
heights, so the units, their surrounding landscape and their sight can be read; and it logs the numbers that
explain the scale (screen px per world unit, a unit's drawn width, the sight radius).
Run: OM_RUN_ID=ans11 pytest tests/qa/desktop/plays/C/ans11_zoomed.py -s
See also: scenes/ground3d/camera_rig_3d.gd (heights, bands), scenes/ground3d/ground_units.gd (BODY_RADIUS_WU)."""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _play  # noqa: E402

ZOOM_NOTCH_WU = 300.0
HEIGHTS = [900.0, 600.0, 300.0]


@pytest.fixture(scope="module")
def game():
    g = _play.start_ground_game()
    try:
        yield g
    finally:
        g.stop()


def _groups(q):
    own = [u for u in q["units"].values() if u.get("faction") == q.get("local_faction", 0)]
    groups = []
    for u in own:
        for gp in groups:
            if abs(gp["x"] - u["x"]) < 1500 and abs(gp["y"] - u["y"]) < 1500:
                gp["n"] += 1
                gp["sx"] += u["x"]
                gp["sy"] += u["y"]
                gp["x"], gp["y"] = gp["sx"] / gp["n"], gp["sy"] / gp["n"]
                break
        else:
            groups.append({"x": u["x"], "y": u["y"], "sx": u["x"], "sy": u["y"], "n": 1, "type": u.get("type")})
    return sorted(groups, key=lambda gp: (gp["y"], gp["x"]))


def _cam(game):
    c = _play.ground3d(game)
    return c["camera"]["x"], c["camera"]["y"], c["camera_height"], c["scale"]


def _pan_to(game, x, y):
    r = game.client.call("qa_pan", float(x), float(y))
    assert r.get("ok") is True, "qa_pan refused: %r" % r
    _play.step(game, 2)


def _set_height(game, h):
    """Wheel +1 zooms in, -1 out (plays/C/s236.py); closed loop on camera_height, a notch is 300 wu."""
    for _ in range(40):
        _, _, cur, _ = _cam(game)
        notches = int(round((cur - h) / ZOOM_NOTCH_WU))
        if notches == 0:
            return
        game.client.call("input", "wheel", max(-30, min(30, notches)))
        _play.step(game, 2)


def test_ans11_zoomed_group_shots(game):
    game.client.call("input", "move", 960, 540)  # off the edge-scroll zones
    q = _play.qa(game)
    gs = _groups(q)
    log = {"groups": [{k: gp[k] for k in ("x", "y", "n", "type")} for gp in gs], "shots": []}
    for gi, gp in enumerate(gs):
        for h in HEIGHTS:
            _set_height(game, h)
            _pan_to(game, gp["x"], gp["y"])
            _play.step(game, 2)
            time.sleep(0.4)
            cx, cy, ch, sc = _cam(game)
            name = "g%d_h%d" % (gi + 1, int(round(ch)))
            _play.evidence(game, "ans11", name)
            q = _play.qa(game)
            log["shots"].append({"name": name, "group": gi + 1, "camera": [cx, cy], "height": ch, "px_per_wu": sc,
                                 "band": _play.ground3d(game)["band"],
                                 "inventory_fog_layer": q["inventory"].get("fog_layer")})
    _play.SHOT_DIR.mkdir(parents=True, exist_ok=True)
    (_play.SHOT_DIR / "ans11_log.json").write_text(json.dumps(log, indent=1))
    print(json.dumps(log, indent=1))
