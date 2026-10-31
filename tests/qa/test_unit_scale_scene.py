# spec: docs/stories/H-023.md (Scene, Values file, Tests; Machine lines)
"""H-023, unit-scale-comparison-scene: qa_state() element inventory, the slider-to-values-file write,
the four metrics per role, and the positive control.

Scene under test: res://scenes/proto/unit_scale/unit_scale.tscn (DRAFT path, story Machine lines).
Launched directly (not via the main menu) with the desktop QA daemon, the same GodotGame launcher
tests/qa/desktop/ uses; GodotScene below only adds the scene path ahead of the `--`.

PREMISES (dumped by running the harness on the base tree, see the commit body):
  * state() = {"scene": <scene_file_path>, "tick", "qa": <scene.qa_state()>, "inventory":
    {"nodes_by_name", "hud_texts"}} (autoload/qa_daemon.gd state()).
  * tree() = {"controls": [{"path", "class", "text", "rect_px"}...]}; a slider is a control whose class
    contains "Slider" and whose path names the role.
  * The story gives NO key names for qa_state(). These tests therefore match by the story's own words
    (role names, position names, metric words), case-insensitive, separators ignored, anywhere in the
    qa_state() tree (as a key or as a string value). The builder picks the exact keys; the Architect may
    freeze them afterwards. No value is pinned: stage size, radii and visual scales are builder or
    Westley drafts (story "Drafts for Westley"), so only presence, type and structure are asserted.
  * Stage-size draft: "shown on screen" (story) is checked as a HUD text mentioning "stage".

CONTROL (green on the base tree): CONTROL-harness reads an existing scene's qa_state() through the same
launcher; CONTROL-detector runs the inventory detector on a synthetic full state and on the same state
with one role removed. The story's own positive control, "a role removed from the scene fails the
inventory test", is test_h023_control_role_removed_fails_inventory (red today: the scene is missing).
"""
from __future__ import annotations

import copy
import json
import re
import sys
import time
import tomllib
from pathlib import Path

import pytest

_DESKTOP = Path(__file__).resolve().parent / "desktop"
sys.path.insert(0, str(_DESKTOP))
from daemon_client import GodotGame, REPO_ROOT, pick_free_port  # noqa: E402

SCENE = "res://scenes/proto/unit_scale/unit_scale.tscn"
VALUES_FILE = REPO_ROOT / "data" / "unit_scale.toml"
CONTROL_SCENE = "res://scenes/mockups/units/units_mockup.tscn"

# Story: "Roster: six baseline types, Raider, Interceptor, Vanguard, Warden, Bombard, Bastion".
ROLES = ["Raider", "Interceptor", "Vanguard", "Warden", "Bombard", "Bastion"]

# Story: "every E-17 node kind on land (objective, staging, transit, chokepoint, flank_route, vantage,
# hazard_anchor) plus a cover obstacle, a slope with height bands, and a city footprint".
# name -> list of normalized tokens, ALL of which must appear in one key or string value.
POSITIONS = {
    "objective": ["objective"],
    "staging": ["staging"],
    "transit": ["transit"],
    "chokepoint": ["chokepoint"],
    "flank_route": ["flankroute"],
    "vantage": ["vantage"],
    "hazard_anchor": ["hazardanchor"],
    "cover_obstacle": ["cover"],
    "slope": ["slope"],
    "height_bands": ["height", "band"],
    "city_footprint": ["city"],
}

# Story: "A metrics panel per role: radius in world units, units abreast across the narrowest choke on
# stage, units needed to ring the city footprint, seconds to cross the stage at walk speed."
METRICS = {
    "radius": "radius",
    "abreast": "abreast",
    "ring": "ring",
    "cross": "cross",
}


def _norm(s) -> str:
    return re.sub(r"[^a-z0-9]", "", str(s).lower())


# ---------------------------------------------------------------- qa_state tree helpers (detector)

def _walk(node, path=()):
    """Yield (path_tuple, key_or_None, value) for every dict entry and list element."""
    if isinstance(node, dict):
        for k, v in node.items():
            yield path, k, v
            yield from _walk(v, path + (k,))
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield path, None, v
            yield from _walk(v, path + (i,))


