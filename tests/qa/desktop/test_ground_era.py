# spec: docs/northstar/plans/2026-10-06-terrain-stage3-spec.md rev 3, piece 3e (and the 3d desktop line)
"""Piece 3e, desktop: `--era greek_placeholder` (space form) boots a ground era.

GodotGame gains `extra_args` (pre-flight: "daemon_client.py gains extra_args"; the args go after the
`--` with --qa-port and --seed). With `--era greek_placeholder` the walk menu -> galaxy -> mission ->
briefing -> tactical reaches `tactical_view`, and the tactical QA state names the ground layer: some
key of qa_state() containing "ground" with a truthy value (the key name is the card writer's; spec 3d:
"the QA state names the ground layer"). RED on origin/push/t3-contract: GodotGame has no extra_args.

CONTROL: the same walk with no --era leaves the ground-layer key absent or falsy, so the detector is
not always-true. Space-era frames stay as today ("Space: nothing added, screen byte-identical").
"""
from __future__ import annotations

import pytest

from daemon_client import GodotGame, pick_free_port
from test_tactical_play import _to_tactical


def _ground_keys(qa: dict) -> dict:
    # TD-T3-ground-keys: a dict value counts only when it says present.
    def _on(v):
        return bool(v.get("present")) if isinstance(v, dict) and "present" in v else bool(v)
    return {k: v for k, v in qa.items() if "ground" in str(k).lower() and _on(v)}


@pytest.fixture()
def ground_game():
    g = GodotGame(qa_port=pick_free_port(), seed=1, extra_args=["--era", "greek_placeholder"])
    g.start()
    g.wait_for_port(timeout=60.0)
    try:
        _to_tactical(g)
        yield g
    finally:
        g.stop()


@pytest.fixture()
def space_game():
    g = GodotGame(qa_port=pick_free_port(), seed=1)
    g.start()
    g.wait_for_port(timeout=60.0)
    try:
        _to_tactical(g)
        yield g
    finally:
        g.stop()


def test_3e_era_arg_reaches_tactical_with_a_ground_layer(ground_game):
    qa = ground_game.client.state()["result"]["qa"]
    assert _ground_keys(qa), "ground era (--era greek_placeholder): qa_state() names no ground layer; keys=%s" % sorted(qa)


def test_3e_control_space_era_has_no_ground_layer(space_game):
    qa = space_game.client.state()["result"]["qa"]
    assert not _ground_keys(qa), "CONTROL: a space-era tactical view reports a ground layer: %r" % _ground_keys(qa)
