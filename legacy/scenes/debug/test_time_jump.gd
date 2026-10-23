extends Control

var _sequencer: Node
var _panel: VBoxContainer
var _step_index: int = 0

const FACTIONS := {
	"f_player": Color(0.2, 0.5, 1.0),
	"f_enemy": Color(0.9, 0.2, 0.2),
	"f_neutral": Color(0.5, 0.5, 0.5),
}

const REGIONS := [
	{"region_id": "r_01", "owner_faction_id": "f_player", "significance": 0.7, "x": -20.0, "z": -15.0},
	{"region_id": "r_02", "owner_faction_id": "f_player", "significance": 0.5, "x": -10.0, "z": -5.0},
	{"region_id": "r_03", "owner_faction_id": "f_player", "significance": 0.6, "x": 0.0, "z": -20.0},
	{"region_id": "r_04", "owner_faction_id": "f_enemy", "significance": 0.8, "x": 15.0, "z": 5.0},
	{"region_id": "r_05", "owner_faction_id": "f_enemy", "significance": 0.5, "x": 25.0, "z": -10.0},
	{"region_id": "r_06", "owner_faction_id": "f_neutral", "significance": 0.4, "x": 5.0, "z": 15.0},
]

var _keyframes: Array[Dictionary] = []
var _entries: Array[Dictionary] = []


func _ready() -> void:
	_build_scripted_data()
	_build_ui()


func _build_scripted_data() -> void:
	_keyframes = [
		{
			"type": "keyframe",
			"time_jump_id": "tj_test",
			"keyframe_index": 0,
			"tick": 1000,
			"chronicle_entry_id": "ce_01",
			"ownership_changes": [],
			"military_events": [
				{"kind": "attack", "attacker_region_id": "r_04", "defender_region_id": "r_03"}
			],
			"regions_snapshot": [
				{"region_id": "r_01", "owner_faction_id": "f_player", "significance": 0.7, "x": -20.0, "z": -15.0},
				{"region_id": "r_02", "owner_faction_id": "f_player", "significance": 0.5, "x": -10.0, "z": -5.0},
				{"region_id": "r_03", "owner_faction_id": "f_player", "significance": 0.6, "x": 0.0, "z": -20.0},
				{"region_id": "r_04", "owner_faction_id": "f_enemy", "significance": 0.8, "x": 15.0, "z": 5.0},
				{"region_id": "r_05", "owner_faction_id": "f_enemy", "significance": 0.5, "x": 25.0, "z": -10.0},
				{"region_id": "r_06", "owner_faction_id": "f_neutral", "significance": 0.4, "x": 5.0, "z": 15.0},
			],
		},
		{
			"type": "keyframe",
			"time_jump_id": "tj_test",
			"keyframe_index": 1,
			"tick": 2000,
			"chronicle_entry_id": "ce_02",
			"ownership_changes": [
				{"region_id": "r_03", "old_faction_id": "f_player", "new_faction_id": "f_enemy"}
			],
			"military_events": [
				{"kind": "conquest", "attacker_region_id": "r_04", "defender_region_id": "r_03"}
			],
			"regions_snapshot": [
				{"region_id": "r_03", "owner_faction_id": "f_enemy", "significance": 0.65, "x": 0.0, "z": -20.0},
				{"region_id": "r_04", "owner_faction_id": "f_enemy", "significance": 0.85, "x": 15.0, "z": 5.0},
			],
		},
		{
			"type": "keyframe",
			"time_jump_id": "tj_test",
			"keyframe_index": 2,
			"tick": 3000,
			"chronicle_entry_id": null,
			"ownership_changes": [],
			"military_events": [
				{"kind": "attack", "attacker_region_id": "r_02", "defender_region_id": "r_03"}
			],
			"regions_snapshot": [
				{"region_id": "r_02", "owner_faction_id": "f_player", "significance": 0.55, "x": -10.0, "z": -5.0},
				{"region_id": "r_06", "owner_faction_id": "f_neutral", "significance": 0.45, "x": 5.0, "z": 15.0},
			],
		},
	]

	_entries = [
		{
			"entry_id": "ce_01",
			"base_form": "In the decades following the commander's victory at the frontier, the Conqueror's forces began probing the border regions. Scouts reported movement along the outer rim, a gathering of ships that suggested ambitions beyond mere posturing.",
			"expanded_form": "In the decades following the commander's victory at the frontier, the Conqueror's forces began probing the border regions. Scouts reported movement along the outer rim, a gathering of ships that suggested ambitions beyond mere posturing. Intelligence suggested the buildup was personal — the Conqueror had not forgotten the humiliation at Nak Reach, and the frontier worlds would pay the price for the Republic's defiance.",
		},
		{
			"entry_id": "ce_02",
			"base_form": "The fall of the outer colonies came swiftly. Region Three, long considered the Republic's most vulnerable holding, capitulated after a sustained siege. The garrison commander's final transmission was three words: hold the core.",
			"expanded_form": "The fall of the outer colonies came swiftly. Region Three, long considered the Republic's most vulnerable holding, capitulated after a sustained siege. The garrison commander's final transmission was three words: hold the core. The Sorn family's ancestral claim to the system — four generations of military governors — ended not with a battle but with a signature on terms of surrender.",
		},
	]


