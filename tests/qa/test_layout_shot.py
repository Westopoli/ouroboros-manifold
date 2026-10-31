# spec: docs/stories/H-025.md (layout-catalogue-producer), DEC-lab-catalogue-mass-produced-2026-10-30
"""H-025 layout shot scene: res://scenes/proto/layout_shot/layout_shot.tscn.

Story H-025: "Layouts are mass-produced from the recorded rules, each with a 3D shot and a predicted verdict,
and Westley approves or denies each one with feedback; only approved layouts reach the lab."

Story test proved here: "run the scene headless with `OM_LAYOUT` on a produced layout, read `qa_state()`, assert `unit_count` equals the file's rows,
every role present is in `legend`, `layers_visible` is true; and `OM_SHOT_OUT` yields a PNG that is not blank."
Scene contract: "It reads the layout JSON path from the environment variable `OM_LAYOUT` and, when `OM_SHOT_OUT` is set, saves a PNG there after 30 frames
and quits. `qa_state()` keys: `scene` (the scene path), `layout_id`, `unit_count`, `units` (list of {id, side, role, layer, x, y, facing}), `legend`
(list of role names drawn), `layers_visible` (bool)."

The scene is launched the desktop-QA way (tests/qa/desktop/daemon_client.py: Xvfb, software GL, --qa-port), with the scene path inserted before the `--`
so Godot opens it instead of run/main_scene. OM_SHOT_OUT is read as the path of the PNG file ("saves a PNG there"); the story does not say file or directory.

Positive controls (green today): the existing scenes/ground3d/ harness test (tests/test_vg_c5_ground3d_host.gd) passes under the same runner, and the
blank-PNG detector used below flags an all-black PNG.

Red on the built tree: the scene file does not exist, so Godot opens no scene and the qa-port never serves a layout_shot qa_state; the layout comes
from scripts/skilllab/catalogue/produce.py, which does not exist either.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tests" / "qa" / "desktop"))

from daemon_client import GodotGame, pick_free_port, wait_for  # noqa: E402

SCENE = "res://scenes/proto/layout_shot/layout_shot.tscn"
STATE_KEYS = {"scene", "layout_id", "unit_count", "units", "legend", "layers_visible"}
UNIT_KEYS = {"id", "side", "role", "layer", "x", "y", "facing"}
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


class ShotGame(GodotGame):
    """GodotGame that opens SCENE: the scene path goes before the `--` that starts the user args."""

    def godot_args(self, godot: str = "godot") -> list[str]:
        args = super().godot_args(godot)
        args.insert(args.index("--"), SCENE)
        return args


def _produce_one(out: Path) -> Path:
    r = subprocess.run([sys.executable, "-m", "scripts.skilllab.catalogue.produce", "--out", str(out), "--situations", "chokepoint",
                        "--pairs", "16:32", "--seed", "1"], cwd=ROOT, capture_output=True, text=True, timeout=300)
    assert r.returncode == 0, "producer CLI rc=%s: %s" % (r.returncode, r.stderr[-400:])
    files = sorted(out.glob("L-*.json"))
    assert files, "producer wrote no layout JSON in %s" % out
    return files[0]


@pytest.fixture(scope="module")
def layout(tmp_path_factory) -> Path:
    return _produce_one(tmp_path_factory.mktemp("shot_layout"))


def _png_distinct_colours(path: Path) -> int:
    """Distinct pixel values of a PNG (Pillow); 0 when the file is not a PNG."""
    from PIL import Image
    with Image.open(path) as im:
        colours = im.convert("RGBA").getcolors(maxcolors=im.width * im.height)
    return len(colours)


def _blank_png(path: Path, rgb=(0, 0, 0)) -> None:
    from PIL import Image
    Image.new("RGB", (64, 48), rgb).save(path)


# ---------------------------------------------------------------- positive controls (green today)

def test_control_ground3d_harness_test_passes_today(tmp_path):
    """H-025 "built on scenes/ground3d/". CONTROL: the existing Ground3D host test passes under scripts/run_godot_tests.sh on this tree,
    so a red scene test below is the missing layout_shot scene, not a broken Godot setup."""
    env = dict(os.environ, TMPDIR=str(tmp_path))
    r = subprocess.run(["timeout", "1700", str(ROOT / "scripts" / "run_godot_tests.sh"), "tests/test_vg_c5_ground3d_host.gd"],
                       cwd=ROOT, capture_output=True, text=True, env=env, timeout=1800)
    assert r.returncode == 0 and "PASS: res://tests/test_vg_c5_ground3d_host.gd" in r.stdout, r.stdout[-600:] + r.stderr[-300:]


def test_control_blank_detector_flags_a_black_png(tmp_path):
    """H-025 "`OM_SHOT_OUT` yields a PNG that is not blank". CONTROL: an all-black PNG has one colour, so the check below would reject it."""
    p = tmp_path / "black.png"
    _blank_png(p)
    assert _png_distinct_colours(p) == 1


# ---------------------------------------------------------------- the scene

def test_scene_file_exists():
    """H-025 "Scene res://scenes/proto/layout_shot/layout_shot.tscn, built on scenes/ground3d/"."""
    assert (ROOT / "scenes" / "proto" / "layout_shot" / "layout_shot.tscn").is_file()


@pytest.fixture()
def shot_game(layout, monkeypatch):
    monkeypatch.setenv("OM_LAYOUT", str(layout))
    monkeypatch.delenv("OM_SHOT_OUT", raising=False)
    g = ShotGame(qa_port=pick_free_port(), seed=1)
    g.start()
    try:
        g.wait_for_port(timeout=90.0)
        yield g
    finally:
        g.stop()


def test_qa_state_inventory_lists_every_unit_and_the_legend(shot_game, layout):
    """H-025 "run the scene headless with OM_LAYOUT on a produced layout, read qa_state(), assert unit_count equals the file's rows, every role present is in
    legend, layers_visible is true"; qa_state keys scene, layout_id, unit_count, units {id, side, role, layer, x, y, facing}, legend, layers_visible."""
    want = json.loads(layout.read_text())
    rows = want["side_a"]["units"] + want["side_b"]["units"]
    res = wait_for(shot_game.client, lambda r: r.get("scene") == SCENE and "qa" in r, timeout=60.0, label="layout_shot scene")
    qa = res["qa"]
    assert STATE_KEYS <= set(qa), "qa_state keys %s lack %s" % (sorted(qa), sorted(STATE_KEYS - set(qa)))
    assert qa["scene"] == SCENE
    assert qa["layout_id"] == want["id"]
    assert qa["unit_count"] == len(rows), "unit_count %s, the file has %d rows" % (qa["unit_count"], len(rows))
    assert len(qa["units"]) == len(rows)
    assert all(UNIT_KEYS <= set(u) for u in qa["units"]), "a unit lacks keys %s: %s" % (sorted(UNIT_KEYS), qa["units"][:1])
    assert len({u["id"] for u in qa["units"]}) == len(rows), "unit ids are not unique"
    sides = {}
    for u in qa["units"]:
        sides.setdefault(u["side"], []).append(u)
    assert sorted(len(v) for v in sides.values()) == sorted([want["side_a"]["headcount"], want["side_b"]["headcount"]]), \
        "units per side %s, the file has %d and %d" % ({k: len(v) for k, v in sides.items()}, want["side_a"]["headcount"], want["side_b"]["headcount"])
    key = lambda u: (u["role"], int(u["layer"]), round(float(u["x"]), 3), round(float(u["y"]), 3), round(float(u["facing"]), 3))
    assert sorted(map(key, qa["units"])) == sorted(map(key, rows)), "scene units differ from the layout file's rows"
    roles = {u["role"] for u in rows}
    assert roles <= set(qa["legend"]), "roles %s are not all in legend %s" % (sorted(roles), qa["legend"])
    assert qa["layers_visible"] is True


def test_shot_out_writes_a_png_that_is_not_blank(layout, tmp_path, monkeypatch):
    """H-025 "when OM_SHOT_OUT is set, saves a PNG there after 30 frames and quits"; "`OM_SHOT_OUT` yields a PNG that is not blank"."""
    shot = tmp_path / "shot.png"
    monkeypatch.setenv("OM_LAYOUT", str(layout))
    monkeypatch.setenv("OM_SHOT_OUT", str(shot))
    g = ShotGame(qa_port=pick_free_port(), seed=1)
    g.start()
    try:
        try:
            g.proc.wait(timeout=180)
        except subprocess.TimeoutExpired:
            pytest.fail("the scene did not quit after saving the shot (OM_SHOT_OUT set); stderr tail:\n" + g.stderr_tail())
        assert shot.is_file(), "no PNG at OM_SHOT_OUT; stderr tail:\n" + g.stderr_tail()
        assert shot.read_bytes()[:8] == PNG_MAGIC, "OM_SHOT_OUT file is not a PNG"
        assert _png_distinct_colours(shot) > 1, "the shot is a single colour (blank)"
    finally:
        g.stop()
