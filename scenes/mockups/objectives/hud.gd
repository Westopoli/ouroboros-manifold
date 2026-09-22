extends CanvasLayer

const ARCHETYPE_NAMES := [
	"defensive_stand", "siege_breaking", "reconquest", "assault", "suppression",
	"multi_front_defense", "interception", "rear_guard", "containment", "counterinsurgency",
]
const BAR_WIDTH := 320.0
const BAR_HEIGHT := 6.0
const PLAY_HZ := 20.0
const MINIMAP_SIZE := Vector2(200, 200)
const MONO_FONT := preload("res://theme/fonts/JetBrainsMono-Regular.ttf")

var _root: Node3D
var _playing := false
var _play_accum := 0.0

@onready var _archetype_option: OptionButton = $VBoxContainer/ArchetypeOption
@onready var _seed_spinbox: SpinBox = $VBoxContainer/SeedSpinBox
@onready var _regenerate_button: Button = $VBoxContainer/RegenerateButton
@onready var _tick_button: Button = $VBoxContainer/TickButton
@onready var _play_button: Button = $VBoxContainer/PlayButton
@onready var _objective_label: Label = $VBoxContainer/ObjectiveLabel
@onready var _bar_bg: ColorRect = $VBoxContainer/ObjectiveBarBG
@onready var _bar_fill: ColorRect = $VBoxContainer/ObjectiveBarBG/ObjectiveBarFill
@onready var _sat_label: Label = $VBoxContainer/SatLabel
@onready var _timing_label: Label = $VBoxContainer/TimingLabel
@onready var _minimap: Control = $Minimap


func bind(root: Node3D) -> void:
	_root = root
	_objective_label.add_theme_font_override("font", MONO_FONT)
	for n in ARCHETYPE_NAMES:
		_archetype_option.add_item(n)
	_archetype_option.focus_mode = Control.FOCUS_NONE
	_seed_spinbox.focus_mode = Control.FOCUS_NONE
	_regenerate_button.focus_mode = Control.FOCUS_NONE
	_tick_button.focus_mode = Control.FOCUS_NONE
	_play_button.focus_mode = Control.FOCUS_NONE
	_archetype_option.item_selected.connect(_on_archetype_selected)
	_regenerate_button.pressed.connect(_on_regenerate_pressed)
	_tick_button.pressed.connect(func(): _root.qa_tick(50))
	_play_button.pressed.connect(_on_play_pressed)
	_minimap.draw.connect(_on_minimap_draw)
	on_regenerated()


func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and not event.echo:
		if event.keycode == KEY_R:
			_on_regenerate_pressed()
		elif event.keycode == KEY_T:
			_root.qa_tick(50)
		elif event.keycode == KEY_P:
			_on_play_pressed()


func _process(delta: float) -> void:
	if _playing:
		_play_accum += delta * PLAY_HZ
		while _play_accum >= 1.0:
			_play_accum -= 1.0
			_root.qa_tick(1)
			if _root.get_mission().status == "complete":
				_playing = false
				break
	refresh()


func _on_regenerate_pressed() -> void:
	_root.qa_seed(int(_seed_spinbox.value))


func _on_archetype_selected(idx: int) -> void:
	_root.qa_set("archetype", ARCHETYPE_NAMES[idx])


func _on_play_pressed() -> void:
	_playing = not _playing


func on_regenerated() -> void:
	if _root == null:
		return
	var st: Dictionary = _root.qa_state()
	_seed_spinbox.value = st.seed
	var idx: int = ARCHETYPE_NAMES.find(st.archetype)
	if idx >= 0:
		_archetype_option.select(idx)
	refresh()
	_minimap.queue_redraw()


func refresh() -> void:
	if _root == null:
		return
	var m: Dictionary = _root.get_mission()
	if m.is_empty():
		return
	var label: String = MissionGen.DISPLAY_NAMES.get(m.kind, m.kind)
	var pct := int(round(m.progress * 100.0))
	var filled := int(round(m.progress * 10.0))
	var bar := "#".repeat(filled) + "-".repeat(10 - filled)
	_objective_label.text = "PRIMARY  %s  %s %d%%" % [label, bar, pct]
	_bar_bg.custom_minimum_size = Vector2(BAR_WIDTH, BAR_HEIGHT)
	_bar_fill.position = Vector2.ZERO
	_bar_fill.size = Vector2(BAR_WIDTH * clampf(m.progress, 0.0, 1.0), BAR_HEIGHT)
	_sat_label.text = "Sat: %s  route %.0fwu  limit %.0fticks  skipped %s" % [
		"yes" if m.satisfiable else "no", m.route_len_wu, m.time_limit_ticks, m.skipped]
	_timing_label.text = "Gen: %.1fms" % float(_root.qa_state().timing_ms.gen)


func _on_minimap_draw() -> void:
	if _root == null:
		return
	var m: Dictionary = _root.get_mission()
	var places = _root.get_places()
	if m.is_empty() or places == null:
		return
	var canvas: float = places.canvas
	_minimap.draw_rect(Rect2(Vector2.ZERO, MINIMAP_SIZE), Color(0.05, 0.06, 0.08, 0.85), true)
	for n in places.nodes:
		var p: Vector2 = n.pos / canvas * MINIMAP_SIZE
		_minimap.draw_circle(p, 1.5, Color(0.5, 0.5, 0.55, 0.6))
	var sp: Vector2 = places.player_spawn().pos / canvas * MINIMAP_SIZE
	_minimap.draw_rect(Rect2(sp - Vector2(3, 3), Vector2(6, 6)), Color("#4099ff"), true)
	var mp: Vector2 = m.pos / canvas * MINIMAP_SIZE
	var col := Color(0.3, 0.85, 1.0)
	match m.kind:
		"hold_zone":
			_minimap.draw_rect(Rect2(mp - Vector2(4, 4), Vector2(8, 8)), col, true)
		"eliminate_force":
			var pts := PackedVector2Array([mp + Vector2(0, -5), mp + Vector2(5, 0), mp + Vector2(0, 5), mp + Vector2(-5, 0)])
			_minimap.draw_colored_polygon(pts, col)
		"escort_to_extraction":
			var pts2 := PackedVector2Array([mp + Vector2(0, -5), mp + Vector2(4, 4), mp + Vector2(-4, 4)])
			_minimap.draw_colored_polygon(pts2, col)
		_:
			_minimap.draw_circle(mp, 4.0, col)
