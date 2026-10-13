extends SceneTree
# test-timeout: 10000

# VG-B26-chronicle-serial: the chronicle scroll prints one entry at a time.
# TESTS FIRST: written against the built tree (scenes/world/chronicle_scroll_panel.gd
# start_printing starts an entry at once, no queue); the red cases name the rule.
#
# Rules proved (docs/bible/epics/E-09-chronicle.md:98 and :99, quoted word for word):
#
# R-069-03  "Given the map animation is the master clock, When an entry's tick range is
#   reached and no other entry is printing, Then that entry begins printing; entries print
#   one after another, never two at once, so the scroll reads like a book (Westley,
#   2026-10-13, on the S-108 frame: "in the python version they were printed out one at a
#   time so the user would read it like a book"); an entry whose tick is reached while
#   another prints waits its turn; a printed entry holds for at least 3.0 s. Whether the
#   map holds at that entry's keyframe until it has printed is open (Q-069-03)."
# R-069-04  "Given an entry is printing, When the player clicks it, Then nothing happens;
#   Given it is printed (blinking cursor shown), When clicked, Then the expanded form
#   overlays the scroll and the map, clock, and any printing entry pause; dismissing
#   resumes from the exact word and frame."
# Q-069-03 default (b) (docs/northstar/ambiguity_register.md): the map runs on at 2 ticks
#   per second and the scroll catches up (the clock-level entries_started list is unchanged).
#
# Gaps not ruled, null actions taken (none blocking), each named at the case that uses it:
#   GAP 1  PRINT_HOLD_S := 3.0 in the panel; a _process(delta) countdown frozen while
#          paused, the expansion overlay is visible or InspectionState is paused; it gates
#          only the start of the NEXT entry; the sequencer settle hold is unchanged.
#   GAP 2  start_printing is idempotent (unknown, printing, queued, PRINTED: ignored);
#          begin_time_jump and load_frame clear queue, hold and printing id.
#   GAP 3  panel qa_state gains print = {printing_id: int (-1 none), queued: [int],
#          printed: [int], hold_left_s: float}; nothing else changes.
#   GAP 4  skip_all clears queue, hold and printing id first, then prints every
#          unprinted entry as today.
#   GAP 5  FIFO in call order.
#   GAP 6  S-108 play unchanged (not tested here).
#   GAP 7  the sequencer is not edited (INTEGRATION below drives the unedited sequencer).
#
# Thresholds: only the rule's 3.0 s (PRINT_HOLD_S below), CHRONICLE_PACE's 0.08 s word
# interval and 0.20 s fade (scenes/world/chronicle_scroll_panel.gd:30-33), and the
# neighbour's TIMING_SLACK_S (tests/test_chronicle_scene_open.gd:46, 0.25) appear. The
# 0.15 s SERIAL wait is "one word interval plus a frame" (0.08 s interval, jitter to
# 0.118 s, floor 0.032 s: chronicle_entry.gd _schedule_next_tick).
#
# Controls (GREEN today): CONTROL (two entry nodes, both QUEUED, no words), DETECTOR
# CONTROL (start_printing on one entry shows words, so the words-shown helper can see).
# RED today: SERIAL, HOLD, ORDER, PAUSE, INVENTORY, INTEGRATION (SKIP only on the missing
# print key); the old panel starts every entry the moment it is called.
#
# Run: timeout 1800 scripts/run_godot_tests.sh tests/test_vg_b_b26.gd   (headless-safe;
# the INTEGRATION case mounts the sequencer headless the same way
# tests/test_chronicle_scene_open.gd does, in the same run).

const PanelScene := "res://scenes/world/chronicle_scroll_panel.tscn"
const SequencerScene := "res://scenes/world/time_jump_sequencer.tscn"
const SIM_SESSION := "res://autoload/sim_session.gd"
const RecordingBridge := preload("res://tests/support/recording_bridge.gd")
const PRINT_HOLD_S := 3.0  # R-069-03: "a printed entry holds for at least 3.0 s"
const TIMING_SLACK_S := 0.25  # tests/test_chronicle_scene_open.gd:46 (cited, not new)
const QUEUED := 0
const PRINTING := 1
const PRINTED := 2
const OLD_QA_KEYS := ["scene", "error_panel", "tick", "plants", "hash", "timing_ms",
	"regen_count", "entries", "expanded_id", "owners", "pace", "dropped_entries",
	"unresolved_refs"]
