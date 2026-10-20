extends SceneTree
# test-timeout: 10000

# VG-B26-chronicle-serial: the chronicle scroll prints one entry at a time, like a book.
# TESTS FIRST: written against the tree where chronicle_scroll_panel.gd start_printing starts an
# entry at once (no queue, no hold) and the sequencer's _advance_replay never waits for the scroll.
#
# Rules proved (docs/bible/epics/E-09-chronicle.md, word for word):
#
# R-069-03 (:98): "Given the map animation is the master clock, When an entry's tick range is
#   reached and no other entry is printing, Then that entry begins printing; entries print one
#   after another, never two at once, so the scroll reads like a book (Westley, 2026-10-13, on the
#   S-108 frame: "in the python version they were printed out one at a time so the user would read
#   it like a book"); an entry whose tick is reached while another prints waits its turn; a printed
#   entry holds for at least 3.0 s. Whether the map holds at that entry's keyframe until it has
#   printed is open (Q-069-03)."
# R-069-04 (:99): "Given an entry is printing, When the player clicks it, Then nothing happens;
#   Given it is printed (blinking cursor shown), When clicked, Then the expanded form overlays the
#   scroll and the map, clock, and any printing entry pause; dismissing resumes from the exact word
#   and frame."
# Q-069-03 (a), reading (docs/northstar/ambiguity_register.md :272, Westley to confirm): "the map
#   holds at the next keyframe until the entry has printed and its hold has passed; scroll and map
#   stay in step like a book with pictures" (ledger :1112).
#
# The brief's gaps 1 to 7 are not ruled; the null actions are what is pinned here:
#   (1) hold PRINT_HOLD_S = 3.0 s after an entry prints, counted in the panel's _process(delta), frozen
#       while paused, while the expansion overlay is visible (or InspectionState paused); it gates only
#       the start of the NEXT entry.
#   (2) start_printing is idempotent (unknown, printing, queued, PRINTED: ignored).
#   (3) panel qa_state gains print = {printing_id:int (-1 none), queued:[int], printed:[int], hold_left_s:float}.
#   (4) skip_all clears queue and hold first, then prints every unprinted entry as today.
#   (5) FIFO in call order.
#   (7) the sequencer's _advance_replay does not move the tick past the first keyframe not yet hit while
#       the panel is_busy() (from start_printing until entry_finished_printing plus the hold).
#
# Timing numbers: 3.0 s is R-069-03; 0.08 s and 0.20 s are CHRONICLE_PACE (panel); the only tolerance is
# TIMING_SLACK_S (0.25), the one tests/test_chronicle_scene_open.gd:46 already uses, plus the 0.05 s the
# brief gives for a frozen hold_left_s. The replay rate (2 ticks per second) is the one of
# tests/test_chronicle_scene_open.gd:42 (TICKS_PER_SECOND).
#
# Deviation from the brief, stated: MAP HOLDS puts the second keyframe at tick 4, not 40. With keyframes at 0
# and 40 the replay needs 20 s to reach 40, so "stays below 40 for 2.0 s" is true on the old tree too and
# the case could not be red for the stated reason. At tick 4 the old tree passes the keyframe at 2.0 s of
# clock, while the first entry (60 words, about 5 s) still prints.
#
# Positive controls (green on the old tree): CONTROL, DETECTOR CONTROL, MAP HOLDS CONTROL.
# Run: scripts/run_godot_tests.sh tests/test_vg_b_b26.gd  (headless; the INTEGRATION and MAP HOLDS cases
# mount the sequencer headless exactly as tests/test_chronicle_scene_open.gd does).

const PanelScene := "res://scenes/world/chronicle_scroll_panel.tscn"
const SequencerScene := "res://scenes/world/time_jump_sequencer.tscn"
const SIM_SESSION := "res://autoload/sim_session.gd"
const RecordingBridge := preload("res://tests/support/recording_bridge.gd")

const QUEUED := 0
const PRINTING := 1
const PRINTED := 2

const PRINT_HOLD_S := 3.0  # R-069-03
const TIMING_SLACK_S := 0.25  # tests/test_chronicle_scene_open.gd:46
const HOLD_LEFT_TOL_S := 0.05  # the brief's tolerance for a frozen hold_left_s
const TICKS_PER_SECOND := 2.0  # tests/test_chronicle_scene_open.gd:42
const KEYFRAME_TICK := 4  # the second keyframe of MAP HOLDS, see the deviation note
const EXISTING_QA_KEYS := ["scene", "error_panel", "tick", "plants", "hash", "timing_ms", "regen_count",
	"entries", "expanded_id", "owners", "pace", "dropped_entries", "unresolved_refs"]
