extends SceneTree
# test-timeout: 30000

# G-C3 client unit 2 (A48 item 13, A52, A59, A65; E-09 R-069-03, R-069-05;
# E-16 R-110-02/07): scenes/world/time_jump_sequencer.gd replays the map from
# the chronicle frame's "ownership" snapshots (docs/architecture.md "chronicle
# frame") instead of SimBridge.ownership_timeline.
#
# Interface this test fixes (the Doer builds exactly this; Q-candidates in the
# report where the rulings leave a choice):
#   const REPLAY_TICKS_PER_SECOND  (2, A52; the only place the speed lives)
#   func load_frame(frame: Dictionary, live_owners: Array) -> void
#       frame is a chronicle frame; live_owners is the owner per region index
#       (-1 unowned) of the world the client holds after the jump. It starts
#       a replay, replacing any replay in progress.
#   _ready() does the same from SimSession.bridge().chronicle_frame() and the
#       bridge's region owners (the wiring; checked in _check_wired_live).
#   qa_state()["replay"] = {active: bool, tick: int, from_tick: int,
#       to_tick: int, snapshot_count: int, shown_owners: Array[int],
#       keyframes_hit: Array[int], entries_started: Array[int]}
#       tick = the tick the map currently shows (from_tick .. to_tick),
#       shown_owners = the owner per region the map currently shows,
#       keyframes_hit = frame keyframes the replay clock has passed, in order,
#       entries_started = ids of entries whose start_tick the clock reached,
#       in order (an entry begins printing there). The live frame's replay takes
#       its computed reading time, not a fixed 25 s: while the scroll prints and
#       holds an entry the map waits at the next keyframe (R-069-03, Q-069-03 (a),
#       Westley 2026-10-19; TD-VG-B-22 supersedes the A52 fixed-time reading).
# Behaviour:
#   * the replay takes (to_tick - from_tick) / REPLAY_TICKS_PER_SECOND seconds
#     (tolerance TOL_SYNTH / TOL_LIVE below); snapshot k is shown from tick
#     from_tick + 2k; odd lengths get no final snapshot, the last picture is
#     live_owners, reached at to_tick (A59);
#   * "ownership" absent (after a load): no replay at all, the map shows
#     live_owners at once, tick == to_tick (A59);
#   * SimBridge.ownership_timeline is never read (a decoy there changes nothing).
# Positive control: with the fields present the replay runs (active true, tick
# moves, shown_owners changes). Mutation control: the timing checks read the
# real clock, so any constant other than 2 fails them; the constant is also
# read straight from the script.

const SCENE_PATH := "res://scenes/world/time_jump_sequencer.tscn"
const SCRIPT_PATH := "res://scenes/world/time_jump_sequencer.gd"
const TOL_SYNTH := 0.4  # seconds; a few frames at 60 fps (provisional, Westley owns tolerances)
const TOL_LIVE := 1.0   # seconds; the live frame is built while the scene loads
const LIVE_N_REGIONS := 60
const ENTRY_HOLD_S := 3.0  # R-069-03: a printed entry holds 3.0 s (Q-069-03 (a), Westley 2026-10-19)
const MODEL_DT := 0.005    # seconds; step of the reading-time model, far below the tolerance
const LOOP_MARGIN_S := 10.0  # seconds past computed time plus TOL_LIVE before the wait loop gives up

var _pass_count := 0
var _fail_count := 0
var _fail_msgs: Array[String] = []


func _initialize() -> void:
	await _run_tests()
	print("\n=== Time Jump Replay Results ===")
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


func _synth_frame(from_tick: int, to_tick: int, snapshots: Array, keyframes: Array, entries: Array) -> Dictionary:
	return {
		"type": "chronicle",
		"jump": {"from_tick": from_tick, "to_tick": to_tick, "chapter_end_reason": 0},
		"entries": entries,
		"ownership": {"stride": 2, "from_tick": from_tick, "n_regions": 4, "snapshots": snapshots},
		"keyframes": keyframes,
	}


func _entry(id: int, s: int, e: int) -> Dictionary:
	return {"id": id, "start_tick": s, "end_tick": e, "category": 3, "cluster_type": 1,
		"refs": {"regions": [0], "factions": [0]}, "fragment": -1, "fragment_ids": [-1, -1, -1], "significance": 0.8}