func _build_ui() -> void:
	_panel = VBoxContainer.new()
	_panel.set_anchors_preset(Control.PRESET_TOP_LEFT)
	_panel.offset_left = 10
	_panel.offset_top = 10
	_panel.add_theme_constant_override("separation", 6)
	add_child(_panel)

	var bg := PanelContainer.new()
	var style := StyleBoxFlat.new()
	style.bg_color = Color(0, 0, 0, 0.7)
	style.set_content_margin_all(10)
	bg.add_theme_stylebox_override("panel", style)
	var inner := VBoxContainer.new()
	inner.add_theme_constant_override("separation", 4)
	bg.add_child(inner)
	_panel.add_child(bg)

	var title := Label.new()
	title.text = "Time Jump Sequencer Test"
	title.add_theme_font_size_override("font_size", 16)
	inner.add_child(title)

	_add_button(inner, "1. Start time jump", _emit_start)
	_add_button(inner, "2. Send entry 1 + keyframe 1", _emit_kf1)
	_add_button(inner, "3. Send entry 2 + keyframe 2", _emit_kf2)
	_add_button(inner, "4. Send keyframe 3 (no entry)", _emit_kf3)
	_add_button(inner, "5. End time jump", _emit_end)
	_add_button(inner, "Run all (2s intervals)", _run_all)


func _add_button(parent: Node, text: String, callback: Callable) -> void:
	var btn := Button.new()
	btn.text = text
	btn.pressed.connect(callback)
	parent.add_child(btn)


func _emit_start() -> void:
	UIDataBus.time_jump_started.emit("tj_test", 27, 3, 2, {})


func _emit_kf1() -> void:
	UIDataBus.chronicle_entry.emit(_entries[0])
	await get_tree().create_timer(0.3).timeout
	UIDataBus.time_jump_keyframe.emit(_keyframes[0])


func _emit_kf2() -> void:
	UIDataBus.chronicle_entry.emit(_entries[1])
	await get_tree().create_timer(0.3).timeout
	UIDataBus.time_jump_keyframe.emit(_keyframes[1])


func _emit_kf3() -> void:
	UIDataBus.time_jump_keyframe.emit(_keyframes[2])


func _emit_end() -> void:
	UIDataBus.time_jump_ended.emit("tj_test")


func _run_all() -> void:
	_emit_start()
	await get_tree().create_timer(2.0).timeout
	_emit_kf1()
	await get_tree().create_timer(2.0).timeout
	_emit_kf2()
	await get_tree().create_timer(2.0).timeout
	_emit_kf3()
	await get_tree().create_timer(2.0).timeout
	_emit_end()
