extends SceneTree

# Piece C5 (docs/northstar/plans/push/pieces.toml; docs/northstar/plans/briefs/
# 2026-09-22-two-day-push.md wave-2 row C5, attach step 7): res://scenes/tactical_c/
# tactical_view.tscn is a fresh, minimal renderer over a C transport v1 "tactical"
# snapshot (docs/architecture.md "C transport v1"): units drawn as blocks, move/
# attack-move/attack-target/box-select input turned into command JSON, a fixed
# top-down camera bounded to the map canvas. Not built yet (depends on attach/B10,
# attach/B12, attach/T1); this file is red on the missing scene, not a parse error.
#
# Contract this test requires of the root node (recorded verbatim in
# docs/northstar/proving_ground/evidence/push_2026-09-22/c5_t2g_tests_note.md):
#   load_frame(frame: Dictionary) -> void       loads one tactical snapshot (map/
#                                                units/visible), replacing whatever
#                                                was loaded before
#   qa_state() -> Dictionary                    JSON-safe: tick, canvas, units
#                                                {id:{faction,type,tier,hp,layer,
#                                                facing,state,x,y}} (ground truth,
#                                                every unit in the loaded frame),
#                                                units_px {id:[x,y]} (screen space,
#                                                ONLY units the local faction's
#                                                `visible` set contains -- R-089-04,
#                                                no ghost for a hidden or
#                                                never-seen unit), local_faction,
#                                                selected, camera {x,y}
#   qa_plant(id: String) -> bool                PLANTS reused verbatim from the p4
#                                                and p8 mockup briefs; "nope" and
#                                                any id this scene does not
#                                                implement always return false
#   issue_command(cmd: Dictionary) -> Dictionary the command JSON the scene would
#                                                send over the pipe for a UI
#                                                action, never actually sent here
#   qa_box_select(x0,y0,x1,y1: float) -> Array  screen-space rect select; returns
#                                                and records the newly selected ids
#   qa_pan(x, y: float) -> void                  pans/recentres the camera, clamped
#                                                to the loaded frame's map canvas
#                                                (R-103-02)
#
# PLANTS reused verbatim: "facing-fixed", "camera-unbounded" (both listed in
# 2026-09-22-p4-units-mockup.md / -p8-hud-mockup.md's PLANTS arrays). "pass-through",
# "instant-fight", "silhouettes-same", "no-death-visual", "box-one-layer",
# "group-shared", "clock-wallclock", "narrow-moves-focus" do not apply to this
# minimal view (no collision/damage sim, one layer, no clock, no control groups)
# and are not required here -- see the evidence note's "Not tested here". R-105-04
# forbids a select-all command outright, so "select-all-exists" must return false
# from qa_plant() unconditionally, never true even when "planted" -- this scene
# must never wire that fault site up at all.

const SCENE_PATH := "res://scenes/tactical_c/tactical_view.tscn"
const FIXTURE_TICK0_PATH := "res://tests/fixtures/tactical_frame_seed11.json"
const FIXTURE_TICK10_PATH := "res://tests/fixtures/tactical_frame_seed11_tick10.json"
const FIXTURE_PF1_PATH := "res://tests/fixtures/tactical_frame_seed11_pf1.json"
const N_UNITS := 12
const LOCAL_FACTION := 0
const PLANTS := ["facing-fixed", "camera-unbounded"]
const CONTRACT_METHODS := ["load_frame", "qa_state", "qa_plant", "issue_command",
	"qa_box_select", "qa_pan"]

var _pass_count := 0
var _fail_count := 0
var _fail_msgs: Array[String] = []
var _root: Node
var _frame0: Dictionary
var _frame10: Dictionary
var _live_tests_completed := false
var _c53_completed := false
var _c54_completed := false
var _c28_completed := false
var _realtime_step_completed := false


func _initialize() -> void:
	await _run_tests()
	print("\n=== Tactical View Test Results ===")
	print("PASS: %d  FAIL: %d" % [_pass_count, _fail_count])
	if _fail_count > 0:
		print("Failures:")
		for msg in _fail_msgs:
			print("  - " + msg)
		print("=== RED ===\n")
		quit(1)
	else:
		print("=== GREEN ===\n")
		quit(0)


func _assert(cond: bool, msg: String) -> void:
	if cond:
		_pass_count += 1
	else:
		_fail_count += 1
		_fail_msgs.append(msg)


