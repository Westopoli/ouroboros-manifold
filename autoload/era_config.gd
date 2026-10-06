extends Node

const SPACE_ERA_ID: String = "settled_reach"
const GROUND_ERA_ID: String = "greek_placeholder"
const TYPE_IDS: Dictionary = {"raider": 0, "interceptor": 1, "vanguard": 2, "warden": 3, "bombard": 4, "bastion": 5}

var ACTIVE_ERA_ID: String = SPACE_ERA_ID
var _arg_era := false

const LAYER_HEIGHT: float = 250.0
const UNIT_VISUAL_SCALE: float = 2.0

const INACTIVE_LAYER_ALPHA: float = 0.4
const MINIMAP_ENEMY_DIM_ALPHA: float = 0.6


func _ready() -> void:
	var args := OS.get_cmdline_user_args()
	var idx := args.find("--era")
	if idx != -1 and idx + 1 < args.size() and _manifest(args[idx + 1]) != {}:
		ACTIVE_ERA_ID = args[idx + 1]
		_arg_era = true


# Called by UIDataBus once the saved [game] era_id is read; --era wins over it.
func apply_saved(era_id: String) -> void:
	if not _arg_era and _manifest(era_id) != {}:
		ACTIVE_ERA_ID = era_id


func set_era(era_id: String) -> void:
	if _manifest(era_id) != {}:
		ACTIVE_ERA_ID = era_id
		_arg_era = false


func kind() -> String:
	return str(_manifest(ACTIVE_ERA_ID).get("kind", "space"))


# Flat [type_id, kind, ...] for the mission_start request: 0 flying, 1 walking.
func movement_kinds() -> Array:
	var units: Dictionary = _manifest(ACTIVE_ERA_ID).get("units", {})
	var out: Array = []
	for name in TYPE_IDS:
		var row: Dictionary = units.get(name, {})
		out.append(int(TYPE_IDS[name]))
		out.append(1 if str(row.get("movement", "flying")) == "walking" else 0)
	return out


func _manifest(era_id: String) -> Dictionary:
	var text := FileAccess.get_file_as_string("res://assets/eras/%s/manifest.json" % era_id)
	var parsed = JSON.parse_string(text)
	return parsed if parsed is Dictionary else {}
