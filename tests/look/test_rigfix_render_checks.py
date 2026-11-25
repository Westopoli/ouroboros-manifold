"""look-judge-rig fixes, defects 5 and 6 (measurement 2026-11-24, real fights L-0083 and L-0061 rendered at 1920x1080; fixtures in tests/look/fixtures/slice_{a,b,c}).
Spec piece 3 (render): "samples pixels at sidecar positions, counts per-unit ID-colour pixels (overlap, hidden, wrong layer)"; R-097-05 (units standing inside each other) is
judged on the fight file's wu geometry: same layer, living units, closer than one radius (DRAFT-look-radius 15 wu, Westley's, passed in).

Defect 5: `overlaps()` tested sidecar discs of about 9.6 px, ignored layer and alive, and built a full 1920x1080 mask per pair: it flagged 106 of 106 frames, 24 minutes in all.
Interface pinned (the smaller change; the sidecar has no layer or alive and Godot is not touched): `overlaps(id_png, *, fight=None, frame=None, radius_wu=None)`. Called with
`fight` (the fight dict), `frame` (index into fight["frames"], the same i as frame-<i>.id.png) and `radius_wu`, it returns [{"a", "b", ...}] for exactly the living same-layer
pairs closer than radius_wu in that fight frame (a < b, sorted); called with the png alone it keeps the sidecar-disc behaviour of test_render_checks.py.
Defect 6 (position) is in test_rigfix_position_offset.py and tests/qa/test_replay_sidecar_glyph_centre.py.
"""
from __future__ import annotations

import itertools
import json
import math
import sys
import time
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
FIX = ROOT / "tests" / "look" / "fixtures"
RADIUS_WU = 15.0  # DRAFT-look-radius, a test-side stand-in for Westley's number
RUNTIME_BOUND_S = 60.0  # the brief's bound for 41 frames; the measured cost was about 24 minutes for 106


@pytest.fixture()
def rc():
    try:
        from scripts.look import render_checks
    except ImportError as e:
        pytest.fail("scripts.look.render_checks is missing: %s" % e)
    return render_checks


def load(slice_name):
    d = FIX / slice_name
    return d, json.loads((d / "fight.json").read_text())


def truth_pairs(fight, i, radius=RADIUS_WU):
    us = [u for u in fight["frames"][i]["units"] if u["alive"]]
    return {(min(a["id"], b["id"]), max(a["id"], b["id"])) for a, b in itertools.combinations(us, 2)
            if a["layer"] == b["layer"] and math.hypot(a["x"] - b["x"], a["y"] - b["y"]) < radius}


def flagged(rc, d, fight, i, radius=RADIUS_WU):
    return {(r["a"], r["b"]) for r in rc.overlaps(d / ("frame-%d.id.png" % i), fight=fight, frame=i, radius_wu=radius)}


def test_control_premises_of_the_real_slices(rc):
    """Premises dumped (measured 2026-11-24, green today): slice c (L-0061, ticks 600..640, 41 frames) has no same-layer pair under 15 wu, though 32 and 46 are 14.2 wu apart
    on different layers; slice a (L-0083, 18 frames from tick 495) has 35/69 and 69/70; slice b (L-0083 frames 5..22 of the tick 820 slice) has 47/71, 48/71 and 35/60. Today's
    sidecar-disc `overlaps(png)` flags the clean frame of slice c anyway: that is the defect."""
    d, c = load("slice_c")
    assert len(c["frames"]) == 41 and all(not truth_pairs(c, i) for i in range(41))
    f16 = {u["id"]: u for u in c["frames"][16]["units"]}
    assert f16[32]["layer"] != f16[46]["layer"] and math.hypot(f16[32]["x"] - f16[46]["x"], f16[32]["y"] - f16[46]["y"]) < 15
    d, a = load("slice_a")
    assert set().union(*(truth_pairs(a, i) for i in range(18))) == {(35, 69), (69, 70)}
    assert {i for i in range(18) if (35, 69) in truth_pairs(a, i)} == {9, 10, 11, 12} and {i for i in range(18) if (69, 70) in truth_pairs(a, i)} == {14, 15}
    d, b = load("slice_b")
    assert set().union(*(truth_pairs(b, i) for i in range(5, 23))) == {(47, 71), (48, 71), (35, 60)}
    assert rc.overlaps(FIX / "slice_c" / "frame-0.id.png"), "premise: the sidecar discs alone flag a frame with no overlapping pair"


