extends Node

var _shell: Node
var _camera_move_received := false


func _ready() -> void:
	var viewport := SubViewport.new()
	viewport.transparent_bg = true
	viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	add_child(viewport)

	var shell_scene := load("res://scenes/shared/world_view/world_view_shell.tscn")
	_shell = shell_scene.instantiate()
	add_child(_shell)

	_shell.set_viewport(viewport)
	_shell.camera_move_completed.connect(func(): _camera_move_received = true)

	print("\n=== WorldViewShell Wiring Test ===\n")

	print("--- setup_era ---")
	_shell.setup_era("settled_reach")

	print("\n--- add_region_node ---")
	_shell.add_region_node("r1", Vector3(10, 0, 5), 3.0, Color.RED, "faction_alpha")
	_shell.add_region_node("r2", Vector3(-15, 0, 10), 2.5, Color.BLUE, "faction_beta")
	_shell.add_region_node("r3", Vector3(0, 0, -20), 4.0, Color.GREEN, "faction_gamma")

	print("\n--- set_territory ---")
	_shell.set_territory("r1", Vector3(10, 0, 5), 12.0, Color(1, 0, 0, 0.3))
	_shell.set_territory("r2", Vector3(-15, 0, 10), 10.0, Color(0, 0, 1, 0.3))
	_shell.set_territory("r3", Vector3(0, 0, -20), 15.0, Color(0, 1, 0, 0.3))

	print("\n--- add_connection ---")
	_shell.add_connection("r1", "r2", "trade", Color.YELLOW)
	_shell.add_connection("r2", "r3", "military", Color.ORANGE)

	print("\n--- flash_military_activity ---")
	_shell.flash_military_activity("r1", 0.8)

	print("\n--- flash_conflict ---")
	_shell.flash_conflict("r1", "r2", 0.6)

	print("\n--- highlight_region ---")
	_shell.highlight_region("r2")

	print("\n--- move_camera_to_region ---")
	_camera_move_received = false
	_shell.move_camera_to_region("r1", 2.0)
	_check("camera_move_completed received (move_to_region)", _camera_move_received)

	print("\n--- move_camera_to_overview ---")
	_camera_move_received = false
	_shell.move_camera_to_overview(3.0)
	_check("camera_move_completed received (move_to_overview)", _camera_move_received)

	print("\n--- start_auto_camera ---")
	_shell.start_auto_camera()

	print("\n--- update_region_node ---")
	_shell.update_region_node("r1", 6.0, Color.MAGENTA)

	print("\n--- update_territory ---")
	_shell.update_territory("r1", 18.0, Color(1, 0, 1, 0.3))

	print("\n--- clear_highlight ---")
	_shell.clear_highlight()

	print("\n--- remove_connection ---")
	_shell.remove_connection("r1", "r2")

	print("\n--- remove_territory ---")
	_shell.remove_territory("r3")

	print("\n--- remove_region_node ---")
	_shell.remove_region_node("r3")

	print("\n--- clear_region_nodes ---")
	_shell.clear_region_nodes()

	print("\n--- cleanup ---")
	_shell.cleanup()

	print("\n=== Shell Wiring Test Complete ===\n")
	get_tree().quit()


func _check(label: String, condition: bool) -> void:
	if condition:
		print("  PASS: %s" % label)
	else:
		print("  FAIL: %s" % label)
