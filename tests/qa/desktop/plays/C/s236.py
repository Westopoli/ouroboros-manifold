"""S-236 play: one camera from a single unit up to the map view, land drawn as real height (R-236-01, R-236-02).
Moment 1 'micro': zoom all the way in, ground3d.band == micro. Moment 2 'map': zoom all the way out, band == map and
camera.scale smaller. The band names are C3's (micro, tactical, map). CONTROL: the two moments' screenshots differ."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _play  # noqa: E402


@pytest.fixture(scope="module")
def game():
    g = _play.start_ground_game()
    try:
        yield g
    finally:
        g.stop()


def test_s236_zoom_range_changes_band_and_scale(game):
    c = game.client
    for _ in range(40):
        c.call("input", "wheel", 1)
    _play.step(game, 2)
    g_in = _play.ground3d(game)
    _play.evidence(game, "s236", "micro")
    assert g_in["band"] == "micro", "R-236-01: fully zoomed in the band is %r, expected micro" % g_in["band"]
    for _ in range(80):
        c.call("input", "wheel", -1)
    _play.step(game, 2)
    g_out = _play.ground3d(game)
    shot = _play.evidence(game, "s236", "map")
    assert g_out["band"] == "map", "R-236-01: fully zoomed out the band is %r, expected map" % g_out["band"]
    assert g_out["scale"] < g_in["scale"], "R-236-01: scale did not fall from micro (%r) to map (%r)" % (g_in["scale"], g_out["scale"])
    micro = (_play.SHOT_DIR / "s236_micro.png").read_bytes()
    assert micro != shot.read_bytes(), "CONTROL: micro and map screenshots are byte-identical, the camera did not move the picture"
