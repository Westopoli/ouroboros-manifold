extends SceneTree

# Piece C3-G3 (docs/northstar/plans/2026-09-28-gap-fix-and-migration-plan.md, "Decisions" and G3;
# E-16 R-110-01): the main menu offers New Game (the bible says "New Campaign"; the
# label wording is not pinned here), Continue, Era Library, Settings and Quit -- and
# nothing else. Replay Tutorial and the "Have an access key?" hint leave the menu.
#
# Era Library: R-110-01 lists only New Campaign, Continue, Settings and Quit, while the
# gap-fix plan decision keeps Era Library (and makes its data real under E1). This
# test follows the plan decision; the rule text is out of date (flagged to the Architect).

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

	_assert(_any_contains(texts, ["new game", "new campaign"]), "G3: no New Game / New Campaign item")
	_assert(_any_contains(texts, ["continue"]), "G3: no Continue item")
	_assert(_any_contains(texts, ["era library"]), "G3: no Era Library item (kept by the gap-fix plan decision)")
	_assert(_any_contains(texts, ["settings"]), "G3: no Settings item")

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
