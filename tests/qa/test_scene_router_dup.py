# spec: docs/stories/H-069.md (loading-screen-requests-once), DEC-h069-router-rule-2026-11-02
"""H-069: SceneRouter.go_to does not turn a request for the scene already being transitioned TO into a second transition.

Story H-069: "The beta's start does not shout at itself: asking for the same scene twice is not a replacement."
Story ruling (the `_transitioning` branch of `SceneRouter.go_to`): "a request that names the scene being transitioned TO and carries the same
params is not queued and starts no second transition. ... a request for the same scene with DIFFERENT params is not swallowed ... The check holds
for as long as the transition runs, fade-out included. If something is already in `_pending` ..., it is discarded: the running target is the latest
request, so latest-wins holds, and the existing `queued '%s' replaced by '%s'` warning is printed for the discarded request. If nothing is queued,
`go_to` returns silently. A request for a different scene (not the running target) keeps today's behaviour: it warns if something is queued and
overwrites `_pending`. The idle path is unchanged."
Story test lines proved here (numbers are the story's Tests list):
  1. "Two or more same-scene, same-params requests while a transition runs produce exactly one transition of that scene (swap count == 1) and no
     warning."                                                          -> test_same_scene_same_params_*
  2. "Running A, queued B, then A requested again: the final scene is A, one warning for the discarded B, and no second swap of A."
                                                                         -> test_running_a_queued_b_then_a_*
  3. "The same scene with DIFFERENT params requested while it runs: a second transition with the new params still happens."
                                                                         -> test_same_scene_different_params_*
  4. "Control: a different scene requested while one is running and another is queued still warns and overwrites (latest wins)."
                                                                         -> test_control_different_scene_*
  5. "Control: the idle path is unchanged (a `go_to` with nothing in flight transitions, and a later one transitions again)."
                                                                         -> test_control_idle_*
Red today (main 00dc3f16) for the story's stated reason: `go_to` compares no names, so a request for the running target is queued and
`_finish_transition` runs a second transition of that same scene (fade, free, rebuild). Cases 3, 4, 5 and the positive control are green today and
must stay green: they guard against a fix that swallows too much.

Seam (the story: "Model: tests/test_scene_router_queue.gd ... a router subclass whose `_swap_scene` is overridden to log each swap and its params,
stub scenes, real scene names as keys, run headless; the warnings are counted from the engine output. Swaps are counted, not `go_to` calls"):
each case runs in its own headless Godot process (a SceneTree script written to a scratch dir and run with `--path <repo> --script`). The driver
builds the router subclass from source at run time (a compile-time subclass would name the ThemeConstants autoload, which a SceneTree main script
cannot see), logs `{name, params}` per `_swap_scene`, and prints one `H069_RESULT {json}` line. The warnings are counted from that process's
engine output (lines `WARNING: SceneRouter: queued 'X' replaced by 'Y'`). One process per case keeps the warning counts per case exact.

Premises dumped on the built tree (base 00dc3f16, godot 4.x headless, 2026-11-02): ThemeConstants.FADE_DURATION == 0.3 (fade in, swap, fade out,
`_finish_transition` at about 0.6 s); a `go_to` made before the swap (t=0) and one made after it (t=0.4, in the fade-out) both reach the
`_transitioning` branch; push_warning prints `WARNING: SceneRouter: queued 'B' replaced by 'A'` to the engine output; `current_scene.tag` is the
stub's scene name.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
GODOT = os.environ.get("GODOT", str(Path.home() / ".local" / "bin" / "godot.real"))
TIMEOUT_S = 120
RESULT_PREFIX = "H069_RESULT "
WARN_RE = re.compile(r"WARNING: SceneRouter: queued '([^']*)' replaced by '([^']*)'")

# One driver script, one case per process (case name in the user args after `--`). Each case ends by printing H069_RESULT {swaps, final}.
DRIVER_SRC = r'''extends SceneTree

const STUB_SRC := """extends Node
var tag := ""
"""
const ROUTER_SRC := """extends "res://autoload/scene_router.gd"
var swaps: Array = []
var stub_script: GDScript
func _swap_scene(scene_name: String, params: Dictionary) -> void:
	swaps.append({"name": scene_name, "params": params})
	var tree := get_tree()
	if tree.current_scene:
		tree.current_scene.queue_free()
	var stub: Node = stub_script.new()
	stub.tag = scene_name
	tree.root.add_child(stub)
	tree.current_scene = stub
