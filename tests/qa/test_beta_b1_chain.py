# spec: docs/stories/H-060.md (beta stage B1, plan docs/northstar/plans/2026-11-02-beta-staircase.md)
"""H-060 beta-b1-approved-screens: the approved screens chain to an empty field in the beta build.

Story H-060: "The main menu, galaxy view, and mission preparation screens are all approved, so those can be ported right in."
Story test lines proved here (Tests, word for word):
  1. "Headless with `OM_BETA=1`: `qa_state()` walks boot to main menu to galaxy to mission preparation to `beta_field` by the same verbs a player
     uses (the QA port), each screen's `scene` key named in order; positive control: without `OM_BETA`, Launch reaches `tactical_c`."
  2. "The picker exists on mission preparation with one entry under `OM_BETA=1` and is absent otherwise."
  3. "The story play: `scripts/play.sh --story H-060 --check` reaches `beta_field`."
Story Change lines: "mission preparation's Launch routes to it when the build is the beta (DRAFT: an `OM_BETA=1` env the `om-beta` launcher sets;
`tactical_c` otherwise)"; "A dev picker placeholder on mission preparation (DRAFT-variant-picker): an OptionButton labelled "variant" with one entry,
hidden unless `OM_BETA=1`"; "a HUD line "beta B1: field placeholder, sha"". Machine line: "Scene: res://scenes/beta/stage_field.tscn".

Premises dumped on the built tree (base 761c36cd origin/main, 2026-11-02), qa-port `state` replies and `tree` controls, seed 1, xvfb 1280x720:
  boot: scene = "res://scenes/privacy_modal/privacy_modal.tscn" (click AcceptButton, the spine's way), then
  main menu: scene = "res://scenes/main_menu/main_menu.tscn", qa.scene = "main_menu"; control "NewGame" (its label reads NEW CAMPAIGN);
  galaxy:   scene = "res://scenes/galaxy/galaxy_view.tscn", qa.tick counts up (the spine waits for >= 10); control "Mission";
  mission preparation = the briefing: scene = "res://scenes/mission_briefing/mission_briefing.tscn", qa.scene = "mission_briefing",
    qa.deploy_enabled = true; controls Deploy ("DEPLOY FORCES"), Refuse, TMButton ("BACK"); no OptionButton anywhere in the scene
    (inventory.nodes_by_name has no class OptionButton);
  Deploy today (OM_BETA unset AND OM_BETA=1): scene = "res://scenes/tactical_c/tactical_view.tscn" (the beta route does not exist yet).
The `scene` key throughout is the top-level `scene` of the daemon's `state` reply (the scene's res:// path), as tests/qa/desktop/test_flow_spine.py
reads it; `beta_field`'s is the story's own Machine line, res://scenes/beta/stage_field.tscn.

Names the story does not fix, accepted both ways here (reported as gaps, none invented):
  the button: the story says "Launch"; the scene's control is named "Deploy" (text "DEPLOY FORCES") and the story changes no screen, so Deploy is
    clicked, with a control named Launch (or whose text holds LAUNCH) accepted too;
  the picker: the story says an OptionButton "labelled" variant; a node named "variant" (any case), an OptionButton whose text holds "variant", or an
    OptionButton beside a label holding "variant" all count;
  the picker's one entry: not observable through the standing qa surface (see the gap in the report); the test checks the picker shows a non-empty
    selected entry (text of an OptionButton is its selected item), which a picker with no entry cannot.
Waits are harness waits, not rule thresholds.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tests" / "qa" / "desktop"))

from daemon_client import GodotGame, control_center, control_names, find_control, pick_free_port, wait_for  # noqa: E402

PRIVACY = "res://scenes/privacy_modal/privacy_modal.tscn"
MAIN_MENU = "res://scenes/main_menu/main_menu.tscn"
GALAXY = "res://scenes/galaxy/galaxy_view.tscn"
BRIEFING = "res://scenes/mission_briefing/mission_briefing.tscn"
TACTICAL = "res://scenes/tactical_c/tactical_view.tscn"
BETA_FIELD = "res://scenes/beta/stage_field.tscn"  # H-060 Machine line "Scene:"
BOOT_S = 45.0
STEP_S = 10.0
PORT_S = 60.0
AFTER_DEPLOY_S = 15.0
HUD_PREFIX = "beta B1: field placeholder"  # Change: 'a HUD line "beta B1: field placeholder, sha"'


@dataclass
class Walk:
    """One launch walked by the QA port: the scenes reached in order, the briefing's state and controls, the scene after Deploy."""
    scenes: list = field(default_factory=list)
    briefing_state: dict = field(default_factory=dict)
    briefing_controls: list = field(default_factory=list)
    after_state: dict = field(default_factory=dict)


