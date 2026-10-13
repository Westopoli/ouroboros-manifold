extends SceneTree

# Piece VG-B9 (docs/northstar/plans/2026-10-07-visible-game-spec.md rev 4 lane B,
# "B9 time-jump renderer (handoff from G-timejump)";
# docs/northstar/plans/preflight_2026-10-07/3-galaxy-field.md "A second galaxy
# renderer"). S-069 (E-09: the map changes on the left while the scroll writes
# on the right) shares the galaxy renderer of S-106/S-107 (E-16): the chronicle
# and time jump render through res://scenes/galaxy/galaxy_view.tscn, and the old
# res://scenes/shared/world_view/world_view_shell.tscn path is retired from
# scenes/world/time_jump_sequencer.gd behind a parity test: every call the
# sequencer made on the old shell is answered by the galaxy renderer.
# No Westley threshold here, so no *_park_* file.

const SEQ_PATH := "res://scenes/world/time_jump_sequencer.gd"
const SEQ_SCENE := "res://scenes/world/time_jump_sequencer.tscn"
const GALAXY_SCENE := "res://scenes/galaxy/galaxy_view.tscn"
const OLD_SHELL := "scenes/shared/world_view/world_view_shell"

# Every method time_jump_sequencer.gd calls on its renderer (read from main,
# lines 140-618) plus the two signals it listens to.
const PARITY_METHODS := ["add_region_node", "update_region_node", "set_territory",
	"update_territory", "remove_territory", "add_connection", "flash_military_activity",
	"flash_conflict", "highlight_region", "clear_highlight", "move_camera_to_region",
	"move_camera_to_regions", "move_camera_to_overview", "start_auto_camera",
	"stop_auto_camera"]
const PARITY_SIGNALS := ["camera_move_completed", "region_clicked", "empty_space_clicked"]

var _pass_count := 0
var _fail_count := 0
var _fail_msgs: Array[String] = []


func _initialize() -> void:
	await _run_tests()
	print("\n=== VG-B9 Test Results ===")
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
	_check_source_wiring()
	await _check_parity()
	await _check_runtime_tree()


func _check_source_wiring() -> void:
	var f := FileAccess.open(SEQ_PATH, FileAccess.READ)
	_assert(f != null, "cannot read " + SEQ_PATH)
	if f == null:
		return
	var src := f.get_as_text()
	_assert(src.find(OLD_SHELL) == -1,
		"S-069 (shared with S-106): %s still loads the old %s; it must render through %s"
		% [SEQ_PATH, OLD_SHELL, GALAXY_SCENE])
	_assert(src.find("scenes/galaxy/galaxy_view") != -1,
		"S-069 (shared with S-106): %s does not reference scenes/galaxy/galaxy_view" % SEQ_PATH)


# Parity: the galaxy renderer answers the whole old-shell API the sequencer used.
func _check_parity() -> void:
	var packed = load(GALAXY_SCENE)
	_assert(packed is PackedScene, "cannot load " + GALAXY_SCENE)
	if not (packed is PackedScene):
		return
	var g: Node = (packed as PackedScene).instantiate()
	get_root().add_child(g)
	await process_frame
	for m in PARITY_METHODS:
		_assert(g.has_method(m),
			"S-069 parity: galaxy_view lacks %s(), which time_jump_sequencer.gd called on the old shell" % m)
	for s in PARITY_SIGNALS:
		_assert(g.has_signal(s),
			"S-069 parity: galaxy_view lacks signal %s, which time_jump_sequencer.gd listens to" % s)
	g.queue_free()


# Runtime: the sequencer's tree holds a galaxy_view and no old shell.
func _check_runtime_tree() -> void:
	var packed = load(SEQ_SCENE)
	_assert(packed is PackedScene, "cannot load " + SEQ_SCENE)
	if not (packed is PackedScene):
		return
	var seq: Node = (packed as PackedScene).instantiate()
	get_root().add_child(seq)
	await process_frame
	await process_frame
	var galaxy := _find_scene(seq, GALAXY_SCENE)
	var old := _find_scene(seq, "res://" + OLD_SHELL + ".tscn")
	_assert(galaxy != null,
		"S-069: no node instanced from %s under the time-jump sequencer" % GALAXY_SCENE)
	_assert(old == null,
		"S-069: the sequencer tree still holds the retired world_view_shell node")
	seq.queue_free()


func _find_scene(n: Node, path: String) -> Node:
	if n.scene_file_path == path:
		return n
	for c in n.get_children():
		var r := _find_scene(c, path)
		if r != null:
			return r
	return null
