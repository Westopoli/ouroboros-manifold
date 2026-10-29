extends SceneTree
# test-timeout: 10000

# Chronicle scene opening, rulings round 2 Addenda 27 and 28 (docs/northstar/
# plans/2026-10-01-architect-rulings-2.md) with E-09 R-069-01, R-069-03,
# R-069-06 and E-16 R-108-02. TESTS FIRST: written before the implementation;
# red ones name the rule they prove.
#
#   A69/A75/A77  opening the chronicle scene never advances the sim: neither
#        the sequencer's nor the embedded scroll panel's _ready sends any
#        command. Behavioural, no source scan: recording stand-ins for the
#        shared session bridge (tests/support/recording_bridge.gd) and for the
#        legacy SimBridge autoload (tests/support/recording_legacy_sink.gd).
#        The jump is issued once by Proceed from the debrief
#        (tests/test_debrief_proceed_jump.gd); the sequencer reads the held
#        frame and hands that same frame to the panel.
#   A76  no frame held (after a load): scroll with no entries, no replay, both
#        footer controls (PROCEED, EXIT TO MAIN MENU) shown; Proceed sends no
#        command and moves on to the screen after the chronicle in the normal
#        flow (mission_briefing, as after a replay).
#   A71/A78  live path: the panel slides in (narrower than 38 percent at the
#        start, at 38 percent within 0.40 s) and is visible at 38 percent
#        before the first entry prints (R-069-01, R-108-02).
#   A72 (rewritten, TD-VG-B-22)  with keyframe entries pending the map holds at
#        the next unhit keyframe while an entry prints and holds 3.0 s, and
#        runs on once it has (R-069-03 as rewritten, Q-069-03 (a)). The A72 and
#        A79 rulings (docs/northstar/plans/2026-10-01-architect-rulings-2.md:465,
#        :481) that said keyframes never delay the map clock are superseded by
#        Westley 2026-10-19 ("time varying is ok it is like a book").
#   A79  settle = replay clock at the jump's last tick AND the last entry
#        printed and held 3.0 s. A pending keyframe never delays settle.
#   A73  an entry with no mentions is valid; an entry with empty text still
#        yields the structural line, so the count on screen equals the
#        distiller's count (R-069-06).
#
# Controls (expected GREEN today): A73, footer hidden while the
# replay runs, footer hidden at clock end while the last entry still prints.
# Expected RED today: the rest of A69, A71/A78, A76, A72 (map hold), A79.
#
# Run: xvfb-run -a godot --headless --path . -s res://tests/test_chronicle_scene_open.gd

const SequencerScene := "res://scenes/world/time_jump_sequencer.tscn"
const PanelScene := "res://scenes/world/chronicle_scroll_panel.tscn"
const SIM_SESSION := "res://autoload/sim_session.gd"
const RecordingBridge := preload("res://tests/support/recording_bridge.gd")
const LegacySink := preload("res://tests/support/recording_legacy_sink.gd")
const TICKS_PER_SECOND := 2.0
const WIDTH_TOL := 0.02
const ENTRY_HOLD_S := 3.0
const SLIDE_S := 0.40
const TIMING_SLACK_S := 0.25

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


# Implementation-neutral: the on-screen fraction of the viewport width the panel covers (its global
# rect clipped to the viewport), so a position slide and a size slide both measure the same way.
func _visible_fraction(panel: Control) -> float:
	var vw := maxf(panel.get_viewport_rect().size.x, 1.0)
	var r := panel.get_global_rect()
	return maxf(0.0, minf(r.end.x, vw) - maxf(r.position.x, 0.0)) / vw


func _footer_button(seq: Node, text: String) -> Button:
	var footer = seq.get("_footer")
	if footer == null:
		return null
	for c in footer.get_children():
		if c is Button and (c as Button).text == text:
			return c
	return null


func _run_tests() -> void:
	# let the autoloads finish _ready (SimBridge opens its command file there) before a stand-in swaps it
	await process_frame
	await process_frame
	await _a69_open_with_frame()
	await _a69_open_without_frame()
	await _a69_general_ready_rule()
	await _a71_panel_visible_before_first_entry()
	await _a72_keyframes_hold_clock_until_the_entry_has_printed()
	await _a79_settle()
	await _a73_entries_without_mentions_and_text()
	await _a76_no_frame_proceed()
	load(SIM_SESSION).reset()


