# spec: docs/stories/H-041.md (Consumers, Tests, QA seam ruling 2026-11-02)
"""H-041, unit-scale-readthrough, CONSUMERS LANDING tests (phase 2 of the builder; the contract landing's tests are
tests/csim/test_collision_radius.py, already pushed).

Story H-041, Tests: "`tests/qa/test_unit_scale_readthrough.py` (headless): with Westley's file the registered radius per role
equals the file's radius; with the file missing the radius stays 15 and one warning line is printed; the drawn scale per role
follows the file's visual_scale."
Consumers (a): "reads `data/unit_scale.toml` at boot and calls the new function per role; a missing file or key keeps 15 with one
warning line." (b): "The game's unit drawing uses the file's `visual_scale` per role in place of the era default."
QA seam (Architect ruling): `tactical_view.qa_state()` gains the additive key `unit_scale`, one entry per role
`{radius, visual_scale, drawn_scale}`: radius = what c_bridge pushed to the roster at boot (15 on the missing-file fallback),
visual_scale = EraThemeResolver.get_unit_visual_scale(role) after the file is applied, drawn_scale = what units draw with
(UnitVisuals._vscale[type]), null when the tactical view is not up. Further rulings: ONE lookup, the file wins, the cap
MAX_VISUAL_SCALE 1.0 in scenes/tactical_c/unit_visuals.gd goes; the number means the H-023 scene's: drawn radius =
visual_scale x 15 wu, equal to the file's radius, so the unit's ground footprint radius must equal the file's radius.

PREMISES (dumped on the base tree, origin/main 9c9721ff merged into s/H-041-unit-scale-readthrough, 2026-11-02):
  * Launch: tests/qa/desktop/daemon_client.GodotGame (xvfb-run, --path REPO_ROOT, --qa-port), then the C5-3 route of
    tests/qa/desktop/test_tactical_play.py (boot, privacy Accept, NewGame, galaxy, step 10, Mission, Deploy) to scene
    res://scenes/tactical_c/tactical_view.tscn. state()["result"] = {scene, tick, qa, inventory}; qa = tactical_view.qa_state().
  * qa keys today (scenes/tactical_c/tactical_view.gd:569-595): scene "tactical_view", tick, plants, canvas, scale, unit_count, units,
    ... , inventory, sight_discs. There is NO `unit_scale` key today: every test that reads it is red for that one reason.
  * data/unit_scale.toml on this tree is Westley's (radius 4.05, 8.25, 11.25, 11.55, 21.6, 30.0; visual_scale 0.27 ... 2.0).
  * Era default today: EraThemeResolver.get_unit_visual_scale falls back to EraConfig.UNIT_VISUAL_SCALE (autoload/era_config.gd:11, 2.0);
    the settled_reach manifest overrides it per role (raider 1.0, interceptor 1.0, vanguard 1.5, warden 200.0, bombard 2.0, bastion 2.0)
    and UnitVisuals caps the drawn factor at 1.0. Ruling 1 retires both, so the missing-file test pins the constant 2.0 read from
    era_config.gd (see GAPS in the commit body).
  * The warning line: Godot push_warning prints "WARNING: <text>" then an indented "at: ..." line to stderr; the test counts stderr lines
    that mention "unit_scale" (case-insensitive) and are not "at:" frames. The builder's text must name the file.
  * The file-missing run cannot delete data/unit_scale.toml from the tree under test, and the story gives no path override, so it launches
    the same project through a symlink farm (every top-level entry, and every file of data/ except unit_scale.toml, linked).

CONTROLS (green on the base tree): the harness reaches the tactical view with the real file and with the farm; the farm lacks the file;
the real file is Westley's (no role at 15, so radius == file is not 15 == 15); the real-file run prints no unit_scale line (the detector
of the one-warning test sees an absent warning).
GAPS: the model's NATIVE footprint is not on any seam, so the footprint test pins footprint = 15 x drawn_scale (the H-023 meaning) against
the file's radius within tests/qa/unit_scale_park_footprint.py FOOTPRINT_TOL_PCT; measuring each model is the builder's, and if it derives a
drawn_scale that is not visual_scale the Architect picks which of the two assertions stands.
"""
from __future__ import annotations