def _click(client, name_options: tuple, label: str, text_options: tuple = ()) -> None:
    tree = client.tree()
    ctrl = next((find_control(tree, n) for n in name_options if find_control(tree, n)), None)
    if ctrl is None:
        up = [t.upper() for t in text_options]
        ctrl = next((c for c in tree["result"]["controls"] if any(u in str(c.get("text") or "").upper() for u in up)), None) if up else None
    assert ctrl is not None, "%s: none of the controls %r found among %r" % (label, name_options, control_names(tree))
    client.click(*control_center(ctrl))


def _walk(beta: bool) -> Walk:
    """Boot -> main menu -> galaxy -> mission preparation -> Deploy/Launch, only through the QA port's state/tree/click verbs."""
    saved = {k: os.environ.get(k) for k in ("OM_BETA", "XDG_DATA_HOME")}
    os.environ.pop("XDG_DATA_HOME", None)  # a private user dir under the game's scratch, so no stored profile or privacy flag leaks in
    if beta:
        os.environ["OM_BETA"] = "1"
    else:
        os.environ.pop("OM_BETA", None)
    g = GodotGame(pick_free_port(), seed=1)
    try:
        g.start()
        g.wait_for_port(PORT_S)
        for k, v in saved.items():  # the child has its environment already
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        c = g.client
        w = Walk()
        s = wait_for(c, lambda st: st.get("scene") in (PRIVACY, MAIN_MENU), BOOT_S, label="boot")
        if s["scene"] == PRIVACY:
            _click(c, ("AcceptButton",), "boot")
        wait_for(c, lambda st: st.get("scene") == MAIN_MENU, BOOT_S, label="main menu")
        w.scenes.append(MAIN_MENU)
        _click(c, ("NewGame",), "main menu")
        wait_for(c, lambda st: st.get("scene") == GALAXY, STEP_S, label="galaxy")
        w.scenes.append(GALAXY)
        wait_for(c, lambda st: int(st.get("qa", {}).get("tick", 0)) >= 10, STEP_S, label="galaxy tick 10")
        _click(c, ("Mission",), "galaxy")
        w.briefing_state = wait_for(c, lambda st: st.get("scene") == BRIEFING, STEP_S, label="mission preparation")
        w.scenes.append(BRIEFING)
        time.sleep(1.0)  # settle, the neighbouring plays' value
        w.briefing_state = c.state()["result"]
        w.briefing_controls = c.tree()["result"]["controls"]
        _click(c, ("Launch", "Deploy"), "mission preparation", ("LAUNCH",))
        want = BETA_FIELD if beta else TACTICAL
        deadline = time.monotonic() + AFTER_DEPLOY_S
        last: dict = {}
        while time.monotonic() < deadline:
            last = c.state()["result"]
            if last.get("scene") == want:
                break
            time.sleep(0.5)
        w.after_state = last
        w.scenes.append(last.get("scene"))
        return w
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        g.stop()
        shutil.rmtree(g.scratch, ignore_errors=True)


@pytest.fixture(scope="module")
def beta_walk() -> Walk:
    return _walk(True)


