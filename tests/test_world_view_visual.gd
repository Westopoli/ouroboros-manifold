extends Control

var _shell: Node
var _flash_timer := 0.0


func _ready() -> void:
	var bg := ColorRect.new()
	bg.color = Color(0.02, 0.02, 0.05)
	bg.set_anchors_preset(Control.PRESET_FULL_RECT)
	add_child(bg)

	var container := SubViewportContainer.new()
	container.set_anchors_preset(Control.PRESET_FULL_RECT)
	container.stretch = true
	add_child(container)

	var viewport := SubViewport.new()
	viewport.transparent_bg = true
	viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	container.add_child(viewport)

	var shell_scene := load("res://scenes/shared/world_view/world_view_shell.tscn")
	_shell = shell_scene.instantiate()
	add_child(_shell)
	_shell.set_viewport(viewport)
	_shell.setup_era("settled_reach")

	_shell.add_region_node("alpha_prime", Vector3(15, 0, 0), 3.0, Color(0.9, 0.2, 0.2), "crimson_order")
	_shell.add_region_node("alpha_sec", Vector3(22, 0, 8), 2.0, Color(0.8, 0.3, 0.3), "crimson_order")
	_shell.add_region_node("alpha_outpost", Vector3(10, 0, -10), 1.5, Color(0.7, 0.25, 0.25), "crimson_order")

	_shell.add_region_node("beta_core", Vector3(-18, 0, 5), 3.5, Color(0.2, 0.4, 0.9), "azure_pact")
	_shell.add_region_node("beta_colony", Vector3(-25, 0, -8), 2.0, Color(0.3, 0.4, 0.8), "azure_pact")
	_shell.add_region_node("beta_fringe", Vector3(-10, 0, 12), 1.8, Color(0.25, 0.35, 0.75), "azure_pact")

	_shell.add_region_node("gamma_hub", Vector3(0, 0, -22), 4.0, Color(0.2, 0.8, 0.3), "verdant_league")
	_shell.add_region_node("gamma_reach", Vector3(-8, 0, -30), 2.5, Color(0.25, 0.7, 0.35), "verdant_league")
	_shell.add_region_node("gamma_watch", Vector3(8, 0, -15), 1.5, Color(0.2, 0.65, 0.3), "verdant_league")

	_shell.set_territory("alpha_prime", Vector3(16, 0, -1), 14.0, Color(0.9, 0.2, 0.2, 0.3))
	_shell.set_territory("beta_core", Vector3(-18, 0, 3), 16.0, Color(0.2, 0.4, 0.9, 0.3))
	_shell.set_territory("gamma_hub", Vector3(0, 0, -22), 18.0, Color(0.2, 0.8, 0.3, 0.3))

	_shell.add_connection("alpha_prime", "alpha_sec", "supply", Color(0.9, 0.5, 0.5, 0.6))
	_shell.add_connection("alpha_prime", "alpha_outpost", "supply", Color(0.9, 0.5, 0.5, 0.6))
	_shell.add_connection("beta_core", "beta_colony", "supply", Color(0.5, 0.5, 0.9, 0.6))
	_shell.add_connection("beta_core", "beta_fringe", "supply", Color(0.5, 0.5, 0.9, 0.6))
	_shell.add_connection("gamma_hub", "gamma_reach", "supply", Color(0.5, 0.9, 0.5, 0.6))
	_shell.add_connection("gamma_hub", "gamma_watch", "supply", Color(0.5, 0.9, 0.5, 0.6))

	_shell.add_connection("alpha_outpost", "gamma_watch", "contested", Color(1.0, 0.8, 0.2, 0.4))
	_shell.add_connection("beta_fringe", "alpha_prime", "trade", Color(0.8, 0.8, 0.8, 0.3))

	_shell.highlight_region("alpha_prime")

	_shell.move_camera_to_overview(0.01)
	_shell.camera_move_completed.connect(_on_overview_done, CONNECT_ONE_SHOT)


func _on_overview_done() -> void:
	_shell.start_auto_camera()
	print("[VisualTest] Camera orbiting. Close window when done reviewing.")
	print("[VisualTest] Periodic flashes will fire every 3 seconds.")


func _process(delta: float) -> void:
	if not _shell:
		return
	_flash_timer += delta
	if _flash_timer >= 3.0:
		_flash_timer = 0.0
		var choices := ["alpha_prime", "beta_core", "gamma_hub", "alpha_sec", "beta_colony", "gamma_reach"]
		var idx := randi() % choices.size()
		_shell.flash_military_activity(choices[idx], randf_range(0.5, 1.0))
		if randf() > 0.5:
			var pairs := [
				["alpha_outpost", "gamma_watch"],
				["beta_fringe", "alpha_prime"],
			]
			var pair: Array = pairs[randi() % pairs.size()]
			_shell.flash_conflict(pair[0], pair[1], randf_range(0.4, 0.9))