import os
import re
import sys
import time
import tomllib
from pathlib import Path

import pytest

_QA = Path(__file__).resolve().parent
sys.path.insert(0, str(_QA / "desktop"))
sys.path.insert(0, str(_QA))
from daemon_client import GodotGame, REPO_ROOT, control_center, find_control, pick_free_port, wait_for  # noqa: E402
from unit_scale_park_footprint import FOOTPRINT_TOL_PCT, H023_BASE_RADIUS_WU  # noqa: E402

ROLES = ["Raider", "Interceptor", "Vanguard", "Warden", "Bombard", "Bastion"]
VALUES_FILE = REPO_ROOT / "data" / "unit_scale.toml"
FALLBACK_RADIUS = 15.0   # story: "a missing file or key keeps 15"
TACTICAL_SCENE = "res://scenes/tactical_c/tactical_view.tscn"
MAIN_MENU_SCENE = "res://scenes/main_menu/main_menu.tscn"
PRIVACY_MODAL_SCENE = "res://scenes/privacy_modal/privacy_modal.tscn"
GALAXY_SCENE = "res://scenes/galaxy/galaxy_view.tscn"
BRIEFING_SCENE = "res://scenes/mission_briefing/mission_briefing.tscn"
BOOT_TIMEOUT_S = 45.0
STEP_TIMEOUT_S = 30.0
EPS = 1e-6   # float round trip of a three-decimal toml number, not a rule tolerance


def _file_values() -> dict:
    raw = tomllib.loads(VALUES_FILE.read_text())
    return {r: {"radius": float(raw[r]["radius"]), "visual_scale": float(raw[r]["visual_scale"])} for r in ROLES}


def _era_default_scale() -> float:
    m = re.search(r"const\s+UNIT_VISUAL_SCALE\s*:\s*float\s*=\s*([0-9.]+)", (REPO_ROOT / "autoload" / "era_config.gd").read_text())
    assert m, "autoload/era_config.gd no longer declares UNIT_VISUAL_SCALE"
    return float(m.group(1))


class FarmGame(GodotGame):
    """The same game launched from a symlink farm of the project in which data/unit_scale.toml does not exist."""

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self.farm = self.scratch / "project_without_unit_scale"
        self.farm.mkdir()
        for entry in REPO_ROOT.iterdir():
            if entry.name in (".git", "data"):
                continue
            (self.farm / entry.name).symlink_to(entry)
        (self.farm / "data").mkdir()
        for entry in (REPO_ROOT / "data").iterdir():
            if entry.name != "unit_scale.toml":
                (self.farm / "data" / entry.name).symlink_to(entry)

    def godot_args(self, godot: str = "godot") -> list[str]:
        args = super().godot_args(godot)
        args[args.index(str(REPO_ROOT))] = str(self.farm)
        return args


def _to_tactical(game: GodotGame) -> None:
    """The C5-3 route of tests/qa/desktop/test_tactical_play.py."""
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


def _stderr_unit_scale_lines(game: GodotGame) -> list[str]:
    text = (game.out_dir / "stderr.log").read_text(errors="replace")
    return [ln for ln in text.splitlines() if "unit_scale" in ln.lower() and not ln.strip().startswith("at:")]


@pytest.fixture(scope="module")
def real_game():
    g = GodotGame(qa_port=pick_free_port(), seed=1, resolution="1920x1080")
    g.start()
    g.wait_for_port(timeout=60.0)
    try:
        _to_tactical(g)
        yield g
    finally:
        g.stop()


@pytest.fixture(scope="module")
def missing_game():
    g = FarmGame(qa_port=pick_free_port(), seed=1, resolution="1920x1080")
    g.start()
    g.wait_for_port(timeout=60.0)
    try:
        _to_tactical(g)
        yield g
    finally:
        g.stop()


