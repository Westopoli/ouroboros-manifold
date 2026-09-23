# spec: docs/northstar/plans/push/specs/C8.md::Acceptance
"""Piece C8 "flow spine" fenced acceptance test (S-C8-01..07, piece-local
ids -- M0 maps them to real S-###/R-###-## story ids once C8 is queued).

Launches the real game (project.godot's run/main_scene, no scene argument)
once for this module under Xvfb, drives it over autoload/qa_daemon.gd's
--qa-port TCP protocol (tests/qa/desktop/daemon_client.py), and walks the
main-menu -> galaxy -> mission briefing -> tactical -> debrief -> chronicle
-> galaxy loop scene_router.gd does not wire today (its SCENES dict has no
"galaxy" entry at all -- see docs/northstar/plans/push/specs/C8.md).

Button-name contract (none of these controls exist in the current main
menu/galaxy/mission_briefing scenes -- C8 adds them):
    NewGame     main menu, replaces the unnamed "NEW GAME" HBoxContainer
    Mission     galaxy_view.tscn, new
    Deploy      mission_briefing.tscn, new
    EndMission  tactical_c/tactical_view.tscn, new
    Continue    debrief.tscn, new
    Return      chronicle-bearing scene, new

Real boot machinery (privacy_modal -> loading_screen -> main_menu) sits in
front of every rule this test proves and is not itself a rule; S-C8-01
drives through it (clicking privacy_modal's existing AcceptButton if seen)
because user://privacy_accepted is a per-machine OS file
(config/use_custom_user_dir + custom_user_dir_name="data" in project.godot),
not something a fresh --qa-port launch can assume is already set.

S-C8-07 is a second rule, not boot plumbing: boot must reach the main menu
whether or not user://privacy_accepted already exists. It launches its own
second game instance with the flag pre-created (the way the game itself
writes it), instead of using the module-scoped `game` fixture (which always
deletes the flag first for the other six tests' own determinism). See
docs/northstar/plans/push/specs/C8.md "Findings" for the reproduced bug
this proves: SimBridge's sim_ready fires while SceneRouter is still
mid-transition from privacy_modal, go_to() drops the request, and nothing
ever retries it.
"""
from __future__ import annotations

import time

import pytest

from daemon_client import (
    GodotGame,
    control_center,
    control_names,
    find_control,
    pick_free_port,
    wait_for,
    write_privacy_flag,
)

PRIVACY_MODAL_SCENE = "res://scenes/privacy_modal/privacy_modal.tscn"
MAIN_MENU_SCENE = "res://scenes/main_menu/main_menu.tscn"
GALAXY_SCENE = "res://scenes/galaxy/galaxy_view.tscn"
MISSION_BRIEFING_SCENE = "res://scenes/mission_briefing/mission_briefing.tscn"
TACTICAL_SCENE = "res://scenes/tactical_c/tactical_view.tscn"
DEBRIEF_SCENE = "res://scenes/debrief/debrief.tscn"
CHRONICLE_SCENE = "res://scenes/world/chronicle_scroll_panel.tscn"

# SIM_STARTUP_TIMEOUT_SEC in autoload/sim_bridge.gd is 30s (a real python3
# simulation/pipe_transport.py subprocess) plus scene-router fade margin;
# every other step only swaps scenes locally, so 10s (the spec default) holds.
BOOT_TIMEOUT_S = 45.0
STEP_TIMEOUT_S = 10.0
PORT_TIMEOUT_S = 60.0
# S-C8-07's bug hangs forever (confirmed with a 90s wait while writing this
# test); 15s is plenty to prove red without burning minutes on every future
# run once it's fixed and green.
PRIVACY_FLAG_BOOT_TIMEOUT_S = 15.0

SCREENSHOT_HINT = (
    "user://qa/%s.png (globalized: ~/.local/share/data/qa/%s.png per "
    "project.godot's config/custom_user_dir_name=\"data\")"
)


@pytest.fixture(scope="module")
def game():
    port = pick_free_port()
    g = GodotGame(qa_port=port, seed=1)
    g.start()
    g.wait_for_port(timeout=PORT_TIMEOUT_S)
    try:
        yield g
    finally:
        g.stop()


def _shoot(client, name: str) -> None:
    client.screenshot(name)
    print("screenshot: " + SCREENSHOT_HINT % (name, name))


def _reach_main_menu(client) -> dict:
    deadline = time.monotonic() + BOOT_TIMEOUT_S
    clicked_privacy = False
    last_scene = None
    while time.monotonic() < deadline:
        resp = client.state()
        assert resp.get("ok"), "S-C8-01: state call failed: %r" % resp
        last_scene = resp["result"].get("scene")
        if last_scene == MAIN_MENU_SCENE:
            return resp["result"]
        if last_scene == PRIVACY_MODAL_SCENE and not clicked_privacy:
            accept = find_control(client.tree(), "AcceptButton")
            if accept is not None:
                cx, cy = control_center(accept)
                client.click(cx, cy)
                clicked_privacy = True
        time.sleep(0.5)
    tree_resp = client.tree()
    raise AssertionError(
        "S-C8-01: never reached main menu (%s) within %ss; last scene seen = %r; "
        "controls present = %r" % (MAIN_MENU_SCENE, BOOT_TIMEOUT_S, last_scene, control_names(tree_resp))
    )