func _mount() -> Node:
	load("res://autoload/sim_session.gd").reset()
	var root_node: Node = (load(SCENE_PATH) as PackedScene).instantiate()
	get_root().add_child(root_node)
	await process_frame
	await process_frame
	return root_node


func _replay(node: Node) -> Dictionary:
	return (node.qa_state() as Dictionary).get("replay", {})


func _run_tests() -> void:
	var script: Script = load(SCRIPT_PATH)
	var consts: Dictionary = script.get_script_constant_map()
	_assert(consts.has("REPLAY_TICKS_PER_SECOND"), "A52: time_jump_sequencer.gd has no REPLAY_TICKS_PER_SECOND constant")
	_assert(consts.has("REPLAY_TICKS_PER_SECOND") and float(consts["REPLAY_TICKS_PER_SECOND"]) == 2.0,
		"A52: REPLAY_TICKS_PER_SECOND = %s, expected 2" % str(consts.get("REPLAY_TICKS_PER_SECOND")))

	var decoy: Array = []
	for i in range(7):
		decoy.append({"0": "decoy_faction"})
	var sim_bridge = get_root().get_node_or_null("SimBridge")
	if sim_bridge != null:
		sim_bridge.ownership_timeline = decoy

	var node: Node = await _mount()
	if not (node.has_method("load_frame") and "replay" in node.qa_state()):
		_assert(node.has_method("load_frame"), "sequencer has no load_frame(frame, live_owners)")
		_assert("replay" in node.qa_state(), "sequencer qa_state() has no \"replay\" block")
		node.queue_free()
		return
	await _check_even(node)
	await _check_odd(node)
	await _check_absent(node)
	node.queue_free()
	await process_frame
	await _check_wired_live()
	if sim_bridge != null:
		sim_bridge.ownership_timeline = []


# 10 ticks, 6 snapshots (ticks 100,102,...,110); the last equals the live state.
func _check_even(node: Node) -> void:
	var snaps := [[0, 0, 1, -1], [0, 0, 1, -1], [0, 1, 1, -1], [0, 1, 1, 1], [1, 1, 1, 1], [1, 1, 1, 2]]
	var live := [1, 1, 1, 2]
	var kfs := [102, 105, 108]
	var entries := [_entry(1, 103, 106), _entry(2, 108, 110)]
	var frame := _synth_frame(100, 110, snaps, kfs, entries)
	var t0 := Time.get_ticks_msec()
	node.load_frame(frame, live)
	await process_frame
	var r: Dictionary = _replay(node)
	_assert(bool(r.get("active", false)), "positive control: with ownership present the replay is not active")
	_assert(int(r.get("snapshot_count", -1)) == 6, "even: snapshot_count = %s, expected 6 (the decoy SimBridge timeline has 7)" % str(r.get("snapshot_count")))
	_assert(int(r.get("from_tick", -1)) == 100 and int(r.get("to_tick", -1)) == 110, "even: from/to tick = %s/%s, expected 100/110" % [str(r.get("from_tick")), str(r.get("to_tick"))])
	_assert(r.get("shown_owners", []) == snaps[0], "even: first picture %s, expected snapshot 0 %s" % [str(r.get("shown_owners")), str(snaps[0])])
	var seen_owners := {}
	var order_ok := true
	var late_msg := ""
	var early_msg := ""
	var elapsed := 0.0
	var mid_tick := -1
	while bool(r.get("active", false)) and Time.get_ticks_msec() - t0 < 12000:
		await process_frame
		r = _replay(node)
		elapsed = (Time.get_ticks_msec() - t0) / 1000.0
		var tick := int(r.get("tick", -1))
		seen_owners[str(r.get("shown_owners"))] = true
		if elapsed >= 2.5 and mid_tick < 0:
			mid_tick = tick
		# snapshot k is on screen from tick 100+2k; the shown picture is one of the frame's snapshots
		var idx := (tick - 100) / 2
		if bool(r.get("active", false)) and idx >= 0 and idx < snaps.size() and r.get("shown_owners", []) != snaps[idx]:
			order_ok = false
		for k in r.get("keyframes_hit", []):
			if int(k) > tick:
				early_msg = "keyframe %d hit at replay tick %d" % [int(k), tick]
		for k in kfs:
			if tick >= int(k) + 1 and not (r.get("keyframes_hit", []) as Array).has(k):
				late_msg = "keyframe %d still not hit at replay tick %d" % [int(k), tick]
		for id in r.get("entries_started", []):
			var st := 103 if int(id) == 1 else 108
			if st > tick:
				early_msg = "entry %d started at replay tick %d (start_tick %d)" % [int(id), tick, st]
	_assert(not bool(r.get("active", false)), "even: replay still active after 12 s")
	_assert(absf(elapsed - 5.0) <= TOL_SYNTH, "R-069-03: a 10-tick replay took %.2f s, expected 5.0 s +/- %.1f" % [elapsed, TOL_SYNTH])
	_assert(mid_tick >= 104 and mid_tick <= 106, "even: replay tick after 2.5 s = %d, expected about 105" % mid_tick)
	_assert(order_ok, "even: the picture shown did not follow snapshot[(tick-from_tick)/2] while the replay ran")
	_assert(seen_owners.size() >= 5, "even: only %d distinct pictures shown across the replay, expected the frame's 6 snapshots" % seen_owners.size())
	_assert(early_msg == "", "R-069-05/03: " + early_msg)
	_assert(late_msg == "", "R-069-05: " + late_msg)
	_assert(r.get("keyframes_hit", []) == kfs, "even: keyframes_hit = %s, expected %s" % [str(r.get("keyframes_hit")), str(kfs)])
	_assert(r.get("entries_started", []) == [1, 2], "even: entries_started = %s, expected [1, 2]" % str(r.get("entries_started")))
	_assert(r.get("shown_owners", []) == live, "even: final picture %s != live state %s" % [str(r.get("shown_owners")), str(live)])
	_assert(int(r.get("tick", -1)) == 110, "even: final tick %s, expected 110" % str(r.get("tick")))


