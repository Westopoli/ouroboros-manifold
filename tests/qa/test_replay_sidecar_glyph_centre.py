"""Look-judge rig fixes, defect 6 (measurement 2026-11-24). Spec piece 3 (docs/northstar/plans/cascades/look-judge-rig/spec.md): "frame-<i>.json beside each frame-<i>.png (every
unit: id, side, screen x, y, radius px, colour)" and render_checks.check_position: "each unit's ID-colour centroid lies within max_offset_px of its sidecar x, y".

The sidecar x, y was each unit's ground point; the drawn glyph centroid sits about 5 px above it, so every frame failed the 2 px check. The pinned fix: the sidecar x, y is the glyph
centre. Rendered here as tests/qa/test_replay_sidecar.py renders (GodotGame, private Xvfb, software GL), on the 18-frame real fight tests/look/fixtures/slice_a/fight.json (L-0083
ticks 495..512, 72 units; premises dumped 2026-11-24: 18 frames, per-unit centroid offset from the old sidecar dx +1.1, dy -5.0, std 0.6).

The per-unit worst case is not asserted: the glyph is not a disc (it fills 55-60 percent of the sidecar disc) and the worst isolated unit stays about 3.5 px off even after the mean
offset is removed, so a "every unit within 2 px" assertion could not be satisfied by any sidecar. The median over units with no neighbour within three radii is the robust statistic;
the 2 px is the stand-in for Westley's DRAFT-look-position-offset-px (see tests/look/test_render_checks.py).
"""
from __future__ import annotations

import json
import math
import shutil
import statistics
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tests" / "qa" / "desktop"))
sys.path.insert(0, str(ROOT))

from daemon_client import GodotGame, pick_free_port  # noqa: E402

SCENE = "res://scenes/proto/fight_replay/fight_replay.tscn"
FIGHT = ROOT / "tests/look/fixtures/slice_a/fight.json"
N_FRAMES = 18
DRAFT_OFFSET_PX = 2.0  # DRAFT-look-position-offset-px, stand-in for Westley's number
QUIT_TIMEOUT = 600  # harness bound only

pytestmark = pytest.mark.skipif(
    not (shutil.which("godot") or shutil.which("godot4")) or not shutil.which("xvfb-run"),
    reason="needs godot and xvfb-run (the replay scene runs under a private Xvfb)",
)


class ReplayGame(GodotGame):
    def godot_args(self, godot: str = "godot") -> list[str]:
        args = super().godot_args(godot)
        args.insert(args.index("--"), SCENE)
        return args


@pytest.fixture(scope="module")
def shots(tmp_path_factory):
    out = tmp_path_factory.mktemp("glyph_centre_shots")
    mp = pytest.MonkeyPatch()
    try:
        mp.setenv("OM_FIGHT", str(FIGHT))
        mp.setenv("OM_SHOT_OUT", str(out))
        mp.setenv("OM_ID_RENDER", "1")
        mp.delenv("OM_AUTOPLAY", raising=False)
        mp.delenv("OM_LAYOUT", raising=False)
        g = ReplayGame(qa_port=pick_free_port(), seed=1, resolution="1920x1080")
        g.start()
        try:
            try:
                g.proc.wait(timeout=QUIT_TIMEOUT)
            except subprocess.TimeoutExpired:
                pytest.fail("the scene did not quit after saving frames; stderr tail:\n" + g.stderr_tail())
        finally:
            g.stop()
    finally:
        mp.undo()
    return out


def test_control_the_fixture_fight_and_the_render_exist(shots):
    """Positive control (green today): the 18-frame fixture fight renders 18 sidecars and ID images, each sidecar listing 72 units, so a red below is the offset and not the render."""
    assert len(json.loads(FIGHT.read_text())["frames"]) == N_FRAMES
    for i in range(N_FRAMES):
        sc = json.loads((shots / ("frame-%d.json" % i)).read_text())
        assert (shots / ("frame-%d.id.png" % i)).exists() and len(sc["units"]) == 72


def test_sidecar_position_is_the_glyph_centre(shots):
    """Spec piece 3 check_position "each unit's ID-colour centroid lies within max_offset_px of its sidecar x, y": over frames 0, 5, 10, 15 and every unit with no other unit within
    three radii (premise: at least 20 such units), the median distance from the ID-colour centroid to the sidecar x, y is within 2 px (today about 5)."""
    from PIL import Image
    offs = []
    for i in (0, 5, 10, 15):
        sc = json.loads((shots / ("frame-%d.json" % i)).read_text())
        img = np.array(Image.open(shots / ("frame-%d.id.png" % i)).convert("RGB"))
        us = sc["units"]
        for u in us:
            if any(v is not u and math.hypot(v["x"] - u["x"], v["y"] - u["y"]) < 3 * u["radius"] for v in us):
                continue
            ys, xs = np.nonzero((img == tuple(int(u["colour"][k:k + 2], 16) for k in (1, 3, 5))).all(axis=2))
            if len(xs):
                offs.append(math.hypot(xs.mean() - u["x"], ys.mean() - u["y"]))
    assert len(offs) >= 20, "premise: only %d isolated units sampled" % len(offs)
    assert statistics.median(offs) <= DRAFT_OFFSET_PX, "median offset %.2f px over %d isolated units" % (statistics.median(offs), len(offs))
