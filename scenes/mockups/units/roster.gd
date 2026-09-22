class_name Roster
extends RefCounted

const QaPlants := preload("res://scenes/mockups/_shared/qa_plants.gd")

const ROLE_ORDER: Array[String] = ["flanker", "screen", "frontliner", "support", "artillery", "anchor"]
const CATEGORY_OF_ROLE := {
	"flanker": "Strike", "screen": "Strike",
	"frontliner": "Line", "support": "Line",
	"artillery": "Siege", "anchor": "Siege",
}
const TURN_RATE_RAD_S := {"Strike": 6.0, "Line": 4.0, "Siege": 2.5}

var kit_name: String = ""
var palette: Dictionary = {}
var roles: Dictionary = {}


static func from_dict(data: Dictionary) -> Roster:
	var r := Roster.new()
	r.kit_name = str(data.get("name", ""))
	r.palette = data.get("palette", {})
	r.roles = data.get("roles", {})
	return r


static func load_kit(path: String) -> Roster:
	var text := FileAccess.get_file_as_string(path)
	var data = JSON.parse_string(text)
	if typeof(data) != TYPE_DICTIONARY:
		return Roster.from_dict({})
	return Roster.from_dict(data)


func get_role(role: String) -> Dictionary:
	return roles.get(role, {})


func get_stats(role: String) -> Dictionary:
	return get_role(role).get("stats", {})


func get_silhouette(role: String) -> Dictionary:
	var sil: Dictionary = get_role(role).get("silhouette", {})
	if sil.is_empty() or not QaPlants.is_active("silhouettes-same"):
		return sil
	var uniform := sil.duplicate(true)
	uniform["shape"] = "wide_block"
	uniform["size"] = [26, 38, 14]
	return uniform


func get_display_name(role: String) -> String:
	return str(get_role(role).get("display_name", role))


func get_category(role: String) -> String:
	return String(get_stats(role).get("category", CATEGORY_OF_ROLE.get(role, "Line")))


func is_valid() -> bool:
	for role in ROLE_ORDER:
		if not roles.has(role):
			return false
		if get_stats(role).is_empty():
			return false
		if get_silhouette(role).is_empty():
			return false
	return true