const PRINT_KEYS := ["printing_id", "queued", "printed", "hold_left_s"]

var _pass_count := 0
var _fail_count := 0
var _fail_msgs: Array[String] = []
var _fin: Array = []  # entry ids in the order entry_finished_printing fired


func _initialize() -> void:
	await _run_tests()
	print("\n=== VG-B26 Chronicle Serial Results ===")
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
	# let the autoloads finish _ready before a stand-in bridge replaces the session's
	await process_frame
	await process_frame
	await _case_control()
	await _case_detector_control()
	await _case_serial()
	await _case_hold()
	await _case_order_idempotence()
	await _case_skip()
	await _case_pause()
	await _case_pause_overlay()
	await _case_inventory()
	await _case_integration()
	await _case_map_holds()
	await _case_map_holds_control()
	load(SIM_SESSION).reset()


# ---- fixtures and helpers ----------------------------------------------------

func _now() -> float:
	return Time.get_ticks_msec() / 1000.0


func _wait(seconds: float) -> void:
	var t0 := _now()
	while _now() - t0 < seconds:
		await process_frame


# n distinct words, so the text splits into n printable words
func _words_text(n: int, tag: String) -> String:
	var parts: PackedStringArray = []
	for i in range(n):
		parts.append("%s%d" % [tag, i])
	return " ".join(parts)


func _entry_def(id: int, start_tick: int, text: String) -> Dictionary:
	return {"id": id, "start_tick": start_tick, "end_tick": start_tick + 2, "category": 5, "cluster_type": 0,
		"refs": {"regions": [], "factions": []}, "fragment": -1, "fragment_ids": [-1, -1, -1],
		"significance": 1.0, "text": text, "mentions": [], "expanded_text": "", "expanded_mentions": []}


# texts[i] becomes entry id i + 1
func _panel_frame(texts: Array) -> Dictionary:
	var entries: Array = []
	for i in range(texts.size()):
		entries.append(_entry_def(i + 1, i * 10, texts[i]))
	return JSON.parse_string(JSON.stringify({
		"type": "chronicle", "jump": {"from_tick": 0, "to_tick": 50}, "entries": entries}))


func _mount_panel(texts: Array) -> Node:
	var panel: Node = (load(PanelScene) as PackedScene).instantiate()
	panel.set("hosted", true)  # loads no held frame
	get_root().add_child(panel)
	await process_frame
	await process_frame
	panel.set_snapshot({"regions": [], "factions": []})
	panel.load_frame(_panel_frame(texts))
	_fin = []
	panel.entry_finished_printing.connect(_on_fin)
	return panel


func _on_fin(entry_id: String) -> void:
	_fin.append(entry_id)


func _unmount(node: Node) -> void:
	node.queue_free()
	await process_frame
	await process_frame


func _node(panel: Node, id: int) -> Node:
	var entries: Dictionary = panel.get("_entries")
	return entries.get(str(id), null)


func _state(panel: Node, id: int) -> int:
	var n := _node(panel, id)
	return int(n.get_current_state()) if n != null else -1


# true when the entry has put at least one word on screen or is PRINTED
func _words_shown(entry: Node) -> bool:
	if entry == null:
		return false
	return int(entry.get("_words_started")) > 0 or int(entry.get_current_state()) == PRINTED


func _shown(panel: Node, id: int) -> bool:
	return _words_shown(_node(panel, id))


func _print_of(panel: Node) -> Dictionary:
	var p = panel.qa_state().get("print", null)
	return p if p is Dictionary else {}


func _hold_left(panel: Node) -> float:
	return float(_print_of(panel).get("hold_left_s", -1.0))


func _is_int_array(a) -> bool:
	if not (a is Array):
		return false
	for v in a:
		if typeof(v) != TYPE_INT:
			return false
	return true


func _states_str(panel: Node, ids: Array) -> String:
	var parts: PackedStringArray = []
	for id in ids:
		parts.append("%d:state=%d,words=%s" % [id, _state(panel, id), str(_shown(panel, id))])
	return " ".join(parts)


