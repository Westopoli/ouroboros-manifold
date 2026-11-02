extends RefCounted

# H-060 ruling 7: beta mode is one question asked in one place. A static
# holder rather than a project autoload (like SimSession): no project.godot
# line. True when env OM_BETA is 1, or --om-beta is on the command line, or
# beta_build.txt sits beside the executable (the exported beta carries it).
# See also: docs/stories/H-060.md, scripts/beta_refresh.sh (writes the file).


static func active() -> bool:
	if OS.get_environment("OM_BETA") == "1":
		return true
	if "--om-beta" in OS.get_cmdline_user_args() or "--om-beta" in OS.get_cmdline_args():
		return true
	return FileAccess.file_exists(OS.get_executable_path().get_base_dir().path_join("beta_build.txt"))
