extends SceneTree

const KITS_DIR := "res://scenes/mockups/landscape/kits/"

var _failures := 0


func _init() -> void:
	_check_determinism()
	_check_kit_vocab()
	if _failures > 0:
		print("VERIFY FAILED: %d check(s)" % _failures)
		quit(1)
		return
	print("VERIFY OK")
	quit(0)


func _check_determinism() -> void:
	var a := FieldMap.new()
	a.generate(11, 16000.0, 60.0)
	var b := FieldMap.new()
	b.generate(11, 16000.0, 60.0)
	_assert(a.compute_hash() == b.compute_hash(), "seed 11 generated twice must hash equal")

	var c := FieldMap.new()
	c.generate(12, 16000.0, 60.0)
	_assert(a.compute_hash() != c.compute_hash(), "seed 12 must hash differently from seed 11")


func _check_kit_vocab() -> void:
	var dir := DirAccess.open(KITS_DIR)
	if dir == null:
		_assert(false, "cannot open kits dir %s" % KITS_DIR)
		return

	dir.list_dir_begin()
	var file_name := dir.get_next()
	while file_name != "":
		if not dir.current_is_dir() and file_name.ends_with(".json"):
			_check_one_kit(KITS_DIR + file_name)
		file_name = dir.get_next()
	dir.list_dir_end()


func _check_one_kit(path: String) -> void:
	var kit := Placer.load_kit(path)
	_assert(not kit.is_empty(), "%s failed to parse" % path)
	if kit.is_empty():
		return

	var mesh_names := _collect_mesh_names(kit)
	var bad: Array = []
	for m in mesh_names:
		if m != "none" and not Placer.is_known_mesh_name(m):
			bad.append(m)
	_assert(bad.is_empty(), "%s references unknown mesh name(s): %s" % [path, bad])

	var field_map := FieldMap.new()
	field_map.generate(11, 16000.0, 60.0)
	var world := Node3D.new()
	get_root().add_child(world)
	var placer := Placer.new()
	var result := placer.place(field_map, kit, world)
	print("%s: %d pieces (%s)" % [kit.get("name", path), result.total, result.by_type])
	world.queue_free()


func _collect_mesh_names(kit: Dictionary) -> Array:
	var names: Array = []
	for rule in kit.get("terrain", []):
		names.append(rule.get("mesh", "none"))
	for rule in kit.get("city", []):
		names.append(rule.get("mesh", "none"))
	for border_kind in kit.get("borders", {}).keys():
		var border: Dictionary = kit.borders[border_kind]
		names.append(border.get("mesh", "none"))
		for crossing_kind in border.get("crossing", {}).keys():
			names.append(border.crossing[crossing_kind].get("mesh", "none"))
	for node_type in kit.get("nodes", {}).keys():
		names.append(kit.nodes[node_type].get("mesh", "none"))
	if kit.has("backdrop"):
		names.append(kit.backdrop.get("mesh", "none"))
	return names


func _assert(condition: bool, message: String) -> void:
	if not condition:
		_failures += 1
		print("FAIL: %s" % message)
