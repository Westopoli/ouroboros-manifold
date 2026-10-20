"""Shared driver for lane F story plays (not a test module).

A play drives the real game over the QA daemon like a player (real clicks, live clock), then saves one screenshot
and the qa_state JSON of the moment to docs/northstar/story_reviews/shots/<run id>/<story>_<moment>.{png,json}.
Run id: env PLAY_RUN_ID, else a UTC timestamp fixed per process. Pattern: tests/qa/desktop/test_flow_spine.py.
Run one play:  pytest tests/qa/desktop/plays/F/S-141.py

Q-F-1 (Westley, 2026-10-11, closed): "allowed, so long as the test does everything it can to emulate the reality of
two players joining and not taking shortcuts beyond what is strictly necessary given the limitation". So a match here
is two real game processes (a host and a guest, each with its own lobby) on the Steam-less local test network
(--net-local, VG-F-SKEL-A/B): the guest types the host's lobby id into its own lobby and joins, the host presses
Start, both reach the battle screen. No solo-host start, no net_loopback_start, no call into the lobby or NetMatch.
"""
from __future__ import annotations

import json
import math
import os
import shutil
import signal
import socket
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
PAIR_S = 45.0  # harness wait (join, match start), liberty 2026-10-11
# DRAFT-s140-settle-ticks (ledger docs/northstar/plans/push_ledger_2026-09-22.md): measured 781 game ticks x 1.5; game
# ticks, not wall seconds, A17's rule
SETTLE_TICKS = 1200
# 1080p is Westley's review resolution (memory: QA plays like the user, 1080p).
RESOLUTION = "1920x1080"


def start_game(seed: int = 1, extra_args: list[str] | None = None) -> GodotGame:
    g = GodotGame(qa_port=pick_free_port(), seed=seed, resolution=RESOLUTION, renderer="vulkan",
                  extra_args=extra_args)
    g.start()
    g.wait_for_port(timeout=PORT_S)
    return g


def note(*parts) -> None:
    """Premise dump line (visible with pytest -s)."""
    print("PREMISE", *parts, flush=True)


def _udp_free(port: int) -> bool:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.bind(("127.0.0.1", port))
        return True
    except OSError:
        return False
    finally:
        s.close()


def draw_ports() -> tuple[int, int, int, int]:
    """(host qa port, guest qa port, lobby port L, UDP base U) for one pair (batch-2 ruling 15). pick_free_port tests
    TCP only, so the UDP bind is the real check: L and U..U+3 (peer ids 0..3) must be free, distinct from each other
    and from the games' qa ports. The plays never use a hardcoded 47000 or 47100."""
    for _ in range(200):
        qa_h, qa_g, lobby, udp = (pick_free_port() for _ in range(4))
        block = range(udp, udp + 4)
        if len({qa_h, qa_g, lobby}) != 3 or lobby in block or qa_h in block or qa_g in block:
            continue
        if _udp_free(lobby) and all(_udp_free(p) for p in block):
            return qa_h, qa_g, lobby, udp
    raise RuntimeError("no free UDP ports found for the pair")


def pair_games(seed: int = 1, host_args: list[str] | None = None, guest_args: list[str] | None = None):
    """Generator for a module-scoped pytest fixture: yields (host, guest) GodotGame instances, both running, neither
    past the loading screen's privacy modal. Host 1920x1080 (the shots are the host's, review resolution); guest
    1280x720 (memory cap, spec Rev 12b F-SKEL (8)). Both are started before either answers the privacy modal: a
    privacy flag present at a game's boot leaves it on the loading screen (daemon_client.py GodotGame.start).
    host_args / guest_args: extra user args appended after the common ones (VG-F-S143, spec Rev 13 gap 2: the S-143
    pair case gives each side `--net-local-eras <id,id>`); default none, so every other pair play is unchanged."""
    qa_h, qa_g, lobby, udp = draw_ports()
    note("ports lobby L=%d udp base U=%d qa host=%d qa guest=%d" % (lobby, udp, qa_h, qa_g))
    # Both games get `--seed <seed>` (GodotGame, default 1): the lobby takes its match seed from it (ledger row
    # RULE-lobby-seed-arg), so host and guest runs are repeatable.
    common = ["--net-local", "--net-local-lobby-port", str(lobby), "--net-local-udp-base", str(udp)]
    host = GodotGame(qa_port=qa_h, seed=seed, resolution=RESOLUTION, renderer="vulkan",
                     extra_args=[*common, "--net-local-id", "1", *(host_args or [])])
    guest = GodotGame(qa_port=qa_g, seed=seed, resolution="1280x720", renderer="vulkan",
                      extra_args=[*common, "--net-local-id", "2", *(guest_args or [])])
    host.lobby_port = lobby  # read by reach_pair_lobby
    try:
        host.start()
        guest.start()
        host.wait_for_port(timeout=PORT_S)
        guest.wait_for_port(timeout=PORT_S)
        yield host, guest
    finally:
        guest.stop()
        host.stop()


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


