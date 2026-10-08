"""VG-C piece C9, PARKED (Westley's number): the `look` regression for the ground view (spec section 4 and rev 4 0b:
warn-only until the threshold lands; compared with main's frame at the same play moment, a candidate may not be blanker
than main). LOOK_MIN_NONBLANK_FRACTION is Westley's and stays None until he sets it. Red today: qa_state has no
`ground3d` (the 3D ground is not drawn). After the build it stays red until the number is set.
CONTROL: a uniform image has non-blank fraction 0 and would fail any positive threshold."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _play  # noqa: E402

LOOK_MIN_NONBLANK_FRACTION = None


def _nonblank_fraction(path) -> float:
    a = np.asarray(Image.open(path).convert("RGB")).astype(int)
    med = np.median(a.reshape(-1, 3), axis=0)
    return float((np.abs(a - med).sum(axis=2) > 24).mean())


@pytest.fixture(scope="module")
def game():
    g = _play.start_ground_game()
    try:
        yield g
    finally:
        g.stop()


def test_c9_look_metric_against_westleys_threshold(game, tmp_path):
    blank = tmp_path / "blank.png"
    Image.new("RGB", (64, 64), (90, 90, 90)).save(blank)
    assert _nonblank_fraction(blank) == 0.0, "CONTROL: a uniform image has non-blank pixels"
    _play.ground3d(game)
    shot = _play.evidence(game, "c9", "look")
    frac = _nonblank_fraction(shot)
    print("C9 look metric: non-blank fraction %.4f" % frac)
    assert LOOK_MIN_NONBLANK_FRACTION is not None, "PARKED: Westley has not set LOOK_MIN_NONBLANK_FRACTION (measured %.4f)" % frac
    assert frac >= LOOK_MIN_NONBLANK_FRACTION, "C9: look %.4f below %.4f" % (frac, LOOK_MIN_NONBLANK_FRACTION)
