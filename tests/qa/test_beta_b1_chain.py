# spec: docs/stories/H-060.md (beta stage B1, plan docs/northstar/plans/2026-11-02-beta-staircase.md)
"""H-060 beta-b1-approved-screens: the approved screens chain to an empty field in the beta build.

Story H-060: "The main menu, galaxy view, and mission preparation screens are all approved, so those can be ported right in."
Story test lines proved here (Tests, word for word):
  1. "Headless with `OM_BETA=1`: `qa_state()` walks boot to main menu to galaxy to mission preparation to `beta_field` by the same verbs a player
     uses (the QA port), each screen's `scene` key named in order; positive control: without `OM_BETA`, Launch reaches `tactical_c`."
  2. "The picker exists on mission preparation with one entry under `OM_BETA=1` and is absent otherwise."
  3. "The story play: `scripts/play.sh --story H-060 --check` reaches `beta_field`."
  4. "With `OM_BETA_BUILD_FILE` naming a planted file holding a 40-hex sha, the field HUD reads `beta B1: field placeholder, <first 8 hex>`; with it
     naming a missing file the HUD reads `..., dev`."
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

Names the story's "Rulings for the build" (2026-11-02, origin/main 1c2cce20) fix, pinned exactly here:
  1. "'Launch' in this story is the existing `Deploy` button ("DEPLOY FORCES") on mission preparation; no approved screen is relabelled."
  2. "The picker is an `OptionButton` named `VariantPicker` beside a `Label` whose text is `variant`."
  3. "Mission preparation's `qa_state()` gains an additive key `variant_picker: {count, selected}` (present only when `OM_BETA=1`); B1 pins `count == 1`".
     The key sits in the state reply's `qa` dict (where deploy_enabled is); `selected` is present but its value is not pinned (nobody gave one).
  4. "The field HUD reads `beta B1: field placeholder, <sha8>` ... read from a file `beta_build.txt` beside the exported binary ... and `dev` when the file
     is absent (runs from a checkout)." The story play runs from a checkout (godot beside no beta_build.txt), so its HUD must read "..., dev".
  5. "`OS.get_executable_path().get_base_dir().path_join("beta_build.txt")` by default, and the environment variable `OM_BETA_BUILD_FILE`, when set,
     names the file instead. The variable is a test seam only" (round-two ruling): the planted-file tests set it for the child process.
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
PLANTED_SHA = "0123abcd4567ef890123abcd4567ef890123abcd"  # 40 hex; the HUD must show its first 8, 0123abcd
HUD_DEV = "beta B1: field placeholder, dev"  # Ruling 4: `dev` when beta_build.txt is absent (a checkout run)


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
    """Boot -> main menu -> galaxy -> mission preparation -> Deploy, only through the QA port's state/tree/click verbs."""
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
        _click(c, ("Deploy",), "mission preparation")  # ruling 1: Launch is the Deploy button
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


def _nodes(walk: Walk) -> dict:
    return walk.briefing_state.get("inventory", {}).get("nodes_by_name", {})


def _label_texts(walk: Walk) -> list:
    return [str(t) for t in walk.briefing_state.get("inventory", {}).get("hud_texts", {}).values()]


def _visible_picker(walk: Walk):
    """The `VariantPicker` node entry when it is an OptionButton and visible, else None (ruling 2)."""
    n = _nodes(walk).get("VariantPicker")
    return n if n and n.get("class") == "OptionButton" and n.get("visible", True) else None


def _option_buttons_anywhere(walk: Walk) -> list:
    """Every visible OptionButton on mission preparation (inventory.nodes_by_name carries class and visible per node name)."""
    return [n for n, v in _nodes(walk).items() if v.get("class") == "OptionButton" and v.get("visible", True)]


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
    """H-060 test 2 positive control and second half (green today): "The picker exists on mission preparation with one entry under `OM_BETA=1` and is
    absent otherwise." Without `OM_BETA` no VariantPicker and no OptionButton shows on mission preparation, no Label reads `variant`, and `qa_state()`
    has no `variant_picker` key (ruling 3: "present only when `OM_BETA=1`"). The inventory itself was read (the Deploy control is there)."""
    assert find_control({"result": {"controls": plain_walk.briefing_controls}}, "Deploy") is not None, "control: briefing tree lacks Deploy"
    assert _visible_picker(plain_walk) is None, "a VariantPicker shows on mission preparation without OM_BETA: %r" % (_nodes(plain_walk).get("VariantPicker"),)
    assert _option_buttons_anywhere(plain_walk) == [], "a visible OptionButton on mission preparation without OM_BETA: %r" % (_option_buttons_anywhere(plain_walk),)
    assert "variant" not in _label_texts(plain_walk), "a Label reading `variant` on mission preparation without OM_BETA"
    assert "variant_picker" not in plain_walk.briefing_state.get("qa", {}), "qa_state has variant_picker without OM_BETA: %r" % (plain_walk.briefing_state.get("qa"),)


def test_picker_node_present_under_om_beta(beta_walk):
    """H-060 test 2 and ruling 2: "The picker exists on mission preparation ... under `OM_BETA=1`"; "The picker is an `OptionButton` named `VariantPicker`
    beside a `Label` whose text is `variant`." RED today: no VariantPicker node, no `variant` Label on mission preparation."""
    node = _visible_picker(beta_walk)
    assert node is not None, "H-060: no visible OptionButton named VariantPicker on mission preparation under OM_BETA=1; OptionButtons anywhere = %r, node = %r" % (
        _option_buttons_anywhere(beta_walk), _nodes(beta_walk).get("VariantPicker"))
    assert "variant" in _label_texts(beta_walk), "H-060: no Label with text `variant` beside the picker; texts = %r" % (_label_texts(beta_walk),)


