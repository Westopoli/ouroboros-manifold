extends "res://tests/support/vg_c_case.gd"
# Rule pins: R-104-01@d9c166, R-104-02@03d7aa, R-235-01@4f35af, R-235-02@138056, R-235-03@14ac1a, R-235-04@a81fce

# VG-E1M tests: S-235 ticker beats (scenes/economy/ticker_beats.gd, class TickerBeats) and the three-line skip in
# scenes/tactical_c/hud/events_feed.gd (Architect ruling G2 (b), 2026-10-14). Spec:
# docs/northstar/plans/2026-10-07-visible-game-spec.md, "S-235 ticker (amends the E1m and E1n paragraphs;
# Q-235-01 closed)", lane E1 part b, lane A row A8.
#
# Rules proved, word for word (docs/bible/epics/E-16-client-camera-hud-and-world-view.md):
#   R-104-01 (:70)  "Given a mission, When the HUD is drawn, Then the player can always see the objective list with
#     progress (top-left) and a quiet ticker of notable beats beneath it; the ticker recognizes structure captured,
#     structure lost, force routed, and objective threshold crossed, and nothing else at launch."
#   R-235-01 (:271) "Given the map view (S-161) and the tactical view, When the economy's places are drawn, Then the
#     economic locations, the neutral settlements, the objective, the side's base of operations, its expansions and
#     forward works, and on land maps the strongpoints are marked (E-22 S-175, S-177; E-15)."   (E1n, MapMarkers: its
#     own test file; not proved here)
#   R-235-02 (:272) "Given an environmental trouble travelling across the map, When it is drawn, Then both sides see
#     where it is as it moves (E-15 holds what it does)."   (not E1m)
#   R-235-03 (:273) "Given the ticker (R-104-01), When a base is occupied, a side falls back to an expansion, an
#     expansion is founded, a weather trouble arrives, or a strongpoint is taken or lost, Then the ticker names it; no
#     other economy beat reaches the ticker (Westley, 2026-10-12)."
#   R-235-04 (:274) "Given a shipment that does not arrive (E-22 S-176), When the ticker, the banners and the map are
#     read, Then nothing on them explains why."
# Spec sentence: "The ticker carries the four beats plus a strongpoint taken or lost; forward bases are not named."
#
# Rulings used: G2 (b) (E1m emits its own strongpoint_taken / strongpoint_lost from the structures rows joined to the
# strongpoint ids of frame["strongpoints"]; a strongpoint that leaves the rows while own counts as lost; events_feed.gd
# skips a strongpoint id so there is one ticker line per event); G3 (a) (the four other beats have no frame source,
# they are STUB: proved by emit_beat and the A8 listening path only); PIN a8-feed (the skip keys only on
# frame["strongpoints"], or on ids remembered from a full frame that carried it; tests/test_vg_a_events_feed.gd is not
# edited). Texts are DRAFT-e1m-beat-text, so no text is asserted except that TEXTS[kind] is non-empty and is what
# reaches the ticker.
#
# Groups: [CONTROL] green on the built tree; [LOAD] [EMIT] [A8] [FEED] [SKIP] [NOSOURCE] red until built.
# The SKIP group has a half that is green on the built tree (an ordinary structure flip still gives exactly one
# Structure captured / Structure lost line: the positive control that A8 still beats ordinary structures) and a half
# that is red on it (A8 beats a strongpoint today).

const TICKER := "res://scenes/economy/ticker_beats.gd"
const EVENTS := "res://scenes/tactical_c/hud/events_feed.gd"
const SIX := ["base_occupied", "fallback", "expansion", "weather", "strongpoint_taken", "strongpoint_lost"]
const SP3 := 3
const SP4 := 4
const PLAIN := 9
const LOCAL := 0
const ENEMY := 1
const OTHER := 2


func _run() -> void:
	await _control()
	await _load_group()
	await _emit_group()
	await _a8_group()
	await _feed_group()
	await _skip_group()
	await _nosource_group()


# ---------------------------------------------------------------- helpers

func _put(n: Node) -> Node:
	root.add_child(n)
	return n


func _drop(nodes: Array) -> void:
	for n in nodes:
		if n != null and is_instance_valid(n):
			if n.get_parent() != null:
				n.get_parent().remove_child(n)
			n.free()


