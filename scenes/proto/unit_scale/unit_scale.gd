extends Control

## H-023 unit-scale comparison scene (prototype, docs/stories/H-023.md). A stage at true game scale, a gallery of each role beside a
## human-height reference, one slider per role and a metrics line per role. Every slider change rewrites data/unit_scale.toml.

const Model := preload("res://scenes/proto/unit_scale/unit_scale_model.gd")
const Stage := preload("res://scenes/proto/unit_scale/unit_scale_stage.gd")

var _values: Dictionary = {}
var _stage: Control
var _sliders: Dictionary = {}
var _metric_labels: Dictionary = {}
var _value_labels: Dictionary = {}
var _hud: Label


func _ready() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	_values = Model.load_values()
	_stage = Stage.new()
	_stage.name = "Stage"
	_stage.values = _values
	_stage.stage_rect = Rect2(10.0, 44.0, 1380.0, 1380.0 * Model.STAGE_H / Model.STAGE_W)
	_stage.gallery_rect = Rect2(10.0, 44.0 + _stage.stage_rect.size.y + 6.0, 1380.0, 1070.0 - (44.0 + _stage.stage_rect.size.y + 6.0))
	_stage.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	_stage.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_stage)

	_hud = Label.new()
	_hud.name = "StageSizeLabel"
	_hud.position = Vector2(10.0, 8.0)
	_hud.text = "Stage %d x %d wu (DRAFT), 1 m = %d wu (DRAFT), human %.1f m = %d wu; %d px per 1000 wu on the stage. Walk speeds: sim roster profile." % [
		int(Model.STAGE_W), int(Model.STAGE_H), int(Model.WU_PER_METRE), Model.HUMAN_HEIGHT_M, int(Model.human_height_wu()),
		int(1000.0 * _stage.stage_px_per_wu())]
	add_child(_hud)

	var panel := VBoxContainer.new()
	panel.name = "SlidersPanel"
	panel.position = Vector2(1400.0, 8.0)
	panel.custom_minimum_size = Vector2(510.0, 0.0)
	add_child(panel)
	for role in Model.ROLES:
		var row := VBoxContainer.new()
		row.name = "Row_%s" % role
		panel.add_child(row)
		var title := Label.new()
		title.name = "Title_%s" % role
		row.add_child(title)
		_value_labels[role] = title
		var s := HSlider.new()
		s.name = "Slider_%s" % role
		s.min_value = Model.SCALE_MIN
		s.max_value = Model.SCALE_MAX
		s.step = 0.01
		s.custom_minimum_size = Vector2(480.0, 20.0)
		s.value = clampf(float(_values[role]["visual_scale"]), Model.SCALE_MIN, Model.SCALE_MAX)
		s.value_changed.connect(_on_slider.bind(role))
		row.add_child(s)
		_sliders[role] = s
		var m := Label.new()
		m.name = "Metrics_%s" % role
		row.add_child(m)
		_metric_labels[role] = m
		_refresh_role(role)


func _on_slider(v: float, role: String) -> void:
	_values[role]["visual_scale"] = v
	_values[role]["radius"] = Model.BASE_RADIUS * v  # DRAFT-slider-ties-radius
	_refresh_role(role)
	Model.save_values(_values)
	_stage.queue_redraw()


func _refresh_role(role: String) -> void:
	var v: Dictionary = _values[role]
	var met := Model.metrics(role, float(v["radius"]))
	_value_labels[role].text = "%s   visual_scale %.2f   radius %.2f wu   walk %d wu/s" % [role, float(v["visual_scale"]), float(v["radius"]), int(Model.WALK_SPEED[role])]
	_metric_labels[role].text = "abreast at choke (%d wu): %d | ring city: %d | cross stage: %.1f s" % [
		int(Model.CHOKE_WIDTH), met["units_abreast"], met["units_to_ring_city"], met["seconds_to_cross_stage"]]


func qa_state() -> Dictionary:
	var roles := {}
	for role in Model.ROLES:
		var v: Dictionary = _values[role]
		roles[role] = {
			"role": role,
			"radius": float(v["radius"]),
			"visual_scale": float(v["visual_scale"]),
			"walk_speed": float(Model.WALK_SPEED[role]),
			"metrics": Model.metrics(role, float(v["radius"])),
			"slider_value": _sliders[role].value,
		}
	return {
		"stage": {"width_wu": Model.STAGE_W, "height_wu": Model.STAGE_H, "wu_per_metre": Model.WU_PER_METRE,
			"choke_width_wu": Model.CHOKE_WIDTH, "city_radius_wu": Model.CITY_RADIUS},
		"human_reference": {"height_m": Model.HUMAN_HEIGHT_M, "height_wu": Model.human_height_wu(), "shoulder_wu": Model.human_shoulder_wu()},
		"roles": roles,
		"positions": Model.POSITIONS.duplicate(true),
	}