const SIX := "one two three four five six"

var _pass_count := 0
var _fail_count := 0
var _fail_msgs: Array[String] = []


func _initialize() -> void:
	await process_frame
	await process_frame
	await _run_tests()
	print("\n=== VG-B26 Chronicle Serial Results ===")
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
	await _control()
	await _detector_control()
	await _serial()
	await _hold()
	await _order_and_idempotence()
	await _skip()
	await _pause()
	await _pause_by_expansion()
	await _inventory()
	await _integration()
	load(SIM_SESSION).reset()


# ---- helpers ---------------------------------------------------------------------------

func _entry(id: int, s: int, e: int, text: String) -> Dictionary:
	return {"id": id, "start_tick": s, "end_tick": e, "category": 3, "cluster_type": 1,
		"refs": {"regions": [], "factions": []}, "fragment": -1, "fragment_ids": [-1, -1, -1],
		"significance": 0.8, "text": text, "mentions": [], "expanded_text": text + " More.",
		"expanded_mentions": []}


# Entries 1..n in the shape of tests/test_chronicle_mentions.gd _synthetic_frame; the numbers
# go through JSON text so ints arrive as floats, as the bridge delivers them.
func _frame(texts: Array) -> Dictionary:
	var entries: Array = []
	for i in range(texts.size()):
		entries.append(_entry(i + 1, 1 + i * 10, 9 + i * 10, str(texts[i])))
	var frame := {"type": "chronicle", "jump": {"from_tick": 0, "to_tick": 50}, "entries": entries}
	return JSON.parse_string(JSON.stringify(frame))


# A hosted panel (loads no held frame) filled with the given entry texts.
func _panel(texts: Array) -> Node:
	var panel: Node = (load(PanelScene) as PackedScene).instantiate()
	panel.set("hosted", true)
	get_root().add_child(panel)
	await process_frame
	await process_frame
	panel.set_snapshot({"regions": [], "factions": []})
	panel.load_frame(_frame(texts))
	await process_frame
	return panel


func _unmount(node: Node) -> void:
	node.queue_free()
	await process_frame
	await process_frame


func _node(panel: Node, id: int) -> Node:
	return (panel.get("_entries") as Dictionary).get(str(id), null)


func _state(panel: Node, id: int) -> int:
	var n := _node(panel, id)
	return int(n.get_current_state()) if n != null else -1


func _state_name(s: int) -> String:
	return ["QUEUED", "PRINTING", "PRINTED"][s] if s >= 0 and s <= 2 else "none(%d)" % s


# True when the entry has shown a word or is PRINTED (the detector the neighbours' private
# pattern allows: chronicle_entry.gd _words_started, get_current_state).
func _words_shown(entry: Node) -> bool:
	return entry != null and (int(entry.get("_words_started")) > 0 or int(entry.get_current_state()) == PRINTED)


func _shown(panel: Node, id: int) -> bool:
	return _words_shown(_node(panel, id))


func _wait(seconds: float) -> void:
	var t0 := Time.get_ticks_msec()
	while (Time.get_ticks_msec() - t0) / 1000.0 < seconds:
		await process_frame


# Waits until the entry is PRINTED; returns the seconds waited, -1.0 on timeout.
func _wait_printed(panel: Node, id: int, limit_s: float) -> float:
	var t0 := Time.get_ticks_msec()
	while true:
		var el := (Time.get_ticks_msec() - t0) / 1000.0
		if _state(panel, id) == PRINTED:
			return el
		if el > limit_s:
			return -1.0
		await process_frame
	return -1.0


func _print_of(panel: Node) -> Dictionary:
	var p = panel.qa_state().get("print", null)
	return p if p is Dictionary else {}


func _int_list(v) -> Array:
	var out: Array = []
	if v is Array:
		for x in v:
			out.append(x if typeof(x) == TYPE_INT else str(x))
	return out


func _hold_left(panel: Node) -> float:
	return float(_print_of(panel).get("hold_left_s", -1.0))


# ---- CONTROL (green today) -------------------------------------------------------------

