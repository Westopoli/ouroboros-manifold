# spec: docs/northstar/plans/push/specs/C5.md (tactical view), E-13 R-096/R-105, piece C5-3
"""Piece C5-3: the tactical view on a real mission, driven with real input.

Boot -> NewGame -> galaxy -> step 10 ticks (the seed-1 mission at tick 10 is the
archetype with 572 units) -> Mission -> Deploy -> tactical view. Then:
  C5-3-01  the drawn units (the local faction's, fog-gated by visible["0"]) are on
           screen: every units_px point lies inside the 1920x1080 canvas.
  C5-3-02  a real left-drag over the top edge (where the player's force stands) selects
           every drawn unit.
  C5-3-03  a real right-click orders that selection to move: the command is acknowledged
           over the session (qa_state().last_command.ok).
Sim-side gap when written: ordered units do not move over the pipe, so movement is not
asserted here (fixture frames prove the plants in tests/test_tactical_view.gd).
"""
from __future__ import annotations

import time

import pytest

from daemon_client import (
    GodotGame,
    control_center,
    find_control,
    pick_free_port,
    wait_for,
)

MAIN_MENU_SCENE = "res://scenes/main_menu/main_menu.tscn"
PRIVACY_MODAL_SCENE = "res://scenes/privacy_modal/privacy_modal.tscn"
GALAXY_SCENE = "res://scenes/galaxy/galaxy_view.tscn"
BRIEFING_SCENE = "res://scenes/mission_briefing/mission_briefing.tscn"
TACTICAL_SCENE = "res://scenes/tactical_c/tactical_view.tscn"
BOOT_TIMEOUT_S = 45.0
STEP_TIMEOUT_S = 30.0


def _to_tactical(game: GodotGame) -> None:
    client = game.client
    deadline = time.monotonic() + BOOT_TIMEOUT_S
    clicked = False
    while time.monotonic() < deadline:
        scene = client.state()["result"].get("scene")
        if scene == MAIN_MENU_SCENE:
            break
        if scene == PRIVACY_MODAL_SCENE and not clicked:
            accept = find_control(client.tree(), "AcceptButton")
            if accept is not None:
                client.click(*control_center(accept))
                clicked = True
        time.sleep(0.5)
    else:
        raise AssertionError("never reached the main menu")
    time.sleep(2.0)
    client.click(*control_center(find_control(client.tree(), "NewGame")))
    wait_for(client, lambda s: s.get("scene") == GALAXY_SCENE, STEP_TIMEOUT_S, label="galaxy")
    time.sleep(2.0)
    client.call("step", 10)
    wait_for(client, lambda s: int(s.get("qa", {}).get("tick", 0)) >= 10, STEP_TIMEOUT_S, label="galaxy tick 10")
    client.click(*control_center(find_control(client.tree(), "Mission")))
    wait_for(client, lambda s: s.get("scene") == BRIEFING_SCENE, STEP_TIMEOUT_S, label="briefing")
    time.sleep(2.0)
    client.click(*control_center(find_control(client.tree(), "Deploy")))
    wait_for(client, lambda s: s.get("scene") == TACTICAL_SCENE, STEP_TIMEOUT_S, label="tactical")
    time.sleep(2.0)


@pytest.fixture()
def tactical_game():
    g = GodotGame(qa_port=pick_free_port(), seed=1)
    g.start()
    g.wait_for_port(timeout=60.0)
    try:
        _to_tactical(g)
        yield g
    finally:
        g.stop()


def _qa(client) -> dict:
    return client.state()["result"]["qa"]


def test_c5_3_drawn_units_are_on_screen(tactical_game):
    qa = _qa(tactical_game.client)
    px = qa["units_px"]
    assert len(px) >= 100, "only %d units drawn on a 572-unit mission (canvas %r)" % (len(px), qa.get("canvas"))
    off = [k for k, (x, y) in px.items() if not (0 <= x <= 1920 and 0 <= y <= 1080)]
    assert not off, "%d of %d drawn units are outside the 1920x1080 canvas, e.g. %s at %s" % (len(off), len(px), off[0], px[off[0]])


def test_c5_3_real_drag_selects_and_right_click_orders_a_move(tactical_game):
    client = tactical_game.client
    drawn = len(_qa(client)["units_px"])
    client.call("input", "drag", 0, 0, 1900, 140)
    time.sleep(0.5)
    selected = _qa(client)["selected"]
    assert len(selected) == drawn and drawn > 0, "drag selected %d of %d drawn units" % (len(selected), drawn)
    client.call("input", "click", 960, 540, 2)
    time.sleep(1.0)
    last = _qa(client).get("last_command", {})
    assert last.get("ok") is True and last.get("kind") == "move" and int(last.get("units", 0)) == len(selected), (
        "last_command after the right-click = %r" % last
    )
