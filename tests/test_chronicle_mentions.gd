extends SceneTree

# GC2 client unit (docs/northstar/plans/2026-10-01-architect-rulings-2.md
# A53 and A66 (a)-(f); docs/bible/epics/E-09-chronicle.md R-069-07, S-069).
# The sim now sends each chronicle entry's finished prose and the names in it:
#   text, mentions[{start,len,kind,id:int}], expanded_text, expanded_mentions
# with Unicode code point offsets into that string as sent (A66b). The panel
# (scenes/world/chronicle_scroll_panel.gd load_frame) shows `text` as sent:
# its rebuild of prose from fragment ids leaves the live path when the entry
# carries `text` (A66a), and it hands chronicle_entry.gd / chronicle_entry_
# expansion.gd the client's existing mention shape {kind, start, end, id:String}
# (end = start + len) plus expanded_form / expanded_mentions. A click on a link
# emits mention_clicked(kind, id) with the exact id the sim sent (A66c).
#
# Scope notes.
# - Links are word-granular by design (chronicle_entry.gd wraps whole printed
#   words), so the word-level link check strips edge punctuation; the exact
#   code point check is on the converted data the panel hands the entry.
# - A66d (faction click centres on the centroid of its systems at the Regional
#   distance) is galaxy-side and NOT tested here. Known gap, see report: the
#   standalone chronicle scene has no consumer of mention_clicked; the only
#   handler is time_jump_sequencer.gd _on_scroll_mention_clicked (legacy
#   string-keyed _regions_state path, 1.5 s camera move, no Regional distance).
# - Frames without `text` (fixtures, older frames) keep the fragment rebuild,
#   so tests/test_chronicle_scroll.gd is untouched.
#
# Controls: the checkers below are run against a planted off-by-one span and a
# planted UTF-8 byte offset and must reject both (control_* functions).
#
# Run: xvfb-run -a godot --headless --path . -s res://tests/test_chronicle_mentions.gd

const SCENE_PATH := "res://scenes/world/chronicle_scroll_panel.tscn"
const DASHES := "— — — — —"  # five em dashes: 15 UTF-8 bytes, 5 code points

var _pass_count := 0
var _fail_count := 0
var _fail_msgs: Array[String] = []
var _root: Node
var _clicks: Array = []


func _initialize() -> void:
	await _run_tests()
	print("\n=== Chronicle Mentions Test Results ===")
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
	_control_off_by_one_rejected()
	_control_bytes_vs_code_points()

	var packed = load(SCENE_PATH)
	_assert(packed is PackedScene, "cannot load %s" % SCENE_PATH)
	if not (packed is PackedScene):
		return
	_root = (packed as PackedScene).instantiate()
	get_root().add_child(_root)
	await process_frame
	await process_frame
	for m in ["load_frame", "skip_all", "set_snapshot"]:
		if not _root.has_method(m):
			_assert(false, "panel root missing method " + m)
			return
	_root.mention_clicked.connect(func(kind: String, id: String): _clicks.append([kind, id]))

	await _check_synthetic_frame()
	await _check_live_frame()


# ---- synthetic frame ---------------------------------------------------------

func _synthetic_frame() -> Dictionary:
	# Numbers go through JSON text so ints arrive as floats, exactly as the
	# bridge delivers them (a client that does str(id) would show "7.0").
	var t_a := "It held %s and held on until Brant of Kessmere signed for the Sable Court." % DASHES
	var t_b := "Nothing of note was named, so nothing here is a link."
	var t_c := "Kessmere fell quiet."
	var x_c := "Kessmere fell quiet — then louder — and the Sable Court noted it."
	var frame := {
		"type": "chronicle",
		"jump": {"from_tick": 0, "to_tick": 50},
		"entries": [
			{"id": 1, "start_tick": 1, "end_tick": 9, "category": 2, "cluster_type": 0,
				"refs": {"regions": [], "factions": []}, "fragment": 1, "fragment_ids": [1, 6, 15],
				"significance": 1.0, "text": t_a, "mentions": [
					_span(t_a, "Kessmere", "region", 7), _span(t_a, "Sable Court", "faction", 3)],
				"expanded_text": t_a + " Later.", "expanded_mentions": [
					_span(t_a, "Kessmere", "region", 7), _span(t_a, "Sable Court", "faction", 3)]},
			{"id": 2, "start_tick": 10, "end_tick": 19, "category": 5, "cluster_type": 0,
				"refs": {"regions": [], "factions": []}, "fragment": 287, "fragment_ids": [287, 291, 299],
				"significance": 1.0, "text": t_b, "mentions": [],
				"expanded_text": t_b + " Still none.", "expanded_mentions": []},
			{"id": 3, "start_tick": 20, "end_tick": 29, "category": 5, "cluster_type": 0,
				"refs": {"regions": [], "factions": []}, "fragment": 251, "fragment_ids": [251, 255, 261],
				"significance": 1.0, "text": t_c, "mentions": [_span(t_c, "Kessmere", "region", 12)],
				"expanded_text": x_c, "expanded_mentions": [
					_span(x_c, "Kessmere", "region", 12), _span(x_c, "Sable Court", "faction", 3)]},
		],
	}
	return JSON.parse_string(JSON.stringify(frame))


