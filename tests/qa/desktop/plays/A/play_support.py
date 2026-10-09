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


def start_tactical_game(fog_off: bool = False) -> GodotGame:
    """fog_off (or OM_PLAY_FOG=off) sends the daemon verb set_fog_filter with the bare bool false (one bool arg, TD-VG-A-7) before the mission loads (TD-VG-A-5).
    The verb reads args[0] as one bool; a dict arg is truthy and leaves the filter on."""
    extra = {"extra_args": ["--era", ERA_ARG], "renderer": "vulkan"} if ERA_ARG else {}
    g = GodotGame(qa_port=pick_free_port(), seed=1, resolution=RESOLUTION, **extra)
    g.start()
    g.wait_for_port(timeout=60.0)
    if fog_off or os.environ.get("OM_PLAY_FOG", "").lower() == "off":
        r = g.client.call("set_fog_filter", False)
        assert r.get("ok", True), "play_support: set_fog_filter refused: %r" % r
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


def select_own_by_drag(client) -> None:
    """TD-VG-A-9: a real drag over the bounding box of the own-faction entries of qa_state units_px, padded 8 px and clamped
    at least 8 px inside the screen so the 4 px edge-scroll margin is never touched. Replaces the flat-view drag 0,0 to
    1900,140, which selects nothing on the tilted 3D ground view. The play runs at 1920x1080, so driver pixels equal canvas pixels."""
    q = qa(client)
    me = q["local_faction"]
    pts = [tuple(p) for uid, p in q["units_px"].items() if uid in q["units"] and q["units"][uid]["faction"] == me]
    assert pts, "play_support: no own-faction unit in units_px; nothing to drag over"
    w, h = (int(v) for v in RESOLUTION.split("x"))
    x0 = int(max(min(p[0] for p in pts) - 8, 8))
    y0 = int(max(min(p[1] for p in pts) - 8, 8))
    x1 = int(min(max(p[0] for p in pts) + 8, w - 8))
    y1 = int(min(max(p[1] for p in pts) + 8, h - 8))
    client.call("input", "drag", x0, y0, x1, y1)


def nearest_enemy_px(client, q: dict) -> tuple:
    """TD-VG-A-9b: screen pixel of the enemy unit nearest (world distance) to the local faction's units. The enemy is found
    in qa_state units (all units, fog filter off, TD-VG-A-7); its pixel comes from the test-only daemon verb "project"
    (the view's own projection, flat or ground rig), because units_px holds only the visible set (R-089-04) so an unseen
    enemy never has a pixel there. Clamped at least 70 px inside the screen: camera_rig_3d.gd EDGE_SCROLL_ZONE is 60 px,
    so a click nearer the edge would scroll the camera."""
    units, me = q["units"], q["local_faction"]
    mine = [u for u in units.values() if u["faction"] == me]
    foes = [u for u in units.values() if u["faction"] != me]
    assert mine and foes, "play_support: no local or no enemy units in qa_state"
    k = min(range(len(foes)), key=lambda i: min((foes[i]["x"] - m["x"]) ** 2 + (foes[i]["y"] - m["y"]) ** 2 for m in mine))
    e = foes[k]
    r = client.call("project", float(e["x"]), float(e["y"]))
    assert r.get("ok") is True, "play_support: FINDING: the project verb refused: %r" % r
    for _ in range(12):  # TD-VG-A-9c: an off-screen enemy is zoomed into view as a player would; wheel +1 zooms out (plays/C/s236.py)
        if r["result"].get("on_screen"):
            break
        client.call("input", "wheel", 1)
        r = client.call("project", float(e["x"]), float(e["y"]))
        assert r.get("ok") is True, "play_support: FINDING: the project verb refused: %r" % r
    w, h = (int(v) for v in RESOLUTION.split("x"))
    # TD-VG-A-9e: the ground rig's zoom is capped, so a player scrolls with real pointer input (no camera verb). The edge is
    # chosen from the WORLD delta enemy minus camera, not from the projected pixel: a point behind the eye unprojects to a
    # mirrored pixel. The live pan (tactical_view.gd _pan_input) scrolls only after a mouse-motion event, so a small move is
    # re-sent every 0.5 s. SCREEN_WU is a named draft (a screen's worth of world, 3000 wu at the start height): both axes
    # scroll only when both deltas exceed it; otherwise the larger one. on_screen must hold for two consecutive polls.
    SCREEN_WU = 3000.0
    if not r["result"].get("on_screen"):
        cam = q["camera"]
        ddx, ddy = e["x"] - cam["x"], e["y"] - cam["y"]
        both = abs(ddx) > SCREEN_WU and abs(ddy) > SCREEN_WU
        ex_ = w // 2
        ey_ = h // 2
        if both or abs(ddx) >= abs(ddy):
            ex_ = w - 3 if ddx > 0 else 2
        if both or abs(ddy) > abs(ddx):
            ey_ = h - 3 if ddy > 0 else 2
        client.call("input", "move", ex_, ey_)
        deadline = time.monotonic() + 30.0
        last_nudge = time.monotonic()
        hits = 0
        while time.monotonic() < deadline and hits < 2:
            time.sleep(0.2)
            if time.monotonic() - last_nudge >= 0.5:
                client.call("input", "move", ex_ + (1 if ex_ < w // 2 else -1 if ex_ > w // 2 else 0), ey_ + (1 if ey_ < h // 2 else -1 if ey_ > h // 2 else 0))
                client.call("input", "move", ex_, ey_)
                last_nudge = time.monotonic()
            r = client.call("project", float(e["x"]), float(e["y"]))
            assert r.get("ok") is True, "play_support: FINDING: the project verb refused: %r" % r
            hits = hits + 1 if r["result"].get("on_screen") else 0
        client.call("input", "move", w // 2, h // 2)
        if hits < 2:
            r["result"]["on_screen"] = False
    assert r["result"].get("on_screen"), "play_support: FINDING: enemy %s off screen after zoom-out and 30 s edge scroll toward it" % k
    px, py = r["result"]["x"], r["result"]["y"]
    return int(min(max(px, 70), w - 70)), int(min(max(py, 70), h - 70))
