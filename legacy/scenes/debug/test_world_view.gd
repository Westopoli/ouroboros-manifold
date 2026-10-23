extends Control

var _shell: Node
var _viewport: SubViewport

const FACTIONS := {
	"f_player": Color(0.3, 0.6, 1.0),
	"f_enemy": Color(1.0, 0.3, 0.2),
	"f_neutral": Color(0.4, 0.8, 0.3),
}

const REGIONS := [
	{"id": "r_01", "pos": Vector3(-15, 6, -10), "size": 2.0, "faction": "f_player"},
	{"id": "r_02", "pos": Vector3(-5, -3, -8), "size": 1.5, "faction": "f_player"},
	{"id": "r_03", "pos": Vector3(5, 4, -5), "size": 1.8, "faction": "f_player"},
	{"id": "r_04", "pos": Vector3(15, -5, -12), "size": 1.2, "faction": "f_enemy"},
	{"id": "r_05", "pos": Vector3(10, 2, 5), "size": 2.2, "faction": "f_enemy"},
	{"id": "r_06", "pos": Vector3(-10, -4, 8), "size": 1.6, "faction": "f_neutral"},
	{"id": "r_07", "pos": Vector3(0, 7, 10), "size": 1.4, "faction": "f_neutral"},
	{"id": "r_08", "pos": Vector3(-8, -1, -2), "size": 1.0, "faction": "f_player"},
]

var _step := 0


func _ready() -> void:
	_setup_viewport()
	_setup_shell()
	_populate_regions()
	_populate_territories()
	_populate_connections()
	_shell.start_auto_camera()
	_setup_ui()


func _setup_viewport() -> void:
	var container := SubViewportContainer.new()
	container.set_anchors_preset(Control.PRESET_FULL_RECT)
	container.stretch = true
	container.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(container)
	move_child(container, 0)

	_viewport = SubViewport.new()
	_viewport.transparent_bg = false
	_viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	container.add_child(_viewport)

	var env := WorldEnvironment.new()
	var environment := Environment.new()
	environment.background_mode = Environment.BG_COLOR
	environment.background_color = Color(0.0, 0.0, 0.0)
	env.environment = environment
	_viewport.add_child(env)


func _setup_shell() -> void:
	var shell_scene := load("res://scenes/shared/world_view/world_view_shell.tscn")
	_shell = shell_scene.instantiate()
	_viewport.add_child(_shell)
	_shell.set_viewport(_viewport)
	_shell.setup_era("settled_reach")


func _populate_regions() -> void:
	for r in REGIONS:
		_shell.add_region_node(r["id"], r["pos"], r["size"], FACTIONS[r["faction"]], r["faction"])


func _populate_territories() -> void:
	for r in REGIONS:
		var radius: float = r["size"] * 5.0
		_shell.set_territory(r["id"], r["pos"], radius, FACTIONS[r["faction"]])


func _populate_connections() -> void:
	_shell.add_connection("r_01", "r_02", "border", FACTIONS["f_player"])
	_shell.add_connection("r_02", "r_03", "border", FACTIONS["f_player"])
	_shell.add_connection("r_02", "r_08", "border", FACTIONS["f_player"])
	_shell.add_connection("r_03", "r_05", "border", FACTIONS["f_enemy"])
	_shell.add_connection("r_04", "r_05", "border", FACTIONS["f_enemy"])
	_shell.add_connection("r_06", "r_07", "border", FACTIONS["f_neutral"])
	_shell.add_connection("r_01", "r_06", "trade", FACTIONS["f_player"])
	_shell.add_connection("r_03", "r_07", "trade", FACTIONS["f_neutral"])
	_shell.add_connection("r_05", "r_07", "trade", FACTIONS["f_enemy"])


func _setup_ui() -> void:
	var panel := VBoxContainer.new()
	panel.set_anchors_preset(Control.PRESET_TOP_LEFT)
	panel.position = Vector2(20, 20)
	add_child(panel)

	var title := Label.new()
	title.text = "World View Test Harness"
	title.add_theme_font_size_override("font_size", 18)
	panel.add_child(title)

	var info := Label.new()
	info.text = "3 factions, 8 regions, 9 connections (6 border, 3 trade)"
	panel.add_child(info)

	_add_button(panel, "Flash r_03 (player)", func(): _shell.flash_military_activity("r_03", 0.8))
	_add_button(panel, "Flash conflict r_03 ↔ r_05", func(): _shell.flash_conflict("r_03", "r_05", 1.0))
	_add_button(panel, "Flash burst (rapid fire)", func(): _fire_flash_burst())
	_add_button(panel, "Highlight r_05 (enemy)", func(): _shell.highlight_region("r_05"))
	_add_button(panel, "Clear highlight", func(): _shell.clear_highlight())
	_add_button(panel, "Camera → r_01", func(): _shell.move_camera_to_region("r_01", 2.0))
	_add_button(panel, "Camera → overview", func(): _shell.move_camera_to_overview(2.0))
	_add_button(panel, "Camera → position (high)", func():
		_shell.move_camera_to_position(Vector3(0, 60, 30), Vector3(0, 0, 0), 2.5))
	_add_button(panel, "Camera → position (low angle)", func():
		_shell.move_camera_to_position(Vector3(30, 15, 30), Vector3(0, 0, 0), 2.5))
	_add_button(panel, "Conquer r_07 (neutral → enemy)", func(): _conquer_region())
	_add_button(panel, "Remove territory r_04", func():
		_shell.remove_territory("r_04"))
	_add_button(panel, "Start auto camera", func(): _shell.start_auto_camera())
	_add_button(panel, "Stop auto camera", func(): _shell.stop_auto_camera())


func _add_button(parent: Node, label: String, callback: Callable) -> void:
	var btn := Button.new()
	btn.text = label
	btn.pressed.connect(callback)
	parent.add_child(btn)


func _conquer_region() -> void:
	_shell.update_territory("r_07", 7.0, FACTIONS["f_enemy"])


func _fire_flash_burst() -> void:
	var region_ids := ["r_01", "r_02", "r_03", "r_04", "r_05", "r_06", "r_07", "r_08"]
	var burst_count := randi_range(3, 7)
	for i in burst_count:
		var delay := randf() * 0.3
		var tw := create_tween()
		tw.tween_callback(func():
			if randf() < 0.5:
				var rid: String = region_ids[randi() % region_ids.size()]
				_shell.flash_military_activity(rid, randf_range(0.4, 1.0))
			else:
				var a: String = region_ids[randi() % region_ids.size()]
				var b: String = region_ids[randi() % region_ids.size()]
				if a != b:
					_shell.flash_conflict(a, b, randf_range(0.5, 1.0))
		).set_delay(delay)