# What the sim would send: code point offsets (Godot String.find is by code point).
func _span(text: String, name: String, kind: String, id: int) -> Dictionary:
	var s := text.find(name)
	return {"start": s, "len": name.length(), "kind": kind, "id": id}


func _check_synthetic_frame() -> void:
	var frame := _synthetic_frame()
	var src: Array = frame["entries"]
	_root.set_snapshot({"regions": [], "factions": []})
	_root._entries.clear()  # load_frame leaves freed nodes from the _ready() live load here (report, Q-GC2C-03)
	_root.load_frame(frame)
	await process_frame
	_root.skip_all()
	await process_frame
	await process_frame

	var entries: Dictionary = _root._entries
	_assert(entries.size() == 3, "synthetic frame: %d entry nodes, expected 3" % entries.size())
	var qa: Array = _root.qa_state().get("entries", [])
	for i in range(src.size()):
		var e: Dictionary = src[i]
		var key := str(int(e["id"]))
		# text as sent (A66a); the fragment rebuild must not replace it
		if i < qa.size():
			_assert(str(qa[i].get("text", "")) == e["text"],
				"entry %s: qa_state text = %s, expected the sim's text as sent: %s" % [key, qa[i].get("text", ""), e["text"]])
		_assert(entries.has(key), "entry %s has no node" % key)
		if not entries.has(key):
			continue
		var node: Node = entries[key]
		var data: Dictionary = node.get_entry_data()
		_assert(str(data.get("base_form", "")) == e["text"], "entry %s: base_form is not the sim's text as sent" % key)
		_check_converted(key, "mentions", e["text"], e["mentions"], data.get("mentions", []))
		_assert(str(data.get("expanded_form", "")) == e["expanded_text"], "entry %s: expanded_form is not expanded_text as sent" % key)
		_check_converted(key, "expanded_mentions", e["expanded_text"], e["expanded_mentions"], data.get("expanded_mentions", []))

		# links in the printed label: only the named words, nothing else
		var label := _label_of(node)
		var bb: String = label.text if label != null else ""
		var links := _linked_texts(bb)
		var want := {}
		for m in e["mentions"]:
			want["%s:%d" % [m["kind"], int(m["id"])]] = (e["text"] as String).substr(int(m["start"]), int(m["len"]))
		_assert(links.size() == want.size(), "entry %s: %d distinct links in the printed text, expected %d (%s vs %s)" % [key, links.size(), want.size(), links.keys(), want.keys()])
		for k in want:
			_assert(links.has(k) and _strip_edges(links[k]) == want[k],
				"entry %s: link %s covers '%s', expected '%s'" % [key, k, links.get(k, "<none>"), want[k]])
		if e["mentions"].is_empty():
			_assert("[url" not in bb, "entry %s has no mentions but its text carries a link: %s" % [key, bb])

	# clicks: every link in the printed entries reports the exact kind and id
	_clicks.clear()
	var expect := {"region:7": true, "faction:3": true, "region:12": true}
	for key in entries:
		var label := _label_of(entries[key])
		for meta in _linked_texts(label.text if label != null else ""):
			label.meta_clicked.emit(meta)
	var got := {}
	for c in _clicks:
		got["%s:%s" % [c[0], c[1]]] = true
	_assert(got == expect, "clicking every link emitted %s, expected exactly %s (ids are the sim's integers as strings, no '7.0')" % [got.keys(), expect.keys()])

	# expansion: same shape, clicks reach the panel signal
	_root._show_expansion("3")
	await process_frame
	var xl := _label_in(_root._expansion_overlay)
	_assert(xl != null, "expansion for entry 3 did not open a label")
	if xl != null:
		var xlinks := _linked_texts(xl.text)
		_assert(xlinks.has("region:12") and xlinks.has("faction:3") and xlinks.size() == 2,
			"expansion links = %s, expected region:12 and faction:3" % [xlinks.keys()])
		_assert(_strip_edges(xlinks.get("faction:3", "")) == "Sable Court", "expansion faction link covers '%s'" % xlinks.get("faction:3", ""))
		_clicks.clear()
		for meta in xlinks:
			xl.meta_clicked.emit(meta)
		var xgot := {}
		for c in _clicks:
			xgot["%s:%s" % [c[0], c[1]]] = true
		_assert(xgot == {"region:12": true, "faction:3": true}, "expansion clicks emitted %s" % [xgot.keys()])
	_root._close_expansion()