# ---- sequencer fixtures (as tests/test_chronicle_scene_open.gd) ---------------

func _snapshot() -> Dictionary:
	var regions := []
	for i in range(4):
		regions.append({"i": i, "owner": 0 if i < 2 else 1})
	return {"type": "snapshot", "tick": 110, "regions": regions, "factions": [{"id": 0}, {"id": 1}]}


func _seq_entry(id: int, start_tick: int, text: String) -> Dictionary:
	return {"id": id, "start_tick": start_tick, "end_tick": start_tick + 2, "category": 3, "cluster_type": 1,
		"refs": {"regions": [0], "factions": [0]}, "fragment": -1, "fragment_ids": [-1, -1, -1],
		"significance": 0.8, "text": text, "mentions": [], "expanded_text": "", "expanded_mentions": []}


func _seq_frame(entries: Array, keyframes: Array, from_tick: int, to_tick: int) -> Dictionary:
	var snaps := []
	for i in range((to_tick - from_tick) / 2 + 1):
		snaps.append([0, 0, 1, 1])
	return {
		"type": "chronicle",
		"jump": {"from_tick": from_tick, "to_tick": to_tick, "chapter_end_reason": 0},
		"entries": entries,
		"ownership": {"stride": 2, "from_tick": from_tick, "n_regions": 4, "snapshots": snaps},
		"keyframes": keyframes,
	}


func _install(frame: Dictionary, held: bool) -> Object:
	var session = load(SIM_SESSION)
	session.reset()
	var bridge = RecordingBridge.new()
	if held:
		bridge.hold_jump(frame, _snapshot())
	else:
		bridge.canned_chronicle = frame
		bridge.canned_snapshot = _snapshot()
		bridge._snapshot = _snapshot()
	session.set("_bridge", bridge)
	return bridge


func _mount_seq() -> Node:
	var node: Node = (load(SequencerScene) as PackedScene).instantiate()
	get_root().add_child(node)
	await process_frame
	await process_frame
	return node


func _replay_tick(seq: Node) -> int:
	return int(seq.qa_state().get("replay", {}).get("tick", -1))


# ---- CONTROL -------------------------------------------------------------------

func _case_control() -> void:
	var panel: Node = await _mount_panel([_words_text(2, "a"), _words_text(2, "b")])
	var entries: Dictionary = panel.get("_entries")
	_assert(entries.size() == 2, "CONTROL: load_frame of two entries yields %d entry nodes, expected 2" % entries.size())
	for id in [1, 2]:
		_assert(_state(panel, id) == QUEUED, "CONTROL: entry %d is not QUEUED after load_frame (state %d)" % [id, _state(panel, id)])
		_assert(not _shown(panel, id), "CONTROL: entry %d shows words before it is printed" % id)
	# premises, pasted into the report
	var qa: Dictionary = panel.qa_state()
	print("PREMISE panel.qa_state keys: ", qa.keys())
	print("PREMISE panel.qa_state pace: ", qa.get("pace"))
	print("PREMISE _entries keys (type): ", entries.keys(), " type=", typeof(entries.keys()[0]) if entries.size() > 0 else -1, " (TYPE_STRING=%d)" % TYPE_STRING)
	var qa_ids: Array = []
	for e in qa.get("entries", []):
		qa_ids.append(e.get("entry_id"))
	print("PREMISE qa_state.entries entry_id values: ", qa_ids, " type=", typeof(qa_ids[0]) if qa_ids.size() > 0 else -1, " (TYPE_INT=%d)" % TYPE_INT)
	print("PREMISE node states right after load_frame: ", [_state(panel, 1), _state(panel, 2)], " _words_started: ", [_node(panel, 1).get("_words_started"), _node(panel, 2).get("_words_started")])
	print("PREMISE panel _printing_id=", var_to_str(panel.get("_printing_id")), " _finished_count=", panel.get("_finished_count"))
	_assert(float(qa.get("pace", {}).get("word_interval_s", 0.0)) == 0.08 and float(qa.get("pace", {}).get("fade_s", 0.0)) == 0.20,
		"CONTROL: CHRONICLE_PACE is %s, expected word_interval_s 0.08 and fade_s 0.20" % str(qa.get("pace")))
	await _unmount(panel)


# ---- DETECTOR CONTROL ----------------------------------------------------------