func _events() -> Node:
	var s := _load(EVENTS)
	if s == null:
		return null
	return _put(s.new())


func _ticker() -> Node:
	var s := _load(TICKER)
	if s == null:
		return null
	var n: Node = s.new()
	_put(n)
	return n


func _ticker_ok(t: Node, who: String) -> bool:
	if t == null:
		return false
	var ok := true
	for m in ["emit_beat", "feed", "beats_emitted", "last_beat"]:
		if not t.has_method(m):
			_check(false, "%s: TickerBeats lacks method %s" % [who, m])
			ok = false
	return ok


func _kinds(lines: Array) -> Array:
	var k := []
	for l in lines:
		k.append(String(l["kind"]))
	return k


# A reconstructed tactical view (CBridge._reconstruct_tactical): the whole structures list, the strongpoints of the
# last full frame, no structures_changed. `owners` maps structure id -> owner for the rows that are present;
# strongpoints always lists SP3 and SP4, their owner read from `owners` (-1 when the row is absent).
func _view(tick: int, owners: Dictionary, extra: Dictionary = {}) -> Dictionary:
	var ids := owners.keys()
	ids.sort()
	var rows := []
	for id in ids:
		rows.append({"id": id, "type": 0, "owner": owners[id], "x": 2000.0 + 100.0 * id, "y": 1500.0, "hp": 500.0,
			"stage": 0, "cap": 0, "nst": 150, "next_type": 0, "period": 100})
	var sps := []
	for id in [SP3, SP4]:
		sps.append({"id": id, "x": 2000.0 + 100.0 * id, "y": 1500.0, "owner": owners.get(id, -1), "state": 0})
	var f := {"type": "tactical", "full": true, "tick": tick, "player_faction": LOCAL, "units": [], "events": [],
		"objectives": [], "structures": rows, "strongpoints": sps, "economy": {"doctrine": 3, "resources": {}}}
	f.merge(extra, true)
	return f


func _delta(tick: int, changed: Array, extra: Dictionary = {}) -> Dictionary:
	var rows := []
	for c in changed:
		rows.append({"id": c[0], "owner": c[1]})
	var f := {"type": "tactical_delta", "tick": tick, "structures_changed": rows}
	f.merge(extra, true)
	return f


# One structure owner change fed the way the live game would see it: the delta to Events, the view to TickerBeats.
func _flip(ev: Node, tk: Node, owners: Dictionary, tick: int, id: int, new_owner: int, delta_extra: Dictionary = {}) -> void:
	owners[id] = new_owner
	ev.feed(_delta(tick, [[id, new_owner]], delta_extra), LOCAL)
	if tk != null:
		tk.feed(_view(tick, owners), LOCAL)


# ---------------------------------------------------------------- [CONTROL]

# A stub node named TickerBeats with the signal beat(kind, text) beside the real events_feed.gd: Events listens to it
# today (A8, events_feed.gd:_connect_ticker). Green on the built tree; the positive control of every group below.
func _control() -> void:
	var g := GDScript.new()
	g.source_code = "extends Node\nsignal beat(kind: String, text: String)\n"
	var err := g.reload()
	_check(err == OK, "[CONTROL] the stub TickerBeats script compiles")
	var stub := Node.new()
	stub.set_script(g)
	stub.name = "TickerBeats"
	_put(stub)
	var ev := _events()
	if ev == null:
		_drop([stub])
		return
	await process_frame
	ev.feed({}, LOCAL)
	_check(root.find_child("TickerBeats", true, false) == stub, "[CONTROL] the stub is findable as TickerBeats")
	stub.emit_signal("beat", "weather", "stub weather text")
	var texts := []
	for l in ev.lines():
		texts.append(String(l["text"]))
	_check(texts == ["stub weather text"], "[CONTROL] R-235-03 the A8 listening path: a beat(kind, text) from a node named TickerBeats reaches Events.lines(); got %s" % [texts])
	_check(ev.banner() == "stub weather text", "[CONTROL] the same beat raises the banner (R-104-02)")
	_drop([ev, stub])


# ---------------------------------------------------------------- [LOAD]

