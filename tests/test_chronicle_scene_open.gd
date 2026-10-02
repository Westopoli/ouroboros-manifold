extends SceneTree

# Chronicle scene opening, rulings round 2 Addendum 27 (docs/northstar/plans/
# 2026-10-01-architect-rulings-2.md) with E-09 R-069-01, R-069-03, R-069-06 and
# E-16 R-108-02. TESTS FIRST: written before the implementation; red ones name
# the rule they prove.
#
#   A69  opening the chronicle scene never advances the sim: neither the
#        sequencer's nor the embedded scroll panel's _ready sends `jump` (or
#        any other sim-changing command). The jump is issued once by the flow
#        that leads in (Proceed from the debrief; tests/test_debrief_proceed_jump.gd);
#        the sequencer holds that jump's frame and the panel shows the same one.
#        With no frame held (after a load, before any jump) the scene shows the
#        scroll with no entries, no replay and its footer, and sends nothing.
#        General rule: a scene's _ready reads state and frames, sends no
#        command that changes the sim (checked on the sequencer's and the
#        panel's _ready source, and on the recording bridge).
#   A71  live path: the scroll panel is visible and at 38 percent width before
#        the first entry prints (R-069-01, R-108-02).
#   A72  keyframes never delay the map clock: replay position advances at
#        REPLAY_TICKS_PER_SECOND with keyframe entries pending (R-069-03).
#   A73  an entry with no mentions is valid; an entry with empty text still
#        yields the structural line, so the count on screen equals the
#        distiller's count (R-069-06).
#
# Controls (expected GREEN today): A72, A73, and the planted-source detector
# control. Expected RED today: A69 (all), A71.
# Interpretations the Architect should confirm are listed in the Doer report.
#
# Run: xvfb-run -a godot --headless --path . -s res://tests/test_chronicle_scene_open.gd

const SequencerScene := "res://scenes/world/time_jump_sequencer.tscn"
const PanelScene := "res://scenes/world/chronicle_scroll_panel.tscn"
const SIM_SESSION := "res://autoload/sim_session.gd"
const RecordingBridge := preload("res://tests/support/recording_bridge.gd")
const TICKS_PER_SECOND := 2.0
const WIDTH_TOL := 0.02

var _pass_count := 0
var _fail_count := 0
var _fail_msgs: Array[String] = []


func _initialize() -> void:
	await _run_tests()
	print("\n=== Chronicle Scene Open Results ===")
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


func _snapshot() -> Dictionary:
	var regions := []
	for i in range(4):
		regions.append({"i": i, "owner": 0 if i < 2 else 1})
	return {"type": "snapshot", "tick": 110, "regions": regions, "factions": [{"id": 0}, {"id": 1}]}


func _entry(id: int, s: int, e: int, text: String = "Text %d." % 0) -> Dictionary:
	return {"id": id, "start_tick": s, "end_tick": e, "category": 3, "cluster_type": 1,
		"refs": {"regions": [0], "factions": [0]}, "fragment": -1, "fragment_ids": [-1, -1, -1],
		"significance": 0.8, "text": text, "mentions": [], "expanded_text": "", "expanded_mentions": []}


# 10-tick jump (5 s of replay), entries start well after the first frames.
func _frame() -> Dictionary:
	var snaps := [[0, 0, 1, 1], [0, 0, 1, 1], [0, 1, 1, 1], [0, 1, 1, 1], [1, 1, 1, 1], [1, 1, 1, 1]]
	return {
		"type": "chronicle",
		"jump": {"from_tick": 100, "to_tick": 110, "chapter_end_reason": 0},
		"entries": [_entry(1, 106, 108, "The border held."), _entry(2, 108, 110, "The harbour fell.")],
		"ownership": {"stride": 2, "from_tick": 100, "n_regions": 4, "snapshots": snaps},
		"keyframes": [102, 105, 108],
	}


func _install(held: bool) -> Object:
	var session = load(SIM_SESSION)
	session.reset()
	var bridge = RecordingBridge.new()
	if held:
		bridge.hold_jump(_frame(), _snapshot())
	else:
		# after a load: a world, but no jump taken yet
		bridge.canned_chronicle = _frame()
		bridge.canned_snapshot = _snapshot()
		bridge._snapshot = _snapshot()
	session.set("_bridge", bridge)
	return bridge