func _case_detector_control() -> void:
	var panel: Node = await _mount_panel([_words_text(30, "a"), _words_text(30, "b")])
	panel.start_printing("1")
	await _wait(0.3)
	_assert(_shown(panel, 1), "DETECTOR CONTROL: entry 1 shows no words 0.3 s after start_printing (%s)" % _states_str(panel, [1]))
	_assert(not _shown(panel, 2), "DETECTOR CONTROL: entry 2 was never started yet shows words (%s)" % _states_str(panel, [2]))
	await _unmount(panel)


# ---- SERIAL (RED today) --------------------------------------------------------

func _case_serial() -> void:
	var panel: Node = await _mount_panel([_words_text(40, "a"), _words_text(2, "b")])
	panel.start_printing("1")
	panel.start_printing("2")
	await _wait(0.15)  # one word interval (0.08 s) plus a frame
	_assert(_shown(panel, 1), "SERIAL: entry A (id 1) shows no words 0.15 s after it was enqueued (%s)" % _states_str(panel, [1, 2]))
	_assert(not _shown(panel, 2),
		"SERIAL: entry B (id 2) shows words while entry A is still printing; two entries print at once (%s)" % _states_str(panel, [1, 2]))
	_assert(_state(panel, 2) == QUEUED,
		"SERIAL: entry B (id 2) is not QUEUED while A prints (state %d, expected %d)" % [_state(panel, 2), QUEUED])
	await _unmount(panel)


# ---- HOLD (RED today) ----------------------------------------------------------

func _case_hold() -> void:
	var panel: Node = await _mount_panel([_words_text(2, "a"), _words_text(2, "b")])
	panel.start_printing("1")
	panel.start_printing("2")
	var t0 := _now()
	var t_a := -1.0
	var t_b := -1.0
	var b_state_at_25 := -1
	var b_checked := false
	while _now() - t0 < 9.0:
		await process_frame
		var t := _now()
		if t_a < 0.0 and _state(panel, 1) == PRINTED:
			t_a = t
		if t_b < 0.0 and _state(panel, 2) != QUEUED:
			t_b = t
		if t_a >= 0.0 and not b_checked and t - t_a >= PRINT_HOLD_S - 0.5:
			b_checked = true
			b_state_at_25 = _state(panel, 2)
		if b_checked and t_b >= 0.0:
			break
		if t_a >= 0.0 and t - t_a > PRINT_HOLD_S + TIMING_SLACK_S + 0.5:
			break
	var times := "A PRINTED at %.2f s, B left QUEUED at %.2f s (wall, from enqueue)" % [t_a - t0, t_b - t0 if t_b >= 0.0 else -1.0]
	_assert(t_a >= 0.0, "HOLD: entry A never reached PRINTED within 9 s (%s)" % times)
	_assert(b_state_at_25 == QUEUED,
		"HOLD: B was not still QUEUED 2.5 s after A printed (state %d); the hold is 3.0 s (%s)" % [b_state_at_25, times])
	_assert(t_b >= 0.0 and t_a >= 0.0 and t_b - t_a <= PRINT_HOLD_S + TIMING_SLACK_S,
		"HOLD: B did not start within 3.0 s + 0.25 s of A printing (%s)" % times)
	await _unmount(panel)


# ---- ORDER and IDEMPOTENCE ------------------------------------------------------

