extends Node

signal camera_move_completed()

var _data: Node
var _renderer: Node
var _camera: Node
var _config: Resource
var _visual_container: Node
var _viewport: SubViewport


func setup_era(era_id: String) -> void:
	cleanup()

	_config = load("res://scenes/shared/world_view/era_world_view_config.tres")

	var data_script := load("res://scenes/shared/world_view/world_view_data.gd")
	_data = Node.new()
	_data.set_script(data_script)
	_data.name = "WorldViewData"
	add_child(_data)

	var renderer_path: String = _config.get_renderer_path(era_id)
	if renderer_path.is_empty():
		return
	_renderer = load(renderer_path).instantiate()
	add_child(_renderer)

	var camera_path: String = _config.get_camera_path(era_id)
	print("[SHELL] camera_path='%s' renderer=%s" % [camera_path, _renderer])
	if camera_path.is_empty():
		# Integrated renderer+camera (e.g., world_view_structure for Settled Reach)
		print("[SHELL] calling _renderer.setup(_data)")
		_renderer.setup(_data)
		_camera = _renderer
	else:
		# Separate renderer + camera (future non-space eras)
		_visual_container = Node3D.new()
		_visual_container.name = "VisualContainer"
		add_child(_visual_container)
		_renderer.setup(_data, _visual_container)
		_camera = load(camera_path).instantiate()
		add_child(_camera)
		if _viewport:
			_camera.setup(_renderer, _viewport)

	if _camera and _camera.has_signal("camera_move_completed"):
		_camera.camera_move_completed.connect(func(): camera_move_completed.emit())


func set_viewport(viewport: SubViewport) -> void:
	_viewport = viewport


func cleanup() -> void:
	if _camera and _camera != _renderer:
		if _camera.has_method("teardown"):
			_camera.teardown()
		_camera.queue_free()
	_camera = null
	if _renderer:
		if _renderer.has_method("teardown"):
			_renderer.teardown()
		_renderer.queue_free()
		_renderer = null
	if _visual_container:
		_visual_container.queue_free()
		_visual_container = null
	if _data:
		_data.queue_free()
		_data = null


func add_region_node(id: String, position: Vector3, size: float, color: Color, faction_id: String) -> void:
	if _data:
		_data.add_region(id, position, size, color, faction_id)


func remove_region_node(id: String) -> void:
	if _data:
		_data.remove_region(id)


func update_region_node(id: String, size: float, color: Color) -> void:
	if _data:
		_data.update_region(id, size, color)


func clear_region_nodes() -> void:
	if _data:
		_data.clear_regions()


func set_territory(region_id: String, center: Vector3, radius: float, color: Color) -> void:
	if _data:
		_data.set_territory(region_id, center, radius, color)


func update_territory(region_id: String, radius: float, color: Color) -> void:
	if _data:
		_data.update_territory(region_id, radius, color)


func remove_territory(region_id: String) -> void:
	if _data:
		_data.remove_territory(region_id)


func add_connection(from_id: String, to_id: String, connection_type: String, color: Color) -> void:
	if _data:
		_data.add_connection(from_id, to_id, connection_type, color)


func remove_connection(from_id: String, to_id: String) -> void:
	if _data:
		_data.remove_connection(from_id, to_id)


func flash_military_activity(region_id: String, intensity: float) -> void:
	if _data:
		_data.request_flash_region(region_id, intensity)


func flash_conflict(from_id: String, to_id: String, intensity: float) -> void:
	if _data:
		_data.request_flash_conflict(from_id, to_id, intensity)


func highlight_region(region_id: String) -> void:
	if _data:
		_data.set_highlight(region_id)


func clear_highlight() -> void:
	if _data:
		_data.set_highlight("")


func move_camera_to_region(region_id: String, duration: float) -> void:
	if _camera:
		_camera.move_to_region(region_id, duration)


func move_camera_to_overview(duration: float) -> void:
	if _camera:
		_camera.move_to_overview(duration)


func move_camera_to_position(pos: Vector3, look_at_target: Vector3, duration: float) -> void:
	if _camera:
		_camera.move_to_position(pos, look_at_target, duration)


func start_auto_camera() -> void:
	if _camera:
		_camera.start_ambient_motion()


func stop_auto_camera() -> void:
	if _camera:
		_camera.stop_ambient_motion()


func get_camera_position() -> Vector3:
	if _camera:
		return _camera.get_current_position()
	return Vector3.ZERO


func get_camera_target() -> Vector3:
	if _camera:
		return _camera.get_current_target()
	return Vector3.ZERO


func set_opacity(alpha: float) -> void:
	var parent := get_parent()
	if parent:
		parent.modulate = Color(1, 1, 1, alpha)
