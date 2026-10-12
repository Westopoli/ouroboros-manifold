"""S-004 play: a walker that must climb a slope to reach its ordered place changes layer on the slope. Spec paragraph
"C-s004 play fix" (docs/northstar/plans/2026-10-07-visible-game-spec.md, rev 12, with the Architect rulings of 2026-10-12).
Moment 'transit': select every own unit, send them to the top edge of the nearest slope that starts on their layer
with a move click, step in chunks and watch for a selected unit that is on the slope's upper layer past the midline.

Rules proved, word for word (docs/bible/epics/E-01-layer-system.md):
R-001-05  Given a unit ordered to move to a destination, When its route is planned, Then it takes the route with the shortest travel time to the goal, counting each transfer, across every layer it may use, changing layer along the way wherever that shortens the route (a flying or swimming unit by a timed transfer, a walking unit by a slope, R-001-07), with S-004's time and exposure applying to each change; so a unit on layer 1 ordered to a place on layer 1 crosses layer 2 when layer 2 lies on the shortest route; and Given a destination blocked on every layer the unit may occupy, When the order is issued, Then the unit paths as close as it can and stops; a flying unit ends on the layer it was ordered on, a pending hard transfer stays pending, and a preferred layer is returned to where it is open (provisional, held as runtime settings).
R-004-06  Given a unit on a slope that joins layers L and L+1, When it is at any point along the slope's length, Then its transition progress is its position along the slope, not a timer: below the midline, units on layer L may attack it and units on layer L+1 may not; at or above the midline, units on layer L+1 may attack it and units on layer L may not; the same holds going up or down; on a slope that spans more than two layers the same holds at each cross-over (R-001-06).
R-004-01 is the timed transfer of a flying or swimming unit (state bit 4); a walker on a slope is R-004-06's case and
carries no bit 4, so the detector is the layer and the position, not the state bit.

Where the target comes from (Architect 2026-10-12): the play regenerates the terrain from the mission seed through the
pipe dump (csrc/pipe/pipe_dumps.c terrain_dump) as its oracle; the sim is deterministic, so it is the ground the player
sees. No product change and no new qa_state key. The target is the nearest slope (by the units' centroid) whose bottom
edge lies on the units' band; the click target is that slope's top edge (R-190-03), so the route must cross it.
CONTROLS: c0 the oracle reproduces the game's own units; c3 before the order no unit is in transit; c1 every selected unit
stands on one layer and the picked cell is on another band; c2 the order was accepted and landed in the picked cell."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _play  # noqa: E402

_REPO = Path(__file__).resolve().parents[5]
_hs = importlib.util.spec_from_file_location("long_harness", _REPO / "tests/long/harness.py")
_h = importlib.util.module_from_spec(_hs)
_hs.loader.exec_module(_h)

SCREEN_W, SCREEN_H = 1920, 1080  # _play.start_ground_game resolution
EDGE_MARGIN = 70  # px: camera_rig_3d.gd EDGE_SCROLL_ZONE is 60 (TD-VG-A-9), so a click nearer the edge would scroll
GALAXY_STEPS = 10  # tests/qa/desktop/test_tactical_play.py _to_tactical: client.call("step", 10) before the mission
ALL_WALKING = [0, 1, 1, 1, 2, 1, 3, 1, 4, 1, 5, 1]  # greek_placeholder manifest.json: all six types walk (EraConfig.movement_kinds)


@pytest.fixture(scope="module")
def game():
    g = _play.start_ground_game()
    try:
        yield g
    finally:
        g.stop()


def _own(q):
    f = q.get("local_faction", 0)
    return [i for i, u in q.get("units", {}).items() if u.get("faction") == f]


def _in_transit(q):
    return [i for i, u in q.get("units", {}).items() if int(u.get("state", 0)) & 4]


def _until(pp, kind):
    """Read pipe frames until one of type `kind`; an error frame is a failure."""
    while True:
        f = pp.read_more()
        assert f.get("type") != "error", "oracle pipe answered an error: %r" % (f,)
        if f["type"] == kind:
            return f


def _oracle(seed):
    """(terrain dump, tactical frame) of the game's own mission, regenerated through a second pipe the way the game
    opens it (CBridge.ensure_world then _ensure_mission): set_seed with the default region count and features, the
    galaxy steps, mission_start on a ground era, mission_begin, terrain_dump."""
    pp = _h.Pipe()
    try:
        pp.cmd("set_seed", seed=seed, n_regions=_h.N_REGIONS, features=_h.FEATURES, new_campaign=True)
        pp.cmd("step", n=GALAXY_STEPS)
        _until(pp, "ack")
        pp.cmd("mission_start", faction=0, era_kind=1, movement_kinds=ALL_WALKING)
        _until(pp, "mission")
        pp.cmd("mission_begin")
        tactical = _until(pp, "tactical")
        pp.cmd("terrain_dump")
        return _until(pp, "terrain"), tactical
    finally:
        pp.close()


def _pick_slope(dump, units):
    """The nearest slope (distance from the units' centroid to its bottom edge) whose bottom edge lies on the units' band.
    A unit on engine layer k stands on band k+1 (docs/architecture.md terrain_dump), so the band is layer + 1."""
    n = len(units)
    cx, cy = sum(u["x"] for u in units) / n, sum(u["y"] for u in units) / n
    band = int(units[0]["layer"]) + 1
    cands = [s for s in dump["slopes"] if s["lower_band"] == band]
    assert cands, "gap: no slope starts on band %d for this seed (%d slopes in all)" % (band, len(dump["slopes"]))
    s = min(cands, key=lambda t: (t["x0"] - cx) ** 2 + (t["y0"] - cy) ** 2)
    return s, cx, cy


def test_s004_transit_is_visible(game):
    c = game.client
    q0 = _play.qa(game)
    print("PREMISE qa keys:", sorted(q0))
    g0 = _play.ground3d(game)
    print("PREMISE ground3d keys:", sorted(g0), "cells_w", g0["cells_w"], "cells_h", g0["cells_h"])
    own = _own(q0)
    units = [q0["units"][i] for i in own]
    layers = {}
    for u in units:
        layers[u["layer"]] = layers.get(u["layer"], 0) + 1
    print("PREMISE units", len(q0["units"]), "own", len(own), "local faction", q0.get("local_faction"), "own layers", layers)
    dump, tactical = _oracle(game.seed)
    # c0, the oracle control: the regenerated mission holds the same own units, so it is the same ground
    mine = lambda us: sorted((float(u["x"]), float(u["y"]), int(u["layer"])) for u in us)  # noqa: E731
    pipe_own = [u for u in tactical["units"] if u["faction"] == q0["local_faction"]]
    assert mine(pipe_own) == mine(units), "c0: the oracle mission differs from the game's (own units %d vs %d)" % (len(pipe_own), len(units))
    assert (dump["cells_w"], dump["cells_h"]) == (g0["cells_w"], g0["cells_h"]), "c0: oracle grid %sx%s, game %sx%s" % (
        dump["cells_w"], dump["cells_h"], g0["cells_w"], g0["cells_h"])
    # c3, the control that was here before: nothing is in transit before the order
    assert not _in_transit(q0), "CONTROL: a unit is in transit before any order"
    s, cx, cy = _pick_slope(dump, units)
    cell = float(q0["canvas"]) / dump["cells_w"]
    tcx, tcy = int(s["x1"] // cell), int(s["y1"] // cell)
    bands = bytes.fromhex(dump["bands"])
    band = bands[tcy * dump["cells_w"] + tcx]
    layer = int(units[0]["layer"])
    # c1, the picker control: one layer for every selected unit; the picked cell's band - 1 is another layer
    assert len(layers) == 1, "c1: the selected units stand on several layers %r" % layers
    assert band - 1 != layer, "c1: picked cell (%d,%d) band %d - 1 = layer %d, the units' own layer" % (tcx, tcy, band, layer)
    assert band == s["upper_band"], "c1: picked cell band %d is not the slope's upper band %d" % (band, s["upper_band"])
    r = c.call("project", float(s["x1"]), float(s["y1"]))
    assert r.get("ok") is True, "project verb refused: %r" % (r,)
    pr = r["result"]
    target = (int(min(max(pr["x"], EDGE_MARGIN), SCREEN_W - EDGE_MARGIN)), int(min(max(pr["y"], EDGE_MARGIN), SCREEN_H - EDGE_MARGIN)))
    dist = ((s["x1"] - cx) ** 2 + (s["y1"] - cy) ** 2) ** 0.5
    print("PREMISE slope", s, "centroid", (cx, cy), "picked cell", (tcx, tcy), "band", band, "layer implied", band - 1)
    print("PREMISE project(%s, %s) = %r -> click %r; straight-line wu centroid to cell %.1f (route length not observable)" % (
        s["x1"], s["y1"], pr, target, dist))
    c.call("qa_select", [int(i) for i in own])
    _play.ground3d(game)
    c.call("input", "click", float(target[0]), float(target[1]), 2)
    lc = _play.qa(game).get("last_command", {})
    print("PREMISE last_command after the click:", lc)
    # c2, the click control: the order was accepted and landed in the picked cell, so a red result is not a mis-click
    assert lc.get("ok") is True, "c2: the move order was refused: %r" % (lc,)
    assert int(lc["x"] // cell) == tcx and int(lc["y"] // cell) == tcy, "c2: the click landed at (%s, %s), outside picked cell (%d, %d)" % (
        lc.get("x"), lc.get("y"), tcx, tcy)
    upper = s["upper_band"] - 1  # the engine layer of the slope's upper band
    ax, ay = s["x1"] - s["x0"], s["y1"] - s["y0"]
    seen = None
    for _ in range(40):
        _play.step(game, 25)
        q = _play.qa(game)
        sel = [q["units"][i] for i in own if i in q["units"]]
        past = [u for u in sel if int(u["layer"]) == upper and (u["x"] - s["mx"]) * ax + (u["y"] - s["my"]) * ay >= 0.0]
        print("SAMPLE tick %s layers %s bit4 %d in_transit %s slopes %s past_midline_on_upper %d" % (
            q["tick"], sorted({int(u["layer"]) for u in sel}), len(_in_transit(q)), q["ground3d"]["slope_view"]["in_transit"],
            q["ground3d"]["slope_view"]["slopes"], len(past)))
        if past:
            seen = q
            break
    assert seen is not None, "R-004-06: no selected unit reached layer %d past the slope midline within 1000 ticks of a move to the slope's top edge" % upper
    g = _play.ground3d(game)
    _play.evidence(game, "s004", "transit")
    assert g["slope_view"]["in_transit"] == len(_in_transit(_play.qa(game))), "R-004-01: slope view in_transit %r disagrees with the frame" % g["slope_view"]