def _texts(node) -> list[str]:
    out = []
    for _p, k, v in _walk(node):
        if k is not None:
            out.append(_norm(k))
        if isinstance(v, str):
            out.append(_norm(v))
    return out


def _mentions(node, tokens: list[str]) -> bool:
    texts = _texts(node)
    return all(any(t in s for s in texts) for t in tokens)


def _role_records(qa, role: str) -> list:
    """Every dict/value that is 'the role': the value under a key naming it, or a dict holding a
    string value equal to the role (e.g. {"role": "Raider", ...})."""
    want = _norm(role)
    found = []
    stack = [qa]
    while stack:
        n = stack.pop()
        if isinstance(n, dict):
            for k, v in n.items():
                if _norm(k) == want:
                    found.append(v)
            if any(isinstance(v, str) and _norm(v) == want for v in n.values()):
                found.append(n)
            stack.extend(n.values())
        elif isinstance(n, list):
            stack.extend(n)
    return found


def _without_role(qa, role: str):
    """The same state with every key, record and list element naming the role removed
    (the story's 'a role removed from the scene')."""
    want = _norm(role)

    def clean(n):
        if isinstance(n, dict):
            if any(isinstance(v, str) and _norm(v) == want for v in n.values()):
                return None
            out = {}
            for k, v in n.items():
                if _norm(k) == want:
                    continue
                c = clean(v)
                if c is not None or v is None:
                    out[k] = c
            return out
        if isinstance(n, list):
            return [c for c in (clean(v) for v in n) if c is not None]
        if isinstance(n, str) and _norm(n) == want:
            return None
        return n

    return clean(copy.deepcopy(qa))


def missing_roles(qa) -> list[str]:
    return [r for r in ROLES if not _role_records(qa, r)]


def missing_positions(qa) -> list[str]:
    return [name for name, toks in POSITIONS.items() if not _mentions(qa, toks)]


def _numeric_under(record, token: str) -> list:
    """Numbers (not bool) under a key whose normalized name contains token, anywhere inside record."""
    vals = []
    for _p, k, v in _walk(record):
        if k is not None and token in _norm(k) and isinstance(v, (int, float)) and not isinstance(v, bool):
            vals.append(v)
    return vals


def missing_metrics(qa) -> list[str]:
    """role:metric pairs with no numeric value in any record of that role."""
    out = []
    for r in ROLES:
        recs = _role_records(qa, r)
        for m, tok in METRICS.items():
            if not any(_numeric_under(rec, tok) for rec in recs if isinstance(rec, (dict, list))):
                out.append("%s:%s" % (r, m))
    return out


def toml_problems(doc: dict) -> list[str]:
    """Story: 'one table per role, keys radius and visual_scale'."""
    bad = []
    for r in ROLES:
        key = next((k for k in doc if _norm(k) == _norm(r)), None)
        if key is None or not isinstance(doc[key], dict):
            bad.append("no table for %s" % r)
            continue
        for sub in ("radius", "visual_scale"):
            v = doc[key].get(sub)
            if isinstance(v, bool) or not isinstance(v, (int, float)) or v <= 0:
                bad.append("%s.%s not a positive number: %r" % (r, sub, v))
    return bad


def _synthetic_full_state() -> dict:
    """A compliant stand-in, used ONLY to show the detector works (CONTROL-detector)."""
    return {
        "roles": {r: {"radius": 15.0, "visual_scale": 1.0, "metrics": {
            "radius_world_units": 15.0, "units_abreast": 4, "units_to_ring_city": 30, "seconds_to_cross": 12.5}}
            for r in ROLES},
        "human_reference": {"height": 1.8},
        "positions": [{"kind": k} for k in (
            "objective", "staging", "transit", "chokepoint", "flank_route", "vantage", "hazard_anchor",
            "cover_obstacle", "slope", "height_bands", "city_footprint")],
    }


# ---------------------------------------------------------------- launcher

class GodotScene(GodotGame):
    """GodotGame with a scene path ahead of the `--` (Godot positional scene argument)."""

    def __init__(self, scene: str, **kw):
        super().__init__(**kw)
        self.scene = scene

    def godot_args(self, godot: str = "godot") -> list[str]:
        args = super().godot_args(godot)
        i = args.index("--")
        return args[:i] + [self.scene] + args[i:]