func _mount(path: String) -> Node:
	var node: Node = (load(path) as PackedScene).instantiate()
	get_root().add_child(node)
	await process_frame
	await process_frame
	return node


func _unmount(node: Node) -> void:
	node.queue_free()
	await process_frame
	await process_frame


func _panel_of(seq: Node) -> Node:
	return seq.get("_scroll")


func _entry_ids(panel: Node) -> Array:
	var ids: Array = []
	for e in panel.qa_state().get("entries", []):
		ids.append(int(e.get("entry_id", -1)))
	return ids


# A source-level check of the general rule: a _ready body must not mention a
# command sender. Returns the offending tokens.
func _ready_body_offences(script_path: String) -> Array:
	var src := FileAccess.get_file_as_string(script_path)
	return _offences_in_ready(src)


func _offences_in_ready(src: String) -> Array:
	var start := src.find("func _ready()")
	if start < 0:
		return []
	var end := src.find("\nfunc ", start + 5)
	var body := src.substr(start, (end if end >= 0 else src.length()) - start)
	var hits: Array = []
	for token in ["send_command", "load_chronicle_live", "\"jump\"", "load_debrief_live", "load_mission_live", "ready_for_time_jump"]:
		if body.find(token) >= 0:
			hits.append(token)
	return hits


func _run_tests() -> void:
	# --- detector positive control: the scan flags a planted sender, and not a clean body.
	_assert(_offences_in_ready("func _ready() -> void:\n\tbridge.send_command({})\n").size() > 0,
		"control: the _ready scan did not flag a planted send_command")
	_assert(_offences_in_ready("func _ready() -> void:\n\tvar f = bridge.chronicle_frame()\n\nfunc other():\n\tx.send_command({})\n").is_empty(),
		"control: the _ready scan flagged a clean _ready (or read past it)")

	await _a69_open_with_frame()
	await _a69_open_without_frame()
	await _a69_general_ready_rule()
	await _a71_panel_visible_before_first_entry()
	await _a72_keyframes_never_hold_clock()
	await _a73_entries_without_mentions_and_text()
	load(SIM_SESSION).reset()


# A69: the sequencer opens on the frame the flow already issued, and sends nothing.
func _a69_open_with_frame() -> void:
	var bridge = _install(true)
	var seq: Node = await _mount(SequencerScene)
	_assert(bridge.count("jump") == 0,
		"A69: opening the chronicle scene sent %d `jump` command(s) from _ready; the jump belongs to the flow leading in (Proceed from the debrief)" % bridge.count("jump"))
	_assert(bridge.sim_changing_sent().is_empty(),
		"A69: opening the chronicle scene sent sim-changing commands %s from _ready" % str(bridge.sim_changing_sent()))
	var panel := _panel_of(seq)
	var replay: Dictionary = seq.qa_state().get("replay", {})
	_assert(int(replay.get("to_tick", -1)) == 110 and int(replay.get("from_tick", -1)) == 100,
		"A69: the sequencer is not showing the held frame (replay %s)" % str(replay))
	_assert(panel != null and panel.qa_state().get("tick", -1) == 110,
		"A69: the embedded scroll panel is not showing the held frame's tick (qa tick %s, expected 110)" % str(panel.qa_state().get("tick", null) if panel != null else null))
	_assert(panel != null and _entry_ids(panel) == [1, 2],
		"A69: sequencer and scroll panel show different frames (panel entries %s, held frame has [1, 2])" % str(_entry_ids(panel) if panel != null else null))
	_assert(panel != null and int(panel.qa_state().get("regen_count", 99)) == 1,
		"A69: the panel was filled %s times; the sequencer hands it the held frame once" % str(panel.qa_state().get("regen_count") if panel != null else null))
	await _unmount(seq)


