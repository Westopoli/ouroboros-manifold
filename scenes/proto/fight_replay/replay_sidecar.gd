extends RefCounted

## Look-judge rig piece 3 (docs/northstar/plans/cascades/look-judge-rig/spec.md): the per-frame sidecar of the fight replay. `write` saves `frame-<i>.json` (every unit: id, side,
## screen x, y of the glyph centre, radius in px, ID colour) and, with OM_ID_RENDER=1, `frame-<i>.id.png`: the same frame with every unit one flat unique colour, no ground, features, marks or HUD.
## Pure helper: the replay scene passes itself in. Scripts/look/render_checks.py reads the files. See also scenes/proto/fight_replay/fight_replay.gd.

## Distinct from the sky colour and from each other: three channels of 8 steps each, 512 colours, no unit count above that is supported.
const ID_LOW := 60  # not lower: the renderer returns the darkest levels one step off
const ID_STEP := 27
const ID_MAX_UNITS := 512


static func id_colour(k: int) -> Color:
	return Color8(ID_LOW + (k % 8) * ID_STEP, ID_LOW + ((k / 8) % 8) * ID_STEP, ID_LOW + ((k / 64) % 8) * ID_STEP)


## Save the sidecar for frame `i` of `host` (the fight replay, already showing frame i) at `base` (path without extension); then the ID render when OM_ID_RENDER=1.
static func write(host: Node, i: int, base: String) -> void:
	var frame: Dictionary = host._fight_frames[i]
	var size: Vector2 = host.get_viewport().get_texture().get_image().get_size()
	var ratio: float = host._px_ratio()
	var units: Array = []
	var colours: Dictionary = {}
	for u in frame["units"]:
		var k: int = host._ordinal[int(u["id"])]
		if k >= ID_MAX_UNITS:
			push_error("replay_sidecar: unit %d has no unique ID colour (more than %d units)" % [int(u["id"]), ID_MAX_UNITS])
		var c := id_colour(k)
		colours[int(u["id"])] = c
		# x, y is the glyph centre: the drawn body sits GLYPH_LIFT_WU above its ground point, about 5 px higher on screen (check_position measures the glyph against this point)
		var node: Node3D = host._units3d.unit_node(host._ordinal[int(u["id"])])
		var p: Vector2 = host._ground.camera_rig().get_camera().unproject_position(node.global_position) * ratio
		units.append({"id": int(u["id"]), "side": String(u["side"]), "x": p.x, "y": p.y, "radius": host._glyph_width_px(host._ground, float(u["x"]), float(u["y"]), host._glyph_k) * 0.5,
				"colour": "#" + c.to_html(false)})
	var f := FileAccess.open(base + ".json", FileAccess.WRITE)
	if f == null:
		push_error("replay_sidecar: cannot write %s.json" % base)
	else:
		f.store_string(JSON.stringify({"frame": i, "width": int(size.x), "height": int(size.y), "units": units}))
		f.close()
	if OS.get_environment("OM_ID_RENDER") == "1":
		await _write_id_render(host, i, base + ".id.png", colours)


static func _write_id_render(host: Node, i: int, path: String, colours: Dictionary) -> void:
	var hidden: Array = [host._overlay, host._feature_layer, host._ground._mesh, host._ground._slope_view]
	for parent in [host, host.get_tree().root]:  # the HUD and legend layers, and the autoload scanline overlay
		for child in parent.get_children():
			if child is CanvasLayer:
				hidden.append(child)
	for n in hidden:
		n.visible = false
	for u in host._fight_frames[i]["units"]:
		var node: MeshInstance3D = host._units3d.unit_node(host._ordinal[int(u["id"])])
		node.material_override = host._unshaded(colours[int(u["id"])])
		node.get_node("Arrow").visible = false
	await host.get_tree().process_frame
	await RenderingServer.frame_post_draw
	var err: int = host.get_viewport().get_texture().get_image().save_png(path)
	if err != OK:
		push_error("replay_sidecar: save_png %s failed (%d)" % [path, err])
	for n in hidden:
		n.visible = true
	host._show(i)  # the next frame's _show would reset the glyph materials; this resets them now so the scene is as it was