func _check_converted(key: String, field: String, text: String, sent: Array, got: Array) -> void:
	_assert(got.size() == sent.size(), "entry %s: %s has %d items, expected %d" % [key, field, got.size(), sent.size()])
	if got.size() != sent.size():
		return
	for i in range(sent.size()):
		var s: Dictionary = sent[i]
		var g: Dictionary = got[i]
		var start := int(s["start"])
		var end := start + int(s["len"])
		_assert(int(g.get("start", -1)) == start and int(g.get("end", -1)) == end,
			"entry %s %s[%d]: start/end = %s/%s, expected %d/%d (code points, end = start + len)" % [key, field, i, g.get("start"), g.get("end"), start, end])
		_assert(typeof(g.get("id")) == TYPE_STRING and g.get("id") == str(int(s["id"])),
			"entry %s %s[%d]: id = %s (type %d), expected String '%d'" % [key, field, i, g.get("id"), typeof(g.get("id")), int(s["id"])])
		_assert(g.get("kind", "") == s["kind"], "entry %s %s[%d]: kind = %s, expected %s" % [key, field, i, g.get("kind"), s["kind"]])
		_assert(_slice_is_name(text, int(g.get("start", -1)), int(g.get("end", -1)) - int(g.get("start", -1))),
			"entry %s %s[%d]: [%s,%s) does not read as a whole name in the text" % [key, field, i, g.get("start"), g.get("end")])


# ---- live frame from the real pipe ------------------------------------------

func _check_live_frame() -> void:
	var CBridge = load("res://autoload/c_bridge.gd")
	var bridge = CBridge.new()
	var ok: bool = bridge.load_chronicle_live(1, CBridge.DEFAULT_N_REGIONS, CBridge.DEFAULT_FEATURES)
	_assert(ok, "live: load_chronicle_live failed: %s" % bridge.last_error())
	if not ok:
		return
	var frame: Dictionary = bridge.chronicle_frame()
	var src: Array = frame.get("entries", [])
	_assert(src.size() > 0, "live: the jump produced no chronicle entries")
	_root.set_snapshot(bridge.chronicle_snapshot())
	_root._entries.clear()  # see _check_synthetic_frame
	_root.load_frame(frame.duplicate(true))
	await process_frame
	_root.skip_all()
	await process_frame
	await process_frame

	var with_mentions := 0
	var non_ascii_before_mention := false
	var shown := 0
	for e in src:
		var text: String = str(e.get("text", ""))
		_assert(e.get("mentions", null) is Array and e.get("expanded_mentions", null) is Array,
			"live: entry %s has no mentions / expanded_mentions arrays" % e.get("id"))
		if text == "":
			continue  # sim sent no prose for this entry (see report, Q-GC2C-02)
		var key := str(int(e["id"]))
		var node = _root._entries.get(key)
		_assert(node != null, "live: entry %s has no node" % key)
		if node == null:
			continue
		shown += 1
		var data: Dictionary = node.get_entry_data()
		_assert(str(data.get("base_form", "")) == text, "live: entry %s shows other prose than the sim's text" % key)
		_check_converted(key, "mentions", text, e["mentions"], data.get("mentions", []))
		_check_converted(key, "expanded_mentions", str(e.get("expanded_text", "")), e["expanded_mentions"], data.get("expanded_mentions", []))
		if not (e["mentions"] as Array).is_empty():
			with_mentions += 1
			var first := int(e["mentions"][0]["start"])
			for m in e["mentions"]:
				var s := int(m["start"])
				if s != text.substr(0, s).to_utf8_buffer().size():
					non_ascii_before_mention = true
		var label := _label_of(node)
		var links := _linked_texts(label.text if label != null else "")
		_assert(links.size() == _distinct_ids(e["mentions"]),
			"live: entry %s shows %d distinct links, expected %d" % [key, links.size(), _distinct_ids(e["mentions"])])
		if (e["mentions"] as Array).is_empty():
			_assert(links.is_empty(), "live: entry %s has no mentions but shows links" % key)
	_assert(shown > 0, "live: no entry with text reached the panel")
	_assert(with_mentions > 0, "live: no entry in a real 50-tick jump carries any mention")
	_assert(non_ascii_before_mention,
		"live: seed 1 no longer has a mention after a multi-byte character; the code point check is not exercised, pick another seed")


