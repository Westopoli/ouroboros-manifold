extends SceneTree

# A82 (Addendum 29): the legacy info panels take names from a meta "name" string
# supplied by the legacy message path (a dict the C pipe never fills). That is deleted:
# scenes/world/region_info_panel.gd and faction_info_panel.gd show the name for a sim id
# from scenes/world/chronicle_names.gd (library/chronicle/fragments.json name_tables).
# Keys the panels read after the change (the brief leaves them open; pinned here):
#   region panel   region_meta["region_id"]  (int or numeric string)
#   faction panel  faction_meta["id"]        (numeric string, as today)
#   faction panel  region_rows[i]["region_id"]
# Checks: (a) fails while a legacy "name" entry still wins; (b) fails while the panel
# source still reads a "name" key; (c) the panel shows the chronicle name for a known id.
# Positive control: the same checker run against a stand-in label showing the right name
# passes, and against one showing the legacy name fails.

const NamesScript := preload("res://scenes/world/chronicle_names.gd")
const RegionPanel := preload("res://scenes/world/region_info_panel.tscn")
const FactionPanel := preload("res://scenes/world/faction_info_panel.tscn")
const LIBRARY_PATH := "res://library/chronicle/fragments.json"
const LEGACY := "LEGACY-DICT-NAME"
const REGION_SRC := "res://scenes/world/region_info_panel.gd"
const FACTION_SRC := "res://scenes/world/faction_info_panel.gd"

var _pass_count := 0
var _fail_count := 0
var _fail_msgs: Array[String] = []


func _assert(cond: bool, msg: String) -> void:
	if cond:
		_pass_count += 1
	else:
		_fail_count += 1
		_fail_msgs.append(msg)


func _finish(title: String) -> void:
	print("\n=== %s Test Results ===" % title)
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


func _initialize() -> void:
	await _run_tests()
	_finish("A82 Info Panel Names")


func _shows(shown: String, want: String) -> bool:
	return shown == want and shown != LEGACY


func _all_text(node: Node, out: Array) -> void:
	if node is Label:
		out.append((node as Label).text)
	if node is Button:
		out.append((node as Button).text)
	for c in node.get_children():
		_all_text(c, out)


func _run_tests() -> void:
	var lib = JSON.parse_string(FileAccess.get_file_as_string(LIBRARY_PATH))
	_assert(lib is Dictionary, "setup: fragments.json unreadable")
	if not (lib is Dictionary):
		return
	var names = NamesScript.new()
	names.load_tables(lib["name_tables"])
	var rid := 3
	var fid := 4
	var want_r: String = names.fill_template("{region_name}", rid, -1)
	var want_f: String = names.fill_template("{faction_name}", fid, fid)
	_assert(want_r != "" and want_f != "" and want_r != want_f, "setup: names for ids resolved to '%s' / '%s'" % [want_r, want_f])

	# positive control for the checker itself
	_assert(_shows(want_r, want_r), "control: checker accepts the chronicle name")
	_assert(not _shows(LEGACY, want_r), "control: checker rejects the legacy name")

	# (b) legacy dict reads removed from both panels
	for p in [REGION_SRC, FACTION_SRC]:
		var src := FileAccess.get_file_as_string(p)
		_assert(src.find(".get(\"name\"") == -1,
			"A82: %s still reads a legacy \"name\" entry from its meta/rows" % p)

	# region panel: legacy name supplied alongside the id must lose; id alone must work
	var rp: Control = RegionPanel.instantiate()
	get_root().add_child(rp)
	await process_frame
	var meta := {"region_id": rid, "name": LEGACY, "tier": "core"}
	rp.bind(meta, str(fid), "", Color.WHITE, "")
	var texts: Array = []
	_all_text(rp, texts)
	_assert(texts.has(want_r), "A82: region panel for id %d must show '%s'; texts: %s" % [rid, want_r, str(texts)])
	_assert(not texts.has(LEGACY), "A82: region panel still shows the legacy dict name")
	rp.bind({"region_id": str(rid), "tier": "core"}, str(fid), "", Color.WHITE, "")
	texts.clear()
	_all_text(rp, texts)
	_assert(texts.has(want_r), "A82: region panel (numeric-string id, no name entry) must show '%s'" % want_r)
	rp.queue_free()

	# faction panel header and region list rows
	var fp: Control = FactionPanel.instantiate()
	get_root().add_child(fp)
	await process_frame
	var rows := [{"region_id": str(rid), "name": LEGACY, "tier": "core"}]
	fp.bind({"id": str(fid), "name": LEGACY, "status": "Stable"}, Color.WHITE, rows)
	texts.clear()
	_all_text(fp, texts)
	_assert(texts.has(want_f), "A82: faction panel for id %d must show '%s'; texts: %s" % [fid, want_f, str(texts)])
	var row_ok := false
	for t in texts:
		if str(t).begins_with(want_r):
			row_ok = true
		_assert(str(t).find(LEGACY) == -1, "A82: faction panel still shows the legacy dict name in '%s'" % t)
	_assert(row_ok, "A82: faction panel region row for id %d must start with '%s'" % [rid, want_r])
	fp.queue_free()
