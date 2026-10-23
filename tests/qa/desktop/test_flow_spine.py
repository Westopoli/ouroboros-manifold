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

import json
import os
import shutil
import signal
import struct
import time
import zlib
from pathlib import Path

import numpy as np
import pytest

from daemon_client import (
    GodotGame,
    control_center,
    control_names,
    find_control,
    pick_free_port,
    wait_for,
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
    "user://qa/%s.png (globalized: <user dir>/qa/%s.png per "
    "project.godot's config/custom_user_dir_name=\"data\")"
)
# C5-3: tactical screenshot must differ from blank grey by this many pixels.
# 572 units drawn as ~1-px dots each give ~500 non-grey pixels; HUD text
# alone (0 units case) gives ~50-150. 300 is comfortably between the two.
MIN_TACTICAL_DIFF_PX = 300


def _real_saves_snapshot(game) -> dict:
    """Every file in the player's real save directory with its mtime and size."""
    root = game.user_dir / "saves"
    if not root.exists():
        return {}
    return {str(p): (p.stat().st_mtime_ns, p.stat().st_size) for p in root.rglob("*") if p.is_file()}


@pytest.fixture(scope="module")
def game(request):
    # HARNESS-flow-spine-teardown: the finalizer removes the scratch dir and kills the xvfb-run/godot
    # tree also when setup fails; the handlers run it on SIGTERM/SIGINT, which skip a generator's finally.
    started: list = []

    def teardown():
        for g in started:
            g.stop()
            shutil.rmtree(g.scratch, ignore_errors=True)
        started.clear()

    def on_signal(signum, frame):
        teardown()
        signal.signal(signum, signal.SIG_DFL)
        os.kill(os.getpid(), signum)

    old = {s: signal.signal(s, on_signal) for s in (signal.SIGTERM, signal.SIGINT)}

    def restore():
        for s, h in old.items():
            signal.signal(s, h)

    request.addfinalizer(restore)
    request.addfinalizer(teardown)
    port = pick_free_port()
    g = GodotGame(qa_port=port, seed=1)
    started.append(g)
    real_before = _real_saves_snapshot(g)
    g.start()
    g.wait_for_port(timeout=PORT_TIMEOUT_S)
    try:
        yield g
    finally:
        g.stop()
    # C1-3: the flow's autosaves (mission start, debrief, chronicle jump) went to the
    # per-run OM_SAVE_DIR; the player's real save directory must be untouched.
    assert _real_saves_snapshot(g) == real_before, "the flow wrote into the real save directory"
    assert any(g.save_dir.glob("campaign_*.omsave")), "control: the flow wrote no autosave at all into OM_SAVE_DIR"


def _autosave_meta(game) -> dict:
    """The mission-start/jump autosave's sidecar ({"tick","chapter",...}, docs/
    architecture.md "Save slots"; chapter is om_chapter_get_number). The client's
    qa_state does not expose the chapter number, so this is the one readable
    surface; the player's single campaign slot is rewritten at each autosave."""
    deadline = time.monotonic() + STEP_TIMEOUT_S
    while time.monotonic() < deadline:
        for p in sorted(game.save_dir.glob("campaign_*.omsave.json")):
            try:
                return json.loads(p.read_text())
            except ValueError:
                pass
        time.sleep(0.2)
    raise AssertionError("no campaign autosave sidecar in %s" % game.save_dir)


# Filled by test_s_c8_04 (state at mission 1 start), read by test_s_c8_09.
MISSION1 = {}


def _read_png_rgb(path: Path) -> "np.ndarray":
    """Minimal pure-Python PNG decoder; returns uint8 array (H, W, 3)."""
    data = path.read_bytes()
    assert data[:8] == b"\x89PNG\r\n\x1a\n", "not a PNG: %s" % path
    pos, width, height, depth, ctype = 8, 0, 0, 0, 0
    idat = b""
    while pos < len(data):
        (length,) = struct.unpack(">I", data[pos:pos + 4])
        tag = data[pos + 4:pos + 8]
        body = data[pos + 8:pos + 8 + length]
        if tag == b"IHDR":
            width, height, depth, ctype = struct.unpack(">IIBB", body[:10])
        elif tag == b"IDAT":
            idat += body
        pos += 12 + length
    assert depth == 8 and ctype in (2, 6), "unsupported PNG (depth %d type %d)" % (depth, ctype)
    bpp = 3 if ctype == 2 else 4
    raw = zlib.decompress(idat)
    stride = width * bpp
    out = np.zeros((height, stride), dtype=np.uint8)
    prev = np.zeros(stride, dtype=np.int32)
    offset = 0
    for y in range(height):
        ftype = raw[offset]
        line = np.frombuffer(raw, dtype=np.uint8, count=stride, offset=offset + 1).astype(np.int32)
        offset += 1 + stride
        if ftype == 0:
            cur = line
        elif ftype == 1:
            cur = line.copy()
            for x in range(bpp, stride):
                cur[x] = (cur[x] + cur[x - bpp]) & 255
        elif ftype == 2:
            cur = (line + prev) & 255
        elif ftype == 3:
            cur = line.copy()
            for x in range(stride):
                left = cur[x - bpp] if x >= bpp else 0
                cur[x] = (cur[x] + ((left + prev[x]) >> 1)) & 255
        elif ftype == 4:
            cur = line.copy()
            for x in range(stride):
                a = cur[x - bpp] if x >= bpp else 0
                b = prev[x]
                c = prev[x - bpp] if x >= bpp else 0
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                pred = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                cur[x] = (cur[x] + pred) & 255
        else:
            raise AssertionError("bad PNG filter %d" % ftype)
        out[y] = cur
        prev = cur
    return out.reshape(height, width, bpp)[:, :, :3]


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