func _run_tests() -> void:
	_frame0 = _read_json(FIXTURE_TICK0_PATH)
	_assert(not _frame0.is_empty(), "fixture missing or unparsable: " + FIXTURE_TICK0_PATH)
	_frame10 = _read_json(FIXTURE_TICK10_PATH)
	_assert(not _frame10.is_empty(), "fixture missing or unparsable: " + FIXTURE_TICK10_PATH)
	if _frame0.is_empty() or _frame10.is_empty():
		return
	_assert(_frame0.get("units", []).size() == N_UNITS,
		"fixture setup bug: tick0 fixture should carry %d units" % N_UNITS)

	var packed = load(SCENE_PATH)
	_assert(packed != null, "cannot load %s (piece C5 not attached yet)" % SCENE_PATH)
	if packed == null or not (packed is PackedScene):
		return

	_root = (packed as PackedScene).instantiate()
	_assert(_root != null, "%s failed to instantiate" % SCENE_PATH)
	if _root == null:
		return
	get_root().add_child(_root)
	await process_frame
	# B9-N: tactical_view now steps the live mission on its own from
	# _process() (real-time play). Every other section here drives ticks
	# explicitly (load_frame()/qa_step()) and asserts exact tick/frame
	# state, so automatic stepping is switched off for every view this test
	# file mounts; _run_realtime_step_tests() below is the one section that
	# exercises _process() itself, and it does so by calling it directly.
	# Godot auto-enables processing once a script defines _process(), on the
	# node's own _ready() (deferred to this first awaited frame, not
	# synchronous inside add_child()), so set_process(false) only sticks once
	# called after that frame has run.
	_root.set_process(false)
	await process_frame

	for m in CONTRACT_METHODS:
		_assert(_root.has_method(m), "tactical_view root missing method: " + m)
	for m in CONTRACT_METHODS:
		if not _root.has_method(m):
			return

	_root.load_frame(_frame0)
	await process_frame

	_check_qa_state_json_safe()
	_check_units_count_and_px_in_viewport()
	_check_only_visible_set_drawn_R089_04()
	await _check_moved_unit_and_facing_R100_01()
	_check_dead_unit_gone_and_hidden_unit_no_ghost()
	_check_command_move_R096_01()
	_check_command_attack_move_R096_02()
	_check_command_attack_target_R096_04()
	_check_box_select_then_move_R105_01()
	_check_camera_bounded_R103_02()
	_check_plant_camera_unbounded()
	await _check_plant_facing_fixed_R100_01()
	_check_select_all_never_exists_R105_04()
	_check_plant_nope_and_all_real_plants_true()

	await _run_c53_tests()
	_assert(_c53_completed, "the C5-3 checks did not run to the end (a script error aborted them, or the view lacks send_command / qa_step / the stuck and rubber-band plants)")
	await _run_live_tests()
	_assert(_live_tests_completed, "the live-frame checks did not run to the end (a script error aborted them, or c_bridge.gd lacks load_tactical_live / tactical_frame / DEFAULT_FEATURES)")
	await _run_c54_tests()
	_assert(_c54_completed, "the C5-4 checks did not run to the end (a script error aborted them, or tactical_view.gd lacks commands_sent_last_order / units_in_last_command / move-order-dropped plant)")
	await _run_c28_tests()
	_assert(_c28_completed, "the C2-8 checks did not run to the end (a script error aborted them, or tactical_view.gd does not read player_faction from the loaded frame)")
	await _run_mission_over_routing_test()
	await _run_realtime_step_tests()
	_assert(_realtime_step_completed, "the real-time stepping checks did not run to the end (a script error aborted them, or tactical_view.gd lacks _process real-time stepping)")


# Piece C5-2 (docs/architecture.md "session commands (v1.1)"): with no
# load_frame() call the view reads the first frame the live pipe answers to
# mission_start + tactical_step (c_bridge.gd load_tactical_live), not
# tests/fixtures/tactical_frame_seed11.json. Known sim-side gap when this was
# written: mission_start loads no tactical map and no force, so the live
# frame arrives with canvas 0 and no units; the view is asserted to show
# exactly what the live frame carries (its tick and unit count), which the
# 12-unit fixture cannot satisfy. Units moving live needs the persistent
# pipe session (C2-4's design) and is not tested here.
func _run_live_tests() -> void:
	var CBridge = load("res://autoload/c_bridge.gd")
	var bridge = CBridge.new()
	for m in ["load_tactical_live", "tactical_frame", "last_error"]:
		_assert(bridge.has_method(m), "c_bridge.gd missing method (piece C5-2 not attached yet): " + m)
		if not bridge.has_method(m):
			return
	if not CBridge.get_script_constant_map().has("DEFAULT_FEATURES"):
		_assert(false, "c_bridge.gd missing constant DEFAULT_FEATURES")
		return

	var ok: bool = bridge.load_tactical_live(1, CBridge.DEFAULT_N_REGIONS, CBridge.DEFAULT_FEATURES)
	_assert(ok, "load_tactical_live(1, %d, DEFAULT_FEATURES) returned false (last_error = %s)" % [CBridge.DEFAULT_N_REGIONS, bridge.last_error()])
	var live: Dictionary = bridge.tactical_frame()
	_assert(live.get("type", "") == "tactical", "live tactical frame type = %s, expected tactical" % live.get("type", ""))
	_assert(live.get("units", null) is Array and live.get("map", null) is Dictionary, "live tactical frame lacks units or map")
	_assert(int(live.get("tick", -1)) == 1, "first live tactical frame tick = %s, expected 1 (one tactical_step)" % live.get("tick", -1))

	var again = CBridge.new()
	again.load_tactical_live(1, CBridge.DEFAULT_N_REGIONS, CBridge.DEFAULT_FEATURES)
	_assert(again.tactical_frame() == live, "same seed answered two different tactical frames (determinism)")

	var bad = CBridge.new()
	_assert(not bad.load_tactical_live(1, 30, CBridge.DEFAULT_FEATURES), "load_tactical_live at 30 regions (below the feasibility floor) returned true")
	_assert(bad.last_error() != "", "a failed live tactical load left last_error empty (silent failure)")
	_assert(bad.tactical_frame().is_empty(), "a failed live tactical load still exposed a tactical frame")

	_assert((live.get("units", []) as Array).size() != (_frame0.get("units", []) as Array).size() or int(live.get("tick", -1)) != int(_frame0.get("tick", -2)),
		"live tactical frame equals the fixture; the live check below cannot tell them apart (fixture control)")

	# The scenes share one process-wide session (autoload/sim_session.gd, C2-6):
	# start the scene under test on a fresh world, the one the private bridge
	# above answered from.
	load("res://autoload/sim_session.gd").reset()
	var fresh: Node = (load(SCENE_PATH) as PackedScene).instantiate()
	get_root().add_child(fresh)
	# A67 (test-defect): _ready() has run synchronously inside add_child(), so
	# stop processing before any frame is awaited; on a rendered display an
	# extra _process otherwise ran first and stepped the live tick to 2.
	fresh.set_process(false)
	await process_frame
	var st: Dictionary = fresh.qa_state()
	_assert(int(st.get("tick", -1)) == int(live.get("tick", -2)),
		"view with no load_frame() call shows tick %s, live frame says %s (still showing the fixture?)" % [st.get("tick"), live.get("tick")])
	_assert((st.get("units", {}) as Dictionary).size() == (live.get("units", []) as Array).size(),
		"view with no load_frame() call shows %d units, live frame carries %d" % [(st.get("units", {}) as Dictionary).size(), (live.get("units", []) as Array).size()])
	fresh.queue_free()
	await process_frame
	_live_tests_completed = true


