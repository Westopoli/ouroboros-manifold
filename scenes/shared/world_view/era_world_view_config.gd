extends Resource
class_name EraWorldViewConfig

@export var era_configs: Dictionary = {
	"settled_reach": {
		"renderer": "res://scenes/shared/world_view/renderers/settled_reach_renderer.tscn",
		"camera": "res://scenes/shared/world_view/cameras/orbital_camera_3d.tscn",
	},
}

func get_renderer_path(era_id: String) -> String:
	if era_id in era_configs:
		return era_configs[era_id].get("renderer", "")
	push_error("No world view config for era: " + era_id)
	return ""

func get_camera_path(era_id: String) -> String:
	if era_id in era_configs:
		return era_configs[era_id].get("camera", "")
	push_error("No world view config for era: " + era_id)
	return ""
