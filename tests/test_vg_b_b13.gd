extends SceneTree

# Piece B13 (docs/northstar/plans/2026-10-07-visible-game-spec.md rev 4, lane B):
# the Unknown faction label. Ruling A48 item 6
# (docs/northstar/plans/2026-10-01-architect-rulings-2.md): "An unknown faction
# id is an error reported in qa_state and shown as "Unknown"; the text
# "[faction]" never reaches the screen." Proves S-106/S-107 (E-16) labels for
# the approved field look (origin/push/galaxy-field shell_renderer.gd label
# path: Label3D per faction under the ShellRenderer node).
#
# Seam: the live galaxy_view scene given a snapshot whose region 0 is owned by
# a faction id absent from snapshot.factions. Label texts are found by walking
# the scene tree (any Label3D / Label under ShellRenderer), so the test does not fix the renderer's
# internal shape. The qa_state error key is NOT fixed by the spec; this test
# requires some top-level qa_state key containing "unknown_faction" (open
# question reported to the Architect).

const SCENE_PATH := "res://scenes/galaxy/galaxy_view.tscn"
const FIXTURE_PATH := "res://tests/transport/fixtures/snapshot_seed1_tick10.json"
const UNKNOWN_OWNER := 9999

var _pass := 0
var _fail := 0
var _msgs: Array[String] = []


func _initialize() -> void:
	await _run()
	print("\n=== B13 Unknown faction label ===\nPASS: %d  FAIL: %d" % [_pass, _fail])
	for m in _msgs:
		print("  - " + m)
	print("=== RED ===" if _fail > 0 else "=== GREEN ===")
	quit(1 if _fail > 0 else 0)


func _assert(cond: bool, msg: String) -> void:
	if cond:
		_pass += 1
	else:
		_fail += 1
		_msgs.append(msg)


func _label_texts(n: Node, out: Array) -> void:
	if n is Label3D:
		out.append((n as Label3D).text)
	elif n is Label:
		out.append((n as Label).text)
	for c in n.get_children():
		_label_texts(c, out)


func _run() -> void:
	var f := FileAccess.open(FIXTURE_PATH, FileAccess.READ)
	_assert(f != null, "fixture missing: " + FIXTURE_PATH)
	if f == null:
		return
	var snap: Dictionary = JSON.parse_string(f.get_as_text())
	var known: Array = []
	for fac in snap.get("factions", []):
		known.append(int(fac.get("id", fac.get("i", -1))) if fac is Dictionary else int(fac))
	_assert(not known.has(UNKNOWN_OWNER), "fixture precondition: %d must not be a known faction id" % UNKNOWN_OWNER)
	snap["regions"][0]["owner"] = UNKNOWN_OWNER

	var packed = load(SCENE_PATH)
	_assert(packed is PackedScene, "cannot load " + SCENE_PATH)
	if not (packed is PackedScene):
		return
	var root: Node = (packed as PackedScene).instantiate()
	get_root().add_child(root)
	await process_frame
	await process_frame
	root.set_snapshot(snap)
	await process_frame
	await process_frame

	var shell: Node = root.find_child("ShellRenderer", true, false)
	_assert(shell != null, "A48-6: no ShellRenderer node under galaxy_view (spec node name; piece B4 wiring/B3b labels not built)")
	if shell == null:
		root.queue_free()
		return
	var texts: Array = []
	_label_texts(shell, texts)

	# Positive control: the renderer draws faction labels at all (the known
	# factions of the fixture), so absence of "[faction]" cannot pass on an
	# empty tree.
	_assert(texts.size() > 0,
		"S-106/R-106-03 A48-6: galaxy_view draws no faction Label3D/Label at all (ShellRenderer labels, piece B3b, not wired); an unknown owner id cannot be labelled")
	_assert(texts.has("Unknown"),
		"A48-6: an owner id %d absent from snapshot.factions must be labelled exactly \"Unknown\"; label texts = %s" % [UNKNOWN_OWNER, str(texts)])
	for t in texts:
		_assert(not str(t).contains("[faction]"),
			"A48-6: the text \"[faction]\" reached the screen: %s" % str(t))
		_assert(str(t) != "", "A48-6: an empty faction label is on screen")

	var state: Dictionary = root.qa_state()
	var has_key := false
	for k in state.keys():
		if str(k).contains("unknown_faction"):
			has_key = true
			var v = state[k]
			var reported: bool = (v is Array and (v as Array).size() > 0) or (not (v is Array) and v != null and v != 0 and v != false)
			_assert(reported,
				"A48-6: qa_state[%s] must report the unknown faction (non-empty / non-zero)" % str(k))
	_assert(has_key, "A48-6: qa_state has no key containing \"unknown_faction\" reporting the unknown id (keys: %s)" % str(state.keys()))

	# Control: the same scene with every owner known reports no unknown.
	var clean: Dictionary = snap.duplicate(true)
	clean["regions"][0]["owner"] = 0
	root.set_snapshot(clean)
	await process_frame
	await process_frame
	var texts2: Array = []
	_label_texts(shell, texts2)
	_assert(not texts2.has("Unknown"),
		"A48-6 control: with all owners known no \"Unknown\" label may remain; texts = %s" % str(texts2))
	root.queue_free()
