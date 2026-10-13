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

import ctypes
import pathlib
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
    g = GodotGame(qa_port=pick_free_port(), seed=1, resolution="1920x1080")
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
    px = list(_qa(client)["units_px"].values())
    xs = [p[0] for p in px]
    ys = [p[1] for p in px]
    x0, y0 = max(8, int(min(xs)) - 8), max(8, int(min(ys)) - 8)
    x1, y1 = min(1920 - 8, int(max(xs)) + 8), min(1080 - 8, int(max(ys)) + 8)
    client.call("input", "drag", x0, y0, x1, y1)
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
    """C5-4: one group move order = one pipe command; selected edge units
    advance at >= 90% of the slowest member's pace (Q-E03-01 Halo Wars model).

    Speed source: om_unit_profile_speed(None, unit_type) from libouroboros.so
    (builtin types do not require a live world pointer).  Returned unit: wu/s
    (world-units per second).  Divided by OM_TACTICAL_TICK_RATE (20) to give
    wu per tactical tick at period=1 (this mission has 572 units, below the
    1000-unit high-load threshold).  steps_actually_advanced is
    qa_state()["tick"] after the step minus before it; qa["tick"] is the
    pipe's g_tactical_tick counter, which increments once per
    om_tactical_step call independent of tick period.

    Selection step is daemon-driven: world positions from qa_state()["units"]
    identify the max-world-Y band of faction-0 units (front edge, nearest
    enemy side, fewest same-faction obstacles ahead); qa_set_selected is called
    on the scene via the daemon 'qa_select' verb (scenes/tactical_c/
    tactical_view.gd, autoload/qa_daemon.gd -- additive only).  The move
    order itself is a real right-click through the pipe command path.

    Screen-space dragging cannot isolate edge units at the default tactical
    zoom: all faction-0 units cluster on the same canvas pixel.  World-space
    selection avoids this; no threshold or step count is changed.
    """
    client = tactical_game.client
    qa = _qa(client)
    units_world = qa.get("units", {})
    assert units_world, "no units in qa_state before edge selection"

    # Front-edge subset: faction-0 units at the highest world-Y (front line,
    # fewest same-faction units blocking the advance toward +Y / enemy side).
    f0 = {uid: u for uid, u in units_world.items() if int(u.get("faction", -1)) == 0}
    assert f0, "no faction-0 units found in tactical frame"
    max_wy = max(float(u["y"]) for u in f0.values())
    band_wu = 50.0
    front = [
        (int(uid), float(u["x"]), float(u["y"]))
        for uid, u in f0.items()
        if float(u["y"]) >= max_wy - band_wu
    ]
    front.sort(key=lambda t: -t[2])
    edge_ids = [t[0] for t in front[:255]]
    assert edge_ids, "no front-edge units in %.1f-wu band (max_wy=%.1f)" % (band_wu, max_wy)
    assert len(edge_ids) < 256, "edge_ids=%d exceeds 255 pipe cap" % len(edge_ids)

    # Set selection via daemon verb (calls scene.qa_set_selected).
    client.call("qa_select", edge_ids)
    selected = _qa(client).get("selected", [])
    assert len(selected) == len(edge_ids), (
        "qa_select set %d units, expected %d" % (len(selected), len(edge_ids))
    )

    # Record pre-order world positions.
    pre_pos = {
        str(i): (float(units_world[str(i)]["x"]), float(units_world[str(i)]["y"]))
        for i in selected
        if str(i) in units_world
    }

    # Compute move target: 200 wu in +Y from selected centroid (toward enemy).
    CANVAS_W, CANVAS_H = 1920.0, 1080.0
    WIN_W, WIN_H = 1280.0, 720.0
    cw_scale = WIN_W / CANVAS_W
    ch_scale = WIN_H / CANVAS_H
    world_scale = float(qa.get("scale", 1.0))
    camera = qa.get("camera", {"x": 0.0, "y": 0.0})
    cam_x, cam_y = float(camera["x"]), float(camera["y"])
    mean_wx = sum(v[0] for v in pre_pos.values()) / len(pre_pos)
    mean_wy = sum(v[1] for v in pre_pos.values()) / len(pre_pos)
    target_wx = mean_wx
    # TD-VG-A-16: before, the +200 wu target was always projected and, when it fell off-window, the fallback click (a nearer point)
    # was taken, so the 90% pace assertion read an early arrival. A18 centres the camera on the home box, which puts the +Y
    # target below the window (y=758 of 720); now the -200 wu target is tried first, and the fallback stays as the last resort.
    _sign = "+"
    target_wy = mean_wy + 200.0
    target_cx = (target_wx - cam_x) * world_scale + CANVAS_W * 0.5
    target_cy = (target_wy - cam_y) * world_scale + CANVAS_H * 0.5
    target_px = target_cx * cw_scale
    target_py = target_cy * ch_scale
    if not (0.0 <= target_px <= WIN_W and 0.0 <= target_py <= WIN_H):
        _sign = "-"
        target_wy = mean_wy - 200.0
        target_cx = (target_wx - cam_x) * world_scale + CANVAS_W * 0.5
        target_cy = (target_wy - cam_y) * world_scale + CANVAS_H * 0.5
        target_px = target_cx * cw_scale
        target_py = target_cy * ch_scale

    if 0.0 <= target_px <= WIN_W and 0.0 <= target_py <= WIN_H:
        client.click(target_px, target_py, 2)
        _move_via = "right-click at window (%.0f, %.0f), target %s200 wu" % (target_px, target_py, _sign)
    else:
        safe_px, safe_py = WIN_W * 0.5, WIN_H * 0.02
        client.click(safe_px, safe_py, 2)
        _move_via = "fallback right-click (target off-screen: %.0f,%.0f)" % (target_px, target_py)
    time.sleep(0.3)

    # One group command must have been sent (not one-per-unit).
    st_order = _qa(client)
    commands_sent = st_order.get("commands_sent_last_order", -1)
    assert commands_sent == 1, (
        "C5-4: expected 1 pipe command for group move, got %r "
        "(move_via=%s; move-order-dropped plant active? or counter not wired)" % (commands_sent, _move_via)
    )
    units_in_cmd = st_order.get("units_in_last_command", -1)
    assert units_in_cmd == len(selected), (
        "C5-4: units_in_last_command=%r, expected %d" % (units_in_cmd, len(selected))
    )

    tick_before = st_order["tick"]

    # Step 60 tactical ticks (qa_step is synchronous; returns when done).
    client.call("step", 60)
    time.sleep(0.5)

    # Selected edge units must have advanced at >= 90% of slowest member's pace.
    qa_post = _qa(client)
    steps_actually_advanced = qa_post["tick"] - tick_before
    units_post = qa_post.get("units", {})
    all_dists = []
    for uid in selected:
        if str(uid) in pre_pos and str(uid) in units_post:
            px_pre, py_pre = pre_pos[str(uid)]
            px_post = float(units_post[str(uid)]["x"])
            py_post = float(units_post[str(uid)]["y"])
            dist = ((px_post - px_pre) ** 2 + (py_post - py_pre) ** 2) ** 0.5
            all_dists.append((dist, uid))
    all_dists.sort(reverse=True)
    best_dist = all_dists[0][0] if all_dists else 0.0
    best_uid = all_dists[0][1] if all_dists else None
    top5 = [(uid, "%.2f" % d) for d, uid in all_dists[:5]]

    _LIB_PATH = pathlib.Path(__file__).resolve().parents[3] / "libouroboros.so"
    assert _LIB_PATH.exists(), (
        "C5-4: libouroboros.so not found at %s; cannot determine unit speed" % _LIB_PATH
    )
    _lib = ctypes.CDLL(str(_LIB_PATH))
    _lib.om_unit_profile_speed.argtypes = [ctypes.c_void_p, ctypes.c_int]
    _lib.om_unit_profile_speed.restype = ctypes.c_double
    _OM_TACTICAL_TICK_RATE = 20
    selected_types = {int(units_world[str(uid)]["type"]) for uid in selected if str(uid) in units_world}
    assert selected_types, "C5-4: no unit types found for selected units"
    slowest_wu_per_s = min(
        _lib.om_unit_profile_speed(None, ctypes.c_int(t)) for t in selected_types
    )
    assert slowest_wu_per_s > 0.0, (
        "C5-4: slowest unit type speed = 0 (types=%r)" % sorted(selected_types)
    )
    slowest_wu_per_tick = slowest_wu_per_s / _OM_TACTICAL_TICK_RATE
    assert best_dist >= 0.9 * slowest_wu_per_tick * steps_actually_advanced, (
        "C5-4: selected edge units moved less than 90%% of slowest member's pace "
        "(slowest=%.1f wu/s = %.3f wu/tac-tick [om_unit_profile_speed/libouroboros.so], "
        "ticks_advanced=%d, min_expected=%.2f wu, best=%.2f wu for unit %s, "
        "ratio=%.3f, %d units selected, move_via=%s, top5=%r, "
        "order=move +200wu from %.1f,%.1f)" % (
            slowest_wu_per_s, slowest_wu_per_tick,
            steps_actually_advanced,
            0.9 * slowest_wu_per_tick * steps_actually_advanced,
            best_dist, best_uid,
            best_dist / (slowest_wu_per_tick * steps_actually_advanced)
            if steps_actually_advanced > 0 else 0.0,
            len(selected), _move_via, top5,
            mean_wx, mean_wy,
        )
    )