# A69: the sequencer opens on the frame the flow already issued, and sends nothing.
func _a69_open_with_frame() -> void:
	var bridge = _install(true)
	var sink = LegacySink.begin(get_root())
	var seq: Node = await _mount(SequencerScene)
	_assert(sink.sent().is_empty(),
		"A77: opening the chronicle scene sent %s through the legacy SimBridge from _ready" % str(sink.sent()))
	sink.end()
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
	var sink = LegacySink.begin(get_root())
	var seq: Node = await _mount(SequencerScene)
	_assert(sink.sent().is_empty(),
		"A77: opened with no frame held, the scene sent %s through the legacy SimBridge" % str(sink.sent()))
	sink.end()
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
	_assert(_footer_button(seq, "PROCEED") != null and _footer_button(seq, "EXIT TO MAIN MENU") != null,
		"A76: opened with no frame held, both footer controls (PROCEED, EXIT TO MAIN MENU) must exist")
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


# A69 general rule, behavioural (A77): the debrief's _ready sends nothing either.
func _a69_general_ready_rule() -> void:
	var bridge = _install(true)
	bridge._debrief = {"type": "debrief", "band": 2, "achieved": 0.8, "brought_home": 0.6,
		"region_delta": {"military": -4.0, "economy": 2.0, "tension": -3.0, "population": 0.0}}
	var debrief: Node = await _mount("res://scenes/debrief/debrief.tscn")
	_assert(bridge.sim_changing_sent().is_empty() and bridge.sent.is_empty(),
		"A69 general: opening the debrief sent %s from _ready" % str(bridge.sent))
	await _unmount(debrief)


# A71/A78: the panel slides in (narrower than 38 percent at the start, 38 percent within 0.40 s),
# and is visible at 38 percent before the first entry prints (R-069-01, R-108-02).
func _a71_panel_visible_before_first_entry() -> void:
	_install(true)
	var seq: Node = await _mount(SequencerScene)
	var panel := _panel_of(seq)
	_assert(panel != null, "A71: no scroll panel on the sequencer")
	if panel == null:
		await _unmount(seq)
		return
	var t0 := Time.get_ticks_msec()
	var first_frac := _visible_fraction(panel)
	_assert(panel.visible and panel.is_visible_in_tree(),
		"A71: scroll panel is hidden at the start, before the first entry printed (R-069-01, R-108-02)")
	_assert(first_frac < 0.38 - WIDTH_TOL,
		"A78: scroll panel shows %.3f of the viewport width at the start, expected under 0.38: the panel slides in over 0.40 s, by position or by size (R-069-01)" % first_frac)
	var reached := -1.0
	var started_early := false
	while true:
		var elapsed := (Time.get_ticks_msec() - t0) / 1000.0
		var frac := _visible_fraction(panel)
		if absf(frac - 0.38) <= WIDTH_TOL and reached < 0.0:
			reached = elapsed
			started_early = (seq.qa_state().get("replay", {}).get("entries_started", []) as Array).size() > 0
			break
		if elapsed > 2.0:
			break
		await process_frame
	_assert(reached >= 0.0 and reached <= SLIDE_S + TIMING_SLACK_S,
		"A78: scroll panel reached 38 percent width at %.2f s, expected within %.2f s of the start (R-069-01)" % [reached, SLIDE_S])
	_assert(reached >= 0.0 and not started_early,
		"A71: the panel reached 38 percent only after the first entry began printing")
	await _unmount(seq)