def test_slice_c_clean_fight_raises_no_overlap_flag_fast(rc):
    """R-097-05 / spec piece 3: on slice c (no pair under 15 wu on one layer; the 14.2 wu pair 32/46 is on two layers) not one of 41 frames flags, inside the runtime bound."""
    d, c = load("slice_c")
    t0 = time.monotonic()
    got = {i: flagged(rc, d, c, i) for i in range(41)}
    took = time.monotonic() - t0
    assert {i: p for i, p in got.items() if p} == {}
    assert took < RUNTIME_BOUND_S, "41 frames took %.1f s" % took


@pytest.mark.parametrize("slice_name,frames", [("slice_a", range(18)), ("slice_b", range(5, 23))])
def test_slices_a_and_b_flag_exactly_the_pairs_under_15_wu(rc, slice_name, frames):
    """R-097-05 / spec piece 3: per frame, the flagged pairs equal the fight file's living same-layer pairs under 15 wu (a: 35/69 at frames 9..12 and 69/70 at 14..15; b: 47/71,
    48/71, 35/60), never more, never fewer."""
    d, fight = load(slice_name)
    wrong = {i: (sorted(flagged(rc, d, fight, i)), sorted(truth_pairs(fight, i))) for i in frames if flagged(rc, d, fight, i) != truth_pairs(fight, i)}
    assert wrong == {}


def _planted(tmp_path, units, fight_units, frame=0):
    """A 200x120 flat PNG, a sidecar for `units` (id -> (x, y)), and a one-frame fight dict with `fight_units`."""
    png = tmp_path / ("frame-%d.id.png" % frame)
    Image.fromarray(np.full((120, 200, 3), 10, np.uint8)).save(png)
    side = {"frame": frame, "width": 200, "height": 120,
            "units": [{"id": i, "side": "A", "x": x, "y": y, "radius": 9.6, "colour": "#%02x%02x%02x" % (60 + 27 * i, 60, 60)} for i, (x, y) in units.items()]}
    (tmp_path / ("frame-%d.json" % frame)).write_text(json.dumps(side))
    fu = [{"id": i, "side": "A", "role": "Vanguard", "layer": lay, "x": x, "y": y, "hp": 100.0, "alive": al, "facing": 0.0, "fired": False, "target": None}
          for i, x, y, lay, al in fight_units]
    return png, {"schema": "om-fight-2", "frames": [{"tick": 0, "alive": [len(fu), 0], "units": fu}]}


def test_dead_other_layer_and_far_pairs_never_flag(rc, tmp_path):
    """R-097-05 "same layer, living units": of four close-looking pairs (the sidecar discs all touch), only the living same-layer pair under 15 wu flags: 1/2 flags; 3/4 has a dead
    unit, 5/6 sit on different layers, 7/8 are 20 wu apart."""
    pos = {1: (20, 20), 2: (26, 20), 3: (60, 20), 4: (66, 20), 5: (100, 20), 6: (106, 20), 7: (140, 20), 8: (146, 20)}
    wu = {1: (0, 0), 2: (10, 0), 3: (100, 0), 4: (108, 0), 5: (200, 0), 6: (208, 0), 7: (300, 0), 8: (320, 0)}
    fu = [(1, *wu[1], 0, True), (2, *wu[2], 0, True), (3, *wu[3], 0, False), (4, *wu[4], 0, True),
          (5, *wu[5], 0, True), (6, *wu[6], 1, True), (7, *wu[7], 0, True), (8, *wu[8], 0, True)]
    png, fight = _planted(tmp_path, pos, fu)
    assert flagged(rc, tmp_path, fight, 0) == {(1, 2)}


def test_the_radius_is_the_callers_number(rc, tmp_path):
    """Spec: the overlap radius is Westley's (DRAFT-look-radius) and is passed in: a pair 20 wu apart flags at radius 25 and not at 15."""
    png, fight = _planted(tmp_path, {1: (20, 20), 2: (26, 20)}, [(1, 0, 0, 0, True), (2, 20, 0, 0, True)])
    assert flagged(rc, tmp_path, fight, 0, 15.0) == set()
    assert flagged(rc, tmp_path, fight, 0, 25.0) == {(1, 2)}