func _unit(id: int, faction: int, x: float, y: float) -> Dictionary:
	return {"id": id, "faction": faction, "type": 0, "tier": 0, "x": x, "y": y, "hp": 100.0, "layer": 0, "facing": 0.0, "target": -1, "state": 0}


func _mount_view() -> Node:
	var v: Node = (load(SCENE_PATH) as PackedScene).instantiate()
	get_root().add_child(v)
	await process_frame
	v.set_process(false)  # see the _root mount above for why
	await process_frame
	return v


# B9-N (2026-09-28 QA-run wiring brief): load_frame() routes to the debrief
# scene the same way the End Mission button does (see the pressed handler in
# _ready() above) the moment a loaded frame carries "mission_over": true --
# docs/architecture.md "C transport v1", tactical snapshot. SceneRouter.go_to()
# sets _current_scene_name synchronously before its fade tween runs (see
# tests/test_briefing_debrief.gd's C4-9 pin for the same pattern), so no
# await is needed after load_frame() to observe the routing target.
func _run_mission_over_routing_test() -> void:
	var view := await _mount_view()
	var scene_router := get_root().get_node("SceneRouter")

	# Earlier sections in this same script run their own SceneRouter.go_to()
	# calls (the live-frame checks route through an error screen on a
	# feasibility-floor failure); its one-shot _transitioning lock can still
	# be mid-fade when this section starts, which would silently drop this
	# section's own go_to() call below. Wait it out first.
	var settle_guard := 0
	while bool(scene_router.get("_transitioning")) and settle_guard < 60:
		await process_frame
		settle_guard += 1

	# Control: an ordinary frame (no mission_over key at all, matching every
	# fixture above) must not route away from tactical_c.
	view.load_frame(_frame0)
	await process_frame
	_assert(str(scene_router.get("_current_scene_name")) != "debrief",
		"a frame with no mission_over key routed to debrief (false positive)")

	var over_frame: Dictionary = _frame0.duplicate(true)
	over_frame["mission_over"] = true
	over_frame["band"] = 4
	view.load_frame(over_frame)
	await process_frame
	_assert(str(scene_router.get("_current_scene_name")) == "debrief",
		"load_frame() with mission_over=true did not route to debrief, SceneRouter._current_scene_name = %s" % str(scene_router.get("_current_scene_name")))

	view.queue_free()
	await process_frame


func _px_of(view: Node, id: int) -> Array:
	return (view.qa_state().get("units_px", {}) as Dictionary).get(str(id), [])


