# test_cover_render.gd
# Headless isolation test for _scatter_cover_asteroids in terrain_renderer.
# Run via: bash scripts/run_godot_tests.sh tests/test_cover_render.gd
# Manual repro: godot --headless --path . --script res://tests/test_cover_render.gd --quit-after 30
# Does NOT require TacticalBridge or EraThemeResolver autoloads — terrain_renderer is
# instantiated in isolation and _scatter_cover_asteroids is called directly.

extends SceneTree

func _init() -> void:
	var renderer: Node = load("res://scenes/tactical/terrain_renderer.gd").new()
	get_root().add_child(renderer)

	var asteroids: Array = [
		{"id": "a1", "cluster": "c1", "x": 100.0, "y": 200.0, "r": 2.0,  "h": 3.0,  "class": "tiny"},
		{"id": "a2", "cluster": "c1", "x": 300.0, "y": 400.0, "r": 5.0,  "h": 6.0,  "class": "small"},
		{"id": "a3", "cluster": "c2", "x": 500.0, "y": 600.0, "r": 12.0, "h": 15.0, "class": "medium"},
		{"id": "a4", "cluster": "c2", "x": 700.0, "y": 800.0, "r": 40.0, "h": 50.0, "class": "huge"},
	]

	renderer._scatter_cover_asteroids(asteroids, 42)

	# Collect all MultiMeshInstance3D children added by the call
	var mmis: Array = []
	for child in renderer.get_children():
		if child is MultiMeshInstance3D:
			mmis.append(child)

	# Assertion 1: 4 MultiMeshInstance3D children (one per scale_class)
	assert(mmis.size() == 4, "Expected 4 MultiMeshInstance3D, got %d" % mmis.size())

	# Build lookup: class → mmi
	var class_mmi: Dictionary = {}
	for mmi in mmis:
		# Name format: CoverAsteroid_<class>
		var parts: Array = mmi.name.split("_")
		var cls: String = parts[parts.size() - 1]
		class_mmi[cls] = mmi

	for cls in ["tiny", "small", "medium", "huge"]:
		assert(class_mmi.has(cls), "Missing MultiMeshInstance3D for class=%s" % cls)

		var mmi: MultiMeshInstance3D = class_mmi[cls]

		# Assertion 2: instance_count == 1 for each
		assert(mmi.multimesh.instance_count == 1,
			"class=%s expected instance_count=1, got %d" % [cls, mmi.multimesh.instance_count])

	# Assertion 3: transform origins match manifest x/y
	var expected: Dictionary = {
		"tiny":   Vector3(100.0, 0.0, 200.0),
		"small":  Vector3(300.0, 0.0, 400.0),
		"medium": Vector3(500.0, 0.0, 600.0),
		"huge":   Vector3(700.0, 0.0, 800.0),
	}
	for cls in expected:
		var mmi: MultiMeshInstance3D = class_mmi[cls]
		var origin: Vector3 = mmi.multimesh.get_instance_transform(0).origin
		var want: Vector3 = expected[cls]
		assert(origin.is_equal_approx(want),
			"class=%s origin=%s expected=%s" % [cls, origin, want])

	print("PASS: test_cover_render all assertions green")
	quit(0)
