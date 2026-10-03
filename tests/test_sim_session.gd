extends SceneTree

# Piece C2-6: one pipe session for the whole run, shared by every scene.
# autoload/sim_session.gd is a static holder (no project autoload line needed):
# SimSession.bridge() returns the one c_bridge.gd instance for the process,
# created on first use and never replaced; the scenes ask it for their frames
# (c_bridge.gd ensure_session / load_*_live) and never close it. What this
# proves is continuity: the world the galaxy stepped is the world the
# briefing, debrief and chronicle then read, and it is still there when the
# galaxy scene is built again.
#
# Contract required of c_bridge.gd on top of C2-4's session API:
#   ensure_session(seed, n_regions, features) -> bool   open if closed, reuse if the same
#                                                       arguments are open, else reopen;
#                                                       blocks until the first snapshot
#   session_id() -> int                                 +1 on every (re)open
#   mission_active() -> bool                            set by a mission frame, cleared by a debrief
#   load_mission_live / load_debrief_live / load_chronicle_live / load_tactical_live
#       (seed, n_regions, features) run over the open session (no new process)
# and of autoload/sim_session.gd: static bridge() and reset() (close + forget).

const SimSession := preload("res://autoload/sim_session.gd")
const GALAXY_SCENE := "res://scenes/galaxy/galaxy_view.tscn"
const BRIEFING_SCENE := "res://scenes/mission_briefing/mission_briefing.tscn"
const DEBRIEF_SCENE := "res://scenes/debrief/debrief.tscn"
const CHRONICLE_SCENE := "res://scenes/world/chronicle_scroll_panel.tscn"
const STEPS := 200

var _pass_count := 0
var _fail_count := 0
var _fail_msgs: Array[String] = []
var _completed := false


func _initialize() -> void:
	await _run_tests()
	_assert(_completed, "the session checks did not run to the end (a script error aborted them, or autoload/sim_session.gd / c_bridge.gd lack the contract above)")
	print("\n=== Sim Session Test Results ===")
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


func _owners(snap: Dictionary) -> Dictionary:
	var out := {}
	for r in snap.get("regions", []):
		out[int(r.get("i", -1))] = int(r.get("owner", -1))
	return out


func _pump_until(bridge, pred: Callable, timeout_ms: int) -> bool:
	var deadline := Time.get_ticks_msec() + timeout_ms
	while Time.get_ticks_msec() < deadline:
		bridge.pump()
		if pred.call():
			return true
		OS.delay_msec(5)
	return false


func _mount(path: String) -> Node:
	var scene: Node = (load(path) as PackedScene).instantiate()
	get_root().add_child(scene)
	await process_frame
	await process_frame
	return scene