# Piece C5-3 (look 5, first_look/README.md finding 1): a real mission's canvas is
# 24000 with the forces on opposite edges, and the view's fixed 0.25 scale drew every
# unit off screen. The view scales the whole canvas into the screen height, sends unit
# commands over the shared session, steps the live mission (qa_step), and carries the
# plants the QA detectors need: "stuck" (a unit's drawn position stops following the
# frames) and "rubber-band" (every third load_frame draws the units where the frame
# before it had them, a snap backwards). Known sim-side gap when this was written:
# ordered units do not move over the pipe (movement steps off w->tick, held still while
# the mission phase holds), so movement itself is proven on fixture frames here, not live.
func _run_c53_tests() -> void:
	SimSession_reset()
	var big := {
		"type": "tactical", "tick": 1,
		"map": {"canvas": 24000.0, "nodes": [], "cover": [], "obstacles": []},
		"units": [_unit(1, 0, 11760.0, 15.0), _unit(2, 0, 12240.0, 15.0), _unit(3, 1, 11745.0, 23985.0)],
		"visible": {"0": [1, 2, 3]},
	}
	var view: Node = await _mount_view()
	for m in ["send_command", "qa_step"]:
		_assert(view.has_method(m), "tactical_view root missing method (piece C5-3 not attached yet): " + m)
		if not view.has_method(m):
			view.queue_free()
			return
	view.load_frame(big)
	await process_frame
	var st: Dictionary = view.qa_state()
	# TD-VG-A-13 (premise-changed, Architect 2026-10-13): was
	# `is_equal_approx(float(st["scale"]), 1080.0 / 24000.0)`; A18 frames the own box
	# (units, spawn, own lots), not the whole canvas, so the scale is the canvas fit
	# times the framing zoom (clamped to ZOOM_MIN..ZOOM_MAX / ZOOM_STEP), read after load_frame.
	var fit_scale: float = (1080.0 / 24000.0) * view._framing_zoom()
	_assert(st.has("scale") and is_equal_approx(float(st["scale"]), fit_scale), "qa_state().scale = %s, expected the canvas fit times the framing zoom (%s)" % [st.get("scale"), fit_scale])
	var px: Dictionary = st.get("units_px", {})
	_assert(px.size() == 3, "expected 3 drawn units on the 24000 canvas, got %d" % px.size())
	# TD-VG-A-13: was every entry of px; now own-faction ids only (units 1 and 2,
	# faction 0): the enemy at y=23985 is outside the own box and may sit off screen.
	for k in px:
		if int(big["units"][int(k) - 1]["faction"]) != 0:
			continue
		var p: Array = px[k]
		_assert(p[0] >= 0.0 and p[0] <= 1920.0 and p[1] >= 0.0 and p[1] <= 1080.0, "unit %s drawn at %s, outside the 1920x1080 screen on a real-size canvas" % [k, str(p)])

	# Commands over the shared session, on the live mission.
	view.queue_free()
	await process_frame
	SimSession_reset()
	# Advance the shared session's strategic world to tick 10 so the mission
	# has units; seed-1 at tick 0 is archetype 0 with 0 units, at tick 10 it
	# is archetype 3 with 572 units. Test defect: the fixture never stepped
	# the world before mounting the view (see assignment brief).
	var _b = load("res://autoload/sim_session.gd").bridge()
	var _CBridge = load("res://autoload/c_bridge.gd")
	_b.ensure_session(1, _CBridge.DEFAULT_N_REGIONS, _CBridge.DEFAULT_FEATURES)
	_b.step(10)
	var _step_ddl := Time.get_ticks_msec() + 5000
	while Time.get_ticks_msec() < _step_ddl and int(_b.snapshot().get("tick", 0)) < 10:
		_b.pump()
		OS.delay_msec(5)
	var live_view: Node = await _mount_view()
	var live: Dictionary = live_view.qa_state()
	var own: Array = []
	for k in live.get("units", {}):
		if int(live["units"][k]["faction"]) == 0 and own.size() < 3:
			own.append(int(k))
	_assert(own.size() == 3, "live mission has fewer than 3 faction-0 units (%d)" % own.size())
	_assert(live_view.send_command({"kind": "move", "unit_ids": own, "x": 12000.0, "y": 6000.0}), "send_command(move) was not acknowledged")
	var last: Dictionary = live_view.qa_state().get("last_command", {})
	_assert(bool(last.get("ok", false)) and last.get("kind", "") == "move" and int(last.get("units", 0)) == 3, "qa_state().last_command after a move = %s" % str(last))
	_assert(not live_view.send_command({"kind": "no-such-kind", "unit_ids": own}), "an unknown command kind was reported as sent")
	_assert(not bool(live_view.qa_state().get("last_command", {}).get("ok", true)), "last_command.ok stayed true after a refused command")
	var tick0 := int(live_view.qa_state().get("tick", -1))
	live_view.qa_step(3)
	_assert(int(live_view.qa_state().get("tick", -1)) == tick0 + 3, "qa_step(3) moved the view from tick %d to %s, expected %d" % [tick0, live_view.qa_state().get("tick"), tick0 + 3])
	live_view.queue_free()
	await process_frame

	# Plants, on the two fixture frames (units move between them).
	var moved := -1
	var u0 := {}
	for u in _frame0.get("units", []):
		u0[int(u["id"])] = u
	for u in _frame10.get("units", []):
		var id := int(u["id"])
		if u0.has(id) and (abs(float(u["x"]) - float(u0[id]["x"])) > 1.0 or abs(float(u["y"]) - float(u0[id]["y"])) > 1.0):
			moved = id
			break
	_assert(moved != -1, "fixture setup bug: no unit moves between the tick-0 and tick-10 frames")
	if moved == -1:
		return
	var clean: Node = await _mount_view()
	clean.load_frame(_frame0.duplicate(true))
	var clean_a: Array = _px_of(clean, moved)
	clean.load_frame(_frame10.duplicate(true))
	var clean_b: Array = _px_of(clean, moved)
	clean.load_frame(_frame10.duplicate(true))
	var clean_c: Array = _px_of(clean, moved)
	_assert(clean_a != clean_b, "control: the moved unit's drawn position did not change between the two fixture frames")
	_assert(clean_c == clean_b, "control: reloading the same frame moved the drawn unit")
	clean.queue_free()
	await process_frame

	var stuck: Node = await _mount_view()
	_assert(stuck.qa_plant("stuck"), "qa_plant(stuck) was not accepted")
	stuck.load_frame(_frame0.duplicate(true))
	var stuck_a: Array = _px_of(stuck, moved)
	stuck.load_frame(_frame10.duplicate(true))
	_assert(_px_of(stuck, moved) == stuck_a, "stuck plant: the drawn unit still followed the frames (%s vs %s)" % [str(_px_of(stuck, moved)), str(stuck_a)])
	stuck.queue_free()
	await process_frame

	var band: Node = await _mount_view()
	_assert(band.qa_plant("rubber-band"), "qa_plant(rubber-band) was not accepted")
	band.load_frame(_frame0.duplicate(true))
	var band_a: Array = _px_of(band, moved)
	band.load_frame(_frame10.duplicate(true))
	var band_b: Array = _px_of(band, moved)
	band.load_frame(_frame10.duplicate(true))
	var band_c: Array = _px_of(band, moved)
	_assert(band_b == clean_b, "rubber-band plant: the second frame should still draw the frame's own position (%s vs %s)" % [str(band_b), str(clean_b)])
	_assert(band_c == band_a, "rubber-band plant: the third load should snap the unit back to where the frame before had it (%s vs %s)" % [str(band_c), str(band_a)])
	band.queue_free()
	await process_frame
	SimSession_reset()
	_c53_completed = true


func SimSession_reset() -> void:
	load("res://autoload/sim_session.gd").reset()