# 9 ticks, 5 snapshots (ticks 100..108): no final snapshot; live differs from the last one.
func _check_odd(node: Node) -> void:
	var snaps := [[0, 0, 1, -1], [0, 0, 1, -1], [0, 1, 1, -1], [0, 1, 1, 1], [1, 1, 1, 1]]
	var live := [2, 2, 2, 2]
	var frame := _synth_frame(100, 109, snaps, [], [])
	var t0 := Time.get_ticks_msec()
	node.load_frame(frame, live)
	await process_frame
	var r: Dictionary = _replay(node)
	var last_pic_before_live: Array = []
	while bool(r.get("active", false)) and Time.get_ticks_msec() - t0 < 12000:
		await process_frame
		r = _replay(node)
		if bool(r.get("active", false)):
			last_pic_before_live = r.get("shown_owners", [])
	var elapsed := (Time.get_ticks_msec() - t0) / 1000.0
	_assert(int(r.get("snapshot_count", -1)) == 5, "odd: snapshot_count = %s, expected 5" % str(r.get("snapshot_count")))
	_assert(absf(elapsed - 4.5) <= TOL_SYNTH, "R-069-03: a 9-tick replay took %.2f s, expected 4.5 s +/- %.1f" % [elapsed, TOL_SYNTH])
	_assert(r.get("shown_owners", []) == live, "A59: odd length ends on %s, expected the live state %s (no final snapshot)" % [str(r.get("shown_owners")), str(live)])
	_assert(int(r.get("tick", -1)) == 109, "odd: final tick %s, expected 109" % str(r.get("tick")))
	_assert(last_pic_before_live != live, "odd: the live state appeared before the replay ended")
	_assert((r.get("keyframes_hit", [1]) as Array).is_empty(), "odd: keyframes_hit not empty with no keyframes in the frame")


