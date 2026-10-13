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
    global _CLIENT, _FOLLOW
    _CLIENT, _FOLLOW = g.client, False
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


# DRAFT-scroll-cap-ticks (ledger, Architect draft; Westley owns the threshold)
SCROLL_STALL_TICKS = 60  # game ticks without camera movement (more than 1.0 wu, the TD-VG-A-9i number) before the scroll gives up
SCROLL_CAP_TICKS = 400  # game ticks (20 s game time) from the start of one scroll before it gives up
# DRAFT-a17-contact-budget (ledger TD-VG-A-12, Architect 2026-10-12 ruling 2; Westley's to change): game ticks of attack-move the S-134 and S-136 plays allow before first contact
CONTACT_BUDGET_TICKS = 5920
SCROLL_LOG: list = []  # one line per scroll (A17): wall s, game s, notches, scales, camera from and to, how it ended


def _zoom_out_fully(client) -> tuple:
    """A player zooms out with the wheel: one notch at a time while qa scale changes. client.call("input", "wheel", -1) is
    ONE notch OUT (n < 0 = WHEEL_DOWN, qa_driver.gd _do_wheel; the opposite sign zooms IN, TD-VG-C-1 lost a play to that).
    Returns (notches that changed the scale, the scale factor of the first notch). The last notch is clamped at the minimum
    zoom, so the same count of +1 notches restores a little more zoomed in than the saved scale (measured: 13 notches out,
    restored 0.8185 for a saved 0.6740); the caller predicts the restored scale as the scale out times factor ** notches."""
    w, h = (int(v) for v in RESOLUTION.split("x"))
    client.call("input", "move", w // 2, h // 2)  # the wheel acts at the pointer: keep it off the pan margin and HUD
    notches, scale, step = 0, qa(client)["scale"], 1.0
    while True:
        client.call("input", "wheel", -1)
        now = qa(client)["scale"]
        if now == scale:
            time.sleep(0.2)  # harness wait: the wheel event may land a frame later at 2 to 4 software fps
            now = qa(client)["scale"]
        if now == scale:
            return notches, step
        if notches == 0:
            step = scale / now
        notches, scale = notches + 1, now


def _zoom_restore(client, notches: int) -> None:
    for _ in range(notches):
        client.call("input", "wheel", 1)


def _edge_scroll_to(client, wx: float, wy: float, cam: dict) -> bool:
    """TD-VG-A-9i/9j/12: the edge-scroll method, measured in GAME ticks (qa_state tick), not wall seconds.

    R-103-09 (E-16): "Given the player pans by keys or by edge-scroll, When the zoom changes, Then the pan speed stays the
    same on screen, so the ground covered per second grows in proportion as the camera zooms out; the Settings pan-speed
    slider (R-110-02) scales that speed." Westley 2026-10-11: "more of a model doing the testing issue than an issue with
    the game's behaviour". Under the harness (--fixed-fps 30 at 2 to 4 software fps) one wall second is 0.075 to 0.13 game
    seconds, so a wall window sees about an eighth of the real pan rate; the scroll therefore stalls on SCROLL_STALL_TICKS
    and gives up on SCROLL_CAP_TICKS of game time, and before a scroll longer than one screen it zooms fully out with
    wheel notches as a player does (only when ground3d.present is false: the 3D rig keeps the old path, FU-A17-3d-scroll).

    Edge from the WORLD delta (wx, wy) minus camera, input move to 2 px inside the edge. Short scroll (no delta over
    SCREEN_WU, a named draft: a screen's worth of world at the start height): stop on two consecutive project on_screen
    polls. Long scroll: fully out, scroll until the camera is within the half-screen extent, at the restored scale, of the
    target on each axis (Architect 2026-10-12, A17 ruling 1), then restore the zoom by the same notch count; the target
    must then project on screen. Returns False with a distinct SCROLL_LOG line on stall, cap, or off screen after restore.
    Long = either delta over SCREEN_WU; each axis scrolls while outside the stop extent, the old both-axes rule picks the
    axes of a short scroll. The pointer goes back to the centre on every exit."""
    w, h = (int(v) for v in RESOLUTION.split("x"))
    SCREEN_WU = 3000.0
    ddx, ddy = wx - cam["x"], wy - cam["y"]
    both = abs(ddx) > SCREEN_WU and abs(ddy) > SCREEN_WU
    q0 = qa(client)
    tick0, scale0, wall0 = q0["tick"], q0["scale"], time.monotonic()
    cam0 = (q0["camera"]["x"], q0["camera"]["y"])
    far = max(abs(ddx), abs(ddy)) > SCREEN_WU and not q0["ground3d"].get("present")
    notches, scale_out, scale_back, how, hits, ticked, edge = 0, scale0, scale0, "arrival", 0, False, None
    cam1, end_tick = q0["camera"], tick0
    restored, polls = False, 0  # polls: near-pass polls run at the restored zoom (FINDING-edge-scroll-restore-overshoot)
    try:
        if far:
            notches, step = _zoom_out_fully(client)
            scale_out = qa(client)["scale"]
            scale_back = scale_out * step ** notches  # the scale the restore below reaches, the half-screen extent is taken at it
        start = qa(client)["tick"]  # the scroll itself starts here: the cap and the stall count from this tick
        last, last_move_tick = cam0, start
        half_x, half_y = (w / 2.0) / scale_back, (h / 2.0) / scale_back  # half a screen in wu at the scale the zoom is restored to
        while True:
            q = qa(client)
            c, tick = q["camera"], q["tick"]
            cam1, end_tick = c, tick
            dx, dy = wx - c["x"], wy - c["y"]
            if far:
                sx, sy = abs(dx) > half_x, abs(dy) > half_y
                if not (sx or sy):
                    # FINDING-edge-scroll-restore-overshoot: the pointer is released here, not in the finally (one qa plus one
                    # input round trip later at 13,300 wu/s full zoom-out is the 445 wu overshoot). Restore the zoom, then
                    # when the target is not on screen finish with the near pass below at the restored zoom (about 83 wu per poll).
                    client.call("input", "move", w // 2, h // 2)
                    edge = (w // 2, h // 2)
                    _zoom_restore(client, notches)
                    restored = True
                    r = client.call("project", float(wx), float(wy))
                    assert r.get("ok") is True, "play_support: FINDING: the project verb refused: %r" % r
                    if r["result"].get("on_screen"):
                        break
                    c = qa(client)["camera"]
                    far, both, hits = False, False, 0
                    start = qa(client)["tick"]  # the near pass counts its stall and cap from here
                    last, last_move_tick = (c["x"], c["y"]), start
                    continue
            else:
                sx = both or abs(dx) >= abs(dy)
                sy = both or abs(dy) > abs(dx)
            # the pointer pixel for this poll; the centre on an axis that is not scrolling; it is sent only when it changes
            want = ((w - 3 if dx > 0 else 2) if sx else w // 2, (h - 3 if dy > 0 else 2) if sy else h // 2)
            if want != edge:
                client.call("input", "move", want[0], want[1])
                edge = want
            time.sleep(0.2)  # harness wait between polls (wall clock); progress, stall and cap below are game ticks
            q = qa(client)
            c, tick = q["camera"], q["tick"]
            cam1, end_tick = c, tick
            if not ticked:
                assert tick > start, "play_support: premise: tick frozen (qa tick %d did not advance over the first poll window)" % tick
                ticked = True
            if not far:
                polls += 1
                r = client.call("project", float(wx), float(wy))
                assert r.get("ok") is True, "play_support: FINDING: the project verb refused: %r" % r
                hits = hits + 1 if r["result"].get("on_screen") else 0
                if hits >= 2:
                    break
            if abs(c["x"] - last[0]) > 1.0 or abs(c["y"] - last[1]) > 1.0:
                last, last_move_tick = (c["x"], c["y"]), tick
            if tick - last_move_tick >= SCROLL_STALL_TICKS:
                how = "stall"
                break
            if tick - start >= SCROLL_CAP_TICKS:
                how = "cap"
                break
    finally:
        client.call("input", "move", w // 2, h // 2)
        if far and not restored:
            _zoom_restore(client, notches)
        line = "SCROLL wall %.1f s, game %.1f s (%d ticks), notches %d, scale saved %.4f out %.4f restored %.4f, camera (%.0f, %.0f) to (%.0f, %.0f), ended by %s, converged %d polls" % (
            time.monotonic() - wall0, (end_tick - tick0) / 20.0, end_tick - tick0, notches, scale0, scale_out, qa(client)["scale"],
            cam0[0], cam0[1], cam1["x"], cam1["y"], how, polls)
        print(line)
        SCROLL_LOG.append(line)
    if how != "arrival":
        return False
    if far:
        r = client.call("project", float(wx), float(wy))
        assert r.get("ok") is True, "play_support: FINDING: the project verb refused: %r" % r
        if not r["result"].get("on_screen"):
            c = qa(client)["camera"]
            SCROLL_LOG.append("SCROLL off screen after the restore: target (%.0f, %.0f), camera (%.0f, %.0f)" % (wx, wy, c["x"], c["y"]))
            print(SCROLL_LOG[-1])
            return False
        return True
    return hits >= 2


def follow_army_on() -> None:
    """TD-VG-A-9j: after the attack-move order a player follows the army. Turns on the per-chunk follow in step_until."""
    global _FOLLOW
    _FOLLOW = True


def _pan_enemy_into_view(client) -> None:
    """TD-VG-A-9j: own-units centroid from qa_state; when project() says it is off screen, edge-scroll toward it (9i method)."""
    q = qa(client)
    me = q["local_faction"]
    mine = [u for u in q["units"].values() if u["faction"] == me]
    if not mine:
        return
    cx = sum(u["x"] for u in mine) / len(mine)
    cy = sum(u["y"] for u in mine) / len(mine)
    r = client.call("project", float(cx), float(cy))
    if r.get("ok") is True and not r["result"].get("on_screen"):
        _edge_scroll_to(client, cx, cy, q["camera"])


def step_until(client, pred, max_ticks: int, chunk: int = 5) -> bool:
    """Steps the mission chunk ticks at a time until pred(qa) holds; False when max_ticks pass first."""
    done = 0
    while done < max_ticks:
        if pred(qa(client)):
            return True
        client.call("step", chunk)
        if _FOLLOW and client is _CLIENT:
            _pan_enemy_into_view(client)
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
    w, h = (int(v) for v in RESOLUTION.split("x"))
    # TD-VG-A-9e/9g, A17: a player scrolls with real pointer input (no camera verb); before a scroll longer than one screen _edge_scroll_to zooms
    # out with the wheel and restores the zoom, and it measures game ticks, not wall seconds (the pan is a screen rate, 600 px/s, and A19 zoomed the opening frame about 14.5x). The edge is
    # chosen from the WORLD delta enemy minus camera, not from the projected pixel: a point behind the eye unprojects to a
    # mirrored pixel. The live pan (tactical_view.gd _pan_input) scrolls only after a mouse-motion event, so one move to the edge pixel is sent and the pointer stays there (TD-VG-A-9f: nudges
    # take it out of the margin and the pan runs in bursts). SCREEN_WU is a named draft (a screen's worth of world, 3000 wu at the start height): both axes
    # scroll only when both deltas exceed it; otherwise the larger one. on_screen must hold for two consecutive polls.
    if not r["result"].get("on_screen"):
        if not _edge_scroll_to(client, e["x"], e["y"], qa(client)["camera"]):
            c = qa(client)["camera"]
            assert False, "play_support: FINDING: enemy %s off screen, camera stopped making progress (%s, %s)" % (k, c["x"], c["y"])
        r = client.call("project", float(e["x"]), float(e["y"]))
    assert r["result"].get("on_screen"), "play_support: FINDING: enemy %s off screen after the edge scroll toward it" % k
    px, py = r["result"]["x"], r["result"]["y"]
    return int(min(max(px, 70), w - 70)), int(min(max(py, 70), h - 70))
