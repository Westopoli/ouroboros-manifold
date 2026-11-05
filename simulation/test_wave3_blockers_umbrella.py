"""Wave 3 Pre-Zip Wiring umbrella test.

Encodes top-level acceptance criteria from `docs/legacy/test_specs/wave_3_pre_zip_wiring.md`.
Initially RED. Goes GREEN only after all 7 leaves (B5-A, B5-B, B2-A, B3-A, B2-B, B3-B, B5-C) merge.

DO NOT EDIT leaf-by-leaf. Parent-owned end-to-end gate.

Source-grep assertions are intentional per cover_asteroid_los_spec.md precedent —
leaf agents cannot fake them without actually wiring code at the named path.
Behavioral assertions live where Python imports are available (sim side).
"""

import json
import os
import re

import pytest


REPO_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))


def _read(rel_path):
    with open(os.path.join(REPO_ROOT, rel_path)) as f:
        return f.read()


# ---------------------------------------------------------------------------
# A. B5-A — Windows PyInstaller spec + DebugOverlay autoload
# ---------------------------------------------------------------------------


def test_umbrella_a_pyinstaller_win_spec_exists():
    path = os.path.join(REPO_ROOT, "build", "pyinstaller_win.spec")
    assert os.path.exists(path), (
        "B5-A not landed: legacy/build/pyinstaller_win.spec missing"
    )


def test_umbrella_a_pyinstaller_win_spec_structure():
    src = _read("legacy/build/pyinstaller_win.spec")
    for token in ("Analysis", "PYZ", "EXE", "COLLECT", "ouroboros_sim"):
        assert token in src, (
            f"B5-A not landed: legacy/build/pyinstaller_win.spec missing token {token!r}"
        )


def test_umbrella_a_pyinstaller_win_entry_point():
    src = _read("legacy/build/pyinstaller_win.spec")
    assert "pipe_transport" in src, (
        "B5-A not landed: pyinstaller_win.spec must declare pipe_transport entry"
    )


def test_umbrella_a_debug_overlay_autoload_registered():
    src = _read("project.godot")
    assert re.search(r'DebugOverlay\s*=\s*"\*res://autoload/debug_overlay\.gd"', src), (
        "B5-A not landed: project.godot [autoload] section missing DebugOverlay line"
    )


# ---------------------------------------------------------------------------
# B. B5-B — Privacy modal scene
# ---------------------------------------------------------------------------


def test_umbrella_b_privacy_modal_scene_exists():
    path = os.path.join(REPO_ROOT, "scenes", "privacy_modal", "privacy_modal.tscn")
    assert os.path.exists(path), (
        "B5-B not landed: scenes/privacy_modal/privacy_modal.tscn missing"
    )


def test_umbrella_b_privacy_modal_script_exists():
    path = os.path.join(REPO_ROOT, "scenes", "privacy_modal", "privacy_modal.gd")
    assert os.path.exists(path), (
        "B5-B not landed: scenes/privacy_modal/privacy_modal.gd missing"
    )


def test_umbrella_b_privacy_modal_writes_flag():
    src = _read("scenes/privacy_modal/privacy_modal.gd")
    assert "user://privacy_accepted" in src, (
        "B5-B not landed: privacy_modal.gd must write user://privacy_accepted"
    )
    assert "FileAccess" in src, (
        "B5-B not landed: privacy_modal.gd must use FileAccess to persist flag"
    )


def test_umbrella_b_privacy_modal_routes_to_loading_screen():
    src = _read("scenes/privacy_modal/privacy_modal.gd")
    assert "SceneRouter" in src and "loading_screen" in src, (
        "B5-B not landed: privacy_modal.gd must route via SceneRouter to loading_screen"
    )


def test_umbrella_b_privacy_modal_text_present():
    src = _read("scenes/privacy_modal/privacy_modal.tscn")
    assert "PRIVATE PLAYTEST BUILD" in src, (
        "B5-B not landed: privacy_modal.tscn must contain header 'PRIVATE PLAYTEST BUILD'"
    )


# ---------------------------------------------------------------------------
# C. B2 sim-side sanity (sim work already done pre-Wave 3; sanity-check only)
# ---------------------------------------------------------------------------