# ---- helpers and controls ----------------------------------------------------

func _distinct_ids(mentions: Array) -> int:
	var d := {}
	for m in mentions:
		d["%s:%d" % [m["kind"], int(m["id"])]] = true
	return d.size()


func _label_of(node: Node) -> RichTextLabel:
	return _label_in(node)


func _label_in(node: Node) -> RichTextLabel:
	var found := node.find_children("*", "RichTextLabel", true, false)
	return found[0] as RichTextLabel if found.size() > 0 else null


# {"kind:id": "word word"} from [url=kind:id]...[color]word[/color]...[/url] pieces.
func _linked_texts(bbcode: String) -> Dictionary:
	var out := {}
	var rx := RegEx.new()
	rx.compile("\\[url=([a-z]+:[0-9.]+)\\](.*?)\\[/url\\]")
	var tags := RegEx.new()
	tags.compile("\\[/?color[^\\]]*\\]")
	for m in rx.search_all(bbcode):
		var k := m.get_string(1)
		var plain := tags.sub(m.get_string(2), "", true)
		out[k] = (out[k] + " " + plain) if out.has(k) else plain
	return out


func _strip_edges(s: String) -> String:
	var a := 0
	var b := s.length()
	while a < b and not _is_letter(s[a]):
		a += 1
	while b > a and not _is_letter(s[b - 1]):
		b -= 1
	return s.substr(a, b - a)


func _is_letter(c: String) -> bool:
	return c.to_lower() != c.to_upper()


# A span reads as a whole name: letters at both ends, not inside a word.
func _slice_is_name(text: String, start: int, n: int) -> bool:
	if start < 0 or n <= 0 or start + n > text.length():
		return false
	if not (_is_letter(text[start]) and _is_letter(text[start + n - 1])):
		return false
	if start > 0 and _is_letter(text[start - 1]):
		return false
	if start + n < text.length() and _is_letter(text[start + n]):
		return false
	return true


func _control_off_by_one_rejected() -> void:
	var t := "It held — and Kessmere signed."
	var s := t.find("Kessmere")
	_assert(_slice_is_name(t, s, 8), "control: the checker rejects a correct span")
	_assert(not _slice_is_name(t, s + 1, 8), "control: the checker accepts a span shifted by +1")
	_assert(not _slice_is_name(t, s - 1, 8), "control: the checker accepts a span shifted by -1")
	_assert(not _slice_is_name(t, s, 7) and not _slice_is_name(t, s, 9), "control: the checker accepts a span one too short or long")


func _control_bytes_vs_code_points() -> void:
	var t := "It held %s and Kessmere signed." % DASHES
	var cp := t.find("Kessmere")
	var bytes := t.substr(0, cp).to_utf8_buffer().size()
	_assert(bytes == cp + 10, "control: five em dashes should put the byte offset 10 past the code point offset (cp %d, bytes %d)" % [cp, bytes])
	_assert(_slice_is_name(t, cp, 8), "control: the code point span reads as the name")
	_assert(not _slice_is_name(t, bytes, 8), "control: the UTF-8 byte offset must not read as the name")