def test_S_C8_08_galaxy_has_content(game):
    """P1 rung finding: scenes/galaxy/galaxy_view.gd:69 asks the live pipe
    for only 60 regions (below the 75-region feasibility floor for the
    default 15-faction generator), the pipe answers an error frame on
    set_seed, and the galaxy screen is empty in real play. Proves S-106/
    R-106-01 (docs/bible/epics/E-16-client-camera-hud-and-world-view.md)
    end to end through the daemon: the "state" frame must carry the current
    scene's qa_state() dict merged in under a "qa" key (autoload/
    qa_daemon.gd's state() does not do this yet -- the fix doer adds it),
    and that dict's system_count/owners must reflect an 80-region, at-least-
    partially-owned galaxy, not the empty one the 60-region request produces
    today."""
    client = game.client
    resp = client.state()
    assert resp.get("ok"), "S-C8-08: state call failed: %r" % resp
    result = resp["result"]
    assert "qa" in result, (
        "S-C8-08: state frame has no \"qa\" key -- autoload/qa_daemon.gd's state() "
        "must merge the current scene's qa_state() dict in under \"qa\" when the "
        "scene defines a qa_state() method; state result keys = %r" % sorted(result.keys())
    )
    qa = result["qa"]
    assert qa.get("system_count") == 80, (
        "S-C8-08: qa.system_count = %r, expected 80 (S-106/R-106-01; scenes/galaxy/"
        "galaxy_view.gd:69 _load_live_snapshot must request >= the 75-region "
        "feasibility floor, not 60)" % qa.get("system_count")
    )
    owners = qa.get("owners", {})
    assert len(owners) == 80, (
        "S-C8-08: qa.owners has %d entries, expected 80" % len(owners)
    )
    owned = sum(1 for v in owners.values() if int(v) >= 0)
    assert owned >= 1, "S-C8-08: qa.owners has no owned region (all -1); expected at least 1"


def test_s_c8_03_mission_reaches_briefing(game):
    client = game.client
    # C5-3: advance the galaxy 10 strategic ticks so the mission is archetype 3
    # (572 units); a tick-0 world is archetype 0 with 0 units. Mirrors
    # test_tactical_play.py::_to_tactical's step call. Test defect: the flow
    # never stepped the world before clicking Mission.
    client.call("step", 10)
    wait_for(client, lambda s: int(s.get("qa", {}).get("tick", 0)) >= 10, STEP_TIMEOUT_S, label="galaxy tick 10")
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
    MISSION1.update(_autosave_meta(game))  # chapter and tick as mission 1 starts
    # C4-4: Deploy is the player's Begin. It sends mission_begin over the shared session
    # and the tactical view then steps the begun mission (a mission still in recon
    # refuses the step and the view stays at tick 0). Since C5-6, the mission steps in
    # real time, so by the time this check runs the tick has already advanced past 1 --
    # the subject is "reached a live mission frame", not a frozen single step.
    tactical_qa = client.state()["result"].get("qa", {})
    assert int(tactical_qa.get("tick", -1)) >= 1, (
        "S-C8-04: tactical view tick = %r after Deploy, expected >= 1 (mission_begin then real-time stepping); qa = %r"
        % (tactical_qa.get("tick"), sorted(tactical_qa.keys()))
    )
    _shoot(client, "flow_04_tactical")
    # C5-3: units must be present and the reported count must match the live
    # tactical frame's own unit list (R-056-04: the galaxy now opens after the
    # opening jump, so the mission's composed force size is no longer a fixed
    # 572 -- read it from the frame instead of a magic number).
    unit_count = int(tactical_qa.get("unit_count", -1))
    units = tactical_qa.get("units", {})
    assert unit_count > 0, "S-C8-04: qa.unit_count = %r after Deploy, expected > 0" % unit_count
    assert unit_count == len(units), (
        "S-C8-04: qa.unit_count = %r does not match len(qa.units) = %r"
        % (unit_count, len(units))
    )
    # C5-3: tactical screenshot must not be blank grey -- the view must draw
    # unit markers. Use the median pixel value as the background reference so
    # the check is robust against the exact Godot clear colour.
    time.sleep(0.5)
    shot_path = client.user_dir / "qa" / "flow_04_tactical.png"
    assert shot_path.exists(), "S-C8-04: screenshot not written at %s" % shot_path
    shot = _read_png_rgb(shot_path)
    bg = int(np.median(shot))
    diff_px = int(np.any(np.abs(shot.astype(int) - bg) > 30, axis=2).sum())
    assert diff_px >= MIN_TACTICAL_DIFF_PX, (
        "S-C8-04: tactical screenshot looks blank (bg grey%d; %d pixels differ "
        "by > 30, need >= %d; unit markers must be drawn)"
        % (bg, diff_px, MIN_TACTICAL_DIFF_PX)
    )


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

    # C3-6: chronicle screen must have at least one rendered entry after the
    # strategic run and jump. Reads qa_state().entries via the daemon's state verb.
    chronicle_result = client.state().get("result", {})
    chronicle_qa = chronicle_result.get("qa", {})
    chronicle_entries = chronicle_qa.get("entries", [])
    assert len(chronicle_entries) >= 1, (
        "C3-6: chronicle screen has %d entries after end-mission jump; "
        "expected >= 1 (qa_state().entries = %r; if sim returns 0 entries "
        "this is blocked on sim csrc/chronicle.c)"
        % (len(chronicle_entries), chronicle_entries)
    )


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
    # The game keeps running: test_s_c8_09 plays the next chapter; the fixture stops it.