func _control() -> void:
	var panel := await _panel(["First entry text.", "Second entry text."])
	_assert(panel != null and panel.has_method("start_printing") and panel.has_method("qa_state"),
		"CONTROL: the chronicle scroll panel scene does not instantiate with start_printing/qa_state")
	var entries: Dictionary = panel.get("_entries")
	_assert(entries.size() == 2, "CONTROL: load_frame of two entries yields %d entry nodes, expected 2" % entries.size())
	for id in [1, 2]:
		_assert(_state(panel, id) == QUEUED,
			"CONTROL: entry %d is %s right after load_frame, expected QUEUED" % [id, _state_name(_state(panel, id))])
		_assert(not _shown(panel, id), "CONTROL: entry %d shows words right after load_frame, expected none" % id)
	await _unmount(panel)


# ---- DETECTOR CONTROL (green today) ----------------------------------------------------

func _detector_control() -> void:
	var panel := await _panel([SIX, SIX])
	panel.start_printing("1")
	await _wait(0.3)
	_assert(_shown(panel, 1),
		"DETECTOR CONTROL: start_printing on entry 1 and 0.3 s later no words shown (state %s): the words-shown helper cannot see words" % _state_name(_state(panel, 1)))
	_assert(not _shown(panel, 2), "DETECTOR CONTROL: entry 2 was never started and shows words")
	await _unmount(panel)


# ---- SERIAL (R-069-03: never two at once; GAP 5 FIFO) ----------------------------------

func _serial() -> void:
	var panel := await _panel([SIX, SIX])
	panel.start_printing("1")
	panel.start_printing("2")
	await _wait(0.15)
	_assert(_shown(panel, 1),
		"SERIAL: entry A (id 1, started first) shows no words after 0.15 s (state %s)" % _state_name(_state(panel, 1)))
	_assert(not _shown(panel, 2) and _state(panel, 2) == QUEUED,
		"SERIAL R-069-03 (entries print one after another, never two at once): after enqueuing A then B and 0.15 s, B is %s with words shown = %s; expected B QUEUED with no words while A prints" % [_state_name(_state(panel, 2)), str(_shown(panel, 2))])
	await _unmount(panel)


# ---- HOLD (R-069-03: a printed entry holds for at least 3.0 s; GAP 1) ------------------

func _hold() -> void:
	var panel := await _panel(["Short entry", "Second entry text here."])
	panel.start_printing("1")
	panel.start_printing("2")
	var t_printed := await _wait_printed(panel, 1, 4.0)
	_assert(t_printed >= 0.0, "HOLD: entry A (2 words) did not reach PRINTED within 4 s")
	var t0 := Time.get_ticks_msec()
	var queued_at_2_5 := true
	var b_state_at_2_5 := QUEUED
	var t_b_start := -1.0
	var at_2_5_done := false
	while true:
		var el := (Time.get_ticks_msec() - t0) / 1000.0
		if not at_2_5_done and el >= 2.5:
			at_2_5_done = true
			b_state_at_2_5 = _state(panel, 2)
			queued_at_2_5 = b_state_at_2_5 == QUEUED
		if _shown(panel, 2) and t_b_start < 0.0:
			t_b_start = el
		if (at_2_5_done and t_b_start >= 0.0) or el > PRINT_HOLD_S + TIMING_SLACK_S + 0.5:
			break
		await process_frame
	var times := "A PRINTED at %.2f s after entry start; B first showed words %s s after A printed" % [t_printed, ("%.2f" % t_b_start) if t_b_start >= 0.0 else "never"]
	_assert(queued_at_2_5,
		"HOLD R-069-03 (a printed entry holds for at least 3.0 s): 2.5 s after A printed, B is %s, expected QUEUED (%s)" % [_state_name(b_state_at_2_5), times])
	_assert(t_b_start >= 0.0 and t_b_start <= PRINT_HOLD_S + TIMING_SLACK_S,
		"HOLD: B must be PRINTING or PRINTED by %.2f s after A printed (hold %.1f s + slack %.2f s); %s" % [PRINT_HOLD_S + TIMING_SLACK_S, PRINT_HOLD_S, TIMING_SLACK_S, times])
	await _unmount(panel)


# ---- ORDER and IDEMPOTENCE (GAP 2, GAP 5) ----------------------------------------------