# A59: both fields absent (a load): no replay, the final state at once.
func _check_absent(node: Node) -> void:
	var live := [1, 1, 1, 2]
	var frame := {"type": "chronicle", "jump": {"from_tick": 100, "to_tick": 110, "chapter_end_reason": 0},
		"entries": [_entry(1, 103, 106)]}
	node.load_frame(frame, live)
	var samples := 0
	var ever_active := false
	var t0 := Time.get_ticks_msec()
	while Time.get_ticks_msec() - t0 < 1500:
		await process_frame
		var r: Dictionary = _replay(node)
		ever_active = ever_active or bool(r.get("active", false))
		samples += 1
		if samples == 1:
			_assert(r.get("shown_owners", []) == live, "A59: with no \"ownership\" the first picture is %s, expected the live state %s" % [str(r.get("shown_owners")), str(live)])
			_assert(int(r.get("tick", -1)) == 110, "A59: with no \"ownership\" the tick shown is %s, expected 110" % str(r.get("tick")))
	_assert(not ever_active, "A59: with no \"ownership\" a replay ran")
	# ownership absent but keyframes present: still nothing to replay
	var frame2: Dictionary = frame.duplicate(true)
	frame2["keyframes"] = [103]
	node.load_frame(frame2, live)
	await process_frame
	await process_frame
	_assert(not bool(_replay(node).get("active", false)), "A59: keyframes alone started a replay")
	_assert(_replay(node).get("shown_owners", []) == live, "A59: keyframes alone changed the picture")


# Reading time of a replay, computed from the loaded frame (R-069-03, Q-069-03 (a), "time varying is
# ok it is like a book", Westley 2026-10-19; supersedes the fixed 50 ticks = 25 s of A52). The map runs at
# REPLAY_TICKS_PER_SECOND; entries print one at a time, first in first out, each taking
# words * word_interval + fade seconds (the last word's fade ends the entry) and then holding hold_s
# before the next may start; while the scroll is busy the map holds at the first keyframe it has not
# yet hit, and resumes from it once the printing entry and its hold have passed. frame_s is the mean frame
# time of the run: every timer and tween the panel uses ends on a frame boundary, so each word costs half a
# frame more than its interval and each entry about two frames more (fade end, hold end, next start);
# frame_s = 0 gives the ideal reading time with no frame quantisation.
# entry_words: entry id -> words on screen; start_tick of each entry comes from the frame.
func _computed_reading_s(frame: Dictionary, entry_words: Dictionary, word_interval_s: float, fade_s: float, hold_s: float, ticks_per_s: float, frame_s: float = 0.0) -> float:
	var from_tick := int(frame["jump"]["from_tick"])
	var to_tick := int(frame["jump"]["to_tick"])
	var keyframes: Array = frame.get("keyframes", [])
	var entries: Array = frame.get("entries", [])
	var t := 0.0
	var clock := 0.0
	var started := {}
	var hit := {}
	var queue: Array = []
	var printing_left := 0.0
	var printing := false
	var hold_left := 0.0
	while t < 1000.0:
		clock += MODEL_DT * ticks_per_s
		var tick := from_tick + int(clock)
		var busy := printing or hold_left > 0.0 or not queue.is_empty()
		var held_kf := -1
		if busy:
			for k in keyframes:
				if not hit.has(int(k)):
					if tick >= int(k):
						tick = int(k)
						clock = float(tick - from_tick)
						held_kf = tick
					break
		for k in keyframes:
			if int(k) <= tick and int(k) != held_kf:
				hit[int(k)] = true
		for e in entries:
			var id := int(e["id"])
			if held_kf >= 0 and int(e["start_tick"]) >= held_kf:
				continue
			if int(e["start_tick"]) <= tick and not started.has(id):
				started[id] = true
				queue.append(id)
		t += MODEL_DT
		if tick >= to_tick:
			return t
		if hold_left > 0.0:
			hold_left = maxf(0.0, hold_left - MODEL_DT)
		if printing:
			printing_left -= MODEL_DT
			if printing_left <= 0.0:
				printing = false
				hold_left = hold_s
		if not printing and hold_left <= 0.0 and not queue.is_empty():
			var next_id: int = queue.pop_front()
			printing = true
			printing_left = float(entry_words.get(next_id, 0)) * (word_interval_s + 0.5 * frame_s) + fade_s + 2.0 * frame_s
	return t


