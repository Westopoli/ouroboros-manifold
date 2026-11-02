extends Node3D

# H-060 beta stage B1: the empty field Launch leads to in the beta, in place of
# tactical_c. A flat plane under the existing camera rig and one HUD line.
# See also: docs/stories/H-060.md (rulings 4, 5), autoload/beta_mode.gd.

@onready var _hud: Label = $Hud/Line


func _ready() -> void:
	_hud.text = "beta B1: field placeholder, %s" % _sha8()


# The build's sha: first 8 hex of the first line of beta_build.txt beside the
# executable (scripts/beta_refresh.sh writes it), `dev` when there is none.
func _sha8() -> String:
	var path := OS.get_executable_path().get_base_dir().path_join("beta_build.txt")
	var seam := OS.get_environment("OM_BETA_BUILD_FILE")
	if seam != "":
		path = seam  # TEST SEAM only (H-060 ruling 5): lets the sha case run headless
	if not FileAccess.file_exists(path):
		return "dev"
	var first := FileAccess.get_file_as_string(path).split("\n")[0].strip_edges()
	return first.substr(0, 8) if first != "" else "dev"
