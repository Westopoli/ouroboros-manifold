"""look-judge-rig fixes, defect 6 (measurement 2026-11-24): the sidecar x, y is a unit's ground point and the glyph is drawn about 5.5 px above it, so `check_position` failed
every real frame at 2 px. Spec piece 3: "samples pixels at sidecar positions"; check_position: "each unit's ID-colour centroid lies within max_offset_px of its sidecar x, y".

Decision (smaller change, reported): the sidecar carries the glyph centre. Changing the check instead would break the synthetic tests of test_render_checks.py (they paint at the
sidecar position and expect PASS) and the offset differs per view (about 5.0 px in slice a, 4.6 in slice c), so a constant in the check cannot be right. The change is in
scenes/proto/fight_replay/replay_sidecar.gd; the proof is tests/qa/test_replay_sidecar_glyph_centre.py, which renders. This file holds the Python-side control: the recorded
frames in tests/look/fixtures/slice_* were written before the fix and still show the ground-point offset.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
FIX = ROOT / "tests" / "look" / "fixtures"


def centroid_offsets(png):
    sc = json.loads(png.with_name(png.name.replace(".id.png", ".json")).read_text())
    img = np.array(Image.open(png).convert("RGB"))
    out = []
    for u in sc["units"]:
        ys, xs = np.nonzero((img == tuple(int(u["colour"][k:k + 2], 16) for k in (1, 3, 5))).all(axis=2))
        if len(xs):
            out.append((xs.mean() - u["x"], ys.mean() - u["y"]))
    return np.array(out)


@pytest.mark.parametrize("slice_name,frame", [("slice_a", 10), ("slice_b", 10), ("slice_c", 10)])
def test_control_recorded_frames_show_a_ground_point_offset_and_fail_the_2px_check(slice_name, frame):
    """Positive control (green today, defect 6): in the recorded frames the glyph centroid sits a steady 3..8 px above the sidecar point (median dy) with dx near 0, and
    check_position at 2 px FAILs: the harness reads the real frames; what is missing is the sidecar carrying the glyph centre (see tests/qa/test_replay_sidecar_glyph_centre.py)."""
    from scripts.look import render_checks
    png = FIX / slice_name / ("frame-%d.id.png" % frame)
    o = centroid_offsets(png)
    assert -8 < np.median(o[:, 1]) < -3 and abs(np.median(o[:, 0])) < 2
    assert render_checks.check_position(png, max_offset_px=2.0)["verdict"] == "FAIL"