func _case_order_idempotence() -> void:
	var panel: Node = await _mount_panel([_words_text(2, "a"), _words_text(2, "b"), _words_text(2, "c")])
	panel.start_printing("1")
	panel.start_printing("2")
	panel.start_printing("3")
	panel.start_printing("1")  # again, while printing: ignored
	var shown_order: Array = []
	var prev_printed_when_started: Dictionary = {}  # id -> was the entry before it PRINTED when it first showed words
	var t0 := _now()
	while _now() - t0 < 14.0 and _fin.size() < 3:
		await process_frame
		for id in [1, 2, 3]:
			if not shown_order.has(id) and _shown(panel, id):
				shown_order.append(id)
				prev_printed_when_started[id] = id == 1 or _state(panel, id - 1) == PRINTED
	await _wait(0.6)  # a restarted entry would fire entry_finished_printing again
	_assert(shown_order == [1, 2, 3], "ORDER: entries first showed words in order %s, expected [1, 2, 3]" % str(shown_order))
	for id in [2, 3]:
		_assert(prev_printed_when_started.get(id, false),
			"ORDER: entry %d started printing before entry %d was PRINTED; entries must print one after another (%s)" % [id, id - 1, _states_str(panel, [1, 2, 3])])
	_assert(_fin == ["1", "2", "3"], "ORDER: entry_finished_printing fired %s, expected [\"1\", \"2\", \"3\"] (A enqueued again, printed once)" % str(_fin))
	var printed_n := 0
	for id in [1, 2, 3]:
		if _state(panel, id) == PRINTED:
			printed_n += 1
	_assert(printed_n == 3, "ORDER: %d entries PRINTED, expected 3 (%s)" % [printed_n, _states_str(panel, [1, 2, 3])])
	_assert(int(panel.get("_finished_count")) == 3, "IDEMPOTENCE: _finished_count is %s, expected 3" % str(panel.get("_finished_count")))
	# a PRINTED entry and an unknown id are ignored
	panel.start_printing("1")
	panel.start_printing("99")
	await _wait(0.5)
	_assert(_state(panel, 1) == PRINTED, "IDEMPOTENCE: start_printing on a PRINTED entry restarted it (state %d)" % _state(panel, 1))
	_assert(_fin.size() == 3 and int(panel.get("_finished_count")) == 3,
		"IDEMPOTENCE: start_printing on a PRINTED or unknown entry changed finished count (fired %s, _finished_count %s)" % [str(_fin), str(panel.get("_finished_count"))])
	await _unmount(panel)


# ---- SKIP -----------------------------------------------------------------------

func _case_skip() -> void:
	var panel: Node = await _mount_panel([_words_text(40, "a"), _words_text(2, "b"), _words_text(2, "c")])
	panel.start_printing("1")
	panel.start_printing("2")
	panel.start_printing("3")
	await _wait(0.2)
	_assert(_state(panel, 1) == PRINTING, "SKIP: entry A is not PRINTING before skip_all (state %d)" % _state(panel, 1))
	_fin = []
	panel.skip_all()
	await process_frame
	for id in [1, 2, 3]:
		_assert(_state(panel, id) == PRINTED, "SKIP: entry %d is not PRINTED right after skip_all (state %d)" % [id, _state(panel, id)])
	var pr := _print_of(panel)
	_assert(pr.has("queued") and pr.get("queued") == [],
		"SKIP: print.queued is %s after skip_all, expected [] (print key present: %s)" % [str(pr.get("queued", "<missing>")), str(pr.has("queued"))])
	await _wait(0.5)
	var printing_n := 0
	for id in [1, 2, 3]:
		if _state(panel, id) == PRINTING:
			printing_n += 1
	_assert(printing_n == 0, "SKIP: %d entries are PRINTING 0.5 s after skip_all (%s)" % [printing_n, _states_str(panel, [1, 2, 3])])
	var counts := {}
	for id in _fin:
		counts[id] = int(counts.get(id, 0)) + 1
	_assert(_fin.size() == 3 and counts.get("1", 0) == 1 and counts.get("2", 0) == 1 and counts.get("3", 0) == 1,
		"SKIP: entry_finished_printing fired %s after skip_all, expected once per entry" % str(_fin))
	await _unmount(panel)


# ---- PAUSE ----------------------------------------------------------------------

func _case_pause() -> void:
	var panel: Node = await _mount_panel([_words_text(2, "a"), _words_text(2, "b")])
	panel.start_printing("1")
	panel.start_printing("2")
	var t0 := _now()
	while _now() - t0 < 5.0 and _state(panel, 1) != PRINTED:
		await process_frame
	_assert(_state(panel, 1) == PRINTED, "PAUSE: entry A never reached PRINTED within 5 s")
	panel.pause()
	var h0 := _hold_left(panel)
	_assert(h0 > 0.0 and h0 <= PRINT_HOLD_S,
		"PAUSE: print.hold_left_s is %.3f right after A printed and the panel paused, expected within (0, 3.0] (print dict: %s)" % [h0, str(_print_of(panel))])
	await _wait(1.5)
	var h1 := _hold_left(panel)
	_assert(_state(panel, 2) == QUEUED, "PAUSE: B left QUEUED while the panel was paused (state %d)" % _state(panel, 2))
	_assert(absf(h1 - h0) <= HOLD_LEFT_TOL_S,
		"PAUSE: hold_left_s moved from %.3f to %.3f while paused for 1.5 s, expected unchanged to %.2f" % [h0, h1, HOLD_LEFT_TOL_S])
	panel.resume()
	var t_r := _now()
	while _now() - t_r < PRINT_HOLD_S + 2.0 and _state(panel, 2) == QUEUED:
		await process_frame
	var dt := _now() - t_r
	_assert(_state(panel, 2) != QUEUED, "PAUSE: B never started after resume() (waited %.2f s)" % dt)
	_assert(dt >= h0 - HOLD_LEFT_TOL_S and dt <= h0 + TIMING_SLACK_S,
		"PAUSE: B started %.2f s after resume(), expected the remaining hold %.2f s (-0.05 / +0.25)" % [dt, h0])
	await _unmount(panel)


