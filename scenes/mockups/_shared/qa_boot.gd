extends SceneTree

func _initialize() -> void:
	var args := OS.get_cmdline_user_args()
	var scene_path := ""
	for i in args.size():
		if args[i] == "--qa-scene" and i + 1 < args.size():
			scene_path = args[i + 1]
	if scene_path == "":
		push_error("qa_boot: missing --qa-scene")
		quit(2)
		return
	if args.has("--qa-live"):
		OS.set_environment("QA_LIVE", "1")
	var packed = load(scene_path)
	if packed == null:
		push_error("qa_boot: cannot load %s" % scene_path)
		quit(2)
		return
	if OS.get_environment("QA_KEEP_AUTOLOADS") == "":
		for child in root.get_children():
			root.remove_child(child)
			child.free()
	var node: Node = packed.instantiate()
	root.add_child(node)
	current_scene = node