def test_s_c8_09_next_chapter_after_chronicle(game):
    """Proves the MVP loop closes: E-08 R-055-06 (chapter counter advances by
    one at the end of the jump that follows a mission), E-08 R-056-01 (a jump
    runs an integer number of strategic ticks in [20, 100]), E-08 R-055-01
    (chapter order: briefing, recon, mission, resolution, jump with chronicle,
    next briefing), E-10 R-074-04 (a mission deploys an enemy force and a
    player force). Starts from the galaxy test_s_c8_06 returned to.
    Not assertable: qa_state exposes no chapter number on any scene, so the
    chapter is read from the autosave sidecar the chronicle jump wrote."""
    client = game.client
    before = MISSION1
    assert before, "S-C8-09: test_s_c8_04 recorded no mission-1 autosave meta (run the whole module)"
    after = _autosave_meta(game)
    assert int(after["chapter"]) == int(before["chapter"]) + 1, (
        "S-C8-09: chapter after the mission-1 jump = %r, expected %r + 1 (R-055-06)"
        % (after.get("chapter"), before.get("chapter"))
    )
    state = client.state()["result"]
    assert state.get("scene") == GALAXY_SCENE, "S-C8-09: not on the galaxy: %r" % state.get("scene")
    jump_ticks = int(state["qa"]["tick"]) - int(before["tick"])
    assert 20 <= jump_ticks <= 100, (
        "S-C8-09: world tick advanced %d (from %r), expected an integer jump in [20, 100] (R-056-01)"
        % (jump_ticks, before.get("tick"))
    )

    control = find_control(client.tree(), "Mission")
    assert control is not None, "S-C8-09: no Mission control on the galaxy among %r" % control_names(client.tree())
    cx, cy = control_center(control)
    client.click(cx, cy)
    wait_for(client, lambda s: s.get("scene") == MISSION_BRIEFING_SCENE, STEP_TIMEOUT_S, label="S-C8-09 (briefing 2)")
    control = find_control(client.tree(), "Deploy")
    assert control is not None, "S-C8-09: no Deploy control on briefing 2 among %r" % control_names(client.tree())
    cx, cy = control_center(control)
    client.click(cx, cy)
    wait_for(client, lambda s: s.get("scene") == TACTICAL_SCENE, STEP_TIMEOUT_S, label="S-C8-09 (tactical 2)")
    tqa = client.state()["result"].get("qa", {})
    units = tqa.get("units", {})
    assert len(units) > 0, "S-C8-09: mission 2 has no units; qa = %r" % sorted(tqa.keys())
    factions = {int(u["faction"]) for u in units.values()}
    # Rulebook row 38 (K-h: "this assertion reads own units ... (RP, quoting K-h)"): the live game filters hidden units
    # (fog_filter, R-089-03), so qa.units holds the local faction's own units; enemies are not asserted.
    assert int(tqa.get("local_faction", -1)) in factions, (
        "S-C8-09: mission 2 needs own units present; factions present = %r, local_faction = %r"
        % (sorted(factions), tqa.get("local_faction"))
    )
    assert client.state()["result"].get("scene") == TACTICAL_SCENE, "S-C8-09: mission 2 is not running on the tactical scene"


def test_s_c8_07_boot_reaches_main_menu_with_privacy_flag_present():
    """Boot must reach the main menu whether or not user://privacy_accepted
    already exists (real players hit this on their second-ever launch).
    Uses its own game instance -- reset_privacy_flag=False so start() does
    not delete the flag this test just wrote."""
    port = pick_free_port()
    g = GodotGame(qa_port=port, seed=1, reset_privacy_flag=False)
    g.write_privacy_flag()
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