func _load_group() -> void:
	var s := _load(TICKER)
	if s == null:
		return
	_check(s.get_global_name() == &"TickerBeats", "[LOAD] ticker_beats.gd declares class_name TickerBeats; got '%s'" % [s.get_global_name()])
	var sig_ok := false
	for sg in s.get_script_signal_list():
		if sg["name"] == "beat":
			var names := []
			for a in sg["args"]:
				names.append(a["name"])
			sig_ok = names == ["kind", "text"]
	_check(sig_ok, "[LOAD] the script has signal beat(kind: String, text: String)")
	var consts := s.get_script_constant_map()
	_check(consts.has("KINDS"), "[LOAD] const KINDS exists")
	_check(consts.has("TEXTS"), "[LOAD] const TEXTS exists")
	if consts.has("KINDS"):
		var kinds: Array = consts["KINDS"]
		_check(kinds.size() == 6 and SIX.all(func(k): return k in kinds), "[LOAD] R-235-03 KINDS is exactly the six kinds %s; got %s" % [SIX, kinds])
		if consts.has("TEXTS"):
			var texts: Dictionary = consts["TEXTS"]
			for k in SIX:
				_check(texts.has(k) and texts[k] is String and String(texts[k]) != "", "[LOAD] TEXTS[%s] is a non-empty string (DRAFT-e1m-beat-text)" % k)
			_check(texts.size() == 6, "[LOAD] R-235-03 TEXTS names the six kinds and nothing else; got %d keys" % texts.size())
			for k in texts:
				var low := String(texts[k]).to_lower()
				_check(low.find("shipment") < 0, "[LOAD] R-235-04 the text of %s does not mention a shipment" % k)
				_check(low.find("forward") < 0, "[LOAD] spec: forward bases are not named (text of %s)" % k)
	var n: Node = s.new()
	_put(n)
	await process_frame
	_check(n.name == "TickerBeats", "[LOAD] _ready sets name = TickerBeats; got '%s'" % n.name)
	_check(root.find_child("TickerBeats", true, false) == n, "[LOAD] the node is findable by find_child(\"TickerBeats\", true, false)")
	_drop([n])


# ---------------------------------------------------------------- [EMIT]

func _emit_group() -> void:
	var s := _load(TICKER)
	if s == null:
		return
	var t := _ticker()
	if not _ticker_ok(t, "[EMIT]"):
		_drop([t])
		return
	var texts: Dictionary = s.get_script_constant_map().get("TEXTS", {})
	var got := []
	t.connect("beat", func(k, x): got.append([k, x]))
	_check(t.beats_emitted() == 0 and t.last_beat() == {}, "[EMIT] before any beat: beats_emitted 0 and last_beat {}")
	var n := 0
	for k in SIX:
		got.clear()
		var r = t.emit_beat(k)
		n += 1
		_check(r == true, "[EMIT] R-235-03 emit_beat(%s) returns true" % k)
		_check(got == [[k, texts.get(k, "<no TEXTS entry>")]], "[EMIT] R-235-03 emit_beat(%s) emits exactly one beat(%s, TEXTS[%s]); got %s" % [k, k, k, got])
		_check(t.beats_emitted() == n, "[EMIT] beats_emitted counts %d after %s" % [n, k])
		_check(t.last_beat() == {"kind": k, "text": texts.get(k, "<no TEXTS entry>")}, "[EMIT] last_beat is {kind, text} of %s; got %s" % [k, t.last_beat()])
	for bad in ["shipment", "forward_base", "unknown", ""]:
		got.clear()
		var before: int = t.beats_emitted()
		var last: Dictionary = t.last_beat()
		var r = t.emit_beat(bad)
		_check(r == false, "[EMIT] R-235-04 / spec :327 emit_beat('%s') returns false" % bad)
		_check(got.is_empty(), "[EMIT] R-235-03 'no other economy beat reaches the ticker': emit_beat('%s') emits nothing; got %s" % [bad, got])
		_check(t.beats_emitted() == before and t.last_beat() == last, "[EMIT] emit_beat('%s') leaves the counters alone" % bad)
	_drop([t])


# ---------------------------------------------------------------- [A8]