def _launch(scene: str) -> GodotScene:
    g = GodotScene(scene, qa_port=pick_free_port(), seed=1)
    g.start()
    g.wait_for_port(timeout=60.0)
    return g


def _settled_state(g: GodotScene, want_scene: str, timeout: float = 30.0) -> dict:
    deadline = time.monotonic() + timeout
    last = {}
    while time.monotonic() < deadline:
        resp = g.client.state()
        last = resp.get("result", {})
        if last.get("scene") == want_scene and "qa" in last:
            return last
        time.sleep(0.5)
    raise AssertionError("scene %s never reached with a qa_state(); last scene=%r, keys=%s"
                         % (want_scene, last.get("scene"), sorted(last)))


@pytest.fixture(scope="module")
def stage():
    """(game, state) or (None, reason): a launch failure is carried to the tests so each one fails on an
    assertion line naming the missing scene instead of erroring in setup."""
    g = None
    try:
        g = _launch(SCENE)
        yield g, _settled_state(g, SCENE)
    except (RuntimeError, TimeoutError, AssertionError) as e:
        yield None, "scene %s did not start: %s" % (SCENE, str(e).splitlines()[0] + " | " + " | ".join(
            ln.strip() for ln in str(e).splitlines() if "Cannot open file" in ln or "never reached" in ln))
    finally:
        if g is not None:
            g.stop()


def _live(stage):
    g, st = stage
    assert g is not None, st
    return g, st


@pytest.fixture()
def values_file_restored():
    """The scene writes data/unit_scale.toml into the checkout; put it back as found."""
    before = VALUES_FILE.read_bytes() if VALUES_FILE.exists() else None
    try:
        yield before
    finally:
        if before is None:
            VALUES_FILE.unlink(missing_ok=True)
        else:
            VALUES_FILE.write_bytes(before)


# ---------------------------------------------------------------- CONTROLS (green on the base tree)

def test_h023_control_harness_reads_an_existing_scene_qa_state():
    """CONTROL-harness (H-023 "`qa_state()` element inventory"): the same launcher, pointed at an existing
    scene, returns that scene's path and a qa_state() dict, so a red below means the feature is missing,
    not that the harness is broken."""
    g = _launch(CONTROL_SCENE)
    try:
        st = _settled_state(g, CONTROL_SCENE)
        assert isinstance(st["qa"], dict) and st["qa"], "existing scene returned an empty qa_state()"
        assert "inventory" in st
    finally:
        g.stop()


def test_h023_control_detector_flags_a_removed_role():
    """CONTROL-detector (H-023 "Positive control: a role removed from the scene fails the inventory
    test"): the inventory detectors pass a full synthetic state and each fails once its role is removed."""
    full = _synthetic_full_state()
    assert missing_roles(full) == []
    assert missing_positions(full) == []
    assert missing_metrics(full) == []
    for r in ROLES:
        cut = _without_role(full, r)
        assert missing_roles(cut) == [r], "detector did not flag removed role %s: %r" % (r, missing_roles(cut))
    assert toml_problems({r: {"radius": 15, "visual_scale": 1.0} for r in ROLES}) == []
    assert toml_problems({r: {"radius": 15, "visual_scale": 1.0} for r in ROLES[:-1]}) == ["no table for Bastion"]


# ---------------------------------------------------------------- RED: the scene and the values file

def test_h023_scene_loads_with_a_qa_state(stage):
    """H-023 Machine lines "Scene: res://scenes/proto/unit_scale/unit_scale.tscn": one Godot scene, a
    comparison stage, that answers qa_state() through the desktop QA daemon."""
    _g, st = _live(stage)
    assert st["scene"] == SCENE
    assert isinstance(st["qa"], dict) and st["qa"]


def test_h023_inventory_every_role_present(stage):
    """H-023 Tests "`qa_state()` element inventory: every role present": Raider, Interceptor, Vanguard,
    Warden, Bombard, Bastion each appear in qa_state(), "every unit role above standing beside a
    human-height reference" (a human reference is present too)."""
    _g, st = _live(stage)
    qa = st["qa"]
    assert missing_roles(qa) == [], "roles missing from qa_state(): %r; keys=%s" % (missing_roles(qa), sorted(qa))
    assert _mentions(qa, ["human"]), "no human-height reference in qa_state(); keys=%s" % sorted(qa)