# A72 (rewritten, TD-VG-B-22): pending keyframe entries (the legacy bus path) hold the map at the next unhit
# keyframe while an entry prints and holds, and the map runs on once it has (R-069-03, Q-069-03 (a)).
# The earlier A72/A79 rulings (docs/northstar/plans/2026-10-01-architect-rulings-2.md:465, :481), that keyframes
# never stop or slow the clock, are superseded by Westley 2026-10-19 ("time varying is ok it is like a book").
# Premise: a 10-tick replay from 100, keyframes at 101, 102, 103; entry "e1" (12 words, about 1.2 s to print)
# is started by the first keyframe and then holds ENTRY_HOLD_S. The map reaches 101 at 0.5 s and waits there.
# Control: with the map running on (no hold) it shows tick 104 at 2 s and ends at 5.0 s, which fails the asserts below.
func _a72_keyframes_hold_clock_until_the_entry_has_printed() -> void:
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
	var finished := {"at": -1.0}
	seq.get("_scroll").entry_finished_printing.connect(func(_id: String) -> void:
		finished["at"] = (Time.get_ticks_msec() - t0) / 1000.0)
	var tick_at_start := int(seq.qa_state().get("replay", {}).get("tick", -1))
	var mid_tick := -1
	var max_tick_before_release := -1
	var elapsed := 0.0
	var r: Dictionary = seq.qa_state().get("replay", {})
	while bool(r.get("active", false)) and Time.get_ticks_msec() - t0 < 15000:
		await process_frame
		r = seq.qa_state().get("replay", {})
		elapsed = (Time.get_ticks_msec() - t0) / 1000.0
		if elapsed >= 2.0 and mid_tick < 0:
			mid_tick = int(r.get("tick", -1))
		# before the printed entry has held ENTRY_HOLD_S (less a frame of slack) the map may not pass tick 101
		if finished["at"] < 0.0 or elapsed < finished["at"] + ENTRY_HOLD_S - TIMING_SLACK_S:
			max_tick_before_release = maxi(max_tick_before_release, int(r.get("tick", -1)))
	print("INFO: A72 entry printed at %.2f s, tick at 2 s %d, highest tick before release %d, replay ended at %.2f s" % [finished["at"], mid_tick, max_tick_before_release, elapsed])
	var release_at: float = finished["at"] + ENTRY_HOLD_S
	var expected_end: float = release_at + float(110 - 101) / TICKS_PER_SECOND
	_assert(tick_at_start == 100, "A72: replay did not start at from_tick (tick %d)" % tick_at_start)
	_assert(finished["at"] > 0.0 and finished["at"] < 2.0,
		"A72: control: the keyframe entry finished printing at %.2f s, expected within 2 s (12 words at 0.08 s each)" % finished["at"])
	_assert(mid_tick == 101,
		"A72: replay tick after 2 s was %d while the keyframe entry prints and holds, expected 101: the map holds at the next unhit keyframe (R-069-03, Q-069-03 (a))" % mid_tick)
	_assert(max_tick_before_release <= 101,
		"A72: the replay tick reached %d before the printed entry had held %.1f s (printed at %.2f s), expected never past the keyframe at 101" % [max_tick_before_release, ENTRY_HOLD_S, finished["at"]])
	_assert(not bool(r.get("active", false)) and absf(elapsed - expected_end) <= 0.6,
		"A72: a 10-tick replay with a keyframe entry pending took %.2f s, expected %.2f s (entry printed at %.2f s, held %.1f s, then 9 ticks at %.0f per second)" % [elapsed, expected_end, finished["at"], ENTRY_HOLD_S, TICKS_PER_SECOND])
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


func _timed_footer_run(frame: Dictionary, with_pending_keyframe: bool, limit_s: float) -> Dictionary:
	_install(true)
	var seq: Node = await _mount(SequencerScene)
	seq.load_frame(frame, [1, 1, 1, 1])
	if with_pending_keyframe:
		# a keyframe on the legacy bus path that nothing consumes: the old queue-hold shape
		var bus = get_root().get_node("UIDataBus")
		bus.time_jump_keyframe.emit({"chronicle_entry_id": "", "regions_snapshot": [], "connections_snapshot": [], "military_events": []})
	var footer = seq.get("_footer")
	var t0 := Time.get_ticks_msec()
	var out := {"clock_end": -1.0, "last_printed": -1.0, "settle": -1.0, "visible_while_replay": false,
		"visible_at_clock_end_unprinted": false, "printed_at_settle": -1}
	var total: int = (frame.get("entries", []) as Array).size()
	while true:
		await process_frame
		var elapsed := (Time.get_ticks_msec() - t0) / 1000.0
		var qa: Dictionary = seq.qa_state()
		var active := bool(qa.get("replay", {}).get("active", false))
		var printed := int(qa.get("entries_printed", 0))
		if active and footer != null and footer.visible:
			out["visible_while_replay"] = true
		if not active and out["clock_end"] < 0.0:
			out["clock_end"] = elapsed
			if printed < total and footer != null and footer.visible:
				out["visible_at_clock_end_unprinted"] = true
		if printed >= total and out["last_printed"] < 0.0:
			out["last_printed"] = elapsed
		if footer != null and footer.visible and out["settle"] < 0.0:
			out["settle"] = elapsed
			out["printed_at_settle"] = printed
			break
		if elapsed > limit_s:
			break
	await _unmount(seq)
	return out


