extends SceneTree

# T16 (docs/northstar/ROADMAP.md T16; S-245 in docs/bible/epics/E-16-client-camera-hud-and-world-view.md,
# rules R-245-01 and R-245-02; Q-245-01 and Q-245-02 closed): three additions on the F12 stack
# (autoload/bug_report_manager.gd, scenes/bug_report/bug_report_popup.gd).
#
# Contract these tests specify (the builder implements exactly this):
#   - BUFFER_SNAPSHOTS = 10 (ten 1-per-second snapshots) and COMMAND_BUFFER_SEC = 10.0 (R-245-02, window 10 s).
#   - metadata.json gains "seed" (int, SimSession.bridge().live_seed()) and "scene" (string, SceneRouter's
#     current scene name) (R-245-02).
#   - WORDS STORAGE = words.txt BESIDE the zip, not a re-zip (R-245-01). The zip is built before the player
#     types, and a re-zip would need the screenshot and snapshots kept alive until Send; a sidecar file does not.
#     Name: the zip's path with ".zip" replaced by ".words.txt", written next to BOTH copies (Downloads and
#     user://logs/reports). The words are the file's exact text. metadata.json never gets a "words" key.
#   - The popup has a TextEdit named "WordsField" and a Button named "SendButton" (both found by name, any
#     depth). Send with non-empty text writes the two sidecar files; Send with empty text writes nothing.
#     The popup still shows the Downloads path and "Also saved to" the reports path; the clipboard copy is
#     untouched (it happens in capture(), before the popup).
# Tests drive _build_zip / _process directly: capture() awaits frame_post_draw, which never fires headless.
# Fakes: a bridge with tactical_frame() and live_seed(), swapped into SimSession._bridge; SceneRouter's
# _current_scene_name set directly (it has no setter and go_to() fades and swaps scenes).
#
# Tests, by id:
#   W1  snapshot ring holds 10 after 12 s of simulated _process time; constants are 10 and 10.0.   (R-245-02)
#   W2  metadata.json carries seed and scene matching the fakes.                                   (R-245-02)
#   W3  popup Send with "the walkers froze" writes words.txt beside both zip copies.               (R-245-01)
#   W4  no words: no "words" key in metadata, Send with empty text writes no words file.           (R-245-01)
#   W5  the popup has the WordsField and a SendButton, and still names where the file went.        (R-245-01)
#   C1  positive control: zip layout keys unchanged (metadata.json base keys, tactical_snapshots/,
#       command_log.json) and the reader/fake work, so W1..W4 cannot fail on a broken harness.

const SimSession := preload("res://autoload/sim_session.gd")
const POPUP_SCENE := "res://scenes/bug_report/bug_report_popup.tscn"
const WORDS := "the walkers froze"
const FAKE_SEED := 424242
const FAKE_SCENE := "galaxy"

var _pass_count := 0
var _fail_count := 0
var _fail_msgs: Array[String] = []


class FakeBridge extends RefCounted:
	var tick := 0

	func tactical_frame() -> Dictionary:
		tick += 1
		return {"tick": tick, "units": [{"id": 1, "x": 1.0, "y": 2.0}], "structures": [], "objectives": []}

	func live_seed() -> int:
		return 424242

	func close_session() -> void:
		pass


func _initialize() -> void:
	await _run_tests()
	print("\n=== Bug Report Words/Seed Test Results ===")
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


func _read_zip_bytes(data: PackedByteArray) -> Dictionary:
	var out := {}
	var path := "user://t16_read.zip"
	var f := FileAccess.open(path, FileAccess.WRITE)
	f.store_buffer(data)
	f.close()
	var z := ZIPReader.new()
	if z.open(path) == OK:
		for n in z.get_files():
			out[n] = z.read_file(n)
		z.close()
	DirAccess.remove_absolute(path)
	return out


func _meta(files: Dictionary) -> Dictionary:
	if not files.has("metadata.json"):
		return {}
	var m: Variant = JSON.parse_string((files["metadata.json"] as PackedByteArray).get_string_from_utf8())
	return m if m is Dictionary else {}


func _find(root: Node, node_name: String) -> Node:
	return root.find_child(node_name, true, false)


func _label_texts(root: Node) -> String:
	var out := ""
	var stack: Array = [root]
	while not stack.is_empty():
		var n: Node = stack.pop_back()
		if n is Label:
			out += (n as Label).text + "\n"
		stack.append_array(n.get_children())
	return out