func _order_and_idempotence() -> void:
	var panel := await _panel(["Alpha one two", "Bravo one two", "Charlie one two"])
	var finished: Array = []
	panel.entry_finished_printing.connect(func(id: String): finished.append(id))
	panel.start_printing("1")
	panel.start_printing("2")
	panel.start_printing("3")
	panel.start_printing("1")  # GAP 2: a repeat of a known entry is ignored
	var first_printing: Array = []
	var max_printing := 0
	var max_printed := 0
	var t0 := Time.get_ticks_msec()
	var done_at := -1.0
	while true:
		var el := (Time.get_ticks_msec() - t0) / 1000.0
		var n_printing := 0
		var n_printed := 0
		for id in [1, 2, 3]:
			var s := _state(panel, id)
			if s == PRINTING:
				n_printing += 1
				if not first_printing.has(id):
					first_printing.append(id)
			elif s == PRINTED:
				n_printed += 1
		max_printing = maxi(max_printing, n_printing)
		max_printed = maxi(max_printed, n_printed)
		if finished.size() >= 3 and done_at < 0.0:
			done_at = el
		if (done_at >= 0.0 and el >= done_at + 0.5) or el > 16.0:
			break
		await process_frame
	_assert(max_printing <= 1,
		"ORDER R-069-03 (never two at once): up to %d entries were PRINTING at the same time after enqueuing A, B, C and A again; expected at most 1" % max_printing)
	_assert(first_printing == [1, 2, 3],
		"ORDER GAP 5 (FIFO in call order): entries began printing in order %s, expected [1, 2, 3]" % str(first_printing))
	_assert(finished == ["1", "2", "3"],
		"ORDER GAP 2 (repeat of A ignored): entry_finished_printing fired in order %s, expected [1, 2, 3] with A once" % str(finished))
	_assert(max_printed <= 3, "ORDER: %d entries PRINTED at once with only 3 entries" % max_printed)
	_assert(int(panel.get("_finished_count")) == 3,
		"ORDER GAP 2: finished_count is %d after A, B, C, A, expected 3 (A printed once)" % int(panel.get("_finished_count")))
	await _unmount(panel)


# ---- SKIP (GAP 4) ----------------------------------------------------------------------

func _skip() -> void:
	var panel := await _panel([SIX, SIX, SIX])
	var fired: Dictionary = {}
	panel.entry_finished_printing.connect(func(id: String): fired[id] = int(fired.get(id, 0)) + 1)
	panel.start_printing("1")
	panel.start_printing("2")
	panel.start_printing("3")
	await _wait(0.1)
	panel.skip_all()
	await process_frame
	for id in [1, 2, 3]:
		_assert(_state(panel, id) == PRINTED,
			"SKIP GAP 4: right after skip_all entry %d is %s, expected PRINTED" % [id, _state_name(_state(panel, id))])
	var p := _print_of(panel)
	_assert(p.has("queued") and _int_list(p.get("queued")).is_empty() and int(p.get("printing_id", 99)) == -1,
		"SKIP GAP 4: after skip_all the print queue must be empty and printing_id -1, got print = %s (the print key is missing on the old panel: GAP 3)" % str(p))
	await _wait(0.5)
	for id in [1, 2, 3]:
		_assert(_state(panel, id) != PRINTING, "SKIP GAP 4: entry %d is PRINTING 0.5 s after skip_all" % id)
		_assert(int(fired.get(str(id), 0)) == 1,
			"SKIP GAP 4: entry_finished_printing fired %d times for entry %d, expected exactly once" % [int(fired.get(str(id), 0)), id])
	await _unmount(panel)


# ---- PAUSE (GAP 1; R-069-04 "any printing entry pause") --------------------------------

func _pause() -> void:
	var panel := await _panel(["Brief", "Second entry text here."])
	panel.start_printing("1")
	panel.start_printing("2")
	var t_printed := await _wait_printed(panel, 1, 4.0)
	_assert(t_printed >= 0.0, "PAUSE: entry A (1 word) did not reach PRINTED within 4 s")
	await _wait(0.2)
	panel.pause()
	var h0 := _hold_left(panel)
	await _wait(1.5)
	_assert(_state(panel, 2) == QUEUED,
		"PAUSE GAP 1: with A PRINTED and the hold running, 1.5 s after pause() B is %s, expected QUEUED (the old panel starts B at once)" % _state_name(_state(panel, 2)))
	var h1 := _hold_left(panel)
	_assert(h0 > 0.0 and absf(h1 - h0) <= 0.05,
		"PAUSE GAP 1: print.hold_left_s moved from %.3f to %.3f over 1.5 s of pause (expected unchanged to 0.05; -1 means the print key is missing)" % [h0, h1])
	panel.resume()
	var limit := (h0 if h0 > 0.0 else PRINT_HOLD_S) + TIMING_SLACK_S
	var t0 := Time.get_ticks_msec()
	var started := false
	while (Time.get_ticks_msec() - t0) / 1000.0 <= limit:
		if _state(panel, 2) != QUEUED:
			started = true
			break
		await process_frame
	_assert(started,
		"PAUSE GAP 1: after resume() the hold (%.2f s left) did not complete and start B within %.2f s; B is %s" % [h0, limit, _state_name(_state(panel, 2))])
	await _unmount(panel)


