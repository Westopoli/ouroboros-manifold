extends Control

# Piece C5-C1 (R-108-02, R-069-01): the scene routed as "chronicle". The galaxy
# view fills the window until narration begins, then settles at MAP_FRACTION of
# the width while the scroll panel slides in over SLIDE_SEC and spans the rest.
# The root keeps the chronicle entry points by forwarding to the panel.
# See also: scenes/world/chronicle_scroll_panel.gd, tests/test_chronicle_composite.gd

const MAP_FRACTION := 0.62
const SLIDE_SEC := 0.40
# The synchronous load makes the first frame deltas long; the slide skips them
# and clamps every step so the tween never jumps to its end.
const START_FRAME := 2
const MAX_STEP := 0.05

@onready var _map: SubViewportContainer = $MapContainer
@onready var _panel: PanelContainer = $ChronicleScrollPanel

var _frame := 0
var _elapsed := 0.0


func _ready() -> void:
	var mission := get_node_or_null("MapContainer/MapViewport/GalaxyView/UI/Mission")
	if mission != null:
		mission.hide()
	resized.connect(_layout)
	_layout()


func _process(delta: float) -> void:
	_frame += 1
	if _frame < START_FRAME or _elapsed >= SLIDE_SEC:
		return
	_elapsed = minf(_elapsed + minf(delta, MAX_STEP), SLIDE_SEC)
	_layout()


func _layout() -> void:
	if not is_node_ready():
		return
	var progress := 1.0 - pow(1.0 - _elapsed / SLIDE_SEC, 3.0)
	var w := size.x
	var map_w := lerpf(w, w * MAP_FRACTION, progress)
	_map.position = Vector2.ZERO
	_map.size = Vector2(map_w, size.y)
	_panel.size = Vector2(w * (1.0 - MAP_FRACTION), size.y)
	_panel.position = Vector2(lerpf(w, w * MAP_FRACTION, progress), 0.0)


func qa_state() -> Dictionary:
	return _panel.qa_state()


func qa_plant(id: String) -> bool:
	return _panel.qa_plant(id)


func qa_click_entry(entry_id: int) -> void:
	_panel.qa_click_entry(entry_id)


func qa_dismiss() -> void:
	_panel.qa_dismiss()


func set_snapshot(snapshot: Dictionary) -> void:
	_panel.set_snapshot(snapshot)


func load_frame(frame: Dictionary) -> void:
	_panel.load_frame(frame)