func _a8_group() -> void:
	var t := _ticker()
	if not _ticker_ok(t, "[A8]"):
		_drop([t])
		return
	var ev := _events()
	if ev == null:
		_drop([t])
		return
	await process_frame
	ev.feed({}, LOCAL)
	var s := _load(TICKER)
	var texts: Dictionary = s.get_script_constant_map().get("TEXTS", {})
	var w := String(texts.get("weather", "<no TEXTS entry>"))
	t.emit_beat("weather")
	_check(_kinds(ev.lines()) == ["weather"], "[A8] R-235-03 a weather beat reaches Events.lines() as one 'weather' line; got %s" % [_kinds(ev.lines())])
	_check(ev.lines().size() == 1 and String(ev.lines()[0]["text"]) == w, "[A8] the line holds TEXTS['weather'] (DRAFT-e1m-beat-text)")
	_check(ev.banner() == w, "[A8] R-104-01 / R-104-02 the beat sets the banner to its text")
	ev.advance(4.1)
	_check(ev.banner() == "", "[A8] R-104-02 the banner clears after 4 s")
	t.emit_beat("shipment")
	t.emit_beat("forward_base")
	_check(_kinds(ev.lines()) == ["weather"], "[A8] R-235-04 a shipment or a forward base adds no ticker line; got %s" % [_kinds(ev.lines())])
	for k in ["base_occupied", "fallback", "expansion"]:
		t.emit_beat(k)
	_check(_kinds(ev.lines()) == ["weather", "base_occupied", "fallback", "expansion"], "[A8] the other STUB beats reach the ticker too; got %s" % [_kinds(ev.lines())])
	_drop([ev, t])


# ---------------------------------------------------------------- [FEED]

func _feed_group() -> void:
	var t := _ticker()
	if not _ticker_ok(t, "[FEED]"):
		_drop([t])
		return
	var kinds := []
	t.connect("beat", func(k, _x): kinds.append(k))
	var o := {SP3: ENEMY, SP4: ENEMY, PLAIN: ENEMY}
	t.feed(_view(1, o), LOCAL)
	_check(kinds.is_empty() and t.beats_emitted() == 0, "[FEED] the first frame only records owners and emits nothing; got %s" % [kinds])
	o[SP3] = LOCAL
	t.feed(_view(2, o), LOCAL)
	_check(kinds == ["strongpoint_taken"], "[FEED] R-235-03 a strongpoint structure flipping to the local faction is one strongpoint_taken; got %s" % [kinds])
	t.feed(_view(3, o), LOCAL)
	_check(kinds == ["strongpoint_taken"], "[FEED] the same frame again is not a second beat; got %s" % [kinds])
	o[SP3] = ENEMY
	t.feed(_view(4, o), LOCAL)
	_check(kinds == ["strongpoint_taken", "strongpoint_lost"], "[FEED] R-235-03 flipping back is one strongpoint_lost; got %s" % [kinds])
	# negative control of the detector: a structure that is not a strongpoint, and a flip between two other factions
	o[PLAIN] = LOCAL
	t.feed(_view(5, o), LOCAL)
	o[PLAIN] = ENEMY
	t.feed(_view(6, o), LOCAL)
	_check(kinds == ["strongpoint_taken", "strongpoint_lost"], "[FEED] CONTROL: an ordinary structure flipping to and from us is no strongpoint beat; got %s" % [kinds])
	o[SP4] = OTHER
	t.feed(_view(7, o), LOCAL)
	_check(kinds == ["strongpoint_taken", "strongpoint_lost"], "[FEED] CONTROL: a strongpoint passing between two other factions is no beat; got %s" % [kinds])
	_check(t.beats_emitted() == 2 and t.last_beat().get("kind", "") == "strongpoint_lost", "[FEED] beats_emitted 2 and last_beat the lost one")
	_drop([t])

	# local_faction is the argument, not a constant: the same flip is 'lost' for faction 1
	var t1 := _ticker()
	var k1 := []
	t1.connect("beat", func(k, _x): k1.append(k))
	var o1 := {SP3: ENEMY, SP4: ENEMY}
	t1.feed(_view(1, o1), ENEMY)
	o1[SP3] = LOCAL
	t1.feed(_view(2, o1), ENEMY)
	_check(k1 == ["strongpoint_lost"], "[FEED] with local_faction 1 the owner flip 1 -> 0 of a strongpoint is strongpoint_lost; got %s" % [k1])
	_drop([t1])

	# a first frame that already shows us owning a strongpoint is still no beat
	var t2 := _ticker()
	var k2 := []
	t2.connect("beat", func(k, _x): k2.append(k))
	t2.feed(_view(1, {SP3: LOCAL, SP4: ENEMY}), LOCAL)
	_check(k2.is_empty(), "[FEED] a first frame with an own strongpoint is only recorded; got %s" % [k2])
	# GAP 2 (b): an own strongpoint whose structures row is gone from the next frame counts as lost
	t2.feed(_view(2, {SP4: ENEMY}), LOCAL)
	_check(k2 == ["strongpoint_lost"], "[FEED] G2 (b) an own strongpoint absent from the next frame's structures is one strongpoint_lost; got %s" % [k2])
	t2.feed(_view(3, {SP4: ENEMY}), LOCAL)
	_check(k2 == ["strongpoint_lost"], "[FEED] the lost strongpoint is not lost again on the next frame; got %s" % [k2])
	_drop([t2])

	# CONTROL: an enemy-owned strongpoint leaving the rows is no beat of ours
	var t3 := _ticker()
	var k3 := []
	t3.connect("beat", func(k, _x): k3.append(k))
	t3.feed(_view(1, {SP3: ENEMY, SP4: ENEMY}), LOCAL)
	t3.feed(_view(2, {SP4: ENEMY}), LOCAL)
	_check(k3.is_empty(), "[FEED] CONTROL: a strongpoint we did not own leaving the rows is no beat; got %s" % [k3])
	_drop([t3])


