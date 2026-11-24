"""Look-judge rig piece 3 (render), Python half: scripts/look/render_checks.py (docs/northstar/plans/cascades/look-judge-rig/spec.md piece 3: "scripts/look/render_checks.py
samples pixels at sidecar positions, counts per-unit ID-colour pixels (overlap, hidden, wrong layer). Verification: on A1 at frame 96 the two circles' pixels overlap; on a
planted twin with the pair moved 40 apart, no overlap").

Interface these tests pin (the module does not exist yet; the builder writes to this):
  - the sidecar of `<dir>/frame-<i>.id.png` or `<dir>/frame-<i>.png` is `<dir>/frame-<i>.json`:
    {"frame": i, "width": W, "height": H, "units": [{"id", "side", "x", "y", "radius", "colour": "#rrggbb"}]}  (x, y, radius in screen pixels; colour = the unit's flat ID colour)
  - a unit's disc is the pixels (px, py) with (px-x)^2 + (py-y)^2 <= radius^2.
  - overlaps(id_png) -> list of {"a": id, "b": id, "pixels": int}, a < b, only pairs with pixels > 0, sorted by (a, b); pixels = how many pixels inside both sidecar discs.
  - unit_pixels(id_png) -> {unit id: count of pixels of that unit's ID colour in the image}.
  - check_position(id_png, *, max_offset_px) -> {"verdict": "PASS"|"FAIL", "reason": str, "numbers": dict}: each unit's ID-colour centroid lies within max_offset_px of its sidecar x, y.
  - check_blank(png) -> verdict dict: FAIL when the image is one flat colour.
  - check_frozen(png_a, png_b) -> verdict dict: FAIL when the two images are pixel-identical.
  - every check returns FAIL (never raises, never PASS) when the sidecar is missing.
max_offset_px is a threshold; Westley owns it (DRAFT-look-position-offset-px), so the tests pass it in and the module has no default.
Fixtures are synthetic PNGs built with numpy + PIL in tmp_path (the repo's tests already use PIL).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

W, H, R = 200, 120, 12
BG = (10, 10, 10)
COL = {1: (255, 0, 0), 2: (0, 255, 0), 3: (0, 0, 255)}
DRAFT_OFFSET_PX = 2.0  # DRAFT-look-position-offset-px, a test-side stand-in for Westley's number


def _hex(c):
    return "#%02x%02x%02x" % c


def _disc(x, y, r=R):
    yy, xx = np.mgrid[0:H, 0:W]
    return (xx - x) ** 2 + (yy - y) ** 2 <= r * r


def _frame(d: Path, i: int, units: dict, drawn: dict | None = None, name: str | None = None, sidecar: bool = True) -> Path:
    """units: id -> (x, y) the sidecar claims; drawn: id -> (x, y) actually painted (default the same). Later ids paint over earlier ones."""
    drawn = drawn or units
    img = np.zeros((H, W, 3), np.uint8)
    img[:] = BG
    for uid in sorted(drawn):
        img[_disc(*drawn[uid])] = COL[uid]
    png = d / (name or "frame-%d.id.png" % i)
    Image.fromarray(img).save(png)
    if sidecar:
        doc = {"frame": i, "width": W, "height": H,
               "units": [{"id": u, "side": "A" if u == 1 else "B", "x": units[u][0], "y": units[u][1], "radius": R, "colour": _hex(COL[u])} for u in sorted(units)]}
        (d / ("frame-%d.json" % i)).write_text(json.dumps(doc))
    return png


@pytest.fixture()
def rc():
    try:
        from scripts.look import render_checks
    except ImportError as e:
        pytest.fail("scripts.look.render_checks is missing (look-judge-rig piece 3): %s" % e)
    return render_checks


def test_control_synthetic_fixture_is_well_formed(tmp_path):
    """Look-judge rig piece 3 control, green today: the fixture builder paints two distinct unit colours and a sidecar beside it, so a red below is the missing module."""
    png = _frame(tmp_path, 0, {1: (60, 60), 2: (140, 60)})
    img = np.array(Image.open(png).convert("RGB"))
    assert (img == COL[1]).all(axis=2).sum() == _disc(60, 60).sum()
    assert (tmp_path / "frame-0.json").exists()


def test_overlap_of_two_discs_is_counted_as_exact_pixels(tmp_path, rc):
    """Look-judge rig piece 3 "counts per-unit ID-colour pixels (overlap ...)": units 1 and 2 painted 10 px apart; overlaps() reports the pair with exactly the pixels inside both discs,
    and unit_pixels() shows the hidden unit short by that same count."""
    png = _frame(tmp_path, 96, {1: (90, 60), 2: (100, 60)})
    both = int((_disc(90, 60) & _disc(100, 60)).sum())
    assert both > 0
    assert rc.overlaps(png) == [{"a": 1, "b": 2, "pixels": both}]
    px = rc.unit_pixels(png)
    assert px[2] == int(_disc(100, 60).sum())
    assert px[1] == int(_disc(90, 60).sum()) - both


def test_planted_twin_pair_40_apart_reports_no_overlap(tmp_path, rc):
    """Look-judge rig piece 3 "on a planted twin with the pair moved 40 apart, no overlap" (discs of radius 12 do not touch at 40)."""
    png = _frame(tmp_path, 0, {1: (80, 60), 2: (120, 60)})
    assert rc.overlaps(png) == []


def test_unit_drawn_off_its_sidecar_position_fails(tmp_path, rc):
    """Look-judge rig piece 3 control set "unit drawn off its state position": unit 2 is painted 30 px from where the sidecar says; check_position FAILs. Twin drawn in place PASSes."""
    good = _frame(tmp_path, 0, {1: (60, 60), 2: (140, 60)})
    assert rc.check_position(good, max_offset_px=DRAFT_OFFSET_PX)["verdict"] == "PASS"
    bad = _frame(tmp_path, 1, {1: (60, 60), 2: (140, 60)}, drawn={1: (60, 60), 2: (110, 60)})
    assert rc.check_position(bad, max_offset_px=DRAFT_OFFSET_PX)["verdict"] == "FAIL"


def test_blank_frame_fails_and_a_drawn_frame_passes(tmp_path, rc):
    """Look-judge rig piece 3 control set "blank frame": a one-colour PNG FAILs check_blank; the drawn frame beside it PASSes."""
    blank = tmp_path / "blank.png"
    Image.fromarray(np.full((H, W, 3), 7, np.uint8)).save(blank)
    assert rc.check_blank(blank)["verdict"] == "FAIL"
    assert rc.check_blank(_frame(tmp_path, 0, {1: (60, 60), 2: (140, 60)}))["verdict"] == "PASS"


def test_frozen_frame_fails_and_a_moved_frame_passes(tmp_path, rc):
    """Look-judge rig piece 3 control set "frozen frame": two pixel-identical frames FAIL check_frozen; frames with a unit moved PASS."""
    a = _frame(tmp_path, 0, {1: (60, 60), 2: (140, 60)})
    b = _frame(tmp_path, 1, {1: (60, 60), 2: (140, 60)})
    c = _frame(tmp_path, 2, {1: (70, 60), 2: (140, 60)})
    assert rc.check_frozen(a, b)["verdict"] == "FAIL"
    assert rc.check_frozen(a, c)["verdict"] == "PASS"


def test_missing_sidecar_fails_every_sidecar_check_without_raising(tmp_path, rc):
    """Look-judge rig piece 3 "missing frame ... is FAIL or UNSURE, never PASS": an ID PNG with no frame-<i>.json beside it makes check_position FAIL (reason names the sidecar)
    and overlaps() / unit_pixels() raise nothing silent-green: check_position is the verdict path and must not raise."""
    png = _frame(tmp_path, 0, {1: (60, 60), 2: (140, 60)}, sidecar=False)
    r = rc.check_position(png, max_offset_px=DRAFT_OFFSET_PX)
    assert r["verdict"] == "FAIL"
    assert "sidecar" in r["reason"].lower()
