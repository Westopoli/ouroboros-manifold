"""Look-judge rig piece 3 (render), Godot half (docs/northstar/plans/cascades/look-judge-rig/spec.md piece 3): "new scenes/proto/fight_replay/replay_sidecar.gd writes
`frame-<i>.json` beside each `frame-<i>.png` (every unit: id, side, screen x, y, radius px, colour) and, behind env `OM_ID_RENDER=1`, a second flat-colour ID render
`frame-<i>.id.png` (each unit one unique flat colour, no effects, no HUD)". "On A1 at frame 96 the two circles' pixels overlap."

Launched as tests/qa/test_fight_replay.py launches the scene (GodotGame: private Xvfb via xvfb-run, software GL, scratch data dir). The spec asks for the capped systemd-run
scope; scripts/play.sh has no systemd-run today, so the harness GodotGame launch is the only pattern in the repo and is used as is (reported).
Sidecar schema pinned: {"frame": i, "width": W, "height": H, "units": [{"id", "side", "x", "y", "radius", "colour": "#rrggbb"}]}; colour is the unit's ID-render colour.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tests" / "qa" / "desktop"))
sys.path.insert(0, str(ROOT))

from daemon_client import GodotGame, pick_free_port  # noqa: E402

SCENE = "res://scenes/proto/fight_replay/fight_replay.tscn"
FIGHT = ROOT / "docs/northstar/story_reviews/westley/look_2026-11-19/A1-stacked-pair-near.fight.json"
QUIT_TIMEOUT = 600  # harness bound only
N_FRAMES = 201

pytestmark = pytest.mark.skipif(
    not (shutil.which("godot") or shutil.which("godot4")) or not shutil.which("xvfb-run"),
    reason="needs godot and xvfb-run (the replay scene runs under a private Xvfb)",
)


class ReplayGame(GodotGame):
    def godot_args(self, godot: str = "godot") -> list[str]:
        args = super().godot_args(godot)
        args.insert(args.index("--"), SCENE)
        return args


def _run(monkeypatch, out: Path, id_render: bool) -> None:
    monkeypatch.setenv("OM_FIGHT", str(FIGHT))
    monkeypatch.setenv("OM_SHOT_OUT", str(out))
    monkeypatch.delenv("OM_AUTOPLAY", raising=False)
    monkeypatch.delenv("OM_LAYOUT", raising=False)
    if id_render:
        monkeypatch.setenv("OM_ID_RENDER", "1")
    else:
        monkeypatch.delenv("OM_ID_RENDER", raising=False)
    g = ReplayGame(qa_port=pick_free_port(), seed=1, resolution="1920x1080")
    g.start()
    try:
        try:
            g.proc.wait(timeout=QUIT_TIMEOUT)
        except subprocess.TimeoutExpired:
            pytest.fail("the scene did not quit after saving frames; stderr tail:\n" + g.stderr_tail())
    finally:
        g.stop()


@pytest.fixture(scope="module")
def shots(tmp_path_factory):
    mp = pytest.MonkeyPatch()
    out = tmp_path_factory.mktemp("sidecar_shots")
    try:
        _run(mp, out, id_render=True)
    finally:
        mp.undo()
    return out


def _sidecar(shots: Path, i: int) -> dict:
    p = shots / ("frame-%d.json" % i)
    assert p.exists(), "no frame-%d.json beside frame-%d.png (replay_sidecar.gd missing or not wired); dir: %s" % (i, i, sorted(x.name for x in shots.iterdir())[:8])
    return json.loads(p.read_text())


def test_control_a1_fight_file_has_the_frames_and_units_the_tests_rely_on():
    """Look-judge rig piece 3 control, green today: A1 has 201 frames and frame 96 is tick 1396 with 250 units (premise dumped, not assumed)."""
    doc = json.loads(FIGHT.read_text())
    assert len(doc["frames"]) == N_FRAMES
    assert doc["frames"][96]["tick"] == 1396


def test_sidecar_json_beside_every_png_lists_every_unit(shots):
    """Look-judge rig piece 3 "writes frame-<i>.json beside each frame-<i>.png (every unit: id, side, screen x, y, radius px, colour)": for each of the 201 frames the sidecar
    holds every unit of the fight file's frame (ids equal, sides equal) with numeric x, y, radius > 0 and a #rrggbb colour."""
    doc = json.loads(FIGHT.read_text())
    for i in range(N_FRAMES):
        assert (shots / ("frame-%d.png" % i)).exists(), "frame-%d.png missing" % i
        sc = _sidecar(shots, i)
        want = {u["id"]: u["side"] for u in doc["frames"][i]["units"]}
        got = {u["id"]: u["side"] for u in sc["units"]}
        assert got == want, "frame %d: sidecar units differ from the fight file" % i
        for u in sc["units"]:
            assert isinstance(u["x"], (int, float)) and isinstance(u["y"], (int, float))
            assert u["radius"] > 0
            assert len(u["colour"]) == 7 and u["colour"][0] == "#"


def test_id_render_gives_each_unit_one_unique_flat_colour(shots):
    """Look-judge rig piece 3 "with OM_ID_RENDER=1 a second flat-colour ID render frame-<i>.id.png (each unit one unique flat colour, no effects, no HUD)": at frame 96 every
    unit's colour in the sidecar is distinct, and the ID image holds no colour outside the unit colours plus one background (no antialiasing, no HUD text)."""
    from PIL import Image
    png = shots / "frame-96.id.png"
    assert png.exists(), "frame-96.id.png missing (OM_ID_RENDER=1 not implemented)"
    sc = _sidecar(shots, 96)
    cols = [u["colour"] for u in sc["units"]]
    assert len(set(cols)) == len(cols), "unit ID colours are not unique"
    img = Image.open(png).convert("RGB")
    present = {"#%02x%02x%02x" % c for _, c in img.getcolors(maxcolors=1 << 20)}
    assert len(present - set(cols)) <= 1, "colours beyond the unit colours and one background: %s" % sorted(present - set(cols))[:5]
    assert present & set(cols), "no unit colour appears in the ID render"


def test_id_png_exists_for_every_frame(shots):
    """Look-judge rig piece 3: frame-<i>.id.png for every frame when OM_ID_RENDER=1."""
    missing = [i for i in range(N_FRAMES) if not (shots / ("frame-%d.id.png" % i)).exists()]
    assert not missing, "no id png for frames %s" % missing[:10]


def test_a1_frame_96_the_two_circles_overlap(shots):
    """Look-judge rig piece 3 verification "on A1 at frame 96 the two circles' pixels overlap" (R-097-05 stacked pair): the sidecar has a pair of units closer than the sum of
    their radii, and in the ID render the pair's colours are not both fully visible (the top one hides part of the other)."""
    from PIL import Image
    sc = _sidecar(shots, 96)
    us = sc["units"]
    pairs = [(a, b) for k, a in enumerate(us) for b in us[k + 1:]
             if ((a["x"] - b["x"]) ** 2 + (a["y"] - b["y"]) ** 2) ** 0.5 < a["radius"] + b["radius"]]
    assert pairs, "no two unit circles overlap at frame 96 in the sidecar"
    img = Image.open(shots / "frame-96.id.png").convert("RGB")
    counts = {"#%02x%02x%02x" % c: n for n, c in img.getcolors(maxcolors=1 << 20)}
    import math
    a, b = pairs[0]
    full = math.pi * a["radius"] ** 2
    assert min(counts.get(a["colour"], 0), counts.get(b["colour"], 0)) < full * 0.98, "overlapping pair both fully visible in the ID render"