# Wiring: with no load_frame() call the scene replays the frame the bridge holds, ending on the bridge's
# live owners. The time it takes is the computed reading time of that frame (see _computed_reading_s).
func _check_wired_live() -> void:
	var bridge = load("res://autoload/sim_session.gd").bridge()
	var CBridge = load("res://autoload/c_bridge.gd")
	if not bridge.load_chronicle_live(1, CBridge.DEFAULT_N_REGIONS, CBridge.DEFAULT_FEATURES):
		_assert(false, "wired: load_chronicle_live failed: %s" % bridge.last_error())
		return
	var node: Node = (load(SCENE_PATH) as PackedScene).instantiate()
	get_root().add_child(node)
	await process_frame
	await process_frame
	var r: Dictionary = _replay(node)
	_assert(bool(r.get("active", false)), "wired: the scene did not start a replay from the bridge's chronicle frame")
	_assert(int(r.get("snapshot_count", -1)) == 26, "wired: snapshot_count = %s, expected 26 for a 50-tick jump (the decoy SimBridge timeline has 7)" % str(r.get("snapshot_count")))
	_assert(int(r.get("to_tick", 0)) - int(r.get("from_tick", 0)) == 50, "wired: replay spans %s ticks, expected 50" % str(int(r.get("to_tick", 0)) - int(r.get("from_tick", 0))))
	_assert((r.get("shown_owners", []) as Array).size() == CBridge.DEFAULT_N_REGIONS, "wired: shown_owners has %d entries, expected %d" % [(r.get("shown_owners", []) as Array).size(), CBridge.DEFAULT_N_REGIONS])
	# the premise, all from the frame this scene holds: entries, words on screen, pace
	var frame: Dictionary = bridge.chronicle_frame()
	var scroll_qa: Dictionary = node.get("_scroll").qa_state()
	var entry_words := {}
	for qe in scroll_qa.get("entries", []):
		entry_words[int(qe["entry_id"])] = (str(qe["text"]) as String).split(" ", false).size()
	var pace: Dictionary = scroll_qa.get("pace", {})
	var word_interval_s := float(pace.get("word_interval_s", 0.0))
	var fade_s := float(pace.get("fade_s", 0.0))
	var ideal := _computed_reading_s(frame, entry_words, word_interval_s, fade_s, ENTRY_HOLD_S, 2.0)
	var total_words := 0
	for id in entry_words:
		total_words += int(entry_words[id])
	_assert(entry_words.size() == (frame.get("entries", []) as Array).size() and total_words > 0 and ideal > 25.0,
		"wired: the premise is %d entries shown of %d, %d words, computed reading time %.1f s; expected every entry shown, words on screen, and more than the map alone (25 s)" % [entry_words.size(), (frame.get("entries", []) as Array).size(), total_words, ideal])
	print("INFO: live replay premise: %d entries, %d words, pace %s, hold %.1f s, ideal computed reading time %.2f s" % [entry_words.size(), total_words, str(pace), ENTRY_HOLD_S, ideal])
	var t0 := Time.get_ticks_msec()
	var frames := 0
	while bool(r.get("active", false)) and Time.get_ticks_msec() - t0 < int((ideal + TOL_LIVE + LOOP_MARGIN_S) * 1000.0):
		await process_frame
		frames += 1
		r = _replay(node)
	var elapsed := (Time.get_ticks_msec() - t0) / 1000.0
	var frame_s := elapsed / maxf(float(frames), 1.0)
	var expected := _computed_reading_s(frame, entry_words, word_interval_s, fade_s, ENTRY_HOLD_S, 2.0, frame_s)
	print("INFO: live replay took %.2f s from the first check over %d frames (mean frame %.2f ms); computed %.2f s with frame quantisation" % [elapsed, frames, frame_s * 1000.0, expected])
	_assert(absf(elapsed - expected) <= TOL_LIVE, "R-069-03: the live 50-tick replay took %.1f s from the first check, expected the computed reading time %.1f s +/- %.1f" % [elapsed, expected, TOL_LIVE])
	var live: Array = []
	for i in range(CBridge.DEFAULT_N_REGIONS):
		live.append(bridge.owner_of(i))
	_assert(r.get("shown_owners", []) == live, "wired: the replay did not end on the bridge's live owners")
	node.queue_free()
	await process_frame