@pytest.fixture(scope="module")
def plain_walk() -> Walk:
    return _walk(False)


def _pickers(walk: Walk) -> list:
    """OptionButtons on mission preparation that read as the variant picker (see the module docstring for the accepted forms)."""
    options = [c for c in walk.briefing_controls if c.get("class") == "OptionButton"]
    texts = [str(t).lower() for t in walk.briefing_state.get("inventory", {}).get("hud_texts", {}).values()]
    label_there = any("variant" in t for t in texts)
    out = []
    for c in options:
        name = c["path"].rsplit("/", 1)[-1].lower()
        if "variant" in name or "variant" in str(c.get("text") or "").lower() or label_there:
            out.append(c)
    return out


def _option_buttons_anywhere(walk: Walk) -> list:
    """Every OptionButton on mission preparation, visible or hidden (inventory.nodes_by_name carries class and visible per node name)."""
    names = walk.briefing_state.get("inventory", {}).get("nodes_by_name", {})
    return [n for n, v in names.items() if v.get("class") == "OptionButton" and v.get("visible", True)]


# --- Test 1: the chain ----------------------------------------------------------------------------------------------------------------------

def test_control_without_om_beta_launch_reaches_tactical_c(plain_walk):
    """H-060 test 1 positive control (green today): "without `OM_BETA`, Launch reaches `tactical_c`". Also pins the walk itself: main menu, galaxy,
    mission preparation in order, so a red in the next test means the beta route is missing, not that the harness cannot walk."""
    assert plain_walk.scenes == [MAIN_MENU, GALAXY, BRIEFING, TACTICAL], "scenes reached without OM_BETA = %r" % (plain_walk.scenes,)


def test_chain_under_om_beta_reaches_mission_preparation(beta_walk):
    """H-060 test 1, first half (green today): with `OM_BETA=1` the same verbs reach main menu, galaxy and mission preparation, in order, each
    screen's scene key named; the approved screens are not changed by the beta."""
    assert beta_walk.scenes[:3] == [MAIN_MENU, GALAXY, BRIEFING], "scenes reached under OM_BETA=1 = %r" % (beta_walk.scenes,)


def test_chain_under_om_beta_launch_reaches_beta_field(beta_walk):
    """H-060 test 1: "Headless with `OM_BETA=1`: `qa_state()` walks boot to main menu to galaxy to mission preparation to `beta_field`". RED today:
    there is no `beta_field` route (no scenes/beta/stage_field.tscn), Launch still goes to tactical_c."""
    assert beta_walk.scenes == [MAIN_MENU, GALAXY, BRIEFING, BETA_FIELD], (
        "H-060: after Launch under OM_BETA=1 the scene is %r, wanted %s (SceneRouter has no beta_field route); scenes in order = %r"
        % (beta_walk.after_state.get("scene"), BETA_FIELD, beta_walk.scenes))


# --- Test 2: the picker ---------------------------------------------------------------------------------------------------------------------

def test_control_picker_absent_without_om_beta(plain_walk):
    """H-060 test 2 positive control and second half (green today): "The picker ... is absent otherwise." Without `OM_BETA` no OptionButton shows
    on mission preparation (inventory and controls both checked), and the inventory itself was read (the Deploy control is there)."""
    assert find_control({"result": {"controls": plain_walk.briefing_controls}}, "Deploy") is not None, "control: briefing tree lacks Deploy"
    assert _pickers(plain_walk) == [], "a variant picker shows on mission preparation without OM_BETA: %r" % (_pickers(plain_walk),)
    assert _option_buttons_anywhere(plain_walk) == [], "a visible OptionButton on mission preparation without OM_BETA: %r" % (_option_buttons_anywhere(plain_walk),)


