"""Shared helpers for lane A story plays (visible-game spec rev 4, section 2 and the story-review queue).

Each play reaches the tactical view through the real game under daemon_client, reads the section 2 inventory from
state()["result"]["qa"], and at each story moment writes the screenshot and the qa_state dump to
docs/northstar/story_reviews/shots/<run id>/<story>_<moment>.{png,json}. The run id is VG_RUN_ID or a timestamp plus
the commit hash, so a re-run never overwrites.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve()
REPO = HERE.parents[5]
sys.path.insert(0, str(HERE.parents[2]))  # tests/qa/desktop: daemon_client, test_tactical_play

from daemon_client import GodotGame, pick_free_port  # noqa: E402
from test_tactical_play import _to_tactical  # noqa: E402

QA_SHOT_DIR = Path.home() / ".local/share/data/qa"
RESOLUTION = "1920x1080"  # Westley's resolution (mission-plays rulings)
# TD-VG-A-4: OM_PLAY_ERA picks the era the plays run in. Unset = the current space era; "ground" = the ground era the
# lane C plays boot (tests/qa/desktop/plays/C/_play.py). Any other value is passed through as an --era value.
PLAY_ERA = os.environ.get("OM_PLAY_ERA", "")
ERA_ARG = {"ground": "greek_placeholder"}.get(PLAY_ERA, PLAY_ERA)
ERA_SUFFIX = ("_" + PLAY_ERA) if PLAY_ERA else ""


def _run_id() -> str:
    if os.environ.get("VG_RUN_ID"):
        return os.environ["VG_RUN_ID"]
    try:
        sha = subprocess.run(["git", "-C", str(REPO), "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()
    except OSError:
        sha = "nogit"
    return time.strftime("%Y%m%d-%H%M") + "-" + sha


RUN_ID = _run_id()
SHOT_DIR = REPO / "docs/northstar/story_reviews/shots" / RUN_ID


def start_tactical_game() -> GodotGame:
    extra = {"extra_args": ["--era", ERA_ARG], "renderer": "vulkan"} if ERA_ARG else {}
    g = GodotGame(qa_port=pick_free_port(), seed=1, resolution=RESOLUTION, **extra)
    g.start()
    g.wait_for_port(timeout=60.0)
    _to_tactical(g)
    return g


def qa(client) -> dict:
    return client.state()["result"]["qa"]


def _lookup(d: dict, key: str):
    if key in d:
        return d[key]
    cur = d
    for part in key.split("."):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        else:
            return None
    return cur


def inv(state: dict) -> dict:
    """The section 2 inventory: state["inventory"] when present, else the qa_state itself."""
    i = state.get("inventory")
    return i if isinstance(i, dict) else state


def has_key(state: dict, key: str) -> bool:
    return _lookup(inv(state), key) is not None


def count(state: dict, key: str) -> int:
    v = _lookup(inv(state), key)
    if isinstance(v, bool):
        return int(v)
    if isinstance(v, (list, dict)):
        return len(v)
    if isinstance(v, (int, float)):
        return int(v)
    return 0


def moment(client, story: str, label: str) -> dict:
    """Screenshot plus qa_state dump for one story moment; returns the qa_state."""
    name = "%s_%s%s" % (story, label, ERA_SUFFIX)
    client.screenshot(name)
    SHOT_DIR.mkdir(parents=True, exist_ok=True)
    src = QA_SHOT_DIR / (name + ".png")
    deadline = time.monotonic() + 5.0
    while not src.exists() and time.monotonic() < deadline:
        time.sleep(0.1)
    assert src.exists(), "%s: the daemon wrote no screenshot at %s" % (story, src)
    shutil.copy(src, SHOT_DIR / (name + ".png"))
    state = client.state()["result"]
    (SHOT_DIR / (name + ".json")).write_text(json.dumps(state, indent=1, sort_keys=True))
    return state.get("qa", {})


def step_until(client, pred, max_ticks: int, chunk: int = 5) -> bool:
    """Steps the mission chunk ticks at a time until pred(qa) holds; False when max_ticks pass first."""
    done = 0
    while done < max_ticks:
        if pred(qa(client)):
            return True
        client.call("step", chunk)
        done += chunk
        time.sleep(0.05)
    return pred(qa(client))


def nearest_enemy_px(q: dict) -> tuple:
    """Screen pixel of the enemy unit nearest (world distance) to the local faction's units, read from qa_state units and
    projected with the flat view the tactical view uses (screen = (world - camera) * scale + half screen), clamped to the
    screen. Enemies are fogged at the start, so units_px cannot be used."""
    units, me = q["units"], q["local_faction"]
    mine = [u for u in units.values() if u["faction"] == me]
    foes = [u for u in units.values() if u["faction"] != me]
    assert mine and foes, "play_support: no local or no enemy units in qa_state"
    e = min(foes, key=lambda f: min((f["x"] - m["x"]) ** 2 + (f["y"] - m["y"]) ** 2 for m in mine))
    w, h = (int(v) for v in RESOLUTION.split("x"))
    cam, sc = q["camera"], q["scale"]
    px = (e["x"] - cam["x"]) * sc + w / 2
    py = (e["y"] - cam["y"]) * sc + h / 2
    return int(min(max(px, 1), w - 2)), int(min(max(py, 1), h - 2))