func _run_tests() -> void:
	var holder = SimSession
	var names := []
	for m in (holder as GDScript).get_script_method_list():
		names.append(m["name"])
	_assert(names.has("bridge") and names.has("reset"), "autoload/sim_session.gd lacks static bridge() / reset()")
	if not (names.has("bridge") and names.has("reset")):
		return
	holder.reset()
	var bridge = holder.bridge()
	_assert(bridge == holder.bridge(), "SimSession.bridge() did not return the same instance twice")
	for m in ["ensure_session", "session_id", "mission_active"]:
		_assert(bridge.has_method(m), "c_bridge.gd missing method (piece C2-6 not attached yet): " + m)
		if not bridge.has_method(m):
			return
	var CBridge = load("res://autoload/c_bridge.gd")
	var features = CBridge.DEFAULT_FEATURES
	var n: int = CBridge.DEFAULT_N_REGIONS

	# new_campaign:false throughout -- this test is about session identity
	# (reuse/reopen/recover), not R-056-04's opening jump; the tick check
	# below needs a raw tick-0 world.
	_assert(bridge.ensure_session(1, n, features, false), "ensure_session(1) failed: %s" % bridge.last_error())
	var id1: int = bridge.session_id()
	_assert(bridge.ensure_session(1, n, features, false) and bridge.session_id() == id1, "the same arguments reopened the session (id %d -> %d)" % [id1, bridge.session_id()])
	_assert(bridge.ensure_session(2, n, features, false) and bridge.session_id() == id1 + 1, "different arguments did not reopen the session")
	_assert(not bridge.ensure_session(1, 30, features, false) and bridge.last_error() == "generation failed", "ensure_session below the region floor did not fail with 'generation failed' (last_error = %s)" % bridge.last_error())
	_assert(bridge.ensure_session(1, n, features, false), "ensure_session(1) after a failed open did not recover: %s" % bridge.last_error())

	# The galaxy steps the world; leaving the scene must not end it.
	var galaxy: Node = await _mount(GALAXY_SCENE)
	var start_tick := int(bridge.snapshot().get("tick", -1))
	_assert(start_tick == 0, "world tick before stepping = %d, expected 0" % start_tick)
	var id_run: int = bridge.session_id()
	galaxy.qa_step(STEPS)
	var ran := _pump_until(bridge, func(): return int(bridge.snapshot().get("tick", 0)) >= STEPS, 30000)
	_assert(ran, "the shared world did not reach tick %d (tick = %s)" % [STEPS, bridge.snapshot().get("tick")])
	await process_frame
	var galaxy_owners := _owners(bridge.snapshot())
	var initial_owned := 0
	for k in galaxy.qa_state().get("owners", {}):
		if int(galaxy.qa_state()["owners"][k]) >= 0:
			initial_owned += 1
	galaxy.queue_free()
	await process_frame
	_assert(bridge.session_id() == id_run, "freeing the galaxy scene ended or reopened the session")
	_assert(int(bridge.snapshot().get("tick", -1)) >= STEPS, "the world was reset by leaving the galaxy (tick = %s)" % bridge.snapshot().get("tick"))

	# The next scenes read the same world.
	var briefing: Node = await _mount(BRIEFING_SCENE)
	_assert(bridge.mission_active(), "the briefing scene did not leave a mission running on the shared world")
	_assert(bridge.session_id() == id_run, "the briefing scene opened its own session")
	briefing.queue_free()
	await process_frame
	# A39(b), ledger row day12 "A39 fixture changes": the debrief shows the frame the bridge
	# holds and no longer ends the mission itself; end it through the bridge first (as the
	# tactical view does).
	bridge.send_command({"type": "cmd", "name": "mission_end"})
	_assert(_pump_until(bridge, func(): return not bridge.mission_active(), 5000), "mission_end did not end the mission the briefing left running")
	var debrief: Node = await _mount(DEBRIEF_SCENE)
	_assert(not bridge.mission_active(), "the debrief scene left a mission running after the one it followed ended")
	_assert(bridge.session_id() == id_run, "the debrief scene opened its own session")
	debrief.queue_free()
	await process_frame
	# A69 (ledger TD-A69-simsession): the jump is issued once, by the debrief's Proceed
	# (_on_continue -> load_chronicle_live); opening the chronicle scene sends nothing.
	var tick_before_jump := int(bridge.snapshot().get("tick", -1))
	_assert(bridge.load_chronicle_live(bridge.live_seed(), n, features), "load_chronicle_live (the debrief's Proceed call) failed: %s" % bridge.last_error())
	_assert(bridge.session_id() == id_run, "the debrief's Proceed jump opened its own session")
	_assert(int(bridge.snapshot().get("tick", -1)) == tick_before_jump + 50, "the Proceed jump did not advance the shared world by 50 (tick %d -> %s)" % [tick_before_jump, bridge.snapshot().get("tick")])
	var tick_after_jump := int(bridge.snapshot().get("tick", -1))
	var chronicle: Node = await _mount(CHRONICLE_SCENE)
	_assert(bridge.session_id() == id_run, "the chronicle scene opened its own session")
	_assert(int(bridge.snapshot().get("tick", -1)) == tick_after_jump, "opening the chronicle scene sent a further jump (tick %d -> %s)" % [tick_after_jump, bridge.snapshot().get("tick")])
	chronicle.queue_free()
	await process_frame

	# A new galaxy scene shows the world as it now is, conquests included.
	var again: Node = await _mount(GALAXY_SCENE)
	_assert(bridge.session_id() == id_run, "the second galaxy scene opened its own session")
	var shown: Dictionary = again.qa_state().get("owners", {})
	var changed := 0
	for i in shown:
		if int(shown[i]) != int(_owners(bridge.snapshot()).get(int(i), -99)):
			changed += 1
	_assert(changed == 0, "the rebuilt galaxy shows %d owners that differ from the shared world" % changed)
	_assert(int(again.qa_state().get("tick", -1)) == tick_after_jump, "the rebuilt galaxy reports tick %s, expected the shared world's %d (after the Proceed jump, none from opening the chronicle)" % [again.qa_state().get("tick"), tick_after_jump])
	var reowned := 0
	for i in shown:
		if int(shown[i]) >= 0:
			reowned += 1
	_assert(reowned > 0, "the rebuilt galaxy shows no owned regions")
	again.queue_free()
	await process_frame

	holder.reset()
	_assert(holder.bridge().session_id() >= 0, "reset() left the holder unusable")
	_completed = true