def test_picker_present_under_om_beta(beta_walk):
    """H-060 test 2: "The picker exists on mission preparation with one entry under `OM_BETA=1`" (Change: 'an OptionButton labelled "variant" with one
    entry'). RED today: no OptionButton on mission preparation. The entry is checked as a non-empty selected text; the exactly-one count is a
    reported gap (no qa surface for item_count)."""
    found = _pickers(beta_walk)
    assert len(found) == 1, "H-060: %d variant pickers (OptionButton) on mission preparation under OM_BETA=1, wanted 1; OptionButtons anywhere = %r" % (
        len(found), _option_buttons_anywhere(beta_walk))
    assert str(found[0].get("text") or "").strip() != "", "H-060: the picker shows no selected entry (text empty): %r" % (found[0],)


# --- Test 3: the story play -----------------------------------------------------------------------------------------------------------------

class SceneGame(GodotGame):
    """GodotGame that opens a named scene the way play.sh does (godot ... <scene> -- --qa-port N), instead of project.godot's main scene."""

    def __init__(self, scene: str, *a, **kw):
        super().__init__(*a, **kw)
        self.scene = scene

    def godot_args(self, godot: str = "godot") -> list[str]:
        args = super().godot_args(godot)
        at = args.index("--fixed-fps")
        return args[:at] + [self.scene] + args[at:]


def _play_sh_scene() -> str:
    """The scene `scripts/play.sh --story H-060` launches, read from its own --dry-run launch line (no display, no build)."""
    r = subprocess.run(["bash", str(ROOT / "scripts" / "play.sh"), "--tree", str(ROOT), "--story", "H-060", "--dry-run"],
                       cwd=ROOT, capture_output=True, text=True, timeout=120)
    assert r.returncode == 0, "play.sh --story H-060 --dry-run exited %d: %s" % (r.returncode, (r.stdout + r.stderr)[-600:])
    launch = [ln for ln in r.stdout.splitlines() if ln.startswith("launch:")]
    assert launch, "no launch line in the dry run: %s" % r.stdout[-600:]
    scenes = [tok for tok in launch[0].split() if tok.startswith("res://")]
    assert scenes, "the launch line carries no res:// scene: %s" % launch[0]
    return scenes[0]


def test_control_story_play_launch_line_carries_the_scene():
    """H-060 test 3 positive control (green today): `scripts/play.sh --story H-060` launches the story's Machine-line scene, so the play below
    reaches the scene the story names. (The real `--check` needs the live desktop and play.lock; its launch is mirrored below under Xvfb the way
    tests/method/test_play.py mirrors it with --dry-run, and tests/qa/desktop/plays/ drive scenes by the same daemon.)"""
    assert _play_sh_scene() == BETA_FIELD


def test_story_play_reaches_beta_field_with_its_hud_line():
    """H-060 test 3: "`scripts/play.sh --story H-060 --check` reaches `beta_field`." The play launches the scene play.sh launches, under Xvfb, with
    --qa-port as --check does, and asserts the scene key and the inventory: the HUD line "beta B1: field placeholder, sha". RED today: scene
    res://scenes/beta/stage_field.tscn does not exist."""
    scene = _play_sh_scene()
    assert (ROOT / scene.replace("res://", "")).exists(), "H-060: %s does not exist, so play.sh --story H-060 --check cannot reach it" % scene
    saved = os.environ.pop("XDG_DATA_HOME", None)
    g = SceneGame(scene, pick_free_port(), seed=1)
    try:
        g.start()
        try:
            g.wait_for_port(PORT_S)
        except RuntimeError as e:
            raise AssertionError("H-060: godot exited before the qa port opened on %s: %s" % (scene, str(e)[-400:]))
        state = wait_for(g.client, lambda st: st.get("scene") == scene, STEP_S * 2, label="story play")
        hud = [str(t) for t in state["inventory"]["hud_texts"].values()]
        assert any(t.startswith(HUD_PREFIX) for t in hud), "H-060: no HUD line starting %r among %r" % (HUD_PREFIX, hud)
    finally:
        if saved is not None:
            os.environ["XDG_DATA_HOME"] = saved
        g.stop()
        shutil.rmtree(g.scratch, ignore_errors=True)
