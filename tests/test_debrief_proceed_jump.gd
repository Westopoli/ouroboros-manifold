extends SceneTree

# A69 (docs/northstar/plans/2026-10-01-architect-rulings-2.md Addendum 27) with
# E-09 R-069-01: the jump is issued once, by the flow that leads to the
# chronicle, which is Proceed from the debrief (debrief.gd _on_continue, the
# CONTINUE button). That flow holds the jump's frame on the shared bridge; the
# chronicle scene that opens afterwards only reads it and sends nothing.
# A74: Proceed routes to "time_jump". A75: Proceed issues the jump once through
# the bridge (load_chronicle_live), the bridge holds the frame, the sequencer
# reads chronicle_frame() and hands that frame to the panel; neither scene jumps.
# TESTS FIRST. Expected RED today: Proceed sends no jump (the chronicle panel's
# _ready does, later) and routes to "chronicle", so the flow checks fail; the control (Proceed still emits
# debrief_completed and routes onward) is GREEN.
#
# Run: xvfb-run -a godot --headless --path . -s res://tests/test_debrief_proceed_jump.gd

const SIM_SESSION := "res://autoload/sim_session.gd"
const RecordingBridge := preload("res://tests/support/recording_bridge.gd")

var _pass_count := 0
var _fail_count := 0
var _fail_msgs: Array[String] = []


func _initialize() -> void:
	await _run_tests()
	print("\n=== Debrief Proceed Jump Results ===")
	print("PASS: %d  FAIL: %d" % [_pass_count, _fail_count])
	for msg in _fail_msgs:
		print("  - " + msg)
	print("=== %s ===\n" % ("RED" if _fail_count > 0 else "GREEN"))
	quit(1 if _fail_count > 0 else 0)


func _assert(cond: bool, msg: String) -> void:
	if cond:
		_pass_count += 1
	else:
		_fail_count += 1
		_fail_msgs.append(msg)


func _run_tests() -> void:
	var session = load(SIM_SESSION)
	session.reset()
	var bridge = RecordingBridge.new()
	bridge._debrief = {"type": "debrief", "band": 2, "achieved": 0.8, "brought_home": 0.6,
		"region_delta": {"military": -4.0, "economy": 2.0, "tension": -3.0, "population": 0.0}}
	bridge._snapshot = {"type": "snapshot", "tick": 100, "regions": [{"i": 0, "owner": 0}, {"i": 1, "owner": 1}], "factions": [{"id": 0}, {"id": 1}]}
	var frame := {
		"type": "chronicle",
		"jump": {"from_tick": 100, "to_tick": 150, "chapter_end_reason": 0},
		"entries": [{"id": 7, "start_tick": 120, "end_tick": 130, "category": 3, "cluster_type": 1,
			"refs": {"regions": [0], "factions": [0]}, "fragment": -1, "fragment_ids": [-1, -1, -1],
			"significance": 0.8, "text": "The border held.", "mentions": [], "expanded_text": "", "expanded_mentions": []}],
	}
	bridge.canned_chronicle = frame
	bridge.canned_snapshot = bridge._snapshot
	session.set("_bridge", bridge)

	var debrief: Node = (load("res://scenes/debrief/debrief.tscn") as PackedScene).instantiate()
	get_root().add_child(debrief)
	await process_frame
	await process_frame
	_assert(bridge.count("jump") == 0, "A69: the debrief sent `jump` before Proceed")

	var completed := [false]
	debrief.debrief_completed.connect(func(): completed[0] = true)
	debrief._on_continue()
	# control: unchanged behaviour
	_assert(completed[0], "control: Proceed no longer emits debrief_completed")

	# A74: Proceed routes to the sequencer, which embeds the scroll; "chronicle" is not on this path
	_assert(str(get_root().get_node("SceneRouter").get("_current_scene_name")) == "time_jump",
		"A74: Proceed routed to %s, expected time_jump" % str(get_root().get_node("SceneRouter").get("_current_scene_name")))

	# the jump is issued by Proceed itself, before any scene change, exactly once
	_assert(bridge.count("jump") == 1,
		"A69: Proceed from the debrief issued %d `jump` command(s) by the time it returned, expected exactly 1" % bridge.count("jump"))
	_assert(bridge.chronicle_frame() == frame,
		"A69: after Proceed the bridge does not hold the jump's frame for the sequencer to take")

	# the chronicle scene that opens next adds none and shows the held frame
	var seq: Node = (load("res://scenes/world/time_jump_sequencer.tscn") as PackedScene).instantiate()
	get_root().add_child(seq)
	await process_frame
	await process_frame
	await create_timer(1.5).timeout
	_assert(bridge.count("jump") == 1,
		"A69: after the chronicle scene opened the session has seen %d `jump` commands, expected exactly 1 (Proceed's)" % bridge.count("jump"))
	var replay: Dictionary = seq.qa_state().get("replay", {})
	_assert(int(replay.get("to_tick", -1)) == 150 and int(replay.get("from_tick", -1)) == 100,
		"A69: the sequencer is not showing the frame Proceed's jump produced (replay %s)" % str(replay))
	var panel = seq.get("_scroll")
	var ids: Array = []
	if panel != null:
		for e in panel.qa_state().get("entries", []):
			ids.append(int(e.get("entry_id", -1)))
	_assert(ids == [7], "A69: the scroll panel shows entries %s, expected [7] from Proceed's frame" % str(ids))
	seq.queue_free()
	debrief.queue_free()
	session.reset()