# The expansion overlay being visible freezes the hold (gap 1). Only the overlay-visible ingredient is
# driven (the flag the panel owns); the InspectionState path also calls pause() and is the PAUSE case
# above, so it is covered by reading only.
func _case_pause_overlay() -> void:
	var panel: Node = await _mount_panel([_words_text(2, "a"), _words_text(2, "b")])
	panel.start_printing("1")
	panel.start_printing("2")
	var t0 := _now()
	while _now() - t0 < 5.0 and _state(panel, 1) != PRINTED:
		await process_frame
	var overlay: Control = panel.get("_expansion_overlay")
	overlay.visible = true
	var h0 := _hold_left(panel)
	await _wait(1.0)
	var h1 := _hold_left(panel)
	overlay.visible = false
	_assert(h0 > 0.0, "PAUSE OVERLAY: print.hold_left_s is %.3f when A has printed, expected > 0 (print dict: %s)" % [h0, str(_print_of(panel))])
	_assert(absf(h1 - h0) <= HOLD_LEFT_TOL_S,
		"PAUSE OVERLAY: hold_left_s moved from %.3f to %.3f with the expansion overlay visible for 1.0 s, expected unchanged to %.2f" % [h0, h1, HOLD_LEFT_TOL_S])
	_assert(_state(panel, 2) == QUEUED, "PAUSE OVERLAY: B left QUEUED while the overlay was visible (state %d)" % _state(panel, 2))
	await _unmount(panel)


# ---- INVENTORY (qa_state print) ----------------------------------------------------

func _case_inventory() -> void:
	var panel: Node = await _mount_panel([_words_text(20, "a"), _words_text(2, "b")])
	var qa: Dictionary = panel.qa_state()
	for k in EXISTING_QA_KEYS:
		_assert(qa.has(k), "INVENTORY: the existing qa_state key '%s' is gone (keys %s)" % [k, str(qa.keys())])
	panel.start_printing("1")
	panel.start_printing("2")
	await _wait(0.15)
	var pr := _print_of(panel)
	_assert(pr is Dictionary and not pr.is_empty(), "INVENTORY: qa_state has no print dict (qa_state keys %s)" % str(panel.qa_state().keys()))
	for k in PRINT_KEYS:
		_assert(pr.has(k), "INVENTORY: print.%s is missing (print dict: %s)" % [k, str(pr)])
	_assert(typeof(pr.get("printing_id")) == TYPE_INT and int(pr.get("printing_id", -2)) == 1,
		"INVENTORY: while A prints, print.printing_id is %s, expected int 1" % str(pr.get("printing_id", "<missing>")))
	_assert(_is_int_array(pr.get("queued")) and pr.get("queued") == [2],
		"INVENTORY: while A prints and B waits, print.queued is %s, expected [2] (ints)" % str(pr.get("queued", "<missing>")))
	_assert(_is_int_array(pr.get("printed")) and pr.get("printed") == [],
		"INVENTORY: while A prints, print.printed is %s, expected []" % str(pr.get("printed", "<missing>")))
	_assert(typeof(pr.get("hold_left_s")) == TYPE_FLOAT and float(pr.get("hold_left_s", -1.0)) == 0.0,
		"INVENTORY: while A prints, print.hold_left_s is %s, expected 0.0" % str(pr.get("hold_left_s", "<missing>")))
	var t0 := _now()
	while _now() - t0 < 6.0 and _state(panel, 1) != PRINTED:
		await process_frame
	pr = _print_of(panel)
	_assert(int(pr.get("printing_id", -2)) == -1,
		"INVENTORY: after A finished (during the hold), print.printing_id is %s, expected -1" % str(pr.get("printing_id", "<missing>")))
	_assert(pr.get("queued") == [2], "INVENTORY: during the hold, print.queued is %s, expected [2]" % str(pr.get("queued", "<missing>")))
	_assert(pr.get("printed") == [1], "INVENTORY: during the hold, print.printed is %s, expected [1]" % str(pr.get("printed", "<missing>")))
	var h := float(pr.get("hold_left_s", -1.0))
	_assert(h > 0.0 and h <= PRINT_HOLD_S, "INVENTORY: during the hold, print.hold_left_s is %.3f, expected within (0, 3.0]" % h)
	t0 = _now()
	while _now() - t0 < PRINT_HOLD_S + 4.0 and _state(panel, 2) != PRINTED:
		await process_frame
	pr = _print_of(panel)
	_assert(pr.get("printed") == [1, 2], "INVENTORY: after all done, print.printed is %s, expected [1, 2] in that order" % str(pr.get("printed", "<missing>")))
	_assert(pr.get("queued") == [] and int(pr.get("printing_id", -2)) == -1,
		"INVENTORY: after all done, print.queued is %s and printing_id %s, expected [] and -1" % [str(pr.get("queued", "<missing>")), str(pr.get("printing_id", "<missing>"))])
	await _unmount(panel)