def test_picker_qa_key_counts_one_entry_under_om_beta(beta_walk):
    """H-060 test 2 and ruling 3: "The picker exists ... with one entry under `OM_BETA=1`"; "Mission preparation's `qa_state()` gains an additive key
    `variant_picker: {count, selected}` (present only when `OM_BETA=1`); B1 pins `count == 1`". RED today: qa_state has no variant_picker key."""
    qa = beta_walk.briefing_state.get("qa", {})
    vp = qa.get("variant_picker")
    assert isinstance(vp, dict), "H-060: qa_state of mission preparation has no variant_picker dict under OM_BETA=1; qa keys = %r" % (sorted(qa),)
    assert "selected" in vp, "H-060: variant_picker lacks `selected`: %r" % (vp,)
    assert vp.get("count") == 1, "H-060: variant_picker.count = %r, wanted 1" % (vp.get("count"),)


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


def _story_play_hud(build_file: str | None) -> list:
    """Launch the scene play.sh launches under Xvfb with --qa-port, as --check does, and return the HUD texts of its state reply.
    `build_file` None leaves OM_BETA_BUILD_FILE unset (a checkout run); a string sets it for the child only."""
    scene = _play_sh_scene()
    assert (ROOT / scene.replace("res://", "")).exists(), "H-060: %s does not exist, so play.sh --story H-060 --check cannot reach it" % scene
    saved = {k: os.environ.get(k) for k in ("XDG_DATA_HOME", "OM_BETA_BUILD_FILE")}
    os.environ.pop("XDG_DATA_HOME", None)
    os.environ.pop("OM_BETA_BUILD_FILE", None)
    if build_file is not None:
        os.environ["OM_BETA_BUILD_FILE"] = build_file
    g = SceneGame(scene, pick_free_port(), seed=1)
    try:
        g.start()
        for k, v in saved.items():  # the child has its environment already
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        try:
            g.wait_for_port(PORT_S)
        except RuntimeError as e:
            raise AssertionError("H-060: godot exited before the qa port opened on %s: %s" % (scene, str(e)[-400:]))
        state = wait_for(g.client, lambda st: st.get("scene") == scene, STEP_S * 2, label="story play")
        return [str(t) for t in state["inventory"]["hud_texts"].values()]
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        g.stop()
        shutil.rmtree(g.scratch, ignore_errors=True)


def test_story_play_reaches_beta_field_with_its_hud_line():
    """H-060 test 3: "`scripts/play.sh --story H-060 --check` reaches `beta_field`." The play launches the scene play.sh launches, under Xvfb, with
    --qa-port as --check does, and asserts the scene key and the inventory: the HUD line, which reads `dev` from a checkout (ruling 4: "`dev` when the
    file is absent (runs from a checkout)"). RED today: scene
    res://scenes/beta/stage_field.tscn does not exist."""
    hud = _story_play_hud(None)
    assert HUD_DEV in hud, "H-060: no HUD line %r among %r" % (HUD_DEV, hud)


# --- Test 4: the sha on the HUD (rulings 4 and 5) ---------------------------------------------------------------------------------------------

def test_control_planted_build_file_fixture_is_a_40_hex_first_line(tmp_path):
    """H-060 test 4 positive control (green today): the planted file this test writes holds a 40-hex sha on its first line and its first 8 hex are
    what the HUD must show; the missing path is really missing. Checks the fixture, so a red below means the scene's read is missing."""
    f = tmp_path / "beta_build.txt"
    f.write_text(PLANTED_SHA + "\n")
    first = f.read_text().splitlines()[0]
    assert len(first) == 40 and all(c in "0123456789abcdef" for c in first) and first[:8] == PLANTED_SHA[:8]
    assert not (tmp_path / "absent_beta_build.txt").exists()


def test_story_play_hud_reads_first_8_hex_of_planted_build_file(tmp_path):
    """H-060 test 4 and ruling 5: "With `OM_BETA_BUILD_FILE` naming a planted file holding a 40-hex sha, the field HUD reads `beta B1: field
    placeholder, <first 8 hex>`"; ruling 4: "`<sha8>` is the first 8 hex of the build's sha, read from a file `beta_build.txt`". The variable is a test
    seam: "the environment variable `OM_BETA_BUILD_FILE`, when set, names the file instead". RED today: scenes/beta/stage_field.tscn does not exist."""
    f = tmp_path / "beta_build.txt"
    f.write_text(PLANTED_SHA + "\n")
    hud = _story_play_hud(str(f))
    want = "beta B1: field placeholder, " + PLANTED_SHA[:8]
    assert want in hud, "H-060: no HUD line %r among %r" % (want, hud)


def test_story_play_hud_reads_dev_when_build_file_env_names_a_missing_file(tmp_path):
    """H-060 test 4 and ruling 5: "with it naming a missing file the HUD reads `..., dev`"; ruling 4: "`dev` when the file is absent". Nothing sits
    beside the godot binary. RED today: scenes/beta/stage_field.tscn does not exist."""
    hud = _story_play_hud(str(tmp_path / "absent_beta_build.txt"))
    assert HUD_DEV in hud, "H-060: no HUD line %r among %r" % (HUD_DEV, hud)
