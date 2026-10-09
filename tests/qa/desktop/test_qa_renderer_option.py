"""Piece H-renderer: GodotGame takes a renderer choice (no Godot is launched here).

Contract under test (names fixed by this header):
  GodotGame(qa_port, ..., renderer="opengl3"|"vulkan")  -- default "opengl3"; env OM_QA_RENDERER overrides the default.
  GodotGame.godot_args() -> list[str]  -- the full argv start() would run; holds "--rendering-driver", <renderer>.
Story plays (plays/*/_play.py, plays/K/_k_common.py; whichever exist in the tree) start vulkan when
OM_QA_RENDERER is unset. Pixel and flow tests construct GodotGame without the argument and stay opengl3.
Open point left untested: explicit constructor argument versus a set env var (which wins).
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

import daemon_client
from daemon_client import GodotGame

HERE = Path(__file__).resolve().parent
HELPERS = sorted(p for pat in ("*/_play.py", "*/_k_common.py") for p in (HERE / "plays").glob(pat))


def driver(game) -> str:
    argv = game.godot_args()
    i = argv.index("--rendering-driver")
    return argv[i + 1]


def test_default_is_opengl3(monkeypatch):
    monkeypatch.delenv("OM_QA_RENDERER", raising=False)
    assert driver(GodotGame(qa_port=1)) == "opengl3"


@pytest.mark.parametrize("r", ["opengl3", "vulkan"])
def test_constructor_choice(monkeypatch, r):
    monkeypatch.delenv("OM_QA_RENDERER", raising=False)
    assert driver(GodotGame(qa_port=1, renderer=r)) == r


def test_env_overrides_default(monkeypatch):
    monkeypatch.setenv("OM_QA_RENDERER", "vulkan")
    assert driver(GodotGame(qa_port=1)) == "vulkan"


def test_start_uses_godot_args():
    assert hasattr(GodotGame, "godot_args"), "GodotGame.godot_args missing"


def test_plays_exist():
    assert HELPERS, "no story-play helper found under plays/"


@pytest.mark.parametrize("helper", HELPERS, ids=lambda p: "%s/%s" % (p.parent.name, p.name))
def test_story_plays_default_vulkan(monkeypatch, helper):
    monkeypatch.delenv("OM_QA_RENDERER", raising=False)
    made = []
    monkeypatch.setattr(GodotGame, "start", lambda self: made.append(self))
    monkeypatch.setattr(GodotGame, "wait_for_port", lambda self, timeout=0: None)
    spec = importlib.util.spec_from_file_location("play_" + helper.parent.name, helper)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    if hasattr(mod, "_to_tactical"):
        monkeypatch.setattr(mod, "_to_tactical", lambda *a, **k: None)
    starter = getattr(mod, "start_game", None) or getattr(mod, "start_ground_game", None)
    assert starter, "%s has no start_game/start_ground_game" % helper
    starter()
    assert made, "starter did not build a GodotGame"
    assert driver(made[0]) == "vulkan"
