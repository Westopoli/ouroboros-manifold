"""Shared driver for the lane K story plays (tests/qa/desktop/plays/K/<story>.py).

Boots the real game under daemon_client, walks main menu -> galaxy -> briefing -> tactical exactly as
tests/qa/desktop/test_flow_spine.py does, and gives each play `moment(client, name)`: it takes the
screenshot and writes the scene's qa_state next to it in docs/northstar/story_reviews/shots/<run id>/
(run id: env VG_RUN_ID, else a UTC timestamp fixed once per process). Plays assert on qa_state keys
named by the spec's inventory (section 2); a key the view does not yet publish is the red line.
"""
import json
import os
import shutil
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve()
REPO = HERE.parents[5]
sys.path.insert(0, str(HERE.parents[2]))  # tests/qa/desktop

from daemon_client import GodotGame, control_center, control_names, find_control, pick_free_port, wait_for  # noqa: E402

MAIN_MENU = "res://scenes/main_menu/main_menu.tscn"
GALAXY = "res://scenes/galaxy/galaxy_view.tscn"
BRIEFING = "res://scenes/mission_briefing/mission_briefing.tscn"
TACTICAL = "res://scenes/tactical_c/tactical_view.tscn"
PRIVACY = "res://scenes/privacy_modal/privacy_modal.tscn"
QA_SHOT_DIR = Path.home() / ".local/share/data/qa"
RUN_ID = os.environ.get("VG_RUN_ID") or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
SHOT_DIR = REPO / "docs/northstar/story_reviews/shots" / RUN_ID
BOOT_TIMEOUT = 45.0
STEP_TIMEOUT = 10.0


def start_game(seed=1):
    port = pick_free_port()
    g = GodotGame(qa_port=port, seed=seed, resolution="1920x1080", renderer="vulkan")
    g.start()
    g.wait_for_port(timeout=60.0)
    return g


def _click(client, name, label):
    ctl = find_control(client.tree(), name)
    assert ctl is not None, "%s: control %s not found among %r" % (label, name, control_names(client.tree()))
    client.click(*control_center(ctl))


def to_tactical(client):
    """Boot, New Game, Mission, Deploy; returns the tactical qa_state. Same steps as the flow spine."""
    deadline = time.monotonic() + BOOT_TIMEOUT
    clicked = False
    while time.monotonic() < deadline:
        scene = client.state()["result"].get("scene")
        if scene == MAIN_MENU:
            break
        if scene == PRIVACY and not clicked:
            accept = find_control(client.tree(), "AcceptButton")
            if accept is not None:
                client.click(*control_center(accept))
                clicked = True
        time.sleep(0.5)
    else:
        raise AssertionError("never reached the main menu")
    _click(client, "NewGame", "play boot")
    wait_for(client, lambda s: s.get("scene") == GALAXY, STEP_TIMEOUT, label="galaxy")
    client.call("step", 10)
    _click(client, "Mission", "play galaxy")
    wait_for(client, lambda s: s.get("scene") == BRIEFING, STEP_TIMEOUT, label="briefing")
    _click(client, "Deploy", "play briefing")
    wait_for(client, lambda s: s.get("scene") == TACTICAL, STEP_TIMEOUT, label="tactical")
    return client.state()["result"].get("qa", {})


def step_ticks(client, n):
    client.call("step", n)
    return client.state()["result"].get("qa", {})


def moment(client, story, name):
    """Screenshot + qa_state for one story moment, into the run's shots folder; returns the qa_state."""
    shot = "vg_%s_%s" % (story, name)
    client.screenshot(shot)
    time.sleep(0.5)
    SHOT_DIR.mkdir(parents=True, exist_ok=True)
    src = QA_SHOT_DIR / (shot + ".png")
    if src.exists():
        shutil.copy2(src, SHOT_DIR / (shot + ".png"))
    qa = client.state()["result"].get("qa", {})
    (SHOT_DIR / (shot + ".qa_state.json")).write_text(json.dumps(qa, indent=1, sort_keys=True))
    return qa