# The expansion overlay path (R-069-04): panel._show_expansion is the click path's body; it
# acquires InspectionState and shows the overlay; the hold must freeze until dismissal.
func _pause_by_expansion() -> void:
	var panel := await _panel(["Brief", "Second entry text here."])
	panel.start_printing("1")
	panel.start_printing("2")
	var t_printed := await _wait_printed(panel, 1, 4.0)
	_assert(t_printed >= 0.0, "PAUSE (expansion): entry A (1 word) did not reach PRINTED within 4 s")
	await _wait(0.2)
	panel.call("_show_expansion", "1")
	await process_frame
	var overlay: Control = panel.get("_expansion_overlay")
	_assert(overlay != null and overlay.visible, "PAUSE (expansion) control: the expansion overlay is not visible after _show_expansion on a PRINTED entry")
	var h0 := _hold_left(panel)
	await _wait(1.5)
	_assert(_state(panel, 2) == QUEUED,
		"PAUSE (expansion) R-069-04 (any printing entry pauses): with the overlay open on A, 1.5 s later B is %s, expected QUEUED (the old panel starts B at once)" % _state_name(_state(panel, 2)))
	var h1 := _hold_left(panel)
	_assert(h0 > 0.0 and absf(h1 - h0) <= 0.05,
		"PAUSE (expansion) GAP 1: print.hold_left_s moved from %.3f to %.3f with the overlay open (expected unchanged to 0.05; -1 means the print key is missing)" % [h0, h1])
	# dismiss exactly as the overlay's own dismissed signal does (releases InspectionState)
	if overlay != null:
		for child in overlay.get_children():
			child.emit_signal("dismissed")
	var inspection = get_root().get_node_or_null("InspectionState")
	if inspection != null:
		inspection.clear()
	await process_frame
	await _unmount(panel)


# ---- INVENTORY (GAP 3: qa_state print) -------------------------------------------------

func _inventory() -> void:
	var panel := await _panel([SIX, "Two words"])
	panel.start_printing("1")
	panel.start_printing("2")
	await _wait(0.05)
	var qa: Dictionary = panel.qa_state()
	for k in OLD_QA_KEYS:
		_assert(qa.has(k), "INVENTORY GAP 3: the existing qa_state key '%s' is gone" % k)
	_assert(qa.has("print") and qa.get("print") is Dictionary,
		"INVENTORY GAP 3: qa_state() has no `print` dictionary (keys: %s)" % str(qa.keys()))
	var p := _print_of(panel)
	_assert(p.has("printing_id") and typeof(p.get("printing_id")) == TYPE_INT and int(p.get("printing_id")) == 1,
		"INVENTORY GAP 3: while A prints, print.printing_id = %s, expected int 1 (print = %s)" % [str(p.get("printing_id")), str(p)])
	_assert(_int_list(p.get("queued")) == [2],
		"INVENTORY GAP 3: while A prints and B waits, print.queued = %s, expected [2]" % str(p.get("queued")))
	_assert(_int_list(p.get("printed")) == [] and p.has("printed"),
		"INVENTORY GAP 3: while A prints, print.printed = %s, expected []" % str(p.get("printed")))
	_assert(p.has("hold_left_s") and float(p.get("hold_left_s")) == 0.0,
		"INVENTORY GAP 3: while A prints, print.hold_left_s = %s, expected 0.0" % str(p.get("hold_left_s")))
	var t := await _wait_printed(panel, 1, 4.0)
	_assert(t >= 0.0, "INVENTORY: entry A did not reach PRINTED within 4 s")
	await _wait(0.1)
	p = _print_of(panel)
	_assert(p.has("printing_id") and int(p.get("printing_id")) == -1,
		"INVENTORY GAP 3: during the hold print.printing_id = %s, expected -1" % str(p.get("printing_id")))
	_assert(_int_list(p.get("queued")) == [2],
		"INVENTORY GAP 3: during the hold print.queued = %s, expected [2]" % str(p.get("queued")))
	_assert(_int_list(p.get("printed")) == [1],
		"INVENTORY GAP 3: during the hold print.printed = %s, expected [1]" % str(p.get("printed")))
	var h := float(p.get("hold_left_s", -1.0))
	_assert(h > 0.0 and h <= PRINT_HOLD_S,
		"INVENTORY GAP 3: during the hold print.hold_left_s = %s, expected above 0.0 and at most %.1f" % [str(p.get("hold_left_s")), PRINT_HOLD_S])
	var t2 := await _wait_printed(panel, 2, PRINT_HOLD_S + 4.0)
	_assert(t2 >= 0.0, "INVENTORY: entry B did not reach PRINTED within %.1f s" % (PRINT_HOLD_S + 4.0))
	await process_frame
	p = _print_of(panel)
	_assert(_int_list(p.get("printed")) == [1, 2] and _int_list(p.get("queued")).is_empty() and int(p.get("printing_id", 99)) == -1,
		"INVENTORY GAP 3: after both finished print = %s, expected printed [1, 2] in that order, queued [], printing_id -1" % str(p))
	await _unmount(panel)