# ---- INTEGRATION (sequencer) --------------------------------------------------------

func _case_integration() -> void:
	# two entries whose start ticks (100, 101) are both reached 1.0 s into a 10-tick replay; no keyframes, so
	# only the serial feeder is under test here
	var frame := _seq_frame([_seq_entry(1, 100, _words_text(40, "a")), _seq_entry(2, 101, _words_text(2, "b"))], [], 100, 110)
	_install(frame, true)
	var seq: Node = await _mount_seq()
	var t_mount := _now()
	var panel: Node = seq.get("_scroll")
	_assert(panel != null and panel.qa_state().get("entries", []).size() == 2, "INTEGRATION: the panel does not show the held frame's two entries")
	await _wait(maxf(0.0, 1.0 - (_now() - t_mount)))
	var replay: Dictionary = seq.qa_state().get("replay", {})
	var tick := int(replay.get("tick", -1))
	print("PREMISE integration at 1.0 s: replay tick=", tick, " entries_started=", replay.get("entries_started"), " ", _states_str(panel, [1, 2]))
	_assert(replay.get("entries_started", []) == [1, 2],
		"INTEGRATION: replay.entries_started is %s at 1.0 s (tick %d), expected [1, 2]: both ticks are reached" % [str(replay.get("entries_started")), tick])
	var shown_n := 0
	for id in [1, 2]:
		if _shown(panel, id):
			shown_n += 1
	_assert(shown_n == 1 and _shown(panel, 1) and not _shown(panel, 2),
		"INTEGRATION: through the real feeder %d of the two entries show words 1.0 s in (%s), expected only entry 1; the sequencer starts both" % [shown_n, _states_str(panel, [1, 2])])
	_assert(_state(panel, 2) == QUEUED, "INTEGRATION: entry 2 is not QUEUED while entry 1 prints (state %d)" % _state(panel, 2))
	await _unmount(seq)
	load(SIM_SESSION).reset()


# ---- MAP HOLDS (sequencer, Q-069-03 (a)) ---------------------------------------------

# 20-tick replay (10 s). Keyframes at 0 and KEYFRAME_TICK. Entry 1 (start 0) has 60 words, about 5 s of
# printing; entry 2 starts at KEYFRAME_TICK.
func _map_frame() -> Dictionary:
	return _seq_frame([_seq_entry(1, 0, _words_text(60, "a")), _seq_entry(2, KEYFRAME_TICK, _words_text(2, "b"))],
		[0, KEYFRAME_TICK], 0, 20)