# A69: no frame held (after a load, before any jump).
func _a69_open_without_frame() -> void:
	var bridge = _install(false)
	var seq: Node = await _mount(SequencerScene)
	_assert(bridge.sent.is_empty(),
		"A69: opened with no frame held, the scene sent %s; it must send nothing" % str(bridge.sent))
	var panel := _panel_of(seq)
	_assert(panel != null and _entry_ids(panel).is_empty(),
		"A69: opened with no frame held, the scroll shows entries %s; expected none" % str(_entry_ids(panel) if panel != null else null))
	var replay: Dictionary = seq.qa_state().get("replay", {})
	_assert(not bool(replay.get("active", true)) and int(replay.get("snapshot_count", -1)) == 0,
		"A69: opened with no frame held, a replay is present (%s); expected none" % str(replay))
	_assert(panel != null and panel.visible,
		"A69: opened with no frame held, the scroll is not shown")
	var footer = seq.get("_footer")
	_assert(footer != null and footer.visible,
		"A69: opened with no frame held, the footer is not shown (nothing to wait for, so it must not stay hidden)")
	await _unmount(seq)

	# the standalone scroll panel scene (routed as "chronicle") obeys the same rule
	bridge = _install(false)
	var solo: Node = await _mount(PanelScene)
	_assert(bridge.sent.is_empty(),
		"A69: the standalone chronicle panel opened with no frame held sent %s; it must send nothing" % str(bridge.sent))
	_assert(_entry_ids(solo).is_empty(),
		"A69: the standalone chronicle panel opened with no frame held shows entries %s; expected none" % str(_entry_ids(solo)))
	_assert(solo.get_node_or_null("**/Return") != null or solo.find_child("Return", true, false) != null,
		"A69: the standalone chronicle panel opened with no frame held has no Return control (its footer)")
	await _unmount(solo)


# A69 general rule: a scene's _ready reads and sends no sim-changing command.
func _a69_general_ready_rule() -> void:
	for path in ["res://scenes/world/time_jump_sequencer.gd", "res://scenes/world/chronicle_scroll_panel.gd", "res://scenes/debrief/debrief.gd"]:
		var hits := _ready_body_offences(path)
		_assert(hits.is_empty(), "A69 general: %s _ready mentions command senders %s" % [path, str(hits)])
	var bridge = _install(true)
	bridge._debrief = {"type": "debrief", "band": 2, "achieved": 0.8, "brought_home": 0.6,
		"region_delta": {"military": -4.0, "economy": 2.0, "tension": -3.0, "population": 0.0}}
	var debrief: Node = await _mount("res://scenes/debrief/debrief.tscn")
	_assert(bridge.sim_changing_sent().is_empty() and bridge.sent.is_empty(),
		"A69 general: opening the debrief sent %s from _ready" % str(bridge.sent))
	await _unmount(debrief)


# A71: slide-in happens before the first entry prints (R-069-01, R-108-02).
func _a71_panel_visible_before_first_entry() -> void:
	_install(true)
	var seq: Node = await _mount(SequencerScene)
	var panel := _panel_of(seq)
	var checked := false
	var frames := 0
	while frames < 30 and panel != null:
		var replay: Dictionary = seq.qa_state().get("replay", {})
		if (replay.get("entries_started", []) as Array).size() > 0:
			break
		if frames >= 1:
			checked = true
			var width_frac: float = panel.size.x / maxf(seq.size.x, 1.0)
			_assert(panel.visible and panel.is_visible_in_tree(),
				"A71: scroll panel is hidden at frame %d, before the first entry printed (R-069-01, R-108-02)" % frames)
			_assert(absf(width_frac - 0.38) <= WIDTH_TOL,
				"A71: scroll panel is %.3f of the scene width before the first entry printed, expected 0.38 (R-108-02)" % width_frac)
			break
		await process_frame
		frames += 1
	_assert(checked, "A71: no frame was sampled before the first entry printed (replay entries already started)")
	await _unmount(seq)


