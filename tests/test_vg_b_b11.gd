extends SceneTree
# Rule pins: R-106-05@a91085

# Piece B11 tests (docs/northstar/plans/2026-10-07-visible-game-spec.md rev 4, lane B; bible E-16
# S-106 R-106-05, as B11 read it: "When idle, an ambient particle field (rings, inflow streams, dust,
# starfield, central glow) fills the space behind the territory at low opacity". B25 (rev 12d) moves the
# starfield and dust off particles onto a wash, four star-layer meshes and a MultiMesh of motes
# (tests/test_vg_b_b25.gd owns those); this file still counts the remaining GPUParticles3D: rings, streams,
# central glow, which keep the contract below). The tier expectations are
# the A60 stack's (ruling A54/A60, origin/push/A54-ambient-tests tests/qa/desktop/test_galaxy_ambient.py):
#   tier 0 full field; tier 1 same field (only the shells change); tier 2 HALF the amount (+-0.02).
# Names chosen by this test (the builder must match): the field is the subtree under a node named
# "AmbientRig" inside res://scenes/galaxy/galaxy_view.tscn; its amount is the sum of `amount` over
# every GPUParticles3D / CPUParticles3D under it; the tier is read from the stored setting
# [display] galaxy_quality via UIDataBus.save_settings, applied when the view is built.
# Positive controls: tier 0 is non-zero, so the ratios mean something; every particle in the view is
# under AmbientRig (a field living elsewhere would not count); no emitter is deleted at tier 2.
# The user settings file is restored at the end.

const SCENE_PATH := "res://scenes/galaxy/galaxy_view.tscn"
const FIXTURE_PATH := "res://tests/transport/fixtures/snapshot_seed1_tick10.json"
const HALF := 0.5
const TOLERANCE := 0.02

var _pass_count := 0
var _fail_count := 0
var _fail_msgs: Array[String] = []
var _completed := false


func _initialize() -> void:
	await _run_tests()
	_assert(_completed, "the B11 checks did not run to the end (a script error aborted them)")
	print("\n=== VG B11 Ambient Field Test Results ===")
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
	var bus = get_root().get_node_or_null("UIDataBus")
	_assert(bus != null, "UIDataBus autoload missing")
	if bus == null:
		return
	var original: Dictionary = bus.get_settings().duplicate(true)
	var snapshot = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE_PATH))
	_assert(snapshot is Dictionary, "snapshot fixture unreadable")
	var reads := {}
	for tier in [0, 1, 2]:
		var s: Dictionary = bus.get_settings().duplicate(true)
		s["galaxy_quality"] = tier
		bus.save_settings(s)
		reads[tier] = await _build_and_measure(snapshot)
	bus.save_settings(original)

	var r0: Dictionary = reads[0]
	var r1: Dictionary = reads[1]
	var r2: Dictionary = reads[2]
	for tier in [0, 1]:
		var r: Dictionary = reads[tier]
		_assert(r["has_rig"], "R-106-05 tier %d: no node named AmbientRig in the galaxy view (the ambient particle field is not built)" % tier)
		_assert(r["ambient"] > 0, "R-106-05 tier %d: the ambient field has no particles (view-wide total %d)" % [tier, r["particles"]])
		_assert(r["amounts"].size() > 0 and r["amounts"].all(func(a): return a > 0), "R-106-05 tier %d: an emitter has no particles" % tier)
	_assert(r0["ambient"] > 0, "control: tier 0 must carry a field to compare against")
	_assert(r1["ambient"] == r0["ambient"], "A60 tier 1 changes the ambient field (%d vs %d); it changes only the shells" % [r1["ambient"], r0["ambient"]])
	if r0["ambient"] > 0:
		var ratio := float(r2["ambient"]) / float(r0["ambient"])
		_assert(absf(ratio - HALF) <= TOLERANCE, "A60 tier 2 ambient field %d vs tier 0 %d: ratio %.3f, expected %.2f within %.2f" % [r2["ambient"], r0["ambient"], ratio, HALF, TOLERANCE])
	else:
		_assert(false, "A60 tier 2 ratio unmeasurable: tier 0 has no ambient field")
	_assert(r2["amounts"].size() == r0["amounts"].size() and r0["amounts"].size() > 0, "A60 tier 2 thins amounts, it does not delete emitters (%d vs %d emitters)" % [r2["amounts"].size(), r0["amounts"].size()])
	_assert(r2["amounts"].all(func(a): return a >= 1), "A60 tier 2 has an emitter with no particles: %s" % str(r2["amounts"]))
	_assert(r0["has_rig"] and r0["particles"] == r0["ambient"], "particles exist in the view outside AmbientRig (%d vs %d under it)" % [r0["particles"], r0["ambient"]])
	_completed = true


func _build_and_measure(snapshot) -> Dictionary:
	var packed = load(SCENE_PATH)
	var out := {"has_rig": false, "ambient": 0, "particles": 0, "amounts": []}
	if packed == null:
		return out
	var view: Node = (packed as PackedScene).instantiate()
	get_root().add_child(view)
	await process_frame
	await process_frame
	if view.has_method("set_snapshot"):
		view.set_snapshot(snapshot)
	for _i in 5:
		await process_frame
	var rig := view.find_child("AmbientRig", true, false)
	out["has_rig"] = rig != null
	var all := [0]
	_count(view, all, null)
	out["particles"] = all[0]
	if rig != null:
		var inrig := [0]
		_count(rig, inrig, out["amounts"])
		out["ambient"] = inrig[0]
	view.queue_free()
	await process_frame
	return out


func _count(node: Node, total: Array, amounts) -> void:
	if node is GPUParticles3D or node is CPUParticles3D:
		total[0] += int(node.amount)
		if amounts != null:
			amounts.append(int(node.amount))
	for c in node.get_children():
		_count(c, total, amounts)