# A72/A79: settle = clock at the last tick AND the last entry printed and held 3.0 s; a pending
# keyframe never delays it (R-069-03).
func _a79_settle() -> void:
	# short entries: the clock (5.0 s) ends before the last entry has held 3.0 s
	for pending in [false, true]:
		var tag := "with a pending keyframe" if pending else "with no keyframe pending"
		var r: Dictionary = await _timed_footer_run(_frame(), pending, 12.0)
		_assert(not r["visible_while_replay"], "A79 control: the footer showed while the replay was still running (%s)" % tag)
		_assert(r["settle"] >= 0.0,
			"A79: the footer never settled within 12 s %s; settle is the clock at the last tick plus the last entry printed and held (R-069-03)" % tag)
		if r["settle"] >= 0.0:
			_assert(r["settle"] >= r["clock_end"] - 0.05 and r["settle"] >= r["last_printed"] + ENTRY_HOLD_S - TIMING_SLACK_S,
				"A79: settled at %.2f s %s; clock ended %.2f s, last entry printed %.2f s, it must hold %.1f s first" % [r["settle"], tag, r["clock_end"], r["last_printed"], ENTRY_HOLD_S])
			_assert(r["settle"] <= r["last_printed"] + ENTRY_HOLD_S + 1.5,
				"A79: settled at %.2f s %s, long after the last entry printed (%.2f s) and held %.1f s; a pending keyframe must not delay settle" % [r["settle"], tag, r["last_printed"], ENTRY_HOLD_S])
	# a last entry that is still printing when the clock ends: settle waits for it
	var frame := _frame()
	var words := ""
	for i in range(30):
		words += "word%d " % i
	frame["entries"] = [_entry(1, 106, 108, "The border held."), _entry(2, 109, 110, words.strip_edges())]
	var slow: Dictionary = await _timed_footer_run(frame, true, 18.0)
	_assert(not slow["visible_at_clock_end_unprinted"],
		"A79 control: the footer showed at the end of the clock while the last entry was still printing")
	_assert(slow["settle"] >= 0.0,
		"A79: the footer never settled within 18 s when the last entry printed after the clock ended")
	if slow["settle"] >= 0.0:
		_assert(slow["printed_at_settle"] == 2 and slow["settle"] >= slow["last_printed"] + ENTRY_HOLD_S - TIMING_SLACK_S,
			"A79: settled at %.2f s with %s of 2 entries printed (last printed %.2f s); settle only after the last entry printed and held %.1f s" % [slow["settle"], str(slow["printed_at_settle"]), slow["last_printed"], ENTRY_HOLD_S])


# A76: no frame held; Proceed sends no command and moves on to the screen after the chronicle.
func _a76_no_frame_proceed() -> void:
	var bridge = _install(false)
	var sink = LegacySink.begin(get_root())
	var seq: Node = await _mount(SequencerScene)
	var proceed := _footer_button(seq, "PROCEED")
	_assert(proceed != null, "A76: no PROCEED control with no frame held")
	var router = get_root().get_node("SceneRouter")
	router.set("_current_scene_name", "")
	if proceed != null:
		seq.call("_on_proceed")
		var t0 := Time.get_ticks_msec()
		while str(router.get("_current_scene_name")) == "" and Time.get_ticks_msec() - t0 < 2500:
			await process_frame
	_assert(str(router.get("_current_scene_name")) == "mission_briefing",
		"A76: Proceed with no frame held went to '%s', expected mission_briefing (the screen after the chronicle, as after a replay)" % str(router.get("_current_scene_name")))
	_assert(bridge.sent.is_empty() and sink.sent().is_empty(),
		"A76: Proceed with no frame held sent %s / legacy %s; it must send nothing to the sim" % [str(bridge.sent), str(sink.sent())])
	sink.end()
	if is_instance_valid(seq):
		await _unmount(seq)