def _qa(game: GodotGame) -> dict:
    return game.client.state()["result"]["qa"]


def _unit_scale(game: GodotGame) -> dict:
    """{role: {radius, visual_scale, drawn_scale}} from qa_state()["unit_scale"]; keyed by role name, case-insensitive."""
    qa = _qa(game)
    assert "unit_scale" in qa, "H-041: qa_state() has no `unit_scale` key (the QA seam is not built); qa keys = %s" % sorted(qa)
    raw = qa["unit_scale"]
    assert isinstance(raw, dict), "qa_state()['unit_scale'] must be a dict keyed by role, got %r" % (raw,)
    by_lower = {str(k).lower(): v for k, v in raw.items()}
    out = {}
    for r in ROLES:
        assert r.lower() in by_lower, "qa_state()['unit_scale'] has no entry for %s; keys = %s" % (r, sorted(raw))
        e = by_lower[r.lower()]
        for f in ("radius", "visual_scale", "drawn_scale"):
            assert f in e, "unit_scale[%s] lacks %r: %r" % (r, f, e)
        out[r] = e
    return out


# ---- controls (green today) ----------------------------------------------------------------------------------------

def test_H_041_control_the_values_file_is_westleys_and_not_the_15_fallback():
    """Control: data/unit_scale.toml holds Westley's six pairs (DEC-unit-scale-values-2026-11-02), none of them 15, so
    'radius equals the file' below cannot pass on the fallback."""
    v = _file_values()
    assert [v[r]["radius"] for r in ROLES] == [4.05, 8.25, 11.25, 11.55, 21.6, 30.0]
    assert [v[r]["visual_scale"] for r in ROLES] == [0.27, 0.55, 0.75, 0.77, 1.44, 2.0]


def test_H_041_control_harness_reaches_the_tactical_view_with_the_real_file(real_game):
    """Control (green today): the launch reaches the tactical view and qa_state() answers, so a red below is the missing key."""
    assert _qa(real_game).get("scene") == "tactical_view"


def test_H_041_control_harness_reaches_the_tactical_view_without_the_file(missing_game):
    """Control (green today): the symlink farm has no data/unit_scale.toml, the game still reaches the tactical view."""
    assert not (missing_game.farm / "data" / "unit_scale.toml").exists()
    assert (missing_game.farm / "data" / "loading_tips.json").exists()
    assert _qa(missing_game).get("scene") == "tactical_view"


def test_H_041_control_a_run_with_the_file_prints_no_unit_scale_line(real_game):
    """Control (green today, and after): with the file present no stderr line mentions unit_scale. Counterpart of the
    one-warning test: the line count is 0 here and exactly 1 there."""
    assert _stderr_unit_scale_lines(real_game) == []


# ---- with Westley's file -------------------------------------------------------------------------------------------

def test_H_041_with_the_file_each_roles_registered_radius_equals_the_files_radius(real_game):
    """H-041 Tests: "with Westley's file the registered radius per role equals the file's radius". Red today: no unit_scale key."""
    us, f = _unit_scale(real_game), _file_values()
    for r in ROLES:
        assert float(us[r]["radius"]) == pytest.approx(f[r]["radius"], abs=EPS), "%s: radius %r, file %r" % (r, us[r]["radius"], f[r]["radius"])


def test_H_041_with_the_file_each_roles_visual_scale_equals_the_files_visual_scale(real_game):
    """Seam ruling: visual_scale = EraThemeResolver.get_unit_visual_scale(role) after the file is applied, equal to the file's.
    Red today: no unit_scale key (and the resolver would answer the era manifest's value)."""
    us, f = _unit_scale(real_game), _file_values()
    for r in ROLES:
        assert float(us[r]["visual_scale"]) == pytest.approx(f[r]["visual_scale"], abs=EPS), "%s: %r, file %r" % (r, us[r]["visual_scale"], f[r]["visual_scale"])


