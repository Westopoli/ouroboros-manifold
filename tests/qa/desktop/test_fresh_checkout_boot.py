# spec: docs/northstar/plans/archive/specs/2026-10-03-loop-fix-workflow-brief.md, Lane 2 (fresh checkout boots)
"""A fresh checkout (no .venv, no logs/ folder) on a machine whose Python has no
numpy must boot to the main menu, never to error_screen. Today autoload/sim_bridge.gd
spawns the legacy Python sim (simulation/pipe_transport.py), which needs numpy and a
logs/ folder, dies, and SimBridge routes to error_screen.

The numpy-less Python is forced, not assumed: a shim `python3`/`python` dir leads PATH
and PYTHONPATH carries a numpy.py that raises ImportError. The test never creates or
removes .venv or logs/ in the checkout; it fails loudly if either is present, because
then it would not be testing a fresh checkout.
"""
from __future__ import annotations

import os
import stat
import sys
import time

import pytest

from daemon_client import REPO_ROOT, GodotGame, control_center, find_control, pick_free_port

MAIN_MENU_SCENE = "res://scenes/main_menu/main_menu.tscn"
PRIVACY_MODAL_SCENE = "res://scenes/privacy_modal/privacy_modal.tscn"
ERROR_SCENE = "res://scenes/error_screen/error_screen.tscn"
BOOT_TIMEOUT_S = 60.0
HOLD_S = 12.0  # the legacy sim's death is detected within a frame or two; hold well past it


@pytest.fixture()
def game(tmp_path, monkeypatch):
    assert not (REPO_ROOT / "logs").exists(), "checkout has a logs/ folder; not a fresh checkout"
    assert not (REPO_ROOT / ".venv").exists(), "checkout has a .venv; not a fresh checkout"
    shim = tmp_path / "bin"
    shim.mkdir()
    for name in ("python3", "python"):
        p = shim / name
        p.write_text('#!/bin/sh\nexec "%s" "$@"\n' % os.path.realpath(sys.executable))
        p.chmod(p.stat().st_mode | stat.S_IEXEC)
    block = tmp_path / "nonumpy"
    block.mkdir()
    (block / "numpy.py").write_text('raise ImportError("numpy blocked by test_fresh_checkout_boot")\n')
    monkeypatch.setenv("PATH", "%s:%s" % (shim, os.environ["PATH"]))
    monkeypatch.setenv("PYTHONPATH", str(block))
    g = GodotGame(qa_port=pick_free_port(), seed=1)
    g.start()
    g.wait_for_port(timeout=BOOT_TIMEOUT_S)
    try:
        yield g
    finally:
        g.stop()


def test_fresh_checkout_boots_to_main_menu_without_numpy_or_logs(game):
    client = game.client
    deadline = time.monotonic() + BOOT_TIMEOUT_S
    clicked = False
    menu_since = None
    scenes: list[str] = []
    while time.monotonic() < deadline:
        scene = client.state()["result"].get("scene")
        if not scenes or scenes[-1] != scene:
            scenes.append(scene)
        assert scene != ERROR_SCENE, "booted to error_screen; scenes seen: %r" % (scenes,)
        if scene == PRIVACY_MODAL_SCENE and not clicked:
            accept = find_control(client.tree(), "AcceptButton")
            if accept is not None:
                client.click(*control_center(accept))
                clicked = True
        if scene == MAIN_MENU_SCENE:
            menu_since = menu_since or time.monotonic()
            if time.monotonic() - menu_since >= HOLD_S:
                return
        else:
            menu_since = None
        time.sleep(0.5)
    raise AssertionError("never held the main menu for %ss; scenes seen: %r" % (HOLD_S, scenes))
