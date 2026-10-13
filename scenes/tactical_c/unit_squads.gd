extends Node2D
# See also: unit_visuals.gd draws the single body; this draws the extra squad models of marked types (R-132-03).

const OFFSETS: Array[Vector2] = [
	Vector2(0.0, 0.0),
	Vector2(-60.0, 60.0),
	Vector2(60.0, 60.0),
	Vector2(0.0, 110.0),
	Vector2(0.0, -60.0),
]
const MODEL_RADIUS := 10.0
const FACTION_COLORS: Array[Color] = [Color(0.3, 0.6, 1.0), Color(1.0, 0.35, 0.3)]

var _models: Dictionary = {}
var _batches: Array = []


func _init() -> void:
	name = "UnitSquads"


func set_frame(frame: Dictionary, local_faction: int, world_scale: float, camera: Vector2) -> void:
	_models.clear()
	_batches.clear()
	var visible_ids := {}
	for id in frame.get("visible", {}).get(str(local_faction), []):
		visible_ids[int(id)] = true
	var names := {}
	for n in EraConfig.TYPE_IDS:
		names[EraConfig.TYPE_IDS[n]] = n
	# The manifest is read directly: EraThemeResolver loads it in _ready, which can run after the first frame.
	var units: Dictionary = EraConfig._manifest(EraConfig.ACTIVE_ERA_ID).get("units", {})
	var half := get_viewport_rect().size * 0.5 if is_inside_tree() else Vector2(960, 540)
	for u in frame.get("units", []):
		var id := int(u["id"])
		if not visible_ids.has(id):
			continue
		var tname: String = names.get(int(u["type"]), "")
		var row: Dictionary = units.get(tname, {})
		var count: int = clampi(int(row.get("squad_count", 1)), 1, OFFSETS.size())
		if count < 3:
			continue
		var offs: Array = []
		for i in count:
			offs.append(OFFSETS[i] * world_scale)
		_models[id] = offs
		var centre := (Vector2(float(u["x"]), float(u["y"])) - camera) * world_scale + half
		var rot := float(u.get("facing", 0.0)) + float(row.get("facing_offset_rad", 0.0))
		_batches.append({"c": centre, "offs": offs, "rot": rot, "f": int(u["faction"]), "s": world_scale})
	queue_redraw()


func squad_models(id: int) -> Array:
	return _models.get(id, [])


func _draw() -> void:
	for d in _batches:
		var col: Color = FACTION_COLORS[clampi(d["f"], 0, FACTION_COLORS.size() - 1)]
		var r: float = MODEL_RADIUS * clampf(d["s"] * 4.0, 0.5, 1.0)
		for o in d["offs"]:
			var p: Vector2 = d["c"] + o
			var tri := PackedVector2Array([
				p + Vector2(r, 0).rotated(d["rot"]),
				p + Vector2(-r, r * 0.7).rotated(d["rot"]),
				p + Vector2(-r, -r * 0.7).rotated(d["rot"]),
			])
			draw_colored_polygon(tri, col)