def test_h023_inventory_every_position_present(stage):
    """H-023 Tests "every position present": "every E-17 node kind on land (objective, staging, transit,
    chokepoint, flank_route, vantage, hazard_anchor) plus a cover obstacle, a slope with height bands, and
    a city footprint"."""
    _g, st = _live(stage)
    qa = st["qa"]
    assert missing_positions(qa) == [], "positions missing from qa_state(): %r; keys=%s" % (missing_positions(qa), sorted(qa))


def test_h023_four_metrics_per_role(stage):
    """H-023 Scene "A metrics panel per role: radius in world units, units abreast across the narrowest
    choke on stage, units needed to ring the city footprint, seconds to cross the stage at walk speed":
    each role carries four numeric metrics in qa_state() (no value is pinned: the stage size is the
    builder's draft)."""
    _g, st = _live(stage)
    assert missing_metrics(st["qa"]) == [], "role:metric pairs with no number: %r" % missing_metrics(st["qa"])


def test_h023_stage_size_shown_on_screen(stage):
    """H-023 Drafts for Westley "the stage size is the builder's draft and is shown on screen": some HUD
    text mentions the stage."""
    _g, st = _live(stage)
    texts = st.get("inventory", {}).get("hud_texts", {})
    assert any("stage" in str(v).lower() or "stage" in str(k).lower() for k, v in texts.items()), \
        "no HUD text mentions the stage size; hud_texts=%r" % texts


def test_h023_control_role_removed_fails_inventory(stage):
    """H-023 Tests "Positive control: a role removed from the scene fails the inventory test": the
    inventory detector passes the live scene's qa_state() and flags exactly the role cut from it."""
    _g, st = _live(stage)
    qa = st["qa"]
    assert missing_roles(qa) == [], "live scene already lacks roles %r" % missing_roles(qa)
    for r in ROLES:
        cut = _without_role(qa, r)
        assert missing_roles(cut) == [r], "removing %s from the live qa_state() was not flagged: %r" % (r, missing_roles(cut))


def test_h023_one_slider_per_role(stage):
    """H-023 Scene "A sliders panel, one per role, that scales the unit live": the control tree holds a
    slider control naming each role."""
    g, _st = _live(stage)
    controls = g.client.tree().get("result", {}).get("controls", [])
    sliders = [c for c in controls if "Slider" in c.get("class", "")]
    absent = [r for r in ROLES if not any(r.lower() in c["path"].lower() for c in sliders)]
    assert absent == [], "no slider for roles %r; slider paths=%r" % (absent, [c["path"] for c in sliders])


def test_h023_slider_change_writes_values_file(stage, values_file_restored):
    """H-023 Tests "a slider change writes the file" and Values file "`data/unit_scale.toml`: one table per
    role, keys radius and visual_scale": moving a role's slider rewrites the file with a table per role
    and a different visual_scale for the moved role."""
    g, _st = _live(stage)
    controls = g.client.tree().get("result", {}).get("controls", [])
    role = ROLES[0]
    slider = next((c for c in controls if "Slider" in c.get("class", "") and role.lower() in c["path"].lower()), None)
    assert slider is not None, "no slider for %s; control classes=%r" % (role, sorted({c.get("class") for c in controls}))
    x, y, w, h = slider["rect_px"]
    seen = []
    for frac in (0.1, 0.9):
        VALUES_FILE.unlink(missing_ok=True)
        g.client.click(x + w * frac, y + h / 2.0)
        deadline = time.monotonic() + 10.0
        while time.monotonic() < deadline and not VALUES_FILE.exists():
            time.sleep(0.25)
        assert VALUES_FILE.exists(), "slider click at %.0f%% wrote no %s" % (frac * 100, VALUES_FILE)
        time.sleep(0.5)
        doc = tomllib.loads(VALUES_FILE.read_text())
        assert toml_problems(doc) == [], "values file shape: %r" % toml_problems(doc)
        key = next(k for k in doc if _norm(k) == _norm(role))
        seen.append(doc[key]["visual_scale"])
    assert seen[0] != seen[1], "moving the %s slider from 10%% to 90%% left visual_scale at %r" % (role, seen[0])