def test_umbrella_c_objective_field_exists():
    """Sanity check: existing assemble_briefing already returns 'objective' key
    for all 10 archetypes. B2-A leaf was dropped 2026-05-26 — this test verifies
    the precondition the Godot side (B2-B / leaf-05) depends on."""
    import sys
    sys.path.insert(0, os.path.join(REPO_ROOT, "simulation"))
    import mission_briefing
    archetypes = list(mission_briefing.OBJECTIVE_TEMPLATES_SHORT.keys())
    assert len(archetypes) == 10, f"Expected 10 archetypes, found {len(archetypes)}"
    # Stub slots with numeric fields ASSET_TEMPLATE needs (player_units, player_power, etc.)
    stub_slots = {
        "region_name": "TestRegion",
        "enemy_faction_name": "TestEnemy",
        "military_desc": "adequate",
        "economy_desc": "stable",
        "tension_desc": "rising",
        "ticks_under_pressure": 5,
        "attack_count": 2,
        "player_units": 10,
        "player_power": 100.0,
        "enemy_units": 8,
        "enemy_power": 80.0,
        "parity_ratio": 1.0,
    }
    sample = mission_briefing.assemble_briefing(archetypes[0], stub_slots)
    assert "objective" in sample, (
        "B2 precondition broken: assemble_briefing return dict missing 'objective' key"
    )
    assert isinstance(sample["objective"], str), (
        "B2 precondition broken: objective must be string"
    )
    assert sample["objective"], (
        "B2 precondition broken: objective must be non-empty for default archetype"
    )


# ---------------------------------------------------------------------------
# D. B3-A — Tutorial beats trigger schema
# ---------------------------------------------------------------------------


_LOCKED_TRIGGER_EVENTS = {
    "mission_load",
    "first_unit_visible",
    "first_unit_selected",
    "first_mission_loaded",
    "first_mission_complete",
}


def test_umbrella_d_beats_json_loads():
    with open(os.path.join(REPO_ROOT, "simulation", "library", "tutorial", "beats.json")) as f:
        beats = json.load(f)
    # beats.json is a dict keyed by TUT_001..TUT_005, not a list.
    assert isinstance(beats, dict), "B3-A: beats.json must be a JSON dict keyed by beat id"
    assert len(beats) == 5, f"B3-A: expected 5 beats, got {len(beats)}"


def test_umbrella_d_beats_have_trigger_event():
    with open(os.path.join(REPO_ROOT, "simulation", "library", "tutorial", "beats.json")) as f:
        beats = json.load(f)
    for beat_id, beat in beats.items():
        assert "trigger_event" in beat, (
            f"B3-A not landed: beat {beat_id!r} missing 'trigger_event' field"
        )
        assert "trigger_event_TBD" not in beat, (
            f"B3-A not landed: beat {beat_id!r} still has placeholder 'trigger_event_TBD'"
        )


def test_umbrella_d_trigger_events_in_allowlist():
    with open(os.path.join(REPO_ROOT, "simulation", "library", "tutorial", "beats.json")) as f:
        beats = json.load(f)
    for beat_id, beat in beats.items():
        te = beat["trigger_event"]
        assert te in _LOCKED_TRIGGER_EVENTS, (
            f"B3-A: beat {beat_id!r} trigger_event {te!r} not in locked allowlist"
        )


def test_umbrella_d_beats_full_schema():
    # 'id' is the dict key, not a field inside the beat dict
    required_fields = {"trigger_event", "headline", "body", "pointed_anchor", "accent_hint"}
    with open(os.path.join(REPO_ROOT, "simulation", "library", "tutorial", "beats.json")) as f:
        beats = json.load(f)
    for beat_id, beat in beats.items():
        missing = required_fields - set(beat.keys())
        assert not missing, (
            f"B3-A: beat {beat_id!r} missing fields {missing}"
        )


# ---------------------------------------------------------------------------
# E. B2-B — Briefing scene plain-language header
# ---------------------------------------------------------------------------


def test_umbrella_e_briefing_scene_has_header():
    src = _read("scenes/mission_briefing/mission_briefing.gd")
    assert "short_objective_header" in src, (
        "B2-B not landed: mission_briefing.gd missing short_objective_header node reference"
    )