# ---------------------------------------------------------------- [SKIP]

func _skip_group() -> void:
	# TickerBeats may be absent (the built tree): Events alone still proves the Structure-line half, which is
	# green for an ordinary structure and red for a strongpoint (A8 beats a strongpoint today).
	var t: Node = null
	if ResourceLoader.exists(TICKER):
		t = _ticker()
		if not _ticker_ok(t, "[SKIP]"):
			_drop([t])
			return
	var ev := _events()
	if ev == null:
		_drop([t])
		return
	await process_frame
	var texts: Dictionary = {}
	if t != null:
		texts = _load(TICKER).get_script_constant_map().get("TEXTS", {})
	var o := {SP3: ENEMY, SP4: ENEMY, PLAIN: ENEMY}
	var full := _view(1, o)
	ev.feed(full, LOCAL)
	if t != null:
		t.feed(full, LOCAL)
	_check(ev.lines().is_empty(), "[SKIP] CONTROL: the first (full) frame is no beat")

	# the ordinary structure flips first: green on the built tree (A8 beats ordinary structures)
	_flip(ev, t, o, 2, PLAIN, LOCAL)
	_check(_kinds(ev.lines()) == ["captured"], "[SKIP] CONTROL R-104-01 an ordinary structure flipping to us is exactly one 'Structure captured' line; got %s" % [_kinds(ev.lines())])
	_flip(ev, t, o, 3, PLAIN, ENEMY)
	_check(_kinds(ev.lines()) == ["captured", "lost"], "[SKIP] CONTROL R-104-01 flipping back is exactly one 'Structure lost' line; got %s" % [_kinds(ev.lines())])
	if t != null:
		_check(t.beats_emitted() == 0, "[SKIP] CONTROL: an ordinary structure flip is no strongpoint beat; beats_emitted %d" % t.beats_emitted())

	# the strongpoint flips: no Structure line (G2 (b); red today because A8 beats it), then exactly one strongpoint line
	_flip(ev, t, o, 4, SP3, LOCAL)
	_check(_structure_lines(ev) == ["captured", "lost"], "[SKIP] G2 (b) a strongpoint flipping to us gives no 'Structure captured' line; got %s" % [_kinds(ev.lines())])
	_check(_kinds(ev.lines()) == ["captured", "lost", "strongpoint_taken"], "[SKIP] G2 (b) a strongpoint flipping to us is exactly one 'Strongpoint taken' line; got %s" % [_kinds(ev.lines())])
	_flip(ev, t, o, 5, SP3, ENEMY)
	_check(_structure_lines(ev) == ["captured", "lost"], "[SKIP] G2 (b) a strongpoint flipping away from us gives no 'Structure lost' line; got %s" % [_kinds(ev.lines())])
	_check(_kinds(ev.lines()) == ["captured", "lost", "strongpoint_taken", "strongpoint_lost"], "[SKIP] G2 (b) flipping back is exactly one 'Strongpoint lost' line; got %s" % [_kinds(ev.lines())])
	var l: Array = ev.lines()
	if l.size() == 4:
		_check(String(l[2]["text"]) == String(texts.get("strongpoint_taken", "<none>")) and String(l[3]["text"]) == String(texts.get("strongpoint_lost", "<none>")), "[SKIP] the strongpoint lines hold TEXTS['strongpoint_taken'] and TEXTS['strongpoint_lost']")
	# the owners were still remembered while skipping: an ordinary flip afterwards is judged against the right owner
	_flip(ev, t, o, 6, PLAIN, LOCAL)
	_check(_structure_lines(ev) == ["captured", "lost", "captured"], "[SKIP] after the skipped lines an ordinary flip is still exactly one 'captured' line; got %s" % [_kinds(ev.lines())])
	_drop([ev, t])

	# PIN a8-feed: a delta that itself carries the strongpoints key is skipped even when no full frame carried it
	var t2: Node = null
	if ResourceLoader.exists(TICKER):
		t2 = _ticker()
	var ev2 := _events()
	await process_frame
	var o2 := {SP3: ENEMY, SP4: ENEMY, PLAIN: ENEMY}
	var full2 := _view(1, o2)
	var bare := full2.duplicate()
	bare.erase("strongpoints")
	ev2.feed(bare, LOCAL)
	if t2 != null:
		t2.feed(full2, LOCAL)
	_flip(ev2, t2, o2, 2, SP4, LOCAL, {"strongpoints": full2["strongpoints"]})
	_check(_structure_lines(ev2).is_empty(), "[SKIP] PIN a8-feed a delta carrying frame['strongpoints'] gives no Structure line for a strongpoint id; got %s" % [_kinds(ev2.lines())])
	_check(_kinds(ev2.lines()) == ["strongpoint_taken"], "[SKIP] PIN a8-feed ... and exactly one 'Strongpoint taken' line; got %s" % [_kinds(ev2.lines())])
	_drop([ev2, t2])


