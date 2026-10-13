"""Shared driver for the lane C story plays (spec lane C; one scenario per story moment).

Each play launches the real game in a ground era (`--era greek_placeholder`, the stage 3 flag used by
tests/qa/desktop/test_ground_era.py), walks menu -> tactical like a player, then acts the story moment.
Evidence goes to docs/northstar/story_reviews/shots/<run id>/: `<story>_<moment>.png` (the daemon's screenshot,
copied out of the fixed QA dir) and `<story>_<moment>.json` (the `qa` block of state()). Run id: env OM_RUN_ID,
else a UTC timestamp fixed per process.
"""
from __future__ import annotations

import json
import os
import shutil
import sys
import time
from pathlib import Path

DESKTOP = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(DESKTOP))

from daemon_client import GodotGame, pick_free_port  # noqa: E402
from test_tactical_play import _to_tactical  # noqa: E402

REPO = Path(__file__).resolve().parents[5]
QA_SHOT_DIR = Path.home() / ".local/share/data/qa"
RUN_ID = os.environ.get("OM_RUN_ID") or time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
SHOT_DIR = REPO / "docs/northstar/story_reviews/shots" / RUN_ID


def start_ground_game() -> GodotGame:
    g = GodotGame(qa_port=pick_free_port(), seed=1, resolution="1920x1080", extra_args=["--era", "greek_placeholder"], renderer="vulkan")
    g.start()
    g.wait_for_port(timeout=60.0)
    _to_tactical(g)
    return g


def qa(game: GodotGame) -> dict:
    return game.client.state()["result"].get("qa", {})


def ground3d(game: GodotGame) -> dict:
    """The qa_state `ground3d` block (spec section 2); asserts it exists and says present."""
    q = qa(game)
    g = q.get("ground3d")
    assert isinstance(g, dict) and g.get("present"), (
        "qa_state.ground3d missing or not present (the 3D ground is not drawn); qa keys = %s" % sorted(q))
    return g


def evidence(game: GodotGame, story: str, moment: str) -> Path:
    """Screenshot plus qa_state for one story moment, written under SHOT_DIR; returns the png path."""
    name = "%s_%s" % (story, moment)
    game.client.screenshot(name)
    time.sleep(0.5)
    SHOT_DIR.mkdir(parents=True, exist_ok=True)
    src = QA_SHOT_DIR / (name + ".png")
    dst = SHOT_DIR / (name + ".png")
    assert src.exists(), "screenshot %s was not written by the daemon" % src
    shutil.copy2(src, dst)
    (SHOT_DIR / (name + ".json")).write_text(json.dumps(qa(game), indent=1, sort_keys=True))
    return dst


def px(v):
    """A units_px / objects_px entry as (x, y): the JSON form is [x, y] or {x, y}."""
    if isinstance(v, dict):
        return float(v["x"]), float(v["y"])
    return float(v[0]), float(v[1])


def step(game: GodotGame, n: int) -> None:
    game.client.call("step", n)