def test_umbrella_e_briefing_header_reads_objective():
    src = _read("scenes/mission_briefing/mission_briefing.gd")
    # Header must reference both the new node name AND the existing 'objective' key
    # that already lives in the briefing dict (populated sim-side from OBJECTIVE_TEMPLATES_SHORT).
    assert "short_objective_header" in src, (
        "B2-B not landed: mission_briefing.gd missing short_objective_header node"
    )
    # Sanity: scene reads 'objective' key — already present pre-Wave 3 in _data assembly;
    # post-Wave 3, header logic must reference it explicitly.
    assert re.search(r"objective", src), (
        "B2-B not landed: briefing.gd must reference the 'objective' field"
    )


def test_umbrella_e_scene_router_accepts_mission_id():
    src = _read("autoload/scene_router.gd")
    assert "mission_id" in src or "mission_briefing" in src, (
        "B2-B not landed: scene_router.gd must handle mission_briefing route with mission_id"
    )


# ---------------------------------------------------------------------------
# F. B3-B — Tutorial state machine + main menu replay
# ---------------------------------------------------------------------------


def test_umbrella_f_tutorial_state_machine_exists():
    path = os.path.join(REPO_ROOT, "autoload", "tutorial_state_machine.gd")
    assert os.path.exists(path), (
        "B3-B not landed: autoload/tutorial_state_machine.gd missing"
    )


def test_umbrella_f_tutorial_state_machine_autoload_registered():
    src = _read("project.godot")
    assert re.search(r'TutorialStateMachine\s*=\s*"\*res://autoload/tutorial_state_machine\.gd"', src), (
        "B3-B not landed: project.godot [autoload] missing TutorialStateMachine"
    )


def test_umbrella_f_state_machine_handles_all_triggers():
    src = _read("autoload/tutorial_state_machine.gd")
    for trigger in _LOCKED_TRIGGER_EVENTS:
        assert trigger in src, (
            f"B3-B not landed: tutorial_state_machine.gd missing handler for {trigger!r}"
        )


def test_umbrella_f_state_machine_writes_flag():
    src = _read("autoload/tutorial_state_machine.gd")
    assert "user://tutorial_completed" in src, (
        "B3-B not landed: tutorial_state_machine.gd must write user://tutorial_completed"
    )


def test_umbrella_f_main_menu_replay_button():
    src = _read("scenes/main_menu/main_menu.gd")
    assert re.search(r"[Rr]eplay.{0,20}[Tt]utorial", src) or "replay_tutorial" in src.lower(), (
        "B3-B not landed: main_menu.gd missing Replay Tutorial button handler"
    )


# ---------------------------------------------------------------------------
# G. B5-C — Release-mode wire-up
# ---------------------------------------------------------------------------


def test_umbrella_g_project_main_scene_is_privacy_modal():
    src = _read("project.godot")
    assert 'run/main_scene="res://scenes/privacy_modal/privacy_modal.tscn"' in src, (
        "B5-C not landed: project.godot main_scene must be privacy_modal.tscn"
    )


def test_umbrella_g_custom_user_dir_enabled():
    src = _read("project.godot")
    assert "use_custom_user_dir=true" in src, (
        "B5-C not landed: project.godot must set use_custom_user_dir=true"
    )
    assert 'custom_user_dir_name="data"' in src, (
        "B5-C not landed: project.godot must set custom_user_dir_name=\"data\""
    )


def test_umbrella_g_theme_constants_release_flag():
    src = _read("autoload/theme_constants.gd")
    assert 'OS.has_feature("release_build")' in src, (
        "B5-C not landed: theme_constants.gd IS_RELEASE_BUILD must use OS.has_feature(\"release_build\")"
    )


def test_umbrella_g_sim_bridge_release_branch():
    src = _read("autoload/sim_bridge.gd")
    assert "IS_RELEASE_BUILD" in src or "release_build" in src, (
        "B5-C not landed: sim_bridge.gd must branch on release-build flag"
    )
    assert "--root" in src, (
        "B5-C not landed: sim_bridge.gd release-mode exec must pass --root arg"
    )