def reach_main_menu_pair(host, guest) -> None:
    """Both games boot first; wait until both show the privacy modal, then accept on both."""
    clients = [host.client, guest.client]
    deadline = time.monotonic() + BOOT_S  # harness wait, liberty 2026-10-11
    while time.monotonic() < deadline:
        if all(c.state()["result"].get("scene") == PRIVACY for c in clients):
            break
        time.sleep(0.5)
    else:
        raise AssertionError("both games never showed the privacy modal: %r" %
                             [c.state()["result"].get("scene") for c in clients])
    for c in clients:
        click_named(c, "AcceptButton", "privacy")
    for c in clients:
        reach_main_menu(c)


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


def go_to_lobby(client) -> dict:
    reach_main_menu(client)
    click_text(client, "multiplayer", "menu")
    return wait_for(client, lambda s: s.get("scene") == LOBBY, STEP_S, label="lobby")


def lobby_qa(res: dict) -> dict:
    return res.get("qa", res)


def wait_until(predicate, timeout: float, label: str, poll: float = 0.5, why=None):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        v = predicate()
        if v:
            return v
        time.sleep(poll)
    raise AssertionError("%s: timed out after %ss%s" % (label, timeout, "; " + why() if why else ""))


def field_text(client, name: str) -> str | None:
    c = find_control(client.tree(), name)
    return None if c is None else str(c.get("text") or "")


def reach_pair_lobby(host, guest) -> tuple[dict, dict]:
    """Two players joining: stops at the two-member lobby (S-141 needs this far). Returns (host, guest) lobby results."""
    reach_main_menu_pair(host, guest)
    hc, gc = host.client, guest.client
    for c in (hc, gc):
        click_text(c, "multiplayer", "menu")
    wait_for(hc, lambda s: s.get("scene") == LOBBY, STEP_S, label="host lobby")
    gl = wait_for(gc, lambda s: s.get("scene") == LOBBY, STEP_S, label="guest lobby")
    # Positive control (green on any tree with a lobby): both games reached the lobby scene under --net-local, the
    # lobby qa_state has a members list, and the Host button exists. A red after this line means the feature is missing.
    hl = hc.state()["result"]
    for who, res, cl in (("host", hl, hc), ("guest", gl, gc)):
        assert "members" in lobby_qa(res), "CONTROL: %s lobby qa_state has no members list: %r" % (who, res)
        assert find_control(cl.tree(), "HostButton") is not None, "CONTROL: %s lobby has no HostButton" % who
        note(who, "lobby (before Host) qa:", json.dumps(lobby_qa(res), sort_keys=True),
             "controls:", sorted(control_names(cl.tree())), "StatusLine:", field_text(cl, "StatusLine"))
    lobby_id = str(host.lobby_port)
    click_named(hc, "HostButton", "host lobby")
    # The id appears only if the lobby-created event reached the lobby through the poll pump.
    wait_until(lambda: field_text(hc, "LobbyIdField") == lobby_id, STEP_S, "host LobbyIdField shows the lobby id",
               why=lambda: "LobbyIdField=%r, StatusLine=%r (a disabled HostButton leaves the field empty)" %
               (field_text(hc, "LobbyIdField"), field_text(hc, "StatusLine")))
    # The guest types the id as digit keys (there is no type-text verb); the digits are what a player would key in.
    click_named(gc, "LobbyIdField", "guest lobby")
    for ch in lobby_id:
        gc.call("input", "key", ch)
    typed = field_text(gc, "LobbyIdField")
    assert typed == lobby_id, "spec-gap: no way to type the lobby id (typed %r, wanted %r)" % (typed, lobby_id)
    note("digits typed into the guest LobbyIdField:", lobby_id)
    click_named(gc, "JoinButton", "guest lobby")
    h = wait_for(hc, lambda s: len(lobby_qa(s).get("members", [])) == 2, PAIR_S, label="host sees two members")
    g = wait_for(gc, lambda s: len(lobby_qa(s).get("members", [])) == 2, PAIR_S, label="guest sees two members")
    note("host lobby qa:", json.dumps(lobby_qa(h), sort_keys=True), "controls:", sorted(control_names(hc.tree())))
    note("guest lobby qa:", json.dumps(lobby_qa(g), sort_keys=True), "controls:", sorted(control_names(gc.tree())))
    return h, g


def start_pair_match(host, guest) -> tuple[dict, dict]:
    """Host presses Start in the two-member lobby; both games wait for the TACTICAL scene (the battle screen)."""
    reach_pair_lobby(host, guest)
    click_named(host.client, "StartButton", "host lobby")
    h = wait_for(host.client, lambda s: s.get("scene") == TACTICAL, PAIR_S, label="host match start")
    g = wait_for(guest.client, lambda s: s.get("scene") == TACTICAL, PAIR_S, label="guest match start")
    for who, res in (("host", h), ("guest", g)):
        qa = res["qa"]
        note(who, "tactical qa keys:", sorted(qa.keys()), "units:", len(qa["units"]), "tick:", qa["tick"])
    return h, g