# Piece C5-4: group move order reaches pipe as ONE command; move-order-dropped
# plant sends one command per unit (detector).
func _run_c54_tests() -> void:
	SimSession_reset()
	var _b = load("res://autoload/sim_session.gd").bridge()
	var _CBridge = load("res://autoload/c_bridge.gd")
	_b.ensure_session(1, _CBridge.DEFAULT_N_REGIONS, _CBridge.DEFAULT_FEATURES)
	_b.step(10)
	var _step_ddl := Time.get_ticks_msec() + 5000
	while Time.get_ticks_msec() < _step_ddl and int(_b.snapshot().get("tick", 0)) < 10:
		_b.pump()
		OS.delay_msec(5)
	var view: Node = await _mount_view()
	var live: Dictionary = view.qa_state()

	# qa_state() must expose the new counter keys and list move-order-dropped
	_assert(live.has("commands_sent_last_order"),
		"C5-4: qa_state() missing commands_sent_last_order")
	_assert(live.has("units_in_last_command"),
		"C5-4: qa_state() missing units_in_last_command")
	_assert(live.has("plants") and (live.get("plants") as Array).has("move-order-dropped"),
		"C5-4: qa_state().plants does not include move-order-dropped")

	# Gather up to 3 faction-0 unit ids from the live mission frame
	var own: Array = []
	for k in live.get("units", {}):
		if int(live["units"][k]["faction"]) == 0 and own.size() < 3:
			own.append(int(k))
	_assert(own.size() >= 2,
		"C5-4: live mission has fewer than 2 faction-0 units (%d); cannot test counter" % own.size())
	if own.size() < 2:
		view.queue_free()
		await process_frame
		SimSession_reset()
		return

	# Counter test (clean): one group order -> one pipe command
	view.send_command({"kind": "move", "unit_ids": own, "x": 12000.0, "y": 6000.0})
	var st: Dictionary = view.qa_state()
	_assert(int(st.get("commands_sent_last_order", -1)) == 1,
		"C5-4: commands_sent_last_order should be 1 for a group move (got %s)" % st.get("commands_sent_last_order"))
	_assert(int(st.get("units_in_last_command", -1)) == own.size(),
		"C5-4: units_in_last_command should be %d (got %s)" % [own.size(), st.get("units_in_last_command")])

	# Detector: plant makes counter equal selection size (> 1 for multi-unit)
	_assert(view.qa_plant("move-order-dropped"),
		"C5-4: qa_plant(move-order-dropped) must return true")
	# Positive control (clean): without the plant the one-command check passed above.
	# Planted run: counter must NOT be 1 (= one per unit) -- this is the caught case.
	view.send_command({"kind": "move", "unit_ids": own, "x": 12000.0, "y": 6000.0})
	var st2: Dictionary = view.qa_state()
	var dropped: int = int(st2.get("commands_sent_last_order", -1))
	_assert(dropped == own.size(),
		"C5-4 PLANT: commands_sent_last_order should equal %d (one per unit) with move-order-dropped, got %d" % [own.size(), dropped])
	_assert(dropped != 1,
		"C5-4 DETECTOR: move-order-dropped plant must break the one-command invariant (commands_sent_last_order=%d)" % dropped)

	view.queue_free()
	await process_frame
	SimSession_reset()
	_c54_completed = true


# Piece C5-N (2026-09-28 QA-run wiring brief): before this fix, a deployed
# mission only ever advanced through the qa_step() QA hook -- _process() did
# nothing, so real play froze at tick 0. Same live-mission setup as
# _run_c54_tests, but seed 3 (stepped to strategic tick 10: under 1,000
# live units, so R-099-03 does not halve the call rate; om_tactical_step is
# not the zero-unit no-op, csrc/unit.c:1651).
# Rate: OM_TACTICAL_TICK_RATE = 20 base ticks/sec (csrc/om_constants.h;
# E-13 R-099-02, docs/bible/epics/E-13-tactical-combat.md).
func _run_realtime_step_tests() -> void:
	SimSession_reset()
	var _b = load("res://autoload/sim_session.gd").bridge()
	var _CBridge = load("res://autoload/c_bridge.gd")
	var _TacticalView = load("res://scenes/tactical_c/tactical_view.gd")
	_b.ensure_session(3, _CBridge.DEFAULT_N_REGIONS, _CBridge.DEFAULT_FEATURES)
	_b.step(10)
	var _step_ddl := Time.get_ticks_msec() + 5000
	while Time.get_ticks_msec() < _step_ddl and int(_b.snapshot().get("tick", 0)) < 10:
		_b.pump()
		OS.delay_msec(5)

	var view: Node = await _mount_view()
	if not view.has_method("_process"):
		_assert(false, "tactical_view root missing _process (piece C5-N not attached yet)")
		view.queue_free()
		await process_frame
		SimSession_reset()
		return

	# _mount_view() already disabled automatic per-frame processing (see its
	# comment); _process() is driven directly below with a fixed delta so
	# the expected-ticks arithmetic is exact, not at the mercy of real
	# wall-clock frame timing.
	var tick0 := int(view.qa_state().get("tick", -1))
	_assert(tick0 >= 0, "no tick in qa_state() before real-time stepping")

	var rate: float = float(_TacticalView.TACTICAL_BASE_TICKS_PER_SECOND)
	var frame_dt := 1.0 / 60.0
	for _i in range(60):
		view._process(frame_dt)
	var tick1 := int(view.qa_state().get("tick", -1))
	var advanced := tick1 - tick0
	var expected := int(round(rate))
	var frame_tolerance := int(ceil(rate * frame_dt))
	_assert(abs(advanced - expected) <= frame_tolerance,
		"~1s of _process() advanced tick by %d, expected ~%d (rate %s ticks/sec), tolerance +-%d" % [advanced, expected, rate, frame_tolerance])

	# Stepping must stop once a frame reports mission_over, even though the
	# accumulator still owes ticks -- _mission_over_seen latches in
	# load_frame() (docs/architecture.md "C transport v1", tactical snapshot).
	var over_frame: Dictionary = _frame0.duplicate(true)
	over_frame["tick"] = tick1
	over_frame["mission_over"] = true
	view.load_frame(over_frame)
	for _i in range(60):
		view._process(frame_dt)
	var tick2 := int(view.qa_state().get("tick", -1))
	_assert(tick2 == tick1,
		"_process() kept stepping after a mission_over frame: tick moved from %d to %d" % [tick1, tick2])

	view.queue_free()
	await process_frame
	SimSession_reset()
	_realtime_step_completed = true


func _check_qa_state_json_safe() -> void:
	var text := JSON.stringify(_root.qa_state())
	_assert(text != "", "qa_state() did not survive JSON.stringify")