"""

var FADE: float = 0.3
var r: Node


func _wait(seconds: float) -> void:
	var end := Time.get_ticks_msec() + int(seconds * 1000.0)
	while Time.get_ticks_msec() < end:
		await process_frame


func _make_router() -> Node:
	var stub_script := GDScript.new()
	stub_script.source_code = STUB_SRC
	stub_script.reload()
	var router_script := GDScript.new()
	router_script.source_code = ROUTER_SRC
	router_script.reload()
	var n: Node = router_script.new()
	n.stub_script = stub_script
	n.name = "TestRouter"
	root.add_child(n)
	return n


func _initialize() -> void:
	await _run()


func _run() -> void:
	await process_frame
	FADE = root.get_node("ThemeConstants").FADE_DURATION
	r = _make_router()
	var case_name: String = OS.get_cmdline_user_args()[0]
	match case_name:
		"idle_twice_same_scene", "idle_two_scenes":
			await _idle(case_name)
		"same_scene_same_params_burst":
			r.go_to("settings")
			r.go_to("settings")
			r.go_to("settings")
			await _wait(FADE * 4)
		"same_scene_same_params_per_frame":
			r.go_to("settings")
			for i in 90:
				r.go_to("settings")
				await process_frame
			await _wait(FADE * 3)
		"same_scene_same_params_in_fade_out":
			r.go_to("settings")
			await _wait(FADE + 0.1)
			r.go_to("settings")
			r.go_to("settings")
			await _wait(FADE * 4)
		"same_scene_same_params_equal_value_dicts":
			r.go_to("mission_briefing", {"mission": 1})
			r.go_to("mission_briefing", {"mission": 1})
			await _wait(FADE + 0.1)
			r.go_to("mission_briefing", {"mission": 1})
			await _wait(FADE * 4)
		"running_a_queued_b_then_a":
			r.go_to("settings")
			r.go_to("galaxy")
			r.go_to("settings")
			await _wait(FADE * 5)
		"running_a_queued_b_then_a_in_fade_out":
			r.go_to("settings")
			await _wait(FADE + 0.1)
			r.go_to("galaxy")
			r.go_to("settings")
			await _wait(FADE * 5)
		"same_scene_different_params":
			r.go_to("mission_briefing", {"mission": 1})
			r.go_to("mission_briefing", {"mission": 2})
			await _wait(FADE * 5)
		"same_scene_different_params_in_fade_out":
			r.go_to("mission_briefing", {"mission": 1})
			await _wait(FADE + 0.1)
			r.go_to("mission_briefing", {"mission": 2})
			await _wait(FADE * 5)
		"different_scene_with_queue":
			r.go_to("settings")
			r.go_to("era_library")
			r.go_to("galaxy")
			await _wait(FADE * 5)
		_:
			printerr("unknown case " + case_name)
			quit(2)
			return
	_report()


func _idle(case_name: String) -> void:
	r.go_to("settings")
	await _wait(FADE * 2 + 0.4)
	r.go_to("settings" if case_name == "idle_twice_same_scene" else "galaxy")
	await _wait(FADE * 2 + 0.4)


func _report() -> void:
	var cs := current_scene
	var final_tag := "" if cs == null or not "tag" in cs else str(cs.tag)
	print("H069_RESULT " + JSON.stringify({"swaps": r.swaps, "final": final_tag}))
	quit(0)
'''


def run_case(case: str) -> dict:
    """Run one driver case headless; returns {"swaps": [{name, params}], "final": str, "warnings": [(queued, replacement)], "log": str}."""
    scratch = Path(tempfile.mkdtemp(prefix="h069_"))
    try:
        script = scratch / "h069_driver.gd"
        script.write_text(DRIVER_SRC)
        env = {**os.environ, "OM_SAVE_DIR": str(scratch / "saves"), "XDG_DATA_HOME": str(scratch / "xdg")}
        proc = subprocess.run([GODOT, "--headless", "--path", str(ROOT), "--script", str(script), "--", case],
                              capture_output=True, text=True, timeout=TIMEOUT_S, env=env)
        out = proc.stdout + "\n" + proc.stderr
        lines = [ln for ln in out.splitlines() if ln.startswith(RESULT_PREFIX)]
        assert len(lines) == 1, "case %s: expected one %s line (exit %s), got %d; output tail:\n%s" % (
            case, RESULT_PREFIX.strip(), proc.returncode, len(lines), out[-1500:])
        res = json.loads(lines[0][len(RESULT_PREFIX):])
        res["warnings"] = WARN_RE.findall(out)
        res["log"] = out
        return res
    finally:
        shutil.rmtree(scratch, ignore_errors=True)


def names(res: dict) -> list[str]:
    return [s["name"] for s in res["swaps"]]


def fmt(res: dict) -> str:
    return "swaps %s, warnings %s, final %r" % (json.dumps(res["swaps"]), res["warnings"], res["final"])


# Positive control: green today. The harness runs the router, logs swaps, and sees the final scene, so a red below means the feature is missing.
def test_control_harness_sees_one_swap_and_no_warning():
    """H-069 positive control: "Control: the idle path is unchanged (a `go_to` with nothing in flight transitions ...)". One go_to on an idle router
    produces one logged swap of that scene, no warning, and the stub is the current scene."""
    res = run_case("idle_two_scenes")
    assert names(res)[:1] == ["settings"], "harness control: first idle go_to must swap settings, " + fmt(res)
    assert res["warnings"] == [], "harness control: idle path warns nothing, " + fmt(res)


# 5. Control: the idle path is unchanged.
def test_control_idle_go_to_transitions_and_a_later_one_transitions_again():
    """H-069 case 5: "Control: the idle path is unchanged (a `go_to` with nothing in flight transitions, and a later one transitions again)."
    Different scenes, each after the previous transition finished: two swaps, in order, no warning, final scene is the later one."""
    res = run_case("idle_two_scenes")
    assert names(res) == ["settings", "galaxy"], fmt(res)
    assert res["warnings"] == [], fmt(res)
    assert res["final"] == "galaxy", fmt(res)


def test_control_idle_same_scene_again_after_finish_transitions_again():
    """H-069 case 5 / ruling "The idle path is unchanged": the same-target check lives in the `_transitioning` branch only, so a request for the
    same scene after its transition has finished is an idle request and transitions again (two swaps of settings, no warning)."""
    res = run_case("idle_twice_same_scene")
    assert names(res) == ["settings", "settings"], fmt(res)
    assert res["warnings"] == [], fmt(res)


# 1. Same scene, same params, while a transition runs: exactly one swap, no warning.
def test_same_scene_same_params_burst_is_one_swap_no_warning():
    """H-069 case 1: "Two or more same-scene, same-params requests while a transition runs produce exactly one transition of that scene (swap count
    == 1) and no warning." Three go_to("settings") in the same frame, router idle at the first."""
    res = run_case("same_scene_same_params_burst")
    assert names(res) == ["settings"], "swap count must be 1 (the repeat requests start no second transition): " + fmt(res)
    assert res["warnings"] == [], "no warning: " + fmt(res)
    assert res["final"] == "settings", fmt(res)