func _case_map_holds() -> void:
	_install(_map_frame(), true)
	var seq: Node = await _mount_seq()
	var panel: Node = seq.get("_scroll")
	var t0 := _now()
	var t_a := -1.0
	var max_tick_while_printing := -1
	var max_tick_during_hold := -1
	var b_state_late := -1
	var late_checked := false
	var release_t := -1.0
	var release_tick := -1
	while _now() - t0 < 14.0:
		await process_frame
		var t := _now()
		var tick := _replay_tick(seq)
		if t_a < 0.0:
			if _state(panel, 1) == PRINTED:
				t_a = t
			else:
				max_tick_while_printing = maxi(max_tick_while_printing, tick)
		else:
			if t - t_a < PRINT_HOLD_S - 0.5:
				max_tick_during_hold = maxi(max_tick_during_hold, tick)
			elif not late_checked:
				late_checked = true
				b_state_late = _state(panel, 2)
			if release_t < 0.0 and tick > KEYFRAME_TICK and _state(panel, 2) != QUEUED:
				release_t = t
				release_tick = tick
			if late_checked and release_t >= 0.0:
				break
			if t - t_a > PRINT_HOLD_S + TIMING_SLACK_S + 1.0 / TICKS_PER_SECOND:
				break
	var printing_s := (t_a - t0) if t_a >= 0.0 else -1.0
	print("PREMISE map holds: A PRINTED at %.2f s; max tick while A printing %d; max tick in first 2.5 s of the hold %d; release at %.2f s tick %d" % [printing_s, max_tick_while_printing, max_tick_during_hold, release_t - t0 if release_t >= 0.0 else -1.0, release_tick])
	_assert(t_a >= 0.0 and printing_s >= 2.0, "MAP HOLDS: entry 1 printed for %.2f s, the case needs at least 2.0 s of clock while it prints" % printing_s)
	_assert(max_tick_while_printing <= KEYFRAME_TICK,
		"MAP HOLDS: the replay tick reached %d while entry 1 was still printing (%.2f s in), past the next keyframe at tick %d; the map must hold there (Q-069-03 (a))" % [max_tick_while_printing, printing_s, KEYFRAME_TICK])
	_assert(max_tick_during_hold <= KEYFRAME_TICK,
		"MAP HOLDS: the replay tick reached %d during the 3.0 s hold after entry 1 printed, past the keyframe at tick %d" % [max_tick_during_hold, KEYFRAME_TICK])
	_assert(late_checked and b_state_late == QUEUED,
		"MAP HOLDS: entry 2 was not still QUEUED 2.5 s into the hold (state %d, -1 = the hold never lasted that long); it left QUEUED at %.2f s after entry 1 printed" % [b_state_late, release_t - t_a if release_t >= 0.0 else -1.0])
	_assert(release_t >= 0.0,
		"MAP HOLDS: after entry 1 printed and its hold passed (3.0 s + 0.25 s + one tick), the tick did not pass %d with entry 2 started (tick now %d, entry 2 state %d)" % [KEYFRAME_TICK, _replay_tick(seq), _state(panel, 2)])
	await _unmount(seq)
	load(SIM_SESSION).reset()


# Control: the same frame on a panel whose is_busy() is false lets the tick pass the keyframe while entry 1
# prints. Green on both trees: the old sequencer never asks the panel, the new one asks and gets false.
func _case_map_holds_control() -> void:
	_install(_map_frame(), false)
	var seq: Node = await _mount_seq()
	var stub_script := GDScript.new()
	stub_script.source_code = "extends \"res://scenes/world/chronicle_scroll_panel.gd\"\n\nfunc is_busy() -> bool:\n\treturn false\n"
	var err := stub_script.reload()
	_assert(err == OK, "MAP HOLDS CONTROL: the stub panel script did not compile (error %d)" % err)
	var stub: Node = stub_script.new()
	stub.set("hosted", true)
	seq.add_child(stub)
	var old: Node = seq.get("_scroll")
	seq.set("_scroll", stub)
	old.queue_free()
	await process_frame
	stub.set_snapshot(_snapshot())
	stub.load_frame(_map_frame())
	seq.load_frame(_map_frame(), [1, 1, 1, 1])
	var t0 := _now()
	var tick := -1
	while _now() - t0 < 7.0:
		await process_frame
		tick = _replay_tick(seq)
		if tick > KEYFRAME_TICK:
			break
	var a_state := _state(stub, 1)
	_assert(tick > KEYFRAME_TICK and a_state == PRINTING,
		"MAP HOLDS CONTROL: with is_busy() false the tick is %d after %.2f s and entry 1 state %d, expected the tick past %d while entry 1 is PRINTING" % [tick, _now() - t0, a_state, KEYFRAME_TICK])
	await _unmount(seq)
	load(SIM_SESSION).reset()