func _check_units_count_and_px_in_viewport() -> void:
	var state: Dictionary = _root.qa_state()
	var units: Dictionary = state.get("units", {})
	_assert(units.size() == N_UNITS,
		"units should carry all %d units from the loaded frame (ground truth), got %d" % [N_UNITS, units.size()])

	var px: Dictionary = state.get("units_px", {})
	# get_root().size is not a reliable viewport measurement under
	# --headless (observed 100x100 regardless of project.godot's configured
	# 1920x1080), so a too-small reading falls back to the configured size
	# rather than asserting against a meaningless 100x100 box.
	# A67 (test-defect): the scene lays out against the stretched logical
	# viewport (canvas_items stretch, 1920x1080 base), which is what
	# get_visible_rect() reports; get_root().size is the raw window and is
	# 1280x720 under a 720p display.
	var vp: Vector2 = _root.get_viewport().get_visible_rect().size
	if vp.x < 200.0 or vp.y < 200.0:
		vp = Vector2(1920, 1080)
	var outside := 0
	# TD-VG-A-13: was every px entry; now own-faction ids only (the frame's
	# player_faction, default LOCAL_FACTION); A18 frames the own box, so enemy
	# units may sit off screen. The count assertion above is unchanged.
	var own_faction: int = int(_frame0.get("player_faction", LOCAL_FACTION))
	var own_ids: Dictionary = {}
	for u in _frame0.get("units", []):
		if int(u.get("faction", -1)) == own_faction:
			own_ids[str(int(u.get("id")))] = true
	for id in px:
		if not own_ids.has(str(id)):
			continue
		var p = px[id]
		if typeof(p) != TYPE_ARRAY or p.size() != 2 or p[0] < 0 or p[0] > vp.x or p[1] < 0 or p[1] > vp.y:
			outside += 1
	_assert(outside == 0,
		"%d/%d drawn units_px entries fall outside the %dx%d viewport" % [outside, px.size(), int(vp.x), int(vp.y)])


# R-089-04: visibility has no memory of last-seen positions. Only the local
# faction's `visible` set is drawn; an enemy the fixture never lists (11, 12)
# must have no node at all.
func _check_only_visible_set_drawn_R089_04() -> void:
	var state: Dictionary = _root.qa_state()
	_assert(int(state.get("local_faction", -1)) == LOCAL_FACTION,
		"local_faction should be %d in Round 1 (single player), got %s" % [LOCAL_FACTION, state.get("local_faction")])

	var expected: Array = _frame0.get("visible", {}).get(str(LOCAL_FACTION), [])
	var drawn := _int_keys(state.get("units_px", {}))
	_assert(_same_set(drawn, expected),
		"tick0: drawn ids %s should equal visible[\"0\"] %s exactly" % [str(drawn), str(expected)])

	for hidden_id in [11, 12]:
		_assert(not drawn.has(hidden_id),
			"tick0: unit %d is outside visible[\"0\"] and must have no node" % hidden_id)


func _check_moved_unit_and_facing_R100_01() -> void:
	var state0: Dictionary = _root.qa_state()
	var px0 = state0.get("units_px", {}).get("4")
	var facing0 = state0.get("units", {}).get("4", {}).get("facing")
	_assert(px0 != null, "unit 4 should be drawn at tick0 (positive control)")
	_assert(facing0 != null, "unit 4 should report a facing at tick0")

	_root.load_frame(_frame10)
	await process_frame
	var state10: Dictionary = _root.qa_state()
	var px10 = state10.get("units_px", {}).get("4")
	var facing10 = state10.get("units", {}).get("4", {}).get("facing")
	_assert(px10 != null, "unit 4 should still be drawn at tick10")
	_assert(facing10 != null, "unit 4 should report a facing at tick10")
	if px0 == null or px10 == null or facing0 == null or facing10 == null:
		return

	_assert(float(facing0) != float(facing10),
		"R-100-01: unit 4's facing should change between tick0 (%s) and tick10 (%s) after a pure +x move" % [facing0, facing10])

	var dx: float = abs(float(px10[0]) - float(px0[0]))
	var dy: float = abs(float(px10[1]) - float(px0[1]))
	_assert(max(dx, dy) > 3.0,
		"unit 4's screen position should visibly move between the two frames (dx=%s dy=%s)" % [dx, dy])
	_assert(dx > 3.0 * dy or dy > 3.0 * dx,
		"unit 4 moved 75 wu along +x with y unchanged; the screen delta should read as one dominant axis, not a diagonal (dx=%s dy=%s)" % [dx, dy])


func _check_dead_unit_gone_and_hidden_unit_no_ghost() -> void:
	var state10: Dictionary = _root.qa_state()
	var units: Dictionary = state10.get("units", {})
	var px: Dictionary = state10.get("units_px", {})

	_assert(not units.has("2"), "R-136 placeholder: unit 2 died between the frames and must be gone from qa_state().units entirely")
	_assert(not px.has("2"), "unit 2 must have no drawn node at tick10")

	_assert(units.has("10"), "unit 10 is still alive at tick10 (fixture setup: only left faction 0's visible set)")
	_assert(not px.has("10"),
		"R-089-04: unit 10 left visible[\"0\"] at tick10; it must have no node and no ghost of its tick0 position")


func _check_command_move_R096_01() -> void:
	var cmd: Dictionary = _root.issue_command({"kind": "move", "unit_ids": [4], "x": 500.0, "y": 300.0})
	_assert(cmd.get("type") == "cmd", "move command must carry type=cmd, got %s" % cmd.get("type"))
	_assert(cmd.get("name") == "command_move", "move command name should be command_move, got %s" % cmd.get("name"))
	_assert(_ints_eq_ordered(cmd.get("unit_ids", []), [4]), "move command unit_ids should be [4], got %s" % str(cmd.get("unit_ids")))
	_assert(float(cmd.get("x", -1)) == 500.0 and float(cmd.get("y", -1)) == 300.0,
		"move command should carry the destination coordinates, got x=%s y=%s" % [cmd.get("x"), cmd.get("y")])