def test_s_c8_01_boot_reaches_main_menu(game):
    client = game.client
    result = _reach_main_menu(client)
    assert result["scene"] == MAIN_MENU_SCENE
    _shoot(client, "flow_01_main_menu")


def test_s_c8_02_new_game_reaches_galaxy(game):
    client = game.client
    tree_resp = client.tree()
    control = find_control(tree_resp, "NewGame")
    assert control is not None, (
        "S-C8-02: control NewGame not found among %r (see button-name contract "
        "in docs/northstar/plans/push/specs/C8.md)" % control_names(tree_resp)
    )
    cx, cy = control_center(control)
    client.click(cx, cy)
    wait_for(client, lambda s: s.get("scene") == GALAXY_SCENE, STEP_TIMEOUT_S, label="S-C8-02")
    _shoot(client, "flow_02_galaxy")


def test_s_c8_03_mission_reaches_briefing(game):
    client = game.client
    tree_resp = client.tree()
    control = find_control(tree_resp, "Mission")
    assert control is not None, (
        "S-C8-03: control Mission not found among %r" % control_names(tree_resp)
    )
    cx, cy = control_center(control)
    client.click(cx, cy)
    wait_for(client, lambda s: s.get("scene") == MISSION_BRIEFING_SCENE, STEP_TIMEOUT_S, label="S-C8-03")
    _shoot(client, "flow_03_mission_briefing")


def test_s_c8_04_deploy_reaches_tactical(game):
    client = game.client
    tree_resp = client.tree()
    control = find_control(tree_resp, "Deploy")
    assert control is not None, (
        "S-C8-04: control Deploy not found among %r" % control_names(tree_resp)
    )
    cx, cy = control_center(control)
    client.click(cx, cy)
    wait_for(client, lambda s: s.get("scene") == TACTICAL_SCENE, STEP_TIMEOUT_S, label="S-C8-04")
    _shoot(client, "flow_04_tactical")


def test_s_c8_05_end_mission_reaches_chronicle(game):
    client = game.client
    tree_resp = client.tree()
    end_mission = find_control(tree_resp, "EndMission")
    assert end_mission is not None, (
        "S-C8-05: control EndMission not found among %r" % control_names(tree_resp)
    )
    cx, cy = control_center(end_mission)
    client.click(cx, cy)
    wait_for(client, lambda s: s.get("scene") == DEBRIEF_SCENE, STEP_TIMEOUT_S, label="S-C8-05 (debrief)")
    _shoot(client, "flow_05_debrief")

    tree_resp = client.tree()
    continue_ctrl = find_control(tree_resp, "Continue")
    assert continue_ctrl is not None, (
        "S-C8-05: control Continue not found among %r" % control_names(tree_resp)
    )
    cx, cy = control_center(continue_ctrl)
    client.click(cx, cy)

    def _reached_chronicle(state: dict) -> bool:
        # No scene named "world" is registered in scene_router.gd's SCENES
        # dict today. If the chronicle ends up its own routed scene, match
        # CHRONICLE_SCENE exactly; if it ends up embedded (e.g. inside
        # whatever scene eventually plays the debrief -> world transition),
        # accept ANY scene as long as ChronicleScrollPanel is present.
        if state.get("scene") == CHRONICLE_SCENE:
            return True
        return any("ChronicleScrollPanel" in name for name in control_names(client.tree()))

    wait_for(client, _reached_chronicle, STEP_TIMEOUT_S, label="S-C8-05 (chronicle)")
    _shoot(client, "flow_05_chronicle")


def test_s_c8_06_return_to_galaxy_then_shutdown(game):
    client = game.client
    tree_resp = client.tree()
    return_ctrl = find_control(tree_resp, "Return")
    assert return_ctrl is not None, (
        "S-C8-06: control Return not found among %r" % control_names(tree_resp)
    )
    cx, cy = control_center(return_ctrl)
    client.click(cx, cy)
    wait_for(client, lambda s: s.get("scene") == GALAXY_SCENE, STEP_TIMEOUT_S, label="S-C8-06")
    _shoot(client, "flow_06_return")

    resp = client.state()
    assert resp.get("ok"), "S-C8-06: daemon not responsive for final state check: %r" % resp

    game.stop()


def test_s_c8_07_boot_reaches_main_menu_with_privacy_flag_present():
    """Boot must reach the main menu whether or not user://privacy_accepted
    already exists (real players hit this on their second-ever launch).
    Uses its own game instance -- reset_privacy_flag=False so start() does
    not delete the flag this test just wrote."""
    write_privacy_flag()
    port = pick_free_port()
    g = GodotGame(qa_port=port, seed=1, reset_privacy_flag=False)
    g.start()
    try:
        g.wait_for_port(timeout=PORT_TIMEOUT_S)
        client = g.client
        deadline = time.monotonic() + PRIVACY_FLAG_BOOT_TIMEOUT_S
        last_scene = None
        while time.monotonic() < deadline:
            resp = client.state()
            assert resp.get("ok"), "S-C8-07: state call failed: %r" % resp
            last_scene = resp["result"].get("scene")
            if last_scene == MAIN_MENU_SCENE:
                return
            time.sleep(0.5)
        raise AssertionError(
            "S-C8-07: never reached main menu (%s) within %ss with "
            "user://privacy_accepted present; last scene seen = %r"
            % (MAIN_MENU_SCENE, PRIVACY_FLAG_BOOT_TIMEOUT_S, last_scene)
        )
    finally:
        g.stop()