def test_same_scene_same_params_every_frame_is_one_swap_no_warning():
    """H-069 case 1, the loading screen's shape ("scenes/loading_screen/loading_screen.gd:47 (`_process`) calls `SceneRouter.go_to(_target_scene)`
    every frame"): 90 frames of go_to("settings") are one swap and no warning. The loading screen itself is not asserted (the story: "calls from the
    loading screen are not asserted")."""
    res = run_case("same_scene_same_params_per_frame")
    assert names(res) == ["settings"], "swap count must be 1: " + fmt(res)
    assert res["warnings"] == [], "no warning: " + fmt(res)


def test_same_scene_same_params_requested_in_fade_out_is_one_swap_no_warning():
    """H-069 case 1: "The check holds for as long as the transition runs, fade-out included." Two repeat requests after the swap, while the
    overlay fades out: still one swap of settings and no warning."""
    res = run_case("same_scene_same_params_in_fade_out")
    assert names(res) == ["settings"], "swap count must be 1: " + fmt(res)
    assert res["warnings"] == [], "no warning: " + fmt(res)


def test_same_scene_equal_value_params_is_one_swap_no_warning():
    """H-069 case 1: "carries the same params ... compares with Dictionary equality". Separate but equal dictionaries {"mission": 1}, one before
    the swap and one in the fade-out: one swap, no warning."""
    res = run_case("same_scene_same_params_equal_value_dicts")
    assert names(res) == ["mission_briefing"], "swap count must be 1: " + fmt(res)
    assert res["swaps"][0]["params"] == {"mission": 1}, fmt(res)
    assert res["warnings"] == [], "no warning: " + fmt(res)