# ---- INTEGRATION (the unedited sequencer feeds the panel; GAP 7) -----------------------

func _snapshot() -> Dictionary:
	var regions := []
	for i in range(4):
		regions.append({"i": i, "owner": 0 if i < 2 else 1})
	return {"type": "snapshot", "tick": 110, "regions": regions, "factions": [{"id": 0}, {"id": 1}]}


# 10-tick jump (5 s of replay at 2 ticks per second); entries start at ticks 100 and 101.
func _seq_frame() -> Dictionary:
	var snaps := [[0, 0, 1, 1], [0, 0, 1, 1], [0, 1, 1, 1], [0, 1, 1, 1], [1, 1, 1, 1], [1, 1, 1, 1]]
	var a := _entry(1, 100, 104, "The border held through the long winter.")
	var b := _entry(2, 101, 105, "The harbour fell.")
	for e in [a, b]:
		e["refs"] = {"regions": [0], "factions": [0]}
	return {
		"type": "chronicle",
		"jump": {"from_tick": 100, "to_tick": 110, "chapter_end_reason": 0},
		"entries": [a, b],
		"ownership": {"stride": 2, "from_tick": 100, "n_regions": 4, "snapshots": snaps},
		"keyframes": [],
	}


func _integration() -> void:
	var session = load(SIM_SESSION)
	session.reset()
	var bridge = RecordingBridge.new()
	bridge.hold_jump(_seq_frame(), _snapshot())
	session.set("_bridge", bridge)
	var seq: Node = (load(SequencerScene) as PackedScene).instantiate()
	get_root().add_child(seq)
	await process_frame
	await process_frame
	var panel: Node = seq.get("_scroll")
	_assert(panel != null and (panel.get("_entries") as Dictionary).size() == 2,
		"INTEGRATION control: the sequencer's scroll panel does not hold the two held-frame entries")
	if panel == null:
		await _unmount(seq)
		return
	await _wait(1.0)
	var replay: Dictionary = seq.qa_state().get("replay", {})
	var started: Array = replay.get("entries_started", [])
	_assert(int(replay.get("tick", -1)) >= 102,
		"INTEGRATION control: replay tick %s about 1.0 s after load, expected 102 or later (both entry ticks reached)" % str(replay.get("tick")))
	_assert(started == [1, 2],
		"INTEGRATION Q-069-03 (b): replay.entries_started = %s, expected [1, 2] (the clock-level list is unchanged: both ticks reached)" % str(started))
	var n_shown := 0
	for id in [1, 2]:
		if _shown(panel, id):
			n_shown += 1
	_assert(n_shown == 1 and _shown(panel, 1) and not _shown(panel, 2),
		"INTEGRATION R-069-03 (serial via the real feeder): at replay tick %s both entry ticks are reached; entry 1 is %s (shown %s), entry 2 is %s (shown %s); expected exactly entry 1 showing words and entry 2 QUEUED" % [str(replay.get("tick")), _state_name(_state(panel, 1)), str(_shown(panel, 1)), _state_name(_state(panel, 2)), str(_shown(panel, 2))])
	await _unmount(seq)