def tactical_qa(client) -> dict:
    return client.state()["result"]["qa"]


def positions(client, uids) -> dict:
    """uid -> (x, y, layer) from the client's qa_state, exact values."""
    return unit_sample(client, uids)[1]


def unit_sample(client, uids) -> tuple[int, dict, dict]:
    """(tick, uid -> (x, y, layer), last_command) from ONE qa_state call, so the positions and the tick are the same
    frame."""
    qa = tactical_qa(client)
    units = qa["units"]
    pos = {u: (units[u]["x"], units[u]["y"], units[u]["layer"]) for u in uids if u in units}
    return int(qa["tick"]), pos, qa.get("last_command", {})


def _centroid(pos: dict) -> tuple[float, float]:
    n = len(pos)
    return sum(p[0] for p in pos.values()) / n, sum(p[1] for p in pos.values()) / n


def wait_settled(host, guest, uids, start: dict) -> tuple[dict, dict]:
    """After the host's order: both peers must show the same thing at a common tick (Architect ruling 2026-10-12; the
    story is that both peers see the same after an order, so the condition is equality, not rest). Settled = at a
    common game tick T >= order_tick + SETTLE_TICKS (order_tick = the host's tick when this is called, right after the
    right-click):
      (a) every ordered unit's (x, y, layer) from qa_state at T is byte-equal on host and guest (exact, no tolerance:
          determinism is the contract);
      (b) the ordered units' centroid at T is nearer the click point (the host's last_command x, y, world coords) than
          at the order tick (`start`) by at least half the starting distance, so a refused order cannot pass.
    Both peers are sampled in turn with the plain `state` verb, every (tick -> positions) kept from the target tick on;
    T is the lowest tick sampled on both. No pixel tolerance, no allowance list, no wall-clock deadline: the hang guard
    is the gate's per-play timeout, whose SIGTERM turns into a failure naming both ticks. Returns the host and guest
    positions at T."""
    order_tick, _, cmd = unit_sample(host.client, uids)
    target = order_tick + SETTLE_TICKS
    seen = {"h": order_tick, "g": None}  # last tick read on each peer, for the failure message

    def on_term(signum, frame):
        raise AssertionError("no common tick T >= %d (order tick %d + %d) sampled on both peers before the play "
                             "timeout: last host tick %r, last guest tick %r" %
                             (target, order_tick, SETTLE_TICKS, seen["h"], seen["g"]))

    old = signal.signal(signal.SIGTERM, on_term)
    try:
        hist_h, hist_g = {}, {}
        while True:
            for who, client, hist in (("h", host.client, hist_h), ("g", guest.client, hist_g)):
                tick, pos, c = unit_sample(client, uids)
                seen[who] = tick
                if who == "h" and c.get("x") is not None:
                    cmd = c
                if tick >= target:
                    hist[tick] = pos
            common = set(hist_h) & set(hist_g)
            if common:
                break
            time.sleep(0.005)
    finally:
        signal.signal(signal.SIGTERM, old)
    T = min(common)
    ph, pg = hist_h[T], hist_g[T]
    note("settle: order tick %d, common tick T=%d (%d ticks after the order); latest read host %d guest %d" %
         (order_tick, T, T - order_tick, seen["h"], seen["g"]))
    assert cmd.get("ok") is True and cmd.get("kind") == "move", "the host's order was refused: last_command %r" % (cmd,)
    for u in uids:
        assert ph.get(u) == pg.get(u), "unit %s differs at common tick: host tick %d %r, guest tick %d %r" % (u, T, ph.get(u), T, pg.get(u))
    assert set(ph) == set(pg) and ph, "tick %d: ordered units on host %r, on guest %r" % (T, sorted(ph), sorted(pg))
    click = (float(cmd["x"]), float(cmd["y"]))
    d0 = math.dist(_centroid(start), click)
    d1 = math.dist(_centroid(ph), click)
    assert d0 - d1 >= d0 / 2, ("the order made no progress: centroid %.1f from the click at the order tick, %.1f at "
                               "tick %d (needs at most %.1f)" % (d0, d1, T, d0 / 2))
    return ph, pg


def record(client, story: str, moment: str) -> dict:
    """Screenshot + qa_state of the moment, copied under the run id. Returns the qa_state result."""
    SHOT_DIR.mkdir(parents=True, exist_ok=True)
    name = f"{story}_{moment}"
    client.screenshot(name)
    src = client.user_dir / "qa" / f"{name}.png"
    deadline = time.monotonic() + 5
    while not src.exists() and time.monotonic() < deadline:
        time.sleep(0.1)
    assert src.exists(), "screenshot %s was not written" % src
    shutil.copy(src, SHOT_DIR / f"{name}.png")
    res = client.state()["result"]
    (SHOT_DIR / f"{name}.json").write_text(json.dumps(res, indent=2, sort_keys=True))
    return res