# 2. Running A, queued B, A requested again.
def test_running_a_queued_b_then_a_ends_on_a_one_warning_one_swap():
    """H-069 case 2: "Running A, queued B, then A requested again: the final scene is A, one warning for the discarded B, and no second swap of
    A." A = settings, B = galaxy, all three requests in one frame."""
    res = run_case("running_a_queued_b_then_a")
    assert res["final"] == "settings", fmt(res)
    assert res["warnings"] == [("galaxy", "settings")], "one warning, for the discarded galaxy: " + fmt(res)
    assert names(res) == ["settings"], "no second swap of settings, and galaxy never runs: " + fmt(res)


def test_running_a_queued_b_then_a_in_fade_out_ends_on_a_one_warning_one_swap():
    """H-069 case 2 with "The check holds for as long as the transition runs, fade-out included.": settings has swapped in, galaxy is queued
    during the fade-out, then settings is requested again: final scene settings, one warning for the discarded galaxy, one swap."""
    res = run_case("running_a_queued_b_then_a_in_fade_out")
    assert res["final"] == "settings", fmt(res)
    assert res["warnings"] == [("galaxy", "settings")], "one warning, for the discarded galaxy: " + fmt(res)
    assert names(res) == ["settings"], "no second swap of settings: " + fmt(res)


# 3. Same scene, different params: still transitions.
def test_same_scene_different_params_still_transitions():
    """H-069 case 3: "The same scene with DIFFERENT params requested while it runs: a second transition with the new params still happens."
    mission_briefing {"mission": 1} running, {"mission": 2} requested before the swap: two swaps, the second with the new params. Green today;
    guards a fix that compares names only."""
    res = run_case("same_scene_different_params")
    assert names(res) == ["mission_briefing", "mission_briefing"], fmt(res)
    assert [s["params"] for s in res["swaps"]] == [{"mission": 1}, {"mission": 2}], fmt(res)
    assert res["warnings"] == [], "nothing was queued when the second request arrived: " + fmt(res)


def test_same_scene_different_params_in_fade_out_still_transitions():
    """H-069 case 3 with "fade-out included": the different-params request arrives after the swap, during the fade-out; the second transition,
    with the new params, still happens."""
    res = run_case("same_scene_different_params_in_fade_out")
    assert [s["params"] for s in res["swaps"]] == [{"mission": 1}, {"mission": 2}], fmt(res)
    assert res["final"] == "mission_briefing", fmt(res)


# 4. Control: a different scene still warns and overwrites.
def test_control_different_scene_with_one_queued_warns_and_latest_wins():
    """H-069 case 4: "Control: a different scene requested while one is running and another is queued still warns and overwrites (latest wins)."
    settings running, era_library queued, galaxy requested: one warning (era_library replaced by galaxy), swaps settings then galaxy, never
    era_library."""
    res = run_case("different_scene_with_queue")
    assert res["warnings"] == [("era_library", "galaxy")], fmt(res)
    assert names(res) == ["settings", "galaxy"], fmt(res)
    assert res["final"] == "galaxy", fmt(res)
