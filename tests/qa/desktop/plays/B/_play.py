"""Shared driver for lane B (galaxy) story plays (not a test module).

A play drives the real game over the QA daemon like a player (real clicks, live clock), then saves one screenshot
and the qa_state JSON of the moment to docs/northstar/story_reviews/shots/<run id>/<story>.png and <story>.state.json.
Run id: env PLAY_RUN_ID, else a UTC timestamp fixed per process. Pattern: tests/qa/desktop/test_flow_spine.py.
Run one play:  pytest tests/qa/desktop/plays/B/S-106.py
"""
from __future__ import annotations

import json
import os
import shutil
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve()
ROOT = HERE.parents[5]
sys.path.insert(0, str(ROOT / "tests/qa/desktop"))

from daemon_client import (  # noqa: E402
    GodotGame, control_center, control_names, find_control, pick_free_port, wait_for,
)

RUN_ID = os.environ.get("PLAY_RUN_ID") or datetime.now(timezone.utc).strftime("run-%Y%m%dT%H%M%SZ")
SHOT_DIR = ROOT / "docs/northstar/story_reviews/shots" / RUN_ID
MAIN_MENU = "res://scenes/main_menu/main_menu.tscn"
PRIVACY = "res://scenes/privacy_modal/privacy_modal.tscn"
LOBBY = "res://scenes/lobby/lobby.tscn"
TACTICAL = "res://scenes/tactical_c/tactical_view.tscn"
BOOT_S, STEP_S, PORT_S = 45.0, 10.0, 60.0
# 1080p is Westley's review resolution (memory: QA plays like the user, 1080p).
RESOLUTION = "1920x1080"


def start_game(seed: int = 1) -> GodotGame:
    g = GodotGame(qa_port=pick_free_port(), seed=seed, resolution=RESOLUTION, renderer="vulkan")
    g.start()
    g.wait_for_port(timeout=PORT_S)
    return g


def reach_main_menu(client) -> dict:
    deadline = time.monotonic() + BOOT_S
    clicked = False
    while time.monotonic() < deadline:
        res = client.state()["result"]
        if res.get("scene") == MAIN_MENU:
            return res
        if res.get("scene") == PRIVACY and not clicked:
            c = find_control(client.tree(), "AcceptButton")
            if c is not None:
                client.click(*control_center(c))
                clicked = True
        time.sleep(0.5)
    raise AssertionError("never reached the main menu; controls: %r" % control_names(client.tree()))


def control_with_text(client, needle: str) -> dict | None:
    for c in client.tree().get("result", {}).get("controls", []):
        if needle in str(c.get("text") or "").lower():
            return c
    return None


def click_text(client, needle: str, label: str) -> None:
    c = control_with_text(client, needle)
    assert c is not None, "%s: no control with text %r among %r" % (label, needle, control_names(client.tree()))
    client.click(*control_center(c))


def click_named(client, name: str, label: str) -> None:
    c = find_control(client.tree(), name)
    assert c is not None, "%s: control %s not found among %r" % (label, name, control_names(client.tree()))
    client.click(*control_center(c))


GALAXY = "res://scenes/galaxy/galaxy_view.tscn"


def new_game(client) -> dict:
    """Main menu -> NewGame button -> galaxy, then a short wait so the first frames draw."""
    reach_main_menu(client)
    click_named(client, "NewGame", "menu")
    res = wait_for(client, lambda s: s.get("scene") == GALAXY, STEP_S * 2, label="galaxy")
    time.sleep(4.0)
    return res


def record(client, story: str) -> dict:
    """Screenshot + qa_state of the moment under the run id. Returns the qa_state result."""
    SHOT_DIR.mkdir(parents=True, exist_ok=True)
    client.screenshot(story)
    src = client.user_dir / "qa" / f"{story}.png"
    deadline = time.monotonic() + 5
    while not src.exists() and time.monotonic() < deadline:
        time.sleep(0.1)
    assert src.exists(), "screenshot %s was not written" % src
    shutil.copy(src, SHOT_DIR / f"{story}.png")
    res = client.state()["result"]
    (SHOT_DIR / f"{story}.state.json").write_text(json.dumps(res, indent=2, sort_keys=True))
    return res
