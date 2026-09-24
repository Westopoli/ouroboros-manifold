# spec: docs/northstar/plans/push/specs/C2.md::S-106/R-106-02
"""Piece C2-4: a conquest over the live persistent pipe session recolours the galaxy.

Launches the real game once per test under Xvfb, walks boot -> NewGame -> galaxy,
then advances the sim 200 ticks through the daemon's `step` verb (which the galaxy
scene forwards to its own qa_step, the way `plant` reaches qa_plant) with the full
strategic feature set the galaxy requests. The galaxy holds ONE pipe session open
(docs/architecture.md "persistent client session (v1.1)"), applies the streamed
deltas in place and redraws.

Rules proven (S-106/R-106-02: a region that changes owner is drawn in its new
owner's colour):
  C2-4-01  after 200 live ticks at least one region has a new owner.
  C2-4-02  every region whose owner changed shows its new owner's colour in
           qa_state()["region_colours"], and that colour differs from the one it had.
Positive control: the conquest-no-recolour plant leaves the colours stale after the
same run, so the same detector must report a failure on it.
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

GALAXY_SCENE = "res://scenes/galaxy/galaxy_view.tscn"
MAIN_MENU_SCENE = "res://scenes/main_menu/main_menu.tscn"
PRIVACY_MODAL_SCENE = "res://scenes/privacy_modal/privacy_modal.tscn"
BOOT_TIMEOUT_S = 45.0
STEP_TIMEOUT_S = 10.0
RUN_TIMEOUT_S = 30.0
STEPS = 200
COLOUR_TOLERANCE = 0.01


def _boot_to_galaxy(game: GodotGame) -> None:
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


def _qa(client) -> dict:
    return client.state()["result"]["qa"]


def _run_200_ticks(client) -> tuple[dict, dict]:
    before = _qa(client)
    resp = client.call("step", STEPS)
    assert resp.get("ok"), "step verb failed: %r" % resp
    deadline = time.monotonic() + RUN_TIMEOUT_S
    after = before
    while time.monotonic() < deadline:
        after = _qa(client)
        if int(after.get("tick", 0)) >= STEPS:
            break
        time.sleep(0.5)
    assert int(after.get("tick", 0)) >= STEPS, (
        "galaxy qa_state tick = %r after step %d and %ds (persistent session not advancing; qa keys = %r)"
        % (after.get("tick"), STEPS, RUN_TIMEOUT_S, sorted(after.keys()))
    )
    return before, after


def _recolour_failures(before: dict, after: dict) -> list[str]:
    problems = []
    changed = [
        i for i, owner in after["owners"].items()
        if int(before["owners"].get(i, owner)) != int(owner)
    ]
    if not changed:
        problems.append("C2-4-01: no region changed owner over %d ticks" % STEPS)
        return problems
    stale, wrong = [], []
    for i in changed:
        new_colour = after["region_colours"][i]
        want = after["owner_colours"][str(after["owners"][i])]
        if any(abs(a - b) > COLOUR_TOLERANCE for a, b in zip(new_colour, want)):
            wrong.append(i)
        if all(abs(a - b) <= COLOUR_TOLERANCE for a, b in zip(new_colour, before["region_colours"][i])):
            stale.append(i)
    if wrong:
        problems.append("C2-4-02: %d of %d conquered regions do not show their new owner's colour (e.g. region %s)" % (len(wrong), len(changed), wrong[0]))
    if stale:
        problems.append("C2-4-02: %d of %d conquered regions kept their old colour (e.g. region %s)" % (len(stale), len(changed), stale[0]))
    return problems


@pytest.fixture()
def galaxy_game():
    g = GodotGame(qa_port=pick_free_port(), seed=1)
    g.start()
    g.wait_for_port(timeout=60.0)
    try:
        _boot_to_galaxy(g)
        yield g
    finally:
        g.stop()


def test_c2_4_conquest_recolours_over_the_live_session(galaxy_game):
    before, after = _run_200_ticks(galaxy_game.client)
    problems = _recolour_failures(before, after)
    assert not problems, "; ".join(problems)


def test_control_conquest_no_recolour_trips_the_detector(galaxy_game):
    client = galaxy_game.client
    resp = client.call("plant", "conquest-no-recolour")
    assert resp.get("ok") and resp["result"].get("activated"), "plant did not activate: %r" % resp
    before, after = _run_200_ticks(client)
    problems = _recolour_failures(before, after)
    assert problems, (
        "control is dead: the detector reported no problem on a galaxy that skips recolouring "
        "after a conquest (%d owner changes)"
        % sum(1 for i, o in after["owners"].items() if int(before["owners"].get(i, o)) != int(o))
    )
