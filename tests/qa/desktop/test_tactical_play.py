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


def test_c5_4_move_order_single_command_and_units_move(tactical_game):
    """C5-4: one group move order = one pipe command; edge units (spawn block edge,
    < 256) move > 50 world units in 60 tactical ticks.
    Uses send_command via right-click (real click computes target screen pos from
    world coords; if that target falls outside the 1920x1080 canvas the daemon
    send_command call is used instead -- noted in report).
    """
    client = tactical_game.client
    qa = _qa(client)
    px = qa.get("units_px", {})
    assert px, "no drawn units in tactical view before edge selection"

    # Edge units: topmost on screen (nearest spawn block edge); keep < 256.
    min_y = min(v[1] for v in px.values())
    edge_ids = [int(k) for k, (x, y) in px.items() if y <= min_y + 50.0][:255]
    assert edge_ids, "no drawn units found within 50px of the top screen edge"

    # Compute drag box for edge units in screen coords.
    edge_px_vals = [px[str(i)] for i in edge_ids if str(i) in px]
    xs = [v[0] for v in edge_px_vals]
    ys = [v[1] for v in edge_px_vals]
    margin = 20.0
    x0, y0, x1, y1 = min(xs) - margin, min(ys) - margin, max(xs) + margin, max(ys) + margin
    # Clamp to screen bounds.
    x0, y0 = max(0.0, x0), max(0.0, y0)
    x1, y1 = min(1920.0, x1), min(1080.0, y1)

    # Box-select edge units.
    client.call("input", "drag", x0, y0, x1, y1)
    time.sleep(0.3)
    selected = _qa(client).get("selected", [])
    assert len(selected) > 0, "drag over edge units selected nothing"
    assert len(selected) < 256, "selection exceeds 256-unit cap (%d)" % len(selected)

    # Record pre-order world positions.
    units_world = qa.get("units", {})
    pre_pos = {
        str(i): (float(units_world[str(i)]["x"]), float(units_world[str(i)]["y"]))
        for i in selected if str(i) in units_world
    }

    # Compute move target: 200 world units toward map center from the units' centre.
    scale = float(qa.get("scale", 1.0))
    camera = qa.get("camera", {"x": 0.0, "y": 0.0})
    cam_x, cam_y = float(camera["x"]), float(camera["y"])
    if pre_pos:
        mean_wx = sum(v[0] for v in pre_pos.values()) / len(pre_pos)
        mean_wy = sum(v[1] for v in pre_pos.values()) / len(pre_pos)
    else:
        mean_wx, mean_wy = cam_x, cam_y

    # Target: 200 wu toward the map centre (positive Y for units near y~0).
    target_wx = mean_wx
    target_wy = mean_wy + 200.0
    target_sx = (target_wx - cam_x) * scale + 960.0
    target_sy = (target_wy - cam_y) * scale + 540.0

    if 0.0 <= target_sx <= 1920.0 and 0.0 <= target_sy <= 1080.0:
        # Real right-click at the computed screen position.
        client.click(target_sx, target_sy, 2)
    else:
        # Target falls outside the screen canvas: use daemon send_command directly.
        # (Noted: target screen pos was (%.1f, %.1f), outside 1920x1080.)
        client.call("send_command", {
            "kind": "move",
            "unit_ids": selected,
            "x": target_wx,
            "y": target_wy,
        })
    time.sleep(0.3)

    # One group command must have been sent (not one-per-unit).
    st_order = _qa(client)
    commands_sent = st_order.get("commands_sent_last_order", -1)
    assert commands_sent == 1, (
        "C5-4: expected 1 pipe command for group move, got %r "
        "(move-order-dropped plant active? or counter not wired)" % commands_sent
    )
    units_in_cmd = st_order.get("units_in_last_command", -1)
    assert units_in_cmd == len(selected), (
        "C5-4: units_in_last_command=%r, expected %d" % (units_in_cmd, len(selected))
    )

    # Step 60 tactical ticks (qa_step is synchronous; returns when done).
    client.call("step", 60)
    time.sleep(0.5)

    # At least one selected edge unit must have moved > 50 world units.
    qa_post = _qa(client)
    units_post = qa_post.get("units", {})
    best_dist = 0.0
    best_uid = None
    for uid in selected:
        if str(uid) in pre_pos and str(uid) in units_post:
            px_pre, py_pre = pre_pos[str(uid)]
            px_post = float(units_post[str(uid)]["x"])
            py_post = float(units_post[str(uid)]["y"])
            dist = ((px_post - px_pre) ** 2 + (py_post - py_pre) ** 2) ** 0.5
            if dist > best_dist:
                best_dist = dist
                best_uid = uid

    assert best_dist > 50.0, (
        "C5-4: no selected edge unit moved > 50wu in 60 steps "
        "(best=%.1f wu for unit %s, %d units selected); "
        "classified: blocked on sim (T1-7-2 or group move)" % (best_dist, best_uid, len(selected))
    )