# A72: pending keyframe entries (the legacy bus path) never stop or slow the clock (R-069-03).
func _a72_keyframes_never_hold_clock() -> void:
	_install(true)
	var seq: Node = await _mount(SequencerScene)
	var frame := _frame()
	frame["entries"] = [_entry(1, 100, 104, "A keyframe entry that prints slowly, for a long while, over many words.")]
	frame["keyframes"] = [101, 102, 103]
	var live := [1, 1, 1, 1]
	seq.load_frame(frame, live)
	# a keyframe paired with an entry that has not finished printing: the old queue-hold shape
	var bus = get_root().get_node("UIDataBus")
	bus.time_jump_started.emit("tj", 1, 3, 1, {"f0": "Alpha", "f1": "Beta"})
	bus.chronicle_entry.emit({"entry_id": "e1", "base_form": "This entry keeps printing for a long time while the map keeps moving.", "mentions": []})
	for i in range(3):
		bus.time_jump_keyframe.emit({"chronicle_entry_id": "e1", "regions_snapshot": [], "connections_snapshot": [], "military_events": []})
	var t0 := Time.get_ticks_msec()
	var tick_at_start := int(seq.qa_state().get("replay", {}).get("tick", -1))
	var mid_tick := -1
	var elapsed := 0.0
	var r: Dictionary = seq.qa_state().get("replay", {})
	while bool(r.get("active", false)) and Time.get_ticks_msec() - t0 < 9000:
		await process_frame
		r = seq.qa_state().get("replay", {})
		elapsed = (Time.get_ticks_msec() - t0) / 1000.0
		if elapsed >= 2.0 and mid_tick < 0:
			mid_tick = int(r.get("tick", -1))
	_assert(tick_at_start == 100, "A72: replay did not start at from_tick (tick %d)" % tick_at_start)
	_assert(mid_tick >= 103 and mid_tick <= 105,
		"A72: replay tick after 2 s was %d with keyframe entries pending, expected about 104 (%.0f ticks per second; the map is the master clock, R-069-03)" % [mid_tick, TICKS_PER_SECOND])
	_assert(not bool(r.get("active", false)) and absf(elapsed - 5.0) <= 0.6,
		"A72: a 10-tick replay with keyframe entries pending took %.2f s, expected 5.0 s" % elapsed)
	await _unmount(seq)


# A73: no mentions is valid; empty text falls back to the structural line; count on screen = distiller count.
func _a73_entries_without_mentions_and_text() -> void:
	_install(true)
	var panel: Node = await _mount(PanelScene)
	var no_mentions := {"id": 11, "start_tick": 100, "end_tick": 104, "category": 3, "cluster_type": 1,
		"refs": {"regions": [0], "factions": [0]}, "fragment": -1, "fragment_ids": [-1, -1, -1],
		"significance": 0.8, "text": "A quiet year.", "expanded_text": ""}
	var empty_text := {"id": 12, "start_tick": 104, "end_tick": 108, "category": 5, "cluster_type": 1,
		"refs": {"regions": [1], "factions": [0]}, "fragment": -1, "fragment_ids": [-1, -1, -1],
		"significance": 0.6, "text": "", "mentions": [], "expanded_text": "", "expanded_mentions": []}
	var with_mentions := _entry(13, 108, 110, "Alpha took the harbour.")
	with_mentions["mentions"] = [{"kind": "faction", "start": 0, "len": 5, "id": 0}]
	var frame := {"type": "chronicle", "jump": {"from_tick": 100, "to_tick": 110}, "entries": [no_mentions, empty_text, with_mentions]}
	panel.set_snapshot(_snapshot())
	panel.load_frame(frame)
	await process_frame
	await process_frame
	var qa: Dictionary = panel.qa_state()
	var shown := 0
	var container = panel.get("_entry_container")
	for child in container.get_children():
		if not child.is_queued_for_deletion():
			shown += 1
	_assert(qa.get("entries", []).size() == 3 and qa.get("dropped_entries", -1) == 0,
		"A73/R-069-06: distiller produced 3 entries, panel kept %d (dropped %s)" % [qa.get("entries", []).size(), str(qa.get("dropped_entries"))])
	_assert(shown == 3, "A73/R-069-06: count on screen is %d, distiller count is 3" % shown)
	var texts: Array = []
	for e in qa.get("entries", []):
		texts.append(str(e.get("text", "")))
	_assert(texts.size() == 3 and texts[0] == "A quiet year.", "A73: an entry with no `mentions` key is not shown as sent (texts %s)" % str(texts))
	_assert(texts.size() == 3 and texts[1] != "" and texts[1].find("{") < 0 and texts[1].find("[") < 0,
		"A73: an entry with empty text did not get the structural-line fallback (text %s)" % str(texts[1] if texts.size() > 1 else null))
	await _unmount(panel)