func _check_command_attack_move_R096_02() -> void:
	var cmd: Dictionary = _root.issue_command({"kind": "attack_move", "unit_ids": [1, 3], "x": 900.0, "y": 900.0})
	_assert(cmd.get("type") == "cmd", "attack-move command must carry type=cmd")
	_assert(cmd.get("name") == "command_attack_move", "attack-move command name should be command_attack_move, got %s" % cmd.get("name"))
	_assert(_ints_eq_ordered(cmd.get("unit_ids", []), [1, 3]), "attack-move command unit_ids should be [1, 3], got %s" % str(cmd.get("unit_ids")))
	_assert(float(cmd.get("x", -1)) == 900.0 and float(cmd.get("y", -1)) == 900.0,
		"attack-move command should carry the destination coordinates")


func _check_command_attack_target_R096_04() -> void:
	var cmd: Dictionary = _root.issue_command({"kind": "attack_target", "unit_ids": [1], "target": 7})
	_assert(cmd.get("type") == "cmd", "attack-target command must carry type=cmd")
	_assert(cmd.get("name") == "command_attack_target", "attack-target command name should be command_attack_target, got %s" % cmd.get("name"))
	_assert(_ints_eq_ordered(cmd.get("unit_ids", []), [1]), "attack-target command unit_ids should be [1], got %s" % str(cmd.get("unit_ids")))
	_assert(int(cmd.get("target", -999)) == 7, "attack-target command should carry the target id, got %s" % cmd.get("target"))


func _check_box_select_then_move_R105_01() -> void:
	var state: Dictionary = _root.qa_state()
	var px: Dictionary = state.get("units_px", {})
	var p1 = px.get("1")
	var p3 = px.get("3")
	_assert(p1 != null and p3 != null, "units 1 and 3 should both be drawn at tick10 (positive control for the box-select fixture)")
	if p1 == null or p3 == null:
		return

	var x0: float = min(float(p1[0]), float(p3[0])) - 2.0
	var y0: float = min(float(p1[1]), float(p3[1])) - 2.0
	var x1: float = max(float(p1[0]), float(p3[0])) + 2.0
	var y1: float = max(float(p1[1]), float(p3[1])) + 2.0

	var selected: Array = _root.qa_box_select(x0, y0, x1, y1)
	_assert(_same_set(_as_ints(selected), [1, 3]),
		"R-105-01: a box drawn tightly around units 1 and 3 should select exactly {1, 3}, got %s" % str(selected))

	var cmd: Dictionary = _root.issue_command({"kind": "move", "unit_ids": selected, "x": 10.0, "y": 20.0})
	_assert(_same_set(_as_ints(cmd.get("unit_ids", [])), [1, 3]),
		"a move issued right after the box-select should carry both selected ids, got %s" % str(cmd.get("unit_ids")))


# R-103-02: the mission canvas edges bound the camera; it never leaves the map.
func _check_camera_bounded_R103_02() -> void:
	var canvas: float = float(_frame10.get("map", {}).get("canvas", 0.0))
	_assert(canvas > 0.0, "fixture setup bug: map.canvas should be > 0")

	_root.qa_pan(canvas * 0.5, canvas * 0.5)
	var cam_mid: Dictionary = _root.qa_state().get("camera", {})
	_assert(abs(float(cam_mid.get("x", -1)) - canvas * 0.5) < 1.0 and abs(float(cam_mid.get("y", -1)) - canvas * 0.5) < 1.0,
		"clean: panning to the canvas centre should land there (positive control), got %s" % str(cam_mid))

	_root.qa_pan(999999.0, 999999.0)
	var cam_edge: Dictionary = _root.qa_state().get("camera", {})
	var cx: float = float(cam_edge.get("x", -1))
	var cy: float = float(cam_edge.get("y", -1))
	_assert(cx >= 0.0 and cx <= canvas and cy >= 0.0 and cy <= canvas,
		"R-103-02: panning far past the edge should clamp the camera inside [0, %s], got %s" % [canvas, str(cam_edge)])
	_assert(cx < 999999.0,
		"camera should not simply pass the raw pan target through unclamped")


func _check_plant_camera_unbounded() -> void:
	var canvas: float = float(_frame10.get("map", {}).get("canvas", 0.0))
	_assert(_root.qa_plant("camera-unbounded"), "qa_plant(camera-unbounded) must return true")
	_root.qa_pan(999999.0, 999999.0)
	var cam: Dictionary = _root.qa_state().get("camera", {})
	_assert(float(cam.get("x", 0.0)) > canvas,
		"PLANT camera-unbounded: the clamp should be gone, camera.x should exceed the canvas, got %s" % str(cam))


# The clean run above already proved unit 4's facing differs between tick0
# and tick10 (positive control). Under facing-fixed, reloading both frames
# must no longer reproduce that difference.
func _check_plant_facing_fixed_R100_01() -> void:
	_assert(_root.qa_plant("facing-fixed"), "qa_plant(facing-fixed) must return true")
	_root.load_frame(_frame0)
	await process_frame
	var facing_a = _root.qa_state().get("units", {}).get("4", {}).get("facing")
	_root.load_frame(_frame10)
	await process_frame
	var facing_b = _root.qa_state().get("units", {}).get("4", {}).get("facing")
	_assert(facing_a != null and facing_b != null, "unit 4's facing should still be reported under the plant")
	if facing_a != null and facing_b != null:
		_assert(float(facing_a) == float(facing_b),
			"PLANT facing-fixed: unit 4's facing should stay frozen across the two frames, got %s then %s" % [facing_a, facing_b])


