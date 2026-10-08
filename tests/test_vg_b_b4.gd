extends SceneTree

# Lane B piece B4 (docs/northstar/plans/2026-10-07-visible-game-spec.md rev 4,
# lane B; docs/northstar/plans/preflight_2026-10-07/3-galaxy-field.md section 3;
# docs/bible/epics/E-16 S-106 R-106-02/03): scenes/galaxy/galaxy_view.gd gains
# the territory-shell renderer as a child node named ShellRenderer, fed from
# the snapshot with tier -> significance 0.3 / 0.6 / 1.0 (tier 0 / 1 / 2), and
# qa_state gains a "shell_renderer" key. Existing galaxy tests stay as they
# are (test_galaxy_view.gd, test_galaxy_pixels.py, test_galaxy_conquest.py).
#
# Interface this file fixes for the B4 builder (not stated elsewhere):
#   qa_state()["shell_renderer"] is a Dictionary with
#     "present": bool, "significance": {region id (int) -> float}.
# The ShellRenderer child is a DIRECT child of the galaxy_view root.
# No Westley threshold lives here, so there is no *_park_* file.

const SCENE_PATH := "res://scenes/galaxy/galaxy_view.tscn"
const FIXTURE_PATH := "res://tests/transport/fixtures/snapshot_seed1_tick10.json"
const TIER_SIGNIFICANCE := {0: 0.3, 1: 0.6, 2: 1.0}
const PLANTS := ["seed-ignored", "owner-colour-flat", "edges-2d-overlay",
	"pick-radius-zero", "bands-frozen", "conquest-no-recolour"]
const OLD_KEYS := ["scene", "tick", "plants", "system_count", "owners",
	"edge_counts", "systems_px", "region_colours", "owner_colours", "band",
	"distance", "pick_radius_px", "edges_3d", "hash", "error_panel"]

var _pass_count := 0
var _fail_count := 0
var _fail_msgs: Array[String] = []


func _initialize() -> void:
	await _run_tests()
	print("\n=== VG B4 Test Results ===")
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
	var snapshot = _read_json(FIXTURE_PATH)
	_assert(snapshot is Dictionary and snapshot.has("regions"), "fixture %s unreadable" % FIXTURE_PATH)
	if not (snapshot is Dictionary):
		return
	var packed = load(SCENE_PATH)
	_assert(packed is PackedScene, "cannot load " + SCENE_PATH)
	if not (packed is PackedScene):
		return
	var root: Node = (packed as PackedScene).instantiate()
	get_root().add_child(root)
	await process_frame
	await process_frame
	if not (root.has_method("set_snapshot") and root.has_method("qa_state")):
		_assert(false, "galaxy_view root lacks set_snapshot or qa_state")
		return
	root.set_snapshot(snapshot)
	await process_frame

	# B4: the renderer is a child node named ShellRenderer (R-106-02/03 shell).
	var shell: Node = root.get_node_or_null("ShellRenderer")
	_assert(shell != null, "B4: galaxy_view has no direct child node named ShellRenderer (renderer not wired as a child node)")
	if shell != null:
		_assert(shell.get_parent() == root, "B4: ShellRenderer is not a direct child of the galaxy_view root")
		_assert(shell.get_script() != null
				and str(shell.get_script().resource_path).ends_with("shell_renderer.gd"),
				"B4: ShellRenderer is not driven by scenes/galaxy/shell_renderer.gd")
		_assert(shell.has_method("setup") and shell.has_method("teardown")
				and shell.has_method("get_faction_shell_count"),
				"B4: ShellRenderer lacks the setup/teardown/get_faction_shell_count surface")

	# B4: qa_state gains shell_renderer; every old key and plant stays.
	var st: Dictionary = root.qa_state()
	for k in OLD_KEYS:
		_assert(st.has(k), "B4: qa_state lost existing key " + k)
	_assert(st.get("plants", []) == PLANTS, "B4: qa_state plants list changed")
	_assert(st.has("shell_renderer"), "B4: qa_state has no shell_renderer key (element inventory)")
	var sr = st.get("shell_renderer", null)
	_assert(sr is Dictionary, "B4: qa_state.shell_renderer is not a Dictionary")
	if sr is Dictionary:
		_assert(bool(sr.get("present", false)), "B4: qa_state.shell_renderer.present is not true")
		var sig = sr.get("significance", null)
		_assert(sig is Dictionary, "B4: qa_state.shell_renderer.significance is not a Dictionary")
		if sig is Dictionary:
			var regions: Array = snapshot["regions"]
			_assert(sig.size() == regions.size(),
					"B4: significance has %d entries, snapshot has %d regions" % [sig.size(), regions.size()])
			var bad := 0
			var seen := {}
			for r in regions:
				var i := int(r["i"])
				var tier := int(r["tier"])
				seen[tier] = true
				var got = sig.get(i, null)
				if got == null or not is_equal_approx(float(got), float(TIER_SIGNIFICANCE[tier])):
					bad += 1
			_assert(bad == 0, "B4: %d regions with tier->significance not 0.3/0.6/1.0" % bad)
			_assert(seen.size() == 3, "fixture no longer carries all three tiers (control)")

	# Positive control for the mapping: a changed tier moves significance.
	var changed: Dictionary = snapshot.duplicate(true)
	changed["regions"][0]["tier"] = 2 if int(changed["regions"][0]["tier"]) != 2 else 0
	root.set_snapshot(changed)
	await process_frame
	var sr2 = root.qa_state().get("shell_renderer", {})
	var sig2 = sr2.get("significance", {}) if sr2 is Dictionary else {}
	var want: float = TIER_SIGNIFICANCE[int(changed["regions"][0]["tier"])]
	var id0 := int(changed["regions"][0]["i"])
	_assert(sig2 is Dictionary and sig2.has(id0) and is_equal_approx(float(sig2[id0]), want),
			"B4 control: re-tiering region %d did not update significance to %s" % [id0, want])

	# The Mission button and the six plants stay (tests/test_galaxy_view.gd fences them).
	_assert(root.get_node_or_null("UI/Mission") != null, "B4: UI/Mission button lost")

	root.queue_free()
	await process_frame


func _read_json(path: String) -> Variant:
	if not FileAccess.file_exists(path):
		return null
	return JSON.parse_string(FileAccess.get_file_as_string(path))
