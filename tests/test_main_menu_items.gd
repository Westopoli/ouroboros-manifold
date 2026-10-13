extends SceneTree

# Piece C3-G3 (docs/northstar/plans/2026-09-28-gap-fix-and-migration-plan.md, "Decisions" and G3;
# E-16 R-110-01; Architect ruling 2026-10-01 addendum 4 A9): the main menu is exactly five
# entries -- New Campaign, Continue, Era Library, Settings, Quit -- and nothing else. The
# first label is "New Campaign" (the old "New Game" is no longer accepted). Replay Tutorial and
# the "Have an access key?" hint leave the menu. Labels are compared case-insensitively
# (the menu draws its entries in capitals); the wording is exact.
#
# An entry is a visible Button, or a visible menu-item row (an HBoxContainer
# holding an accent bar and a Label, which is what _create_menu_item builds, dimmed or not);
# the visible set must equal the five.

const SCENE_PATH := "res://scenes/main_menu/main_menu.tscn"
const SCRIPT_PATH := "res://scenes/main_menu/main_menu.gd"

var _pass_count := 0
var _fail_count := 0
var _fail_msgs: Array[String] = []
var _completed := false


func _initialize() -> void:
	await _run_tests()
	_assert(_completed, "the main-menu checks did not run to the end (a script error aborted them)")
	print("\n=== Main Menu Items Test Results ===")
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


func _texts(node: Node, out: Array[String]) -> void:
	if node is Label:
		out.append((node as Label).text.to_lower())
	elif node is Button:
		out.append((node as Button).text.to_lower())
	elif node is RichTextLabel:
		out.append((node as RichTextLabel).text.to_lower())
	for c in node.get_children():
		_texts(c, out)


func _entries(node: Node, out: Array[String]) -> void:
	if node is Control and not (node as Control).is_visible_in_tree():
		return
	if node is Button:
		out.append((node as Button).text.strip_edges().to_lower())
	elif node is HBoxContainer:
		var has_accent := false
		var label: Label = null
		for c in node.get_children():
			if c is ColorRect:
				has_accent = true
			elif c is Label and label == null:
				label = c as Label
		if has_accent and label != null:
			out.append(label.text.strip_edges().to_lower())
	for c in node.get_children():
		_entries(c, out)


func _any_contains(texts: Array[String], needles: Array) -> bool:
	for t in texts:
		for n in needles:
			if t.find(n) != -1:
				return true
	return false


func _run_tests() -> void:
	var scene: Node = (load(SCENE_PATH) as PackedScene).instantiate()
	get_root().add_child(scene)
	await process_frame
	await process_frame
	var texts: Array[String] = []
	_texts(scene, texts)

	# Positive control: the detector sees the menu at all.
	_assert(_any_contains(texts, ["quit"]), "control: the text scan found no QUIT item, so the absences below prove nothing; texts: %s" % str(texts))

	_assert(texts.has("new campaign"), "G3: no item labelled exactly 'New Campaign'; texts: %s" % str(texts))
	_assert(not texts.has("new game") and not _any_contains(texts, ["new game"]), "G3: the old 'New Game' label is still in the main menu")
	_assert(_any_contains(texts, ["continue"]), "G3: no Continue item")
	_assert(_any_contains(texts, ["era library"]), "G3: no Era Library item (kept by the gap-fix plan decision)")
	_assert(_any_contains(texts, ["settings"]), "G3: no Settings item")

	var entries: Array[String] = []
	_entries(scene, entries)
	# TD-T3-menu-era-toggle: the Era toggle ("era: space" / "era: ground") sits beside the five.
	var toggles: Array[String] = []
	var rest: Array[String] = []
	for e in entries:
		if e.begins_with("era: "):
			toggles.append(e)
		else:
			rest.append(e)
	_assert(toggles.size() == 1 and (toggles[0] == "era: space" or toggles[0] == "era: ground"),
		"G3/3e: exactly one Era toggle entry (era: space / era: ground) beside the five; got %s" % str(toggles))
	entries = rest
	entries.sort()
	# TD-VG-F-1: the spec's six; W4 added MULTIPLAYER between ERA LIBRARY and SETTINGS.
	var want := ["continue", "era library", "multiplayer", "new campaign", "quit", "settings"]
	_assert(entries == want, "G3: the visible menu entries are %s, expected exactly %s" % [str(entries), str(want)])

	_assert(scene.find_child("ReplayTutorialButton", true, false) == null, "G3: ReplayTutorialButton still in the main menu")
	_assert(not _any_contains(texts, ["replay tutorial", "tutorial"]), "G3: a 'tutorial' text is still in the main menu: %s" % str(texts))
	_assert(not _any_contains(texts, ["access key"]), "G3: the 'Have an access key?' hint is still in the main menu: %s" % str(texts))

	var src := FileAccess.get_file_as_string(SCRIPT_PATH)
	_assert(src != "", "cannot read " + SCRIPT_PATH)
	_assert(src.find("reset_for_replay") == -1 and src.find("_on_replay_tutorial_pressed") == -1,
		"G3: main_menu.gd still carries the Replay Tutorial handler")

	scene.queue_free()
	await process_frame
	_completed = true