func _run_tests() -> void:
	var mgr = get_root().get_node("BugReportManager")
	var router = get_root().get_node("SceneRouter")
	var old_scene: String = router._current_scene_name
	var fake := FakeBridge.new()
	SimSession._bridge = fake
	router._current_scene_name = FAKE_SCENE

	# W1: ten snapshots in the ring after 12 s.
	_assert(int(mgr.BUFFER_SNAPSHOTS) == 10, "W1 (R-245-02): BUFFER_SNAPSHOTS is %d, expected 10" % int(mgr.BUFFER_SNAPSHOTS))
	_assert(is_equal_approx(float(mgr.COMMAND_BUFFER_SEC), 10.0), "W1 (R-245-02): COMMAND_BUFFER_SEC is %s, expected 10.0" % str(mgr.COMMAND_BUFFER_SEC))
	mgr.start_buffering()
	for i in 12:
		mgr._process(1.0)
	var ring: int = mgr.get_snapshot_buffer().size()
	_assert(ring == 10, "W1 (R-245-02): snapshot ring holds %d after 12 s of 1-per-second snapshots, expected 10" % ring)

	# C1 + W2: the zip, built from that ring.
	mgr.log_command({"kind": "move"})
	var files := _read_zip_bytes(mgr._build_zip(PackedByteArray()))
	var meta := _meta(files)
	for k in ["schema_version", "game_version", "os", "timestamp", "current_tick", "buffer_snapshots_count", "command_log_entries", "note"]:
		_assert(meta.has(k), "C1 control: metadata.json lost its existing key '%s' (keys: %s)" % [k, str(meta.keys())])
	var snaps := 0
	for n in files.keys():
		if String(n).begins_with("tactical_snapshots/snapshot_tick_"):
			snaps += 1
	_assert(snaps > 0, "C1 control: zip has no tactical_snapshots/snapshot_tick_N.json entry (entries: %s)" % str(files.keys()))
	_assert(files.has("command_log.json"), "C1 control: zip has no command_log.json (entries: %s)" % str(files.keys()))
	_assert(int(meta.get("seed", -1)) == FAKE_SEED, "W2 (R-245-02): metadata seed is %s, expected %d from live_seed()" % [str(meta.get("seed", "<missing>")), FAKE_SEED])
	_assert(str(meta.get("scene", "")) == FAKE_SCENE, "W2 (R-245-02): metadata scene is '%s', expected '%s' from SceneRouter" % [str(meta.get("scene", "<missing>")), FAKE_SCENE])

	# W4a: no words, no "words" key.
	_assert(not meta.has("words"), "W4 (R-245-01): metadata.json has a 'words' key on a report with no words")

	# Popup fixtures: two fake zip copies in a temp dir.
	var dir := ProjectSettings.globalize_path("user://t16_words")
	DirAccess.make_dir_recursive_absolute(dir.path_join("dl"))
	DirAccess.make_dir_recursive_absolute(dir.path_join("rep"))
	var dl_zip := dir.path_join("dl/bug_report_20261006_120000_001.zip")
	var rep_zip := dir.path_join("rep/bug_report_20261006_120000_001.zip")
	for p in [dl_zip, rep_zip]:
		var f := FileAccess.open(p, FileAccess.WRITE)
		f.store_string("zip")
		f.close()
	var dl_words := dl_zip.get_basename() + ".words.txt"
	var rep_words := rep_zip.get_basename() + ".words.txt"

	var popup: Node = (load(POPUP_SCENE) as PackedScene).instantiate()
	popup.setup(dl_zip, rep_zip)
	get_root().add_child(popup)
	await process_frame
	var field := _find(popup, "WordsField")
	var send := _find(popup, "SendButton")

	# W5: the field and Send exist; the where-it-went text stays.
	_assert(field is TextEdit, "W5 (R-245-01): popup has no TextEdit named 'WordsField'")
	_assert(send is Button, "W5 (R-245-01): popup has no Button named 'SendButton'")
	var texts := _label_texts(popup)
	_assert(texts.find(dl_zip) != -1 and texts.find("Also saved to: " + rep_zip) != -1, "W5 control: popup no longer says where the file went")

	# W4b: Send with empty text writes nothing.
	if send is Button:
		(send as Button).pressed.emit()
	_assert(not FileAccess.file_exists(dl_words) and not FileAccess.file_exists(rep_words), "W4 (R-245-01): Send with no words wrote a words file")

	# W3: Send with words writes both sidecars.
	if field is TextEdit and send is Button:
		(field as TextEdit).text = WORDS
		(send as Button).pressed.emit()
	_assert(FileAccess.file_exists(dl_words) and FileAccess.get_file_as_string(dl_words) == WORDS, "W3 (R-245-01): Downloads copy %s missing or not exactly '%s'" % [dl_words, WORDS])
	_assert(FileAccess.file_exists(rep_words) and FileAccess.get_file_as_string(rep_words) == WORDS, "W3 (R-245-01): reports copy %s missing or not exactly '%s'" % [rep_words, WORDS])

	popup.queue_free()
	for p in [dl_zip, rep_zip, dl_words, rep_words]:
		DirAccess.remove_absolute(p)
	mgr.start_buffering()
	SimSession._bridge = null
	router._current_scene_name = old_scene
