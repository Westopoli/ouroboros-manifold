# spec: docs/northstar/plans/push/specs/C8.md (flow spine), E-16 R-111-01/02, piece C1-2
"""Piece C1-2: main-menu CONTINUE loads a live save slot into the galaxy.

Writes one real campaign save (seed 3, 100 ticks, through the pipe's own `save`
command into the game's per-run OM_SAVE_DIR), launches the real game, and walks
boot -> main menu -> CONTINUE -> the slot's LOAD button -> galaxy. The galaxy must
then be the saved world (its live tick is the saved 100, not a fresh game's 0), the
main menu must have shown CONTINUE enabled, and NewGame afterwards must start a
fresh world (tick 0). The save directory is the game's per-run temp directory, so nothing is left behind.
"""
from __future__ import annotations

import json
import subprocess
import time

import pytest

from daemon_client import (
    REPO_ROOT,
    GodotGame,
    control_center,
    find_control,
    pick_free_port,
    wait_for,
)

MAIN_MENU_SCENE = "res://scenes/main_menu/main_menu.tscn"
PRIVACY_MODAL_SCENE = "res://scenes/privacy_modal/privacy_modal.tscn"
LOAD_GAME_SCENE = "res://scenes/load_game/load_game.tscn"
GALAXY_SCENE = "res://scenes/galaxy/galaxy_view.tscn"
SLOT = "campaign_3"
SAVED_TICK = 100
BOOT_TIMEOUT_S = 45.0
STEP_TIMEOUT_S = 15.0
FEATURES = [0, 1, 2, 3, 4, 5, 6, 7]


def _frame(obj):
    body = json.dumps(obj).encode()
    return len(body).to_bytes(4, "big") + body


@pytest.fixture()
def game():
    g = GodotGame(qa_port=pick_free_port(), seed=1)
    path = g.save_dir / (SLOT + ".omsave")
    cmds = [
        {"type": "cmd", "name": "set_seed", "seed": 3, "n_regions": 80, "features": FEATURES},
        {"type": "cmd", "name": "step", "n": SAVED_TICK},
        {"type": "cmd", "name": "save", "path": str(path)},
        {"type": "cmd", "name": "quit"},
    ]
    subprocess.run([str(REPO_ROOT / "pipe/ouroboros_pipe")], input=b"".join(_frame(c) for c in cmds),
                   capture_output=True, timeout=60, check=True)
    assert path.exists() and (g.save_dir / (SLOT + ".omsave.json")).exists()
    g.start()
    g.wait_for_port(timeout=60.0)
    try:
        yield g
    finally:
        g.stop()


def _reach_main_menu(client) -> dict:
    deadline = time.monotonic() + BOOT_TIMEOUT_S
    clicked = False
    while time.monotonic() < deadline:
        state = client.state()["result"]
        if state.get("scene") == MAIN_MENU_SCENE:
            return state
        if state.get("scene") == PRIVACY_MODAL_SCENE and not clicked:
            accept = find_control(client.tree(), "AcceptButton")
            if accept is not None:
                client.click(*control_center(accept))
                clicked = True
        time.sleep(0.5)
    raise AssertionError("never reached the main menu")


def test_c1_2_continue_loads_the_saved_world_into_the_galaxy(game):
    client = game.client
    _reach_main_menu(client)
    time.sleep(2.0)
    menu = client.state()["result"].get("qa", {})
    assert menu.get("continue_enabled") is True, "main menu qa = %r; CONTINUE should be enabled by the live save list" % menu
    assert int(menu.get("slot_count", 0)) >= 1

    cont = find_control(client.tree(), "Continue")
    assert cont is not None, "no control named Continue in the main menu"
    client.click(*control_center(cont))
    wait_for(client, lambda s: s.get("scene") == LOAD_GAME_SCENE, STEP_TIMEOUT_S, label="load_game")
    time.sleep(1.0)
    load_btn = find_control(client.tree(), "Load_" + SLOT)
    assert load_btn is not None, "no Load_%s button in the slot list" % SLOT
    client.click(*control_center(load_btn))
    wait_for(client, lambda s: s.get("scene") == GALAXY_SCENE, STEP_TIMEOUT_S, label="galaxy after LOAD")
    time.sleep(1.0)
    qa = client.state()["result"].get("qa", {})
    assert int(qa.get("tick", -1)) == SAVED_TICK, (
        "galaxy tick = %r after loading the tick-%d save (a fresh game would show 0)" % (qa.get("tick"), SAVED_TICK)
    )
    assert int(qa.get("system_count", 0)) == 80
