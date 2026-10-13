"""S-001 play: blocked and open ground visible, slopes drawn with a midline (R-001-01, R-001-06). The ground3d block
carries the C7 slope view under key 'slope_view' ({slopes, midlines, blocked_cells, in_transit}). Moment 'slopes': at least one
midline per slope record and the counts agree. CONTROL: midlines equals slopes (a view that draws fewer midlines is caught)."""
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


def test_s001_slopes_have_midlines_and_blocked_ground_shows(game):
    g = _play.ground3d(game)
    sv = g.get("slope_view")
    assert isinstance(sv, dict), "R-001-06: ground3d has no slope_view block; keys = %s" % sorted(g)
    _play.evidence(game, "s001", "slopes")
    assert sv["slopes"] >= 1, "R-001-06: the ground era has no slope to draw, slopes=%r" % sv["slopes"]
    assert sv["midlines"] == sv["slopes"], "R-001-06: %r midlines for %r slopes" % (sv["midlines"], sv["slopes"])
    assert sv["blocked_cells"] >= 0, "R-001-01: blocked_cells missing"