func _structure_lines(ev: Node) -> Array:
	return _kinds(ev.lines()).filter(func(k): return k == "captured" or k == "lost")


# ---------------------------------------------------------------- [NOSOURCE]

func _nosource_group() -> void:
	var t := _ticker()
	if not _ticker_ok(t, "[NOSOURCE]"):
		_drop([t])
		return
	var kinds := []
	t.connect("beat", func(k, _x): kinds.append(k))
	var o := {SP3: ENEMY, SP4: ENEMY, PLAIN: ENEMY}
	var eco1 := {"doctrine": 1, "resources": {"food": 120.0, "metal": 40.0}}
	var eco2 := {"doctrine": 2, "resources": {"food": 10.0, "metal": 400.0, "energy": 5.0}}
	t.feed(_view(1, o, {"economy": eco1}), LOCAL)
	t.feed(_view(2, o, {"economy": eco2}), LOCAL)
	t.feed(_view(3, o, {"economy": eco1, "weather": {"kind": 1, "x": 10.0, "y": 20.0}}), LOCAL)
	_check(kinds.is_empty() and t.beats_emitted() == 0, "[NOSOURCE] G3 an economy key with resources and doctrine (and a weather key) never emits base_occupied, fallback, expansion or weather; got %s" % [kinds])
	# positive control inside the group: the same feed path does emit a strongpoint beat
	o[SP3] = LOCAL
	t.feed(_view(4, o, {"economy": eco2}), LOCAL)
	_check(kinds == ["strongpoint_taken"], "[NOSOURCE] CONTROL: the same feed path emits the one real beat; got %s" % [kinds])
	for k in kinds:
		_check(k in ["strongpoint_taken", "strongpoint_lost"], "[NOSOURCE] feed() emits only the two strongpoint kinds; got %s" % k)
	_drop([t])