def test_H_041_with_the_file_the_drawn_scale_follows_the_files_visual_scale(real_game):
    """H-041 Tests: "the drawn scale per role follows the file's visual_scale"; ruling 1: one lookup, the file wins, the
    MAX_VISUAL_SCALE 1.0 cap goes (Bombard 1.44 and Bastion 2.0 are over it). drawn_scale is non-null while the tactical
    view is up and equals visual_scale. Red today: no unit_scale key."""
    us, f = _unit_scale(real_game), _file_values()
    for r in ROLES:
        assert us[r]["drawn_scale"] is not None, "%s: drawn_scale is null while the tactical view is up" % r
        assert float(us[r]["drawn_scale"]) == pytest.approx(f[r]["visual_scale"], abs=EPS), "%s: drawn %r, file %r" % (r, us[r]["drawn_scale"], f[r]["visual_scale"])


def test_H_041_with_the_file_the_footprint_radius_equals_the_files_radius_within_the_parked_tolerance(real_game):
    """Ruling 2: the unit's ground footprint radius equals the file's radius. The footprint is computed as the H-023 scene
    draws it, H023_BASE_RADIUS_WU x drawn_scale (native model footprints are not on a seam, see GAPS), and may differ from
    the file's radius by FOOTPRINT_TOL_PCT percent (parked, Westley's). Red today: no unit_scale key."""
    us, f = _unit_scale(real_game), _file_values()
    for r in ROLES:
        footprint = H023_BASE_RADIUS_WU * float(us[r]["drawn_scale"])
        want = f[r]["radius"]
        assert abs(footprint - want) <= want * FOOTPRINT_TOL_PCT / 100.0, "%s: footprint %.3f wu, file radius %.3f, tolerance %.1f %%" % (r, footprint, want, FOOTPRINT_TOL_PCT)


def test_H_041_positive_control_the_footprint_detector_sees_a_wrong_scale():
    """Positive control of the footprint test: the same arithmetic rejects the capped scale (Bastion drawn at the old
    MAX_VISUAL_SCALE 1.0 gives a 15 wu footprint against 30) and accepts the file's value. Green today."""
    want = _file_values()["Bastion"]["radius"]
    tol = want * FOOTPRINT_TOL_PCT / 100.0
    assert abs(H023_BASE_RADIUS_WU * 1.0 - want) > tol
    assert abs(H023_BASE_RADIUS_WU * 2.0 - want) <= tol


# ---- with the file missing -----------------------------------------------------------------------------------------

def test_H_041_without_the_file_every_roles_radius_stays_15(missing_game):
    """H-041 Tests: "with the file missing the radius stays 15". Red today: no unit_scale key."""
    us = _unit_scale(missing_game)
    for r in ROLES:
        assert float(us[r]["radius"]) == FALLBACK_RADIUS, "%s: radius %r with no file" % (r, us[r]["radius"])


def test_H_041_without_the_file_visual_scale_is_the_era_default(missing_game):
    """Seam ruling: "with the file missing ... visual_scale is the era default". Ruling 1 retires the per-role manifest
    value, leaving EraConfig.UNIT_VISUAL_SCALE (2.0, read from autoload/era_config.gd). Red today: no unit_scale key."""
    us, want = _unit_scale(missing_game), _era_default_scale()
    for r in ROLES:
        assert float(us[r]["visual_scale"]) == pytest.approx(want, abs=EPS), "%s: %r, era default %r" % (r, us[r]["visual_scale"], want)


def test_H_041_without_the_file_exactly_one_warning_line_is_printed(missing_game):
    """H-041 Tests: "with the file missing ... one warning line is printed"; Consumers (a): "a missing file or key keeps 15 with
    one warning line". Exactly one stderr line mentions unit_scale. Red today: none is printed."""
    lines = _stderr_unit_scale_lines(missing_game)
    assert len(lines) == 1, "expected exactly one unit_scale warning line on stderr, got %d: %r" % (len(lines), lines)
    assert "warn" in lines[0].lower(), "the line is not a warning: %r" % lines[0]