# R-105-04: no select-all, select-all-army, or select-all-of-type command may
# ever exist. Unlike a normal plant (false until activated, true after),
# this id must never be wired to a fault site at all, so it stays false
# whether or not it is "planted".
func _check_select_all_never_exists_R105_04() -> void:
	_assert(not _root.qa_plant("select-all-exists"),
		"R-105-04: qa_plant(select-all-exists) must return false -- this scene must never expose a select-all fault site to enable")


func _check_plant_nope_and_all_real_plants_true() -> void:
	_assert(not _root.qa_plant("nope"), "qa_plant('nope') must return false")
	for id in PLANTS:
		_assert(_root.qa_plant(id), "qa_plant(%s) must return true" % id)


# Piece C2-8: the view reads player_faction from the loaded frame so that
# faction-1 units are the player's when player_faction == 1.
# RED before source change: LOCAL_FACTION constant is 0, so the pf=1 fixture
# drives the view as if the player were faction 0 (wrong colours, wrong visible
# set used).
func _run_c28_tests() -> void:
	SimSession_reset()
	var frame_pf1: Dictionary = _read_json(FIXTURE_PF1_PATH)
	_assert(not frame_pf1.is_empty(), "C2-8 fixture missing or unparsable: " + FIXTURE_PF1_PATH)
	if frame_pf1.is_empty():
		return
	_assert(int(frame_pf1.get("player_faction", -999)) == 1, "C2-8 fixture bug: player_faction should be 1, got %s" % frame_pf1.get("player_faction"))

	# The pf=1 fixture lists visible["1"] as the player's set and visible["0"]
	# as the opponent's set.  faction-1 unit ids: 7..12.  faction-0 ids: 1..6.
	# visible["1"] = [7,8,9,10,11,12,1,2,3,4]; 5 and 6 are outside that set.
	var expected_pf1: Array = frame_pf1.get("visible", {}).get("1", [])
	var faction1_ids: Array = []
	var faction0_ids: Array = []
	for u in frame_pf1.get("units", []):
		if int(u.get("faction", -1)) == 1:
			faction1_ids.append(int(u.get("id")))
		else:
			faction0_ids.append(int(u.get("id")))
	_assert(faction1_ids.size() > 0, "C2-8 fixture bug: no faction-1 units")
	_assert(faction0_ids.size() > 0, "C2-8 fixture bug: no faction-0 units")

	var view: Node = await _mount_view()
	view.load_frame(frame_pf1)
	await process_frame
	var st: Dictionary = view.qa_state()

	# local_faction must equal the frame's player_faction (1) once the source is fixed.
	# RED: local_faction == 0 because LOCAL_FACTION is a literal constant.
	_assert(int(st.get("local_faction", -1)) == 1,
		"C2-8: local_faction should be 1 when frame carries player_faction=1, got %s" % st.get("local_faction"))

	# The visible set for pf=1 is visible["1"]; drawn units should equal that set.
	var drawn_pf1: Array = _int_keys(st.get("units_px", {}))
	_assert(_same_set(drawn_pf1, expected_pf1),
		"C2-8 pf=1: drawn ids %s should equal visible['1'] %s" % [str(drawn_pf1), str(expected_pf1)])

	# faction-1 units inside visible["1"] must appear; faction-0 units outside it must not.
	for id in faction1_ids:
		_assert(drawn_pf1.has(id),
			"C2-8 pf=1: faction-1 unit %d should be drawn (own faction)" % id)
	var invisible_f0: Array = []
	for id in faction0_ids:
		if not (expected_pf1 as Array).map(func(v): return int(v)).has(id):
			invisible_f0.append(id)
	for id in invisible_f0:
		_assert(not drawn_pf1.has(id),
			"C2-8 pf=1: faction-0 unit %d is outside visible['1'] and must not be drawn" % id)

	view.queue_free()
	await process_frame

	# The pf=0 path: original fixture (no player_faction field) still works as before.
	SimSession_reset()
	var view0: Node = await _mount_view()
	view0.load_frame(_frame0)
	await process_frame
	var st0: Dictionary = view0.qa_state()
	_assert(int(st0.get("local_faction", -1)) == 0,
		"C2-8 pf=0: local_faction should be 0 with the original fixture, got %s" % st0.get("local_faction"))
	var expected_pf0: Array = _frame0.get("visible", {}).get("0", [])
	var drawn_pf0: Array = _int_keys(st0.get("units_px", {}))
	_assert(_same_set(drawn_pf0, expected_pf0),
		"C2-8 pf=0: drawn ids %s should equal visible['0'] %s" % [str(drawn_pf0), str(expected_pf0)])
	view0.queue_free()
	await process_frame
	SimSession_reset()
	_c28_completed = true


func _int_keys(d: Dictionary) -> Array:
	var out := []
	for k in d.keys():
		out.append(int(k))
	return out


func _as_ints(a: Array) -> Array:
	var out := []
	for v in a:
		out.append(int(v))
	return out


# Array equality/`.has()` in GDScript compares element type strictly (1 ==
# 1.0 as scalars, but [1] == [1.0] as arrays is false, and [1.0].has(1) is
# false); JSON always parses whole numbers as floats, so every id set this
# file compares is normalized to int here, never left to the caller.
func _same_set(a: Array, b: Array) -> bool:
	var ia := _as_ints(a)
	var ib := _as_ints(b)
	if ia.size() != ib.size():
		return false
	for v in ia:
		if not ib.has(v):
			return false
	return true


func _ints_eq_ordered(a: Array, b: Array) -> bool:
	var ia := _as_ints(a)
	var ib := _as_ints(b)
	if ia.size() != ib.size():
		return false
	for i in range(ia.size()):
		if ia[i] != ib[i]:
			return false
	return true


func _read_json(path: String) -> Dictionary:
	var f := FileAccess.open(path, FileAccess.READ)
	if f == null:
		return {}
	var text := f.get_as_text()
	f.close()
	var data = JSON.parse_string(text)
	return data if typeof(data) == TYPE_DICTIONARY else {}
