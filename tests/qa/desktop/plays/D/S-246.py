"""S-246 play: the space landscape as stacked 3D sheets with the vision tube (R-246-02, R-246-03, R-246-04, Q-009-02).

Launches the real game in the default (space) era, walks menu -> tactical like a player, then reads the qa_state `space3d`
block (draft pin shared with tests/test_vg_d_d7.gd: {present, layers, layer_y, sheets, meteors, tube: {active, radius,
foci, cut_layers}, occlusion_marks, cue: {own, other}}). Evidence goes to docs/northstar/story_reviews/shots/<run id>/ via
the lane C driver (plays/C/_play.py: screenshot plus qa json). Moments: 'sheets' (five layers 1000 wu apart, plates and
meteors drawn), 'tube' (a click on a unit puts a tube on it; layers above its layer are cut; no occlusion mark).
CONTROL: a ground-era game has no space3d block (present false), so the detector is not always true.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[1] / "C"))   # reuse lane C's evidence driver (this lane owns no _play.py)
import _play  # noqa: E402
from daemon_client import GodotGame, pick_free_port  # noqa: E402
from test_tactical_play import _to_tactical  # noqa: E402


def _start(era=None) -> GodotGame:
    extra = ["--era", era] if era else []
    g = GodotGame(qa_port=pick_free_port(), seed=1, resolution="1920x1080", extra_args=extra)
    g.start()
    g.wait_for_port(timeout=60.0)
    _to_tactical(g)
    return g


def _space3d(game: GodotGame) -> dict:
    q = _play.qa(game)
    s = q.get("space3d")
    assert isinstance(s, dict) and s.get("present"), (
        "qa_state.space3d missing or not present (the space field is not drawn); qa keys = %s" % sorted(q))
    return s


@pytest.fixture(scope="module")
def game():
    g = _start()
    try:
        yield g
    finally:
        g.stop()


def test_s246_five_separated_sheets_with_meteors(game):
    s = _space3d(game)
    _play.evidence(game, "s246", "sheets")
    assert s["layers"] == 5, "R-001-04: %r layers" % s["layers"]
    ys = [float(v) for v in s["layer_y"]]
    assert ys == [0.0, 1000.0, 2000.0, 3000.0, 4000.0], "R-246-02: layers not (k-1) x 1000 wu apart: %r" % ys
    assert s["sheets"] >= 5, "R-246-03: only %r sheet meshes drawn" % s["sheets"]
    assert s["meteors"] > 0, "R-246-02: no placeholder meteors fill the blocked space"
    assert s["occlusion_marks"] == 0, "Q-009-02: an occlusion mark is drawn"


def test_s246_a_selected_unit_gets_a_vision_tube(game):
    s = _space3d(game)
    assert not s["tube"]["active"], "CONTROL: a tube is active before anything is selected"
    units = _play.qa(game).get("units_px", {})
    assert units, "no units_px to click"
    uid = sorted(units)[0]
    x, y = _play.px(units[uid])
    game.client.click(x, y)
    _play.step(game, 1)
    s = _space3d(game)
    _play.evidence(game, "s246", "tube")
    t = s["tube"]
    assert t["active"] and t["radius"] > 0, "R-246-04: clicking a unit put no tube on it: %r" % t
    assert t.get("foci"), "R-246-04: the tube has no focus (cursor or selection)"
    top = max(int(f["layer"]) for f in t["foci"])
    assert sorted(int(c) for c in t["cut_layers"]) == list(range(top + 1, 5)), (
        "R-246-04: cut layers %r are not exactly the layers above focus layer %r" % (t["cut_layers"], top))
    assert s["occlusion_marks"] == 0, "Q-009-02: an occlusion mark is drawn beside the tube"


def test_s246_control_ground_era_has_no_space_sheets():
    g = _start("greek_placeholder")
    try:
        s = _play.qa(g).get("space3d", {})
        assert not (isinstance(s, dict) and s.get("present")), "CONTROL: a ground era reports space sheets: %r" % s
    finally:
        g.stop()
