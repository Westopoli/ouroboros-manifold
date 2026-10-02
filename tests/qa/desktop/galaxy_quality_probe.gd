extends SceneTree

# Ruling A54 (docs/northstar/plans/2026-10-01-architect-rulings-2.md Addendum 23): galaxy quality is
# a manual setting; each value changes what the galaxy view draws; the game never changes it.
# Child of tests/qa/desktop/test_galaxy_quality.py, booted on a real display with a settings.cfg
# fixture (the tier under test) in a throwaway XDG_DATA_HOME. Prints one "PROBE {json}" line and asserts nothing.
# Stored key and qa_state key are the ones tests/test_galaxy_quality_setting.gd and A54 name:
# [display] galaxy_quality, qa_state "quality_tier".
#
# Reported, before and after a planted slow-frame run:
#   quality_tier      galaxy_view.qa_state()["quality_tier"]
#   stored            UIDataBus.get_settings()["galaxy_quality"]
#   cfg               the settings.cfg text
#   shells            [[mesh class, material class]] for every MeshInstance3D under the ShellRenderer node
#   ambient_particles `amount` summed over the node named "AmbientRig" under the view (0 if absent)
#   emitter_amounts   every particle emitter's `amount` under the view
#   particles         total `amount` over every GPUParticles3D / CPUParticles3D under the view
# Slow-frame hook: this probe stalls its own frames (OS.delay_msec between process frames), so no
# game-side hook is needed and the game cannot tell a planted stall from real load. The measured mean
# frame time is reported so the parent can assert the stall really happened (positive control).

const SCENE_PATH := "res://scenes/galaxy/galaxy_view.tscn"
const FIXTURE_PATH := "res://tests/transport/fixtures/snapshot_seed1_tick10.json"
const SLOW_FRAMES := 130
const STALL_MSEC := 60


func _initialize() -> void:
	var out := {}
	var view: Node = (load(SCENE_PATH) as PackedScene).instantiate()
	get_root().add_child(view)
	await process_frame
	await process_frame
	view.set_snapshot(JSON.parse_string(FileAccess.get_file_as_string(FIXTURE_PATH)))
	for _i in 5:
		await process_frame
	out["before"] = _measure(view)
	var t0 := Time.get_ticks_msec()
	for _i in SLOW_FRAMES:
		OS.delay_msec(STALL_MSEC)
		await process_frame
	out["mean_frame_ms"] = float(Time.get_ticks_msec() - t0) / float(SLOW_FRAMES)
	out["after"] = _measure(view)
	# A60: the view reads the setting when it is built; a change made afterwards does not re-apply.
	# Store the next tier through the real save path, let frames pass, read the SAME view again; then
	# build a second view (positive control: the changed value is picked up at the next build).
	var bus = get_root().get_node_or_null("UIDataBus")
	var changed_to := (int(bus.get_settings().get("galaxy_quality", 0)) + 1) % 3
	var settings: Dictionary = bus.get_settings()
	settings["galaxy_quality"] = changed_to
	bus.save_settings(settings)
	for _i in 10:
		await process_frame
	out["changed_to"] = changed_to
	out["stored_after_change"] = bus.get_settings().get("galaxy_quality", null)
	out["same_view_after_change"] = _measure(view)
	var view2: Node = (load(SCENE_PATH) as PackedScene).instantiate()
	get_root().add_child(view2)
	await process_frame
	await process_frame
	view2.set_snapshot(JSON.parse_string(FileAccess.get_file_as_string(FIXTURE_PATH)))
	for _i in 5:
		await process_frame
	out["rebuilt_view"] = _measure(view2)
	print("PROBE ", JSON.stringify(out))
	quit(0)


func _measure(view: Node) -> Dictionary:
	var bus = get_root().get_node_or_null("UIDataBus")
	var stored = bus.get_settings().get("galaxy_quality", null) if bus != null else null
	var cfg_text := FileAccess.get_file_as_string("user://settings.cfg") if FileAccess.file_exists("user://settings.cfg") else ""
	var shells: Array = []
	var shell_node := view.get_node_or_null("ShellRenderer")
	if shell_node != null:
		_collect_shells(shell_node, shells)
	var particles := [0]
	_count_particles(view, particles)
	var ambient := [0]
	var amounts: Array = []
	var rig := view.find_child("AmbientRig", true, false)
	if rig != null:
		_count_particles(rig, ambient)
	_list_amounts(view, amounts)
	return {
		"quality_tier": view.qa_state().get("quality_tier", null),
		"stored": stored,
		"cfg": cfg_text,
		"shells": shells,
		"particles": particles[0],
		"ambient_particles": ambient[0],
		"emitter_amounts": amounts,
	}


func _collect_shells(node: Node, out: Array) -> void:
	if node is MeshInstance3D:
		var mesh_class: String = node.mesh.get_class() if node.mesh != null else ""
		var mat_class: String = node.material_override.get_class() if node.material_override != null else ""
		out.append([mesh_class, mat_class])
	for child in node.get_children():
		_collect_shells(child, out)


func _count_particles(node: Node, total: Array) -> void:
	if node is GPUParticles3D or node is CPUParticles3D:
		total[0] += int(node.amount)
	for child in node.get_children():
		_count_particles(child, total)


func _list_amounts(node: Node, out: Array) -> void:
	if node is GPUParticles3D or node is CPUParticles3D:
		out.append(int(node.amount))
	for child in node.get_children():
		_list_amounts(child, out)
